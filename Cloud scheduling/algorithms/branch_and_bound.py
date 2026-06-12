"""
Branch and Bound (B&B) exact algorithm for the cloud task scheduling problem.

Uses best-first search with an admissible lower bound to prune the assignment
tree.  Terminates when either the search tree is exhausted (proven optimal) or
the time / node budget is reached.  Reports the best solution found and the
optimality gap so metaheuristic results can be contextualised.
"""
from __future__ import annotations

import heapq
import time
from dataclasses import dataclass

import numpy as np

from tools.data_loader import SchedulingProblemData
from tools.objective import (
    evaluate_schedule, ObjectiveWeights, ScheduleEvaluation, _PRIORITY_WEIGHTS,
)
from tools.initial_solution import build_greedy_assignment


# ---------------------------------------------------------------------------
# Greedy completion of a partial assignment
# ---------------------------------------------------------------------------

def _greedy_complete(
    depth: int,
    assignment: list[int],
    cpu_loads: np.ndarray,
    mem_loads: np.ndarray,
    data: SchedulingProblemData,
) -> list[int]:
    """
    Extend a partial assignment to a full assignment by greedily placing each
    remaining task on the server that minimises an energy+violation score
    (efficiency * task_energy + heavy penalty for capacity violations).

    Used as an "anytime upper bound" at every popped B&B node so the incumbent
    keeps improving as deeper partial commitments are explored, even when the
    best-first search never reaches a true leaf within the time budget.
    """
    n, m = data.n_tasks, data.n_servers
    if depth >= n:
        return list(assignment)

    complete = list(assignment)
    cpu = cpu_loads.copy()
    mem = mem_loads.copy()
    eff = data.server_efficiency
    cap_cpu = data.server_cpu_cap
    cap_mem = data.server_mem_cap

    for i in range(depth, n):
        task_cpu = data.cpu[i]
        task_mem = data.mem[i]
        task_e   = data.energy[i]

        # Vectorised score across all servers: energy cost + huge violation penalty.
        new_cpu = cpu + task_cpu
        new_mem = mem + task_mem
        viol = (np.maximum(0.0, new_cpu - cap_cpu)
              + np.maximum(0.0, new_mem - cap_mem))
        score = eff * task_e + 1e6 * viol
        j = int(np.argmin(score))

        complete.append(j)
        cpu[j] = new_cpu[j]
        mem[j] = new_mem[j]

    return complete


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

@dataclass
class BBStatistics:
    """Diagnostics reported after one B&B run."""

    nodes_explored: int        # search-tree nodes expanded
    root_lower_bound: float    # LB at the root — tightest lower bound on F*
    proven_optimal: bool       # True only if tree exhausted before time/node limit
    time_elapsed: float        # wall-clock seconds
    optimality_gap: float      # (best_cost - root_lb) / root_lb; 0 when proven optimal

    # Expose the same interface as SA/GA/UMDA history so the plotter works
    @property
    def best_cost_history(self) -> list[float]:
        return []


# ---------------------------------------------------------------------------
# Admissible lower bound
# ---------------------------------------------------------------------------

