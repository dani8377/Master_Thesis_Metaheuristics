"""Cover graphic for the thesis title page.

Two quiet schematics side by side, no text: left, tasks packed onto
heterogeneous servers (cloud scheduling); right, a smooth closed tour
with charging stops (EV routing). Restrained palette: charcoal + greys,
DTU red as the single accent, muted blue for charging.
Output: report/graphics/cover_dual_problems.pdf (+ PNG preview).
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle

ROOT = Path(__file__).resolve().parents[2]
PREVIEW_DIR = ROOT / "EV_routing" / "results" / "sf_75" / "figures"

DTU_RED = "#C41237"     # dtured (report/preamble/dtucolors.sty)
BLUE = "#3A6FB4"        # muted charging-blue
INK = "#333333"
GREY_A = "#DCDCDC"
GREY_B = "#C2C2C2"
HAIR = "#C8C8C8"

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.2, 4.1))
for ax in (ax1, ax2):
    ax.set_aspect("equal")
    ax.axis("off")

# ------------------------------------------------------------------
# Left: cloud task scheduling — bin-packing onto servers
# ------------------------------------------------------------------
BAR_W = 0.62

# (x, capacity, [(height, color), ...]); one idle server, one red segment
servers = [
    (0.0, 3.0, [(0.95, GREY_A), (0.70, GREY_B)]),
    (1.0, 4.2, [(1.25, GREY_B), (0.85, GREY_A), (0.60, GREY_B)]),
    (2.0, 2.4, []),
    (3.0, 3.4, [(1.10, GREY_A), (0.80, GREY_B), (0.55, DTU_RED)]),
]

ax1.add_line(Line2D([-0.35, 3.97], [0, 0], color=HAIR, lw=1.2, zorder=1))

for x, cap, segs in servers:
    ax1.add_patch(Rectangle((x, 0), BAR_W, cap, fill=False,
                            edgecolor=INK, linewidth=1.3, zorder=3))
    y = 0.0
    for h, c in segs:
        ax1.add_patch(Rectangle((x + 0.05, y + 0.05), BAR_W - 0.10, h - 0.10,
                                facecolor=c, edgecolor="none", zorder=2))
        y += h

# small queue of pending tasks, the red one being assigned
queue = [(1.30, GREY_A), (1.85, GREY_B), (2.40, DTU_RED)]
for qx, c in queue:
    ax1.add_patch(Rectangle((qx, 5.05), 0.40, 0.40, facecolor=c,
                            edgecolor=INK, linewidth=1.0, zorder=3))

ax1.add_patch(FancyArrowPatch((2.72, 5.05), (3.31, 2.75),
                              arrowstyle="-|>", mutation_scale=9,
                              linewidth=1.0, color="#8A8A8A", zorder=4,
                              connectionstyle="arc3,rad=-0.25"))

ax1.set_xlim(-0.55, 4.2)
ax1.set_ylim(-1.05, 5.95)

# ------------------------------------------------------------------
# Right: EV routing — smooth closed tour with charging stops
# ------------------------------------------------------------------
route = np.array([
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
])
station_idx = {6, 11}
depot_idx = 0

def catmull_rom_closed(pts, samples_per_seg=24):
    """Closed Catmull-Rom spline through all points."""
    n = len(pts)
    out = []
    for i in range(n):
        p0, p1 = pts[(i - 1) % n], pts[i]
        p2, p3 = pts[(i + 1) % n], pts[(i + 2) % n]
        t = np.linspace(0, 1, samples_per_seg, endpoint=False)[:, None]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t
                          + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t**2
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * t**3))
    return np.vstack(out + [out[0][:1]])

curve = catmull_rom_closed(route)
ax2.plot(curve[:, 0], curve[:, 1], color=DTU_RED, lw=1.8, zorder=1,
         solid_capstyle="round")

def lightning(ax, cx, cy, s, color):
    pts = [(0.16, 0.50), (-0.22, -0.04), (-0.02, -0.04),
           (-0.16, -0.50), (0.22, 0.06), (0.02, 0.06)]
    ax.add_patch(Polygon([(cx + px * s, cy + py * s) for px, py in pts],
                         closed=True, facecolor=color, edgecolor="none",
                         zorder=6))

for i, (x, y) in enumerate(route):
    if i == depot_idx:
        ax2.scatter([x], [y], s=380, marker="*", color=DTU_RED,
                    edgecolor="white", linewidth=1.0, zorder=5)
    elif i in station_idx:
        ax2.scatter([x], [y], s=260, marker="s", color=BLUE,
                    edgecolor="white", linewidth=1.0, zorder=5)
        lightning(ax2, x, y, 0.20, "white")
    else:
        ax2.scatter([x], [y], s=52, color=INK, edgecolor="white",
                    linewidth=0.9, zorder=4)

ax2.set_xlim(-1.48, 1.52)
ax2.set_ylim(-1.55, 1.45)

# hairline divider between the two motifs
fig.subplots_adjust(left=0.02, right=0.98, top=0.97, bottom=0.03, wspace=0.16)
fig.add_artist(Line2D([0.503, 0.503], [0.14, 0.86],
                      transform=fig.transFigure, color=HAIR, lw=1.0))

out_pdf = ROOT / "report" / "graphics" / "cover_dual_problems.pdf"
fig.savefig(out_pdf, bbox_inches="tight", pad_inches=0.05, transparent=True)
fig.savefig(PREVIEW_DIR / "cover_dual_problems_preview.png", dpi=170,
            bbox_inches="tight", pad_inches=0.05)
print("wrote", out_pdf)
