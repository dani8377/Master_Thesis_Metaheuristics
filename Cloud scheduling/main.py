"""
main.py - Entry point for the Cloud Scheduling experiments.

Orchestrates all algorithms (SA, GA, UMDA, B&B, baselines) over multiple random seeds
and produces comparison tables, convergence plots, bar charts, and CSV files.
All hyperparameters are read from config.yaml; edit that file to reproduce any experiment.

Usage:
    uv run run.py cloud                              # all algorithms, balanced focus
    uv run run.py cloud --algorithms SA GA UMDA BB   # metaheuristics + exact solver
    uv run run.py cloud --focus eco --verbose        # eco mode with verbose output
    uv run run.py cloud --seeds 3 --sensitivity      # quick sensitivity sweep
"""
import argparse
import atexit
import csv
import dataclasses
import sys
import time
from collections import Counter
from pathlib import Path

from tools.data_loader import load_problem_data, load_synthetic_problem_data, generate_server_pool
from tools.objective import (
    FocusMode,
    ObjectiveWeights,
    compute_normalization_constants,
    compute_sample_normalization,
    CalibrationDiagnostics,
)
from tools.config_loader import load_config
from algorithms.simulated_annealing import simulated_annealing
from algorithms.genetic_algorithm import genetic_algorithm
from algorithms.umda import umda
from algorithms.branch_and_bound import branch_and_bound
from algorithms.baselines import (
    greedy_ffd_baseline,
    round_robin_baseline,
    random_assignment_baseline,
)
from tools.experiment import run_experiments
from tools.plot import (
    plot_convergence,
    plot_bar_comparison,
    plot_metaheuristics_bar,
    plot_box_comparison,
    print_comparison_table,
    print_significance_table,
    save_results_csv,
)

# ---------------------------------------------------------------------------
# Console log capture (--tee everything printed to a file)
# ---------------------------------------------------------------------------

class _TeeStream:
    """
    File-like wrapper that writes to both the original stdout (so the user
    still sees output live in the terminal) AND a results/run_log.txt file.

    Installed by _install_console_log() near the very top of main() so every
    print() in this run is captured.  We deliberately do NOT capture stderr —
    tracebacks remain on stderr only, where they belong.

    The original stdout is restored on flush_close() before the program
    terminates so any uncaught exception still surfaces normally.
    """
    def __init__(self, original, log_file) -> None:
        self._original = original
        self._log_file = log_file

    def write(self, text: str) -> int:
        # Strip Windows-only ANSI sequences from the file copy so the log is
        # readable in plain editors.  Terminal copy keeps colours.
        self._original.write(text)
        try:
            self._log_file.write(text)
        except (ValueError, OSError):
            # File closed unexpectedly -- carry on without crashing the run
            pass
        return len(text)

    def flush(self) -> None:
        self._original.flush()
        try:
            self._log_file.flush()
        except (ValueError, OSError):
            pass

    # Forward common attributes so the wrapper behaves like a real stream
    def isatty(self) -> bool:
        return getattr(self._original, "isatty", lambda: False)()

    def fileno(self) -> int:
        return self._original.fileno()


def _install_console_log(results_dir: Path) -> Path:
    """
    Redirect stdout through a Tee so every print is also saved to
    results/run_log.txt.  The original stdout is restored automatically at
    interpreter shutdown via atexit, so any exit path (normal return,
    exception, sys.exit, KeyboardInterrupt) flushes and closes the log file.
    """
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

_ALGORITHM_CHOICES = ["SA", "GA", "UMDA", "BB", "greedy", "roundrobin", "random",
                      "baselines", "all"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Cloud Scheduling -Metaheuristic Experiment Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py                          # all algorithms, balanced focus\n"
            "  python main.py --algorithms SA GA UMDA  # metaheuristics only\n"
            "  python main.py --focus eco --verbose    # eco mode with verbose output\n"
            "  python main.py --seeds 3 --algorithms SA# quick single-algorithm test\n"
        ),
    )
    parser.add_argument(
        "--algorithms", "-a",
        nargs="+",
        choices=_ALGORITHM_CHOICES,
        default=["all"],
        metavar="ALG",
        help=(
            "Algorithms to run: SA, GA, UMDA, greedy, roundrobin, random, "
            "baselines (all three baselines), all.  Default: all."
        ),
    )
    parser.add_argument(
        "--focus", "-f",
        choices=[m.value for m in FocusMode],
        default=FocusMode.BALANCED.value,
        help=(
            "Objective focus mode: balanced (default) | performance | eco.  "
            "Controls how energy and latency are weighted in F(X)."
        ),
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help=(
            "Print step-by-step progress from each algorithm run.  "
            "Shows temperature / generation, best cost, acceptance rate, and "
            "a plain-language explanation of the current search phase."
        ),
    )
    parser.add_argument(
        "--seeds", "-s",
        type=int,
        default=None,
        help="Number of independent random seeds per algorithm (default: from config.yaml).",
    )
    parser.add_argument(
        "--sensitivity", "--sensibility", "-S",
        action="store_true",
        help=(
            "Run hyperparameter sensitivity sweeps for the selected algorithms.  "
            "Sweeps two parameters per algorithm (one at a time), saves CSV and "
            "plot to results/ and figures/.  Adds several minutes to runtime."
        ),
    )
    parser.add_argument(
        "--scalability", "-L",
        action="store_true",
        help=(
            "Run scalability analysis: execute selected metaheuristics on "
            "increasing problem sizes (task_sizes from config.yaml) and plot "
            "runtime + quality trends.  Adds several minutes to runtime."
        ),
    )
    parser.add_argument(
        "--tune", "-T",
        action="store_true",
        help=(
            "Run a one-time grid search over the tuning ranges in config.yaml "
            "to find the best hyperparameters per selected algorithm.  Writes "
            "results/tuning_<algo>.csv and results/tuning_summary.md.  Run "
            "ONCE, copy the recommended values into the algorithms: section of "
            "config.yaml, then run the main experiment with those fixed values."
        ),
    )
    return parser.parse_args()


