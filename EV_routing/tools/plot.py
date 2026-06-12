from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.figure
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches

from tools.experiment import ExperimentResults
from tools.tuning import TrialResult


# ---------------------------------------------------------------------------
# Global style — applied once at import
# ---------------------------------------------------------------------------

def _setup_style() -> None:
    plt.rcParams.update({
        "savefig.dpi": 200,
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "legend.framealpha": 0.9,
        "legend.edgecolor": "#cccccc",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linewidth": 0.65,
        "grid.color": "#bbbbbb",
        "lines.linewidth": 2.0,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "xtick.direction": "out",
        "ytick.direction": "out",
        "axes.axisbelow": True,
    })


_setup_style()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Wong (2011) colorblind-safe palette
_ALGO_COLORS = [
    "#0072B2",  # blue
    "#D55E00",  # vermilion
    "#009E73",  # bluish green
    "#E69F00",  # orange
    "#CC79A7",  # reddish purple
    "#56B4E9",  # sky blue
    "#F0E442",  # yellow
]


def _algo_color(idx: int) -> str:
    return _ALGO_COLORS[idx % len(_ALGO_COLORS)]


def _save_and_show(fig: matplotlib.figure.Figure, save_path: Any, show: bool) -> None:
    if save_path is not None:
        p = Path(save_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(p, dpi=200, bbox_inches="tight")
        print(f"Saved: {p}")
    if show:
        plt.show()
    else:
        plt.close(fig)


# ---------------------------------------------------------------------------
# 1. Convergence by step (original, kept for backward compatibility)
# ---------------------------------------------------------------------------

def plot_convergence(
    results: ExperimentResults | list[ExperimentResults],
    title: str | None = None,
    save_path: str | Path | None = None,
    show: bool = True,
) -> matplotlib.figure.Figure:
    """
    Best-cost convergence curves indexed by algorithm step.

    For SA a step is one temperature reduction; for GA a step is one generation.
    X-axes are NOT comparable across algorithms — use plot_convergence_by_evaluations
    for a controlled comparison.
    """
    if isinstance(results, ExperimentResults):
        results_list = [results]
    else:
        results_list = list(results)

    fig, ax = plt.subplots(figsize=(11, 5))

    for idx, exp in enumerate(results_list):
        histories = [
            s.best_cost_history
            for s in exp.all_stats
            if hasattr(s, "best_cost_history") and s.best_cost_history
        ]
        if not histories:
            print(f"Warning: {exp.algorithm_name} has no best_cost_history — skipped.")
            continue

        max_len = max(len(h) for h in histories)
        padded = np.array([h + [h[-1]] * (max_len - len(h)) for h in histories])
        steps = np.arange(1, max_len + 1)
        mean = padded.mean(axis=0)
        std = padded.std(axis=0)

        color = _algo_color(idx)
        ax.plot(steps, mean, linewidth=2.0, label=exp.algorithm_name, color=color)
        ax.fill_between(steps, mean - std, mean + std, alpha=0.12, color=color)

    ax.set_xlabel("Step (temperature reduction / generation)")
    ax.set_ylabel("Best objective value")
    ax.set_title(title or "Convergence by algorithm step")
    ax.legend(loc="upper right")
    plt.tight_layout()
    _save_and_show(fig, save_path, show)
    return fig


# ---------------------------------------------------------------------------
# 2. Convergence by evaluations — fair cross-algorithm comparison
# ---------------------------------------------------------------------------

def plot_convergence_by_evaluations(
    results: ExperimentResults | list[ExperimentResults],
    title: str | None = None,
    save_path: str | Path | None = None,
    show: bool = True,
) -> matplotlib.figure.Figure:
    """
    Best-cost convergence with number of objective evaluations on the x-axis.

    Uses ``stats.evals_at_step`` so both SA (per temperature step) and GA
    (per generation) are placed on the same evaluation axis, enabling a
    fair computational-budget comparison for the thesis.
    """
    if isinstance(results, ExperimentResults):
        results_list = [results]
    else:
        results_list = list(results)

    fig, ax = plt.subplots(figsize=(11, 5))

    for idx, exp in enumerate(results_list):
        valid = [
            (s.evals_at_step, s.best_cost_history)
            for s in exp.all_stats
            if hasattr(s, "evals_at_step") and s.evals_at_step and s.best_cost_history
        ]
        if not valid:
            print(f"Warning: {exp.algorithm_name} has no evals_at_step — skipped.")
            continue

        all_evals = [v[0] for v in valid]
        all_costs = [v[1] for v in valid]
        max_eval = max(e[-1] for e in all_evals)
        grid = np.linspace(0, max_eval, 600)

        interp_costs = []
        for evals, costs in zip(all_evals, all_costs):
            interp_costs.append(np.interp(grid, evals, costs))

        mat = np.array(interp_costs)
        mean = mat.mean(axis=0)
        std = mat.std(axis=0)

        color = _algo_color(idx)
        ax.plot(grid / 1_000, mean, linewidth=2.0, label=exp.algorithm_name, color=color)
        ax.fill_between(grid / 1_000, mean - std, mean + std, alpha=0.10, color=color)

    ax.set_xlabel("Objective evaluations (thousands)")
    ax.set_ylabel("Best objective value")
    ax.set_title(title or "Convergence by evaluation budget")
    ax.legend(loc="upper right")
    plt.tight_layout()
    _save_and_show(fig, save_path, show)
    return fig


# ---------------------------------------------------------------------------
# 3. Box plot — robustness across seeds
# ---------------------------------------------------------------------------

def plot_box_comparison(
    results: ExperimentResults | list[ExperimentResults],
    title: str | None = None,
    save_path: str | Path | None = None,
    show: bool = True,
) -> matplotlib.figure.Figure:
    """
    Side-by-side box plots of final solution costs across all seeds.

    Visualises solution quality *and* robustness: a tighter box means more
    consistent results; outliers reveal sensitivity to initialisation.
    """
    if isinstance(results, ExperimentResults):
        results_list = [results]
    else:
        results_list = list(results)

    n = len(results_list)
    fig, ax = plt.subplots(figsize=(max(5, 2.2 * n), 5))

    data_to_plot = [exp.best_costs for exp in results_list]
    labels = [exp.algorithm_name for exp in results_list]
    colors = [_algo_color(i) for i in range(n)]

    bp = ax.boxplot(
        data_to_plot,
        labels=labels,
        patch_artist=True,
        medianprops={"color": "#222222", "linewidth": 2.2},
        whiskerprops={"linewidth": 1.3, "linestyle": "--", "color": "#555555"},
        capprops={"linewidth": 1.3, "color": "#555555"},
        flierprops={"marker": "o", "markersize": 4, "alpha": 0.5, "markeredgewidth": 0},
        widths=0.45,
    )
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.55)
        patch.set_linewidth(1.2)

    rng = np.random.default_rng(0)
    for i, (costs, color) in enumerate(zip(data_to_plot, colors), start=1):
        jitter = rng.uniform(-0.15, 0.15, len(costs))
        ax.scatter(
            np.full(len(costs), i) + jitter,
            costs,
            color=color,
            s=28,
            zorder=4,
            alpha=0.85,
            edgecolors="white",
            linewidths=0.5,
        )

    # Annotate mean above each box
    ymin, ymax = ax.get_ylim()
    for i, costs in enumerate(data_to_plot, start=1):
        ax.text(
            i, np.mean(costs) + (ymax - ymin) * 0.005,
            f"μ={np.mean(costs):.3f}",
            ha="center", va="bottom", fontsize=8.5, color="#333333",
        )

    ax.set_ylabel("Best objective value")
    ax.set_title(title or "Solution quality across seeds")
    ax.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    _save_and_show(fig, save_path, show)
    return fig


