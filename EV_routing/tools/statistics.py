"""
Statistical analysis utilities for thesis experiments.

Provides:
  - Wilcoxon signed-rank test (paired, two-sided) for metaheuristic comparison
  - Pairwise comparison table
  - Summary table (console + LaTeX)
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from itertools import combinations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tools.experiment import ExperimentResults


# ---------------------------------------------------------------------------
# Wilcoxon signed-rank test
# ---------------------------------------------------------------------------

@dataclass
class WilcoxonResult:
    algo_a: str
    algo_b: str
    statistic: float
    p_value: float
    p_holm: float           # Holm step-down adjusted p-value (family = all pairs)
    significant: bool       # based on the Holm-adjusted p-value
    better: str  # name of algorithm with lower mean cost


def _norm_cdf(z: float) -> float:
    """Abramowitz & Stegun approximation of the standard normal CDF."""
    t = 1.0 / (1.0 + 0.2316419 * abs(z))
    poly = t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))))
    cdf = 1.0 - (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * z * z) * poly
    return cdf if z >= 0 else 1.0 - cdf


def _wilcoxon_signed_rank(x: list[float], y: list[float]) -> tuple[float, float]:
    """
    Two-sided Wilcoxon signed-rank test for paired samples.
    Uses scipy.stats.wilcoxon when available; falls back to a manual
    normal-approximation for small samples (n ≤ 30).
    """
    try:
        from scipy.stats import wilcoxon
        stat, p = wilcoxon(x, y, alternative="two-sided", zero_method="wilcox")
        return float(stat), float(p)
    except ImportError:
        pass

    diffs = [xi - yi for xi, yi in zip(x, y)]
    diffs = [d for d in diffs if d != 0.0]
    n = len(diffs)
    if n == 0:
        return 0.0, 1.0

    abs_d = [abs(d) for d in diffs]
    order = sorted(range(n), key=lambda i: abs_d[i])

    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j < n - 1 and abs_d[order[j]] == abs_d[order[j + 1]]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg_rank
        i = j + 1

    w_plus  = sum(ranks[i] for i in range(n) if diffs[i] > 0)
    w_minus = sum(ranks[i] for i in range(n) if diffs[i] < 0)
    w = min(w_plus, w_minus)

    mu    = n * (n + 1) / 4.0
    sigma = math.sqrt(n * (n + 1) * (2 * n + 1) / 24.0)
    if sigma == 0:
        return w, 1.0
    z = (w - mu) / sigma
    p = 2.0 * (1.0 - _norm_cdf(abs(z)))
    return w, max(0.0, min(1.0, p))


def pairwise_wilcoxon(
    results_list: list["ExperimentResults"],
    alpha: float = 0.05,
) -> list[WilcoxonResult]:
    """
    Pairwise Wilcoxon signed-rank tests for all algorithm pairs.

    Paired test is appropriate here because all algorithms were run with the
    same 10 seeds, so seed-specific difficulty is controlled for.
    """
    out: list[WilcoxonResult] = []
    for r1, r2 in combinations(results_list, 2):
        if len(r1.best_costs) != len(r2.best_costs):
            raise ValueError(
                f"Paired test requires equal seed counts: "
                f"{r1.algorithm_name}={len(r1.best_costs)}, "
                f"{r2.algorithm_name}={len(r2.best_costs)}"
            )
        stat, p = _wilcoxon_signed_rank(r1.best_costs, r2.best_costs)
        mean_a = statistics.mean(r1.best_costs)
        mean_b = statistics.mean(r2.best_costs)
        better = r1.algorithm_name if mean_a <= mean_b else r2.algorithm_name
        out.append(WilcoxonResult(
            algo_a=r1.algorithm_name,
            algo_b=r2.algorithm_name,
            statistic=stat,
            p_value=p,
            p_holm=p,            # provisional; adjusted below
            significant=False,   # provisional; set below
            better=better,
        ))

    # Holm step-down correction over the family of all pairwise tests:
    # sort raw p ascending, multiply the i-th smallest by (m - i), enforce
    # monotonicity, cap at 1.  Controls the family-wise error rate without
    # the full conservativeness of Bonferroni (Holm 1979).
    m = len(out)
    order = sorted(range(m), key=lambda i: out[i].p_value)
    running = 0.0
    for rank, i in enumerate(order):
        adj = min(1.0, (m - rank) * out[i].p_value)
        running = max(running, adj)
        out[i].p_holm = running
        out[i].significant = running < alpha
    return out


def print_wilcoxon_table(tests: list[WilcoxonResult], alpha: float = 0.05) -> None:
    """Print pairwise Wilcoxon results as a formatted table."""
    print(f"=== Pairwise Wilcoxon Signed-Rank Tests (paired, two-sided, Holm-adjusted, α={alpha}) ===")
    print(f"  {'Pair':<40}  {'W':>8}  {'p-value':>9}  {'p-Holm':>9}  Result")
    print(f"  {'-'*40}  {'-'*8}  {'-'*9}  {'-'*9}  {'-'*24}")
    for t in tests:
        pair = f"{t.algo_a} vs {t.algo_b}"
        if t.significant:
            verdict = f"{t.better} better *"
        else:
            verdict = "no sig. difference"
        print(f"  {pair:<40}  {t.statistic:>8.1f}  {t.p_value:>9.4f}  {t.p_holm:>9.4f}  {verdict}")
    print(f"  (* Holm-adjusted p < {alpha})\n")


# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------

def print_summary_table(results_list: list["ExperimentResults"]) -> None:
    """
    Print a thesis-style result summary table:
    Algorithm | Best | Mean ± Std | Median | CV% | Feasible% | Avg runtime
    """
    print("=== Result Summary Table ===")
    header = (
        f"{'Algorithm':<24}"
        f"{'Best':>10}"
        f"{'Mean ± Std':>22}"
        f"{'Median':>10}"
        f"{'CV%':>7}"
        f"{'Feasible':>10}"
        f"{'Avg time':>10}"
    )
    sep = "-" * len(header)
    print(sep)
    print(header)
    print(sep)

    for r in results_list:
        med = statistics.median(r.best_costs)
        cv  = (r.std_cost / r.average_cost * 100) if r.average_cost > 0 else 0.0
        feas_pct = r.feasible_run_count / len(r.seeds) * 100
        mean_std = f"{r.average_cost:.3f} ± {r.std_cost:.3f}"
        print(
            f"{r.algorithm_name:<24}"
            f"{r.best_cost:>10.3f}"
            f"{mean_std:>22}"
            f"{med:>10.3f}"
            f"{cv:>7.1f}"
            f"{feas_pct:>9.0f}%"
            f"{r.average_runtime:>9.1f}s"
        )
    print(sep)
    print()


def to_latex_table(
    results_list: list["ExperimentResults"],
    caption: str = "Algorithm comparison results (10 seeds, mean ± std).",
    label: str = "tab:results",
) -> str:
    """
    Return a complete LaTeX table string for the thesis.

    Columns: Algorithm | Best | Mean ± Std | CV% | Feasible% | Avg time (s)
    The best mean is highlighted with \\textbf{}.
    """
    best_mean = min(r.average_cost for r in results_list)

    rows = []
    for r in results_list:
        cv       = (r.std_cost / r.average_cost * 100) if r.average_cost > 0 else 0.0
        feas_pct = r.feasible_run_count / len(r.seeds) * 100
        mean_str = f"{r.average_cost:.3f}"
        if abs(r.average_cost - best_mean) < 1e-9:
            mean_str = r"\textbf{" + mean_str + "}"
        rows.append(
            f"  {r.algorithm_name} & {r.best_cost:.3f} & "
            f"${mean_str} \\pm {r.std_cost:.3f}$ & "
            f"{cv:.1f} & {feas_pct:.0f} & {r.average_runtime:.1f} \\\\"
        )

    lines = [
        r"\begin{table}[ht]",
        r"  \centering",
        f"  \\caption{{{caption}}}",
        f"  \\label{{{label}}}",
        r"  \begin{tabular}{lrrrrrr}",
        r"    \hline",
        r"    \textbf{Algorithm} & \textbf{Best} & \textbf{Mean $\pm$ Std}"
        r" & \textbf{CV\%} & \textbf{Feasible\%} & \textbf{Avg time (s)} \\",
        r"    \hline",
    ] + rows + [
        r"    \hline",
        r"  \end{tabular}",
        r"\end{table}",
    ]
    return "\n".join(lines)
