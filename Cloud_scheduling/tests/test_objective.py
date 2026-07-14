"""
test_objective.py — Sanity tests for the cloud scheduling objective function.

Each test constructs a tiny problem instance by hand, computes the expected
F(X), and verifies that evaluate_schedule() returns the same number.  This
gives empirical proof that the formula implementation matches the thesis
specification, line by line.

Run from the Cloud_scheduling directory:
    uv run python tests/test_objective.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make the package importable when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import math

import numpy as np
import pandas as pd

from tools.data_loader import SchedulingProblemData
from tools.objective import (
    ObjectiveWeights,
    compute_normalization_constants,
    evaluate_schedule,
)


# ---------------------------------------------------------------------------
# Hand-built tiny instance: 4 tasks × 3 servers
# ---------------------------------------------------------------------------

def _tiny_instance() -> SchedulingProblemData:
    """
    4 tasks, 3 servers.  Resource demands and capacities chosen so the
    arithmetic is easy to verify on paper:

      Task  cpu  mem  energy  latency  priority
       0     50  100    20      100      0  (Low,    ω=1)
       1     30   50    10       50      1  (Medium, ω=2)
       2     40   80    15       80      2  (High,   ω=4)
       3     20   40     5       40      0  (Low,    ω=1)

      Server  cap_cpu  cap_mem  idle  η
        0      100      200     10   1.0
        1       80      150     20   1.5
        2       60      100     15   0.8
    """
    tasks_df = pd.DataFrame({"_": [0, 1, 2, 3]})  # placeholder; not used by evaluate_schedule
    return SchedulingProblemData(
        tasks=tasks_df,
        n_tasks=4,
        n_servers=3,
        cpu=np.array([50, 30, 40, 20], dtype=np.float64),
        mem=np.array([100, 50, 80, 40], dtype=np.float64),
        energy=np.array([20, 10, 15, 5], dtype=np.float64),
        latency=np.array([100, 50, 80, 40], dtype=np.float64),
        priority=np.array([0, 1, 2, 0], dtype=np.int32),
        server_cpu_cap=np.array([100, 80, 60], dtype=np.float64),
        server_mem_cap=np.array([200, 150, 100], dtype=np.float64),
        server_idle_power=np.array([10, 20, 15], dtype=np.float64),
        server_efficiency=np.array([1.0, 1.5, 0.8], dtype=np.float64),
    )


# ---------------------------------------------------------------------------
# Test 1 — Feasible packing with no congestion
# ---------------------------------------------------------------------------

def test_feasible_no_congestion() -> None:
    """
    Place each task on its own server (assignment = [0, 1, 0, 2]):
      Server 0: tasks 0, 2  (cpu=90, mem=180) — within capacity
      Server 1: task 1      (cpu=30, mem=50)  — within capacity
      Server 2: task 3      (cpu=20, mem=40)  — within capacity

    Expected (γ=1, raw units, no normalisation):

      idle_energy     = 10 + 20 + 15 = 45 W   (all 3 servers active)
      workload_energy = η_0·e_0 + η_1·e_1 + η_0·e_2 + η_2·e_3
                      = 1.0·20 + 1.5·10 + 1.0·15 + 0.8·5
                      = 20 + 15 + 15 + 4 = 54
      total_energy    = 45 + 54 = 99 W

      load_ratio[0] = 90/100 = 0.90
      load_ratio[1] = 30/80  = 0.375
      load_ratio[2] = 20/60  = 0.333…
      eff_latency[0] = 100·(1 + 0.90)  = 190.0
      eff_latency[1] =  50·(1 + 0.375) =  68.75
      eff_latency[2] =  80·(1 + 0.90)  = 152.0
      eff_latency[3] =  40·(1 + 0.333) =  53.333…
      ω = [1, 2, 4, 1]
      total_latency = 1·190 + 2·68.75 + 4·152 + 1·53.333…
                    = 190 + 137.5 + 608 + 53.333…
                    = 988.833…

      cpu_violation = max(0, 90-100) + max(0, 30-80) + max(0, 20-60) = 0
      mem_violation = 0
      feasible = True
    """
    data = _tiny_instance()
    weights = ObjectiveWeights(
        energy_weight=1.0, latency_weight=1.0,
        cpu_penalty=10.0, mem_penalty=10.0, congestion_factor=1.0,
    )

    assignment = [0, 1, 0, 2]
    ev = evaluate_schedule(assignment, data, weights)

    expected_energy  = 45 + 54
    expected_latency = 1 * 100 * 1.90 + 2 * 50 * 1.375 + 4 * 80 * 1.90 + 1 * 40 * (1 + 20/60)
    expected_F       = expected_energy + expected_latency

    assert math.isclose(ev.total_energy, expected_energy, rel_tol=1e-9), \
        f"energy: got {ev.total_energy}, expected {expected_energy}"
    assert math.isclose(ev.total_latency, expected_latency, rel_tol=1e-9), \
        f"latency: got {ev.total_latency}, expected {expected_latency}"
    assert ev.cpu_violation == 0.0
    assert ev.mem_violation == 0.0
    assert ev.feasible is True
    assert ev.n_active_servers == 3
    assert math.isclose(ev.objective_value, expected_F, rel_tol=1e-9), \
        f"F(X): got {ev.objective_value}, expected {expected_F}"

    print(f"  [PASS] test_feasible_no_congestion: F(X) = {ev.objective_value:.4f} (expected {expected_F:.4f})")


# ---------------------------------------------------------------------------
# Test 2 — Capacity violation produces correct penalty
# ---------------------------------------------------------------------------

def test_capacity_violation() -> None:
    """
    Place all 4 tasks on server 2 (cap_cpu=60, cap_mem=100):
      cpu_load[2] = 50+30+40+20 = 140 — violates cap by 80
      mem_load[2] = 100+50+80+40 = 270 — violates cap by 170
      cpu_violation = 80
      mem_violation = 170
      feasible = False

    With cpu_penalty=10 and mem_penalty=10 (raw units, no normalisation):
      penalty_cpu = 10 * 80 = 800
      penalty_mem = 10 * 170 = 1700
    """
    data = _tiny_instance()
    weights = ObjectiveWeights(
        energy_weight=1.0, latency_weight=1.0,
        cpu_penalty=10.0, mem_penalty=10.0, congestion_factor=1.0,
    )

    assignment = [2, 2, 2, 2]
    ev = evaluate_schedule(assignment, data, weights)

    assert ev.cpu_violation == 80.0, f"cpu_violation: got {ev.cpu_violation}"
    assert ev.mem_violation == 170.0, f"mem_violation: got {ev.mem_violation}"
    assert ev.feasible is False
    assert ev.n_active_servers == 1

    # The penalty terms should appear in F(X)
    assert ev.objective_value > ev.total_energy + ev.total_latency, \
        "F(X) should be greater than just energy+latency when there are violations"

    print(f"  [PASS] test_capacity_violation: violations correctly detected and penalised")


# ---------------------------------------------------------------------------
# Test 3 — Priority weights ω(p) ∈ {1, 2, 4}
# ---------------------------------------------------------------------------

def test_priority_weights() -> None:
    """
    Place all 4 tasks on server 0.  Latency should be priority-weighted:
      Task 0 (Low,    ω=1): base_lat=100, eff_lat=100·(1+1·140/100)=240
      Task 1 (Medium, ω=2): base_lat=50,  eff_lat=50·(1+1.4)=120
      Task 2 (High,   ω=4): base_lat=80,  eff_lat=80·(1+1.4)=192
      Task 3 (Low,    ω=1): base_lat=40,  eff_lat=40·(1+1.4)=96

      total_latency = 1·240 + 2·120 + 4·192 + 1·96
                    = 240 + 240 + 768 + 96 = 1344
    """
    data = _tiny_instance()
    weights = ObjectiveWeights(
        energy_weight=1.0, latency_weight=1.0,
        cpu_penalty=10.0, mem_penalty=10.0, congestion_factor=1.0,
    )

    assignment = [0, 0, 0, 0]
    ev = evaluate_schedule(assignment, data, weights)

    expected_latency = 1 * 240 + 2 * 120 + 4 * 192 + 1 * 96
    assert math.isclose(ev.total_latency, expected_latency, rel_tol=1e-9), \
        f"priority-weighted latency: got {ev.total_latency}, expected {expected_latency}"

    print(f"  [PASS] test_priority_weights: omega(Low/Med/High) = (1,2,4) correctly applied")


# ---------------------------------------------------------------------------
# Test 4 — Congestion factor γ scales latency correctly
# ---------------------------------------------------------------------------

def test_congestion_factor() -> None:
    """
    Same assignment, two different γ values:
      With γ=0: latency should equal Σ ω · l_i (no congestion adjustment).
      With γ=2: latency at load_ratio=r should be l_i · (1+2r).
    """
    data = _tiny_instance()

    # γ = 0 → eff_latency = base_latency
    w0 = ObjectiveWeights(
        energy_weight=1.0, latency_weight=1.0,
        cpu_penalty=10.0, mem_penalty=10.0, congestion_factor=0.0,
    )
    ev0 = evaluate_schedule([0, 0, 0, 0], data, w0)
    base_latency = 1 * 100 + 2 * 50 + 4 * 80 + 1 * 40   # 1*100+2*50+4*80+1*40 = 560
    assert math.isclose(ev0.total_latency, base_latency, rel_tol=1e-9), \
        f"γ=0 latency: got {ev0.total_latency}, expected {base_latency}"

    # γ = 2 → load_ratio = 140/100 = 1.4, eff multiplier = 1+2·1.4 = 3.8
    w2 = ObjectiveWeights(
        energy_weight=1.0, latency_weight=1.0,
        cpu_penalty=10.0, mem_penalty=10.0, congestion_factor=2.0,
    )
    ev2 = evaluate_schedule([0, 0, 0, 0], data, w2)
    expected_latency_g2 = 3.8 * base_latency
    assert math.isclose(ev2.total_latency, expected_latency_g2, rel_tol=1e-9), \
        f"γ=2 latency: got {ev2.total_latency}, expected {expected_latency_g2}"

    print(f"  [PASS] test_congestion_factor: gamma=0 -> no congestion, gamma=2 -> 3.8x multiplier")


# ---------------------------------------------------------------------------
# Test 5 — Normalisation constants
# ---------------------------------------------------------------------------

def test_normalization_constants() -> None:
    """
    For the tiny instance:
      E_ref = Σ idle + max(η)·Σ e = (10+20+15) + 1.5·(20+10+15+5) = 45 + 75 = 120
      CPU_ref = Σ cpu = 50+30+40+20 = 140
      Mem_ref = Σ mem = 100+50+80+40 = 270
      L_ref with γ=1:
        max_load_ratio = Σcpu / min(cap) = 140 / 60 ≈ 2.333…
        Σω·l = 1·100 + 2·50 + 4·80 + 1·40 = 560
        L_ref = (1 + 1·2.333…) · 560 ≈ 1866.667
    """
    data = _tiny_instance()
    e_ref, l_ref, cpu_ref, mem_ref = compute_normalization_constants(data, congestion_factor=1.0)

    assert math.isclose(e_ref, 45 + 75, rel_tol=1e-9), f"E_ref: got {e_ref}, expected 120"
    assert math.isclose(cpu_ref, 140.0, rel_tol=1e-9)
    assert math.isclose(mem_ref, 270.0, rel_tol=1e-9)
    expected_l_ref = (1 + 140.0 / 60.0) * 560
    assert math.isclose(l_ref, expected_l_ref, rel_tol=1e-9), \
        f"L_ref: got {l_ref}, expected {expected_l_ref}"

    print(f"  [PASS] test_normalization_constants: E_ref={e_ref:.2f}, L_ref={l_ref:.2f}, "
          f"CPU_ref={cpu_ref:.2f}, Mem_ref={mem_ref:.2f}")


# ---------------------------------------------------------------------------
# Test 6 — Normalised F(X) is always in [0, ∞), with each term ≤ 1 in feasible region
# ---------------------------------------------------------------------------

def test_normalised_terms_in_unit_range() -> None:
    """
    For a feasible solution with γ=1, the normalised energy and latency terms
    should both be in [0, 1] (since refs are worst-case upper bounds).
    """
    data = _tiny_instance()
    e_ref, l_ref, cpu_ref, mem_ref = compute_normalization_constants(data, congestion_factor=1.0)

    weights = ObjectiveWeights(
        energy_weight=1.0, latency_weight=1.0,
        cpu_penalty=10.0, mem_penalty=10.0, congestion_factor=1.0,
        energy_ref=e_ref, latency_ref=l_ref, cpu_ref=cpu_ref, mem_ref=mem_ref,
    )

    # Feasible assignment from test 1
    ev = evaluate_schedule([0, 1, 0, 2], data, weights)
    e_term = ev.total_energy / e_ref
    l_term = ev.total_latency / l_ref

    assert 0 <= e_term <= 1.0, f"normalised energy term out of range: {e_term}"
    assert 0 <= l_term <= 1.0, f"normalised latency term out of range: {l_term}"
    assert ev.feasible is True
    assert math.isclose(ev.objective_value, e_term + l_term, rel_tol=1e-9), \
        "F(X) should equal sum of normalised energy and latency for feasible solution"

    print(f"  [PASS] test_normalised_terms_in_unit_range: E_norm={e_term:.3f}, L_norm={l_term:.3f}")


# ---------------------------------------------------------------------------
# Test 7 — Single-task assignment uses only one server's idle power
# ---------------------------------------------------------------------------

def test_single_task_one_server_active() -> None:
    """One task on server 0: idle_energy = 10 (only server 0 active)."""
    data = _tiny_instance()
    weights = ObjectiveWeights(
        energy_weight=1.0, latency_weight=1.0,
        cpu_penalty=10.0, mem_penalty=10.0, congestion_factor=1.0,
    )
    # Put just one task on server 0 by setting the others on... wait, we need 4 tasks.
    # Instead, put all 4 on server 0:
    ev = evaluate_schedule([0, 0, 0, 0], data, weights)
    assert ev.n_active_servers == 1, f"expected 1 active server, got {ev.n_active_servers}"

    # Idle energy should be exactly server 0's idle = 10
    # Workload energy = 1.0·(20+10+15+5) = 50
    expected_energy = 10 + 50
    assert math.isclose(ev.total_energy, expected_energy, rel_tol=1e-9), \
        f"single-server energy: got {ev.total_energy}, expected {expected_energy}"

    print(f"  [PASS] test_single_task_one_server_active: only one server's idle power counted")


# ---------------------------------------------------------------------------
# Test 8 — Empty servers contribute zero idle energy
# ---------------------------------------------------------------------------

def test_empty_servers_no_idle_cost() -> None:
    """
    Place tasks only on server 1 (none on 0 or 2).  Servers 0 and 2 should
    be inactive (yⱼ=0) and contribute zero idle energy.
    """
    data = _tiny_instance()
    weights = ObjectiveWeights(
        energy_weight=1.0, latency_weight=1.0,
        cpu_penalty=10.0, mem_penalty=10.0, congestion_factor=1.0,
    )

    # All 4 tasks on server 1
    ev = evaluate_schedule([1, 1, 1, 1], data, weights)
    assert ev.n_active_servers == 1

    # Only server 1's idle counted: 20
    # Workload: 1.5 · (20+10+15+5) = 75
    expected_energy = 20 + 75
    assert math.isclose(ev.total_energy, expected_energy, rel_tol=1e-9), \
        f"got {ev.total_energy}, expected {expected_energy}"

    print(f"  [PASS] test_empty_servers_no_idle_cost: inactive servers contribute 0")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all() -> None:
    tests = [
        test_feasible_no_congestion,
        test_capacity_violation,
        test_priority_weights,
        test_congestion_factor,
        test_normalization_constants,
        test_normalised_terms_in_unit_range,
        test_single_task_one_server_active,
        test_empty_servers_no_idle_cost,
    ]

    print("=" * 70)
    print("  Objective Function Sanity Tests — Cloud Scheduling")
    print("=" * 70)

    failures = 0
    for test in tests:
        try:
            test()
        except AssertionError as exc:
            print(f"  [FAIL] {test.__name__}: {exc}")
            failures += 1
        except Exception as exc:
            print(f"  [ERROR] {test.__name__}: {type(exc).__name__}: {exc}")
            failures += 1

    print("=" * 70)
    if failures == 0:
        print(f"  All {len(tests)} tests passed — objective function matches thesis formula.")
    else:
        print(f"  {failures}/{len(tests)} tests FAILED — see output above.")
        sys.exit(1)


if __name__ == "__main__":
    run_all()
