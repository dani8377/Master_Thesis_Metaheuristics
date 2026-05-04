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

    depot     = pd.read_csv(dataset_dir / "sf_depot.csv").copy()
    customers = pd.read_csv(dataset_dir / "sf_customers.csv").copy()
    stations  = pd.read_csv(dataset_dir / "sf_charging_stations.csv").copy()

    dist_path = dataset_dir / "sf_distance_matrix.csv"
    if not dist_path.exists():
        import warnings
        warnings.warn(
            f"OSRM distance matrix not found at {dist_path}. "
            "Falling back to Haversine distances — run build_instance.py to generate real road data.",
            stacklevel=2,
        )
        dist_path = dataset_dir / "sf_distance_matrix_haversine.csv"
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
    elev_path = dataset_dir / "sf_node_elevations.csv"
    dur_path  = dataset_dir / "sf_duration_matrix.csv"
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
        customer_ids=frozenset(all_customer_ids_list),
        station_ids=frozenset(all_station_ids_list),
        all_customer_ids=all_customer_ids_list,
        all_station_ids=all_station_ids_list,
        customer_matrix_idx=customer_matrix_idx,
        station_matrix_idx=station_matrix_idx,
    )
