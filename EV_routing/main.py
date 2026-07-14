"""
main.py - Entry point for the EV Routing experiments.

Orchestrates all algorithms (SA, GA, MA, ACO, Greedy) over multiple random seeds
and produces comparison tables, convergence plots, box charts, and CSV files.
Hyperparameters are read from params.json; objective weights from weights.json.

Usage:
    PYTHONPATH=EV_routing python EV_routing/main.py
    PYTHONPATH=EV_routing python EV_routing/main.py --seeds 5
    PYTHONPATH=EV_routing python EV_routing/main.py --sensitivity
    PYTHONPATH=EV_routing python EV_routing/main.py --algorithms SA ACO
"""
import argparse
import atexit
import csv
import json
import sys
import time
from pathlib import Path

from tools.data_loader import load_problem_data
from tools.battery import EVParameters
from tools.objective import ObjectiveWeights
from tools.experiment import ExperimentResults, run_experiments
from algorithms.simulated_annealing import simulated_annealing
from algorithms.genetic_algorithm import genetic_algorithm
from algorithms.ant_colony import ant_colony_optimization
from algorithms.greedy import greedy_nearest_neighbor
from tools.compare import run_controlled_comparison, print_detailed_metrics
from tools.statistics import pairwise_wilcoxon, print_wilcoxon_table, print_summary_table, to_latex_table
from tools.plot import (
    plot_convergence,
    plot_convergence_by_evaluations,
    plot_box_comparison,
    plot_sa_diagnostics,
    plot_ga_diagnostics,
    plot_aco_diagnostics,
    plot_cost_breakdown,
    plot_runtime_comparison,
    plot_scalability,
    plot_optimality_gap_comparison,
    print_comparison_table,
)

# ── Instance selection ────────────────────────────────────────────────────────
INSTANCE      = "sf_75"
INSTANCE_DIR  = Path(f"EV_routing/instances/{INSTANCE}")
RESULTS_DIR   = Path(f"EV_routing/results/{INSTANCE}")
FIGURES_DIR   = RESULTS_DIR / "figures"
PARAMS_FILE   = RESULTS_DIR / "params.json"
# ─────────────────────────────────────────────────────────────────────────────

MAX_EVALS = 150_000

# ── Focus modes ───────────────────────────────────────────────────────────────
# Weight presets applied on top of the calibrated weights, mirroring the cloud
# module's Performance/Balanced/Eco modes.  Each multiplier vector sums to 4.0,
# so a typical feasible route still scores ~4.0 and the 100x big-M penalty
# ratio is preserved; only the emphasis among the four real-cost terms shifts.
FOCUS_MODES = {
    "balanced": {"distance": 1.0, "time": 1.0, "energy": 1.0, "charging_cost": 1.0},
    "eco":      {"distance": 0.4, "time": 0.4, "energy": 2.8, "charging_cost": 0.4},
    "time":     {"distance": 0.4, "time": 2.8, "energy": 0.4, "charging_cost": 0.4},
}


# ---------------------------------------------------------------------------
# Console log capture — tee stdout to run_log.txt
# ---------------------------------------------------------------------------

class _TeeStream:
    def __init__(self, original, log_file) -> None:
        self._original = original
        self._log_file = log_file

    def write(self, text: str) -> int:
        self._original.write(text)
        try:
            self._log_file.write(text)
        except (ValueError, OSError):
            pass
        return len(text)

    def flush(self) -> None:
        self._original.flush()
        try:
            self._log_file.flush()
        except (ValueError, OSError):
            pass

    def isatty(self) -> bool:
        return getattr(self._original, "isatty", lambda: False)()

    def fileno(self) -> int:
        return self._original.fileno()


def _install_console_log(results_dir: Path) -> Path:
    results_dir.mkdir(parents=True, exist_ok=True)
    log_path = results_dir / "run_log.txt"
    log_file = open(log_path, "w", encoding="utf-8", newline="")
    original_stdout = sys.stdout
    sys.stdout = _TeeStream(original_stdout, log_file)

    def _restore() -> None:
        sys.stdout = original_stdout
        try:
            log_file.flush()
            log_file.close()
        except Exception:
            pass

    atexit.register(_restore)
    return log_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

_ALGORITHM_CHOICES = ["SA", "GA", "MA", "ACO", "Greedy", "all"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="EV Routing — Metaheuristic Experiment Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py                           # all algorithms, 10 seeds\n"
            "  python main.py --algorithms SA ACO       # selected algorithms only\n"
            "  python main.py --seeds 5                 # quick 5-seed test run\n"
            "  python main.py --sensitivity             # add parameter sensitivity sweeps\n"
            "  python main.py --sensitivity --seeds 3   # fast sensitivity check\n"
        ),
    )
    parser.add_argument(
        "--algorithms", "-a",
        nargs="+",
        choices=_ALGORITHM_CHOICES,
        default=["all"],
        metavar="ALG",
        help="Algorithms to run: SA, GA, MA, ACO, Greedy, all.  Default: all.",
    )
    parser.add_argument(
        "--seeds", "-s",
        type=int,
        default=None,
        help="Number of independent random seeds per algorithm (default: 10).",
    )
    parser.add_argument(
        "--sensitivity", "-S",
        action="store_true",
        help=(
            "Run hyperparameter sensitivity sweeps for selected algorithms.  "
            "Sweeps 2 key parameters per algorithm using a reduced budget "
            "(30 k evals) and 3 seeds per point.  Saves CSV + errorbar plot."
        ),
    )
    parser.add_argument(
        "--scalability", "-L",
        action="store_true",
        help=(
            "Run scalability analysis: (1) vary customer count across dedicated "
            "instances sf_25 … sf_500 (9 points) to show runtime and quality "
            "trends, and (2) vary battery capacity from 5 to 20 kWh (7 points) "
            "on the sf_75 instance.  Uses 3 seeds and a 30 k eval budget per point."
        ),
    )
    parser.add_argument(
        "--opt-gap", "-G",
        action="store_true",
        dest="opt_gap",
        help=(
            "Compute optimality gap vs Best-Known Solution (BKS) after the "
            "main comparison.  BKS = best cost found across all algorithms and "
            "seeds in that run.  Saves optimality_gap.csv and "
            "figures/optimality_gap.png.  Use --seeds 20 for a robust estimate."
        ),
    )
    parser.add_argument(
        "--mode", "-M",
        choices=list(FOCUS_MODES),
        default="balanced",
        help=(
            "Objective focus mode: 'balanced' uses the calibrated weights "
            "unchanged; 'eco' shifts 70%% of the real-cost weight onto energy; "
            "'time' shifts 70%% onto total (travel + charging) time.  "
            "Non-balanced modes write to results/<instance>_<mode>/."
        ),
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print per-seed progress during multi-seed runs.",
    )
    return parser.parse_args()


def _resolve_algorithms(selections: list[str]) -> dict[str, bool]:
    run_sa = run_ga = run_ma = run_aco = run_greedy = False
    for sel in selections:
        if sel == "all":
            run_sa = run_ga = run_ma = run_aco = run_greedy = True
        elif sel == "SA":
            run_sa = True
        elif sel == "GA":
            run_ga = True
        elif sel == "MA":
            run_ma = True
        elif sel == "ACO":
            run_aco = True
        elif sel == "Greedy":
            run_greedy = True
    return {"SA": run_sa, "GA": run_ga, "MA": run_ma, "ACO": run_aco, "Greedy": run_greedy}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _print_section(title: str) -> None:
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Sensitivity analysis
# ---------------------------------------------------------------------------

