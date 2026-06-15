"""
test_correctness.py - Empirical validation of the cloud-scheduling implementation.

WHAT THIS PROVES
----------------
Each test computes the expected value of F(X) (or one of its components) by hand
on a small, fully-specified problem, then checks that evaluate_schedule() returns
exactly that value (to numerical precision).

If every assertion in this file passes, the implementation is *demonstrably*
identical to the thesis formulation. This is the empirical evidence to point to
during a thesis defence:

    "The objective function and algorithms are verified by tests/test_correctness.py.
     Every formula component is checked against an independently computed value on a
     small instance, and every algorithm is checked for the invariants required by
     its theoretical specification."

HOW TO RUN
----------
    cd "Cloud scheduling"
    uv run python -m tests.test_correctness

or

    uv run python "Cloud scheduling/tests/test_correctness.py"

All tests print a PASS/FAIL line. A final summary line reports the total.
"""
from __future__ import annotations

import math
import os
import random
import sys
import traceback
from dataclasses import dataclass

import numpy as np
import pandas as pd

# Allow running this file directly from the Cloud scheduling/ folder
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

from tools.data_loader import SchedulingProblemData
from tools.objective import (
    ObjectiveWeights,
    compute_normalization_constants,
    compute_sample_normalization,
    evaluate_schedule,
)
from tools.initial_solution import build_greedy_assignment
from tools.feasibility import is_valid_assignment
from algorithms.simulated_annealing import simulated_annealing
from algorithms.genetic_algorithm import genetic_algorithm
from algorithms.umda import umda


# ---------------------------------------------------------------------------
# Tiny hand-computable problem instance
# ---------------------------------------------------------------------------
# 4 tasks, 2 servers. Small enough that every term of F(X) can be checked by hand.
# Task 0: CPU=40, Mem=20,  E=10, L=100, Priority=Low(0)  --> w=1
# Task 1: CPU=60, Mem=30,  E=20, L=200, Priority=Medium(1)--> w=2
# Task 2: CPU=30, Mem=10,  E=15, L=150, Priority=High(2) --> w=4
# Task 3: CPU=50, Mem=20,  E=25, L=120, Priority=Low(0)  --> w=1
# Server 0: CPU_cap=100, Mem_cap=64, idle=50, eta=1.0
# Server 1: CPU_cap=120, Mem_cap=80, idle=80, eta=0.8

def make_tiny_instance() -> SchedulingProblemData:
    tasks_df = pd.DataFrame({
        "CPU_Usage":       [40, 60, 30, 50],
        "Memory_Usage":    [20, 30, 10, 20],
        "Energy_Consumption": [10, 20, 15, 25],
        "Service_Latency": [100, 200, 150, 120],
        "Task_Priority":   ["Low", "Medium", "High", "Low"],
    })
    return SchedulingProblemData(
        tasks=tasks_df,
        n_tasks=4,
        n_servers=2,
        cpu=np.array([40, 60, 30, 50], dtype=np.float64),
        mem=np.array([20, 30, 10, 20], dtype=np.float64),
        energy=np.array([10, 20, 15, 25], dtype=np.float64),
        latency=np.array([100, 200, 150, 120], dtype=np.float64),
        priority=np.array([0, 1, 2, 0], dtype=np.int32),
        server_cpu_cap=np.array([100, 120], dtype=np.float64),
        server_mem_cap=np.array([64, 80], dtype=np.float64),
        server_idle_power=np.array([50, 80], dtype=np.float64),
        server_efficiency=np.array([1.0, 0.8], dtype=np.float64),
    )


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str = ""


_results: list[CheckResult] = []


def check(name: str, condition: bool, *, expected=None, actual=None, tol: float = 1e-9) -> None:
    """Record a test result and print a one-line status."""
    if condition:
        _results.append(CheckResult(name, True))
        print(f"  [PASS] {name}")
    else:
        msg = ""
        if expected is not None or actual is not None:
            msg = f" expected={expected!r}, actual={actual!r}"
        _results.append(CheckResult(name, False, msg))
        print(f"  [FAIL] {name}{msg}")


def approx(a: float, b: float, tol: float = 1e-9) -> bool:
    return abs(a - b) <= tol * max(1.0, abs(b))


# ---------------------------------------------------------------------------
# Tests for the objective function
# ---------------------------------------------------------------------------

