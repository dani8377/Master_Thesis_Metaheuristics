# Master Thesis — Metaheuristics for Combinatorial Optimisation

This repository contains the Python implementations developed for the Masters
thesis. Two distinct combinatorial optimisation problems are studied, each
solved with a Simulated Annealing (SA) metaheuristic. The two problems share
the same algorithmic skeleton but are completely independent of each other.

---

## Problems

### 1. EV Routing (`EV_routing/`)

An Electric Vehicle routing problem set in San Francisco.  A single EV must
visit a set of customer locations, starting and ending at a central depot,
while managing its battery charge.  Charging stations can be inserted into the
route when needed.

**What the optimiser decides:** the order in which customers are visited and
where to stop for charging.

**Objective:** minimise a weighted combination of total distance, travel time,
charging time, energy consumed, and charging cost.  Battery depletion is
handled as a soft penalty so the search can temporarily enter infeasible
regions and naturally recover.

**Dataset:** synthetic San Francisco instance — 75 customers, 30 charging
stations, pre-computed Haversine distance and energy matrices.

---

### 2. Cloud Scheduling (`Cloud scheduling/`)

A cloud resource allocation scheduling problem.  A batch of independent
computational tasks must be assigned to a pool of heterogeneous physical
servers.  Each server has fixed CPU and memory capacity; each task has a
resource footprint, an energy draw, a service latency, and a priority class.

**What the optimiser decides:** which server each task runs on.

**Objective:** minimise a weighted combination of total energy consumption
(idle power of active servers + workload energy scaled by server efficiency)
and priority-weighted service latency (which increases with server congestion).
Capacity violations are soft penalties.

**Dataset:** `cloud_resource_allocation_dataset.csv` — 6,345 task records.
The server pool (10 heterogeneous servers) is synthesised as instance
parameters (see `tools/data_loader.py`).

---

## Project Structure

```
Master_Thesis_Metaheuristics/
│
├── run.py                          ← top-level runner (see Usage below)
├── Makefile                        ← alias for make-based systems
│
├── EV_routing/
│   ├── main.py                     ← entry point for EV routing
│   ├── datasets/                   ← SF customers, stations, distance/energy matrices
│   ├── figures/                    ← convergence plots saved here
│   ├── algorithms/
│   │   └── simmulated_annealing.py ← SA implementation for routing
│   └── tools/
│       ├── data_loader.py          ← loads datasets into ProblemData
│       ├── objective.py            ← route evaluation and objective function
│       ├── feasibility.py          ← structural route validation
│       ├── initial_solution.py     ← greedy EV-feasible initial route
│       ├── neighborhoods.py        ← swap / relocate / 2-opt / station moves
│       ├── experiment.py           ← multi-seed experiment harness
│       ├── plot.py                 ← convergence plot + comparison table
│       ├── energy.py               ← EVParameters and energy helpers
│       ├── energy_model.py         ← physics-based arc energy computation
│       ├── distance.py             ← distance providers (Euclidean / Haversine)
│       └── node_utils.py           ← station attribute lookup helpers
│
└── Cloud scheduling/
    ├── main.py                     ← entry point for cloud scheduling
    ├── datasets/                   ← cloud_resource_allocation_dataset.csv
    ├── figures/                    ← convergence plots saved here
    ├── algorithms/
    │   └── simulated_annealing.py  ← SA implementation for scheduling
    └── tools/
        ├── data_loader.py          ← loads CSV + synthesises server pool
        ├── objective.py            ← schedule evaluation and objective function
        ├── feasibility.py          ← structural assignment validation
        ├── initial_solution.py     ← greedy first-fit-decreasing initial solution
        ├── neighborhoods.py        ← reassign / swap / consolidate / spread moves
        ├── experiment.py           ← multi-seed experiment harness
        └── plot.py                 ← convergence plot + comparison table
```

---

## Usage

All commands are run from the **project root** directory.

### Running with `run.py` (recommended — works on all systems)

```bash
# Cloud scheduling only
uv run run.py cloud

# EV routing only
uv run run.py ev

# Both problems in sequence
uv run run.py
```

### Running with `make` (requires make to be installed)

```bash
make cloud    # cloud scheduling only
make ev       # EV routing only
make all      # both
```

To install make on Windows:
```bash
winget install GnuWin32.Make   # via winget
scoop install make             # via scoop
```

### Running a single script directly

```bash
# From inside the problem directory:
uv run --with numpy --with pandas --with matplotlib python main.py
```

---

## Dependencies

The project uses [uv](https://github.com/astral-sh/uv) for Python and package
management.  No virtual environment or `pip install` step is needed — `uv run`
downloads and caches packages automatically on first use.

Required packages: `numpy`, `pandas`, `matplotlib`

---

## Output

Each run produces:

- A **single-run diagnostic printout** — objective value, energy, latency,
  capacity violations, active server count, SA acceptance/feasibility rates,
  and a per-server task distribution bar chart.
- A **10-seed experiment table** — Best / Average / Worst / Std Dev /
  Feasible runs / Average runtime.
- A **convergence plot** saved to `figures/sa_convergence.png` inside the
  relevant problem folder.
