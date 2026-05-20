# Master Thesis — Metaheuristics for Combinatorial Optimisation

This repository contains the Python implementations developed for the Masters thesis
_"Evaluation of Metaheuristic Algorithms for Energy Optimisation in Scheduling and Routing"_.
Two distinct combinatorial optimisation problems are studied, each solved with multiple
metaheuristics and baseline heuristics. The two problems share the same algorithmic
infrastructure (experiment harness, plotting utilities, data loaders) but are completely
independent in their problem formulations and solution representations.

---

## Table of Contents

1. [Cloud Resource Scheduling](#1-cloud-resource-scheduling)
   - [Problem Statement](#problem-statement)
   - [Mathematical Formulation](#mathematical-formulation)
   - [Thesis Formula Verification](#thesis-formula-verification)
   - [Algorithms](#algorithms)
   - [Algorithm Parameters](#algorithm-parameters)
   - [Focus Modes](#focus-modes)
   - [Running Cloud Scheduling](#running-cloud-scheduling)
   - [Output Files](#output-files)
   - [Scalability Analysis](#scalability-analysis)
   - [Sensitivity Analysis](#sensitivity-analysis)
   - [Hyperparameter Tuning (`--tune`)](#hyperparameter-tuning---tune)
2. [Electric Vehicle Routing](#2-electric-vehicle-routing)
3. [Project Structure](#project-structure)
4. [Limitations and Threats to Validity](#limitations-and-threats-to-validity)
5. [Dependencies](#dependencies)

---

## 1. Cloud Resource Scheduling

**Directory:** `Cloud scheduling/`

### Problem Statement

A batch of **n = 50** independent computational tasks must be assigned to a pool of
**m = 10** heterogeneous physical servers. Each server has fixed CPU and memory capacity;
each task has a CPU footprint, a memory footprint, an energy draw, a base service
latency, and a priority class (Low / Medium / High).

**What the optimiser decides:** which server each task runs on.

**Solution representation:** an integer vector **X** = [x₁, x₂, …, xₙ] where
xᵢ ∈ {0, …, m−1} is the index of the server assigned to task i. This corresponds to the
binary assignment matrix xᵢⱼ ∈ {0, 1} from the thesis formulation, with the
one-hot constraint Σⱼ xᵢⱼ = 1 enforced implicitly by the integer encoding.

**Dataset:** `datasets/cloud_resource_allocation_dataset.csv` — 6,345 task records;
50 tasks are sampled per run. The 10-server pool is defined synthetically in
`tools/data_loader.py`.

---

### Mathematical Formulation

#### Objective Function

The scalar fitness to minimise is:

```
F(X) = wₑ · Ẽ(X) + wₗ · L̃(X)
     + λ_cpu · Σⱼ max(0, U^cpu_j − Cⱼ) / CPU_ref
     + λ_mem · Σⱼ max(0, U^mem_j − Mⱼ) / Mem_ref
```

where `Ẽ(X) = E(X) / E_ref` and `L̃(X) = L(X) / L_ref` are the normalised energy and
latency terms respectively. All four terms are dimensionless after normalisation, so
the weights wₑ and wₗ express true preference shares between 0 and 1.

#### Energy Model

```
E(X) = Σⱼ e^idle_j · yⱼ(X)   +   Σᵢ η_{xᵢ} · eᵢ
```

| Symbol | Description |
|---|---|
| `e^idle_j` | Idle power draw of server j (Watts) — consumed whenever the server is active |
| `yⱼ(X)` | Active-server indicator: 1 if at least one task is assigned to server j; 0 otherwise |
| `η_j` | Server efficiency factor (dimensionless). `η > 1` means the server uses more energy per unit of workload than a reference machine. |
| `eᵢ` | Workload energy draw of task i (Watts) |

The first sum captures the **idle energy** cost of turning servers on. The second sum
captures the **workload energy**, scaled by each server's efficiency. Consolidating tasks
onto fewer servers reduces idle power but may increase workload energy if the active
servers are less efficient. This tension is one of the core trade-offs the optimiser must resolve.

#### Priority-Weighted Congestion Latency

```
L(X) = Σᵢ ω(pᵢ) · l̂ᵢ(X)

l̂ᵢ(X) = lᵢ · (1 + γ · U^cpu_{xᵢ} / C_{xᵢ})

U^cpu_j = Σᵢ cᵢ · 𝟙[xᵢ = j]     (total CPU demand assigned to server j)
```

| Symbol | Description |
|---|---|
| `lᵢ` | Base latency of task i (ms) |
| `U^cpu_j` | Aggregate CPU demand of all tasks currently assigned to server j |
| `Cⱼ` | CPU capacity of server j |
| `γ` | Congestion factor — controls how steeply latency increases with server load |
| `ω(pᵢ)` | Priority weight: `ω(Low=0) = 1`, `ω(Medium=1) = 2`, `ω(High=2) = 4` |
| `pᵢ` | Priority class of task i |

Each task's **effective latency** grows linearly with its server's CPU utilisation ratio.
High-priority tasks (ω = 4) contribute four times more to L(X) than low-priority tasks
(ω = 1), so the optimiser is incentivised to place them on lightly loaded servers.

#### Capacity Penalties

Capacity constraints are enforced as **soft penalties** — the search is allowed to enter
infeasible regions temporarily, which keeps the fitness landscape smooth and explorable:

```
CPU penalty  = λ_cpu · Σⱼ max(0, U^cpu_j − Cⱼ) / CPU_ref
Memory penalty = λ_mem · Σⱼ max(0, U^mem_j − Mⱼ) / Mem_ref
```

A solution is **feasible** when both CPU and memory penalties are exactly zero.

#### Normalisation and Penalty Calibration

Two normalisation methods are supported (set in
`Cloud scheduling/config.yaml` &rarr; `experiment.normalize_method`):

##### `sample` (default, recommended) — Deb (2001) sample-based normalisation

> _Objective weights were calibrated using sample-based normalisation over a
> pool of 150 candidate solutions, of which the feasible subset (≈ 100–140
> at the default 50-task / 10-server instance) was used following Deb (2001),
> so that each normalised objective contributes equally in expectation.
> Constraint penalty weights were set as a 100× multiplier over the maximum
> feasible weighted-normalised objective following Deb (2000), ensuring every
> infeasible solution is strictly dominated by every feasible one._

This is the methodology your weights live inside — the values `wₑ = 1.0`,
`wₗ = 0.2` are not free constants, they are **preference ratios applied on
top of statistically calibrated normalisation constants**. The procedure
(implemented in
[`tools/objective.py:compute_sample_normalization`](Cloud%20scheduling/tools/objective.py)):

1. **Generate the calibration pool.** Draw `n_calibration_samples = 150`
   candidate assignments — *not* by repeated random initialisation alone, but
   by a deliberately constructed mix that lands enough samples in the feasible
   region:
   - 1 candidate from the **greedy Best-Fit-Decreasing** constructor (deterministic,
     typically feasible),
   - ≈ 40% greedy-with-low-perturbation (10% of genes reassigned uniformly),
   - ≈ 30% greedy-with-high-perturbation (30% of genes reassigned),
   - ≈ 30% **uniformly random** assignments.

   This mix anchors the pool around the greedy solution but spreads out enough
   that the resulting feasible subset spans a meaningful slice of the feasible
   region rather than being a deterministic point. See
   [`tools/objective.py:_sample_calibration_pool`](Cloud%20scheduling/tools/objective.py).
2. **Filter to feasibles.** Each candidate is evaluated; only those with zero
   CPU and memory capacity violations are kept. The number of feasibles found
   is recorded in `run_manifest.yaml → calibration_diagnostics.n_feasible`.
3. **Compute normalisation constants:**
   ```
   E_ref = mean( E(X) | X feasible )
   L_ref = mean( L(X) | X feasible )
   ```
   so the normalised energy and latency terms each have expectation **1** across
   the sample. *This is the step that makes the weight ratios meaningful* —
   without it, `wₑ` and `wₗ` would be silently absorbing the Watts-vs-milliseconds
   unit-scale mismatch. With it, `(1, 1)` really does mean equal contribution
   and `(1, 5)` really does mean latency-five-times-energy.
4. **Calibrate penalty weights** (Deb 2000 parameter-less rule):
   ```
   λ_cpu = λ_mem = penalty_multiplier · F_max(feasible)
   ```
   where `F_max(feasible) = max(wₑ · Ẽ + wₗ · L̃)` over the feasible sample and
   `penalty_multiplier = 100`. This guarantees that any infeasible solution
   strictly dominates every feasible one — a violation contributing even 1% of
   total CPU/memory demand adds `λ × 0.01 = F_max`, equal to the entire feasible
   objective range.
5. **Fallback.** If fewer than `experiment.min_feasible_calibration` feasibles
   are found (default 10, only triggers at extreme constraint tightness), the
   calibrator reverts to the worst-case method below and emits a prominent
   warning to the console and to `run_manifest.yaml`.

The exact constants used for every run are persisted to
`Cloud scheduling/results/run_manifest.yaml` (`objective.energy_ref`,
`objective.latency_ref`, `objective.cpu_penalty`, `objective.mem_penalty`,
plus the full `calibration_diagnostics` block), so each result is traceable
back to the calibration that produced it.

##### `worst_case` (legacy) — geometric upper bounds

```
E_ref   = Σⱼ e^idle_j  +  max_j(ηⱼ) · Σᵢ eᵢ
L_ref   = (1 + γ · Σᵢ cᵢ / min_j(Cⱼ)) · Σᵢ ω(pᵢ) · lᵢ
CPU_ref = Σᵢ cᵢ
Mem_ref = Σᵢ mᵢ
```

Cheap (no sampling) but the bounds are loose: feasible solutions typically
realise &lt;&lt; `E_ref` and `L_ref`, so `w_e = w_l = 1` does **not** guarantee
equal expected contribution. Penalty weights `λ_cpu` and `λ_mem` are taken
from `config.yaml`. Provided for backwards compatibility and ablation only.

**Implementation note:** the normalisation is implemented in
[`Cloud scheduling/tools/objective.py`](Cloud%20scheduling/tools/objective.py)
using fully vectorised numpy operations, making it fast enough to be called
~150,000 times per experiment run without bottleneck. The actual calibration
constants used for every run are persisted to
`Cloud scheduling/results/run_manifest.yaml` (`objective` + `calibration_diagnostics`).

---

### Thesis Formula Verification

Use this checklist to confirm that the code exactly matches the thesis formulation.
Each item points to the precise function and lines to inspect.

| Formula element | Code location | What to check |
|---|---|---|
| **F(X) = wₑÃ+wₗL̃+λ_cpu·…+λ_mem·…** | `objective.py:evaluate_schedule()` lines 248–259 | Four terms combined; refs applied; returns `ScheduleEvaluation.objective_value` |
| **E(X) = Σ idle·y + Σ η·e** | `objective.py` lines 218–221 | `idle_energy` + `workload_energy`; `server_efficiency[a]` gives η for each task |
| **yⱼ = 𝟙[≥1 task on j]** | `objective.py` line 212 | `active = np.bincount(a, minlength=m) > 0` |
| **U^cpu_j = Σᵢ cᵢ·𝟙[xᵢ=j]** | `objective.py` line 209 | `cpu_load = np.bincount(a, weights=data.cpu, minlength=m)` |
| **l̂ᵢ = lᵢ·(1+γ·U/C)** | `objective.py` lines 229–230 | `load_ratio = cpu_load[a] / server_cpu_cap[a]`; `eff_latency = latency*(1+γ*load_ratio)` |
| **ω(p): 1/2/4** | `objective.py` line 23 | `_PRIORITY_WEIGHTS = np.array([1.0, 2.0, 4.0])` |
| **E_ref formula** | `objective.py` line 173 | `sum(idle) + max(efficiency)*sum(energy)` |
| **L_ref formula** | `objective.py` lines 176–177 | `(1+γ*Σcpu/min_cap)*Σω·latency` |
| **SA Metropolis: exp(−ΔF/T)** | `simulated_annealing.py` line 178 | `math.exp(-delta / temperature)` |
| **SA T₀ calibration** | `simulated_annealing.py:estimate_initial_temperature()` | `T₀ = -mean_delta / ln(0.80)` |
| **GA uniform crossover** | `genetic_algorithm.py` | Per-gene Bernoulli(0.5) swap |
| **GA tournament selection k=3** | `genetic_algorithm.py` | Sample k individuals, keep best |
| **UMDA model: Laplace-smoothed MLE** | `umda.py:_build_probability_model()` | `P[i][j] = (count+α)/(n_sel+m·α)` |
| **UMDA entropy: −Σ P·log₂P** | `umda.py:_model_entropy()` | Shannon entropy per task row, averaged |
| **Greedy BFD ordering** | `initial_solution.py` | Sort tasks by CPU desc; assign to server with most remaining capacity |

**Config values to cross-check with thesis:**

| Config key | Default value | Thesis description |
|---|---|---|
| `algorithms.sa.cooling_rate` | 0.995 | Geometric cooling factor α |
| `algorithms.sa.max_temp_steps` | 3,000 | Number of temperature levels |
| `algorithms.sa.iterations_per_temperature` | 50 | Inner-loop evaluations per level |
| `algorithms.sa.reheat_patience` | 300 | Steps without improvement before reheat |
| `algorithms.sa.reheat_factor` | 0.4 | Fraction of T₀ for reheated temperature |
| `algorithms.ga.population_size` | 50 | |
| `algorithms.ga.n_generations` | 3,000 | |
| `algorithms.ga.tournament_size` | 3 | Tournament selection k |
| `algorithms.ga.crossover_prob` | 0.8 | Applied per pair with this probability |
| `algorithms.ga.elitism_count` | 2 | Best individuals copied unchanged |
| `algorithms.umda.population_size` | 100 | |
| `algorithms.umda.n_generations` | 1,500 | |
| `algorithms.umda.selection_ratio` | 0.5 | Truncation: top 50% selected |
| `algorithms.umda.smoothing` | 0.1 | Laplace smoothing coefficient α |
| `objective.balanced.cpu_penalty` | 10.0 | λ_cpu (normalised regime) |
| `objective.balanced.mem_penalty` | 10.0 | λ_mem (normalised regime) |
| `objective.balanced.congestion_factor` | 1.0 | γ (linear congestion) |

---

### Algorithms

#### Simulated Annealing (SA)

Single-solution trajectory metaheuristic. Starts from a Greedy BFD construction and
explores the neighbourhood via five problem-specific move operators:

1. **Reassign** — move a randomly chosen task to a random server.
2. **Swap** — swap the server assignments of two randomly chosen tasks.
3. **Rescue** — move one task from the most overloaded server to a random server.
4. **Consolidate** — move a task from the least-loaded server to the most-loaded (saves idle power).
5. **Spread** — move a task from the most-loaded server to the least-loaded (reduces congestion).

**Acceptance criterion (Metropolis):**
```
P(accept worsening move) = exp(−ΔF / T)
```

**Cooling schedule:** geometric — `T_{k+1} = α · T_k` with `α = 0.995`.

**Initial temperature T₀:** auto-estimated from 400 random neighbour moves at the
greedy starting solution, calibrated so that approximately **80% of worsening moves
are accepted at step 0** (Kirkpatrick et al. 1983). This keeps SA correctly calibrated
regardless of whether the objective is normalised or not. Override by setting
`initial_temperature` to a float in `config.yaml`.

**Adaptive reheating:** if no improvement is found for `reheat_patience = 300`
consecutive temperature steps, the temperature is reset to `0.4 · T₀` to escape
local optima.

**Evaluation budget:** `iterations_per_temperature × max_temp_steps = 50 × 3,000 = 150,000`.

#### Genetic Algorithm (GA)

Population-based evolutionary metaheuristic. Maintains a population of P = 50 candidate
assignment vectors evolved over 3,000 generations.

**Initialisation:** 1 Greedy BFD solution + P−1 uniformly random assignments. This
ensures initial diversity while anchoring the population with one strong starting point.

**Selection:** k-tournament selection (k = 3) — draw k individuals uniformly at random,
keep the one with the lowest F(X) as a parent. Repeat to select the second parent.

**Crossover:** Uniform crossover — for each task (gene) independently, swap the server
assignments between the two parents with probability 0.5. Applied with probability 0.8;
otherwise children are direct copies of their parents.

**Mutation:** Per-gene mutation — each task's server assignment is replaced with a
uniformly random server with probability `p_mut = 1 / n_tasks ≈ 0.02`. Expected number
of mutations per offspring: 1.

**Elitism:** the 2 best individuals from the current generation are copied unchanged
into the next generation, guaranteeing that the best solution found so far is never lost.

**Evaluation budget:** `population_size × n_generations = 50 × 3,000 = 150,000`.

#### UMDA — Univariate Marginal Distribution Algorithm (EDA)

Estimation of Distribution Algorithm. Instead of crossover and mutation operators,
UMDA learns a categorical probability model **P[task i][server j]** from the
top-`selection_ratio` fraction of the population each generation, then samples entirely
new solutions from this model.

**Model estimation (truncation selection):**
```
P[i][j] = (count(a[i] = j  for a in selected) + α) / (n_selected + m · α)
```

where `α = 0.1` is the Laplace smoothing coefficient. Laplace smoothing ensures
P[i][j] > 0 for all (i, j), preventing any server from being permanently excluded
from future samples once the model begins to converge.

**Sampling:** vectorised inverse-CDF sampling via numpy — the full population of
`population_size − elitism_count` candidates is drawn in one batched numpy call
per generation (no Python loop over tasks). See `umda.py:_sample_population()`.

**Model entropy:** Shannon entropy `H = −Σⱼ P[i][j] log₂ P[i][j]` is tracked per
generation. Maximum entropy ≈ log₂(10) ≈ 3.32 bits means the model is uniform (broad
exploration). Entropy approaching 0 means the model has converged to near-deterministic
server assignments (exploitation). This is reported in verbose mode.

**Elitism:** the global best-ever solution is always injected directly into each new
population before sampling, so the best solution is never "forgotten" if the model drifts.

**Evaluation budget:** `population_size × n_generations ≈ 100 × 1,500 = 150,000`.

#### Branch and Bound (B&B)

Exact solver included as an optimality reference. Explores a task-assignment tree
depth-first, pruning branches whose lower-bound cost already exceeds the best known
solution. Stops after `time_limit = 60s` or `max_nodes = 500,000` nodes, whichever
comes first, and reports the **optimality gap** (how far the best-found solution is
from the true optimum). Used primarily in the lower-bound scalability axis (n = 20 tasks,
m = 4 servers) to validate that metaheuristics find near-optimal solutions on tractable instances.

#### Baselines

| Baseline | Description | Notes |
|---|---|---|
| **Greedy BFD** | First-Fit Decreasing: sort tasks by CPU demand (largest first), assign each to the most-loaded server with remaining capacity. Deterministic. | Starting point for SA and GA. |
| **Round-Robin** | Assign task i to server `i % m` cyclically. Ignores resource demands. Deterministic. | Runs once (1 seed) — additional seeds produce identical results. |
| **Random** | Assign each task to a uniformly random server. Provides a worst-case reference. Varies per seed. | Always infeasible at n=50, m=10 due to capacity violations. |

---

### Algorithm Parameters

All hyperparameters are stored in [`Cloud scheduling/config.yaml`](Cloud%20scheduling/config.yaml)
and read at runtime. Key values (balanced focus mode):

| Parameter | SA | GA | UMDA |
|---|---|---|---|
| Evaluation budget | 150,000 | 150,000 | ≈ 150,100 |
| Population / parallel solutions | — | 50 | 100 |
| Generations / temperature steps | 3,000 | 3,000 | 1,500 |
| Inner iterations per step | 50 | — | — |
| Selection operator | — | Tournament k=3 | Truncation top 50% |
| Crossover operator | — | Uniform, p=0.8 | — (model-based) |
| Mutation operator | — | Per-gene p=1/n | — (model-based) |
| Elitism count | — | 2 best | 1 best |
| Cooling rate α | 0.995 | — | — |
| Reheat patience | 300 steps | — | — |
| Reheat factor | 0.4 × T₀ | — | — |
| Initial temperature | Auto (~80% accept) | — | — |
| Laplace smoothing | — | — | α = 0.1 |

---

### Focus Modes

A focus mode bundles two independent groups of parameters: **objective
preference ratios** (`wₑ`, `wₗ`, `λ_cpu`, `λ_mem`) and **latency-model parameters**
(`γ`). They are independent because `γ` shapes the latency *function* before
any normalisation is applied, whereas `wₑ`, `wₗ` express preferences *between*
already-normalised objectives.

#### 1. Objective preference ratios

With `normalize_objective: true` (default) each term of F(X) is divided by its
calibration constant — `Ẽ = E / E_ref`, `L̃ = L / L_ref` — so both terms have
expectation 1 across the feasible calibration sample (Deb 2001). At that point
`wₑ` and `wₗ` express a **true preference ratio**, not a unit-conversion factor.
Writing `(wₑ, wₗ) = (0.2, 1.0)` is mathematically identical to `(1, 5)`; both
mean *"latency is five times as important as energy"*. The presets below use
the smaller-than-one convention so `wₑ + wₗ` is bounded.

| Mode | wₑ | wₗ | Energy : latency preference | When to choose it |
|---|---|---|---|---|
| `balanced` (default) | 1.0 | 1.0 | 1 : 1 — equal | Thesis default. Neutral trade-off between energy and latency. |
| `performance` | 0.2 | 1.0 | 1 : 5 — latency-prioritised | Latency is the SLA bottleneck; energy is a secondary concern. |
| `eco` | 1.0 | 0.2 | 5 : 1 — energy-prioritised | Energy efficiency is the goal; latency budget has slack. |

With `normalize_method: sample` (default), `λ_cpu = λ_mem = penalty_multiplier ×
F_max(feasible)` is *computed* at run time per Deb (2000), so the values in
`config.yaml` under `objective.<mode>.cpu_penalty` / `mem_penalty` are only used
under the legacy `worst_case` method. The actual values used are written to
`results/run_manifest.yaml` under `objective.cpu_penalty` and
`calibration_diagnostics.f_max_feasible`.

#### 2. Latency-model parameter

`γ` is **not** an objective weight. It is a parameter of the latency function
itself:

```
l̂ᵢ(X) = lᵢ · (1 + γ · U^cpu_{xᵢ} / C_{xᵢ})
```

Different `γ` values therefore produce different L(X) *before* normalisation;
the calibration constant `L_ref` absorbs that, but the *shape* of the latency
landscape changes. Higher `γ` makes the optimiser pay disproportionately for
packing tasks onto a busy server, encouraging load-spreading; lower `γ`
flattens the penalty so consolidation is cheaper. The per-mode values express
SLA tightness, not preference.

| Mode | γ | Effect on latency function |
|---|---|---|
| `balanced` | 1.0 | Linear congestion — neutral assumption. |
| `performance` | 1.5 | Steeper congestion — rewards spreading load across many servers. |
| `eco` | 0.5 | Shallower congestion — tolerates dense packing without latency blowing up. |

---

### Running Cloud Scheduling

All commands are run from the **project root** directory.

```bash
# Default: balanced focus, all algorithms, 10 seeds
uv run run.py cloud

# Choose specific algorithms
uv run run.py cloud --algorithms SA GA UMDA

# Eco-friendly focus with verbose per-step progress
uv run run.py cloud --focus eco --verbose

# Performance focus, 5 seeds, SA only
uv run run.py cloud --algorithms SA --focus performance --seeds 5

# Run sensitivity analysis (sweeps SA, GA, UMDA hyperparameters — adds ~10 min)
uv run run.py cloud --sensitivity

# Run three-axis scalability analysis (adds ~10–60 min depending on sizes)
uv run run.py cloud --scalability

# Both together
uv run run.py cloud --sensitivity --scalability

# Grid-search hyperparameters (run ONCE, then copy recommendations into config.yaml)
uv run run.py cloud --tune --algorithms SA GA UMDA
```

**Cloud scheduling CLI options** (passed after `cloud`):

| Option | Short | Values | Default | Description |
|---|---|---|---|---|
| `--algorithms` | `-a` | `SA GA UMDA BB greedy roundrobin random baselines all` | `all` | Which algorithms to run |
| `--focus` | `-f` | `balanced performance eco` | `balanced` | Objective weighting mode |
| `--verbose` | `-v` | flag | off | Print per-step algorithm progress |
| `--seeds` | `-s` | integer | 10 | Random seeds per algorithm |
| `--sensitivity` / `--sensibility` | `-S` | flag | off | Run SA/GA/UMDA hyperparameter sweeps |
| `--scalability` | `-L` | flag | off | Run three-axis scalability analysis |
| `--tune` | `-T` | flag | off | Grid-search the tuning ranges in `config.yaml`, write `results/tuning_<algo>.csv` and `results/tuning_summary.md`, then exit |

---

### Output Files

#### Always generated

| File | Contents |
|---|---|
| `results/results_per_seed.csv` | One row per (algorithm, seed): cost, energy (W), latency (ms), violations, feasible, runtime (s). |
| `results/results_summary.csv` | One row per algorithm: best, average, worst, std dev, feasible count, avg runtime. |
| `results/algorithm_diagnostics.csv` | One row per algorithm with mean diagnostics across seeds: total evaluations, generations completed, SA reheats / final T / acceptance / feasibility rates, UMDA final model entropy, B&B nodes / root LB / gap. |
| `results/run_manifest.yaml` | Complete parameter snapshot of this run — CLI args, instance stats, calibrated objective weights and refs, calibration sample diagnostics, every algorithm hyperparameter. Commit alongside any result to make it reproducible. |
| `results/run_log.txt` | Full console transcript of the run (verbose progress, tables, plot paths). |
| `results/summary.md` | **Human-readable summary** — winner, ranking table, energy/latency decomposition, feasibility notes, key findings. Read this first after a run. |
| `figures/convergence_all_algorithms.png` | SA, GA, UMDA convergence curves overlaid (mean ± 1σ, budget-normalised x-axis). |
| `figures/convergence_{sa,ga,umda}.png` | Per-algorithm convergence detail. |
| `figures/algorithm_comparison_bar.png` | Horizontal grouped bar chart: Best / Avg / Worst for all algorithms. |
| `figures/metaheuristics_comparison.png` | Vertical bars for SA/GA/UMDA: objective distribution + energy/latency decomposition. |
| `figures/boxplot_comparison.png` | Box plots with individual seed dots for all algorithms. |

#### With `--tune`

| File | Contents |
|---|---|
| `results/tuning_sa.csv` | Every SA hyperparameter combination tried + mean/std F(X), runtime, feasibility %. |
| `results/tuning_ga.csv` | Every GA hyperparameter combination tried + scores. |
| `results/tuning_umda.csv` | Every UMDA hyperparameter combination tried + scores. |
| `results/tuning_summary.md` | Recommended values per algorithm — copy into `config.yaml` → `algorithms:` section, then run the main experiment without `--tune`. |

#### With `--sensitivity`

| File | Contents |
|---|---|
| `results/sensitivity_sa.csv` | SA: T₀ sweep and α (cooling rate) sweep — best/avg/std per configuration. |
| `results/sensitivity_ga.csv` | GA: population size and crossover probability sweeps. |
| `results/sensitivity_umda.csv` | UMDA: population size and selection ratio sweeps. |
| `figures/sa_sensitivity.png` | SA parameter sensitivity heatmap / line plot. |
| `figures/ga_sensitivity.png` | GA parameter sensitivity plot. |
| `figures/umda_sensitivity.png` | UMDA parameter sensitivity plot. |

#### With `--scalability`

| File | Contents |
|---|---|
| `results/scalability_horizontal.csv` | Algorithm × task count: n_tasks, **n_servers**, avg runtime, avg F(X), % improvement over Greedy. |
| `results/scalability_vertical.csv` | Algorithm × server count: constraint tightness, quality, feasibility %, runtime. |
| `results/scalability_lower_bound.csv` | All algorithms on 20-task instance: cost vs B&B optimum, gap %. |
| `figures/scalability_horizontal.png` | Runtime and quality vs task count (log x-axis). |
| `figures/scalability_vertical.png` | Quality and feasibility vs server count (inverted x-axis — left=loose, right=tight). |
| `figures/scalability_lower_bound.png` | Grouped bar with B&B reference line and gap annotations. |

---

### Scalability Analysis

Run with `uv run run.py cloud --scalability`. Three orthogonal axes are tested.

#### Axis 1 — Horizontal: Task-Count Scaling

Synthetic tasks are drawn from the empirical distribution of the real dataset (mean ± σ
per attribute, empirical priority distribution), allowing instances far larger than the
6,345-row dataset limit. Server count scales proportionally at 1 server per 5 tasks
(`server_ratio: 5`) so CPU utilisation stays constant (~50%) across all sizes — runtime
growth therefore reflects algorithmic scaling, not increasing constraint pressure.

Default sizes (edit `config.yaml` → `scalability.horizontal.task_sizes` to change):

| Instance | Tasks | Servers |
|---|---|---|
| XS (lower-bound ref) | 20 | 4 |
| S (baseline) | 50 | 10 |
| M | 100 | 20 |
| L | 200 | 40 |
| XL | 500 | 100 |

**Important: fixed-budget behaviour at n ≥ 200 tasks**

The evaluation budget (150,000 calls) was calibrated for n = 50 tasks. At n ≥ 200,
the search space grows combinatorially faster than the budget, causing different
algorithms to degrade differently:

- **SA** initialises from the greedy solution and lacks sufficient budget to escape it;
  the improvement over Greedy BFD collapses to ≈ 0% at n = 200+. This is expected
  single-trajectory behaviour, not a code error.
- **UMDA** has the same pattern: its probability model has n × m parameters
  (200 × 40 = 8,000 at n = 200) but only ~50 training samples per generation — too
  sparse to learn reliable task-server preferences. The model effectively reproduces
  greedy-like assignments.
- **GA** maintains an improvement advantage because crossover between its 49 diverse
  random starting solutions produces useful offspring without relying on a single
  greedy initialisation or a learned model.

This is a valid and interesting thesis finding: *at fixed evaluation budget,
population-diversity methods (GA) scale better than single-trajectory (SA) and
model-based (UMDA) methods as problem size grows.*

To restore improvement at larger n, scale the budget in `config.yaml` proportionally:
```yaml
algorithms:
  sa:
    max_temp_steps: 6000   # 2× for n=100 tasks
```

#### Axis 2 — Vertical: Constraint Tightness

The same 50 real tasks are used throughout; only the server count varies. Fewer servers
means each server handles more tasks — CPU utilisation rises from ~25% (20 servers,
loose) to ~80%+ (6 servers, near-critical). This axis reveals how quality and feasibility
degrade as the bin-packing pressure increases, independent of problem size.

| Servers | Approx. CPU utilisation |
|---|---|
| 20 | ~25% (loose) |
| 15 | ~33% |
| 10 | ~50% (baseline) |
| 8 | ~63% |
| 6 | ~80%+ (tight) |

#### Axis 3 — Lower-Bound Reference (Optimality Gaps)

A small instance (n = 20 tasks, m = 4 servers) is solved by Branch & Bound to optimality
(or near-optimality within the 60 s time limit). SA, GA, and UMDA are also run on the same
instance; their gaps from the B&B bound give a direct, baseline-independent measure of
solution quality. This validates that the metaheuristics find near-optimal solutions on
tractable instances before being trusted on larger ones.

---

### Sensitivity Analysis

Run with `uv run run.py cloud --sensitivity` (or `--sensibility` — both spellings accepted).

#### What sensitivity analysis is for

Sensitivity analysis answers the question: *"How much does performance change if I
adjust one hyperparameter while keeping all others fixed?"*

A **robust** parameter barely affects results across its range — the chosen default
is fine anywhere nearby. A **sensitive** parameter changes results significantly —
the thesis must justify why the chosen value was selected, and the sensitivity plot
provides that justification.

Concretely, this analysis:
1. Validates that the chosen hyperparameter values are at or near the optimum.
2. Demonstrates that performance is not fragile (the algorithm works well across a range).
3. Identifies which parameters matter most for this specific problem instance.
4. Provides figures for the thesis showing parameter influence.

#### What is swept

- **SA:** `initial_temperature` over [0.005, 0.01, 0.05, 0.1, 0.5, 1.0] and
  `cooling_rate` over [0.990, 0.992, 0.995, 0.997, 0.999]. 5 seeds each.
- **GA:** `population_size` over [20, 50, 100] and `crossover_prob` over
  [0.6, 0.7, 0.8, 0.9, 1.0]. 5 seeds each.
- **UMDA:** `population_size` over [50, 100, 200] and `selection_ratio` over
  [0.2, 0.3, 0.5, 0.7]. 5 seeds each.

#### Key findings from a typical run

- **SA T₀:** Values below ≈ 0.05 give good results; values ≥ 0.1 degrade quality
  (temperature too high — too many worsening moves accepted throughout). The auto-
  estimation (`null` in config) reliably lands in the good range.
- **SA α (cooling rate):** α = 0.990 (faster cooling) often gives the best raw score
  because the reheating mechanism triggers more frequently, effectively running multiple
  restarts. α ≥ 0.992 gives similar, consistent results. The default α = 0.995 is safe.
- **GA population size:** larger is better (100 > 50 > 20) but with diminishing returns.
  Pop = 50 provides a good quality/speed trade-off.
- **GA crossover prob:** robust — performance is similar across 0.6–1.0.

Results are saved to `results/sensitivity_{sa,ga,umda}.csv` and
`figures/{sa,ga,umda}_sensitivity.png`.

---

### Hyperparameter Tuning (`--tune`)

`--sensitivity` answers *"is my chosen value robust?"* but it varies only one
parameter at a time. `--tune` answers the prior question *"what value should I
pick in the first place?"* by sweeping the full Cartesian product of the
tuning grids declared in `config.yaml` &rarr; `tuning:` and reporting the
combination with the lowest mean F(X).

#### Workflow

1. Run `uv run run.py cloud --tune --algorithms SA GA UMDA` **once** at the
   start of a thesis chapter (typically on `n_tasks = 50`).
2. Read `results/tuning_summary.md` for the recommended values per algorithm.
3. Copy those values into `config.yaml` &rarr; `algorithms:` section.
4. Run the main experiment **without** `--tune` so all subsequent figures use
   the chosen values.
5. Optionally run `--sensitivity` afterwards to demonstrate the chosen values
   sit in a robust region.

#### Why this is not run every time

Grid search multiplies runtime by 9–27&times; (depending on grid size). The
thesis workflow is "tune once, freeze, then evaluate"; algorithm comparisons
must use **fixed** hyperparameters or the results are not meaningful. Running
`--tune` before every experiment would also implicitly let each algorithm
re-tune on the test instance, which biases the comparison.

#### Default tuning grids

- **SA:** `cooling_rate` ∈ {0.990, 0.995, 0.999} × `iterations_per_temperature`
  ∈ {25, 50, 100} = 9 combinations.
- **GA:** `population_size` ∈ {25, 50, 100} × `crossover_prob` ∈
  {0.6, 0.8, 0.95} = 9 combinations.
- **UMDA:** `population_size` ∈ {50, 100, 200} × `selection_ratio` ∈
  {0.3, 0.5, 0.7} = 9 combinations.

Each combination is run for `tuning.n_seeds` (default 3) seeds with the
algorithm's evaluation budget reduced to 1/3 (`tuning.reduced_budget: true`)
so the full sweep completes in minutes. The relative ranking of combinations
is preserved at reduced budget (Birattari 2009), but the absolute F values
are not directly comparable to the main experiment.

---

## 2. Electric Vehicle Routing

**Directory:** `EV_routing/`

A single Electric Vehicle must visit **75 customer locations** in San Francisco, starting
and ending at a central depot, while managing its battery charge. Charging stations can
be inserted into the route when needed.

**What the optimiser decides:** the order in which customers are visited and where to
insert charging stops.

**Objective:** minimise a weighted combination of total distance, travel time, charging
time, energy consumed, and charging cost. Battery depletion is handled as a soft
penalty (10,000×) so the search can temporarily enter infeasible regions and recover.

**Dataset:** synthetic San Francisco instance — 75 customers, 30 charging stations,
pre-computed Haversine distance and energy matrices.

**Algorithm:** Simulated Annealing with 8 neighbourhood operators (customer swap,
relocate, 2-opt, insert/remove/replace/move charging station, battery repair).

**Battery parameters:** 20 kWh capacity, 0.50 kWh/km consumption, 50 km/h speed.

---

## Project Structure

```
Master_Thesis_Metaheuristics/
│
├── run.py                              ← top-level launcher
├── Makefile                            ← make-based shortcuts
│
├── Cloud scheduling/                   ← Problem 1 (thesis Chapter 3)
│   ├── main.py                         ← entry point; orchestrates all experiments
│   ├── config.yaml                     ← all hyperparameters and experiment settings
│   ├── BEGINNERS_GUIDE.md              ← reading-order guide for new readers
│   ├── datasets/
│   │   └── cloud_resource_allocation_dataset.csv
│   ├── figures/                        ← plots saved here
│   ├── results/                        ← CSV and summary.md saved here
│   ├── algorithms/
│   │   ├── simulated_annealing.py      ← SA with auto-T₀, geometric cooling, reheating
│   │   ├── genetic_algorithm.py        ← GA with tournament, uniform crossover, elitism
│   │   ├── umda.py                     ← UMDA (EDA) with Laplace smoothing, entropy tracking
│   │   ├── branch_and_bound.py         ← exact B&B solver (time-limited)
│   │   └── baselines.py                ← Greedy BFD, Round-Robin, Random
│   └── tools/
│       ├── config_loader.py            ← reads config.yaml into typed dataclasses
│       ├── data_loader.py              ← loads CSV + synthesises server pool
│       ├── objective.py                ← FocusMode, ObjectiveWeights, evaluate_schedule()
│       ├── feasibility.py              ← validates assignment vector structure
│       ├── initial_solution.py         ← Greedy BFD / round-robin / random constructors
│       ├── neighborhoods.py            ← 5 SA move operators
│       ├── experiment.py               ← multi-seed experiment harness
│       └── plot.py                     ← convergence / bar / box / CSV export
│
└── EV_routing/                         ← Problem 2 (thesis Chapter 4)
    ├── main.py
    ├── datasets/
    ├── figures/
    ├── algorithms/
    │   └── simmulated_annealing.py
    └── tools/
        ├── data_loader.py
        ├── objective.py
        ├── feasibility.py
        ├── initial_solution.py
        ├── neighborhoods.py
        ├── experiment.py
        ├── plot.py
        ├── energy.py
        ├── energy_model.py
        ├── distance.py
        └── node_utils.py
```

---

## Limitations and Threats to Validity

A frank list of the methodological constraints a reviewer will (rightly) probe.
Each one is acknowledged here so the thesis can preempt the question rather
than defend against it.

### Algorithm and model limitations

- **UMDA univariate-independence assumption.** UMDA factorises the joint
  distribution over assignments as the product of per-task marginals
  P[task_i][server_j]. It cannot represent dependencies between tasks
  (e.g. *"if task 7 goes to server 3 then task 12 should also go to server 3
  to share its memory locality"*). This is an intentional scope choice — the
  thesis compares three representative metaheuristic families (trajectory,
  population-based, model-based), not every EDA variant. Capturing
  dependencies would require BMDA, COMIT, or BOA, which are out of scope.
- **Soft capacity penalties (not hard constraints).** CPU and memory
  capacities are enforced as additive penalty terms, not as hard constraints
  with repair operators. This is the conventional penalty-function approach
  (Coello 2002) and is theoretically supported by Deb 2000's parameter-less
  penalty calibration (which we use). The cost is that all three algorithms
  spend some fraction of their evaluation budget exploring infeasible regions.
- **B&B optimality gap under the penalty regime.** When greedy BFD returns an
  infeasible warm-start (only at very tight constraint settings), the initial
  upper bound `best_cost` already includes a `λ × violation` term that can be
  ~100× larger than any feasible objective. The root lower bound, computed
  with optimistic remaining-task assumptions, is much smaller, so B&B's
  reported gap on tight instances should be read as *"the search hasn't yet
  pruned enough infeasible-region nodes"*, not *"the metaheuristics are
  dramatically suboptimal"*.

### Experimental-design limitations

- **Fixed evaluation budget calibrated for n = 50.** All algorithms use ~150 K
  evaluate_schedule() calls per run, chosen so the small thesis instance
  (50 tasks, 10 servers) converges. At n ≥ 200 the search space grows
  combinatorially faster than the budget, so SA and UMDA visibly under-perform
  GA at large scale. The scalability analysis (`--scalability`) reports this
  as a finding, not a bug — see the "Important: fixed-budget behaviour"
  paragraph above. If the goal were to measure asymptotic algorithm quality
  rather than fixed-budget behaviour, the budget would have to scale with n.
- **SA carries a small extra T₀-calibration cost (~400 evaluations).** SA's
  auto-T₀ probe consumes ≈ 400 evaluations before the main loop, giving SA
  a total budget of ~150 400 vs ~150 000 for GA/UMDA — a 0.3% asymmetry.
  This is now reported separately in the diagnostics CSV under
  `stats.t0_probe_evaluations` and folded into `total_budget_consumed`, so the
  thesis can quote the exact figure.
- **10 seeds for the main experiment, 3–5 for scalability.** Sample sizes are
  small by inferential-statistics standards. Quoted standard deviations are
  point estimates of population SD with wide confidence intervals; the
  significance tests in the results table should be read as exploratory
  rather than confirmatory. The thesis presentation should be honest about
  this; expanding to 30+ seeds is a straightforward follow-up.
- **Single problem instance per setting.** Each `(focus_mode, n_tasks,
  n_servers)` triple uses one fixed task subset (`df.head(n_tasks)`) plus the
  same server pool, with only the algorithm RNG varying across seeds. This
  isolates algorithm noise but does not test cross-instance robustness — a
  defender can ask *"would the relative ranking hold on a different 50-task
  draw?"*. The vertical scalability axis partially addresses this by varying
  server count on the same task set, but a full instance-sweep is out of scope.

### Data limitations

- **Synthetic server pool.** The 10-server pool in
  [`tools/data_loader.py:DEFAULT_SERVER_POOL`](Cloud%20scheduling/tools/data_loader.py)
  is hand-specified — capacities, idle powers, and efficiencies are stated
  as instance parameters of the experiment, not measured from real hardware.
  The CSV dataset only describes tasks. This is a modelling choice; the
  experiment compares algorithms on a *fixed* heterogeneous environment, so
  internal validity is preserved even if external validity (claims about real
  data-centre energy savings) would require empirical server data.
- **Task attributes sampled from one CSV.** All task instances come from
  `cloud_resource_allocation_dataset.csv`; the scalability axis samples
  larger instances from the empirical distribution fit to that file. Findings
  generalise to workloads with similar statistical character.

### Calibration limitations

- **Mode-dependent λ.** The penalty multiplier `λ = 100 × F_max(feasible)` is
  computed using the active mode's preference weights, so eco mode and
  performance mode end up with different λ values on the same instance. This
  is correct per Deb (2000) — the penalty must dominate the *actually
  attainable* feasible objective — but means cross-mode F values are not
  directly comparable. Within a mode, comparisons are fully valid.
- **Calibration fallback on extremely tight instances.** If fewer than
  `experiment.min_feasible_calibration` candidates (default 10) are feasible
  in the 150-sample pool, the code falls back to worst-case normalisation
  and prints a loud warning. This is logged to `results/run_manifest.yaml`
  so any reported result on such an instance is traceable. Loosening the
  capacity constraints or increasing `n_calibration_samples` avoids the
  fallback.

---

## Dependencies

The project uses [uv](https://github.com/astral-sh/uv) for Python and package
management. No virtual environment or `pip install` step is needed — `uv run`
downloads and caches packages automatically on first use.

Required packages: `numpy`, `pandas`, `matplotlib`, `scipy`, `pyyaml`
