from __future__ import annotations

import random
import statistics
import time
from dataclasses import dataclass, field

import numpy as np

from tools.objective import evaluate_route, ObjectiveWeights, RouteEvaluation
from tools.initial_solution import build_ev_feasible_solution
from tools.feasibility import is_energy_feasible, is_valid_basic_route
from tools.neighborhoods import repair_battery_violation, generate_neighbor
from tools.data_loader import ProblemData
from tools.battery import EVParameters


@dataclass
class ACOStatistics:
    """Diagnostic statistics collected during an ACO run."""

    best_cost_history: list[float] = field(default_factory=list)
    mean_cost_history: list[float] = field(default_factory=list)
    # Cost CV of the ant colony per iteration — mirrors GA's diversity metric.
    diversity_history: list[float] = field(default_factory=list)
    # Pheromone CV: std/mean of the full τ matrix.
    # Starts near-zero (uniform τ_max); rises as pheromone concentrates on
    # good arcs, signalling algorithmic convergence.
    pheromone_cv_history: list[float] = field(default_factory=list)
    feasibility_history: list[float] = field(default_factory=list)
    evals_at_step: list[int] = field(default_factory=list)

    total_evaluated: int = 0
    total_iterations: int = 0

    @property
    def feasibility_rate(self) -> float:
        if not self.feasibility_history:
            return 0.0
        return self.feasibility_history[-1]


# ---------------------------------------------------------------------------
# Next-node selection  (ACS pseudo-random proportional rule)
# ---------------------------------------------------------------------------

def _select_next_idx(attract_row: np.ndarray, q0: float) -> int:
    """
    Return the 0-based position within ``attract_row`` of the selected candidate.

    Greedy (argmax) with probability q0; probabilistic otherwise.
    """
    n = len(attract_row)
    if n == 1:
        return 0

    if random.random() < q0:
        return int(attract_row.argmax())

    total = float(attract_row.sum())
    if total == 0.0:
        return random.randrange(n)

    r = random.random() * total
    cumsum = 0.0
    for i in range(n):
        cumsum += float(attract_row[i])
        if r <= cumsum:
            return i
    return n - 1


# ---------------------------------------------------------------------------
# Route construction for one ant
# ---------------------------------------------------------------------------

