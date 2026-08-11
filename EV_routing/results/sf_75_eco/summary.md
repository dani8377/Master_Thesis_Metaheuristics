# EV Routing — Experiment Summary

_Generated: 2026-07-27 15:24_

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
| Simulated Annealing | 2.4507 | 2.5438 | 2.6555 | 0.0602 | 20/20 | 7.85s |
| Memetic Algorithm | 2.5877 | 2.7097 | 2.8169 | 0.0772 | 20/20 | 11.78s |
| ACO | 2.7104 | 2.7818 | 2.8025 | 0.0256 | 20/20 | 54.22s |
| Genetic Algorithm | 2.6986 | 2.8936 | 3.1730 | 0.1416 | 20/20 | 50.11s |
| Greedy | 3.6037 | 3.6037 | 3.6037 | 0.0000 | 20/20 | 0.00s |

## Winner and Baseline Comparison

**Simulated Annealing** achieved the best average objective = **2.5438** (best seed: 2.4507).

Improvement over Greedy baseline:
- **Simulated Annealing**: +29.41% (avg 2.5438 vs Greedy 3.6037)
- **Genetic Algorithm**: +19.71% (avg 2.8936 vs Greedy 3.6037)
- **Memetic Algorithm**: +24.81% (avg 2.7097 vs Greedy 3.6037)
- **ACO**: +22.81% (avg 2.7818 vs Greedy 3.6037)

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

