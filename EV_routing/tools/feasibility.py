from __future__ import annotations

from collections import Counter

from tools.data_loader import ProblemData


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

    customer_ids  = set(data.customers["Node ID"].tolist())
    station_ids   = set(data.stations["Node ID"].tolist())
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
    Hard EV feasibility check using fast numpy distance lookup.
    Returns False immediately if battery goes below zero on any arc.
    """
    dist_array  = data.dist_array
    dist_index  = data.dist_index
    station_ids = set(data.stations["Node ID"].tolist())

    battery_kwh = battery_capacity_kwh

    for i in range(len(route) - 1):
        origin      = route[i]
        destination = route[i + 1]

        oi = dist_index.get(origin)
        di = dist_index.get(destination)
        if oi is None or di is None:
            return False

        battery_kwh -= dist_array[oi, di] * energy_consumption_kwh_per_km
        if battery_kwh < 0:
            return False

        if destination in station_ids:
            battery_kwh = battery_capacity_kwh

    return True
