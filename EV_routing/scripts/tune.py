"""
Standalone hyperparameter tuning pipeline.

Run from the project root:

    PYTHONPATH=EV_routing python EV_routing/scripts/tune.py

What it does
------------
1. Loads the problem data once.
2. For each algorithm listed in ALGORITHMS, runs grid or random search
   (controlled per-algorithm via SEARCH below).
3. Prints a ranked top-10 table of configurations.
4. Saves all trial results to  EV_routing/results/<instance>/tuning/<algo>_results.csv
5. Saves a two-panel analysis figure to EV_routing/results/<instance>/figures/tuning/<algo>_tuning.png
6. Writes the best parameters for ALL algorithms to EV_routing/results/<instance>/params.json
   so main.py picks them up automatically.

Adjusting the search
--------------------
- SEARCH  — dict mapping algorithm name → "grid" or "random".
  Use "grid" only for fast algorithms (SA) or small grids (< ~200 combos).
  Use "random" for GA / MA / ACO — same quality, much faster.
- N_RANDOM_TRIALS — number of random trials (used when strategy is "random").
- TUNE_SEEDS       — seeds per trial. More = slower but more reliable.
- TUNE_EVALS       — eval budget per seed per trial.  Kept EQUAL across all
  algorithms (50k) so no algorithm is tuned closer to the final 150k
  deployment budget than another.

Runtime reference (@ 50k evals on this machine, 30 random trials × 2 seeds):
  SA   60 runs × ~2s   ≈  2 min
  GA   60 runs × ~12s  ≈ 12 min
  MA   60 runs × ~7s   ≈  7 min
  ACO  60 runs × ~18s  ≈ 18 min
"""

import json
import sys
import time
from pathlib import Path

# Make sure EV_routing is on the path when run via PYTHONPATH=EV_routing
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.data_loader import load_problem_data
from tools.battery import EVParameters
from tools.objective import ObjectiveWeights
from tools.tuning import grid_search, random_search, save_results
from tools.plot import plot_tuning_results
from algorithms.simmulated_annealing import simulated_annealing
from algorithms.genetic_algorithm import genetic_algorithm
from algorithms.ant_colony import ant_colony_optimization

# ── Instance selection ────────────────────────────────────────────────────────
# List every instance you want to tune in one run.
# Each must exist under EV_routing/instances/.
INSTANCES = ["sf_75"]

# Set True to skip an instance whose params.json already exists.
# Set False to force re-tuning (e.g. after changing grids or TUNE_EVALS).
SKIP_IF_EXISTS = False
# ─────────────────────────────────────────────────────────────────────────────

# ── Which algorithms to tune ──────────────────────────────────────────────────
# Comment out any you don't want to re-tune.
ALGORITHMS = ["SA", "GA", "MA", "ACO"]

# ── Search strategy (per algorithm) ──────────────────────────────────────────
# "grid"   → exhaustive over every combination (only practical for SA).
# "random" → sample N_RANDOM_TRIALS configs at random (use for GA/MA/ACO).
SEARCH = {
    "SA":  "random",
    "GA":  "random",
    "MA":  "random",
    "ACO": "random",
}
N_RANDOM_TRIALS = 30       # used when strategy is "random"

# ── Tuning budget ─────────────────────────────────────────────────────────────
TUNE_SEEDS  = [0, 1]       # seeds per trial (more = slower but more reliable)
# All algorithms get the SAME reduced tuning budget (50k).  Equal budgets
# ensure no algorithm's hyperparameters are selected under conditions closer
# to the final 150k experiment than another's — the asymmetry, not the
# reduction, is what would bias the comparison.  Any reduced-budget transfer
# error applies to all four algorithms identically.
TUNE_EVALS  = {
    "SA":  50_000,
    "GA":  50_000,
    "MA":  50_000,
    "ACO": 50_000,
}

# =============================================================================
# Parameter grids
# =============================================================================
# Each entry is  parameter_name → list of values to try.
# For grid search every combination is evaluated, so keep lists short.
# Rule of thumb: aim for < 200 total combinations per algorithm.
# For random search the lists act as the sampling pool.

