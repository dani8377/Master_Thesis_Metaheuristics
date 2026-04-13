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

build_greedy_assignment  ← used by SA
    First-Fit Decreasing (FFD) bin-packing variant.  Tasks are sorted heaviest
    CPU-first, then each task is placed on the most-loaded server that still
    has room.  This packs tasks tightly, minimises idle servers, and produces
    a near-feasible starting point with reasonable energy cost.

WHY FFD?
--------
The FFD heuristic is a classical bin-packing algorithm that is known to
achieve near-optimal packing in linear time.  By starting SA from a compact,
mostly-feasible assignment, the search spends far fewer early iterations just
trying to fix capacity violations and can focus sooner on improving the
energy–latency trade-off.
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
    Greedy First-Fit Decreasing (FFD) initial assignment.

    Algorithm
    ---------
    1. Sort tasks by CPU usage descending — heaviest tasks first.
       (CPU is typically the tighter resource; placing large tasks first
        leaves smaller tasks more room to fit anywhere.)
    2. For each task, find all servers that still have spare capacity for
       both its CPU and memory requirements.
    3. Among feasible servers, pick the one with the highest current CPU
       load (best-fit packing).  This consolidates tasks onto fewer servers,
       reducing the number of active servers and their idle-power cost.
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
