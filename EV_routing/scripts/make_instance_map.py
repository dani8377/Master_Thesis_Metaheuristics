"""
Render the sf_75 instance map used in the Problem Specification chapter.

Reads the *existing* frozen instance data and only redraws the figure, so it
never touches the instance itself (unlike build_instance.py, which regenerates
the nodes).  Differences from the map build_instance.py saves alongside the
data: no in-figure title, since the LaTeX caption already carries it, and a
tight bounding box so the file contains no wasted margin.

Node positions are projected to Web Mercator and the axes keep equal aspect,
so the map is not stretched in either direction.

Usage:
    PYTHONPATH=EV_routing python3.12 EV_routing/scripts/make_instance_map.py
"""
from __future__ import annotations

from pathlib import Path

import contextily as ctx
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

INSTANCE = "sf_75"
INST_DIR = Path(f"EV_routing/instances/{INSTANCE}")
OUT_REPORT = Path("report/graphics/sf75_instance_map.png")


def to_gdf(df: pd.DataFrame) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["Longitude"], df["Latitude"]),
        crs="EPSG:4326",
    ).to_crs(epsg=3857)


def main() -> None:
    stations = pd.read_csv(INST_DIR / "charging_stations.csv")
    customers = pd.read_csv(INST_DIR / "customers.csv")
    depot = pd.read_csv(INST_DIR / "depot.csv")

    # Canvas matches the data's own aspect, so equal-aspect axes leave no
    # dead margin on either side.
    fig, ax = plt.subplots(figsize=(7.8, 10))
    to_gdf(stations).plot(ax=ax, color="#3A6FB4", markersize=34,
                          label=f"Charging stations ({len(stations)})")
    to_gdf(customers).plot(ax=ax, color="#2E8B57", markersize=17, alpha=0.75,
                           label=f"Customers ({len(customers)})")
    to_gdf(depot).plot(ax=ax, color="#C41237", markersize=190, marker="X",
                       label="Depot")
    # CartoDB.Positron rather than OSM Mapnik: the Mapnik tile server rejects
    # scripted access, and Positron is the basemap the route figure already uses.
    ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)
    ax.set_axis_off()
    ax.legend(loc="upper right", fontsize=11, framealpha=0.92)

    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_REPORT, dpi=220, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print(f"[save] {OUT_REPORT}")


if __name__ == "__main__":
    main()
