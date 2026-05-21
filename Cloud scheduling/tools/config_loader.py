"""
config_loader.py — Load and validate config.yaml into typed Python objects.

Reads the project-level config.yaml and converts each section into dataclasses
that the rest of the code can import directly, with IDE autocomplete and type
checking.  If config.yaml is missing the module falls back to built-in defaults
so the code still runs without a config file present.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from tools.objective import ObjectiveWeights


# ---------------------------------------------------------------------------
# Typed config dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ExperimentConfig:
    n_seeds: int
    n_tasks: int
    normalize_objective: bool
    normalize_method: str = "sample"        # 'sample' (Deb 2001) or 'worst_case'
    n_calibration_samples: int = 150        # used when normalize_method='sample'
    penalty_multiplier: float = 100.0       # Deb 2000 multiplier on F_max(feasible)
    calibration_seed: int = 0               # deterministic calibration sampling
    min_feasible_calibration: int = 10      # min feasibles required before computing means;
                                            # below this we fall back to worst-case norm


@dataclass
class AlgorithmConfig:
    sa: dict[str, Any]
    ga: dict[str, Any]
    umda: dict[str, Any]
    bb: dict[str, Any]


@dataclass
class SensitivityConfig:
    n_seeds: int
    sa: dict[str, Any]
    ga: dict[str, Any]
    umda: dict[str, Any]


@dataclass
class TuningConfig:
    """Grid-search tuning ranges (--tune flag)."""
    n_seeds: int
    reduced_budget: bool
    sa: dict[str, Any]
    ga: dict[str, Any]
    umda: dict[str, Any]


@dataclass
class HorizontalScalingConfig:
    task_sizes: list[int]
    server_ratio: int   # n_servers = max(4, n_tasks // server_ratio)
    n_seeds: int


@dataclass
class VerticalScalingConfig:
    n_tasks: int
    server_counts: list[int]
    n_seeds: int


@dataclass
class OptimalityGapConfig:
    n_tasks: int
    n_servers: int
    n_seeds: int


@dataclass
class ScalabilityConfig:
    horizontal: HorizontalScalingConfig
    vertical: VerticalScalingConfig
    optimality_gap: OptimalityGapConfig


@dataclass
class AppConfig:
    experiment: ExperimentConfig
    objective: dict[str, ObjectiveWeights]   # keyed by focus mode name
    algorithms: AlgorithmConfig
    sensitivity: SensitivityConfig
    tuning: TuningConfig
    scalability: ScalabilityConfig


# ---------------------------------------------------------------------------
# Defaults (used when config.yaml is absent)
# ---------------------------------------------------------------------------

_DEFAULT_EXPERIMENT = ExperimentConfig(
    n_seeds=10,
    n_tasks=50,
    normalize_objective=True,
    normalize_method="sample",
    n_calibration_samples=150,
    penalty_multiplier=100.0,
    calibration_seed=0,
    min_feasible_calibration=10,
)

_DEFAULT_OBJECTIVE: dict[str, ObjectiveWeights] = {
    "performance": ObjectiveWeights(
        energy_weight=0.2, latency_weight=1.0,
        cpu_penalty=10.0, mem_penalty=10.0, congestion_factor=1.5,
    ),
    "balanced": ObjectiveWeights(
        energy_weight=1.0, latency_weight=1.0,
        cpu_penalty=10.0, mem_penalty=10.0, congestion_factor=1.0,
    ),
    "eco": ObjectiveWeights(
        energy_weight=1.0, latency_weight=0.2,
        cpu_penalty=10.0, mem_penalty=10.0, congestion_factor=0.5,
    ),
}

_DEFAULT_ALGORITHMS = AlgorithmConfig(
    sa=dict(
        initial_temperature=None, cooling_rate=0.995, min_temperature=1e-8,
        iterations_per_temperature=50, max_temp_steps=3000,
        reheat_patience=300, reheat_factor=0.4,
    ),
    ga=dict(
        population_size=50, n_generations=3000, tournament_size=3,
        crossover_prob=0.8, mutation_prob=None, elitism_count=2,
    ),
    umda=dict(
        population_size=100, n_generations=1500,
        selection_ratio=0.5, smoothing=0.1, elitism_count=1,
    ),
    bb=dict(
        time_limit=60.0, max_nodes=500_000,
    ),
)

_DEFAULT_SENSITIVITY = SensitivityConfig(
    n_seeds=5,
    sa=dict(
        # Calibrated for the NORMALISED objective (F(X) ~ 1).  Earlier defaults
        # used raw-units values (500..20000) which are 4-5 orders of magnitude
        # too large once normalisation is enabled.  Keep these in lockstep with
        # config.yaml -> sensitivity.sa.temperatures.
        temperatures=[0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
        cooling_rates=[0.990, 0.992, 0.995, 0.997, 0.999],
    ),
    ga=dict(
        population_sizes=[20, 50, 100],
        crossover_probs=[0.6, 0.7, 0.8, 0.9, 1.0],
    ),
    umda=dict(
        population_sizes=[50, 100, 200],
        selection_ratios=[0.2, 0.3, 0.5, 0.7],
    ),
)

_DEFAULT_TUNING = TuningConfig(
    n_seeds=3,
    reduced_budget=True,
    sa=dict(
        cooling_rates=[0.990, 0.995, 0.999],
        iterations_per_temperature=[25, 50, 100],
    ),
    ga=dict(
        population_sizes=[25, 50, 100],
        crossover_probs=[0.6, 0.8, 0.95],
    ),
    umda=dict(
        population_sizes=[50, 100, 200],
        selection_ratios=[0.3, 0.5, 0.7],
    ),
)

_DEFAULT_SCALABILITY = ScalabilityConfig(
    horizontal=HorizontalScalingConfig(
        task_sizes=[20, 50, 100, 200, 500, 1000, 2000],
        server_ratio=5,
        n_seeds=3,
    ),
    vertical=VerticalScalingConfig(
        n_tasks=50,
        server_counts=[20, 15, 10, 8, 6],
        n_seeds=3,
    ),
    optimality_gap=OptimalityGapConfig(
        n_tasks=20,
        n_servers=4,
        n_seeds=5,
    ),
)

_DEFAULT_CONFIG = AppConfig(
    experiment=_DEFAULT_EXPERIMENT,
    objective=_DEFAULT_OBJECTIVE,
    algorithms=_DEFAULT_ALGORITHMS,
    sensitivity=_DEFAULT_SENSITIVITY,
    tuning=_DEFAULT_TUNING,
    scalability=_DEFAULT_SCALABILITY,
)


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def load_config(config_path: Path | None = None) -> AppConfig:
    """
    Load config.yaml and return a fully typed AppConfig.

    Falls back to built-in defaults if the file is not found, so the code
    works without a config file during development or quick tests.
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"

    if not config_path.exists():
        print(f"  [config] {config_path.name} not found — using built-in defaults.")
        return _DEFAULT_CONFIG

    with open(config_path, encoding="utf-8") as f:
        raw: dict = yaml.safe_load(f)

    # ---- experiment ----
    exp_raw = raw.get("experiment", {})
    experiment = ExperimentConfig(
        n_seeds=int(exp_raw.get("n_seeds", _DEFAULT_EXPERIMENT.n_seeds)),
        n_tasks=int(exp_raw.get("n_tasks", _DEFAULT_EXPERIMENT.n_tasks)),
        normalize_objective=bool(exp_raw.get(
            "normalize_objective", _DEFAULT_EXPERIMENT.normalize_objective
        )),
        normalize_method=str(exp_raw.get(
            "normalize_method", _DEFAULT_EXPERIMENT.normalize_method
        )),
        n_calibration_samples=int(exp_raw.get(
            "n_calibration_samples", _DEFAULT_EXPERIMENT.n_calibration_samples
        )),
        penalty_multiplier=float(exp_raw.get(
            "penalty_multiplier", _DEFAULT_EXPERIMENT.penalty_multiplier
        )),
        calibration_seed=int(exp_raw.get(
            "calibration_seed", _DEFAULT_EXPERIMENT.calibration_seed
        )),
        min_feasible_calibration=int(exp_raw.get(
            "min_feasible_calibration", _DEFAULT_EXPERIMENT.min_feasible_calibration
        )),
    )

    # ---- objective weights per mode ----
    obj_raw = raw.get("objective", {})
    objective: dict[str, ObjectiveWeights] = {}
    for mode, defaults in _DEFAULT_OBJECTIVE.items():
        section = obj_raw.get(mode, {})
        objective[mode] = ObjectiveWeights(
            energy_weight=float(section.get("energy_weight", defaults.energy_weight)),
            latency_weight=float(section.get("latency_weight", defaults.latency_weight)),
            cpu_penalty=float(section.get("cpu_penalty", defaults.cpu_penalty)),
            mem_penalty=float(section.get("mem_penalty", defaults.mem_penalty)),
            congestion_factor=float(section.get("congestion_factor", defaults.congestion_factor)),
        )

    # ---- algorithm hyperparameters ----
    algo_raw = raw.get("algorithms", {})

    def _merge(key: str, default: dict) -> dict:
        section = algo_raw.get(key, {})
        return {**default, **{k: v for k, v in section.items() if v is not None}}

    def _merge_with_none(key: str, default: dict) -> dict:
        """Like _merge but preserves explicit null values (e.g. mutation_prob)."""
        section = algo_raw.get(key, {})
        merged = dict(default)
        merged.update(section)
        return merged

    algorithms = AlgorithmConfig(
        # _merge_with_none for SA and GA so explicit null values (initial_temperature,
        # mutation_prob) are preserved and trigger auto-estimation in the algorithm.
        sa=_merge_with_none("sa",   _DEFAULT_ALGORITHMS.sa),
        ga=_merge_with_none("ga",   _DEFAULT_ALGORITHMS.ga),
        umda=_merge("umda",         _DEFAULT_ALGORITHMS.umda),
        bb=_merge("bb",             _DEFAULT_ALGORITHMS.bb),
    )

    # ---- sensitivity sweep values ----
    sens_raw = raw.get("sensitivity", {})
    sensitivity = SensitivityConfig(
        n_seeds=int(sens_raw.get("n_seeds", _DEFAULT_SENSITIVITY.n_seeds)),
        sa={**_DEFAULT_SENSITIVITY.sa, **sens_raw.get("sa", {})},
        ga={**_DEFAULT_SENSITIVITY.ga, **sens_raw.get("ga", {})},
        umda={**_DEFAULT_SENSITIVITY.umda, **sens_raw.get("umda", {})},
    )

    # ---- tuning grids (grid search) ----
    tune_raw = raw.get("tuning", {})
    tuning = TuningConfig(
        n_seeds=int(tune_raw.get("n_seeds", _DEFAULT_TUNING.n_seeds)),
        reduced_budget=bool(tune_raw.get("reduced_budget", _DEFAULT_TUNING.reduced_budget)),
        sa={**_DEFAULT_TUNING.sa, **tune_raw.get("sa", {})},
        ga={**_DEFAULT_TUNING.ga, **tune_raw.get("ga", {})},
        umda={**_DEFAULT_TUNING.umda, **tune_raw.get("umda", {})},
    )

    # ---- scalability axes ----
    scal_raw = raw.get("scalability", {})

    h_raw = scal_raw.get("horizontal", {})
    dh = _DEFAULT_SCALABILITY.horizontal
    horizontal = HorizontalScalingConfig(
        task_sizes=list(h_raw.get("task_sizes", dh.task_sizes)),
        server_ratio=int(h_raw.get("server_ratio", dh.server_ratio)),
        n_seeds=int(h_raw.get("n_seeds", dh.n_seeds)),
    )

    v_raw = scal_raw.get("vertical", {})
    dv = _DEFAULT_SCALABILITY.vertical
    vertical = VerticalScalingConfig(
        n_tasks=int(v_raw.get("n_tasks", dv.n_tasks)),
        server_counts=list(v_raw.get("server_counts", dv.server_counts)),
        n_seeds=int(v_raw.get("n_seeds", dv.n_seeds)),
    )

    # Accept legacy key `lower_bound` as a fallback so existing config.yaml files
    # with the old name still load.  Prefer the new `optimality_gap` key.
    og_raw = scal_raw.get("optimality_gap", scal_raw.get("lower_bound", {}))
    dog = _DEFAULT_SCALABILITY.optimality_gap
    optimality_gap = OptimalityGapConfig(
        n_tasks=int(og_raw.get("n_tasks", dog.n_tasks)),
        n_servers=int(og_raw.get("n_servers", dog.n_servers)),
        n_seeds=int(og_raw.get("n_seeds", dog.n_seeds)),
    )

    scalability = ScalabilityConfig(
        horizontal=horizontal,
        vertical=vertical,
        optimality_gap=optimality_gap,
    )

    return AppConfig(
        experiment=experiment,
        objective=objective,
        algorithms=algorithms,
        sensitivity=sensitivity,
        tuning=tuning,
        scalability=scalability,
    )