# ---------------------------------------------------------------------------
# 4. Runtime comparison — wall-clock vs CPU time per algorithm
# ---------------------------------------------------------------------------

def plot_runtime_comparison(
    results: list[ExperimentResults],
    title: str | None = None,
    save_path: str | Path | None = None,
    show: bool = True,
) -> matplotlib.figure.Figure:
    """
    Two-panel figure:
      Left  — mean wall-clock time ± std per algorithm (grouped bars).
      Right — CPU efficiency = mean CPU time / mean wall time per algorithm.

    CPU efficiency close to 1.0 means the algorithm is fully CPU-bound.
    """
    names        = [r.algorithm_name for r in results]
    wall_means   = [r.average_runtime  for r in results]
    wall_stds    = [r.std_runtime      for r in results]
    cpu_means    = [r.average_cpu_time for r in results]
    cpu_stds     = [r.std_cpu_time     for r in results]
    efficiencies = [r.cpu_efficiency   for r in results]

    x      = np.arange(len(names))
    width  = 0.35
    colors = [_algo_color(i) for i in range(len(results))]

    fig, (ax_time, ax_eff) = plt.subplots(1, 2, figsize=(13, 5))

    for i, (wm, ws, cm, cs, color) in enumerate(
        zip(wall_means, wall_stds, cpu_means, cpu_stds, colors)
    ):
        ax_time.bar(
            x[i] - width / 2, wm, width, yerr=ws,
            color=color, alpha=0.85, capsize=5, label=None,
            error_kw={"linewidth": 1.2, "ecolor": "#555555"},
        )
        ax_time.bar(
            x[i] + width / 2, cm, width, yerr=cs,
            color=color, alpha=0.35, capsize=5, hatch="///", label=None,
            error_kw={"linewidth": 1.2, "ecolor": "#555555"},
        )

    wall_patch = mpatches.Patch(facecolor="#777777", alpha=0.85, label="Wall-clock time")
    cpu_patch  = mpatches.Patch(facecolor="#777777", alpha=0.35, hatch="///", label="CPU time")
    ax_time.legend(handles=[wall_patch, cpu_patch], loc="upper left")
    ax_time.set_xticks(x)
    ax_time.set_xticklabels(names, rotation=15, ha="right")
    ax_time.set_ylabel("Time (s)")
    ax_time.set_title("Mean runtime per seed ± std")

    bars = ax_eff.bar(names, efficiencies, color=colors, alpha=0.78,
                      edgecolor="white", linewidth=0)
    ax_eff.axhline(1.0, color="#333333", linewidth=1.0, linestyle="--",
                   label="Fully CPU-bound (1.0)")
    ax_eff.set_ylim(0, max(1.2, max(efficiencies) * 1.12))
    ax_eff.set_ylabel("CPU time / wall time")
    ax_eff.set_title("CPU efficiency")
    ax_eff.set_xticklabels(names, rotation=15, ha="right")
    ax_eff.legend(fontsize=9)

    for bar, v in zip(bars, efficiencies):
        ax_eff.text(
            bar.get_x() + bar.get_width() / 2, v + 0.015,
            f"{v:.2f}", ha="center", va="bottom", fontsize=9,
        )

    fig.suptitle(title or "Runtime comparison", fontsize=13)
    plt.tight_layout()
    _save_and_show(fig, save_path, show)
    return fig


