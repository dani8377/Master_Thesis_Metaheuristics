"""
umda.py — UMDA (Univariate Marginal Distribution Algorithm) for Cloud Scheduling.

PURPOSE
-------
Implements UMDA, a member of the Estimation of Distribution Algorithm (EDA) family.
Unlike Simulated Annealing (which explores via a single trajectory of small moves)
or Genetic Algorithm (which recombines solutions via crossover and mutation), UMDA
learns an explicit *probabilistic model* of good solutions and generates new
candidates by *sampling* from that model.  No crossover or mutation operators are
needed — the model plays the role of implicit recombination.

THE ALGORITHM (high level)
--------------------------
1.  Initialise a population of pop_size candidate solutions.
    One solution is built with the greedy FFD heuristic; the rest are random.
2.  Evaluate every individual.
3.  Repeat for n_generations generations:
    a.  Truncation selection: sort individuals by objective value (ascending)
        and keep the best n_select = floor(pop_size × selection_ratio) of them.
    b.  Build the probability model from the selected set:
        P[i][j] = (count of selected solutions where task i → server j
                   + smoothing)
                / (n_selected + n_servers × smoothing)
        Laplace smoothing prevents zero probabilities that would permanently
        eliminate a server from consideration for a given task.
    c.  Sample pop_size new individuals from the model:
        for each task i independently, draw its server from distribution P[i].
    d.  Elitism: inject the global best-ever solution into the new population,
        replacing the worst sampled individual.  This prevents the algorithm
        from "forgetting" the best solution found.
    e.  Evaluate all new individuals and update the global best.
4.  Return the best assignment seen across all generations.

THE UNIVARIATE MODEL
--------------------
The model is a matrix P of shape (n_tasks × n_servers) where each row P[i]
is a discrete probability distribution over servers for task i.  Rows are
treated as *independent* — the probability of task i going to server j does
not depend on where task k goes.

This independence assumption is the defining feature of UMDA ("univariate" =
one-dimensional marginals only).  The full joint distribution would have
n_servers^n_tasks = 10^50 states — completely intractable.  The univariate
model uses only n_tasks × n_servers = 50 × 10 = 500 parameters.

The independence assumption is approximately valid here: while server loads
couple tasks together (a task's latency depends on what else is on its server),
the coupling is mediated through the objective rather than through hard
combinatorial constraints, so the model still captures the dominant signal.

MODEL ENTROPY
-------------
The Shannon entropy of each row P[i] indicates how confident the model is
about task i's server placement:
  - High entropy (≈ log2(10) ≈ 3.32 bits) → model is uncertain; broad search.
  - Low entropy (≈ 0 bits) → model has converged; task i always goes to one server.
Tracking mean entropy over generations shows when the search has converged.

SELECTION
---------
Truncation selection: keep the top selection_ratio fraction of the population.
With selection_ratio=0.5 (default), the best 50 of 100 individuals are selected
each generation.  Truncation selection is simple, deterministic, and standard
in EDA literature.

COMPUTATIONAL BUDGET
--------------------
With default parameters (population_size=100, n_generations=1500), the total
number of evaluate_schedule() calls is approximately:
    population_size + n_generations × (population_size - elitism_count)
    = 100 + 1500 × 99 = 148,600
This is intentionally calibrated to match SA's ~150,000 evaluations for a
fair algorithm comparison under equal computational budget.

STATISTICS
----------
UMDAStatistics mirrors the SAStatistics and GAStatistics interface: it exposes
best_cost_history (one entry per generation), so plot_convergence() in plot.py
works for all three algorithms without any code changes.  The additional
model_entropy_history field provides insight into convergence behaviour.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from tools.data_loader import SchedulingProblemData
from tools.objective import evaluate_schedule, ObjectiveWeights, ScheduleEvaluation
from tools.initial_solution import build_greedy_assignment, build_random_assignment


# ---------------------------------------------------------------------------
# Diagnostic statistics container
# ---------------------------------------------------------------------------

@dataclass
class UMDAStatistics:
    """
    Diagnostic data collected during one UMDA run.

    best_cost_history has one entry per generation and is the field accessed
    by plot.py to draw convergence curves — it must use exactly this name.

    model_entropy_history provides a diagnostic of model convergence:
    when entropy stops decreasing, the model has identified stable
    server-task preferences and is no longer learning new structure.
    """

    # Per-generation histories (length == n_generations_completed)
    best_cost_history: list[float]     = field(default_factory=list)
    mean_cost_history: list[float]     = field(default_factory=list)
    model_entropy_history: list[float] = field(default_factory=list)

    # Aggregate counters
    total_evaluations: int       = 0
    n_generations_completed: int = 0


# ---------------------------------------------------------------------------
# Probability model helpers
# ---------------------------------------------------------------------------

def _build_probability_model(
    selected: list[list[int]],
    n_tasks: int,
    n_servers: int,
    smoothing: float,
) -> list[list[float]]:
    """
    Estimate the univariate probability model from a set of selected solutions.

    For each task i, count how many selected solutions assign task i to each
    server j, then normalise with Laplace smoothing:

        P[i][j] = (count(a[i] == j for a in selected) + smoothing)
                / (len(selected) + n_servers * smoothing)

    Laplace smoothing ensures P[i][j] > 0 for all (i, j), preventing any
    server from being permanently excluded from future samples.  A smoothing
    value of 0.1 is negligible compared to the empirical counts once
    len(selected) ≥ 2, but sufficient to keep every option reachable.

    Returns a list-of-lists (Python floats) so that random.choices() can be
    used directly for sampling, preserving the experiment harness's seed control.
    """
    n_selected = len(selected)
    denominator = float(n_selected + n_servers * smoothing)
    model: list[list[float]] = []

    for i in range(n_tasks):
        # Initialise all counts with the Laplace smoothing term
        counts = [smoothing] * n_servers
        for sol in selected:
            counts[sol[i]] += 1.0  # increment the server this solution chose for task i

        # Normalise to a proper probability distribution
        row = [c / denominator for c in counts]
        model.append(row)

    return model


def _sample_from_model(
    model: list[list[float]],
    n_tasks: int,
    n_servers: int,
) -> list[int]:
    """
    Sample one new candidate solution from the univariate probability model.

    For each task i independently, draw its server assignment from the
    marginal distribution P[i] using Python's random.choices(), which
    respects the random state seeded by the experiment harness and therefore
    makes each run fully reproducible.

    Independence means we make n_tasks = 50 separate single-draw decisions,
    one for each task.
    """
    server_range = list(range(n_servers))
    assignment: list[int] = []
    for i in range(n_tasks):
        # random.choices returns a list; [0] extracts the single drawn value
        server = random.choices(server_range, weights=model[i], k=1)[0]
        assignment.append(server)
    return assignment


def _model_entropy(model: list[list[float]]) -> float:
    """
    Compute the mean Shannon entropy across all rows of the probability model.

    Entropy of row i:   H_i = -Σ_j P[i][j] * log2(P[i][j])

    Maximum (uniform):  log2(n_servers) ≈ 3.32 bits  →  broad, uncertain model.
    Minimum (degenerate): 0 bits  →  task i always placed on one specific server.

    Mean entropy is averaged across all n_tasks rows.
    """
    total_entropy = 0.0
    for row in model:
        for p in row:
            if p > 1e-15:
                total_entropy -= p * math.log2(p)
    # Normalise by number of tasks to get average per-task entropy
    return total_entropy / len(model)


# ---------------------------------------------------------------------------
# Main UMDA function
# ---------------------------------------------------------------------------

def umda(
    data: SchedulingProblemData,
    weights: ObjectiveWeights,
    population_size: int = 100,
    n_generations: int = 1500,
    selection_ratio: float = 0.5,
    smoothing: float = 0.1,
    elitism_count: int = 1,
) -> tuple[list[int], ScheduleEvaluation, UMDAStatistics]:
    """
    Run UMDA for cloud resource allocation scheduling.

    Parameters
    ----------
    population_size:
        Number of candidate solutions per generation.  Larger populations
        give more reliable probability estimates but cost more per generation.
        100 is a reasonable default for 50 tasks × 10 servers.
    n_generations:
        Maximum number of model-learning and sampling iterations.
        With population_size=100 and elitism_count=1, total evaluations ≈ 148,600
        (matching SA's ~150,000 for a fair budget comparison).
    selection_ratio:
        Fraction of the population retained for model estimation (truncation
        selection).  0.5 keeps the best 50 individuals from each 100-strong
        population.
    smoothing:
        Laplace smoothing added to all model counts.  0.1 is negligible once
        the selection size is > 2 but prevents zero-probability server choices.
    elitism_count:
        Number of best-ever solutions forcibly inserted into each new population.
        Prevents "forgetting" — the model can drift away from the global best,
        so reinserting it keeps it in the gene pool.

    Returns
    -------
    best_assignment:  list[int] — best task-to-server mapping found.
    best_eval:        ScheduleEvaluation with the full cost breakdown.
    stats:            UMDAStatistics with per-generation histories and counters.
    """
    stats    = UMDAStatistics()
    # Ensure at least 2 individuals selected so the model is non-trivial
    n_select = max(2, int(population_size * selection_ratio))

    # ------------------------------------------------------------------ #
    # Initialise population                                                #
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

    # Global best seen so far — tracked across all generations
    best_idx      = min(range(population_size), key=lambda i: fitness[i])
    best_solution = population[best_idx][:]
    best_eval     = evaluate_schedule(best_solution, data, weights)
    best_cost     = best_eval.objective_value

    # ------------------------------------------------------------------ #
    # Main UMDA loop                                                       #
    # ------------------------------------------------------------------ #
    for _ in range(n_generations):

        # --- Truncation selection: keep the top n_select individuals ---
        ranked   = sorted(range(population_size), key=lambda i: fitness[i])
        selected = [population[ranked[k]] for k in range(n_select)]

        # --- Build probability model from selected individuals ---
        model = _build_probability_model(
            selected, data.n_tasks, data.n_servers, smoothing
        )

        # --- Sample a completely new population from the model ---
        new_population: list[list[int]] = []
        new_fitness: list[float]        = []

        # Elitism: inject the global best-ever solution directly into the
        # new population before sampling.  This guarantees the best solution
        # is never lost even if the model has drifted away from its region.
        for _ in range(elitism_count):
            new_population.append(best_solution[:])
            new_fitness.append(best_cost)

        # Sample the remaining individuals from the learned model
        while len(new_population) < population_size:
            candidate = _sample_from_model(model, data.n_tasks, data.n_servers)
            ev        = evaluate_schedule(candidate, data, weights)
            new_population.append(candidate)
            new_fitness.append(ev.objective_value)
            stats.total_evaluations += 1

            # Update global best if this sampled individual is better
            if ev.objective_value < best_cost:
                best_solution = candidate[:]
                best_eval     = ev
                best_cost     = ev.objective_value

        population = new_population
        fitness    = new_fitness

        # --- Record per-generation diagnostics ---
        mean_cost = sum(fitness) / len(fitness)
        stats.best_cost_history.append(best_cost)
        stats.mean_cost_history.append(mean_cost)
        stats.model_entropy_history.append(_model_entropy(model))
        stats.n_generations_completed += 1

    return best_solution, best_eval, stats
