from tools.data_loader import load_problem_data
from tools.energy import EVParameters
from tools.objective import ObjectiveWeights
from algorithms.simmulated_annealing import simulated_annealing
from tools.experiment import run_experiments


def main() -> None:
    data = load_problem_data("EV_routing/datasets")

    ev_params = EVParameters(
        battery_capacity_kwh=60.0,
        initial_battery_kwh=60.0,
        energy_consumption_kwh_per_km=0.20,
        average_speed_kmh=35.0,
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
        initial_temperature=1000.0,
        cooling_rate=0.995,
        min_temperature=1e-3,
        iterations_per_temperature=50,
        max_temp_steps=2000,
        reheat_patience=150,
        reheat_factor=0.3,
    )

    # ------------------------------------------------------------------
    # Single run
    # ------------------------------------------------------------------
    print("=== Single Run ===")
    best_solution, best_eval, stats = simulated_annealing(
        data=data,
        ev_params=ev_params,
        weights=weights,
        **sa_kwargs,
    )

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
    # Multi-seed experiment (10 independent runs)
    # ------------------------------------------------------------------
    print("=== Multi-Seed Experiment (10 runs) ===")
    results = run_experiments(
        data=data,
        ev_params=ev_params,
        weights=weights,
        seeds=list(range(10)),
        verbose=True,
        **sa_kwargs,
    )
    print()
    print(f"  Best cost:      {results.best_cost:.4f}  (seed {results.best_seed})")
    print(f"  Average cost:   {results.average_cost:.4f}")
    print(f"  Worst cost:     {results.worst_cost:.4f}")
    print(f"  Std deviation:  {results.std_cost:.4f}")
    print(f"  Feasible runs:  {results.feasible_run_count}/{len(results.seeds)}")
    print()
    print("Best route found across all runs:")
    print(results.best_solution)


if __name__ == "__main__":
    main()
