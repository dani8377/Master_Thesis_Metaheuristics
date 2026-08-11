# Master's Thesis — Metaheuristics for Combinatorial Optimisation

Python code for the Master's thesis _"Evaluation of Metaheuristic Algorithms for
Energy Optimisation in Scheduling and Routing"_ (DTU Compute).

Two combinatorial optimisation problems are studied, each with its own solution
representation, objective function and set of algorithms:

| | Problem | Directory | Algorithms compared |
|---|---|---|---|
| **1** | Cloud resource scheduling (50 tasks → 10 servers) | [`Cloud_scheduling/`](Cloud_scheduling/) | SA, GA, UMDA, Branch & Bound, 3 baselines |
| **2** | Single-vehicle electric-vehicle routing (75 customers, 30 charging stations) | [`EV_routing/`](EV_routing/) | SA, GA, MA, ACO, greedy baseline, plus an ACO→SA hybrid as a follow-up |

The two modules are independent in their problem formulations but follow the same
experimental protocol: a fixed evaluation budget of 150,000 objective calls per
run, multi-seed repetition, hyperparameters frozen after a separate tuning stage,
and every result written to disk together with a manifest of the parameters that
produced it.

The written thesis lives in [`report/`](report/), a git submodule tracking the
Overleaf project. If it is empty after cloning, run `git submodule update --init`.

---

## Quick start

