"""
fetch_elevation_and_roads.py
────────────────────────────
One-time data-fetching script. Run from the project root:

    python EV_routing/scripts/fetch_elevation_and_roads.py

Generates two files:
    EV_routing/datasets/sf_node_elevations.csv
    EV_routing/datasets/sf_energy_matrix.csv

Requirements:
    pip install srtm.py requests
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

# Allow imports from the EV_routing package
sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools.energy_model import build_energy_matrix

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATASET_DIR  = Path("EV_routing/datasets")
HAVERSINE_CSV = DATASET_DIR / "sf_distance_matrix_haversine.csv"
ALL_NODES_CSV = DATASET_DIR / "sf_all_nodes.csv"

OUTPUT_ELEVATIONS  = DATASET_DIR / "sf_node_elevations.csv"
OUTPUT_ENERGY      = DATASET_DIR / "sf_energy_matrix.csv"

# Energy model parameters (must match what you put in EVParameters)
BASE_CONSUMPTION = 0.50   # kWh/km at reference speed on flat road
GRADE_FACTOR     = 3.0    # 10% slope → ±30% energy
SPEED_REF_KMH    = 50.0   # reference speed for speed_multiplier baseline
SPEED_EXPONENT   = 2.0    # aerodynamic drag exponent

# OSRM public server
OSRM_BASE = "http://router.project-osrm.org/table/v1/driving"
OSRM_CHUNK_SIZE = 40      # nodes per group; each URL has 2×40=80 coords max
OSRM_RETRY_MAX  = 3
OSRM_SLEEP_S    = 0.6     # pause between requests to be polite

# Sentinel values for unreachable OSRM pairs
SENTINEL_DIST_M = 999_000.0
SENTINEL_DUR_S  = 99_999.0


# ---------------------------------------------------------------------------
# Step 1: Load node list (same order as dist_array)
# ---------------------------------------------------------------------------

def load_nodes() -> pd.DataFrame:
    dist_df = pd.read_csv(HAVERSINE_CSV, index_col=0)
    node_ids = list(dist_df.index.map(str))

    nodes_df = pd.read_csv(ALL_NODES_CSV)
    nodes_df["Node ID"] = nodes_df["Node ID"].astype(str)
    nodes_df = nodes_df.set_index("Node ID")

    records = []
    for nid in node_ids:
        row = nodes_df.loc[nid]
        records.append({"Node ID": nid, "Latitude": row["Latitude"], "Longitude": row["Longitude"]})

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Step 2: Fetch SRTM elevations
# ---------------------------------------------------------------------------

def fetch_elevations(nodes_df: pd.DataFrame) -> dict[str, float]:
    try:
        import srtm
    except ImportError:
        print("ERROR: srtm.py not installed. Run: pip install srtm.py")
        sys.exit(1)

    print("Fetching SRTM elevations...")
    elevation_data = srtm.get_data()
    elevations: dict[str, float] = {}

    for _, row in nodes_df.iterrows():
        nid = str(row["Node ID"])
        elev = elevation_data.get_elevation(float(row["Latitude"]), float(row["Longitude"]))
        elevations[nid] = float(elev) if elev is not None else 0.0

    elev_values = list(elevations.values())
    print(f"  Elevation range: {min(elev_values):.1f}m – {max(elev_values):.1f}m")
    return elevations


# ---------------------------------------------------------------------------
# Step 3: Fetch OSRM road matrix
# ---------------------------------------------------------------------------

def _osrm_block(
    src_indices: list[int],
    dst_indices: list[int],
    all_coords: list[tuple[float, float]],
) -> tuple[np.ndarray, np.ndarray]:
    """
    Fetch one block of the road matrix from OSRM.

    Sends only the union of src and dst node coordinates in the URL
    (never more than OSRM_CHUNK_SIZE*2 total), and uses sources/destinations
    index params to select the appropriate rows/cols.

    Returns (dist_m, dur_s) shaped (len(src), len(dst)).
    """
    # Build a combined list: src nodes first, then dst nodes (no duplicates in global indices)
    combined_indices = src_indices + dst_indices
    coord_str = ";".join(f"{all_coords[i][0]},{all_coords[i][1]}" for i in combined_indices)

    n_src = len(src_indices)
    n_dst = len(dst_indices)

    # sources = positions 0..n_src-1  in combined list
    # destinations = positions n_src..n_src+n_dst-1
    sources_str      = ";".join(str(i) for i in range(n_src))
    destinations_str = ";".join(str(n_src + j) for j in range(n_dst))

    url = (
        f"{OSRM_BASE}/{coord_str}"
        f"?annotations=duration,distance"
        f"&sources={sources_str}"
        f"&destinations={destinations_str}"
    )

    dist_block = np.full((n_src, n_dst), SENTINEL_DIST_M)
    dur_block  = np.full((n_src, n_dst), SENTINEL_DUR_S)

    for attempt in range(1, OSRM_RETRY_MAX + 1):
        try:
            resp = requests.get(url, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            break
        except Exception as exc:
            if attempt == OSRM_RETRY_MAX:
                raise RuntimeError(f"OSRM block request failed: {exc}") from exc
            wait = 2 ** attempt
            print(f"    Retry {attempt}/{OSRM_RETRY_MAX} after {wait}s ({exc})")
            time.sleep(wait)

    raw_dists = data.get("distances", [])
    raw_durs  = data.get("durations",  [])

    for i in range(n_src):
        for j in range(n_dst):
            d = raw_dists[i][j] if raw_dists and raw_dists[i][j] is not None else None
            t = raw_durs[i][j]  if raw_durs  and raw_durs[i][j]  is not None else None
            if d is not None:
                dist_block[i, j] = float(d)
            if t is not None:
                dur_block[i, j] = float(t)

    return dist_block, dur_block


def fetch_osrm_matrix(nodes_df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """
    Fetch full NxN road distance (m) and duration (s) matrices from OSRM.

    The public OSRM server limits requests to ~100 coordinates. We split the
    N nodes into groups of OSRM_CHUNK_SIZE and issue one request per
    (src_group, dst_group) pair, each URL containing at most 2×OSRM_CHUNK_SIZE
    coordinates.
    """
    n = len(nodes_df)
    coords = [(float(row["Longitude"]), float(row["Latitude"])) for _, row in nodes_df.iterrows()]

    print(f"Fetching OSRM road matrix for {n} nodes (block strategy, chunk_size={OSRM_CHUNK_SIZE})...")

    dist_m = np.full((n, n), SENTINEL_DIST_M)
    dur_s  = np.full((n, n), SENTINEL_DUR_S)
    np.fill_diagonal(dist_m, 0.0)
    np.fill_diagonal(dur_s,  0.0)

    # Build groups of indices
    groups: list[list[int]] = []
    for start in range(0, n, OSRM_CHUNK_SIZE):
        groups.append(list(range(start, min(start + OSRM_CHUNK_SIZE, n))))

    total_blocks = len(groups) ** 2
    block_num = 0

    for gi, src_group in enumerate(groups):
        for gj, dst_group in enumerate(groups):
            block_num += 1
            print(f"  Block {block_num}/{total_blocks}: "
                  f"rows {src_group[0]}–{src_group[-1]} × "
                  f"cols {dst_group[0]}–{dst_group[-1]} "
                  f"({len(src_group)+len(dst_group)} coords in URL)...")

            dist_block, dur_block = _osrm_block(src_group, dst_group, coords)

            for li, gi_idx in enumerate(src_group):
                for lj, gj_idx in enumerate(dst_group):
                    if gi_idx == gj_idx:
                        dist_m[gi_idx, gj_idx] = 0.0
                        dur_s[gi_idx, gj_idx]  = 0.0
                    else:
                        dist_m[gi_idx, gj_idx] = dist_block[li, lj]
                        dur_s[gi_idx, gj_idx]  = dur_block[li, lj]

            if block_num < total_blocks:
                time.sleep(OSRM_SLEEP_S)

    valid = dist_m[(dist_m > 0) & (dist_m < SENTINEL_DIST_M)]
    if len(valid) > 0:
        print(f"  Mean road distance (reachable arcs): {valid.mean() / 1000.0:.2f} km")
    return dist_m, dur_s


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if OUTPUT_ELEVATIONS.exists() and OUTPUT_ENERGY.exists():
        print("Both output files already exist:")
        print(f"  {OUTPUT_ELEVATIONS}")
        print(f"  {OUTPUT_ENERGY}")
        print("Delete them and re-run to regenerate.")
        return

    nodes_df = load_nodes()
    node_ids = nodes_df["Node ID"].tolist()
    n = len(node_ids)
    print(f"Loaded {n} nodes.")

    # --- Elevations ---
    elevations = fetch_elevations(nodes_df)
    elev_df = pd.DataFrame([
        {"Node ID": nid, "Elevation_m": elevations[nid]}
        for nid in node_ids
    ])
    elev_df.to_csv(OUTPUT_ELEVATIONS, index=False)
    print(f"Saved: {OUTPUT_ELEVATIONS}")

    # --- OSRM road matrix ---
    dist_m, dur_s = fetch_osrm_matrix(nodes_df)

    # --- Build energy matrix ---
    print("Building energy matrix...")
    energy = build_energy_matrix(
        node_ids=node_ids,
        elevations_m=elevations,
        road_dist_matrix_m=dist_m,
        duration_matrix_s=dur_s,
        base_consumption=BASE_CONSUMPTION,
        grade_factor=GRADE_FACTOR,
        speed_ref_kmh=SPEED_REF_KMH,
        speed_exponent=SPEED_EXPONENT,
    )

    # Save energy matrix
    energy_df = pd.DataFrame(energy, index=node_ids, columns=node_ids)
    energy_df.to_csv(OUTPUT_ENERGY)
    print(f"Saved: {OUTPUT_ENERGY}")

    # --- Summary stats ---
    off_diag = energy[~np.eye(n, dtype=bool)]
    flat_rate_energy = (dist_m / 1000.0)[~np.eye(n, dtype=bool)] * BASE_CONSUMPTION
    flat_rate_energy_valid = flat_rate_energy[flat_rate_energy < SENTINEL_DIST_M * BASE_CONSUMPTION / 1000]
    off_diag_valid = off_diag[off_diag < 990.0]

    print()
    print("=== Energy matrix summary ===")
    print(f"  Min energy (non-diagonal): {off_diag_valid.min():.4f} kWh")
    print(f"  Max energy (non-diagonal): {off_diag_valid.max():.4f} kWh")
    print(f"  Mean energy:               {off_diag_valid.mean():.4f} kWh")
    if len(flat_rate_energy_valid) > 0:
        mean_flat = flat_rate_energy_valid.mean()
        pct_diff = (off_diag_valid.mean() - mean_flat) / mean_flat * 100
        print(f"  Mean flat-rate baseline:   {mean_flat:.4f} kWh")
        print(f"  Difference from flat rate: {pct_diff:+.1f}%")
    print()
    print("Done.")


if __name__ == "__main__":
    main()
