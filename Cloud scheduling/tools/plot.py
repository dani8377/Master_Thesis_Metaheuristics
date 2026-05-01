"""
plot.py — Visualisation and CSV export utilities for the Cloud Scheduling experiments.

PURPOSE
-------
Provides all output-generation functions called after experiments complete:

1.  plot_convergence()
    Mean best-cost convergence ± 1 std-dev band per algorithm, plotted over
    iterations / generations.  Multiple algorithms are overlaid on the same
    axes for direct visual comparison.  Designed for SA, GA, and UMDA (all
    of which record best_cost_history with one entry per step / generation).

2.  plot_bar_comparison()
    Grouped horizontal bar chart showing Best / Average / Worst objective
    values for each algorithm side by side.  Easier to read than the table
    for a thesis figure, especially when there are many algorithms.

3.  print_comparison_table()
    Formatted plain-text comparison table with columns:
    Algorithm | Best | Average | Worst | Std Dev | Feasible | Avg Time.
    Designed to be copy-pasteable directly into a LaTeX tabular environment.

4.  save_results_csv()
    Writes per-run results (one row per seed × algorithm) to a CSV file for
    downstream analysis in Excel, Pandas, or R.  Also writes a separate
    per-algorithm aggregate summary CSV.

DESIGN NOTES
------------
- All functions are problem-agnostic: they only depend on ExperimentResults,
  which is algorithm-independent.  The same functions work for SA, GA, UMDA,
  and the one-shot baselines.
- Baselines with best_cost_history of length 1 are valid inputs but are
  deliberately excluded from the convergence plot (no meaningful convergence
  curve to draw for a one-shot constructor).
- The x-axis label is configurable (default "Iteration / Generation") because
  SA uses temperature steps, GA uses generations, and UMDA uses generations.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Union

from tools.experiment import ExperimentResults


# ---------------------------------------------------------------------------
# 1. Convergence plot
# ---------------------------------------------------------------------------

def plot_convergence(
    results: Union[ExperimentResults, list[ExperimentResults]],
    title: str  = "Cloud Scheduling — Convergence",
    xlabel: str = "Iteration / Generation",
    save_path: str | None = None,
    show: bool = True,
) -> None:
    """
    Plot mean best-cost convergence ± 1 std-dev band per algorithm.

    Only algorithms with best_cost_history longer than 1 element are plotted
    (one-shot baselines are automatically skipped since they produce a
    degenerate single-point curve that adds visual clutter without information).

    Parameters
    ----------
    results:
        A single ExperimentResults or a list — one entry per algorithm.
        Multiple entries are overlaid on the same axes for comparison.
    title:
        Figure title.
    xlabel:
        Label for the x-axis.  Use "Temperature step" for SA-only plots,
        "Generation" for GA/UMDA-only plots, or the default
        "Iteration / Generation" for mixed-algorithm comparison plots.
    save_path:
        If provided, the figure is saved as a PNG at this path.
    show:
        If True, plt.show() blocks until the window is closed.
        Set to False for headless or batch operation.
    """
    import numpy as np
    import matplotlib.pyplot as plt

    # Accept a single result or a list
    if isinstance(results, ExperimentResults):
        results = [results]

    # Filter out one-shot baselines (history length == 1 means no convergence)
    iterative = [r for r in results if any(len(s.best_cost_history) > 1
                                           for s in r.all_stats)]
    if not iterative:
        return  # nothing iterative to plot

    fig, ax = plt.subplots(figsize=(10, 5))

    for r in iterative:
        # Collect best-cost histories; skip empty histories
        histories = [s.best_cost_history for s in r.all_stats
                     if s.best_cost_history]
        if not histories:
            continue

        max_len = max(len(h) for h in histories)

        # Pad shorter runs to the same length by repeating their final value.
        # This allows a ragged matrix to become a rectangular numpy array.
        padded = []
        for h in histories:
            if h:
                padded.append(h + [h[-1]] * (max_len - len(h)))
            else:
                padded.append([float("nan")] * max_len)

        arr  = np.array(padded)         # shape (n_runs, max_len)
        mean = np.nanmean(arr, axis=0)  # mean best cost per step across seeds
        std  = np.nanstd(arr, axis=0)   # std dev across seeds per step
        xs   = np.arange(max_len)

        (line,) = ax.plot(xs, mean, label=r.algorithm_name, linewidth=1.5)
        # Shaded band shows run-to-run variability (±1σ)
        ax.fill_between(xs, mean - std, mean + std,
                        alpha=0.15, color=line.get_color())

    ax.set_xlabel(xlabel)
    ax.set_ylabel("Best objective value F(X)")
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")

    if show:
        plt.show()

    plt.close(fig)


# ---------------------------------------------------------------------------
# 2. Bar comparison chart
# ---------------------------------------------------------------------------

def plot_bar_comparison(
    results_list: list[ExperimentResults],
    title: str = "Algorithm Comparison — Cloud Scheduling",
    save_path: str | None = None,
    show: bool = True,
) -> None:
    """
    Grouped bar chart comparing Best, Average, and Worst objective values
    for each algorithm in results_list.

    The chart is drawn with algorithms on the y-axis (horizontal bars) so
    that long algorithm names do not get clipped.  Each algorithm gets three
    bars (Best / Average / Worst) shown in a different shade.

    Parameters
    ----------
    results_list:
        One ExperimentResults per algorithm (baselines included).
    title:
        Figure title.
    save_path:
        If provided, the figure is saved at this path.
    show:
        Whether to call plt.show() after drawing.
    """
    import numpy as np
    import matplotlib.pyplot as plt

    names   = [r.algorithm_name for r in results_list]
    bests   = [r.best_cost     for r in results_list]
    avgs    = [r.average_cost  for r in results_list]
    worsts  = [r.worst_cost    for r in results_list]

    n_algs  = len(names)
    y_pos   = np.arange(n_algs)
    height  = 0.25  # bar height fraction

    fig, ax = plt.subplots(figsize=(10, max(4, n_algs * 1.2)))

    # Draw three groups of bars offset vertically
    ax.barh(y_pos + height,  bests,  height, label="Best",    color="steelblue")
    ax.barh(y_pos,           avgs,   height, label="Average", color="darkorange")
    ax.barh(y_pos - height,  worsts, height, label="Worst",   color="salmon")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names)
    ax.set_xlabel("Objective value F(X)  (lower is better)")
    ax.set_title(title)
    ax.legend(loc="lower right")
    ax.grid(True, axis="x", alpha=0.3)
    plt.tight_layout()

    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")

    if show:
        plt.show()

    plt.close(fig)


# ---------------------------------------------------------------------------
# 3. Comparison table (plain-text / LaTeX-ready)
# ---------------------------------------------------------------------------

def print_comparison_table(results_list: list[ExperimentResults]) -> None:
    """
    Print a formatted comparison table for one or more experiment results.

    Columns:
        Algorithm  |  Best  |  Average  |  Worst  |  Std Dev  |  Feasible  |  Avg Time

    The alignment is designed so the output can be pasted directly into a
    LaTeX tabular environment with minimal editing.
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
# 4. CSV export
# ---------------------------------------------------------------------------