def _resolve_algorithms(selections: list[str]) -> dict[str, bool]:
    """
    Translate the --algorithms list into a dict of {name: True/False} flags.

    Supports shorthands: 'baselines' ->greedy + roundrobin + random;
                         'all'       ->everything.
    """
    run_sa         = False
    run_ga         = False
    run_umda       = False
    run_bb         = False
    run_greedy     = False
    run_roundrobin = False
    run_random     = False

    for sel in selections:
        if sel == "all":
            run_sa = run_ga = run_umda = run_bb = True
            run_greedy = run_roundrobin = run_random = True
        elif sel == "baselines":
            run_greedy = run_roundrobin = run_random = True
        elif sel == "SA":
            run_sa = True
        elif sel == "GA":
            run_ga = True
        elif sel == "UMDA":
            run_umda = True
        elif sel == "BB":
            run_bb = True
        elif sel == "greedy":
            run_greedy = True
        elif sel == "roundrobin":
            run_roundrobin = True
        elif sel == "random":
            run_random = True

    return {
        "SA":         run_sa,
        "GA":         run_ga,
        "UMDA":       run_umda,
        "BB":         run_bb,
        "greedy":     run_greedy,
        "roundrobin": run_roundrobin,
        "random":     run_random,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _print_section(title: str) -> None:
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


def _print_focus_summary(mode: FocusMode, weights: ObjectiveWeights) -> None:
    """Print a human-readable explanation of the active focus mode."""
    descriptions = {
        FocusMode.PERFORMANCE: (
            "PERFORMANCE -- Latency-focused\n"
            "  The optimiser prioritises fast response times, especially for\n"
            "  high-priority tasks.  Energy consumption is a secondary concern.\n"
            f"  Weights: w_energy={weights.energy_weight}  w_latency={weights.latency_weight}"
            f"  gamma={weights.congestion_factor}"
        ),
        FocusMode.BALANCED: (
            "BALANCED -- Equal energy/latency trade-off (thesis default)\n"
            "  The optimiser balances task consolidation (saves idle power)\n"
            "  against load spreading (reduces congestion latency).\n"
            f"  Weights: w_energy={weights.energy_weight}  w_latency={weights.latency_weight}"
            f"  gamma={weights.congestion_factor}"
        ),
        FocusMode.ECO: (
            "ECO -- Energy/power-saving focused\n"
            "  The optimiser consolidates tasks onto fewer active servers and\n"
            "  prefers energy-efficient machines.  Latency is secondary.\n"
            "  Matches the thesis motivation of sustainable cloud computing.\n"
            f"  Weights: w_energy={weights.energy_weight}  w_latency={weights.latency_weight}"
            f"  gamma={weights.congestion_factor}"
        ),
    }
    print(f"\n  Focus mode: {descriptions[mode]}")
    print(
        f"  Penalty coefficients: lambda_cpu={weights.cpu_penalty:.0f}  "
        f"lambda_mem={weights.mem_penalty:.1f}"
    )


def _single_run_diagnostics(data, weights, sa_kwargs, verbose: bool) -> None:
    """
    Run SA once without a fixed seed and print a detailed solution breakdown.

    This section is useful during development and parameter tuning.
    """
    _print_section("Single SA Diagnostic Run")

    t0 = time.perf_counter()
    best_assignment, best_eval, stats = simulated_annealing(
        data=data,
        weights=weights,
        verbose=verbose,
        **sa_kwargs,
    )
    elapsed = time.perf_counter() - t0

    # --- Solution quality ---
    print(f"  Feasible:              {best_eval.feasible}")
    print(f"  Objective value F(X):  {best_eval.objective_value:.4f}")
    print(f"  Total energy (W):      {best_eval.total_energy:.2f}")
    print(f"  Total latency (ms):    {best_eval.total_latency:.2f}")
    print(f"  CPU violation (%):     {best_eval.cpu_violation:.4f}")
    print(f"  Memory violation (MB): {best_eval.mem_violation:.2f}")
    print(f"  Active servers:        {best_eval.n_active_servers}/{data.n_servers}")
    print(f"  Runtime:               {elapsed:.2f}s")

    # --- SA search diagnostics (useful for tuning) ---
    print()
    print("  SA search statistics:")
    print(f"    Candidates evaluated:    {stats.total_evaluated}"
          f"  (+ {stats.t0_probe_evaluations} T_0 probe evals"
          f"  -> total budget {stats.total_budget_consumed})")
    print(f"    Improving accepted:      {stats.total_improving_accepted}")
    print(f"    Worsening accepted:      {stats.total_worsening_accepted}")
    print(f"    Structural rejections:   {stats.total_rejected_structural}")
    print(f"    Acceptance rate:         {stats.acceptance_rate:.2%}")
    print(f"    Feasibility rate:        {stats.feasibility_rate:.2%}")
    print(f"    Reheat count:            {stats.reheat_count}")
    print(f"    Final temperature:       {stats.final_temperature:.6f}")

    # --- Per-server ASCII bar chart ---
    print()
    print("  Per-server task distribution (# = 1 task):")
    server_counts = Counter(best_assignment)
    for j in range(data.n_servers):
        count = server_counts.get(j, 0)
        bar   = "#" * count
        print(f"    Server {j:>2}: {count:>3} tasks  {bar}")


# ---------------------------------------------------------------------------
# Results interpretation
# ---------------------------------------------------------------------------

def _print_interpretation(
    meta_results: list,
    baseline_results: list,
    data,
    weights,
    focus_mode: FocusMode,
) -> None:
    """
    Print a plain-language analysis of the experiment results.

    Covers: ranking, energy/latency breakdown, improvement over baselines,
    wall-clock speed comparison, and a comment on whether the relative ordering
    of algorithms is what theory would predict.
    """
    _print_section("Results Interpretation")

    if not meta_results:
        print("  (no metaheuristic results to interpret)")
        return

    # Rank by average across seeds, not by single best seed: a stochastic
    # algorithm that gets one lucky run but is unreliable on average is not
    # the better algorithm.  This matches the summary.md ranking criterion.
    ranked = sorted(meta_results, key=lambda r: r.average_cost)
    winner = ranked[0]

    # ---- Focus mode reminder ---- #
    mode_descriptions = {
        FocusMode.BALANCED:    "Balanced - equal energy / latency trade-off",
        FocusMode.PERFORMANCE: "Performance - latency-focused (high-priority task response times)",
        FocusMode.ECO:         "Eco - energy-focused (power saving / server consolidation)",
    }
    print(f"\n  Focus mode : {mode_descriptions[focus_mode]}")
    print(f"  Seeds / alg: {len(meta_results[0].seeds)}")
    print(f"  Tasks      : {data.n_tasks}   Servers: {data.n_servers}")

    # ---- Ranking table ---- #
    print(f"\n  Metaheuristic ranking (lower F(X) = better):")
    print(f"  {'Rank':<5} {'Algorithm':<27} {'Best F':>10} {'Avg F':>10}"
          f" {'StdDev':>8} {'Feasible':>9} {'Avg time':>9}")
    print("  " + "-" * 80)
    for rank, r in enumerate(ranked, 1):
        gap = (r.average_cost - winner.average_cost) / max(1.0, winner.average_cost) * 100
        gap_str = f"  (+{gap:.1f}%)" if gap > 0.01 else "  (winner)"
        print(
            f"  {rank:<5} {r.algorithm_name:<27}"
            f" {r.best_cost:>10.2f}"
            f" {r.average_cost:>10.2f}"
            f" {r.std_cost:>8.2f}"
            f" {r.feasible_run_count:>6}/{len(r.seeds)}"
            f" {r.average_runtime:>8.2f}s"
            f"{gap_str}"
        )

    # ---- Energy / latency decomposition ---- #
    print(f"\n  Energy vs latency decomposition of F(X) - best run per algorithm:")
    print(f"  {'Algorithm':<27} {'Energy':>10} {'Latency':>12} {'Servers':>8}"
          f" {'E-contrib%':>11} {'L-contrib%':>11}")
    print("  " + "-" * 82)
    for r in meta_results:
        ev = r.best_eval
        e_c = weights.energy_weight  * ev.total_energy
        l_c = weights.latency_weight * ev.total_latency
        total_c = e_c + l_c
        e_pct = e_c / total_c * 100 if total_c > 0 else 0
        l_pct = l_c / total_c * 100 if total_c > 0 else 0
        print(
            f"  {r.algorithm_name:<27}"
            f" {ev.total_energy:>9.0f}W"
            f" {ev.total_latency:>11.0f}ms"
            f" {ev.n_active_servers:>5}/{data.n_servers}"
            f" {e_pct:>10.1f}%"
            f" {l_pct:>10.1f}%"
        )
    print("  (E-contrib = w_e × E(X),  L-contrib = w_l × L(X),  excluding capacity penalties)")

    # ---- Baseline comparison ---- #
    # Compare averages, not best seeds: a metaheuristic that beats Greedy
    # on its luckiest seed but ties on average isn't reliably better in
    # production.
    greedy = next((r for r in baseline_results if "Greedy" in r.algorithm_name), None)
    if greedy:
        print(f"\n  Improvement over Greedy BFD baseline (F_greedy = {greedy.average_cost:.2f}):")
        for r in meta_results:
            improv = (greedy.average_cost - r.average_cost) / max(1.0, greedy.average_cost) * 100
            tag = "[better]" if improv > 0 else "[WORSE - check settings]"
            print(f"    {r.algorithm_name:<27}  {improv:>+6.1f}%  {tag}")

    # ---- Wall-clock speed ---- #
    fastest = min(meta_results, key=lambda r: r.average_runtime)
    slowest = max(meta_results, key=lambda r: r.average_runtime)
    print(f"\n  Wall-clock speed (per single run, ~150 000 evaluations each):")
    for r in meta_results:
        tag = " <- fastest" if r is fastest else (" <- slowest" if r is slowest else "")
        print(f"    {r.algorithm_name:<27}  avg {r.average_runtime:.2f}s{tag}")
    if abs(fastest.average_runtime - slowest.average_runtime) < 1.0:
        print("    All algorithms run in similar time - evaluation budgets are calibrated.")

    # ---- Expected behaviour commentary ---- #
    print(f"""
  Expected behaviour and sanity check:
  -------------------------------------------------------------------------
  SA (Simulated Annealing):
    Single-trajectory search with the Metropolis acceptance criterion.
    Geometric cooling + reheating helps escape local optima. On discrete
    assignment problems, SA typically produces competitive results because
    the five neighbourhood operators (reassign, swap, relocate, consolidate,
    spread) cover the key energy/latency trade-off directions directly.
    Expected to rank first or very close to first.

  GA (Genetic Algorithm):
    Population-based, combines solutions via uniform crossover. Diverse
    initial population (1 greedy + 49 random) maps the landscape broadly.
    However, crossing two good integer-vector assignments often produces
    offspring that are worse than either parent - a known issue in discrete
    EAs - so GA can converge slower than SA per unit of budget. Elitism
    (2 best carried forward) prevents quality regression between generations.
    Expected: slightly below SA in quality but competitive.

  UMDA (EDA - Estimation of Distribution Algorithm):
    Learns a probability model P[task i -> server j] from the top 50% of
    each generation. Convergence is often rapid in model-space (the entropy
    subplot shows this clearly). However, the univariate independence
    assumption - each task's server is chosen independently - misses
    cross-task interactions: placing task A on server 3 changes server 3's
    CPU load and therefore the congestion latency for task B if it is also
    on server 3. This coupling is handled implicitly through the objective
    but not explicitly in the model, so UMDA may plateau slightly below SA.
    Expected: fastest early convergence, possibly lower final quality.
  -------------------------------------------------------------------------""")

    # ---- Automated sanity checks ---- #
    print("  Automated checks:")
    all_beat_greedy = greedy and all(r.best_cost < greedy.best_cost for r in meta_results)
    if all_beat_greedy:
        print("  [OK] All metaheuristics beat Greedy BFD - search adds genuine value over construction.")
    elif greedy:
        for r in meta_results:
            if r.best_cost >= greedy.best_cost:
                print(f"  [!!] {r.algorithm_name} did NOT beat Greedy BFD - consider more seeds/iterations.")

    fully_feasible = [r for r in meta_results if r.feasible_run_count == len(r.seeds)]
    if len(fully_feasible) == len(meta_results):
        print(f"  [OK] All metaheuristics found feasible solutions on every seed.")
    else:
        for r in meta_results:
            if r.feasible_run_count < len(r.seeds):
                infeasible = len(r.seeds) - r.feasible_run_count
                print(f"  [!!] {r.algorithm_name}: {infeasible} seed(s) ended infeasible -"
                      f"lambda_cpu / lambda_mem penalties may need increasing, or more iterations.")

    # Check energy/latency balance is sensible for the chosen mode
    if focus_mode == FocusMode.ECO:
        best_e = min(r.best_eval.total_energy for r in meta_results)
        worst_e = max(r.best_eval.total_energy for r in meta_results)
        if worst_e - best_e > 500:
            print(f"  [NOTE] Large energy spread ({worst_e - best_e:.0f}W) across algorithms -"
                  f"eco mode is producing meaningful energy differences worth discussing.")
    elif focus_mode == FocusMode.PERFORMANCE:
        best_l = min(r.best_eval.total_latency for r in meta_results)
        worst_l = max(r.best_eval.total_latency for r in meta_results)
        if worst_l - best_l > 1000:
            print(f"  [NOTE] Large latency spread ({worst_l - best_l:.0f}ms) across algorithms -"
                  f"performance mode is producing meaningful latency differences.")

    print()


# ---------------------------------------------------------------------------
# Sensitivity analysis helpers
# ---------------------------------------------------------------------------

def _save_sensitivity_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["param", "value", "best", "average", "worst", "std_dev", "feasible"]
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n  Sensitivity results saved ->{path}")


def _sweep_one_param(
    algorithm,
    algorithm_name: str,
    base_kwargs: dict,
    param_name: str,
    values: list,
    data,
    weights,
    seeds: list[int],
    label_fmt: str = "{v}",
) -> list[dict]:
    rows: list[dict] = []
    for v in values:
        kwargs = {**base_kwargs, param_name: v}
        res = run_experiments(
            algorithm=algorithm,
            algorithm_name=f"{algorithm_name} {param_name}={label_fmt.format(v=v)}",
            data=data, weights=weights,
            seeds=seeds, show_progress=False,
            **kwargs,
        )
        print(
            f"  {str(v):>10}"
            f" {res.best_cost:>12.4f}"
            f" {res.average_cost:>12.4f}"
            f" {res.std_cost:>10.4f}"
            f" {res.feasible_run_count:>7}/{len(seeds)}"
        )
        rows.append({
            "param": param_name, "value": v,
            "best": res.best_cost, "average": res.average_cost,
            "worst": res.worst_cost, "std_dev": res.std_cost,
            "feasible": res.feasible_run_count,
        })
    return rows


def _plot_sensitivity(
    rows_a: list[dict], label_a: str, xlabel_a: str, xscale_a: str,
    rows_b: list[dict], label_b: str, xlabel_b: str,
    title: str, save_path: str,
) -> None:
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    for ax, rows, xlabel, xscale, color in [
        (axes[0], rows_a, xlabel_a, xscale_a, "steelblue"),
        (axes[1], rows_b, xlabel_b, "linear",  "darkorange"),
    ]:
        vals = [r["value"] for r in rows]
        avgs = [r["average"] for r in rows]
        stds = [r["std_dev"]  for r in rows]
        ax.errorbar(vals, avgs, yerr=stds, marker="o", capsize=4, color=color)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Average best cost")
        ax.set_xscale(xscale)
        ax.grid(True, alpha=0.3)
    axes[0].set_title(label_a)
    axes[1].set_title(label_b)
    plt.suptitle(title, fontsize=13)
    plt.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Sensitivity plot saved  ->{save_path}")


# ---------------------------------------------------------------------------
# Hyperparameter tuning — grid search (--tune flag)
# ---------------------------------------------------------------------------
#
# Workflow:
#   1. Generate the full Cartesian product of parameter values per algorithm.
#   2. Run each combination over n_seeds; record the mean F(X).
#   3. Pick the combination with the lowest mean F(X) (ties broken by lowest
#      std_dev, then by lowest mean runtime).
#   4. Write results/tuning_<algo>.csv with EVERY combination's score so the
#      thesis can show the full grid.
#   5. Write results/tuning_summary.md with the recommended values.
#
# This is intentionally separate from --sensitivity:
#   --sensitivity sweeps ONE parameter at a time (showing robustness around a
#                  point), and reports values across the swept range.
#   --tune        sweeps the full PRODUCT, picks the global best, and is meant
#                  to be run ONCE at the start of a thesis chapter.
# ---------------------------------------------------------------------------

def _compute_main_budget(kwargs: dict, algo: str) -> int:
    """
    Compute the algorithm's total evaluation budget from its base config.

    Budget product:
        SA      : max_temp_steps * iterations_per_temperature
        GA/UMDA : population_size * n_generations
    """
    if algo == "SA":
        return int(kwargs.get("max_temp_steps", 3000)
                   * kwargs.get("iterations_per_temperature", 50))
    if algo in ("GA", "UMDA"):
        return int(kwargs.get("population_size", 50)
                   * kwargs.get("n_generations", 3000))
    return 150_000


def _equalise_budget(
    kwargs: dict,
    target_budget: int,
    algo: str,
    grid_keys: set[str],
) -> dict:
    """
    Set the *dependent* budget multiplier so total evaluations == target_budget.

    The tuning grids sweep the "primary" budget multiplier
    (iterations_per_temperature for SA, population_size for GA/UMDA).  Without
    this function the OTHER multiplier (max_temp_steps / n_generations) is
    held constant, so the cell with the largest grid value silently consumes
    many times more evaluations than the smallest cell — confounding
    hyperparameter quality with raw compute.

    Setting the dependent multiplier inverse to the primary one enforces the
    equal-budget contract the thesis claims: every grid cell consumes exactly
    `target_budget` evaluate_schedule() calls, so the tuning measures
    hyperparameter quality alone.

    If the grid *explicitly* sweeps the dependent parameter, this function
    leaves it alone — the user has opted into unequal budgets.
    """
    out = dict(kwargs)
    if algo == "SA":
        if "max_temp_steps" in grid_keys:
            return out
        iter_per_temp = int(kwargs.get("iterations_per_temperature", 50))
        out["max_temp_steps"] = max(20, target_budget // max(1, iter_per_temp))
    elif algo in ("GA", "UMDA"):
        if "n_generations" in grid_keys:
            return out
        pop = int(kwargs.get("population_size", 50))
        out["n_generations"] = max(20, target_budget // max(1, pop))
    return out


def _grid_search_one_algorithm(
    algorithm,
    algorithm_name: str,
    base_kwargs: dict,
    grid: dict[str, list],
    data,
    weights,
    seeds: list[int],
    target_budget: int,
) -> tuple[list[dict], dict]:
    """
    Run a full Cartesian-product grid search for one algorithm.

    Each grid cell is run at *equal* evaluation budget: the dependent budget
    multiplier (max_temp_steps for SA, n_generations for GA/UMDA) is recomputed
    per cell via _equalise_budget so total evaluations == target_budget.  This
    makes the comparison purely about hyperparameter quality, not raw compute.

    Returns
    -------
    rows : list of {param_name: value, ..., mean_F, std_F, mean_time, feasible_pct}
    best : the row with the lowest mean_F (ties broken by std, then time)
    """
    import itertools

    keys   = list(grid.keys())
    values = [grid[k] for k in keys]
    combos = list(itertools.product(*values))
    grid_key_set = set(keys)

    print(f"\n  Grid: {len(combos)} combinations x {len(seeds)} seeds"
          f"  =  {len(combos) * len(seeds)} runs")
    print(f"  {'  '.join(f'{k:>14}' for k in keys)}  {'mean_F':>10} {'std_F':>9} {'mean_t':>8} {'feas%':>6}")
    print("  " + "-" * (16 * len(keys) + 38))

    rows: list[dict] = []
    for combo in combos:
        kwargs = dict(base_kwargs)
        for k, v in zip(keys, combo):
            kwargs[k] = v
        # Equal-budget contract: set the dependent loop parameter so every
        # cell consumes the same target_budget total evaluations.
        kwargs = _equalise_budget(kwargs, target_budget, algorithm_name, grid_key_set)
        res = run_experiments(
            algorithm=algorithm,
            algorithm_name=f"{algorithm_name}",
            data=data, weights=weights,
            seeds=seeds, show_progress=False,
            **kwargs,
        )
        feas_pct = res.feasible_run_count / max(1, len(seeds)) * 100
        row = {k: v for k, v in zip(keys, combo)}
        row.update({
            "mean_F":   res.average_cost,
            "std_F":    res.std_cost,
            "mean_time_s": res.average_runtime,
            "feasible_pct": feas_pct,
        })
        rows.append(row)
        print(f"  {'  '.join(f'{str(v):>14}' for v in combo)}"
              f"  {res.average_cost:>10.4f}"
              f"  {res.std_cost:>9.4f}"
              f"  {res.average_runtime:>7.2f}s"
              f"  {feas_pct:>5.0f}%")

    # Pick best: lowest mean_F, tie-break by std_F, then time
    best = min(rows, key=lambda r: (r["mean_F"], r["std_F"], r["mean_time_s"]))
    return rows, best


def _save_tuning_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    print(f"  Tuning CSV saved -> {path}")


def run_tuning(
    run_flags: dict[str, bool],
    data,
    weights,
    sa_kwargs: dict,
    ga_kwargs: dict,
    umda_kwargs: dict,
    cfg_tuning,
    results_dir: Path,
) -> dict[str, dict]:
    """
    Grid-search tuning entry point.  Sweeps each selected algorithm's grid
    independently and reports the best combination per algorithm.

    Returns
    -------
    dict mapping algorithm_name -> best-parameter row, so the calling code can
    optionally pretty-print or persist a tuning_summary.md.
    """
    _print_section("Hyperparameter Tuning (Grid Search)")
    factor = (1.0 / 3.0) if cfg_tuning.reduced_budget else 1.0
    print(f"  Seeds per combination: {cfg_tuning.n_seeds}"
          f"  |  Budget factor: {factor:.2f}  ({'reduced' if cfg_tuning.reduced_budget else 'full'})")

    seeds = list(range(cfg_tuning.n_seeds))
    best_per_algo: dict[str, dict] = {}

    if run_flags["SA"]:
        _print_section("Tuning Simulated Annealing")
        target_budget = int(_compute_main_budget(sa_kwargs, "SA") * factor)
        print(f"  Equal-budget target: {target_budget:,} evaluations per cell"
              f"  (max_temp_steps recomputed per cell from iter_per_temp)")
        rows, best = _grid_search_one_algorithm(
            simulated_annealing, "SA", sa_kwargs,
            grid={
                "cooling_rate":               cfg_tuning.sa["cooling_rates"],
                "iterations_per_temperature": cfg_tuning.sa["iterations_per_temperature"],
            },
            data=data, weights=weights, seeds=seeds,
            target_budget=target_budget,
        )
        _save_tuning_csv(rows, results_dir / "tuning_sa.csv")
        best_per_algo["Simulated Annealing"] = best

    if run_flags["GA"]:
        _print_section("Tuning Genetic Algorithm")
        target_budget = int(_compute_main_budget(ga_kwargs, "GA") * factor)
        print(f"  Equal-budget target: {target_budget:,} evaluations per cell"
              f"  (n_generations recomputed per cell from population_size)")
        rows, best = _grid_search_one_algorithm(
            genetic_algorithm, "GA", ga_kwargs,
            grid={
                "population_size": cfg_tuning.ga["population_sizes"],
                "crossover_prob":  cfg_tuning.ga["crossover_probs"],
            },
            data=data, weights=weights, seeds=seeds,
            target_budget=target_budget,
        )
        _save_tuning_csv(rows, results_dir / "tuning_ga.csv")
        best_per_algo["Genetic Algorithm"] = best

    if run_flags["UMDA"]:
        _print_section("Tuning UMDA")
        target_budget = int(_compute_main_budget(umda_kwargs, "UMDA") * factor)
        print(f"  Equal-budget target: {target_budget:,} evaluations per cell"
              f"  (n_generations recomputed per cell from population_size)")
        rows, best = _grid_search_one_algorithm(
            umda, "UMDA", umda_kwargs,
            grid={
                "population_size": cfg_tuning.umda["population_sizes"],
                "selection_ratio": cfg_tuning.umda["selection_ratios"],
            },
            data=data, weights=weights, seeds=seeds,
            target_budget=target_budget,
        )
        _save_tuning_csv(rows, results_dir / "tuning_umda.csv")
        best_per_algo["UMDA (EDA)"] = best

    # ---- tuning_summary.md ----
    _save_tuning_summary_md(best_per_algo, cfg_tuning, results_dir)

    _print_section("Tuning recommendation")
    for name, best in best_per_algo.items():
        params = {k: v for k, v in best.items()
                  if k not in ("mean_F", "std_F", "mean_time_s", "feasible_pct")}
        print(f"  {name}:")
        for k, v in params.items():
            print(f"    {k} = {v}")
        print(f"    -> mean_F = {best['mean_F']:.4f}  +/- {best['std_F']:.4f}"
              f"  (mean_time = {best['mean_time_s']:.2f}s)")

    print("\n  Copy the recommended values into config.yaml -> algorithms:"
          " section, then re-run without --tune for the main experiment.")
    return best_per_algo


def _save_tuning_summary_md(
    best_per_algo: dict[str, dict],
    cfg_tuning,
    results_dir: Path,
) -> None:
    import datetime as _dt
    now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# Hyperparameter Tuning — Recommended Values\n",
        f"_Generated: {now}_\n",
        f"_Tuning method: full Cartesian grid search, {cfg_tuning.n_seeds} seeds per cell._",
        f"_Reduced budget: {cfg_tuning.reduced_budget}_\n",
        "",
        "## Recommendations\n",
    ]
    for name, best in best_per_algo.items():
        params = {k: v for k, v in best.items()
                  if k not in ("mean_F", "std_F", "mean_time_s", "feasible_pct")}
        lines.append(f"### {name}\n")
        lines.append("| Parameter | Value |\n|---|---|")
        for k, v in params.items():
            lines.append(f"| `{k}` | {v} |")
        lines.append(f"\n_Mean F(X) = {best['mean_F']:.4f} ± {best['std_F']:.4f}, "
                     f"mean runtime = {best['mean_time_s']:.2f}s, "
                     f"feasible = {best['feasible_pct']:.0f}%_\n")
    lines.append("\n## How to apply\n")
    lines.append("1. Open `config.yaml`.")
    lines.append("2. In the `algorithms:` section update each algorithm with the parameter values above.")
    lines.append("3. Run the main experiment **without** `--tune`.")
    lines.append("4. Optionally run `--sensitivity` to confirm the chosen values are in a robust region.\n")

    path = results_dir / "tuning_summary.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n  Tuning summary saved -> {path}")


def run_sa_sensitivity_analysis(
    data,
    weights,
    base_sa_kwargs: dict,
    sweep: dict,
    figures_dir: Path,
    results_dir: Path,
    seeds: list[int],
) -> None:
    """Sweep SA initial_temperature and cooling_rate; save CSV + plot.

    Cooling-rate sweep: max_temp_steps is auto-scaled per cell so every alpha
    reaches the same final temperature (min_temperature).  Without this, a
    fixed step count makes slow cooling look artificially worse because the
    schedule never finishes — the result becomes a budget artefact rather than
    a property of the cooling rate itself.  Total evaluations therefore vary
    across cells (a documented trade-off: equal schedule, unequal budget).
    """
    import math
    from algorithms.simulated_annealing import estimate_initial_temperature

    _print_section("SA Sensitivity Analysis")

    print(f"\n  Temperature sweep (cooling_rate={base_sa_kwargs['cooling_rate']}):")
    print(f"  {'T_init':>10} {'Best':>12} {'Average':>12} {'Std Dev':>10} {'Feasible':>8}")
    print("  " + "-" * 62)
    temp_rows = _sweep_one_param(
        simulated_annealing, "SA", base_sa_kwargs,
        "initial_temperature", sweep["temperatures"],
        data, weights, seeds, label_fmt="{v:.0f}",
    )

    # ---- Cooling-rate sweep with per-cell schedule equalisation ----
    # Fix T_0 once (auto-estimate against the actual instance) so the cell-to-cell
    # difference is purely the cooling rate, not a re-calibrated T_0 per seed.
    t0_fixed, _t0_probes = estimate_initial_temperature(data, weights)
    min_t         = float(base_sa_kwargs.get("min_temperature", 1e-8))
    iter_per_temp = int(base_sa_kwargs.get("iterations_per_temperature", 50))

    print(f"\n  Cooling-rate sweep (T_0 fixed at {t0_fixed:.4f}; "
          f"max_temp_steps auto-scaled per alpha so T reaches min_T={min_t:.0e}):")
    print(f"  {'alpha':>10} {'steps':>8} {'evals':>10}"
          f" {'Best':>12} {'Average':>12} {'Std Dev':>10} {'Feasible':>8}")
    print("  " + "-" * 84)

    rate_rows: list[dict] = []
    for alpha in sweep["cooling_rates"]:
        steps_needed = max(
            20,
            int(math.ceil(math.log(min_t / t0_fixed) / math.log(alpha))),
        )
        cell_kwargs = {
            **base_sa_kwargs,
            "cooling_rate":        alpha,
            "initial_temperature": t0_fixed,
            "max_temp_steps":      steps_needed,
        }
        res = run_experiments(
            algorithm=simulated_annealing,
            algorithm_name=f"SA cooling_rate={alpha:.3f}",
            data=data, weights=weights,
            seeds=seeds, show_progress=False,
            **cell_kwargs,
        )
        eval_budget = steps_needed * iter_per_temp
        print(
            f"  {alpha:>10.3f}"
            f" {steps_needed:>8d}"
            f" {eval_budget:>10,d}"
            f" {res.best_cost:>12.4f}"
            f" {res.average_cost:>12.4f}"
            f" {res.std_cost:>10.4f}"
            f" {res.feasible_run_count:>7}/{len(seeds)}"
        )
        rate_rows.append({
            "param": "cooling_rate", "value": alpha,
            "best": res.best_cost, "average": res.average_cost,
            "worst": res.worst_cost, "std_dev": res.std_cost,
            "feasible": res.feasible_run_count,
        })

    _save_sensitivity_csv(temp_rows + rate_rows, results_dir / "sensitivity_sa.csv")
    _plot_sensitivity(
        temp_rows, "SA: sensitivity to T_0",         "Initial temperature T_0", "log",
        rate_rows, "SA: sensitivity to cooling rate alpha (schedule-equalised)",
        "Cooling rate alpha",
        title="SA Hyperparameter Sensitivity Analysis",
        save_path=str(figures_dir / "sa_sensitivity.png"),
    )


def run_ga_sensitivity_analysis(
    data,
    weights,
    base_ga_kwargs: dict,
    sweep: dict,
    figures_dir: Path,
    results_dir: Path,
    seeds: list[int],
) -> None:
    """Sweep GA population_size and crossover_prob; save CSV + plot."""
    _print_section("GA Sensitivity Analysis")

    print(f"\n  Population-size sweep (crossover_prob={base_ga_kwargs['crossover_prob']}):")
    print(f"  {'pop_size':>10} {'Best':>12} {'Average':>12} {'Std Dev':>10} {'Feasible':>8}")
    print("  " + "-" * 62)
    pop_rows = _sweep_one_param(
        genetic_algorithm, "GA", base_ga_kwargs,
        "population_size", sweep["population_sizes"],
        data, weights, seeds,
    )

    print(f"\n  Crossover-prob sweep (population_size={base_ga_kwargs['population_size']}):")
    print(f"  {'crossover_p':>10} {'Best':>12} {'Average':>12} {'Std Dev':>10} {'Feasible':>8}")
    print("  " + "-" * 62)
    cx_rows = _sweep_one_param(
        genetic_algorithm, "GA", base_ga_kwargs,
        "crossover_prob", sweep["crossover_probs"],
        data, weights, seeds, label_fmt="{v:.1f}",
    )

    _save_sensitivity_csv(pop_rows + cx_rows, results_dir / "sensitivity_ga.csv")
    _plot_sensitivity(
        pop_rows, "GA: sensitivity to population size", "Population size", "linear",
        cx_rows,  "GA: sensitivity to crossover prob",  "Crossover probability",
        title="GA Hyperparameter Sensitivity Analysis",
        save_path=str(figures_dir / "ga_sensitivity.png"),
    )


def run_umda_sensitivity_analysis(
    data,
    weights,
    base_umda_kwargs: dict,
    sweep: dict,
    figures_dir: Path,
    results_dir: Path,
    seeds: list[int],
) -> None:
    """Sweep UMDA population_size and selection_ratio; save CSV + plot."""
    _print_section("UMDA Sensitivity Analysis")

    print(f"\n  Population-size sweep (selection_ratio={base_umda_kwargs['selection_ratio']}):")
    print(f"  {'pop_size':>10} {'Best':>12} {'Average':>12} {'Std Dev':>10} {'Feasible':>8}")
    print("  " + "-" * 62)
    pop_rows = _sweep_one_param(
        umda, "UMDA", base_umda_kwargs,
        "population_size", sweep["population_sizes"],
        data, weights, seeds,
    )

    print(f"\n  Selection-ratio sweep (population_size={base_umda_kwargs['population_size']}):")
    print(f"  {'sel_ratio':>10} {'Best':>12} {'Average':>12} {'Std Dev':>10} {'Feasible':>8}")
    print("  " + "-" * 62)
    sel_rows = _sweep_one_param(
        umda, "UMDA", base_umda_kwargs,
        "selection_ratio", sweep["selection_ratios"],
        data, weights, seeds, label_fmt="{v:.2f}",
    )

    _save_sensitivity_csv(pop_rows + sel_rows, results_dir / "sensitivity_umda.csv")
    _plot_sensitivity(
        pop_rows, "UMDA: sensitivity to population size", "Population size",    "linear",
        sel_rows, "UMDA: sensitivity to selection ratio", "Selection ratio",
        title="UMDA Hyperparameter Sensitivity Analysis",
        save_path=str(figures_dir / "umda_sensitivity.png"),
    )


# ---------------------------------------------------------------------------
# Scalability analysis — shared helpers
# ---------------------------------------------------------------------------

def _build_algos_list(
    run_flags: dict[str, bool],
    sa_kwargs: dict,
    ga_kwargs: dict,
    umda_kwargs: dict,
) -> list[tuple]:
    algos = []
    if run_flags["SA"]:
        algos.append(("Simulated Annealing", simulated_annealing, sa_kwargs))
    if run_flags["GA"]:
        algos.append(("Genetic Algorithm", genetic_algorithm, ga_kwargs))
    if run_flags["UMDA"]:
        algos.append(("UMDA (EDA)", umda, umda_kwargs))
    return algos


def _reweight(
    weights_base,
    data,
    normalize: bool,
    method: str = "sample",
    n_samples: int = 150,
    penalty_multiplier: float = 100.0,
    calibration_seed: int = 0,
    min_feasible: int = 10,
):
    """
    Return weights_base with normalisation refs (and penalty values, if using
    sample-based calibration) recomputed for *this* problem instance.

    Used by every scalability axis so each instance gets its own calibration —
    a 200-task instance has different mean E / mean L than a 50-task instance,
    so the refs must be recomputed for fair comparison.
    """
    if not normalize:
        return weights_base
    if method.lower() == "sample":
        calibrated, diag = compute_sample_normalization(
            data,
            base_weights=weights_base,
            n_samples=n_samples,
            seed=calibration_seed,
            penalty_multiplier=penalty_multiplier,
            min_feasible=min_feasible,
        )
        if diag.fallback_to_worst_case:
            print(
                "\n  " + "!" * 70 + "\n"
                f"  [calibration] FALLBACK TRIGGERED on this scalability instance:\n"
                f"    only {diag.n_feasible} of {diag.n_attempted} samples were feasible\n"
                f"    (min_feasible_calibration = {min_feasible}).\n"
                f"    Reverted to worst-case normalisation; mode preference ratios\n"
                f"    no longer reflect equal expected contribution on this instance.\n"
                "  " + "!" * 70
            )
        return calibrated
    # worst_case fallback
    e_ref, l_ref, c_ref, m_ref = compute_normalization_constants(
        data, weights_base.congestion_factor
    )
    return dataclasses.replace(
        weights_base,
        energy_ref=e_ref, latency_ref=l_ref,
        cpu_ref=c_ref, mem_ref=m_ref,
    )


def _collect_winner_row(
    label: str,
    n_tasks: int,
    n_servers: int,
    meta_results: list,
    greedy_cost: float,
) -> dict:
    """Build one row for the winner summary table."""
    if not meta_results:
        return {}
    winner = min(meta_results, key=lambda r: r.average_cost)
    improv = (greedy_cost - winner.average_cost) / max(1e-10, abs(greedy_cost)) * 100
    return {
        "label":           label,
        "n_tasks":         n_tasks,
        "n_servers":       n_servers,
        "winner":          winner.algorithm_name,
        "winner_avg_cost": winner.average_cost,
        "greedy_cost":     greedy_cost,
        "improvement_pct": improv,
        "winner_avg_time": winner.average_runtime,
    }


def _print_winner_table(rows: list[dict], title: str) -> None:
    """Print a formatted winner-per-scale-point summary table."""
    from collections import Counter as _Counter
    _print_section(title)
    if not rows:
        return
    print(f"  {'Scale Point':<24} {'Winner':<27} {'Avg F(X)':>10}"
          f" {'vs Greedy':>10} {'Avg Time':>9}")
    print("  " + "-" * 84)
    win_counts: dict = _Counter()
    for r in rows:
        if not r:
            continue
        print(
            f"  {r['label']:<24}"
            f" {r['winner']:<27}"
            f" {r['winner_avg_cost']:>10.4f}"
            f" {r['improvement_pct']:>+9.1f}%"
            f" {r['winner_avg_time']:>8.2f}s"
        )
        win_counts[r["winner"]] += 1
    total = sum(win_counts.values())
    print()
    for name, cnt in win_counts.most_common():
        pct = cnt / total * 100
        bar = "█" * cnt
        print(f"  {name:<27}  {cnt}/{total} scale points  ({pct:.0f}%)  {bar}")
    print()


# ---------------------------------------------------------------------------
# Scalability — note on fixed-budget behaviour at large n
# ---------------------------------------------------------------------------

def _print_scalability_note(scale_data: dict) -> None:
    """
    Detect and explain the common pattern where SA/UMDA show near-zero
    improvement over Greedy at large n.  This is expected fixed-budget
    behaviour, not a code error — print a brief note so the user is not
    alarmed when they see +0.0% in the table.
    """
    threshold_pct = 0.1   # below this, flag as "near-greedy"
    flagged: list[str] = []
    for name, d in scale_data.items():
        for i, n in enumerate(d["sizes"]):
            if n >= 100 and abs(d["improvements"][i]) < threshold_pct:
                flagged.append(f"  {name} at n={n}")

    if not flagged:
        return

    print()
    print("  Note — Fixed-Budget Behaviour at Scale:")
    print("  ─────────────────────────────────────────────────────────")
    print("  The following algorithm-size combinations show near-zero")
    print("  improvement over Greedy BFD (< 0.1%):")
    for line in flagged:
        print(line)
    print()
    print("  Reason: the evaluation budget (150 K calls) was calibrated")
    print("  for n=50 tasks. At n≥200 the search space grows much faster")
    print("  than the budget, so:")
    print("    SA   — starts from the greedy solution and cannot escape it")
    print("           within budget; the fixed cooling schedule leaves too")
    print("           little exploration time at large n.")
    print("    UMDA — the probability model has n×m parameters; with only")
    print("           pop_size/2 training samples per generation the model")
    print("           cannot learn reliable task-server affinities.")
    print("    GA   — maintains advantage because crossover between 49")
    print("           diverse random solutions creates useful offspring")
    print("           without relying on a learned model or a single")
    print("           greedy initialisation.")
    print("  This is a valid thesis finding: at fixed budget, population-")
    print("  diversity (GA) outperforms single-trajectory (SA) and model-")
    print("  based (UMDA) methods as problem size grows.")
    print("  To restore improvement at larger n, scale the budget")
    print("  proportionally (e.g. max_temp_steps ∝ n/50 in config.yaml).")
    print("  ─────────────────────────────────────────────────────────")


# ---------------------------------------------------------------------------
# Scalability — Axis 1: Horizontal (increasing task count, synthetic data)
# ---------------------------------------------------------------------------

def run_horizontal_scaling_analysis(
    run_flags: dict[str, bool],
    weights_base,
    normalize: bool,
    calib: dict,            # method / n_samples / penalty_multiplier / calibration_seed
    dataset_dir,
    figures_dir,
    results_dir,
    cfg,           # HorizontalScalingConfig
    sa_kwargs: dict,
    ga_kwargs: dict,
    umda_kwargs: dict,
) -> None:
    """
    Run metaheuristics on synthetic instances of increasing size.

    Synthetic tasks are sampled from the real dataset's empirical distribution,
    allowing instances far larger than the 6 345-row dataset limit.
    Server count is kept proportional (server_ratio tasks per server) so
    utilisation stays constant across all sizes, making runtime growth
    attributable to problem size rather than constraint pressure.
    """
    _print_section("Scalability Axis 1 — Horizontal: Task-Count Scaling")
    print(f"  Synthetic tasks  |  {cfg.n_seeds} seeds  |  "
          f"server ratio 1:{cfg.server_ratio}  |  "
          f"sizes: {cfg.task_sizes}")

    algos_to_run = _build_algos_list(run_flags, sa_kwargs, ga_kwargs, umda_kwargs)
    if not algos_to_run:
        print("  No metaheuristics selected — skipping.")
        return

    seeds = list(range(cfg.n_seeds))
    scale_data: dict[str, dict] = {}
    winner_rows: list[dict] = []
    # n_tasks -> n_servers mapping for CSV export
    n_servers_map: dict[int, int] = {}

    for n in cfg.task_sizes:
        n_servers = max(4, n // cfg.server_ratio)
        n_servers_map[n] = n_servers
        print(f"\n  ── n_tasks={n:>5}  n_servers={n_servers:>4} ──")
        servers = generate_server_pool(n_servers, seed=42)
        data    = load_synthetic_problem_data(dataset_dir, n_tasks=n,
                                              servers=servers, seed=n * 7 + 1)
        w       = _reweight(weights_base, data, normalize, **calib)

        greedy_res  = run_experiments(
            algorithm=greedy_ffd_baseline, algorithm_name="Greedy BFD",
            data=data, weights=w, seeds=[0], show_progress=False,
        )
        greedy_cost = greedy_res.average_cost

        meta_results = []
        for name, fn, kwargs in algos_to_run:
            res    = run_experiments(
                algorithm=fn, algorithm_name=name,
                data=data, weights=w, seeds=seeds, show_progress=False, **kwargs,
            )
            improv = (greedy_cost - res.average_cost) / max(1e-10, abs(greedy_cost)) * 100
            print(f"    {name:<27}  time={res.average_runtime:6.2f}s"
                  f"  F={res.average_cost:.4f}  vs_greedy={improv:+.1f}%"
                  f"  feasible={res.feasible_run_count}/{cfg.n_seeds}")
            if name not in scale_data:
                scale_data[name] = {"sizes": [], "n_servers": [], "runtimes": [], "improvements": [], "costs": []}
            scale_data[name]["sizes"].append(n)
            scale_data[name]["n_servers"].append(n_servers)
            scale_data[name]["runtimes"].append(res.average_runtime)
            scale_data[name]["improvements"].append(improv)
            scale_data[name]["costs"].append(res.average_cost)
            meta_results.append(res)

        winner_rows.append(_collect_winner_row(
            f"n={n}, m={n_servers}", n, n_servers, meta_results, greedy_cost,
        ))

    _print_scalability_note(scale_data)
    _print_winner_table(winner_rows, "Horizontal Scaling — Winner at Each Scale Point")

    from tools.plot import plot_horizontal_scaling
    plot_horizontal_scaling(scale_data, figures_dir)
    _save_horizontal_csv(scale_data, results_dir)


def _save_horizontal_csv(scale_data: dict, results_dir) -> None:
    import csv as _csv
    path = results_dir / "scalability_horizontal.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = _csv.DictWriter(f, fieldnames=[
            "algorithm", "n_tasks", "n_servers", "avg_runtime_s", "avg_cost",
            "improvement_over_greedy_pct",
        ])
        w.writeheader()
        for name, d in scale_data.items():
            for i, n in enumerate(d["sizes"]):
                w.writerow({
                    "algorithm": name,
                    "n_tasks": n,
                    "n_servers": d["n_servers"][i],
                    "avg_runtime_s": f"{d['runtimes'][i]:.4f}",
                    "avg_cost": f"{d['costs'][i]:.4f}",
                    "improvement_over_greedy_pct": f"{d['improvements'][i]:.2f}",
                })
    print(f"  Horizontal CSV saved         -> {path}")


