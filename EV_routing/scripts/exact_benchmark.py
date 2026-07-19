"""
Exact optimality-gap benchmark for the EVRP on a small instance (sf_10).

1. Builds the sf_10 instance as a prefix subset of sf_25 (same fixed customer
   ordering, same 30 stations, same depot) — no OSRM calls needed, all
   matrices are sliced from the existing sf_25 files.
2. Runs Greedy + SA/GA/MA/ACO (sf_75 tuned params, sf_75 calibrated weights,
   10 seeds, 150k evaluations — the main-experiment protocol).
3. Solves the instance EXACTLY with A* over states
   (visited-customer set, current node, battery level), which searches the
   full route space including arbitrary charging-station chains.  The lower
   bound is admissible (sum of cheapest incoming real-cost arcs for unvisited
   customers + cheapest return arc), so the first goal state popped is the
   optimum over battery-feasible routes.
4. Verifies the exact route through evaluate_route and writes
   results/sf_10/exact_gap.csv with true optimality gaps.

Usage:
    PYTHONPATH=EV_routing python3.12 EV_routing/scripts/exact_benchmark.py
"""
from __future__ import annotations

import csv
import heapq
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

import sys
sys.path.insert(0, "EV_routing")

from tools.data_loader import load_problem_data
from tools.battery import EVParameters
from tools.objective import ObjectiveWeights, evaluate_route
from tools.experiment import run_experiments
from algorithms.simulated_annealing import simulated_annealing
from algorithms.genetic_algorithm import genetic_algorithm
from algorithms.ant_colony import ant_colony_optimization
from algorithms.greedy import greedy_nearest_neighbor

N_CUSTOMERS   = 10
SRC_INSTANCE  = Path("EV_routing/instances/sf_25")
DST_INSTANCE  = Path("EV_routing/instances/sf_10")
RESULTS_DIR   = Path("EV_routing/results/sf_10")
BASE_RESULTS  = Path("EV_routing/results/sf_75")   # weights + tuned params
SEEDS         = list(range(10))
MAX_EVALS     = 150_000
EPS           = 1e-9


# ---------------------------------------------------------------------------
# 1. Instance construction (prefix subset of sf_25)
# ---------------------------------------------------------------------------

def build_sf10() -> None:
    if (DST_INSTANCE / "distance_matrix.csv").exists():
        print(f"[build] {DST_INSTANCE} already exists — skipping build.")
        return
    DST_INSTANCE.mkdir(parents=True, exist_ok=True)

    customers = pd.read_csv(SRC_INSTANCE / "customers.csv").head(N_CUSTOMERS)
    stations  = pd.read_csv(SRC_INSTANCE / "charging_stations.csv")
    depot     = pd.read_csv(SRC_INSTANCE / "depot.csv")

    keep_ids = (
        list(depot["Node ID"])
        + list(customers["Customer ID"])
        + list(stations["Station ID"])
    )

    dist = pd.read_csv(SRC_INSTANCE / "distance_matrix.csv", index_col=0)
    dur  = pd.read_csv(SRC_INSTANCE / "duration_matrix.csv", index_col=0)
    dist.index = dist.index.map(str); dist.columns = dist.columns.map(str)
    dur.index  = dur.index.map(str);  dur.columns  = dur.columns.map(str)

    elev = pd.read_csv(SRC_INSTANCE / "node_elevations.csv")
    elev = elev[elev["Node ID"].isin(keep_ids)]

    customers.to_csv(DST_INSTANCE / "customers.csv", index=False)
    stations.to_csv(DST_INSTANCE / "charging_stations.csv", index=False)
    depot.to_csv(DST_INSTANCE / "depot.csv", index=False)
    dist.loc[keep_ids, keep_ids].to_csv(DST_INSTANCE / "distance_matrix.csv")
    dur.loc[keep_ids, keep_ids].to_csv(DST_INSTANCE / "duration_matrix.csv")
    elev.to_csv(DST_INSTANCE / "node_elevations.csv", index=False)

    meta = {
        "name": "sf_10",
        "n_customers": N_CUSTOMERS,
        "n_stations": len(stations),
        "built_from": "sf_25 (prefix subset, same fixed customer ordering)",
    }
    (DST_INSTANCE / "instance.json").write_text(json.dumps(meta, indent=2))
    print(f"[build] wrote {DST_INSTANCE} ({N_CUSTOMERS} customers, "
          f"{len(stations)} stations)")


# ---------------------------------------------------------------------------
# 2. Exact A* search
# ---------------------------------------------------------------------------