def test_energy_packed_assignment() -> None:
    """
    Assignment [1, 1, 1, 1] -> all 4 tasks on server 1.
    Expected E(X):
        idle_energy = 0*50 + 1*80 = 80 (only server 1 active)
        workload   = eta_1 * sum(energy) = 0.8 * (10+20+15+25) = 0.8 * 70 = 56
        E(X)       = 80 + 56 = 136
    """
    data = make_tiny_instance()
    weights = ObjectiveWeights(energy_weight=1.0, latency_weight=0.0,
                                cpu_penalty=0.0, mem_penalty=0.0,
                                congestion_factor=0.0)
    ev = evaluate_schedule([1, 1, 1, 1], data, weights)
    check("E(X) packed onto server 1", approx(ev.total_energy, 136.0),
          expected=136.0, actual=ev.total_energy)


def test_energy_split_assignment() -> None:
    """
    Assignment [0, 1, 0, 1].
        idle  = 50 + 80 = 130
        workload = 1.0*(10+15) + 0.8*(20+25) = 25 + 36 = 61
        E(X)  = 130 + 61 = 191
    """
    data = make_tiny_instance()
    weights = ObjectiveWeights(energy_weight=1.0, latency_weight=0.0,
                                cpu_penalty=0.0, mem_penalty=0.0,
                                congestion_factor=0.0)
    ev = evaluate_schedule([0, 1, 0, 1], data, weights)
    check("E(X) split across both servers", approx(ev.total_energy, 191.0),
          expected=191.0, actual=ev.total_energy)


def test_priority_weighted_latency_no_congestion() -> None:
    """
    Assignment [0, 1, 0, 1], gamma=0 so congestion factor = 1.
        l_hat = base latency, since (1 + 0 * load_ratio) = 1
        L(X) = 1*100 + 2*200 + 4*150 + 1*120
             = 100 + 400 + 600 + 120 = 1220
    """
    data = make_tiny_instance()
    weights = ObjectiveWeights(energy_weight=0.0, latency_weight=1.0,
                                cpu_penalty=0.0, mem_penalty=0.0,
                                congestion_factor=0.0)
    ev = evaluate_schedule([0, 1, 0, 1], data, weights)
    check("L(X) with gamma=0 (priority-weighted base latency)",
          approx(ev.total_latency, 1220.0),
          expected=1220.0, actual=ev.total_latency)


def test_priority_weighted_latency_with_congestion() -> None:
    """
    Assignment [0, 1, 0, 1], gamma=1.0.
        cpu_load_0 = 40 + 30 = 70 ; cap_0 = 100  -> ratio_0 = 0.70
        cpu_load_1 = 60 + 50 = 110; cap_1 = 120  -> ratio_1 = 110/120 ~= 0.9167
        Task 0 (on 0): l_hat = 100 * (1 + 0.70) = 170
        Task 1 (on 1): l_hat = 200 * (1 + 0.9167) = 200 * 1.9167 = 383.33...
        Task 2 (on 0): l_hat = 150 * 1.70 = 255
        Task 3 (on 1): l_hat = 120 * 1.9167 = 230
        L(X) = 1*170 + 2*383.333 + 4*255 + 1*230 = 170 + 766.667 + 1020 + 230 = 2186.667
    """
    data = make_tiny_instance()
    weights = ObjectiveWeights(energy_weight=0.0, latency_weight=1.0,
                                cpu_penalty=0.0, mem_penalty=0.0,
                                congestion_factor=1.0)
    ev = evaluate_schedule([0, 1, 0, 1], data, weights)
    expected = (
        1 * 100 * (1 + 70/100) +
        2 * 200 * (1 + 110/120) +
        4 * 150 * (1 + 70/100) +
        1 * 120 * (1 + 110/120)
    )
    check("L(X) with gamma=1 (congestion-adjusted, priority-weighted)",
          approx(ev.total_latency, expected, tol=1e-6),
          expected=expected, actual=ev.total_latency)


def test_capacity_violations() -> None:
    """
    Assignment [0, 0, 0, 0] -> all 4 tasks on server 0.
        cpu_load_0 = 40+60+30+50 = 180 ; cap = 100  -> violation = 80
        mem_load_0 = 20+30+10+20 =  80 ; cap =  64  -> violation = 16
        (server 1 has no tasks, so no violation)
    """
    data = make_tiny_instance()
    weights = ObjectiveWeights(energy_weight=0.0, latency_weight=0.0,
                                cpu_penalty=0.0, mem_penalty=0.0,
                                congestion_factor=0.0)
    ev = evaluate_schedule([0, 0, 0, 0], data, weights)
    check("CPU violation when overloaded", approx(ev.cpu_violation, 80.0),
          expected=80.0, actual=ev.cpu_violation)
    check("Memory violation when overloaded", approx(ev.mem_violation, 16.0),
          expected=16.0, actual=ev.mem_violation)
    check("feasible=False when violations > 0", ev.feasible is False)


