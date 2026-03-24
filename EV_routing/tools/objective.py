from __future__ import annotations

from dataclasses import dataclass

from tools.data_loader import ProblemData
from tools.energy import (
    EVParameters,
    energy_needed_kwh,
    travel_time_hours,
    charging_time_hours,
)


@dataclass
class ObjectiveWeights:
    distance_weight: float = 1.0
    travel_time_weight: float = 10.0
    energy_weight: float = 2.0
    charging_cost_weight: float = 20.0
    battery_violation_weight: float = 10000.0
    infeasible_visit_weight: float = 5000.0


@dataclass
class RouteEvaluation:
    total_distance_km: float
    total_travel_time_h: float
    total_charging_time_h: float
    total_energy_consumed_kwh: float
    total_charging_cost_usd: float
    battery_violation_kwh: float
    infeasible_visits: int
    objective_value: float
    feasible: bool


def build_station_price_lookup(data: ProblemData) -> dict[str, float]:
    return {
        str(row["Node ID"]): float(row["Cost (USD/kWh)"])
        for _, row in data.stations.iterrows()
    }


def build_station_power_lookup(data: ProblemData) -> dict[str, float]:
    return {
        str(row["Node ID"]): float(row["Charging Capacity (kW)"])
        for _, row in data.stations.iterrows()
    }


def evaluate_route(
    route: list[str],
    data: ProblemData,
    ev_params: EVParameters,
    weights: ObjectiveWeights,
    charge_to_full: bool = True,
) -> RouteEvaluation:
    """
    Evaluate a route using EV-aware cost components:
    - distance
    - travel time
    - charging time
    - energy consumption
    - charging price
    - infeasibility penalties
    """

    distance_matrix = data.distance_matrix
    node_types = data.node_types

    station_price = build_station_price_lookup(data)
    station_power = build_station_power_lookup(data)

    battery_kwh = ev_params.initial_battery_kwh

    total_distance_km = 0.0
    total_travel_time_h = 0.0
    total_charging_time_h = 0.0
    total_energy_consumed_kwh = 0.0
    total_charging_cost_usd = 0.0
    battery_violation_kwh = 0.0
    infeasible_visits = 0

    for i in range(len(route) - 1):
        origin = route[i]
        destination = route[i + 1]

        if origin not in distance_matrix.index or destination not in distance_matrix.columns:
            infeasible_visits += 1
            continue

        distance_km = float(distance_matrix.loc[origin, destination])
        energy_kwh = energy_needed_kwh(
            distance_km,
            ev_params.energy_consumption_kwh_per_km,
        )
        travel_h = travel_time_hours(
            distance_km,
            ev_params.average_speed_kmh,
        )

        total_distance_km += distance_km
        total_energy_consumed_kwh += energy_kwh
        total_travel_time_h += travel_h

        battery_kwh -= energy_kwh

        if battery_kwh < 0:
            battery_violation_kwh += abs(battery_kwh)

        if node_types.get(destination) == "station":
            power_kw = station_power.get(destination, 0.0)
            price_per_kwh = station_price.get(destination, 0.0)

            if power_kw <= 0:
                infeasible_visits += 1
                continue

            current_battery_nonnegative = max(battery_kwh, 0.0)

            if charge_to_full:
                charged_energy_kwh = ev_params.battery_capacity_kwh - current_battery_nonnegative
            else:
                charged_energy_kwh = max(0.0, -battery_kwh)

            if charged_energy_kwh > 0:
                total_charging_time_h += charging_time_hours(charged_energy_kwh, power_kw)
                total_charging_cost_usd += charged_energy_kwh * price_per_kwh
                battery_kwh = min(
                    ev_params.battery_capacity_kwh,
                    current_battery_nonnegative + charged_energy_kwh,
                )

    objective_value = (
        weights.distance_weight * total_distance_km
        + weights.travel_time_weight * (total_travel_time_h + total_charging_time_h)
        + weights.energy_weight * total_energy_consumed_kwh
        + weights.charging_cost_weight * total_charging_cost_usd
        + weights.battery_violation_weight * battery_violation_kwh
        + weights.infeasible_visit_weight * infeasible_visits
    )

    feasible = (battery_violation_kwh == 0.0) and (infeasible_visits == 0)

    return RouteEvaluation(
        total_distance_km=total_distance_km,
        total_travel_time_h=total_travel_time_h,
        total_charging_time_h=total_charging_time_h,
        total_energy_consumed_kwh=total_energy_consumed_kwh,
        total_charging_cost_usd=total_charging_cost_usd,
        battery_violation_kwh=battery_violation_kwh,
        infeasible_visits=infeasible_visits,
        objective_value=objective_value,
        feasible=feasible,
    )