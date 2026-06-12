from __future__ import annotations
from dataclasses import dataclass
from tools.data_loader import ProblemData
from tools.battery import EVParameters

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

    dist_array    = data.dist_array
    dist_index    = data.dist_index
    energy_array  = data.energy_array
    node_types    = data.node_types
    station_price = data.station_price
    station_power = data.station_power

    speed        = ev_params.average_speed_kmh
    capacity     = ev_params.battery_capacity_kwh
    battery_kwh  = ev_params.initial_battery_kwh

    total_distance_km        = 0.0
    total_travel_time_h      = 0.0
    total_charging_time_h    = 0.0
    total_energy_consumed_kwh = 0.0
    total_charging_cost_usd  = 0.0
    battery_violation_kwh    = 0.0
    infeasible_visits        = 0

    for i in range(len(route) - 1):
        origin      = route[i]
        destination = route[i + 1]

        oi = dist_index.get(origin)
        di = dist_index.get(destination)
        if oi is None or di is None:
            infeasible_visits += 1
            continue

        distance_km = dist_array[oi, di]
        energy_kwh  = energy_array[oi, di]
        travel_h    = distance_km / speed

        total_distance_km         += distance_km
        total_energy_consumed_kwh += energy_kwh
        total_travel_time_h       += travel_h

        battery_kwh -= energy_kwh

        if battery_kwh < 0:
            battery_violation_kwh += -battery_kwh

        if node_types.get(destination) == "station":
            power_kw      = station_power.get(destination, 0.0)
            price_per_kwh = station_price.get(destination, 0.0)

            if power_kw <= 0:
                infeasible_visits += 1
                continue

            current_battery_nonnegative = battery_kwh if battery_kwh > 0.0 else 0.0

            if charge_to_full:
                charged_energy_kwh = capacity - current_battery_nonnegative
            else:
                charged_energy_kwh = -battery_kwh if battery_kwh < 0.0 else 0.0

            if charged_energy_kwh > 0:
                total_charging_time_h   += charged_energy_kwh / power_kw
                total_charging_cost_usd += charged_energy_kwh * price_per_kwh
                battery_kwh = min(capacity, current_battery_nonnegative + charged_energy_kwh)

    # Structural completeness: every customer must appear exactly once.
    # Charged as infeasible visits (lambda_vis, Eq. 3.25) so the objective can
    # never reward dropping or duplicating a customer.  All current callers
    # only evaluate structurally valid routes, so this changes no results;
    # it closes the latent gap for any future caller that skips validation.
    visit_counts: dict[str, int] = {}
    customer_ids = data.customer_ids
    for node in route:
        if node in customer_ids:
            visit_counts[node] = visit_counts.get(node, 0) + 1
    missing_customers    = len(customer_ids) - len(visit_counts)
    duplicate_customers  = sum(c - 1 for c in visit_counts.values())
    infeasible_visits   += missing_customers + duplicate_customers

    objective_value = (
        weights.distance_weight        * total_distance_km
        + weights.travel_time_weight   * (total_travel_time_h + total_charging_time_h)
        + weights.energy_weight        * total_energy_consumed_kwh
        + weights.charging_cost_weight * total_charging_cost_usd
        + weights.battery_violation_weight * battery_violation_kwh
        + weights.infeasible_visit_weight  * infeasible_visits
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