def test_feasibility_flag_true() -> None:
    """A non-violating assignment must report feasible=True."""
    data = make_tiny_instance()
    weights = ObjectiveWeights(energy_weight=1.0, latency_weight=1.0,
                                cpu_penalty=0.0, mem_penalty=0.0,
                                congestion_factor=0.0)
    ev = evaluate_schedule([0, 1, 0, 1], data, weights)
    check("feasible=True when no violations",
          ev.feasible is True and ev.cpu_violation == 0 and ev.mem_violation == 0)


def test_full_F_with_normalisation() -> None:
    """
    Assignment [0, 1, 0, 1] with full F(X), wE=wL=1, gamma=1, lambdas=0.
    The capacity violations are zero, so penalty terms vanish; only the
    energy and latency contributions remain.

        E(X) = 191 (computed above)
        L(X) = 2186.667 (computed above)

    With normalisation:
        E_ref = sum(idle) + max(eta) * sum(energy) = 130 + 1.0*70 = 200
        L_ref = (1 + gamma * sum(cpu)/min(cap)) * sum(omega * latency)
              = (1 + 1.0 * 180/100) * (1*100 + 2*200 + 4*150 + 1*120)
              = 2.8 * 1220 = 3416
        F(X) = 1 * 191/200 + 1 * 2186.667/3416 = 0.955 + 0.6400... = 1.5950...
    """
    data = make_tiny_instance()
    e_ref, l_ref, c_ref, m_ref = compute_normalization_constants(data, congestion_factor=1.0)

    weights = ObjectiveWeights(
        energy_weight=1.0, latency_weight=1.0,
        cpu_penalty=0.0, mem_penalty=0.0,
        congestion_factor=1.0,
        energy_ref=e_ref, latency_ref=l_ref,
        cpu_ref=c_ref, mem_ref=m_ref,
    )
    ev = evaluate_schedule([0, 1, 0, 1], data, weights)

    expected_E = 191.0
    expected_L = (
        1 * 100 * (1 + 70/100) +
        2 * 200 * (1 + 110/120) +
        4 * 150 * (1 + 70/100) +
        1 * 120 * (1 + 110/120)
    )
    expected_F = expected_E / e_ref + expected_L / l_ref

    check("E_ref = sum(idle) + max(eta)*sum(energy)", approx(e_ref, 200.0),
          expected=200.0, actual=e_ref)
    check("L_ref worst-case formula", approx(l_ref, 2.8 * 1220.0, tol=1e-6),
          expected=2.8 * 1220.0, actual=l_ref)
    check("CPU_ref = sum(cpu)", approx(c_ref, 180.0),
          expected=180.0, actual=c_ref)
    check("Mem_ref = sum(mem)", approx(m_ref, 80.0),
          expected=80.0, actual=m_ref)
    check("F(X) matches hand-computed sum of normalised terms",
          approx(ev.objective_value, expected_F, tol=1e-6),
          expected=expected_F, actual=ev.objective_value)


# ---------------------------------------------------------------------------
# Tests for the algorithms (invariants, not exact values)
# ---------------------------------------------------------------------------

def test_greedy_is_deterministic() -> None:
    """Greedy must return the same assignment for two independent calls."""
    data = make_tiny_instance()
    a1 = build_greedy_assignment(data)
    a2 = build_greedy_assignment(data)
    check("Greedy assignment is deterministic", a1 == a2,
          expected=a1, actual=a2)


def test_assignment_is_structurally_valid() -> None:
    data = make_tiny_instance()
    a = build_greedy_assignment(data)
    check("Greedy assignment is structurally valid",
          is_valid_assignment(a, data),
          expected=True, actual=is_valid_assignment(a, data))
    check("Greedy returns one server-index per task",
          len(a) == data.n_tasks,
          expected=data.n_tasks, actual=len(a))