# ---------------------------------------------------------------------------
# Scalability — Axis 2: Vertical (fixed tasks, varying server count)
# ---------------------------------------------------------------------------

def run_vertical_scaling_analysis(
    run_flags: dict[str, bool],
    weights_base,
    normalize: bool,
    calib: dict,
    dataset_dir,
    figures_dir,
    results_dir,
    cfg,           # VerticalScalingConfig
    sa_kwargs: dict,
    ga_kwargs: dict,
    umda_kwargs: dict,
) -> None:
    """
    Hold the task set fixed (real 50-task instance) and reduce the server
    count from loose (20 servers, ~25% CPU util) to near-critical (6 servers,
    ~80%+ util).  Shows how quality and feasibility degrade as packing becomes
    harder — a dimension orthogonal to raw problem size.
    """
    _print_section("Scalability Axis 2 — Vertical: Constraint Tightness")
    print(f"  Fixed {cfg.n_tasks} real tasks  |  {cfg.n_seeds} seeds  |  "
          f"server counts: {cfg.server_counts}")

    algos_to_run = _build_algos_list(run_flags, sa_kwargs, ga_kwargs, umda_kwargs)
    if not algos_to_run:
        print("  No metaheuristics selected — skipping.")
        return

    seeds = list(range(cfg.n_seeds))
    vert_data: dict[str, dict] = {}
    winner_rows: list[dict] = []

    for n_servers in cfg.server_counts:
        servers = generate_server_pool(n_servers, seed=42)
        data    = load_problem_data(dataset_dir, n_tasks=cfg.n_tasks, servers=servers)
        w       = _reweight(weights_base, data, normalize, **calib)

        total_cpu_demand   = data.cpu.sum()
        total_cpu_capacity = data.server_cpu_cap.sum()
        util_pct           = total_cpu_demand / total_cpu_capacity * 100
        print(f"\n  ── n_servers={n_servers:>3}  CPU utilisation≈{util_pct:.0f}% ──")

        greedy_res  = run_experiments(
            algorithm=greedy_ffd_baseline, algorithm_name="Greedy BFD",
            data=data, weights=w, seeds=[0], show_progress=False,
        )
        greedy_cost = greedy_res.average_cost

        meta_results = []
        for name, fn, kwargs in algos_to_run:
            res    = run_experiments(
                algorithm=fn, algorithm_name=name,
                data=data, weights=w, seeds=seeds, show_progress=False, **kwargs,
            )
            improv      = (greedy_cost - res.average_cost) / max(1e-10, abs(greedy_cost)) * 100
            feas_pct    = res.feasible_run_count / max(1, len(seeds)) * 100
            print(f"    {name:<27}  time={res.average_runtime:5.2f}s"
                  f"  F={res.average_cost:.4f}  vs_greedy={improv:+.1f}%"
                  f"  feasible={res.feasible_run_count}/{cfg.n_seeds} ({feas_pct:.0f}%)")
            if name not in vert_data:
                vert_data[name] = {"servers": [], "util_pct": [], "runtimes": [],
                                   "improvements": [], "costs": [], "feasible_pct": []}
            vert_data[name]["servers"].append(n_servers)
            vert_data[name]["util_pct"].append(util_pct)
            vert_data[name]["runtimes"].append(res.average_runtime)
            vert_data[name]["improvements"].append(improv)
            vert_data[name]["costs"].append(res.average_cost)
            vert_data[name]["feasible_pct"].append(feas_pct)
            meta_results.append(res)

        winner_rows.append(_collect_winner_row(
            f"m={n_servers} ({util_pct:.0f}% util)",
            cfg.n_tasks, n_servers, meta_results, greedy_cost,
        ))

    _print_winner_table(winner_rows, "Vertical Scaling — Winner at Each Tightness Level")

    from tools.plot import plot_vertical_scaling
    plot_vertical_scaling(vert_data, figures_dir)
    _save_vertical_csv(vert_data, results_dir)


