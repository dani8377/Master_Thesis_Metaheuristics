"""
Three follow-up experiments on the sf_75 instance family:

1. hybrid   — ACO→SA budget-adaptive hybrid vs. its parents at 30k and 150k
              evaluations (balanced mode, 10 seeds).
2. eco      — ACO with the energy-based construction heuristic (η = 1/energy)
              vs. the standard distance heuristic under eco weights
              (10 seeds, 150k evaluations); tests whether the eco-mode
              steerability failure is caused by the distance heuristic.
3. candlist — ACO candidate-list sizes k ∈ {0, 15, 25} at n ∈ {300, 500}
              (5 seeds, 30k evaluations); tests the standard remedy for
              ACO's super-linear per-iteration cost.

Usage:
    PYTHONPATH=EV_routing python3.12 EV_routing/scripts/side_experiments.py [--smoke]
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
from algorithms.ant_colony import ant_colony_optimization
from algorithms.hybrid_aco_sa import hybrid_aco_sa

SMOKE = "--smoke" in sys.argv

BASE = Path("EV_routing/results/sf_75")
OUT = Path("EV_routing/results/side_experiments")
OUT.mkdir(parents=True, exist_ok=True)

EV_PARAMS = EVParameters(
    battery_capacity_kwh=20.0, initial_battery_kwh=20.0,
    energy_consumption_kwh_per_km=0.50, average_speed_kmh=50.0,
    grade_factor=3.0, speed_exponent=2.0,
)

_w = json.loads((BASE / "weights.json").read_text())["weights"]
PARAMS = json.loads((BASE / "params.json").read_text())

ECO_MULT = {"distance": 0.4, "time": 0.4, "energy": 2.8, "charging_cost": 0.4}


def make_weights(mult: dict | None = None) -> ObjectiveWeights:
    w = ObjectiveWeights(**_w)
    if mult:
        w.distance_weight *= mult["distance"]
        w.travel_time_weight *= mult["time"]
        w.energy_weight *= mult["energy"]
        w.charging_cost_weight *= mult["charging_cost"]
    return w


def row_from(res, extra: dict) -> dict:
    ev = res.best_eval
    return {
        **extra,
        "algorithm": res.algorithm_name,
        "best": f"{res.best_cost:.6f}",
        "avg": f"{res.average_cost:.6f}",
        "std": f"{res.std_cost:.6f}",
        "feasible_runs": res.feasible_run_count,
        "n_runs": len(res.seeds),
        "avg_runtime_s": f"{res.average_runtime:.4f}",
        "best_energy_kwh": f"{ev.total_energy_consumed_kwh:.4f}",
        "avg_energy_kwh": f"{sum(e.total_energy_consumed_kwh for e in res.best_evals)/len(res.best_evals):.4f}",
        "avg_time_h": f"{sum(e.total_travel_time_h + e.total_charging_time_h for e in res.best_evals)/len(res.best_evals):.4f}",
        "avg_charge_usd": f"{sum(e.total_charging_cost_usd for e in res.best_evals)/len(res.best_evals):.4f}",
    }


FIELDS = ["experiment", "budget", "instance", "k", "heuristic",
          "algorithm", "best", "avg", "std", "feasible_runs", "n_runs",
          "avg_runtime_s", "best_energy_kwh", "avg_energy_kwh",
          "avg_time_h", "avg_charge_usd"]


def save(rows: list[dict], name: str) -> None:
    path = OUT / name
    with open(path, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=FIELDS, restval="")
        wr.writeheader()
        wr.writerows(rows)
    print(f"[save] {path}")


def run_hybrid() -> None:
    seeds = [0] if SMOKE else list(range(10))
    budgets = [3_000] if SMOKE else [30_000, 150_000]
    data = load_problem_data(Path("EV_routing/instances/sf_75"), EV_PARAMS)
    weights = make_weights()
    rows = []
    for budget in budgets:
        for name, fn, kw in [
            ("Simulated Annealing", simulated_annealing, PARAMS["SA"]),
            ("ACO", ant_colony_optimization, PARAMS["ACO"]),
            ("Hybrid ACO+SA", hybrid_aco_sa,
             {"aco_frac": 0.2, "aco_kwargs": PARAMS["ACO"],
              "sa_kwargs": PARAMS["SA"]}),
        ]:
            res = run_experiments(fn, data, EV_PARAMS, weights, seeds=seeds,
                                  algorithm_name=name, verbose=False,
                                  max_evaluations=budget, **kw)
            rows.append(row_from(res, {"experiment": "hybrid",
                                       "budget": budget, "instance": "sf_75"}))
            print(f"[hybrid] budget={budget:>7,} {name:<20} "
                  f"avg={res.average_cost:.4f} best={res.best_cost:.4f} "
                  f"t={res.average_runtime:.1f}s")
    save(rows, "hybrid.csv")


def run_eco() -> None:
    seeds = [0] if SMOKE else list(range(10))
    budget = 3_000 if SMOKE else 150_000
    data = load_problem_data(Path("EV_routing/instances/sf_75"), EV_PARAMS)
    weights = make_weights(ECO_MULT)
    rows = []
    for label, basis in [("distance", "distance"), ("energy", "energy")]:
        kw = dict(PARAMS["ACO"])
        kw["heuristic_basis"] = basis
        res = run_experiments(ant_colony_optimization, data, EV_PARAMS,
                              weights, seeds=seeds,
                              algorithm_name=f"ACO ({label} heuristic)",
                              verbose=False, max_evaluations=budget, **kw)
        rows.append(row_from(res, {"experiment": "eco", "budget": budget,
                                   "instance": "sf_75", "heuristic": label}))
        print(f"[eco] heuristic={label:<9} avg_F={res.average_cost:.4f} "
              f"avg_energy={rows[-1]['avg_energy_kwh']} kWh "
              f"t={res.average_runtime:.1f}s")
    save(rows, "eco_heuristic.csv")


def run_candlist() -> None:
    seeds = [0] if SMOKE else list(range(5))
    budget = 3_000 if SMOKE else 30_000
    sizes = [300] if SMOKE else [300, 500]
    rows = []
    for n in sizes:
        data = load_problem_data(Path(f"EV_routing/instances/sf_{n}"),
                                 EV_PARAMS)
        weights = make_weights()
        for k in [0, 15, 25]:
            kw = dict(PARAMS["ACO"])
            kw["candidate_list_k"] = k
            res = run_experiments(ant_colony_optimization, data, EV_PARAMS,
                                  weights, seeds=seeds,
                                  algorithm_name=f"ACO (k={k})",
                                  verbose=False, max_evaluations=budget, **kw)
            rows.append(row_from(res, {"experiment": "candlist",
                                       "budget": budget,
                                       "instance": f"sf_{n}", "k": k}))
            print(f"[candlist] n={n} k={k:<3} avg_F={res.average_cost:.4f} "
                  f"t={res.average_runtime:.1f}s")
    save(rows, "candidate_list.csv")


if __name__ == "__main__":
    run_hybrid()
    run_eco()
    run_candlist()
    print("[done] all side experiments complete")
