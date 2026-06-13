# EV Routing — Experiment Summary

_Generated: 2026-06-13 01:41_

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
| Simulated Annealing | 2.7257 | 2.8423 | 2.9596 | 0.0814 | 10/10 | 7.14s |
| ACO | 2.9161 | 2.9315 | 2.9658 | 0.0154 | 10/10 | 52.87s |
| Memetic Algorithm | 2.8600 | 2.9537 | 3.0557 | 0.0600 | 10/10 | 10.53s |
| Genetic Algorithm | 3.0259 | 3.1228 | 3.2472 | 0.0786 | 10/10 | 36.73s |
| Greedy | 3.6359 | 3.6359 | 3.6359 | 0.0000 | 10/10 | 0.00s |

## Winner and Baseline Comparison

**Simulated Annealing** achieved the best average objective = **2.8423** (best seed: 2.7257).

Improvement over Greedy baseline:
- **Simulated Annealing**: +21.83% (avg 2.8423 vs Greedy 3.6359)
- **Genetic Algorithm**: +14.11% (avg 3.1228 vs Greedy 3.6359)
- **Memetic Algorithm**: +18.76% (avg 2.9537 vs Greedy 3.6359)
- **ACO**: +19.37% (avg 2.9315 vs Greedy 3.6359)

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

