"""
main.py — Entry point for the Cloud Scheduling experiments.

PURPOSE
-------
This is the top-level orchestration script for the Cloud Scheduling problem.
It wires together every module in this package, runs all algorithms over
multiple random seeds, and produces the tables, plots, and CSV files used
in the thesis.

WHAT IT DOES
------------
1.  Loads 50 tasks from the dataset and synthesises a 10-server pool.
2.  Prints a diagnostic single-run with Simulated Annealing, showing the
    full solution breakdown and SA internal statistics (acceptance rates,
    reheat count, etc.).  Useful for verifying the implementation is working
    and for tuning hyperparameters.
3.  Runs a 10-seed experiment for each of the six algorithms:
        Simulated Annealing (SA)
        Genetic Algorithm    (GA)
        UMDA                 (Univariate Marginal Distribution Algorithm / EDA)
        Greedy FFD           (deterministic construction baseline)
        Round-Robin          (cyclic assignment baseline)
        Random Assignment    (random baseline)
4.  Prints a unified comparison table ready to paste into the thesis.
5.  Saves a convergence plot comparing SA, GA, and UMDA side by side.
6.  Saves a bar chart comparing all six algorithms on Best / Average / Worst.
7.  Saves per-seed and per-algorithm CSV files for statistical analysis.
8.  Optionally runs a Simulated Annealing sensitivity analysis (set
    RUN_SENSITIVITY = True at the top of this file) that sweeps over
    initial temperatures and cooling rates, saving results to CSV.

HOW TO RUN
----------
    uv run run.py cloud         # from the project root (recommended)
    uv run --with numpy --with pandas --with matplotlib python main.py
                                # from inside this directory

SENSITIVITY ANALYSIS FLAG
--------------------------
Set RUN_SENSITIVITY = True below to also run the SA hyperparameter sweep.
This adds roughly 3–5 minutes to the total runtime.  It is disabled by
default so that normal experiment runs stay fast.

PARAMETER DESIGN RATIONALE
----------------------------
All algorithm hyperparameters below are documented with their justification.
These descriptions should be reproduced or cited in the thesis Methodology
section.

SA hyperparameters:
  initial_temperature = 5000:
    Tuned so that ~70–80% of worsening moves are accepted at step 0.
    For typical Δ ≈ 100–500 at the start, P(accept) = exp(-Δ/5000) ≈ 0.90.
  cooling_rate = 0.995:
    Temperature halves every ≈138 steps.  Over 3000 steps the temperature
    drops from 5000 to ≈5×10⁻⁷, achieving thorough exploitation at the end.
  iterations_per_temperature = 50:
    50 neighbourhood evaluations per temperature level.  Combined with 3000
    levels this gives 150,000 total evaluations for budget comparison.
  reheat_patience = 300:
    Reheat after ≈2 cooling half-lives with no improvement.  Prevents the
    search from getting trapped prematurely in a deep local basin.

GA hyperparameters:
  population_size = 50:
    Standard for problems of this size (50 tasks).  Provides diversity while
    staying computationally affordable.
  n_generations = 3000:
    Gives ≈144,050 total evaluations (matching SA's ≈150,000 for fair comparison).
  tournament_size = 3:
    Moderate selection pressure.  Favours good individuals without eliminating
    diversity too quickly.
  crossover_prob = 0.8, mutation_prob = 1/n_tasks:
    Standard EA parameter settings.  Crossover is the primary search driver;
    mutation provides background diversity.

UMDA hyperparameters:
  population_size = 100:
    Larger population gives more reliable probability estimates for the model.
  n_generations = 1500:
    Gives ≈148,600 total evaluations (matching SA and GA for fair comparison).
  selection_ratio = 0.5:
    Keep the top 50% of the population for model learning (truncation selection).
  smoothing = 0.1:
    Laplace smoothing prevents zero-probability server assignments.
"""
import csv
import time
from collections import Counter
from pathlib import Path

from tools.data_loader import load_problem_data
from tools.objective import ObjectiveWeights
from algorithms.simulated_annealing import simulated_annealing
from algorithms.genetic_algorithm import genetic_algorithm
from algorithms.umda import umda
from algorithms.baselines import (
    greedy_ffd_baseline,
    round_robin_baseline,
    random_assignment_baseline,
)
from tools.experiment import run_experiments
from tools.plot import (
    plot_convergence,
    plot_bar_comparison,
    print_comparison_table,
    save_results_csv,
)

# ---------------------------------------------------------------------------
# Global flags
# ---------------------------------------------------------------------------

# Set to True to also run the SA sensitivity analysis (adds ~3–5 minutes).
RUN_SENSITIVITY = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _print_section(title: str) -> None:
    """Print a clearly visible section heading."""
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