def exact_solve(data, ev_params, weights, incumbent_cost: float,
                incumbent_route: list[str]):
    """
    A* over (visited-customer set, current node, battery).

    Real-cost arc matrix R = w_d*d + w_t*t + w_e*e; charging at station s
    costs q * k_s with k_s = w_t/power_s + w_c*price_s and refills to
    capacity.  Only battery-feasible transitions are expanded, so the
    result is the optimum over routes with zero battery violation.
    """
    ids   = list(data.dist_index.keys())
    idx   = data.dist_index
    n_all = len(ids)

    D = data.dist_array
    E = data.energy_array
    T = data.dur_array / 3600.0
    # constant-speed fallback for unknown durations (matches evaluate_route)
    fallback = D / ev_params.average_speed_kmh
    T = np.where(data.dur_array > 0.0, T, fallback)

    w_d, w_t, w_e = (weights.distance_weight, weights.travel_time_weight,
                     weights.energy_weight)
    w_c = weights.charging_cost_weight
    R = w_d * D + w_t * T + w_e * E

    cust_idx    = [idx[c] for c in ids if data.node_types.get(c) == "customer"]
    station_idx = [idx[s] for s in ids if data.node_types.get(s) == "station"]
    depot_i     = idx["DEPOT"]
    k_cust      = len(cust_idx)
    cust_pos    = {ci: p for p, ci in enumerate(cust_idx)}
    C           = ev_params.battery_capacity_kwh

    k_s = np.zeros(n_all)
    for s in station_idx:
        sid = ids[s]
        k_s[s] = (w_t / data.station_power[sid]
                  + w_c * data.station_price[sid])

    # Admissible LB components: cheapest incoming real-cost arc per customer,
    # cheapest incoming arc to depot (for the final return).
    min_in = np.full(n_all, 0.0)
    for u in cust_idx + [depot_i]:
        col = R[:, u].copy()
        col[u] = np.inf
        min_in[u] = col.min()

    full_mask = (1 << k_cust) - 1

    def lb(mask: int) -> float:
        b = min_in[depot_i]
        for ci in cust_idx:
            if not (mask >> cust_pos[ci]) & 1:
                b += min_in[ci]
        return b

    # state: (f, cost, mask, node, battery, parent_key)
    start = (lb(0), 0.0, 0, depot_i, C)
    heap = [(start[0], 0.0, 0, depot_i, C, None)]
    # dominance: (mask, node) -> list of (battery, cost) non-dominated
    seen: dict[tuple[int, int], list[tuple[float, float]]] = {}
    parent: dict[tuple[int, int, float], tuple] = {}
    popped = 0
    t0 = time.perf_counter()

    def dominated(mask, node, batt, cost) -> bool:
        for (b2, c2) in seen.get((mask, node), []):
            if b2 >= batt - EPS and c2 <= cost + EPS:
                return True
        return False

    def record(mask, node, batt, cost):
        lst = seen.setdefault((mask, node), [])
        lst[:] = [(b2, c2) for (b2, c2) in lst
                  if not (batt >= b2 - EPS and cost <= c2 + EPS)]
        lst.append((batt, cost))

    best_cost  = incumbent_cost
    best_state = None

    while heap:
        f, cost, mask, node, batt, pkey = heapq.heappop(heap)
        popped += 1
        if f >= best_cost - 1e-12:
            break   # admissible bound: nothing better remains
        if dominated(mask, node, batt, cost):
            continue
        record(mask, node, batt, cost)
        key = (mask, node, round(batt, 9))
        parent[key] = pkey

        if mask == full_mask:
            # return to depot
            e = E[node, depot_i]
            if batt - e >= -EPS:
                total = cost + R[node, depot_i]
                if total < best_cost:
                    best_cost  = total
                    best_state = key
            continue

        # expand to unvisited customers
        for ci in cust_idx:
            if (mask >> cust_pos[ci]) & 1:
                continue
            e = E[node, ci]
            if batt - e >= -EPS:
                nc = cost + R[node, ci]
                nm = mask | (1 << cust_pos[ci])
                nb = batt - e
                if nc + lb(nm) < best_cost and not dominated(nm, ci, nb, nc):
                    heapq.heappush(heap, (nc + lb(nm), nc, nm, ci, nb, key))

        # expand to stations (recharge to full)
        for si in station_idx:
            e = E[node, si]
            if batt - e >= -EPS:
                arrive = max(0.0, batt - e)
                q = C - arrive
                nc = cost + R[node, si] + q * k_s[si]
                if nc + lb(mask) < best_cost and not dominated(mask, si, C, nc):
                    heapq.heappush(heap, (nc + lb(mask), nc, mask, si, C, key))

    elapsed = time.perf_counter() - t0
    print(f"[exact] A* done: {popped:,} states popped, {elapsed:.1f}s, "
          f"optimum F* = {best_cost:.6f}")

    if best_state is None:
        print("[exact] incumbent (metaheuristic BKS) is already optimal.")
        return incumbent_cost, incumbent_route, popped, elapsed

    # reconstruct route
    route_rev = ["DEPOT"]
    keyk = best_state
    while keyk is not None:
        mask, node, _ = keyk
        route_rev.append(ids[node])
        keyk = parent.get(keyk)
    route = list(reversed(route_rev))
    return best_cost, route, popped, elapsed