def _sweep_one_param(
    algo_fn,
    base_kwargs: dict,
    param_name: str,
    values: list,
    data,
    ev_params,
    weights,
    seeds: list[int],
    max_evals: int,
    label_fmt: str = "{v}",
) -> list[dict]:
    rows: list[dict] = []
    for v in values:
        kwargs = {**base_kwargs, param_name: v, "max_evaluations": max_evals}
        res = run_experiments(
            algorithm=algo_fn,
            data=data, ev_params=ev_params, weights=weights,
            seeds=seeds, algorithm_name="sweep",
            verbose=False, **kwargs,
        )
        print(
            f"  {label_fmt.format(v=v):>12}"
            f"  best={res.best_cost:>10.4f}"
            f"  avg={res.average_cost:>10.4f}"
            f"  std={res.std_cost:>8.4f}"
            f"  feasible={res.feasible_run_count}/{len(seeds)}"
        )
        rows.append({
            "param": param_name, "value": v,
            "best": res.best_cost, "average": res.average_cost,
            "worst": res.worst_cost, "std_dev": res.std_cost,
            "feasible": res.feasible_run_count,
        })
    return rows


def _save_sensitivity_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["param", "value", "best", "average", "worst", "std_dev", "feasible"]
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Sensitivity CSV         -> {path}")


def _plot_sensitivity_sweep(
    rows_a: list[dict], label_a: str, xlabel_a: str, xscale_a: str,
    rows_b: list[dict], label_b: str, xlabel_b: str,
    title: str, save_path: Path,
) -> None:
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    for ax, rows, xlabel, xscale, color in [
        (axes[0], rows_a, xlabel_a, xscale_a, "steelblue"),
        (axes[1], rows_b, xlabel_b, "linear",  "darkorange"),
    ]:
        vals = [r["value"] for r in rows]
        avgs = [r["average"] for r in rows]
        stds = [r["std_dev"] for r in rows]
        ax.errorbar(vals, avgs, yerr=stds, marker="o", capsize=4, color=color, linewidth=1.5)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Average best objective")
        ax.set_xscale(xscale)
        ax.grid(True, alpha=0.3)
    axes[0].set_title(label_a)
    axes[1].set_title(label_b)
    plt.suptitle(title, fontsize=13)
    plt.tight_layout()
    save_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Sensitivity plot        -> {save_path}")


def run_sa_sensitivity(data, ev_params, weights, base_kwargs, sweep_cfg, figures_dir, results_dir, seeds):
    _print_section("SA Sensitivity Analysis")

    print(f"\n  T0 sweep  (cooling_rate={base_kwargs['cooling_rate']}):")
    print(f"  {'T_init':>12}  {'best':>14}  {'avg':>14}  {'std':>12}  feasible")
    print("  " + "-" * 70)
    t0_rows = _sweep_one_param(
        simulated_annealing, base_kwargs,
        "initial_temperature", sweep_cfg["temperatures"],
        data, ev_params, weights, seeds, sweep_cfg["max_evals"],
        label_fmt="{v:.4f}",
    )

    print(f"\n  Cooling-rate sweep  (initial_temperature={base_kwargs['initial_temperature']}):")
    print(f"  {'alpha':>12}  {'best':>14}  {'avg':>14}  {'std':>12}  feasible")
    print("  " + "-" * 70)
    cr_rows = _sweep_one_param(
        simulated_annealing, base_kwargs,
        "cooling_rate", sweep_cfg["cooling_rates"],
        data, ev_params, weights, seeds, sweep_cfg["max_evals"],
        label_fmt="{v:.4f}",
    )

    _save_sensitivity_csv(t0_rows + cr_rows, results_dir / "sensitivity_sa.csv")
    _plot_sensitivity_sweep(
        t0_rows, "SA: sensitivity to initial temperature T₀", "Initial temperature T₀", "log",
        cr_rows, "SA: sensitivity to cooling rate α", "Cooling rate α",
        title="SA Hyperparameter Sensitivity",
        save_path=figures_dir / "sa_sensitivity.png",
    )


def run_ga_sensitivity(data, ev_params, weights, base_kwargs, sweep_cfg, figures_dir, results_dir, seeds):
    _print_section("GA Sensitivity Analysis")

    print(f"\n  Population-size sweep  (crossover_rate={base_kwargs['crossover_rate']}):")
    print(f"  {'pop_size':>12}  {'best':>14}  {'avg':>14}  {'std':>12}  feasible")
    print("  " + "-" * 70)
    pop_rows = _sweep_one_param(
        genetic_algorithm, base_kwargs,
        "population_size", sweep_cfg["population_sizes"],
        data, ev_params, weights, seeds, sweep_cfg["max_evals"],
    )

    print(f"\n  Crossover-rate sweep  (population_size={base_kwargs['population_size']}):")
    print(f"  {'cx_rate':>12}  {'best':>14}  {'avg':>14}  {'std':>12}  feasible")
    print("  " + "-" * 70)
    cx_rows = _sweep_one_param(
        genetic_algorithm, base_kwargs,
        "crossover_rate", sweep_cfg["crossover_rates"],
        data, ev_params, weights, seeds, sweep_cfg["max_evals"],
        label_fmt="{v:.2f}",
    )

    _save_sensitivity_csv(pop_rows + cx_rows, results_dir / "sensitivity_ga.csv")
    _plot_sensitivity_sweep(
        pop_rows, "GA: sensitivity to population size", "Population size", "linear",
        cx_rows,  "GA: sensitivity to crossover rate", "Crossover rate",
        title="GA Hyperparameter Sensitivity",
        save_path=figures_dir / "ga_sensitivity.png",
    )


def run_ma_sensitivity(data, ev_params, weights, base_kwargs, sweep_cfg, figures_dir, results_dir, seeds):
    _print_section("MA Sensitivity Analysis")

    print(f"\n  Population-size sweep  (local_search_iters={base_kwargs['local_search_iters']}):")
    print(f"  {'pop_size':>12}  {'best':>14}  {'avg':>14}  {'std':>12}  feasible")
    print("  " + "-" * 70)
    pop_rows = _sweep_one_param(
        genetic_algorithm, base_kwargs,
        "population_size", sweep_cfg["population_sizes"],
        data, ev_params, weights, seeds, sweep_cfg["max_evals"],
    )

    print(f"\n  Local-search-iters sweep  (population_size={base_kwargs['population_size']}):")
    print(f"  {'ls_iters':>12}  {'best':>14}  {'avg':>14}  {'std':>12}  feasible")
    print("  " + "-" * 70)
    ls_rows = _sweep_one_param(
        genetic_algorithm, base_kwargs,
        "local_search_iters", sweep_cfg["local_search_iters"],
        data, ev_params, weights, seeds, sweep_cfg["max_evals"],
    )

    _save_sensitivity_csv(pop_rows + ls_rows, results_dir / "sensitivity_ma.csv")
    _plot_sensitivity_sweep(
        pop_rows, "MA: sensitivity to population size",     "Population size",         "linear",
        ls_rows,  "MA: sensitivity to local-search iters",  "Local-search iterations",
        title="MA Hyperparameter Sensitivity",
        save_path=figures_dir / "ma_sensitivity.png",
    )


def run_aco_sensitivity(data, ev_params, weights, base_kwargs, sweep_cfg, figures_dir, results_dir, seeds):
    _print_section("ACO Sensitivity Analysis")

    print(f"\n  Alpha sweep  (beta={base_kwargs['beta']}):")
    print(f"  {'alpha':>12}  {'best':>14}  {'avg':>14}  {'std':>12}  feasible")
    print("  " + "-" * 70)
    alpha_rows = _sweep_one_param(
        ant_colony_optimization, base_kwargs,
        "alpha", sweep_cfg["alphas"],
        data, ev_params, weights, seeds, sweep_cfg["max_evals"],
        label_fmt="{v:.2f}",
    )

    print(f"\n  Beta sweep  (alpha={base_kwargs['alpha']}):")
    print(f"  {'beta':>12}  {'best':>14}  {'avg':>14}  {'std':>12}  feasible")
    print("  " + "-" * 70)
    beta_rows = _sweep_one_param(
        ant_colony_optimization, base_kwargs,
        "beta", sweep_cfg["betas"],
        data, ev_params, weights, seeds, sweep_cfg["max_evals"],
        label_fmt="{v:.1f}",
    )

    _save_sensitivity_csv(alpha_rows + beta_rows, results_dir / "sensitivity_aco.csv")
    _plot_sensitivity_sweep(
        alpha_rows, "ACO: sensitivity to α (pheromone weight)", "Pheromone weight α", "linear",
        beta_rows,  "ACO: sensitivity to β (heuristic weight)",  "Heuristic weight β",
        title="ACO Hyperparameter Sensitivity",
        save_path=figures_dir / "aco_sensitivity.png",
    )


