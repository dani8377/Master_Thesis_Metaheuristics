from __future__ import annotations

import random
import statistics
import time
from dataclasses import dataclass
from typing import Any, Callable

from tools.data_loader import ProblemData
from tools.energy import EVParameters
from tools.objective import ObjectiveWeights, RouteEvaluation


# Any algorithm callable must match this signature:
#   algorithm(data, ev_params, weights, **kwargs) -> (solution, RouteEvaluation, stats)
AlgorithmFn = Callable[..., tuple[list[str], RouteEvaluation, Any]]


@dataclass
class ExperimentResults:
    """Aggregated results over multiple independent runs of any algorithm."""

    algorithm_name: str
    best_costs: list[float]
    best_solutions: list[list[str]]
    best_evals: list[RouteEvaluation]
    all_stats: list[Any]        # algorithm-specific stats objects
    runtimes: list[float]       # wall-clock seconds per run
    seeds: list[int]

    # ------------------------------------------------------------------
    # Cost aggregates
    # ------------------------------------------------------------------

    @property
    def best_cost(self) -> float:
        return min(self.best_costs)

    @property
    def average_cost(self) -> float:
        return statistics.mean(self.best_costs)

    @property
    def worst_cost(self) -> float:
        return max(self.best_costs)

    @property
    def std_cost(self) -> float:
        return statistics.stdev(self.best_costs) if len(self.best_costs) >= 2 else 0.0

    # ------------------------------------------------------------------
    # Best run
    # ------------------------------------------------------------------

    @property
    def best_run_index(self) -> int:
        return self.best_costs.index(self.best_cost)

    @property
    def best_solution(self) -> list[str]:
        return self.best_solutions[self.best_run_index]

    @property
    def best_eval(self) -> RouteEvaluation:
        return self.best_evals[self.best_run_index]

    @property
    def best_seed(self) -> int:
        return self.seeds[self.best_run_index]

    # ------------------------------------------------------------------
    # Feasibility
    # ------------------------------------------------------------------

    @property
    def feasible_run_count(self) -> int:
        return sum(1 for e in self.best_evals if e.feasible)

    # ------------------------------------------------------------------
    # Runtime
    # ------------------------------------------------------------------

    @property
    def average_runtime(self) -> float:
        return statistics.mean(self.runtimes)

    @property
    def total_runtime(self) -> float:
        return sum(self.runtimes)


def run_experiments(
    algorithm: AlgorithmFn,
    data: ProblemData,
    ev_params: EVParameters,
    weights: ObjectiveWeights,
    seeds: list[int],
    algorithm_name: str = "Algorithm",
    verbose: bool = True,
    **algorithm_kwargs,
) -> ExperimentResults:
    """
    Run any algorithm once per seed and collect results.

    The algorithm must be callable as:
        algorithm(data, ev_params, weights, **algorithm_kwargs)
            -> (solution: list[str], eval: RouteEvaluation, stats: Any)

    Each seed is applied to Python's built-in random module before each run,
    making all runs reproducible and independent.
    """
    best_costs: list[float] = []
    best_solutions: list[list[str]] = []
    best_evals: list[RouteEvaluation] = []
    all_stats: list[Any] = []
    runtimes: list[float] = []

    for idx, seed in enumerate(seeds):
        random.seed(seed)
        t0 = time.perf_counter()
        solution, eval_result, stats = algorithm(
            data=data,
            ev_params=ev_params,
            weights=weights,
            **algorithm_kwargs,
        )
        runtime = time.perf_counter() - t0

        best_costs.append(eval_result.objective_value)
        best_solutions.append(solution)
        best_evals.append(eval_result)
        all_stats.append(stats)
        runtimes.append(runtime)

        if verbose:
            feasible_tag = "feasible" if eval_result.feasible else "infeasible"
            print(
                f"  Run {idx + 1:>2}/{len(seeds)}  seed={seed}"
                f"  cost={eval_result.objective_value:.2f}"
                f"  time={runtime:.1f}s"
                f"  [{feasible_tag}]"
            )

    return ExperimentResults(
        algorithm_name=algorithm_name,
        best_costs=best_costs,
        best_solutions=best_solutions,
        best_evals=best_evals,
        all_stats=all_stats,
        runtimes=runtimes,
        seeds=seeds,
    )
