from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from tools.battery import EVParameters


@dataclass
class ProblemData:
    depot: pd.DataFrame
    customers: pd.DataFrame
    stations: pd.DataFrame
    distance_matrix: pd.DataFrame          # kept for compatibility / inspection
    node_types: dict[str, str]

    # Fast lookup structures — built once at load time
    dist_array: np.ndarray = field(repr=False)    # NxN float64, road km
    dist_index: dict[str, int] = field(repr=False)  # node_id -> row/col index
    station_price: dict[str, float] = field(repr=False)   # node_id -> USD/kWh
    station_power: dict[str, float] = field(repr=False)   # node_id -> kW
    energy_array: np.ndarray = field(repr=False)  # NxN float64, arc energy kWh
    dur_array: np.ndarray = field(repr=False)     # NxN float64, arc travel time in seconds (0 = unknown)

    # Precomputed sets/index arrays — avoid repeated pandas access in hot loops
    customer_ids: frozenset[str] = field(repr=False)      # O(1) membership test
    station_ids: frozenset[str] = field(repr=False)
    all_customer_ids: list[str] = field(repr=False)       # ordered, matches customer_matrix_idx
    all_station_ids: list[str] = field(repr=False)        # ordered, matches station_matrix_idx
    customer_matrix_idx: np.ndarray = field(repr=False)   # customer pos → dist_array index
    station_matrix_idx: np.ndarray = field(repr=False)    # station pos  → dist_array index


def _build_energy_matrix(
    node_ids: list[str],
    dist_km: np.ndarray,
    dur_s: np.ndarray,
    elevations_m: dict[str, float],
    ev_params: EVParameters,
) -> np.ndarray:
    """
    Compute the NxN arc energy matrix (kWh) from road geometry and EV parameters.

    E(i,j) = dist_km × base_consumption × grade_multiplier × speed_multiplier

    grade_multiplier = max(0.1, 1 + grade_factor × slope)
        slope = Δelevation_m / road_dist_m   (dimensionless rise-over-run)

    speed_multiplier = (speed_kmh / average_speed_kmh) ^ speed_exponent
        speed_kmh = road_dist_m / duration_s × 3.6
    """
    n      = len(node_ids)
    energy = np.zeros((n, n), dtype=np.float64)

    for i in range(n):
        elev_i = elevations_m.get(node_ids[i], 0.0)
        for j in range(n):
            if i == j:
                continue
            d_km = dist_km[i, j]
            if d_km <= 0.0:
                continue
            t_s   = dur_s[i, j]
            speed = (d_km * 1000.0 / t_s) * 3.6 if t_s > 0 else ev_params.average_speed_kmh

            slope      = (elevations_m.get(node_ids[j], 0.0) - elev_i) / (d_km * 1000.0)
            grade_mult = max(0.1, 1.0 + ev_params.grade_factor * slope)
            speed_mult = (speed / ev_params.average_speed_kmh) ** ev_params.speed_exponent

            energy[i, j] = d_km * ev_params.energy_consumption_kwh_per_km * grade_mult * speed_mult

    return energy


