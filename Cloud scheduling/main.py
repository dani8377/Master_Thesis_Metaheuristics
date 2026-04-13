"""
main.py — Entry point for the Cloud Scheduling experiments.

PURPOSE
-------
This script is the top-level runner for the Cloud Scheduling problem.
It wires together every module in this package, configures the algorithm
parameters, executes the experiment, and produces a convergence plot.

WHAT IT DOES
------------
1.  Loads 50 tasks from the dataset and synthesises a 10-server pool.
2.  Runs a single SA run (no fixed seed) and prints a detailed diagnostic
    breakdown: objective value, energy, latency, capacity violations, active
    servers, and per-server task distribution.
3.  Runs a 10-seed experiment (seeds 0–9) so results are statistically
    meaningful and reproducible.
4.  Prints a comparison table (ready to copy into the thesis).
5.  Saves a convergence plot to figures/sa_convergence.png.

HOW TO RUN
----------
    uv run run.py cloud         # from the project root (recommended)
    uv run --with numpy --with pandas --with matplotlib python main.py
                                # from inside this directory

PARAMETER TUNING NOTES
-----------------------
initial_temperature:  5000 gives ~70–80% worsening-move acceptance at step 0
                      for this problem size (50 tasks, delta ≈ few hundred).
cooling_rate:         0.995 → temperature halves every ~138 steps.
                      With max_temp_steps=3000, final T ≈ 5000 × 0.995^3000 ≈ 5×10⁻⁷.
reheat_patience:      300 steps — roughly two cooling half-lives before reheating.
cpu_penalty:          1000 per % CPU overcapacity.  A server 100% over limit
                      contributes 100,000 to F(X) — far above any real energy
                      or latency term, ensuring SA prioritises feasibility.
mem_penalty:          5 per MB.  Memory violations can be 10,000s of MB, so
                      keeping λ_mem small (relative to λ_cpu) balances the
                      two penalties in absolute contribution to F(X).
"""
import time
from collections import Counter
from pathlib import Path

from tools.data_loader import load_problem_data
from tools.objective import ObjectiveWeights
from algorithms.simulated_annealing import simulated_annealing
from tools.experiment import run_experiments
from tools.plot import plot_convergence, print_comparison_table


def main() -> None:
    # ------------------------------------------------------------------
    # Load problem instance
    # ------------------------------------------------------------------
    dataset_dir = Path(__file__).parent / "datasets"
    data = load_problem_data(dataset_dir, n_tasks=50)

    print("=== Cloud Scheduling Problem Instance ===")
    print(f"  Tasks:               {data.n_tasks}")
    print(f"  Servers:             {data.n_servers}")
    print(f"  Total CPU demand:    {data.cpu.sum():.1f} %")
    print(f"  Total memory demand: {data.mem.sum() / 1024:.1f} GB")
    print(f"  Total CPU capacity:  {data.server_cpu_cap.sum():.0f} %")
    print(f"  Total mem capacity:  {data.server_mem_cap.sum() / 1024:.0f} GB")
    print()

    # ------------------------------------------------------------------
    # Objective weights and SA hyperparameters
    # (reported in the Methodology section of the thesis)
    # ------------------------------------------------------------------
    weights = ObjectiveWeights(
        energy_weight=1.0,
        latency_weight=1.0,
        cpu_penalty=1000.0,    # λ_cpu
        mem_penalty=5.0,       # λ_mem
        congestion_factor=1.0, # γ
    )

    sa_kwargs = dict(
        initial_temperature=5000.0,
        cooling_rate=0.995,
        min_temperature=1e-3,
        iterations_per_temperature=50,
        max_temp_steps=3000,
        reheat_patience=300,
        reheat_factor=0.4,
    )

    # ------------------------------------------------------------------
    # Single run — detailed diagnostics
    # ------------------------------------------------------------------
    print("=== Single Run ===")
    t0 = time.perf_counter()
    best_assignment, best_eval, stats = simulated_annealing(
        data=data,
        weights=weights,
        **sa_kwargs,
    )
    single_run_time = time.perf_counter() - t0

    # Solution quality
    print(f"  Feasible:              {best_eval.feasible}")
    print(f"  Objective value:       {best_eval.objective_value:.4f}")
    print(f"  Total energy (W):      {best_eval.total_energy:.2f}")
    print(f"  Total latency (ms):    {best_eval.total_latency:.2f}")
    print(f"  CPU violation (%):     {best_eval.cpu_violation:.4f}")
    print(f"  Memory violation (MB): {best_eval.mem_violation:.2f}")
    print(f"  Active servers:        {best_eval.n_active_servers}/{data.n_servers}")
    print(f"  Runtime:               {single_run_time:.2f}s")
    print()

    # SA search diagnostics — useful for tuning parameters
    print("  --- SA diagnostics ---")
    print(f"  Candidates evaluated:  {stats.total_evaluated}")
    print(f"  Improving accepted:    {stats.total_improving_accepted}")
    print(f"  Worsening accepted:    {stats.total_worsening_accepted}")
    print(f"  Structural rejections: {stats.total_rejected_structural}")
    print(f"  Acceptance rate:       {stats.acceptance_rate:.2%}")
    print(f"  Feasibility rate:      {stats.feasibility_rate:.2%}")
    print(f"  Reheat count:          {stats.reheat_count}")
    print(f"  Final temperature:     {stats.final_temperature:.6f}")
    print()

    # Per-server task distribution — shows how tasks are spread
    server_task_counts = Counter(best_assignment)
    print("  Assignment summary (server index: task count):")
    for j in range(data.n_servers):
        count = server_task_counts.get(j, 0)
        bar   = "#" * count  # ASCII bar chart for quick visual inspection
        print(f"    Server {j:>2}: {count:>3} tasks  {bar}")
    print()

    # ------------------------------------------------------------------
    # Multi-seed experiment — statistically meaningful results
    # ------------------------------------------------------------------
    print("=== Multi-Seed Experiment (10 runs) ===")
    sa_results = run_experiments(
        algorithm=simulated_annealing,
        algorithm_name="Simulated Annealing",
        data=data,
        weights=weights,
        seeds=list(range(10)),  # seeds 0–9 for reproducibility
        verbose=True,
        **sa_kwargs,
    )
    print()
    print_comparison_table([sa_results])
    print()
    print(f"  Best seed:   {sa_results.best_seed}")
    best = sa_results.best_eval
    print(f"  Best eval:   energy={best.total_energy:.2f}W"
          f"  latency={best.total_latency:.2f}ms"
          f"  active={best.n_active_servers}/{data.n_servers}"
          f"  feasible={best.feasible}")
    print()

    # ------------------------------------------------------------------
    # Convergence plot — saved to figures/
    # ------------------------------------------------------------------
    figures_dir = Path(__file__).parent / "figures"
    figures_dir.mkdir(exist_ok=True)
    save_path = str(figures_dir / "sa_convergence.png")
    plot_convergence(
        sa_results,
        title="Simulated Annealing — Cloud Scheduling Convergence (10 seeds)",
        save_path=save_path,
        show=False,   # set show=True to open an interactive window
    )
    print(f"Convergence plot saved to {save_path}")


if __name__ == "__main__":
    main()