# ---------------------------------------------------------------------------
# 5. SA diagnostics — explains SA's exploration/exploitation transition
# ---------------------------------------------------------------------------

def plot_sa_diagnostics(
    results: ExperimentResults,
    seed_idx: int = 0,
    title: str | None = None,
    save_path: str | Path | None = None,
    show: bool = True,
) -> matplotlib.figure.Figure:
    """
    Three-panel diagnostic for a single SA run:

    - Top:    Temperature schedule (shows geometric cooling + any reheats)
    - Middle: Current−Best gap (smoothed) — high early = exploration; low late = exploitation
    - Bottom: Best cost vs current cost
    """
    stats = results.all_stats[seed_idx]
    if not hasattr(stats, "temperature_history") or not stats.temperature_history:
        print(f"No SA diagnostics available for seed index {seed_idx}.")
        return plt.figure()

    steps   = np.arange(1, len(stats.best_cost_history) + 1)
    temp    = np.array(stats.temperature_history[: len(steps)])
    best    = np.array(stats.best_cost_history)
    current = np.array(stats.current_cost_history[: len(steps)])
    gap     = current - best

    c_main = _algo_color(1)
    c_sec  = _algo_color(2)

    fig, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=True)
    fig.suptitle(
        title or f"{results.algorithm_name} — diagnostics (seed {seed_idx})",
        fontsize=13,
    )

    axes[0].plot(steps, temp, color=c_main, linewidth=1.8)
    axes[0].set_ylabel("Temperature (log scale)")
    axes[0].set_yscale("log")
    axes[0].yaxis.set_minor_formatter(plt.NullFormatter())

    axes[1].plot(steps, gap, color=c_sec, linewidth=0.8, alpha=0.45)
    if len(gap) > 20:
        w = max(5, len(gap) // 60)
        smooth = np.convolve(gap, np.ones(w) / w, mode="same")
        axes[1].plot(steps, smooth, color=c_sec, linewidth=1.9,
                     label=f"Smoothed (w={w})")
        axes[1].legend(loc="upper right")
    axes[1].set_ylabel("Current − Best (exploration gap)")
    axes[1].set_ylim(bottom=0)

    axes[2].plot(steps, best,    color=c_main, linewidth=2.0, label="Best")
    axes[2].plot(steps, current, color=c_sec,  linewidth=0.9, alpha=0.5, label="Current")
    axes[2].set_ylabel("Objective value")
    axes[2].set_xlabel("Temperature step")
    axes[2].legend(loc="upper right")

    for ax in axes:
        ax.grid(True, alpha=0.28)

    plt.tight_layout()
    _save_and_show(fig, save_path, show)
    return fig


# ---------------------------------------------------------------------------
# 6. GA diagnostics — explains GA's population dynamics
# ---------------------------------------------------------------------------

def plot_ga_diagnostics(
    results: ExperimentResults,
    seed_idx: int = 0,
    title: str | None = None,
    save_path: str | Path | None = None,
    show: bool = True,
) -> matplotlib.figure.Figure:
    """
    Three-panel diagnostic for a single GA run:

    - Top:    Best cost vs population mean cost per generation
    - Middle: Population diversity (coefficient of variation of costs)
    - Bottom: Fraction of the population that is feasible over time
    """
    stats = results.all_stats[seed_idx]
    if not hasattr(stats, "mean_cost_history") or not stats.mean_cost_history:
        print(f"No GA diagnostics available for seed index {seed_idx}.")
        return plt.figure()

    gens = np.arange(1, len(stats.best_cost_history) + 1)
    best = np.array(stats.best_cost_history)
    mean = np.array(stats.mean_cost_history[: len(gens)])
    div  = np.array(stats.diversity_history[: len(gens)])
    feas = np.array(stats.feasibility_history[: len(gens)])

    c_best = _algo_color(2)
    c_mean = _algo_color(3)
    c_div  = _algo_color(3)
    c_feas = _algo_color(4)

    fig, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=True)
    fig.suptitle(
        title or f"{results.algorithm_name} — diagnostics (seed {seed_idx})",
        fontsize=13,
    )

    axes[0].plot(gens, mean, color=c_mean, linewidth=1.5, alpha=0.7, label="Population mean")
    axes[0].plot(gens, best, color=c_best, linewidth=2.0, label="Best")
    axes[0].set_ylabel("Objective value")
    axes[0].legend(loc="upper right")

    axes[1].plot(gens, div, color=c_div, linewidth=1.8)
    axes[1].set_ylabel("Diversity (cost CV)")
    axes[1].set_ylim(bottom=0)

    axes[2].plot(gens, feas * 100, color=c_feas, linewidth=1.8)
    axes[2].set_ylabel("Feasible population (%)")
    axes[2].set_xlabel("Generation")
    axes[2].set_ylim(0, 105)

    for ax in axes:
        ax.grid(True, alpha=0.28)

    plt.tight_layout()
    _save_and_show(fig, save_path, show)
    return fig