# ---------------------------------------------------------------------------
# Scalability analysis
# ---------------------------------------------------------------------------

def _build_algo_list(
    run_flags: dict[str, bool],
    sa_kwargs: dict,
    ga_kwargs: dict,
    ma_kwargs: dict,
    aco_kwargs: dict,
) -> list[tuple]:
    algos = []
    if run_flags["SA"]:
        algos.append(("Simulated Annealing", simulated_annealing, sa_kwargs))
    if run_flags["GA"]:
        algos.append(("Genetic Algorithm", genetic_algorithm, ga_kwargs))
    if run_flags["MA"]:
        algos.append(("Memetic Algorithm", genetic_algorithm, ma_kwargs))
    if run_flags["ACO"]:
        algos.append(("ACO", ant_colony_optimization, aco_kwargs))
    return algos


def _print_scale_winner_table(rows: list[dict], title: str) -> None:
    from collections import Counter as _Counter
    _print_section(title)
    if not rows:
        return
    print(f"  {'Scale point':<22} {'Winner':<27} {'Avg F(X)':>10} {'Avg time':>9}")
    print("  " + "-" * 72)
    win_counts: dict = _Counter()
    for r in rows:
        if not r:
            continue
        print(
            f"  {r['label']:<22}"
            f" {r['winner']:<27}"
            f" {r['winner_avg']:>10.4f}"
            f" {r['winner_time']:>8.2f}s"
        )
        win_counts[r["winner"]] += 1
    total = sum(win_counts.values())
    print()
    for name, cnt in win_counts.most_common():
        bar = "█" * cnt
        print(f"  {name:<27}  {cnt}/{total} points  ({cnt/total*100:.0f}%)  {bar}")
    print()


def _run_customer_scaling(
    algos: list[tuple],
    ev_params,
    weights,
    seeds: list[int],
    max_evals: int,
) -> dict:
    """
    Load each dedicated instance (sf_25 … sf_500) to vary problem size
    with real road distances.  The base instance is kept for n=75.
    """
    INSTANCES = [25, 50, 75, 100, 150, 200, 300, 400, 500]
    scale_data: dict = {}
    winner_rows: list[dict] = []

    for n in INSTANCES:
        inst_dir = Path(f"EV_routing/instances/sf_{n}")
        if not inst_dir.exists():
            print(f"\n  ── n_customers={n}: instance not found, skipping ──")
            continue
        sub = load_problem_data(inst_dir, ev_params)
        print(f"\n  ── n_customers={n}  ({inst_dir}) ──")

        best_res = None
        for name, fn, kwargs in algos:
            res = run_experiments(
                fn, sub, ev_params, weights,
                seeds=seeds, algorithm_name=name, verbose=False,
                max_evaluations=max_evals, **kwargs,
            )
            print(
                f"    {name:<27}  time={res.average_runtime:5.1f}s"
                f"  F={res.average_cost:.4f}"
                f"  feasible={res.feasible_run_count}/{len(seeds)}"
            )
            if name not in scale_data:
                scale_data[name] = {"sizes": [], "runtimes": [], "costs": []}
            scale_data[name]["sizes"].append(n)
            scale_data[name]["runtimes"].append(res.average_runtime)
            scale_data[name]["costs"].append(res.average_cost)
            if best_res is None or res.average_cost < best_res.average_cost:
                best_res = res

        if best_res is not None:
            winner_rows.append({
                "label": f"n={n}",
                "winner": best_res.algorithm_name,
                "winner_avg": best_res.average_cost,
                "winner_time": best_res.average_runtime,
            })

    _print_scale_winner_table(winner_rows, "Customer Scaling — Winner at Each Size")
    return scale_data


def _run_battery_scaling(
    algos: list[tuple],
    data,
    ev_params,
    weights,
    seeds: list[int],
    max_evals: int,
) -> dict:
    """
    Hold customer set fixed (all 75) and vary battery capacity from 5 to 20 kWh.
    Lower capacity → more charging stops required → harder constraint regime.
    """
    CAPACITIES = [5, 8, 10, 12, 15, 18, 20]
    battery_data: dict = {}
    winner_rows: list[dict] = []

    for cap in CAPACITIES:
        new_params = EVParameters(
            battery_capacity_kwh=cap,
            initial_battery_kwh=cap,
            energy_consumption_kwh_per_km=ev_params.energy_consumption_kwh_per_km,
            average_speed_kmh=ev_params.average_speed_kmh,
            grade_factor=ev_params.grade_factor,
            speed_exponent=ev_params.speed_exponent,
        )
        print(f"\n  ── battery_capacity={cap} kWh ──")

        best_res = None
        for name, fn, kwargs in algos:
            res = run_experiments(
                fn, data, new_params, weights,
                seeds=seeds, algorithm_name=name, verbose=False,
                max_evaluations=max_evals, **kwargs,
            )
            feas_pct = res.feasible_run_count / max(1, len(seeds)) * 100
            print(
                f"    {name:<27}  time={res.average_runtime:5.1f}s"
                f"  F={res.average_cost:.4f}"
                f"  feasible={feas_pct:.0f}%"
            )
            if name not in battery_data:
                battery_data[name] = {
                    "capacities": [], "runtimes": [], "costs": [], "feasible_pct": [],
                }
            battery_data[name]["capacities"].append(cap)
            battery_data[name]["runtimes"].append(res.average_runtime)
            battery_data[name]["costs"].append(res.average_cost)
            battery_data[name]["feasible_pct"].append(feas_pct)
            if best_res is None or res.average_cost < best_res.average_cost:
                best_res = res

        if best_res is not None:
            winner_rows.append({
                "label": f"{cap} kWh",
                "winner": best_res.algorithm_name,
                "winner_avg": best_res.average_cost,
                "winner_time": best_res.average_runtime,
            })

    _print_scale_winner_table(winner_rows, "Battery Scaling — Winner at Each Capacity Level")
    return battery_data


def _save_scalability_csv(
    customer_data: dict,
    battery_data: dict,
    results_dir: Path,
) -> None:
    path = results_dir / "scalability_customer.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "algorithm", "n_customers", "avg_runtime_s", "avg_cost",
        ])
        writer.writeheader()
        for name, d in customer_data.items():
            for i, n in enumerate(d["sizes"]):
                writer.writerow({
                    "algorithm": name,
                    "n_customers": n,
                    "avg_runtime_s": f"{d['runtimes'][i]:.4f}",
                    "avg_cost": f"{d['costs'][i]:.4f}",
                })
    print(f"  Customer scaling CSV    -> {path}")

    path = results_dir / "scalability_battery.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "algorithm", "battery_capacity_kwh", "avg_runtime_s", "avg_cost", "feasible_pct",
        ])
        writer.writeheader()
        for name, d in battery_data.items():
            for i, cap in enumerate(d["capacities"]):
                writer.writerow({
                    "algorithm": name,
                    "battery_capacity_kwh": cap,
                    "avg_runtime_s": f"{d['runtimes'][i]:.4f}",
                    "avg_cost": f"{d['costs'][i]:.4f}",
                    "feasible_pct": f"{d['feasible_pct'][i]:.1f}",
                })
    print(f"  Battery scaling CSV     -> {path}")


