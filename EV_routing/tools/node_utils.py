from __future__ import annotations

from tools.data_loader import ProblemData


def build_station_price_lookup(data: ProblemData) -> dict[str, float]:
    lookup: dict[str, float] = {}
    for _, row in data.stations.iterrows():
        lookup[row["Node ID"]] = float(row["Cost (USD/kWh)"])
    return lookup


def build_station_power_lookup(data: ProblemData) -> dict[str, float]:
    lookup: dict[str, float] = {}
    for _, row in data.stations.iterrows():
        lookup[row["Node ID"]] = float(row["Charging Capacity (kW)"])
    return lookup


def build_station_availability_lookup(data: ProblemData) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for _, row in data.stations.iterrows():
        lookup[row["Node ID"]] = str(row["Availability"])
    return lookup