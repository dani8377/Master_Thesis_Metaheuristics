"""
UMDA (Univariate Marginal Distribution Algorithm) for the cloud task scheduling problem.

An Estimation of Distribution Algorithm (EDA): instead of crossover and mutation,
UMDA learns a probability matrix P[task][server] from the best solutions each
generation and samples new candidates from it.  Laplace smoothing prevents early
collapse of the model.  Budget calibrated to ~150 000 evaluations to match SA/GA.

Performance note: all inner-loop operations (model building, sampling, entropy)
are implemented as vectorised NumPy operations.  This keeps UMDA competitive in
wall-clock time even at n_tasks > 200, where a pure-Python sampling loop would
be prohibitively slow (each model sample requires n_tasks draws).
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

import numpy as np

from tools.data_loader import SchedulingProblemData
from tools.objective import evaluate_schedule, ObjectiveWeights, ScheduleEvaluation
from tools.initial_solution import build_greedy_assignment, build_random_assignment


# ---------------------------------------------------------------------------
# Diagnostic statistics container
# ---------------------------------------------------------------------------

@dataclass
class UMDAStatistics:
    """Per-run diagnostics: convergence histories, model entropy, and evaluation counts."""

    best_cost_history: list[float]     = field(default_factory=list)  # one per generation
    mean_cost_history: list[float]     = field(default_factory=list)
    model_entropy_history: list[float] = field(default_factory=list)  # mean Shannon entropy of P

    total_evaluations: int       = 0
    n_generations_completed: int = 0


# ---------------------------------------------------------------------------
# Probability model helpers (vectorised NumPy implementations)
# ---------------------------------------------------------------------------

def _build_probability_model(
    selected: list[list[int]],
    n_tasks: int,
    n_servers: int,
    smoothing: float,
) -> np.ndarray:
    """
    Estimate the univariate probability model from a set of selected solutions.

    For each task i, count how many selected solutions assign task i to each
    server j, then normalise with Laplace smoothing:

        P[i][j] = (count(a[i] == j for a in selected) + smoothing)
                / (len(selected) + n_servers * smoothing)

    Implementation: fully vectorised via np.bincount on a flat index, avoiding
    any Python loop over tasks or solutions.

    Returns a (n_tasks, n_servers) float64 array where each row is a valid
    probability distribution (rows sum to 1.0).
    """
    n_selected = len(selected)
    # Stack into array: shape (n_selected, n_tasks); values in [0, n_servers)
    arr = np.array(selected, dtype=np.intp)  # (n_selected, n_tasks)

    # Flat index: (task_idx * n_servers + server_idx) uniquely identifies a
    # (task, server) pair in [0, n_tasks * n_servers).
    # arr.T has shape (n_tasks, n_selected); ravel gives (n_tasks * n_selected,)
    # with layout: all solutions for task 0, then task 1, etc.
    task_idx   = np.repeat(np.arange(n_tasks, dtype=np.intp), n_selected)
    server_idx = arr.T.ravel()

    counts = np.bincount(
        task_idx * n_servers + server_idx,
        minlength=n_tasks * n_servers,
    ).reshape(n_tasks, n_servers).astype(np.float64)

    counts += smoothing
    counts /= float(n_selected + n_servers * smoothing)
    return counts  # shape (n_tasks, n_servers), rows sum to 1.0


def _sample_population(
    model: np.ndarray,
    n_samples: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Draw n_samples candidate solutions from the univariate probability model.

    Uses vectorised inverse-CDF (quantile) sampling:
      1. Compute CDF along the server axis: shape (n_tasks, n_servers).
      2. Draw n_samples × n_tasks uniform values in [0, 1).
      3. For each (sample, task) pair find the first server j where CDF[task,j] >= u.
         np.argmax on the boolean mask returns that index efficiently.

    Returns an integer array of shape (n_samples, n_tasks) where each value is
    the server index assigned to that task in that candidate solution.

    The intermediate boolean tensor has shape (n_samples, n_tasks, n_servers).
    At the config default of population_size=100 and n_tasks=500, n_servers=100
    this is 100 × 500 × 100 = 5 M bools ≈ 5 MB — well within typical memory.
    """
    n_tasks, n_servers = model.shape
    cdf = np.cumsum(model, axis=1)
    cdf[:, -1] = 1.0  # clamp last column to exactly 1.0 (float rounding guard)

    # u: (n_samples, n_tasks), each value in [0, 1)
    u = rng.random((n_samples, n_tasks))

    # Comparison broadcast: cdf (1, n_tasks, n_servers) vs u (n_samples, n_tasks, 1)
    # Result shape: (n_samples, n_tasks, n_servers) — True where cdf >= u
    # argmax along server axis returns the first True index per (sample, task) pair.
    return np.argmax(cdf[np.newaxis] >= u[:, :, np.newaxis], axis=-1)  # (n_samples, n_tasks)


