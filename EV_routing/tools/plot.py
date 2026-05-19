from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.figure
import matplotlib.gridspec as gridspec

from tools.experiment import ExperimentResults
from tools.tuning import TrialResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ALGO_COLORS = ["#2196F3", "#F44336", "#4CAF50", "#FF9800", "#9C27B0"]


def _algo_color(idx: int) -> str:
    return _ALGO_COLORS[idx % len(_ALGO_COLORS)]


def _save_and_show(fig: matplotlib.figure.Figure, save_path: Any, show: bool) -> None:
    if save_path is not None:
        p = Path(save_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(p, dpi=150, bbox_inches="tight")
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

    fig, ax = plt.subplots(figsize=(10, 5))

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
        (line,) = ax.plot(steps, mean, linewidth=1.5, label=exp.algorithm_name, color=color)
        ax.fill_between(steps, mean - std, mean + std, alpha=0.15, color=color)

    ax.set_xlabel("Step (temperature reduction / generation)")
    ax.set_ylabel("Best objective value")
    ax.set_title(title or "Convergence: " + " vs ".join(e.algorithm_name for e in results_list))
    ax.legend()
    ax.grid(True, alpha=0.3)
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

    fig, ax = plt.subplots(figsize=(10, 5))

    for idx, exp in enumerate(results_list):
        valid = [
            (s.evals_at_step, s.best_cost_history)
            for s in exp.all_stats
            if hasattr(s, "evals_at_step") and s.evals_at_step and s.best_cost_history
        ]
        if not valid:
            print(f"Warning: {exp.algorithm_name} has no evals_at_step — skipped.")
            continue

        # Interpolate all runs onto a common evaluation grid
        all_evals = [v[0] for v in valid]
        all_costs = [v[1] for v in valid]
        max_eval = max(e[-1] for e in all_evals)
        grid = np.linspace(0, max_eval, 500)

        interp_costs = []
        for evals, costs in zip(all_evals, all_costs):
            interp_costs.append(np.interp(grid, evals, costs))

        mat = np.array(interp_costs)
        mean = mat.mean(axis=0)
        std = mat.std(axis=0)

        color = _algo_color(idx)
        ax.plot(grid, mean, linewidth=1.5, label=exp.algorithm_name, color=color)
        ax.fill_between(grid, mean - std, mean + std, alpha=0.15, color=color)

    ax.set_xlabel("Objective evaluations")
    ax.set_ylabel("Best objective value")
    ax.set_title(title or "Convergence by evaluations: " + " vs ".join(e.algorithm_name for e in results_list))
    ax.legend()
    ax.grid(True, alpha=0.3)
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

    fig, ax = plt.subplots(figsize=(max(5, 2.5 * len(results_list)), 5))

    data_to_plot = [exp.best_costs for exp in results_list]
    labels = [exp.algorithm_name for exp in results_list]
    colors = [_algo_color(i) for i in range(len(results_list))]

    bp = ax.boxplot(
        data_to_plot,
        labels=labels,
        patch_artist=True,
        medianprops={"color": "black", "linewidth": 2},
        whiskerprops={"linewidth": 1.2},
        capprops={"linewidth": 1.2},
    )
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)

    # Overlay individual seed points
    for i, costs in enumerate(data_to_plot, start=1):
        jitter = np.random.default_rng(0).uniform(-0.1, 0.1, len(costs))
        ax.scatter(
            np.full(len(costs), i) + jitter,
            costs,
            color=colors[i - 1],
            s=30,
            zorder=3,
            alpha=0.8,
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
    Lower values indicate time spent waiting (I/O, GIL contention, etc.).
    """
    names  = [r.algorithm_name for r in results]
    wall_means = [r.average_runtime  for r in results]
    wall_stds  = [r.std_runtime      for r in results]
    cpu_means  = [r.average_cpu_time for r in results]
    cpu_stds   = [r.std_cpu_time     for r in results]
    efficiencies = [r.cpu_efficiency for r in results]

    x      = np.arange(len(names))
    width  = 0.35
    colors = [_algo_color(i) for i in range(len(results))]

    fig, (ax_time, ax_eff) = plt.subplots(1, 2, figsize=(13, 5))

    # ── Left panel: wall vs CPU time bars ────────────────────────────────
    for i, (wm, ws, cm, cs, color) in enumerate(
        zip(wall_means, wall_stds, cpu_means, cpu_stds, colors)
    ):
        ax_time.bar(x[i] - width / 2, wm, width, yerr=ws,
                    color=color, alpha=0.85, capsize=4, label=None)
        ax_time.bar(x[i] + width / 2, cm, width, yerr=cs,
                    color=color, alpha=0.40, capsize=4, hatch="//", label=None)

    # Legend proxies
    import matplotlib.patches as mpatches
    wall_patch = mpatches.Patch(facecolor="grey", alpha=0.85, label="Wall-clock time")
    cpu_patch  = mpatches.Patch(facecolor="grey", alpha=0.40, hatch="//", label="CPU time")
    ax_time.legend(handles=[wall_patch, cpu_patch])

    ax_time.set_xticks(x)
    ax_time.set_xticklabels(names, rotation=15, ha="right")
    ax_time.set_ylabel("Time (s)")
    ax_time.set_title("Mean runtime per seed ± std")
    ax_time.grid(True, axis="y", alpha=0.3)

    # ── Right panel: CPU efficiency ───────────────────────────────────────
    bars = ax_eff.bar(names, efficiencies,
                      color=colors, alpha=0.75, edgecolor="white")
    ax_eff.axhline(1.0, color="black", linewidth=0.8, linestyle="--",
                   label="Fully CPU-bound (1.0)")
    ax_eff.set_ylim(0, max(1.15, max(efficiencies) * 1.1))
    ax_eff.set_ylabel("CPU time / wall time")
    ax_eff.set_title("CPU efficiency")
    ax_eff.set_xticklabels(names, rotation=15, ha="right")
    ax_eff.legend(fontsize=9)
    ax_eff.grid(True, axis="y", alpha=0.3)

    for bar, v in zip(bars, efficiencies):
        ax_eff.text(bar.get_x() + bar.get_width() / 2, v + 0.01,
                    f"{v:.2f}", ha="center", va="bottom", fontsize=9)

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
    - Middle: Worsening-acceptance rate per temperature step (sliding window of 50)
              High early → exploration; low late → exploitation
    - Bottom: Best cost vs current cost (gap shows how far SA escapes local optima)
    """
    stats = results.all_stats[seed_idx]
    if not hasattr(stats, "temperature_history") or not stats.temperature_history:
        print(f"No SA diagnostics available for seed index {seed_idx}.")
        return plt.figure()

    steps = np.arange(1, len(stats.best_cost_history) + 1)
    temp = np.array(stats.temperature_history[: len(steps)])
    best = np.array(stats.best_cost_history)
    current = np.array(stats.current_cost_history[: len(steps)])

    # Approximate per-step worsening acceptance from totals (linear interpolation)
    # We use the current_cost minus best_cost gap as a proxy instead.
    gap = current - best

    fig, axes = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
    fig.suptitle(title or f"{results.algorithm_name} — run diagnostics (seed idx {seed_idx})")

    axes[0].plot(steps, temp, color=_algo_color(0), linewidth=1.2)
    axes[0].set_ylabel("Temperature")
    axes[0].set_yscale("log")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(steps, gap, color=_algo_color(2), linewidth=0.8, alpha=0.7)
    axes[1].set_ylabel("Current − Best cost\n(exploration gap)")
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(steps, best, color=_algo_color(0), linewidth=1.5, label="Best")
    axes[2].plot(steps, current, color=_algo_color(2), linewidth=0.8, alpha=0.6, label="Current")
    axes[2].set_ylabel("Objective value")
    axes[2].set_xlabel("Temperature step")
    axes[2].legend(fontsize=9)
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    _save_and_show(fig, save_path, show)
    return fig


# ---------------------------------------------------------------------------
# 5. GA diagnostics — explains GA's population dynamics
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
              Gap closing = selection pressure winning; gap re-opening = mutation diversity
    - Middle: Population diversity (coefficient of variation of costs)
              High CV = diverse population; near-zero = converged
    - Bottom: Fraction of the population that is feasible over time
    """
    stats = results.all_stats[seed_idx]
    if not hasattr(stats, "mean_cost_history") or not stats.mean_cost_history:
        print(f"No GA diagnostics available for seed index {seed_idx}.")
        return plt.figure()

    gens = np.arange(1, len(stats.best_cost_history) + 1)
    best = np.array(stats.best_cost_history)
    mean = np.array(stats.mean_cost_history[: len(gens)])
    div = np.array(stats.diversity_history[: len(gens)])
    feas = np.array(stats.feasibility_history[: len(gens)])

    fig, axes = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
    fig.suptitle(title or f"{results.algorithm_name} — run diagnostics (seed idx {seed_idx})")

    axes[0].plot(gens, mean, color=_algo_color(2), linewidth=1.0, alpha=0.7, label="Population mean")
    axes[0].plot(gens, best, color=_algo_color(1), linewidth=1.5, label="Best")
    axes[0].set_ylabel("Objective value")
    axes[0].legend(fontsize=9)
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(gens, div, color=_algo_color(3), linewidth=1.2)
    axes[1].set_ylabel("Diversity\n(cost coeff. of variation)")
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(gens, feas * 100, color=_algo_color(4), linewidth=1.2)
    axes[2].set_ylabel("Feasible population (%)")
    axes[2].set_xlabel("Generation")
    axes[2].set_ylim(0, 105)
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    _save_and_show(fig, save_path, show)
    return fig


# ---------------------------------------------------------------------------
# 6. Cost component breakdown — what drives the objective?
# ---------------------------------------------------------------------------

def plot_cost_breakdown(
    results: ExperimentResults | list[ExperimentResults],
    title: str | None = None,
    save_path: str | Path | None = None,
    show: bool = True,
) -> matplotlib.figure.Figure:
    """
    Stacked horizontal bar chart of the raw (unweighted) cost components for
    the best solution found by each algorithm.

    Shows what each algorithm is actually trading off: distance vs charging
    time vs energy vs cost, which links back to the weighted objective.
    """
    if isinstance(results, ExperimentResults):
        results_list = [results]
    else:
        results_list = list(results)

    component_labels = [
        "Distance (km)",
        "Travel time (h)",
        "Charging time (h)",
        "Energy (kWh)",
        "Charging cost ($)",
    ]
    component_colors = ["#2196F3", "#4CAF50", "#FF9800", "#F44336", "#9C27B0"]

    rows = []
    row_labels = []
    for exp in results_list:
        ev = exp.best_eval
        rows.append([
            ev.total_distance_km,
            ev.total_travel_time_h,
            ev.total_charging_time_h,
            ev.total_energy_consumed_kwh,
            ev.total_charging_cost_usd,
        ])
        row_labels.append(exp.algorithm_name)

    fig, ax = plt.subplots(figsize=(10, max(3, 1.2 * len(rows) + 1.5)))

    y_positions = np.arange(len(rows))
    bar_height = 0.5

    # Normalise each component to 0-100% of its own maximum for visualisation
    arr = np.array(rows, dtype=float)
    col_max = arr.max(axis=0)
    col_max[col_max == 0] = 1.0
    norm = arr / col_max * 100

    lefts = np.zeros(len(rows))
    for j, (label, color) in enumerate(zip(component_labels, component_colors)):
        ax.barh(
            y_positions,
            norm[:, j],
            left=lefts,
            height=bar_height,
            label=label,
            color=color,
            alpha=0.85,
        )
        lefts += norm[:, j]

    ax.set_yticks(y_positions)
    ax.set_yticklabels(row_labels)
    ax.set_xlabel("Relative component magnitude (% of column max)")
    ax.set_title(title or "Cost component breakdown (best solution per algorithm)")
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(True, axis="x", alpha=0.3)
    plt.tight_layout()
    _save_and_show(fig, save_path, show)
    return fig


# ---------------------------------------------------------------------------
# 7. ACO diagnostics — pheromone learning + exploration
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
              Gap closing = pheromone guiding ants toward good regions
    - Middle: Pheromone coefficient of variation over iterations
              Starts near-zero (uniform τ_max init); rises as pheromone
              concentrates on good arcs — shows the learning/convergence
              process unique to ACO
    - Bottom: Fraction of the ant colony that is feasible per iteration
    """
    stats = results.all_stats[seed_idx]
    if not hasattr(stats, "pheromone_cv_history") or not stats.pheromone_cv_history:
        print(f"No ACO diagnostics available for seed index {seed_idx}.")
        return plt.figure()

    iters = np.arange(1, len(stats.best_cost_history) + 1)
    best = np.array(stats.best_cost_history)
    mean = np.array(stats.mean_cost_history[: len(iters)])
    ph_cv = np.array(stats.pheromone_cv_history[: len(iters)])
    feas = np.array(stats.feasibility_history[: len(iters)])

    fig, axes = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
    fig.suptitle(title or f"{results.algorithm_name} — run diagnostics (seed idx {seed_idx})")

    axes[0].plot(iters, mean, color=_algo_color(2), linewidth=1.0, alpha=0.7, label="Iteration mean")
    axes[0].plot(iters, best, color=_algo_color(1), linewidth=1.5, label="Best so far")
    axes[0].set_ylabel("Objective value")
    axes[0].legend(fontsize=9)
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(iters, ph_cv, color=_algo_color(3), linewidth=1.2)
    axes[1].set_ylabel("Pheromone CV\n(std / mean of τ matrix)")
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(iters, feas * 100, color=_algo_color(4), linewidth=1.2)
    axes[2].set_ylabel("Feasible ants (%)")
    axes[2].set_xlabel("Iteration")
    axes[2].set_ylim(0, 105)
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    _save_and_show(fig, save_path, show)
    return fig


# ---------------------------------------------------------------------------
# 8. Tuning results — search landscape visualisation
# ---------------------------------------------------------------------------

def plot_tuning_results(
    results: list[TrialResult],
    algorithm_name: str = "",
    save_path: str | Path | None = None,
    show: bool = True,
) -> matplotlib.figure.Figure:
    """
    Two-panel tuning analysis figure.

    Top panel — Best-score progression over trials:
        Shows how the search improves over time.  A plateau means more
        trials are unlikely to help; a still-falling curve means the grid
        or random search could benefit from more trials.

    Bottom panels — Per-parameter sensitivity (one box per param):
        Each sub-panel groups all trial scores by the value of one parameter,
        revealing which parameters matter and which the algorithm is robust to.
        A flat set of boxes = that parameter has little effect.
        A steep gradient = worth tuning carefully.
    """
    if not results:
        return plt.figure()

    param_keys = [k for k in results[0] if k not in ("mean_cost", "seed_costs")]
    costs = np.array([r["mean_cost"] for r in results])
    n_trials = len(results)

    # Running best (cumulative minimum)
    running_best = np.minimum.accumulate(costs)

    n_params = len(param_keys)
    # Layout: 1 row for progression + rows of 3 for param sensitivity
    n_sens_rows = (n_params + 2) // 3
    total_rows = 1 + n_sens_rows
    fig = plt.figure(figsize=(14, 3.5 * total_rows))
    gs = gridspec.GridSpec(total_rows, 3, figure=fig, hspace=0.55, wspace=0.35)

    title = f"{algorithm_name} — tuning results ({n_trials} trials)" if algorithm_name else f"Tuning results ({n_trials} trials)"
    fig.suptitle(title, fontsize=12, y=1.0)

    # --- Top: score progression spanning all 3 columns ---
    ax_prog = fig.add_subplot(gs[0, :])
    ax_prog.scatter(range(1, n_trials + 1), costs, s=18, alpha=0.5,
                    color=_algo_color(0), zorder=2, label="Trial score")
    ax_prog.plot(range(1, n_trials + 1), running_best, color=_algo_color(1),
                 linewidth=2.0, label="Best so far")
    ax_prog.set_xlabel("Trial")
    ax_prog.set_ylabel("Mean objective value")
    ax_prog.set_title("Score progression")
    ax_prog.legend(fontsize=9)
    ax_prog.grid(True, alpha=0.3)

    # --- Bottom: per-parameter sensitivity ---
    for p_idx, key in enumerate(param_keys):
        row = 1 + p_idx // 3
        col = p_idx % 3
        ax = fig.add_subplot(gs[row, col])

        # Group costs by the unique values of this parameter
        unique_vals = sorted(set(r[key] for r in results))
        grouped = [[r["mean_cost"] for r in results if r[key] == v] for v in unique_vals]
        labels = [str(v) for v in unique_vals]

        bp = ax.boxplot(
            grouped,
            labels=labels,
            patch_artist=True,
            medianprops={"color": "black", "linewidth": 1.5},
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
        ax.grid(True, axis="y", alpha=0.3)

    plt.tight_layout()
    _save_and_show(fig, save_path, show)
    return fig


# ---------------------------------------------------------------------------
# 9. Summary table (console)
# ---------------------------------------------------------------------------

def print_comparison_table(results_list: list[ExperimentResults]) -> None:
    """
    Print a formatted results table across algorithms — ready to copy into a thesis.

    Columns: Algorithm | Best | Average | Worst | Std | Feasible | Avg Time
    """
    col_widths = [22, 10, 10, 10, 10, 10, 10]
    headers = ["Algorithm", "Best", "Average", "Worst", "Std Dev", "Feasible", "Avg Time"]

    header_line = "  ".join(h.ljust(w) if i == 0 else h.rjust(w) for i, (h, w) in enumerate(zip(headers, col_widths)))
    separator = "-" * len(header_line)

    print(separator)
    print(header_line)
    print(separator)

    for r in results_list:
        feasible_str = f"{r.feasible_run_count}/{len(r.seeds)}"
        time_str = f"{r.average_runtime:.1f}s"
        row = [
            r.algorithm_name,
            f"{r.best_cost:.2f}",
            f"{r.average_cost:.2f}",
            f"{r.worst_cost:.2f}",
            f"{r.std_cost:.2f}",
            feasible_str,
            time_str,
        ]
        print("  ".join(v.ljust(col_widths[0]) if i == 0 else v.rjust(col_widths[i]) for i, v in enumerate(row)))

    print(separator)
