"""
Ablation: does SA's reheating mechanism actually help on sf_75?

SA is configured with reheat_patience = 250 and reheat_factor = 0.2, adopted as
a standard defence against stagnation.  This disables reheating by pushing the
patience beyond the number of temperature steps the budget affords, holding
every other tuned parameter fixed, and compares against the reheat-enabled
figures in results/sf_75/results_summary.csv over the same 20 seeds.

The comparison is conservative: the reheat parameters were tuned jointly with
the rest of the SA configuration *with* reheating enabled, so the retained
parameters favour the reheat-on arm if anything.

Usage:
    PYTHONPATH=EV_routing python3.12 EV_routing/scripts/sa_reheat_ablation.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, "EV_routing")

from tools.data_loader import load_problem_data
from tools.battery import EVParameters
from tools.objective import ObjectiveWeights
from tools.experiment import run_experiments
from algorithms.simulated_annealing import simulated_annealing

EV_PARAMS = EVParameters(
    battery_capacity_kwh=20.0, initial_battery_kwh=20.0,
    energy_consumption_kwh_per_km=0.50, average_speed_kmh=50.0,
    grade_factor=3.0, speed_exponent=2.0,
)
BASE = Path("EV_routing/results/sf_75")


def main() -> None:
    data = load_problem_data(Path("EV_routing/instances/sf_75"), EV_PARAMS)
    weights = ObjectiveWeights(**json.loads((BASE / "weights.json").read_text())["weights"])
    sa_kwargs = json.loads((BASE / "params.json").read_text())["SA"]

    no_reheat = dict(sa_kwargs)
    no_reheat["reheat_patience"] = 1_000_000   # beyond any reachable step count

    res = run_experiments(
        simulated_annealing, data, EV_PARAMS, weights, seeds=list(range(20)),
        algorithm_name="SA (reheating disabled)", verbose=False,
        max_evaluations=150_000, **no_reheat,
    )
    print(f"reheat OFF : best={res.best_cost:.6f}  mean={res.average_cost:.6f}  "
          f"worst={res.worst_cost:.6f}  std={res.std_cost:.6f}  "
          f"feasible={res.feasible_run_count}/20")
    print("reheat ON  : see results/sf_75/results_summary.csv "
          "(best=2.464935 mean=2.558273 worst=2.752221 std=0.066545)")


if __name__ == "__main__":
    main()
