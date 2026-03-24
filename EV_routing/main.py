from tools.data_loader import load_problem_data
from tools.energy import EVParameters
from tools.objective import ObjectiveWeights
from algorithms.simmulated_annealing import simulated_annealing


def main() -> None:
    data = load_problem_data("datasets")

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

    best_solution, best_eval = simulated_annealing(
        data=data,
        ev_params=ev_params,
        weights=weights,
        initial_temperature=1000.0,
        cooling_rate=0.995,
        min_temperature=1e-3,
        max_iterations=5000,
    )

    print("Best solution:")
    print(best_solution)
    print()
    print(f"Feasible: {best_eval.feasible}")
    print(f"Objective value: {best_eval.objective_value:.4f}")
    print(f"Total distance (km): {best_eval.total_distance_km:.4f}")
    print(f"Total travel time (h): {best_eval.total_travel_time_h:.4f}")
    print(f"Total charging time (h): {best_eval.total_charging_time_h:.4f}")
    print(f"Total energy consumed (kWh): {best_eval.total_energy_consumed_kwh:.4f}")
    print(f"Total charging cost (USD): {best_eval.total_charging_cost_usd:.4f}")
    print(f"Battery violation (kWh): {best_eval.battery_violation_kwh:.4f}")
    print(f"Infeasible visits: {best_eval.infeasible_visits}")


if __name__ == "__main__":
    main()