"""
genetic_algorithm.py — Genetic Algorithm metaheuristic for the Cloud Scheduling problem.

PURPOSE
-------
Implements a standard generational Genetic Algorithm (GA) for the cloud resource
allocation problem.  GA is a population-based metaheuristic: instead of moving
a single solution around the search space like Simulated Annealing does, it
maintains a *population* of P candidate solutions and evolves them over multiple
generations using selection, crossover, and mutation operators.

THE ALGORITHM (high level)
--------------------------
1.  Initialise a population of P solutions.
    One solution is built with the greedy FFD heuristic (an informed head start);
    the remaining P-1 solutions are generated randomly to ensure population diversity.
2.  Evaluate every individual in the initial population.
3.  Repeat for n_generations generations:
    a.  Elitism: copy the elitism_count best individuals unchanged into the next
        generation.  This guarantees the best-ever cost never degrades between
        generations.
    b.  Fill remaining slots in the new generation by:
        - Selecting two parents via tournament selection.
        - Applying uniform crossover to produce two offspring.
        - Applying per-gene mutation to each offspring.
        - Evaluating each offspring with the objective function.
    c.  Replace the current population with the new generation.
    d.  Update the global best (the best solution ever seen across all generations).
4.  Return the best assignment, its full evaluation, and diagnostic statistics.

ENCODING
--------
A solution is represented as an integer vector A = (a_1, ..., a_n) where
a_i ∈ {0, ..., m-1} gives the index of the server task i is assigned to.
This is the identical encoding used by SA, so the objective function and all
supporting tools (evaluate_schedule, is_valid_assignment, etc.) work unchanged.

SELECTION
---------
Tournament selection is used because:
  - It is scale-invariant: it works directly with raw objective values
    (lower = better) without any fitness-scaling transformations.
  - It offers controllable selection pressure via tournament_size:
    a larger tournament favours the best individuals more strongly.
  - It is O(tournament_size) per selection, making it computationally cheap.
  - It handles minimisation naturally, unlike fitness-proportionate selection.

CROSSOVER
---------
Uniform crossover: for each task position i, the server assignment is
independently inherited from one of the two parents with equal probability.
This maximises the mixing of genetic material and is appropriate for the
integer vector encoding where there is no meaningful spatial ordering along
the task axis.

MUTATION
--------
Per-gene mutation: each task's server assignment is independently replaced with
a uniformly random server with probability mutation_prob.  With the default
mutation_prob = 1/n_tasks, on average one task is reassigned per offspring,
producing a small perturbation that maintains diversity without disrupting good
partial assignments.

COMPUTATIONAL BUDGET
--------------------
With default parameters (population_size=50, n_generations=3000), the total
number of evaluate_schedule() calls is approximately:
    population_size + n_generations × (population_size - elitism_count)
    = 50 + 3000 × 48 = 144,050
This is intentionally calibrated to match SA's budget of approximately:
    max_temp_steps × iterations_per_temperature = 3000 × 50 = 150,000
evaluations, enabling a fair algorithm comparison.

STATISTICS
----------
GAStatistics records per-generation histories using the same best_cost_history
interface as SAStatistics, so the same plot_convergence() function in plot.py
works for both algorithms without any modification.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from tools.data_loader import SchedulingProblemData
from tools.objective import evaluate_schedule, ObjectiveWeights, ScheduleEvaluation
from tools.initial_solution import build_greedy_assignment, build_random_assignment


# ---------------------------------------------------------------------------
# Diagnostic statistics container
# ---------------------------------------------------------------------------

@dataclass
class GAStatistics:
    """
    Diagnostic data collected during one GA run.

    best_cost_history and mean_cost_history each hold one entry per completed
    generation.  best_cost_history is the field accessed by plot.py to draw
    convergence curves — it must be present and use exactly this name.

    mean_cost_history tracks the average population fitness, which shows
    whether the population is converging or maintaining healthy diversity:
    a gap between best_cost and mean_cost indicates ongoing exploration.
    """

    # Per-generation histories (length == n_generations_completed)
    best_cost_history: list[float] = field(default_factory=list)
    mean_cost_history: list[float] = field(default_factory=list)

    # Aggregate counters for the whole run
    total_evaluations: int       = 0
    n_generations_completed: int = 0


# ---------------------------------------------------------------------------
# Genetic operators
# ---------------------------------------------------------------------------

def _tournament_select(
    population: list[list[int]],
    fitness: list[float],
    tournament_size: int,
) -> list[int]:
    """
    Tournament selection: randomly draw tournament_size candidates and return
    a copy of the one with the lowest (best) objective value.

    Scale-invariant and works directly with minimisation objectives.
    tournament_size=3 is a standard setting providing moderate selection
    pressure — strong enough to favour good individuals but weak enough to
    avoid premature convergence on small populations.
    """
    candidates   = random.sample(range(len(population)), tournament_size)
    winner_index = min(candidates, key=lambda i: fitness[i])
    return population[winner_index][:]


def _uniform_crossover(
    parent1: list[int],
    parent2: list[int],
) -> tuple[list[int], list[int]]:
    """
    Uniform crossover: for each task i, randomly and independently swap the
    server assignments between the two children with probability 0.5.

    Both children are initialised as copies of parent1 and parent2 respectively,
    then random positions are swapped.  Over many crossover events this produces
    offspring that are roughly 50% from each parent, maximising recombination.

    Returns two new children (does not modify the parent lists).
    """
    child1 = parent1[:]
    child2 = parent2[:]
    for i in range(len(child1)):
        # Independently swap each gene with 50% probability
        if random.random() < 0.5:
            child1[i], child2[i] = child2[i], child1[i]
    return child1, child2


def _mutate(
    solution: list[int],
    n_servers: int,
    mutation_prob: float,
) -> list[int]:
    """
    Per-gene mutation: each task's server is independently replaced with a
    uniformly random server index with probability mutation_prob.

    The replacement is drawn uniformly from [0, n_servers), so it can return
    the current server (a no-op for that gene).  This keeps the operator
    unbiased and avoids inadvertently penalising good assignments.

    Returns a new list (does not modify the input).
    """
    mutant = solution[:]
    for i in range(len(mutant)):
        if random.random() < mutation_prob:
            mutant[i] = random.randrange(n_servers)
    return mutant


# ---------------------------------------------------------------------------
# Main GA function
# ---------------------------------------------------------------------------

def genetic_algorithm(
    data: SchedulingProblemData,
    weights: ObjectiveWeights,
    population_size: int = 50,
    n_generations: int = 3000,
    tournament_size: int = 3,
    crossover_prob: float = 0.8,
    mutation_prob: float | None = None,
    elitism_count: int = 2,
) -> tuple[list[int], ScheduleEvaluation, GAStatistics]:
    """
    Run a Genetic Algorithm for cloud resource allocation scheduling.

    Parameters
    ----------
    population_size:
        Number of candidate solutions maintained each generation.
        Larger populations explore more broadly but cost more per generation.
        50 is a well-established default for problems of this size.
    n_generations:
        Number of evolutionary generations.  With population_size=50 and
        elitism_count=2, this gives ~144,050 total evaluations, matching SA.
    tournament_size:
        Number of candidates drawn per tournament selection event.
        3 gives moderate selection pressure (standard default).
    crossover_prob:
        Probability that two parents exchange genetic material.
        When set to 0.0, children are direct copies of parents (no crossover).
    mutation_prob:
        Per-gene mutation probability.  Defaults to 1/n_tasks so that on
        average one task is reassigned per offspring — a minimal perturbation.
    elitism_count:
        Number of best solutions carried unchanged to the next generation.
        Guarantees the best-ever cost is non-increasing across generations.

    Returns
    -------
    best_assignment:  list[int] of length n_tasks mapping each task to a server.
    best_eval:        ScheduleEvaluation with the full cost breakdown.
    stats:            GAStatistics with per-generation histories and counters.
    """
    stats = GAStatistics()

    # Default: 1 expected mutation per offspring (standard rule-of-thumb)
    if mutation_prob is None:
        mutation_prob = 1.0 / data.n_tasks

    # ------------------------------------------------------------------ #
    # Initialise population                                                #
    # One greedy-FFD solution gives the population a strong head start.   #
    # The rest are random to ensure initial diversity.                     #
    # ------------------------------------------------------------------ #
    population: list[list[int]] = [build_greedy_assignment(data)]
    for _ in range(population_size - 1):
        population.append(build_random_assignment(data))

    # ------------------------------------------------------------------ #
    # Evaluate initial population                                          #
    # ------------------------------------------------------------------ #
    fitness: list[float] = [
        evaluate_schedule(ind, data, weights).objective_value
        for ind in population
    ]
    stats.total_evaluations += population_size

    # Identify the best individual in the initial population
    best_idx      = min(range(population_size), key=lambda i: fitness[i])
    best_solution = population[best_idx][:]
    best_eval     = evaluate_schedule(best_solution, data, weights)
    best_cost     = best_eval.objective_value

    # ------------------------------------------------------------------ #
    # Main generational loop                                               #
    # ------------------------------------------------------------------ #
    for _ in range(n_generations):

        # Sort current population by fitness (ascending = lower cost = better)
        ranked_indices = sorted(range(population_size), key=lambda i: fitness[i])

        # Elitism: carry the best elitism_count individuals forward unchanged.
        # Their fitness values are already known so no re-evaluation is needed.
        new_population: list[list[int]] = [
            population[ranked_indices[k]][:] for k in range(elitism_count)
        ]
        new_fitness: list[float] = [
            fitness[ranked_indices[k]] for k in range(elitism_count)
        ]

        # Breed offspring until the new generation is full
        while len(new_population) < population_size:
            # --- Selection ---
            p1 = _tournament_select(population, fitness, tournament_size)
            p2 = _tournament_select(population, fitness, tournament_size)

            # --- Crossover ---
            if random.random() < crossover_prob:
                child1, child2 = _uniform_crossover(p1, p2)
            else:
                # No crossover: children are direct copies of their parents
                child1, child2 = p1[:], p2[:]

            # --- Mutation ---
            child1 = _mutate(child1, data.n_servers, mutation_prob)
            child2 = _mutate(child2, data.n_servers, mutation_prob)

            # --- Evaluate and add each child ---
            for child in (child1, child2):
                if len(new_population) >= population_size:
                    # Population is full; discard any surplus child
                    break

                ev = evaluate_schedule(child, data, weights)
                new_population.append(child)
                new_fitness.append(ev.objective_value)
                stats.total_evaluations += 1

                # Update global best if this child is the best seen so far
                if ev.objective_value < best_cost:
                    best_solution = child[:]
                    best_eval     = ev
                    best_cost     = ev.objective_value

        # Replace old generation
        population = new_population
        fitness    = new_fitness

        # Record per-generation statistics
        stats.best_cost_history.append(best_cost)
        stats.mean_cost_history.append(sum(fitness) / len(fitness))
        stats.n_generations_completed += 1

    return best_solution, best_eval, stats
