# Metaheuristics for Energy-Aware Scheduling and Routing — source code

Experiment code for the MSc thesis _"Evaluation of Metaheuristic Algorithms for
Energy Optimisation in Scheduling and Routing"_.

- **Authors:** Christian Wu (s194597) and Daniel Diamant (s205336)
- **Supervisor:** Professor Carsten Witt, DTU Compute
- **Institution:** Technical University of Denmark (DTU), Department of Applied
  Mathematics and Computer Science
- **Submitted:** August 2026

The repository contains two independent experiment modules. Each has its own
entry point, its own parameter files and its own results directory, and neither
imports from the other.

| Module | Directory | Algorithms implemented |
|---|---|---|
| Cloud resource scheduling (50 tasks, 10 servers) | [`Cloud_scheduling/`](Cloud_scheduling/) | SA, GA, UMDA, Branch & Bound, greedy BFD / round-robin / random baselines |
| Electric-vehicle routing (75 customers, 30 charging stations) | [`EV_routing/`](EV_routing/) | SA, GA, MA, ACO, greedy nearest-neighbour baseline, ACO→SA hybrid |

All results, figures, tuned parameters and run manifests committed here were
produced by the code in this repository; nothing in `results/` is hand-edited.

---

## Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/), which fetches and caches dependencies per
  run, so there is no virtual environment to create and no `pip install` step
- Runtime dependencies: `numpy`, `pandas`, `matplotlib`, `scipy`, `pyyaml`

`run.py` and the `Makefile` pass these five packages to `uv run` explicitly. If
`uv` is not available, `run.py` exits with a message and the module entry points
can be called with any Python interpreter that already has the five packages
installed.

Optional extras, needed only for the steps named:

| Extra | Needed by |
|---|---|
| `pytest` | the unit-test suite in `Cloud_scheduling/tests/` |
| `requests`, `geopandas`, `shapely`, `contextily` | `build_instance.py` (OSRM queries), `make_route_map.py`, `make_instance_map.py` (OpenStreetMap basemaps) |

Neither extra is required to reproduce the experiments: the built EV instances
are committed, because an OSRM rebuild depends on a live service and is not
reproducible.

---

## Quick start

Run everything from the **project root**.

```bash
uv run run.py                    # both modules with their default settings
uv run run.py cloud              # cloud scheduling only
uv run run.py ev                 # EV routing only

uv run run.py cloud --focus eco --seeds 5      # flags after the target are
uv run run.py ev --seeds 5 --mode eco          # forwarded to that module

uv run run.py cloud --help       # full option list per module
uv run run.py ev --help
```

`make cloud`, `make ev` and `make` (both) are equivalent shortcuts.

Flags are forwarded verbatim to the selected module, and the two modules have
different option sets, so pass flags to one target at a time. `run.py` with
flags but no target prints usage and exits rather than starting a multi-hour run
of both modules.

Unit tests (cloud module, 33 tests):

```bash
cd Cloud_scheduling
uv run --with numpy --with pandas --with matplotlib --with pyyaml \
       --with scipy --with pytest python -m pytest tests -q
```

### Working directories

The two modules resolve paths differently, which is why `run.py` launches them
differently:

- `Cloud_scheduling/main.py` resolves `config.yaml`, `datasets/`, `results/` and
  `figures/` relative to its own file, so it can be started from any directory.
- `EV_routing/main.py` and every script in `EV_routing/scripts/` resolve
  `EV_routing/instances/…` and `EV_routing/results/…` relative to the current
  working directory, and import their own `tools/` package, so they must be
  started **from the project root with `PYTHONPATH=EV_routing`**:

```bash
PYTHONPATH=EV_routing python EV_routing/main.py --seeds 5
PYTHONPATH=EV_routing python EV_routing/scripts/tune.py
```

### Runtimes

Measured on the machine that produced the committed results (Apple M3 Pro), from
the per-algorithm runtimes in `results_summary.csv`:

| Run | Wall time |
|---|---|
| `run.py cloud`, 20 seeds, all algorithms | ≈ 3.5 min, of which 61 s is the Branch & Bound time limit |
| `run.py ev`, 20 seeds, all algorithms | ≈ 39 min, ACO and GA accounting for about 80 % of it |
| `run.py ev`, default 10 seeds | ≈ 20 min |

The `--sensitivity`, `--scalability` and `--tune` sweeps add considerably more.

---

## Repository layout

```
Master_Thesis_Metaheuristics/
│
├── run.py                              ← launcher for both modules
├── Makefile                            ← make cloud / make ev / make
│
├── Cloud_scheduling/
│   ├── main.py                         ← entry point: experiment, sweeps, tuning
│   ├── config.yaml                     ← every hyperparameter and experiment setting
│   ├── visualize.py                    ← server-rack allocation figures and GIFs
│   ├── umda_drift_test.py              ← standalone UMDA population-size experiment
│   ├── datasets/
│   │   ├── cloud_resource_allocation_dataset.csv   ← 6,345 task records
│   │   └── raw/                        ← original download (.xlsx)
│   ├── results/<focus>/                ← CSVs, run_manifest.yaml, run_log.txt, summary.md
│   ├── figures/<focus>/                ← PNG/PDF figures, GIF animations
│   ├── tests/                          ← 33 unit tests over 3 files
│   ├── algorithms/
│   │   ├── simulated_annealing.py      ← SA, auto-T₀ probe, geometric cooling, reheating
│   │   ├── genetic_algorithm.py        ← tournament selection, uniform crossover, elitism
│   │   ├── umda.py                     ← EDA with Laplace smoothing and entropy tracking
│   │   ├── branch_and_bound.py         ← time- and node-limited exact reference
│   │   └── baselines.py                ← greedy BFD, round-robin, random
│   └── tools/
│       ├── config_loader.py            ← config.yaml → typed dataclasses
│       ├── data_loader.py              ← task CSV, server pool, synthetic instances
│       ├── objective.py                ← FocusMode, ObjectiveWeights, evaluate_schedule()
│       ├── feasibility.py              ← assignment-vector validation
│       ├── initial_solution.py         ← greedy BFD / round-robin / random constructors
│       ├── neighborhoods.py            ← 5 SA move operators
│       ├── experiment.py               ← multi-seed harness
│       └── plot.py                     ← convergence / bar / box plots, CSV export
│
└── EV_routing/
    ├── main.py                         ← entry point: experiment, sweeps, optimality gap
    ├── datasets/                       ← raw charging-station and San Francisco node data
    ├── instances/                      ← frozen instances sf_10 … sf_500 (matrices, maps)
    ├── results/
    │   ├── sf_75/                      ← main instance: CSVs, params.json, weights.json,
    │   │                                 tuning/, figures/
    │   ├── sf_75_eco/, sf_75_time/     ← focus-mode reruns
    │   ├── sf_10/                      ← exact A* optimum and optimality gaps
    │   ├── scalability/                ← standalone size sweep sf_25 … sf_500
    │   └── side_experiments/           ← hybrid, eco-heuristic, candidate-list, penalty,
    │                                     eco-steerability studies
    ├── algorithms/
    │   ├── greedy.py                   ← nearest-neighbour baseline
    │   ├── simulated_annealing.py      ← SA with reheating and optional warm start
    │   ├── genetic_algorithm.py        ← GA, and MA when local_search_iters > 0
    │   ├── ant_colony.py               ← Max–Min Ant System
    │   └── hybrid_aco_sa.py            ← ACO construction handed to SA as a warm start
    ├── tools/
    │   ├── data_loader.py              ← instance loading, energy-matrix construction
    │   ├── battery.py                  ← EVParameters dataclass
    │   ├── objective.py                ← evaluate_route()
    │   ├── feasibility.py              ← structural and battery feasibility
    │   ├── initial_solution.py         ← EV-feasible construction and repair
    │   ├── neighborhoods.py            ← 8 move operators
    │   ├── experiment.py               ← multi-seed harness
    │   ├── statistics.py               ← Wilcoxon signed-rank tests, Holm correction
    │   ├── tuning.py                   ← grid and random search
    │   ├── compare.py                  ← controlled comparison driver
    │   ├── plot.py                     ← all EV figures
    │   ├── distance.py                 ← distance providers and matrix builders
    │   └── node_utils.py               ← node-ID helpers
    └── scripts/                        ← standalone studies and figure generation,
                                          see the table in section 2
```

