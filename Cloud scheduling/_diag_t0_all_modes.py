"""Diagnostic: what does auto-T_0 estimate produce in each mode, and how does
that compare to the sensitivity sweep optimum?"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tools.data_loader import load_problem_data, generate_server_pool
from tools.objective import ObjectiveWeights, compute_sample_normalization
from algorithms.simulated_annealing import estimate_initial_temperature


dataset_dir = Path(__file__).parent / "datasets"
servers = generate_server_pool(10, seed=42)
data = load_problem_data(dataset_dir, n_tasks=50, servers=servers)

modes = {
    "performance": dict(energy_weight=0.2, latency_weight=1.0, congestion_factor=1.5),
    "balanced":    dict(energy_weight=1.0, latency_weight=1.0, congestion_factor=1.0),
    "eco":         dict(energy_weight=1.0, latency_weight=0.2, congestion_factor=0.5),
}

print(f"  {'mode':>12}  {'auto T_0':>12}  {'sens best T_0':>15}  {'sens best avg':>15}")
print("-" * 60)
for name, mode_w in modes.items():
    w = ObjectiveWeights(cpu_penalty=10.0, mem_penalty=10.0, **mode_w)
    w, _ = compute_sample_normalization(data, w, n_samples=150, seed=0)
    random.seed(0)
    t0_auto, _ = estimate_initial_temperature(data, w)
    print(f"  {name:>12}  {t0_auto:>12.4f}")
