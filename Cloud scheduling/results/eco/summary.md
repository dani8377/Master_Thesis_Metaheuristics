# Cloud Scheduling — Experiment Summary

_Generated: 2026-05-19 16:40_



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

| UMDA (EDA) | 1.1085 | 1.1099 | 1.1140 | 0.0013 | 20/20 | 4.90s |

| Genetic Algorithm | 1.1088 | 1.1193 | 1.1331 | 0.0068 | 20/20 | 6.97s |

| Branch & Bound | 1.1362 | 1.1362 | 1.1362 | 0.0000 | 1/1 | 60.58s |

| Simulated Annealing | 1.1468 | 1.1536 | 1.1557 | 0.0030 | 20/20 | 7.24s |

| Greedy BFD (baseline) | 1.1557 | 1.1557 | 1.1557 | 0.0000 | 20/20 | 0.00s |

| Round-Robin (baseline) | 9.2911 | 9.2911 | 9.2911 | 0.0000 | 0/1 | 0.00s |

| Random (baseline) | 3.2487 | 16.9628 | 32.7172 | 10.2209 | 0/20 | 0.00s |



## Winner

**UMDA (EDA)** achieved the best average F(X) = **1.1099** (best seed: 1.1085).

- **Simulated Annealing**: +0.18% vs Greedy BFD (avg F=1.1536 vs 1.1557)

- **Genetic Algorithm**: +3.14% vs Greedy BFD (avg F=1.1193 vs 1.1557)

- **UMDA (EDA)**: +3.96% vs Greedy BFD (avg F=1.1099 vs 1.1557)



## Energy vs Latency Decomposition (best run per algorithm)

| Algorithm | Energy (W) | Latency (ms) | Active Servers | E-contrib % | L-contrib % |

|---|---|---|---|---|---|

| Simulated Annealing | 11781 | 23875 | 5/10 | 81.7% | 18.3% |

| Genetic Algorithm | 11286 | 24027 | 4/10 | 81.0% | 19.0% |

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

- `results/eco/optimality_gap.csv` — optimality gaps vs Branch & Bound (separate quality benchmark, not a scalability axis)



**Key pattern at large n (≥200 tasks):** SA and UMDA often show near-zero improvement

over Greedy BFD. This is expected fixed-budget behaviour — the 150K evaluation budget

was calibrated for n=50. GA maintains improvement because population diversity allows

broader exploration without relying on a single greedy initialisation or a learned model.



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


