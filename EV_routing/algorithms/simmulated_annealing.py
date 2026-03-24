from __future__ import annotations

import math
import random

from tools.objective import evaluate_route, ObjectiveWeights, RouteEvaluation
from tools.neighborhoods import generate_neighbor
from tools.initial_solution import build_nearest_neighbor_solution
from tools.feasibility import is_valid_basic_route
from tools.data_loader import ProblemData
from tools.energy import EVParameters


def simulated_annealing(
    data: ProblemData,
    ev_params: EVParameters,
    weights: ObjectiveWeights,
    initial_temperature: float = 1000.0,
    cooling_rate: float = 0.995,
    min_temperature: float = 1e-3,
    max_iterations: int = 10000,
) -> tuple[list[str], RouteEvaluation]:
    current_solution = build_nearest_neighbor_solution(data)
    current_eval = evaluate_route(current_solution, data, ev_params, weights)
    current_cost = current_eval.objective_value

    best_solution = current_solution[:]
    best_eval = current_eval
    best_cost = current_cost

    temperature = initial_temperature

    for _ in range(max_iterations):
        if temperature < min_temperature:
            break

        candidate_solution = generate_neighbor(current_solution)

        # Fast structural validity check
        if not is_valid_basic_route(candidate_solution, data):
            temperature *= cooling_rate
            continue

        candidate_eval = evaluate_route(candidate_solution, data, ev_params, weights)
        candidate_cost = candidate_eval.objective_value
        delta = candidate_cost - current_cost

        if delta < 0:
            current_solution = candidate_solution
            current_eval = candidate_eval
            current_cost = candidate_cost
        else:
            acceptance_probability = math.exp(-delta / temperature)
            if random.random() < acceptance_probability:
                current_solution = candidate_solution
                current_eval = candidate_eval
                current_cost = candidate_cost

        if current_cost < best_cost:
            best_solution = current_solution[:]
            best_eval = current_eval
            best_cost = current_cost

        temperature *= cooling_rate

    return best_solution, best_eval