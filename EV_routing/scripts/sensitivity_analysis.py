"""
Parameter sensitivity analysis from tuning results.

For each algorithm, loads its <algo>_results.csv (produced by tune.py) and
computes how much each hyperparameter shifts the mean objective.  Sensitivity
score = (max_group_mean − min_group_mean) / overall_mean × 100 (%).

Run from the project root:

    PYTHONPATH=EV_routing python EV_routing/scripts/sensitivity_analysis.py

Outputs:
    EV_routing/results/<INSTANCE>/figures/sensitivity/<algo>_sensitivity.png
    EV_routing/results/<INSTANCE>/figures/sensitivity/all_algorithms.png
    EV_routing/results/<INSTANCE>/sensitivity_summary.txt
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# =============================================================================
INSTANCE      = "sf_75"
ALGORITHMS    = ["SA", "GA", "MA", "ACO"]
# =============================================================================

RESULTS_DIR = Path(f"EV_routing/results/{INSTANCE}/tuning")
FIGURES_DIR = Path(f"EV_routing/results/{INSTANCE}/figures/sensitivity")
SUMMARY_FILE = Path(f"EV_routing/results/{INSTANCE}/sensitivity_summary.txt")


def _load_results(algo: str) -> pd.DataFrame | None:
    csv_path = RESULTS_DIR / f"{algo.lower()}_results.csv"
    if not csv_path.exists():
        print(f"  [{algo}] No CSV at {csv_path} — skipping.")
        return None
    df = pd.read_csv(csv_path)
    return df


def _compute_sensitivity(df: pd.DataFrame) -> dict[str, float]:
    """
    Normalized sensitivity score per parameter (%).

    For each hyperparameter column, group by value and compute the mean
    objective within each group.  The score is the range of those group
    means relative to the overall mean — i.e. how much the parameter
    shifts performance when varied across its search range.
    """
    skip = {"mean_cost", "seed_costs"}
    param_cols = [c for c in df.columns if c not in skip]
    overall_mean = df["mean_cost"].mean()
    if overall_mean == 0:
        return {}

    scores: dict[str, float] = {}
    for col in param_cols:
        group_means = df.groupby(col)["mean_cost"].mean()
        scores[col] = (group_means.max() - group_means.min()) / overall_mean * 100.0

    return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))


def _plot_sensitivity(scores: dict[str, float], algo: str, ax: plt.Axes) -> None:
    params = list(scores.keys())
    values = list(scores.values())
    colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(params)))

    bars = ax.barh(params[::-1], values[::-1], color=colors[::-1])
    ax.set_xlabel("Sensitivity score (%)")
    ax.set_title(f"{algo} — Parameter Sensitivity")
    ax.axvline(0, color="black", linewidth=0.5)

    for bar, v in zip(bars, values[::-1]):
        ax.text(
            bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
            f"{v:.1f}%", va="center", fontsize=8,
        )


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    summary_lines: list[str] = [f"Sensitivity Analysis — {INSTANCE}\n", "=" * 60 + "\n"]

    all_scores: dict[str, dict[str, float]] = {}

    for algo in ALGORITHMS:
        df = _load_results(algo)
        if df is None:
            continue

        scores = _compute_sensitivity(df)
        all_scores[algo] = scores

        # Per-algorithm figure
        fig, ax = plt.subplots(figsize=(8, max(3, 0.6 * len(scores))))
        _plot_sensitivity(scores, algo, ax)
        plt.tight_layout()
        out = FIGURES_DIR / f"{algo.lower()}_sensitivity.png"
        fig.savefig(out, dpi=150)
        plt.close(fig)
        print(f"  [{algo}] Saved → {out}")

        # Summary text
        summary_lines.append(f"\n{algo}:\n")
        for param, score in scores.items():
            bar = "█" * int(score / 2)
            summary_lines.append(f"  {param:<30} {score:6.1f}%  {bar}\n")

    # Combined figure (one row per algorithm)
    if all_scores:
        n_algos = len(all_scores)
        fig = plt.figure(figsize=(14, 3.5 * n_algos))
        gs  = gridspec.GridSpec(n_algos, 1, hspace=0.6)

        for i, (algo, scores) in enumerate(all_scores.items()):
            ax = fig.add_subplot(gs[i])
            _plot_sensitivity(scores, algo, ax)

        out = FIGURES_DIR / "all_algorithms.png"
        fig.savefig(out, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"\n  Combined figure → {out}")

    with open(SUMMARY_FILE, "w") as f:
        f.writelines(summary_lines)
    print(f"  Summary text → {SUMMARY_FILE}")


if __name__ == "__main__":
    main()
