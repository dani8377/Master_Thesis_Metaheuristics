"""
visualize.py — Visual frontend for the Cloud Resource Allocation problem.

PURPOSE
-------
Turns the console-only experiment output into an intuitive picture of WHAT the
scheduler actually decides: which tasks land on which servers, how full each
server is (CPU and memory), which servers stay idle (saving idle power), and
how the allocation improves as the search runs.

The renderings are designed to double as thesis figures: colourblind-safe
Okabe–Ito palette, no chartjunk, saved as 300-dpi PNG *and* vector PDF.

WHAT IT SHOWS
-------------
Each server is drawn as a "rack" whose height is proportional to its CPU
capacity C_j, so hardware heterogeneity is visible at a glance.  Tasks are
stacked blocks inside the rack — block height ∝ CPU demand c_i, colour =
priority class (Low / Medium / High).  Next to every rack a slim gauge shows
memory utilisation.  Idle servers are greyed out ("0 W"), directly visualising
the consolidation incentive of the energy term.  A header reports F(X),
energy, latency, active servers and feasibility — the same numbers as the
console tables, computed with the identical calibrated objective.

TWO FIGURE STYLES
-----------------
detailed  — screen-oriented: task IDs, per-server power, memory gauges.
            Best for the defence presentation, the GIF animations, and the
            appendix.  Too dense to survive shrinking to thesis column width.
paper     — print-oriented: drawn at final print size (5.8 in wide) with
            >= 7.5 pt fonts, no task labels, no memory gauge — only the
            message a reader needs in five seconds: which servers are active,
            how full they are, and why F(X) improved.  Include in LaTeX with
            \includegraphics[width=\textwidth]{...} and it will not be
            downscaled below its design size.

USAGE  (run from the "Cloud scheduling" directory)
--------------------------------------------------
    uv run python visualize.py                      # both styles, balanced focus
    uv run python visualize.py --style paper        # print figures only
    uv run python visualize.py --algorithm GA       # compare against the GA instead
    uv run python visualize.py --animate greedy     # GIF: BFD construction, task by task
    uv run python visualize.py --animate sa         # GIF: SA improving the allocation
    uv run python visualize.py --animate both       # both GIFs
    uv run python visualize.py --concept            # small didactic figure (12 tasks x 4
                                                    # servers + assignment vector) for the
                                                    # solution-representation section
    uv run python visualize.py --focus eco --seed 3 # any focus mode / seed
    uv run python visualize.py --show               # also open interactive windows
    uv run python visualize.py --fast               # reduced budget for a quick look

Outputs land in  figures/<focus>/allocation_*.png|pdf|gif  so they sit next to
the other per-focus figures.  Paper-style files carry the `_paper` suffix.

RELATIONSHIP TO THE EXPERIMENTS
-------------------------------
The instance, the focus-mode weights, and the sample-based normalisation
(Deb 2001/2000) are loaded exactly as in main.py, so every F(X) shown here is
directly comparable to the values in the thesis result tables.  The SA
animation uses the snapshot_callback observer hook in simulated_annealing(),
which records the best-so-far assignment whenever it improves and never
influences the search.
"""
from __future__ import annotations

import argparse
import dataclasses
import random
import time
from pathlib import Path

import numpy as np
import matplotlib

from tools.data_loader import load_problem_data, SchedulingProblemData
from tools.config_loader import load_config
from tools.objective import (
    FocusMode,
    ObjectiveWeights,
    ScheduleEvaluation,
    compute_sample_normalization,
    compute_normalization_constants,
    evaluate_schedule,
)
from tools.initial_solution import build_greedy_assignment
from algorithms.simulated_annealing import simulated_annealing
from algorithms.genetic_algorithm import genetic_algorithm
from algorithms.umda import umda


# ---------------------------------------------------------------------------
# Visual language (Okabe–Ito colourblind-safe palette)
# ---------------------------------------------------------------------------

PRIORITY_COLORS = {0: "#56B4E9", 1: "#E69F00", 2: "#D55E00"}   # sky / orange / vermillion
PRIORITY_NAMES  = {0: "Low priority", 1: "Medium priority", 2: "High priority"}
MEM_COLOR       = "#009E73"   # bluish green
IDLE_FACE       = "#F2F2F2"
IDLE_EDGE       = "#B0B0B0"
FRAME_EDGE      = "#3A3A3A"
OVERLOAD_COLOR  = "#CC0000"
ENERGY_COLOR    = "#0072B2"   # blue      — w_e·E/E_ref segment
LATENCY_COLOR   = "#CC79A7"   # magenta   — w_l·L/L_ref segment

RACK_W   = 1.0     # width of a server rack in data units
RACK_GAP = 0.55    # horizontal gap between racks
MEM_W    = 0.16    # width of the memory gauge
PAD      = 0.05    # inner padding of task blocks


# ---------------------------------------------------------------------------
# Core renderer: one datacenter panel
# ---------------------------------------------------------------------------