def _single_run_diagnostics(data, weights, sa_kwargs) -> None:
    """
    Run SA once without a fixed seed and print a detailed solution breakdown.

    This section is useful during development and parameter tuning:
    it shows exactly how the final solution looks, which servers are used,
    and what the SA search statistics were.  It does not affect the
    multi-seed experiment results.
    """
    _print_section("Single SA Diagnostic Run")

    t0 = time.perf_counter()
    best_assignment, best_eval, stats = simulated_annealing(
        data=data,
        weights=weights,
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
    print(f"    Candidates evaluated:    {stats.total_evaluated}")
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
# SA sensitivity analysis
# ---------------------------------------------------------------------------

def run_sa_sensitivity_analysis(
    data,
    weights,
    base_sa_kwargs: dict,
    figures_dir: Path,
    results_dir: Path,
    n_seeds: int = 5,
) -> None:
    """
    Sweep SA hyperparameters and report how solution quality varies.

    Two independent sweeps are performed:
    1.  Vary initial_temperature with cooling_rate fixed at the base value.
    2.  Vary cooling_rate with initial_temperature fixed at the base value.

    Each configuration is run n_seeds times to average out randomness.
    Results are saved to CSV and a summary plot is saved to figures_dir.

    Parameters
    ----------
    data, weights:    Problem instance and objective weights.
    base_sa_kwargs:   Default SA parameters (temperature and rate are overridden).
    figures_dir:      Where to save the sensitivity plot.
    results_dir:      Where to save the sensitivity CSV.
    n_seeds:          Number of seeds per configuration (5 is fast but meaningful).
    """
    import matplotlib.pyplot as plt

    _print_section("SA Sensitivity Analysis")

    # Temperature sweep — 6 values spanning two orders of magnitude
    temperatures = [500.0, 1000.0, 2000.0, 5000.0, 10000.0, 20000.0]
    # Cooling rate sweep — 5 values from fast cooling to very slow cooling
    cooling_rates = [0.990, 0.992, 0.995, 0.997, 0.999]
    seeds = list(range(n_seeds))

    # --- Temperature sweep ---
    print(f"\n  Temperature sweep (cooling_rate={base_sa_kwargs['cooling_rate']}):")
    print(f"  {'T_init':>10} {'Best':>12} {'Average':>12} {'Std Dev':>10} {'Feasible':>10}")
    print("  " + "-" * 60)

    temp_rows: list[dict] = []
    for T0 in temperatures:
        kwargs = {**base_sa_kwargs, "initial_temperature": T0}
        res = run_experiments(
            algorithm=simulated_annealing,
            algorithm_name=f"SA T={T0:.0f}",
            data=data,
            weights=weights,
            seeds=seeds,
            verbose=False,
            **kwargs,
        )
        print(
            f"  {T0:>10.0f}"
            f" {res.best_cost:>12.2f}"
            f" {res.average_cost:>12.2f}"
            f" {res.std_cost:>10.2f}"
            f" {res.feasible_run_count:>8}/{n_seeds}"
        )
        temp_rows.append({
            "param": "initial_temperature",
            "value": T0,
            "best": res.best_cost,
            "average": res.average_cost,
            "worst": res.worst_cost,
            "std_dev": res.std_cost,
            "feasible": res.feasible_run_count,
        })

    # --- Cooling rate sweep ---
    print(f"\n  Cooling-rate sweep (initial_temperature={base_sa_kwargs['initial_temperature']}):")
    print(f"  {'alpha':>10} {'Best':>12} {'Average':>12} {'Std Dev':>10} {'Feasible':>10}")
    print("  " + "-" * 60)

    rate_rows: list[dict] = []
    for alpha in cooling_rates:
        kwargs = {**base_sa_kwargs, "cooling_rate": alpha}
        res = run_experiments(
            algorithm=simulated_annealing,
            algorithm_name=f"SA α={alpha}",
            data=data,
            weights=weights,
            seeds=seeds,
            verbose=False,
            **kwargs,
        )
        print(
            f"  {alpha:>10.3f}"
            f" {res.best_cost:>12.2f}"
            f" {res.average_cost:>12.2f}"
            f" {res.std_cost:>10.2f}"
            f" {res.feasible_run_count:>8}/{n_seeds}"
        )
        rate_rows.append({
            "param": "cooling_rate",
            "value": alpha,
            "best": res.best_cost,
            "average": res.average_cost,
            "worst": res.worst_cost,
            "std_dev": res.std_cost,
            "feasible": res.feasible_run_count,
        })

    # --- Save sensitivity CSV ---
    csv_path = results_dir / "sensitivity_analysis.csv"
    results_dir.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "param", "value", "best", "average", "worst", "std_dev", "feasible"
        ])
        writer.writeheader()
        writer.writerows(temp_rows + rate_rows)
    print(f"\n  Sensitivity results saved → {csv_path}")

    # --- Sensitivity line plot ---
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    # Temperature subplot
    t_vals = [r["value"] for r in temp_rows]
    t_avg  = [r["average"] for r in temp_rows]
    t_std  = [r["std_dev"]  for r in temp_rows]
    axes[0].errorbar(t_vals, t_avg, yerr=t_std, marker="o", capsize=4,
                     color="steelblue")
    axes[0].set_xlabel("Initial temperature T₀")
    axes[0].set_ylabel("Average best cost")
    axes[0].set_title("SA: sensitivity to T₀")
    axes[0].set_xscale("log")
    axes[0].grid(True, alpha=0.3)

    # Cooling rate subplot
    a_vals = [r["value"] for r in rate_rows]
    a_avg  = [r["average"] for r in rate_rows]
    a_std  = [r["std_dev"]  for r in rate_rows]
    axes[1].errorbar(a_vals, a_avg, yerr=a_std, marker="o", capsize=4,
                     color="darkorange")
    axes[1].set_xlabel("Cooling rate α")
    axes[1].set_ylabel("Average best cost")
    axes[1].set_title("SA: sensitivity to cooling rate α")
    axes[1].grid(True, alpha=0.3)

    plt.suptitle("SA Hyperparameter Sensitivity Analysis", fontsize=13)
    plt.tight_layout()
    plot_path = str(figures_dir / "sa_sensitivity.png")
    fig.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Sensitivity plot saved  → {plot_path}")