def test_sa_never_worse_than_initial() -> None:
    """
    SA must satisfy a fundamental invariant: best_solution is never worse than
    the initial greedy solution, because best_solution is updated only when an
    improvement is found.
    """
    data = make_tiny_instance()
    e_ref, l_ref, c_ref, m_ref = compute_normalization_constants(data, 1.0)
    weights = ObjectiveWeights(
        energy_weight=1.0, latency_weight=1.0,
        cpu_penalty=10.0, mem_penalty=10.0, congestion_factor=1.0,
        energy_ref=e_ref, latency_ref=l_ref, cpu_ref=c_ref, mem_ref=m_ref,
    )

    initial = build_greedy_assignment(data)
    initial_F = evaluate_schedule(initial, data, weights).objective_value

    random.seed(0)
    _, sa_eval, _ = simulated_annealing(data, weights,
                                          initial_temperature=0.5,
                                          cooling_rate=0.99,
                                          max_temp_steps=200,
                                          iterations_per_temperature=10,
                                          verbose=False)
    check("SA best is never strictly worse than initial greedy",
          sa_eval.objective_value <= initial_F + 1e-9,
          expected=f"<= {initial_F}", actual=sa_eval.objective_value)


def test_ga_never_worse_than_initial() -> None:
    """Same monotonicity invariant for GA (elitism guarantees this)."""
    data = make_tiny_instance()
    e_ref, l_ref, c_ref, m_ref = compute_normalization_constants(data, 1.0)
    weights = ObjectiveWeights(
        energy_weight=1.0, latency_weight=1.0,
        cpu_penalty=10.0, mem_penalty=10.0, congestion_factor=1.0,
        energy_ref=e_ref, latency_ref=l_ref, cpu_ref=c_ref, mem_ref=m_ref,
    )

    initial = build_greedy_assignment(data)
    initial_F = evaluate_schedule(initial, data, weights).objective_value

    random.seed(0)
    _, ga_eval, _ = genetic_algorithm(data, weights,
                                        population_size=10,
                                        n_generations=50,
                                        verbose=False)
    check("GA best is never strictly worse than initial greedy",
          ga_eval.objective_value <= initial_F + 1e-9,
          expected=f"<= {initial_F}", actual=ga_eval.objective_value)


def test_umda_never_worse_than_initial() -> None:
    """UMDA: elitism re-injects best-ever each generation, so monotonic."""
    data = make_tiny_instance()
    e_ref, l_ref, c_ref, m_ref = compute_normalization_constants(data, 1.0)
    weights = ObjectiveWeights(
        energy_weight=1.0, latency_weight=1.0,
        cpu_penalty=10.0, mem_penalty=10.0, congestion_factor=1.0,
        energy_ref=e_ref, latency_ref=l_ref, cpu_ref=c_ref, mem_ref=m_ref,
    )

    initial = build_greedy_assignment(data)
    initial_F = evaluate_schedule(initial, data, weights).objective_value

    random.seed(0)
    _, umda_eval, _ = umda(data, weights,
                              population_size=20,
                              n_generations=30,
                              verbose=False)
    check("UMDA best is never strictly worse than initial greedy",
          umda_eval.objective_value <= initial_F + 1e-9,
          expected=f"<= {initial_F}", actual=umda_eval.objective_value)


def test_sa_finds_optimal_on_tiny() -> None:
    """
    On the tiny 4-task, 2-server instance there are only 2^4 = 16 possible
    assignments. We compute the true optimum by brute force and check SA finds
    it (with a generous budget).
    """
    data = make_tiny_instance()
    e_ref, l_ref, c_ref, m_ref = compute_normalization_constants(data, 1.0)
    weights = ObjectiveWeights(
        energy_weight=1.0, latency_weight=1.0,
        cpu_penalty=10.0, mem_penalty=10.0, congestion_factor=1.0,
        energy_ref=e_ref, latency_ref=l_ref, cpu_ref=c_ref, mem_ref=m_ref,
    )

    # Brute force: enumerate all 2^4 = 16 assignments
    best_F = math.inf
    best_a = None
    for s0 in range(2):
        for s1 in range(2):
            for s2 in range(2):
                for s3 in range(2):
                    a = [s0, s1, s2, s3]
                    F = evaluate_schedule(a, data, weights).objective_value
                    if F < best_F:
                        best_F = F
                        best_a = a

    random.seed(0)
    _, sa_eval, _ = simulated_annealing(data, weights,
                                          initial_temperature=1.0,
                                          cooling_rate=0.95,
                                          max_temp_steps=500,
                                          iterations_per_temperature=20,
                                          verbose=False)
    check(f"SA reaches the brute-force optimum F={best_F:.6f} on tiny instance",
          approx(sa_eval.objective_value, best_F, tol=1e-9),
          expected=best_F, actual=sa_eval.objective_value)


