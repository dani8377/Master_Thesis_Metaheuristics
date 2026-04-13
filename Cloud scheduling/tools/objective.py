"""
objective.py — Objective function for the Cloud Scheduling problem.

PURPOSE
-------
Implements the scalar fitness function F(X) that the metaheuristic minimises.
Given a candidate assignment vector (which task goes on which server), this
file computes every cost component and combines them into a single number.

THE OBJECTIVE FUNCTION
----------------------
F(X) = w_e · E(X)                          ← energy cost
     + w_l · L(X)                          ← priority-weighted latency
     + λ_cpu · Σ_j max(0, U_cpu_j − C_j)  ← CPU capacity penalty
     + λ_mem · Σ_j max(0, U_mem_j − M_j)  ← memory capacity penalty

Energy model  E(X):
    Idle component:     each active server pays its fixed idle-power cost.
    Workload component: each task adds η_j · e_i Watts, where η_j is the
                        server's efficiency and e_i is the task's baseline draw.
    These two terms together reward consolidation (fewer active servers = less
    idle power) while still preferring efficient machines.

Latency model  L(X):
    Effective latency of task i on server j scales with the server's CPU load:
        l̂_ij = l_i · (1 + γ · U_cpu_j / C_j)
    High-priority tasks are weighted more heavily (ω: Low=1, Medium=2, High=4).
    This creates a deliberate tension with the energy term: energy rewards
    packing tasks tightly, latency penalises the congestion that packing causes.

Penalties:
    Capacity constraints are soft — violated solutions are not hard-rejected
    but are penalised heavily so SA naturally steers back to feasibility.

DESIGN NOTE
-----------
All aggregations use numpy bincount / fancy indexing so the function stays
fully vectorised and can be called hundreds of thousands of times in the SA
inner loop without becoming a bottleneck.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from tools.data_loader import SchedulingProblemData

# Priority weight lookup: index = priority class (0, 1, or 2)
# ω(Low=0) = 1,  ω(Medium=1) = 2,  ω(High=2) = 4
_PRIORITY_WEIGHTS = np.array([1.0, 2.0, 4.0])


# ---------------------------------------------------------------------------
# Configuration dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ObjectiveWeights:
    """
    Tunable coefficients for the objective function.

    w_e, w_l trade off energy versus latency.
    λ_cpu, λ_mem are large penalty coefficients that ensure capacity
    violations dominate the objective, pushing SA back to feasibility.
    γ (congestion_factor) controls how steeply latency rises with server load.
    """

    energy_weight: float     = 1.0      # w_e  — weight on total energy E(X)
    latency_weight: float    = 1.0      # w_l  — weight on total latency L(X)
    cpu_penalty: float       = 1000.0   # λ_cpu — penalty per % of CPU overcapacity
    mem_penalty: float       = 5.0      # λ_mem — penalty per MB of memory overcapacity
                                        #  (mem violations can be tens of thousands of MB,
                                        #   so λ_mem is intentionally smaller than λ_cpu)
    congestion_factor: float = 1.0      # γ — 0 = no congestion effect; 1 = linear


@dataclass
class ScheduleEvaluation:
    """
    Full breakdown of a schedule's cost.

    Returned by evaluate_schedule() and stored by the SA and experiment
    harness.  The objective_value field is the scalar used for all
    accept/reject decisions.
    """

    total_energy: float      # E(X) in Watts
    total_latency: float     # L(X) in ms — priority-weighted, congestion-adjusted
    cpu_violation: float     # Σ_j max(0, U_cpu_j − C_j)  in %
    mem_violation: float     # Σ_j max(0, U_mem_j − M_j)  in MB
    n_active_servers: int    # servers hosting at least one task (y_j = 1)
    objective_value: float   # F(X) — the single number SA minimises
    feasible: bool           # True when cpu_violation = mem_violation = 0


# ---------------------------------------------------------------------------
# Evaluation function
# ---------------------------------------------------------------------------

def evaluate_schedule(
    assignment: list[int],
    data: SchedulingProblemData,
    weights: ObjectiveWeights,
) -> ScheduleEvaluation:
    """
    Evaluate a candidate assignment vector and return a ScheduleEvaluation.

    assignment[i] = j  means task i is placed on server j (0-indexed).
    """
    # Convert to numpy once so all downstream ops are vectorised
    a = np.asarray(assignment, dtype=np.int32)  # shape (n_tasks,)
    m = data.n_servers

    # ------------------------------------------------------------------ #
    # Step 1: Compute per-server CPU and memory loads using bincount.     #
    # bincount(a, weights=x)[j] = sum of x[i] for all i where a[i] == j  #
    # This is equivalent to U_cpu_j = Σ_i c_i · x_ij in the formulation. #
    # ------------------------------------------------------------------ #
    cpu_load = np.bincount(a, weights=data.cpu, minlength=m)   # shape (m,)
    mem_load = np.bincount(a, weights=data.mem, minlength=m)   # shape (m,)
    # y_j = 1 if at least one task is assigned to server j, else 0
    active   = np.bincount(a, minlength=m) > 0                  # bool, shape (m,)

    # ------------------------------------------------------------------ #
    # Step 2: Energy model                                                #
    # E(X) = Σ_j e_idle_j · y_j  +  Σ_i η_{a_i} · e_i                 #
    # ------------------------------------------------------------------ #
    idle_energy     = float(np.dot(data.server_idle_power, active))
    # server_efficiency[a] broadcasts: for each task i, look up η of its server
    workload_energy = float(np.dot(data.server_efficiency[a], data.energy))
    total_energy    = idle_energy + workload_energy

    # ------------------------------------------------------------------ #
    # Step 3: Priority-weighted congestion latency                        #
    # l̂_ij = l_i · (1 + γ · U_cpu_j / C_j)                            #
    # L(X) = Σ_i ω(p_i) · l̂_ij                                        #
    # ------------------------------------------------------------------ #
    # load_ratio[i] = CPU utilisation ratio of the server task i is on
    load_ratio  = cpu_load[a] / data.server_cpu_cap[a]
    eff_latency = data.latency * (1.0 + weights.congestion_factor * load_ratio)

    # Map priority integers to weight values; clip guards against unknown classes
    p_idx     = np.clip(data.priority, 0, 2).astype(np.int32)
    p_weights = _PRIORITY_WEIGHTS[p_idx]                        # shape (n_tasks,)

    total_latency = float(np.dot(p_weights, eff_latency))

    # ------------------------------------------------------------------ #
    # Step 4: Capacity violation penalties                                #
    # ------------------------------------------------------------------ #
    cpu_violation = float(np.sum(np.maximum(0.0, cpu_load - data.server_cpu_cap)))
    mem_violation = float(np.sum(np.maximum(0.0, mem_load - data.server_mem_cap)))

    # ------------------------------------------------------------------ #
    # Step 5: Combine into scalar objective                               #
    # ------------------------------------------------------------------ #
    objective_value = (
        weights.energy_weight  * total_energy
        + weights.latency_weight * total_latency
        + weights.cpu_penalty    * cpu_violation
        + weights.mem_penalty    * mem_violation
    )

    # A solution is feasible only when neither capacity is violated anywhere
    feasible = (cpu_violation == 0.0) and (mem_violation == 0.0)

    return ScheduleEvaluation(
        total_energy=total_energy,
        total_latency=total_latency,
        cpu_violation=cpu_violation,
        mem_violation=mem_violation,
        n_active_servers=int(np.sum(active)),
        objective_value=objective_value,
        feasible=feasible,
    )
