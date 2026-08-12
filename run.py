"""
Run script, replacing the Makefile for systems without make.

Master's thesis "Evaluation of Metaheuristic Algorithms for Energy Optimisation
in Scheduling and Routing".
Christian Wu (s194597) and Daniel Diamant (s205336)
Supervisor: Professor Carsten Witt, DTU Compute
Technical University of Denmark, August 2026

Usage (from the project root):
    uv run run.py                       # both problems, default settings
    uv run run.py ev                    # EV routing only
    uv run run.py cloud                 # cloud scheduling, all algorithms, balanced

Cloud_scheduling options (passed after 'cloud'):
    uv run run.py cloud --algorithms SA GA UMDA   # metaheuristics only
    uv run run.py cloud --focus eco --verbose     # eco mode with verbose output
    uv run run.py cloud --algorithms SA --seeds 3 # quick single-algorithm test
    uv run run.py cloud --focus performance       # latency-focused weights

EV_routing options are passed the same way, after 'ev'.

For the full option list of either problem:
    uv run run.py cloud --help
    uv run run.py ev --help
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
_UV_BIN = shutil.which("uv")
if _UV_BIN is None:
    sys.exit("uv not found on PATH. Install it from https://docs.astral.sh/uv/ "
             "or run main.py directly with a Python that has the dependencies installed.")
UV   = [_UV_BIN,
        "run", "--with", "numpy", "--with", "pandas", "--with", "matplotlib",
        "--with", "pyyaml", "--with", "scipy", "python"]


def run(name: str, directory: str, extra_args: list[str] | None = None,
        from_root: bool = False) -> None:
    print(f"\n{'='*60}")
    print(f"  Running: {name}")
    print(f"{'='*60}\n")
    if from_root:
        # EV_routing/main.py resolves data paths relative to the project root
        # and imports its own tools/ package via PYTHONPATH.
        env = {**os.environ, "PYTHONPATH": str(ROOT / directory)}
        cmd = UV + [f"{directory}/main.py"] + (extra_args or [])
        subprocess.run(cmd, cwd=ROOT, env=env, check=True)
    else:
        cmd = UV + ["main.py"] + (extra_args or [])
        subprocess.run(cmd, cwd=ROOT / directory, check=True)


# Separate problem targets (ev / cloud) from extra flags (--algorithms, etc.)
_args    = sys.argv[1:]
targets  = [a for a in _args if a in ("ev", "cloud")]
extras   = [a for a in _args if a not in ("ev", "cloud")]

# Print usage rather than falling through to the "run both" default below.
# Without this guard, `run.py --help` (or any mistyped target) starts a
# multi-hour run of both problems and overwrites the committed results.
if extras and not targets:
    print(__doc__)
    sys.exit(0 if extras[0] in ("-h", "--help") else 1)

# Default: run both problems if no target given
if not targets:
    targets = ["ev", "cloud"]

for target in targets:
    if target == "ev":
        run("EV Routing", "EV_routing", extras, from_root=True)
    elif target == "cloud":
        run("Cloud Scheduling", "Cloud_scheduling", extras)
