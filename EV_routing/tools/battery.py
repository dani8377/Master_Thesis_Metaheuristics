from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EVParameters:
    battery_capacity_kwh: float
    initial_battery_kwh: float
    energy_consumption_kwh_per_km: float   # baseline at reference speed, flat road
    average_speed_kmh: float
    grade_factor: float = 3.0              # slope sensitivity: 10% grade → ±30% energy
    speed_exponent: float = 2.0            # aerodynamic drag exponent (v²)
