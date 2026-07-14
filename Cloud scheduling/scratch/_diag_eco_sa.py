"""Diagnostic: trace eco SA sensitivity to understand the duplicate-rows pattern."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tools.data_loader import load_problem_data, generate_server_pool
from tools.objective import ObjectiveWeights, compute_sample_normalization
from tools.experiment import run_experiments
from algorithms.simulated_annealing import simulated_annealing, estimate_initial_temperature


random.seed(0)
dataset_dir = Path(__file__).parent / "datasets"
servers = generate_server_pool(10, seed=42)
data = load_problem_data(dataset_dir, n_tasks=50, servers=servers)

# Eco mode weights
w = ObjectiveWeights(
    energy_weight=1.0, latency_weight=0.2,
    cpu_penalty=10.0, mem_penalty=10.0, congestion_factor=0.5,
)
w, diag = compute_sample_normalization(data, w, n_samples=150, seed=0)

print("=" * 70)
print("ECO MODE CALIBRATION")
print("=" * 70)
print(f"  energy_ref = {w.energy_ref:.4f}")
print(f"  latency_ref = {w.latency_ref:.4f}")
print(f"  cpu_penalty = {w.cpu_penalty:.4f}  (= 100 * f_max_feasible)")
print(f"  mem_penalty = {w.mem_penalty:.4f}")
print(f"  f_max_feasible = {diag.f_max_feasible:.4f}")

# Auto-estimate T_0 in eco
random.seed(0)
t0_auto, n_probes = estimate_initial_temperature(data, w, verbose=True)
print()
print(f"  Auto-estimated T_0 = {t0_auto:.6e}")
print(f"  T_0 probe evaluations = {n_probes}")

# Now run SA with each T_0 value from the sensitivity sweep
print()
print("=" * 70)
print("TEMPERATURE SWEEP (n_seeds=5)")
print("=" * 70)
print(f"  {'T_0':>10}  {'best':>10}  {'avg':>10}  {'worst':>10}  {'reheats':>10}")
seeds = list(range(5))
base = dict(
    cooling_rate=0.995,
    min_temperature=1.0e-8,
    iterations_per_temperature=50,
    max_temp_steps=3000,
    reheat_patience=300,
    reheat_factor=0.4,
)
for T_0 in [0.005, 0.01, 0.05, 0.1, 0.5, 1.0]:
    res = run_experiments(
        algorithm=simulated_annealing, algorithm_name=f"T0={T_0}",
        data=data, weights=w, seeds=seeds, show_progress=False,
        initial_temperature=T_0, **base,
    )
    mean_reheats = sum(s.reheat_count for s in res.all_stats) / len(res.all_stats)
    print(f"  {T_0:>10}  {res.best_cost:>10.6f}  {res.average_cost:>10.6f}"
          f"  {res.worst_cost:>10.6f}  {mean_reheats:>10.2f}")

print()
print("=" * 70)
print("COOLING RATE SWEEP (auto T_0)")
print("=" * 70)
random.seed(0)
t0_fixed, _ = estimate_initial_temperature(data, w)
print(f"  t0_fixed = {t0_fixed:.6e}")
print()
print(f"  {'alpha':>8}  {'steps':>8}  {'best':>10}  {'avg':>10}  {'worst':>10}")
min_t = 1e-8
for alpha in [0.990, 0.992, 0.995, 0.997, 0.999]:
    steps = max(20, int(math.ceil(math.log(min_t / t0_fixed) / math.log(alpha))))
    cell_kw = {
        **base,
        "cooling_rate": alpha,
        "initial_temperature": t0_fixed,
        "max_temp_steps": steps,
    }
    res = run_experiments(
        algorithm=simulated_annealing, algorithm_name=f"a={alpha}",
        data=data, weights=w, seeds=seeds, show_progress=False, **cell_kw,
    )
    print(f"  {alpha:>8.3f}  {steps:>8d}  {res.best_cost:>10.6f}"
          f"  {res.average_cost:>10.6f}  {res.worst_cost:>10.6f}")
