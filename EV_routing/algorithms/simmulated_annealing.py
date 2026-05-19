from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field

from tools.objective import evaluate_route, ObjectiveWeights, RouteEvaluation
from tools.neighborhoods import generate_neighbor
from tools.feasibility import is_valid_basic_route
from tools.initial_solution import build_ev_feasible_solution
from tools.data_loader import ProblemData
from tools.battery import EVParameters


@dataclass
class SAStatistics:
    """Diagnostic statistics collected during a simulated annealing run."""

    best_cost_history: list[float] = field(default_factory=list)
    current_cost_history: list[float] = field(default_factory=list)
    temperature_history: list[float] = field(default_factory=list)
    # Cumulative evaluations at each temperature step — enables x-axis normalisation
    # by evaluations when comparing against population-based algorithms.
    evals_at_step: list[int] = field(default_factory=list)

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
    initial_temperature: float = 400.0,
    cooling_rate: float = 0.995,
    min_temperature: float = 1e-3,
    iterations_per_temperature: int = 50,
    reheat_patience: int = 200,
    reheat_factor: float = 0.4,
    max_evaluations: int | None = None,
    time_limit_s: float | None = None,
) -> tuple[list[str], RouteEvaluation, SAStatistics]:
    """
    Simulated annealing for EV routing.

    Parameters
    ----------
    initial_temperature:
        Starting temperature.
    cooling_rate:
        Multiplicative cooling factor applied after each temperature step.
    min_temperature:
        Temperature floor — the schedule never drops below this value, but the
        search continues until the evaluation budget is exhausted.  This is
        intentionally NOT a stopping criterion; ``max_evaluations`` is.
    iterations_per_temperature:
        Number of neighbour attempts at each temperature level (Markov chain).
    reheat_patience:
        Temperature steps without global improvement before reheating.
        At 50 iters/step, patience=200 means ~10,000 evaluations of stagnation.
    reheat_factor:
        After a reheat, T = reheat_factor × initial_temperature.
    max_evaluations:
        Hard stopping criterion — primary budget control shared with all algorithms.
    time_limit_s:
        Optional wall-clock limit.

    Returns
    -------
    (best_solution, best_evaluation, statistics)
    """
    stats = SAStatistics()
    t_start = time.perf_counter()

    def _over_budget() -> bool:
        if max_evaluations is not None and stats.total_evaluated >= max_evaluations:
            return True
        if time_limit_s is not None and time.perf_counter() - t_start >= time_limit_s:
            return True
        return False

    current_solution = build_ev_feasible_solution(data, ev_params)
    current_eval = evaluate_route(current_solution, data, ev_params, weights)
    current_cost = current_eval.objective_value

    best_solution = current_solution[:]
    best_eval = current_eval
    best_cost = current_cost

    temperature = initial_temperature
    steps_without_improvement = 0

    # Primary stop: evaluation budget.  Temperature schedule is a floor,
    # not a stopping criterion — SA continues (and reheats) until budget runs out.
    while not _over_budget():
        step_improved = False

        for _ in range(iterations_per_temperature):
            if _over_budget():
                break

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

        # Floor temperature at min_temperature — don't stop because of it
        temperature = max(temperature * cooling_rate, min_temperature)
        stats.best_cost_history.append(best_cost)
        stats.current_cost_history.append(current_cost)
        stats.temperature_history.append(temperature)
        stats.evals_at_step.append(stats.total_evaluated)

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
