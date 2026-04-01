from __future__ import annotations

from tools.data_loader import ProblemData
from tools.energy import EVParameters


def build_trivial_initial_solution(data: ProblemData) -> list[str]:
    customer_ids = data.customers["Customer ID"].tolist()
    return ["DEPOT", *customer_ids, "DEPOT"]


def build_nearest_neighbor_solution(data: ProblemData) -> list[str]:
    dm = data.distance_matrix
    unvisited = set(data.customers["Customer ID"].tolist())
    current = "DEPOT"
    route = ["DEPOT"]
    while unvisited:
        nxt = min(unvisited, key=lambda c: dm.loc[current, c])
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
    3. Before any arc that would deplete the battery, insert the nearest
       reachable charging station. Recharge to full at every station visit.
    4. If no reachable station exists for a violation, leave it (the
       objective penalty will guide SA to fix it).
    """
    route = build_nearest_neighbor_solution(data)
    dm = data.distance_matrix
    station_ids = set(data.stations["Node ID"].tolist())
    all_station_ids = data.stations["Node ID"].tolist()
    consumption = ev_params.energy_consumption_kwh_per_km

    battery = ev_params.initial_battery_kwh
    i = 0

    while i < len(route) - 1:
        origin = route[i]
        dest = route[i + 1]

        if origin not in dm.index or dest not in dm.columns:
            i += 1
            continue

        energy = float(dm.loc[origin, dest]) * consumption

        if battery - energy < 0:
            best_station: str | None = None
            best_dist = float("inf")
            for s in all_station_ids:
                if s not in dm.columns or origin not in dm.index:
                    continue
                d = float(dm.loc[origin, s])
                if d * consumption <= battery and d < best_dist:
                    best_station = s
                    best_dist = d

            if best_station is not None:
                route.insert(i + 1, best_station)
                # Do not advance i — re-process origin → best_station next
                continue
            else:
                # No reachable station; skip and let penalty handle it
                i += 1
                continue

        battery -= energy
        if dest in station_ids:
            battery = ev_params.battery_capacity_kwh
        i += 1

    return route