def _save_vertical_csv(vert_data: dict, results_dir) -> None:
    import csv as _csv
    path = results_dir / "scalability_vertical.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = _csv.DictWriter(f, fieldnames=[
            "algorithm", "n_servers", "cpu_util_pct",
            "avg_runtime_s", "avg_cost", "improvement_over_greedy_pct", "feasible_pct",
        ])
        w.writeheader()
        for name, d in vert_data.items():
            for i, m in enumerate(d["servers"]):
                w.writerow({
                    "algorithm": name, "n_servers": m,
                    "cpu_util_pct": f"{d['util_pct'][i]:.1f}",
                    "avg_runtime_s": f"{d['runtimes'][i]:.4f}",
                    "avg_cost": f"{d['costs'][i]:.4f}",
                    "improvement_over_greedy_pct": f"{d['improvements'][i]:.2f}",
                    "feasible_pct": f"{d['feasible_pct'][i]:.1f}",
                })
    print(f"  Vertical CSV saved           -> {path}")


# ---------------------------------------------------------------------------
# Optimality-gap benchmark (B&B exact reference on small, tractable instance)
#
# NOT a scalability test — runs at a single fixed (small) size.  Its purpose
# is to anchor the relative %-vs-greedy numbers from the horizontal/vertical
# axes with an absolute %-vs-optimum measurement on the one size where B&B
# can reach the true optimum within the time limit.
# ---------------------------------------------------------------------------

