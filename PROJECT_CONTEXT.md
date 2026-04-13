# Master's Thesis — EV Routing Project Context

This document fully describes a Python metaheuristics project for the Electric Vehicle
Routing Problem (EVRP). Paste this at the start of a new conversation for full context.

---

## 1. Project Goal

A Master's thesis comparing metaheuristic algorithms (Simulated Annealing, Tabu Search,
and potentially ACO/GA/EDA) on the Electric Vehicle Routing Problem. The comparison is
based on solution quality, convergence behaviour, and runtime. All algorithms share the
same instance, objective function, and neighbourhood operators so results are directly
comparable.

---

## 2. Instance

A synthetic San Francisco instance generated from real EV charging station data.

| Element | Count | ID format |
|---------|-------|-----------|
| Depot | 1 | `"DEPOT"` |
| Customers | 75 | `"C001"` … `"C075"` |
| Charging stations | 30 | `"EVSxxxxx"` |

All nodes have (latitude, longitude) coordinates in the San Francisco Bay Area.
Distances are computed with the **Haversine formula** and stored in a precomputed
N×N matrix (`sf_distance_matrix_haversine.csv`). Values range from ~0.2 km to ~27 km.

---

## 3. Problem Formulation

**Decision variable:** a single route σ — an ordered list of node IDs starting and
ending at the depot, visiting every customer exactly once, with zero or more charging
station visits interspersed:

```
σ = [DEPOT, C003, EVS04330, C011, ..., C042, DEPOT]
```

Charging stations may be visited multiple times; customers must be visited exactly once.

### 3.1 EV Parameters

```python
battery_capacity_kwh          = 20.0   # maximum charge
initial_battery_kwh           = 20.0   # starts full
energy_consumption_kwh_per_km = 0.50   # linear consumption
average_speed_kmh             = 50.0   # constant speed
```

The EV departs full. Energy consumed on arc (i→j):

```
energy_ij = distance_km(i,j) × 0.50
```

Travel time on arc (i→j):

```
time_ij = distance_km(i,j) / 50.0
```

### 3.2 Charging Behaviour

When the EV visits a charging station the implementation charges **to full** by default
(`charge_to_full=True`). Each station has:

- **Charging capacity (kW):** determines charging speed (range: ~22–150 kW)
- **Cost (USD/kWh):** price paid per kWh charged (range: ~0.24–0.44 USD/kWh)

Charging time at a station:

```
charging_time_h = energy_charged_kwh / power_kw
```

Charging cost:

```
charging_cost_usd = energy_charged_kwh × price_per_kwh
```

---

## 4. Objective Function

A **weighted penalty sum** that combines real cost components with soft penalty terms
for constraint violations. This allows infeasible solutions to be explored during search.

```
F(σ) = w_dist   × total_distance_km
     + w_time   × (total_travel_time_h + total_charging_time_h)
     + w_energy × total_energy_consumed_kwh
     + w_cost   × total_charging_cost_usd
     + w_bat    × battery_violation_kwh
     + w_inf    × infeasible_visits
```

### Current weights

| Weight | Value | Purpose |
|--------|-------|---------|
| `distance_weight` | 1.0 | minimise total route distance |
| `travel_time_weight` | 10.0 | includes charging stops in time cost |
| `energy_weight` | 2.0 | penalise energy use (redundant with distance at fixed consumption rate) |
| `charging_cost_weight` | 20.0 | penalise expensive charging |
| `battery_violation_weight` | 10000.0 | soft penalty: kWh below zero on any arc |
| `infeasible_visit_weight` | 5000.0 | soft penalty: structural violations (unknown node, zero-power station) |

**Feasibility:** `battery_violation_kwh == 0` AND `infeasible_visits == 0`.

**Note:** `energy_weight` and `distance_weight` are linearly dependent since consumption
rate is constant. Both are kept explicitly so each cost component can be inspected
separately.

