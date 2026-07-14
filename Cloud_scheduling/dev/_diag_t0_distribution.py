"""Diagnostic: trace the actual delta distribution used by estimate_initial_temperature
to identify whether the mean_delta is inflated by infeasibility drift."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np

from tools.data_loader import load_problem_data, generate_server_pool
from tools.objective import ObjectiveWeights, compute_sample_normalization, evaluate_schedule
from tools.neighborhoods import generate_neighbor
from tools.initial_solution import build_greedy_assignment
from tools.feasibility import is_valid_assignment


dataset_dir = Path(__file__).parent.parent / "datasets"
servers = generate_server_pool(10, seed=42)
data = load_problem_data(dataset_dir, n_tasks=50, servers=servers)

modes = {
    "performance": dict(energy_weight=0.2, latency_weight=1.0, congestion_factor=1.5),
    "balanced":    dict(energy_weight=1.0, latency_weight=1.0, congestion_factor=1.0),
    "eco":         dict(energy_weight=1.0, latency_weight=0.2, congestion_factor=0.5),
}

for name, mode_w in modes.items():
    print(f"\n{'='*70}\n{name.upper()}\n{'='*70}")
    w = ObjectiveWeights(cpu_penalty=10.0, mem_penalty=10.0, **mode_w)
    w, _ = compute_sample_normalization(data, w, n_samples=150, seed=0)

    random.seed(0)
    assignment = build_greedy_assignment(data)
    current_eval = evaluate_schedule(assignment, data, w)
    current_cost = current_eval.objective_value
    current_feasible = current_eval.feasible

    print(f"  Greedy start: cost={current_cost:.4f}  feasible={current_feasible}")

    deltas_feas_feas = []   # feasible -> feasible (the "good" deltas)
    deltas_inf_inf   = []   # infeasible -> infeasible (drift-into-infeasibility)
    deltas_mixed     = []   # feasibility-changing (skipped by current filter)

    n_currently_feasible = 0
    n_currently_infeas   = 0

    for _ in range(400):
        candidate = generate_neighbor(assignment, data)
        if not is_valid_assignment(candidate, data):
            continue
        cand_eval = evaluate_schedule(candidate, data, w)
        delta = cand_eval.objective_value - current_cost

        if current_feasible:
            n_currently_feasible += 1
        else:
            n_currently_infeas += 1

        if delta > 0:
            if current_feasible and cand_eval.feasible:
                deltas_feas_feas.append(delta)
            elif (not current_feasible) and (not cand_eval.feasible):
                deltas_inf_inf.append(delta)
            else:
                deltas_mixed.append(delta)

        if random.random() < 0.15:
            assignment = candidate
            current_cost = cand_eval.objective_value
            current_feasible = cand_eval.feasible

    print(f"  Time in feasible region:   {n_currently_feasible} / 400 samples")
    print(f"  Time in infeasible region: {n_currently_infeas} / 400 samples")
    print()
    print(f"  feasible->feasible deltas:    n={len(deltas_feas_feas):>3}"
          f"  mean={np.mean(deltas_feas_feas) if deltas_feas_feas else 0:.6f}"
          f"  median={np.median(deltas_feas_feas) if deltas_feas_feas else 0:.6f}")
    print(f"  infeasible->infeasible:       n={len(deltas_inf_inf):>3}"
          f"  mean={np.mean(deltas_inf_inf) if deltas_inf_inf else 0:.6f}"
          f"  median={np.median(deltas_inf_inf) if deltas_inf_inf else 0:.6f}")
    print(f"  feasibility-changing (mixed): n={len(deltas_mixed):>3}"
          f"  mean={np.mean(deltas_mixed) if deltas_mixed else 0:.6f}")

    all_preserve = deltas_feas_feas + deltas_inf_inf
    print()
    print(f"  CURRENT filter (preserve): n={len(all_preserve)}"
          f"  mean_delta={np.mean(all_preserve):.6f}"
          f"  -> T_0={-np.mean(all_preserve)/math.log(0.8):.6f}")
    if deltas_feas_feas:
        print(f"  TIGHTER filter (feas only): n={len(deltas_feas_feas)}"
              f"  mean_delta={np.mean(deltas_feas_feas):.6f}"
              f"  -> T_0={-np.mean(deltas_feas_feas)/math.log(0.8):.6f}")
