from __future__ import annotations

"""
Controlled cross-algorithm comparison utilities.

Usage
-----
1. Call ``run_controlled_comparison`` to run multiple algorithms under an
   identical evaluation budget and seed list.
2. Call ``print_statistical_summary`` to get pairwise Mann-Whitney U tests.
3. Call ``print_detailed_metrics`` for a richer per-algorithm metrics table
   with coefficient of variation, feasibility rate, and average evaluations.
"""

import statistics
from itertools import combinations
from typing import Any, Callable

from tools.data_loader import ProblemData
from tools.battery import EVParameters
from tools.objective import ObjectiveWeights, RouteEvaluation
from tools.experiment import ExperimentResults, run_experiments

AlgorithmFn = Callable[..., tuple[list[str], RouteEvaluation, Any]]


# ---------------------------------------------------------------------------
# Controlled comparison runner
# ---------------------------------------------------------------------------

def run_controlled_comparison(
    algorithms: dict[str, AlgorithmFn],
    data: ProblemData,
    ev_params: EVParameters,
    weights: ObjectiveWeights,
    seeds: list[int],
    max_evaluations: int = 150_000,
    time_limit_s: float | None = None,
    verbose: bool = True,
    algorithm_kwargs: dict[str, dict] | None = None,
) -> list[ExperimentResults]:
    """
    Run every algorithm in ``algorithms`` under the same evaluation budget
    and seed list, returning one ExperimentResults per algorithm.

    Parameters
    ----------
    algorithms:
        Mapping of display name → callable matching the AlgorithmFn signature.
    max_evaluations:
        Hard upper bound on objective evaluations passed to each algorithm.
    time_limit_s:
        Optional wall-clock limit per run (in addition to max_evaluations).
    algorithm_kwargs:
        Per-algorithm extra kwargs (keyed by display name).  The budget
        parameters ``max_evaluations`` and ``time_limit_s`` are injected
        automatically and do not need to be listed here.
    """
    if algorithm_kwargs is None:
        algorithm_kwargs = {}

    all_results: list[ExperimentResults] = []

    for name, fn in algorithms.items():
        if verbose:
            print(f"\n--- {name} (budget={max_evaluations:,} evals, {len(seeds)} seeds) ---")

        extra = algorithm_kwargs.get(name, {})
        extra = {**extra, "max_evaluations": max_evaluations}
        if time_limit_s is not None:
            extra["time_limit_s"] = time_limit_s

        result = run_experiments(
            algorithm=fn,
            data=data,
            ev_params=ev_params,
            weights=weights,
            seeds=seeds,
            algorithm_name=name,
            verbose=verbose,
            **extra,
        )
        all_results.append(result)

    return all_results


# ---------------------------------------------------------------------------
# Statistical tests
# ---------------------------------------------------------------------------

def _mannwhitney(costs_a: list[float], costs_b: list[float]) -> tuple[float, float]:
    """
    Mann-Whitney U statistic and two-sided p-value.
    Uses scipy.stats if available, otherwise falls back to an exact calculation
    for small samples (n ≤ 20 per group).
    """
    try:
        from scipy import stats as scipy_stats
        stat, p = scipy_stats.mannwhitneyu(costs_a, costs_b, alternative="two-sided")
        return float(stat), float(p)
    except ImportError:
        pass

    # Exact U for small samples (brute-force O(n²))
    na, nb = len(costs_a), len(costs_b)
    u = sum(
        1 if a < b else (0.5 if a == b else 0)
        for a in costs_a
        for b in costs_b
    )
    # Normal approximation for p-value
    import math
    mu_u = na * nb / 2
    sigma_u = math.sqrt(na * nb * (na + nb + 1) / 12)
    if sigma_u == 0:
        return u, 1.0
    z = (u - mu_u) / sigma_u
    # Two-sided p from standard normal CDF approximation
    p = 2 * (1 - _norm_cdf(abs(z)))
    return u, p


def _norm_cdf(z: float) -> float:
    """Abramowitz & Stegun approximation of the standard normal CDF."""
    import math
    t = 1 / (1 + 0.2316419 * abs(z))
    poly = t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))))
    cdf = 1 - (1 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * z * z) * poly
    return cdf if z >= 0 else 1 - cdf


def print_statistical_summary(
    results_list: list[ExperimentResults],
    alpha: float = 0.05,
) -> None:
    """
    Print pairwise Mann-Whitney U tests (unpaired, two-sided) between all
    algorithm pairs.  Effect direction is reported by mean cost.
    """
    print(f"=== Pairwise Statistical Tests (Mann-Whitney U, α={alpha}) ===")
    for r1, r2 in combinations(results_list, 2):
        u, p = _mannwhitney(r1.best_costs, r2.best_costs)
        sig = p < alpha
        sig_str = "SIGNIFICANT" if sig else "not significant"
        print(f"  {r1.algorithm_name} vs {r2.algorithm_name}: U={u:.1f}  p={p:.4f}  [{sig_str}]")
        if sig:
            winner = r1.algorithm_name if statistics.mean(r1.best_costs) < statistics.mean(r2.best_costs) else r2.algorithm_name
            print(f"    → Better algorithm: {winner}")
    print()


# ---------------------------------------------------------------------------
# Detailed metrics table
# ---------------------------------------------------------------------------

def print_detailed_metrics(results_list: list[ExperimentResults]) -> None:
    """
    Extended metrics table with statistics useful for a thesis:

    Algorithm | Best | Mean ± Std | CV% | Feasible | Avg evals | Avg time
    """
    print("=== Detailed Metrics ===")
    header = f"{'Algorithm':<24}{'Best':>10}{'Mean':>10}{'Std':>10}{'CV%':>8}{'Feasible':>10}{'Avg evals':>12}{'Avg time':>10}"
    print("-" * len(header))
    print(header)
    print("-" * len(header))

    for r in results_list:
        cv = (r.std_cost / r.average_cost * 100) if r.average_cost > 0 else 0.0
        feasible_str = f"{r.feasible_run_count}/{len(r.seeds)}"
        avg_evals = statistics.mean(
            s.total_evaluated for s in r.all_stats if hasattr(s, "total_evaluated")
        )
        print(
            f"{r.algorithm_name:<24}"
            f"{r.best_cost:>10.2f}"
            f"{r.average_cost:>10.2f}"
            f"{r.std_cost:>10.2f}"
            f"{cv:>8.1f}"
            f"{feasible_str:>10}"
            f"{avg_evals:>12.0f}"
            f"{r.average_runtime:>10.1f}s"
        )

    print("-" * len(header))
    print()