### RouteEvaluation dataclass (returned by evaluate_route)

```python
@dataclass
class RouteEvaluation:
    total_distance_km: float
    total_travel_time_h: float
    total_charging_time_h: float
    total_energy_consumed_kwh: float
    total_charging_cost_usd: float
    battery_violation_kwh: float
    infeasible_visits: int
    objective_value: float
    feasible: bool
```

---

## 5. Data Structures

### ProblemData (loaded once, passed to all functions)

```python
@dataclass
class ProblemData:
    depot: pd.DataFrame
    customers: pd.DataFrame          # columns: Customer ID, Latitude, Longitude, Node ID
    stations: pd.DataFrame           # columns: Station ID, Latitude, Longitude,
                                     #   Charging Capacity (kW), Cost (USD/kWh), ...
    distance_matrix: pd.DataFrame    # kept for inspection / compatibility
    node_types: dict[str, str]       # node_id -> "depot" | "customer" | "station"

    # Fast lookup structures (built once at load time — use these in hot loops)
    dist_array: np.ndarray           # NxN float64, indexed by dist_index
    dist_index: dict[str, int]       # node_id -> row/col index into dist_array
    station_price: dict[str, float]  # node_id -> USD/kWh
    station_power: dict[str, float]  # node_id -> kW
```

**Performance rule:** always use `dist_array[oi, di]` (numpy index) instead of
`distance_matrix.loc[origin, destination]` (pandas label lookup). The numpy path is
~90× faster and is what all current code uses.

---

## 6. File Structure

```
EV_routing/
├── main.py                          # entry point — runs SA + 10-seed experiment
├── algorithms/
│   └── simmulated_annealing.py      # SA implementation (note typo in filename)
├── tools/
│   ├── data_loader.py               # load_problem_data(), ProblemData
│   ├── energy.py                    # EVParameters dataclass, helper functions
│   ├── objective.py                 # evaluate_route(), ObjectiveWeights, RouteEvaluation
│   ├── feasibility.py               # is_valid_basic_route(), is_energy_feasible()
│   ├── initial_solution.py          # build_ev_feasible_solution() (main), build_nearest_neighbor_solution()
│   ├── neighborhoods.py             # generate_neighbor() + all move operators
│   ├── experiment.py                # run_experiments(), ExperimentResults
│   └── plot.py                      # plot_convergence(), print_comparison_table()
├── datasets/
│   ├── sf_depot.csv
│   ├── sf_customers.csv             # 75 customers
│   ├── sf_charging_stations.csv     # 30 stations
│   └── sf_distance_matrix_haversine.csv   # 106×106 Haversine distance matrix
└── figures/
    ├── sf_instance_map.png
    └── sa_convergence.png
```

Run from the project root (parent of `EV_routing/`):
```bash
python -m EV_routing.main   # or: python EV_routing/main.py
```

---

## 7. Initial Solution

`build_ev_feasible_solution(data, ev_params)` in `tools/initial_solution.py`:

1. Build a nearest-neighbour customer route (greedy, always go to closest unvisited customer).
2. Simulate battery arc-by-arc along that route.
3. **Proactively** insert a charging station when `(battery - energy_to_next) < 0.5 × capacity`.
   Picks the nearest reachable station from the current node (reachable = can get there on remaining charge).
4. After inserting a station, reset battery to full and continue.

This produces a valid, EV-feasible starting route with stations already inserted.

---

## 8. Feasibility Checks

Two separate checks used at different points:

**Structural (`is_valid_basic_route`):**
- Route starts and ends at `"DEPOT"`
- All nodes are known (in depot ∪ customers ∪ stations)
- Every customer visited exactly once

**Energy (`is_energy_feasible`):**
- Battery never goes negative on any arc
- Battery is reset to full when visiting a station

The SA algorithm checks structural feasibility on every candidate before evaluating it.
Energy infeasibility is handled via soft penalty in the objective (not hard rejection).

