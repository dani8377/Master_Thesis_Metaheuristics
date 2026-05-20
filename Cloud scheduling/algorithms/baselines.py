"""
baselines.py — One-shot reference baselines for the Cloud Scheduling problem.

PURPOSE
-------
Provides three simple non-iterative construction heuristics that serve as
reference points for comparing against the metaheuristics (SA, GA, UMDA).
Each baseline builds a single assignment and returns it immediately — there
is no search, no iterations, and no improvement loop.

WHY INCLUDE BASELINES?
-----------------------
Including baselines in the thesis results table answers the fundamental question:
"How much does the metaheuristic actually contribute?"

  - If SA/GA/UMDA achieve dramatically lower costs than the greedy BFD baseline,
    that validates the investment in metaheuristic search.
  - If the greedy baseline is already near-optimal, that tells us the problem
    structure is well-suited to greedy construction and long searches may not
    be worth the computational cost.
  - Random assignment provides an absolute lower bound on algorithm quality —
    no sensible algorithm should be worse than random.

THREE BASELINES
---------------
greedy_ffd_baseline:
    Best-Fit Decreasing bin-packing — the same initial solution that SA and
    GA start from.  It is deterministic: all seeds give identical results.
    Including it isolates the improvement attributable to the search beyond
    the initial construction.  (The "ffd" in the function name is a legacy
    label kept for backwards-compatible imports; the implementation is BFD.)

round_robin_baseline:
    Cyclic assignment: task i → server (i % n_servers).  Spreads tasks evenly
    across servers without considering resource requirements.  Deterministic.
    Provides a load-balanced reference that ignores energy efficiency.

random_assignment_baseline:
    Uniformly random assignment.  The result varies across seeds because the
    experiment harness seeds Python's random module before each call.
    This is the worst-case reference — it shows what happens with zero
    domain knowledge.

STATISTICS INTERFACE
--------------------
Each baseline returns a BaselineStatistics object whose best_cost_history
contains a single element — the one-shot objective value.  This satisfies
the interface expected by run_experiments() and plot.py (which access
stats.best_cost_history), even though there is no convergence to visualise.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from tools.data_loader import SchedulingProblemData
from tools.objective import evaluate_schedule, ObjectiveWeights, ScheduleEvaluation
from tools.initial_solution import (
    build_greedy_assignment,
    build_random_assignment,
    build_round_robin_assignment,
)


# ---------------------------------------------------------------------------
# Minimal statistics container for non-iterative baselines
# ---------------------------------------------------------------------------

@dataclass
class BaselineStatistics:
    """
    Minimal statistics for a one-shot baseline.

    best_cost_history is a single-element list [objective_value] so that
    plot.py and run_experiments() can treat baselines and metaheuristics
    uniformly without special-casing.  There is no meaningful convergence
    curve for a one-shot constructor, so these entries will not be included
    in the convergence plot.

    total_evaluations is always 1: exactly one call to evaluate_schedule().
    """
    best_cost_history: list[float] = field(default_factory=list)
    total_evaluations: int = 1


# ---------------------------------------------------------------------------
# Baseline algorithm functions (AlgorithmFn-compatible)
# ---------------------------------------------------------------------------

def greedy_ffd_baseline(
    data: SchedulingProblemData,
    weights: ObjectiveWeights,
    **_kwargs,
) -> tuple[list[int], ScheduleEvaluation, BaselineStatistics]:
    """
    One-shot greedy Best-Fit Decreasing assignment (same as SA/GA start point).

    Tasks are sorted heaviest-CPU-first and placed on the most-loaded server
    that still has capacity.  Deterministic — identical result across all seeds.

    The "ffd" in this function name is a legacy label retained for
    backwards-compatible imports; the implementation in build_greedy_assignment
    is Best-Fit Decreasing (BFD), not First-Fit Decreasing.

    This baseline answers: "How much does the metaheuristic improve on the
    greedy construction it starts from?"
    """
    assignment = build_greedy_assignment(data)
    ev         = evaluate_schedule(assignment, data, weights)
    return assignment, ev, BaselineStatistics(best_cost_history=[ev.objective_value])


def round_robin_baseline(
    data: SchedulingProblemData,
    weights: ObjectiveWeights,
    **_kwargs,
) -> tuple[list[int], ScheduleEvaluation, BaselineStatistics]:
    """
    One-shot round-robin cyclic assignment: task i → server (i % n_servers).

    Spreads tasks evenly across all servers in sequence.  Completely ignores
    resource demands (CPU, memory) and server heterogeneity (efficiency, idle
    power).  Deterministic — identical result across all seeds.

    This baseline provides a load-balanced reference that makes no attempt
    to optimise for energy or latency.
    """
    assignment = build_round_robin_assignment(data)
    ev         = evaluate_schedule(assignment, data, weights)
    return assignment, ev, BaselineStatistics(best_cost_history=[ev.objective_value])


def random_assignment_baseline(
    data: SchedulingProblemData,
    weights: ObjectiveWeights,
    **_kwargs,
) -> tuple[list[int], ScheduleEvaluation, BaselineStatistics]:
    """
    One-shot uniformly random assignment.

    Each task is independently assigned to a server chosen uniformly at random.
    The result changes across seeds because the experiment harness seeds
    Python's random module before each run.

    This is the weakest possible baseline: zero domain knowledge.  Any
    competent algorithm should significantly outperform random assignment.
    """
    assignment = build_random_assignment(data)
    ev         = evaluate_schedule(assignment, data, weights)
    return assignment, ev, BaselineStatistics(best_cost_history=[ev.objective_value])
