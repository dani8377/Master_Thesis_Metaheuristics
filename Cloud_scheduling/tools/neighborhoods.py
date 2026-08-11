"""
Neighbourhood operators for the cloud scheduling problem.

Every operator returns a new assignment (a shallow copy with one small change)
and never modifies its input:

    reassign_random_task      random task -> random other server.  The general
                              move that keeps the whole space reachable.
    swap_tasks                exchange the servers of two tasks.
    relocate_from_overloaded  move a task off the most CPU-loaded server, which
                              targets the capacity penalty directly.
    consolidate_tasks         least-loaded server -> most-loaded.  Empties
                              servers, so it lowers idle power, E(X).
    spread_tasks              most-loaded server -> least-loaded.  Lowers
                              congestion, L(X).

The last two pull in opposite directions, which is the energy-latency tension
the search has to resolve.  generate_neighbor() picks one operator uniformly
at random; whether the candidate is kept is decided by the acceptance
criterion, not here.
"""
from __future__ import annotations

import random

import numpy as np

from tools.data_loader import SchedulingProblemData


# ---------------------------------------------------------------------------
# Individual neighbourhood operators
# ---------------------------------------------------------------------------

def reassign_random_task(
    assignment: list[int],
    data: SchedulingProblemData,
) -> list[int]:
    """
    Move one randomly chosen task to a randomly chosen *different* server.

    This is the most unconstrained move and provides the broadest coverage
    of the search space.  It can increase or decrease load on any server.
    """
    new_a = assignment[:]
    i = random.randrange(data.n_tasks)
    current = new_a[i]
    # Build list of servers that are not the current one
    others  = [j for j in range(data.n_servers) if j != current]
    if not others:
        return new_a  # only one server — nothing to move to
    new_a[i] = random.choice(others)
    return new_a


def swap_tasks(
    assignment: list[int],
    data: SchedulingProblemData,
) -> list[int]:
    """
    Swap the server assignments of two randomly chosen tasks.

    Swapping preserves the total number of tasks on each server involved
    if the two tasks happen to be on different servers, so it can rebalance
    *which* tasks are where without changing server utilisation totals.
    """
    new_a = assignment[:]
    if data.n_tasks < 2:
        return new_a
    i, j = random.sample(range(data.n_tasks), 2)
    new_a[i], new_a[j] = new_a[j], new_a[i]
    return new_a


def relocate_from_overloaded(
    assignment: list[int],
    data: SchedulingProblemData,
) -> list[int]:
    """
    Move a task away from the most CPU-loaded server.

    Specifically targets the server contributing the most to both the CPU
    penalty term and the congestion latency term.  Moving one of its tasks
    to a random other server directly reduces its load.
    """
    new_a    = assignment[:]
    a        = np.asarray(new_a, dtype=np.int32)
    # Compute per-server CPU load to find the most overloaded one
    cpu_load = np.bincount(a, weights=data.cpu, minlength=data.n_servers)

    overloaded = int(np.argmax(cpu_load))
    tasks_here = [i for i, s in enumerate(new_a) if s == overloaded]
    if not tasks_here:
        return new_a  # server is empty (should not happen if assignment is valid)

    task_to_move  = random.choice(tasks_here)
    other_servers = [j for j in range(data.n_servers) if j != overloaded]
    if not other_servers:
        return new_a

    new_a[task_to_move] = random.choice(other_servers)
    return new_a


def consolidate_tasks(
    assignment: list[int],
    data: SchedulingProblemData,
) -> list[int]:
    """
    Move a task from the least-loaded active server to the most-loaded one.

    INTENT (energy direction):
    If the source server becomes empty after the move, it transitions from
    active (paying e_idle_j Watts) to idle (paying 0 Watts), which directly
    reduces E(X).  This move therefore pushes the solution toward using fewer
    servers — the energy-saving direction of the trade-off.

    TENSION with latency:
    Moving a task onto an already busy server increases that server's CPU
    load, which raises the congestion latency for all tasks on that server.
    SA decides whether to accept this based on the net change in F(X).
    """
    new_a      = assignment[:]
    a          = np.asarray(new_a, dtype=np.int32)
    cpu_load   = np.bincount(a, weights=data.cpu, minlength=data.n_servers)
    task_count = np.bincount(a,                   minlength=data.n_servers)

    # Only consider servers that actually have tasks (active servers)
    active_servers = [j for j in range(data.n_servers) if task_count[j] > 0]
    if len(active_servers) < 2:
        return new_a  # can't consolidate with fewer than 2 active servers

    # Source: the active server with the lowest CPU load (best candidate to empty)
    source = min(active_servers, key=lambda j: cpu_load[j])
    tasks_on_source = [i for i, s in enumerate(new_a) if s == source]
    if not tasks_on_source:
        return new_a
    task_to_move = random.choice(tasks_on_source)

    # Target: the most-loaded server that is not the source
    others = [j for j in active_servers if j != source]
    if not others:
        others = [j for j in range(data.n_servers) if j != source]
    if not others:
        return new_a

    target = max(others, key=lambda j: cpu_load[j])
    new_a[task_to_move] = target
    return new_a


def spread_tasks(
    assignment: list[int],
    data: SchedulingProblemData,
) -> list[int]:
    """
    Move a task from the most CPU-loaded server to the least CPU-loaded one.

    INTENT (latency direction):
    Reduces the CPU utilisation ratio U_cpu_j / C_j on the busiest server,
    which directly lowers the congestion multiplier (1 + γ · load_ratio) for
    all remaining tasks on that server, thereby improving L(X).

    TENSION with energy:
    Spreading tasks may activate a previously idle server, adding its idle
    power draw to E(X).  SA weighs this cost against the latency improvement.
    """
    new_a    = assignment[:]
    a        = np.asarray(new_a, dtype=np.int32)
    cpu_load = np.bincount(a, weights=data.cpu, minlength=data.n_servers)

    most_loaded  = int(np.argmax(cpu_load))
    least_loaded = int(np.argmin(cpu_load))
    if most_loaded == least_loaded:
        return new_a  # all servers have equal load — nothing useful to do

    tasks_on_heavy = [i for i, s in enumerate(new_a) if s == most_loaded]
    if not tasks_on_heavy:
        return new_a

    # Move one randomly chosen task from the heaviest to the lightest server
    new_a[random.choice(tasks_on_heavy)] = least_loaded
    return new_a


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def generate_neighbor(
    assignment: list[int],
    data: SchedulingProblemData,
) -> list[int]:
    """
    Randomly select one of the five neighbourhood operators and apply it.

    All operators are weighted equally (uniform selection).  The SA
    acceptance criterion — not this function — determines whether the
    resulting candidate replaces the current solution.
    """
    moves = [
        reassign_random_task,    # broad exploration
        swap_tasks,              # exchange two tasks
        relocate_from_overloaded,# repair CPU violations / congestion
        consolidate_tasks,       # energy direction: pack onto fewer servers
        spread_tasks,            # latency direction: spread load across servers
    ]
    return random.choice(moves)(assignment, data)
