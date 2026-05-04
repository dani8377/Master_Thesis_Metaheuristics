import time

from tools.data_loader import load_problem_data
from tools.battery import EVParameters
from tools.objective import ObjectiveWeights
from algorithms.simmulated_annealing import simulated_annealing
from algorithms.genetic_algorithm import genetic_algorithm
from algorithms.ant_colony import ant_colony_optimization
from tools.compare import run_controlled_comparison, print_statistical_summary, print_detailed_metrics
from tools.tuning import random_search
from tools.plot import (
    plot_convergence,
    plot_convergence_by_evaluations,
    plot_box_comparison,
    plot_sa_diagnostics,
    plot_ga_diagnostics,
    plot_aco_diagnostics,
    plot_cost_breakdown,
    print_comparison_table,
)

FIGURES    = "EV_routing/figures"
SEEDS      = list(range(10))
MAX_EVALS  = 150_000   # shared evaluation budget for all algorithms

# ── Hyperparameter tuning ─────────────────────────────────────────────────────
# Set TUNE = True to run random-search tuning before the comparison.
# Results are printed and used for the final 10-seed comparison.
# TUNE = False → use the hand-picked defaults below (fast, reproducible).
TUNE           = True
TUNE_TRIALS    = 30          # random configurations per algorithm
TUNE_SEEDS     = [0, 1]      # seeds used during tuning (independent of SEEDS)
TUNE_EVALS     = 20_000      # evaluation budget per seed during tuning

# Search spaces for random search.
# Only algorithmic hyperparameters — budget (max_evaluations) is injected separately.
SA_SPACE = {
    "initial_temperature":      [50, 100, 200, 400, 600, 800, 1200],
    "cooling_rate":             [0.988, 0.990, 0.992, 0.993, 0.995, 0.997, 0.999],
    "iterations_per_temperature": [20, 30, 50, 75, 100],
    "reheat_patience":          [50, 100, 150, 200, 300, 500],
    "reheat_factor":            [0.2, 0.3, 0.4, 0.5, 0.7],
}

GA_SPACE = {
    "population_size":  [40, 60, 80, 100, 150, 200],
    "crossover_rate":   [0.70, 0.75, 0.80, 0.85, 0.90, 0.95],
    "mutation_rate":    [0.05, 0.10, 0.15, 0.20, 0.25, 0.30],
    "tournament_size":  [2, 3, 4, 5],
    "elitism_count":    [1, 2, 3, 5],
}

MA_SPACE = {
    **GA_SPACE,
    "local_search_iters": [5, 10, 15, 20, 30, 50],
}

