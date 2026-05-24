# Hyperparameter Tuning — Recommended Values

_Generated: 2026-05-24 21:23_

_Tuning method: full Cartesian grid search, 3 seeds per cell._
_Reduced budget: True_


## Recommendations

### Simulated Annealing

| Parameter | Value |
|---|---|
| `cooling_rate` | 0.99 |
| `iterations_per_temperature` | 25 |

_Mean F(X) = 1.8120 ± 0.0020, mean runtime = 8.58s, feasible = 100%_

### Genetic Algorithm

| Parameter | Value |
|---|---|
| `population_size` | 100 |
| `crossover_prob` | 0.8 |

_Mean F(X) = 1.8167 ± 0.0038, mean runtime = 2.50s, feasible = 100%_

### UMDA (EDA)

| Parameter | Value |
|---|---|
| `population_size` | 100 |
| `selection_ratio` | 0.5 |

_Mean F(X) = 1.8179 ± 0.0023, mean runtime = 2.40s, feasible = 100%_


## How to apply

1. Open `config.yaml`.
2. In the `algorithms:` section update each algorithm with the parameter values above.
3. Run the main experiment **without** `--tune`.
4. Optionally run `--sensitivity` to confirm the chosen values are in a robust region.