def _lower_bound(
    depth: int,
    assignment: list[int],
    cpu_loads: np.ndarray,
    mem_loads: np.ndarray,
    data: SchedulingProblemData,
    weights: ObjectiveWeights,
    p_weights: np.ndarray,
    work_remain_suffix: np.ndarray,
    plat_suffix: np.ndarray,
) -> float:
    """
    Compute an admissible lower bound on any completion of the partial assignment.

    Underestimates by:
      - placing remaining tasks on the most energy-efficient server (no new idle cost)
      - ignoring the extra congestion that additional tasks add to assigned servers
      - ignoring capacity violations that remaining tasks may introduce

    The bound is admissible: it never exceeds the true cost of any completion,
    so B&B never incorrectly prunes an optimal branch.

    The depth-independent ingredients are precomputed once per run by
    branch_and_bound() and passed in:
      p_weights          : priority weights omega(p_i), shape (n,)
      work_remain_suffix : min(eta) * sum(energy[d:]) for every d, shape (n+1,)
      plat_suffix        : sum(p_weights[d:] * latency[d:]) for every d, shape (n+1,)
    This turns the two O(n) remaining-task sums into O(1) lookups — the bound
    is evaluated for every child of every expanded node, so this dominates
    B&B's per-node cost.
    """
    # --- Energy ---
    # Idle: only currently active servers (adding tasks can only increase this)
    active  = cpu_loads > 0
    idle_e  = float(np.dot(data.server_idle_power, active))

    if depth > 0:
        a_arr       = np.array(assignment, dtype=np.int32)
        work_done   = float(np.dot(data.server_efficiency[a_arr], data.energy[:depth]))
        # Use current CPU loads (underestimate: adding tasks increases congestion)
        load_ratio = cpu_loads[a_arr] / data.server_cpu_cap[a_arr]
        eff_lat    = data.latency[:depth] * (1.0 + weights.congestion_factor * load_ratio)
        lat_done   = float(np.dot(p_weights[:depth], eff_lat))
    else:
        work_done   = 0.0
        lat_done    = 0.0

    # Remaining tasks: optimistic — all on the most efficient server (energy)
    # and with no congestion (latency).  Suffix arrays end in 0.0 at depth=n.
    total_energy  = idle_e + work_done + float(work_remain_suffix[depth])
    total_latency = lat_done + float(plat_suffix[depth])

    # --- Current violations (can only worsen as more tasks are added) ---
    cpu_viol = float(np.sum(np.maximum(0.0, cpu_loads - data.server_cpu_cap)))
    mem_viol = float(np.sum(np.maximum(0.0, mem_loads - data.server_mem_cap)))

    # --- Combine with the same formula as evaluate_schedule ---
    e_ref = weights.energy_ref or 1.0
    l_ref = weights.latency_ref or 1.0
    c_ref = weights.cpu_ref    or 1.0
    m_ref = weights.mem_ref    or 1.0

    return (
          weights.energy_weight  * total_energy   / e_ref
        + weights.latency_weight * total_latency   / l_ref
        + weights.cpu_penalty    * cpu_viol        / c_ref
        + weights.mem_penalty    * mem_viol        / m_ref
    )


# ---------------------------------------------------------------------------
# Branch and Bound
# ---------------------------------------------------------------------------