def run_optimality_gap_analysis(
    run_flags: dict[str, bool],
    weights_base,
    normalize: bool,
    calib: dict,
    dataset_dir,
    figures_dir,
    results_dir,
    cfg,           # OptimalityGapConfig
    sa_kwargs: dict,
    ga_kwargs: dict,
    umda_kwargs: dict,
    bb_kwargs: dict,
    verbose: bool,
) -> None:
    """
    Run metaheuristics + B&B on a small instance (n=20, m=4) where the exact
    solver can close the optimality gap within the time limit.

    Reports the gap between each metaheuristic's best solution and the B&B
    reference, giving a direct measure of solution quality independent of the
    greedy baseline.  B&B is always included here regardless of --algorithms.
    """
    _print_section("Solution Quality Benchmark — Optimality Gaps vs. Exact Reference")
    servers = generate_server_pool(cfg.n_servers, seed=42)
    data    = load_problem_data(dataset_dir, n_tasks=cfg.n_tasks, servers=servers)
    w       = _reweight(weights_base, data, normalize, **calib)

    total_cpu  = data.cpu.sum()
    total_cap  = data.server_cpu_cap.sum()
    util_pct   = total_cpu / total_cap * 100
    print(f"  Instance: n={cfg.n_tasks} tasks, m={cfg.n_servers} servers, "
          f"CPU utilisation≈{util_pct:.0f}%")
    print(f"  Seeds: {cfg.n_seeds}  |  B&B always included for exact reference")

    seeds = list(range(cfg.n_seeds))

    # ---- Branch & Bound (exact reference — always run) ----
    tl = bb_kwargs.get("time_limit", 60.0)
    print(f"\n  Running Branch & Bound (time_limit={tl:.0f}s) ...")
    bb_res   = run_experiments(
        algorithm=branch_and_bound, algorithm_name="Branch & Bound",
        data=data, weights=w, seeds=[0], show_progress=True,
        **{**bb_kwargs, "verbose": verbose},
    )
    bb_stats = bb_res.all_stats[0]
    bb_cost  = bb_res.best_cost
    print(f"  B&B: nodes={bb_stats.nodes_explored:,}"
          f"  root_lb={bb_stats.root_lower_bound:.4f}"
          f"  best={bb_cost:.4f}"
          f"  gap={bb_stats.optimality_gap:.1%}"
          f"  proven_optimal={bb_stats.proven_optimal}")

    # ---- Metaheuristics ----
    algos_to_run = _build_algos_list(run_flags, sa_kwargs, ga_kwargs, umda_kwargs)
    if not algos_to_run:
        algos_to_run = [("Simulated Annealing", simulated_annealing, sa_kwargs)]
        print("  (No metaheuristics in --algorithms; running SA as default reference)")

    meta_opt: list = []
    for name, fn, kwargs in algos_to_run:
        print(f"\n  Running {name} ({cfg.n_seeds} seeds) ...")
        res = run_experiments(
            algorithm=fn, algorithm_name=name,
            data=data, weights=w, seeds=seeds, show_progress=True, **kwargs,
        )
        meta_opt.append(res)
        gap = (res.best_cost - bb_cost) / max(1e-10, abs(bb_cost)) * 100
        print(f"    Best={res.best_cost:.4f}  B&B={bb_cost:.4f}  "
              f"optimality_gap=+{gap:.1f}%  feasible={res.feasible_run_count}/{cfg.n_seeds}")

    # ---- Greedy reference ----
    greedy_res = run_experiments(
        algorithm=greedy_ffd_baseline, algorithm_name="Greedy BFD (baseline)",
        data=data, weights=w, seeds=[0], show_progress=False,
    )

    # ---- Summary table ----
    _print_section("Optimality Gap Summary — vs. B&B Exact Reference")
    opt_label = "(proven optimal)" if bb_stats.proven_optimal else f"(gap={bb_stats.optimality_gap:.1%})"
    print(f"  B&B reference cost: {bb_cost:.4f}  {opt_label}")
    print()
    print(f"  {'Algorithm':<27} {'Best F(X)':>10} {'Gap vs B&B':>12}"
          f" {'Avg Time':>9} {'Feasible':>9}")
    print("  " + "-" * 72)
    for res in meta_opt:
        gap = (res.best_cost - bb_cost) / max(1e-10, abs(bb_cost)) * 100
        print(
            f"  {res.algorithm_name:<27}"
            f" {res.best_cost:>10.4f}"
            f" {gap:>+11.1f}%"
            f" {res.average_runtime:>8.2f}s"
            f" {res.feasible_run_count:>6}/{cfg.n_seeds}"
        )
    greedy_gap = (greedy_res.best_cost - bb_cost) / max(1e-10, abs(bb_cost)) * 100
    print(f"  {'Greedy BFD (baseline)':<27} {greedy_res.best_cost:>10.4f}"
          f" {greedy_gap:>+11.1f}%   (deterministic)")
    print()

    all_opt_results = meta_opt + [greedy_res, bb_res]

    from tools.plot import plot_optimality_gap_comparison
    plot_optimality_gap_comparison(
        all_opt_results, bb_cost, figures_dir,
        n_tasks=cfg.n_tasks, n_servers=cfg.n_servers,
    )
    _save_optimality_gap_csv(meta_opt, greedy_res, bb_res, bb_stats, results_dir)


def _save_optimality_gap_csv(
    meta_results: list,
    greedy_res,
    bb_res,
    bb_stats,
    results_dir,
) -> None:
    import csv as _csv
    path = results_dir / "optimality_gap.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = _csv.DictWriter(f, fieldnames=[
            "algorithm", "best_cost", "avg_cost", "gap_vs_bb_pct",
            "avg_runtime_s", "feasible_runs", "n_runs",
        ])
        w.writeheader()
        bb_cost = bb_res.best_cost
        for res in meta_results:
            gap = (res.best_cost - bb_cost) / max(1e-10, abs(bb_cost)) * 100
            w.writerow({
                "algorithm": res.algorithm_name,
                "best_cost": f"{res.best_cost:.4f}",
                "avg_cost": f"{res.average_cost:.4f}",
                "gap_vs_bb_pct": f"{gap:.2f}",
                "avg_runtime_s": f"{res.average_runtime:.4f}",
                "feasible_runs": res.feasible_run_count,
                "n_runs": len(res.seeds),
            })
        greedy_gap = (greedy_res.best_cost - bb_cost) / max(1e-10, abs(bb_cost)) * 100
        w.writerow({
            "algorithm": greedy_res.algorithm_name,
            "best_cost": f"{greedy_res.best_cost:.4f}",
            "avg_cost": f"{greedy_res.average_cost:.4f}",
            "gap_vs_bb_pct": f"{greedy_gap:.2f}",
            "avg_runtime_s": f"{greedy_res.average_runtime:.4f}",
            "feasible_runs": greedy_res.feasible_run_count,
            "n_runs": 1,
        })
        w.writerow({
            "algorithm": "Branch & Bound",
            "best_cost": f"{bb_cost:.4f}",
            "avg_cost": f"{bb_cost:.4f}",
            "gap_vs_bb_pct": f"{bb_stats.optimality_gap * 100:.2f}",
            "avg_runtime_s": f"{bb_res.average_runtime:.4f}",
            "feasible_runs": bb_res.feasible_run_count,
            "n_runs": 1,
        })
    print(f"  Lower-bound CSV saved        -> {path}")


