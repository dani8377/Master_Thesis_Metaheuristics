"""
Nearest-neighbor greedy baseline for the EV routing problem.

Deterministic constructive heuristic: greedy nearest-neighbor customer ordering
with proactive charging-station insertion. Produces the same route regardless
of the random seed — serves as the reference lower bound for how much the
metaheuristics improve upon the simplest possible approach.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tools.data_loader import ProblemData
from tools.battery import EVParameters
from tools.objective import ObjectiveWeights, RouteEvaluation, evaluate_route
from tools.initial_solution import build_ev_feasible_solution, repair_ev_route


@dataclass
class GreedyStats:
    total_evaluated: int = 1
    feasibility_rate: float = 1.0


def greedy_nearest_neighbor(
    data: ProblemData,
    ev_params: EVParameters,
    weights: ObjectiveWeights,
    max_evaluations: int = 1,
    **kwargs: Any,
) -> tuple[list[str], RouteEvaluation, GreedyStats]:
    """
    Nearest-neighbor greedy heuristic — EV-feasible.

    Visits the nearest unvisited customer at each step, inserting charging
    stops proactively when battery falls below 50 % capacity. Deterministic:
    the seed parameter has no effect.
    """
    route = build_ev_feasible_solution(data, ev_params)
    route = repair_ev_route(route, data, ev_params)
    ev = evaluate_route(route, data, ev_params, weights)
    feasibility = 1.0 if ev.feasible else 0.0
    return route, ev, GreedyStats(total_evaluated=1, feasibility_rate=feasibility)
