"""Diagnostic: check whether SA at n=100/200/500 (horizontal scaling) still
gets stuck at 0% improvement over greedy, now with the fixed T_0 estimator."""
import math
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.data_loader import (
    load_synthetic_problem_data,
    generate_server_pool,
)
from tools.objective import ObjectiveWeights, compute_sample_normalization
from tools.experiment import run_experiments
from algorithms.simulated_annealing import simulated_annealing, estimate_initial_temperature
from algorithms.baselines import greedy_ffd_baseline


dataset_dir = Path(__file__).parent / "datasets"

w_base = ObjectiveWeights(
    energy_weight=1.0, latency_weight=1.0,
    cpu_penalty=10.0, mem_penalty=10.0, congestion_factor=1.0,
)

base_sa = dict(
    initial_temperature=None,
    cooling_rate=0.995,
    min_temperature=1.0e-8,
    iterations_per_temperature=50,
    max_temp_steps=3000,
    reheat_patience=300,
    reheat_factor=0.4,
)

seeds = list(range(3))

print(f"  {'n_tasks':>8}  {'n_serv':>6}  {'auto T_0':>10}  "
      f"{'greedy':>10}  {'SA avg':>10}  {'improv%':>8}  {'time':>6}")
print("-" * 80)

for n in [20, 50, 100, 200, 500]:
    n_servers = max(4, n // 5)
    servers = generate_server_pool(n_servers, seed=42)
    data = load_synthetic_problem_data(dataset_dir, n_tasks=n, servers=servers, seed=n * 7 + 1)
    w, _ = compute_sample_normalization(data, w_base, n_samples=150, seed=0)

    random.seed(0)
    t0_auto, _ = estimate_initial_temperature(data, w)

    g_res = run_experiments(
        algorithm=greedy_ffd_baseline, algorithm_name="Greedy",
        data=data, weights=w, seeds=[0], show_progress=False,
    )
    g_cost = g_res.average_cost

    t0 = time.perf_counter()
    sa_res = run_experiments(
        algorithm=simulated_annealing, algorithm_name="SA",
        data=data, weights=w, seeds=seeds, show_progress=False, **base_sa,
    )
    runtime = (time.perf_counter() - t0) / len(seeds)
    improv = (g_cost - sa_res.average_cost) / max(1e-10, abs(g_cost)) * 100

    print(f"  {n:>8}  {n_servers:>6}  {t0_auto:>10.5f}  "
          f"{g_cost:>10.4f}  {sa_res.average_cost:>10.4f}  {improv:>7.2f}%  {runtime:>5.1f}s")