def save_results_csv(
    results_list: list[ExperimentResults],
    output_dir: str | Path,
) -> None:
    """
    Save experiment results to CSV files in output_dir.

    Two files are written:
    - results_per_seed.csv  — one row per (algorithm, seed) combination.
      Columns: algorithm, seed, best_cost, energy, latency, cpu_violation,
               mem_violation, n_active_servers, feasible, runtime_s
    - results_summary.csv   — one row per algorithm with aggregate statistics.
      Columns: algorithm, best, average, worst, std_dev, feasible_runs,
               n_runs, avg_runtime_s

    Parameters
    ----------
    results_list:
        List of ExperimentResults, one per algorithm.
    output_dir:
        Directory where the CSV files will be written.  Created if absent.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- Per-seed CSV ---
    per_seed_path = output_dir / "results_per_seed.csv"
    with open(per_seed_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "algorithm", "seed", "best_cost",
            "energy_W", "latency_ms", "cpu_violation", "mem_violation",
            "n_active_servers", "feasible", "runtime_s",
        ])
        for r in results_list:
            for idx, seed in enumerate(r.seeds):
                ev = r.best_evals[idx]
                writer.writerow([
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

    # --- Per-algorithm summary CSV ---
    summary_path = output_dir / "results_summary.csv"
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "algorithm", "best", "average", "worst", "std_dev",
            "feasible_runs", "n_runs", "avg_runtime_s",
        ])
        for r in results_list:
            writer.writerow([
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