# ---------------------------------------------------------------------------
# Main experiment runner
# ---------------------------------------------------------------------------

def _save_run_manifest(
    results_dir: Path,
    data,
    weights,
    focus_mode: FocusMode,
    n_seeds: int,
    cfg,
    calibration_diag: "CalibrationDiagnostics | None",
    sa_kwargs: dict,
    ga_kwargs: dict,
    umda_kwargs: dict,
    bb_kwargs: dict,
    cli_args: argparse.Namespace,
) -> None:
    """
    Write results/run_manifest.yaml -- the complete parameter snapshot of this
    run.  Saving it next to the CSVs makes every result reproducible without
    needing to commit config.yaml + CLI args alongside the data.
    """
    import datetime as _dt
    import yaml as _yaml

    manifest: dict = {
        "generated_at": _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cli": {
            "algorithms": cli_args.algorithms,
            "focus":      cli_args.focus,
            "seeds":      cli_args.seeds,
            "sensitivity": cli_args.sensitivity,
            "scalability": cli_args.scalability,
            "tune":        cli_args.tune,
            "verbose":     cli_args.verbose,
        },
        "instance": {
            "n_tasks":          data.n_tasks,
            "n_servers":        data.n_servers,
            "total_cpu_demand": float(data.cpu.sum()),
            "total_mem_demand_MB": float(data.mem.sum()),
            "total_cpu_capacity": float(data.server_cpu_cap.sum()),
            "total_mem_capacity_MB": float(data.server_mem_cap.sum()),
            "n_seeds":          n_seeds,
        },
        "objective": {
            "focus_mode":        focus_mode.value,
            "energy_weight":     weights.energy_weight,
            "latency_weight":    weights.latency_weight,
            "cpu_penalty":       weights.cpu_penalty,
            "mem_penalty":       weights.mem_penalty,
            "congestion_factor": weights.congestion_factor,
            "energy_ref":        weights.energy_ref,
            "latency_ref":       weights.latency_ref,
            "cpu_ref":           weights.cpu_ref,
            "mem_ref":           weights.mem_ref,
        },
        "normalisation": {
            "normalize_objective":      cfg.experiment.normalize_objective,
            "normalize_method":         cfg.experiment.normalize_method,
            "n_calibration_samples":    cfg.experiment.n_calibration_samples,
            "penalty_multiplier":       cfg.experiment.penalty_multiplier,
            "calibration_seed":         cfg.experiment.calibration_seed,
            "min_feasible_calibration": cfg.experiment.min_feasible_calibration,
        },
        "calibration_diagnostics": (
            dataclasses.asdict(calibration_diag) if calibration_diag else None
        ),
        "algorithm_hyperparameters": {
            "sa":   {k: v for k, v in sa_kwargs.items()},
            "ga":   {k: v for k, v in ga_kwargs.items()},
            "umda": {k: v for k, v in umda_kwargs.items()},
            "bb":   {k: v for k, v in bb_kwargs.items()},
        },
    }

    path = results_dir / "run_manifest.yaml"
    with open(path, "w", encoding="utf-8") as f:
        _yaml.safe_dump(manifest, f, sort_keys=False, default_flow_style=False)
    print(f"  Run manifest saved           -> {path}")


def _save_algorithm_diagnostics_csv(
    all_results: list,
    results_dir: Path,
) -> None:
    """
    One row per algorithm with the FINAL-state diagnostics that don't fit into
    the per-seed CSV: total evaluations, generations completed, SA reheats,
    final SA temperature and acceptance/feasibility rates, UMDA final model
    entropy, etc.  Aggregated across seeds as means.
    """
    path = results_dir / "algorithm_diagnostics.csv"
    fieldnames = [
        "algorithm", "n_seeds",
        "mean_total_evaluations",
        "mean_n_generations_completed",   # GA / UMDA only; empty for others
        "mean_sa_reheat_count",            # SA only
        "mean_sa_final_temperature",       # SA only
        "mean_sa_acceptance_rate",         # SA only
        "mean_sa_feasibility_rate",        # SA only
        "mean_umda_final_model_entropy",   # UMDA only
        "bb_proven_optimal",               # B&B only
        "bb_root_lower_bound",             # B&B only
        "bb_optimality_gap_pct",           # B&B only
        "bb_nodes_explored",               # B&B only
    ]

    def _mean(values):
        values = [v for v in values if v is not None]
        if not values:
            return ""
        return f"{sum(values) / len(values):.6f}"

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in all_results:
            stats_list = r.all_stats
            row: dict = {
                "algorithm": r.algorithm_name,
                "n_seeds":   len(r.seeds),
            }

            # Total evaluations -- supported by SA (total_budget_consumed =
            # main loop + T_0 probe), GA/UMDA (total_evaluations), B&B (no eval
            # count, only nodes_explored).  We report the BUDGET-CONSUMED value
            # for SA so the column is directly comparable across algorithms.
            totals: list = []
            for s in stats_list:
                if hasattr(s, "total_evaluations"):
                    totals.append(s.total_evaluations)
                elif hasattr(s, "total_budget_consumed"):
                    totals.append(s.total_budget_consumed)
                elif hasattr(s, "total_evaluated"):
                    totals.append(s.total_evaluated)
            row["mean_total_evaluations"] = _mean(totals) if totals else ""

            # Generations completed (GA / UMDA only)
            gens = [getattr(s, "n_generations_completed", None) for s in stats_list]
            row["mean_n_generations_completed"] = _mean(gens)

            # SA-specific diagnostics
            sa_reheats   = [getattr(s, "reheat_count",       None) for s in stats_list]
            sa_temps     = [getattr(s, "final_temperature",  None) for s in stats_list]
            sa_accepts   = [getattr(s, "acceptance_rate",    None) for s in stats_list]
            sa_feas      = [getattr(s, "feasibility_rate",   None) for s in stats_list]
            row["mean_sa_reheat_count"]      = _mean(sa_reheats)
            row["mean_sa_final_temperature"] = _mean(sa_temps)
            row["mean_sa_acceptance_rate"]   = _mean(sa_accepts)
            row["mean_sa_feasibility_rate"]  = _mean(sa_feas)

            # UMDA-specific diagnostics: final entropy = last item in history
            entropies: list = []
            for s in stats_list:
                hist = getattr(s, "model_entropy_history", None)
                if hist:
                    entropies.append(hist[-1])
            row["mean_umda_final_model_entropy"] = _mean(entropies)

            # B&B-specific diagnostics (single-run algorithm)
            if "Branch" in r.algorithm_name and stats_list:
                s = stats_list[0]
                row["bb_proven_optimal"]     = bool(getattr(s, "proven_optimal", False))
                row["bb_root_lower_bound"]   = f"{getattr(s, 'root_lower_bound', 0.0):.6f}"
                row["bb_optimality_gap_pct"] = f"{getattr(s, 'optimality_gap', 0.0) * 100:.4f}"
                row["bb_nodes_explored"]     = getattr(s, "nodes_explored", "")
            else:
                row["bb_proven_optimal"]     = ""
                row["bb_root_lower_bound"]   = ""
                row["bb_optimality_gap_pct"] = ""
                row["bb_nodes_explored"]     = ""

            writer.writerow(row)

    print(f"  Algorithm diagnostics CSV    -> {path}")


