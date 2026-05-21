from __future__ import annotations

import random
import statistics
import time
from dataclasses import dataclass, field

from tools.objective import evaluate_route, ObjectiveWeights, RouteEvaluation
from tools.initial_solution import build_ev_feasible_solution
from tools.feasibility import is_valid_basic_route, is_energy_feasible
from tools.neighborhoods import generate_neighbor, repair_battery_violation
from tools.data_loader import ProblemData
from tools.battery import EVParameters


@dataclass
class GAStatistics:
    """Diagnostic statistics collected during a genetic algorithm run."""

    best_cost_history: list[float] = field(default_factory=list)
    mean_cost_history: list[float] = field(default_factory=list)
    # Population diversity measured as coefficient of variation of costs (std/mean).
    # High CV = spread-out population (exploration); low CV = converged (exploitation).
    diversity_history: list[float] = field(default_factory=list)
    feasibility_history: list[float] = field(default_factory=list)
    evals_at_step: list[int] = field(default_factory=list)

    total_evaluated: int = 0
    total_generations: int = 0

    @property
    def feasibility_rate(self) -> float:
        if not self.feasibility_history:
            return 0.0
        return self.feasibility_history[-1]


# ---------------------------------------------------------------------------
# Crossover
# ---------------------------------------------------------------------------

def _ox_crossover(seq1: list[str], seq2: list[str]) -> list[str]:
    """
    Order Crossover (OX) for two customer-only permutations.

    Copies a random contiguous segment from seq1 into the child, then fills
    the remaining slots with seq2's elements in their original relative order.
    Preserves every customer exactly once.
    """
    n = len(seq1)
    if n == 0:
        return seq1[:]
    i, j = sorted(random.sample(range(n), 2))
    child: list[str | None] = [None] * n
    child[i : j + 1] = seq1[i : j + 1]
    segment = set(child[i : j + 1])  # type: ignore[arg-type]
    fill = [x for x in seq2 if x not in segment]
    fill_idx = 0
    for k in range(n):
        if child[k] is None:
            child[k] = fill[fill_idx]
            fill_idx += 1
    return child  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# CS repair after crossover
# ---------------------------------------------------------------------------

def _insert_cs_greedy(
    customer_seq: list[str],
    data: ProblemData,
    ev_params: EVParameters,
) -> list[str]:
    """
    Wrap a customer-only sequence in DEPOT bookends, then iteratively insert
    charging stations at the first energy-infeasible arc until the route is
    energy-feasible or no further improvement is possible.
    """
    route = ["DEPOT"] + customer_seq + ["DEPOT"]
    capacity = ev_params.battery_capacity_kwh
    # Upper bound on insertions: can never need more CS than there are arcs
    limit = len(customer_seq) + len(data.stations)
    for _ in range(limit):
        if is_energy_feasible(route, data, capacity):
            break
        route = repair_battery_violation(route, data, ev_params)
    return route


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------

def _tournament_select(
    population: list[list[str]],
    costs: list[float],
    k: int,
) -> list[str]:
    """Return a copy of the best individual among k randomly sampled candidates."""
    indices = random.sample(range(len(population)), min(k, len(population)))
    return population[min(indices, key=lambda i: costs[i])][:]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _customer_sequence(route: list[str], customer_ids: set[str]) -> list[str]:
    return [n for n in route if n in customer_ids]


def _random_initial_route(
    customer_node_ids: list[str],
    data: ProblemData,
    ev_params: EVParameters,
) -> list[str]:
    """Random customer permutation repaired to be EV-feasible."""
    perm = customer_node_ids[:]
    random.shuffle(perm)
    return _insert_cs_greedy(perm, data, ev_params)


# ---------------------------------------------------------------------------
# Main algorithm
# ---------------------------------------------------------------------------

