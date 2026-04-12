from __future__ import annotations

from tools.data_loader import ProblemData
from tools.energy import EVParameters


def build_trivial_initial_solution(data: ProblemData) -> list[str]:
    customer_ids = data.customers["Customer ID"].tolist()
    return ["DEPOT", *customer_ids, "DEPOT"]


def build_nearest_neighbor_solution(data: ProblemData) -> list[str]:
    dist_array  = data.dist_array
    dist_index  = data.dist_index
    unvisited   = set(data.customers["Customer ID"].tolist())
    current     = "DEPOT"
    route       = ["DEPOT"]

    while unvisited:
        ci = dist_index[current]
        nxt = min(unvisited, key=lambda c: dist_array[ci, dist_index[c]])
        route.append(nxt)
        unvisited.remove(nxt)
        current = nxt

    route.append("DEPOT")
    return route


def build_ev_feasible_solution(data: ProblemData, ev_params: EVParameters) -> list[str]:
    """
    Build an EV-feasible initial solution:
    1. Start from the nearest-neighbor customer route.
    2. Simulate battery step by step.
    3. Insert a charging station proactively when battery after the next arc
       would drop below 50% capacity. Picks the nearest reachable station
       from the current node.
    4. After inserting and recharging, continue from the station.
    """
    route        = build_nearest_neighbor_solution(data)
    dist_array   = data.dist_array
    dist_index   = data.dist_index
    station_ids  = set(data.stations["Node ID"].tolist())
    all_stations = data.stations["Node ID"].tolist()
    consumption  = ev_params.energy_consumption_kwh_per_km
    capacity     = ev_params.battery_capacity_kwh
    threshold    = 0.5 * capacity

    battery = ev_params.initial_battery_kwh
    i = 0

    while i < len(route) - 1:
        origin = route[i]
        dest   = route[i + 1]

        oi = dist_index.get(origin)
        di = dist_index.get(dest)
        if oi is None or di is None:
            i += 1
            continue

        energy_to_dest = dist_array[oi, di] * consumption

        if (battery - energy_to_dest) < threshold:
            # Find nearest reachable station from origin
            best_station: str | None = None
            best_dist = float("inf")
            for s in all_stations:
                if s == dest:
                    continue
                si = dist_index.get(s)
                if si is None:
                    continue
                d = dist_array[oi, si]
                if d * consumption <= battery and d < best_dist:
                    best_station = s
                    best_dist = d

            if best_station is not None:
                route.insert(i + 1, best_station)
                battery -= best_dist * consumption
                battery  = capacity
                i += 1
                continue

        battery -= energy_to_dest
        battery  = max(battery, 0.0)

        if dest in station_ids:
            battery = capacity

        i += 1

    return route