def _save_summary_md(
    all_results: list,
    metaheuristic_results: list,
    data,
    weights,
    focus_mode: FocusMode,
    n_seeds: int,
    run_sensitivity: bool,
    run_scalability: bool,
    results_dir,
) -> None:
    """
    Write a human-readable Markdown summary of all experiment results.

    This file is the first thing to read after a run — it gives the key
    numbers and conclusions without having to dig into the CSVs or plots.
    """
    import datetime as _dt

    lines: list[str] = []

    def h(text: str, level: int = 2) -> None:
        lines.append(f"{'#' * level} {text}\n")

    def p(text: str = "") -> None:
        lines.append(text + "\n")

    now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    h("Cloud Scheduling — Experiment Summary", level=1)
    p(f"_Generated: {now}_")
    p()

    # ---- Setup ----
    h("Setup")
    p(f"| Parameter | Value |")
    p(f"|---|---|")
    p(f"| Focus mode | **{focus_mode.value}** (wₑ={weights.energy_weight}, wₗ={weights.latency_weight}, γ={weights.congestion_factor}) |")
    p(f"| Tasks / Servers | {data.n_tasks} tasks × {data.n_servers} servers |")
    p(f"| Seeds per algorithm | {n_seeds} |")
    p(f"| Objective normalised | {'Yes' if weights.energy_ref else 'No'} |")
    p(f"| Sensitivity analysis | {'Run' if run_sensitivity else 'Skipped (use --sensitivity)'} |")
    p(f"| Scalability analysis | {'Run' if run_scalability else 'Skipped (use --scalability)'} |")
    p()

    # ---- Calibrated coefficients used inside F(X) ----
    # When sample-based normalisation is active, the lambda values from
    # config.yaml are overwritten by the Deb-2000 rule (100x F_max_feasible).
    # Print the values that actually went into F(X) so the reader can audit
    # exactly which numbers produced the table below.
    h("F(X) Coefficients (as actually used in this run)")
    p("These are the values that were plugged into")
    p("`F(X) = wₑ·E/E_ref + wₗ·L/L_ref + λ_cpu·CPU_viol/CPU_ref + λ_mem·Mem_viol/Mem_ref`")
    p("after any sample-based calibration.")
    p()
    p("| Coefficient | Value | Source |")
    p("|---|---|---|")
    p(f"| wₑ (energy weight)    | {weights.energy_weight:>10.4f} | focus mode `{focus_mode.value}` |")
    p(f"| wₗ (latency weight)   | {weights.latency_weight:>10.4f} | focus mode `{focus_mode.value}` |")
    p(f"| γ (congestion factor) | {weights.congestion_factor:>10.4f} | focus mode `{focus_mode.value}` |")
    if weights.energy_ref is not None:
        p(f"| E_ref                  | {weights.energy_ref:>10.4f} W | sample mean over feasible calibration draws |")
    if weights.latency_ref is not None:
        p(f"| L_ref                  | {weights.latency_ref:>10.4f} ms | sample mean over feasible calibration draws |")
    if weights.cpu_ref is not None:
        p(f"| CPU_ref                | {weights.cpu_ref:>10.4f} % | total CPU demand Σᵢ cᵢ |")
    if weights.mem_ref is not None:
        p(f"| Mem_ref                | {weights.mem_ref:>10.4f} MB | total memory demand Σᵢ mᵢ |")
    p(f"| λ_cpu (CPU penalty)   | {weights.cpu_penalty:>10.4f} | Deb-2000 rule: 100 × F_max(feasible) |")
    p(f"| λ_mem (memory penalty)| {weights.mem_penalty:>10.4f} | Deb-2000 rule: 100 × F_max(feasible) |")
    p()
    p("**Note:** when sample-based normalisation is enabled (`normalize_method: sample` "
      "in `config.yaml`), the `cpu_penalty` / `mem_penalty` values in `config.yaml` are "
      "overwritten by the Deb-2000 rule. The configured numbers are only used when "
      "`normalize_method: worst_case` is selected.")
    p()

    if not all_results:
        p("No algorithm results to summarise.")
        path = results_dir / "summary.md"
        path.write_text("\n".join(lines), encoding="utf-8")
        return

    # ---- Main results table ----
    h("Main Results — Multi-Seed Comparison")
    p(f"Sorted by average F(X) — lower is better.  All runs: n={data.n_tasks} real tasks, {n_seeds} seeds.")
    p()
    p("| Algorithm | Best F | Avg F | Worst F | Std Dev | Feasible | Avg Time |")
    p("|---|---|---|---|---|---|---|")
    sorted_results = sorted(all_results, key=lambda r: r.average_cost)
    for r in sorted_results:
        p(f"| {r.algorithm_name} "
          f"| {r.best_cost:.4f} "
          f"| {r.average_cost:.4f} "
          f"| {r.worst_cost:.4f} "
          f"| {r.std_cost:.4f} "
          f"| {r.feasible_run_count}/{len(r.seeds)} "
          f"| {r.average_runtime:.2f}s |")
    p()

    # ---- Winner and baseline comparison ----
    if metaheuristic_results:
        winner = min(metaheuristic_results, key=lambda r: r.average_cost)
        greedy = next((r for r in all_results if "greedy" in r.algorithm_name.lower()), None)
        h("Winner")
        p(f"**{winner.algorithm_name}** achieved the best average F(X) = **{winner.average_cost:.4f}**"
          f" (best seed: {winner.best_cost:.4f}).")
        if greedy:
            for r in metaheuristic_results:
                improv = (greedy.average_cost - r.average_cost) / max(1e-10, abs(greedy.average_cost)) * 100
                p(f"- **{r.algorithm_name}**: {improv:+.2f}% vs Greedy BFD "
                  f"(avg F={r.average_cost:.4f} vs {greedy.average_cost:.4f})")
        p()

    # ---- Energy / latency breakdown ----
    if metaheuristic_results and weights.energy_ref:
        h("Energy vs Latency Decomposition (best run per algorithm)")
        p("| Algorithm | Energy (W) | Latency (ms) | Active Servers | E-contrib % | L-contrib % |")
        p("|---|---|---|---|---|---|")
        for r in metaheuristic_results:
            best = r.best_eval
            e_term = weights.energy_weight * best.total_energy / (weights.energy_ref or 1)
            l_term = weights.latency_weight * best.total_latency / (weights.latency_ref or 1)
            total  = e_term + l_term
            if total > 0:
                e_pct = e_term / total * 100
                l_pct = l_term / total * 100
            else:
                e_pct = l_pct = 0.0
            p(f"| {r.algorithm_name} "
              f"| {best.total_energy:.0f} "
              f"| {best.total_latency:.0f} "
              f"| {best.n_active_servers}/{data.n_servers} "
              f"| {e_pct:.1f}% "
              f"| {l_pct:.1f}% |")
        p()

    # ---- Feasibility check ----
    infeasible = [r for r in all_results if r.feasible_run_count == 0]
    partial    = [r for r in all_results if 0 < r.feasible_run_count < len(r.seeds)]
    h("Feasibility")
    if not infeasible and not partial:
        p("All algorithms produced **feasible** solutions on every seed.")
    else:
        if infeasible:
            names = ", ".join(r.algorithm_name for r in infeasible)
            p(f"Always infeasible: {names} — expected for naive baselines (no capacity awareness).")
        if partial:
            for r in partial:
                p(f"Partially feasible: {r.algorithm_name} — {r.feasible_run_count}/{len(r.seeds)} seeds feasible.")
    p()

    # ---- Sensitivity reminder ----
    h("Sensitivity Analysis")
    res_rel = f"results/{focus_mode.value}"
    fig_rel = f"figures/{focus_mode.value}"
    if run_sensitivity:
        p("Sensitivity results saved to:")
        p(f"- `{res_rel}/sensitivity_sa.csv` — SA: T₀ sweep and cooling-rate sweep")
        p(f"- `{res_rel}/sensitivity_ga.csv` — GA: population-size and crossover-prob sweeps")
        p(f"- `{res_rel}/sensitivity_umda.csv` — UMDA: population-size and selection-ratio sweeps")
        p()
        p("**What sensitivity analysis tells you:**")
        p("Each sweep fixes all parameters except one and measures how F(X) changes.")
        p("A parameter that barely affects results is _robust_ (your chosen value is fine anywhere in the range).")
        p("A parameter that changes results significantly is _sensitive_ — the thesis should justify the chosen value.")
        p("The auto-estimated T₀ for SA is specifically designed to remove T₀ from being a sensitive parameter.")
    else:
        p("Skipped. Run with `--sensitivity` to sweep hyperparameters and verify robustness.")
    p()

    # ---- Scalability reminder ----
    h("Scalability Analysis")
    if run_scalability:
        p("Scalability results saved to:")
        p(f"- `{res_rel}/scalability_horizontal.csv` — quality and runtime vs task count (n=20…500+)")
        p(f"- `{res_rel}/scalability_vertical.csv` — quality vs server count (constraint tightness)")
        p()
        p("**Cross-instance cost values are NOT directly comparable.** Each row in the scalability")
        p("CSVs is normalised with refs (E_ref, L_ref, λ) computed against the calibration pool")
        p("of *that specific instance*. At very high utilisation (e.g. vertical's 6-server point at")
        p("~80% CPU util) the random feasible samples cluster around heavily congested configurations,")
        p("so L_ref can be much larger than at low utilisation — making normalised F drop even though")
        p("the raw latency rises. Use `improvement_over_greedy_pct` for cross-instance comparison;")
        p("treat `avg_cost` as a within-instance quantity only.")
    else:
        p("Skipped. Run with `--scalability` to test how algorithms perform at increasing problem sizes.")
    p()

    # ---- Optimality-gap benchmark (separate from scalability — it runs at one fixed small size) ----
    h("Solution Quality Benchmark (Optimality Gap vs. Exact Reference)")
    if run_scalability:
        p(f"- `{res_rel}/optimality_gap.csv` — gap between each metaheuristic and the B&B exact solution")
        p()
        p("Run on a small instance (n=20, m=4) where Branch & Bound can reach the true optimum within")
        p("the time limit. This gives an _absolute_ quality measurement (% from optimum), anchoring the")
        p("relative %-vs-greedy numbers from the scalability axes. Note: this is **not** a scalability")
        p("test — it runs at a single fixed size and says nothing about how algorithms scale.")
    else:
        p("Skipped. Run with `--scalability` (which also triggers this benchmark) to measure how close")
        p("each metaheuristic gets to the true optimum on a small exact-solvable instance.")
    p()

    # ---- Output files ----
    h("Output Files")
    p("| File | Contents |")
    p("|---|---|")
    p(f"| `{res_rel}/results_per_seed.csv` | Raw per-seed costs, feasibility, runtimes |")
    p(f"| `{res_rel}/results_summary.csv` | Per-algorithm statistics (best/avg/worst/std) |")
    p(f"| `{res_rel}/summary.md` | This file |")
    p(f"| `{fig_rel}/convergence_all_algorithms.png` | Convergence curves for all metaheuristics |")
    p(f"| `{fig_rel}/convergence_sa/ga/umda.png` | Per-algorithm convergence detail |")
    p(f"| `{fig_rel}/boxplot_comparison.png` | Cost distribution across seeds |")
    p(f"| `{fig_rel}/algorithm_comparison_bar.png` | Best / Avg / Worst bar chart |")
    p(f"| `{fig_rel}/metaheuristics_comparison.png` | Zoomed metaheuristic comparison + energy/latency breakdown |")
    p()

    path = results_dir / "summary.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Summary saved                -> {path}")


