"""
Scalability analysis: run all algorithms on instances of different sizes.

Pipeline
--------
1. Load calibrated weights ONCE from WEIGHTS_INSTANCE (shared across all sizes).
2. For each instance: load params.json (must exist — run tune.py first).
3. Run 10-seed comparison.

Run from the project root:

    PYTHONPATH=EV_routing python EV_routing/scripts/scalability_analysis.py

Prerequisites
-------------
Build all instances first (one-time):
    PYTHONPATH=EV_routing python EV_routing/scripts/build_instance.py

Calibrate weights for WEIGHTS_INSTANCE (once):
    PYTHONPATH=EV_routing python EV_routing/scripts/calibrate_weights.py

Tune each instance (run tune.py with INSTANCES set to all sizes):
    PYTHONPATH=EV_routing python EV_routing/scripts/tune.py

Outputs
-------
    EV_routing/results/scalability/scalability_results.csv
    EV_routing/results/scalability/scalability_table.txt
    EV_routing/results/scalability/figures/quality_vs_size.png
    EV_routing/results/scalability/figures/runtime_vs_size.png
    EV_routing/results/scalability/figures/feasibility_vs_size.png
"""
from __future__ import annotations

import json
import random
import statistics
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.data_loader import load_problem_data
from tools.battery import EVParameters
from tools.objective import ObjectiveWeights, evaluate_route
from tools.initial_solution import build_ev_feasible_solution
from tools.neighborhoods import generate_neighbor
from tools.feasibility import is_valid_basic_route
from tools.compare import run_controlled_comparison
from tools.tuning import random_search, grid_search
from algorithms.simulated_annealing import simulated_annealing
from algorithms.genetic_algorithm import genetic_algorithm
from algorithms.ant_colony import ant_colony_optimization
from algorithms.greedy import greedy_nearest_neighbor

# =============================================================================
# Configuration
# =============================================================================

INSTANCES      = ["sf_25", "sf_50", "sf_75", "sf_100", "sf_150", "sf_200", "sf_300", "sf_400", "sf_500"]
SEEDS          = list(range(3))

# Eval budget scales inversely with instance size so wall-clock time per
# instance stays roughly constant.  sf_75 gets BASE_EVALS; larger instances
# get fewer evals (each eval is proportionally more expensive).
BASE_EVALS = 10_000   # eval budget for sf_75 (75 customers)
BASE_N     = 75

# Weights are calibrated ONCE on this reference instance and reused for all
# instance sizes.  Since all instances are in the same SF region and we only
# compare algorithms within each instance, the same weights are valid across
# all sizes (each component scales uniformly, so relative balance is preserved).
WEIGHTS_INSTANCE = "sf_75"

# When params.json is missing for an instance, fall back to this instance's
# tuned params instead of re-tuning.  Set to None to disable the fallback
# and raise an error, or set AUTO_TUNE_IF_MISSING=True to auto-tune instead.
FALLBACK_PARAMS_INSTANCE = "sf_75"

# Set True only if you want to auto-tune instances that have no params.json
# AND no fallback instance is set.  Very slow — prefer running tune.py first.
AUTO_TUNE_IF_MISSING = False

# Tuning budget (used when params.json is missing and SKIP_TUNE_IF_EXISTS=False)
TUNE_SEEDS     = [0, 1, 2]
TUNE_EVALS     = 20_000
TUNE_TRIALS    = 30        # random-search trials for GA / MA / ACO

OUTPUT_DIR     = Path("EV_routing/results/scalability")
FIGURES_DIR    = OUTPUT_DIR / "figures"


