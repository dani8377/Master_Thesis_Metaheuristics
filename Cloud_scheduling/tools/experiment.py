"""
experiment.py — Multi-seed experiment harness for the Cloud Scheduling problem.

PURPOSE
-------
Runs any compatible scheduling algorithm multiple times (one run per random
seed) and collects the results into a single ExperimentResults object.

WHY MULTIPLE SEEDS?
-------------------
SA is stochastic — it uses random.random() and random.choice() throughout.
A single run's result is therefore noise-sensitive: it might be unusually
good or bad by luck.  Running with 10 independent seeds and reporting the
mean, standard deviation, best, and worst gives a statistically meaningful
picture of the algorithm's actual performance.

GENERIC DESIGN
--------------
The AlgorithmFn type alias is intentionally loose.  Any callable with the
signature:
    algorithm(data, weights, **kwargs) -> (assignment, ScheduleEvaluation, stats)
can be passed to run_experiments() without modification.  This makes it
trivial to compare multiple algorithms (SA, random restart, greedy, etc.)
using the same harness and the same seeds.

RELATIONSHIP TO EV ROUTING
---------------------------
Mirrors EV_routing/tools/experiment.py exactly in structure, with the
EV-specific types (ProblemData, EVParameters, RouteEvaluation) replaced by
their cloud scheduling equivalents (SchedulingProblemData, ObjectiveWeights,
ScheduleEvaluation).  The ev_params argument is dropped because cloud
scheduling has no physical vehicle model.
"""
from __future__ import annotations

import random
import statistics
import time
from dataclasses import dataclass
from typing import Any, Callable

from tools.data_loader import SchedulingProblemData
from tools.objective import ObjectiveWeights, ScheduleEvaluation


# Type alias: any algorithm must accept (data, weights, **kwargs) and return
# a 3-tuple of (assignment, evaluation, algorithm-specific stats).
AlgorithmFn = Callable[..., tuple[list[int], ScheduleEvaluation, Any]]


# ---------------------------------------------------------------------------
# Results container
# ---------------------------------------------------------------------------

@dataclass
class ExperimentResults:
    """
    Aggregated results from running one algorithm over multiple seeds.

    Stores per-run lists (costs, solutions, evaluations, stats, runtimes)
    and exposes computed properties for common summary statistics.
    """

    algorithm_name: str
    best_costs: list[float]             # best objective value reached per run
    best_solutions: list[list[int]]     # best assignment vector per run
    best_evals: list[ScheduleEvaluation]# full evaluation of the best per run
    all_stats: list[Any]                # SAStatistics (or equivalent) per run
    runtimes: list[float]               # wall-clock seconds per run
    seeds: list[int]                    # random seeds used (one per run)

    # ---- Cost summary across runs ---- #

    @property
    def best_cost(self) -> float:
        """Best objective value across all runs."""
        return min(self.best_costs)

    @property
    def average_cost(self) -> float:
        """Mean best objective value across all runs."""
        return statistics.mean(self.best_costs)

    @property
    def worst_cost(self) -> float:
        """Worst best objective value across all runs."""
        return max(self.best_costs)

    @property
    def std_cost(self) -> float:
        """Standard deviation of best objective values across runs."""
        return statistics.stdev(self.best_costs) if len(self.best_costs) >= 2 else 0.0

    # ---- Best run ---- #

    @property
    def best_run_index(self) -> int:
        """Index of the run that produced the lowest objective value."""
        return self.best_costs.index(self.best_cost)

    @property
    def best_solution(self) -> list[int]:
        """Assignment vector from the best run."""
        return self.best_solutions[self.best_run_index]

    @property
    def best_eval(self) -> ScheduleEvaluation:
        """Full evaluation from the best run."""
        return self.best_evals[self.best_run_index]

    @property
    def best_seed(self) -> int:
        """Random seed that produced the best run."""
        return self.seeds[self.best_run_index]

    # ---- Feasibility ---- #

    @property
    def feasible_run_count(self) -> int:
        """Number of runs whose best solution was fully feasible (zero penalty)."""
        return sum(1 for e in self.best_evals if e.feasible)

    # ---- Runtime ---- #

    @property
    def average_runtime(self) -> float:
        """Mean wall-clock time per run in seconds."""
        return statistics.mean(self.runtimes)

    @property
    def total_runtime(self) -> float:
        """Total wall-clock time across all runs in seconds."""
        return sum(self.runtimes)


# ---------------------------------------------------------------------------
# Harness
# ---------------------------------------------------------------------------

def run_experiments(
    algorithm: AlgorithmFn,
    data: SchedulingProblemData,
    weights: ObjectiveWeights,
    seeds: list[int],
    algorithm_name: str = "Algorithm",
    show_progress: bool = True,
    **algorithm_kwargs,
) -> ExperimentResults:
    """
    Run *algorithm* once per seed and collect all results.

    Each run seeds Python's built-in random module before calling the
    algorithm, making runs fully reproducible and independent of each other.

    Parameters
    ----------
    algorithm:      Any AlgorithmFn-compatible callable.
    data:           The scheduling problem instance.
    weights:        Objective weights and penalty coefficients.
    seeds:          List of integer seeds — one run per seed.
    algorithm_name: Label used in plots and tables.
    show_progress:  If True, prints a one-line summary after each run.
                    Named show_progress (not verbose) so that a verbose=True
                    kwarg in algorithm_kwargs can pass through to the algorithm
                    without a naming collision.
    **algorithm_kwargs:
        Passed directly to the algorithm — including verbose=True/False for
        per-step progress inside SA / GA / UMDA.
    """
    best_costs: list[float]           = []
    best_solutions: list[list[int]]   = []
    best_evals: list[ScheduleEvaluation] = []
    all_stats: list[Any]              = []
    runtimes: list[float]             = []

    for idx, seed in enumerate(seeds):
        random.seed(seed)          # seed once per run for reproducibility
        t0 = time.perf_counter()

        solution, eval_result, stats = algorithm(
            data=data,
            weights=weights,
            **algorithm_kwargs,
        )

        runtime = time.perf_counter() - t0

        best_costs.append(eval_result.objective_value)
        best_solutions.append(solution)
        best_evals.append(eval_result)
        all_stats.append(stats)
        runtimes.append(runtime)

        if show_progress:
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