def _construct_route(
    attract: np.ndarray,          # precomputed τ^α · η^β  (n_nodes × n_nodes)
    q0: float,
    battery_threshold_frac: float,
    data: ProblemData,
    ev_params: EVParameters,
    candidate_list: np.ndarray | None = None,  # shape (n_nodes, k) — customer positions
) -> list[str]:
    """
    Construct one ant's complete route.

    Customer reachability is checked with a vectorised numpy mask over the
    customer index array, avoiding the O(n) Python loop per step.

    Charging stations are inserted two ways:
      - Forced:    no customer reachable → nearest reachable CS, deterministic.
      - Optional:  battery < threshold   → CS added to candidate set,
                   chosen by attract.
    A battery-full-but-stuck guard prevents infinite loops when a customer is
    unreachable from any node even at maximum battery.
    """
    dist_index          = data.dist_index
    energy_array        = data.energy_array
    dist_array          = data.dist_array
    customer_node_ids   = data.all_customer_ids
    customer_matrix_idx = data.customer_matrix_idx
    all_stations        = data.all_station_ids
    station_matrix_idx  = data.station_matrix_idx
    capacity           = ev_params.battery_capacity_kwh
    threshold          = battery_threshold_frac * capacity
    n_cust             = len(customer_node_ids)

    # Boolean mask + integer counter (avoids repeated .any() numpy calls)
    unvisited_mask = np.ones(n_cust, dtype=bool)
    n_unvisited = n_cust
    route: list[str] = ["DEPOT"]
    battery = ev_params.initial_battery_kwh
    current = "DEPOT"
    ci = dist_index[current]  # always valid — updated on each move

    while n_unvisited > 0:
        # Vectorised reachability: energy from ci to each customer ≤ battery
        energy_to_custs = energy_array[ci, customer_matrix_idx]
        reachable_mask = unvisited_mask & (energy_to_custs <= battery)
        n_reachable = int(reachable_mask.sum())

        if n_reachable == 0:
            unvisited_cidx = customer_matrix_idx[unvisited_mask]
            energy_to_sta = energy_array[ci, station_matrix_idx]

            if battery >= capacity - 1e-6:
                # Full battery, no direct customer path.
                # Bridge: nearest station that can reach ≥1 unvisited customer.
                can_bridge = (energy_array[station_matrix_idx, :][:, unvisited_cidx] <= capacity).any(axis=1)
                reachable_bridge = can_bridge & (energy_to_sta <= battery)
                if not reachable_bridge.any():
                    break
                dist_to_sta = dist_array[ci, station_matrix_idx]
                best_pos = int(np.where(reachable_bridge, dist_to_sta, np.inf).argmin())
                route.append(all_stations[best_pos])
                battery = capacity
                current = all_stations[best_pos]
                ci = dist_index[current]
                continue

            # Low battery — forced charge at nearest reachable station
            reachable_sta = energy_to_sta <= battery
            if not reachable_sta.any():
                break
            dist_to_sta = dist_array[ci, station_matrix_idx]
            best_pos = int(np.where(reachable_sta, dist_to_sta, np.inf).argmin())
            route.append(all_stations[best_pos])
            battery = capacity
            current = all_stations[best_pos]
            ci = dist_index[current]
            continue

        # Build candidate set — numpy throughout, no Python list comprehensions.
        # cand_cust_pos: positions in customer_node_ids / customer_matrix_idx
        if candidate_list is not None:
            # Restrict to k-nearest customers; fall back to all reachable if none qualify.
            cl_pos = candidate_list[ci]                          # k nearest customer positions
            cl_unvis = cl_pos[unvisited_mask[cl_pos]]
            cl_reach = cl_unvis[(energy_to_custs[cl_unvis] <= battery)]
            cand_cust_pos = cl_reach if len(cl_reach) > 0 else np.where(reachable_mask)[0]
        else:
            cand_cust_pos  = np.where(reachable_mask)[0]
        cand_cust_midx = customer_matrix_idx[cand_cust_pos]   # matrix indices

        # Optional stations when battery is below threshold
        sta_cand_pos: np.ndarray | None = None
        if battery < threshold:
            energy_to_sta  = energy_array[ci, station_matrix_idx]
            sta_reach_mask = energy_to_sta <= battery
            if sta_reach_mask.any():
                sta_cand_pos   = np.where(sta_reach_mask)[0]
                cand_all_midx  = np.concatenate([cand_cust_midx, station_matrix_idx[sta_cand_pos]])
            else:
                cand_all_midx  = cand_cust_midx
        else:
            cand_all_midx = cand_cust_midx

        attract_row = attract[ci, cand_all_midx]
        sel          = _select_next_idx(attract_row, q0)

        n_cust_cands = len(cand_cust_pos)
        if sel < n_cust_cands:
            p          = int(cand_cust_pos[sel])
            ni         = int(cand_cust_midx[sel])
            next_node  = customer_node_ids[p]
            battery   -= energy_array[ci, ni]
            unvisited_mask[p] = False
            n_unvisited -= 1
        else:
            sp         = int(sta_cand_pos[sel - n_cust_cands])  # type: ignore[index]
            ni         = int(station_matrix_idx[sp])
            next_node  = all_stations[sp]
            battery   -= energy_array[ci, ni]
            battery    = capacity

        route.append(next_node)
        current = next_node
        ci      = ni  # update cached index

    # Safety net: append remaining unvisited customers before the depot return.
    # Appending keeps them contiguous so repair_battery_violation can fix the
    # block in a single pass rather than scattered violations.
    missed = [customer_node_ids[int(p)] for p in np.where(unvisited_mask)[0]]
    for c in missed:
        route.append(c)

    # Return to depot, inserting CS if energy is insufficient
    ci = dist_index.get(current)
    di_depot = dist_index.get("DEPOT")
    if ci is not None and di_depot is not None:
        energy_to_sta = energy_array[ci, station_matrix_idx]
        for _ in range(len(all_stations) + 1):
            if battery >= energy_array[ci, di_depot]:
                break
            if battery >= capacity - 1e-6:
                break
            reachable_sta = energy_to_sta <= battery
            if not reachable_sta.any():
                break
            dist_to_sta = dist_array[ci, station_matrix_idx]
            dist_to_sta_masked = np.where(reachable_sta, dist_to_sta, np.inf)
            best_pos = int(dist_to_sta_masked.argmin())
            route.append(all_stations[best_pos])
            battery = capacity
            current = all_stations[best_pos]
            ci = dist_index[current]
            energy_to_sta = energy_array[ci, station_matrix_idx]

    route.append("DEPOT")

    # Energy repair for violations from safety-net insertions.
    # Cap at 5 passes: violations from end-appended customers almost always
    # resolve in ≤3; remaining infeasibility is handled by the objective penalty.
    for _ in range(5):
        if is_energy_feasible(route, data, capacity):
            break
        route = repair_battery_violation(route, data, ev_params)

    return route


