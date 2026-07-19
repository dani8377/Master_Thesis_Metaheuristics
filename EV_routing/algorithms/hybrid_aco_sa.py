"""
Budget-adaptive ACO→SA hybrid.

Motivated by the budget-dependent reversal observed in the benchmarking
study: ACO's battery-aware construction reaches good routes within the
first few thousand evaluations, while SA needs a long cooling schedule but
ultimately descends further.  The hybrid spends the first fraction of the
evaluation budget on ACO construction, then hands ACO's best route to SA
as a warm start for the remainder of the budget.

Both stages use the tuned hyperparameters of their parent algorithms; the
only new parameter is ``aco_frac``, the share of the budget given to the
construction stage.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from tools.data_loader import ProblemData
from tools.battery import EVParameters
from tools.objective import ObjectiveWeights, RouteEvaluation
from algorithms.ant_colony import ant_colony_optimization
from algorithms.simulated_annealing import simulated_annealing


@dataclass
class HybridStatistics:
    total_evaluated: int = 0
    aco_evaluations: int = 0
    sa_evaluations: int = 0
    aco_best_cost: float = float("inf")
    aco_stats: Any = field(default=None, repr=False)
    sa_stats: Any = field(default=None, repr=False)


def hybrid_aco_sa(
    data: ProblemData,
    ev_params: EVParameters,
    weights: ObjectiveWeights,
    aco_frac: float = 0.2,
    aco_kwargs: dict | None = None,
    sa_kwargs: dict | None = None,
    max_evaluations: int = 150_000,
    **_ignored,
) -> tuple[list[str], RouteEvaluation, HybridStatistics]:
    """
    Run ACO for ``aco_frac`` of the budget, then SA (warm-started from
    ACO's best route) for the remainder.  Returns whichever of the two
    stage-best solutions is better (SA can only improve on its warm start,
    so in practice this is SA's result).
    """
    aco_kwargs = dict(aco_kwargs or {})
    sa_kwargs = dict(sa_kwargs or {})
    stats = HybridStatistics()

    aco_budget = max(1, int(max_evaluations * aco_frac))
    sa_budget = max_evaluations - aco_budget

    aco_route, aco_eval, aco_stats = ant_colony_optimization(
        data, ev_params, weights,
        max_evaluations=aco_budget, **aco_kwargs,
    )
    stats.aco_evaluations = getattr(aco_stats, "total_evaluated", aco_budget)
    stats.aco_best_cost = aco_eval.objective_value
    stats.aco_stats = aco_stats

    sa_route, sa_eval, sa_stats = simulated_annealing(
        data, ev_params, weights,
        max_evaluations=sa_budget,
        initial_solution=aco_route,
        **sa_kwargs,
    )
    stats.sa_evaluations = getattr(sa_stats, "total_evaluated", sa_budget)
    stats.sa_stats = sa_stats
    stats.total_evaluated = stats.aco_evaluations + stats.sa_evaluations

    if sa_eval.objective_value <= aco_eval.objective_value:
        return sa_route, sa_eval, stats
    return aco_route, aco_eval, stats
