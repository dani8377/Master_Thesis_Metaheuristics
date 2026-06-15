"""
Simulated Annealing (SA) for the cloud task scheduling problem.

Metropolis acceptance criterion with geometric cooling and adaptive reheating.
Initial temperature is estimated automatically from the problem instance so the
schedule is correctly calibrated regardless of objective function scale.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from tools.data_loader import SchedulingProblemData
from tools.objective import evaluate_schedule, ObjectiveWeights, ScheduleEvaluation
from tools.neighborhoods import generate_neighbor
from tools.initial_solution import build_greedy_assignment
from tools.feasibility import is_valid_assignment


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

@dataclass
class SAStatistics:
    """Per-run diagnostics: convergence histories and acceptance counters.

    Budget accounting:
      * total_evaluated         — main-loop evaluate_schedule() calls; this is
                                   the denominator of acceptance_rate.
      * t0_probe_evaluations    — calls consumed by the auto-T_0 probe (held
                                   separately so they do not deflate the
                                   acceptance-rate metric).
      * total_budget_consumed   — sum of the two; this is what should be
                                   compared against GA / UMDA budgets for a
                                   fair equal-budget comparison.
    """

    best_cost_history: list[float]    = field(default_factory=list)
    current_cost_history: list[float] = field(default_factory=list)
    temperature_history: list[float]  = field(default_factory=list)

    total_evaluated: int            = 0
    total_improving_accepted: int   = 0
    total_worsening_accepted: int   = 0
    total_rejected_structural: int  = 0
    total_feasible_evaluated: int   = 0
    t0_probe_evaluations: int       = 0   # evaluate_schedule() calls in auto-T_0 probe

    reheat_count: int        = 0
    final_temperature: float = 0.0

    @property
    def total_budget_consumed(self) -> int:
        """Combined evaluation count (main loop + T_0 probe) for budget comparisons."""
        return self.total_evaluated + self.t0_probe_evaluations

    @property
    def acceptance_rate(self) -> float:
        if self.total_evaluated == 0:
            return 0.0
        return (self.total_improving_accepted + self.total_worsening_accepted) / self.total_evaluated

    @property
    def feasibility_rate(self) -> float:
        if self.total_evaluated == 0:
            return 0.0
        return self.total_feasible_evaluated / self.total_evaluated


# ---------------------------------------------------------------------------
# Temperature auto-estimation
# ---------------------------------------------------------------------------

def estimate_initial_temperature(
    data: SchedulingProblemData,
    weights: ObjectiveWeights,
    target_acceptance: float = 0.80,
    n_samples: int = 400,
    verbose: bool = False,
) -> tuple[float, int]:
    """
    Estimate T_0 so that `target_acceptance` fraction of random worsening moves
    are accepted at the start of the search.

    Method: sample n_samples random neighbour moves from the greedy solution,
    collect the positive deltas (worsening), then solve
        exp(-mean_delta / T_0) = target_acceptance  =>  T_0 = -mean_delta / ln(p).

    Returns
    -------
    T_0 : float
        Calibrated starting temperature.
    n_evaluated : int
        Number of evaluate_schedule() calls consumed by the probe (to be added
        to the algorithm's total budget counter so SA, GA, UMDA budgets remain
        directly comparable).

    Feasibility filter (theoretical motivation):
    --------------------------------------------
    Worsening moves that involve the infeasible region produce huge deltas
    dominated by the lambda*violation penalty term, not the objective gradient
    we actually want to calibrate against.  Two failure modes if we include
    those deltas:

      (a) feasibility-changing moves (feasible -> infeasible, or vice-versa)
          jump the full lambda*violation step and skew mean_delta upward.
      (b) infeasible -> infeasible moves are STILL dominated by penalty-term
          changes because lambda is ~100x F_max_feasible; their mean delta is
          one to two orders of magnitude larger than the feasible-to-feasible
          objective-gradient deltas that matter for SA's actual search.

    The previous version filtered to "feasibility-preserving" (current and
    candidate share feasibility status), accepting (b).  Combined with the 15%
    walk-forward (which drifts the probe into the infeasible region — empirically
    ~68% of probe steps end up infeasible even when starting from feasible
    greedy), this inflated mean_delta by ~20-30x and produced T_0 values that
    caused SA to random-walk away from the strong greedy starting basin instead
    of exploiting it.

    We therefore restrict the calibration sample to **feasible -> feasible**
    worsening moves and prevent the walk-forward from drifting into the
    infeasible region once the probe has reached a feasible state.

    If too few feasible-to-feasible worsening deltas are found (e.g. when
    greedy itself is infeasible at extreme constraint tightness), fall back
    progressively: same-feasibility-class deltas, then all worsening deltas,
    then T_0 = 1.0.
    """
    assignment       = build_greedy_assignment(data)
    current_eval     = evaluate_schedule(assignment, data, weights)
    current_cost     = current_eval.objective_value
    current_feasible = current_eval.feasible
    n_evaluated      = 1  # the greedy evaluation above

    deltas_feas: list[float]      = []   # feasible -> feasible (preferred)
    deltas_same_class: list[float] = []  # same feasibility class (fallback 1)
    deltas_all: list[float]       = []   # all worsening (fallback 2)
    for _ in range(n_samples):
        candidate = generate_neighbor(assignment, data)
        if not is_valid_assignment(candidate, data):
            continue
        candidate_eval = evaluate_schedule(candidate, data, weights)
        n_evaluated   += 1
        candidate_cost = candidate_eval.objective_value
        delta = candidate_cost - current_cost
        if delta > 0:
            deltas_all.append(delta)
            if candidate_eval.feasible == current_feasible:
                deltas_same_class.append(delta)
                if current_feasible and candidate_eval.feasible:
                    deltas_feas.append(delta)
        # Walk forward to sample diverse parts of the landscape, but once we
        # are in the feasible region stay there — drifting into infeasibility
        # would let penalty-term magnitudes dominate the calibration sample.
        if random.random() < 0.15 and (not current_feasible or candidate_eval.feasible):
            assignment       = candidate
            current_cost     = candidate_cost
            current_feasible = candidate_eval.feasible

    if len(deltas_feas) >= 10:
        deltas = deltas_feas
        if verbose:
            print(f"  [SA] T_0 calibration: {len(deltas)} feasible-to-feasible"
                  f" worsening deltas (of {len(deltas_all)} total worsening)")
    elif len(deltas_same_class) >= 10:
        deltas = deltas_same_class
        print(
            "  [SA] T_0 calibration NOTE: only "
            f"{len(deltas_feas)} feasible-to-feasible worsening deltas found"
            f" (< 10 threshold); falling back to {len(deltas_same_class)}"
            " same-feasibility-class deltas. Greedy may be infeasible —"
            " expect T_0 calibrated against penalty-dominated deltas."
        )
    elif deltas_all:
        deltas = deltas_all
        print(
            "  [SA] T_0 calibration WARNING: only "
            f"{len(deltas_feas)} feasible-to-feasible and"
            f" {len(deltas_same_class)} same-feasibility-class worsening deltas"
            f" found; falling back to all {len(deltas_all)} worsening deltas."
            " T_0 may be inflated by penalty-term magnitudes."
        )
    else:
        print(
            "  " + "!" * 70 + "\n"
            "  [SA] T_0 calibration FALLBACK: no worsening moves observed in "
            f"{n_samples} probes.\n"
            "    Falling back to T_0 = 1.0 (safe default for normalised F).\n"
            "    This indicates an extremely flat or degenerate landscape;\n"
            "    SA may behave like pure hill-climbing.\n"
            "  " + "!" * 70
        )
        return 1.0, n_evaluated

    mean_delta = sum(deltas) / len(deltas)
    return -mean_delta / math.log(target_acceptance), n_evaluated  # log(p<1) < 0 -> result > 0


# ---------------------------------------------------------------------------
# SA implementation
# ---------------------------------------------------------------------------

def simulated_annealing(
    data: SchedulingProblemData,
    weights: ObjectiveWeights,
    initial_temperature: float | None = None,  # None -> auto-estimate
    cooling_rate: float = 0.995,
    min_temperature: float = 1e-8,
    iterations_per_temperature: int = 50,
    max_temp_steps: int = 3000,
    reheat_patience: int = 300,
    reheat_factor: float = 0.4,
    verbose: bool = False,
) -> tuple[list[int], ScheduleEvaluation, SAStatistics]:
    """
    Run Simulated Annealing for cloud resource allocation.

    When initial_temperature is None (or 0), it is estimated automatically
    so that ~80% of random worsening moves are accepted at step 0.  This
    keeps the annealing schedule correctly calibrated after objective normalisation.

    Returns (best_assignment, best_evaluation, diagnostics).
    """
    stats = SAStatistics()

    # ---- Temperature initialisation ----
    if initial_temperature is None or initial_temperature <= 0.0:
        initial_temperature, t0_probes = estimate_initial_temperature(
            data, weights, verbose=verbose,
        )
        # Held in a separate counter so it does not deflate acceptance_rate;
        # surfaced via stats.total_budget_consumed for budget-comparison plots.
        stats.t0_probe_evaluations = t0_probes
        if verbose:
            print(f"  [SA] Auto T_0 = {initial_temperature:.6f}"
                  f"  ({t0_probes} probe evaluations consumed)")

    # ---- Solution initialisation ----
    current_solution = build_greedy_assignment(data)
    current_eval     = evaluate_schedule(current_solution, data, weights)
    current_cost     = current_eval.objective_value

    best_solution = current_solution[:]
    best_eval     = current_eval
    best_cost     = current_cost

    temperature               = initial_temperature
    steps_without_improvement = 0

    verbose_interval = max(1, max_temp_steps // 10)
    _window_evals    = 0
    _window_accepts  = 0

    # ---- Main loop ----
    # min_temperature is a FLOOR, not a stopping criterion: the schedule never
    # drops below it, but the search always runs all max_temp_steps so SA
    # consumes its full evaluation budget (iterations_per_temperature x
    # max_temp_steps), matching GA/UMDA and the EV module's SA.  Near the
    # floor, acceptance of worsening moves is effectively zero, so the tail
    # behaves as hill-climbing until a reheat fires.
    for step_num in range(max_temp_steps):
        step_improved = False

        for _ in range(iterations_per_temperature):
            candidate = generate_neighbor(current_solution, data)

            if not is_valid_assignment(candidate, data):
                stats.total_rejected_structural += 1
                continue

            candidate_eval = evaluate_schedule(candidate, data, weights)
            candidate_cost = candidate_eval.objective_value
            stats.total_evaluated += 1
            _window_evals += 1
            if candidate_eval.feasible:
                stats.total_feasible_evaluated += 1

            delta = candidate_cost - current_cost

            if delta < 0:
                current_solution = candidate
                current_eval     = candidate_eval
                current_cost     = candidate_cost
                stats.total_improving_accepted += 1
                _window_accepts += 1
            elif random.random() < math.exp(-delta / temperature):
                # Metropolis: accept worsening move with probability exp(-delta/T)
                current_solution = candidate
                current_eval     = candidate_eval
                current_cost     = candidate_cost
                stats.total_worsening_accepted += 1
                _window_accepts += 1

            if current_cost < best_cost:
                best_solution = current_solution[:]
                best_eval     = current_eval
                best_cost     = current_cost
                step_improved = True

        # ---- Cooling (floored at min_temperature) ----
        temperature = max(temperature * cooling_rate, min_temperature)
        stats.best_cost_history.append(best_cost)
        stats.current_cost_history.append(current_cost)
        stats.temperature_history.append(temperature)

        # ---- Reheat if stuck ----
        if step_improved:
            steps_without_improvement = 0
        else:
            steps_without_improvement += 1

        if steps_without_improvement >= reheat_patience:
            temperature               = reheat_factor * initial_temperature
            steps_without_improvement = 0
            stats.reheat_count       += 1

        # ---- Verbose progress ----
        if verbose and (step_num + 1) % verbose_interval == 0:
            t_frac      = temperature / initial_temperature
            window_rate = _window_accepts / max(1, _window_evals)
            _window_evals = _window_accepts = 0
            phase = (
                "exploring  (high T)"   if t_frac > 0.30 else
                "transitioning"          if t_frac > 0.05 else
                "exploiting (low T)"
            )
            print(
                f"  [SA] step {step_num+1:>4}/{max_temp_steps}"
                f"  T={temperature:.4f}"
                f"  best={best_cost:.4f}"
                f"  accept={window_rate:.1%}"
                f"  reheats={stats.reheat_count}"
                f"  [{phase}]"
            )

    stats.final_temperature = temperature
    return best_solution, best_eval, stats
