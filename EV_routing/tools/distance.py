from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from math import radians, sin, cos, sqrt, atan2
from typing import Iterable, Optional

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Node:
    """
    Generic routing node.

    Attributes
    ----------
    node_id : str
        Unique node identifier.
    latitude : float
        Latitude in decimal degrees.
    longitude : float
        Longitude in decimal degrees.
    node_type : str
        E.g. 'depot', 'customer', 'station'.
    """
    node_id: str
    latitude: float
    longitude: float
    node_type: str = "generic"


class DistanceProvider(ABC):
    """
    Abstract base class for all distance backends.

    Later you can implement:
    - EuclideanDistanceProvider
    - HaversineDistanceProvider
    - RoadMatrixDistanceProvider
    - GoogleMapsDistanceProvider
    - OSRMDistanceProvider
    """

    @abstractmethod
    def distance(self, a: Node, b: Node) -> float:
        """
        Return distance between two nodes.
        """
        raise NotImplementedError

    def distance_matrix(self, nodes: Iterable[Node]) -> np.ndarray:
        """
        Build a full NxN distance matrix for a list of nodes.
        """
        nodes = list(nodes)
        n = len(nodes)
        matrix = np.zeros((n, n), dtype=float)

        for i in range(n):
            for j in range(n):
                if i == j:
                    matrix[i, j] = 0.0
                else:
                    matrix[i, j] = self.distance(nodes[i], nodes[j])

        return matrix


class EuclideanDistanceProvider(DistanceProvider):
    """
    Euclidean distance on latitude/longitude coordinates.

    This is simple and fast, but only an approximation.
    Good enough for the first thesis implementation.
    """

    def distance(self, a: Node, b: Node) -> float:
        return float(
            sqrt((a.latitude - b.latitude) ** 2 + (a.longitude - b.longitude) ** 2)
        )


class HaversineDistanceProvider(DistanceProvider):
    """
    Great-circle distance between two lat/lon points in kilometers.
    More realistic than Euclidean distance for geographic data.
    """

    EARTH_RADIUS_KM = 6371.0

    def distance(self, a: Node, b: Node) -> float:
        lat1, lon1 = radians(a.latitude), radians(a.longitude)
        lat2, lon2 = radians(b.latitude), radians(b.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        h = (
            sin(dlat / 2) ** 2
            + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        )
        c = 2 * atan2(sqrt(h), sqrt(1 - h))

        return float(self.EARTH_RADIUS_KM * c)


class PrecomputedMatrixDistanceProvider(DistanceProvider):
    """
    Distance provider backed by a precomputed matrix.

    Useful later if you get distances from Google API / OSRM / road data.
    """

    def __init__(self, node_ids: list[str], matrix: np.ndarray):
        if matrix.shape[0] != matrix.shape[1]:
            raise ValueError("Distance matrix must be square.")
        if matrix.shape[0] != len(node_ids):
            raise ValueError("Number of node_ids must match matrix size.")

        self.node_ids = node_ids
        self.matrix = matrix
        self.index = {node_id: i for i, node_id in enumerate(node_ids)}

    def distance(self, a: Node, b: Node) -> float:
        try:
            i = self.index[a.node_id]
            j = self.index[b.node_id]
        except KeyError as exc:
            raise KeyError(f"Node not found in precomputed matrix: {exc}") from exc

        return float(self.matrix[i, j])


def dataframe_to_nodes(
    df: pd.DataFrame,
    id_col: str,
    lat_col: str = "Latitude",
    lon_col: str = "Longitude",
    type_col: Optional[str] = None,
    default_type: str = "generic",
) -> list[Node]:
    """
    Convert a pandas DataFrame to a list of Node objects.
    """
    required = {id_col, lat_col, lon_col}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    nodes: list[Node] = []

    for _, row in df.iterrows():
        node_type = row[type_col] if type_col and type_col in df.columns else default_type
        nodes.append(
            Node(
                node_id=str(row[id_col]),
                latitude=float(row[lat_col]),
                longitude=float(row[lon_col]),
                node_type=str(node_type),
            )
        )

    return nodes


def combine_node_dataframes(
    depot_df: pd.DataFrame,
    customers_df: pd.DataFrame,
    stations_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Standardize depot, customer, and station DataFrames into one node table.
    """
    depot = depot_df.copy()
    customers = customers_df.copy()
    stations = stations_df.copy()

    depot = depot.rename(columns={"Node ID": "Node ID"})
    if "Node ID" not in depot.columns:
        depot["Node ID"] = "DEPOT"
    depot["Node Type"] = "depot"

    if "Node ID" not in customers.columns:
        if "Customer ID" not in customers.columns:
            raise ValueError("Customers must contain either 'Node ID' or 'Customer ID'.")
        customers = customers.rename(columns={"Customer ID": "Node ID"})
    customers["Node Type"] = "customer"

    if "Node ID" not in stations.columns:
        if "Station ID" not in stations.columns:
            raise ValueError("Stations must contain either 'Node ID' or 'Station ID'.")
        stations = stations.rename(columns={"Station ID": "Node ID"})
    stations["Node Type"] = "station"

    cols = ["Node ID", "Latitude", "Longitude", "Node Type"]

    return pd.concat(
        [
            depot[cols],
            customers[cols],
            stations[cols],
        ],
        ignore_index=True,
    )


def build_distance_matrix(
    nodes_df: pd.DataFrame,
    provider: DistanceProvider,
    id_col: str = "Node ID",
    lat_col: str = "Latitude",
    lon_col: str = "Longitude",
    type_col: str = "Node Type",
) -> tuple[list[Node], np.ndarray]:
    """
    Convert node table into nodes and compute a full distance matrix.
    """
    nodes = dataframe_to_nodes(
        nodes_df,
        id_col=id_col,
        lat_col=lat_col,
        lon_col=lon_col,
        type_col=type_col,
    )
    matrix = provider.distance_matrix(nodes)
    return nodes, matrix


def distance_matrix_to_dataframe(nodes: list[Node], matrix: np.ndarray) -> pd.DataFrame:
    """
    Convert a distance matrix to a labeled pandas DataFrame.
    """
    node_ids = [node.node_id for node in nodes]
    return pd.DataFrame(matrix, index=node_ids, columns=node_ids)