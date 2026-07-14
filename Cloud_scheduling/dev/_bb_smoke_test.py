"""Smoke test for the B&B fix: verify the incumbent improves beyond greedy."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.data_loader import load_problem_data, generate_server_pool
from tools.objective import (
    ObjectiveWeights, compute_sample_normalization, evaluate_schedule,
)
from tools.initial_solution import build_greedy_assignment
from algorithms.branch_and_bound import branch_and_bound


def run(n_tasks: int, n_servers: int, time_limit: float):
    random.seed(0)
    dataset_dir = Path(__file__).parent.parent / "datasets"
    servers = generate_server_pool(n_servers, seed=42)
    data = load_problem_data(dataset_dir, n_tasks=n_tasks, servers=servers)

    w = ObjectiveWeights(
        energy_weight=1.0, latency_weight=1.0,
        cpu_penalty=100.0, mem_penalty=100.0, congestion_factor=1.0,
    )
    w, _diag = compute_sample_normalization(data, w, n_samples=400, seed=0)

    greedy_assign = build_greedy_assignment(data)
    greedy_eval = evaluate_schedule(greedy_assign, data, w)

    print(f"--- B&B on n={n_tasks} m={n_servers} (time_limit={time_limit}s) ---")
    print(f"  Greedy BFD baseline F = {greedy_eval.objective_value:.4f}")
    sol, ev, stats = branch_and_bound(
        data, w, time_limit=time_limit, max_nodes=2_000_000, verbose=True,
    )
    delta = greedy_eval.objective_value - ev.objective_value
    print(f"  B&B best F       = {ev.objective_value:.4f}")
    print(f"  Improvement vs greedy = {delta:+.4f}  ({delta / greedy_eval.objective_value * 100:+.2f}%)")
    print(f"  Nodes explored   = {stats.nodes_explored:,}")
    print(f"  Root LB          = {stats.root_lower_bound:.4f}")
    print(f"  Optimality gap   = {stats.optimality_gap:.1%}")
    print(f"  Proven optimal   = {stats.proven_optimal}")
    print()


if __name__ == "__main__":
    run(n_tasks=20, n_servers=4,  time_limit=15.0)
    run(n_tasks=50, n_servers=10, time_limit=30.0)