# ---------------------------------------------------------------------------
# 7. Cost component breakdown — what drives the objective?
# ---------------------------------------------------------------------------

def plot_cost_breakdown(
    results: ExperimentResults | list[ExperimentResults],
    title: str | None = None,
    save_path: str | Path | None = None,
    show: bool = True,
) -> matplotlib.figure.Figure:
    """
    Six-panel figure showing raw cost components for the best solution per algorithm.

    Each panel shows one metric (distance, travel time, charging time, energy,
    charging cost, total weighted objective) with one bar per algorithm.
    Actual values are displayed, not a normalised percentage, so magnitudes
    are directly comparable within each panel.
    """
    if isinstance(results, ExperimentResults):
        results_list = [results]
    else:
        results_list = list(results)

    labels = [exp.algorithm_name for exp in results_list]
    colors = [_algo_color(i) for i in range(len(results_list))]
    x      = np.arange(len(labels))
    width  = 0.55

    # Pre-extract metric matrix: shape (n_algos, 5)
    metrics = np.array([
        [
            exp.best_eval.total_distance_km,
            exp.best_eval.total_travel_time_h,
            exp.best_eval.total_charging_time_h,
            exp.best_eval.total_energy_consumed_kwh,
            exp.best_eval.total_charging_cost_usd,
        ]
        for exp in results_list
    ])
    total_obj = np.array([exp.best_cost for exp in results_list])

    panel_specs = [
        ("Distance",        "km",  0),
        ("Travel time",     "h",   1),
        ("Charging time",   "h",   2),
        ("Energy consumed", "kWh", 3),
        ("Charging cost",   "USD", 4),
    ]

    fig, axes = plt.subplots(2, 3, figsize=(13, 7))
    fig.suptitle(
        title or "Cost component breakdown — best solution per algorithm",
        fontsize=12,
    )
    axes_flat = axes.flatten()

    def _draw_bars(ax, vals, ylabel, panel_title, fmt=".1f"):
        bars = ax.bar(x, vals, width=width, color=colors, alpha=0.80,
                      edgecolor="white", linewidth=0)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=22, ha="right", fontsize=9)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.set_title(panel_title, fontsize=10)
        ypad = (vals.max() - vals.min()) * 0.04 + vals.max() * 0.01
        for bar, v in zip(bars, vals):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                v + ypad,
                f"{v:{fmt}}",
                ha="center", va="bottom", fontsize=8.5,
            )

    for ax, (cname, unit, cidx) in zip(axes_flat[:5], panel_specs):
        _draw_bars(ax, metrics[:, cidx], unit, cname)

    _draw_bars(axes_flat[5], total_obj, "Objective", "Total objective", fmt=".3f")

    plt.tight_layout()
    _save_and_show(fig, save_path, show)
    return fig


