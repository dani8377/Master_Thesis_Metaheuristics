from __future__ import annotations

import csv
import itertools
import json
import random
import time
from pathlib import Path
from typing import Any, Callable

from tools.data_loader import ProblemData
from tools.battery import EVParameters
from tools.objective import ObjectiveWeights, RouteEvaluation

AlgorithmFn = Callable[..., tuple[list[str], RouteEvaluation, Any]]

# Type alias for one trial's result record
TrialResult = dict[str, Any]  # param keys + "mean_cost" + "seed_costs"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _evaluate_params(
    algorithm: AlgorithmFn,
    params: dict[str, Any],
    data: ProblemData,
    ev_params: EVParameters,
    weights: ObjectiveWeights,
    tune_seeds: list[int],
    tune_evaluations: int,
) -> tuple[float, list[float]]:
    """Run algorithm on every seed and return (mean_cost, per_seed_costs)."""
    costs: list[float] = []
    for seed in tune_seeds:
        random.seed(seed)
        try:
            _, eval_result, _ = algorithm(
                data=data,
                ev_params=ev_params,
                weights=weights,
                max_evaluations=tune_evaluations,
                **params,
            )
            costs.append(eval_result.objective_value)
        except Exception:
            costs.append(float("inf"))
    return sum(costs) / len(costs), costs


def save_results(
    all_results: list[TrialResult],
    best_params: dict[str, Any],
    best_mean_cost: float,
    algorithm_name: str,
    results_dir: str | Path,
) -> None:
    """Write CSV of all trials and JSON of best params to results_dir."""
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    name = algorithm_name.lower().replace(" ", "_") or "algorithm"

    # CSV — one row per trial, seed_costs stored as a string
    csv_path = results_dir / f"{name}_results.csv"
    if all_results:
        param_keys = [k for k in all_results[0] if k not in ("mean_cost", "seed_costs")]
        fieldnames = param_keys + ["mean_cost", "seed_costs"]
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in all_results:
                writer.writerow({
                    **{k: row[k] for k in param_keys},
                    "mean_cost": row["mean_cost"],
                    "seed_costs": str(row["seed_costs"]),
                })
        print(f"  Results  → {csv_path}")

    # JSON — best params + score
    json_path = results_dir / f"{name}_best_params.json"
    with open(json_path, "w") as f:
        json.dump({"algorithm": algorithm_name,
                   "best_mean_cost": best_mean_cost,
                   "best_params": best_params}, f, indent=2)
    print(f"  Best params → {json_path}")


# ---------------------------------------------------------------------------
# Grid search
# ---------------------------------------------------------------------------

