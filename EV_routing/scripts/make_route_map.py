"""
Route-map figure: greedy nearest-neighbour route vs. SA's best route on the
sf_75 instance, drawn over the OpenStreetMap basemap (same style as the
instance map in the Problem Specification chapter).

Runs greedy (deterministic) and SA (seed 0, 150k evaluations, tuned
parameters) fresh, then plots both routes side by side.

Output:
    EV_routing/results/sf_75/figures/route_comparison_map.png
    report/graphics/ev_route_comparison.png

Usage:
    PYTHONPATH=EV_routing python3.12 EV_routing/scripts/make_route_map.py
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, "EV_routing")

import contextily as cx
import geopandas as gpd
from shapely.geometry import Point

from tools.data_loader import load_problem_data
from tools.battery import EVParameters
from tools.objective import ObjectiveWeights, evaluate_route
from algorithms.simulated_annealing import simulated_annealing
from algorithms.greedy import greedy_nearest_neighbor

INSTANCE = Path("EV_routing/instances/sf_75")
BASE = Path("EV_routing/results/sf_75")
OUT_FIG = BASE / "figures" / "route_comparison_map.png"
OUT_REPORT = Path("report/graphics/ev_route_comparison.png")

DTU_RED = "#C41237"
BLUE = "#3A6FB4"
INK = "#333333"

ev_params = EVParameters(
    battery_capacity_kwh=20.0, initial_battery_kwh=20.0,
    energy_consumption_kwh_per_km=0.50, average_speed_kmh=50.0,
    grade_factor=3.0, speed_exponent=2.0,
)
data = load_problem_data(INSTANCE, ev_params)
w = json.loads((BASE / "weights.json").read_text())["weights"]
weights = ObjectiveWeights(**w)
params = json.loads((BASE / "params.json").read_text())

# --- solutions -------------------------------------------------------------
random.seed(0)
greedy_route, greedy_eval, _ = greedy_nearest_neighbor(
    data, ev_params, weights)
print(f"[greedy] F={greedy_eval.objective_value:.4f} "
      f"dist={greedy_eval.total_distance_km:.1f} km "
      f"feasible={greedy_eval.feasible}")

random.seed(0)
sa_route, sa_eval, _ = simulated_annealing(
    data, ev_params, weights, max_evaluations=150_000, **params["SA"])
print(f"[SA]     F={sa_eval.objective_value:.4f} "
      f"dist={sa_eval.total_distance_km:.1f} km "
      f"feasible={sa_eval.feasible}")

# --- coordinates -----------------------------------------------------------
cust = pd.read_csv(INSTANCE / "customers.csv")
stat = pd.read_csv(INSTANCE / "charging_stations.csv")
depo = pd.read_csv(INSTANCE / "depot.csv")

coords: dict[str, tuple[float, float]] = {}
for _, r in cust.iterrows():
    coords[r["Customer ID"]] = (r["Longitude"], r["Latitude"])
for _, r in stat.iterrows():
    coords[r["Station ID"]] = (r["Longitude"], r["Latitude"])
for _, r in depo.iterrows():
    coords[r["Node ID"]] = (r["Longitude"], r["Latitude"])


def to_webmerc(lonlat: list[tuple[float, float]]):
    gdf = gpd.GeoDataFrame(geometry=[Point(x, y) for x, y in lonlat],
                           crs="EPSG:4326").to_crs(epsg=3857)
    return [(p.x, p.y) for p in gdf.geometry]


# --- plot ------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(13, 7), sharex=True, sharey=True)

panels = [
    ("Greedy nearest-neighbour", greedy_route, greedy_eval, axes[0]),
    ("Simulated Annealing (best, seed 0)", sa_route, sa_eval, axes[1]),
]

cust_xy = to_webmerc([coords[c] for c in cust["Customer ID"]])
stat_xy = to_webmerc([coords[s] for s in stat["Station ID"]])
depo_xy = to_webmerc([coords[depo["Node ID"].iloc[0]]])

for title, route, ev, ax in panels:
    path_xy = to_webmerc([coords[nid] for nid in route])
    xs, ys = zip(*path_xy)
    ax.plot(xs, ys, color=INK, lw=1.4, alpha=0.85, zorder=3)

    cxs, cys = zip(*cust_xy)
    ax.scatter(cxs, cys, s=22, color="#3C8A3C", edgecolor="white",
               linewidth=0.4, zorder=4, label="Customers (75)")
    sxs, sys_ = zip(*stat_xy)
    ax.scatter(sxs, sys_, s=34, marker="^", color=BLUE, edgecolor="white",
               linewidth=0.4, zorder=4, label="Charging stations (30)")
    # stations actually visited by this route
    visited = [coords[nid] for nid in route
               if data.node_types.get(nid) == "station"]
    if visited:
        vxy = to_webmerc(visited)
        vx, vy = zip(*vxy)
        ax.scatter(vx, vy, s=90, marker="^", facecolor="none",
                   edgecolor=DTU_RED, linewidth=1.6, zorder=5,
                   label=f"Stations visited ({len(visited)})")
    dx, dy = depo_xy[0]
    ax.scatter([dx], [dy], s=170, marker="*", color=DTU_RED,
               edgecolor="white", linewidth=0.6, zorder=6, label="Depot")

    n_stops = sum(1 for nid in route if data.node_types.get(nid) == "station")
    ax.set_title(f"{title}\n$F = {ev.objective_value:.3f}$, "
                 f"{ev.total_distance_km:.0f} km, "
                 f"{n_stops} charging stop{'s' if n_stops != 1 else ''}",
                 fontsize=11)
    cx.add_basemap(ax, source=cx.providers.CartoDB.Positron,
                   attribution_size=5)
    ax.set_axis_off()

axes[0].legend(loc="lower left", fontsize=8, framealpha=0.9)
fig.tight_layout()

OUT_FIG.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT_FIG, dpi=200, bbox_inches="tight")
fig.savefig(OUT_REPORT, dpi=200, bbox_inches="tight")
print(f"[save] {OUT_FIG}\n[save] {OUT_REPORT}")