# ---------------------------------------------------------------------------
# 8. ACO diagnostics — pheromone learning + exploration
# ---------------------------------------------------------------------------

def plot_aco_diagnostics(
    results: ExperimentResults,
    seed_idx: int = 0,
    title: str | None = None,
    save_path: str | Path | None = None,
    show: bool = True,
) -> matplotlib.figure.Figure:
    """
    Three-panel diagnostic for a single ACO run:

    - Top:    Best cost vs iteration mean cost
    - Middle: Pheromone coefficient of variation — rises as trails concentrate
    - Bottom: Fraction of the ant colony that is feasible per iteration
    """
    stats = results.all_stats[seed_idx]
    if not hasattr(stats, "pheromone_cv_history") or not stats.pheromone_cv_history:
        print(f"No ACO diagnostics available for seed index {seed_idx}.")
        return plt.figure()

    iters = np.arange(1, len(stats.best_cost_history) + 1)
    best  = np.array(stats.best_cost_history)
    mean  = np.array(stats.mean_cost_history[: len(iters)])
    ph_cv = np.array(stats.pheromone_cv_history[: len(iters)])
    feas  = np.array(stats.feasibility_history[: len(iters)])

    c_best = _algo_color(0)
    c_mean = _algo_color(3)
    c_ph   = _algo_color(3)
    c_feas = _algo_color(4)

    fig, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=True)
    fig.suptitle(
        title or f"{results.algorithm_name} — diagnostics (seed {seed_idx})",
        fontsize=13,
    )

    axes[0].plot(iters, mean, color=c_mean, linewidth=1.5, alpha=0.7, label="Iteration mean")
    axes[0].plot(iters, best, color=c_best, linewidth=2.0, label="Best so far")
    axes[0].set_ylabel("Objective value")
    axes[0].legend(loc="upper right")

    axes[1].plot(iters, ph_cv, color=c_ph, linewidth=1.8)
    axes[1].set_ylabel("Pheromone CV (std / mean τ)")
    axes[1].set_ylim(bottom=0)

    axes[2].plot(iters, feas * 100, color=c_feas, linewidth=1.8)
    axes[2].set_ylabel("Feasible ants (%)")
    axes[2].set_xlabel("Iteration")
    axes[2].set_ylim(0, 105)

    for ax in axes:
        ax.grid(True, alpha=0.28)

    plt.tight_layout()
    _save_and_show(fig, save_path, show)
    return fig


# ---------------------------------------------------------------------------
# 9. Scalability analysis — two axes
# ---------------------------------------------------------------------------

