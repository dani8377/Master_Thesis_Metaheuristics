from __future__ import annotations

"""
Random-search hyperparameter tuner for metaheuristic algorithms.

Each trial uniformly samples one configuration from the parameter space,
runs it on every seed in ``tune_seeds`` with a reduced evaluation budget,
and tracks the configuration with the lowest mean objective value.

Rationale for random search over grid search: for 4–6 continuous-ish
parameters, random search explores the space more efficiently than a
Cartesian grid (Bergstra & Bengio 2012).
"""

import random
import time
from typing import Any, Callable

from tools.data_loader import ProblemData
from tools.battery import EVParameters
from tools.objective import ObjectiveWeights, RouteEvaluation

AlgorithmFn = Callable[..., tuple[list[str], RouteEvaluation, Any]]


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
) -> tuple[dict[str, Any], float]:
    """
    Random-search tuner.

    Parameters
    ----------
    algorithm:
        Callable matching ``(data, ev_params, weights, **kwargs) → (sol, eval, stats)``.
    param_space:
        Mapping of parameter name → list of candidate values.  One value is
        sampled uniformly per trial.
    n_trials:
        Number of random configurations to evaluate.
    tune_seeds:
        Random seeds used per trial.  Mean cost across seeds is the objective.
        Defaults to ``[0, 1, 2]``.
    tune_evaluations:
        Evaluation budget per individual seed run during tuning.  Should be
        smaller than the final comparison budget to keep tuning tractable.
    algorithm_name:
        Label shown in verbose output.
    verbose:
        Print progress.

    Returns
    -------
    (best_params, best_mean_cost)
        ``best_params`` is a dict ready to be passed as ``**kwargs`` to the
        algorithm (does not include budget parameters).
    """
    if tune_seeds is None:
        tune_seeds = [0, 1, 2]

    best_params: dict[str, Any] = {}
    best_mean_cost = float("inf")
    t_start = time.perf_counter()

    label = f" [{algorithm_name}]" if algorithm_name else ""
    if verbose:
        print(
            f"Tuning{label}: {n_trials} trials × {len(tune_seeds)} seeds"
            f" × {tune_evaluations:,} evals/seed"
        )

    for trial in range(n_trials):
        params = {k: random.choice(v) for k, v in param_space.items()}

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

        mean_cost = sum(costs) / len(costs)

        if mean_cost < best_mean_cost:
            best_mean_cost = mean_cost
            best_params = params.copy()
            if verbose:
                print(f"  [{trial + 1:2d}/{n_trials}] ★ {mean_cost:.2f}  {params}")
        elif verbose and (trial + 1) % 5 == 0:
            elapsed = time.perf_counter() - t_start
            print(
                f"  [{trial + 1:2d}/{n_trials}]   {mean_cost:.2f}"
                f"  (best={best_mean_cost:.2f},  {elapsed:.0f}s elapsed)"
            )

    if verbose:
        elapsed = time.perf_counter() - t_start
        print(f"  Done — best {best_mean_cost:.2f} in {elapsed:.0f}s\n")

    return best_params, best_mean_cost