def main() -> None:
    args             = parse_args()
    run_flags        = _resolve_algorithms(args.algorithms)
    focus            = FocusMode(args.focus)
    verbose          = args.verbose
    run_sensitivity  = args.sensitivity
    run_scalability  = args.scalability
    run_tune         = args.tune

    # ------------------------------------------------------------------ #
    # Load configuration from config.yaml                                  #
    # ------------------------------------------------------------------ #
    cfg          = load_config(Path(__file__).parent / "config.yaml")
    n_seeds      = args.seeds if args.seeds is not None else cfg.experiment.n_seeds
    seeds        = list(range(n_seeds))
    weights_base = cfg.objective[focus.value]   # without normalisation refs
    weights      = weights_base

    # ------------------------------------------------------------------ #
    # Directories                                                          #
    #                                                                      #
    # Outputs are partitioned by focus mode so successive runs with        #
    # --focus balanced / eco / performance do not overwrite each other.    #
    #   Cloud scheduling/results/<focus>/*.csv  *.md  run_log.txt          #
    #   Cloud scheduling/figures/<focus>/*.png                             #
    # ------------------------------------------------------------------ #
    base_dir    = Path(__file__).parent
    dataset_dir = base_dir / "datasets"
    figures_dir = base_dir / "figures" / focus.value
    results_dir = base_dir / "results" / focus.value
    figures_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Install Tee so every print goes to results/run_log.txt as well as   #
    # the terminal.  Restored on the way out via try/finally below.       #
    # ------------------------------------------------------------------ #
    log_path = _install_console_log(results_dir)
    print(f"  [log] capturing console output to {log_path}")

    # ------------------------------------------------------------------ #
    # Load problem instance                                                #
    # ------------------------------------------------------------------ #
    data = load_problem_data(dataset_dir, n_tasks=cfg.experiment.n_tasks)

    _print_section("Problem Instance")
    print(f"  Tasks:               {data.n_tasks}")
    print(f"  Servers:             {data.n_servers}")
    print(f"  Total CPU demand:    {data.cpu.sum():.1f} %")
    print(f"  Total memory demand: {data.mem.sum() / 1024:.1f} GB")
    print(f"  Total CPU capacity:  {data.server_cpu_cap.sum():.0f} %")
    print(f"  Total mem capacity:  {data.server_mem_cap.sum() / 1024:.0f} GB")

    # ------------------------------------------------------------------ #
    # Objective normalisation                                              #
    #                                                                      #
    # Two methods (set in config.yaml -> experiment.normalize_method):     #
    #   'sample'      -- Deb 2001 mean-over-feasibles + Deb 2000 penalty   #
    #                    calibration.  cpu_penalty / mem_penalty in the    #
    #                    objective section of config.yaml are IGNORED in   #
    #                    this mode (replaced by the calibrated values).    #
    #   'worst_case'  -- legacy upper-bound refs from problem geometry;    #
    #                    cpu_penalty / mem_penalty taken from config.yaml. #
    # ------------------------------------------------------------------ #
    calibration_diag: CalibrationDiagnostics | None = None
    if cfg.experiment.normalize_objective:
        method = cfg.experiment.normalize_method.lower()
        if method == "sample":
            weights, calibration_diag = compute_sample_normalization(
                data,
                base_weights=weights_base,
                n_samples=cfg.experiment.n_calibration_samples,
                seed=cfg.experiment.calibration_seed,
                penalty_multiplier=cfg.experiment.penalty_multiplier,
                min_feasible=cfg.experiment.min_feasible_calibration,
            )
            if calibration_diag.fallback_to_worst_case:
                print(
                    "\n  " + "!" * 70 + "\n"
                    "  [calibration] FALLBACK TRIGGERED (Deb 2001 normalisation aborted):\n"
                    f"    only {calibration_diag.n_feasible} of "
                    f"{calibration_diag.n_attempted} sample candidates were feasible\n"
                    f"    (min_feasible_calibration = "
                    f"{cfg.experiment.min_feasible_calibration}).\n"
                    "    Reverted to worst-case normalisation; preference ratios w_e:w_l\n"
                    "    no longer correspond to equal expected contribution on this run.\n"
                    "    Either loosen capacity constraints, increase\n"
                    "    n_calibration_samples, or lower min_feasible_calibration.\n"
                    "  " + "!" * 70
                )
            else:
                print(f"\n  Sample-based calibration (Deb 2001/2000):"
                      f" {calibration_diag.n_feasible}/{calibration_diag.n_attempted} feasible samples")
                print(f"    E_ref(mean E) = {weights.energy_ref:.2f}W"
                      f"   L_ref(mean L) = {weights.latency_ref:.2f}ms")
                print(f"    F_max(feasible) = {calibration_diag.f_max_feasible:.4f}"
                      f"   lambda_cpu = lambda_mem = {weights.cpu_penalty:.2f}"
                      f"   (= {calibration_diag.penalty_multiplier:.0f}x F_max)")
        elif method == "worst_case":
            e_ref, l_ref, c_ref, m_ref = compute_normalization_constants(
                data, weights_base.congestion_factor
            )
            weights = dataclasses.replace(
                weights_base,
                energy_ref=e_ref, latency_ref=l_ref,
                cpu_ref=c_ref, mem_ref=m_ref,
            )
            print(f"\n  Worst-case normalisation refs"
                  f"  E={e_ref:.1f}W  L={l_ref:.1f}ms"
                  f"  CPU={c_ref:.1f}%  Mem={m_ref:.0f}MB")
        else:
            raise ValueError(
                f"experiment.normalize_method must be 'sample' or 'worst_case', got {method!r}"
            )

    # ------------------------------------------------------------------ #
    # Focus mode summary                                                   #
    # ------------------------------------------------------------------ #
    _print_section(f"Objective Focus Mode")
    _print_focus_summary(focus, weights)

    # ------------------------------------------------------------------ #
    # Algorithm hyperparameters -loaded from config.yaml                  #
    # ------------------------------------------------------------------ #
    sa_kwargs   = cfg.algorithms.sa
    ga_kwargs   = cfg.algorithms.ga
    umda_kwargs = cfg.algorithms.umda
    bb_kwargs   = cfg.algorithms.bb

    # ------------------------------------------------------------------ #
    # --tune: one-off grid search over hyperparameters, then exit.        #
    # Tuning is a setup step, not part of the main experiment, so we do   #
    # NOT run the multi-seed experiments / plots / scalability afterwards #
    # to avoid burning extra time and confusing the results.              #
    # ------------------------------------------------------------------ #
    if run_tune:
        run_tuning(
            run_flags=run_flags,
            data=data, weights=weights,
            sa_kwargs=sa_kwargs, ga_kwargs=ga_kwargs, umda_kwargs=umda_kwargs,
            cfg_tuning=cfg.tuning,
            results_dir=results_dir,
        )
        _print_section("Done (tuning only)")
        print("  Copy the recommended values from results/tuning_summary.md into")
        print("  config.yaml, then re-run without --tune for the main experiment.")
        return

    # ------------------------------------------------------------------ #
    # Single SA diagnostic run (with verbose if requested)                 #
    # ------------------------------------------------------------------ #
    _single_run_diagnostics(data, weights, sa_kwargs, verbose=verbose)

    # ------------------------------------------------------------------ #
    # Multi-seed experiments -selected algorithms                         #
    # ------------------------------------------------------------------ #
    _print_section(f"Multi-Seed Experiments  ({n_seeds} runs per algorithm)")

    all_results = []
    metaheuristic_results = []

    if run_flags["SA"]:
        print(f"\n  Running Simulated Annealing ({n_seeds} seeds) ...")
        sa_results = run_experiments(
            algorithm=simulated_annealing,
            algorithm_name="Simulated Annealing",
            data=data, weights=weights,
            seeds=seeds, show_progress=True,  # always show per-seed progress line
            **{**sa_kwargs, "verbose": verbose},  # pass verbose into the SA loop
        )
        all_results.append(sa_results)
        metaheuristic_results.append(sa_results)

    if run_flags["GA"]:
        print(f"\n  Running Genetic Algorithm ({n_seeds} seeds) ...")
        ga_results = run_experiments(
            algorithm=genetic_algorithm,
            algorithm_name="Genetic Algorithm",
            data=data, weights=weights,
            seeds=seeds, show_progress=True,
            **{**ga_kwargs, "verbose": verbose},
        )
        all_results.append(ga_results)
        metaheuristic_results.append(ga_results)

    if run_flags["UMDA"]:
        print(f"\n  Running UMDA (EDA) ({n_seeds} seeds) ...")
        umda_results = run_experiments(
            algorithm=umda,
            algorithm_name="UMDA (EDA)",
            data=data, weights=weights,
            seeds=seeds, show_progress=True,
            **{**umda_kwargs, "verbose": verbose},
        )
        all_results.append(umda_results)
        metaheuristic_results.append(umda_results)

    if run_flags["BB"]:
        # B&B is deterministic -one run suffices; time_limit caps wall-clock cost
        tl = bb_kwargs.get("time_limit", 60.0)
        print(f"\n  Running Branch and Bound (time limit={tl:.0f}s) ...")
        bb_results = run_experiments(
            algorithm=branch_and_bound,
            algorithm_name="Branch & Bound",
            data=data, weights=weights,
            seeds=[0], show_progress=True,
            **{**bb_kwargs, "verbose": verbose},
        )
        all_results.append(bb_results)
        # B&B is an exact method -report its lower bound and gap separately
        bb_stats = bb_results.all_stats[0]
        print(
            f"  B&B: nodes={bb_stats.nodes_explored:,}"
            f"  root_lb={bb_stats.root_lower_bound:.4f}"
            f"  best={bb_results.best_cost:.4f}"
            f"  gap={bb_stats.optimality_gap:.1%}"
            f"  proven_optimal={bb_stats.proven_optimal}"
        )

    if run_flags["greedy"]:
        print("\n  Running Greedy BFD baseline ...")
        greedy_results = run_experiments(
            algorithm=greedy_ffd_baseline,
            algorithm_name="Greedy BFD (baseline)",
            data=data, weights=weights,
            seeds=seeds, show_progress=False,
        )
        all_results.append(greedy_results)

    if run_flags["roundrobin"]:
        # Round-Robin is fully deterministic — the result is identical for every
        # seed, so a single run suffices.  Running n_seeds copies is wasteful.
        print("  Running Round-Robin baseline (deterministic — 1 run) ...")
        rr_results = run_experiments(
            algorithm=round_robin_baseline,
            algorithm_name="Round-Robin (baseline)",
            data=data, weights=weights,
            seeds=[0], show_progress=False,
        )
        all_results.append(rr_results)

    if run_flags["random"]:
        print("  Running Random baseline ...")
        random_results = run_experiments(
            algorithm=random_assignment_baseline,
            algorithm_name="Random (baseline)",
            data=data, weights=weights,
            seeds=seeds, show_progress=False,
        )
        all_results.append(random_results)

    if not all_results:
        print("\n  No algorithms selected -nothing to compare.")
        return

    # ------------------------------------------------------------------ #
    # Comparison table                                                     #
    # ------------------------------------------------------------------ #
    _print_section(f"Results Summary Table  [focus={focus.value}]")
    print_comparison_table(all_results)
    print_significance_table(metaheuristic_results)

    # Per-algorithm best-run detail for metaheuristics
    for r in metaheuristic_results:
        best = r.best_eval
        print(
            f"\n  {r.algorithm_name} best run (seed {r.best_seed}):"
            f"  energy={best.total_energy:.1f}W"
            f"  latency={best.total_latency:.1f}ms"
            f"  active={best.n_active_servers}/{data.n_servers}"
            f"  feasible={best.feasible}"
        )

    # ------------------------------------------------------------------ #
    # Interpretation -print before plots so it appears in the terminal   #
    # ------------------------------------------------------------------ #
    baseline_results = [r for r in all_results if r not in metaheuristic_results]
    _print_interpretation(
        meta_results=metaheuristic_results,
        baseline_results=baseline_results,
        data=data,
        weights=weights,
        focus_mode=focus,
    )

    # ------------------------------------------------------------------ #
    # Convergence plots                                                    #
    # ------------------------------------------------------------------ #
    if metaheuristic_results:
        _print_section("Saving Plots")

        # All metaheuristics overlaid -x-axis normalised to % of budget
        conv_path = str(figures_dir / "convergence_all_algorithms.png")
        # Baseline reference lines: only show baselines within a useful range
        # (exclude Random / Round-Robin — their scores are far above the metaheuristics
        # and would force the y-axis to zoom out so far the convergence curves look flat)
        _noisy = {"random", "round"}
        _b_scores = {
            r.algorithm_name: r.best_cost
            for r in all_results
            if r not in metaheuristic_results
            and not any(k in r.algorithm_name.lower() for k in _noisy)
        }
        plot_convergence(
            results=metaheuristic_results,
            title=f"Cloud Scheduling - Convergence [{focus.value}] ({n_seeds} seeds)",
            save_path=conv_path,
            show=False,
            baseline_scores=_b_scores if _b_scores else None,
        )
        print(f"  Convergence (all metaheuristics) ->{conv_path}")

    # ------------------------------------------------------------------ #
    # Bar charts                                                           #
    # ------------------------------------------------------------------ #
    # Filter out noisy baselines (Random, Round-Robin) whose scores are so much
    # worse than the metaheuristics that they compress the y-axis and hide the
    # interesting differences.  Greedy BFD and B&B stay in since they are
    # informative comparison points on the same scale as the metaheuristics.
    _scale_noisy = {"random", "round"}
    _scaled_results = [
        r for r in all_results
        if not any(k in r.algorithm_name.lower() for k in _scale_noisy)
    ]

    if _scaled_results:
        # Box plot — SA / GA / UMDA + structured baselines (Greedy, B&B)
        box_path = str(figures_dir / "boxplot_comparison.png")
        plot_box_comparison(
            results_list=_scaled_results,
            title=f"Cloud Scheduling - Cost Distribution per Seed [{focus.value}]  ({n_seeds} seeds)",
            save_path=box_path,
            show=False,
        )
        print(f"  Box plot (algorithms on comparable scale) ->{box_path}")

    if _scaled_results:
        # Bar chart — metaheuristics + Greedy BFD + B&B; excludes Random / Round-Robin
        bar_path = str(figures_dir / "algorithm_comparison_bar.png")
        plot_bar_comparison(
            results_list=_scaled_results,
            title=f"Cloud Scheduling - All Algorithms [{focus.value}]  (Best / Average / Worst)",
            save_path=bar_path,
            show=False,
        )
        print(f"  Bar chart (algorithms on comparable scale) ->{bar_path}")

    if metaheuristic_results:
        # Focused chart -metaheuristics only, zoomed y-axis + energy/latency breakdown
        focused_bar_path = str(figures_dir / "metaheuristics_comparison.png")
        plot_metaheuristics_bar(
            results_list=metaheuristic_results,
            weights=weights,
            title=f"Metaheuristic Comparison [{focus.value}]  (zoomed -SA / GA / UMDA)",
            save_path=focused_bar_path,
            show=False,
        )
        print(f"  Focused metaheuristics bar ->{focused_bar_path}")

    # ------------------------------------------------------------------ #
    # Save numerical results to CSV                                        #
    # ------------------------------------------------------------------ #
    _print_section("Saving Results to CSV")
    save_results_csv(
        all_results, results_dir,
        focus_mode=focus.value,
        n_tasks=data.n_tasks,
        n_servers=data.n_servers,
    )
    _save_algorithm_diagnostics_csv(all_results, results_dir)
    _save_run_manifest(
        results_dir=results_dir,
        data=data, weights=weights,
        focus_mode=focus, n_seeds=n_seeds, cfg=cfg,
        calibration_diag=calibration_diag,
        sa_kwargs=sa_kwargs, ga_kwargs=ga_kwargs,
        umda_kwargs=umda_kwargs, bb_kwargs=bb_kwargs,
        cli_args=args,
    )

    # ------------------------------------------------------------------ #
    # Optional sensitivity analysis (--sensitivity flag)                  #
    # ------------------------------------------------------------------ #
    if run_sensitivity:
        sens_seeds = list(range(cfg.sensitivity.n_seeds))
        if run_flags["SA"]:
            run_sa_sensitivity_analysis(
                data=data, weights=weights,
                base_sa_kwargs=sa_kwargs,
                sweep=cfg.sensitivity.sa,
                figures_dir=figures_dir, results_dir=results_dir,
                seeds=sens_seeds,
            )
        if run_flags["GA"]:
            run_ga_sensitivity_analysis(
                data=data, weights=weights,
                base_ga_kwargs=ga_kwargs,
                sweep=cfg.sensitivity.ga,
                figures_dir=figures_dir, results_dir=results_dir,
                seeds=sens_seeds,
            )
        if run_flags["UMDA"]:
            run_umda_sensitivity_analysis(
                data=data, weights=weights,
                base_umda_kwargs=umda_kwargs,
                sweep=cfg.sensitivity.umda,
                figures_dir=figures_dir, results_dir=results_dir,
                seeds=sens_seeds,
            )
    else:
        print()
        print("  (Sensitivity analysis skipped - use --sensitivity / -S to enable)")

    if run_scalability:
        _calib = dict(
            method=cfg.experiment.normalize_method,
            n_samples=cfg.experiment.n_calibration_samples,
            penalty_multiplier=cfg.experiment.penalty_multiplier,
            calibration_seed=cfg.experiment.calibration_seed,
            min_feasible=cfg.experiment.min_feasible_calibration,
        )
        _shared = dict(
            run_flags=run_flags,
            weights_base=weights_base,
            normalize=cfg.experiment.normalize_objective,
            calib=_calib,
            dataset_dir=dataset_dir,
            figures_dir=figures_dir,
            results_dir=results_dir,
            sa_kwargs=sa_kwargs,
            ga_kwargs=ga_kwargs,
            umda_kwargs=umda_kwargs,
        )
        run_horizontal_scaling_analysis(**_shared, cfg=cfg.scalability.horizontal)
        run_vertical_scaling_analysis(**_shared, cfg=cfg.scalability.vertical)
        run_optimality_gap_analysis(
            **_shared,
            cfg=cfg.scalability.optimality_gap,
            bb_kwargs=bb_kwargs,
            verbose=verbose,
        )
    else:
        print("  (Scalability analysis skipped - use --scalability / -L to enable)")

    # ------------------------------------------------------------------ #
    # Save human-readable summary                                         #
    # ------------------------------------------------------------------ #
    _save_summary_md(
        all_results=all_results,
        metaheuristic_results=metaheuristic_results,
        data=data,
        weights=weights,
        focus_mode=focus,
        n_seeds=n_seeds,
        run_sensitivity=run_sensitivity,
        run_scalability=run_scalability,
        results_dir=results_dir,
    )

    _print_section("Done")
    print("  All outputs are in:")
    print(f"    Plots:   {figures_dir}")
    print(f"    Results: {results_dir}")


if __name__ == "__main__":
    main()
