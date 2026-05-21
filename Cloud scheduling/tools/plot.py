"""
plot.py - Visualisation and CSV export utilities for the Cloud Scheduling experiments.

Functions:
  plot_convergence()         - Mean best-cost convergence +/- std band, budget-normalised x-axis.
  plot_bar_comparison()      - Best/Average/Worst bar chart for all algorithms.
  plot_metaheuristics_bar()  - Focused chart for SA/GA/UMDA with energy/latency breakdown.
  plot_box_comparison()      - Box plots of per-seed cost distributions.
  print_comparison_table()   - Plain-text comparison table.
  print_significance_table() - Pairwise Wilcoxon signed-rank p-value matrix.
  save_results_csv()         - Per-seed and summary CSV export.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Union

from tools.experiment import ExperimentResults

# ---------------------------------------------------------------------------
# Shared visual style
# ---------------------------------------------------------------------------

# Consistent colours per algorithm across all plots.  Any algorithm name that
# contains one of these keys (case-insensitive) gets the matching colour.
_ALGO_COLOURS: dict[str, str] = {
    "simulated annealing": "#2196F3",
    "sa":                  "#2196F3",
    "genetic algorithm":   "#FF9800",
    "ga":                  "#FF9800",
    "umda":                "#4CAF50",
    "greedy":              "#9C27B0",
    "round":               "#E91E63",
    "random":              "#795548",
    "b&b":                 "#607D8B",
    "branch":              "#607D8B",
}

_FIGURE_SIZE  = (10, 6)   # default figure size (width, height in inches)
_FIGURE_DPI   = 150       # consistent DPI for all saved figures
_GRID_ALPHA   = 0.3       # transparency for background grid lines


def _algo_colour(name: str, fallback_idx: int = 0) -> str:
    """Return a consistent colour for the given algorithm display name."""
    import matplotlib.pyplot as plt
    lower = name.lower()
    for key, colour in _ALGO_COLOURS.items():
        if key in lower:
            return colour
    # Fall back to the tab10 palette for unknown algorithms
    return plt.colormaps["tab10"](fallback_idx / 10)


def _apply_style() -> None:
    """Apply a consistent matplotlib style for all cloud scheduling plots."""
    import matplotlib.pyplot as plt
    try:
        plt.style.use("seaborn-v0_8-whitegrid")
    except OSError:
        try:
            plt.style.use("seaborn-whitegrid")
        except OSError:
            pass  # keep matplotlib defaults if seaborn styles are unavailable


# ---------------------------------------------------------------------------
# 1. Convergence plot (budget-normalised x-axis)
# ---------------------------------------------------------------------------

def plot_convergence(
    results: Union[ExperimentResults, list[ExperimentResults]],
    title: str  = "Cloud Scheduling — Convergence",
    xlabel: str | None = None,
    save_path: str | None = None,
    show: bool = True,
    baseline_scores: dict[str, float] | None = None,
) -> None:
    """
    Plot mean best-cost convergence ± 1 std-dev band per algorithm.

    X-axis: percentage of each algorithm's total search budget consumed
    (0% = start, 100% = end of run).  Normalising to budget percentage makes
    SA (3000 steps), GA (3000 generations) and UMDA (1500 generations) lie on
    the same horizontal scale, so the convergence *shapes* can be compared
    directly: a curve that drops steeply at 10% converges faster than one
    that drops at 40%, regardless of the algorithms' raw step counts.

    Only algorithms with best_cost_history longer than 1 element are plotted
    (one-shot baselines produce a single-point curve with no information).

    Parameters
    ----------
    results:
        A single ExperimentResults or a list — one entry per algorithm.
    title:
        Figure title.
    xlabel:
        Override the x-axis label.  Default: "Search budget consumed (%)".
    save_path:
        If provided, the figure is saved as a PNG at this path.
    show:
        If True, plt.show() blocks until the window is closed.
    baseline_scores:
        Optional dict mapping baseline name → best_cost.  When provided, a
        dashed horizontal reference line is drawn for each baseline so the
        reader can instantly see how much better the metaheuristics are.
        Example: {"Greedy BFD": 1.42, "Round-Robin": 3.71}
    """
    import numpy as np
    import matplotlib.pyplot as plt

    _apply_style()

    if isinstance(results, ExperimentResults):
        results = [results]

    iterative = [r for r in results if any(len(s.best_cost_history) > 1
                                           for s in r.all_stats)]
    if not iterative:
        return

    fig, ax = plt.subplots(figsize=_FIGURE_SIZE)

    for idx, r in enumerate(iterative):
        histories = [s.best_cost_history for s in r.all_stats
                     if s.best_cost_history]
        if not histories:
            continue

        max_len = max(len(h) for h in histories)

        # Pad shorter runs by repeating their final value
        padded = []
        for h in histories:
            padded.append(h + [h[-1]] * (max_len - len(h)) if h
                          else [float("nan")] * max_len)

        arr  = np.array(padded)
        mean = np.nanmean(arr, axis=0)
        std  = np.nanstd(arr, axis=0)

        # Normalise x to [0, 100] — percentage of this algorithm's budget
        xs = np.linspace(0, 100, max_len)

        colour = _algo_colour(r.algorithm_name, idx)
        ax.plot(xs, mean, label=r.algorithm_name, linewidth=2.0, color=colour)
        ax.fill_between(xs, mean - std, mean + std,
                        alpha=0.15, color=colour)

    # Optional horizontal reference lines for baseline scores
    if baseline_scores:
        baseline_colours = ["#9C27B0", "#E91E63", "#795548", "#607D8B"]
        for i, (name, score) in enumerate(baseline_scores.items()):
            colour = baseline_colours[i % len(baseline_colours)]
            ax.axhline(
                score, linestyle="--", linewidth=1.2, color=colour, alpha=0.7,
                label=f"{name} ({score:.3f})",
            )

    # Zoom y-axis to the range actually traced by the convergence curves so that
    # differences between algorithms are visible.  We use the final 20% of each
    # curve (the plateau region) as the lower bound and the first 10% as the
    # upper bound, then add a 20% margin so the lines are not flush with the edges.
    import numpy as np
    all_vals: list[float] = []
    for r in iterative:
        for s in r.all_stats:
            if s.best_cost_history:
                all_vals.extend(s.best_cost_history)
    if all_vals:
        y_lo = min(all_vals)
        y_hi = max(all_vals)
        margin = max((y_hi - y_lo) * 0.20, 1e-4)
        ax.set_ylim(y_lo - margin * 0.5, y_hi + margin * 1.5)

    ax.set_xlabel(xlabel or "Search budget consumed (%)", fontsize=11)
    ax.set_ylabel("Best objective value F(X)  (lower is better)", fontsize=11)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=_GRID_ALPHA)

    # Footnote explaining the normalisation.  We compute the actual budget
    # from the stats objects we have, so the footnote stays accurate even if
    # the user changes max_temp_steps / n_generations in config.yaml.
    budget_lines: list[str] = []
    for r in iterative:
        # Prefer SA's total_budget_consumed (= main loop + T_0 probe) so the
        # convergence plot's budget footnote matches the diagnostics CSV.
        evals = [(getattr(s, "total_budget_consumed", None)
                  or getattr(s, "total_evaluated", None)
                  or getattr(s, "total_evaluations", None))
                 for s in r.all_stats]
        evals = [e for e in evals if e is not None]
        if evals:
            budget_lines.append(f"{r.algorithm_name}: ~{int(sum(evals) / len(evals)):,} evals/run")
    if budget_lines:
        fig.text(
            0.5, -0.02,
            "Note: x-axis shows % of each algorithm's total evaluation budget consumed.  "
            + "  ".join(budget_lines),
            ha="center", va="top", fontsize=7, color="gray", wrap=True,
        )

    plt.tight_layout()

    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=_FIGURE_DPI, bbox_inches="tight")

    if show:
        plt.show()

    plt.close(fig)


# ---------------------------------------------------------------------------
# 2. Full bar comparison chart (all algorithms)
# ---------------------------------------------------------------------------

def plot_bar_comparison(
    results_list: list[ExperimentResults],
    title: str = "Algorithm Comparison — Cloud Scheduling",
    save_path: str | None = None,
    show: bool = True,
) -> None:
    """
    Grouped horizontal bar chart comparing Best, Average, and Worst objective
    values for every algorithm in results_list (including baselines).

    Because baselines often produce much worse scores than metaheuristics,
    this chart's y-axis spans a wide range.  Use plot_metaheuristics_bar()
    for a zoomed view of SA / GA / UMDA differences.
    """
    import numpy as np
    import matplotlib.pyplot as plt

    _apply_style()

    names   = [r.algorithm_name for r in results_list]
    bests   = [r.best_cost     for r in results_list]
    avgs    = [r.average_cost  for r in results_list]
    worsts  = [r.worst_cost    for r in results_list]

    n_algs  = len(names)
    y_pos   = np.arange(n_algs)
    height  = 0.25

    fig, ax = plt.subplots(figsize=(max(10, 6), max(5, n_algs * 1.3)))

    bars_best  = ax.barh(y_pos + height, bests,  height, label="Best",    color="#2196F3", alpha=0.85)
    bars_avg   = ax.barh(y_pos,          avgs,   height, label="Average", color="#FF9800", alpha=0.85)
    bars_worst = ax.barh(y_pos - height, worsts, height, label="Worst",   color="#F44336", alpha=0.85)

    # Annotate each bar with its value
    x_max = max(worsts) if worsts else 1.0
    label_offset = x_max * 0.005
    for bar in bars_best:
        w = bar.get_width()
        ax.text(w + label_offset, bar.get_y() + bar.get_height() / 2,
                f"{w:.3f}", va="center", ha="left", fontsize=7, color="#1565C0")
    for bar in bars_avg:
        w = bar.get_width()
        ax.text(w + label_offset, bar.get_y() + bar.get_height() / 2,
                f"{w:.3f}", va="center", ha="left", fontsize=7, color="#E65100")
    for bar in bars_worst:
        w = bar.get_width()
        ax.text(w + label_offset, bar.get_y() + bar.get_height() / 2,
                f"{w:.3f}", va="center", ha="left", fontsize=7, color="#B71C1C")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=10)
    ax.set_xlabel("Objective value F(X)  (lower is better)", fontsize=11)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(True, axis="x", alpha=_GRID_ALPHA)
    # Give the value labels a little extra room on the right
    ax.set_xlim(right=x_max * 1.12)
    plt.tight_layout()

    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=_FIGURE_DPI, bbox_inches="tight")

    if show:
        plt.show()

    plt.close(fig)


# ---------------------------------------------------------------------------
# 3. Focused metaheuristics comparison (SA / GA / UMDA only)
# ---------------------------------------------------------------------------

def plot_metaheuristics_bar(
    results_list: list[ExperimentResults],
    weights=None,
    title: str = "Metaheuristic Comparison — Cloud Scheduling",
    save_path: str | None = None,
    show: bool = True,
) -> None:
    """
    Focused comparison chart for the iterative metaheuristics (SA, GA, UMDA).

    Top panel — Objective value distribution:
        Vertical grouped bars for Best / Average / Worst per algorithm.
        Y-axis is *zoomed to their range*, not starting from 0, so small
        differences between algorithms are clearly visible.
        Individual seed dots are overlaid so run-to-run variance can be
        judged at a glance.

    Bottom panel — Energy vs latency decomposition of F(X):
        Stacked bars showing the weighted energy and weighted latency
        contributions of each algorithm's best run.
        w_energy × E(X) vs w_latency × L(X) makes explicit how much of the
        objective score comes from each term (excluding capacity penalties).

    Parameters
    ----------
    results_list:
        All experiment results; one-shot baselines are filtered out
        automatically (they have best_cost_history of length 1).
    weights:
        ObjectiveWeights used in the run — needed for the breakdown panel.
        If None, the breakdown panel is omitted.
    title:
        Main figure title.
    save_path / show:
        Standard output controls.
    """
    import numpy as np
    import matplotlib.pyplot as plt

    _apply_style()

    # Only keep iterative algorithms
    iterative = [r for r in results_list
                 if any(len(s.best_cost_history) > 1 for s in r.all_stats)]
    if not iterative:
        iterative = results_list

    n_algs = len(iterative)
    x_pos  = np.arange(n_algs)
    names  = [r.algorithm_name for r in iterative]
    bests  = [r.best_cost      for r in iterative]
    avgs   = [r.average_cost   for r in iterative]
    worsts = [r.worst_cost     for r in iterative]
    stds   = [r.std_cost       for r in iterative]

    n_rows = 2 if weights is not None else 1
    fig, axes = plt.subplots(n_rows, 1, figsize=(max(6, n_algs * 2.8),
                                                  4 * n_rows + 1))
    if n_rows == 1:
        axes = [axes]

    # ---- Top panel: objective value distribution ---- #
    ax = axes[0]
    width = 0.22

    ax.bar(x_pos - width, bests,  width, label="Best",    color="#2196F3",  alpha=0.85)
    ax.bar(x_pos,         avgs,   width, label="Average", color="#FF9800", alpha=0.85,
           yerr=stds, capsize=5, error_kw={"linewidth": 1.5, "ecolor": "black"})
    ax.bar(x_pos + width, worsts, width, label="Worst",   color="#F44336",     alpha=0.85)

    # Individual seed scatter dots — shows variance beyond std-dev bars
    rng = np.random.default_rng(0)
    for idx, r in enumerate(iterative):
        jitter = rng.uniform(-0.08, 0.08, len(r.best_costs))
        ax.scatter(idx + jitter, r.best_costs,
                   color="navy", alpha=0.45, s=22, zorder=5, label="_nolegend_")

    # Zoom y-axis to the data range with a 10% margin
    all_vals = [v for r in iterative for v in r.best_costs]
    y_min = min(all_vals)
    y_max = max(worsts)
    margin = max(1.0, (y_max - y_min) * 0.12)
    ax.set_ylim(y_min - margin, y_max + margin)

    ax.set_xticks(x_pos)
    ax.set_xticklabels(names, fontsize=10)
    ax.set_ylabel("Best objective value F(X)  (lower is better)", fontsize=11)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(True, axis="y", alpha=_GRID_ALPHA)

    # ---- Bottom panel: energy vs latency breakdown ---- #
    if weights is not None:
        ax2 = axes[1]

        # F(X) decomposition requires the NORMALISED contributions:
        #   F_energy_term  = w_e * E(X) / E_ref       (dimensionless)
        #   F_latency_term = w_l * L(X) / L_ref       (dimensionless)
        # Plotting raw w_e*E (in Watts) stacked on top of w_l*L (in ms) is
        # meaningless because the units differ.  Divide by the calibration
        # references so the stacked bars actually sum to (w_e*E/E_ref +
        # w_l*L/L_ref), which IS the feasible part of F(X).
        e_ref = weights.energy_ref  or 1.0
        l_ref = weights.latency_ref or 1.0

        e_contribs = [weights.energy_weight  * r.best_eval.total_energy  / e_ref
                      for r in iterative]
        l_contribs = [weights.latency_weight * r.best_eval.total_latency / l_ref
                      for r in iterative]

        ax2.bar(x_pos, e_contribs, 0.45,
                label=f"w_e · E(X) / E_ref   (E_ref = {e_ref:.1f} W)",
                color="#2196F3",  alpha=0.85)
        ax2.bar(x_pos, l_contribs, 0.45, bottom=e_contribs,
                label=f"w_l · L(X) / L_ref   (L_ref = {l_ref:.1f} ms)",
                color="#FF9800", alpha=0.85)

        # Annotate each bar with (a) the dimensionless contribution and
        # (b) the raw energy / latency for context.
        for idx, r in enumerate(iterative):
            ev    = r.best_eval
            e_pct = e_contribs[idx] / max(1e-9, e_contribs[idx] + l_contribs[idx]) * 100
            l_pct = 100.0 - e_pct
            ax2.text(idx, e_contribs[idx] / 2,
                     f"{e_contribs[idx]:.3f}\n({e_pct:.0f}%)\n{ev.total_energy:.0f} W",
                     ha="center", va="center",
                     fontsize=7, color="white", fontweight="bold")
            ax2.text(idx, e_contribs[idx] + l_contribs[idx] / 2,
                     f"{l_contribs[idx]:.3f}\n({l_pct:.0f}%)\n{ev.total_latency:.0f} ms",
                     ha="center", va="center",
                     fontsize=7, color="white", fontweight="bold")

        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(names, fontsize=10)
        ax2.set_ylabel("Contribution to F(X)  (dimensionless)", fontsize=11)
        ax2.set_title("F(X) decomposition — normalised energy and latency terms  (best run)",
                      fontsize=12, fontweight="bold")
        ax2.legend(loc="upper right", fontsize=8)
        ax2.grid(True, axis="y", alpha=_GRID_ALPHA)

    plt.tight_layout()

    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=_FIGURE_DPI, bbox_inches="tight")

    if show:
        plt.show()

    plt.close(fig)


# ---------------------------------------------------------------------------
# 4. Box plots — per-seed cost distribution
# ---------------------------------------------------------------------------

def plot_box_comparison(
    results_list: list[ExperimentResults],
    title: str = "Algorithm Comparison - Result Distribution",
    save_path: str | None = None,
    show: bool = True,
) -> None:
    """
    Box plots of per-seed objective value distributions, one box per algorithm.

    Individual seed results are overlaid as jittered scatter points so the
    reader can see the raw spread beyond what the quartiles convey.  Algorithms
    with only one seed (e.g. B&B) are included as a single dot.
    """
    import numpy as np
    import matplotlib.pyplot as plt

    _apply_style()

    if not results_list:
        return

    names = [r.algorithm_name for r in results_list]
    data  = [r.best_costs     for r in results_list]

    n_algs = len(results_list)
    colors = [_algo_colour(r.algorithm_name, i) for i, r in enumerate(results_list)]

    fig, ax = plt.subplots(figsize=(max(8, n_algs * 2.0), 6))

    bp = ax.boxplot(
        data, labels=names, patch_artist=True,
        medianprops=dict(color="black", linewidth=2),
        # hide flier markers — we draw our own scatter points instead
        flierprops=dict(marker="", markersize=0),
        widths=0.5,
    )
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.45)

    # Individual seed dots (jittered horizontally for readability)
    rng = np.random.default_rng(42)
    for i, (r, color) in enumerate(zip(results_list, colors)):
        x_base = i + 1
        jitter = rng.uniform(-0.15, 0.15, len(r.best_costs))
        ax.scatter(
            x_base + jitter, r.best_costs,
            color=color, edgecolors="black", linewidths=0.6,
            s=45, zorder=5, alpha=0.9,
        )

    ax.set_ylabel("Best objective value F(X)  (lower is better)", fontsize=11)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.grid(True, axis="y", alpha=_GRID_ALPHA)
    plt.xticks(rotation=20, ha="right", fontsize=9)
    plt.tight_layout()

    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=_FIGURE_DPI, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)


# ---------------------------------------------------------------------------
# 5. Significance table — pairwise Wilcoxon signed-rank tests
# ---------------------------------------------------------------------------

def print_significance_table(results_list: list[ExperimentResults]) -> None:
    """
    Print a pairwise Wilcoxon signed-rank test p-value matrix.

    Each cell (row A, col B) reports whether the per-seed costs of algorithm A
    are significantly different from those of algorithm B.  Uses the two-sided
    Wilcoxon signed-rank test (non-parametric, no normality assumption).

    Significance stars: *** p<0.001  ** p<0.01  * p<0.05  ns = not significant.

    Algorithms with only one seed are excluded (test needs paired observations).
    Low seed counts (< 10) reduce statistical power — the note is printed as a
    warning so the reader is not over-confident in high p-values.
    """
    try:
        from scipy.stats import wilcoxon
    except ImportError:
        print("  [!] scipy not installed - skipping significance tests.")
        return

    testable = [r for r in results_list if len(r.best_costs) >= 2]
    if len(testable) < 2:
        print("  (need >= 2 algorithms with >= 2 seeds for significance testing)")
        return

    min_seeds = min(len(r.best_costs) for r in testable)
    if min_seeds < 10:
        print(f"  [!] Only {min_seeds} seeds - Wilcoxon power is low; use >=10 for reliable p-values.")

    names   = [r.algorithm_name for r in testable]
    col_w   = max(len(n) for n in names)
    cell_w  = 13

    print("\n  Pairwise Wilcoxon signed-rank test  (two-sided, per-seed costs)")
    print("  *** p<0.001   ** p<0.01   * p<0.05   ns = not significant")
    print()

    # Header
    header = f"  {'':{col_w}}"
    for name in names:
        header += f"  {name[:cell_w]:>{cell_w}}"
    print(header)
    print("  " + "-" * (col_w + (cell_w + 2) * len(names)))

    for r_a in testable:
        row = f"  {r_a.algorithm_name:{col_w}}"
        for r_b in testable:
            if r_a is r_b:
                cell = "---"
            else:
                n     = min(len(r_a.best_costs), len(r_b.best_costs))
                a_val = r_a.best_costs[:n]
                b_val = r_b.best_costs[:n]
                if a_val == b_val:
                    cell = "identical"
                else:
                    try:
                        _, p = wilcoxon(a_val, b_val)
                        stars = (
                            "***" if p < 0.001 else
                            "**"  if p < 0.01  else
                            "*"   if p < 0.05  else
                            "ns"
                        )
                        cell = f"{p:.3f} {stars}"
                    except Exception:
                        cell = "n/a"
            row += f"  {cell:>{cell_w}}"
        print(row)
    print()


# ---------------------------------------------------------------------------
# 6. Comparison table (plain-text / LaTeX-ready)
# ---------------------------------------------------------------------------

def print_comparison_table(results_list: list[ExperimentResults]) -> None:
    """
    Print a formatted comparison table for one or more experiment results.

    Columns:
        Algorithm  |  Best  |  Average  |  Worst  |  Std Dev  |  Feasible  |  Avg Time
    """
    header = (
        f"{'Algorithm':<32} {'Best':>12} {'Average':>12} {'Worst':>12}"
        f" {'Std Dev':>10} {'Feasible':>10} {'Avg Time':>10}"
    )
    separator = "-" * len(header)
    print(header)
    print(separator)
    for r in results_list:
        print(
            f"{r.algorithm_name:<32}"
            f" {r.best_cost:>12.2f}"
            f" {r.average_cost:>12.2f}"
            f" {r.worst_cost:>12.2f}"
            f" {r.std_cost:>10.2f}"
            f" {r.feasible_run_count:>7}/{len(r.seeds)}"
            f" {r.average_runtime:>9.2f}s"
        )


# ---------------------------------------------------------------------------
# 7. CSV export
# ---------------------------------------------------------------------------

def _safe_open(path: Path, **kwargs):
    """
    Open a file for writing, falling back to a timestamped name if the
    original is locked (e.g. open in VS Code / Excel on Windows).
    """
    import datetime
    try:
        return open(path, **kwargs)
    except PermissionError:
        stamp = datetime.datetime.now().strftime("%H%M%S")
        fallback = path.with_stem(path.stem + f"_{stamp}")
        print(f"  [!] {path.name} is locked — writing to {fallback.name} instead")
        return open(fallback, **kwargs)


def save_results_csv(
    results_list: list[ExperimentResults],
    output_dir: str | Path,
    focus_mode: str | None = None,
    n_tasks: int | None = None,
    n_servers: int | None = None,
) -> None:
    """
    Save experiment results to CSV files in output_dir.

    Two files are written:
    - results_per_seed.csv  — one row per (algorithm, seed) combination.
    - results_summary.csv   — one row per algorithm with aggregate statistics.

    When focus_mode / n_tasks / n_servers are supplied, they are written as
    extra columns on every row so that CSVs from different runs (e.g. one
    per focus mode, or one per scalability scale point) can be concatenated
    and analysed jointly without losing context.

    If either file is locked (open in VS Code / Excel), the output is written
    to a timestamped fallback name so the run never crashes.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Context columns prepended to every row.  Kept order-stable so that
    # downstream pandas reads always see the same schema.
    context_cols: list[tuple[str, object]] = []
    if focus_mode is not None:
        context_cols.append(("focus_mode", focus_mode))
    if n_tasks is not None:
        context_cols.append(("n_tasks", n_tasks))
    if n_servers is not None:
        context_cols.append(("n_servers", n_servers))
    context_names  = [c[0] for c in context_cols]
    context_values = [c[1] for c in context_cols]

    per_seed_path = output_dir / "results_per_seed.csv"
    with _safe_open(per_seed_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(context_names + [
            "algorithm", "seed", "best_cost",
            "energy_W", "latency_ms", "cpu_violation", "mem_violation",
            "n_active_servers", "feasible", "runtime_s",
        ])
        for r in results_list:
            for idx, seed in enumerate(r.seeds):
                ev = r.best_evals[idx]
                writer.writerow(context_values + [
                    r.algorithm_name,
                    seed,
                    f"{ev.objective_value:.4f}",
                    f"{ev.total_energy:.4f}",
                    f"{ev.total_latency:.4f}",
                    f"{ev.cpu_violation:.4f}",
                    f"{ev.mem_violation:.4f}",
                    ev.n_active_servers,
                    ev.feasible,
                    f"{r.runtimes[idx]:.4f}",
                ])

    summary_path = output_dir / "results_summary.csv"
    with _safe_open(summary_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(context_names + [
            "algorithm", "best", "average", "worst", "std_dev",
            "feasible_runs", "n_runs", "avg_runtime_s",
        ])
        for r in results_list:
            writer.writerow(context_values + [
                r.algorithm_name,
                f"{r.best_cost:.4f}",
                f"{r.average_cost:.4f}",
                f"{r.worst_cost:.4f}",
                f"{r.std_cost:.4f}",
                r.feasible_run_count,
                len(r.seeds),
                f"{r.average_runtime:.4f}",
            ])

    print(f"  Results saved: {per_seed_path.name}  &  {summary_path.name}"
          f"  (in {output_dir})")


# ---------------------------------------------------------------------------
# 8. Scalability plots (three axes)
# ---------------------------------------------------------------------------

def plot_horizontal_scaling(scale_data: dict, figures_dir) -> None:
    """
    Two-panel figure for Axis 1 (horizontal) scalability.

    Left panel  — average runtime vs number of tasks (log x-axis).
    Right panel — % improvement over Greedy BFD vs number of tasks.
    """
    import matplotlib.pyplot as plt

    _apply_style()

    if not scale_data:
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for idx, (name, d) in enumerate(scale_data.items()):
        color = _algo_colour(name, idx)
        axes[0].plot(d["sizes"], d["runtimes"],     marker="o", label=name,
                     color=color, linewidth=2.0)
        axes[1].plot(d["sizes"], d["improvements"], marker="o", label=name,
                     color=color, linewidth=2.0)

    for ax in axes:
        ax.set_xscale("log")
        ax.grid(True, alpha=_GRID_ALPHA)
        ax.legend(fontsize=9)

    axes[0].set_xlabel("Number of tasks  (log scale)", fontsize=11)
    axes[0].set_ylabel("Average runtime per run (s)", fontsize=11)
    axes[0].set_title("Runtime Scaling", fontsize=12, fontweight="bold")

    axes[1].set_xlabel("Number of tasks  (log scale)", fontsize=11)
    axes[1].set_ylabel("Improvement over Greedy BFD (%)", fontsize=11)
    axes[1].set_title("Solution Quality vs. Problem Size", fontsize=12, fontweight="bold")
    axes[1].axhline(0, color="gray", linewidth=0.8, linestyle="--")

    plt.suptitle(
        "Horizontal Scalability — Synthetic tasks, proportional server pool (5:1 ratio)",
        fontsize=12, fontweight="bold",
    )
    plt.tight_layout()

    save_path = str(Path(figures_dir) / "scalability_horizontal.png")
    fig.savefig(save_path, dpi=_FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Horizontal scalability plot  -> {save_path}")


def plot_vertical_scaling(vert_data: dict, figures_dir) -> None:
    """
    Two-panel figure for Axis 2 (vertical / constraint tightness) scalability.

    Left panel  — % improvement over Greedy BFD vs server count.
    Right panel — % of runs that ended feasible vs server count.
    X-axis is inverted so the plot reads left=loose, right=tight.
    """
    import matplotlib.pyplot as plt

    _apply_style()

    if not vert_data:
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for idx, (name, d) in enumerate(vert_data.items()):
        color = _algo_colour(name, idx)
        axes[0].plot(d["servers"], d["improvements"],  marker="o", label=name,
                     color=color, linewidth=2.0)
        axes[1].plot(d["servers"], d["feasible_pct"],  marker="s", label=name,
                     color=color, linewidth=2.0)

    for ax in axes:
        ax.invert_xaxis()   # fewer servers = harder, so right side is tightest
        ax.grid(True, alpha=_GRID_ALPHA)
        ax.legend(fontsize=9)

    axes[0].set_xlabel("Number of servers  (← more constrained)", fontsize=11)
    axes[0].set_ylabel("Improvement over Greedy BFD (%)", fontsize=11)
    axes[0].set_title("Solution Quality vs. Constraint Tightness",
                      fontsize=12, fontweight="bold")
    axes[0].axhline(0, color="gray", linewidth=0.8, linestyle="--")

    axes[1].set_xlabel("Number of servers  (← more constrained)", fontsize=11)
    axes[1].set_ylabel("Feasible solutions (%)", fontsize=11)
    axes[1].set_title("Feasibility Rate vs. Constraint Tightness",
                      fontsize=12, fontweight="bold")
    axes[1].set_ylim(-5, 110)

    plt.suptitle(
        "Vertical Scalability — 50 real tasks, server count varied from loose to tight",
        fontsize=12, fontweight="bold",
    )
    plt.tight_layout()

    save_path = str(Path(figures_dir) / "scalability_vertical.png")
    fig.savefig(save_path, dpi=_FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Vertical scalability plot    -> {save_path}")


def plot_optimality_gap_comparison(
    all_results: list,
    bb_cost: float,
    figures_dir,
    n_tasks: int | None = None,
    n_servers: int | None = None,
) -> None:
    """
    Bar chart comparing every algorithm (SA, GA, UMDA, Greedy, B&B) on the
    small exact-solvable instance.  The B&B optimal/best cost is drawn as a
    dashed reference line; gap annotations show how far each metaheuristic
    is from the exact solution.

    Parameters
    ----------
    n_tasks / n_servers:
        Problem size to put in the title.  Passed in by the caller because
        the ExperimentResults objects do not carry the instance size directly.
    """
    import numpy as np
    import matplotlib.pyplot as plt

    _apply_style()

    if not all_results:
        return

    names  = [r.algorithm_name for r in all_results]
    bests  = [r.best_cost      for r in all_results]
    avgs   = [r.average_cost   for r in all_results]
    colors = [_algo_colour(r.algorithm_name, i) for i, r in enumerate(all_results)]

    n  = len(all_results)
    x  = np.arange(n)
    w  = 0.35

    fig, ax = plt.subplots(figsize=(max(8, n * 2.2), 6))

    ax.bar(x - w / 2, bests, w, label="Best cost",    color=colors, alpha=0.88)
    ax.bar(x + w / 2, avgs,  w, label="Average cost", color=colors, alpha=0.45,
           edgecolor="black", linewidth=0.8)

    ax.axhline(bb_cost, color=_ALGO_COLOURS["b&b"], linewidth=2.0, linestyle="--",
               label=f"B&B reference  ({bb_cost:.4f})")

    # Gap annotations above each best-cost bar
    for i, best in enumerate(bests):
        gap = (best - bb_cost) / max(1e-10, abs(bb_cost)) * 100
        if gap > 0.05:
            ax.text(i - w / 2, best + (max(bests) - min(bests)) * 0.02,
                    f"+{gap:.1f}%", ha="center", fontsize=8, color="black")

    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=15, ha="right", fontsize=9)
    ax.set_ylabel("Objective value F(X)  (lower is better)", fontsize=11)
    # Title subline: use the actual problem size (passed in by the caller).
    # NOTE: an earlier version of this function pulled `seeds[0]` here — that
    # is a SEED VALUE (e.g. 0), not a task count, so the title was wrong.
    size_str = f"{n_tasks} tasks x {n_servers} servers" if n_tasks is not None else "small instance"
    ax.set_title(
        "Optimality Gap — metaheuristics vs. B&B exact reference\n"
        f"({size_str} — small enough for B&B to find optimal or near-optimal)",
        fontsize=11, fontweight="bold",
    )
    ax.legend(fontsize=9)
    ax.grid(True, axis="y", alpha=_GRID_ALPHA)

    plt.tight_layout()

    save_path = str(Path(figures_dir) / "optimality_gap.png")
    fig.savefig(save_path, dpi=_FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Optimality-gap plot          -> {save_path}")


