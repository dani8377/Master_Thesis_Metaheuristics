from __future__ import annotations

import random

import numpy as np

from tools.data_loader import ProblemData
from tools.battery import EVParameters


# ---------------------------------------------------------------------------
# Classic route-improvement operators (customer-aware)
# ---------------------------------------------------------------------------

def swap_customers(route: list[str], data: ProblemData, ev_params: EVParameters) -> list[str]:
    """Swap two customer nodes. Leaves depot and station positions untouched."""
    new_route    = route[:]
    customer_ids = data.customer_ids
    positions    = [i for i, n in enumerate(new_route) if n in customer_ids]
    if len(positions) < 2:
        return new_route
    i, j = random.sample(positions, 2)
    new_route[i], new_route[j] = new_route[j], new_route[i]
    return new_route


def relocate_customer(route: list[str], data: ProblemData, ev_params: EVParameters) -> list[str]:
    """Remove a random customer and reinsert it at a different position."""
    new_route    = route[:]
    customer_ids = data.customer_ids
    positions    = [i for i, n in enumerate(new_route) if n in customer_ids]
    if not positions:
        return new_route
    i    = random.choice(positions)
    node = new_route.pop(i)
    valid = list(range(1, len(new_route)))
    if not valid:
        new_route.insert(i, node)
        return new_route
    new_route.insert(random.choice(valid), node)
    return new_route


def two_opt(route: list[str], data: ProblemData, ev_params: EVParameters) -> list[str]:
    """Reverse a random interior subsequence."""
    new_route = route[:]
    if len(new_route) < 4:
        return new_route
    i, j = sorted(random.sample(range(1, len(new_route) - 1), 2))
    new_route[i : j + 1] = list(reversed(new_route[i : j + 1]))
    return new_route


# ---------------------------------------------------------------------------
# EV-specific neighborhood operators
# ---------------------------------------------------------------------------

def insert_charging_station(route: list[str], data: ProblemData, ev_params: EVParameters) -> list[str]:
    """Insert a randomly chosen charging station at a random interior position."""
    new_route    = route[:]
    all_stations = data.all_station_ids
    if not all_stations:
        return new_route
    new_route.insert(random.randint(1, len(new_route) - 1), random.choice(all_stations))
    return new_route


def remove_charging_station(route: list[str], data: ProblemData, ev_params: EVParameters) -> list[str]:
    """Remove a random charging station from the route."""
    new_route    = route[:]
    station_ids  = data.station_ids
    positions    = [i for i, n in enumerate(new_route) if n in station_ids]
    if not positions:
        return new_route
    new_route.pop(random.choice(positions))
    return new_route


def replace_charging_station(route: list[str], data: ProblemData, ev_params: EVParameters) -> list[str]:
    """Replace a station in the route with a different one."""
    new_route    = route[:]
    all_stations = data.all_station_ids
    if len(all_stations) < 2:
        return new_route
    station_ids = data.station_ids
    positions   = [i for i, n in enumerate(new_route) if n in station_ids]
    if not positions:
        return insert_charging_station(route, data, ev_params)
    pos        = random.choice(positions)
    candidates = [s for s in all_stations if s != new_route[pos]]
    if not candidates:
        return new_route
    new_route[pos] = random.choice(candidates)
    return new_route


def move_charging_station(route: list[str], data: ProblemData, ev_params: EVParameters) -> list[str]:
    """Remove a charging station and reinsert it at a different position."""
    new_route   = route[:]
    station_ids = data.station_ids
    positions   = [i for i, n in enumerate(new_route) if n in station_ids]
    if not positions:
        return insert_charging_station(route, data, ev_params)
    from_pos = random.choice(positions)
    station  = new_route.pop(from_pos)
    valid    = list(range(1, len(new_route)))
    if not valid:
        new_route.insert(from_pos, station)
        return new_route
    new_route.insert(random.choice(valid), station)
    return new_route


def repair_battery_violation(route: list[str], data: ProblemData, ev_params: EVParameters) -> list[str]:
    """
    Simulate battery along the route. At the first arc where battery would go
    negative, insert the nearest reachable charging station before that arc.
    """
    new_route          = route[:]
    dist_array         = data.dist_array
    dist_index         = data.dist_index
    energy_array       = data.energy_array
    station_ids        = data.station_ids
    station_matrix_idx = data.station_matrix_idx
    all_stations       = data.all_station_ids
    battery            = ev_params.initial_battery_kwh
    capacity           = ev_params.battery_capacity_kwh

    for i in range(len(new_route) - 1):
        origin = new_route[i]
        dest   = new_route[i + 1]

        oi = dist_index.get(origin)
        di = dist_index.get(dest)
        if oi is None or di is None:
            continue

        energy = energy_array[oi, di]

        if battery - energy < 0:
            energy_to_sta = energy_array[oi, station_matrix_idx]
            reachable = energy_to_sta <= battery
            # Avoid re-inserting the station that is already the next node
            if dest in station_ids and di is not None:
                reachable &= station_matrix_idx != di
            if reachable.any():
                dists    = dist_array[oi, station_matrix_idx]
                best_pos = int(np.where(reachable, dists, np.inf).argmin())
                new_route.insert(i + 1, all_stations[best_pos])
            return new_route

        battery -= energy
        if dest in station_ids:
            battery = capacity

    return new_route


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def generate_neighbor(route: list[str], data: ProblemData, ev_params: EVParameters) -> list[str]:
    """
    Randomly select a neighborhood move. EV modify-moves are only included
    when the route already contains at least one charging station.
    """
    station_ids        = data.station_ids
    route_has_stations = any(n in station_ids for n in route)

    classic   = [swap_customers, relocate_customer, two_opt]
    ev_insert = [insert_charging_station, repair_battery_violation]
    ev_modify = [remove_charging_station, replace_charging_station, move_charging_station]

    moves = classic + ev_insert + (ev_modify if route_has_stations else [])
    return random.choice(moves)(route, data, ev_params)