def _save_optimality_gap_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "algorithm", "best_cost", "avg_cost",
            "gap_best_pct", "gap_avg_pct",
            "avg_runtime_s", "feasible_runs", "n_runs", "bks",
        ])
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "algorithm":     row["algorithm"],
                "best_cost":     f"{row['best_cost']:.6f}",
                "avg_cost":      f"{row['avg_cost']:.6f}",
                "gap_best_pct":  f"{row['gap_best_pct']:.4f}",
                "gap_avg_pct":   f"{row['gap_avg_pct']:.4f}",
                "avg_runtime_s": f"{row['avg_runtime_s']:.4f}",
                "feasible_runs": row["feasible_runs"],
                "n_runs":        row["n_runs"],
                "bks":           f"{row['bks']:.6f}",
            })
    print(f"  Optimality gap CSV      -> {path}")


def run_optimality_gap_analysis(
    all_results: list[ExperimentResults],
    figures_dir: Path,
    results_dir: Path,
) -> None:
    """
    Compute optimality gap vs BKS from the main-comparison results.

    BKS is the best solution found by any algorithm across all seeds.
    Reports gap_best (best cost vs BKS) and gap_avg (avg cost vs BKS),
    saves optimality_gap.csv, and plots optimality_gap.png.
    """
    if not all_results:
        print("  No results available for optimality gap analysis.")
        return

    _print_section("Optimality Gap Analysis")

    bks        = min(r.best_cost for r in all_results)
    total_runs = sum(len(r.seeds) for r in all_results)
    print(f"  BKS (Best-Known Solution) = {bks:.6f}")
    print(f"  (minimum best cost across all {total_runs} runs)\n")

    gap_rows: list[dict] = []
    for r in all_results:
        gap_best = (r.best_cost    - bks) / max(1e-10, bks) * 100
        gap_avg  = (r.average_cost - bks) / max(1e-10, bks) * 100
        gap_rows.append({
            "algorithm":     r.algorithm_name,
            "best_cost":     r.best_cost,
            "avg_cost":      r.average_cost,
            "gap_best_pct":  gap_best,
            "gap_avg_pct":   gap_avg,
            "avg_runtime_s": r.average_runtime,
            "feasible_runs": r.feasible_run_count,
            "n_runs":        len(r.seeds),
            "bks":           bks,
        })
        print(
            f"  {r.algorithm_name:<27}"
            f"  best={r.best_cost:>10.4f}  gap_best={gap_best:>6.2f}%"
            f"  avg={r.average_cost:>10.4f}  gap_avg={gap_avg:>7.2f}%"
            f"  feasible={r.feasible_run_count}/{len(r.seeds)}"
        )

    _save_optimality_gap_csv(gap_rows, results_dir / "optimality_gap.csv")
    plot_optimality_gap_comparison(
        gap_rows, figures_dir=figures_dir, show=False,
    )


def run_scalability_analysis(
    run_flags: dict[str, bool],
    data,
    ev_params,
    weights,
    sa_kwargs: dict,
    ga_kwargs: dict,
    ma_kwargs: dict,
    aco_kwargs: dict,
    figures_dir: Path,
    results_dir: Path,
) -> None:
    """
    Two-axis scalability study:

    Axis 1 — Customer count (25 / 50 / 75 / 100 / 150 / 200 / 300 / 400 / 500):
        Load each dedicated SF instance with real OSRM road distances.
        Shows how runtime and solution quality scale as the problem grows
        from small to large.

    Axis 2 — Battery capacity (5 / 8 / 10 / 12 / 15 / 18 / 20 kWh):
        Fix all 75 customers; reduce battery capacity toward 5 kWh.
        Tighter capacity forces more charging stops (harder constraint
        regime) and may make some algorithm seeds infeasible.
    """
    algos = _build_algo_list(run_flags, sa_kwargs, ga_kwargs, ma_kwargs, aco_kwargs)
    if not algos:
        print("  No metaheuristics selected — skipping scalability.")
        return

    SCALE_SEEDS = [0, 1, 2]
    SCALE_EVALS = 30_000

    _print_section(
        f"Scalability Axis 1 — Customer-Count Scaling  "
        f"({len(SCALE_SEEDS)} seeds, {SCALE_EVALS:,} evals/run)"
    )
    customer_data = _run_customer_scaling(
        algos, ev_params, weights, SCALE_SEEDS, SCALE_EVALS,
    )

    _print_section(
        f"Scalability Axis 2 — Battery Constraint Tightness  "
        f"({len(SCALE_SEEDS)} seeds, {SCALE_EVALS:,} evals/run)"
    )
    battery_data = _run_battery_scaling(
        algos, data, ev_params, weights, SCALE_SEEDS, SCALE_EVALS,
    )

    _print_section("Saving scalability output")
    _save_scalability_csv(customer_data, battery_data, results_dir)
    plot_scalability(
        customer_data, battery_data,
        figures_dir=figures_dir,
        show=False,
    )


# ---------------------------------------------------------------------------
# Results interpretation
# ---------------------------------------------------------------------------

def _print_interpretation(
    all_results: list[ExperimentResults],
    meta_results: list[ExperimentResults],
    max_evals: int,
    n_seeds: int,
) -> None:
    _print_section("Results Interpretation")

    if not meta_results:
        print("  (no metaheuristic results to interpret)")
        return

    ranked = sorted(meta_results, key=lambda r: r.average_cost)
    winner = ranked[0]

    print(f"\n  Evaluation budget: {max_evals:,} evals/run  |  Seeds: {n_seeds}")

    # Ranking table
    print("\n  Metaheuristic ranking (lower objective = better):")
    print(f"  {'Rank':<5} {'Algorithm':<27} {'Best':>10} {'Avg':>10} {'StdDev':>8}"
          f" {'Feasible':>9} {'Avg time':>9}")
    print("  " + "-" * 80)
    for rank, r in enumerate(ranked, 1):
        gap = (r.average_cost - winner.average_cost) / max(1e-10, winner.average_cost) * 100
        gap_str = f"  (+{gap:.1f}%)" if gap > 0.01 else "  (winner)"
        print(
            f"  {rank:<5} {r.algorithm_name:<27}"
            f" {r.best_cost:>10.4f}"
            f" {r.average_cost:>10.4f}"
            f" {r.std_cost:>8.4f}"
            f" {r.feasible_run_count:>6}/{n_seeds}"
            f" {r.average_runtime:>8.2f}s"
            f"{gap_str}"
        )

    # Cost component breakdown
    print("\n  Cost component decomposition (best run per algorithm):")
    print(f"  {'Algorithm':<27} {'Dist(km)':>10} {'Time(h)':>9} {'Energy(kWh)':>12}"
          f" {'Cost($)':>9} {'BattViol':>9}")
    print("  " + "-" * 82)
    for r in meta_results:
        ev = r.best_eval
        print(
            f"  {r.algorithm_name:<27}"
            f" {ev.total_distance_km:>9.1f}"
            f" {ev.total_travel_time_h + ev.total_charging_time_h:>9.2f}"
            f" {ev.total_energy_consumed_kwh:>11.2f}"
            f" {ev.total_charging_cost_usd:>8.2f}"
            f" {ev.battery_violation_kwh:>9.4f}"
        )

    # Improvement over greedy
    greedy = next((r for r in all_results if r.algorithm_name == "Greedy"), None)
    if greedy:
        print(f"\n  Improvement over Greedy baseline  (F_greedy avg = {greedy.average_cost:.4f}):")
        for r in meta_results:
            improv = (greedy.average_cost - r.average_cost) / max(1e-10, abs(greedy.average_cost)) * 100
            tag = "[better]" if improv > 0 else "[WORSE — check settings]"
            print(f"    {r.algorithm_name:<27}  {improv:>+6.1f}%  {tag}")

    # Speed comparison
    fastest = min(meta_results, key=lambda r: r.average_runtime)
    slowest = max(meta_results, key=lambda r: r.average_runtime)
    print(f"\n  Wall-clock speed (avg per single run, {max_evals:,} evals):")
    for r in meta_results:
        tag = "  <- fastest" if r is fastest else ("  <- slowest" if r is slowest else "")
        print(f"    {r.algorithm_name:<27}  avg {r.average_runtime:.2f}s{tag}")

    # Sanity checks
    print("\n  Automated checks:")
    if greedy and all(r.best_cost < greedy.best_cost for r in meta_results):
        print("  [OK] All metaheuristics beat Greedy — search adds genuine value over construction.")
    elif greedy:
        for r in meta_results:
            if r.best_cost >= greedy.best_cost:
                print(f"  [!!] {r.algorithm_name} did NOT beat Greedy — consider more seeds/iterations.")

    fully_feasible = [r for r in meta_results if r.feasible_run_count == len(r.seeds)]
    if len(fully_feasible) == len(meta_results):
        print("  [OK] All metaheuristics found feasible solutions on every seed.")
    else:
        for r in meta_results:
            if r.feasible_run_count < len(r.seeds):
                n_infeas = len(r.seeds) - r.feasible_run_count
                print(f"  [!!] {r.algorithm_name}: {n_infeas} seed(s) ended infeasible.")
    print()