def branch_and_bound(
    data: SchedulingProblemData,
    weights: ObjectiveWeights,
    time_limit: float = 60.0,
    max_nodes: int = 500_000,
    verbose: bool = False,
) -> tuple[list[int], ScheduleEvaluation, BBStatistics]:
    """
    Best-first Branch and Bound for cloud task scheduling.

    Assigns tasks one at a time (depth 0..n_tasks-1).  At each node the
    algorithm branches over all n_servers choices for the current task and
    prunes any child whose lower bound >= best known cost.

    Warm-started with the greedy FFD solution as the initial upper bound,
    which typically prunes the tree aggressively from the first iteration.

    Terminates when:
      - the heap is empty  =>  proven optimal, or
      - time_limit seconds have elapsed, or
      - max_nodes nodes have been expanded.

    Returns (best_assignment, best_evaluation, BBStatistics).
    The optimality_gap field quantifies how far the best solution may be from
    F* even when the search was stopped early.
    """
    t_start = time.perf_counter()
    n, m    = data.n_tasks, data.n_servers

    # Greedy warm-start: gives a tight initial upper bound that aggressively prunes
    best_assignment = build_greedy_assignment(data)
    best_eval       = evaluate_schedule(best_assignment, data, weights)
    best_cost       = best_eval.objective_value

    # ---- Precompute depth-independent lower-bound ingredients (once per run) ----
    # The bound is evaluated for every child of every expanded node, so the
    # remaining-task sums must be O(1) lookups, not O(n) re-sums per call.
    p_weights = data.priority_weights
    if p_weights is None:
        p_idx     = np.clip(data.priority, 0, 2).astype(np.int32)
        p_weights = _PRIORITY_WEIGHTS[p_idx]

    # work_remain_suffix[d] = min(eta) * sum(energy[d:]);  [n] = 0.0
    energy_suffix        = np.zeros(n + 1, dtype=np.float64)
    energy_suffix[:n]    = np.cumsum(data.energy[::-1])[::-1]
    work_remain_suffix   = float(data.server_efficiency.min()) * energy_suffix

    # plat_suffix[d] = sum(p_weights[d:] * latency[d:]);  [n] = 0.0
    plat_suffix          = np.zeros(n + 1, dtype=np.float64)
    plat_suffix[:n]      = np.cumsum((p_weights * data.latency)[::-1])[::-1]

    # Root lower bound (empty partial assignment)
    root_lb = _lower_bound(0, [], np.zeros(m), np.zeros(m), data, weights,
                           p_weights, work_remain_suffix, plat_suffix)

    # Heap elements: (lb, tie_break_counter, depth, assignment, cpu_loads, mem_loads)
    counter = 0
    heap: list = [(root_lb, counter, 0, [], np.zeros(m), np.zeros(m))]

    nodes_explored = 0
    proven_optimal = False
    # Greedy-completion frequency: 1 = every internal node, 5 = every 5th, etc.
    # Cheap (vectorised + one evaluate_schedule) but adds overhead at very large n.
    complete_every = 1

    if verbose:
        print(f"  [B&B] root_lb={root_lb:.4f}  upper_bound={best_cost:.4f}"
              f"  gap={(best_cost-root_lb)/max(1e-10,root_lb):.1%}")

    while heap:
        elapsed = time.perf_counter() - t_start
        if elapsed >= time_limit or nodes_explored >= max_nodes:
            break

        lb, _, depth, assignment, cpu_loads, mem_loads = heapq.heappop(heap)
        nodes_explored += 1

        # Prune: this whole subtree cannot improve on the current best
        if lb >= best_cost:
            continue

        if depth == n:
            # Complete assignment found below the current best — update
            ev = evaluate_schedule(assignment, data, weights)
            if ev.objective_value < best_cost:
                best_cost       = ev.objective_value
                best_assignment = list(assignment)
                best_eval       = ev
                if verbose:
                    gap = (best_cost - root_lb) / max(1e-10, root_lb)
                    print(f"  [B&B] new best={best_cost:.4f}  gap={gap:.1%}"
                          f"  nodes={nodes_explored}")
            continue

        # Anytime upper-bound: complete this partial assignment greedily and
        # use it as a candidate incumbent.  Without this, best-first B&B on a
        # loose lower bound (LB ≈ 1.35 vs true optimum ≈ 1.81) explores
        # breadth-first and never reaches a leaf within the budget, so the
        # incumbent would stay at the warm-start forever.
        if depth > 0 and (nodes_explored % complete_every == 0):
            completion = _greedy_complete(depth, assignment, cpu_loads, mem_loads, data)
            ev_c = evaluate_schedule(completion, data, weights)
            if ev_c.objective_value < best_cost:
                best_cost       = ev_c.objective_value
                best_assignment = completion
                best_eval       = ev_c
                if verbose:
                    gap = (best_cost - root_lb) / max(1e-10, root_lb)
                    print(f"  [B&B] new best (greedy-complete)={best_cost:.4f}"
                          f"  gap={gap:.1%}  depth={depth}  nodes={nodes_explored}")

        # Branch: try assigning task `depth` to each server
        task_cpu = data.cpu[depth]
        task_mem = data.mem[depth]

        for j in range(m):
            new_cpu = cpu_loads.copy()
            new_mem = mem_loads.copy()
            new_cpu[j] += task_cpu
            new_mem[j] += task_mem

            new_assign = assignment + [j]
            child_lb   = _lower_bound(depth + 1, new_assign, new_cpu, new_mem, data, weights,
                                      p_weights, work_remain_suffix, plat_suffix)

            if child_lb < best_cost:   # only push if this branch can improve
                counter += 1
                heapq.heappush(heap, (child_lb, counter, depth + 1,
                                      new_assign, new_cpu, new_mem))

    # If the heap drained completely, every branch was pruned or evaluated
    proven_optimal = len(heap) == 0 and nodes_explored < max_nodes
    elapsed        = time.perf_counter() - t_start
    gap            = 0.0 if proven_optimal else (
        (best_cost - root_lb) / max(1e-10, root_lb)
    )

    stats = BBStatistics(
        nodes_explored    = nodes_explored,
        root_lower_bound  = root_lb,
        proven_optimal    = proven_optimal,
        time_elapsed      = elapsed,
        optimality_gap    = gap,
    )
    return best_assignment, best_eval, stats