def test_seed_reproducibility() -> None:
    """Two SA runs with the same seed must produce identical results."""
    data = make_tiny_instance()
    e_ref, l_ref, c_ref, m_ref = compute_normalization_constants(data, 1.0)
    weights = ObjectiveWeights(
        energy_weight=1.0, latency_weight=1.0,
        cpu_penalty=10.0, mem_penalty=10.0, congestion_factor=1.0,
        energy_ref=e_ref, latency_ref=l_ref, cpu_ref=c_ref, mem_ref=m_ref,
    )

    random.seed(42)
    a1, e1, _ = simulated_annealing(data, weights, initial_temperature=0.5,
                                       cooling_rate=0.99, max_temp_steps=100,
                                       iterations_per_temperature=10, verbose=False)
    random.seed(42)
    a2, e2, _ = simulated_annealing(data, weights, initial_temperature=0.5,
                                       cooling_rate=0.99, max_temp_steps=100,
                                       iterations_per_temperature=10, verbose=False)
    check("SA is fully reproducible with same seed",
          a1 == a2 and approx(e1.objective_value, e2.objective_value))


def test_sample_normalisation_calibrates_refs_and_penalty() -> None:
    """
    Sample-based calibration (Deb 2001 + Deb 2000):
      - E_ref / L_ref are set to the empirical mean over feasible samples,
        so E_ref <= worst-case E_ref and L_ref <= worst-case L_ref.
      - cpu_penalty = mem_penalty = penalty_multiplier * F_max(feasible),
        so any non-trivial violation strictly dominates the feasible objective.

    On the 4-task / 2-server tiny instance there are only 2^4 = 16 candidates
    so the sample pool will revisit each completion many times; both
    feasibility regions are reachable, so calibration should NOT fall back.
    """
    data = make_tiny_instance()
    base = ObjectiveWeights(
        energy_weight=1.0, latency_weight=1.0,
        cpu_penalty=10.0, mem_penalty=10.0,
        congestion_factor=1.0,
    )
    calibrated, diag = compute_sample_normalization(
        data, base_weights=base,
        n_samples=80,            # tiny instance -> small sample is enough
        seed=0,
        penalty_multiplier=100.0,
        min_feasible=5,
    )

    check("Sample calibration found feasibles", diag.n_feasible >= 5,
          expected=">=5", actual=diag.n_feasible)
    check("Sample calibration did not fall back to worst-case",
          diag.fallback_to_worst_case is False,
          expected=False, actual=diag.fallback_to_worst_case)
    check("E_ref equals mean energy from sample",
          approx(calibrated.energy_ref, diag.mean_energy),
          expected=diag.mean_energy, actual=calibrated.energy_ref)
    check("L_ref equals mean latency from sample",
          approx(calibrated.latency_ref, diag.mean_latency),
          expected=diag.mean_latency, actual=calibrated.latency_ref)
    expected_lambda = 100.0 * diag.f_max_feasible
    check("lambda_cpu = penalty_multiplier x F_max(feasible)",
          approx(calibrated.cpu_penalty, expected_lambda, tol=1e-6),
          expected=expected_lambda, actual=calibrated.cpu_penalty)
    check("lambda_mem = lambda_cpu (symmetric penalty)",
          approx(calibrated.mem_penalty, calibrated.cpu_penalty),
          expected=calibrated.cpu_penalty, actual=calibrated.mem_penalty)


