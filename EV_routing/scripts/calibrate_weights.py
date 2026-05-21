"""
Calibrate objective function weights for a specific problem instance.

Run once from the project root:

    PYTHONPATH=EV_routing python EV_routing/scripts/calibrate_weights.py

What it does
------------
Generates N_SAMPLES feasible solutions, measures the mean raw value of each
objective component (distance, time, energy, charging cost), then sets each
weight to 1 / mean so every component contributes ~1.0 to the objective on
average.  This is sample-based normalization as described in:

    Deb, K. (2001). Multi-Objective Optimization Using Evolutionary
    Algorithms. Wiley. Ch. 3.

The penalty weights (battery violation, infeasible visits) are kept as big-M
values following:

    Deb, K. (2000). An efficient constraint handling method for genetic
    algorithms. Computer Methods in Applied Mechanics and Engineering, 186(2-4).

Big-M rule: penalty weight × typical violation >> max feasible objective,
so any infeasible solution scores worse than any feasible one.

Output
------
Saves EV_routing/results/<INSTANCE>/weights.json with:
  - calibrated weights ready for ObjectiveWeights(**weights["weights"])
  - component means (for inspection / reporting)
  - metadata (instance, n_samples, method)

main.py loads this file automatically — no need to copy values by hand.
"""

from __future__ import annotations

import json
import random
import sys
import statistics
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.data_loader import load_problem_data
from tools.battery import EVParameters
from tools.objective import ObjectiveWeights, evaluate_route
from tools.initial_solution import build_ev_feasible_solution
from tools.neighborhoods import generate_neighbor
from tools.feasibility import is_valid_basic_route

# =============================================================================
# CONFIGURATION
# =============================================================================

# Instances to calibrate.  Add as many as you need; they run in order.
INSTANCES = ["sf_75"]

# Set True to skip an instance whose weights.json already exists.
# Set False to force recalibration (e.g. after changing EVParameters).
SKIP_IF_EXISTS = False

# How many feasible solutions to sample.  More = more stable means.
# 100–200 is plenty; computation is fast (each solution ~0.1s).
N_SAMPLES   = 150

# Neighbour perturbations applied to each greedy solution before sampling.
# Adds diversity beyond what the greedy builder alone produces.
N_PERTURB   = 3

# Penalty factor: penalties = PENALTY_FACTOR × (sum of all real terms at their
# mean).  At factor=100, any infeasible solution is ~100× worse than a typical
# feasible one.  Must be >> 1.
PENALTY_FACTOR = 100

# =============================================================================


def _collect_samples(data, ev_params, n_samples: int, n_perturb: int) -> list[dict]:
    """
    Build N_SAMPLES feasible solutions and return their raw component values.

    Strategy: for each seed, build one greedy solution, then apply N_PERTURB
    random neighbour moves.  We keep only valid routes so the means reflect
    actually-feasible solutions.
    """
    unit_weights = ObjectiveWeights(
        distance_weight=1.0,
        travel_time_weight=1.0,
        energy_weight=1.0,
        charging_cost_weight=1.0,
        battery_violation_weight=0.0,   # ignore penalties during sampling
        infeasible_visit_weight=0.0,
    )

    samples: list[dict] = []
    seed = 0

    while len(samples) < n_samples:
        random.seed(seed)
        seed += 1

        route = build_ev_feasible_solution(data, ev_params)

        # Apply a few neighbour moves for diversity
        for _ in range(n_perturb):
            candidate = generate_neighbor(route, data, ev_params)
            if is_valid_basic_route(candidate, data):
                route = candidate

        ev = evaluate_route(route, data, ev_params, unit_weights)
        if not ev.feasible:
            continue  # only calibrate on feasible routes

        samples.append({
            "distance_km":      ev.total_distance_km,
            "time_h":           ev.total_travel_time_h + ev.total_charging_time_h,
            "energy_kwh":       ev.total_energy_consumed_kwh,
            "charging_cost_usd": ev.total_charging_cost_usd,
        })

    return samples