# ---------------------------------------------------------------------------
# CSV output
# ---------------------------------------------------------------------------

def _save_results_per_seed_csv(all_results: list[ExperimentResults], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "algorithm", "seed", "cost", "feasible",
            "distance_km", "travel_time_h", "charging_time_h",
            "energy_kwh", "charging_cost_usd", "battery_violation_kwh",
            "infeasible_visits", "runtime_s",
        ])
        writer.writeheader()
        for r in all_results:
            for i, seed in enumerate(r.seeds):
                ev = r.best_evals[i]
                writer.writerow({
                    "algorithm":             r.algorithm_name,
                    "seed":                  seed,
                    "cost":                  f"{r.best_costs[i]:.6f}",
                    "feasible":              ev.feasible,
                    "distance_km":           f"{ev.total_distance_km:.4f}",
                    "travel_time_h":         f"{ev.total_travel_time_h:.4f}",
                    "charging_time_h":       f"{ev.total_charging_time_h:.4f}",
                    "energy_kwh":            f"{ev.total_energy_consumed_kwh:.4f}",
                    "charging_cost_usd":     f"{ev.total_charging_cost_usd:.4f}",
                    "battery_violation_kwh": f"{ev.battery_violation_kwh:.6f}",
                    "infeasible_visits":     ev.infeasible_visits,
                    "runtime_s":             f"{r.runtimes[i]:.4f}",
                })
    print(f"  Per-seed CSV            -> {path}")


def _save_results_summary_csv(all_results: list[ExperimentResults], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "algorithm", "best", "average", "worst", "std_dev",
            "feasible_runs", "n_runs", "avg_runtime_s",
        ])
        writer.writeheader()
        for r in all_results:
            writer.writerow({
                "algorithm":    r.algorithm_name,
                "best":         f"{r.best_cost:.6f}",
                "average":      f"{r.average_cost:.6f}",
                "worst":        f"{r.worst_cost:.6f}",
                "std_dev":      f"{r.std_cost:.6f}",
                "feasible_runs": r.feasible_run_count,
                "n_runs":        len(r.seeds),
                "avg_runtime_s": f"{r.average_runtime:.4f}",
            })
    print(f"  Summary CSV             -> {path}")


def _save_algorithm_diagnostics_csv(all_results: list[ExperimentResults], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "algorithm", "n_seeds",
        "mean_total_evaluations",
        "mean_sa_acceptance_rate", "mean_sa_feasibility_rate", "mean_sa_reheat_count",
        "mean_ga_generations", "mean_aco_iterations",
    ]

    def _mean(vals):
        vals = [v for v in vals if v is not None]
        return f"{sum(vals) / len(vals):.6f}" if vals else ""

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in all_results:
            sl = r.all_stats
            evals = [getattr(s, "total_evaluated", None) for s in sl]
            writer.writerow({
                "algorithm":                r.algorithm_name,
                "n_seeds":                  len(r.seeds),
                "mean_total_evaluations":   _mean(evals),
                "mean_sa_acceptance_rate":  _mean([getattr(s, "acceptance_rate",   None) for s in sl]),
                "mean_sa_feasibility_rate": _mean([getattr(s, "feasibility_rate",  None) for s in sl]),
                "mean_sa_reheat_count":     _mean([getattr(s, "reheat_count",      None) for s in sl]),
                "mean_ga_generations":      _mean([getattr(s, "total_generations", None) for s in sl]),
                "mean_aco_iterations":      _mean([getattr(s, "total_iterations",  None) for s in sl]),
            })
    print(f"  Algorithm diagnostics   -> {path}")


# ---------------------------------------------------------------------------
# Run manifest
# ---------------------------------------------------------------------------

def _save_run_manifest(
    results_dir: Path,
    n_seeds: int,
    max_evals: int,
    sa_kwargs: dict,
    ga_kwargs: dict,
    ma_kwargs: dict,
    aco_kwargs: dict,
    weights,
    run_sensitivity: bool,
    instance: str,
    focus_mode: str = "balanced",
) -> None:
    import datetime as _dt
    try:
        import yaml as _yaml
    except ImportError:
        print("  (yaml not available — skipping run manifest)")
        return

    manifest: dict = {
        "generated_at":    _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "instance":        instance,
        "focus_mode":      focus_mode,
        "n_seeds":         n_seeds,
        "max_evaluations": max_evals,
        "run_sensitivity": run_sensitivity,
        "algorithm_hyperparameters": {
            "SA":  sa_kwargs,
            "GA":  ga_kwargs,
            "MA":  ma_kwargs,
            "ACO": aco_kwargs,
        },
        "objective_weights": {
            "distance_weight":          weights.distance_weight,
            "travel_time_weight":       weights.travel_time_weight,
            "energy_weight":            weights.energy_weight,
            "charging_cost_weight":     weights.charging_cost_weight,
            "battery_violation_weight": weights.battery_violation_weight,
            "infeasible_visit_weight":  weights.infeasible_visit_weight,
        },
    }
    path = results_dir / "run_manifest.yaml"
    with open(path, "w", encoding="utf-8") as f:
        _yaml.safe_dump(manifest, f, sort_keys=False, default_flow_style=False)
    print(f"  Run manifest            -> {path}")


# ---------------------------------------------------------------------------
# Summary markdown
# ---------------------------------------------------------------------------