---

# 1. Cloud_scheduling

`main.py` loads the task CSV and the server pool, calibrates the objective for
the selected focus mode, runs the selected algorithms over the configured seeds
under a shared evaluation budget, and writes results, figures and a manifest.
Everything it needs is in `config.yaml`; no argument is required to reproduce a
run other than the focus mode.

## Command line

```bash
uv run run.py cloud                                   # defaults
uv run run.py cloud --algorithms SA GA UMDA           # metaheuristics only
uv run run.py cloud --focus eco --verbose             # eco mode, per-step progress
uv run run.py cloud --algorithms SA --seeds 5         # quick single-algorithm check
uv run run.py cloud --sensitivity                     # one-parameter-at-a-time sweeps
uv run run.py cloud --scalability                     # three-axis scaling study
uv run run.py cloud --tune --algorithms SA GA UMDA    # grid search, then exit
```

| Option | Short | Values | Default | Effect |
|---|---|---|---|---|
| `--algorithms` | `-a` | `SA GA UMDA BB greedy roundrobin random baselines all` | `all` | which algorithms to run; `baselines` selects all three |
| `--focus` | `-f` | `balanced performance eco` | `balanced` | objective weighting mode, also selects the output directory |
| `--seeds` | `-s` | integer | from `config.yaml` (20) | seeds per algorithm |
| `--verbose` | `-v` | flag | off | per-step algorithm progress |
| `--sensitivity` / `--sensibility` | `-S` | flag | off | hyperparameter sweeps, 10 seeds per point |
| `--scalability` | `-L` | flag | off | task-count, server-count and optimality-gap axes |
| `--tune` | `-T` | flag | off | grid search over the `tuning:` grids, writes CSVs and exits |

## Configuration

[`Cloud_scheduling/config.yaml`](Cloud_scheduling/config.yaml) is read at startup
and holds every tunable value. Its six sections:

| Section | Contents |
|---|---|
| `experiment` | `n_seeds: 20`, `n_tasks: 50`, normalisation method and its calibration settings (`n_calibration_samples: 150`, `penalty_multiplier: 100`, `calibration_seed: 0`, `min_feasible_calibration: 10`) |
| `objective` | per focus mode: energy and latency weights, CPU and memory penalties, congestion factor |
| `algorithms` | SA, GA, UMDA and B&B hyperparameters. The evaluation budget is the product of the per-algorithm counts: SA 50 × 3,000, GA 100 × 1,500, UMDA 100 × 1,500, all ≈ 150,000 calls to `evaluate_schedule()`. B&B is bounded by wall time (60 s) and nodes (500,000) instead |
| `sensitivity` | sweep values used by `--sensitivity`, 10 seeds per point |
| `tuning` | grids used by `--tune`, 3 seeds per combination at one third of the budget |
| `scalability` | the three `--scalability` axes: task sizes `[20, 50, 100, 200, 500]` at 8 seeds, server counts `[20, 15, 10, 8, 6]` at 8 seeds, and a 20-task / 4-server optimality-gap instance at 10 seeds |

The tuned values in `algorithms:` are the ones used for the reported runs and are
frozen across focus modes. `--tune` is a separate step whose recommendations are
copied into that section by hand; the main experiment never re-tunes.

## Outputs

Results go to `results/<focus>/` and figures to `figures/<focus>/`, so runs in
different focus modes never overwrite each other.

**Every run**