# ---------------------------------------------------------------------------
# 3. Benchmark runner
# ---------------------------------------------------------------------------

def main() -> None:
    build_sf10()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    ev_params = EVParameters(
        battery_capacity_kwh=20.0, initial_battery_kwh=20.0,
        energy_consumption_kwh_per_km=0.50, average_speed_kmh=50.0,
        grade_factor=3.0, speed_exponent=2.0,
    )
    data = load_problem_data(DST_INSTANCE, ev_params)

    w = json.loads((BASE_RESULTS / "weights.json").read_text())["weights"]
    weights = ObjectiveWeights(**w)
    params = json.loads((BASE_RESULTS / "params.json").read_text())

    algos = [
        ("Greedy",              greedy_nearest_neighbor,  {}),
        ("Simulated Annealing", simulated_annealing,      params["SA"]),
        ("Genetic Algorithm",   genetic_algorithm,        params["GA"]),
        ("Memetic Algorithm",   genetic_algorithm,        params["MA"]),
        ("ACO",                 ant_colony_optimization,  params["ACO"]),
    ]

    all_results = []
    for name, fn, kw in algos:
        seeds = [0] if name == "Greedy" else SEEDS
        res = run_experiments(fn, data, ev_params, weights, seeds=seeds,
                              algorithm_name=name, verbose=False,
                              max_evaluations=MAX_EVALS, **kw)
        all_results.append(res)
        print(f"[run] {name:<22} best={res.best_cost:.6f} "
              f"avg={res.average_cost:.6f} feasible="
              f"{res.feasible_run_count}/{len(seeds)} "
              f"t={res.average_runtime:.1f}s")

    bks_res   = min((r for r in all_results if r.algorithm_name != "Greedy"),
                    key=lambda r: r.best_cost)
    incumbent = bks_res.best_cost
    inc_route = bks_res.best_solution
    print(f"[run] metaheuristic incumbent: {incumbent:.6f} "
          f"({bks_res.algorithm_name})")

    f_star, route, popped, elapsed = exact_solve(
        data, ev_params, weights, incumbent + 1e-9, inc_route)

    # verify through the objective function
    check = evaluate_route(route, data, ev_params, weights)
    assert abs(check.objective_value - f_star) < 1e-6, (
        f"exact-solver mismatch: DP={f_star:.8f} "
        f"evaluate_route={check.objective_value:.8f}")
    assert check.feasible, "exact route not feasible?!"
    print(f"[exact] verified with evaluate_route: F = "
          f"{check.objective_value:.6f}, feasible = {check.feasible}")
    print(f"[exact] route: {' '.join(route)}")

    # save
    (RESULTS_DIR / "exact_route.json").write_text(json.dumps({
        "objective": f_star, "route": route,
        "states_popped": popped, "solve_time_s": elapsed,
        "weights_from": str(BASE_RESULTS / "weights.json"),
        "params_from": str(BASE_RESULTS / "params.json"),
        "seeds": SEEDS, "max_evaluations": MAX_EVALS,
    }, indent=2))

    with open(RESULTS_DIR / "exact_gap.csv", "w", newline="") as fcsv:
        wr = csv.DictWriter(fcsv, fieldnames=[
            "algorithm", "best", "avg", "std",
            "gap_best_pct", "gap_avg_pct", "feasible_runs", "n_runs",
            "avg_runtime_s", "f_star",
        ])
        wr.writeheader()
        for r in all_results:
            wr.writerow({
                "algorithm":     r.algorithm_name,
                "best":          f"{r.best_cost:.6f}",
                "avg":           f"{r.average_cost:.6f}",
                "std":           f"{r.std_cost:.6f}",
                "gap_best_pct":  f"{(r.best_cost - f_star)/f_star*100:.4f}",
                "gap_avg_pct":   f"{(r.average_cost - f_star)/f_star*100:.4f}",
                "feasible_runs": r.feasible_run_count,
                "n_runs":        len(r.seeds),
                "avg_runtime_s": f"{r.average_runtime:.4f}",
                "f_star":        f"{f_star:.6f}",
            })
    print(f"[save] {RESULTS_DIR/'exact_gap.csv'}")


if __name__ == "__main__":
    main()