SA_GRID = {
    # Calibrated for TUNE_EVALS=50k (equal across algorithms), MAX_EVALS=150k.
    # Objective is normalised to ~4.0 for a feasible route.
    #
    # Temperature scale: exp(-delta/T) ≈ 0.8 for a typical worsening move
    # of delta≈0.1 → T ≈ 0.45.  Range [0.1, 0.5, 1.5] covers cold/warm/hot starts.
    #
    # Cooling-cycle budget check (T_min=1e-3): even the slowest schedule
    # (rate=0.997, 100 iters/temp → 2,301 × 100 = 230k) completes most of a
    # cycle at 150k; faster schedules fit multiple full cycles + reheats.
    "initial_temperature":        [0.1,  0.5,  1.5],
    "cooling_rate":               [0.993, 0.995, 0.997],
    "iterations_per_temperature": [20,   50,   100],
    "reheat_patience":            [100,  250,  500],
    "reheat_factor":              [0.2,  0.4,  0.6],
}
# 3^5 = 243 combos — random search with 60 trials samples this well

GA_GRID = {
    "population_size": [40,  100, 200],
    "crossover_rate":  [0.75, 0.85, 0.95],
    "mutation_rate":   [0.05, 0.15, 0.25],
    "tournament_size": [2,   4],
    "elitism_count":   [1,   3,   5],
}
# 3^3 × 2^2 = 108 combos × 2 seeds × ~5s ≈ 18 min  (use SEARCH="random" if too slow)

MA_GRID = {
    **GA_GRID,
    "local_search_iters": [5, 15, 30],
}
# 108 × 3 = 324 combos — recommend SEARCH="random" for MA

ACO_GRID = {
    "n_ants":                [10,  20,  30],
    "alpha":                 [0.5, 1.0, 2.0],
    "beta":                  [2.0, 4.0, 6.0],
    "rho":                   [0.05, 0.15, 0.30],
    "q0":                    [0.75, 0.85, 0.95],
    "battery_threshold_frac":[0.2,  0.4],
    "local_search_iters":    [0,   10],
    "candidate_list_k":      [0,   15],
}
# 3^5 × 2^3 = 1944 combos — use SEARCH="random" for ACO

GRIDS = {"SA": SA_GRID, "GA": GA_GRID, "MA": MA_GRID, "ACO": ACO_GRID}
ALGO_FNS = {
    "SA":  simulated_annealing,
    "GA":  genetic_algorithm,
    "MA":  genetic_algorithm,   # MA uses the same function with local_search_iters
    "ACO": ant_colony_optimization,
}


# =============================================================================
# Helpers
# =============================================================================

def _print_top_n(results: list, n: int = 10, algorithm_name: str = "") -> None:
    sorted_r = sorted(results, key=lambda r: r["mean_cost"])
    label = f" [{algorithm_name}]" if algorithm_name else ""
    print(f"\n  Top {min(n, len(sorted_r))} configurations{label}:")
    print(f"  {'Rank':>4}  {'Mean cost':>10}  Parameters")
    print(f"  {'-'*4}  {'-'*10}  {'-'*50}")
    for rank, r in enumerate(sorted_r[:n], 1):
        params = {k: v for k, v in r.items() if k not in ("mean_cost", "seed_costs")}
        print(f"  {rank:4d}  {r['mean_cost']:10.2f}  {params}")


# =============================================================================
# Main
# =============================================================================