# ---------------------------------------------------------------------------
# Main experiment runner
# ---------------------------------------------------------------------------

def main() -> None:
    # ------------------------------------------------------------------ #
    # Directories                                                          #
    # ------------------------------------------------------------------ #
    base_dir    = Path(__file__).parent
    dataset_dir = base_dir / "datasets"
    figures_dir = base_dir / "figures"
    results_dir = base_dir / "results"
    figures_dir.mkdir(exist_ok=True)
    results_dir.mkdir(exist_ok=True)

    # ------------------------------------------------------------------ #
    # Load problem instance                                                #
    # ------------------------------------------------------------------ #
    data = load_problem_data(dataset_dir, n_tasks=50)

    _print_section("Problem Instance")
    print(f"  Tasks:               {data.n_tasks}")
    print(f"  Servers:             {data.n_servers}")
    print(f"  Total CPU demand:    {data.cpu.sum():.1f} %")
    print(f"  Total memory demand: {data.mem.sum() / 1024:.1f} GB")
    print(f"  Total CPU capacity:  {data.server_cpu_cap.sum():.0f} %")
    print(f"  Total mem capacity:  {data.server_mem_cap.sum() / 1024:.0f} GB")

    # ------------------------------------------------------------------ #
    # Shared objective weights                                             #
    # (documented in the Methodology section of the thesis)               #
    # ------------------------------------------------------------------ #
    weights = ObjectiveWeights(
        energy_weight=1.0,
        latency_weight=1.0,
        cpu_penalty=1000.0,    # λ_cpu: penalises CPU overcapacity heavily
        mem_penalty=5.0,       # λ_mem: smaller because violations are large in MB
        congestion_factor=1.0, # γ:    linear congestion model
    )

    # ------------------------------------------------------------------ #
    # Algorithm hyperparameters                                            #
    # ------------------------------------------------------------------ #

    # SA — tuned so that total evaluations ≈ 150,000
    sa_kwargs = dict(
        initial_temperature=5000.0,
        cooling_rate=0.995,
        min_temperature=1e-3,
        iterations_per_temperature=50,   # 50 × 3000 steps = 150,000 evals
        max_temp_steps=3000,
        reheat_patience=300,
        reheat_factor=0.4,
    )

    # GA — population_size=50, n_generations=3000 → ≈144,050 evals
    ga_kwargs = dict(
        population_size=50,
        n_generations=3000,
        tournament_size=3,
        crossover_prob=0.8,
        mutation_prob=None,   # defaults to 1/n_tasks inside genetic_algorithm()
        elitism_count=2,
    )

    # UMDA — population_size=100, n_generations=1500 → ≈148,600 evals
    umda_kwargs = dict(
        population_size=100,
        n_generations=1500,
        selection_ratio=0.5,
        smoothing=0.1,
        elitism_count=1,
    )

    # Experiment settings
    seeds     = list(range(10))   # seeds 0–9 for 10 independent replications
    n_seeds   = len(seeds)

    # ------------------------------------------------------------------ #
    # Single SA diagnostic run (development / parameter verification)     #
    # ------------------------------------------------------------------ #
    _single_run_diagnostics(data, weights, sa_kwargs)

    # ------------------------------------------------------------------ #
    # Multi-seed experiments — all algorithms                              #
    # ------------------------------------------------------------------ #
    _print_section("Multi-Seed Experiments  (10 runs per algorithm)")

    print("\n  Running Simulated Annealing …")
    sa_results = run_experiments(
        algorithm=simulated_annealing,
        algorithm_name="Simulated Annealing",
        data=data, weights=weights,
        seeds=seeds, verbose=True,
        **sa_kwargs,
    )

    print("\n  Running Genetic Algorithm …")
    ga_results = run_experiments(
        algorithm=genetic_algorithm,
        algorithm_name="Genetic Algorithm",
        data=data, weights=weights,
        seeds=seeds, verbose=True,
        **ga_kwargs,
    )

    print("\n  Running UMDA (EDA) …")
    umda_results = run_experiments(
        algorithm=umda,
        algorithm_name="UMDA (EDA)",
        data=data, weights=weights,
        seeds=seeds, verbose=True,
        **umda_kwargs,
    )

    print("\n  Running baselines …")
    greedy_results = run_experiments(
        algorithm=greedy_ffd_baseline,
        algorithm_name="Greedy FFD (baseline)",
        data=data, weights=weights,
        seeds=seeds, verbose=False,
    )
    rr_results = run_experiments(
        algorithm=round_robin_baseline,
        algorithm_name="Round-Robin (baseline)",
        data=data, weights=weights,
        seeds=seeds, verbose=False,
    )
    random_results = run_experiments(
        algorithm=random_assignment_baseline,
        algorithm_name="Random (baseline)",
        data=data, weights=weights,
        seeds=seeds, verbose=False,
    )

    # Ordered list — metaheuristics first, then baselines (table row order)
    all_results = [
        sa_results,
        ga_results,
        umda_results,
        greedy_results,
        rr_results,
        random_results,
    ]

    # ------------------------------------------------------------------ #
    # Comparison table                                                     #
    # ------------------------------------------------------------------ #
    _print_section("Results Summary Table")
    print_comparison_table(all_results)

    # Print best-run detail for the three metaheuristics
    for r in [sa_results, ga_results, umda_results]:
        best = r.best_eval
        print(
            f"\n  {r.algorithm_name} best run (seed {r.best_seed}):"
            f"  energy={best.total_energy:.1f}W"
            f"  latency={best.total_latency:.1f}ms"
            f"  active={best.n_active_servers}/{data.n_servers}"
            f"  feasible={best.feasible}"
        )

    # ------------------------------------------------------------------ #
    # Convergence plot — SA, GA, UMDA overlaid                            #
    # ------------------------------------------------------------------ #
    _print_section("Saving Plots")

    conv_path = str(figures_dir / "convergence_all_algorithms.png")
    plot_convergence(
        results=[sa_results, ga_results, umda_results],
        title="Cloud Scheduling — Convergence Comparison (10 seeds)",
        xlabel="Iteration / Generation",
        save_path=conv_path,
        show=False,
    )
    print(f"  Convergence plot saved → {conv_path}")

    # Keep the original SA-only convergence plot for backward compatibility
    sa_conv_path = str(figures_dir / "sa_convergence.png")
    plot_convergence(
        results=sa_results,
        title="Simulated Annealing — Cloud Scheduling Convergence (10 seeds)",
        xlabel="Temperature step",
        save_path=sa_conv_path,
        show=False,
    )
    print(f"  SA convergence plot saved → {sa_conv_path}")

    # Bar comparison chart — all algorithms
    bar_path = str(figures_dir / "algorithm_comparison_bar.png")
    plot_bar_comparison(
        results_list=all_results,
        title="Cloud Scheduling — Algorithm Comparison (Best / Average / Worst)",
        save_path=bar_path,
        show=False,
    )
    print(f"  Bar comparison chart saved → {bar_path}")

    # ------------------------------------------------------------------ #
    # Save numerical results to CSV                                        #
    # ------------------------------------------------------------------ #
    _print_section("Saving Results to CSV")
    save_results_csv(all_results, results_dir)

    # ------------------------------------------------------------------ #
    # Optional SA sensitivity analysis                                     #
    # ------------------------------------------------------------------ #
    if RUN_SENSITIVITY:
        run_sa_sensitivity_analysis(
            data=data,
            weights=weights,
            base_sa_kwargs=sa_kwargs,
            figures_dir=figures_dir,
            results_dir=results_dir,
            n_seeds=5,
        )
    else:
        print()
        print("  (SA sensitivity analysis skipped — set RUN_SENSITIVITY = True to enable)")

    _print_section("Done")
    print("  All outputs are in:")
    print(f"    Plots:   {figures_dir}")
    print(f"    Results: {results_dir}")


if __name__ == "__main__":
    main()