def grid_search(
    algorithm: AlgorithmFn,
    param_grid: dict[str, list],
    data: ProblemData,
    ev_params: EVParameters,
    weights: ObjectiveWeights,
    tune_seeds: list[int] | None = None,
    tune_evaluations: int = 20_000,
    algorithm_name: str = "",
    verbose: bool = True,
    max_combos_warning: int = 500,
) -> tuple[dict[str, Any], float, list[TrialResult]]:
    """
    Exhaustive grid search over the Cartesian product of param_grid values.

    Parameters
    ----------
    param_grid:
        Mapping of parameter name → list of candidate values.
        Every combination is evaluated.
    tune_seeds:
        Seeds used per trial.  Mean cost is the objective.  Defaults to [0, 1, 2].
    tune_evaluations:
        Evaluation budget per seed run.
    max_combos_warning:
        Print a warning (but still run) if the grid exceeds this many combos.

    Returns
    -------
    (best_params, best_mean_cost, all_results)
        all_results is a list of dicts, one per combination, with all
        parameter keys plus "mean_cost" and "seed_costs".
    """
    if tune_seeds is None:
        tune_seeds = [0, 1, 2]

    keys = list(param_grid.keys())
    combos = list(itertools.product(*[param_grid[k] for k in keys]))
    n_trials = len(combos)

    label = f" [{algorithm_name}]" if algorithm_name else ""
    if verbose:
        print(f"\nGrid search{label}: {n_trials} combinations "
              f"× {len(tune_seeds)} seeds × {tune_evaluations:,} evals/seed")
        if n_trials > max_combos_warning:
            print(f"  WARNING: {n_trials} combos is large — consider reducing "
                  f"grid values or switching to random_search.")
        # Print the grid so it's obvious what's being tried
        print("  Parameter grid:")
        for k in keys:
            print(f"    {k:30s} {param_grid[k]}")
        print()

    best_params: dict[str, Any] = {}
    best_mean_cost = float("inf")
    all_results: list[TrialResult] = []
    t_start = time.perf_counter()
    log_every = max(1, n_trials // 10)

    for trial, combo in enumerate(combos):
        params = dict(zip(keys, combo))
        mean_cost, costs = _evaluate_params(
            algorithm, params, data, ev_params, weights, tune_seeds, tune_evaluations
        )

        all_results.append({**params, "mean_cost": mean_cost, "seed_costs": costs})

        if mean_cost < best_mean_cost:
            best_mean_cost = mean_cost
            best_params = params.copy()
            if verbose:
                print(f"  [{trial + 1:4d}/{n_trials}] ★ {mean_cost:.2f}  {params}")
        elif verbose and (trial + 1) % log_every == 0:
            elapsed = time.perf_counter() - t_start
            eta = elapsed / (trial + 1) * (n_trials - trial - 1)
            print(f"  [{trial + 1:4d}/{n_trials}]   {mean_cost:.2f}"
                  f"  (best={best_mean_cost:.2f},  {elapsed:.0f}s elapsed,"
                  f"  ~{eta:.0f}s remaining)")

    if verbose:
        elapsed = time.perf_counter() - t_start
        print(f"  Done — best {best_mean_cost:.2f} in {elapsed:.0f}s\n")

    return best_params, best_mean_cost, all_results


# ---------------------------------------------------------------------------
# Random search
# ---------------------------------------------------------------------------

def random_search(
    algorithm: AlgorithmFn,
    param_space: dict[str, list],
    data: ProblemData,
    ev_params: EVParameters,
    weights: ObjectiveWeights,
    n_trials: int = 30,
    tune_seeds: list[int] | None = None,
    tune_evaluations: int = 30_000,
    algorithm_name: str = "",
    verbose: bool = True,
) -> tuple[dict[str, Any], float, list[TrialResult]]:
    """
    Random-search tuner: uniformly samples n_trials configurations.

    More efficient than grid search for 5+ parameters
    (Bergstra & Bengio 2012).

    Returns
    -------
    (best_params, best_mean_cost, all_results)
        Signature matches grid_search for drop-in use in tune.py.
    """
    if tune_seeds is None:
        tune_seeds = [0, 1, 2]

    best_params: dict[str, Any] = {}
    best_mean_cost = float("inf")
    all_results: list[TrialResult] = []
    t_start = time.perf_counter()

    label = f" [{algorithm_name}]" if algorithm_name else ""
    if verbose:
        print(f"\nRandom search{label}: {n_trials} trials "
              f"× {len(tune_seeds)} seeds × {tune_evaluations:,} evals/seed")
        print("  Parameter space:")
        for k, v in param_space.items():
            print(f"    {k:30s} {v}")
        print()

    for trial in range(n_trials):
        params = {k: random.choice(v) for k, v in param_space.items()}
        mean_cost, costs = _evaluate_params(
            algorithm, params, data, ev_params, weights, tune_seeds, tune_evaluations
        )

        all_results.append({**params, "mean_cost": mean_cost, "seed_costs": costs})

        if mean_cost < best_mean_cost:
            best_mean_cost = mean_cost
            best_params = params.copy()
            if verbose:
                print(f"  [{trial + 1:3d}/{n_trials}] ★ {mean_cost:.2f}  {params}")
        elif verbose and (trial + 1) % 5 == 0:
            elapsed = time.perf_counter() - t_start
            print(f"  [{trial + 1:3d}/{n_trials}]   {mean_cost:.2f}"
                  f"  (best={best_mean_cost:.2f},  {elapsed:.0f}s elapsed)")

    if verbose:
        elapsed = time.perf_counter() - t_start
        print(f"  Done — best {best_mean_cost:.2f} in {elapsed:.0f}s\n")

    return best_params, best_mean_cost, all_results
