# EV Routing — Experiment Summary

_Generated: 2026-07-18 21:59_

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
| Simulated Annealing | 2.5044 | 2.5611 | 2.6132 | 0.0356 | 10/10 | 7.79s |
| ACO | 2.6668 | 2.7105 | 2.7524 | 0.0340 | 10/10 | 54.18s |
| Memetic Algorithm | 2.5773 | 2.7201 | 2.7870 | 0.0624 | 10/10 | 11.70s |
| Genetic Algorithm | 2.8218 | 3.0464 | 3.2816 | 0.1593 | 10/10 | 39.54s |
| Greedy | 3.5969 | 3.5969 | 3.5969 | 0.0000 | 10/10 | 0.00s |

## Winner and Baseline Comparison

**Simulated Annealing** achieved the best average objective = **2.5611** (best seed: 2.5044).

Improvement over Greedy baseline:
- **Simulated Annealing**: +28.80% (avg 2.5611 vs Greedy 3.5969)
- **Genetic Algorithm**: +15.30% (avg 3.0464 vs Greedy 3.5969)
- **Memetic Algorithm**: +24.38% (avg 2.7201 vs Greedy 3.5969)
- **ACO**: +24.64% (avg 2.7105 vs Greedy 3.5969)

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

