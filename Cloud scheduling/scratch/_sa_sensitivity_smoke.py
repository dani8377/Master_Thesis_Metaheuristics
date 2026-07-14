"""Smoke test: verify the fixed cooling-rate sweep no longer monotonically
worsens with slower cooling."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.data_loader import load_problem_data, generate_server_pool
from tools.objective import ObjectiveWeights, compute_sample_normalization
from tools.experiment import run_experiments
from algorithms.simulated_annealing import simulated_annealing, estimate_initial_temperature


random.seed(0)
dataset_dir = Path(__file__).parent / "datasets"
servers = generate_server_pool(10, seed=42)
data = load_problem_data(dataset_dir, n_tasks=50, servers=servers)

w = ObjectiveWeights(
    energy_weight=1.0, latency_weight=1.0,
    cpu_penalty=10.0, mem_penalty=10.0, congestion_factor=1.0,
)
w, _diag = compute_sample_normalization(data, w, n_samples=150, seed=0)

base_kwargs = dict(
    initial_temperature=None,
    cooling_rate=0.995,
    min_temperature=1.0e-8,
    iterations_per_temperature=50,
    max_temp_steps=3000,
    reheat_patience=300,
    reheat_factor=0.4,
)

t0_fixed, _ = estimate_initial_temperature(data, w)
min_t = base_kwargs["min_temperature"]
iter_per_temp = base_kwargs["iterations_per_temperature"]
seeds = list(range(3))

print(f"T_0 (auto-estimated) = {t0_fixed:.6f}")
print(f"min_T = {min_t:.0e}")
print()
print(f"{'alpha':>8} {'steps':>8} {'evals':>10} {'mean F':>10} {'std':>8}")
print("-" * 50)

for alpha in [0.990, 0.992, 0.995, 0.997, 0.999]:
    steps_needed = max(20, int(math.ceil(math.log(min_t / t0_fixed) / math.log(alpha))))
    kwargs = {
        **base_kwargs,
        "cooling_rate": alpha,
        "initial_temperature": t0_fixed,
        "max_temp_steps": steps_needed,
    }
    res = run_experiments(
        algorithm=simulated_annealing,
        algorithm_name=f"SA a={alpha}",
        data=data, weights=w, seeds=seeds, show_progress=False, **kwargs,
    )
    print(f"{alpha:>8.3f} {steps_needed:>8d} {steps_needed*iter_per_temp:>10,d}"
          f" {res.average_cost:>10.4f} {res.std_cost:>8.4f}")
