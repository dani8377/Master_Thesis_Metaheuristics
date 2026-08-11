"""
Initial assignment constructors for the cloud scheduling problem.

    build_random_assignment       uniformly random.  Usually infeasible.
    build_round_robin_assignment  task i -> server i % m.  Ignores demands.
    build_greedy_assignment       Best-Fit Decreasing.  Used as the warm start
                                  for SA, GA and UMDA, and as the greedy baseline.

Naming: the function and the baseline runner (greedy_ffd_baseline) keep their
old "ffd" labels so existing imports still work, but the implementation is
best-fit, not first-fit, and everything user-facing calls it "Greedy BFD".
Best-fit packs tighter than first-fit, which leaves more servers empty and so
saves idle power, which is what this objective rewards.
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
    Greedy Best-Fit Decreasing assignment.

    Tasks are sorted by CPU demand descending (CPU is the tighter resource, so
    the large tasks are placed while there is still room), and each is put on
    the feasible server with the highest current CPU load.  If no server has
    room, the task goes to the least-loaded one, which leaves a violation for
    the penalty terms to repair rather than failing the construction.
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
