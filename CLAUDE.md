# EV Routing — Master's Thesis

## Running the project

Always run from the project root with `EV_routing` on the path:

```bash
PYTHONPATH=EV_routing python EV_routing/main.py
```

Rebuild datasets (only needed when nodes change — not when tuning energy parameters):

```bash
python EV_routing/scripts/build_instance.py
```

## Problem

Single-vehicle EVRP on a San Francisco instance: 1 depot, 75 customers, 30 charging stations (106 nodes total). Every customer must be visited exactly once. The vehicle starts and ends at the depot. Charging stations may be visited multiple times; each visit recharges to full. No time windows, no vehicle load capacity.

Route format: `list[str]` starting and ending with `"DEPOT"`, e.g. `["DEPOT", "C001", "EVS04656", "C002", "DEPOT"]`.

## Key data structures

- `ProblemData` (`tools/data_loader.py`) — loaded once, passed to everything. Fast numpy arrays: `dist_array` (road km), `energy_array` (arc kWh), `dist_index` (node → matrix index).
- `EVParameters` (`tools/battery.py`) — battery and energy model config. Defined once in `main.py`, passed to `load_problem_data` and all algorithms.
- `ObjectiveWeights` (`tools/objective.py`) — penalty weights for the objective function.
- `RouteEvaluation` (`tools/objective.py`) — result of `evaluate_route()`.

## Energy matrix

Computed at load time in `load_problem_data(dataset_dir, ev_params)` from three raw data files (`sf_distance_matrix.csv`, `sf_road_dur_s.csv`, `sf_node_elevations.csv`). Changing `grade_factor` or `speed_exponent` in `EVParameters` takes effect on next run — no script re-run needed.

## Objective function

Weighted sum (see `tools/objective.py`):
```
distance × w_dist
+ (travel_time + charging_time) × w_time
+ energy × w_energy
+ charging_cost × w_charging
+ battery_violation_kwh × w_battery_penalty   ← soft constraint
+ infeasible_visits × w_visit_penalty
```

## Adding a new algorithm

Algorithms live in `EV_routing/algorithms/`. Any algorithm must match this signature:

```python
def my_algorithm(
    data: ProblemData,
    ev_params: EVParameters,
    weights: ObjectiveWeights,
    **kwargs,
) -> tuple[list[str], RouteEvaluation, Any]:   # solution, eval, stats
```

Plug it into `main.py` alongside SA and pass it to `run_experiments()` for multi-seed comparison.

Shared building blocks in `tools/`:
- `initial_solution.py` — `build_ev_feasible_solution()` for a good starting point
- `neighborhoods.py` — `generate_neighbor()` and individual move operators
- `feasibility.py` — `is_valid_basic_route()`, `is_energy_feasible()`
- `evaluate_route()` — single objective call, O(route length)