def draw_datacenter(
    ax,
    assignment: list[int],
    data: SchedulingProblemData,
    *,
    highlight_tasks: set[int] | None = None,
    show_task_labels: bool = True,
    y_max: float | None = None,
) -> None:
    """
    Draw the full allocation state on *ax*: one rack per server with stacked
    task blocks (CPU), a memory gauge, capacity lines, power labels, and
    idle-server greying.  Pure rendering — computes nothing that is not
    derivable from (assignment, data).
    """
    from matplotlib.patches import Rectangle

    highlight_tasks = highlight_tasks or set()
    m = data.n_servers
    a = np.asarray(assignment, dtype=np.int32)

    cpu_load = np.bincount(a, weights=data.cpu, minlength=m)
    mem_load = np.bincount(a, weights=data.mem, minlength=m)
    counts   = np.bincount(a, minlength=m)

    if y_max is None:
        y_max = float(max(data.server_cpu_cap.max(), cpu_load.max())) * 1.22

    label_min_h = 0.030 * y_max   # only label blocks tall enough to fit text

    for j in range(m):
        x      = j * (RACK_W + RACK_GAP)
        cap    = float(data.server_cpu_cap[j])
        active = counts[j] > 0

        # ---- Rack frame (height = CPU capacity) ----
        ax.add_patch(Rectangle(
            (x, 0), RACK_W, cap,
            facecolor="white" if active else IDLE_FACE,
            edgecolor=FRAME_EDGE if active else IDLE_EDGE,
            hatch=None if active else "///",
            linewidth=1.3, zorder=1,
        ))

        # ---- Stacked task blocks ----
        tasks_here = [int(i) for i in np.flatnonzero(a == j)]
        tasks_here.sort(key=lambda i: data.cpu[i], reverse=True)  # big blocks at the bottom
        y = 0.0
        for i in tasks_here:
            h    = float(data.cpu[i])
            over = y + h > cap + 1e-9
            ax.add_patch(Rectangle(
                (x + PAD, y), RACK_W - 2 * PAD, h,
                facecolor=PRIORITY_COLORS[int(np.clip(data.priority[i], 0, 2))],
                edgecolor="black" if i in highlight_tasks else "white",
                linewidth=1.8 if i in highlight_tasks else 0.6,
                alpha=0.95, zorder=3 if i in highlight_tasks else 2,
            ))
            if show_task_labels and h >= label_min_h:
                ax.text(
                    x + RACK_W / 2, y + h / 2, f"T{i}",
                    ha="center", va="center", fontsize=7,
                    color="white" if not over else "black", zorder=4,
                )
            y += h

        # ---- Overload marking ----
        if cpu_load[j] > cap + 1e-9:
            ax.plot([x - 0.06, x + RACK_W + 0.06], [cap, cap],
                    color=OVERLOAD_COLOR, linewidth=1.6, linestyle="--", zorder=5)
            ax.text(x + RACK_W / 2, cpu_load[j] + 0.012 * y_max, "OVERLOAD",
                    ha="center", va="bottom", fontsize=7.5,
                    color=OVERLOAD_COLOR, fontweight="bold", zorder=5)

        # ---- Memory gauge (fraction of M_j, drawn at rack height scale) ----
        mem_frac = float(mem_load[j] / data.server_mem_cap[j])
        gx = x + RACK_W + 0.07
        ax.add_patch(Rectangle(
            (gx, 0), MEM_W, cap,
            facecolor="white" if active else IDLE_FACE,
            edgecolor=IDLE_EDGE, linewidth=0.8, zorder=1,
        ))
        if mem_frac > 0:
            ax.add_patch(Rectangle(
                (gx, 0), MEM_W, min(mem_frac, 1.0) * cap,
                facecolor=MEM_COLOR if mem_frac <= 1.0 else OVERLOAD_COLOR,
                edgecolor="none", alpha=0.9, zorder=2,
            ))

        # ---- Per-server annotations ----
        watts = float(data.server_idle_power[j]
                      + data.server_efficiency[j]
                      * sum(data.energy[i] for i in tasks_here)) if active else 0.0
        util = cpu_load[j] / cap * 100
        top  = max(cap, cpu_load[j])
        if active:
            ax.text(x + RACK_W / 2, top + 0.015 * y_max,
                    f"{util:.0f}%\n{watts:.0f} W",
                    ha="center", va="bottom", fontsize=8, color="#222",
                    linespacing=1.25)
        else:
            ax.text(x + RACK_W / 2, top + 0.015 * y_max, "idle\n0 W",
                    ha="center", va="bottom", fontsize=8, color="#999",
                    style="italic", linespacing=1.25)

        # ---- Server spec label under the axis ----
        cores = data.server_cpu_cap[j] / 100.0
        ax.text(x + RACK_W / 2, -0.055 * y_max,
                f"S{j}\n{cores:.0f}-core\nη={data.server_efficiency[j]:.2f}",
                ha="center", va="top", fontsize=7.5, color="#444",
                linespacing=1.3)

    # ---- Axes cosmetics ----
    ax.set_xlim(-0.5, m * (RACK_W + RACK_GAP) - RACK_GAP + MEM_W + 0.45)
    ax.set_ylim(0, y_max)
    ax.set_xticks([])
    ax.set_ylabel("Server CPU load (%)", fontsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.grid(axis="y", alpha=0.25, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", labelsize=8.5)


def _stats_line(ev: ScheduleEvaluation, data: SchedulingProblemData) -> str:
    feas = "feasible" if ev.feasible else "INFEASIBLE"
    return (f"F(X) = {ev.objective_value:.4f}     "
            f"energy {ev.total_energy:,.0f} W     "
            f"latency {ev.total_latency:,.0f} ms     "
            f"servers {ev.n_active_servers}/{data.n_servers}     "
            f"{feas}")


def _add_legend(fig, *, highlight_label: str | None = None) -> None:
    from matplotlib.patches import Patch
    handles = [Patch(facecolor=PRIORITY_COLORS[p], edgecolor="white",
                     label=PRIORITY_NAMES[p]) for p in (0, 1, 2)]
    handles.append(Patch(facecolor=MEM_COLOR, edgecolor=IDLE_EDGE,
                         label="Memory gauge (fill = used / capacity)"))
    handles.append(Patch(facecolor=IDLE_FACE, edgecolor=IDLE_EDGE, hatch="///",
                         label="Idle server (0 W)"))
    if highlight_label:
        handles.append(Patch(facecolor="#DDDDDD", edgecolor="black",
                             linewidth=1.8, label=highlight_label))
    fig.legend(handles=handles, loc="lower center",
               ncol=len(handles), fontsize=8.5, frameon=False,
               bbox_to_anchor=(0.5, 0.005))


def _save(fig, out_dir: Path, stem: str, *, show: bool, pdf: bool = True) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    png = out_dir / f"{stem}.png"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    print(f"  saved -> {png}")
    if pdf:
        pdf_path = out_dir / f"{stem}.pdf"
        fig.savefig(pdf_path, bbox_inches="tight")
        print(f"  saved -> {pdf_path}")
    if not show:
        import matplotlib.pyplot as plt
        plt.close(fig)


# ---------------------------------------------------------------------------
# Static figures
# ---------------------------------------------------------------------------

def _fig_width(n_servers: int) -> float:
    return max(9.0, 1.35 * n_servers + 2.0)


def render_snapshot(
    assignment: list[int],
    data: SchedulingProblemData,
    weights: ObjectiveWeights,
    name: str,
    focus: str,
    out_dir: Path,
    stem: str,
    show: bool,
) -> ScheduleEvaluation:
    """One-panel allocation figure for a single algorithm's final solution."""
    import matplotlib.pyplot as plt

    ev  = evaluate_schedule(assignment, data, weights)
    fig, ax = plt.subplots(figsize=(_fig_width(data.n_servers), 6.8))
    draw_datacenter(ax, assignment, data)
    ax.set_title(name, fontsize=14, fontweight="bold", pad=34)
    ax.text(0.5, 1.022, _stats_line(ev, data), transform=ax.transAxes,
            ha="center", fontsize=9.5, color="#333")
    fig.suptitle(f"Cloud Resource Allocation   [{focus} focus]",
                 fontsize=10.5, color="#666", y=0.985)
    _add_legend(fig)
    fig.subplots_adjust(bottom=0.17, top=0.86)
    _save(fig, out_dir, stem, show=show)
    return ev


def render_comparison(
    assign_a: list[int], name_a: str,
    assign_b: list[int], name_b: str,
    data: SchedulingProblemData,
    weights: ObjectiveWeights,
    focus: str,
    out_dir: Path,
    stem: str,
    show: bool,
) -> None:
    """
    Side-by-side before/after figure (e.g. Greedy BFD vs SA) with a shared
    y-scale and an F(X)-decomposition strip underneath, so the reader can see
    both WHERE tasks moved and WHY the objective improved.
    """
    import matplotlib.pyplot as plt

    ev_a = evaluate_schedule(assign_a, data, weights)
    ev_b = evaluate_schedule(assign_b, data, weights)

    a_arr = np.asarray(assign_a); b_arr = np.asarray(assign_b)
    y_max = float(max(
        data.server_cpu_cap.max(),
        np.bincount(a_arr, weights=data.cpu, minlength=data.n_servers).max(),
        np.bincount(b_arr, weights=data.cpu, minlength=data.n_servers).max(),
    )) * 1.22
    moved = {i for i in range(data.n_tasks) if assign_a[i] != assign_b[i]}

    fig = plt.figure(figsize=(2 * _fig_width(data.n_servers) * 0.72, 8.6))
    gs  = fig.add_gridspec(2, 2, height_ratios=[5.2, 1.0], hspace=0.42, wspace=0.14)
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1], sharey=ax_a)
    ax_d = fig.add_subplot(gs[1, :])

    draw_datacenter(ax_a, assign_a, data, y_max=y_max)
    draw_datacenter(ax_b, assign_b, data, y_max=y_max, highlight_tasks=moved)
    ax_b.set_ylabel("")

    for ax, name, ev in ((ax_a, name_a, ev_a), (ax_b, name_b, ev_b)):
        ax.set_title(name, fontsize=13, fontweight="bold", pad=32)
        ax.text(0.5, 1.022, _stats_line(ev, data), transform=ax.transAxes,
                ha="center", fontsize=9, color="#333")

    improv = (ev_a.objective_value - ev_b.objective_value) / abs(ev_a.objective_value) * 100
    fig.suptitle(
        f"Cloud Resource Allocation — {name_a} vs {name_b}   [{focus} focus]"
        f"\n{name_b} improves F(X) by {improv:.1f}%   ·   "
        f"{len(moved)} of {data.n_tasks} tasks moved",
        fontsize=12, y=0.995,
    )

    # ---- F(X) decomposition strip (normalised terms, as they enter F) ----
    e_ref = weights.energy_ref or 1.0
    l_ref = weights.latency_ref or 1.0
    rows = []
    for name, ev in ((name_a, ev_a), (name_b, ev_b)):
        e_term = weights.energy_weight * ev.total_energy / e_ref
        l_term = weights.latency_weight * ev.total_latency / l_ref
        pen    = ev.objective_value - e_term - l_term
        rows.append((name, e_term, l_term, max(pen, 0.0)))

    ypos = [1.0, 0.0]
    for (name, e_term, l_term, pen), yp in zip(rows, ypos):
        ax_d.barh(yp, e_term, height=0.62, color=ENERGY_COLOR, edgecolor="white")
        ax_d.barh(yp, l_term, height=0.62, left=e_term, color=LATENCY_COLOR, edgecolor="white")
        if pen > 1e-9:
            ax_d.barh(yp, pen, height=0.62, left=e_term + l_term,
                      color=OVERLOAD_COLOR, edgecolor="white")
        ax_d.text(e_term / 2, yp, f"{e_term:.2f}", ha="center", va="center",
                  fontsize=8.5, color="white", fontweight="bold")
        ax_d.text(e_term + l_term / 2, yp, f"{l_term:.2f}", ha="center", va="center",
                  fontsize=8.5, color="white", fontweight="bold")
        ax_d.text(e_term + l_term + pen + 0.02, yp,
                  f"F = {e_term + l_term + pen:.3f}", ha="left", va="center",
                  fontsize=9, color="#222")

    ax_d.set_yticks(ypos)
    ax_d.set_yticklabels([r[0] for r in rows], fontsize=9.5)
    ax_d.set_xlabel("Contribution to F(X)   "
                    "(blue = w$_e$·E/E$_{ref}$,  magenta = w$_l$·L/L$_{ref}$,  red = penalty)",
                    fontsize=9)
    ax_d.spines["top"].set_visible(False)
    ax_d.spines["right"].set_visible(False)
    ax_d.set_xlim(0, max(r[1] + r[2] + r[3] for r in rows) * 1.28)
    ax_d.grid(axis="x", alpha=0.25, linewidth=0.6)
    ax_d.set_axisbelow(True)
    ax_d.tick_params(labelsize=8.5)

    _add_legend(fig, highlight_label=f"Task on a different server than under {name_a}")
    fig.subplots_adjust(bottom=0.14, top=0.84)
    _save(fig, out_dir, stem, show=show)


