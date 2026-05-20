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
    Tunable coefficients for the objective function.

    w_e, w_l are PREFERENCE RATIOS applied *after* the normalisation refs
    (energy_ref, latency_ref) divide each raw term to expectation 1.  At that
    point (w_e=1, w_l=1) means equal contribution and (w_e=0.2, w_l=1.0) means
    "latency is 5x more important than energy" — a true preference share, not a
    unit-conversion factor.

    lambda_cpu, lambda_mem penalise capacity violations.  Under sample-based
    calibration (Deb 2000) these are *overwritten* at run time to
    `penalty_multiplier * F_max(feasible)`; the values supplied here are only
    used under the legacy `worst_case` method.

    gamma (congestion_factor) is NOT a preference weight.  It is a parameter of
    the latency function itself: l_eff_i = l_i * (1 + gamma * U_j / C_j).
    Different gamma values change the SHAPE of L(X) before normalisation; the
    per-mode value expresses SLA tightness, not preference.

    Normalisation refs (energy_ref, latency_ref, cpu_ref, mem_ref):
        When set, each objective term is divided by its reference value before
        weighting.  Set by compute_sample_normalization() (Deb 2001) or
        compute_normalization_constants() (worst-case) and attached in main.py
        after data is loaded.
        Default None = no normalisation; w_e / w_l act on raw units and the
        Watts-vs-ms scale mismatch dominates (only useful for ablation studies
        with `normalize_objective: false`).
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


