import time

from tools.data_loader import load_problem_data
from tools.energy import EVParameters
from tools.objective import ObjectiveWeights
from algorithms.simmulated_annealing import simulated_annealing
from tools.experiment import run_experiments
from tools.plot import plot_convergence, print_comparison_table


def main() -> None:
    data = load_problem_data("EV_routing/datasets")

    ev_params = EVParameters(
        battery_capacity_kwh=20.0,
        initial_battery_kwh=20.0,
        energy_consumption_kwh_per_km=0.50,
        average_speed_kmh=50.0,
        grade_factor=3.0,    # used when generating sf_energy_matrix.csv
        speed_exponent=2.0,  # used when generating sf_energy_matrix.csv
    )

    weights = ObjectiveWeights(
        distance_weight=1.0,
        travel_time_weight=10.0,
        energy_weight=2.0,
        charging_cost_weight=20.0,
        battery_violation_weight=10000.0,
        infeasible_visit_weight=5000.0,
    )

    sa_kwargs = dict(
        initial_temperature=400.0,   # 80% acceptance of median worsening move (~88)
        cooling_rate=0.995,
        min_temperature=1e-3,
        iterations_per_temperature=50,
        max_temp_steps=3000,         # enough to cool 400 → 0.001 (needs ~2635 steps)
        reheat_patience=3000,        # effectively disabled — no reheat until full cooldown
        reheat_factor=0.4,
    )

    # ------------------------------------------------------------------
    # Single run
    # ------------------------------------------------------------------
    print("=== Single Run ===")
    t0 = time.perf_counter()
    best_solution, best_eval, stats = simulated_annealing(
        data=data,
        ev_params=ev_params,
        weights=weights,
        **sa_kwargs,
    )
    single_run_time = time.perf_counter() - t0

    print("Route:", best_solution)
    print()
    print(f"  Feasible:                {best_eval.feasible}")
    print(f"  Objective value:         {best_eval.objective_value:.4f}")
    print(f"  Total distance (km):     {best_eval.total_distance_km:.4f}")
    print(f"  Total travel time (h):   {best_eval.total_travel_time_h:.4f}")
    print(f"  Total charging time (h): {best_eval.total_charging_time_h:.4f}")
    print(f"  Total energy (kWh):      {best_eval.total_energy_consumed_kwh:.4f}")
    print(f"  Total charging cost ($): {best_eval.total_charging_cost_usd:.4f}")
    print(f"  Battery violation (kWh): {best_eval.battery_violation_kwh:.4f}")
    print(f"  Infeasible visits:       {best_eval.infeasible_visits}")
    print(f"  Runtime:                 {single_run_time:.2f}s")
    print()
    print("  --- SA diagnostics ---")
    print(f"  Candidates evaluated:    {stats.total_evaluated}")
    print(f"  Improving accepted:      {stats.total_improving_accepted}")
    print(f"  Worsening accepted:      {stats.total_worsening_accepted}")
    print(f"  Structural rejections:   {stats.total_rejected_structural}")
    print(f"  Acceptance rate:         {stats.acceptance_rate:.2%}")
    print(f"  Feasibility rate:        {stats.feasibility_rate:.2%}")
    print(f"  Reheat count:            {stats.reheat_count}")
    print(f"  Final temperature:       {stats.final_temperature:.6f}")
    print()

    # ------------------------------------------------------------------
    # Multi-seed experiment
    # ------------------------------------------------------------------
    print("=== Multi-Seed Experiment (10 runs) ===")
    sa_results = run_experiments(
        algorithm=simulated_annealing,
        algorithm_name="Simulated Annealing",
        data=data,
        ev_params=ev_params,
        weights=weights,
        seeds=list(range(10)),
        verbose=True,
        **sa_kwargs,
    )
    print()
    print_comparison_table([sa_results])
    print()
    print(f"  Best seed:   {sa_results.best_seed}")
    print(f"  Best route:  {sa_results.best_solution}")
    print()

    # ------------------------------------------------------------------
    # Convergence plot
    # ------------------------------------------------------------------
    plot_convergence(
        sa_results,
        title="Simulated Annealing — Convergence (10 seeds)",
        save_path="EV_routing/figures/sa_convergence.png",
        show=False,
    )


if __name__ == "__main__":
    main()
