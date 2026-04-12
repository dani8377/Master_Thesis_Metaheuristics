from __future__ import annotations

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.figure

from tools.experiment import ExperimentResults


def plot_convergence(
    results: ExperimentResults | list[ExperimentResults],
    title: str | None = None,
    save_path: str | Path | None = None,
    show: bool = True,
) -> matplotlib.figure.Figure:
    """
    Plot best-cost convergence curves for one or more algorithms.

    For each algorithm, draws the mean best-cost across all seeds (solid line)
    with a ±1 std-deviation band. Requires each run's stats object to have a
    ``best_cost_history`` attribute (list of best cost per iteration/temperature
    step). Runs without this attribute are silently skipped.

    Parameters
    ----------
    results:
        A single ExperimentResults or a list (one per algorithm) for comparison.
    title:
        Plot title. Defaults to the algorithm name(s).
    save_path:
        If given, the figure is saved here (parent directory is created if needed).
    show:
        Call plt.show() after plotting.
    """
    if isinstance(results, ExperimentResults):
        results_list = [results]
    else:
        results_list = list(results)

    fig, ax = plt.subplots(figsize=(10, 5))

    for exp in results_list:
        histories = [
            s.best_cost_history
            for s in exp.all_stats
            if hasattr(s, "best_cost_history") and s.best_cost_history
        ]

        if not histories:
            print(f"Warning: {exp.algorithm_name} has no best_cost_history — skipped.")
            continue

        # Pad shorter runs to the length of the longest
        max_len = max(len(h) for h in histories)
        padded = np.array([h + [h[-1]] * (max_len - len(h)) for h in histories])

        steps = np.arange(1, max_len + 1)
        mean = padded.mean(axis=0)
        std = padded.std(axis=0)

        (line,) = ax.plot(steps, mean, linewidth=1.5, label=exp.algorithm_name)
        ax.fill_between(steps, mean - std, mean + std, alpha=0.15, color=line.get_color())

    ax.set_xlabel("Step")
    ax.set_ylabel("Best objective value")
    ax.set_title(title or "Convergence: " + " vs ".join(e.algorithm_name for e in results_list))
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150)
        print(f"Convergence plot saved to: {save_path}")

    if show:
        plt.show()

    return fig


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