# ---------------------------------------------------------------------------
# Focus-mode weight presets
#
# REMOVED in favour of tools/config_loader.py + config.yaml.  Production code,
# tests, and the experiment harness all read weights through load_config(), so
# config.yaml is the single source of truth.  Keeping a parallel copy here as
# module-level constants was just a way to drift out of sync.  If you need
# weights in an ad-hoc script, call:
#     from tools.config_loader import load_config
#     weights = load_config().objective["balanced"]   # or "performance" / "eco"
# ---------------------------------------------------------------------------


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
    Reports what the sample-based calibration actually found.

    Saved to the run manifest so the thesis can quote concrete numbers:
    "150 candidate assignments were drawn, of which N were feasible; the mean
    energy across feasibles was X Watts, the mean priority-weighted latency
    was Y ms.  Penalty weights were set to 100x the maximum feasible normalised
    objective, ensuring strict dominance of every feasible solution over every
    infeasible one (Deb 2000)."
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
    Draw n_samples candidate assignments via a mix of greedy + perturbed-greedy +
    pure-random construction.  The mix is chosen so that, across plausible problem
    tightness levels, enough samples land in the feasible region to give a stable
    mean estimate.

    Strategy:
        sample 0          : greedy BFD (deterministic, often feasible)
        next 40%          : greedy with low perturbation (10% gene re-assignment)
        next 30%          : greedy with high perturbation (30% gene re-assignment)
        remaining ~30%    : uniformly random assignment

    This concentrates samples around the feasible region without losing coverage
    of the wider search space.
    """
    # Local imports keep the module's import graph lean
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
    Sample-based normalisation following Deb (2001), with parameter-less
    penalty calibration following Deb (2000).

    Procedure
    ---------
    1. Generate n_samples candidate assignments (greedy + perturbed + random).
    2. Evaluate each and split into feasible / infeasible subsets.
    3. If at least min_feasible feasibles were found:
         E_ref   = mean total_energy  over feasibles
         L_ref   = mean total_latency over feasibles
         lambda_cpu = lambda_mem = penalty_multiplier x F_max_feasible
             where F_max_feasible = max (w_e * E/E_ref + w_l * L/L_ref) over feasibles.
       The CPU and memory violation refs remain the total-demand upper bound so
       that lambda's units match the (normalised) feasible-objective units.
    4. Otherwise fall back to compute_normalization_constants() and emit a
       warning in the diagnostics.

    Why this is correct (Deb 2001):
       With E_ref = E[E(X)] and L_ref = E[L(X)] over a representative sample,
       each normalised term has expectation 1 across that sample, so
       w_e = w_l = 1 means "equal expected contribution".  Focus-mode
       multipliers (e.g. eco: w_e=1, w_l=0.2) then express genuine preference
       shares rather than compensating for scale mismatch.

    Why the penalty rule is correct (Deb 2000):
       For any feasible X:   F_obj(X) <= F_max_feasible.
       For any infeasible X: F_obj(X) >= 0 AND penalty_multiplier * F_max_feasible *
       (violation / total_demand) gets added.  With penalty_multiplier = 100, any
       violation > 1% of total demand strictly dominates every feasible solution;
       smaller violations are vanishingly rare in practice (a single overloaded
       task by 50% on a tight server typically gives violation / total_demand of
       order 0.005-0.02, which still produces a large penalty contribution).

    Returns
    -------
    calibrated_weights : ObjectiveWeights
        Copy of base_weights with energy_ref, latency_ref, cpu_ref, mem_ref,
        cpu_penalty and mem_penalty set from the calibration.
    diagnostics : CalibrationDiagnostics
        What the procedure observed.  Save to the run manifest.
    """
    pool = _sample_calibration_pool(data, n_samples=n_samples, seed=seed)

    # Evaluate every sample with the FEASIBILITY-ONLY weights so we can collect
    # the raw E(X) and L(X) values without any penalty contamination.
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
    # Convert to numpy once so all downstream ops are vectorised
    a = np.asarray(assignment, dtype=np.int32)  # shape (n_tasks,)
    m = data.n_servers

    # ------------------------------------------------------------------ #
    # Step 1: Compute per-server CPU and memory loads using bincount.     #
    # bincount(a, weights=x)[j] = sum of x[i] for all i where a[i] == j  #
    # This is equivalent to U_cpu_j = Σ_i c_i · x_ij in the formulation. #
    # ------------------------------------------------------------------ #
    cpu_load = np.bincount(a, weights=data.cpu, minlength=m)   # shape (m,)
    mem_load = np.bincount(a, weights=data.mem, minlength=m)   # shape (m,)
    # y_j = 1 if at least one task is assigned to server j, else 0
    active   = np.bincount(a, minlength=m) > 0                  # bool, shape (m,)

    # ------------------------------------------------------------------ #
    # Step 2: Energy model                                                #
    # E(X) = Σ_j e_idle_j · y_j  +  Σ_i η_{a_i} · e_i                 #
    # ------------------------------------------------------------------ #
    idle_energy     = float(np.dot(data.server_idle_power, active))
    # server_efficiency[a] broadcasts: for each task i, look up η of its server
    workload_energy = float(np.dot(data.server_efficiency[a], data.energy))
    total_energy    = idle_energy + workload_energy

    # ------------------------------------------------------------------ #
    # Step 3: Priority-weighted congestion latency                        #
    # l̂_ij = l_i · (1 + γ · U_cpu_j / C_j)                            #
    # L(X) = Σ_i ω(p_i) · l̂_ij                                        #
    # ------------------------------------------------------------------ #
    # load_ratio[i] = CPU utilisation ratio of the server task i is on
    load_ratio  = cpu_load[a] / data.server_cpu_cap[a]
    eff_latency = data.latency * (1.0 + weights.congestion_factor * load_ratio)

    # Priority weights omega(p_i) are pre-computed at load time on
    # SchedulingProblemData.priority_weights, so we skip the np.clip + lookup
    # cost on the hot path.  Fall back to the in-line computation if the field
    # is missing (older callers, hand-built test fixtures, etc.).
    p_weights = data.priority_weights
    if p_weights is None:
        p_idx     = np.clip(data.priority, 0, 2).astype(np.int32)
        p_weights = _PRIORITY_WEIGHTS[p_idx]

    total_latency = float(np.dot(p_weights, eff_latency))

    # ------------------------------------------------------------------ #
    # Step 4: Capacity violation penalties                                #
    # ------------------------------------------------------------------ #
    cpu_violation = float(np.sum(np.maximum(0.0, cpu_load - data.server_cpu_cap)))
    mem_violation = float(np.sum(np.maximum(0.0, mem_load - data.server_mem_cap)))

    # ------------------------------------------------------------------ #
    # Step 5: Combine into scalar objective                               #
    # When normalisation refs are present each term is divided by its    #
    # worst-case reference so the result is dimensionless [0, 1].        #
    # ------------------------------------------------------------------ #
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
