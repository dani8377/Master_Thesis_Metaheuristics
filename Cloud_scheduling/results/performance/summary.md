# Cloud Scheduling — Experiment Summary

_Generated: 2026-07-18 22:16_

## Setup

| Parameter | Value |
|---|---|
| Focus mode | **performance** (wₑ=0.2, wₗ=1.0, γ=1.5) |
| Tasks / Servers | 50 tasks × 10 servers |
| Seeds per algorithm | 20 |
| Objective normalised | Yes |
| Sensitivity analysis | Skipped (use --sensitivity) |
| Scalability analysis | Skipped (use --scalability) |

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

Sorted by average F(X) — lower is better.  All runs: n=50 dataset tasks, 20 seeds.

| Algorithm | Best F | Avg F | Worst F | Std Dev | Feasible | Avg Time |
|---|---|---|---|---|---|---|
| Simulated Annealing | 0.9539 | 0.9574 | 0.9639 | 0.0025 | 20/20 | 2.47s |
| Genetic Algorithm | 0.9575 | 0.9615 | 0.9656 | 0.0026 | 20/20 | 2.29s |
| UMDA (EDA) | 0.9585 | 0.9644 | 0.9709 | 0.0037 | 20/20 | 2.02s |
| Branch & Bound | 1.2187 | 1.2187 | 1.2187 | 0.0000 | 1/1 | 61.08s |
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

Skipped. Run with `--sensitivity` to sweep hyperparameters and verify robustness.

## Scalability Analysis

Skipped. Run with `--scalability` to test how algorithms perform at increasing problem sizes.

## Solution Quality Benchmark (Optimality Gap vs. Exact Reference)

Skipped. Run with `--scalability` (which also triggers this benchmark) to measure how close
each metaheuristic gets to the true optimum on a small exact-solvable instance.

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

