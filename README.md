# Master Thesis — Metaheuristics for Combinatorial Optimisation

This repository contains the Python implementations developed for the Masters
thesis.  Two distinct combinatorial optimisation problems are studied, each
solved with multiple metaheuristics and baseline heuristics.  The two problems
share the same algorithmic infrastructure (experiment harness, plotting
utilities, data loaders) but are completely independent in their problem
formulations and solution representations.

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

**Algorithms:** Simulated Annealing (SA).

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
Capacity violations are soft penalties that steer the search back to feasibility.

**Dataset:** `cloud_resource_allocation_dataset.csv` — 6,345 task records.
The server pool (10 heterogeneous servers) is synthesised as instance
parameters (see `tools/data_loader.py`).

**Algorithms:** three metaheuristics (SA, GA, UMDA) plus three baselines
(Greedy FFD, Round-Robin, Random).

---

## Cloud Scheduling Algorithms

### Simulated Annealing (SA)

Single-solution trajectory metaheuristic.  Starts from a greedy FFD
construction and explores the neighbourhood via five problem-specific move
operators.  Uses a geometric cooling schedule with reheating.

Key parameters: `initial_temperature=5000`, `cooling_rate=0.995`,
`iterations_per_temperature=50`, `max_temp_steps=3000`.

Total evaluations: ≈150,000 per run.

### Genetic Algorithm (GA)

Population-based evolutionary metaheuristic.  Maintains a population of 50
candidate assignments and evolves them via tournament selection, uniform
crossover, and per-gene mutation.  Elitism (2 best individuals) is applied
each generation to guarantee monotone improvement of the best-ever solution.

Key parameters: `population_size=50`, `n_generations=3000`,
`tournament_size=3`, `crossover_prob=0.8`, `mutation_prob=1/n_tasks`.

Total evaluations: ≈144,050 per run — comparable to SA for fair comparison.

### UMDA — Univariate Marginal Distribution Algorithm (EDA)

Estimation of Distribution Algorithm.  Learns a univariate probability model
P[task i][server j] from the top-50% of the population each generation, then
samples new candidate solutions directly from this model.  No crossover or
mutation operators are needed — the model provides implicit recombination.

Key parameters: `population_size=100`, `n_generations=1500`,
`selection_ratio=0.5`, `smoothing=0.1` (Laplace smoothing).

Total evaluations: ≈148,600 per run — comparable to SA and GA.

### Baselines

| Baseline | Description |
|---|---|
| **Greedy FFD** | First-Fit Decreasing bin-packing — the same construction SA and GA start from.  Deterministic. |
| **Round-Robin** | Cyclic assignment: task i → server i % m.  Ignores resource demands.  Deterministic. |
| **Random** | Uniform random assignment.  Varies per seed.  Worst-case reference. |

---

## Project Structure

```
Master_Thesis_Metaheuristics/
│
├── run.py                              ← top-level runner (see Usage)
├── Makefile                            ← make-based shortcuts
│
├── EV_routing/
│   ├── main.py                         ← EV routing entry point
│   ├── datasets/                       ← SF customers, stations, matrices
│   ├── figures/                        ← convergence plots
│   ├── algorithms/
│   │   └── simmulated_annealing.py     ← SA for routing
│   └── tools/
│       ├── data_loader.py              ← load ProblemData
│       ├── objective.py                ← route fitness function
│       ├── feasibility.py              ← structural route validation
│       ├── initial_solution.py         ← greedy nearest-neighbour start
│       ├── neighborhoods.py            ← 8 route move operators
│       ├── experiment.py               ← multi-seed harness
│       ├── plot.py                     ← convergence plot + table
│       ├── energy.py                   ← EVParameters + energy helpers
│       ├── energy_model.py             ← physics-based arc energy
│       ├── distance.py                 ← Haversine / Euclidean
│       └── node_utils.py               ← station attribute helpers
│
└── Cloud scheduling/
    ├── main.py                         ← cloud scheduling entry point
    ├── datasets/
    │   └── cloud_resource_allocation_dataset.csv
    ├── figures/                        ← plots saved here
    │   ├── convergence_all_algorithms.png  ← SA + GA + UMDA overlaid
    │   ├── sa_convergence.png              ← SA only
    │   └── algorithm_comparison_bar.png   ← Best/Avg/Worst bar chart
    ├── results/                        ← numerical results saved here
    │   ├── results_per_seed.csv        ← one row per (algorithm, seed)
    │   ├── results_summary.csv         ← per-algorithm aggregates
    │   └── sensitivity_analysis.csv   ← SA hyperparameter sweep (optional)
    ├── algorithms/
    │   ├── simulated_annealing.py      ← SA + SAStatistics
    │   ├── genetic_algorithm.py        ← GA + GAStatistics
    │   ├── umda.py                     ← UMDA + UMDAStatistics
    │   └── baselines.py                ← greedy / round-robin / random
    └── tools/
        ├── data_loader.py              ← load CSV + synthesise server pool
        ├── objective.py                ← ScheduleEvaluation + ObjectiveWeights
        ├── feasibility.py              ← structural assignment validation
        ├── initial_solution.py         ← greedy FFD / round-robin / random
        ├── neighborhoods.py            ← 5 move operators
        ├── experiment.py               ← generic multi-seed harness
        └── plot.py                     ← convergence / bar / table / CSV
```

