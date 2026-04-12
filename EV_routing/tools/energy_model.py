from __future__ import annotations

import numpy as np


def compute_arc_energy(
    road_dist_km: float,
    elev_origin_m: float,
    elev_dest_m: float,
    speed_kmh: float,
    base_consumption: float,
    grade_factor: float,
    speed_ref_kmh: float,
    speed_exponent: float,
) -> float:
    """
    Compute energy consumed on a single arc (kWh).

    Formula:
        E = road_dist_km
          × base_consumption
          × grade_multiplier
          × speed_multiplier

    Grade multiplier:
        slope = (elev_dest - elev_origin) / road_dist_m
        grade_multiplier = max(0.1, 1 + grade_factor × slope)
        Uphill (slope > 0) → more energy; downhill capped at 10% of base.

    Speed multiplier:
        speed_multiplier = (speed_kmh / speed_ref_kmh) ^ speed_exponent
        Reflects aerodynamic drag growing with speed squared.
    """
    if road_dist_km <= 0.0:
        return 0.0

    road_dist_m = road_dist_km * 1000.0
    slope = (elev_dest_m - elev_origin_m) / road_dist_m
    grade_multiplier = max(0.1, 1.0 + grade_factor * slope)

    if speed_kmh <= 0.0:
        speed_multiplier = 1.0
    else:
        speed_multiplier = (speed_kmh / speed_ref_kmh) ** speed_exponent

    return road_dist_km * base_consumption * grade_multiplier * speed_multiplier


def build_energy_matrix(
    node_ids: list[str],
    elevations_m: dict[str, float],
    road_dist_matrix_m: np.ndarray,
    duration_matrix_s: np.ndarray,
    base_consumption: float,
    grade_factor: float,
    speed_ref_kmh: float,
    speed_exponent: float,
) -> np.ndarray:
    """
    Build a full NxN energy matrix (kWh) from road distances, durations, and elevations.

    Parameters
    ----------
    node_ids:
        Ordered list of node IDs matching the rows/cols of the matrices.
    elevations_m:
        Dict mapping node_id -> elevation in metres.
    road_dist_matrix_m:
        NxN array of road distances in metres (from OSRM).
    duration_matrix_s:
        NxN array of travel durations in seconds (from OSRM).
    base_consumption:
        Baseline energy consumption in kWh/km at reference speed on flat road.
    grade_factor:
        Slope sensitivity (dimensionless). 3.0 → 10% slope adds 30% energy.
    speed_ref_kmh:
        Reference speed for the speed multiplier baseline (e.g. 50.0).
    speed_exponent:
        Speed exponent for aerodynamic drag term (e.g. 2.0).

    Returns
    -------
    NxN float64 numpy array of energy in kWh per arc.
    """
    n = len(node_ids)
    energy = np.zeros((n, n), dtype=np.float64)

    for i in range(n):
        elev_i = elevations_m.get(node_ids[i], 0.0)
        for j in range(n):
            if i == j:
                continue

            road_dist_m = road_dist_matrix_m[i, j]
            dur_s = duration_matrix_s[i, j]

            road_dist_km = road_dist_m / 1000.0
            elev_j = elevations_m.get(node_ids[j], 0.0)

            if dur_s > 0:
                speed_kmh = (road_dist_m / dur_s) * 3.6
            else:
                speed_kmh = speed_ref_kmh

            energy[i, j] = compute_arc_energy(
                road_dist_km=road_dist_km,
                elev_origin_m=elev_i,
                elev_dest_m=elev_j,
                speed_kmh=speed_kmh,
                base_consumption=base_consumption,
                grade_factor=grade_factor,
                speed_ref_kmh=speed_ref_kmh,
                speed_exponent=speed_exponent,
            )

    return energy
