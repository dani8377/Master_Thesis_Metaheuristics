from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class ProblemData:
    depot: pd.DataFrame
    customers: pd.DataFrame
    stations: pd.DataFrame
    distance_matrix: pd.DataFrame          # kept for compatibility / inspection
    node_types: dict[str, str]

    # Fast lookup structures — built once at load time
    dist_array: np.ndarray = field(repr=False)   # NxN float64 numpy array (Haversine km)
    dist_index: dict[str, int] = field(repr=False)  # node_id -> row/col index
    station_price: dict[str, float] = field(repr=False)   # node_id -> USD/kWh
    station_power: dict[str, float] = field(repr=False)   # node_id -> kW
    energy_array: np.ndarray = field(repr=False)  # NxN float64 arc energy (kWh)


def load_problem_data(dataset_dir: str | Path) -> ProblemData:
    dataset_dir = Path(dataset_dir)

    depot    = pd.read_csv(dataset_dir / "sf_depot.csv").copy()
    customers = pd.read_csv(dataset_dir / "sf_customers.csv").copy()
    stations  = pd.read_csv(dataset_dir / "sf_charging_stations.csv").copy()
    distance_matrix = pd.read_csv(
        dataset_dir / "sf_distance_matrix_haversine.csv",
        index_col=0,
    ).copy()

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

    # Build fast numpy distance structures
    node_ids   = list(distance_matrix.index)
    dist_index = {nid: i for i, nid in enumerate(node_ids)}
    dist_array = distance_matrix.to_numpy(dtype=np.float64)

    # Build station attribute lookups once
    station_price: dict[str, float] = {}
    station_power: dict[str, float] = {}
    for _, row in stations.iterrows():
        nid = str(row["Node ID"])
        station_price[nid] = float(row["Cost (USD/kWh)"])
        station_power[nid] = float(row["Charging Capacity (kW)"])

    # Load precomputed energy matrix if available; fall back to flat rate
    energy_path = dataset_dir / "sf_energy_matrix.csv"
    if energy_path.exists():
        energy_df = pd.read_csv(energy_path, index_col=0)
        energy_df.index   = energy_df.index.map(str)
        energy_df.columns = energy_df.columns.map(str)
        energy_df = energy_df.reindex(index=node_ids, columns=node_ids, fill_value=0.0)
        energy_array = energy_df.to_numpy(dtype=np.float64)
    else:
        # Flat-rate fallback: 0.50 kWh/km — project still runs before data is fetched
        energy_array = dist_array * 0.50

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
    )