def _model_entropy(model: np.ndarray) -> float:
    """
    Compute the mean Shannon entropy across all rows of the probability model.

    Entropy of row i:   H_i = -sum_j P[i][j] * log2(P[i][j])
    Maximum (uniform):  log2(n_servers) bits  -> broad, uncertain model.
    Minimum (degenerate): 0 bits  -> task i always placed on one specific server.

    Vectorised: avoids any Python loop; the eps guard prevents log2(0).
    """
    eps  = 1e-15
    safe = np.where(model > eps, model, 1.0)   # avoid log2(0) — replaced with log2(1)=0
    h_per_row = -np.sum(model * np.where(model > eps, np.log2(safe), 0.0), axis=1)
    return float(h_per_row.mean())


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
    verbose: bool = False,
) -> tuple[list[int], ScheduleEvaluation, UMDAStatistics]:
    """
    Run UMDA for cloud resource allocation scheduling.

    Parameters
    ----------
    population_size:
        Number of candidate solutions per generation.  Larger populations
        give more reliable probability estimates but cost more per generation.
        100 is a reasonable default for 50 tasks x 10 servers.
    n_generations:
        Maximum number of model-learning and sampling iterations.
        With population_size=100 and elitism_count=1, total evaluations ~148,600
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
    n_select = max(2, int(population_size * selection_ratio))

    verbose_interval = max(1, n_generations // 10)

    # Create a reproducible NumPy RNG seeded from the Python random state.
    # The experiment harness seeds random.seed(seed) before calling this function,
    # so random.randint(...) here is deterministic per seed.
    np_rng = np.random.default_rng(random.randint(0, 2**31 - 1))

    # ------------------------------------------------------------------ #
    # Initialise population                                                #
    #                                                                      #
    # Theoretical motivation for the mixed strategy:                       #
    #                                                                      #
    # Pure random initialisation gives UMDA's univariate model an almost   #
    # uniform marginal distribution as input — at large n the random       #
    # assignments are heavily infeasible and dominated by penalty terms,   #
    # so the model can't learn meaningful task-server preferences and      #
    # tends to return the greedy elite unchanged.                          #
    #                                                                      #
    # Strategy: seed half the population with PERTURBED greedy variants    #
    # (each task reassigned with probability 0.1 to a random server) and   #
    # the rest with pure random assignments.  This gives the model         #
    # information-rich starting points (which it can learn from) while     #
    # preserving exploration via random samples.  At n=50 this slightly    #
    # speeds convergence; at n>=200 it is what allows the model to learn   #
    # at all.                                                              #
    # ------------------------------------------------------------------ #
    population: list[list[int]] = [build_greedy_assignment(data)]
    greedy_base = population[0]
    n_perturbed = (population_size - 1) // 2  # roughly half perturbed, half random
    perturb_rate = 0.10                       # probability each gene is mutated
    for _ in range(n_perturbed):
        perturbed = greedy_base[:]
        for i in range(data.n_tasks):
            if random.random() < perturb_rate:
                perturbed[i] = random.randrange(data.n_servers)
        population.append(perturbed)
    for _ in range(population_size - 1 - n_perturbed):
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
    # Main UMDA loop                                                       #
    # ------------------------------------------------------------------ #
    n_new = population_size - elitism_count  # candidates to sample each generation

    for _ in range(n_generations):

        # --- Truncation selection: keep the top n_select individuals ---
        ranked   = sorted(range(population_size), key=lambda i: fitness[i])
        selected = [population[ranked[k]] for k in range(n_select)]

        # --- Build probability model (vectorised) ---
        model = _build_probability_model(
            selected, data.n_tasks, data.n_servers, smoothing
        )

        # --- Sample n_new candidates at once (vectorised) ---
        # candidates: (n_new, n_tasks) integer array
        candidates_arr = _sample_population(model, n_new, np_rng)

        # --- Compose new population: elites first, then sampled ---
        new_population: list[list[int]] = [best_solution[:] for _ in range(elitism_count)]
        new_fitness: list[float]        = [best_cost] * elitism_count

        for row in candidates_arr:
            candidate = row.tolist()
            ev        = evaluate_schedule(candidate, data, weights)
            new_population.append(candidate)
            new_fitness.append(ev.objective_value)
            stats.total_evaluations += 1

            if ev.objective_value < best_cost:
                # NOTE: copy with [:] to avoid aliasing — `candidate` is also
                # appended to new_population above, and best_solution must not
                # share storage with any list that future code may mutate.
                best_solution = candidate[:]
                best_eval     = ev
                best_cost     = ev.objective_value

        population = new_population
        fitness    = new_fitness

        # --- Record per-generation diagnostics ---
        mean_cost   = sum(fitness) / len(fitness)
        gen_entropy = _model_entropy(model)
        stats.best_cost_history.append(best_cost)
        stats.mean_cost_history.append(mean_cost)
        stats.model_entropy_history.append(gen_entropy)
        stats.n_generations_completed += 1

        gen = stats.n_generations_completed
        if verbose and gen % verbose_interval == 0:
            max_entropy = math.log2(data.n_servers)
            rel_entropy = gen_entropy / max_entropy if max_entropy > 0 else 0.0
            t_frac      = gen / n_generations
            if rel_entropy > 0.7:
                phase = "model uncertain - sampling broadly across all servers"
            elif rel_entropy > 0.3:
                phase = "model learning - server preferences emerging per task"
            else:
                phase = "model converged - focused sampling in high-confidence region"
            feasible_tag = "feasible" if best_eval.feasible else "infeasible"
            print(
                f"  [UMDA] gen {gen:>4}/{n_generations}"
                f"  best_F={best_cost:>10.2f} ({feasible_tag})"
                f"  entropy={gen_entropy:>5.2f}/{max_entropy:.2f} bits"
                f"  -> {phase}"
            )

    return best_solution, best_eval, stats
