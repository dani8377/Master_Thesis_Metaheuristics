# EV Routing — Experiment Summary

_Generated: 2026-06-13 01:22_

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
| Simulated Annealing | 2.4507 | 2.5443 | 2.6555 | 0.0586 | 10/10 | 7.35s |
| Memetic Algorithm | 2.6262 | 2.7317 | 2.8136 | 0.0591 | 10/10 | 10.86s |
| ACO | 2.7104 | 2.7796 | 2.8025 | 0.0271 | 10/10 | 52.88s |
| Genetic Algorithm | 2.6986 | 2.8853 | 3.1584 | 0.1404 | 10/10 | 54.43s |
| Greedy | 3.6037 | 3.6037 | 3.6037 | 0.0000 | 10/10 | 0.00s |

## Winner and Baseline Comparison

**Simulated Annealing** achieved the best average objective = **2.5443** (best seed: 2.4507).

Improvement over Greedy baseline:
- **Simulated Annealing**: +29.40% (avg 2.5443 vs Greedy 3.6037)
- **Genetic Algorithm**: +19.94% (avg 2.8853 vs Greedy 3.6037)
- **Memetic Algorithm**: +24.20% (avg 2.7317 vs Greedy 3.6037)
- **ACO**: +22.87% (avg 2.7796 vs Greedy 3.6037)

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

