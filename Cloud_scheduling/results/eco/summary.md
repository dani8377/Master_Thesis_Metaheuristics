# Cloud Scheduling — Experiment Summary

_Generated: 2026-07-18 22:13_

## Setup

| Parameter | Value |
|---|---|
| Focus mode | **eco** (wₑ=1.0, wₗ=0.2, γ=0.5) |
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
| wₑ (energy weight)    |     1.0000 | focus mode `eco` |
| wₗ (latency weight)   |     0.2000 | focus mode `eco` |
| γ (congestion factor) |     0.5000 | focus mode `eco` |
| E_ref                  | 12572.2044 W | sample mean over feasible calibration draws |
| L_ref                  | 22764.5187 ms | sample mean over feasible calibration draws |
| CPU_ref                |  2256.6576 % | total CPU demand Σᵢ cᵢ |
| Mem_ref                | 446274.9268 MB | total memory demand Σᵢ mᵢ |
| λ_cpu (CPU penalty)   |   127.0761 | Deb-2000 rule: 100 × F_max(feasible) |
| λ_mem (memory penalty)|   127.0761 | Deb-2000 rule: 100 × F_max(feasible) |

**Note:** when sample-based normalisation is enabled (`normalize_method: sample` in `config.yaml`), the `cpu_penalty` / `mem_penalty` values in `config.yaml` are overwritten by the Deb-2000 rule. The configured numbers are only used when `normalize_method: worst_case` is selected.

## Main Results — Multi-Seed Comparison

Sorted by average F(X) — lower is better.  All runs: n=50 dataset tasks, 20 seeds.

| Algorithm | Best F | Avg F | Worst F | Std Dev | Feasible | Avg Time |
|---|---|---|---|---|---|---|
| Simulated Annealing | 1.1075 | 1.1083 | 1.1103 | 0.0009 | 20/20 | 2.48s |
| UMDA (EDA) | 1.1085 | 1.1099 | 1.1140 | 0.0013 | 20/20 | 2.04s |
| Genetic Algorithm | 1.1086 | 1.1165 | 1.1347 | 0.0086 | 20/20 | 2.32s |
| Branch & Bound | 1.1362 | 1.1362 | 1.1362 | 0.0000 | 1/1 | 61.31s |
| Greedy BFD (baseline) | 1.1557 | 1.1557 | 1.1557 | 0.0000 | 20/20 | 0.00s |
| Round-Robin (baseline) | 9.2911 | 9.2911 | 9.2911 | 0.0000 | 0/1 | 0.00s |
| Random (baseline) | 3.2487 | 16.9628 | 32.7172 | 10.2209 | 0/20 | 0.00s |

## Winner

**Simulated Annealing** achieved the best average F(X) = **1.1083** (best seed: 1.1075).
- **Simulated Annealing**: +4.09% vs Greedy BFD (avg F=1.1083 vs 1.1557)
- **Genetic Algorithm**: +3.39% vs Greedy BFD (avg F=1.1165 vs 1.1557)
- **UMDA (EDA)**: +3.96% vs Greedy BFD (avg F=1.1099 vs 1.1557)

## Energy vs Latency Decomposition (best run per algorithm)

| Algorithm | Energy (W) | Latency (ms) | Active Servers | E-contrib % | L-contrib % |
|---|---|---|---|---|---|
| Simulated Annealing | 11263 | 24091 | 4/10 | 80.9% | 19.1% |
| Genetic Algorithm | 11290 | 23976 | 4/10 | 81.0% | 19.0% |
| UMDA (EDA) | 11297 | 23898 | 4/10 | 81.1% | 18.9% |

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
| `results/eco/results_per_seed.csv` | Raw per-seed costs, feasibility, runtimes |
| `results/eco/results_summary.csv` | Per-algorithm statistics (best/avg/worst/std) |
| `results/eco/summary.md` | This file |
| `figures/eco/convergence_all_algorithms.png` | Convergence curves for all metaheuristics |
| `figures/eco/convergence_sa/ga/umda.png` | Per-algorithm convergence detail |
| `figures/eco/boxplot_comparison.png` | Cost distribution across seeds |
| `figures/eco/algorithm_comparison_bar.png` | Best / Avg / Worst bar chart |
| `figures/eco/metaheuristics_comparison.png` | Zoomed metaheuristic comparison + energy/latency breakdown |

