"""
plot.py — Visualisation utilities for the Cloud Scheduling experiments.

PURPOSE
-------
Provides two output functions used after an experiment completes:

1.  plot_convergence()
    Draws the SA convergence curve: best objective value per temperature step,
    averaged across all seeds with a ±1 std-dev shaded band.  Multiple
    algorithms can be overlaid on the same axes for direct comparison.

2.  print_comparison_table()
    Prints a formatted plain-text table summarising Best / Average / Worst /
    Std Dev / Feasible runs / Average runtime for one or more algorithms.
    The format is designed to be copy-pasteable into a LaTeX tabular.

DESIGN NOTE
-----------
Both functions are fully problem-agnostic: they only depend on ExperimentResults
and SAStatistics (which has a best_cost_history attribute).  The same functions
can therefore be reused for any scheduling algorithm without modification.
"""
from __future__ import annotations

from typing import Union

from tools.experiment import ExperimentResults


def print_comparison_table(results_list: list[ExperimentResults]) -> None:
    """
    Print a summary comparison table for one or more experiment results.

    Columns: Algorithm | Best | Average | Worst | Std Dev | Feasible | Avg Time
    """
    header = (
        f"{'Algorithm':<30} {'Best':>12} {'Average':>12} {'Worst':>12}"
        f" {'Std Dev':>10} {'Feasible':>10} {'Avg Time':>10}"
    )
    print(header)
    print("-" * len(header))
    for r in results_list:
        print(
            f"{r.algorithm_name:<30}"
            f" {r.best_cost:>12.2f}"
            f" {r.average_cost:>12.2f}"
            f" {r.worst_cost:>12.2f}"
            f" {r.std_cost:>10.2f}"
            f" {r.feasible_run_count:>8}/{len(r.seeds)}"   # e.g. "10/10"
            f" {r.average_runtime:>9.1f}s"
        )


def plot_convergence(
    results: Union[ExperimentResults, list[ExperimentResults]],
    title: str = "Simulated Annealing — Convergence",
    save_path: str | None = None,
    show: bool = True,
) -> None:
    """
    Plot mean best-cost convergence ± 1 std-dev band per algorithm.

    Parameters
    ----------
    results:
        A single ExperimentResults or a list — one entry per algorithm.
        Multiple entries are overlaid on the same axes for comparison.
    title:
        Plot title shown above the axes.
    save_path:
        If given, the figure is saved as a PNG at this path.
    show:
        If True, plt.show() is called (blocks until the window is closed).
        Set to False when running headless or in batch mode.
    """
    import numpy as np
    import matplotlib.pyplot as plt

    # Accept a single result or a list
    if isinstance(results, ExperimentResults):
        results = [results]

    fig, ax = plt.subplots(figsize=(10, 5))

    for r in results:
        # Collect per-run best-cost histories from SAStatistics objects
        max_len = max(len(s.best_cost_history) for s in r.all_stats)

        # Pad shorter runs to the longest by repeating their final value.
        # This avoids a jagged matrix when runs terminate at different steps.
        padded = []
        for s in r.all_stats:
            hist = s.best_cost_history
            if hist:
                padded.append(hist + [hist[-1]] * (max_len - len(hist)))
            else:
                padded.append([float("nan")] * max_len)

        arr  = np.array(padded)           # shape (n_runs, max_len)
        mean = np.nanmean(arr, axis=0)    # mean best cost per step
        std  = np.nanstd(arr, axis=0)     # std dev across seeds per step
        xs   = np.arange(max_len)

        (line,) = ax.plot(xs, mean, label=r.algorithm_name)
        # Shaded band shows run-to-run variability
        ax.fill_between(xs, mean - std, mean + std, alpha=0.2, color=line.get_color())

    ax.set_xlabel("Temperature step")
    ax.set_ylabel("Best objective value")
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150)

    if show:
        plt.show()

    plt.close(fig)