| File | Contents |
|---|---|
| `results_per_seed.csv` | one row per (algorithm, seed): cost, energy, latency, violations, feasibility, runtime |
| `results_summary.csv` | one row per algorithm: best, average, worst, standard deviation, feasible count, mean runtime |
| `algorithm_diagnostics.csv` | mean diagnostics per algorithm: evaluations, generations, SA reheats and final temperature and acceptance rate, UMDA final entropy, B&B nodes, root bound and gap |
| `run_manifest.yaml` | full parameter snapshot: CLI arguments, instance statistics, calibrated weights and references, calibration diagnostics, every hyperparameter |
| `run_log.txt` | complete console transcript |
| `summary.md` | readable summary: ranking table, energy and latency decomposition, feasibility notes |
| `figures/convergence_all_algorithms.png` | SA, GA and UMDA convergence, mean ± 1σ, x-axis normalised by evaluations |
| `figures/algorithm_comparison_bar.png` | best / average / worst per algorithm |
| `figures/metaheuristics_comparison.png` | objective distribution with energy and latency split |
| `figures/boxplot_comparison.png` | box plots with individual seed points |

**Flag-specific**

| Flag | Files |
|---|---|
| `--sensitivity` | `sensitivity_{sa,ga,umda}.csv`, `figures/{sa,ga,umda}_sensitivity.png` |
| `--scalability` | `scalability_horizontal.csv`, `scalability_vertical.csv`, `optimality_gap.csv` and the matching figures |
| `--tune` | `tuning_{sa,ga,umda}.csv` with every combination tried, `tuning_summary.md` with the recommended values |

## Tests

`Cloud_scheduling/tests/` holds 33 tests in three files:

| File | Tests | Covers |
|---|---|---|
| `test_objective.py` | 8 | hand-computed objective terms against `evaluate_schedule()`: idle and workload energy, priority weights, congestion, capacity violations, normalisation constants |
| `test_algorithms.py` | 8 | baseline determinism, best-fit rather than first-fit packing, each metaheuristic improving on greedy, seed reproducibility, and the evaluation budget matching `config.yaml` |
| `test_correctness.py` | 17 | objective decomposition on hand-built instances, feasibility flags, sample-based calibration (references, penalty dominance, bounded F), monotone improvement over the initial solution, and an exactly solvable tiny instance |

Each file also runs standalone, for example `uv run python tests/test_objective.py`
from `Cloud_scheduling/`. The EV module has no test suite.

## Additional entry points

| Script | What it does |
|---|---|
| `visualize.py` | Server-rack allocation figures in a screen and a print variant (PNG and PDF), two GIF animations of the greedy construction and the SA search, and a small concept figure. Run from `Cloud_scheduling/`; see its module docstring for the flag list. Writes to `figures/<focus>/`. |
| `umda_drift_test.py` | Standalone experiment that grows the UMDA population with the instance size at a fixed total budget, mirroring the horizontal scalability axis. Run from `Cloud_scheduling/`; `--smoke` runs a reduced version. Writes `results/umda_drift_test.csv`. |

---

# 2. EV_routing

`main.py` loads the frozen `sf_75` instance, reads the calibrated weights from
`results/sf_75/weights.json` and the tuned hyperparameters from
`results/sf_75/params.json`, runs the selected algorithms over the requested
seeds at a 150,000-evaluation budget, and writes results, figures, a manifest and
pairwise significance tests. Both files are prerequisites on a fresh instance:
`params.json` is mandatory and the run aborts with a pointer to `scripts/tune.py`
if it is absent, while a missing `weights.json` falls back to built-in default
weights with a warning.

## Command line

```bash
PYTHONPATH=EV_routing python EV_routing/main.py                     # all algorithms, 10 seeds
PYTHONPATH=EV_routing python EV_routing/main.py --seeds 20          # the protocol used for the reported runs
PYTHONPATH=EV_routing python EV_routing/main.py --algorithms SA ACO # selected algorithms
PYTHONPATH=EV_routing python EV_routing/main.py --mode eco          # energy-weighted rerun
PYTHONPATH=EV_routing python EV_routing/main.py --sensitivity       # parameter sweeps
PYTHONPATH=EV_routing python EV_routing/main.py --scalability       # size and battery sweeps
PYTHONPATH=EV_routing python EV_routing/main.py --opt-gap           # gap vs best solution of the run
```

