# EV Routing — Experiment Summary

_Generated: 2026-06-10 17:49_

## Setup

| Parameter | Value |
|---|---|
| Instance | **sf_75** (75 customers, 30 charging stations, 1 depot) |
| Seeds per algorithm | 10 |
| Evaluation budget | 150,000 per run |
| Sensitivity analysis | Skipped — use `--sensitivity` to enable |

## Main Results — Multi-Seed Comparison

Sorted by average objective — lower is better.  Budget: 150,000 evals, 10 seeds.

| Algorithm | Best | Avg | Worst | Std | Feasible | Avg Time |
|---|---|---|---|---|---|---|
| Simulated Annealing | 2.4391 | 2.5137 | 2.6895 | 0.0886 | 10/10 | 6.27s |
| ACO | 2.6154 | 2.6327 | 2.6733 | 0.0197 | 10/10 | 54.27s |
| Memetic Algorithm | 2.5225 | 2.6468 | 2.7675 | 0.0869 | 10/10 | 22.16s |
| Genetic Algorithm | 2.6813 | 2.9126 | 3.1057 | 0.1596 | 10/10 | 36.93s |
| Greedy | 3.5789 | 3.5789 | 3.5789 | 0.0000 | 10/10 | 0.00s |

## Winner and Baseline Comparison

**Simulated Annealing** achieved the best average objective = **2.5137** (best seed: 2.4391).

Improvement over Greedy baseline:
- **Simulated Annealing**: +29.76% (avg 2.5137 vs Greedy 3.5789)
- **Genetic Algorithm**: +18.62% (avg 2.9126 vs Greedy 3.5789)
- **Memetic Algorithm**: +26.04% (avg 2.6468 vs Greedy 3.5789)
- **ACO**: +26.44% (avg 2.6327 vs Greedy 3.5789)

## Sensitivity Analysis

Skipped. Run with `--sensitivity` to sweep hyperparameters and confirm robustness.

## Output Files

| File | Contents |
|---|---|
| `results_per_seed.csv` | Raw per-seed costs and route metrics |
| `results_summary.csv` | Per-algorithm aggregated statistics |
| `algorithm_diagnostics.csv` | SA/GA/MA/ACO internal search diagnostics |
| `run_manifest.yaml` | Full parameter snapshot of this run |
| `run_log.txt` | Complete console output |
| `figures/` | All convergence, box, diagnostic, and breakdown plots |
| `figures/sensitivity/` | Parameter sensitivity errorbar plots |

