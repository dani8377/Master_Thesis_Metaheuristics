# Cloud Scheduling — Experiment Summary

_Generated: 2026-05-19 17:24_



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

| Genetic Algorithm | 0.9572 | 0.9619 | 0.9656 | 0.0023 | 20/20 | 5.37s |

| UMDA (EDA) | 0.9585 | 0.9644 | 0.9709 | 0.0037 | 20/20 | 4.57s |

| Simulated Annealing | 0.9555 | 1.0088 | 1.0276 | 0.0227 | 20/20 | 5.72s |

| Branch & Bound | 1.2268 | 1.2268 | 1.2268 | 0.0000 | 1/1 | 60.60s |

| Greedy BFD (baseline) | 1.2608 | 1.2608 | 1.2608 | 0.0000 | 20/20 | 0.00s |

| Round-Robin (baseline) | 9.0235 | 9.0235 | 9.0235 | 0.0000 | 0/1 | 0.00s |

| Random (baseline) | 2.9691 | 16.8491 | 32.7830 | 10.3226 | 0/20 | 0.00s |



## Winner

**Genetic Algorithm** achieved the best average F(X) = **0.9619** (best seed: 0.9572).

- **Simulated Annealing**: +19.98% vs Greedy BFD (avg F=1.0088 vs 1.2608)

- **Genetic Algorithm**: +23.71% vs Greedy BFD (avg F=0.9619 vs 1.2608)

- **UMDA (EDA)**: +23.51% vs Greedy BFD (avg F=0.9644 vs 1.2608)



## Energy vs Latency Decomposition (best run per algorithm)

| Algorithm | Energy (W) | Latency (ms) | Active Servers | E-contrib % | L-contrib % |

|---|---|---|---|---|---|

| Simulated Annealing | 13188 | 26674 | 10/10 | 22.0% | 78.0% |

| Genetic Algorithm | 13204 | 26726 | 10/10 | 21.9% | 78.1% |

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

- `results/performance/scalability_lower_bound.csv` — optimality gaps vs Branch & Bound



**Key pattern at large n (≥200 tasks):** SA and UMDA often show near-zero improvement

over Greedy BFD. This is expected fixed-budget behaviour — the 150K evaluation budget

was calibrated for n=50. GA maintains improvement because population diversity allows

broader exploration without relying on a single greedy initialisation or a learned model.



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