def genetic_algorithm(
    data: ProblemData,
    ev_params: EVParameters,
    weights: ObjectiveWeights,
    population_size: int = 80,
    crossover_rate: float = 0.85,
    mutation_rate: float = 0.20,
    tournament_size: int = 3,
    elitism_count: int = 2,
    max_evaluations: int = 150_000,
    time_limit_s: float | None = None,
    local_search_iters: int = 0,
) -> tuple[list[str], RouteEvaluation, GAStatistics]:
    """
    Generational GA for EV routing — also serves as the Memetic Algorithm (MA)
    when ``local_search_iters > 0``.

    Representation
    --------------
    Routes are variable-length lists (same as SA): DEPOT → customers+stations → DEPOT.
    Charging stations may appear multiple times.

    Crossover (OX + CS repair)
    --------------------------
    1. Extract the customer-only subsequence from each parent.
    2. Apply Order Crossover to produce a child customer permutation.
    3. Greedily re-insert charging stations wherever energy would run out.

    Mutation
    --------
    With probability ``mutation_rate``, apply one random neighborhood move
    (reuses the same operators as SA: swap, relocate, 2-opt, CS insert/remove/move).

    Local search / Memetic phase (MA only)
    ---------------------------------------
    When ``local_search_iters > 0``, each offspring undergoes up to
    ``local_search_iters`` attempts at a first-improvement move before joining
    the population.  Evaluations consumed here count against ``max_evaluations``,
    keeping the budget comparison honest.  This makes the GA problem-aware at
    the individual level — the same domain operators SA uses are now applied
    locally to every offspring.

    Selection
    ---------
    Tournament selection of size ``tournament_size``.

    Elitism
    -------
    The top ``elitism_count`` individuals survive each generation unchanged.

    Stopping
    --------
    Whichever of ``max_evaluations`` or ``time_limit_s`` is reached first.
    """
    stats = GAStatistics()
    customer_ids = set(data.customers["Node ID"].tolist())
    customer_node_ids = data.customers["Node ID"].tolist()
    t_start = time.perf_counter()

    def _over_budget() -> bool:
        if stats.total_evaluated >= max_evaluations:
            return True
        if time_limit_s is not None and time.perf_counter() - t_start >= time_limit_s:
            return True
        return False

    # ------------------------------------------------------------------
    # Initialise population: first individual is the greedy EV-feasible
    # solution; the rest are random permutations repaired for feasibility.
    # ------------------------------------------------------------------
    population: list[list[str]] = [build_ev_feasible_solution(data, ev_params)]
    for _ in range(population_size - 1):
        population.append(_random_initial_route(customer_node_ids, data, ev_params))

    all_evals = [evaluate_route(ind, data, ev_params, weights) for ind in population]
    costs = [e.objective_value for e in all_evals]
    stats.total_evaluated += len(population)

    best_idx = min(range(len(costs)), key=lambda i: costs[i])
    best_solution = population[best_idx][:]
    best_eval = all_evals[best_idx]
    best_cost = costs[best_idx]

    # ------------------------------------------------------------------
    # Generational loop
    # ------------------------------------------------------------------
    while not _over_budget():
        stats.total_generations += 1

        sorted_idx = sorted(range(len(population)), key=lambda i: costs[i])
        new_population: list[list[str]] = [population[i][:] for i in sorted_idx[:elitism_count]]
        new_evals: list[RouteEvaluation] = [all_evals[i] for i in sorted_idx[:elitism_count]]

        while len(new_population) < population_size and not _over_budget():
            parent1 = _tournament_select(population, costs, tournament_size)
            parent2 = _tournament_select(population, costs, tournament_size)

            # Crossover
            if random.random() < crossover_rate:
                child = _insert_cs_greedy(
                    _ox_crossover(
                        _customer_sequence(parent1, customer_ids),
                        _customer_sequence(parent2, customer_ids),
                    ),
                    data,
                    ev_params,
                )
            else:
                child = parent1[:]

            # Mutation
            if random.random() < mutation_rate:
                candidate = generate_neighbor(child, data, ev_params)
                if is_valid_basic_route(candidate, data):
                    child = candidate

            child_eval = evaluate_route(child, data, ev_params, weights)
            stats.total_evaluated += 1

            # Local search phase (Memetic Algorithm when local_search_iters > 0)
            if local_search_iters > 0:
                child_cost = child_eval.objective_value
                for _ in range(local_search_iters):
                    if _over_budget():
                        break
                    ls_cand = generate_neighbor(child, data, ev_params)
                    if not is_valid_basic_route(ls_cand, data):
                        continue
                    ls_eval = evaluate_route(ls_cand, data, ev_params, weights)
                    stats.total_evaluated += 1
                    if ls_eval.objective_value < child_cost:
                        child = ls_cand
                        child_eval = ls_eval
                        child_cost = ls_eval.objective_value

            if child_eval.objective_value < best_cost:
                best_solution = child[:]
                best_eval = child_eval
                best_cost = child_eval.objective_value

            new_population.append(child)
            new_evals.append(child_eval)

        population = new_population
        all_evals = new_evals
        costs = [e.objective_value for e in all_evals]

        # ------------------------------------------------------------------
        # Per-generation statistics
        # ------------------------------------------------------------------
        mean_cost = statistics.mean(costs)
        std_cost = statistics.stdev(costs) if len(costs) >= 2 else 0.0
        cv = std_cost / mean_cost if mean_cost > 0 else 0.0
        feasible_frac = sum(1 for e in all_evals if e.feasible) / len(all_evals)

        stats.best_cost_history.append(best_cost)
        stats.mean_cost_history.append(mean_cost)
        stats.diversity_history.append(cv)
        stats.feasibility_history.append(feasible_frac)
        stats.evals_at_step.append(stats.total_evaluated)

    return best_solution, best_eval, stats
