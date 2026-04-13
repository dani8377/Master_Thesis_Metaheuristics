"""
data_loader.py — Problem instance loader for the Cloud Scheduling problem.

PURPOSE
-------
This file is responsible for turning the raw CSV dataset into the fast,
numpy-backed data structure (SchedulingProblemData) that every other module
in this package works with.  It is the single point of contact with the
filesystem: all other modules receive a SchedulingProblemData object and
never touch the CSV directly.

WHAT IT DOES
------------
1.  Reads the cloud resource allocation CSV (one row per task).
2.  Extracts the four columns used by the baseline formulation:
    CPU_Usage, Memory_Usage, Energy_Consumption, Service_Latency, Task_Priority.
3.  Synthesises a heterogeneous server pool (since the dataset has no server
    table).  Ten servers with varying core counts, memory, idle power draw,
    and energy efficiency are defined as DEFAULT_SERVER_POOL.
4.  Packs everything into numpy arrays so that the hot evaluation loop in
    objective.py can use vectorised operations instead of Python loops.

HOW IT FITS IN
--------------
    data_loader  →  SchedulingProblemData
                         ↓
              objective / neighborhoods / initial_solution / feasibility
                         ↓
              simulated_annealing  →  experiment  →  plot
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Server configuration
# ---------------------------------------------------------------------------

@dataclass
class ServerConfig:
    """Parameters for a single physical server in the synthesised server pool."""

    cpu_capacity: float   # C_j  — maximum CPU load in % (e.g. 400 = 4-core server)
    mem_capacity: float   # M_j  — maximum memory in MB
    idle_power: float     # e_idle_j — Watts drawn when the server is on but idle
    efficiency: float     # η_j  — energy scaling factor; < 1 is newer/more efficient,
                          #        > 1 is older/less efficient hardware


# Default heterogeneous server pool.
# These values are treated as instance parameters and are reported in the
# Methodology section alongside the experimental results.
#
# The mix covers small (2-core), standard (4-core), large (6-core), and
# high-capacity (8-core) machines with a spread of efficiencies to give the
# optimiser a genuine reason to prefer some servers over others.
DEFAULT_SERVER_POOL: list[ServerConfig] = [
    #                cpu %   mem MB      idle W   η
    ServerConfig(    400,    65_536,     100.0,   1.00),  # Standard 4-core
    ServerConfig(    600,   131_072,     180.0,   0.80),  # Large 6-core, efficient
    ServerConfig(    200,    32_768,      60.0,   1.20),  # Small 2-core, older
    ServerConfig(    400,    65_536,     110.0,   0.90),  # Standard 4-core, newer
    ServerConfig(    800,   262_144,     250.0,   0.70),  # High-capacity 8-core, best efficiency
    ServerConfig(    400,    65_536,      95.0,   1.10),  # Standard 4-core, slightly old
    ServerConfig(    200,    32_768,      55.0,   1.30),  # Small 2-core, old
    ServerConfig(    600,   131_072,     190.0,   0.85),  # Large 6-core, newer
    ServerConfig(    400,    65_536,     105.0,   1.00),  # Standard 4-core
    ServerConfig(    300,    49_152,      80.0,   1.15),  # Medium 3-core, older
]


# ---------------------------------------------------------------------------
# Central data container
# ---------------------------------------------------------------------------

@dataclass
class SchedulingProblemData:
    """
    All data needed to represent and evaluate a cloud scheduling instance.

    Passed by reference to every module that needs problem information.
    Using numpy arrays for the hot-path attributes means the inner evaluation
    loop in objective.py can stay fully vectorised.
    """

    tasks: pd.DataFrame        # raw DataFrame — n_tasks rows, one per task
    n_tasks: int               # n  — total number of tasks to schedule
    n_servers: int             # m  — total number of available servers

    # ---- Task attribute arrays, shape (n_tasks,) ----
    cpu: np.ndarray      # c_i  — CPU requirement in % (from CPU_Usage column)
    mem: np.ndarray      # m_i  — memory requirement in MB
    energy: np.ndarray   # e_i  — baseline energy draw in Watts when the task runs
    latency: np.ndarray  # l_i  — baseline service latency in ms on an unloaded server
    priority: np.ndarray # p_i  — priority class: 0 = Low, 1 = Medium, 2 = High

    # ---- Server attribute arrays, shape (n_servers,) ----
    server_cpu_cap: np.ndarray     # C_j   — CPU capacity per server (%)
    server_mem_cap: np.ndarray     # M_j   — memory capacity per server (MB)
    server_idle_power: np.ndarray  # e_idle_j — idle power draw per server (W)
    server_efficiency: np.ndarray  # η_j   — energy efficiency factor per server


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def load_problem_data(
    dataset_dir: str | Path,
    n_tasks: int = 50,
    servers: list[ServerConfig] | None = None,
    random_sample: bool = False,
    seed: int | None = None,
) -> SchedulingProblemData:
    """
    Load a cloud scheduling problem instance from the dataset directory.

    Parameters
    ----------
    dataset_dir:
        Directory that contains cloud_resource_allocation_dataset.csv.
    n_tasks:
        How many tasks to load.  Uses the first n_tasks rows unless
        random_sample=True.
    servers:
        Server pool to use.  Falls back to DEFAULT_SERVER_POOL when None.
    random_sample:
        If True, draw n_tasks rows at random (reproducible via seed).
    seed:
        Random state for sampling — only used when random_sample=True.
    """
    dataset_dir = Path(dataset_dir)
    csv_path = dataset_dir / "cloud_resource_allocation_dataset.csv"

    df = pd.read_csv(csv_path)

    # Select the task subset
    if random_sample:
        df = df.sample(n=n_tasks, random_state=seed).reset_index(drop=True)
    else:
        df = df.head(n_tasks).reset_index(drop=True)

    if servers is None:
        servers = DEFAULT_SERVER_POOL

    n_servers = len(servers)

    # Extract task attributes as float64 numpy arrays for fast vectorised ops
    cpu      = df["CPU_Usage (%)"].to_numpy(dtype=np.float64)
    mem      = df["Memory_Usage (MB)"].to_numpy(dtype=np.float64)
    energy   = df["Energy_Consumption (Watts)"].to_numpy(dtype=np.float64)
    latency  = df["Service_Latency (ms)"].to_numpy(dtype=np.float64)
    priority = df["Task_Priority"].to_numpy(dtype=np.int32)

    # Build server attribute arrays from the ServerConfig list
    server_cpu_cap    = np.array([s.cpu_capacity for s in servers], dtype=np.float64)
    server_mem_cap    = np.array([s.mem_capacity for s in servers], dtype=np.float64)
    server_idle_power = np.array([s.idle_power   for s in servers], dtype=np.float64)
    server_efficiency = np.array([s.efficiency   for s in servers], dtype=np.float64)

    return SchedulingProblemData(
        tasks=df,
        n_tasks=n_tasks,
        n_servers=n_servers,
        cpu=cpu,
        mem=mem,
        energy=energy,
        latency=latency,
        priority=priority,
        server_cpu_cap=server_cpu_cap,
        server_mem_cap=server_mem_cap,
        server_idle_power=server_idle_power,
        server_efficiency=server_efficiency,
    )