# ---------------------------------------------------------------------------
# Paper-style figures (print-oriented, drawn at final thesis size)
# ---------------------------------------------------------------------------
#
# Design rules for print:
#   * The figure is drawn at the physical size it will occupy on the page
#     (5.8 in ~ \textwidth), so no font ever shrinks below its set size.
#   * No per-task labels, no memory gauge, no per-server wattage — a reader
#     should get the message (which servers are used, how full, why F
#     improved) in seconds without zooming.
#   * All fonts >= 7.5 pt at final size.
# ---------------------------------------------------------------------------

def draw_racks_paper(
    ax,
    assignment: list[int],
    data: SchedulingProblemData,
    *,
    y_max: float | None = None,
    task_labels: bool = False,
    server_sublabel: bool = True,
) -> None:
    """
    Simplified rack renderer for print: capacity-height frames, stacked task
    blocks coloured by priority (no IDs unless task_labels=True), utilisation
    percentage above each active rack, idle racks hatched grey.
    """
    from matplotlib.patches import Rectangle

    m = data.n_servers
    a = np.asarray(assignment, dtype=np.int32)
    cpu_load = np.bincount(a, weights=data.cpu, minlength=m)
    counts   = np.bincount(a, minlength=m)

    if y_max is None:
        y_max = float(max(data.server_cpu_cap.max(), cpu_load.max())) * 1.18

    for j in range(m):
        x      = j * (RACK_W + RACK_GAP)
        cap    = float(data.server_cpu_cap[j])
        active = counts[j] > 0

        ax.add_patch(Rectangle(
            (x, 0), RACK_W, cap,
            facecolor="white" if active else IDLE_FACE,
            edgecolor=FRAME_EDGE if active else IDLE_EDGE,
            hatch=None if active else "///",
            linewidth=1.1, zorder=1,
        ))

        tasks_here = [int(i) for i in np.flatnonzero(a == j)]
        tasks_here.sort(key=lambda i: data.cpu[i], reverse=True)
        y = 0.0
        last_outside_label_y = -1e9   # collision-dodge for outside labels
        for i in tasks_here:
            h = float(data.cpu[i])
            ax.add_patch(Rectangle(
                (x + PAD, y), RACK_W - 2 * PAD, h,
                facecolor=PRIORITY_COLORS[int(np.clip(data.priority[i], 0, 2))],
                edgecolor="white", linewidth=0.7, alpha=0.95, zorder=2,
            ))
            if task_labels:
                if h >= 0.05 * y_max:
                    ax.text(x + RACK_W / 2, y + h / 2, f"T{i}",
                            ha="center", va="center", fontsize=7.5,
                            color="white", zorder=3)
                else:
                    # Block too thin for an internal label: annotate outside
                    # to the left with a short leader line, dodging upward if
                    # the previous outside label on this rack is too close.
                    ly = max(y + h / 2, last_outside_label_y + 0.045 * y_max)
                    last_outside_label_y = ly
                    ax.plot([x - 0.28, x + PAD], [ly, y + h / 2],
                            color="#999", linewidth=0.6, zorder=3)
                    ax.text(x - 0.32, ly, f"T{i}", ha="right", va="center",
                            fontsize=7, color="#333", zorder=3)
            y += h

        if cpu_load[j] > cap + 1e-9:
            ax.plot([x - 0.05, x + RACK_W + 0.05], [cap, cap],
                    color=OVERLOAD_COLOR, linewidth=1.4, linestyle="--", zorder=4)

        top = max(cap, cpu_load[j])
        if active:
            ax.text(x + RACK_W / 2, top + 0.02 * y_max,
                    f"{cpu_load[j] / cap * 100:.0f}%",
                    ha="center", va="bottom", fontsize=7.5, color="#222")
        else:
            ax.text(x + RACK_W / 2, top + 0.02 * y_max, "idle",
                    ha="center", va="bottom", fontsize=7.5,
                    color="#999", style="italic")

        label = f"S{j}"
        if server_sublabel:
            label += f"\n{data.server_cpu_cap[j] / 100:.0f}c"
        ax.text(x + RACK_W / 2, -0.045 * y_max, label,
                ha="center", va="top", fontsize=8, color="#444", linespacing=1.2)

    ax.set_xlim(-0.45, m * (RACK_W + RACK_GAP) - RACK_GAP + 0.45)
    ax.set_ylim(0, y_max)
    ax.set_xticks([])
    ax.set_ylabel("CPU load (%)", fontsize=9)
    for side in ("top", "right", "bottom"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="y", alpha=0.25, linewidth=0.5)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", labelsize=7.5)


