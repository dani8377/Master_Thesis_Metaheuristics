"""
Quantify how much of a closed tour's energy the grade term actually contributes.

The energy model (Problem Specification, Eq. ev_arc_energy) multiplies a
distance-proportional baseline by a grade multiplier G and a speed multiplier S.
Because elevation is a state function and every route returns to the depot, the
gradient contribution should very nearly cancel over a closed tour -- exactly
cancelling if G were purely linear and S constant.  The max(0.1, .) floor on G
and the per-arc variation in S break exact cancellation.

This measures the residual, so the thesis can state the size of the effect
rather than assert that it "largely cancels".

Usage:
    PYTHONPATH=EV_routing python3.12 EV_routing/scripts/energy_decomposition.py
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, "EV_routing")

from tools.data_loader import load_problem_data
from tools.battery import EVParameters
from tools.initial_solution import build_ev_feasible_solution

EV_PARAMS = EVParameters(
    battery_capacity_kwh=20.0, initial_battery_kwh=20.0,
    energy_consumption_kwh_per_km=0.50, average_speed_kmh=50.0,
    grade_factor=3.0, speed_exponent=2.0,
)


def main() -> None:
    data = load_problem_data(Path("EV_routing/instances/sf_75"), EV_PARAMS)
    d, e, dur, idx = data.dist_array, data.energy_array, data.dur_array, data.dist_index

    # Rebuild S exactly as the loader does, then form the energy the same route
    # would consume with the grade multiplier neutralised (G = 1, S retained).
    with np.errstate(divide="ignore", invalid="ignore"):
        speed = np.where(dur > 0,
                         (d * 1000.0 / np.maximum(dur, 1e-9)) * 3.6,
                         EV_PARAMS.average_speed_kmh)
    speed_mult = (speed / EV_PARAMS.average_speed_kmh) ** EV_PARAMS.speed_exponent
    e_nograde = d * EV_PARAMS.energy_consumption_kwh_per_km * speed_mult

    def tour_parts(route: list[str]) -> tuple[float, float, float]:
        tot_e = tot_km = tot_ng = 0.0
        for a, b in zip(route, route[1:]):
            i, j = idx[a], idx[b]
            tot_e += e[i, j]; tot_km += d[i, j]; tot_ng += e_nograde[i, j]
        return tot_e, tot_km, tot_ng

    rows = []
    greedy = build_ev_feasible_solution(data, EV_PARAMS)
    rows.append(("greedy", *tour_parts(greedy)))

    customers = list(data.all_customer_ids)
    for s in range(5):
        random.seed(s)
        perm = customers[:]
        random.shuffle(perm)
        rows.append((f"random {s}", *tour_parts(["DEPOT"] + perm + ["DEPOT"])))

    print(f"{'tour':<11}{'km':>9}{'E (kWh)':>10}{'E|G=1':>10}{'grade part':>12}{'% of E':>9}")
    worst = 0.0
    for name, te, km, ng in rows:
        pct = (te - ng) / te * 100.0
        worst = max(worst, abs(pct))
        print(f"{name:<11}{km:9.1f}{te:10.2f}{ng:10.2f}{te - ng:+12.2f}{pct:+8.2f}%")

    m = d > 0
    print(f"\nlargest |grade share| over these tours : {worst:.2f}% of total energy")
    print(f"corr(arc energy, arc distance)         : {np.corrcoef(d[m], e[m])[0, 1]:.4f}")
    print(f"corr(arc energy, arc grade component)  : "
          f"{np.corrcoef(e[m], (e - e_nograde)[m])[0, 1]:.4f}")


if __name__ == "__main__":
    main()
