# EV Routing — Experiment Summary

_Generated: 2026-07-27 21:49_

## Setup

| Parameter | Value |
|---|---|
| Instance | **sf_75** (75 customers, 30 charging stations, 1 depot) |
| Seeds per algorithm | 20 |
| Evaluation budget | 150,000 per run |
| Sensitivity analysis | Skipped — use `--sensitivity` to enable |

## Main Results — Multi-Seed Comparison

Sorted by average objective — lower is better.  Budget: 150,000 evals, 20 seeds.

| Algorithm | Best | Avg | Worst | Std | Feasible | Avg Time |
|---|---|---|---|---|---|---|
| Simulated Annealing | 2.7257 | 2.8395 | 2.9936 | 0.0861 | 20/20 | 7.96s |
| ACO | 2.8828 | 2.9310 | 2.9675 | 0.0210 | 20/20 | 62.01s |
| Memetic Algorithm | 2.8347 | 2.9393 | 3.0557 | 0.0612 | 20/20 | 11.34s |
| Genetic Algorithm | 2.9199 | 3.1003 | 3.2822 | 0.0940 | 20/20 | 44.77s |
| Greedy | 3.6359 | 3.6359 | 3.6359 | 0.0000 | 20/20 | 0.00s |

## Winner and Baseline Comparison

**Simulated Annealing** achieved the best average objective = **2.8395** (best seed: 2.7257).

Improvement over Greedy baseline:
- **Simulated Annealing**: +21.90% (avg 2.8395 vs Greedy 3.6359)
- **Genetic Algorithm**: +14.73% (avg 3.1003 vs Greedy 3.6359)
- **Memetic Algorithm**: +19.16% (avg 2.9393 vs Greedy 3.6359)
- **ACO**: +19.39% (avg 2.9310 vs Greedy 3.6359)

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

