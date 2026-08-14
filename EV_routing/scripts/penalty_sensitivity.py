"""
Is the penalty multiplier critical?

The penalty coefficients are set to 100x the calibrated feasible cost scale.
That factor is a calibration choice of this thesis, not a value any cited
method supplies, so this sweeps it and measures whether the search notices.

Only the two penalty weights change; the four real-cost weights are untouched,
so the reported objective of a *feasible* solution is directly comparable
across settings.  SA is used because it spends the largest share of its search
in the infeasible region and is therefore the most exposed of the four.

Run on the main instance (20 kWh) and on a tight cell of the battery sweep
(10 kWh), where the feasible region is smaller and fragmented.

Usage:
    PYTHONPATH=EV_routing python3.12 EV_routing/scripts/penalty_sensitivity.py
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
from algorithms.simulated_annealing import simulated_annealing

BASE = Path("EV_routing/results/sf_75")
OUT = Path("EV_routing/results/side_experiments/penalty_sensitivity.csv")
MULTIPLIERS = [10, 100, 1000, 10000]     # 100 is the value used throughout
CAPACITIES = [20.0, 10.0]
SEEDS = list(range(10))


def main() -> None:
    w0 = json.loads((BASE / "weights.json").read_text())["weights"]
    sa = json.loads((BASE / "params.json").read_text())["SA"]
    rows = []

    for cap in CAPACITIES:
        ev = EVParameters(battery_capacity_kwh=cap, initial_battery_kwh=cap,
                          energy_consumption_kwh_per_km=0.50, average_speed_kmh=50.0,
                          grade_factor=3.0, speed_exponent=2.0)
        data = load_problem_data(Path("EV_routing/instances/sf_75"), ev)

        for mult in MULTIPLIERS:
            weights = ObjectiveWeights(**w0)
            weights.battery_violation_weight = 4.0 * mult
            weights.infeasible_visit_weight = 4.0 * mult
            res = run_experiments(simulated_annealing, data, ev, weights, seeds=SEEDS,
                                  algorithm_name=f"SA (penalty x{mult})", verbose=False,
                                  max_evaluations=150_000, **sa)
            feas = [e.objective_value for e in res.best_evals if e.feasible]
            rows.append({
                "battery_kwh": cap,
                "multiplier": mult,
                "lambda": 4.0 * mult,
                "feasible_runs": len(feas),
                "n_runs": len(SEEDS),
                "mean_F_feasible": f"{sum(feas)/len(feas):.6f}" if feas else "",
                "best_F_feasible": f"{min(feas):.6f}" if feas else "",
            })
            print(f"  {cap:>5.0f} kWh  x{mult:<6} lambda={4.0*mult:<7.0f} "
                  f"feasible {len(feas)}/{len(SEEDS)}  "
                  f"mean {rows[-1]['mean_F_feasible']}  best {rows[-1]['best_F_feasible']}",
                  flush=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)
    print(f"[save] {OUT}")


if __name__ == "__main__":
    main()
