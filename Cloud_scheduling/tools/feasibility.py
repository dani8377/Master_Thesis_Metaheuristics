"""
Structural validation of an assignment vector.

A cheap check run before the objective evaluation, so malformed candidates are
discarded without paying for a full evaluate_schedule() call.  Only structure
is checked: the right number of entries, and every entry a real server index.

Capacity is deliberately not checked here.  CPU and memory limits are soft
penalties in objective.py, so the search is allowed to pass through infeasible
assignments and is pulled back by the penalty weights.
"""
from __future__ import annotations

from tools.data_loader import SchedulingProblemData


def is_valid_assignment(assignment: list[int], data: SchedulingProblemData) -> bool:
    """
    Return True if *assignment* has one entry per task and every entry is a
    valid server index.  Capacity is not tested here (see module docstring).
    """
    if len(assignment) != data.n_tasks:
        return False

    n_servers = data.n_servers
    if any(a < 0 or a >= n_servers for a in assignment):
        return False

    return True
