# Cloud Scheduling — Experiment Summary

_Generated: 2026-05-21 18:16_



## Setup

| Parameter | Value |

|---|---|

| Focus mode | **balanced** (wₑ=1.0, wₗ=1.0, γ=1.0) |

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

| wₑ (energy weight)    |     1.0000 | focus mode `balanced` |

| wₗ (latency weight)   |     1.0000 | focus mode `balanced` |

| γ (congestion factor) |     1.0000 | focus mode `balanced` |

| E_ref                  | 12572.2044 W | sample mean over feasible calibration draws |

| L_ref                  | 29266.6374 ms | sample mean over feasible calibration draws |

| CPU_ref                |  2256.6576 % | total CPU demand Σᵢ cᵢ |

| Mem_ref                | 446274.9268 MB | total memory demand Σᵢ mᵢ |

| λ_cpu (CPU penalty)   |   206.4673 | Deb-2000 rule: 100 × F_max(feasible) |

| λ_mem (memory penalty)|   206.4673 | Deb-2000 rule: 100 × F_max(feasible) |



**Note:** when sample-based normalisation is enabled (`normalize_method: sample` in `config.yaml`), the `cpu_penalty` / `mem_penalty` values in `config.yaml` are overwritten by the Deb-2000 rule. The configured numbers are only used when `normalize_method: worst_case` is selected.



## Main Results — Multi-Seed Comparison

Sorted by average F(X) — lower is better.  All runs: n=50 real tasks, 20 seeds.



| Algorithm | Best F | Avg F | Worst F | Std Dev | Feasible | Avg Time |

|---|---|---|---|---|---|---|

| Simulated Annealing | 1.8086 | 1.8116 | 1.8151 | 0.0016 | 20/20 | 8.75s |

| Genetic Algorithm | 1.8132 | 1.8169 | 1.8215 | 0.0023 | 20/20 | 7.50s |

| UMDA (EDA) | 1.8141 | 1.8175 | 1.8248 | 0.0031 | 20/20 | 7.29s |

| Branch & Bound | 1.9981 | 1.9981 | 1.9981 | 0.0000 | 1/1 | 60.66s |

| Greedy BFD (baseline) | 2.0062 | 2.0062 | 2.0062 | 0.0000 | 20/20 | 0.00s |

| Round-Robin (baseline) | 14.9027 | 14.9027 | 14.9027 | 0.0000 | 0/1 | 0.00s |

| Random (baseline) | 5.1077 | 27.4391 | 53.0855 | 16.6268 | 0/20 | 0.00s |



## Winner

**Simulated Annealing** achieved the best average F(X) = **1.8116** (best seed: 1.8086).

- **Simulated Annealing**: +9.70% vs Greedy BFD (avg F=1.8116 vs 2.0062)

- **Genetic Algorithm**: +9.44% vs Greedy BFD (avg F=1.8169 vs 2.0062)

- **UMDA (EDA)**: +9.40% vs Greedy BFD (avg F=1.8175 vs 2.0062)



## Energy vs Latency Decomposition (best run per algorithm)

| Algorithm | Energy (W) | Latency (ms) | Active Servers | E-contrib % | L-contrib % |

|---|---|---|---|---|---|

| Simulated Annealing | 12566 | 23678 | 10/10 | 55.3% | 44.7% |

| Genetic Algorithm | 12593 | 23751 | 10/10 | 55.2% | 44.8% |

| UMDA (EDA) | 12558 | 23858 | 10/10 | 55.1% | 44.9% |



## Feasibility

Always infeasible: Round-Robin (baseline), Random (baseline) — expected for naive baselines (no capacity awareness).



## Sensitivity Analysis

Sensitivity results saved to:

- `results/balanced/sensitivity_sa.csv` — SA: T₀ sweep and cooling-rate sweep

- `results/balanced/sensitivity_ga.csv` — GA: population-size and crossover-prob sweeps

- `results/balanced/sensitivity_umda.csv` — UMDA: population-size and selection-ratio sweeps



**What sensitivity analysis tells you:**

Each sweep fixes all parameters except one and measures how F(X) changes.

A parameter that barely affects results is _robust_ (your chosen value is fine anywhere in the range).

A parameter that changes results significantly is _sensitive_ — the thesis should justify the chosen value.

The auto-estimated T₀ for SA is specifically designed to remove T₀ from being a sensitive parameter.



## Scalability Analysis

Scalability results saved to:

- `results/balanced/scalability_horizontal.csv` — quality and runtime vs task count (n=20…500+)

- `results/balanced/scalability_vertical.csv` — quality vs server count (constraint tightness)



**Cross-instance cost values are NOT directly comparable.** Each row in the scalability

CSVs is normalised with refs (E_ref, L_ref, λ) computed against the calibration pool

of *that specific instance*. At very high utilisation (e.g. vertical's 6-server point at

~80% CPU util) the random feasible samples cluster around heavily congested configurations,

so L_ref can be much larger than at low utilisation — making normalised F drop even though

the raw latency rises. Use `improvement_over_greedy_pct` for cross-instance comparison;

treat `avg_cost` as a within-instance quantity only.



## Solution Quality Benchmark (Optimality Gap vs. Exact Reference)

- `results/balanced/optimality_gap.csv` — gap between each metaheuristic and the B&B exact solution



Run on a small instance (n=20, m=4) where Branch & Bound can reach the true optimum within

the time limit. This gives an _absolute_ quality measurement (% from optimum), anchoring the

relative %-vs-greedy numbers from the scalability axes. Note: this is **not** a scalability

test — it runs at a single fixed size and says nothing about how algorithms scale.



## Output Files

| File | Contents |

|---|---|

| `results/balanced/results_per_seed.csv` | Raw per-seed costs, feasibility, runtimes |

| `results/balanced/results_summary.csv` | Per-algorithm statistics (best/avg/worst/std) |

| `results/balanced/summary.md` | This file |

| `figures/balanced/convergence_all_algorithms.png` | Convergence curves for all metaheuristics |

| `figures/balanced/convergence_sa/ga/umda.png` | Per-algorithm convergence detail |

| `figures/balanced/boxplot_comparison.png` | Cost distribution across seeds |

| `figures/balanced/algorithm_comparison_bar.png` | Best / Avg / Worst bar chart |

| `figures/balanced/metaheuristics_comparison.png` | Zoomed metaheuristic comparison + energy/latency breakdown |


