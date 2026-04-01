from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import pandas as pd


@dataclass
class ProblemData:
    depot: pd.DataFrame
    customers: pd.DataFrame
    stations: pd.DataFrame
    distance_matrix: pd.DataFrame
    node_types: dict[str, str]


def load_problem_data(dataset_dir: str | Path) -> ProblemData:
    dataset_dir = Path(dataset_dir)

    depot = pd.read_csv(dataset_dir / "sf_depot.csv").copy()
    customers = pd.read_csv(dataset_dir / "sf_customers.csv").copy()
    stations = pd.read_csv(dataset_dir / "sf_charging_stations.csv").copy()
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

    node_types: dict[str, str] = {}

    for node_id in depot["Node ID"]:
        node_types[str(node_id)] = "depot"

    for node_id in customers["Node ID"]:
        node_types[str(node_id)] = "customer"

    for node_id in stations["Node ID"]:
        node_types[str(node_id)] = "station"

    distance_matrix.index = distance_matrix.index.map(str)
    distance_matrix.columns = distance_matrix.columns.map(str)

    return ProblemData(
        depot=depot,
        customers=customers,
        stations=stations,
        distance_matrix=distance_matrix,
        node_types=node_types,
    )