---

## Usage

All commands are run from the **project root** directory.

### Recommended — `run.py`

```bash
# Cloud scheduling only
uv run run.py cloud

# EV routing only
uv run run.py ev

# Both problems in sequence
uv run run.py
```

### With `make` (requires make to be installed)

```bash
make cloud    # cloud scheduling
make ev       # EV routing
make all      # both
```

To install make on Windows:
```bash
winget install GnuWin32.Make   # via winget
scoop install make             # via scoop
```

### Direct — inside the problem directory

```bash
uv run --with numpy --with pandas --with matplotlib python main.py
```

---

## Dependencies

The project uses [uv](https://github.com/astral-sh/uv) for Python and package
management.  No virtual environment or `pip install` step is needed — `uv run`
downloads and caches packages automatically on first use.

Required packages: `numpy`, `pandas`, `matplotlib`

---

## Output (Cloud Scheduling)

Each full run of `main.py` produces:

### Console output
- Problem instance summary (task count, server count, total demand vs. capacity).
- Single-run SA diagnostic (solution quality + SA acceptance/feasibility/reheat stats
  + per-server ASCII bar chart of task distribution).
- Per-run progress lines for all 10-seed experiments (SA, GA, UMDA, baselines).
- Unified comparison table:

```
Algorithm                         Best      Average        Worst    Std Dev   Feasible   Avg Time
-----------------------------------------------------------------------------------------------
Simulated Annealing          12345.67     12987.34     14023.11     456.78     10/10     4.52s
Genetic Algorithm            12501.23     13102.45     14501.67     612.34      9/10     5.13s
UMDA (EDA)                   12789.01     13456.78     14678.90     512.34      9/10     4.87s
Greedy FFD (baseline)        15234.56     15234.56     15234.56       0.00     10/10     0.01s
Round-Robin (baseline)       23456.78     23456.78     23456.78       0.00      0/10     0.00s
Random (baseline)            28901.23     31234.56     35678.90    2345.67      0/10     0.00s
```

### Plot files (`figures/`)
| File | What it shows |
|---|---|
| `convergence_all_algorithms.png` | SA, GA, and UMDA convergence curves overlaid (mean ± 1σ across 10 seeds). |
| `sa_convergence.png` | SA-only convergence for direct comparison with thesis SA section. |
| `algorithm_comparison_bar.png` | Grouped horizontal bar chart comparing Best / Average / Worst for all six algorithms. |
| `sa_sensitivity.png` | SA hyperparameter sensitivity (only when `RUN_SENSITIVITY = True`). |

### CSV files (`results/`)
| File | Contents |
|---|---|
| `results_per_seed.csv` | One row per (algorithm, seed): cost, energy, latency, violations, feasible, runtime. |
| `results_summary.csv` | One row per algorithm: best, average, worst, std dev, feasible count, avg runtime. |
| `sensitivity_analysis.csv` | SA parameter sweep results (only when `RUN_SENSITIVITY = True`). |

---

## SA Sensitivity Analysis

The sensitivity analysis is disabled by default to keep runtimes short.
To enable it, open `Cloud scheduling/main.py` and change:

```python
RUN_SENSITIVITY = False
```
to:
```python
RUN_SENSITIVITY = True
```

This sweeps `initial_temperature` over [500, 1000, 2000, 5000, 10000, 20000]
and `cooling_rate` over [0.990, 0.992, 0.995, 0.997, 0.999], running 5 seeds
per configuration.  Results are saved to `results/sensitivity_analysis.csv`
and `figures/sa_sensitivity.png`.