def calibrate(data, ev_params, instance: str = "") -> dict:
    print(f"Generating {N_SAMPLES} feasible sample solutions …")
    samples = _collect_samples(data, ev_params, N_SAMPLES, N_PERTURB)
    print(f"  Collected {len(samples)} feasible solutions\n")

    keys = ["distance_km", "time_h", "energy_kwh", "charging_cost_usd"]
    means = {k: statistics.mean(s[k] for s in samples) for k in keys}
    stds  = {k: statistics.stdev(s[k] for s in samples) for k in keys}

    print("  Component means (raw values of a typical feasible route):")
    print(f"    {'Component':<22} {'Mean':>10}  {'Std':>10}")
    print(f"    {'-'*44}")
    labels = {
        "distance_km":       "Distance (km)",
        "time_h":            "Total time (h)",
        "energy_kwh":        "Energy (kWh)",
        "charging_cost_usd": "Charging cost ($)",
    }
    for k in keys:
        print(f"    {labels[k]:<22} {means[k]:>10.3f}  {stds[k]:>10.3f}")

    # Calibrated real-objective weights: w_i = 1 / mean_i
    # → each term contributes ~1.0 to the objective on an average feasible route
    w_dist  = 1.0 / means["distance_km"]
    w_time  = 1.0 / means["time_h"]
    w_energy= 1.0 / means["energy_kwh"]
    w_cost  = 1.0 / means["charging_cost_usd"]

    # Typical total feasible objective after normalization ≈ 4.0 (one unit per term)
    # Big-M penalty: penalty_weight × typical_violation >> typical_objective
    # A battery violation is ~1-10 kWh; infeasible_visits ~1-5.
    # Setting penalty = PENALTY_FACTOR × 4.0 ensures infeasible >> feasible.
    typical_objective = 4.0  # sum of 4 normalized terms each ~1.0
    w_battery = PENALTY_FACTOR * typical_objective   # e.g. 400
    w_visit   = PENALTY_FACTOR * typical_objective

    weights = {
        "distance_weight":         round(w_dist,   6),
        "travel_time_weight":      round(w_time,   6),
        "energy_weight":           round(w_energy, 6),
        "charging_cost_weight":    round(w_cost,   6),
        "battery_violation_weight":round(w_battery, 4),
        "infeasible_visit_weight": round(w_visit,   4),
    }

    print(f"\n  Calibrated weights (w_i = 1 / mean_i):")
    for k, v in weights.items():
        print(f"    {k:<30} {v}")

    print(f"\n  Penalty weights ({PENALTY_FACTOR}× typical normalized objective ≈ "
          f"{typical_objective:.1f}):")
    print(f"    battery_violation_weight       {w_battery:.1f}")
    print(f"    infeasible_visit_weight        {w_visit:.1f}")

    return {
        "instance": instance,
        "n_samples": N_SAMPLES,
        "n_perturb": N_PERTURB,
        "penalty_factor": PENALTY_FACTOR,
        "method": "sample-based normalization — Deb (2001)",
        "penalty_method": "big-M — Deb (2000)",
        "component_means": {k: round(means[k], 4) for k in keys},
        "component_stds":  {k: round(stds[k],  4) for k in keys},
        "weights": weights,
    }


def main() -> None:
    ev_params = EVParameters(
        battery_capacity_kwh=20.0,
        initial_battery_kwh=20.0,
        energy_consumption_kwh_per_km=0.50,
        average_speed_kmh=50.0,
        grade_factor=3.0,
        speed_exponent=2.0,
    )

    print(f"Calibrating {len(INSTANCES)} instance(s): {INSTANCES}")
    print(f"SKIP_IF_EXISTS = {SKIP_IF_EXISTS}\n")

    for instance in INSTANCES:
        instance_dir = Path(f"EV_routing/instances/{instance}")
        weights_file = Path(f"EV_routing/results/{instance}/weights.json")

        if SKIP_IF_EXISTS and weights_file.exists():
            print(f"[{instance}] weights.json already exists — skipping.")
            continue

        if not instance_dir.exists():
            print(f"[{instance}] Instance directory not found — skipping.")
            print(f"  Run build_instance.py first.")
            continue

        print(f"[{instance}] Loading …")
        data = load_problem_data(instance_dir, ev_params)
        print(f"  {len(data.all_customer_ids)} customers, "
              f"{len(data.all_station_ids)} charging stations\n")

        result = calibrate(data, ev_params, instance)

        weights_file.parent.mkdir(parents=True, exist_ok=True)
        with open(weights_file, "w") as f:
            json.dump(result, f, indent=2)

        print(f"\n  Saved → {weights_file}\n")


if __name__ == "__main__":
    main()
