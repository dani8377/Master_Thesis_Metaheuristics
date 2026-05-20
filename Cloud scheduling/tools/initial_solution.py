"""
initial_solution.py — Initial assignment constructors for the Cloud Scheduling problem.

PURPOSE
-------
Generates the starting assignment that SA begins its search from.  A good
initial solution can dramatically reduce the number of iterations needed to
reach feasibility, so starting smart (rather than randomly) matters.

THREE CONSTRUCTORS ARE PROVIDED
---------------------------------
build_random_assignment:
    Every task gets a uniformly random server.  Simple, but almost always
    starts infeasible and far from optimal.  Useful as a worst-case baseline.

build_round_robin_assignment:
    Tasks are distributed to servers in round-robin order (task i → server
    i % m).  Spreads load evenly but ignores resource demands entirely.
    Nearly always feasible for balanced workloads but rarely energy-optimal.

build_greedy_assignment  ← used by SA, GA, UMDA, and the greedy baseline
    BEST-Fit Decreasing (BFD) bin-packing variant.  Tasks are sorted heaviest
    CPU-first, then each task is placed on the MOST-LOADED feasible server
    (best-fit) — NOT the first feasible server (which would be First-Fit
    Decreasing, FFD).  Best-fit produces a tighter packing than first-fit,
    minimising the number of active servers and their associated idle-power
    cost.  This is a stronger baseline than true FFD.

NAMING NOTE (important for thesis clarity)
-------------------------------------------
The function is named "build_greedy_assignment" and the baseline runner is
named "greedy_ffd_baseline" for backwards-compatibility with older code.
The IMPLEMENTATION is Best-Fit Decreasing (BFD) and the user-facing label in
all current plots, CSVs and tables is "Greedy BFD".  Refer to it as "Greedy
BFD" in the thesis to keep the algorithm description aligned with the code.

WHY BEST-FIT (not FIRST-FIT)?
-----------------------------
Both BFD and FFD are linear-time bin-packing heuristics.  BFD typically
produces tighter packings (more empty bins/servers) because it actively
prefers high-utilisation servers, whereas FFD just picks the first that
fits.  Tighter packing means fewer active servers, which directly reduces
idle-power energy cost — exactly what this objective rewards.
"""
from __future__ import annotations

import random

import numpy as np

from tools.data_loader import SchedulingProblemData


def build_random_assignment(data: SchedulingProblemData) -> list[int]:
    """Assign each task to a uniformly random server.  Used as a naive baseline."""
    return [random.randint(0, data.n_servers - 1) for _ in range(data.n_tasks)]


def build_round_robin_assignment(data: SchedulingProblemData) -> list[int]:
    """
    Assign tasks to servers in round-robin order: task i → server i % m.
    Spreads tasks evenly across all servers regardless of resource demands.
    """
    return [i % data.n_servers for i in range(data.n_tasks)]


def build_greedy_assignment(data: SchedulingProblemData) -> list[int]:
    """
    Greedy Best-Fit Decreasing (BFD) initial assignment.

    Note: function name retains the historical "greedy_assignment" label
    for backwards compatibility, but this is BFD (best-fit), not FFD
    (first-fit).  See module docstring for the distinction.

    Algorithm
    ---------
    1. Sort tasks by CPU usage descending — heaviest tasks first.
       (CPU is typically the tighter resource; placing large tasks first
        leaves smaller tasks more room to fit anywhere.)
    2. For each task, find all servers that still have spare capacity for
       both its CPU and memory requirements.
    3. Among feasible servers, pick the one with the highest current CPU
       load (BEST-FIT packing).  This consolidates tasks onto fewer servers,
       reducing the number of active servers and their idle-power cost.
       (True First-Fit Decreasing would pick the lowest-index feasible server.)
    4. If no server has room, fall back to the least CPU-loaded server.
       This produces a soft-infeasibility that SA will repair via its penalty
       terms rather than crashing the initial construction.
    """
    n = data.n_tasks
    m = data.n_servers

    assignment = [0] * n
    # Track running totals so we don't call bincount on every iteration
    cpu_load   = np.zeros(m, dtype=np.float64)
    mem_load   = np.zeros(m, dtype=np.float64)

    # Process tasks from heaviest CPU requirement to lightest
    order = sorted(range(n), key=lambda i: data.cpu[i], reverse=True)

    for i in order:
        task_cpu = data.cpu[i]
        task_mem = data.mem[i]

        # Servers that can accept this task without exceeding either limit
        feasible = [
            j for j in range(m)
            if (cpu_load[j] + task_cpu <= data.server_cpu_cap[j]
                and mem_load[j] + task_mem <= data.server_mem_cap[j])
        ]

        if feasible:
            # Best-fit: pick the most-loaded feasible server to pack tightly
            j = max(feasible, key=lambda j: cpu_load[j])
        else:
            # Fallback: least-loaded server (allows soft infeasibility)
            j = int(np.argmin(cpu_load))

        assignment[i] = j
        cpu_load[j]  += task_cpu
        mem_load[j]  += task_mem

    return assignment