Everything runs from the **project root**. The project uses
[uv](https://github.com/astral-sh/uv), so there is no virtual environment to
create and no `pip install` step: `uv run` fetches and caches the dependencies
on first use.

```bash
# Both problems with their default settings
uv run run.py

# Cloud scheduling only (all algorithms, balanced focus, 20 seeds)
uv run run.py cloud

# EV routing only (all algorithms, 10 seeds)
uv run run.py ev

# Unit tests for the cloud module (33 tests)
cd Cloud_scheduling && uv run --with numpy --with pandas --with matplotlib \
    --with pyyaml --with scipy --with pytest python -m pytest tests -q
```

`run.py cloud` forwards any extra flags to `Cloud_scheduling/main.py`. The EV
module has a different flag set, so its options are passed by calling its entry
point directly:

```bash
PYTHONPATH=EV_routing python EV_routing/main.py --seeds 5 --mode eco
```

A `Makefile` with the same two targets (`make cloud`, `make ev`) is provided for
convenience.

Rough runtimes from the committed runs: about 3 to 4 minutes for a full cloud run
with 20 seeds (of which 60 s is the Branch & Bound time limit), and about 20
minutes for a full EV run with 10 seeds, most of it ACO. The optional
`--sensitivity` and `--scalability` sweeps add considerably more.

---

## Repository layout

```
Master_Thesis_Metaheuristics/
│
├── run.py                              ← launcher for both problems
├── Makefile                            ← make cloud / make ev
├── report/                             ← thesis LaTeX (git submodule → Overleaf)
│
├── Cloud_scheduling/                   ← Problem 1
│   ├── main.py                         ← entry point, experiment orchestration
│   ├── config.yaml                     ← every hyperparameter and experiment setting
│   ├── visualize.py                    ← server-rack allocation figures and GIFs
│   ├── umda_drift_test.py              ← genetic-drift follow-up experiment
│   ├── datasets/
│   │   ├── cloud_resource_allocation_dataset.csv
│   │   └── raw/                        ← original download (.xlsx)
│   ├── results/<focus>/                ← CSVs, run_manifest.yaml, run_log.txt, summary.md
│   ├── figures/<focus>/                ← PNG/PDF figures, GIF animations
│   ├── tests/                          ← 33 unit tests (objective, algorithms, correctness)
│   ├── algorithms/
│   │   ├── simulated_annealing.py      ← auto-T₀, geometric cooling, reheating
│   │   ├── genetic_algorithm.py        ← tournament selection, uniform crossover, elitism
│   │   ├── umda.py                     ← EDA with Laplace smoothing and entropy tracking
│   │   ├── branch_and_bound.py         ← time-limited exact reference
│   │   └── baselines.py                ← greedy BFD, round-robin, random
│   └── tools/
│       ├── config_loader.py            ← config.yaml → typed dataclasses
│       ├── data_loader.py              ← task CSV + synthetic server pool
│       ├── objective.py                ← FocusMode, ObjectiveWeights, evaluate_schedule()
│       ├── feasibility.py              ← assignment-vector validation
│       ├── initial_solution.py         ← greedy BFD / round-robin / random constructors
│       ├── neighborhoods.py            ← 5 SA move operators
│       ├── experiment.py               ← multi-seed harness
│       └── plot.py                     ← convergence / bar / box plots, CSV export
│
└── EV_routing/                         ← Problem 2
    ├── main.py                         ← entry point, main experiment and sweeps
    ├── datasets/                       ← raw charging-station and San Francisco node data
    ├── instances/                      ← frozen instances sf_10 … sf_500 (matrices, maps)
    ├── results/
    │   ├── sf_75/                      ← main instance: CSVs, params.json, weights.json, figures/
    │   ├── sf_75_eco/, sf_75_time/     ← focus-mode reruns
    │   ├── sf_10/                      ← exact A* optimum and true optimality gaps
    │   ├── scalability/                ← standalone size sweep sf_25 … sf_500
    │   └── side_experiments/           ← hybrid, eco-heuristic, candidate-list studies
    ├── scripts/
    │   ├── build_instance.py           ← OSRM + SRTM instance construction
    │   ├── calibrate_weights.py        ← sample-based weight calibration
    │   ├── tune.py                     ← random-search hyperparameter tuning
    │   ├── sensitivity_analysis.py     ← parameter influence from the tuning trials
    │   ├── scalability_analysis.py     ← size sweep across all instances
    │   ├── exact_benchmark.py          ← exact A* optimum on sf_10
    │   ├── side_experiments.py         ← hybrid / eco-heuristic / candidate-list runs
    │   ├── make_route_map.py           ← greedy vs SA route map figure
    │   ├── make_cover_graphic.py       ← thesis title-page graphic
    │   └── regen_*.py                  ← redraw figures from saved CSVs
    ├── algorithms/
    │   ├── greedy.py                   ← nearest-neighbour baseline
    │   ├── simulated_annealing.py      ← SA with reheating and optional warm start
    │   ├── genetic_algorithm.py        ← GA, and MA when local_search_iters > 0
    │   ├── ant_colony.py               ← Max–Min Ant System
    │   └── hybrid_aco_sa.py            ← ACO construction handed to SA as a warm start
    └── tools/
        ├── data_loader.py              ← instance loading, energy-matrix construction
        ├── battery.py                  ← EVParameters
        ├── objective.py                ← evaluate_route()
        ├── feasibility.py              ← structural and battery feasibility
        ├── initial_solution.py         ← EV-feasible construction and repair
        ├── neighborhoods.py            ← 8 move operators
        ├── experiment.py               ← multi-seed harness
        ├── statistics.py               ← Wilcoxon signed-rank tests, Holm correction
        ├── tuning.py                   ← grid and random search
        ├── compare.py                  ← controlled comparison driver
        ├── plot.py                     ← all EV figures
        ├── distance.py                 ← distance providers and matrix builders
        └── node_utils.py
```

---

# 1. Cloud Resource Scheduling

## Problem statement

A batch of **n = 50** independent tasks must be assigned to **m = 10**
heterogeneous servers. Each server has a fixed CPU and memory capacity, an idle
power draw and an efficiency factor. Each task has a CPU footprint, a memory
footprint, an energy draw, a base service latency and a priority class
(Low / Medium / High).

The optimiser decides which server each task runs on.

**Solution representation:** an integer vector **X** = [x₁, …, xₙ] with
xᵢ ∈ {0, …, m−1}. This is the binary assignment matrix xᵢⱼ of the thesis
formulation with the one-hot constraint Σⱼ xᵢⱼ = 1 built into the encoding.

**Dataset:** `datasets/cloud_resource_allocation_dataset.csv`, 6,345 task
records, of which 50 are used per run. The 10-server pool is defined in
`tools/data_loader.py` as instance parameters of the experiment.

## Objective function

```
F(X) = wₑ · E(X)/E_ref + wₗ · L(X)/L_ref
     + λ_cpu · Σⱼ max(0, U^cpu_j − Cⱼ) / CPU_ref
     + λ_mem · Σⱼ max(0, U^mem_j − Mⱼ) / Mem_ref
```

All four terms are dimensionless after normalisation, so wₑ and wₗ express a
preference ratio rather than a unit conversion.

**Energy.**

```
E(X) = Σⱼ e^idle_j · yⱼ(X)  +  Σᵢ η_{xᵢ} · eᵢ
```

| Symbol | Meaning |
|---|---|
| `e^idle_j` | idle power of server j (W), drawn whenever the server is active |
| `yⱼ(X)` | 1 if at least one task is assigned to server j, else 0 |
| `η_j` | efficiency factor of server j (η > 1 means it burns more per unit of work) |
| `eᵢ` | workload energy of task i (W) |

The first sum is the cost of keeping a server switched on, the second is the work
itself. Consolidating onto fewer servers saves idle power but can raise workload
energy if the surviving servers are inefficient. That tension is the core
trade-off of the problem.

**Priority-weighted congestion latency.**

```
L(X)     = Σᵢ ω(pᵢ) · l̂ᵢ(X)
l̂ᵢ(X)   = lᵢ · (1 + γ · U^cpu_{xᵢ} / C_{xᵢ})
U^cpu_j  = Σᵢ cᵢ · 1[xᵢ = j]
```

with ω(Low) = 1, ω(Medium) = 2, ω(High) = 4. Each task's effective latency grows
linearly with the CPU utilisation of its server, and high-priority tasks count
four times as much, so the optimiser is pushed to place them on lightly loaded
servers.

**Capacity penalties.** CPU and memory capacities are soft constraints. The
search may enter infeasible regions temporarily, which keeps the landscape
connected. A solution counts as feasible only when both violation terms are
exactly zero.

## Normalisation and penalty calibration

Set by `config.yaml → experiment.normalize_method`.

### `sample` (default)

Sample-based normalisation following Deb (2001), with penalty weights from the
parameter-less rule of Deb (2000):

1. **Draw a calibration pool** of `n_calibration_samples = 150` assignments from
   a deliberate mix, so that enough of them land in the feasible region: one
   greedy BFD solution, about 40 % greedy with 10 % of genes reassigned, about
   30 % greedy with 30 % reassigned, and about 30 % uniformly random
   (`tools/objective.py` → `_sample_calibration_pool()`).
2. **Keep the feasible candidates.** The count is recorded in
   `run_manifest.yaml → calibration_diagnostics.n_feasible`.
3. **Set the references** to `E_ref = mean E(X)` and `L_ref = mean L(X)` over
   the feasible subset, so each normalised term has expectation 1. Without this
   step wₑ and wₗ would silently absorb the watts-versus-milliseconds scale gap.
4. **Set the penalties** to `λ_cpu = λ_mem = penalty_multiplier · F_max(feasible)`
   with `penalty_multiplier = 100`, so any infeasible solution is dominated by
   every feasible one.
5. **Fall back** to the worst-case method below if fewer than
   `min_feasible_calibration = 10` feasibles are found, with a warning printed to
   the console and recorded in the manifest.

The calibration is deterministic (`calibration_seed: 0`) and the constants that
were actually used are written to `results/<focus>/run_manifest.yaml`, so every
result traces back to the calibration that produced it.

### `worst_case` (legacy)

Geometric upper bounds computed from the instance
(`tools/objective.py` → `compute_normalization_constants()`):

```
E_ref   = Σⱼ e^idle_j + max_j(ηⱼ) · Σᵢ eᵢ
L_ref   = (1 + γ · Σᵢ cᵢ / min_j(Cⱼ)) · Σᵢ ω(pᵢ) · lᵢ
CPU_ref = Σᵢ cᵢ
Mem_ref = Σᵢ mᵢ
```

Cheap, but loose: feasible solutions realise far less than `E_ref` and `L_ref`,
so equal weights do not give equal expected contribution. Penalty weights are
then read from `config.yaml`. Kept for ablation and backwards compatibility.

## Algorithms

**Simulated Annealing.** Starts from the greedy BFD construction and moves
through five problem-specific operators: reassign a random task, swap two
assignments, rescue a task off the most overloaded server, consolidate from the
least- to the most-loaded server, and spread in the opposite direction. Worsening
moves are accepted with probability exp(−ΔF/T), the temperature follows a
geometric schedule, and T₀ is estimated from 400 probe moves at the greedy
solution so that about 80 % of worsening moves are accepted at step 0
(Kirkpatrick et al. 1983). If no improvement occurs for `reheat_patience`
temperature steps, the temperature is reset to `reheat_factor · T₀`.

**Genetic Algorithm.** Population of 100 assignment vectors, initialised as one
greedy BFD solution plus 99 random ones. Parents are chosen by 3-tournament,
recombined with uniform crossover (per-gene swap with probability 0.5, applied to
a pair with probability 0.8) and mutated per gene with probability 1/n. The two
best individuals survive unchanged into the next generation.

**UMDA.** Estimation-of-distribution algorithm. Instead of crossover and
mutation it estimates a categorical model from the best 50 % of the population,

```
P[i][j] = (count(xᵢ = j among selected) + α) / (n_selected + m · α),  α = 0.1
```

and samples a fresh population from it with a vectorised inverse-CDF draw.
Laplace smoothing keeps every server reachable once the model starts to converge.
The mean row entropy H = −Σⱼ P[i][j] log₂ P[i][j] is tracked per generation
(3.32 bits = uniform, near 0 = converged) and reported in verbose mode and in the
diagnostics CSV.

**Branch & Bound.** Depth-first search over the assignment tree, pruning branches
whose lower bound already exceeds the incumbent. Stops at 60 s or 500,000 nodes
and reports the remaining gap. It is used as an optimality reference on the small
20-task instance, not as a competitor on the full instance.

**Baselines.**

| Baseline | Description |
|---|---|
| Greedy BFD | Best-Fit Decreasing: sort tasks by CPU demand descending, place each on the most-loaded server that still has room. Deterministic, and the warm start for SA and GA. |
| Round-robin | Task i goes to server `i % m`. Ignores demands. Deterministic, so it is run once. |
| Random | Uniformly random assignment. Worst-case reference, and always infeasible at n = 50, m = 10. |

## Hyperparameters

Everything lives in [`Cloud_scheduling/config.yaml`](Cloud_scheduling/config.yaml)
and is read at startup. The values below are the ones used for the thesis runs;
they come from the `--tune` grid search and are frozen across all focus modes.

| Parameter | SA | GA | UMDA |
|---|---|---|---|
| Evaluation budget | 150,000 | 150,000 | ≈ 150,100 |
| Population size | — | 100 | 100 |
| Generations / temperature steps | 3,000 | 1,500 | 1,500 |
| Inner iterations per step | 50 | — | — |
| Selection | — | tournament k = 3 | truncation, top 50 % |
| Crossover | — | uniform, p = 0.8 | model-based |
| Mutation | — | per gene, p = 1/n | model-based |
| Elitism | — | 2 | 1 |
| Cooling rate α | 0.99 | — | — |
| Initial temperature | auto (≈ 80 % acceptance) | — | — |
| Reheating | after 300 steps, to 0.4 · T₀ | — | — |
| Laplace smoothing | — | — | α = 0.1 |

Branch & Bound is budgeted in wall time instead: 60 s, with a secondary cap of
500,000 nodes.

Other experiment-level settings: `n_seeds: 20`, `n_tasks: 50`,
`n_calibration_samples: 150`, `penalty_multiplier: 100`, `calibration_seed: 0`.

## Focus modes

A focus mode bundles two independent things: the preference weights between the
normalised objectives, and γ, which is a parameter of the latency function
itself. They are independent because γ shapes L(X) before any normalisation,
while wₑ and wₗ trade off objectives that are already normalised.

| Mode | wₑ | wₗ | γ | Reading |
|---|---|---|---|---|
| `balanced` (default) | 1.0 | 1.0 | 1.0 | equal preference, linear congestion. Thesis default. |
| `performance` | 0.2 | 1.0 | 1.5 | latency valued 5× energy, steeper congestion, rewards spreading load. |
| `eco` | 1.0 | 0.2 | 0.5 | energy valued 5× latency, shallower congestion, tolerates dense packing. |

Because normalisation makes the weights true ratios, (0.2, 1.0) and (1, 5) are
the same preference. The presets keep the smaller-than-one form so the weights
stay bounded. Note that λ is recomputed per mode from that mode's F_max, which is
correct per Deb (2000) but means F values are comparable within a mode, not
across modes.

## Running it

```bash
uv run run.py cloud                                   # defaults
uv run run.py cloud --algorithms SA GA UMDA           # metaheuristics only
uv run run.py cloud --focus eco --verbose             # eco mode, per-step progress
uv run run.py cloud --algorithms SA --seeds 5         # quick single-algorithm check
uv run run.py cloud --sensitivity                     # one-parameter-at-a-time sweeps
uv run run.py cloud --scalability                     # three-axis scaling study
uv run run.py cloud --tune --algorithms SA GA UMDA    # grid search, run once
```

| Option | Short | Values | Default | Effect |
|---|---|---|---|---|
| `--algorithms` | `-a` | `SA GA UMDA BB greedy roundrobin random baselines all` | `all` | which algorithms to run |
| `--focus` | `-f` | `balanced performance eco` | `balanced` | objective weighting mode |
| `--seeds` | `-s` | integer | 20 (from config) | seeds per algorithm |
| `--verbose` | `-v` | flag | off | per-step algorithm progress |
| `--sensitivity` / `--sensibility` | `-S` | flag | off | hyperparameter sweeps |
| `--scalability` | `-L` | flag | off | horizontal, vertical and optimality-gap axes |
| `--tune` | `-T` | flag | off | grid search, writes tuning CSVs, then exits |

## Output files

Results go to `results/<focus>/` and figures to `figures/<focus>/`, so runs in
different modes never overwrite each other.

**Always written**

| File | Contents |
|---|---|
| `results_per_seed.csv` | one row per (algorithm, seed): cost, energy, latency, violations, feasibility, runtime |
| `results_summary.csv` | one row per algorithm: best, average, worst, standard deviation, feasible count, mean runtime |
| `algorithm_diagnostics.csv` | mean diagnostics per algorithm: evaluations, generations, SA reheats and final temperature and acceptance rate, UMDA final entropy, B&B nodes and root bound and gap |
| `run_manifest.yaml` | full parameter snapshot: CLI arguments, instance statistics, calibrated weights and references, calibration diagnostics, every hyperparameter |
| `run_log.txt` | complete console transcript of the run |
| `summary.md` | readable summary: winner, ranking table, energy and latency decomposition, feasibility notes |
| `figures/convergence_all_algorithms.png` | SA, GA and UMDA convergence, mean ± 1σ, x-axis normalised by evaluations |
| `figures/algorithm_comparison_bar.png` | best / average / worst for every algorithm |
| `figures/metaheuristics_comparison.png` | SA, GA, UMDA objective distribution with energy and latency split |
| `figures/boxplot_comparison.png` | box plots with individual seed points |

**With `--sensitivity`:** `sensitivity_{sa,ga,umda}.csv` and
`figures/{sa,ga,umda}_sensitivity.png`.

**With `--scalability`:** `scalability_horizontal.csv`,
`scalability_vertical.csv`, `optimality_gap.csv` and the matching figures
`scalability_horizontal.png`, `scalability_vertical.png`, `optimality_gap.png`.

**With `--tune`:** `tuning_{sa,ga,umda}.csv` with every combination tried, and
`tuning_summary.md` with the recommended values to copy into `config.yaml`.

**From `visualize.py`:** server-rack allocation figures (`allocation_greedy`,
`allocation_sa`, `allocation_comparison_greedy_vs_sa`) in a screen-oriented and a
print-oriented variant, as PNG and PDF, plus two GIF animations of the greedy
construction and the SA search.

## Scalability analysis

`uv run run.py cloud --scalability` runs three axes.

**Axis 1, task count.** Synthetic tasks drawn from the empirical distribution of
the dataset, so instances larger than the 6,345-row file are possible. The server
count scales with the task count at one server per five tasks, which holds CPU
utilisation near 50 % at every size, so runtime growth reflects algorithmic
scaling and not rising constraint pressure. Sizes: 20, 50, 100, 200, 500 tasks,
3 seeds each.

At n ≥ 200 the budget of 150,000 evaluations, which was calibrated for n = 50,
is no longer enough for the growing search space, and the three algorithms
degrade differently. SA starts from the greedy solution and cannot get far from
it, so its improvement over greedy collapses towards zero. UMDA has n × m model
parameters (8,000 at n = 200) estimated from only about 50 selected individuals
per generation, which is too sparse to learn useful preferences, so it also falls
back to greedy-like assignments. GA keeps an advantage because crossover between
its diverse random starting solutions still produces useful offspring. This
budget-dependent divergence is reported as a finding rather than corrected;
`umda_drift_test.py` follows it up by growing the population with the instance at
the same total budget.

**Axis 2, constraint tightness.** The same 50 tasks throughout, with the server
count varied from 20 (about 25 % CPU utilisation) down to 6 (above 80 %), 3 seeds
each. This shows how quality and feasibility degrade as packing pressure rises,
independent of problem size.

**Axis 3, optimality gap.** A 20-task, 4-server instance is solved by Branch &
Bound, and SA, GA and UMDA are run on the same instance with 5 seeds. Their gaps
from the B&B bound give a baseline-independent measure of solution quality on an
instance small enough to be solved exactly.

## Sensitivity analysis

`uv run run.py cloud --sensitivity` varies one hyperparameter at a time while
holding the rest fixed, with 5 seeds per point. It answers whether the chosen
value sits in a robust region, which is a different question from what `--tune`
answers.

Swept: SA `initial_temperature` over [0.005, 0.01, 0.05, 0.1, 0.5, 1.0] and
`cooling_rate` over [0.990, 0.992, 0.995, 0.997, 0.999]; GA `population_size`
over [20, 50, 100] and `crossover_prob` over [0.6, 0.7, 0.8, 0.9, 1.0]; UMDA
`population_size` over [50, 100, 200] and `selection_ratio` over
[0.2, 0.3, 0.5, 0.7].

## Hyperparameter tuning

`--tune` sweeps the full Cartesian product of the grids under `config.yaml →
tuning:` and reports the combination with the lowest mean F(X). It is run once,
the recommended values are copied into the `algorithms:` section, and the main
experiment then runs with fixed values. Re-tuning before every experiment would
let each algorithm adapt to the test instance and would make the comparison
meaningless.

Grids (extended past the earlier boundary winners so the optimum cannot be an
artefact of a truncated range): SA `cooling_rate` ∈ {0.980, 0.985, 0.990, 0.995,
0.999} × `iterations_per_temperature` ∈ {25, 50, 100, 150, 200}; GA
`population_size` ∈ {25, 50, 100, 150, 200} × `crossover_prob` ∈ {0.6, 0.8,
0.95}; UMDA `population_size` ∈ {50, 100, 200} × `selection_ratio` ∈ {0.3, 0.5,
0.7}. Each combination runs 3 seeds at one third of the normal budget, which
preserves the ranking of combinations (Birattari 2009) but makes the absolute F
values incomparable to the main experiment.

## Formula-to-code map

For cross-checking the thesis formulation against the implementation.

| Formula | Where to look |
|---|---|
| F(X), the four combined terms | `objective.py` → `evaluate_schedule()`, the `objective_value = (...)` block |
| E(X) = Σ idle·y + Σ η·e | `evaluate_schedule()`, `idle_energy` + `workload_energy` |
| yⱼ = 1[≥ 1 task on j] | `evaluate_schedule()`, `active = np.bincount(a, minlength=m) > 0` |
| U^cpu_j = Σᵢ cᵢ·1[xᵢ = j] | `evaluate_schedule()`, `cpu_load = np.bincount(a, weights=data.cpu, ...)` |
| l̂ᵢ = lᵢ·(1 + γ·U/C) | `evaluate_schedule()`, `load_ratio` and `eff_latency` |
| ω(p) = 1 / 2 / 4 | `objective.py` → `_PRIORITY_WEIGHTS` |
| Worst-case E_ref, L_ref | `objective.py` → `compute_normalization_constants()` |
| Sample-based calibration | `objective.py` → `compute_sample_normalization()`, pool from `_sample_calibration_pool()` |
| SA acceptance exp(−ΔF/T) | `simulated_annealing.py`, `math.exp(-delta / temperature)` |
| SA T₀ at 80 % acceptance | `simulated_annealing.py` → `estimate_initial_temperature()` |
| UMDA model, smoothed MLE | `umda.py` → `_build_probability_model()` |
| UMDA sampling | `umda.py` → `_sample_population()` |
| UMDA entropy | `umda.py` → `_model_entropy()` |
| Greedy BFD | `initial_solution.py` → `build_greedy_assignment()` |

---

# 2. Electric Vehicle Routing

## Problem statement

One electric vehicle must visit **75 customers** in San Francisco, starting and
ending at a depot, without running out of battery. Charging stations may be
inserted anywhere in the route and may be revisited; each stop charges to full.
There are no time windows and no load capacity.

The optimiser decides the order of customer visits and where to insert charging
stops.

**Solution representation:** a list of node IDs starting and ending at the depot,
for example `["DEPOT", "C001", "EVS04656", "C002", "DEPOT"]`.

**Main instance (`sf_75`):** 1 depot + 75 customers + 30 public charging stations
= 106 nodes. Distances and per-arc travel times come from OSRM queries on the
real San Francisco road network, not straight-line distances, and node elevations
come from SRTM. Nested instances `sf_10` … `sf_500` (each a prefix of the next,
seed 42) are in `instances/` and are committed, because an OSRM rebuild is not
reproducible.

## Objective function

```
F(route) = w_dist · distance_km
         + w_time · (travel_time_h + charging_time_h)
         + w_energy · energy_kwh
         + w_charge · charging_cost_usd
         + λ_bat · battery_violation_kwh
         + λ_vis · infeasible_visits
```

Battery depletion and structural violations (a missing or duplicated customer, or
a station with no usable power) are soft penalties, so the search can pass
through infeasible regions and recover. A route is feasible only when both
penalty terms are zero. See `tools/objective.py:evaluate_route`, which walks the
route once and is O(route length).

**Energy per arc.** Built once at load time from the road data and the EV
parameters (`tools/data_loader.py` → `_build_energy_matrix()`):

```
E(i,j)      = dist_km · base_consumption · grade_mult · speed_mult
grade_mult  = max(0.1, 1 + grade_factor · Δelevation / road_distance)
speed_mult  = (arc_speed / average_speed) ^ speed_exponent
```

with the arc speed taken from the OSRM duration. Changing `grade_factor` or
`speed_exponent` in `EVParameters` takes effect on the next run; the instances do
not need rebuilding.

**Battery parameters:** 20 kWh capacity, recharge to full at a station,
0.50 kWh/km baseline consumption, grade factor 3.0, speed exponent 2.0 (v² drag),
and a 50 km/h fallback speed for arcs with no OSRM duration.

## Weight calibration

The four real-cost weights are calibrated by the same sample-based procedure used
for the cloud problem (Deb 2001): 150 greedy-feasible routes, each perturbed
three times, giving 450 evaluations, with each weight set to the reciprocal of
its component mean. Each component then contributes about 1.0 on a typical
feasible route, so a feasible route scores around 4.0. The penalty weights follow
Deb (2000) as 100 × 4.0 = 400.

The calibrated values are stored in `results/sf_75/weights.json` together with
the component means and standard deviations they came from, and are reproduced in
every `run_manifest.yaml`.

## Algorithms

**Greedy nearest neighbour.** Visits the nearest unvisited customer at each step
and inserts the nearest reachable charging station whenever the battery would
otherwise fall below 50 % of capacity. Deterministic, so the seed has no effect.
It is both the baseline and the warm start for SA, GA and MA.

**Simulated Annealing.** Metropolis acceptance with geometric cooling and
reheating, moving through the eight shared operators below. It accepts an
optional `initial_solution`, which is what the hybrid uses to warm-start it.

**Genetic Algorithm.** Order crossover (OX) on the customer permutation followed
by greedy station repair, tournament selection, and mutation through the same
neighbourhood operators.

**Memetic Algorithm.** The same GA implementation with `local_search_iters > 0`,
which adds a first-improvement local search to every offspring.

**ACO.** Max–Min Ant System with battery-aware construction: an ant heads for a
charging station once its battery drops below `battery_threshold_frac`, and the
next node is chosen by the ACS pseudo-random proportional rule (greedy with
probability q0, probabilistic otherwise). Pheromone concentration is tracked per
iteration as the coefficient of variation of the τ matrix. Optional settings
include a candidate list of size k and an energy-based construction heuristic
(η = 1/energy) instead of the distance heuristic.

**ACO→SA hybrid** (`algorithms/hybrid_aco_sa.py`). ACO reaches good routes within
the first few thousand evaluations, while SA needs a long schedule but descends
further. The hybrid spends `aco_frac` of the budget on ACO construction and hands
the best route to SA as a warm start for the remainder. The only new parameter is
`aco_frac`; both stages use their parents' tuned values.

**Shared neighbourhood operators** (`tools/neighborhoods.py`): swap two
customers, relocate a customer, 2-opt, insert a charging station, remove one,
replace one with another, move one to a different position, and repair a battery
violation.

## Hyperparameters

Tuned by random search (30 trials × 2 seeds × 50,000 evaluations per trial,
`scripts/tune.py`) and stored in `results/sf_75/params.json`, from where `main.py`
loads them automatically. The budget used for tuning is the same for every
algorithm, so no algorithm is tuned closer to its deployment budget than another.

| SA | GA | MA | ACO |
|---|---|---|---|
| T₀ = 0.1 | population 100 | population 40 | 10 ants |
| α = 0.995 | crossover 0.75 | crossover 0.75 | α = 0.5, β = 6.0 |
| 50 iterations per temperature | mutation 0.15 | mutation 0.25 | ρ = 0.3, q0 = 0.95 |
| reheat after 250 steps, to 0.2 · T₀ | tournament 2, elitism 1 | tournament 4, elitism 3, 30 local-search iterations | battery threshold 0.4, no candidate list |

## Focus modes

`--mode` applies a multiplier on top of the calibrated weights. Each multiplier
vector sums to 4.0, so a typical feasible route still scores about 4.0 and the
100× penalty ratio is preserved; only the emphasis among the four cost terms
changes.

| Mode | distance | time | energy | charging cost | Output directory |
|---|---|---|---|---|---|
| `balanced` (default) | 1.0 | 1.0 | 1.0 | 1.0 | `results/sf_75/` |
| `eco` | 0.4 | 0.4 | 2.8 | 0.4 | `results/sf_75_eco/` |
| `time` | 0.4 | 2.8 | 0.4 | 0.4 | `results/sf_75_time/` |

## Running it

```bash
PYTHONPATH=EV_routing python EV_routing/main.py                          # all algorithms, 10 seeds
PYTHONPATH=EV_routing python EV_routing/main.py --algorithms SA ACO      # selected algorithms
PYTHONPATH=EV_routing python EV_routing/main.py --seeds 5                # quick check
PYTHONPATH=EV_routing python EV_routing/main.py --mode eco               # energy-weighted rerun
PYTHONPATH=EV_routing python EV_routing/main.py --sensitivity            # parameter sweeps
PYTHONPATH=EV_routing python EV_routing/main.py --scalability            # size and battery sweeps
PYTHONPATH=EV_routing python EV_routing/main.py --opt-gap                # gap vs best-known solution
```

| Option | Short | Values | Default | Effect |
|---|---|---|---|---|
| `--algorithms` | `-a` | `SA GA MA ACO Greedy all` | `all` | which algorithms to run |
| `--seeds` | `-s` | integer | 10 | seeds per algorithm |
| `--mode` | `-M` | `balanced eco time` | `balanced` | focus mode, non-balanced modes write to their own directory |
| `--sensitivity` | `-S` | flag | off | two-parameter sweeps per algorithm, 3 seeds and 30,000 evaluations per point |
| `--scalability` | `-L` | flag | off | customer-count and battery-capacity axes, 5 seeds and 30,000 evaluations per point |
| `--opt-gap` | `-G` | flag | off | gap against the best solution found in this run |
| `--verbose` | `-v` | flag | off | per-seed progress |

Rebuilding the instances is only needed if the node sets change, not when energy
parameters are tuned:

```bash
PYTHONPATH=EV_routing python EV_routing/scripts/build_instance.py
```

## Output files

Written to `results/<instance>[_<mode>]/`, with figures under `figures/`.

| File | Contents |
|---|---|
| `results_per_seed.csv` | per-seed cost and route metrics |
| `results_summary.csv` | per-algorithm best, average, worst, standard deviation, feasibility, runtime |
| `algorithm_diagnostics.csv` | per-algorithm search diagnostics (acceptance and feasibility rates, reheats, diversity, pheromone concentration) |
| `run_manifest.yaml` | instance, seeds, budget, every hyperparameter, calibrated weights |
| `run_log.txt` | console transcript |
| `summary.md` | readable summary with ranking, improvement over greedy, and Wilcoxon results |
| `params.json`, `weights.json` | tuned hyperparameters and calibrated weights used by the run |
| `optimality_gap.csv` | gap of each algorithm against the best-known solution (`--opt-gap`) |
| `sensitivity_{sa,ga,ma,aco}.csv` | sensitivity sweeps (`--sensitivity`) |
| `scalability_customer.csv`, `scalability_battery.csv` | scalability sweeps (`--scalability`) |
| `figures/` | convergence by step and by evaluations, box comparison, per-algorithm diagnostics, cost breakdown, runtime comparison, route map, scalability and sensitivity plots |

## Additional studies

| Script | What it does | Output |
|---|---|---|
| `scripts/exact_benchmark.py` | Builds `sf_10` as a prefix of `sf_25`, runs the metaheuristics under the main protocol, and solves the instance exactly with A* over states (visited set, current node, battery level) with an admissible bound, so the first goal state popped is the optimum over battery-feasible routes. | `results/sf_10/exact_gap.csv`, `exact_route.json` |
| `scripts/side_experiments.py` | Three follow-ups: the ACO→SA hybrid against its parents at 30k and 150k evaluations; ACO with the energy-based construction heuristic under eco weights; ACO candidate-list sizes k ∈ {0, 15, 25} at n ∈ {300, 500}. | `results/side_experiments/*.csv` |
| `scripts/scalability_analysis.py` | Standalone size sweep across all instances from `sf_25` to `sf_500`, using per-instance tuned parameters and the shared calibrated weights. | `results/scalability/` |
| `scripts/tune.py` | Random or grid search per algorithm, writes the trial table, a two-panel analysis figure and the best parameters. | `results/<instance>/tuning/`, `params.json` |
| `scripts/sensitivity_analysis.py` | Derives each hyperparameter's influence from the tuning trials as (max group mean − min group mean) / overall mean. | `results/<instance>/sensitivity_summary.txt` and figures |
| `scripts/calibrate_weights.py` | Sample-based weight calibration. | `results/<instance>/weights.json` |
| `scripts/make_route_map.py` | Greedy route against SA's best route on an OpenStreetMap basemap. | `figures/route_comparison_map.png` |

## Statistical testing

Algorithm comparisons use pairwise Wilcoxon signed-rank tests on the paired
per-seed costs, with the Holm step-down correction over the family of all pairs
(`tools/statistics.py`). Holm controls the family-wise error rate without the
full conservativeness of Bonferroni. The tables printed by `main.py` show both
the raw and the adjusted p-value, and mark significance on the adjusted one.

---

# Reproducing the thesis results

The committed results were produced on a single machine (Apple M3 Pro), so
runtimes are comparable across algorithms and problems.

```bash
# Cloud: main comparison, all three focus modes
uv run run.py cloud --focus balanced
uv run run.py cloud --focus performance
uv run run.py cloud --focus eco

# Cloud: sweeps (added to the balanced run for the thesis figures)
uv run run.py cloud --focus balanced --sensitivity --scalability

# EV: main comparison and the two focus-mode reruns
PYTHONPATH=EV_routing python EV_routing/main.py
PYTHONPATH=EV_routing python EV_routing/main.py --mode eco
PYTHONPATH=EV_routing python EV_routing/main.py --mode time

# EV: sweeps and follow-ups
PYTHONPATH=EV_routing python EV_routing/main.py --sensitivity --scalability --opt-gap
PYTHONPATH=EV_routing python EV_routing/scripts/exact_benchmark.py
PYTHONPATH=EV_routing python EV_routing/scripts/side_experiments.py
```

Protocol in both problems: 150,000 objective evaluations per run, hyperparameters
frozen after a separate tuning stage, and a fixed seed set (20 seeds for cloud,
10 for EV, 3 to 5 for the sweeps). Every run writes a `run_manifest.yaml` next to
its results, which is the file to check when a number in the thesis needs to be
traced back to the configuration that produced it.

---

# Limitations and threats to validity

The methodological constraints that a reader will reasonably probe, stated up
front rather than defended later.

### Algorithms and models

- **UMDA assumes independence between tasks.** The model is a product of
  per-task marginals, so it cannot represent "if task 7 goes to server 3 then
  task 12 should too". This is a scope choice: the thesis compares three
  metaheuristic families (trajectory, population, model-based) rather than
  surveying EDA variants. Capturing dependencies would need BMDA, COMIT or BOA.
- **Soft constraints everywhere.** Capacities in the cloud problem and battery
  feasibility in the EV problem are penalty terms, not hard constraints with
  repair. This is the conventional penalty approach (Coello 2002) with Deb-2000
  calibration, but it means every algorithm spends part of its budget in
  infeasible regions.
- **The EV energy model is a simplification.** Consumption is linear in distance
  with a grade multiplier and a v² speed term, calibrated to a plausible baseline
  rather than to measured vehicle data. Regenerative braking, auxiliary loads,
  temperature and battery state-of-health are not modelled. Charging is modelled
  as charge-to-full at constant power, which ignores the tapering of real
  charging curves.
- **B&B gaps under the penalty regime.** When greedy BFD returns an infeasible
  warm start on very tight instances, the initial upper bound carries a penalty
  term far larger than any feasible objective, while the root lower bound is
  computed optimistically. The reported gap there means "the search has not yet
  pruned the infeasible region", not "the metaheuristics are far from optimal".

### Experimental design

- **The evaluation budget is calibrated for the small instance.** 150,000
  evaluations is enough for 50 tasks and for 75 customers, but at n ≥ 200 tasks
  the search space outgrows it, and SA and UMDA fall behind GA. The scalability
  analysis reports this as fixed-budget behaviour, which is a different question
  from asymptotic algorithm quality.
- **SA carries a small extra cost.** The T₀ probe consumes about 400 evaluations
  before the main loop, so SA uses roughly 150,400 against 150,000 for GA and
  UMDA, a 0.3 % asymmetry. It is reported separately as
  `stats.t0_probe_evaluations` in the diagnostics CSV.
- **Sample sizes are modest.** 20 seeds for the cloud comparison, 10 for the EV
  comparison, 3 to 5 for the sweeps. Standard deviations are point estimates with
  wide confidence intervals, and the significance tests should be read as
  exploratory. Holm adjustment is applied, but more seeds would be a
  straightforward improvement.
- **One instance per setting.** Each cloud configuration uses one fixed task
  subset and one server pool, with only the algorithm RNG varying. The EV study
  uses one city and one customer draw per size. This isolates algorithm noise but
  does not test whether the ranking holds on a different draw. The vertical axis
  (server count) and the battery axis partially compensate.

### Data

- **The task and charging-station datasets are synthetic.** Both come from
  public Kaggle datasets that are generated rather than measured. The San
  Francisco road network behind the EV distances and durations is real (OSRM),
  as are the SRTM elevations, but the customer locations are drawn, not
  observed.
- **The server pool is hand-specified.** Capacities, idle powers and efficiencies
  in `tools/data_loader.py` are instance parameters, not measurements. The
  comparison between algorithms on a fixed heterogeneous environment stays valid,
  but claims about real data-centre savings would need measured hardware.

### Calibration

- **λ depends on the mode.** The penalty is 100 × F_max(feasible) computed with
  the active mode's weights, so eco and performance end up with different λ on
  the same instance. That is correct per Deb (2000), since the penalty must
  dominate the attainable feasible objective, but F values are only comparable
  within a mode.
- **Calibration can fall back.** If fewer than 10 of the 150 cloud calibration
  samples are feasible, the code reverts to worst-case normalisation and warns
  loudly. The fallback is recorded in the run manifest, so any affected result is
  identifiable.

---

# Dependencies

Python 3.12 or newer with `numpy`, `pandas`, `matplotlib`, `scipy` and `pyyaml`.
With `uv` these are fetched automatically by `run.py` and by the commands above,
so there is no install step.

Extras are needed only for optional steps: `pytest` for the unit tests, and
`requests`, `geopandas`, `shapely` and `contextily` for the two scripts that
talk to OSRM or draw an OpenStreetMap basemap (`build_instance.py` and
`make_route_map.py`). Neither is needed to reproduce the experiments, since the
built instances are committed.
