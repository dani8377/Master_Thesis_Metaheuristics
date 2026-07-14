# Beginner's Guide to the Cloud Scheduling Implementation

> This guide is for someone who has just opened this folder for the first time.
> It explains what every file does, how data flows through the system, and how to
> read and understand the code. No prior knowledge of metaheuristics is assumed.

---

## 0. Quick Start — Where to Begin Right Now

If you are completely new, do exactly this:

1. **Run the code first** so you can see what it produces:
   ```bash
   uv run run.py cloud --seeds 3
   ```

2. **Read the output** in `results/summary.md` — this is the human-readable summary
   generated automatically after each run. It tells you which algorithm won and why.

3. **Read `config.yaml`** — all algorithm settings live here. This is the one file
   you edit to reproduce different experiments or change hyperparameters.

4. **Then follow the reading order below** (Steps A–F) to understand the code.

> **Just want to verify the thesis formulas match the code?** Jump to
> [Section 12 — Thesis Cross-Reference](#12-thesis-cross-reference) at the bottom.

---

## 1. What Problem Are We Solving?

We have **50 jobs** (called "tasks") and **10 computers** (called "servers"). We need to
decide which job runs on which server. Every possible assignment is a "solution" — but
there are 10^50 possible solutions, which is more than the number of atoms in the
observable universe. We obviously cannot try them all.

Instead, three metaheuristic algorithms (SA, GA, UMDA) search intelligently through
this enormous space and find very good — though not necessarily perfect — solutions.

The quality of a solution is measured by a single number **F(X)** (lower is better):

```
F(X) ≈ (normalised energy) + (normalised latency) + (capacity violation penalties)
```

We want F(X) to be as small as possible.

---

## 2. The File Map

Here is every file, in the order you should read them:

```
Cloud_scheduling/
│
├── config.yaml                     ← START HERE: all tunable numbers in one place
├── main.py                         ← the entry point; run this to reproduce results
│
├── tools/
│   ├── config_loader.py            ← reads config.yaml → typed Python dataclasses
│   ├── data_loader.py              ← loads the CSV dataset → SchedulingProblemData
│   ├── objective.py                ← the math: evaluate_schedule() scores a solution
│   ├── initial_solution.py         ← builds starting assignments (FFD, random, etc.)
│   ├── feasibility.py              ← validates an assignment vector is structurally OK
│   ├── neighborhoods.py            ← 5 move operators that modify a solution slightly
│   ├── experiment.py               ← runs any algorithm N times, collects statistics
│   └── plot.py                     ← all visualisations and CSV export
│
└── algorithms/
    ├── simulated_annealing.py      ← SA algorithm + auto temperature estimation
    ├── genetic_algorithm.py        ← GA with tournament selection, crossover, mutation
    ├── umda.py                     ← UMDA (EDA) with probability model + entropy tracking
    ├── branch_and_bound.py         ← exact solver with time limit (for comparison)
    └── baselines.py                ← one-shot baselines: Greedy BFD, Round-Robin, Random
```

---

## 3. Recommended Reading Order

If you want to understand the full implementation from scratch, read files in this order:

### Step A — Understand the problem data (10 minutes)

Read `tools/data_loader.py`. It loads the CSV and constructs the `SchedulingProblemData`
dataclass. This dataclass is passed to every other function — if you understand it,
you understand the problem.

Key fields of `SchedulingProblemData`:
| Field | Shape | What it is |
|---|---|---|
| `n_tasks` | scalar | Number of tasks (50) |
| `n_servers` | scalar | Number of servers (10) |
| `cpu` | (n_tasks,) | CPU demand of each task |
| `mem` | (n_tasks,) | Memory demand of each task |
| `energy` | (n_tasks,) | Energy draw of each task (Watts) |
| `latency` | (n_tasks,) | Base latency of each task (ms) |
| `priority` | (n_tasks,) | Priority class: 0=Low, 1=Medium, 2=High |
| `server_cpu_cap` | (n_servers,) | CPU capacity of each server |
| `server_mem_cap` | (n_servers,) | Memory capacity of each server |
| `server_idle_power` | (n_servers,) | Idle power draw (Watts) |
| `server_efficiency` | (n_servers,) | Efficiency factor η (>1 = less efficient) |

### Step B — Understand the objective function (20 minutes)

Read `tools/objective.py`. This is the **heart of the system** — it defines what "good"
means. Everything else in the codebase is just a strategy for finding better F(X) values.

Key things to understand:
1. `FocusMode` enum — three named presets (BALANCED, PERFORMANCE, ECO)
2. `ObjectiveWeights` dataclass — the six tunable coefficients (wₑ, wₗ, λ_cpu, λ_mem, γ, refs)
3. `compute_normalization_constants()` — computes E_ref, L_ref, CPU_ref, Mem_ref once
4. `evaluate_schedule(assignment, data, weights)` — the function called ~150,000 times
   per experiment; returns a `ScheduleEvaluation` with the full cost breakdown

The function is fully vectorised with numpy — no Python loops, just array operations.
This is what makes it fast enough to call 150,000 times without becoming a bottleneck.

### Step C — Understand the configuration (5 minutes)

Read `config.yaml`. All hyperparameters are here: population sizes, generation counts,
cooling rates, objective weights per focus mode, sensitivity sweep ranges, and scalability
test sizes. Then read `tools/config_loader.py` to see how these values get loaded into
typed Python dataclasses (`SAConfig`, `GAConfig`, `UMDAConfig`, etc.).

**Rule:** if you want to change any algorithm parameter, edit `config.yaml`. Do not
edit the algorithm files directly.

### Step D — Understand the algorithms (30 minutes each)

Read the algorithm files in this order:

1. `algorithms/simulated_annealing.py` — the simplest conceptually. Start with
   `estimate_initial_temperature()` to understand the auto-calibration trick, then read
   `simulated_annealing()` which is the main loop.

2. `algorithms/genetic_algorithm.py` — read the three helper functions first
   (`_tournament_select`, `_uniform_crossover`, `_mutate`), then the main `genetic_algorithm()` loop.

3. `algorithms/umda.py` — read `_build_probability_model()` and `_model_entropy()` first,
   then `_sample_population()` (vectorised numpy sampler — draws the whole generation at
   once to avoid slow Python loops), then the main `umda()` loop.

4. `algorithms/baselines.py` — one-shot algorithms; very short, no search loop.

### Step E — Understand the experiment harness (10 minutes)

Read `tools/experiment.py`. The `run_experiment()` function takes any algorithm function,
runs it `n_seeds` times with different random seeds, and collects results into an
`ExperimentResults` dataclass. This is how the 10-seed multi-run experiments work.

The harness is **algorithm-agnostic** — it works with SA, GA, and UMDA through the same
interface (`AlgorithmFn` type alias). Adding a new algorithm just means writing a function
with the right signature.

### Step F — Understand the entry point (15 minutes)

Read `main.py`. This is the file that ties everything together:
1. Parses CLI arguments.
2. Loads data and config.
3. Computes normalisation constants.
4. Runs each algorithm through the experiment harness.
5. Prints comparison table and significance tests.
6. Calls plot functions and saves CSV files.

---

## 4. Data Flow Diagram

```
config.yaml
    │
    ▼
config_loader.py ──────────────────────────────────────────────────┐
    │                                                               │
    ▼                                                               │
data_loader.py ──→ SchedulingProblemData                           │
    │                       │                                       │
    │                       ▼                                       │
    │           objective.py                                        │
    │       compute_normalization_constants()                       │
    │       → sets energy_ref, latency_ref on ObjectiveWeights      │
    │                       │                                       │
    │                       ▼                                       │
    │           initial_solution.py                                 │
    │           → build_greedy_assignment(data)                     │
    │                       │                                       │
    │                       ▼                                       │
    │           Algorithm (SA / GA / UMDA)                          │◀───────┐
    │               calls evaluate_schedule(assignment, data, weights)       │
    │               calls generate_neighbor(assignment, data)         │      │
    │               returns (best_assignment, best_eval, statistics)  │      │
    │                       │                                         │      │
    │                       ▼                                         │      │
    │           experiment.py                                         │      │
    │           run_experiment() repeats above N seeds ───────────────┘      │
    │           → ExperimentResults                                          │
    │                       │                                                │
    │                       ▼                                                │
    │           main.py                                              ◀───────┘
    │           print_comparison_table()                             (repeated for
    │           print_significance_table()                            each algorithm)
    │                       │
    │                       ▼
    │           plot.py
    │           plot_convergence()
    │           plot_metaheuristics_bar()
    │           plot_box_comparison()
    │           save_results_csv()
    │                       │
    └──────────────────────────────────── figures/*.png + results/*.csv
```

---

## 5. Key Dataclasses — What Each Field Means

### `ObjectiveWeights` (in `tools/objective.py`)

The six coefficients that define the optimisation goal:

```python
@dataclass
class ObjectiveWeights:
    energy_weight: float     # wₑ — how much energy matters (0.2–1.0)
    latency_weight: float    # wₗ — how much latency matters (0.2–1.0)
    cpu_penalty: float       # λ_cpu — penalty per normalised CPU violation
    mem_penalty: float       # λ_mem — penalty per normalised memory violation
    congestion_factor: float # γ — how steeply latency rises with server load
    energy_ref: float | None # E_ref — worst-case energy (set after data load)
    latency_ref: float | None# L_ref — worst-case latency (set after data load)
    cpu_ref: float | None    # CPU_ref — total CPU demand (normalisation denominator)
    mem_ref: float | None    # Mem_ref — total memory demand (normalisation denominator)
```

### `ScheduleEvaluation` (in `tools/objective.py`)

The full breakdown returned by `evaluate_schedule()`:

```python
@dataclass
class ScheduleEvaluation:
    total_energy: float      # E(X) in Watts
    total_latency: float     # L(X) in ms — priority-weighted, congestion-adjusted
    cpu_violation: float     # Σⱼ max(0, U_cpu_j − Cⱼ) — raw CPU overload
    mem_violation: float     # Σⱼ max(0, U_mem_j − Mⱼ) — raw memory overload
    n_active_servers: int    # how many servers are hosting at least one task
    objective_value: float   # F(X) — the single number used for all comparisons
    feasible: bool           # True iff cpu_violation == mem_violation == 0
```

### `ExperimentResults` (in `tools/experiment.py`)

The aggregate result of running one algorithm N times:

```python
@dataclass
class ExperimentResults:
    algorithm_name: str           # display name shown in tables and plots
    seeds: list[int]              # the random seeds used
    best_costs: list[float]       # best F(X) per seed
    best_evals: list[ScheduleEvaluation]  # full breakdown per seed
    runtimes: list[float]         # wall-clock seconds per seed
    all_stats: list[...]          # per-seed convergence histories (SAStatistics etc.)
    # Derived properties:
    best_cost: float              # min of best_costs
    average_cost: float           # mean of best_costs
    worst_cost: float             # max of best_costs
    std_cost: float               # std of best_costs
    feasible_run_count: int       # how many seeds produced a feasible solution
    average_runtime: float        # mean of runtimes
```

### `SAStatistics`, `GAStatistics`, `UMDAStatistics`

Each algorithm returns its own statistics container with `best_cost_history` — a list
of the best F(X) seen so far, one value per temperature step (SA) or generation
(GA/UMDA). This list is what the convergence plots are drawn from.

---

## 6. How a Solution is Represented

A solution is a Python `list[int]` of length `n_tasks = 50`:

```
assignment = [3, 0, 7, 7, 2, 1, ...]
              ↑  ↑  ↑
              task 0 → server 3
                 task 1 → server 0
                    task 2 → server 7
```

`assignment[i] = j` means task i runs on server j. This is equivalent to the binary
matrix xᵢⱼ from the thesis, but much more compact: 50 integers instead of a 50×10
binary matrix.

---

## 7. How the Objective Function Works (Step by Step)

When `evaluate_schedule(assignment, data, weights)` is called with the assignment above:

**Step 1 — Per-server load aggregation (numpy bincount):**
```python
cpu_load[j] = sum of cpu[i] for all i where assignment[i] == j
mem_load[j] = sum of mem[i] for all i where assignment[i] == j
active[j]   = True if any task is on server j
```

**Step 2 — Energy:**
```python
idle_energy     = dot(server_idle_power, active)      # idle power of active servers
workload_energy = dot(server_efficiency[assignment], energy)  # workload, scaled by η
total_energy    = idle_energy + workload_energy
```

**Step 3 — Priority-weighted congestion latency:**
```python
load_ratio  = cpu_load[assignment] / server_cpu_cap[assignment]  # per-task server load ratio
eff_latency = latency * (1 + γ * load_ratio)                     # congestion-adjusted latency
p_weights   = [1, 2, 4][priority]                                # priority weight per task
total_latency = dot(p_weights, eff_latency)
```

**Step 4 — Capacity violations:**
```python
cpu_violation = sum(max(0, cpu_load[j] - server_cpu_cap[j]) for j in servers)
mem_violation = sum(max(0, mem_load[j] - server_mem_cap[j]) for j in servers)
```

**Step 5 — Combine:**
```python
F(X) = wₑ * total_energy / E_ref
     + wₗ * total_latency / L_ref
     + λ_cpu * cpu_violation / CPU_ref
     + λ_mem * mem_violation / Mem_ref
```

---

## 8. How Each Algorithm Works (One Paragraph Each)

**Simulated Annealing (`algorithms/simulated_annealing.py`):**
Starts from the greedy FFD solution. At each of 3,000 temperature steps, it makes 50
small random changes (one of 5 move types) and accepts each one if it improves F(X),
or with probability exp(−ΔF/T) if it worsens it. T starts high (auto-calibrated to
~80% acceptance) and decreases by factor 0.995 each step. If stuck for 300 steps,
temperature is reset to 40% of T₀. Returns the best solution ever seen.

**Genetic Algorithm (`algorithms/genetic_algorithm.py`):**
Maintains 50 candidate solutions (population). Each generation: sort by F(X), copy the
2 best unchanged (elitism), then fill the rest by tournament selection of parents (pick
best of 3 random), uniform crossover (50% chance to swap each gene), and per-gene
mutation (~2% per task). Repeats for 3,000 generations. Returns the best-ever solution.

**UMDA (`algorithms/umda.py`):**
Maintains 100 candidates. Each generation: keep the best 50 (truncation selection),
count how often each task is assigned to each server among those 50, add 0.1 (Laplace
smoothing), and normalise to get a probability table P[task][server]. Then sample 99
new solutions from P (independently per task). Always inject the global best solution.
Repeats for 1,500 generations. Returns the best-ever solution.

**Branch and Bound (`algorithms/branch_and_bound.py`):**
Exact solver that provably finds the optimum — but exponential in worst case. Limited
to 60 seconds by default. Reports an optimality gap if stopped early. Used as a
reference, not for the main experiments.

**Baselines (`algorithms/baselines.py`):**
- `greedy_ffd`: sort tasks by CPU (largest first), assign to most-loaded server with capacity.
- `round_robin`: assign task i to server i % n_servers.
- `random_assignment`: assign each task to a uniform random server.
All run in milliseconds and produce a single solution (no search).

---

## 9. How to Add a New Algorithm

To add a new algorithm called "MyAlg", follow these steps:

1. **Create the algorithm file** at `algorithms/my_algorithm.py`.

2. **Write the main function** with this signature:
   ```python
   def my_algorithm(
       data: SchedulingProblemData,
       weights: ObjectiveWeights,
       # ... your hyperparameters ...
       verbose: bool = False,
   ) -> tuple[list[int], ScheduleEvaluation, MyStatistics]:
       ...
       return best_assignment, best_eval, stats
   ```

3. **Create a statistics dataclass** with at least `best_cost_history: list[float]`
   so the convergence plot works automatically.

4. **Add config entries** to `config.yaml` under `algorithms:` and update
   `tools/config_loader.py` to parse them.

5. **Register it in `main.py`**:
   - Import the function.
   - Add an entry to the `algorithm_configs` dict that maps a display name to a lambda
     that calls `run_experiment(my_algorithm_fn, data, weights, ...)`.

6. **Test it** with `uv run run.py cloud --algorithms myalg --seeds 3`.

---

## 10. Common Points of Confusion

**Q: Why does SA have 3,000 "steps" but only 150,000 evaluations?**
Each "temperature step" runs 50 inner iterations (evaluations). So:
3,000 steps × 50 evaluations/step = 150,000 total evaluations.
GA and UMDA also run for 150,000 evaluations for a fair budget comparison.

**Q: Why is the initial temperature `None` in the default config?**
`initial_temperature: null` in config.yaml tells SA to auto-estimate T₀ using
`estimate_initial_temperature()`. This samples 400 random moves and computes the T₀
that gives ~80% acceptance of **feasible-to-feasible** worsening deltas. Restricting
to feasible-to-feasible (rather than the broader "feasibility-preserving") avoids
inflating mean_delta with penalty-dominated infeasibility deltas, which previously
gave T₀ values ~20-30× too large. It adapts automatically to different objective
scales (normalised vs. raw), so you never need to tune it manually.

**Q: What is `energy_ref` and why is it `None` at first?**
The `ObjectiveWeights` dataclass is created with `energy_ref=None`. Then in `main.py`,
after the data is loaded, `compute_normalization_constants()` is called and the four
reference values are attached. This two-step setup means the weights object can be
created from config before the data is even loaded.

**Q: Why do baselines always show 0 standard deviation?**
Greedy BFD and Round-Robin are deterministic — they always produce exactly the same
solution regardless of the random seed. Random baseline does vary, but it is run
deterministically per seed so the same seed always gives the same result.

**Q: How does elitism work in UMDA?**
Unlike GA, UMDA replaces the entire population with newly sampled solutions each
generation. Without elitism, the best solution found so far could be lost if the
probability model "drifts" away from its region. Elitism explicitly inserts the
`elitism_count = 1` best-ever solutions into the new population before sampling.

---

## 10b. Reading the Results

After every run, the `results/` and `figures/` folders contain the outputs.
This section explains **what each file is for and how to read it** — start
with `summary.md`, then dig into the CSVs and plots as needed.

### Where to start

1. **`results/summary.md`** — Human-readable markdown digest of the run.
   Lists the winning algorithm, the full ranking table, an energy/latency
   decomposition for each metaheuristic, feasibility notes, and reminders
   about which auxiliary analyses were run. **Read this first.**
2. **`results/run_manifest.yaml`** — Complete parameter snapshot for the run.
   Every CLI flag, instance statistic, calibrated objective weight and
   reference value, the calibration diagnostics, and every algorithm
   hyperparameter is recorded here. Commit it alongside the results so any
   future reader can reproduce the experiment from this one file alone.
3. **`results/run_log.txt`** — Verbatim console transcript of the run. Useful
   when the verbose flag was used and you want to inspect the per-step
   acceptance rate, temperature, GA diversity, or UMDA entropy traces.

### Numerical results — per-seed CSV

`results/results_per_seed.csv` — one row per (algorithm, seed) pair.

| Column | Unit | Meaning |
|---|---|---|
| `algorithm`         | label   | Display name (e.g. `Simulated Annealing`, `Greedy BFD (baseline)`). |
| `seed`              | int     | RNG seed used for this run. Same seed + same hyperparameters = identical result. |
| `best_cost`         | F(X)    | Lowest objective value reached during the run. **This is the column to rank algorithms by.** |
| `energy_W`          | Watts   | Total energy of the best solution: `E(X) = Σ idle_j·y_j + Σ η_{x_i}·e_i`. |
| `latency_ms`        | ms      | Priority-weighted, congestion-adjusted latency `L(X) = Σ ω(p_i)·l̂_i`. |
| `cpu_violation`     | % CPU   | Sum of per-server CPU overcapacity (always `0` for feasible). |
| `mem_violation`     | MB      | Sum of per-server memory overcapacity (always `0` for feasible). |
| `n_active_servers`  | int     | How many servers actually host at least one task in the best solution. |
| `feasible`          | bool    | `True` iff both violations are zero. |
| `runtime_s`         | seconds | Wall-clock time for this specific run. |

To compare algorithms, **pivot on `algorithm` and look at the spread of
`best_cost` across seeds** — a tight distribution means the algorithm is
reliable; a wide distribution means run-to-run variance is high.

### Numerical results — summary CSV

`results/results_summary.csv` — one row per algorithm with aggregated stats.

| Column | Meaning |
|---|---|
| `best`           | Lowest `best_cost` across all seeds — the headline number for thesis tables. |
| `average`        | Mean `best_cost` across seeds — best single statistic for ranking. |
| `worst`          | Largest `best_cost` — shows worst-case behaviour. |
| `std_dev`        | Standard deviation across seeds — small = reliable, large = high variance. |
| `feasible_runs`  | How many seeds produced a feasible solution. |
| `n_runs`         | Total seeds attempted (`feasible_runs / n_runs` is the feasibility rate). |
| `avg_runtime_s`  | Mean wall-clock time per run. |

### Algorithm diagnostics CSV

`results/algorithm_diagnostics.csv` — one row per algorithm, **mean values**
across seeds. Fields that don't apply to a given algorithm are left blank
(SA does not have `mean_n_generations_completed`, UMDA does not have
`mean_sa_reheat_count`, etc.).

| Column | Algorithm(s) | Meaning |
|---|---|---|
| `mean_total_evaluations`          | SA, GA, UMDA | Mean number of objective evaluations per run. Should be ≈ 150,000 for the calibrated budget. |
| `mean_n_generations_completed`    | GA, UMDA     | Mean generations actually completed (sanity check: should equal `n_generations` from config). |
| `mean_sa_reheat_count`            | SA           | How often the adaptive reheat fired. High counts = the search got stuck repeatedly. |
| `mean_sa_final_temperature`       | SA           | T at the end of cooling. Should be near `min_temperature`. |
| `mean_sa_acceptance_rate`         | SA           | Fraction of evaluated moves accepted. Healthy is ~0.5–0.8 on average. |
| `mean_sa_feasibility_rate`        | SA           | Fraction of evaluated candidates that were feasible. |
| `mean_umda_final_model_entropy`   | UMDA         | Final Shannon entropy (bits) of the probability model. Low = converged; near `log2(n_servers)` = uniform. |
| `bb_proven_optimal`               | B&B          | `True` iff the search tree was exhausted within the time limit. |
| `bb_root_lower_bound`             | B&B          | Admissible lower bound on F* at the root. The metaheuristics' gap from this is `(best − root_lb) / root_lb`. |
| `bb_optimality_gap_pct`           | B&B          | `(best − root_lb) / root_lb × 100` — zero iff proven optimal. |
| `bb_nodes_explored`               | B&B          | Number of search-tree nodes expanded. |

### Run manifest

`results/run_manifest.yaml` is a structured YAML file with five sections:

```yaml
generated_at: 2026-05-18 22:11:23
cli: { algorithms: [SA, GA, UMDA], focus: balanced, seeds: 10, ... }
instance: { n_tasks: 50, n_servers: 10, total_cpu_demand: 2256.7, ... }
objective:
  focus_mode: balanced
  energy_weight: 1.0
  latency_weight: 1.0
  cpu_penalty: 206.5             # AUTO-CALIBRATED under normalize_method: sample
  mem_penalty: 206.5             # AUTO-CALIBRATED
  congestion_factor: 1.0
  energy_ref: 12572.2            # mean E(X) over feasible samples (Deb 2001)
  latency_ref: 29266.6           # mean L(X) over feasible samples
  cpu_ref: 2256.7                # total CPU demand
  mem_ref: 446275.0              # total memory demand
normalisation:
  normalize_objective: true
  normalize_method: sample
  n_calibration_samples: 150
  penalty_multiplier: 100.0      # Deb 2000: λ = 100 × F_max(feasible)
  calibration_seed: 0
calibration_diagnostics:
  n_attempted: 150               # how many candidate assignments were drawn
  n_feasible: 67                 # how many were feasible
  f_max_feasible: 2.065          # F_max over feasibles; λ = 100 × this
  fallback_to_worst_case: false  # true if too few feasibles → reverted to worst_case
algorithm_hyperparameters:
  sa:   { cooling_rate: 0.995, iterations_per_temperature: 50, ... }
  ga:   { population_size: 50, crossover_prob: 0.8, ... }
  umda: { population_size: 100, selection_ratio: 0.5, ... }
  bb:   { time_limit: 60.0, max_nodes: 500000 }
```

When a reviewer asks *"what value of λ_cpu did your run actually use?"* — point
them to this file. It is the single source of truth for what happened.

### Figures

| File | What to look at |
|---|---|
| `figures/convergence_all_algorithms.png` | Mean ± 1σ convergence curves on a budget-normalised x-axis (0%–100% of evaluation budget). The **shape** matters — steep early drop = fast convergence; flat plateau = stuck. |
| `figures/convergence_{sa,ga,umda}.png` | Same data, one algorithm per plot — useful when overlaid curves are hard to read. |
| `figures/algorithm_comparison_bar.png` | Horizontal grouped bars of Best / Avg / Worst F(X) for every algorithm. Y-axis is **not** zoomed, so baselines and metaheuristics are on the same scale. |
| `figures/metaheuristics_comparison.png` | Two-panel view focused on SA/GA/UMDA: zoomed objective bars (top) and energy/latency decomposition (bottom). Use this for thesis discussion. |
| `figures/boxplot_comparison.png` | Box plots with individual seed dots overlaid. Shows variance directly. |
| `figures/sa_sensitivity.png` (with `--sensitivity`) | Mean F(X) ± std across the swept range for T₀ and cooling rate. Flat = robust; U-shaped = sensitive. |
| `figures/ga_sensitivity.png` (with `--sensitivity`) | Same for GA population size and crossover prob. |
| `figures/umda_sensitivity.png` (with `--sensitivity`) | Same for UMDA population size and selection ratio. |
| `figures/scalability_horizontal.png` (with `--scalability`) | Runtime and quality vs n_tasks (log x). |
| `figures/scalability_vertical.png` (with `--scalability`) | Quality and feasibility % vs n_servers (inverted x — left=loose, right=tight). |
| `figures/optimality_gap.png` (with `--scalability`) | Each algorithm's gap from the B&B reference on the 20-task instance. (Separate quality benchmark, not a scalability axis.) |

### Scalability + quality CSVs (only with `--scalability`)

| File | Columns |
|---|---|
| `results/scalability_horizontal.csv` | `algorithm, n_tasks, n_servers, avg_runtime_s, avg_cost, improvement_over_greedy_pct` |
| `results/scalability_vertical.csv`   | `algorithm, n_servers, cpu_util_pct, avg_runtime_s, avg_cost, improvement_over_greedy_pct, feasible_pct` |
| `results/optimality_gap.csv`         | `algorithm, best_cost, avg_cost, gap_vs_bb_pct, avg_runtime_s, feasible_runs, n_runs` — runs at one fixed small size; measures absolute gap from the B&B exact reference, **not** a scalability axis. |

### Tuning CSVs (only with `--tune`)

| File | Columns |
|---|---|
| `results/tuning_sa.csv`   | `cooling_rate, iterations_per_temperature, mean_F, std_F, mean_time_s, feasible_pct` — every combination, ordered as it ran. |
| `results/tuning_ga.csv`   | `population_size, crossover_prob, mean_F, std_F, mean_time_s, feasible_pct`. |
| `results/tuning_umda.csv` | `population_size, selection_ratio, mean_F, std_F, mean_time_s, feasible_pct`. |
| `results/tuning_summary.md` | Recommended values per algorithm. Copy these into `config.yaml` &rarr; `algorithms:` section, then re-run **without** `--tune`. |

---

## 10c. Thesis-Defense Q&A

A consolidated set of answers to the kinds of questions an examiner is likely to
ask about this code. Each answer is short, code-anchored, and cites the relevant
file or thesis section. Use this as the reference sheet when reviewing your
implementation before the defence.

---

### Result-interpretation questions

**Q: What does the Wilcoxon signed-rank significance test in the results table mean?**
The Wilcoxon signed-rank test is a *paired* non-parametric test: for two algorithms
A and B run on the same `n_seeds` random seeds, it compares the differences
(F_A(seed_i) − F_B(seed_i)) and asks "is the median difference statistically
distinguishable from zero?" Non-parametric means it does not assume the
differences are normally distributed — which matters here because objective
values can be very skewed (most seeds cluster tightly; one outlier seed pulls
the mean). The output is a p-value: low p (< 0.05) means the two algorithms
genuinely perform differently; high p means the apparent difference could be
random noise. The code uses `scipy.stats.wilcoxon` in
[`tools/plot.py`](tools/plot.py) (`print_significance_table`). Star convention:
*** p<0.001, ** p<0.01, * p<0.05, ns = not significant.

**Q: What do the columns in the multi-seed comparison table mean?**
| Column | Meaning |
|---|---|
| **Best**     | Lowest F(X) achieved across the `n_seeds` runs. Single best outcome. |
| **Average**  | Mean F(X) across the `n_seeds` runs. The headline number for ranking. |
| **Worst**    | Highest F(X) across the runs. Shows the algorithm's bad-case behaviour. |
| **Std Dev**  | Population standard deviation of best-F values across seeds. Measures *consistency*. Low = reliable; high = lucky/unlucky runs. |
| **Feasible** | `<n_feasible>/<n_seeds>`. How many runs produced a fully feasible solution (cpu_violation == mem_violation == 0). |
| **Avg Time** | Mean wall-clock seconds per single run. Used in the scalability axis. |

**Q: In the "Metaheuristic Ranking" output, the Avg Time differs noticeably between algorithms even though their evaluation budgets are equal. Why?**
The 150 K evaluation budget is fixed, but each algorithm has different per-evaluation overhead. SA evaluates one candidate at a time inside a tight loop (~60 µs/eval). GA recombines a pair of parents into two children and evaluates both (~150 µs/eval including selection). UMDA samples from a categorical model in a vectorised numpy step, which is fast in aggregate but pays for the `np.bincount` model-build each generation. So at equal evaluation budget, GA tends to take longest, SA shortest, and UMDA in the middle. Average time is a stable property of the algorithm-instance pair (not a seed artefact) — re-running with different seeds shifts it by < 5 %.

**Q: What is the "energy vs latency decomposition of F(X)" reported per algorithm?**
F(X) = w_e·Ẽ + w_l·L̃ + capacity penalties. For a *feasible* solution the
capacity terms are zero, so F(X) = w_e·Ẽ + w_l·L̃ exactly. The decomposition
reports each term's *share* of the total:
- **E-contrib %** = w_e·Ẽ / (w_e·Ẽ + w_l·L̃) × 100
- **L-contrib %** = w_l·L̃ / (w_e·Ẽ + w_l·L̃) × 100
together summing to 100 %. Interpretation: a 75 % L-contrib means three quarters
of the cost comes from priority-weighted latency; the algorithm spent its
improvement budget mostly fighting latency, not energy. In *balanced* mode
(w_e=w_l=1) an even split (~50/50) suggests the trade-off was actually balanced;
a skewed split suggests one term dominates the realised objective in this
instance.

**Q: What does "Active servers: 5/10" mean?**
An *active* server is one that hosts at least one task (the indicator y_j = 1
in thesis Section 3.1.5). Servers with no tasks are inactive (y_j = 0) and pay
no idle-power cost. "5/10" means 5 of the 10 servers are switched on, 5 are
idle-off. This is the consolidation metric: lower = better energy efficiency
but higher congestion latency, the central trade-off in the problem.

**Q: Are the "Total CPU demand / Total memory demand / Total CPU capacity / Total memory capacity" numbers constant across runs?**
**Yes, for a fixed problem instance.** They are properties of the *input data*
and the *server pool*, not of any algorithm. Total demand = Σᵢ cᵢ (or Σᵢ mᵢ);
total capacity = Σⱼ Cⱼ (or Σⱼ Mⱼ). The 50 tasks read from the dataset and the
10 synthesised servers are identical across every run, so these four numbers
print the same value every time. They change only when you (a) change `n_tasks`
in the config, (b) run scalability with synthetic tasks, or (c) edit
[`tools/data_loader.py`](tools/data_loader.py).

---

### Setup / parameter questions

**Q: Why 10 seeds?**
Statistical convention for stochastic-algorithm benchmarking. With 10 seeds the
Wilcoxon signed-rank test reaches p < 0.01 when one algorithm dominates the
other on ≥ 9 of 10 seeds — strong enough to support thesis claims. Fewer seeds
(3–5) is acceptable for *exploratory* runs (which is why `--scalability` uses
3 seeds per scale point — there's already replication across scales). Set in
[`config.yaml`](config.yaml) → `experiment.n_seeds`; override with `--seeds N`.

**Q: Why is the capacity penalty coefficient λ = 10 in the (normalised) balanced mode?**
This is the **Deb (2000) parameter-less penalty rule**: λ = penalty_multiplier ×
F_max(feasible), where penalty_multiplier = 100 and F_max(feasible) is the
maximum normalised objective observed across the calibration sample. Once
weights and refs are calibrated, a typical feasible F(X) ≈ 1.0; a 10 % capacity
violation contributes 10 × 0.1 = 1.0 to F(X) — equal to the full feasible cost
range. Any non-trivial violation therefore dominates F(X), guaranteeing that
*any* feasible solution beats *any* infeasible one with a > 1 % violation. The
calibration is automatic when `normalize_method: sample` is set; for the legacy
`worst_case` method, λ=10 is the manually chosen value justified in [`config.yaml`](config.yaml).

**Q: What are the normalisation refs E_ref / L_ref / CPU_ref / Mem_ref and what are they used for?**
They are *denominators* that scale each F(X) term to a dimensionless range
roughly in [0, 1]. Without them, energy (Watts ≈ 10³) would numerically swamp
latency (ms ≈ 10²) regardless of the weights, so w_e = w_l = 1 would not
actually mean equal preference. With normalisation, every term has the same
scale and the weights *do* mean what they say.
- `E_ref` = expected energy of a feasible solution (sample-based, Deb 2001).
- `L_ref` = expected priority-weighted latency of a feasible solution.
- `CPU_ref` = total CPU demand Σᵢ cᵢ — used in the CPU-violation penalty term.
- `Mem_ref` = total memory demand Σᵢ mᵢ — used in the memory-violation penalty term.

Computed once per instance by `compute_sample_normalization` (or
`compute_normalization_constants` for the legacy worst-case method) in
[`tools/objective.py`](tools/objective.py) and stored on the
`ObjectiveWeights` dataclass before any algorithm runs.

**Q: Why does GA run for 3,000 generations and UMDA for 1,500?**
Equal evaluation budget. The total budget is 150,000 calls to `evaluate_schedule`,
chosen because SA's natural budget (3,000 temperature steps × 50 inner iterations
= 150,000) is a sensible reference. To match:
- GA evaluates `population_size × n_generations = 50 × 3000 = 150,000` candidates.
- UMDA evaluates `population_size × n_generations = 100 × 1500 = 150,000` (plus
  the initial population, which is small compared to 150 K).
This equal-budget protocol means any quality difference between the three
algorithms is *not* due to one having more compute time — it is genuinely about
search strategy.

**Q: Why tournament selection in GA, not roulette-wheel / fitness-proportionate?**
Tournament selection is **scale-invariant**: it only ranks individuals, so it
doesn't matter that the objective F(X) can take very different magnitudes
across instances (sometimes ≈ 1 with normalisation, sometimes ≈ 10⁵ raw).
Fitness-proportionate selection would require transforming F(X) into a
non-negative "fitness" first (since we minimise), and that transformation
introduces its own scaling artefacts. Tournament size k = 3 gives moderate
selection pressure — De Jong (1975) / Eiben & Smith (2015) standard.

---

### Algorithm-specific questions

**Q: Why does `main.py` run a single SA diagnostic *before* the multi-seed experiments?**
Historical / pedagogical: it gives the reader a quick picture of what one SA
run looks like — solution quality, acceptance statistics, reheat count, and an
ASCII bar chart of tasks per server — before scrolling into the bulk multi-seed
output. SA is **not** algorithmically special; the diagnostic could equally
well be run on GA or UMDA. If you want to skip it, comment out
`_single_run_diagnostics(...)` in [`main.py`](main.py). For the thesis defence
you can state that the diagnostic block is a UX/reporting feature, not part of
the experimental protocol.

**Q: What is the Metropolis acceptance criterion in SA?**
Given the current solution with cost F_current and a candidate move with cost
F_candidate, let Δ = F_candidate − F_current.
- If Δ < 0 (improvement): always accept the move.
- If Δ ≥ 0 (worsening): accept with probability `exp(−Δ / T)` where T is the
  current temperature; otherwise reject.

This is the rule of Metropolis et al. (1953), adapted to optimisation by
Kirkpatrick et al. (1983). High T → most worsening moves accepted (explores);
low T → almost no worsening accepted (exploits). Implemented at
[`simulated_annealing.py:178`](algorithms/simulated_annealing.py#L178).

**Q: What is Greedy BFD (Best-Fit Decreasing), and what are "biggest" and "smallest" jobs?**
The greedy constructor [`build_greedy_assignment`](tools/initial_solution.py):
1. **Sort all tasks by CPU demand cᵢ in *descending* order.** "Biggest job"
   means highest cᵢ (most CPU-hungry); "smallest" means lowest cᵢ.
2. Place each task in order onto the **most-loaded server that still has
   capacity** for both its CPU and memory needs (this is the "best-fit" part).
3. If no server fits, fall back to the least-loaded server, accepting a soft
   infeasibility that the metaheuristic can repair later.

This is *Best-Fit Decreasing*, not classical First-Fit Decreasing. BFD packs
tasks tighter than FFD, leaving fewer servers active and giving the
metaheuristic a strong starting point. Function name retained as
`build_greedy_assignment` for backwards compatibility; the user-facing label is
"Greedy BFD".

**Q: What are the other bin-packing greedy variants?**
| Variant | Rule | Trade-off |
|---|---|---|
| **First-Fit Decreasing (FFD)** | Place on the first (lowest-index) server with capacity | Fastest; ignores load distribution |
| **Best-Fit Decreasing (BFD)** ← *used here* | Place on the most-loaded server with capacity | Tighter packing; better consolidation |
| **Worst-Fit Decreasing (WFD)** | Place on the least-loaded server with capacity | Spreads load; better latency but more active servers |
| **Next-Fit Decreasing (NFD)** | Always place on the current "open" server, opening a new one only when full | Simpler but typically wasteful |

BFD was chosen because the thesis objective rewards consolidation (fewer
active servers → lower idle energy). WFD would be a more natural starting
point for a latency-only objective.

**Q: Did Branch & Bound actually find the optimal solution? When does it stop?**
It stops at the **first** of these conditions:
1. The search tree is exhausted → returns the **provably optimal** solution
   with `proven_optimal=True` and `optimality_gap = 0`.
2. `time_limit = 60s` (in `config.yaml`) is reached → returns the **best
   feasible solution found so far** plus an optimality gap = (best_found −
   lower_bound) / |lower_bound|.
3. `max_nodes = 500_000` nodes have been expanded → same as case 2.

In your previous run B&B printed `nodes=116,573 root_lb=0.5865 best=0.7576
gap=29.2% proven_optimal=False`. That means: B&B explored 116K nodes in 61s,
found a feasible solution worth F=0.7576 (matching greedy), but its
lower-bound estimate at the root of the tree was 0.5865. The 29.2 % gap means
*the optimum could in principle be as low as 0.5865*, but B&B couldn't prove
that within the time limit. **B&B did not find the optimum on the 50-task
instance — that instance is too large for exact methods.** This is *exactly*
why B&B is only used as a reference on the 20-task optimality-gap benchmark,
where it typically runs to provable optimality.

**Q: How does UMDA "start with 100 candidates"?**
[`umda.py`](algorithms/umda.py) initialises the population (size 100) as
follows:
1. 1 candidate from Greedy BFD (a strong starting point).
2. ~49 perturbed copies of the greedy assignment: each task is independently
   reassigned to a uniformly random server with probability 10 %. This gives
   the probability model meaningful local variation to learn from.
3. ~50 fully random assignments. These provide exploration breadth.

Pure-random initialisation (100 random assignments) was previously used but
was changed because at large n the random assignments are heavily infeasible
and dominate the model unhelpfully — see Section 11b in this guide.

**Q: What does "sampling from the probability table" mean in UMDA?**
The probability table is `P[i][j] = probability that task i goes on server j`,
fitted from the top-50 % of the population each generation. To sample one new
candidate solution:
- For each task i (independently), draw a server j from the categorical
  distribution `P[i][·]`.
- Concatenate into an assignment vector of length n_tasks.

This is implemented vectorised: 99 new candidates × 50 tasks = 4,950 draws are
performed in a single numpy `np.argmax(cdf >= uniform_samples)` call — see
[`umda.py:_sample_population`](algorithms/umda.py).

**Q: Why does only SA use `neighborhoods.py`? How does GA make mutations? Can multiple mutations happen at once?**
- **SA** uses `generate_neighbor()` to make one small change to the current
  solution per step (one of 5 move operators chosen uniformly at random:
  reassign, swap, rescue, consolidate, spread).
- **GA** uses **per-gene mutation**: for *each task independently*, with
  probability `p_mut = 1/n_tasks ≈ 0.02`, that task is reassigned to a
  uniformly random server. So GA *can* mutate multiple tasks per offspring
  (expected: exactly 1 task per offspring on average, but could be 0, 1, 2,
  3…). See [`genetic_algorithm.py:_mutate`](algorithms/genetic_algorithm.py).
- **UMDA** has no explicit mutation operator. Diversity is maintained by
  Laplace smoothing on the probability model (`α = 0.1`), which keeps every
  P[i][j] > 0 so no server is ever permanently excluded.

This is a deliberate design difference between the algorithms — SA's
neighbourhood operators are problem-specific moves, GA's mutation is generic
per-gene resampling, UMDA's "mutation" is structural via the smoothed model.

---

### Code-structure / workflow questions

**Q: In what order should I read the files to understand the code?**
Already covered in Section 3 above. Short version:
1. `config.yaml` (parameters)
2. `tools/data_loader.py` (input data)
3. `tools/objective.py` (F(X) — the heart of everything)
4. `tools/initial_solution.py` (greedy BFD constructor)
5. `algorithms/simulated_annealing.py`, then `genetic_algorithm.py`, then `umda.py`
6. `algorithms/baselines.py` (one-shot constructors)
7. `tools/experiment.py` (multi-seed harness)
8. `main.py` (orchestrator)

**Q: Re-running all three baselines (Greedy / Round-Robin / Random) every time wastes time. Can I skip them?**
Yes, two options:
- **Permanent**: in `main.py` `--algorithms` argument, list only the
  metaheuristics: `--algorithms SA GA UMDA BB`.
- **Convenience**: Round-Robin already runs only 1 seed (it's deterministic);
  Random is the only stochastic baseline. To skip Random, use
  `--algorithms SA GA UMDA BB greedy` (keeps Greedy as the comparison baseline
  for `vs_greedy` improvement percentages).

Greedy BFD should always be kept because the "improvement over greedy"
percentage is what the thesis claims hinge on.

---

## 11. Code Correctness — Sanity Test Suite

A test suite in [`tests/`](tests/) empirically verifies the implementation.
Run from the `Cloud_scheduling/` directory:

```bash
uv run --with numpy --with pandas --with pyyaml python tests/test_objective.py
uv run --with numpy --with pandas --with pyyaml python tests/test_algorithms.py
```

**`tests/test_objective.py` (8 tests)** — Hand-built 4-task / 3-server instance
with known F(X) values. Tests:
- Energy formula (idle + workload·η)
- Latency with congestion factor γ (γ=0, γ=1, γ=2)
- Priority weights ω(Low/Med/High) = (1, 2, 4)
- Capacity violation detection and penalty
- Normalisation constants E_ref, L_ref, CPU_ref, Mem_ref
- Normalised feasible terms lie in [0, 1]
- Active-server indicator y_j correctly applied
- Empty servers contribute zero idle energy

**`tests/test_algorithms.py` (8 tests)** — 20-task synthetic instance. Tests:
- Greedy and Round-Robin baselines are deterministic
- SA, GA, UMDA each beat greedy on this small instance (6%, 8%, 4-5% improvement)
- SA reproducibility with fixed seed
- Evaluation budgets match the configured values
- Greedy baseline implements **Best-Fit** (not First-Fit) decreasing

**Status:** all 16 tests pass against the current implementation, providing
empirical evidence that the code matches the thesis formula and that the
algorithms function correctly under sufficient-budget conditions.
The 0%-improvement-at-scale observation therefore reflects budget/scale
ratio limits, not implementation bugs.

---

## 11b. Four Improvements Applied (May 2026)

Following a thesis-defensibility audit, these four improvements were made.
All preserve backward compatibility and pass the test suite.

| # | Issue | Fix | File |
|---|---|---|---|
| 1 | Older versions labelled the construction baseline "Greedy FFD" although the implementation is **Best-Fit Decreasing (BFD)** | User-facing labels are now **"Greedy BFD"** everywhere; the legacy function name `greedy_ffd_baseline` is kept for backwards-compatible imports | [`tools/initial_solution.py`](tools/initial_solution.py), [`algorithms/baselines.py`](algorithms/baselines.py) |
| 2 | SA T₀ inflated by penalty-dominated samples (the calibration probe drifted into the infeasible region, where worsening deltas are dominated by lambda*violation rather than the objective gradient) — caused SA to random-walk away from greedy and miss improvements at n>=200 | T₀ estimation now filters to **feasible-to-feasible** worsening deltas and prevents the walk-forward from drifting into infeasibility | [`algorithms/simulated_annealing.py`](algorithms/simulated_annealing.py) `estimate_initial_temperature()` |
| 3 | UMDA model couldn't learn from mostly-random pop at large n | Initial pop is now **1 greedy + ~half perturbed-greedy + ~half random** | [`algorithms/umda.py`](algorithms/umda.py) |
| 4 | Greedy/FFD naming inconsistency in docs | README, README_kids, this guide all updated | docs |

**Thesis discussion points enabled by these fixes:**
- (#1) The baseline is correctly named — credible bin-packing comparison.
- (#2) SA's T₀ is theoretically motivated: calibrated to the *useful*-move scale,
  not the *penalty* scale. Cite as a methodological improvement.
- (#3) UMDA's information-rich initialisation is a known EDA technique
  (Larrañaga & Lozano 2002). Defensible as a design choice.

---

## 12. Known Behaviour to Be Aware Of

**SA/UMDA show near-zero improvement over Greedy at n ≥ 200 tasks (scalability analysis):**
This is not a bug. The evaluation budget (150,000 calls) was designed for n = 50 tasks.
At n = 200, the search space is exponentially larger but the budget stays fixed. SA
initialises from the greedy solution and cannot escape it within budget. UMDA's probability
model has n × m = 8,000 parameters at n = 200 but only ~50 training samples — too sparse.
GA maintains improvement because crossover between 49 diverse random solutions creates
useful offspring without depending on a single initialisation or a learned model.
This is a valid thesis finding: *GA scales better at fixed budget due to population diversity.*

**Round-Robin always shows 0 standard deviation and runs only once:**
Round-Robin is completely deterministic — the assignment `task_i → server (i % m)` is
the same regardless of random seed. Running 10 seeds would waste time producing identical
results. The code runs it once (`seeds=[0]`) and reports those results for all comparisons.

**UMDA sampling was historically slow (O(n_tasks × pop_size) Python calls):**
The old code sampled one server at a time in a Python loop. The current code in
`_sample_population()` draws the entire population in one batched numpy call using
vectorised inverse-CDF sampling. This is what makes UMDA fast at large n.

---

## 13. Thesis Cross-Reference

Use this table to locate any specific formula or concept from the thesis in the code.

| Thesis element | File | Function / line | Notes |
|---|---|---|---|
| **F(X) = wₑÃ+wₗL̃+penalties** | `tools/objective.py` | `evaluate_schedule()` lines 248–259 | The four terms; refs divide each term |
| **E(X) = Σ idle·y + Σ η·e** | `tools/objective.py` | lines 218–221 | `idle_energy + workload_energy` |
| **yⱼ = active-server indicator** | `tools/objective.py` | line 212 | `np.bincount(a) > 0` |
| **U^cpu_j = Σᵢ cᵢ·𝟙[xᵢ=j]** | `tools/objective.py` | line 209 | `np.bincount(a, weights=data.cpu)` |
| **l̂ᵢ = lᵢ(1+γ·U/C)** | `tools/objective.py` | lines 229–230 | congestion-adjusted latency per task |
| **ω(p): Low=1, Med=2, High=4** | `tools/objective.py` | line 23 | `_PRIORITY_WEIGHTS = [1, 2, 4]` |
| **E_ref worst-case energy** | `tools/objective.py` | `compute_normalization_constants()` line 173 | `sum(idle)+max(η)*sum(energy)` |
| **L_ref worst-case latency** | `tools/objective.py` | lines 176–177 | all tasks on smallest server at max congestion |
| **SA: exp(−ΔF/T) Metropolis** | `algorithms/simulated_annealing.py` | line 178 | `math.exp(-delta / temperature)` |
| **SA T₀ auto-estimation** | `algorithms/simulated_annealing.py` | `estimate_initial_temperature()` | solves `T₀ = -mean_Δ / ln(0.80)` |
| **SA geometric cooling T·α** | `algorithms/simulated_annealing.py` | line 192 | `temperature *= cooling_rate` |
| **SA reheating mechanism** | `algorithms/simulated_annealing.py` | lines 204–207 | triggered after `reheat_patience` steps |
| **GA tournament selection k=3** | `algorithms/genetic_algorithm.py` | `_tournament_select()` | sample k, return best |
| **GA uniform crossover** | `algorithms/genetic_algorithm.py` | `_uniform_crossover()` | per-gene Bernoulli(0.5) swap |
| **GA per-gene mutation** | `algorithms/genetic_algorithm.py` | `_mutate()` | p_mut = 1/n_tasks per gene |
| **UMDA P[i][j] Laplace-MLE** | `algorithms/umda.py` | `_build_probability_model()` | `(count+α)/(n_sel+m·α)` |
| **UMDA vectorised sampling** | `algorithms/umda.py` | `_sample_population()` | inverse-CDF via numpy argmax |
| **UMDA entropy H = −ΣP log₂P** | `algorithms/umda.py` | `_model_entropy()` | mean Shannon entropy across tasks |
| **Greedy BFD construction** | `tools/initial_solution.py` | `build_greedy_assignment()` | sort by CPU desc, assign to best-fit server |
| **5 SA neighbourhood operators** | `tools/neighborhoods.py` | `generate_neighbor()` | reassign, swap, rescue, consolidate, spread |
| **Objective normalisation toggle** | `config.yaml` | `experiment.normalize_objective` | `true` = dimensionless [0,1] terms |
| **λ_cpu, λ_mem penalty coefficients** | `config.yaml` | `objective.balanced.cpu_penalty` | 10.0 in normalised regime |
| **Scalability: fixed-budget drop** | `main.py` | `_print_scalability_note()` | SA/UMDA near-greedy at n≥200 — expected |

---

## 14. Glossary


| Term | Definition |
|---|---|
| **Assignment vector** | A list of n integers where index i gives the server of task i. |
| **Evaluation budget** | Total number of times evaluate_schedule() is called per algorithm run. |
| **F(X)** | The objective value — the single number being minimised. |
| **Feasible** | A solution with no capacity violations (cpu_violation = mem_violation = 0). |
| **FFD** | First-Fit Decreasing — a greedy bin-packing heuristic used as the starting point. |
| **FocusMode** | Named weight preset: BALANCED (equal trade-off), PERFORMANCE (latency-first), ECO (energy-first). |
| **Laplace smoothing** | Adding α = 0.1 to all counts in UMDA's model so no probability is exactly zero. |
| **Normalisation** | Dividing each F(X) term by a worst-case reference so all terms are in [0, 1]. |
| **Priority weight ω** | Multiplier applied to latency: ω(Low)=1, ω(Medium)=2, ω(High)=4. |
| **Seed** | An integer passed to `random.seed()` to make a run reproducible. |
| **Soft penalty** | A penalty term that discourages constraint violations but does not forbid them. |
| **Tournament selection** | Randomly pick k individuals, keep the best one. Used in GA. |
| **Truncation selection** | Keep the best top-k fraction of the population. Used in UMDA. |
| **xᵢⱼ** | Thesis notation: xᵢⱼ = 1 if task i is on server j. Equivalent to assignment[i] == j. |
| **yⱼ(X)** | Thesis notation: yⱼ = 1 if server j has at least one task. Equivalent to bincount(assignment)[j] > 0. |
