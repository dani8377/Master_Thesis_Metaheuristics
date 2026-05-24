# Hyperparameter Tuning — Recommended Values

_Generated: 2026-05-24 21:32_

_Tuning method: full Cartesian grid search, 3 seeds per cell._
_Reduced budget: True_


## Recommendations

### Simulated Annealing

| Parameter | Value |
|---|---|
| `cooling_rate` | 0.99 |
| `iterations_per_temperature` | 50 |

_Mean F(X) = 1.1082 ± 0.0006, mean runtime = 3.21s, feasible = 100%_

### Genetic Algorithm

| Parameter | Value |
|---|---|
| `population_size` | 200 |
| `crossover_prob` | 0.8 |

_Mean F(X) = 1.1102 ± 0.0007, mean runtime = 2.66s, feasible = 100%_

### UMDA (EDA)

| Parameter | Value |
|---|---|
| `population_size` | 200 |
| `selection_ratio` | 0.5 |

_Mean F(X) = 1.1136 ± 0.0037, mean runtime = 2.26s, feasible = 100%_


## How to apply

1. Open `config.yaml`.
2. In the `algorithms:` section update each algorithm with the parameter values above.
3. Run the main experiment **without** `--tune`.
4. Optionally run `--sensitivity` to confirm the chosen values are in a robust region.
