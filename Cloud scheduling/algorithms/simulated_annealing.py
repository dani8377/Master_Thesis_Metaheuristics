"""
simulated_annealing.py — Simulated Annealing metaheuristic for the Cloud Scheduling problem.

PURPOSE
-------
Implements the core search algorithm used in the thesis experiments.  Simulated
Annealing (SA) is a probabilistic local-search metaheuristic that can escape
local optima by occasionally accepting worsening moves.  The probability of
accepting a worsening move decreases as the "temperature" cools, so the search
gradually transitions from broad exploration to fine-grained exploitation.

THE ALGORITHM (high level)
--------------------------
1.  Build a greedy initial assignment (FFD bin-packing).
2.  Repeat for up to max_temp_steps temperature levels:
    a.  Generate iterations_per_temperature candidate neighbours.
    b.  For each candidate:
        - Hard-reject if structurally invalid (is_valid_assignment).
        - Evaluate with evaluate_schedule().
        - Accept immediately if the candidate improves the objective.
        - Accept with probability exp(-Δ / T) if it worsens it  ← Metropolis.
        - Track the global best seen so far.
    c.  Cool: T ← T × cooling_rate.
    d.  Reheat if stuck: if no improvement for reheat_patience steps,
        reset T to reheat_factor × initial_temperature.
3.  Return the best assignment, its evaluation, and diagnostic statistics.

KEY PARAMETERS
--------------
initial_temperature:    High → almost all moves accepted (random walk).
                        Low  → almost no worsening moves accepted (greedy).
                        Rule of thumb: set so that ~80% of typical worsening
                        deltas are accepted at step 0.
cooling_rate:           How fast temperature drops each step (0 < rate < 1).
                        0.995 means temperature halves roughly every 138 steps.
reheat_patience / factor: If stuck for this many steps, reheat to reheat_factor ×
                        initial_temperature to escape a local basin.

STATISTICS
----------
SAStatistics records per-step histories and counters useful for diagnosing
whether the search is exploring well, cooling too fast, or stuck in a basin.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from tools.data_loader import SchedulingProblemData
from tools.objective import evaluate_schedule, ObjectiveWeights, ScheduleEvaluation
from tools.neighborhoods import generate_neighbor
from tools.initial_solution import build_greedy_assignment
from tools.feasibility import is_valid_assignment


# ---------------------------------------------------------------------------
# Diagnostic statistics container
# ---------------------------------------------------------------------------

@dataclass
class SAStatistics:
    """
    Diagnostic data collected during one SA run.

    Histories (one entry per temperature step) let you plot the convergence
    curve and see whether the search is cooling well.  Counters let you
    diagnose acceptance behaviour and feasibility.
    """

    # Per-step histories (length = number of completed temperature steps)
    best_cost_history: list[float]    = field(default_factory=list)
    current_cost_history: list[float] = field(default_factory=list)
    temperature_history: list[float]  = field(default_factory=list)

    # Counters accumulated over the whole run
    total_evaluated: int            = 0   # candidates that passed the structural check
    total_improving_accepted: int   = 0   # moves that reduced the objective
    total_worsening_accepted: int   = 0   # moves that worsened the objective but were accepted (Metropolis)
    total_rejected_structural: int  = 0   # candidates discarded by is_valid_assignment
    total_feasible_evaluated: int   = 0   # evaluated candidates with zero penalty

    reheat_count: int        = 0    # how many times the schedule was reheated
    final_temperature: float = 0.0  # temperature when the run ended

    @property
    def acceptance_rate(self) -> float:
        """Fraction of evaluated candidates that were accepted (improving + Metropolis)."""
        if self.total_evaluated == 0:
            return 0.0
        return (self.total_improving_accepted + self.total_worsening_accepted) / self.total_evaluated

    @property
    def feasibility_rate(self) -> float:
        """Fraction of evaluated candidates that were fully feasible (zero penalty)."""
        if self.total_evaluated == 0:
            return 0.0
        return self.total_feasible_evaluated / self.total_evaluated


# ---------------------------------------------------------------------------
# SA implementation
# ---------------------------------------------------------------------------

def simulated_annealing(
    data: SchedulingProblemData,
    weights: ObjectiveWeights,
    initial_temperature: float = 5000.0,
    cooling_rate: float = 0.995,
    min_temperature: float = 1e-3,
    iterations_per_temperature: int = 50,
    max_temp_steps: int = 2000,
    reheat_patience: int = 150,
    reheat_factor: float = 0.3,
) -> tuple[list[int], ScheduleEvaluation, SAStatistics]:
    """
    Run Simulated Annealing for cloud resource allocation scheduling.

    Returns
    -------
    best_assignment:  list[int] of length n_tasks, where entry i is the
                      index of the server task i is placed on.
    best_eval:        Full ScheduleEvaluation of that assignment.
    stats:            SAStatistics with per-step histories and counters.
    """
    stats = SAStatistics()

    # ---- Initialisation ---- #
    current_solution = build_greedy_assignment(data)  # greedy FFD start
    current_eval     = evaluate_schedule(current_solution, data, weights)
    current_cost     = current_eval.objective_value

    # Keep a copy of the best solution seen anywhere during the run
    best_solution = current_solution[:]
    best_eval     = current_eval
    best_cost     = current_cost

    temperature               = initial_temperature
    steps_without_improvement = 0  # used to trigger reheats

    # ---- Main SA loop ---- #
    for _ in range(max_temp_steps):
        # Early termination if temperature has dropped below the threshold
        if temperature < min_temperature:
            break

        step_improved = False  # did the global best improve this temperature step?

        # Inner loop: generate and evaluate candidates at this temperature
        for _ in range(iterations_per_temperature):
            candidate = generate_neighbor(current_solution, data)

            # Hard-reject structurally invalid candidates (wrong length / index)
            if not is_valid_assignment(candidate, data):
                stats.total_rejected_structural += 1
                continue

            candidate_eval = evaluate_schedule(candidate, data, weights)
            candidate_cost = candidate_eval.objective_value
            stats.total_evaluated += 1
            if candidate_eval.feasible:
                stats.total_feasible_evaluated += 1

            delta = candidate_cost - current_cost  # negative = improvement

            if delta < 0:
                # Improving move — always accept
                current_solution = candidate
                current_eval     = candidate_eval
                current_cost     = candidate_cost
                stats.total_improving_accepted += 1
            elif random.random() < math.exp(-delta / temperature):
                # Worsening move — accept with Metropolis probability
                # At high T: exp(-Δ/T) ≈ 1 (almost always accept)
                # At low  T: exp(-Δ/T) ≈ 0 (almost never accept)
                current_solution = candidate
                current_eval     = candidate_eval
                current_cost     = candidate_cost
                stats.total_worsening_accepted += 1

            # Update global best if the *current* solution just improved it
            if current_cost < best_cost:
                best_solution = current_solution[:]
                best_eval     = current_eval
                best_cost     = current_cost
                step_improved = True

        # ---- Cooling ---- #
        temperature *= cooling_rate
        stats.best_cost_history.append(best_cost)
        stats.current_cost_history.append(current_cost)
        stats.temperature_history.append(temperature)

        # ---- Reheat logic ---- #
        if step_improved:
            steps_without_improvement = 0
        else:
            steps_without_improvement += 1

        if steps_without_improvement >= reheat_patience:
            # Stuck: boost temperature to escape the current basin
            temperature               = reheat_factor * initial_temperature
            steps_without_improvement = 0
            stats.reheat_count       += 1

    stats.final_temperature = temperature
    return best_solution, best_eval, stats
