"""
UMDA genetic-drift mechanism test.

The benchmarking study found UMDA collapsing to greedy-equivalent quality
from n = 200 onward and attributed this to genetic drift: the univariate
model holds n*m marginals but estimates them from only mu = N/2 selected
individuals, so at fixed population size N = 100 the estimation sample
cannot follow the growing model.  If that explanation is right, growing N
with the instance (at the SAME total evaluation budget, i.e. fewer
generations) should restore part of the improvement over greedy; if the
collapse persists at every N, the explanation would need revisiting.

Protocol mirrors the horizontal scalability axis exactly: synthetic tasks
(seed = n*7+1), server pool seed 42, m = n/5, per-instance sample-based
calibration, 3 seeds, ~150k evaluations per run.

Usage:
    cd Cloud_scheduling && python3.12 umda_drift_test.py [--smoke]
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

from tools.data_loader import load_synthetic_problem_data, generate_server_pool
from tools.objective import ObjectiveWeights, compute_sample_normalization
from tools.experiment import run_experiments
from algorithms.umda import umda
from algorithms.baselines import greedy_ffd_baseline

SMOKE = "--smoke" in sys.argv

DATASET_DIR = Path("datasets")
OUT = Path("results/umda_drift_test.csv")

TASK_SIZES = [200, 500] if not SMOKE else [200]
POP_SIZES = {  # population size N per task count (mu = N/2 selected)
    200: [100, 200, 400],
    500: [100, 500, 1000],
}
BUDGET = 150_000 if not SMOKE else 5_000
SEEDS = [0, 1, 2] if not SMOKE else [0]

BASE_WEIGHTS = ObjectiveWeights(
    energy_weight=1.0, latency_weight=1.0,
    cpu_penalty=10.0, mem_penalty=10.0, congestion_factor=1.0,
)


def main() -> None:
    rows = []
    for n in TASK_SIZES:
        m = max(4, n // 5)
        servers = generate_server_pool(m, seed=42)
        data = load_synthetic_problem_data(DATASET_DIR, n_tasks=n,
                                           servers=servers, seed=n * 7 + 1)
        weights, _diag = compute_sample_normalization(
            data, base_weights=BASE_WEIGHTS, n_samples=150, seed=0,
            penalty_multiplier=100.0, min_feasible=10,
        )

        greedy = run_experiments(
            algorithm=greedy_ffd_baseline, algorithm_name="Greedy BFD",
            data=data, weights=weights, seeds=[0], show_progress=False,
        )
        gcost = greedy.average_cost
        print(f"\n== n={n} m={m}  greedy F={gcost:.4f} ==")

        for N in POP_SIZES[n]:
            gens = max(2, BUDGET // N)
            res = run_experiments(
                algorithm=umda, algorithm_name=f"UMDA N={N}",
                data=data, weights=weights, seeds=SEEDS, show_progress=False,
                population_size=N, n_generations=gens,
                selection_ratio=0.5, smoothing=0.1, elitism_count=1,
            )
            improv = (gcost - res.average_cost) / max(1e-10, abs(gcost)) * 100
            print(f"  N={N:<5} mu={N//2:<4} gens={gens:<5} "
                  f"F={res.average_cost:.4f}  vs_greedy={improv:+.2f}%  "
                  f"t={res.average_runtime:.1f}s")
            rows.append({
                "n_tasks": n, "n_servers": m, "population": N,
                "mu": N // 2, "generations": gens,
                "avg_cost": f"{res.average_cost:.6f}",
                "std": f"{res.std_cost:.6f}",
                "greedy_cost": f"{gcost:.6f}",
                "improvement_pct": f"{improv:.4f}",
                "feasible_runs": res.feasible_run_count,
                "n_runs": len(SEEDS),
                "avg_runtime_s": f"{res.average_runtime:.4f}",
            })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)
    print(f"\n[save] {OUT}")


if __name__ == "__main__":
    main()
