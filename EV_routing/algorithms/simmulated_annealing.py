from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from tools.objective import evaluate_route, ObjectiveWeights, RouteEvaluation
from tools.neighborhoods import generate_neighbor
from tools.initial_solution import build_ev_feasible_solution
from tools.feasibility import is_valid_basic_route
from tools.data_loader import ProblemData
from tools.energy import EVParameters


@dataclass
class SAStatistics:
    """Diagnostic statistics collected during a simulated annealing run."""

    best_cost_history: list[float] = field(default_factory=list)
    current_cost_history: list[float] = field(default_factory=list)
    temperature_history: list[float] = field(default_factory=list)

    total_evaluated: int = 0
    total_improving_accepted: int = 0
    total_worsening_accepted: int = 0
    total_rejected_structural: int = 0
    total_feasible_evaluated: int = 0

    reheat_count: int = 0
    final_temperature: float = 0.0

    @property
    def acceptance_rate(self) -> float:
        if self.total_evaluated == 0:
            return 0.0
        return (self.total_improving_accepted + self.total_worsening_accepted) / self.total_evaluated

    @property
    def feasibility_rate(self) -> float:
        if self.total_evaluated == 0:
            return 0.0
        return self.total_feasible_evaluated / self.total_evaluated


def simulated_annealing(
    data: ProblemData,
    ev_params: EVParameters,
    weights: ObjectiveWeights,
    initial_temperature: float = 1000.0,
    cooling_rate: float = 0.995,
    min_temperature: float = 1e-3,
    iterations_per_temperature: int = 50,
    max_temp_steps: int = 2000,
    reheat_patience: int = 150,
    reheat_factor: float = 0.3,
) -> tuple[list[str], RouteEvaluation, SAStatistics]:
    """
    Simulated annealing for EV routing.

    Parameters
    ----------
    iterations_per_temperature:
        Number of neighbor attempts at each temperature level before cooling.
    max_temp_steps:
        Maximum number of temperature reductions (hard stopping criterion).
    reheat_patience:
        Temperature steps without improvement before reheating.
    reheat_factor:
        Temperature after reheat = reheat_factor * initial_temperature.

    Returns
    -------
    (best_solution, best_evaluation, statistics)
    """
    stats = SAStatistics()

    current_solution = build_ev_feasible_solution(data, ev_params)
    current_eval = evaluate_route(current_solution, data, ev_params, weights)
    current_cost = current_eval.objective_value

    best_solution = current_solution[:]
    best_eval = current_eval
    best_cost = current_cost

    temperature = initial_temperature
    steps_without_improvement = 0

    for _ in range(max_temp_steps):
        if temperature < min_temperature:
            break

        step_improved = False

        for _ in range(iterations_per_temperature):
            candidate = generate_neighbor(current_solution, data, ev_params)

            if not is_valid_basic_route(candidate, data):
                stats.total_rejected_structural += 1
                continue

            candidate_eval = evaluate_route(candidate, data, ev_params, weights)
            candidate_cost = candidate_eval.objective_value
            stats.total_evaluated += 1
            if candidate_eval.feasible:
                stats.total_feasible_evaluated += 1

            delta = candidate_cost - current_cost

            if delta < 0:
                current_solution = candidate
                current_eval = candidate_eval
                current_cost = candidate_cost
                stats.total_improving_accepted += 1
            elif random.random() < math.exp(-delta / temperature):
                current_solution = candidate
                current_eval = candidate_eval
                current_cost = candidate_cost
                stats.total_worsening_accepted += 1

            if current_cost < best_cost:
                best_solution = current_solution[:]
                best_eval = current_eval
                best_cost = current_cost
                step_improved = True

        temperature *= cooling_rate
        stats.best_cost_history.append(best_cost)
        stats.current_cost_history.append(current_cost)
        stats.temperature_history.append(temperature)

        if step_improved:
            steps_without_improvement = 0
        else:
            steps_without_improvement += 1

        if steps_without_improvement >= reheat_patience:
            temperature = reheat_factor * initial_temperature
            steps_without_improvement = 0
            stats.reheat_count += 1

    stats.final_temperature = temperature
    return best_solution, best_eval, stats