def _paper_legend(fig, *, y: float = 0.01) -> None:
    from matplotlib.patches import Patch
    handles = [Patch(facecolor=PRIORITY_COLORS[p], edgecolor="white",
                     label=PRIORITY_NAMES[p]) for p in (0, 1, 2)]
    handles.append(Patch(facecolor=IDLE_FACE, edgecolor=IDLE_EDGE, hatch="///",
                         label="Idle server"))
    fig.legend(handles=handles, loc="lower center", ncol=4, fontsize=7.5,
               frameon=False, bbox_to_anchor=(0.5, y),
               handlelength=1.4, columnspacing=1.0, handletextpad=0.5)


def _paper_stats(ev: ScheduleEvaluation, data: SchedulingProblemData) -> str:
    return (f"F(X) = {ev.objective_value:.3f}    "
            f"E = {ev.total_energy:,.0f} W    "
            f"L = {ev.total_latency:,.0f} ms    "
            f"{ev.n_active_servers}/{data.n_servers} servers active")


def render_paper_snapshot(
    assignment: list[int],
    data: SchedulingProblemData,
    weights: ObjectiveWeights,
    name: str,
    out_dir: Path,
    stem: str,
    show: bool,
) -> None:
    """Single-panel allocation figure at print size (~\\textwidth)."""
    import matplotlib.pyplot as plt

    ev = evaluate_schedule(assignment, data, weights)
    fig, ax = plt.subplots(figsize=(5.8, 2.9))
    draw_racks_paper(ax, assignment, data)
    ax.set_title(name, fontsize=10, fontweight="bold", pad=22, loc="left")
    ax.text(0.0, 1.045, _paper_stats(ev, data), transform=ax.transAxes,
            ha="left", fontsize=7.5, color="#333")
    _paper_legend(fig)
    fig.subplots_adjust(bottom=0.30, top=0.80, left=0.09, right=0.99)
    _save(fig, out_dir, stem, show=show)