| Option | Short | Values | Default | Effect |
|---|---|---|---|---|
| `--algorithms` | `-a` | `SA GA MA ACO Greedy all` | `all` | which algorithms to run |
| `--seeds` | `-s` | integer | 10 | seeds per algorithm |
| `--mode` | `-M` | `balanced eco time` | `balanced` | multiplier applied to the calibrated weights; non-balanced modes write to `results/sf_75_<mode>/` |
| `--sensitivity` | `-S` | flag | off | two parameters per algorithm, 3 seeds and 30,000 evaluations per point |
| `--scalability` | `-L` | flag | off | customer-count axis (`sf_25` … `sf_500`) and battery axis (5–20 kWh), 7 seeds and 30,000 evaluations per point |
| `--opt-gap` | `-G` | flag | off | gap of each algorithm against the best cost found anywhere in the same run |
| `--verbose` | `-v` | flag | off | per-seed progress |

The instance is selected by the `INSTANCE` constant at the top of `main.py`
(`sf_75`), not by a flag; the size sweeps are what iterate over the other
instances.

## Instances and parameter files

`instances/sf_10 … sf_500` are frozen and committed. Each holds `depot.csv`,
`customers.csv`, `charging_stations.csv`, `distance_matrix.csv`,
`duration_matrix.csv`, `node_elevations.csv`, `instance.json` and a preview map.
Distances and per-arc durations come from OSRM queries on the San Francisco road
network and elevations from SRTM; the instances are nested, each a prefix of the
next. Rebuilding them (`scripts/build_instance.py`) is only needed if the node
sets change — the energy model reads `EVParameters` at run time, so changing
`grade_factor` or `speed_exponent` takes effect on the next run without a
rebuild.

Two JSON files drive a run and are written by their own scripts:

| File | Written by | Read by |
|---|---|---|
| `results/<instance>/weights.json` | `scripts/calibrate_weights.py` | `main.py`, the standalone studies |
| `results/<instance>/params.json` | `scripts/tune.py` | `main.py` |

Both are committed for `sf_75`, so a run reproduces the reported configuration
without re-running calibration or tuning.

## Outputs

Written to `results/<instance>[_<mode>]/`, with figures under `figures/`.

| File | Contents |
|---|---|
| `results_per_seed.csv` | per-seed cost and route metrics |
| `results_summary.csv` | per-algorithm best, average, worst, standard deviation, feasibility, runtime |
| `algorithm_diagnostics.csv` | per-algorithm search diagnostics: acceptance and feasibility rates, reheats, diversity, pheromone concentration |
| `run_manifest.yaml` | instance, seeds, budget, every hyperparameter, calibrated weights |
| `run_log.txt` | console transcript |
| `summary.md` | ranking, improvement over greedy, Wilcoxon results, list of files written |
| `optimality_gap.csv` | `--opt-gap` |
| `sensitivity_{sa,ga,ma,aco}.csv` and `figures/sensitivity/` | `--sensitivity` |
| `scalability_customer.csv`, `scalability_battery.csv` | `--scalability` |
| `figures/` | convergence by step and by evaluations, box comparison, per-algorithm diagnostics, cost breakdown, runtime comparison, scalability and sensitivity plots |

Algorithm comparisons use pairwise Wilcoxon signed-rank tests on the paired
per-seed costs with Holm step-down correction (`tools/statistics.py`). The tables
printed by `main.py` and written to `summary.md` show the raw and the adjusted
p-value and mark significance on the adjusted one.

## Scripts

All are run from the project root with `PYTHONPATH=EV_routing`.

