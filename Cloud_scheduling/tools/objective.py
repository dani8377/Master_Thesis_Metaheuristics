"""
Objective function for the cloud task scheduling problem.

Scalar fitness F(X) = w_e*E(X)/E_ref + w_l*L(X)/L_ref
                    + lambda_cpu*CPU_viol/CPU_ref + lambda_mem*Mem_viol/Mem_ref

Each term is divided by a normalisation reference so all terms become
dimensionless and w_e, w_l express comparable preference shares.  Two
normalisation methods are provided:

  worst_case  -- compute_normalization_constants: each ref is the worst-case
                 (upper-bound) value of its term.  Cheap (no sampling) but
                 individual terms may sit at very different fractions of
                 their refs in practice, so w_e=w_l=1 does NOT guarantee
                 equal expected contribution.

  sample      -- compute_sample_normalization: draw N feasible solutions and
                 set E_ref / L_ref to their EMPIRICAL MEAN (Deb 2001).  Then
                 with w_e=w_l=1 the two terms contribute equally in
                 expectation, and the focus-mode multipliers become true
                 preference shares.  Penalty weights lambda_cpu / lambda_mem
                 are calibrated to 100x the maximum feasible objective so
                 every infeasible solution is dominated by every feasible
                 one (Deb 2000 parameter-less penalty).

Fully vectorised with numpy so it can be called ~150 000 times per
experiment without bottleneck.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, replace
from enum import Enum

import numpy as np

from tools.data_loader import SchedulingProblemData

# Priority weight lookup: index = priority class (0, 1, or 2)
# ω(Low=0) = 1,  ω(Medium=1) = 2,  ω(High=2) = 4
_PRIORITY_WEIGHTS = np.array([1.0, 2.0, 4.0])


# ---------------------------------------------------------------------------
# Focus modes
# ---------------------------------------------------------------------------

class FocusMode(str, Enum):
    """
    Named optimisation focus modes corresponding to thesis experiment scenarios.

    PERFORMANCE  — latency-driven: prioritise fast response times, especially
                   for high-priority tasks.  Energy cost is secondary.
    BALANCED     — neutral trade-off between energy and latency (thesis default).
                   Both terms contribute roughly equally to F(X).
    ECO          — energy-driven: minimise total power consumption (idle +
                   workload).  Latency is secondary.  Matches the thesis
                   motivation of sustainable cloud computing.
    """
    PERFORMANCE = "performance"
    BALANCED    = "balanced"
    ECO         = "eco"


# ---------------------------------------------------------------------------
# Configuration dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ObjectiveWeights:
    """
    Coefficients of the objective function.

    w_e and w_l are preference ratios that apply after the refs have divided
    each raw term to expectation 1, so (1, 1) means equal contribution and
    (0.2, 1.0) means latency counts five times as much as energy.

    lambda_cpu and lambda_mem penalise capacity violations.  Under sample-based
    calibration they are overwritten at run time with
    penalty_multiplier * F_max(feasible) (Deb 2000); the values set here are
    used only under the legacy worst_case method.

    gamma (congestion_factor) is not a weight but a parameter of the latency
    function, l_eff_i = l_i * (1 + gamma * U_j / C_j), so it changes the shape
    of L(X) before any normalisation.

    The four refs are attached in main.py once the data is loaded, by
    compute_sample_normalization() or compute_normalization_constants().  Left
    at None the objective runs in raw units, where the watts-versus-milliseconds
    scale gap dominates; that is only useful for ablation.
    """

    energy_weight: float     = 1.0      # w_e  — preference share on normalised E
    latency_weight: float    = 1.0      # w_l  — preference share on normalised L
    cpu_penalty: float       = 10.0     # lambda_cpu (worst-case mode only; overwritten under sample-based)
    mem_penalty: float       = 10.0     # lambda_mem (worst-case mode only; overwritten under sample-based)
    congestion_factor: float = 1.0      # gamma — latency-model parameter, NOT a weight
    # Normalisation reference values (None = disabled)
    energy_ref: float | None = None     # mean (Deb 2001) or worst-case E(X) for this instance
    latency_ref: float | None = None    # mean (Deb 2001) or worst-case L(X) for this instance
    cpu_ref: float | None    = None     # reference CPU violation magnitude (total CPU demand)
    mem_ref: float | None    = None     # reference memory violation magnitude (total memory demand)


# Focus-mode weight presets live in config.yaml, not here, so there is one
# source of truth.  Ad-hoc scripts can reach them through
#     load_config().objective["balanced"]   # or "performance" / "eco"


@dataclass
class ScheduleEvaluation:
    """
    Full breakdown of a schedule's cost.

    Returned by evaluate_schedule() and stored by the SA and experiment
    harness.  The objective_value field is the scalar used for all
    accept/reject decisions.
    """

    total_energy: float      # E(X) in Watts
    total_latency: float     # L(X) in ms — priority-weighted, congestion-adjusted
    cpu_violation: float     # Σ_j max(0, U_cpu_j − C_j)  in %
    mem_violation: float     # Σ_j max(0, U_mem_j − M_j)  in MB
    n_active_servers: int    # servers hosting at least one task (y_j = 1)
    objective_value: float   # F(X) — the single number SA minimises
    feasible: bool           # True when cpu_violation = mem_violation = 0


# ---------------------------------------------------------------------------
# Normalisation helper
# ---------------------------------------------------------------------------

def compute_normalization_constants(
    data: SchedulingProblemData,
    congestion_factor: float,
) -> tuple[float, float, float, float]:
    """
    Compute worst-case reference values so each objective term becomes
    dimensionless [0, 1] when divided by its reference.

    E_ref   — all servers active at idle power, all tasks on the least-efficient
              server (highest server_efficiency value, which scales workload energy up).
    L_ref   — all tasks piled onto the single smallest server, so CPU utilisation
              is at its maximum; every task experiences peak congestion.
    CPU_ref — total CPU demand across all tasks (upper bound on any violation).
    Mem_ref — total memory demand across all tasks (upper bound on any violation).
    """
    p_weights = data.priority_weights
    if p_weights is None:
        p_idx     = np.clip(data.priority, 0, 2).astype(np.int32)
        p_weights = _PRIORITY_WEIGHTS[p_idx]

    # Worst-case energy: all servers on + all tasks on the least efficient server
    e_ref = float(data.server_idle_power.sum()) + float(data.server_efficiency.max() * data.energy.sum())

    # Worst-case latency: pack all tasks onto the smallest-capacity server
    max_load_ratio = float(data.cpu.sum() / data.server_cpu_cap.min())
    l_ref = float((1.0 + congestion_factor * max_load_ratio) * np.dot(p_weights, data.latency))

    # Violation references: total demand is the tightest upper bound
    cpu_ref = float(data.cpu.sum())
    mem_ref = float(data.mem.sum())

    return e_ref, l_ref, cpu_ref, mem_ref


# ---------------------------------------------------------------------------
# Sample-based normalisation and penalty calibration (Deb 2001 / Deb 2000)
# ---------------------------------------------------------------------------

@dataclass
class CalibrationDiagnostics:
    """
    What the sample-based calibration found, written to the run manifest so a
    reported result can be traced back to the calibration behind it.
    """

    n_attempted: int        # total candidate assignments drawn
    n_feasible: int         # subset that satisfied CPU and memory capacities
    mean_energy: float      # E[E(X)] over feasible sample (= E_ref under sample-based norm)
    mean_latency: float     # E[L(X)] over feasible sample (= L_ref under sample-based norm)
    f_max_feasible: float   # max (w_e * E/E_ref + w_l * L/L_ref) over feasible sample
    penalty_multiplier: float
    fallback_to_worst_case: bool  # True if too few feasibles found and we reverted


def _sample_calibration_pool(
    data: SchedulingProblemData,
    n_samples: int,
    seed: int,
) -> list[list[int]]:
    """
    Draw n_samples candidate assignments:

        1 x     greedy BFD (deterministic, usually feasible)
        40%     greedy with 10% of genes reassigned
        30%     greedy with 30% reassigned
        ~30%    uniformly random

    The mix keeps enough samples inside the feasible region for a stable mean,
    without collapsing onto the greedy solution.
    """
    from tools.initial_solution import (
        build_greedy_assignment,
        build_random_assignment,
    )

    rng = random.Random(seed)
    n   = data.n_tasks
    m   = data.n_servers

    greedy = build_greedy_assignment(data)
    pool: list[list[int]] = [list(greedy)]

    n_low_perturb  = int(n_samples * 0.40)
    n_high_perturb = int(n_samples * 0.30)
    n_random       = n_samples - 1 - n_low_perturb - n_high_perturb

    def _perturb(base: list[int], rate: float) -> list[int]:
        out = list(base)
        for i in range(n):
            if rng.random() < rate:
                out[i] = rng.randrange(m)
        return out

    for _ in range(n_low_perturb):
        pool.append(_perturb(greedy, 0.10))
    for _ in range(n_high_perturb):
        pool.append(_perturb(greedy, 0.30))
    # Pure-random samples — use a temporary random state so we don't clobber the
    # global random.seed() the experiment harness will set later
    state = random.getstate()
    random.seed(rng.randrange(2**31 - 1))
    try:
        for _ in range(n_random):
            pool.append(build_random_assignment(data))
    finally:
        random.setstate(state)

    return pool


def compute_sample_normalization(
    data: SchedulingProblemData,
    base_weights: "ObjectiveWeights",
    n_samples: int = 150,
    seed: int = 0,
    penalty_multiplier: float = 100.0,
    min_feasible: int = 10,
) -> tuple["ObjectiveWeights", CalibrationDiagnostics]:
    """
    Sample-based normalisation (Deb 2001) with parameter-less penalty
    calibration (Deb 2000).

    Draw n_samples assignments, keep the feasible ones, and set

        E_ref = mean E(X),  L_ref = mean L(X)   over the feasible subset
        lambda_cpu = lambda_mem = penalty_multiplier * F_max_feasible

    where F_max_feasible is the largest w_e*E/E_ref + w_l*L/L_ref among the
    feasibles.  Each normalised term then has expectation 1, so the weights
    read as preference shares, and any violation above about 1% of total demand
    costs more than the entire feasible objective range.  The violation refs
    stay at total demand so lambda has the same units as the normalised
    objective.

    Falls back to compute_normalization_constants() if fewer than min_feasible
    samples are feasible, and records that in the diagnostics.

    Returns the calibrated weights and a CalibrationDiagnostics for the manifest.
    """
    pool = _sample_calibration_pool(data, n_samples=n_samples, seed=seed)

    # Evaluate with penalties and refs switched off, so the collected E(X) and
    # L(X) are raw values.
    raw_weights = replace(
        base_weights,
        cpu_penalty=0.0, mem_penalty=0.0,
        energy_ref=None, latency_ref=None, cpu_ref=None, mem_ref=None,
    )
    energies:  list[float] = []
    latencies: list[float] = []
    for assignment in pool:
        ev = evaluate_schedule(assignment, data, raw_weights)
        if ev.feasible:
            energies.append(ev.total_energy)
            latencies.append(ev.total_latency)

    cpu_ref = float(data.cpu.sum())
    mem_ref = float(data.mem.sum())

    if len(energies) < min_feasible:
        # Too few feasibles to estimate means reliably -> fall back to worst-case
        e_ref, l_ref, _, _ = compute_normalization_constants(
            data, base_weights.congestion_factor
        )
        # Keep the user-supplied penalty values from base_weights in the fallback
        calibrated = replace(
            base_weights,
            energy_ref=e_ref, latency_ref=l_ref,
            cpu_ref=cpu_ref, mem_ref=mem_ref,
        )
        return calibrated, CalibrationDiagnostics(
            n_attempted=len(pool),
            n_feasible=len(energies),
            mean_energy=float(np.mean(energies)) if energies else 0.0,
            mean_latency=float(np.mean(latencies)) if latencies else 0.0,
            f_max_feasible=0.0,
            penalty_multiplier=penalty_multiplier,
            fallback_to_worst_case=True,
        )

    e_ref = float(np.mean(energies))
    l_ref = float(np.mean(latencies))

    # Determine F_max(feasible) under the (mode-weighted) normalised objective
    # so the penalty is calibrated to *this* run's preference shares.
    f_values = [
        base_weights.energy_weight  * e / e_ref
        + base_weights.latency_weight * l / l_ref
        for e, l in zip(energies, latencies)
    ]
    f_max_feasible = float(max(f_values)) if f_values else 1.0

    lambda_value = penalty_multiplier * max(f_max_feasible, 1e-9)

    calibrated = replace(
        base_weights,
        energy_ref=e_ref, latency_ref=l_ref,
        cpu_ref=cpu_ref, mem_ref=mem_ref,
        cpu_penalty=lambda_value, mem_penalty=lambda_value,
    )

    return calibrated, CalibrationDiagnostics(
        n_attempted=len(pool),
        n_feasible=len(energies),
        mean_energy=e_ref,
        mean_latency=l_ref,
        f_max_feasible=f_max_feasible,
        penalty_multiplier=penalty_multiplier,
        fallback_to_worst_case=False,
    )


# ---------------------------------------------------------------------------
# Evaluation function
# ---------------------------------------------------------------------------

def evaluate_schedule(
    assignment: list[int],
    data: SchedulingProblemData,
    weights: ObjectiveWeights,
) -> ScheduleEvaluation:
    """
    Evaluate a candidate assignment vector and return a ScheduleEvaluation.

    assignment[i] = j  means task i is placed on server j (0-indexed).
    """
    a = np.asarray(assignment, dtype=np.int32)  # shape (n_tasks,)
    m = data.n_servers

    # Server loads: bincount(a, weights=x)[j] = sum of x[i] over tasks on j,
    # which is U_cpu_j = sum_i c_i * x_ij.
    cpu_load = np.bincount(a, weights=data.cpu, minlength=m)   # shape (m,)
    mem_load = np.bincount(a, weights=data.mem, minlength=m)   # shape (m,)
    active   = np.bincount(a, minlength=m) > 0                 # y_j

    # Energy:  E(X) = sum_j e_idle_j * y_j  +  sum_i eta_{a_i} * e_i
    idle_energy     = float(np.dot(data.server_idle_power, active))
    workload_energy = float(np.dot(data.server_efficiency[a], data.energy))
    total_energy    = idle_energy + workload_energy

    # Latency:  l_eff_i = l_i * (1 + gamma * U_cpu_j / C_j),
    #           L(X)    = sum_i omega(p_i) * l_eff_i
    load_ratio  = cpu_load[a] / data.server_cpu_cap[a]
    eff_latency = data.latency * (1.0 + weights.congestion_factor * load_ratio)

    # omega(p_i) is precomputed at load time; the fallback covers hand-built
    # test fixtures that do not set the field.
    p_weights = data.priority_weights
    if p_weights is None:
        p_idx     = np.clip(data.priority, 0, 2).astype(np.int32)
        p_weights = _PRIORITY_WEIGHTS[p_idx]

    total_latency = float(np.dot(p_weights, eff_latency))

    # Capacity violations, summed over servers
    cpu_violation = float(np.sum(np.maximum(0.0, cpu_load - data.server_cpu_cap)))
    mem_violation = float(np.sum(np.maximum(0.0, mem_load - data.server_mem_cap)))

    # Scalar objective.  With refs set, every term is divided by its reference
    # first, so the four terms are dimensionless and comparable.
    e_ref = weights.energy_ref or 1.0
    l_ref = weights.latency_ref or 1.0
    c_ref = weights.cpu_ref or 1.0
    m_ref = weights.mem_ref or 1.0

    objective_value = (
        weights.energy_weight  * total_energy   / e_ref
        + weights.latency_weight * total_latency  / l_ref
        + weights.cpu_penalty    * cpu_violation  / c_ref
        + weights.mem_penalty    * mem_violation  / m_ref
    )

    # A solution is feasible only when neither capacity is violated anywhere
    feasible = (cpu_violation == 0.0) and (mem_violation == 0.0)

    return ScheduleEvaluation(
        total_energy=total_energy,
        total_latency=total_latency,
        cpu_violation=cpu_violation,
        mem_violation=mem_violation,
        n_active_servers=int(np.sum(active)),
        objective_value=objective_value,
        feasible=feasible,
    )
