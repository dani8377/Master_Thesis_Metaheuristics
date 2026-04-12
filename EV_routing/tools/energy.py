from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EVParameters:
    battery_capacity_kwh: float
    initial_battery_kwh: float
    energy_consumption_kwh_per_km: float
    average_speed_kmh: float
    grade_factor: float = 3.0       # slope sensitivity: 10% grade → ±30% energy
    speed_exponent: float = 2.0     # aerodynamic drag exponent (v^2)


def energy_needed_kwh(distance_km: float, consumption_kwh_per_km: float) -> float:
    return distance_km * consumption_kwh_per_km


def travel_time_hours(distance_km: float, average_speed_kmh: float) -> float:
    if average_speed_kmh <= 0:
        raise ValueError("average_speed_kmh must be > 0")
    return distance_km / average_speed_kmh


def charging_time_hours(charged_energy_kwh: float, charging_power_kw: float) -> float:
    if charging_power_kw <= 0:
        raise ValueError("charging_power_kw must be > 0")
    return charged_energy_kwh / charging_power_kw