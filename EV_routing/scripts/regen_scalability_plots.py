"""
Regenerate scalability plots from the existing CSV without re-running algorithms.

Run from project root:
    PYTHONPATH=EV_routing python EV_routing/scripts/regen_scalability_plots.py
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Import plot functions and config from scalability_analysis
from scripts.scalability_analysis import (
    INSTANCES, FIGURES_DIR,
    _plot_quality, _plot_improvement_over_greedy,
    _plot_consistency, _plot_runtime, _plot_feasibility,
)

CSV_PATH = Path("EV_routing/results/scalability/scalability_results.csv")


def _build_instance_results(df: pd.DataFrame) -> tuple[dict, list[str]]:
    """Reconstruct the instance_results dict from a CSV row using SimpleNamespace."""
    instance_results: dict = {}
    algo_order: list[str] = []

    for inst in INSTANCES:
        subset = df[df["instance"] == inst]
        if subset.empty:
            continue
        instance_results[inst] = {}
        for _, row in subset.iterrows():
            algo = row["algorithm"]
            if algo not in algo_order:
                algo_order.append(algo)
            n_seeds = max(1, round(row["feasible_pct"] / 100 * 3))  # approximate
            total_seeds = 3
            feasible_count = round(row["feasible_pct"] / 100 * total_seeds)

            r = SimpleNamespace(
                algorithm_name=algo,
                average_cost=row["mean"],
                std_cost=row["std"],
                best_costs=[row["best"], row["mean"], row["median"]],
                average_runtime=row["avg_runtime_s"],
                feasible_run_count=feasible_count,
            )
            # Patch in the properties that plot functions access
            r.feasible_run_count = feasible_count
            instance_results[inst][algo] = r

    return instance_results, algo_order


# Monkey-patch len(SEEDS) to 3 so _is_fully_feasible threshold is correct
import scripts.scalability_analysis as _sa_mod
_sa_mod.SEEDS = [0, 1, 2]


def main() -> None:
    if not CSV_PATH.exists():
        print(f"CSV not found: {CSV_PATH}")
        return

    df = pd.read_csv(CSV_PATH)
    # Rename columns to match what the script expects
    df = df.rename(columns={"algorithm": "algorithm"})
    # Normalise algorithm names to match what main run produces
    name_map = {
        "Simulated Annealing": "Simulated Annealing",
        "Genetic Algorithm": "Genetic Algorithm",
        "Memetic Algorithm": "Memetic Algorithm",
        "ACO": "ACO",
        "Greedy": "Greedy",
    }
    df["algorithm"] = df["algorithm"].map(name_map).fillna(df["algorithm"])

    instance_results, algo_names = _build_instance_results(df)

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    _plot_quality(instance_results, algo_names)
    _plot_improvement_over_greedy(instance_results, algo_names)
    _plot_consistency(instance_results, algo_names)
    _plot_runtime(instance_results, algo_names)
    _plot_feasibility(instance_results, algo_names)
    print(f"Plots regenerated → {FIGURES_DIR}/")


if __name__ == "__main__":
    main()