def render_paper_comparison(
    assign_a: list[int], name_a: str,
    assign_b: list[int], name_b: str,
    data: SchedulingProblemData,
    weights: ObjectiveWeights,
    out_dir: Path,
    stem: str,
    show: bool,
) -> None:
    """
    Print-size before/after figure: baseline rack panel on top, metaheuristic
    rack panel below (vertical stacking keeps each rack wide enough to read),
    plus a compact F(X)-decomposition strip.
    """
    import matplotlib.pyplot as plt

    ev_a = evaluate_schedule(assign_a, data, weights)
    ev_b = evaluate_schedule(assign_b, data, weights)
    improv = (ev_a.objective_value - ev_b.objective_value) / abs(ev_a.objective_value) * 100

    y_max = float(max(
        data.server_cpu_cap.max(),
        np.bincount(np.asarray(assign_a), weights=data.cpu, minlength=data.n_servers).max(),
        np.bincount(np.asarray(assign_b), weights=data.cpu, minlength=data.n_servers).max(),
    )) * 1.18

    fig = plt.figure(figsize=(5.8, 6.4))
    gs = fig.add_gridspec(3, 1, height_ratios=[1.0, 1.0, 0.40], hspace=0.62)
    ax_a = fig.add_subplot(gs[0])
    ax_b = fig.add_subplot(gs[1])
    ax_d = fig.add_subplot(gs[2])

    draw_racks_paper(ax_a, assign_a, data, y_max=y_max)
    draw_racks_paper(ax_b, assign_b, data, y_max=y_max)
    sign = "−" if improv > 0 else "+"   # lower F is better, so improvement = minus
    ax_a.set_title(f"(a)  {name_a}", fontsize=9.5, fontweight="bold",
                   pad=20, loc="left")
    ax_b.set_title(f"(b)  {name_b}   (F(X) {sign}{abs(improv):.1f}% vs. baseline)",
                   fontsize=9.5, fontweight="bold", pad=20, loc="left")
    ax_a.text(0.0, 1.055, _paper_stats(ev_a, data), transform=ax_a.transAxes,
              ha="left", fontsize=7.5, color="#333")
    ax_b.text(0.0, 1.055, _paper_stats(ev_b, data), transform=ax_b.transAxes,
              ha="left", fontsize=7.5, color="#333")

    # ---- Compact F(X) decomposition ----
    e_ref = weights.energy_ref or 1.0
    l_ref = weights.latency_ref or 1.0
    rows = []
    for name, ev in ((name_a, ev_a), (name_b, ev_b)):
        e_term = weights.energy_weight * ev.total_energy / e_ref
        l_term = weights.latency_weight * ev.total_latency / l_ref
        pen    = max(ev.objective_value - e_term - l_term, 0.0)
        rows.append((name, e_term, l_term, pen))

    for (name, e_term, l_term, pen), yp in zip(rows, (1.0, 0.0)):
        ax_d.barh(yp, e_term, height=0.58, color=ENERGY_COLOR, edgecolor="white")
        ax_d.barh(yp, l_term, height=0.58, left=e_term, color=LATENCY_COLOR, edgecolor="white")
        if pen > 1e-9:
            ax_d.barh(yp, pen, height=0.58, left=e_term + l_term,
                      color=OVERLOAD_COLOR, edgecolor="white")
        ax_d.text(e_term / 2, yp, f"{e_term:.2f}", ha="center", va="center",
                  fontsize=7.5, color="white", fontweight="bold")
        ax_d.text(e_term + l_term / 2, yp, f"{l_term:.2f}", ha="center", va="center",
                  fontsize=7.5, color="white", fontweight="bold")
        ax_d.text(e_term + l_term + pen + 0.03, yp, f"F = {e_term + l_term + pen:.3f}",
                  ha="left", va="center", fontsize=8, color="#222")

    ax_d.set_yticks((1.0, 0.0))
    ax_d.set_yticklabels(["(a)", "(b)"], fontsize=8)
    ax_d.set_xlabel(r"Contribution to F(X):  $w_e \cdot E/E_{ref}$ (blue)  +  "
                    r"$w_l \cdot L/L_{ref}$ (magenta)", fontsize=8)
    ax_d.spines["top"].set_visible(False)
    ax_d.spines["right"].set_visible(False)
    ax_d.set_xlim(0, max(r[1] + r[2] + r[3] for r in rows) * 1.30)
    ax_d.grid(axis="x", alpha=0.25, linewidth=0.5)
    ax_d.set_axisbelow(True)
    ax_d.tick_params(labelsize=7.5)

    _paper_legend(fig)
    fig.subplots_adjust(bottom=0.13, top=0.92, left=0.09, right=0.99)
    _save(fig, out_dir, stem, show=show)


def render_concept_figure(base_dir: Path, show: bool) -> None:
    """
    Small didactic figure for the solution-representation section (§3.1.3):
    the first 13 real dataset tasks placed on 4 servers by an illustrative
    balanced assignment (one server deliberately left idle), every task ID
    readable at print size, and the assignment vector A printed underneath —
    tying the picture directly to the mathematical encoding A = (a_1,...,a_n).
    """
    import matplotlib.pyplot as plt
    from tools.data_loader import generate_server_pool

    servers = generate_server_pool(4, seed=42)
    data    = load_problem_data(base_dir / "datasets", n_tasks=13, servers=servers)

    # Illustrative example assignment (NOT an optimiser output): balance the
    # tasks over three of the four servers, longest-processing-time first,
    # leaving S2 idle so the figure also shows the idle-server state that the
    # energy term rewards.  All capacities are comfortably respected.
    active = [0, 1, 3]
    order  = sorted(range(data.n_tasks), key=lambda i: data.cpu[i], reverse=True)
    loads  = {j: 0.0 for j in active}
    assignment = [0] * data.n_tasks
    for i in order:
        j = min(active, key=lambda s: loads[s])
        assignment[i] = j
        loads[j] += float(data.cpu[i])

    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    draw_racks_paper(ax, assignment, data, task_labels=True)
    vec = ",\\, ".join(str(j) for j in assignment)
    fig.text(0.54, 0.195, f"$A = ({vec})$", ha="center", fontsize=9.5)
    fig.text(0.54, 0.135, "entry $i$ = server index assigned to task $T_i$",
             ha="center", fontsize=7.5, color="#555")
    _paper_legend(fig, y=0.015)
    fig.subplots_adjust(bottom=0.40, top=0.965, left=0.11, right=0.99)

    out_dir = base_dir / "figures"
    _save(fig, out_dir, "allocation_concept_paper", show=show)


# ---------------------------------------------------------------------------
# Animation 1: Greedy BFD construction (task by task)
# ---------------------------------------------------------------------------

