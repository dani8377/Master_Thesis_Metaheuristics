from __future__ import annotations

from tools.data_loader import ProblemData
from tools.battery import EVParameters


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
    energy_array = data.energy_array
    station_ids  = set(data.stations["Node ID"].tolist())
    all_stations = data.stations["Node ID"].tolist()
    capacity     = ev_params.battery_capacity_kwh
    threshold    = 0.5 * capacity

    battery = ev_params.initial_battery_kwh
    i = 0
    skip_threshold_check = False  # prevents re-triggering insertion on the arc right after a station

    while i < len(route) - 1:
        origin = route[i]
        dest   = route[i + 1]

        oi = dist_index.get(origin)
        di = dist_index.get(dest)
        if oi is None or di is None:
            skip_threshold_check = False
            i += 1
            continue

        energy_to_dest = energy_array[oi, di]

        if (battery - energy_to_dest) < threshold and not skip_threshold_check:
            # Primary: find nearest reachable station from origin.
            # Fallback: find nearest station by distance even if not reachable —
            # this ensures a stop is always inserted so the vehicle does not
            # silently run dry across multiple arcs (creating many violations).
            best_station: str | None = None
            best_dist = float("inf")
            fallback_station: str | None = None
            fallback_dist = float("inf")

            for s in all_stations:
                if s == dest:
                    continue
                si = dist_index.get(s)
                if si is None:
                    continue
                d_km = dist_array[oi, si]
                if d_km < fallback_dist:
                    fallback_dist    = d_km
                    fallback_station = s
                if energy_array[oi, si] <= battery and d_km < best_dist:
                    best_station = s
                    best_dist    = d_km

            station_to_insert = best_station if best_station is not None else fallback_station

            if station_to_insert is not None:
                si = dist_index[station_to_insert]
                route.insert(i + 1, station_to_insert)
                battery = max(0.0, battery - energy_array[oi, si])
                battery = capacity
                skip_threshold_check = True
                i += 1
                continue

        skip_threshold_check = False
        battery -= energy_to_dest
        battery  = max(battery, 0.0)

        if dest in station_ids:
            battery = capacity

        i += 1

    return route


def repair_ev_route(route: list[str], data: ProblemData, ev_params: EVParameters) -> list[str]:
    """
    Post-processing repair: scan for battery violations and insert stations
    until no violations remain (or no further improvement is possible).

    Unlike build_ev_feasible_solution, this operates on an already-built route
    and fixes actual violations (battery < energy_needed) rather than triggering
    on a threshold. Guarantees feasibility as long as every individual arc is
    reachable from a full battery.
    """
    dist_index   = data.dist_index
    energy_array = data.energy_array
    dist_array   = data.dist_array
    capacity     = ev_params.battery_capacity_kwh
    station_ids  = data.station_ids
    all_stations = data.all_station_ids

    for _ in range(len(route) * 2):
        battery  = ev_params.initial_battery_kwh
        inserted = False

        for i in range(len(route) - 1):
            origin = route[i]
            dest   = route[i + 1]
            oi = dist_index.get(origin)
            di = dist_index.get(dest)
            if oi is None or di is None:
                continue

            e = energy_array[oi, di]
            if battery < e:
                best_s: str | None = None
                best_d = float("inf")
                fallback_s: str | None = None
                fallback_d = float("inf")

                for s in all_stations:
                    if s == dest or s == origin:
                        continue
                    si = dist_index.get(s)
                    if si is None:
                        continue
                    e_to_s = energy_array[oi, si]
                    d      = dist_array[oi, si]
                    if d < fallback_d:
                        fallback_s, fallback_d = s, d
                    if e_to_s <= battery and d < best_d:
                        best_s, best_d = s, d

                insert_s = best_s if best_s is not None else fallback_s
                if insert_s is not None:
                    route.insert(i + 1, insert_s)
                    inserted = True
                    break

            battery = max(0.0, battery - e)
            if dest in station_ids:
                battery = capacity

        if not inserted:
            break

    return route
