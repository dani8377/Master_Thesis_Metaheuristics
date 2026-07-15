"""Cover graphic for the thesis title page.

Two-panel schematic signalling the thesis's two problems side by side:
left, cloud task scheduling (tasks packed onto heterogeneous servers);
right, electric vehicle routing with charging stops. Stylized iconography,
DTU brand colors. Output: report/graphics/cover_dual_problems.pdf (+ PNG preview).
"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle

ROOT = Path(__file__).resolve().parents[2]
PREVIEW_DIR = ROOT / "EV_routing" / "results" / "sf_75" / "figures"

# DTU brand colors (from report/preamble/dtucolors.sty, CMYK -> sRGB)
DTU_RED = "#C41237"     # dtured {0,.91,.72,.23}
DTU_BLUE = "#4080FF"    # s13    {.75,.50,0,0}
INK = "#3A3A3A"
GREY = "#707070"
RED_TINT = "#E8A0B0"
BLUE_TINT = "#B3CCFF"
GREY_TINT = "#C9C9C9"

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.2, 4.3))
for ax in (ax1, ax2):
    ax.set_aspect("equal")
    ax.axis("off")

# ------------------------------------------------------------------
# Left panel: cloud task scheduling (tasks -> heterogeneous servers)
# ------------------------------------------------------------------
BAR_W = 0.62
GAP = 0.10  # white spacer between stacked task segments

# (x, capacity, [segment heights]) — one server idle: consolidation motif
servers = [
    (0.0, 3.0, [1.05, 0.75, 0.55]),
    (1.0, 4.2, [1.30, 0.90, 0.70, 0.45]),
    (2.0, 2.4, []),                     # idle server, draws no power
    (3.0, 3.4, [1.20, 0.95, 0.60]),
]
seg_colors = [RED_TINT, BLUE_TINT, GREY_TINT, RED_TINT]

for x, cap, segs in servers:
    ax1.add_patch(Rectangle((x, 0), BAR_W, cap, fill=False,
                            edgecolor=INK, linewidth=1.5, zorder=3))
    y = 0.0
    for i, h in enumerate(segs):
        ax1.add_patch(Rectangle((x + 0.05, y + 0.04), BAR_W - 0.10, h - 0.08,
                                facecolor=seg_colors[i % len(seg_colors)],
                                edgecolor="none", zorder=2))
        y += h + GAP - 0.04

# queue of incoming tasks above the servers
queue_y = 5.1
task_colors = [BLUE_TINT, RED_TINT, GREY_TINT, RED_TINT, BLUE_TINT]
for i, c in enumerate(task_colors):
    ax1.add_patch(Rectangle((0.15 + i * 0.62, queue_y), 0.44, 0.44,
                            facecolor=c, edgecolor=INK, linewidth=1.1, zorder=3))

# dashed assignment arrows: two tasks dropping into servers
for (x0, y0), (x1, y1) in [((0.55, queue_y - 0.06), (0.31, 2.75)),
                           ((2.65, queue_y - 0.06), (3.31, 3.05))]:
    ax1.add_patch(FancyArrowPatch((x0, y0), (x1, y1),
                                  arrowstyle="-|>", mutation_scale=11,
                                  linestyle=(0, (4, 3)), linewidth=1.2,
                                  color=GREY, zorder=4,
                                  connectionstyle="arc3,rad=-0.12"))

ax1.set_xlim(-0.55, 4.2)
ax1.set_ylim(-1.15, 6.1)

# ------------------------------------------------------------------
# Right panel: electric vehicle routing with charging stops
# ------------------------------------------------------------------
route = [
    (0.00, -1.00),   # depot
    (-0.55, -0.90),
    (-0.98, -0.38),
    (-0.78, 0.12),
    (-1.02, 0.58),
    (-0.48, 0.88),
    (-0.02, 0.62),   # charging station
    (0.36, 0.98),
    (0.88, 0.72),
    (1.08, 0.18),
    (0.68, -0.12),
    (0.98, -0.58),   # charging station
    (0.44, -0.84),
]
station_idx = {6, 11}
depot_idx = 0

xs = [p[0] for p in route] + [route[0][0]]
ys = [p[1] for p in route] + [route[0][1]]
ax2.plot(xs, ys, color=DTU_RED, lw=2.0, zorder=1,
         solid_joinstyle="round", solid_capstyle="round")

def lightning(ax, cx, cy, s, color):
    pts = [(0.16, 0.50), (-0.22, -0.04), (-0.02, -0.04),
           (-0.16, -0.50), (0.22, 0.06), (0.02, 0.06)]
    ax.add_patch(Polygon([(cx + px * s, cy + py * s) for px, py in pts],
                         closed=True, facecolor=color, edgecolor="none",
                         zorder=6))

for i, (x, y) in enumerate(route):
    if i == depot_idx:
        ax2.scatter([x], [y], s=520, marker="*", color=DTU_RED,
                    edgecolor="white", linewidth=1.2, zorder=5)
    elif i in station_idx:
        ax2.scatter([x], [y], s=300, marker="s", color=DTU_BLUE,
                    edgecolor="white", linewidth=1.0, zorder=5)
        lightning(ax2, x, y, 0.22, "white")
    else:
        ax2.scatter([x], [y], s=65, color=INK, edgecolor="white",
                    linewidth=0.8, zorder=4)

ax2.set_xlim(-1.45, 1.5)
ax2.set_ylim(-1.62, 1.42)

# ------------------------------------------------------------------
# Panel labels (spaced capitals, recessive grey)
# ------------------------------------------------------------------
for ax, label in ((ax1, "C L O U D   T A S K   S C H E D U L I N G"),
                  (ax2, "E L E C T R I C   V E H I C L E   R O U T I N G")):
    ax.text(0.5, -0.02, label, transform=ax.transAxes,
            ha="center", va="top", fontsize=10.5, color=GREY, family="sans-serif")

fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.10, wspace=0.14)

out_pdf = ROOT / "report" / "graphics" / "cover_dual_problems.pdf"
fig.savefig(out_pdf, bbox_inches="tight", pad_inches=0.05, transparent=True)
fig.savefig(PREVIEW_DIR / "cover_dual_problems_preview.png", dpi=170,
            bbox_inches="tight", pad_inches=0.05)
print("wrote", out_pdf)