---

## 9. Neighbourhood Operators

All operators have the signature `(route, data, ev_params) -> new_route`.

| Operator | Category | What it does |
|----------|----------|-------------|
| `swap_customers` | classic | Swap two customer nodes |
| `relocate_customer` | classic | Remove a customer, reinsert elsewhere |
| `two_opt` | classic | Reverse a random interior subsequence |
| `insert_charging_station` | EV-insert | Insert a random station at a random position |
| `repair_battery_violation` | EV-insert | Find first arc where battery goes negative, insert nearest reachable station |
| `remove_charging_station` | EV-modify | Remove a random station from the route |
| `replace_charging_station` | EV-modify | Swap a station for a different one |
| `move_charging_station` | EV-modify | Remove a station, reinsert at different position |

`generate_neighbor()` selects uniformly from: classic + EV-insert + (EV-modify only if
route already contains at least one station).

---

## 10. Simulated Annealing

File: `algorithms/simmulated_annealing.py`

### Parameters (current calibrated values)

```python
initial_temperature       = 400.0    # ~80% acceptance of median worsening move
cooling_rate              = 0.995    # geometric cooling: T *= 0.995 each step
min_temperature           = 1e-3
iterations_per_temperature = 50      # Markov chain length at each temperature
max_temp_steps            = 3000     # hard stop: 400 → 0.001 needs ~2635 steps
reheat_patience           = 3000     # effectively disabled (no reheat until full cooldown)
reheat_factor             = 0.4
```

### Algorithm structure

```
current ← build_ev_feasible_solution()
for each temperature step (up to max_temp_steps):
    for each of iterations_per_temperature attempts:
        candidate ← generate_neighbor(current)
        if not is_valid_basic_route(candidate): reject (structural)
        evaluate candidate
        if improving: accept
        else if random() < exp(-delta / T): accept (Metropolis)
        track best seen
    T *= cooling_rate
    if no improvement for reheat_patience steps: T = reheat_factor × T0
return best_solution, best_evaluation, SAStatistics
```

### SAStatistics (returned alongside solution)

```python
best_cost_history: list[float]      # best objective per temperature step
current_cost_history: list[float]   # current objective per temperature step
temperature_history: list[float]
total_evaluated: int
total_improving_accepted: int
total_worsening_accepted: int
total_rejected_structural: int
total_feasible_evaluated: int
reheat_count: int
final_temperature: float
# properties:
acceptance_rate: float              # (improving + worsening) / evaluated
feasibility_rate: float             # feasible / evaluated
```

---

## 11. Experiment Infrastructure

`run_experiments(algorithm, algorithm_name, data, ev_params, weights, seeds, verbose, **algorithm_kwargs)`

- Runs the algorithm once per seed in `seeds` (e.g. `range(10)`)
- Sets `random.seed(seed)` before each run
- Times each run with `time.perf_counter()`
- Returns `ExperimentResults` with properties: `best_cost`, `average_cost`, `worst_cost`, `std_cost`, `feasible_run_count`, `average_runtime`, `best_seed`, `best_solution`

`print_comparison_table(results_list)` prints a formatted table:
`Algorithm | Best | Average | Worst | Std | Feasible | AvgTime`

`plot_convergence(results, title, save_path, show)` plots mean best-cost ± std band
across all seeds.

---

## 12. Typical Output (10-seed SA run)

```
Route: ['DEPOT', 'C047', 'EVS03163', 'C012', ..., 'DEPOT']
Feasible:                True
Objective value:         ~420
Total distance (km):     ~85
Total travel time (h):   ~1.7
Total charging time (h): ~0.8
Total energy (kWh):      ~42
Total charging cost ($):  ~8
Battery violation (kWh): 0.0
Infeasible visits:       0
Runtime:                 ~6–7s per run
```

The SA typically improves from the initial EV-feasible solution (~690) down to ~420
(~38% improvement) within the cooling schedule.
