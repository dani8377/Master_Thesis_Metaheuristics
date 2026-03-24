from __future__ import annotations

from collections import Counter

from tools.data_loader import ProblemData
from tools.energy import energy_needed_kwh


def is_valid_basic_route(route: list[str], data: ProblemData) -> bool:
    """
    Structural route validation:
    - starts and ends at DEPOT
    - contains only known nodes
    - visits every customer exactly once
    """

    if len(route) < 2:
        return False

    if route[0] != "DEPOT" or route[-1] != "DEPOT":
        return False

    customer_ids = set(data.customers["Node ID"].tolist())
    station_ids = set(data.stations["Node ID"].tolist())
    allowed_nodes = {"DEPOT"} | customer_ids | station_ids

    if any(node not in allowed_nodes for node in route):
        return False

    visited_customers = [node for node in route if node in customer_ids]
    counts = Counter(visited_customers)

    if any(count != 1 for count in counts.values()):
        return False

    if set(visited_customers) != customer_ids:
        return False

    return True


def is_energy_feasible(
    route: list[str],
    data: ProblemData,
    battery_capacity_kwh: float,
    energy_consumption_kwh_per_km: float,
) -> bool:
    """
    Hard EV feasibility:
    - vehicle starts full
    - battery decreases on each arc
    - arriving at a station recharges to full
    - returns False immediately if battery goes below zero
    """

    battery_kwh = battery_capacity_kwh
    distance_matrix = data.distance_matrix
    station_ids = set(data.stations["Node ID"].tolist())

    for i in range(len(route) - 1):
        origin = route[i]
        destination = route[i + 1]

        if origin not in distance_matrix.index or destination not in distance_matrix.columns:
            return False

        distance_km = float(distance_matrix.loc[origin, destination])
        energy_kwh = energy_needed_kwh(distance_km, energy_consumption_kwh_per_km)

        battery_kwh -= energy_kwh
        if battery_kwh < 0:
            return False

        if destination in station_ids:
            battery_kwh = battery_capacity_kwh

    return True