def _tune_instance(instance: str, ev_params: EVParameters) -> None:
    instance_dir = Path(f"EV_routing/instances/{instance}")
    results_dir  = Path(f"EV_routing/results/{instance}/tuning")
    figures_dir  = Path(f"EV_routing/results/{instance}/figures/tuning")
    params_file  = Path(f"EV_routing/results/{instance}/params.json")

    if not instance_dir.exists():
        print(f"[{instance}] Instance directory not found — skipping.")
        print("  Run build_instance.py first.")
        return

    if SKIP_IF_EXISTS and params_file.exists():
        print(f"[{instance}] params.json already exists — skipping.")
        print("  Set SKIP_IF_EXISTS = False to force re-tuning.")
        return

    print("Loading problem data …")
    data = load_problem_data(instance_dir, ev_params)
    print(f"  {len(data.all_customer_ids)} customers, "
          f"{len(data.all_station_ids)} charging stations")

    weights_file = params_file.parent / "weights.json"
    if weights_file.exists():
        _w = json.loads(weights_file.read_text())["weights"]
        weights = ObjectiveWeights(**_w)
        print(f"  Weights loaded from {weights_file}")
    else:
        print("  No weights.json found — using defaults. Run calibrate_weights.py first.")
        weights = ObjectiveWeights()
    print()

    print("=" * 60)
    print(f"Instance        : {instance}  ({instance_dir})")
    print(f"Algorithms      : {', '.join(ALGORITHMS)}")
    print(f"Seeds           : {TUNE_SEEDS}")
    for algo_name in ALGORITHMS:
        strategy = SEARCH[algo_name]
        label = f"random ({N_RANDOM_TRIALS} trials)" if strategy == "random" else "grid"
        evals = TUNE_EVALS[algo_name]
        print(f"  {algo_name:4s} → {label}, {evals:,} evals/seed")
    print("=" * 60)

    all_best: dict[str, dict] = {}

    for algo_name in ALGORITHMS:
        grid       = GRIDS[algo_name]
        fn         = ALGO_FNS[algo_name]
        strategy   = SEARCH[algo_name]
        tune_evals = TUNE_EVALS[algo_name]
        t0         = time.perf_counter()

        if strategy == "grid":
            best_params, best_cost, all_results = grid_search(
                algorithm=fn,
                param_grid=grid,
                data=data,
                ev_params=ev_params,
                weights=weights,
                tune_seeds=TUNE_SEEDS,
                tune_evaluations=tune_evals,
                algorithm_name=algo_name,
                verbose=True,
            )
        else:
            best_params, best_cost, all_results = random_search(
                algorithm=fn,
                param_space=grid,
                data=data,
                ev_params=ev_params,
                weights=weights,
                n_trials=N_RANDOM_TRIALS,
                tune_seeds=TUNE_SEEDS,
                tune_evaluations=tune_evals,
                algorithm_name=algo_name,
                verbose=True,
            )

        elapsed = time.perf_counter() - t0
        all_best[algo_name] = best_params

        _print_top_n(all_results, n=10, algorithm_name=algo_name)

        save_results(all_results, best_params, best_cost, algo_name, results_dir)

        fig_path = figures_dir / f"{algo_name.lower()}_tuning.png"
        plot_tuning_results(all_results, algorithm_name=algo_name, save_path=fig_path, show=False)
        print(f"  Figure  → {fig_path}")
        print(f"  Total time: {elapsed:.0f}s\n")

    print("\n" + "=" * 60)
    print("Best parameters found")
    print("=" * 60)
    for name, params in all_best.items():
        print(f"\n  {name}:")
        for k, v in params.items():
            print(f"    {k:30s} = {v}")

    # Preserve params for algorithms NOT in this run
    existing: dict = {}
    if params_file.exists():
        with open(params_file) as f:
            existing = json.load(f)
    for algo_name, params in all_best.items():
        existing[algo_name] = params
    params_file.parent.mkdir(parents=True, exist_ok=True)
    with open(params_file, "w") as f:
        json.dump(existing, f, indent=2)
    print(f"\nParams written to {params_file}")


def main() -> None:
    ev_params = EVParameters(
        battery_capacity_kwh=20.0,
        initial_battery_kwh=20.0,
        energy_consumption_kwh_per_km=0.50,
        average_speed_kmh=50.0,
        grade_factor=3.0,
        speed_exponent=2.0,
    )

    print(f"Tuning {len(INSTANCES)} instance(s): {INSTANCES}")
    print(f"SKIP_IF_EXISTS = {SKIP_IF_EXISTS}\n")

    for instance in INSTANCES:
        print(f"\n{'=' * 60}")
        print(f"  INSTANCE: {instance}")
        print(f"{'=' * 60}")
        _tune_instance(instance, ev_params)


if __name__ == "__main__":
    main()
