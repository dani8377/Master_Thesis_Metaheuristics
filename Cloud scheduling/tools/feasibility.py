"""
feasibility.py — Structural assignment validation for the Cloud Scheduling problem.

PURPOSE
-------
Provides a fast, lightweight check that a candidate assignment vector is
structurally valid before it is passed to the (more expensive) objective
evaluator.  Any candidate that fails this check is immediately discarded by
the SA inner loop without spending time on the full evaluation.

WHAT IS CHECKED (and what is NOT)
----------------------------------
Checked here — structural validity:
  • The assignment has exactly n_tasks entries (one server index per task).
  • Every entry is a valid server index in [0, n_servers).

NOT checked here — handled elsewhere:
  • CPU capacity constraints  ← soft penalty in objective.py
  • Memory capacity constraints ← soft penalty in objective.py

The reason capacity constraints are *not* hard-checked here is intentional:
allowing SA to temporarily visit infeasible regions is mathematically
important for escaping local optima.  The large penalty weights (λ_cpu,
λ_mem) ensure the search returns to the feasible region naturally.

RELATIONSHIP TO EV ROUTING
---------------------------
This file mirrors EV_routing/tools/feasibility.py → is_valid_basic_route(),
which checks that a route starts/ends at the depot and visits all customers
exactly once.  The cloud equivalent is simpler because the assignment vector
representation already guarantees every task is assigned to exactly one server.
"""
from __future__ import annotations

from tools.data_loader import SchedulingProblemData


def is_valid_assignment(assignment: list[int], data: SchedulingProblemData) -> bool:
    """
    Return True if *assignment* is structurally valid.

    A structurally valid assignment has:
    - Exactly data.n_tasks entries (one per task, no missing tasks).
    - Every entry in [0, data.n_servers) (references a real server).

    Capacity feasibility is intentionally NOT tested here — see module
    docstring for the reasoning.
    """
    # Wrong length means a neighborhood operator produced a malformed vector
    if len(assignment) != data.n_tasks:
        return False

    # Every entry must be a legal server index
    n_servers = data.n_servers
    if any(a < 0 or a >= n_servers for a in assignment):
        return False

    return True