| Script | What it does | Output |
|---|---|---|
| `tune.py` | Random or grid search per algorithm: 30 random trials × 2 seeds × 50,000 evaluations. Writes the trial table, an analysis figure and the best parameters. | `results/<instance>/tuning/`, `params.json` |
| `calibrate_weights.py` | Sample-based weight calibration from 150 greedy-feasible routes with 3 perturbations each. | `results/<instance>/weights.json` |
| `build_instance.py` | Builds every instance from OSRM and SRTM data. Needs the network extras. | `instances/sf_*/` |
| `exact_benchmark.py` | Builds `sf_10` as a prefix of `sf_25`, runs the metaheuristics under the main protocol, and solves the instance exactly with A* over (visited set, current node, battery level) states. | `results/sf_10/exact_gap.csv`, `exact_route.json` |
| `scalability_analysis.py` | Standalone size sweep over `sf_25` … `sf_500` with per-instance tuned parameters and the shared calibrated weights. | `results/scalability/` |
| `sensitivity_analysis.py` | Derives each hyperparameter's influence from the tuning trials as (max group mean − min group mean) / overall mean. | `results/<instance>/sensitivity_summary.txt`, figures |
| `side_experiments.py` | Hybrid ACO→SA against its parents at 30k and 150k evaluations; ACO with the energy-based construction heuristic under eco weights; ACO candidate-list sizes. `--smoke` runs a reduced version. | `results/side_experiments/hybrid.csv`, `eco_heuristic.csv`, `candidate_list.csv` |
| `eco_steerability.py` | Factorial sweep of the ACO parameters that could explain its weak eco response. `--smoke` runs a reduced version. | `results/side_experiments/eco_steerability.csv` |
| `penalty_sensitivity.py` | Sweeps the penalty multiplier around its calibrated 100× setting. | `results/side_experiments/penalty_sensitivity.csv` |
| `sa_reheat_ablation.py` | Reruns SA with reheating disabled over the same 20 seeds for comparison against `results_summary.csv`. | console |
| `energy_decomposition.py` | Splits arc energy into its distance, grade and speed components over sample tours. | console |
| `make_route_map.py` | Greedy route against SA's best route on an OpenStreetMap basemap. Needs the network extras. | `results/sf_75/figures/route_comparison_map.png` |
| `make_instance_map.py` | Redraws the `sf_75` instance map from the frozen instance data. Needs the network extras. | `report/graphics/sf75_instance_map.png`, created on demand |
| `make_cover_graphic.py` | Two-panel schematic of the scheduling and routing problems. Its PDF target directory is not created automatically. | `report/graphics/cover_dual_problems.pdf`, preview PNG in `results/sf_75/figures/` |
| `regen_fixed_plots.py`, `regen_scalability_plots.py` | Redraw figures from saved CSVs without re-running any algorithm. | overwrite the corresponding PNGs |

---

# Reproducing the committed results

```bash
# Cloud: main comparison in all three focus modes
uv run run.py cloud --focus balanced
uv run run.py cloud --focus performance
uv run run.py cloud --focus eco

# Cloud: sweeps (added to the balanced run)
uv run run.py cloud --focus balanced --sensitivity --scalability

# EV: main comparison and the two focus-mode reruns
PYTHONPATH=EV_routing python EV_routing/main.py --seeds 20
PYTHONPATH=EV_routing python EV_routing/main.py --seeds 20 --mode eco
PYTHONPATH=EV_routing python EV_routing/main.py --seeds 20 --mode time

# EV: sweeps and standalone studies
PYTHONPATH=EV_routing python EV_routing/main.py --sensitivity --scalability --opt-gap
PYTHONPATH=EV_routing python EV_routing/scripts/exact_benchmark.py
PYTHONPATH=EV_routing python EV_routing/scripts/side_experiments.py
```

Both modules follow the same protocol: a fixed budget of 150,000 objective
evaluations per run, hyperparameters frozen after a separate tuning stage, a
fixed seed set (20 seeds for both main comparisons, 3 to 10 for the sweeps), and
a `run_manifest.yaml` written next to every result set. The manifest is the file
to open when a number needs to be traced back to the configuration that produced
it: it records the CLI arguments, the calibrated constants and every
hyperparameter in force for that run.

Runs are seeded and deterministic given the same instance, parameters and seed
list. Re-running a command overwrites the results directory it writes to, so
copy `results/` aside first if the committed output needs to be kept.