def plot_scalability(
    customer_data: dict,
    battery_data: dict,
    figures_dir: str | Path | None = None,
    save_path: str | Path | None = None,   # legacy — ignored when figures_dir set
    show: bool = True,
) -> None:
    """
    Two separate 2-panel scalability figures, matching the Cloud scheduling structure.

    scalability_customer.png
      Left:  avg runtime vs number of customers  (log x-axis)
      Right: improvement over Greedy (%) vs number of customers

    scalability_battery.png
      Left:  improvement over Greedy (%) vs battery capacity (kWh, inverted axis)
      Right: feasibility rate (%) vs battery capacity (kWh, inverted axis)

    Pass ``figures_dir`` to save both files; ``save_path`` is accepted for
    backward compatibility but ignored when figures_dir is provided.
    """
    out_dir = Path(figures_dir) if figures_dir is not None else (
        Path(save_path).parent if save_path is not None else Path(".")
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    algo_names = list(customer_data.keys()) if customer_data else list(battery_data.keys())
    colors = {name: _algo_color(i) for i, name in enumerate(algo_names)}

    def _plot_line(ax, name, x, y, color, marker="o"):
        ax.plot(x, y, marker=marker, color=color, linewidth=2.0, label=name)

    # ── Figure 1: customer count scaling ─────────────────────────────────────
    if customer_data:
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        fig.suptitle(
            "Horizontal Scalability — dedicated SF instances sf_25 … sf_500",
            fontsize=12, fontweight="bold",
        )

        for name, d in customer_data.items():
            c = colors[name]
            _plot_line(axes[0], name, d["sizes"], d["runtimes"], c)
            _plot_line(axes[1], name, d["sizes"], d["costs"],    c)

        for ax in axes:
            ax.set_xscale("log")
            ax.legend(fontsize=9)

        axes[0].set_xlabel("Number of customers  (log scale)", fontsize=11)
        axes[0].set_ylabel("Average runtime per seed (s)", fontsize=11)
        axes[0].set_title("Runtime Scaling", fontsize=12, fontweight="bold")

        axes[1].set_xlabel("Number of customers  (log scale)", fontsize=11)
        axes[1].set_ylabel("Average objective value  (lower = better)", fontsize=11)
        axes[1].set_title("Solution Quality vs. Problem Size", fontsize=12, fontweight="bold")

        plt.tight_layout()
        p = out_dir / "scalability_customer.png"
        fig.savefig(p, dpi=200, bbox_inches="tight")
        plt.close(fig)
        print(f"  Customer scalability plot   -> {p}")

    # ── Figure 2: battery constraint tightness ───────────────────────────────
    if battery_data:
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        fig.suptitle(
            "Vertical Scalability — 75 customers, battery capacity varied from loose to tight",
            fontsize=12, fontweight="bold",
        )

        for name, d in battery_data.items():
            c = colors[name]
            _plot_line(axes[0], name, d["capacities"], d["costs"],        c)
            _plot_line(axes[1], name, d["capacities"], d["feasible_pct"], c, marker="s")

        for ax in axes:
            ax.invert_xaxis()
            ax.legend(fontsize=9)

        axes[0].set_xlabel("Battery capacity (kWh)  (← more constrained)", fontsize=11)
        axes[0].set_ylabel("Average objective value  (lower = better)", fontsize=11)
        axes[0].set_title("Solution Quality vs. Constraint Tightness", fontsize=12, fontweight="bold")

        axes[1].set_xlabel("Battery capacity (kWh)  (← more constrained)", fontsize=11)
        axes[1].set_ylabel("Feasible solutions (%)", fontsize=11)
        axes[1].set_title("Feasibility Rate vs. Constraint Tightness", fontsize=12, fontweight="bold")
        axes[1].set_ylim(-5, 110)
        axes[1].axhline(100, color="#888888", linewidth=0.8, linestyle=":")

        plt.tight_layout()
        p = out_dir / "scalability_battery.png"
        fig.savefig(p, dpi=200, bbox_inches="tight")
        plt.close(fig)
        print(f"  Battery scalability plot    -> {p}")


# ---------------------------------------------------------------------------
# 10. Tuning results — search landscape visualisation
# ---------------------------------------------------------------------------

def plot_tuning_results(
    results: list[TrialResult],
    algorithm_name: str = "",
    save_path: str | Path | None = None,
    show: bool = True,
) -> matplotlib.figure.Figure:
    """
    Two-panel tuning analysis figure.

    Top panel — Best-score progression over trials.
    Bottom panels — Per-parameter sensitivity (one box per param).
    """
    if not results:
        return plt.figure()

    param_keys   = [k for k in results[0] if k not in ("mean_cost", "seed_costs")]
    costs        = np.array([r["mean_cost"] for r in results])
    n_trials     = len(results)
    running_best = np.minimum.accumulate(costs)

    n_params     = len(param_keys)
    n_sens_rows  = (n_params + 2) // 3
    total_rows   = 1 + n_sens_rows

    fig = plt.figure(figsize=(14, 3.8 * total_rows))
    gs  = gridspec.GridSpec(total_rows, 3, figure=fig, hspace=0.55, wspace=0.38)

    t = (
        f"{algorithm_name} — tuning results ({n_trials} trials)"
        if algorithm_name
        else f"Tuning results ({n_trials} trials)"
    )
    fig.suptitle(t, fontsize=12)

    ax_prog = fig.add_subplot(gs[0, :])
    ax_prog.scatter(
        range(1, n_trials + 1), costs,
        s=20, alpha=0.45, color=_algo_color(0), zorder=2,
        label="Trial score", edgecolors="none",
    )
    ax_prog.plot(
        range(1, n_trials + 1), running_best,
        color=_algo_color(1), linewidth=2.0, label="Best so far",
    )
    ax_prog.set_xlabel("Trial")
    ax_prog.set_ylabel("Mean objective value")
    ax_prog.set_title("Score progression")
    ax_prog.legend()

    for p_idx, key in enumerate(param_keys):
        row = 1 + p_idx // 3
        col = p_idx % 3
        ax  = fig.add_subplot(gs[row, col])

        unique_vals = sorted(set(r[key] for r in results))
        grouped     = [[r["mean_cost"] for r in results if r[key] == v] for v in unique_vals]
        lbs         = [str(v) for v in unique_vals]

        bp = ax.boxplot(
            grouped,
            labels=lbs,
            patch_artist=True,
            medianprops={"color": "#222222", "linewidth": 1.6},
            whiskerprops={"linewidth": 1.0},
            capprops={"linewidth": 1.0},
            flierprops={"markersize": 3},
        )
        for patch in bp["boxes"]:
            patch.set_facecolor(_algo_color(p_idx))
            patch.set_alpha(0.55)

        ax.set_title(key, fontsize=9)
        ax.set_ylabel("Score" if col == 0 else "")
        ax.tick_params(axis="x", labelsize=7.5)

    plt.tight_layout()
    _save_and_show(fig, save_path, show)
    return fig


# ---------------------------------------------------------------------------
# 10. Optimality gap comparison
# ---------------------------------------------------------------------------

def plot_optimality_gap_comparison(
    gap_data: list[dict],
    figures_dir: str | Path | None = None,
    save_path: str | Path | None = None,
    show: bool = True,
) -> matplotlib.figure.Figure:
    """
    Two-panel optimality gap figure.

    Left  — grouped bars (best cost / avg cost) per algorithm with a dashed
             BKS reference line and gap-% annotations.
    Right — gap percentage bars (gap_best and gap_avg) showing how far each
            algorithm sits from the Best-Known Solution.
    """
    if not gap_data:
        return plt.figure()

    names     = [d["algorithm"]   for d in gap_data]
    bests     = np.array([d["best_cost"]    for d in gap_data])
    avgs      = np.array([d["avg_cost"]     for d in gap_data])
    gap_bests = np.array([d["gap_best_pct"] for d in gap_data])
    gap_avgs  = np.array([d["gap_avg_pct"]  for d in gap_data])
    bks       = gap_data[0]["bks"]
    n_runs    = gap_data[0]["n_runs"]

    n      = len(names)
    x      = np.arange(n)
    width  = 0.35
    colors = [_algo_color(i) for i in range(n)]

    fig, (ax_cost, ax_gap) = plt.subplots(1, 2, figsize=(max(12, 3.2 * n), 6))
    fig.suptitle(
        f"Optimality Gap vs. Best-Known Solution (BKS)  —  {n_runs} seeds per algorithm",
        fontsize=12, fontweight="bold",
    )

    # ── Left panel: absolute costs ────────────────────────────────────────────
    for i, (best, avg, color) in enumerate(zip(bests, avgs, colors)):
        ax_cost.bar(x[i] - width / 2, best, width, color=color, alpha=0.88,
                    edgecolor="white", linewidth=0)
        ax_cost.bar(x[i] + width / 2, avg,  width, color=color, alpha=0.40,
                    edgecolor="white", linewidth=0, hatch="///")

    ax_cost.axhline(bks, color="#CC0000", linewidth=1.8, linestyle="--",
                    zorder=5, label=f"BKS = {bks:.4f}")

    # Annotate avg-gap above each pair
    ymax_data = max(max(bests), max(avgs))
    offset    = ymax_data * 0.025
    for i, (best, avg, ga) in enumerate(zip(bests, avgs, gap_avgs)):
        top = max(best, avg) + offset
        ax_cost.text(x[i], top, f"+{ga:.1f}%",
                     ha="center", va="bottom", fontsize=9, color="#333333",
                     fontweight="bold")

    best_patch = mpatches.Patch(facecolor="#777777", alpha=0.88, label="Best cost")
    avg_patch  = mpatches.Patch(facecolor="#777777", alpha=0.40, hatch="///",
                                label="Avg cost")
    bks_line   = plt.Line2D([0], [0], color="#CC0000", linewidth=1.8,
                             linestyle="--", label=f"BKS = {bks:.4f}")
    ax_cost.legend(handles=[best_patch, avg_patch, bks_line],
                   loc="upper left", fontsize=9)
    ax_cost.set_xticks(x)
    ax_cost.set_xticklabels(names, rotation=15, ha="right")
    ax_cost.set_ylabel("Objective value  (lower = better)")
    ax_cost.set_title("Absolute Costs vs. BKS", fontsize=11, fontweight="bold")
    # Add a small top margin so annotations don't clip
    cur_top = ax_cost.get_ylim()[1]
    ax_cost.set_ylim(top=max(cur_top, ymax_data + offset * 6))

    # ── Right panel: gap percentages ──────────────────────────────────────────
    x2 = np.arange(n)
    for i, (gb, ga, color) in enumerate(zip(gap_bests, gap_avgs, colors)):
        ax_gap.bar(x2[i] - width / 2, gb, width, color=color, alpha=0.88,
                   edgecolor="white", linewidth=0)
        ax_gap.bar(x2[i] + width / 2, ga, width, color=color, alpha=0.40,
                   edgecolor="white", linewidth=0, hatch="///")

    ax_gap.axhline(0, color="#CC0000", linewidth=1.5, linestyle="--",
                   zorder=5, label="BKS (0 % gap)")

    best_patch2 = mpatches.Patch(facecolor="#777777", alpha=0.88, label="Best-cost gap")
    avg_patch2  = mpatches.Patch(facecolor="#777777", alpha=0.40, hatch="///",
                                 label="Avg-cost gap")
    bks_line2   = plt.Line2D([0], [0], color="#CC0000", linewidth=1.5,
                              linestyle="--", label="BKS (0 % gap)")
    ax_gap.legend(handles=[best_patch2, avg_patch2, bks_line2],
                  loc="upper left", fontsize=9)
    ax_gap.set_xticks(x2)
    ax_gap.set_xticklabels(names, rotation=15, ha="right")
    ax_gap.set_ylabel("Gap above BKS (%)")
    ax_gap.set_title("Optimality Gap (%)", fontsize=11, fontweight="bold")
    ax_gap.set_ylim(bottom=0)

    # Value labels
    ymax_gap = max(max(gap_bests), max(gap_avgs))
    off2     = ymax_gap * 0.025
    for i, (gb, ga) in enumerate(zip(gap_bests, gap_avgs)):
        ax_gap.text(x2[i] - width / 2, gb + off2, f"{gb:.1f}%",
                    ha="center", va="bottom", fontsize=8, color="#333333")
        ax_gap.text(x2[i] + width / 2, ga + off2, f"{ga:.1f}%",
                    ha="center", va="bottom", fontsize=8, color="#333333")

    plt.tight_layout()

    if figures_dir is not None:
        p = Path(figures_dir) / "optimality_gap.png"
        p.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(p, dpi=200, bbox_inches="tight")
        print(f"  Optimality gap plot     -> {p}")
        if not show:
            plt.close(fig)
            return fig

    _save_and_show(fig, save_path, show)
    return fig


# ---------------------------------------------------------------------------
# 11. Summary table (console)
# ---------------------------------------------------------------------------

def print_comparison_table(results_list: list[ExperimentResults]) -> None:
    """
    Print a formatted results table across algorithms — ready to copy into a thesis.

    Columns: Algorithm | Best | Average | Worst | Std | Feasible | Avg Time
    """
    col_widths = [22, 10, 10, 10, 10, 10, 10]
    headers    = ["Algorithm", "Best", "Average", "Worst", "Std Dev", "Feasible", "Avg Time"]

    header_line = "  ".join(
        h.ljust(w) if i == 0 else h.rjust(w)
        for i, (h, w) in enumerate(zip(headers, col_widths))
    )
    separator = "-" * len(header_line)

    print(separator)
    print(header_line)
    print(separator)

    for r in results_list:
        feasible_str = f"{r.feasible_run_count}/{len(r.seeds)}"
        time_str     = f"{r.average_runtime:.1f}s"
        row = [
            r.algorithm_name,
            f"{r.best_cost:.2f}",
            f"{r.average_cost:.2f}",
            f"{r.worst_cost:.2f}",
            f"{r.std_cost:.2f}",
            feasible_str,
            time_str,
        ]
        print("  ".join(
            v.ljust(col_widths[0]) if i == 0 else v.rjust(col_widths[i])
            for i, v in enumerate(row)
        ))

    print(separator)