def load_problem_data(dataset_dir: str | Path, ev_params: EVParameters) -> ProblemData:
    dataset_dir = Path(dataset_dir)

    depot     = pd.read_csv(dataset_dir / "depot.csv").copy()
    customers = pd.read_csv(dataset_dir / "customers.csv").copy()
    stations  = pd.read_csv(dataset_dir / "charging_stations.csv").copy()

    dist_path = dataset_dir / "distance_matrix.csv"
    if not dist_path.exists():
        import warnings
        warnings.warn(
            f"OSRM distance matrix not found at {dist_path}. "
            "Falling back to Haversine distances — run build_instance.py to generate real road data.",
            stacklevel=2,
        )
        dist_path = dataset_dir / "distance_matrix_haversine.csv"
    distance_matrix = pd.read_csv(dist_path, index_col=0).copy()

    if "Node ID" not in depot.columns:
        depot["Node ID"] = "DEPOT"
    if "Node ID" not in customers.columns:
        customers["Node ID"] = customers["Customer ID"]
    if "Node ID" not in stations.columns:
        stations["Node ID"] = stations["Station ID"]

    distance_matrix.index   = distance_matrix.index.map(str)
    distance_matrix.columns = distance_matrix.columns.map(str)

    node_types: dict[str, str] = {}
    for node_id in depot["Node ID"]:
        node_types[str(node_id)] = "depot"
    for node_id in customers["Node ID"]:
        node_types[str(node_id)] = "customer"
    for node_id in stations["Node ID"]:
        node_types[str(node_id)] = "station"

    node_ids   = list(distance_matrix.index)
    dist_index = {nid: i for i, nid in enumerate(node_ids)}
    dist_array = distance_matrix.to_numpy(dtype=np.float64)

    station_price: dict[str, float] = {}
    station_power: dict[str, float] = {}
    for _, row in stations.iterrows():
        nid = str(row["Node ID"])
        station_price[nid] = float(row["Cost (USD/kWh)"])
        station_power[nid] = float(row["Charging Capacity (kW)"])

    # Build energy matrix from raw road data + ev_params (single source of truth).
    # Falls back to a flat rate if the road data files haven't been generated yet.
    elev_path = dataset_dir / "node_elevations.csv"
    dur_path  = dataset_dir / "duration_matrix.csv"
    if elev_path.exists() and dur_path.exists():
        elev_df = pd.read_csv(elev_path).set_index("Node ID")
        elev_df.index = elev_df.index.map(str)
        elevations_m = {
            nid: float(elev_df.loc[nid, "Elevation_m"]) if nid in elev_df.index else 0.0
            for nid in node_ids
        }

        dur_df = pd.read_csv(dur_path, index_col=0)
        dur_df.index   = dur_df.index.map(str)
        dur_df.columns = dur_df.columns.map(str)
        dur_df = dur_df.reindex(index=node_ids, columns=node_ids, fill_value=0.0)
        dur_s  = dur_df.to_numpy(dtype=np.float64)

        energy_array = _build_energy_matrix(node_ids, dist_array, dur_s, elevations_m, ev_params)
    else:
        # Flat-rate fallback — runs before build_instance.py has been executed
        energy_array = dist_array * ev_params.energy_consumption_kwh_per_km
        dur_s = np.zeros_like(dist_array)

    # Precomputed sets and index arrays (used by neighborhoods / feasibility hot paths)
    all_customer_ids_list = [str(c) for c in customers["Node ID"].tolist() if str(c) in dist_index]
    all_station_ids_list  = [str(s) for s in stations["Node ID"].tolist()  if str(s) in dist_index]
    customer_matrix_idx = np.array([dist_index[c] for c in all_customer_ids_list], dtype=np.intp)
    station_matrix_idx  = np.array([dist_index[s] for s in all_station_ids_list],  dtype=np.intp)

    return ProblemData(
        depot=depot,
        customers=customers,
        stations=stations,
        distance_matrix=distance_matrix,
        node_types=node_types,
        dist_array=dist_array,
        dist_index=dist_index,
        station_price=station_price,
        station_power=station_power,
        energy_array=energy_array,
        dur_array=dur_s,
        customer_ids=frozenset(all_customer_ids_list),
        station_ids=frozenset(all_station_ids_list),
        all_customer_ids=all_customer_ids_list,
        all_station_ids=all_station_ids_list,
        customer_matrix_idx=customer_matrix_idx,
        station_matrix_idx=station_matrix_idx,
    )


def subsample_problem_data(
    data: ProblemData,
    n_customers: int,
    seed: int = 42,
) -> ProblemData:
    """
    Return a new ProblemData containing only ``n_customers`` of the original
    customers using farthest-point spatial sampling on lat/lon coordinates.
    All charging stations and the depot are kept intact.

    Farthest-point sampling ensures geographic spread: start with a random
    customer, then repeatedly pick the customer farthest from the already-
    selected set.  This avoids clustered subsets that create degenerate
    routing problems at small N.

    Subsets are nested (seed controls the initial point).
    """
    import random as _random

    n = min(n_customers, len(data.all_customer_ids))
    if n == len(data.all_customer_ids):
        return data

    # Build lat/lon coordinate array aligned with all_customer_ids ordering
    cust_df = data.customers.copy()
    cust_df["Node ID"] = cust_df["Node ID"].astype(str)
    cust_df = cust_df.set_index("Node ID")

    all_ids = data.all_customer_ids
    n_total = len(all_ids)
    coords = np.array(
        [[float(cust_df.loc[c, "Latitude"]), float(cust_df.loc[c, "Longitude"])]
         for c in all_ids],
        dtype=np.float64,
    )

    # Farthest-point sampling: start at a random customer, greedily add
    # the customer that maximises the minimum distance to all selected so far.
    rng = _random.Random(seed)
    selected_idx: list[int] = [rng.randrange(n_total)]
    min_dists = np.full(n_total, np.inf)

    for _ in range(n - 1):
        last = selected_idx[-1]
        d = np.linalg.norm(coords - coords[last], axis=1)
        np.minimum(min_dists, d, out=min_dists)
        min_dists[selected_idx] = 0.0   # already selected — never re-pick
        selected_idx.append(int(np.argmax(min_dists)))

    selected = [all_ids[i] for i in selected_idx]
    selected_set = frozenset(selected)

    new_customers = data.customers[
        data.customers["Node ID"].astype(str).isin(selected_set)
    ].reset_index(drop=True)

    new_customer_matrix_idx = np.array(
        [data.dist_index[c] for c in selected], dtype=np.intp
    )

    return ProblemData(
        depot=data.depot,
        customers=new_customers,
        stations=data.stations,
        distance_matrix=data.distance_matrix,
        node_types=data.node_types,
        dist_array=data.dist_array,
        dist_index=data.dist_index,
        station_price=data.station_price,
        station_power=data.station_power,
        energy_array=data.energy_array,
        dur_array=data.dur_array,
        customer_ids=selected_set,
        station_ids=data.station_ids,
        all_customer_ids=selected,
        all_station_ids=data.all_station_ids,
        customer_matrix_idx=new_customer_matrix_idx,
        station_matrix_idx=data.station_matrix_idx,
    )