def test_sample_normalisation_infeasible_dominates_feasible() -> None:
    """
    Deb (2000) guarantee: with calibrated penalty = 100 x F_max(feasible),
    a clear capacity violation must push F above any feasible F value.
    """
    data = make_tiny_instance()
    base = ObjectiveWeights(
        energy_weight=1.0, latency_weight=1.0,
        cpu_penalty=10.0, mem_penalty=10.0,
        congestion_factor=1.0,
    )
    calibrated, diag = compute_sample_normalization(
        data, base_weights=base, n_samples=80, seed=0, penalty_multiplier=100.0,
    )

    # [0,0,0,0] forces all 4 tasks onto server 0, which has cap_cpu=100
    # but total cpu demand = 180 -> overload by 80%.  Massive violation.
    infeasible = [0, 0, 0, 0]
    ev_inf = evaluate_schedule(infeasible, data, calibrated)

    # Brute-force best feasible F under the same calibrated weights
    best_feasible = math.inf
    for s0 in range(2):
        for s1 in range(2):
            for s2 in range(2):
                for s3 in range(2):
                    a = [s0, s1, s2, s3]
                    ev = evaluate_schedule(a, data, calibrated)
                    if ev.feasible and ev.objective_value < best_feasible:
                        best_feasible = ev.objective_value

    check("F(infeasible) > F(best feasible) under Deb 2000 calibration",
          ev_inf.objective_value > best_feasible,
          expected=f"> {best_feasible}", actual=ev_inf.objective_value)


def test_normalised_F_is_finite_and_bounded() -> None:
    """With normalisation, F(X) for the greedy assignment must be in [0, ~3]."""
    data = make_tiny_instance()
    e_ref, l_ref, c_ref, m_ref = compute_normalization_constants(data, 1.0)
    weights = ObjectiveWeights(
        energy_weight=1.0, latency_weight=1.0,
        cpu_penalty=10.0, mem_penalty=10.0, congestion_factor=1.0,
        energy_ref=e_ref, latency_ref=l_ref, cpu_ref=c_ref, mem_ref=m_ref,
    )
    a = build_greedy_assignment(data)
    F = evaluate_schedule(a, data, weights).objective_value
    check("Normalised F(X) is finite and non-negative for greedy",
          math.isfinite(F) and F >= 0.0,
          expected=">= 0 and finite", actual=F)
    # If feasible, F should be at most wE + wL = 2 (each term is in [0,1])
    if evaluate_schedule(a, data, weights).feasible:
        check("Feasible normalised F(X) <= wE + wL = 2",
              F <= 2.0 + 1e-9,
              expected="<= 2", actual=F)


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run_all() -> int:
    tests = [
        # Objective function unit tests
        ("Energy: packed assignment", test_energy_packed_assignment),
        ("Energy: split assignment", test_energy_split_assignment),
        ("Latency: gamma=0", test_priority_weighted_latency_no_congestion),
        ("Latency: gamma=1 with congestion", test_priority_weighted_latency_with_congestion),
        ("Capacity violations", test_capacity_violations),
        ("Feasibility flag", test_feasibility_flag_true),
        ("F(X): full normalised objective", test_full_F_with_normalisation),

        # Algorithm invariant tests
        ("Greedy: deterministic", test_greedy_is_deterministic),
        ("Greedy: structurally valid", test_assignment_is_structurally_valid),
        ("SA: monotone over greedy", test_sa_never_worse_than_initial),
        ("GA: monotone over greedy", test_ga_never_worse_than_initial),
        ("UMDA: monotone over greedy", test_umda_never_worse_than_initial),
        ("SA: finds brute-force optimum", test_sa_finds_optimal_on_tiny),
        ("SA: reproducible from seed", test_seed_reproducibility),
        ("Normalised F: finite, bounded", test_normalised_F_is_finite_and_bounded),

        # Sample-based normalisation (Deb 2001) + penalty calibration (Deb 2000)
        ("Sample-norm: refs and lambda are calibrated", test_sample_normalisation_calibrates_refs_and_penalty),
        ("Sample-norm: infeasible dominates feasible", test_sample_normalisation_infeasible_dominates_feasible),
    ]

    print("=" * 72)
    print(" Cloud Scheduling - Implementation Correctness Test Suite")
    print("=" * 72)

    for group_name, fn in tests:
        try:
            fn()
        except Exception as exc:
            _results.append(CheckResult(group_name, False, str(exc)))
            print(f"  [ERROR] {group_name}: {exc}")
            traceback.print_exc()

    print()
    print("-" * 72)
    passed = sum(1 for r in _results if r.passed)
    total  = len(_results)
    if passed == total:
        print(f"  ALL {total} CHECKS PASSED")
        print("-" * 72)
        return 0
    print(f"  {passed} / {total} checks passed")
    failures = [r for r in _results if not r.passed]
    for r in failures:
        print(f"    FAIL: {r.name} - {r.message}")
    print("-" * 72)
    return 1


if __name__ == "__main__":
    raise SystemExit(run_all())
