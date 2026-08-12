# EV Routing — Experiment Summary

_Generated: 2026-08-12 14:57_

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
| Simulated Annealing | 2.4649 | 2.5583 | 2.7522 | 0.0665 | 20/20 | 7.87s |
| Memetic Algorithm | 2.5412 | 2.6997 | 2.7870 | 0.0677 | 20/20 | 11.92s |
| ACO | 2.6668 | 2.7174 | 2.7856 | 0.0364 | 20/20 | 54.10s |
| Genetic Algorithm | 2.8218 | 3.0441 | 3.2816 | 0.1263 | 20/20 | 42.75s |
| Greedy | 3.5969 | 3.5969 | 3.5969 | 0.0000 | 20/20 | 0.00s |

## Winner and Baseline Comparison

**Simulated Annealing** achieved the best average objective = **2.5583** (best seed: 2.4649).

Improvement over Greedy baseline:
- **Simulated Annealing**: +28.88% (avg 2.5583 vs Greedy 3.5969)
- **Genetic Algorithm**: +15.37% (avg 3.0441 vs Greedy 3.5969)
- **Memetic Algorithm**: +24.94% (avg 2.6997 vs Greedy 3.5969)
- **ACO**: +24.45% (avg 2.7174 vs Greedy 3.5969)

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

