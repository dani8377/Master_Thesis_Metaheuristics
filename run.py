"""
Run script — replaces Makefile for systems without make.

Usage (from the project root):
    uv run run.py                       # both problems, default settings
    uv run run.py ev                    # EV routing only
    uv run run.py cloud                 # cloud scheduling, all algorithms, balanced

Cloud scheduling options (passed after 'cloud'):
    uv run run.py cloud --algorithms SA GA UMDA   # metaheuristics only
    uv run run.py cloud --focus eco --verbose     # eco mode with verbose output
    uv run run.py cloud --algorithms SA --seeds 3 # quick single-algorithm test
    uv run run.py cloud --focus performance       # latency-focused weights

For all cloud CLI options:
    uv run run.py cloud --help
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
UV   = [r"C:\Users\chris\.local\bin\uv.exe",
        "run", "--with", "numpy", "--with", "pandas", "--with", "matplotlib",
        "--with", "pyyaml", "--with", "scipy", "python"]


def run(name: str, directory: str, extra_args: list[str] | None = None) -> None:
    print(f"\n{'='*60}")
    print(f"  Running: {name}")
    print(f"{'='*60}\n")
    cmd = UV + ["main.py"] + (extra_args or [])
    subprocess.run(cmd, cwd=ROOT / directory, check=True)


# Separate problem targets (ev / cloud) from extra flags (--algorithms, etc.)
_args    = sys.argv[1:]
targets  = [a for a in _args if a in ("ev", "cloud")]
extras   = [a for a in _args if a not in ("ev", "cloud")]

# Default: run both problems if no target given
if not targets:
    targets = ["ev", "cloud"]

for target in targets:
    if target == "ev":
        run("EV Routing", "EV_routing")          # EV has no extra CLI options
    elif target == "cloud":
        run("Cloud Scheduling", "Cloud scheduling", extras)
    else:
        print(f"Unknown target '{target}'. Use: ev  cloud")
        sys.exit(1)