# ---------------------------------------------------------------------------
# Main algorithm  (MMAS — Max-Min Ant System)
# ---------------------------------------------------------------------------

def _build_candidate_list(
    data: ProblemData,
    k: int,
) -> np.ndarray:
    """
    For each node (row), return the indices of the k nearest *customer* nodes
    in ascending distance order.  Shape: (n_nodes, k).

    Used at construction time to restrict each ant's next-customer candidates
    to its k nearest unvisited customers rather than all 75.  This focuses
    pheromone on short, promising arcs and reduces noise in the selection.
    Standard in ACO-TSP (Dorigo & Stützle 2004, §3.4).
    """
    dist   = data.dist_array                                  # (n, n)
    c_idx  = data.customer_matrix_idx                         # positions of customers
    n      = dist.shape[0]
    k      = min(k, len(c_idx))

    # For every node: distances to each customer node, then argsort
    dist_to_custs = dist[:, c_idx]                            # (n, n_custs)
    # argsort along customer axis — result is customer *positions* (not matrix indices)
    sorted_cust_pos = np.argsort(dist_to_custs, axis=1)[:, :k]  # (n, k)
    return sorted_cust_pos                                    # dtype intp


def ant_colony_optimization(
    data: ProblemData,
    ev_params: EVParameters,
    weights: ObjectiveWeights,
    n_ants: int = 20,
    alpha: float = 1.0,
    beta: float = 3.0,
    rho: float = 0.1,
    q0: float = 0.9,
    battery_threshold_frac: float = 0.3,
    local_search_iters: int = 0,
    candidate_list_k: int = 0,
    max_evaluations: int = 150_000,
    time_limit_s: float | None = None,
) -> tuple[list[str], RouteEvaluation, ACOStatistics]:
    """
    Max-Min Ant System (MMAS) for EV routing.

    Construction
    ------------
    Each ant builds a complete route using a battery-aware ACS selection rule.
    Customers are chosen by pheromone × heuristic (attractiveness matrix,
    precomputed once per iteration for speed).  Charging stations enter the
    candidate set when battery drops below ``battery_threshold_frac``, so the
    pheromone can learn optimal charging positions over iterations.

    Pheromone update (MMAS)
    -----------------------
    Only one ant deposits pheromone per iteration, alternating between the
    iteration-best and the global-best with equal probability.  All values are
    clipped to [τ_min, τ_max] after each update, preventing premature
    convergence and stagnation.

        τ_max = 1 / (ρ × L_best_so_far)
        τ_min = τ_max / (2 × n_nodes)

    Stopping
    --------
    Whichever of ``max_evaluations`` or ``time_limit_s`` is reached first.
    """
    stats = ACOStatistics()
    t_start = time.perf_counter()

    def _over_budget() -> bool:
        if stats.total_evaluated >= max_evaluations:
            return True
        if time_limit_s is not None and time.perf_counter() - t_start >= time_limit_s:
            return True
        return False

    dist_index = data.dist_index
    n_nodes = data.dist_array.shape[0]

    # Precompute candidate list (k nearest customers per node) if requested
    candidate_list: np.ndarray | None = None
    if candidate_list_k > 0:
        candidate_list = _build_candidate_list(data, candidate_list_k)

    # Precompute heuristic matrix η(i,j) = 1/dist, zero on diagonal
    with np.errstate(divide="ignore", invalid="ignore"):
        heuristic = np.where(data.dist_array > 0, 1.0 / data.dist_array, 0.0)

    # Initialise pheromone using the greedy-solution cost (standard MMAS init).
    # The greedy solution is also kept as an "elite ant" that deposits pheromone
    # in the first iteration alongside the constructed ants — same warm-start
    # advantage that SA (starts from greedy) and GA (greedy first individual) get.
    greedy_sol = build_ev_feasible_solution(data, ev_params)
    greedy_eval = evaluate_route(greedy_sol, data, ev_params, weights)
    stats.total_evaluated += 1

    best_solution = greedy_sol[:]
    best_eval = greedy_eval
    best_cost = greedy_eval.objective_value

    tau_max = 1.0 / (rho * best_cost) if best_cost > 0 else 1.0
    tau_min = tau_max / (2.0 * n_nodes)
    pheromone = np.full((n_nodes, n_nodes), tau_max)

    # Precompute heuristic^beta once (it never changes)
    heuristic_beta = heuristic ** beta

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    while not _over_budget():
        stats.total_iterations += 1

        # Attractiveness matrix: τ^α · η^β  (recomputed each iteration)
        # Fast path when alpha == 1.0 (avoids an element-wise power on the full matrix)
        attract = pheromone * heuristic_beta if alpha == 1.0 else (pheromone ** alpha) * heuristic_beta

        # Iteration 1: seed with greedy solution as an elite ant (no extra eval cost —
        # greedy_eval was counted at init).  Gives ACO the same warm-start advantage
        # that SA has (starts from greedy) and GA has (greedy first individual).
        if stats.total_iterations == 1:
            iter_solutions: list[list[str]] = [greedy_sol]
            iter_evals: list[RouteEvaluation] = [greedy_eval]
        else:
            iter_solutions = []
            iter_evals = []

        for _ in range(n_ants):
            if _over_budget():
                break
            route = _construct_route(attract, q0, battery_threshold_frac, data, ev_params, candidate_list)
            route_eval = evaluate_route(route, data, ev_params, weights)
            stats.total_evaluated += 1

            # Local search phase (Hybrid/Memetic ACO when local_search_iters > 0)
            if local_search_iters > 0:
                route_cost = route_eval.objective_value
                for _ in range(local_search_iters):
                    if _over_budget():
                        break
                    ls_cand = generate_neighbor(route, data, ev_params)
                    if not is_valid_basic_route(ls_cand, data):
                        continue
                    ls_eval = evaluate_route(ls_cand, data, ev_params, weights)
                    stats.total_evaluated += 1
                    if ls_eval.objective_value < route_cost:
                        route = ls_cand
                        route_eval = ls_eval
                        route_cost = ls_eval.objective_value

            iter_solutions.append(route)
            iter_evals.append(route_eval)

            if route_eval.objective_value < best_cost:
                best_solution = route[:]
                best_eval = route_eval
                best_cost = route_eval.objective_value

        if not iter_solutions:
            break

        # ------------------------------------------------------------------
        # MMAS pheromone update
        # ------------------------------------------------------------------
        iter_costs = [e.objective_value for e in iter_evals]
        iter_best_idx = int(np.argmin(iter_costs))

        # Alternate iteration-best / global-best deposition
        if random.random() < 0.5:
            update_route, update_cost = iter_solutions[iter_best_idx], iter_costs[iter_best_idx]
        else:
            update_route, update_cost = best_solution, best_cost

        pheromone *= (1.0 - rho)

        delta = 1.0 / update_cost if update_cost > 0 else 0.0
        for k in range(len(update_route) - 1):
            oi = dist_index.get(update_route[k])
            di = dist_index.get(update_route[k + 1])
            if oi is not None and di is not None:
                pheromone[oi, di] += delta

        tau_max = 1.0 / (rho * best_cost) if best_cost > 0 else 1.0
        tau_min = tau_max / (2.0 * n_nodes)
        np.clip(pheromone, tau_min, tau_max, out=pheromone)

        # ------------------------------------------------------------------
        # Per-iteration statistics
        # ------------------------------------------------------------------
        mean_cost = statistics.mean(iter_costs)
        std_cost = statistics.stdev(iter_costs) if len(iter_costs) >= 2 else 0.0
        cost_cv = std_cost / mean_cost if mean_cost > 0 else 0.0

        tau_flat = pheromone.ravel()
        tau_mean = float(tau_flat.mean())
        pheromone_cv = float(tau_flat.std() / tau_mean) if tau_mean > 0 else 0.0

        feasible_frac = sum(1 for e in iter_evals if e.feasible) / len(iter_evals)

        stats.best_cost_history.append(best_cost)
        stats.mean_cost_history.append(mean_cost)
        stats.diversity_history.append(cost_cv)
        stats.pheromone_cv_history.append(pheromone_cv)
        stats.feasibility_history.append(feasible_frac)
        stats.evals_at_step.append(stats.total_evaluated)

    return best_solution, best_eval, stats