def _max_evals_for(n_customers: int) -> int:
    """Eval budget that keeps wall-clock time roughly constant across instance sizes.

    Each objective evaluation is O(route_length), so a 500-node instance is
    ~7× more expensive per eval than sf_75.  Scaling inversely means sf_500
    gets fewer evals but finishes in similar wall-clock time to sf_75.
    """
    return max(3_000, min(BASE_EVALS, BASE_EVALS * BASE_N // n_customers))

# =============================================================================
# Tuning search spaces (same as tune.py)
# =============================================================================

SA_GRID = {
    "initial_temperature":        [0.3,  1.0,  3.0],
    "cooling_rate":               [0.990, 0.993, 0.997],
    "iterations_per_temperature": [20,   50,   100],
    "reheat_patience":            [100,  300,  500],
    "reheat_factor":              [0.3,  0.5,  0.7],
}
GA_SPACE = {
    "population_size": [40,  100, 200],
    "crossover_rate":  [0.75, 0.85, 0.95],
    "mutation_rate":   [0.05, 0.15, 0.25],
    "tournament_size": [2,   4],
    "elitism_count":   [1,   3,   5],
}
MA_SPACE = {**GA_SPACE, "local_search_iters": [5, 15, 30]}
ACO_SPACE = {
    "n_ants":                [10,  20,  30],
    "alpha":                 [0.5, 1.0, 2.0],
    "beta":                  [2.0, 4.0, 6.0],
    "rho":                   [0.05, 0.15, 0.30],
    "q0":                    [0.75, 0.85, 0.95],
    "battery_threshold_frac":[0.2,  0.4],
    "local_search_iters":    [0,   10],
    "candidate_list_k":      [0,   15],
}

# =============================================================================
# Helpers
# =============================================================================

def _calibrate_weights(data, ev_params: EVParameters) -> ObjectiveWeights:
    """Sample-based normalization (Deb 2001) + big-M penalties (Deb 2000)."""
    unit_w = ObjectiveWeights(
        distance_weight=1.0, travel_time_weight=1.0,
        energy_weight=1.0, charging_cost_weight=1.0,
        battery_violation_weight=0.0, infeasible_visit_weight=0.0,
    )
    samples: list[dict] = []
    seed = 0
    while len(samples) < N_SAMPLES_CAL:
        random.seed(seed); seed += 1
        route = build_ev_feasible_solution(data, ev_params)
        for _ in range(N_PERTURB_CAL):
            cand = generate_neighbor(route, data, ev_params)
            if is_valid_basic_route(cand, data):
                route = cand
        ev = evaluate_route(route, data, ev_params, unit_w)
        if not ev.feasible:
            continue
        samples.append({
            "distance_km":       ev.total_distance_km,
            "time_h":            ev.total_travel_time_h + ev.total_charging_time_h,
            "energy_kwh":        ev.total_energy_consumed_kwh,
            "charging_cost_usd": ev.total_charging_cost_usd,
        })

    means = {k: statistics.mean(s[k] for s in samples) for k in samples[0]}
    penalty = PENALTY_FACTOR * 4.0
    return ObjectiveWeights(
        distance_weight        = 1.0 / means["distance_km"],
        travel_time_weight     = 1.0 / means["time_h"],
        energy_weight          = 1.0 / means["energy_kwh"],
        charging_cost_weight   = 1.0 / means["charging_cost_usd"],
        battery_violation_weight = penalty,
        infeasible_visit_weight  = penalty,
    )


def _tune_instance(data, ev_params, weights, results_dir: Path) -> dict:
    """Tune all four algorithms and return params dict."""
    params: dict = {}

    sa_params, _, _ = grid_search(
        simulated_annealing, SA_GRID, data, ev_params, weights,
        TUNE_SEEDS, TUNE_EVALS, "SA", verbose=False,
    )
    params["SA"] = sa_params

    for name, fn, space in [
        ("GA", genetic_algorithm,       GA_SPACE),
        ("MA", genetic_algorithm,       MA_SPACE),
        ("ACO", ant_colony_optimization, ACO_SPACE),
    ]:
        p, _, _ = random_search(
            fn, space, data, ev_params, weights,
            TUNE_TRIALS, TUNE_SEEDS, TUNE_EVALS, name, verbose=False,
        )
        params[name] = p

    return params


def _load_reference_weights() -> ObjectiveWeights:
    """Load weights from the reference instance (calibrated once, reused for all sizes)."""
    weights_file = Path(f"EV_routing/results/{WEIGHTS_INSTANCE}/weights.json")
    if not weights_file.exists():
        raise FileNotFoundError(
            f"Reference weights not found at {weights_file}.\n"
            f"Run: PYTHONPATH=EV_routing python EV_routing/scripts/calibrate_weights.py\n"
            f"(with INSTANCES = [\"{WEIGHTS_INSTANCE}\"] in that script)"
        )
    w = json.loads(weights_file.read_text())["weights"]
    print(f"  Weights loaded from {weights_file} (shared for all instances)")
    return ObjectiveWeights(**w)


def _load_params(params_file: Path, data, ev_params, weights) -> dict:
    if params_file.exists():
        return json.loads(params_file.read_text())

    # Try the fallback instance's params
    if FALLBACK_PARAMS_INSTANCE:
        fallback = Path(f"EV_routing/results/{FALLBACK_PARAMS_INSTANCE}/params.json")
        if fallback.exists():
            print(f"    No params.json — using {FALLBACK_PARAMS_INSTANCE} params as fallback.")
            return json.loads(fallback.read_text())

    if AUTO_TUNE_IF_MISSING:
        print("    Tuning parameters …")
        params = _tune_instance(data, ev_params, weights, params_file.parent)
        params_file.parent.mkdir(parents=True, exist_ok=True)
        params_file.write_text(json.dumps(params, indent=2))
        print("    Tuning done.")
        return params

    raise FileNotFoundError(
        f"No params.json at {params_file}.\n"
        f"Either run tune.py for this instance, set FALLBACK_PARAMS_INSTANCE, "
        "or set AUTO_TUNE_IF_MISSING=True."
    )


# =============================================================================
# Plotting
# =============================================================================

def _is_fully_feasible(r, n_seeds: int) -> bool:
    return r.feasible_run_count == n_seeds


def _plot_quality(instance_results: dict, algo_names: list[str]) -> None:
    """Per-algorithm subplots. Only feasible instances are plotted; infeasible
    ones are marked with red dashed vertical lines so the y-axis stays readable."""
    colors = plt.cm.Set1(np.linspace(0, 0.8, len(algo_names)))
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    n_cols = 2
    n_rows = (len(algo_names) + 1) // n_cols
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(9 * n_cols, 4 * n_rows))
    axes = np.array(axes).flatten()

    for ax, algo, color in zip(axes, algo_names, colors):
        feas_ns, feas_means, feas_stds = [], [], []
        infeas_ns = []

        for inst in INSTANCES:
            if inst not in instance_results:
                continue
            n = int(inst.split("_")[1])
            r = instance_results[inst][algo]
            if _is_fully_feasible(r, len(SEEDS)):
                feas_ns.append(n)
                feas_means.append(r.average_cost)
                feas_stds.append(r.std_cost)
            else:
                infeas_ns.append(n)

        if feas_ns:
            ax.plot(feas_ns, feas_means, marker="o", color=color, linewidth=1.5)
            ax.fill_between(
                feas_ns,
                [m - s for m, s in zip(feas_means, feas_stds)],
                [m + s for m, s in zip(feas_means, feas_stds)],
                alpha=0.15, color=color,
            )

        for xn in infeas_ns:
            ax.axvline(xn, color="red", linestyle="--", alpha=0.55, linewidth=1.0)
            ax.text(xn, 0.02, "✗", transform=ax.get_xaxis_transform(),
                    color="red", ha="center", va="bottom", fontsize=9)

        if infeas_ns:
            ax.axvline(-999, color="red", linestyle="--", alpha=0.55,
                       linewidth=1.0, label="0 % feasible")
            ax.legend(fontsize=8, loc="upper left")

        ax.set_title(algo)
        ax.set_xlabel("Number of customers")
        ax.set_ylabel("Mean objective (feasible runs only)")
        ax.grid(True, alpha=0.3)

    for ax in axes[len(algo_names):]:
        ax.set_visible(False)

    fig.suptitle(
        f"Solution quality vs. instance size\n"
        f"Evaluation budget: {BASE_EVALS:,} evals at n={BASE_N}, scaled as {BASE_EVALS:,}×{BASE_N}/n",
        fontsize=12,
    )
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "quality_vs_size.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_improvement_over_greedy(instance_results: dict, algo_names: list[str]) -> None:
    """% improvement over greedy for instances where BOTH greedy and the
    algorithm are 100% feasible.  Puts all metaheuristics on a single shared
    axis so relative rankings are directly visible."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 5))

    greedy_name = "Greedy"
    meta_names = [a for a in algo_names if a != greedy_name]
    colors = plt.cm.Set1(np.linspace(0, 0.8, len(meta_names)))

    for algo, color in zip(meta_names, colors):
        plot_ns, plot_pcts = [], []
        for inst in INSTANCES:
            if inst not in instance_results:
                continue
            n = int(inst.split("_")[1])
            gr = instance_results[inst].get(greedy_name)
            ar = instance_results[inst][algo]
            if (gr is not None
                    and _is_fully_feasible(gr, len(SEEDS))
                    and _is_fully_feasible(ar, len(SEEDS))):
                pct = (gr.average_cost - ar.average_cost) / gr.average_cost * 100
                plot_ns.append(n)
                plot_pcts.append(pct)
        if plot_ns:
            ax.plot(plot_ns, plot_pcts, marker="o", color=color,
                    linewidth=1.5, label=algo)
            ax.fill_between(plot_ns, [0] * len(plot_ns), plot_pcts,
                            alpha=0.07, color=color)

    ax.axhline(0, color="gray", linestyle="--", linewidth=0.9, label="Greedy baseline")

    # Annotate the budget-dependence finding at sf_BASE_N
    ax.axvline(BASE_N, color="black", linestyle=":", alpha=0.4, linewidth=1.0)
    ax.annotate(
        f"n={BASE_N}: ranking reverses at ~45k evals\n(SA best in main experiment @ 150k evals)",
        xy=(BASE_N, ax.get_ylim()[0] if ax.get_ylim()[0] > 0 else 2),
        xytext=(BASE_N + 20, 5),
        fontsize=7.5,
        color="dimgray",
        arrowprops=dict(arrowstyle="->", color="dimgray", lw=0.8),
    )

    ax.set_xlabel("Number of customers")
    ax.set_ylabel("Improvement over Greedy (%)")
    ax.set_title(
        f"Improvement over greedy baseline  "
        f"(budget: {BASE_EVALS:,}×{BASE_N}/n evals)\n"
        "Only instances where greedy is 100 % feasible"
    )
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "improvement_over_greedy.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_consistency(instance_results: dict, algo_names: list[str]) -> None:
    """Coefficient of variation (std / mean × 100 %) per algorithm.
    Lower CV = more reproducible results across seeds."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = plt.cm.Set1(np.linspace(0, 0.8, len(algo_names)))

    for algo, color in zip(algo_names, colors):
        cv_ns, cv_vals = [], []
        for inst in INSTANCES:
            if inst not in instance_results:
                continue
            n = int(inst.split("_")[1])
            r = instance_results[inst][algo]
            if _is_fully_feasible(r, len(SEEDS)) and r.average_cost > 0:
                cv_ns.append(n)
                cv_vals.append(r.std_cost / r.average_cost * 100)
        if cv_ns:
            ax.plot(cv_ns, cv_vals, marker="s", color=color,
                    linewidth=1.5, label=algo)

    ax.set_xlabel("Number of customers")
    ax.set_ylabel("CV = std / mean  (%)")
    ax.set_title("Algorithm consistency across seeds (lower = more reproducible)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "consistency_vs_size.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_runtime(instance_results: dict, algo_names: list[str]) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    ns = [int(inst.split("_")[1]) for inst in INSTANCES if inst in instance_results]
    colors = plt.cm.Set1(np.linspace(0, 0.8, len(algo_names)))

    for algo, color in zip(algo_names, colors):
        rts = [
            instance_results[inst][algo].average_runtime
            for inst in INSTANCES if inst in instance_results
        ]
        ax.plot(ns, rts, marker="s", label=algo, color=color)

    ax.set_xlabel("Number of customers")
    ax.set_ylabel("Average runtime per seed (s)")
    ax.set_title("Runtime vs. instance size")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "runtime_vs_size.png", dpi=150)
    plt.close(fig)


def _plot_feasibility(instance_results: dict, algo_names: list[str]) -> None:
    """Heatmap (algorithm × instance) coloured by feasibility rate.
    Much easier to read than overlapping lines when many cells are 0 or 100 %."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    inst_list = [inst for inst in INSTANCES if inst in instance_results]
    ns_labels = [f"n={inst.split('_')[1]}" for inst in inst_list]

    matrix = np.array([
        [instance_results[inst][algo].feasible_run_count / len(SEEDS) * 100
         for inst in inst_list]
        for algo in algo_names
    ])

    fig, ax = plt.subplots(figsize=(max(10, len(inst_list) * 1.1), len(algo_names) * 0.9 + 1))
    im = ax.imshow(matrix, aspect="auto", cmap="RdYlGn", vmin=0, vmax=100)
    plt.colorbar(im, ax=ax, label="Feasibility rate (%)")

    ax.set_xticks(range(len(inst_list)))
    ax.set_xticklabels(ns_labels, rotation=45, ha="right")
    ax.set_yticks(range(len(algo_names)))
    ax.set_yticklabels(algo_names)

    for i in range(len(algo_names)):
        for j in range(len(inst_list)):
            v = matrix[i, j]
            txt_color = "white" if v < 50 else "black"
            ax.text(j, i, f"{v:.0f}%", ha="center", va="center",
                    fontsize=9, color=txt_color, fontweight="bold")

    ax.set_title("Feasibility rate (%) — algorithm × instance size")
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "feasibility_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _save_csv_and_table(instance_results: dict, algo_names: list[str]) -> None:
    rows = []
    for inst in INSTANCES:
        if inst not in instance_results:
            continue
        n = int(inst.split("_")[1])
        for algo in algo_names:
            r = instance_results[inst][algo]
            rows.append({
                "instance":    inst,
                "n_customers": n,
                "algorithm":   algo,
                "best":        r.best_cost,
                "mean":        r.average_cost,
                "std":         r.std_cost,
                "median":      statistics.median(r.best_costs),
                "cv_pct":      r.std_cost / r.average_cost * 100 if r.average_cost > 0 else 0,
                "feasible_pct": r.feasible_run_count / len(r.seeds) * 100,
                "avg_runtime_s": r.average_runtime,
            })

    df = pd.DataFrame(rows)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUTPUT_DIR / "scalability_results.csv"
    df.to_csv(csv_path, index=False)
    print(f"  CSV → {csv_path}")

    # Console table
    lines: list[str] = []
    lines.append("\nScalability Summary Table")
    lines.append("=" * 80)
    header = f"  {'Algorithm':<22}" + "".join(
        f"  {inst:>18}" for inst in INSTANCES if inst in instance_results
    )
    lines.append(header)
    lines.append("  " + "-" * (len(header) - 2))
    lines.append("  " + " " * 22 + "".join(
        f"  {'mean ± std':>18}" for inst in INSTANCES if inst in instance_results
    ))
    for algo in algo_names:
        cells = []
        for inst in INSTANCES:
            if inst not in instance_results:
                continue
            r = instance_results[inst][algo]
            cells.append(f"{r.average_cost:.3f} ± {r.std_cost:.3f}")
        lines.append(f"  {algo:<22}" + "".join(f"  {c:>18}" for c in cells))

    table_str = "\n".join(lines)
    print(table_str)

    txt_path = OUTPUT_DIR / "scalability_table.txt"
    with open(txt_path, "w") as f:
        f.write(table_str + "\n")
    print(f"  Table → {txt_path}")


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    ev_params = EVParameters(
        battery_capacity_kwh=20.0,
        initial_battery_kwh=20.0,
        energy_consumption_kwh_per_km=0.50,
        average_speed_kmh=50.0,
        grade_factor=3.0,
        speed_exponent=2.0,
    )

    print("=" * 60)
    print(f"Scalability analysis: {INSTANCES}")
    print(f"Seeds: {SEEDS}   Budget: {BASE_EVALS:,} evals @ sf_{BASE_N} (scaled per instance)")
    print("=" * 60)

    # Load calibrated weights once from the reference instance
    weights = _load_reference_weights()

    instance_results: dict = {}   # inst_name → {algo_name: ExperimentResults}
    algo_names: list[str] = []

    for inst in INSTANCES:
        inst_dir    = Path(f"EV_routing/instances/{inst}")
        params_file = Path(f"EV_routing/results/{inst}/params.json")

        if not inst_dir.exists():
            print(f"\n  [{inst}] Instance directory not found — skipping.")
            print("    Run: PYTHONPATH=EV_routing python EV_routing/scripts/build_instance.py")
            continue

        print(f"\n{'─'*60}")
        print(f"  Instance: {inst}")
        print(f"{'─'*60}")
        t0 = time.perf_counter()

        data   = load_problem_data(inst_dir, ev_params)
        params = _load_params(params_file, data, ev_params, weights)

        n_cust   = len(data.all_customer_ids)
        max_evals = _max_evals_for(n_cust)
        print(f"    {n_cust} customers, "
              f"{len(data.all_station_ids)} charging stations, "
              f"budget={max_evals:,} evals/seed")

        all_results = run_controlled_comparison(
            algorithms={
                "Greedy":              greedy_nearest_neighbor,
                "Simulated Annealing": simulated_annealing,
                "Genetic Algorithm":   genetic_algorithm,
                "Memetic Algorithm":   genetic_algorithm,
                "ACO":                 ant_colony_optimization,
            },
            data=data,
            ev_params=ev_params,
            weights=weights,
            seeds=SEEDS,
            max_evaluations=max_evals,
            verbose=True,
            algorithm_kwargs={
                "Greedy":              {},
                "Simulated Annealing": params.get("SA", {}),
                "Genetic Algorithm":   params.get("GA", {}),
                "Memetic Algorithm":   params.get("MA", {}),
                "ACO":                 params.get("ACO", {}),
            },
        )

        instance_results[inst] = {r.algorithm_name: r for r in all_results}
        if not algo_names:
            algo_names = [r.algorithm_name for r in all_results]

        elapsed = time.perf_counter() - t0
        print(f"  {inst} done in {elapsed:.0f}s")

    if not instance_results:
        print("\nNo instances were successfully analysed.")
        return

    print("\n" + "=" * 60)
    print("Saving plots and tables …")
    _plot_quality(instance_results, algo_names)
    _plot_improvement_over_greedy(instance_results, algo_names)
    _plot_consistency(instance_results, algo_names)
    _plot_runtime(instance_results, algo_names)
    _plot_feasibility(instance_results, algo_names)
    _save_csv_and_table(instance_results, algo_names)
    print(f"\nAll outputs → {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
