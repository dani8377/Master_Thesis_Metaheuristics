"""Cover graphic for the thesis title page.

Draws the best-known sf_75 route (SA, seed 0, F* = 2.504) as a clean
vector polyline over the instance's nodes, straight-line schematic style,
DTU brand colors. Output: report/graphics/cover_route_sf75.pdf (+ PNG preview).
"""
import ast
import math
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SCRATCH = ROOT / "EV_routing" / "results" / "sf_75" / "figures"

# DTU brand colors (from report/preamble/dtucolors.sty, CMYK -> sRGB)
DTU_RED = "#C41237"       # dtured  {0,.91,.72,.23}
DTU_BLUE = "#4080FF"      # s13     {.75,.50,0,0}
INK = "#3A3A3A"           # neutral ink for customer stops

# --- data ------------------------------------------------------------
nodes = pd.read_csv(ROOT / "EV_routing/datasets/sf_all_nodes.csv")
nodes = nodes.set_index("Node ID")

log_line = next(
    line for line in (ROOT / "EV_routing/results/sf_75/run_log.txt").read_text().splitlines()
    if line.startswith("SA  best (seed 0):")
)
route = ast.literal_eval(log_line.split(":", 1)[1].strip())
assert route[0] == route[-1] == "DEPOT" and len(route) > 70

# equirectangular projection so distances aren't distorted east-west
lat0 = nodes["Latitude"].mean()
nodes["x"] = nodes["Longitude"] * math.cos(math.radians(lat0))
nodes["y"] = nodes["Latitude"]

rx = [nodes.loc[n, "x"] for n in route]
ry = [nodes.loc[n, "y"] for n in route]

cust = nodes[nodes["Node Type"] == "customer"]
stat = nodes[nodes["Node Type"].str.contains("charg|station", case=False)]
depot = nodes.loc["DEPOT"]

# stations actually used by the best route (visited mid-route)
used = {n for n in route if n.startswith("EVS")}

# --- figure ----------------------------------------------------------
fig, ax = plt.subplots(figsize=(5.4, 4.9))

# route polyline underneath everything
ax.plot(rx, ry, color=DTU_RED, lw=1.15, alpha=0.9, zorder=1,
        solid_joinstyle="round", solid_capstyle="round")

# unused charging stations: recessive open squares
un = stat.loc[~stat.index.isin(used)]
ax.scatter(un["x"], un["y"], s=16, marker="s", facecolor="white",
           edgecolor=DTU_BLUE, linewidth=0.9, alpha=0.75, zorder=2)
# stations on the route: filled blue squares
us = stat.loc[stat.index.isin(used)]
ax.scatter(us["x"], us["y"], s=34, marker="s", color=DTU_BLUE,
           edgecolor="white", linewidth=0.7, zorder=4)

# customer stops: small ink dots with white ring so the line threads them
ax.scatter(cust["x"], cust["y"], s=13, color=INK, edgecolor="white",
           linewidth=0.5, zorder=3)

# depot: DTU-red star with white ring
ax.scatter([depot["x"]], [depot["y"]], s=210, marker="*", color=DTU_RED,
           edgecolor="white", linewidth=0.9, zorder=5)

ax.set_aspect("equal")
ax.axis("off")
fig.tight_layout(pad=0.1)

out_pdf = ROOT / "report/graphics/cover_route_sf75.pdf"
fig.savefig(out_pdf, bbox_inches="tight", pad_inches=0.02, transparent=True)
fig.savefig(SCRATCH / "cover_route_sf75_preview.png", dpi=170,
            bbox_inches="tight", pad_inches=0.02)
print("wrote", out_pdf)
print("route stops:", len(route), "| stations used:", sorted(used))