ACO_SPACE = {
    "n_ants":                [10, 15, 20, 25, 30],
    "alpha":                 [0.5, 1.0, 1.5, 2.0],
    "beta":                  [2.0, 3.0, 4.0, 5.0, 6.0],
    "rho":                   [0.05, 0.10, 0.15, 0.20, 0.30],
    "q0":                    [0.70, 0.80, 0.85, 0.90, 0.95],
    "battery_threshold_frac":[0.10, 0.20, 0.30, 0.40, 0.50],
    "local_search_iters":    [0, 5, 10, 15, 20],
    "candidate_list_k":      [0, 10, 15, 20, 30],
}
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
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

    data = load_problem_data("EV_routing/datasets", ev_params)

    weights = ObjectiveWeights(
        distance_weight=1.0,
        travel_time_weight=10.0,
        energy_weight=2.0,
        charging_cost_weight=20.0,
        battery_violation_weight=10000.0,
        infeasible_visit_weight=5000.0,
    )

    # ------------------------------------------------------------------
    # Default (hand-picked) parameters — used when TUNE = False
    # ------------------------------------------------------------------
    sa_kwargs = dict(
        initial_temperature=400.0,
        cooling_rate=0.995,
        iterations_per_temperature=50,
        reheat_patience=200,
        reheat_factor=0.4,
    )

    ga_kwargs = dict(
        population_size=80,
        crossover_rate=0.85,
        mutation_rate=0.20,
        tournament_size=3,
        elitism_count=2,
    )

    ma_kwargs = {**ga_kwargs, "local_search_iters": 30}

    aco_kwargs = dict(
        n_ants=20,
        alpha=1.0,
        beta=3.0,
        rho=0.1,
        q0=0.9,
        battery_threshold_frac=0.3,
    )

    # ------------------------------------------------------------------
    # Hyperparameter tuning (optional)
    # ------------------------------------------------------------------
    if TUNE:
        print("=" * 60)
        print(f"Hyperparameter tuning — {TUNE_TRIALS} trials × {len(TUNE_SEEDS)} seeds"
              f" × {TUNE_EVALS:,} evals")
        print("=" * 60)

        sa_kwargs,  _ = random_search(simulated_annealing,    SA_SPACE,  data, ev_params, weights,
                                      TUNE_TRIALS, TUNE_SEEDS, TUNE_EVALS, "SA")
        ga_kwargs,  _ = random_search(genetic_algorithm,       GA_SPACE,  data, ev_params, weights,
                                      TUNE_TRIALS, TUNE_SEEDS, TUNE_EVALS, "GA")
        ma_kwargs,  _ = random_search(genetic_algorithm,       MA_SPACE,  data, ev_params, weights,
                                      TUNE_TRIALS, TUNE_SEEDS, TUNE_EVALS, "MA")
        aco_kwargs, _ = random_search(ant_colony_optimization, ACO_SPACE, data, ev_params, weights,
                                      TUNE_TRIALS, TUNE_SEEDS, TUNE_EVALS, "ACO")

        print("Tuned parameters:")
        for name, kw in [("SA", sa_kwargs), ("GA", ga_kwargs), ("MA", ma_kwargs), ("ACO", aco_kwargs)]:
            print(f"  {name}: {kw}")
        print()

    # ------------------------------------------------------------------
    # Single diagnostic run (SA)
    # ------------------------------------------------------------------
    print("=" * 60)
    print("Single SA run — diagnostics")
    print("=" * 60)
    t0 = time.perf_counter()
    _, best_ev, sa_stats = simulated_annealing(data=data, ev_params=ev_params, weights=weights,
                                                max_evaluations=MAX_EVALS, **sa_kwargs)
    sa_single_time = time.perf_counter() - t0

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
    print(f"  Runtime:             {sa_single_time:.2f}s")
    print()

    # ------------------------------------------------------------------
    # Single diagnostic run (GA)
    # ------------------------------------------------------------------
    print("=" * 60)
    print("Single GA run — diagnostics")
    print("=" * 60)
    t0 = time.perf_counter()
    _, best_ev_ga, ga_stats = genetic_algorithm(data=data, ev_params=ev_params, weights=weights,
                                                max_evaluations=MAX_EVALS, **ga_kwargs)
    ga_single_time = time.perf_counter() - t0

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
    print(f"  Runtime:             {ga_single_time:.2f}s")
    print()

    # ------------------------------------------------------------------
    # Single diagnostic run (MA)
    # ------------------------------------------------------------------
    print("=" * 60)
    print("Single MA run — diagnostics")
    print("=" * 60)
    t0 = time.perf_counter()
    _, best_ev_ma, ma_stats = genetic_algorithm(data=data, ev_params=ev_params, weights=weights,
                                                max_evaluations=MAX_EVALS, **ma_kwargs)
    ma_single_time = time.perf_counter() - t0

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
    print(f"  Runtime:             {ma_single_time:.2f}s")
    print()

    # ------------------------------------------------------------------
    # Single diagnostic run (ACO)
    # ------------------------------------------------------------------
    print("=" * 60)
    print("Single ACO run — diagnostics")
    print("=" * 60)
    t0 = time.perf_counter()
    _, best_ev_aco, aco_stats = ant_colony_optimization(data=data, ev_params=ev_params, weights=weights,
                                                         max_evaluations=MAX_EVALS, **aco_kwargs)
    aco_single_time = time.perf_counter() - t0

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
    print(f"  Runtime:             {aco_single_time:.2f}s")
    print()

    # ------------------------------------------------------------------
    # Controlled multi-seed comparison  (SA vs GA vs MA vs ACO)
    # ------------------------------------------------------------------
    print("=" * 60)
    print(f"Controlled comparison — {len(SEEDS)} seeds, budget={MAX_EVALS:,} evals")
    print("=" * 60)

    all_results = run_controlled_comparison(
        algorithms={
            "Simulated Annealing": simulated_annealing,
            "Genetic Algorithm":   genetic_algorithm,
            "Memetic Algorithm":   genetic_algorithm,
            "ACO":                 ant_colony_optimization,
        },
        data=data,
        ev_params=ev_params,
        weights=weights,
        seeds=SEEDS,
        max_evaluations=MAX_EVALS,
        verbose=True,
        algorithm_kwargs={
            "Simulated Annealing": sa_kwargs,
            "Genetic Algorithm":   ga_kwargs,
            "Memetic Algorithm":   ma_kwargs,
            "ACO":                 aco_kwargs,
        },
    )

    sa_results, ga_results, ma_results, aco_results = all_results

    print()
    print_comparison_table(all_results)
    print()
    print_detailed_metrics(all_results)
    print_statistical_summary(all_results)

    # ------------------------------------------------------------------
    # Figures
    # ------------------------------------------------------------------
    print("Saving figures …")

    # 1. Per-algorithm convergence by step (internal view)
    for res, tag in [(sa_results, "sa"), (ga_results, "ga"), (ma_results, "ma"), (aco_results, "aco")]:
        plot_convergence(
            res,
            title=f"{res.algorithm_name} — Convergence (10 seeds)",
            save_path=f"{FIGURES}/{tag}_convergence_by_step.png",
            show=False,
        )

    # 2. Convergence by evaluations — fair cross-algorithm comparison
    plot_convergence_by_evaluations(
        all_results,
        title=f"Convergence by objective evaluations (budget = {MAX_EVALS:,})",
        save_path=f"{FIGURES}/convergence_by_evaluations.png",
        show=False,
    )

    # 3. Box plots — robustness across seeds
    plot_box_comparison(
        all_results,
        title="Solution quality distribution across 10 seeds",
        save_path=f"{FIGURES}/box_comparison.png",
        show=False,
    )

    # 4. SA diagnostics — temperature schedule + exploration gap + best/current
    plot_sa_diagnostics(
        sa_results,
        seed_idx=sa_results.best_run_index,
        title=f"SA diagnostics — best seed ({sa_results.best_seed})",
        save_path=f"{FIGURES}/sa_diagnostics.png",
        show=False,
    )

    # 5. GA diagnostics — best vs mean, diversity, feasibility rate
    plot_ga_diagnostics(
        ga_results,
        seed_idx=ga_results.best_run_index,
        title=f"GA diagnostics — best seed ({ga_results.best_seed})",
        save_path=f"{FIGURES}/ga_diagnostics.png",
        show=False,
    )

    # 6. MA diagnostics — same panels, shows effect of local search on population
    plot_ga_diagnostics(
        ma_results,
        seed_idx=ma_results.best_run_index,
        title=f"MA diagnostics — best seed ({ma_results.best_seed})",
        save_path=f"{FIGURES}/ma_diagnostics.png",
        show=False,
    )

    # 7. ACO diagnostics — best vs iteration mean, pheromone CV, feasibility
    plot_aco_diagnostics(
        aco_results,
        seed_idx=aco_results.best_run_index,
        title=f"ACO diagnostics — best seed ({aco_results.best_seed})",
        save_path=f"{FIGURES}/aco_diagnostics.png",
        show=False,
    )

    # 8. Cost component breakdown
    plot_cost_breakdown(
        all_results,
        title="Cost component breakdown (best solution per algorithm)",
        save_path=f"{FIGURES}/cost_breakdown.png",
        show=False,
    )

    print()
    print(f"All figures saved to {FIGURES}/")
    print(f"SA  best (seed {sa_results.best_seed}):  {sa_results.best_solution}")
    print(f"GA  best (seed {ga_results.best_seed}):  {ga_results.best_solution}")
    print(f"MA  best (seed {ma_results.best_seed}):  {ma_results.best_solution}")
    print(f"ACO best (seed {aco_results.best_seed}): {aco_results.best_solution}")


if __name__ == "__main__":
    main()
