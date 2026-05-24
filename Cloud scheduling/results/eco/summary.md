# Cloud Scheduling — Experiment Summary

_Generated: 2026-05-24 23:25_

## Setup

| Parameter | Value |
|---|---|
| Focus mode | **eco** (wₑ=1.0, wₗ=0.2, γ=0.5) |
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

Sorted by average F(X) — lower is better.  All runs: n=50 real tasks, 20 seeds.

| Algorithm | Best F | Avg F | Worst F | Std Dev | Feasible | Avg Time |
|---|---|---|---|---|---|---|
| Simulated Annealing | 1.1075 | 1.1083 | 1.1103 | 0.0009 | 20/20 | 5.80s |
| UMDA (EDA) | 1.1085 | 1.1099 | 1.1140 | 0.0013 | 20/20 | 4.75s |
| Genetic Algorithm | 1.1086 | 1.1165 | 1.1347 | 0.0086 | 20/20 | 5.32s |
| Branch & Bound | 1.1362 | 1.1362 | 1.1362 | 0.0000 | 1/1 | 60.67s |
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

Sensitivity results saved to:
- `results/eco/sensitivity_sa.csv` — SA: T₀ sweep and cooling-rate sweep
- `results/eco/sensitivity_ga.csv` — GA: population-size and crossover-prob sweeps
- `results/eco/sensitivity_umda.csv` — UMDA: population-size and selection-ratio sweeps

**What sensitivity analysis tells you:**
Each sweep fixes all parameters except one and measures how F(X) changes.
A parameter that barely affects results is _robust_ (your chosen value is fine anywhere in the range).
A parameter that changes results significantly is _sensitive_ — the thesis should justify the chosen value.
The auto-estimated T₀ for SA is specifically designed to remove T₀ from being a sensitive parameter.

## Scalability Analysis

Scalability results saved to:
- `results/eco/scalability_horizontal.csv` — quality and runtime vs task count (n=20…500+)
- `results/eco/scalability_vertical.csv` — quality vs server count (constraint tightness)

**Cross-instance cost values are NOT directly comparable.** Each row in the scalability
CSVs is normalised with refs (E_ref, L_ref, λ) computed against the calibration pool
of *that specific instance*. At very high utilisation (e.g. vertical's 6-server point at
~80% CPU util) the random feasible samples cluster around heavily congested configurations,
so L_ref can be much larger than at low utilisation — making normalised F drop even though
the raw latency rises. Use `improvement_over_greedy_pct` for cross-instance comparison;
treat `avg_cost` as a within-instance quantity only.

## Solution Quality Benchmark (Optimality Gap vs. Exact Reference)

- `results/eco/optimality_gap.csv` — gap between each metaheuristic and the B&B exact solution

Run on a small instance (n=20, m=4) where Branch & Bound can reach the true optimum within
the time limit. This gives an _absolute_ quality measurement (% from optimum), anchoring the
relative %-vs-greedy numbers from the scalability axes. Note: this is **not** a scalability
test — it runs at a single fixed size and says nothing about how algorithms scale.

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