def _save_summary_md(
    all_results: list[ExperimentResults],
    meta_results: list[ExperimentResults],
    n_seeds: int,
    max_evals: int,
    run_sensitivity: bool,
    results_dir: Path,
    instance: str,
) -> None:
    import datetime as _dt

    lines: list[str] = []

    def h(text, level=2):
        if lines and lines[-1] != "":
            lines.append("")
        lines.append(f"{'#' * level} {text}")
        lines.append("")

    def p(text=""):
        lines.append(text)

    now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    h("EV Routing — Experiment Summary", level=1)
    p(f"_Generated: {now}_")
    p()

    h("Setup")
    p("| Parameter | Value |")
    p("|---|---|")
    p(f"| Instance | **{instance}** (75 customers, 30 charging stations, 1 depot) |")
    p(f"| Seeds per algorithm | {n_seeds} |")
    p(f"| Evaluation budget | {max_evals:,} per run |")
    p(f"| Sensitivity analysis | {'Run' if run_sensitivity else 'Skipped — use `--sensitivity` to enable'} |")
    p()

    if all_results:
        h("Main Results — Multi-Seed Comparison")
        p(f"Sorted by average objective — lower is better.  Budget: {max_evals:,} evals, {n_seeds} seeds.")
        p()
        p("| Algorithm | Best | Avg | Worst | Std | Feasible | Avg Time |")
        p("|---|---|---|---|---|---|---|")
        for r in sorted(all_results, key=lambda r: r.average_cost):
            p(f"| {r.algorithm_name} "
              f"| {r.best_cost:.4f} "
              f"| {r.average_cost:.4f} "
              f"| {r.worst_cost:.4f} "
              f"| {r.std_cost:.4f} "
              f"| {r.feasible_run_count}/{len(r.seeds)} "
              f"| {r.average_runtime:.2f}s |")
        p()

        greedy = next((r for r in all_results if r.algorithm_name == "Greedy"), None)
        if greedy and meta_results:
            winner = min(meta_results, key=lambda r: r.average_cost)
            h("Winner and Baseline Comparison")
            p(f"**{winner.algorithm_name}** achieved the best average objective = "
              f"**{winner.average_cost:.4f}** (best seed: {winner.best_cost:.4f}).")
            p()
            p("Improvement over Greedy baseline:")
            for r in meta_results:
                improv = (greedy.average_cost - r.average_cost) / max(1e-10, abs(greedy.average_cost)) * 100
                p(f"- **{r.algorithm_name}**: {improv:+.2f}% "
                  f"(avg {r.average_cost:.4f} vs Greedy {greedy.average_cost:.4f})")
            p()

    h("Sensitivity Analysis")
    if run_sensitivity:
        p("Sensitivity sweeps saved to:")
        p("- `sensitivity_sa.csv`  — SA: T₀ and cooling-rate sweeps")
        p("- `sensitivity_ga.csv`  — GA: population-size and crossover-rate sweeps")
        p("- `sensitivity_ma.csv`  — MA: population-size and local-search-iters sweeps")
        p("- `sensitivity_aco.csv` — ACO: α and β sweeps")
        p()
        p("**What sensitivity analysis tells you:** each sweep holds all parameters fixed except one")
        p("and measures how the average objective changes across the parameter range.")
        p("A flat curve = robust (chosen value is fine anywhere in the range).")
        p("A steep curve = sensitive — the thesis should justify the chosen value.")
    else:
        p("Skipped. Run with `--sensitivity` to sweep hyperparameters and confirm robustness.")
    p()

    h("Output Files")
    p("| File | Contents |")
    p("|---|---|")
    p("| `results_per_seed.csv` | Raw per-seed costs and route metrics |")
    p("| `results_summary.csv` | Per-algorithm aggregated statistics |")
    p("| `algorithm_diagnostics.csv` | SA/GA/MA/ACO internal search diagnostics |")
    p("| `run_manifest.yaml` | Full parameter snapshot of this run |")
    p("| `run_log.txt` | Complete console output |")
    p("| `figures/` | All convergence, box, diagnostic, and breakdown plots |")
    p("| `figures/sensitivity/` | Parameter sensitivity errorbar plots |")
    p()

    path = results_dir / "summary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  Summary markdown        -> {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    global RESULTS_DIR, FIGURES_DIR

    args             = parse_args()
    run_flags        = _resolve_algorithms(args.algorithms)
    n_seeds          = args.seeds if args.seeds is not None else 10
    seeds            = list(range(n_seeds))
    run_sensitivity  = args.sensitivity
    run_scalability  = args.scalability
    run_opt_gap      = args.opt_gap
    verbose          = args.verbose
    mode             = args.mode

    # Non-balanced modes get their own results directory; weights.json and
    # params.json are always read from the base (balanced) instance directory.
    if mode != "balanced":
        RESULTS_DIR = Path(f"EV_routing/results/{INSTANCE}_{mode}")
        FIGURES_DIR = RESULTS_DIR / "figures"

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    log_path = _install_console_log(RESULTS_DIR)
    print(f"Console log -> {log_path}")

    # ------------------------------------------------------------------
    # Problem setup
    # ------------------------------------------------------------------
    ev_params = EVParameters(
        battery_capacity_kwh=20.0,
        initial_battery_kwh=20.0,
        energy_consumption_kwh_per_km=0.50,
        average_speed_kmh=50.0,
        grade_factor=3.0,
        speed_exponent=2.0,
    )

    data = load_problem_data(INSTANCE_DIR, ev_params)

    _weights_file = Path(f"EV_routing/results/{INSTANCE}") / "weights.json"
    if _weights_file.exists():
        _w = json.loads(_weights_file.read_text())["weights"]
        weights = ObjectiveWeights(**_w)
        print(f"Weights loaded from {_weights_file}")
    else:
        print("No weights.json found — using defaults. Run scripts/calibrate_weights.py first.")
        weights = ObjectiveWeights(
            distance_weight=1.0,
            travel_time_weight=10.0,
            energy_weight=2.0,
            charging_cost_weight=20.0,
            battery_violation_weight=10000.0,
            infeasible_visit_weight=5000.0,
        )

    _mult = FOCUS_MODES[mode]
    weights.distance_weight      *= _mult["distance"]
    weights.travel_time_weight   *= _mult["time"]
    weights.energy_weight        *= _mult["energy"]
    weights.charging_cost_weight *= _mult["charging_cost"]
    print(f"Focus mode '{mode}': multipliers {_mult}")
    if mode != "balanced":
        print(f"Results directory: {RESULTS_DIR}")

    # ------------------------------------------------------------------
    # Load hyperparameters from params.json
    # ------------------------------------------------------------------
    if not PARAMS_FILE.exists():
        raise FileNotFoundError(
            f"No params.json at {PARAMS_FILE}. "
            "Run: PYTHONPATH=EV_routing python EV_routing/scripts/tune.py"
        )
    with open(PARAMS_FILE) as _f:
        _p = json.load(_f)

    sa_kwargs  = _p["SA"]
    ga_kwargs  = _p["GA"]
    ma_kwargs  = _p["MA"]
    aco_kwargs = _p["ACO"]

    # ------------------------------------------------------------------
    # Sensitivity analysis (--sensitivity flag)
    # ------------------------------------------------------------------
    SENS_SEEDS = [0, 1, 2]
    SENS_EVALS = 30_000
    SENS_FIGS  = FIGURES_DIR / "sensitivity"

    if run_sensitivity:
        _print_section(
            f"Sensitivity Analysis — {len(SENS_SEEDS)} seeds, {SENS_EVALS:,} evals/run"
        )

        if run_flags["SA"]:
            run_sa_sensitivity(
                data, ev_params, weights, sa_kwargs,
                sweep_cfg={
                    "temperatures":  [0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
                    "cooling_rates": [0.980, 0.985, 0.990, 0.993, 0.995, 0.997],
                    "max_evals":     SENS_EVALS,
                },
                figures_dir=SENS_FIGS, results_dir=RESULTS_DIR,
                seeds=SENS_SEEDS,
            )

        if run_flags["GA"]:
            run_ga_sensitivity(
                data, ev_params, weights, ga_kwargs,
                sweep_cfg={
                    "population_sizes": [50, 100, 150, 200, 300],
                    "crossover_rates":  [0.50, 0.60, 0.70, 0.80, 0.85, 0.90],
                    "max_evals":        SENS_EVALS,
                },
                figures_dir=SENS_FIGS, results_dir=RESULTS_DIR,
                seeds=SENS_SEEDS,
            )

        if run_flags["MA"]:
            run_ma_sensitivity(
                data, ev_params, weights, ma_kwargs,
                sweep_cfg={
                    "population_sizes":  [15, 25, 40, 60, 80],
                    "local_search_iters": [1, 3, 5, 7, 10],
                    "max_evals":         SENS_EVALS,
                },
                figures_dir=SENS_FIGS, results_dir=RESULTS_DIR,
                seeds=SENS_SEEDS,
            )

        if run_flags["ACO"]:
            run_aco_sensitivity(
                data, ev_params, weights, aco_kwargs,
                sweep_cfg={
                    "alphas":    [0.1, 0.5, 1.0, 1.5, 2.0, 3.0],
                    "betas":     [2.0, 4.0, 5.0, 6.0, 7.0, 8.0],
                    "max_evals": SENS_EVALS,
                },
                figures_dir=SENS_FIGS, results_dir=RESULTS_DIR,
                seeds=SENS_SEEDS,
            )

    # ------------------------------------------------------------------
    # Scalability analysis (--scalability flag)
    # ------------------------------------------------------------------
    if run_scalability:
        run_scalability_analysis(
            run_flags=run_flags,
            data=data,
            ev_params=ev_params,
            weights=weights,
            sa_kwargs=sa_kwargs,
            ga_kwargs=ga_kwargs,
            ma_kwargs=ma_kwargs,
            aco_kwargs=aco_kwargs,
            figures_dir=FIGURES_DIR,
            results_dir=RESULTS_DIR,
        )

    # ------------------------------------------------------------------
    # Single diagnostic runs
    # ------------------------------------------------------------------
    if run_flags["SA"]:
        _print_section("Single SA run — diagnostics")
        t0 = time.perf_counter()
        _, best_ev, sa_stats = simulated_annealing(
            data=data, ev_params=ev_params, weights=weights,
            max_evaluations=MAX_EVALS, **sa_kwargs,
        )
        elapsed = time.perf_counter() - t0
        print(f"  Feasible:            {best_ev.feasible}")
        print(f"  Objective:           {best_ev.objective_value:.4f}")
        print(f"  Distance (km):       {best_ev.total_distance_km:.2f}")
        print(f"  Travel time (h):     {best_ev.total_travel_time_h:.2f}")
        print(f"  Charging time (h):   {best_ev.total_charging_time_h:.2f}")
        print(f"  Energy (kWh):        {best_ev.total_energy_consumed_kwh:.2f}")
        print(f"  Charging cost ($):   {best_ev.total_charging_cost_usd:.2f}")
        print(f"  Battery violation:   {best_ev.battery_violation_kwh:.4f}")
        print(f"  Infeasible visits:   {best_ev.infeasible_visits}")
        print(f"  Evaluations:         {sa_stats.total_evaluated:,}")
        print(f"  Acceptance rate:     {sa_stats.acceptance_rate:.2%}")
        print(f"  Feasibility rate:    {sa_stats.feasibility_rate:.2%}")
        print(f"  Reheats:             {sa_stats.reheat_count}")
        print(f"  Runtime:             {elapsed:.2f}s")

    if run_flags["GA"]:
        _print_section("Single GA run — diagnostics")
        t0 = time.perf_counter()
        _, best_ev_ga, ga_stats = genetic_algorithm(
            data=data, ev_params=ev_params, weights=weights,
            max_evaluations=MAX_EVALS, **ga_kwargs,
        )
        elapsed = time.perf_counter() - t0
        print(f"  Feasible:            {best_ev_ga.feasible}")
        print(f"  Objective:           {best_ev_ga.objective_value:.4f}")
        print(f"  Distance (km):       {best_ev_ga.total_distance_km:.2f}")
        print(f"  Travel time (h):     {best_ev_ga.total_travel_time_h:.2f}")
        print(f"  Charging time (h):   {best_ev_ga.total_charging_time_h:.2f}")
        print(f"  Energy (kWh):        {best_ev_ga.total_energy_consumed_kwh:.2f}")
        print(f"  Charging cost ($):   {best_ev_ga.total_charging_cost_usd:.2f}")
        print(f"  Battery violation:   {best_ev_ga.battery_violation_kwh:.4f}")
        print(f"  Infeasible visits:   {best_ev_ga.infeasible_visits}")
        print(f"  Evaluations:         {ga_stats.total_evaluated:,}")
        print(f"  Generations:         {ga_stats.total_generations:,}")
        print(f"  Feasibility rate:    {ga_stats.feasibility_rate:.2%}")
        print(f"  Runtime:             {elapsed:.2f}s")

    if run_flags["MA"]:
        _print_section("Single MA run — diagnostics")
        t0 = time.perf_counter()
        _, best_ev_ma, ma_stats = genetic_algorithm(
            data=data, ev_params=ev_params, weights=weights,
            max_evaluations=MAX_EVALS, **ma_kwargs,
        )
        elapsed = time.perf_counter() - t0
        print(f"  Feasible:            {best_ev_ma.feasible}")
        print(f"  Objective:           {best_ev_ma.objective_value:.4f}")
        print(f"  Distance (km):       {best_ev_ma.total_distance_km:.2f}")
        print(f"  Travel time (h):     {best_ev_ma.total_travel_time_h:.2f}")
        print(f"  Charging time (h):   {best_ev_ma.total_charging_time_h:.2f}")
        print(f"  Energy (kWh):        {best_ev_ma.total_energy_consumed_kwh:.2f}")
        print(f"  Charging cost ($):   {best_ev_ma.total_charging_cost_usd:.2f}")
        print(f"  Battery violation:   {best_ev_ma.battery_violation_kwh:.4f}")
        print(f"  Infeasible visits:   {best_ev_ma.infeasible_visits}")
        print(f"  Evaluations:         {ma_stats.total_evaluated:,}")
        print(f"  Generations:         {ma_stats.total_generations:,}")
        print(f"  Feasibility rate:    {ma_stats.feasibility_rate:.2%}")
        print(f"  Runtime:             {elapsed:.2f}s")

    if run_flags["ACO"]:
        _print_section("Single ACO run — diagnostics")
        t0 = time.perf_counter()
        _, best_ev_aco, aco_stats = ant_colony_optimization(
            data=data, ev_params=ev_params, weights=weights,
            max_evaluations=MAX_EVALS, **aco_kwargs,
        )
        elapsed = time.perf_counter() - t0
        print(f"  Feasible:            {best_ev_aco.feasible}")
        print(f"  Objective:           {best_ev_aco.objective_value:.4f}")
        print(f"  Distance (km):       {best_ev_aco.total_distance_km:.2f}")
        print(f"  Travel time (h):     {best_ev_aco.total_travel_time_h:.2f}")
        print(f"  Charging time (h):   {best_ev_aco.total_charging_time_h:.2f}")
        print(f"  Energy (kWh):        {best_ev_aco.total_energy_consumed_kwh:.2f}")
        print(f"  Charging cost ($):   {best_ev_aco.total_charging_cost_usd:.2f}")
        print(f"  Battery violation:   {best_ev_aco.battery_violation_kwh:.4f}")
        print(f"  Infeasible visits:   {best_ev_aco.infeasible_visits}")
        print(f"  Evaluations:         {aco_stats.total_evaluated:,}")
        print(f"  Iterations:          {aco_stats.total_iterations:,}")
        print(f"  Feasibility rate:    {aco_stats.feasibility_rate:.2%}")
        print(f"  Runtime:             {elapsed:.2f}s")

    if run_flags["Greedy"]:
        _print_section("Single Greedy run — baseline")
        t0 = time.perf_counter()
        _, best_ev_greedy, _ = greedy_nearest_neighbor(data=data, ev_params=ev_params, weights=weights)
        elapsed = time.perf_counter() - t0
        print(f"  Feasible:            {best_ev_greedy.feasible}")
        print(f"  Objective:           {best_ev_greedy.objective_value:.4f}")
        print(f"  Distance (km):       {best_ev_greedy.total_distance_km:.2f}")
        print(f"  Travel time (h):     {best_ev_greedy.total_travel_time_h:.2f}")
        print(f"  Charging time (h):   {best_ev_greedy.total_charging_time_h:.2f}")
        print(f"  Energy (kWh):        {best_ev_greedy.total_energy_consumed_kwh:.2f}")
        print(f"  Charging cost ($):   {best_ev_greedy.total_charging_cost_usd:.2f}")
        print(f"  Battery violation:   {best_ev_greedy.battery_violation_kwh:.4f}")
        print(f"  Infeasible visits:   {best_ev_greedy.infeasible_visits}")
        print(f"  Runtime:             {elapsed:.2f}s")

    # ------------------------------------------------------------------
    # Controlled multi-seed comparison
    # ------------------------------------------------------------------
    _print_section(f"Controlled comparison — {n_seeds} seeds, budget={MAX_EVALS:,} evals")

    algorithms_to_run: dict = {}
    algo_kwargs: dict = {}

    if run_flags["Greedy"]:
        algorithms_to_run["Greedy"]              = greedy_nearest_neighbor
        algo_kwargs["Greedy"]                    = {}
    if run_flags["SA"]:
        algorithms_to_run["Simulated Annealing"] = simulated_annealing
        algo_kwargs["Simulated Annealing"]       = sa_kwargs
    if run_flags["GA"]:
        algorithms_to_run["Genetic Algorithm"]   = genetic_algorithm
        algo_kwargs["Genetic Algorithm"]         = ga_kwargs
    if run_flags["MA"]:
        algorithms_to_run["Memetic Algorithm"]   = genetic_algorithm
        algo_kwargs["Memetic Algorithm"]         = ma_kwargs
    if run_flags["ACO"]:
        algorithms_to_run["ACO"]                 = ant_colony_optimization
        algo_kwargs["ACO"]                       = aco_kwargs

    all_results = run_controlled_comparison(
        algorithms=algorithms_to_run,
        data=data,
        ev_params=ev_params,
        weights=weights,
        seeds=seeds,
        max_evaluations=MAX_EVALS,
        verbose=verbose,
        algorithm_kwargs=algo_kwargs,
    )

    _name_map    = {r.algorithm_name: r for r in all_results}
    meta_names   = ["Simulated Annealing", "Genetic Algorithm", "Memetic Algorithm", "ACO"]
    meta_results = [r for r in all_results if r.algorithm_name in meta_names]

    sa_results     = _name_map.get("Simulated Annealing")
    ga_results     = _name_map.get("Genetic Algorithm")
    ma_results     = _name_map.get("Memetic Algorithm")
    aco_results    = _name_map.get("ACO")
    greedy_results = _name_map.get("Greedy")

    # ------------------------------------------------------------------
    # Print comparison tables
    # ------------------------------------------------------------------
    print()
    print_comparison_table(all_results)
    print()
    print_detailed_metrics(all_results)
    print()
    print_summary_table(all_results)

    wilcoxon_tests = pairwise_wilcoxon(all_results)
    print_wilcoxon_table(wilcoxon_tests)

    print("LaTeX table:")
    print(to_latex_table(all_results))
    print()

    # ------------------------------------------------------------------
    # Results interpretation
    # ------------------------------------------------------------------
    _print_interpretation(all_results, meta_results, MAX_EVALS, n_seeds)

    # ------------------------------------------------------------------
    # Figures
    # ------------------------------------------------------------------
    _print_section("Saving figures")

    algo_plot_pairs  = [
        (sa_results,  "sa"),
        (ga_results,  "ga"),
        (ma_results,  "ma"),
        (aco_results, "aco"),
    ]
    active_pairs = [(r, tag) for r, tag in algo_plot_pairs if r is not None]

    for res, tag in active_pairs:
        plot_convergence(
            res,
            title=f"{res.algorithm_name} — Convergence ({n_seeds} seeds)",
            save_path=FIGURES_DIR / f"{tag}_convergence_by_step.png",
            show=False,
        )

    if len(active_pairs) > 1:
        plot_convergence_by_evaluations(
            [r for r, _ in active_pairs],
            title=f"Convergence by objective evaluations (budget = {MAX_EVALS:,})",
            save_path=FIGURES_DIR / "convergence_by_evaluations.png",
            show=False,
        )

    plot_box_comparison(
        all_results,
        title=f"Solution quality distribution — {n_seeds} seeds, budget={MAX_EVALS:,} evals",
        save_path=FIGURES_DIR / "box_comparison.png",
        show=False,
    )

    if sa_results:
        plot_sa_diagnostics(
            sa_results, seed_idx=sa_results.best_run_index,
            title=f"SA diagnostics — best seed ({sa_results.best_seed})",
            save_path=FIGURES_DIR / "sa_diagnostics.png", show=False,
        )

    if ga_results:
        plot_ga_diagnostics(
            ga_results, seed_idx=ga_results.best_run_index,
            title=f"GA diagnostics — best seed ({ga_results.best_seed})",
            save_path=FIGURES_DIR / "ga_diagnostics.png", show=False,
        )

    if ma_results:
        plot_ga_diagnostics(
            ma_results, seed_idx=ma_results.best_run_index,
            title=f"MA diagnostics — best seed ({ma_results.best_seed})",
            save_path=FIGURES_DIR / "ma_diagnostics.png", show=False,
        )

    if aco_results:
        plot_aco_diagnostics(
            aco_results, seed_idx=aco_results.best_run_index,
            title=f"ACO diagnostics — best seed ({aco_results.best_seed})",
            save_path=FIGURES_DIR / "aco_diagnostics.png", show=False,
        )

    plot_cost_breakdown(
        all_results,
        title="Cost component breakdown (best solution per algorithm)",
        save_path=FIGURES_DIR / "cost_breakdown.png", show=False,
    )

    plot_runtime_comparison(
        all_results,
        title=f"Runtime comparison — {n_seeds} seeds, budget={MAX_EVALS:,} evals",
        save_path=FIGURES_DIR / "runtime_comparison.png", show=False,
    )

    # ------------------------------------------------------------------
    # CSV output, manifest, summary
    # ------------------------------------------------------------------
    _print_section("Saving CSV output and metadata")

    _save_results_per_seed_csv(all_results,  RESULTS_DIR / "results_per_seed.csv")
    _save_results_summary_csv(all_results,   RESULTS_DIR / "results_summary.csv")
    _save_algorithm_diagnostics_csv(all_results, RESULTS_DIR / "algorithm_diagnostics.csv")
    _save_run_manifest(
        RESULTS_DIR, n_seeds, MAX_EVALS,
        sa_kwargs, ga_kwargs, ma_kwargs, aco_kwargs,
        weights, run_sensitivity, INSTANCE,
        focus_mode=mode,
    )
    _save_summary_md(
        all_results, meta_results, n_seeds, MAX_EVALS,
        run_sensitivity, RESULTS_DIR, INSTANCE,
    )

    # ------------------------------------------------------------------
    # Optimality gap analysis (--opt-gap flag)
    # ------------------------------------------------------------------
    if run_opt_gap:
        run_optimality_gap_analysis(all_results, FIGURES_DIR, RESULTS_DIR)

    print()
    print(f"All figures saved to {FIGURES_DIR}/")
    if greedy_results:
        print(f"Greedy best:              {greedy_results.best_solution}")
    if sa_results:
        print(f"SA  best (seed {sa_results.best_seed}):  {sa_results.best_solution}")
    if ga_results:
        print(f"GA  best (seed {ga_results.best_seed}):  {ga_results.best_solution}")
    if ma_results:
        print(f"MA  best (seed {ma_results.best_seed}):  {ma_results.best_solution}")
    if aco_results:
        print(f"ACO best (seed {aco_results.best_seed}): {aco_results.best_solution}")


if __name__ == "__main__":
    main()
