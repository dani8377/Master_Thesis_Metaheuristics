"""
Run script — replaces Makefile for systems without make.

Usage (from the project root):
    uv run run.py           # both problems
    uv run run.py ev        # EV routing only
    uv run run.py cloud     # cloud scheduling only
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
UV   = [r"C:\Users\chris\.local\bin\uv.exe",
        "run", "--with", "numpy", "--with", "pandas", "--with", "matplotlib", "python"]


def run(name: str, directory: str) -> None:
    print(f"\n{'='*60}")
    print(f"  Running: {name}")
    print(f"{'='*60}\n")
    subprocess.run(UV + ["main.py"], cwd=ROOT / directory, check=True)


targets = sys.argv[1:] or ["ev", "cloud"]

for target in targets:
    if target == "ev":
        run("EV Routing", "EV_routing")
    elif target == "cloud":
        run("Cloud Scheduling", "Cloud scheduling")
    else:
        print(f"Unknown target '{target}'. Use: ev  cloud")
        sys.exit(1)
