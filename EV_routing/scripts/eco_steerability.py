"""
Eco-mode steerability of ACO: is the rigidity paradigmatic or a tuning artefact?

The main experiment finds that ACO barely responds to the Eco weights (energy
+0.6% against Balanced, where SA/MA/GA all fall 3.5-10.7%).  The existing
energy-heuristic follow-up rules out the *basis* of the heuristic as the cause,
but it holds beta = 6.0 fixed -- the exponent tuned under Balanced weights and
reused unchanged in every mode.  Two untested explanations remain:

  (a) beta is too high.  The pheromone term IS mode-aware (deposits are 1/F on
      complete routes, so tau sees all four cost terms), but tau^alpha is
      drowned out by eta^beta at beta = 6.0.  Lowering beta should let the
      mode-aware signal through.
  (b) eta is mode-blind.  Making eta itself reflect the active weights should
      let the mode steer construction directly.

This runs the 2 x 4 factorial (heuristic basis x beta) under Eco weights on
sf_75 at the full budget, 20 seeds, everything else at the tuned values.

Headline metric is mean ENERGY (what Eco mode is meant to minimise), compared
against ACO's Balanced-mode energy (86.09 kWh) and its tuned Eco-mode energy
(86.58 kWh).  Steering works if a variant pushes energy meaningfully below the
latter.

Usage:
    PYTHONPATH=EV_routing python3.12 EV_routing/scripts/eco_steerability.py [--smoke]
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, "EV_routing")

from tools.data_loader import load_problem_data
from tools.battery import EVParameters
from tools.objective import ObjectiveWeights
from tools.experiment import run_experiments
from algorithms.ant_colony import ant_colony_optimization

SMOKE = "--smoke" in sys.argv

BASE = Path("EV_routing/results/sf_75")
OUT = Path("EV_routing/results/side_experiments")
OUT.mkdir(parents=True, exist_ok=True)

EV_PARAMS = EVParameters(
    battery_capacity_kwh=20.0, initial_battery_kwh=20.0,
    energy_consumption_kwh_per_km=0.50, average_speed_kmh=50.0,
    grade_factor=3.0, speed_exponent=2.0,
)

ECO_MULT = {"distance": 0.4, "time": 0.4, "energy": 2.8, "charging_cost": 0.4}

_w = json.loads((BASE / "weights.json").read_text())["weights"]
PARAMS = json.loads((BASE / "params.json").read_text())


def eco_weights() -> ObjectiveWeights:
    w = ObjectiveWeights(**_w)
    w.distance_weight *= ECO_MULT["distance"]
    w.travel_time_weight *= ECO_MULT["time"]
    w.energy_weight *= ECO_MULT["energy"]
    w.charging_cost_weight *= ECO_MULT["charging_cost"]
    return w


FIELDS = ["heuristic", "beta", "avg_F", "best_F", "std_F",
          "avg_energy_kwh", "avg_time_h", "avg_dist_km", "avg_charge_usd",
          "feasible_runs", "n_runs", "avg_runtime_s"]


def main() -> None:
    seeds = [0, 1] if SMOKE else list(range(20))
    budget = 3_000 if SMOKE else 150_000
    betas = [6.0] if SMOKE else [1.0, 2.0, 4.0, 6.0]
    bases = ["distance", "weighted"]

    data = load_problem_data(Path("EV_routing/instances/sf_75"), EV_PARAMS)
    weights = eco_weights()

    rows = []
    for basis in bases:
        for beta in betas:
            kw = dict(PARAMS["ACO"])
            kw["heuristic_basis"] = basis
            kw["beta"] = beta
            res = run_experiments(
                ant_colony_optimization, data, EV_PARAMS, weights, seeds=seeds,
                algorithm_name=f"ACO ({basis}, beta={beta})", verbose=False,
                max_evaluations=budget, **kw,
            )
            evs = res.best_evals
            n = len(evs)
            row = {
                "heuristic": basis,
                "beta": beta,
                "avg_F": f"{res.average_cost:.6f}",
                "best_F": f"{res.best_cost:.6f}",
                "std_F": f"{res.std_cost:.6f}",
                "avg_energy_kwh": f"{sum(e.total_energy_consumed_kwh for e in evs)/n:.4f}",
                "avg_time_h": f"{sum(e.total_travel_time_h + e.total_charging_time_h for e in evs)/n:.4f}",
                "avg_dist_km": f"{sum(e.total_distance_km for e in evs)/n:.4f}",
                "avg_charge_usd": f"{sum(e.total_charging_cost_usd for e in evs)/n:.4f}",
                "feasible_runs": res.feasible_run_count,
                "n_runs": n,
                "avg_runtime_s": f"{res.average_runtime:.4f}",
            }
            rows.append(row)
            print(f"[eco-steer] {basis:<9} beta={beta:<4} "
                  f"F={res.average_cost:.4f}  energy={row['avg_energy_kwh']} kWh  "
                  f"dist={row['avg_dist_km']} km  t={res.average_runtime:.1f}s",
                  flush=True)

    path = OUT / "eco_steerability.csv"
    with open(path, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=FIELDS)
        wr.writeheader()
        wr.writerows(rows)
    print(f"[save] {path}")
    print("\nReference points (20 seeds, tuned ACO):")
    print("  Balanced-mode energy: 86.09 kWh")
    print("  Eco-mode energy (beta=6.0, distance): 86.58 kWh  <- the rigidity")


if __name__ == "__main__":
    main()