def animate_greedy_construction(
    data: SchedulingProblemData,
    weights: ObjectiveWeights,
    focus: str,
    out_dir: Path,
    show: bool,
    fps: int = 2,
) -> None:
    """
    Replay the deterministic Best-Fit-Decreasing construction one placement at
    a time.  Because BFD is sequential and deterministic, placing the first k
    tasks of the CPU-descending order on their final servers reproduces the
    exact intermediate states of the real construction.
    """
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation, PillowWriter
    from matplotlib.patches import Rectangle

    final = build_greedy_assignment(data)
    order = sorted(range(data.n_tasks), key=lambda i: data.cpu[i], reverse=True)

    # Pre-compute, for every step, whether the chosen server was a best-fit
    # placement or the least-loaded fallback (no feasible server).
    cpu_load = np.zeros(data.n_servers)
    mem_load = np.zeros(data.n_servers)
    rule_used: list[str] = []
    for i in order:
        j = final[i]
        feasible = [
            s for s in range(data.n_servers)
            if cpu_load[s] + data.cpu[i] <= data.server_cpu_cap[s]
            and mem_load[s] + data.mem[i] <= data.server_mem_cap[s]
        ]
        rule_used.append(
            "best fit: most-loaded feasible server" if feasible
            else "FALLBACK: no server fits — least-loaded server"
        )
        cpu_load[j] += data.cpu[i]
        mem_load[j] += data.mem[i]

    y_max = float(max(
        data.server_cpu_cap.max(),
        np.bincount(np.asarray(final), weights=data.cpu, minlength=data.n_servers).max(),
    )) * 1.22

    fig = plt.figure(figsize=(_fig_width(data.n_servers) + 2.6, 7.6))
    gs  = fig.add_gridspec(1, 2, width_ratios=[1.0, 6.0], wspace=0.16)
    ax_q = fig.add_subplot(gs[0, 0])
    ax   = fig.add_subplot(gs[0, 1])
    # Caption sits ABOVE the legend row so the two never collide
    caption = fig.text(0.55, 0.085, "", ha="center", fontsize=10.5,
                       color="#111", fontweight="bold")
    _add_legend(fig)
    fig.subplots_adjust(bottom=0.20, top=0.86)

    n_frames = data.n_tasks + 1
    hold_tail = 4  # freeze on the finished allocation for a few frames

    def frame(k: int) -> None:
        k = min(k, data.n_tasks)
        ax.clear(); ax_q.clear()

        # The first k tasks of the CPU-descending order, on their final servers
        placed_ids = list(order[:k])

        # --- Datacenter panel: only placed tasks are visible ---
        highlight = {order[k - 1]} if k > 0 else set()
        _draw_partial(ax, final, placed_ids, data, y_max=y_max, highlight_tasks=highlight)

        ax.set_title("Greedy Best-Fit Decreasing — building the allocation",
                     fontsize=13, fontweight="bold", pad=30)
        if placed_ids:
            ev = _evaluate_partial(placed_ids, final, data, weights)
            ax.text(0.5, 1.020, ev, transform=ax.transAxes,
                    ha="center", fontsize=9, color="#333")

        # --- Queue panel: remaining tasks, in placement order ---
        remaining = order[k:]
        ax_q.set_title(f"Task queue\n({len(remaining)} waiting)", fontsize=9.5, color="#444")
        row_h = 1.0
        max_rows = 24
        for r, i in enumerate(remaining[:max_rows]):
            w = float(data.cpu[i])
            ax_q.add_patch(Rectangle(
                (0, -r * row_h), w, row_h * 0.82,
                facecolor=PRIORITY_COLORS[int(np.clip(data.priority[i], 0, 2))],
                edgecolor="white", linewidth=0.5, alpha=0.95,
            ))
            if r < 12:
                ax_q.text(w + 2.0, -r * row_h + 0.38, f"T{i}", fontsize=7,
                          va="center", color="#444")
        if len(remaining) > max_rows:
            ax_q.text(0, -(max_rows + 0.8) * row_h, f"… +{len(remaining) - max_rows} more",
                      fontsize=7.5, color="#777")
        ax_q.set_xlim(0, max(float(data.cpu.max()) * 1.35, 1.0))
        ax_q.set_ylim(-(max_rows + 2.5) * row_h, 1.2)
        ax_q.axis("off")
        ax_q.text(0, 1.0, "next ↑ sorted by CPU (desc)", fontsize=7.5, color="#777")

        # --- Caption ---
        if k == 0:
            caption.set_text("Tasks are sorted by CPU demand (heaviest first) and placed one at a time.")
        else:
            i = order[k - 1]
            j = final[i]
            caption.set_text(
                f"Step {k}/{data.n_tasks}:  task T{i} "
                f"(CPU {data.cpu[i]:.0f}%, mem {data.mem[i] / 1024:.1f} GB, "
                f"{PRIORITY_NAMES[int(np.clip(data.priority[i], 0, 2))].split()[0]} prio)"
                f"  →  server S{j}   [{rule_used[k - 1]}]"
            )

    anim = FuncAnimation(fig, frame, frames=n_frames + hold_tail, interval=int(1000 / fps))
    out_dir.mkdir(parents=True, exist_ok=True)
    gif = out_dir / "allocation_greedy_construction.gif"
    print("  rendering greedy-construction GIF (this takes ~30s) ...")
    anim.save(gif, writer=PillowWriter(fps=fps), dpi=80)
    print(f"  saved -> {gif}")

    frame(data.n_tasks)   # leave the figure at the final state
    _save(fig, out_dir, "allocation_greedy_final_frame", show=show, pdf=False)
    if show:
        import matplotlib.pyplot as plt
        plt.show()


