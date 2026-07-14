# Cloud Scheduling — Experiment Summary

_Generated: 2026-07-02 14:57_

## Setup

| Parameter | Value |
|---|---|
| Focus mode | **performance** (wₑ=0.2, wₗ=1.0, γ=1.5) |
| Tasks / Servers | 50 tasks × 10 servers |
| Seeds per algorithm | 20 |
| Objective normalised | Yes |
| Sensitivity analysis | Run |
| Scalability analysis | Run |

## F(X) Coefficients (as actually used in this run)

These are the values that were plugged into
`F(X) = wₑ·E/E_ref + wₗ·L/L_ref + λ_cpu·CPU_viol/CPU_ref + λ_mem·Mem_viol/Mem_ref`
after any sample-based calibration.

| Coefficient | Value | Source |
|---|---|---|
| wₑ (energy weight)    |     0.2000 | focus mode `performance` |
| wₗ (latency weight)   |     1.0000 | focus mode `performance` |
| γ (congestion factor) |     1.5000 | focus mode `performance` |
| E_ref                  | 12572.2044 W | sample mean over feasible calibration draws |
| L_ref                  | 35768.7560 ms | sample mean over feasible calibration draws |
| CPU_ref                |  2256.6576 % | total CPU demand Σᵢ cᵢ |
| Mem_ref                | 446274.9268 MB | total memory demand Σᵢ mᵢ |
| λ_cpu (CPU penalty)   |   127.9714 | Deb-2000 rule: 100 × F_max(feasible) |
| λ_mem (memory penalty)|   127.9714 | Deb-2000 rule: 100 × F_max(feasible) |

**Note:** when sample-based normalisation is enabled (`normalize_method: sample` in `config.yaml`), the `cpu_penalty` / `mem_penalty` values in `config.yaml` are overwritten by the Deb-2000 rule. The configured numbers are only used when `normalize_method: worst_case` is selected.

## Main Results — Multi-Seed Comparison

Sorted by average F(X) — lower is better.  All runs: n=50 real tasks, 20 seeds.

| Algorithm | Best F | Avg F | Worst F | Std Dev | Feasible | Avg Time |
|---|---|---|---|---|---|---|
| Simulated Annealing | 0.9539 | 0.9574 | 0.9639 | 0.0025 | 20/20 | 12.42s |
| Genetic Algorithm | 0.9575 | 0.9615 | 0.9656 | 0.0026 | 20/20 | 6.92s |
| UMDA (EDA) | 0.9585 | 0.9644 | 0.9709 | 0.0037 | 20/20 | 9.12s |
| Branch & Bound | 1.2277 | 1.2277 | 1.2277 | 0.0000 | 1/1 | 60.65s |
| Greedy BFD (baseline) | 1.2608 | 1.2608 | 1.2608 | 0.0000 | 20/20 | 0.00s |
| Round-Robin (baseline) | 9.0235 | 9.0235 | 9.0235 | 0.0000 | 0/1 | 0.00s |
| Random (baseline) | 2.9691 | 16.8491 | 32.7830 | 10.3226 | 0/20 | 0.00s |

## Winner

**Simulated Annealing** achieved the best average F(X) = **0.9574** (best seed: 0.9539).
- **Simulated Annealing**: +24.06% vs Greedy BFD (avg F=0.9574 vs 1.2608)
- **Genetic Algorithm**: +23.74% vs Greedy BFD (avg F=0.9615 vs 1.2608)
- **UMDA (EDA)**: +23.51% vs Greedy BFD (avg F=0.9644 vs 1.2608)

## Energy vs Latency Decomposition (best run per algorithm)

| Algorithm | Energy (W) | Latency (ms) | Active Servers | E-contrib % | L-contrib % |
|---|---|---|---|---|---|
| Simulated Annealing | 13058 | 26689 | 10/10 | 21.8% | 78.2% |
| Genetic Algorithm | 13240 | 26714 | 10/10 | 22.0% | 78.0% |
| UMDA (EDA) | 13185 | 26782 | 10/10 | 21.9% | 78.1% |

## Feasibility

Always infeasible: Round-Robin (baseline), Random (baseline) — expected for naive baselines (no capacity awareness).

## Sensitivity Analysis

Sensitivity results saved to:
- `results/performance/sensitivity_sa.csv` — SA: T₀ sweep and cooling-rate sweep
- `results/performance/sensitivity_ga.csv` — GA: population-size and crossover-prob sweeps
- `results/performance/sensitivity_umda.csv` — UMDA: population-size and selection-ratio sweeps

**What sensitivity analysis tells you:**
Each sweep fixes all parameters except one and measures how F(X) changes.
A parameter that barely affects results is _robust_ (your chosen value is fine anywhere in the range).
A parameter that changes results significantly is _sensitive_ — the thesis should justify the chosen value.
The auto-estimated T₀ for SA is specifically designed to remove T₀ from being a sensitive parameter.

## Scalability Analysis

Scalability results saved to:
- `results/performance/scalability_horizontal.csv` — quality and runtime vs task count (n=20…500+)
- `results/performance/scalability_vertical.csv` — quality vs server count (constraint tightness)

**Cross-instance cost values are NOT directly comparable.** Each row in the scalability
CSVs is normalised with refs (E_ref, L_ref, λ) computed against the calibration pool
of *that specific instance*. At very high utilisation (e.g. vertical's 6-server point at
~80% CPU util) the random feasible samples cluster around heavily congested configurations,
so L_ref can be much larger than at low utilisation — making normalised F drop even though
the raw latency rises. Use `improvement_over_greedy_pct` for cross-instance comparison;
treat `avg_cost` as a within-instance quantity only.

## Solution Quality Benchmark (Optimality Gap vs. Exact Reference)

- `results/performance/optimality_gap.csv` — gap between each metaheuristic and the B&B exact solution

Run on a small instance (n=20, m=4) where Branch & Bound can reach the true optimum within
the time limit. This gives an _absolute_ quality measurement (% from optimum), anchoring the
relative %-vs-greedy numbers from the scalability axes. Note: this is **not** a scalability
test — it runs at a single fixed size and says nothing about how algorithms scale.

## Output Files

| File | Contents |
|---|---|
| `results/performance/results_per_seed.csv` | Raw per-seed costs, feasibility, runtimes |
| `results/performance/results_summary.csv` | Per-algorithm statistics (best/avg/worst/std) |
| `results/performance/summary.md` | This file |
| `figures/performance/convergence_all_algorithms.png` | Convergence curves for all metaheuristics |
| `figures/performance/convergence_sa/ga/umda.png` | Per-algorithm convergence detail |
| `figures/performance/boxplot_comparison.png` | Cost distribution across seeds |
| `figures/performance/algorithm_comparison_bar.png` | Best / Avg / Worst bar chart |
| `figures/performance/metaheuristics_comparison.png` | Zoomed metaheuristic comparison + energy/latency breakdown |

