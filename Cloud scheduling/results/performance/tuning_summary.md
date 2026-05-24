# Hyperparameter Tuning — Recommended Values

_Generated: 2026-05-24 21:40_

_Tuning method: full Cartesian grid search, 3 seeds per cell._
_Reduced budget: True_


## Recommendations

### Simulated Annealing

| Parameter | Value |
|---|---|
| `cooling_rate` | 0.985 |
| `iterations_per_temperature` | 100 |

_Mean F(X) = 0.9560 ± 0.0017, mean runtime = 2.78s, feasible = 100%_

### Genetic Algorithm

| Parameter | Value |
|---|---|
| `population_size` | 200 |
| `crossover_prob` | 0.95 |

_Mean F(X) = 0.9600 ± 0.0031, mean runtime = 2.49s, feasible = 100%_

### UMDA (EDA)

| Parameter | Value |
|---|---|
| `population_size` | 100 |
| `selection_ratio` | 0.3 |

_Mean F(X) = 0.9659 ± 0.0020, mean runtime = 2.49s, feasible = 100%_


## How to apply

1. Open `config.yaml`.
2. In the `algorithms:` section update each algorithm with the parameter values above.
3. Run the main experiment **without** `--tune`.
4. Optionally run `--sensitivity` to confirm the chosen values are in a robust region.
