"""
Genetic Algorithm (GA) for the cloud task scheduling problem.

Generational GA with tournament selection, uniform crossover, per-gene mutation,
and elitism.  Population is seeded with one greedy BFD (Best-Fit Decreasing)
solution plus P-1 random assignments.  Evaluation budget is calibrated to match
SA and UMDA (~150 000 calls).
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
    """Per-run diagnostics: convergence histories and evaluation counts."""

    best_cost_history: list[float] = field(default_factory=list)  # one per generation
    mean_cost_history: list[float] = field(default_factory=list)  # population mean

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
    """Return a copy of the lowest-cost individual from a random tournament draw."""
    candidates   = random.sample(range(len(population)), tournament_size)
    winner_index = min(candidates, key=lambda i: fitness[i])
    return population[winner_index][:]


def _uniform_crossover(
    parent1: list[int],
    parent2: list[int],
) -> tuple[list[int], list[int]]:
    """Uniform crossover: swap each gene independently with p=0.5."""
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
    """Per-gene mutation: each task's server reassigned uniformly at random with probability mutation_prob."""
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
    mutation_prob: float | None = None,   # None -> 1/n_tasks
    elitism_count: int = 2,
    verbose: bool = False,
) -> tuple[list[int], ScheduleEvaluation, GAStatistics]:
    """
    Run a Genetic Algorithm for cloud resource allocation.

    Returns (best_assignment, best_evaluation, diagnostics).
    """
    stats = GAStatistics()

    # Default: 1 expected mutation per offspring (standard rule-of-thumb)
    if mutation_prob is None:
        mutation_prob = 1.0 / data.n_tasks

    verbose_interval = max(1, n_generations // 10)

    # ------------------------------------------------------------------ #
    # Initialise population                                                #
    # One greedy-BFD solution gives the population a strong head start.   #
    # The rest are random to ensure initial diversity.                     #
    # ------------------------------------------------------------------ #
    population: list[list[int]] = [build_greedy_assignment(data)]
    for _ in range(population_size - 1):
        population.append(build_random_assignment(data))

    # ------------------------------------------------------------------ #
    # Evaluate initial population                                          #
    # Track the best ScheduleEvaluation as we go so we don't pay for a    #
    # redundant re-evaluation of the winner afterwards.                    #
    # ------------------------------------------------------------------ #
    fitness: list[float]     = []
    best_solution: list[int] = population[0][:]
    best_eval                = evaluate_schedule(population[0], data, weights)
    best_cost                = best_eval.objective_value
    fitness.append(best_cost)
    for ind in population[1:]:
        ev = evaluate_schedule(ind, data, weights)
        fitness.append(ev.objective_value)
        if ev.objective_value < best_cost:
            best_solution = ind[:]
            best_eval     = ev
            best_cost     = ev.objective_value
    stats.total_evaluations += population_size

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
        gen_mean = sum(fitness) / len(fitness)
        stats.best_cost_history.append(best_cost)
        stats.mean_cost_history.append(gen_mean)
        stats.n_generations_completed += 1

        # ---- Periodic verbose progress report ---- #
        gen = stats.n_generations_completed
        if verbose and gen % verbose_interval == 0:
            diversity = gen_mean - best_cost  # gap between mean and best
            t_frac    = gen / n_generations
            if t_frac < 0.33:
                phase = "early evolution — high diversity, mapping the search space"
            elif t_frac < 0.67:
                phase = "mid evolution — population converging around better regions"
            else:
                phase = "late evolution — fine-grained improvement via mutation"
            feasible_tag = "feasible" if best_eval.feasible else "infeasible"
            print(
                f"  [GA] gen {gen:>4}/{n_generations}"
                f"  best_F={best_cost:>10.2f} ({feasible_tag})"
                f"  mean_F={gen_mean:>10.2f}"
                f"  gap={diversity:>8.2f}"
                f"  → {phase}"
            )

    return best_solution, best_eval, stats
