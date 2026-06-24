"""
Regenerate the three figures that had rendering problems, from the saved CSVs.

Fixes:
  1. box_comparison.png        — mean (mu) labels were overprinting the boxes;
                                  now placed clearly above each box.
  2. scalability_battery.png   — the quality panel plotted penalty-dominated
                                  infeasible cells (F up to ~28,000), which
                                  flattened the feasible-region signal; now it
                                  plots feasible cells only (matches the table).
  3. scalability/quality_vs_size.png — x-axis ran to negative customer counts
                                  with misplaced feasibility markers; replaced
                                  with a clean mean-objective-vs-size plot
                                  (feasible cells only, log x).

Run:  PYTHONPATH=EV_routing python EV_routing/scripts/regen_fixed_plots.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

RESULTS = Path("EV_routing/results")

COLORS = {
    "Greedy":              "#7f7f7f",
    "Simulated Annealing": "#1f77b4",
    "Genetic Algorithm":   "#2ca02c",
    "Memetic Algorithm":   "#ff7f0e",
    "ACO":                 "#e377c2",
}
ORDER = ["Greedy", "Simulated Annealing", "Genetic Algorithm", "Memetic Algorithm", "ACO"]
META  = ["Simulated Annealing", "Genetic Algorithm", "Memetic Algorithm", "ACO"]


# ---------------------------------------------------------------------------
# 1. Box comparison — mean labels placed above the boxes
# ---------------------------------------------------------------------------
def fix_box_comparison() -> None:
    df = pd.read_csv(RESULTS / "sf_75/results_per_seed.csv")
    groups = [df.loc[df.algorithm == a, "cost"].to_numpy() for a in ORDER]

    fig, ax = plt.subplots(figsize=(11, 5.5))
    bp = ax.boxplot(groups, patch_artist=True, widths=0.55,
                    medianprops=dict(color="black", linewidth=1.5),
                    flierprops=dict(marker="o", markersize=3, alpha=0.4))
    for patch, a in zip(bp["boxes"], ORDER):
        patch.set_facecolor(COLORS[a]); patch.set_alpha(0.55)

    # jittered points + mean label ABOVE each box
    rng = np.random.default_rng(0)
    ymax = max(g.max() for g in groups)
    ymin = min(g.min() for g in groups)
    pad = (ymax - ymin) * 0.04
    for i, (g, a) in enumerate(zip(groups, ORDER), start=1):
        x = rng.normal(i, 0.06, size=len(g))
        ax.scatter(x, g, color=COLORS[a], edgecolor="white", s=28, zorder=3, alpha=0.9)
        ax.text(i, g.max() + pad, f"$\\mu$={g.mean():.3f}",
                ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax.set_xticks(range(1, len(ORDER) + 1))
    ax.set_xticklabels(ORDER)
    ax.set_ylabel("Best objective value")
    ax.set_ylim(ymin - pad, ymax + pad * 4)
    ax.set_title("Solution quality distribution — 10 seeds, budget = 150,000 evals",
                 fontweight="bold")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    out = RESULTS / "sf_75/figures/box_comparison.png"
    fig.savefig(out, dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"  wrote {out}")


# ---------------------------------------------------------------------------
# 2. Battery scalability — feasible cells only on the quality panel
# ---------------------------------------------------------------------------
def fix_battery() -> None:
    df = pd.read_csv(RESULTS / "sf_75/scalability_battery.csv")
    fig, (axq, axf) = plt.subplots(1, 2, figsize=(13, 5))

    for a in META:
        sub = df[df.algorithm == a].sort_values("battery_capacity_kwh")
        feas = sub[sub.feasible_pct >= 99.9]   # drop penalty-dominated cells
        axq.plot(feas.battery_capacity_kwh, feas.avg_cost, marker="o",
                 color=COLORS[a], label=a, linewidth=1.8)
        axf.plot(sub.battery_capacity_kwh, sub.feasible_pct, marker="s",
                 color=COLORS[a], label=a, linewidth=1.8)

    for ax in (axq, axf):
        ax.invert_xaxis()  # loose -> tight
        ax.set_xlabel("Battery capacity (kWh)  (← more constrained)")
        ax.grid(alpha=0.3)
    axq.set_ylabel("Average objective value (feasible cells only, lower = better)")
    axq.set_title("Solution Quality vs. Constraint Tightness")
    axq.legend(fontsize=9)
    axf.set_ylabel("Feasible solutions (%)")
    axf.set_title("Feasibility Rate vs. Constraint Tightness")
    axf.set_ylim(-5, 105)
    fig.suptitle("Vertical Scalability — 75 customers, battery capacity varied from loose to tight",
                 fontweight="bold")
    fig.tight_layout()
    out = RESULTS / "sf_75/figures/scalability_battery.png"
    fig.savefig(out, dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"  wrote {out}")


# ---------------------------------------------------------------------------
# 3. Customer scalability (standalone study) — clean mean-vs-size, feasible only
# ---------------------------------------------------------------------------
def fix_quality_vs_size() -> None:
    df = pd.read_csv(RESULTS / "scalability/scalability_results.csv")
    fig, ax = plt.subplots(figsize=(10, 5.5))

    for a in META:
        sub = df[(df.algorithm == a) & (df.feasible_pct >= 99.9)].sort_values("n_customers")
        if sub.empty:
            continue
        ax.plot(sub.n_customers, sub["mean"], marker="o",
                color=COLORS[a], label=a, linewidth=1.8)

    ax.set_xscale("log")
    ax.set_xlabel("Number of customers (log scale)")
    ax.set_ylabel("Mean objective value (feasible runs only, lower = better)")
    ax.set_title("Solution quality vs. instance size")
    ax.grid(alpha=0.3, which="both")
    ax.legend(fontsize=9)
    fig.tight_layout()
    out = RESULTS / "scalability/figures/quality_vs_size.png"
    fig.savefig(out, dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"  wrote {out}")


if __name__ == "__main__":
    print("Regenerating fixed figures:")
    fix_box_comparison()
    fix_battery()
    fix_quality_vs_size()
    print("Done.")
