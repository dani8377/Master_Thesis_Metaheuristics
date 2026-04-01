from __future__ import annotations

import random
import statistics
from dataclasses import dataclass

from tools.data_loader import ProblemData
from tools.energy import EVParameters
from tools.objective import ObjectiveWeights, RouteEvaluation
from algorithms.simmulated_annealing import simulated_annealing, SAStatistics


@dataclass
class ExperimentResults:
    """Aggregated results over multiple SA runs with different random seeds."""

    best_costs: list[float]
    best_solutions: list[list[str]]
    best_evals: list[RouteEvaluation]
    all_stats: list[SAStatistics]
    seeds: list[int]

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

    @property
    def feasible_run_count(self) -> int:
        return sum(1 for e in self.best_evals if e.feasible)


def run_experiments(
    data: ProblemData,
    ev_params: EVParameters,
    weights: ObjectiveWeights,
    seeds: list[int],
    verbose: bool = True,
    **sa_kwargs,
) -> ExperimentResults:
    """
    Run simulated annealing once per seed and collect results.

    Each seed is applied to Python's built-in ``random`` module before the
    corresponding SA run, making runs reproducible and independent.

    Parameters
    ----------
    seeds:
        List of integer seeds, one per run.
    verbose:
        Print per-run progress if True.
    **sa_kwargs:
        Forwarded directly to ``simulated_annealing()``.
    """
    best_costs: list[float] = []
    best_solutions: list[list[str]] = []
    best_evals: list[RouteEvaluation] = []
    all_stats: list[SAStatistics] = []

    for idx, seed in enumerate(seeds):
        random.seed(seed)
        solution, eval_result, stats = simulated_annealing(
            data=data,
            ev_params=ev_params,
            weights=weights,
            **sa_kwargs,
        )
        best_costs.append(eval_result.objective_value)
        best_solutions.append(solution)
        best_evals.append(eval_result)
        all_stats.append(stats)

        if verbose:
            feasible_tag = "feasible" if eval_result.feasible else "infeasible"
            print(
                f"  Run {idx + 1:>2}/{len(seeds)}  seed={seed}"
                f"  cost={eval_result.objective_value:.2f}"
                f"  reheats={stats.reheat_count}"
                f"  [{feasible_tag}]"
            )

    return ExperimentResults(
        best_costs=best_costs,
        best_solutions=best_solutions,
        best_evals=best_evals,
        all_stats=all_stats,
        seeds=seeds,
    )
