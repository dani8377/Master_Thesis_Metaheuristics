"""Diagnostic: confirm whether the cost drop at 6 servers (80% util) is just
per-instance normalisation, by also reporting raw energy/latency."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.data_loader import load_problem_data, generate_server_pool
from tools.objective import ObjectiveWeights, compute_sample_normalization
from tools.experiment import run_experiments
from algorithms.simulated_annealing import simulated_annealing
from algorithms.baselines import greedy_ffd_baseline


dataset_dir = Path(__file__).parent.parent / "datasets"

w_base = ObjectiveWeights(
    energy_weight=1.0, latency_weight=1.0,
    cpu_penalty=10.0, mem_penalty=10.0, congestion_factor=1.0,
)

base_sa = dict(
    initial_temperature=None, cooling_rate=0.995, min_temperature=1.0e-8,
    iterations_per_temperature=50, max_temp_steps=3000,
    reheat_patience=300, reheat_factor=0.4,
)

print(f"  {'n_srv':>5}  {'util%':>6}  {'e_ref':>9}  {'l_ref':>9}  "
      f"{'greedy F':>9}  {'SA F':>9}  {'SA E_W':>8}  {'SA L_ms':>9}  {'improv%':>8}")
print("-" * 100)

for n_servers in [20, 15, 10, 8, 6]:
    servers = generate_server_pool(n_servers, seed=42)
    data = load_problem_data(dataset_dir, n_tasks=50, servers=servers)
    w, _ = compute_sample_normalization(data, w_base, n_samples=150, seed=0)

    util = data.cpu.sum() / data.server_cpu_cap.sum() * 100

    g_res = run_experiments(
        algorithm=greedy_ffd_baseline, algorithm_name="Greedy",
        data=data, weights=w, seeds=[0], show_progress=False,
    )
    sa_res = run_experiments(
        algorithm=simulated_annealing, algorithm_name="SA",
        data=data, weights=w, seeds=list(range(3)), show_progress=False, **base_sa,
    )
    sa_energy_avg = sum(e.total_energy for e in sa_res.best_evals) / len(sa_res.best_evals)
    sa_latency_avg = sum(e.total_latency for e in sa_res.best_evals) / len(sa_res.best_evals)
    improv = (g_res.average_cost - sa_res.average_cost) / max(1e-10, abs(g_res.average_cost)) * 100

    print(f"  {n_servers:>5}  {util:>5.1f}%  {w.energy_ref:>9.1f}  {w.latency_ref:>9.1f}  "
          f"{g_res.average_cost:>9.4f}  {sa_res.average_cost:>9.4f}  "
          f"{sa_energy_avg:>8.1f}  {sa_latency_avg:>9.1f}  {improv:>7.2f}%")