def _draw_partial(
    ax,
    final: list[int],
    placed_ids: list[int],
    data: SchedulingProblemData,
    *,
    y_max: float,
    highlight_tasks: set[int],
) -> None:
    """draw_datacenter for a *partial* assignment: only placed tasks shown."""
    placed = set(placed_ids)

    # Mirror of draw_datacenter's loop with unplaced tasks masked out; kept
    # separate so the main renderer stays free of animation-only branches.
    from matplotlib.patches import Rectangle

    m = data.n_servers
    a = np.asarray([final[i] if i in placed else -1 for i in range(data.n_tasks)])
    mask = a >= 0
    cpu_load = np.bincount(a[mask], weights=data.cpu[mask], minlength=m) if mask.any() else np.zeros(m)
    mem_load = np.bincount(a[mask], weights=data.mem[mask], minlength=m) if mask.any() else np.zeros(m)
    counts   = np.bincount(a[mask], minlength=m) if mask.any() else np.zeros(m, dtype=int)

    label_min_h = 0.030 * y_max
    for j in range(m):
        x      = j * (RACK_W + RACK_GAP)
        cap    = float(data.server_cpu_cap[j])
        active = counts[j] > 0
        ax.add_patch(Rectangle(
            (x, 0), RACK_W, cap,
            facecolor="white" if active else IDLE_FACE,
            edgecolor=FRAME_EDGE if active else IDLE_EDGE,
            hatch=None if active else "///",
            linewidth=1.3, zorder=1,
        ))
        tasks_here = [i for i in placed_ids if final[i] == j]
        tasks_here.sort(key=lambda i: data.cpu[i], reverse=True)
        y = 0.0
        for i in tasks_here:
            h = float(data.cpu[i])
            ax.add_patch(Rectangle(
                (x + PAD, y), RACK_W - 2 * PAD, h,
                facecolor=PRIORITY_COLORS[int(np.clip(data.priority[i], 0, 2))],
                edgecolor="black" if i in highlight_tasks else "white",
                linewidth=1.8 if i in highlight_tasks else 0.6,
                alpha=0.95, zorder=3 if i in highlight_tasks else 2,
            ))
            if h >= label_min_h:
                ax.text(x + RACK_W / 2, y + h / 2, f"T{i}", ha="center",
                        va="center", fontsize=7, color="white", zorder=4)
            y += h
        if cpu_load[j] > cap + 1e-9:
            ax.plot([x - 0.06, x + RACK_W + 0.06], [cap, cap],
                    color=OVERLOAD_COLOR, linewidth=1.6, linestyle="--", zorder=5)
        mem_frac = float(mem_load[j] / data.server_mem_cap[j])
        gx = x + RACK_W + 0.07
        ax.add_patch(Rectangle((gx, 0), MEM_W, cap, facecolor="white" if active else IDLE_FACE,
                               edgecolor=IDLE_EDGE, linewidth=0.8, zorder=1))
        if mem_frac > 0:
            ax.add_patch(Rectangle(
                (gx, 0), MEM_W, min(mem_frac, 1.0) * cap,
                facecolor=MEM_COLOR if mem_frac <= 1.0 else OVERLOAD_COLOR,
                edgecolor="none", alpha=0.9, zorder=2,
            ))
        watts = float(data.server_idle_power[j] + data.server_efficiency[j]
                      * sum(data.energy[i] for i in tasks_here)) if active else 0.0
        util = cpu_load[j] / cap * 100
        top  = max(cap, cpu_load[j])
        if active:
            ax.text(x + RACK_W / 2, top + 0.015 * y_max, f"{util:.0f}%\n{watts:.0f} W",
                    ha="center", va="bottom", fontsize=8, color="#222", linespacing=1.25)
        else:
            ax.text(x + RACK_W / 2, top + 0.015 * y_max, "idle\n0 W",
                    ha="center", va="bottom", fontsize=8, color="#999",
                    style="italic", linespacing=1.25)
        cores = data.server_cpu_cap[j] / 100.0
        ax.text(x + RACK_W / 2, -0.055 * y_max,
                f"S{j}\n{cores:.0f}-core\nη={data.server_efficiency[j]:.2f}",
                ha="center", va="top", fontsize=7.5, color="#444", linespacing=1.3)

    ax.set_xlim(-0.5, m * (RACK_W + RACK_GAP) - RACK_GAP + MEM_W + 0.45)
    ax.set_ylim(0, y_max)
    ax.set_xticks([])
    ax.set_ylabel("Server CPU load (%)", fontsize=10)
    for side in ("top", "right", "bottom"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="y", alpha=0.25, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", labelsize=8.5)


def _evaluate_partial(
    placed_ids: list[int],
    final: list[int],
    data: SchedulingProblemData,
    weights: ObjectiveWeights,
) -> str:
    """Human-readable running totals for the partially built greedy solution."""
    placed = list(placed_ids)
    a = np.asarray([final[i] for i in placed])
    m = data.n_servers
    active = np.unique(a)
    idle_e = float(data.server_idle_power[active].sum())
    work_e = float(sum(data.server_efficiency[final[i]] * data.energy[i] for i in placed))
    return (f"{len(placed)}/{data.n_tasks} tasks placed     "
            f"energy so far {idle_e + work_e:,.0f} W     "
            f"active servers {len(active)}/{m}")


# ---------------------------------------------------------------------------
# Animation 2: SA search (best-so-far allocation improving over time)
# ---------------------------------------------------------------------------

def animate_sa_search(
    data: SchedulingProblemData,
    weights: ObjectiveWeights,
    sa_kwargs: dict,
    focus: str,
    seed: int,
    out_dir: Path,
    show: bool,
    max_frames: int = 48,
    fps: int = 3,
) -> None:
    """
    Run SA once (identical settings and seeding as the experiments) while
    recording every improvement of the best-so-far assignment through the
    snapshot_callback observer, then animate the recorded trajectory above
    the convergence curve.
    """
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation, PillowWriter

    snapshots: list[tuple[int, list[int], ScheduleEvaluation, float]] = []

    def record(step, assignment, ev, temperature):
        snapshots.append((step, assignment, ev, temperature))

    print(f"  running SA (seed {seed}) with snapshot recording ...")
    random.seed(seed)
    t0 = time.perf_counter()
    best, best_ev, stats = simulated_annealing(
        data=data, weights=weights, snapshot_callback=record, **sa_kwargs,
    )
    print(f"  SA finished in {time.perf_counter() - t0:.1f}s — "
          f"{len(snapshots)} improvement snapshots, best F = {best_ev.objective_value:.4f}")

    # Downsample to <= max_frames, always keeping first and last
    if len(snapshots) > max_frames:
        idx = np.unique(np.round(np.linspace(0, len(snapshots) - 1, max_frames)).astype(int))
        snapshots = [snapshots[i] for i in idx]

    y_max = float(max(
        data.server_cpu_cap.max(),
        max(np.bincount(np.asarray(s[1]), weights=data.cpu, minlength=data.n_servers).max()
            for s in snapshots),
    )) * 1.22

    fig = plt.figure(figsize=(_fig_width(data.n_servers), 9.4))
    gs  = fig.add_gridspec(2, 1, height_ratios=[4.4, 1.3], hspace=0.34)
    ax   = fig.add_subplot(gs[0])
    ax_c = fig.add_subplot(gs[1])
    _add_legend(fig, highlight_label="Task moved since previous improvement")
    fig.subplots_adjust(bottom=0.11, top=0.90)

    history = stats.best_cost_history
    hold_tail = 5

    def frame(k: int) -> None:
        k = min(k, len(snapshots) - 1)
        step, assignment, ev, temperature = snapshots[k]
        prev = snapshots[k - 1][1] if k > 0 else assignment
        moved = {i for i in range(data.n_tasks) if assignment[i] != prev[i]}

        ax.clear()
        draw_datacenter(ax, assignment, data, y_max=y_max, highlight_tasks=moved)
        label = "greedy start" if step < 0 else f"temperature step {step + 1}/{len(history)}"
        ax.set_title(f"Simulated Annealing — best-so-far allocation   ({label})",
                     fontsize=13, fontweight="bold", pad=30)
        ax.text(0.5, 1.020, _stats_line(ev, data) + f"     T = {temperature:.4g}",
                transform=ax.transAxes, ha="center", fontsize=9, color="#333")

        ax_c.clear()
        ax_c.plot(range(1, len(history) + 1), history, color="#888", linewidth=1.2,
                  label="best F(X) (full run)")
        upto = max(step + 1, 1)
        ax_c.plot(range(1, upto + 1), history[:upto], color=ENERGY_COLOR, linewidth=2.0)
        ax_c.axvline(upto, color=ENERGY_COLOR, linewidth=0.9, linestyle=":")
        ax_c.scatter([upto], [ev.objective_value], color=ENERGY_COLOR, zorder=5, s=28)
        ax_c.annotate(f"F = {ev.objective_value:.4f}", (upto, ev.objective_value),
                      textcoords="offset points", xytext=(8, 8), fontsize=8.5,
                      color=ENERGY_COLOR)
        ax_c.set_xlabel("Temperature step", fontsize=9)
        ax_c.set_ylabel("Best F(X)", fontsize=9)
        ax_c.spines["top"].set_visible(False)
        ax_c.spines["right"].set_visible(False)
        ax_c.grid(alpha=0.25, linewidth=0.6)
        ax_c.set_axisbelow(True)
        ax_c.tick_params(labelsize=8)

    anim = FuncAnimation(fig, frame, frames=len(snapshots) + hold_tail,
                         interval=int(1000 / fps))
    out_dir.mkdir(parents=True, exist_ok=True)
    gif = out_dir / "allocation_sa_search.gif"
    print("  rendering SA-search GIF (this takes ~1 min) ...")
    anim.save(gif, writer=PillowWriter(fps=fps), dpi=80)
    print(f"  saved -> {gif}")

    frame(len(snapshots) - 1)
    _save(fig, out_dir, "allocation_sa_final_frame", show=show, pdf=False)
    if show:
        plt.show()


# ---------------------------------------------------------------------------
# Instance + objective setup (identical to main.py)
# ---------------------------------------------------------------------------

def _load_calibrated(focus: FocusMode):
    cfg  = load_config(Path(__file__).parent / "config.yaml")
    data = load_problem_data(Path(__file__).parent / "datasets",
                             n_tasks=cfg.experiment.n_tasks)
    weights_base = cfg.objective[focus.value]
    weights = weights_base
    if cfg.experiment.normalize_objective:
        if cfg.experiment.normalize_method.lower() == "sample":
            weights, _diag = compute_sample_normalization(
                data, base_weights=weights_base,
                n_samples=cfg.experiment.n_calibration_samples,
                seed=cfg.experiment.calibration_seed,
                penalty_multiplier=cfg.experiment.penalty_multiplier,
                min_feasible=cfg.experiment.min_feasible_calibration,
            )
        else:
            e_ref, l_ref, c_ref, m_ref = compute_normalization_constants(
                data, weights_base.congestion_factor)
            weights = dataclasses.replace(
                weights_base, energy_ref=e_ref, latency_ref=l_ref,
                cpu_ref=c_ref, mem_ref=m_ref)
    return cfg, data, weights


_ALGOS = {
    "SA":   ("Simulated Annealing", simulated_annealing, "sa"),
    "GA":   ("Genetic Algorithm",   genetic_algorithm,   "ga"),
    "UMDA": ("UMDA (EDA)",          umda,                "umda"),
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Visual frontend for the Cloud Resource Allocation problem.")
    parser.add_argument("--focus", "-f", choices=[m.value for m in FocusMode],
                        default=FocusMode.BALANCED.value,
                        help="Objective focus mode (matches main.py).")
    parser.add_argument("--algorithm", "-a", choices=list(_ALGOS.keys()), default="SA",
                        help="Metaheuristic shown next to the Greedy BFD baseline.")
    parser.add_argument("--seed", "-s", type=int, default=0,
                        help="Random seed for the metaheuristic run.")
    parser.add_argument("--style", choices=["detailed", "paper", "both"], default="both",
                        help="Figure style: 'detailed' (screen/appendix, task IDs and "
                             "gauges), 'paper' (print size, simplified — for the thesis "
                             "body), or 'both' (default).")
    parser.add_argument("--animate", choices=["greedy", "sa", "both"], default=None,
                        help="Also render animated GIFs: the greedy construction, "
                             "the SA search, or both.")
    parser.add_argument("--concept", action="store_true",
                        help="Also render the small 12-task/4-server didactic figure "
                             "for the solution-representation section.")
    parser.add_argument("--show", action="store_true",
                        help="Open interactive matplotlib windows as well as saving files.")
    parser.add_argument("--fast", action="store_true",
                        help="Reduce the metaheuristic budget ~5x for a quick look "
                             "(figures are then NOT comparable to the thesis tables).")
    args = parser.parse_args()

    if not args.show:
        matplotlib.use("Agg")

    focus = FocusMode(args.focus)
    out_dir = Path(__file__).parent / "figures" / focus.value

    print("=" * 60)
    print(f"  Cloud Resource Allocation — Visual Frontend  [{focus.value}]")
    print("=" * 60)
    print("  loading instance + calibrating objective (as in main.py) ...")
    cfg, data, weights = _load_calibrated(focus)
    print(f"  instance: {data.n_tasks} tasks x {data.n_servers} servers")

    name, algo_fn, cfg_key = _ALGOS[args.algorithm]
    algo_kwargs = dict(getattr(cfg.algorithms, cfg_key))
    if args.fast:
        if args.algorithm == "SA":
            algo_kwargs["max_temp_steps"] = max(200, algo_kwargs.get("max_temp_steps", 3000) // 5)
        else:
            algo_kwargs["n_generations"] = max(50, algo_kwargs.get("n_generations", 1500) // 5)
        print("  [--fast] reduced budget — results not comparable to thesis tables")

    # ---- Greedy baseline (deterministic) ----
    greedy = build_greedy_assignment(data)

    # ---- Metaheuristic run (same seeding protocol as the experiment harness) ----
    print(f"  running {name} (seed {args.seed}) ...")
    random.seed(args.seed)
    t0 = time.perf_counter()
    best, best_ev, _stats = algo_fn(data=data, weights=weights, **algo_kwargs)
    print(f"  {name}: F = {best_ev.objective_value:.4f}  "
          f"({time.perf_counter() - t0:.1f}s)")

    # ---- Static figures ----
    algo_slug = args.algorithm.lower()
    if args.style in ("detailed", "both"):
        print("\n  rendering detailed figures (screen / appendix) ...")
        render_snapshot(greedy, data, weights, "Greedy BFD (baseline)",
                        focus.value, out_dir, "allocation_greedy", args.show)
        render_snapshot(best, data, weights, name,
                        focus.value, out_dir, f"allocation_{algo_slug}", args.show)
        render_comparison(greedy, "Greedy BFD (baseline)", best, name,
                          data, weights, focus.value, out_dir,
                          f"allocation_comparison_greedy_vs_{algo_slug}", args.show)
    if args.style in ("paper", "both"):
        print("\n  rendering paper figures (print size, simplified) ...")
        render_paper_snapshot(greedy, data, weights, "Greedy BFD (baseline)",
                              out_dir, "allocation_greedy_paper", args.show)
        render_paper_snapshot(best, data, weights, name,
                              out_dir, f"allocation_{algo_slug}_paper", args.show)
        render_paper_comparison(greedy, "Greedy BFD (baseline)", best, name,
                                data, weights, out_dir,
                                f"allocation_comparison_greedy_vs_{algo_slug}_paper",
                                args.show)

    # ---- Didactic concept figure (focus-independent) ----
    if args.concept:
        print("\n  rendering concept figure (12 tasks x 4 servers) ...")
        render_concept_figure(Path(__file__).parent, args.show)

    # ---- Animations ----
    if args.animate in ("greedy", "both"):
        print("\n  animating greedy construction ...")
        animate_greedy_construction(data, weights, focus.value, out_dir, args.show)
    if args.animate in ("sa", "both"):
        print("\n  animating SA search ...")
        sa_kwargs = dict(cfg.algorithms.sa)
        if args.fast:
            sa_kwargs["max_temp_steps"] = max(200, sa_kwargs.get("max_temp_steps", 3000) // 5)
        animate_sa_search(data, weights, sa_kwargs, focus.value,
                          args.seed, out_dir, args.show)

    if args.show:
        import matplotlib.pyplot as plt
        plt.show()

    print("\n  Done. All visual outputs are in:")
    print(f"    {out_dir}")


if __name__ == "__main__":
    main()
