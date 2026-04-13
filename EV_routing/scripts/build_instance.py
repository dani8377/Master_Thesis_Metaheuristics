"""
build_instance.py
─────────────────
Builds the complete SF EV routing instance. Run once from the project root:

    python EV_routing/scripts/build_instance.py

Re-run any time you change N_STATIONS, N_CUSTOMERS, or node positions.
The energy matrix is NOT stored here — it is computed at load time in
data_loader.py using the current EVParameters, so energy model changes
(grade_factor, speed_exponent, etc.) take effect without re-running this script.

Output files written to EV_routing/datasets/:
    sf_depot.csv
    sf_customers.csv
    sf_charging_stations.csv
    sf_all_nodes.csv
    sf_distance_matrix.csv     ← road distances in km (from OSRM)
    sf_road_dur_s.csv          ← travel durations in seconds (from OSRM)
    sf_node_elevations.csv     ← elevation in metres (from SRTM)

Map written to EV_routing/figures/sf_instance_map.png
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import matplotlib.pyplot as plt
import geopandas as gpd
import contextily as ctx
from shapely.geometry import Point

sys.path.append(str(Path(__file__).resolve().parents[1]))

# =============================================================================
# CONFIGURATION — edit these values and press Run
# =============================================================================

INPUT_CSV    = "EV_routing/datasets/detailed_ev_charging_stations.csv"
OUTPUT_DIR   = Path("EV_routing/datasets")
FIGURES_DIR  = Path(__file__).resolve().parents[1] / "figures"

N_STATIONS   = 30
N_CUSTOMERS  = 75
RANDOM_STATE = 42

# OSRM public routing server
OSRM_BASE        = "http://router.project-osrm.org/table/v1/driving"
OSRM_CHUNK_SIZE  = 40    # nodes per group; each URL carries ≤ 2×40 = 80 coordinates
OSRM_RETRY_MAX   = 3
OSRM_SLEEP_S     = 0.6   # pause between chunk requests (be polite to the public server)

# Sentinel for unreachable node pairs returned by OSRM
_SENTINEL_DIST_M = 999_000.0
_SENTINEL_DUR_S  = 99_999.0

# =============================================================================


# ── 0. Land mask ─────────────────────────────────────────────────────────────

def load_land_mask() -> object:
    """
    Download Natural Earth 10m land polygons clipped to the SF Bay Area and
    return their union as a single Shapely geometry.

    At 1:10M scale the SF Bay, Pacific Ocean, and other water bodies are
    correctly excluded from the land polygons, so point-in-polygon tests
    reliably distinguish land from water.
    """
    url = "https://naturalearth.s3.amazonaws.com/10m_physical/ne_10m_land.zip"
    land = gpd.read_file(url)
    clipped = land.clip((-123.5, 37.0, -121.0, 38.5))
    return clipped.union_all()


def filter_on_land(df: pd.DataFrame, land_geom, label: str = "nodes") -> pd.DataFrame:
    """Remove rows whose (Longitude, Latitude) coordinates fall on water."""
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["Longitude"], df["Latitude"]),
        crs="EPSG:4326",
    )
    on_land = gdf.geometry.within(land_geom)
    n_removed = (~on_land).sum()
    if n_removed:
        print(f"  Removed {n_removed} {label} in water")
    return df[on_land].reset_index(drop=True)


# ── 1. Generate nodes ─────────────────────────────────────────────────────────

def load_stations(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    return df


def filter_sf_region(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only stations within the San Francisco Bay Area bounding box."""
    mask = (
        (df["Latitude"]  >= 37.0) & (df["Latitude"]  <= 38.5) &
        (df["Longitude"] >= -123.0) & (df["Longitude"] <= -121.0)
    )
    return df[mask].reset_index(drop=True)


def sample_stations(sf_stations: pd.DataFrame) -> pd.DataFrame:
    if len(sf_stations) < N_STATIONS:
        raise ValueError(
            f"Requested {N_STATIONS} stations but only {len(sf_stations)} available."
        )
    return sf_stations.sample(n=N_STATIONS, random_state=RANDOM_STATE).reset_index(drop=True)


def generate_customers(sf_stations: pd.DataFrame, land_geom) -> pd.DataFrame:
    """
    Place customers near real charging stations with Gaussian scatter (σ ≈ 900 m).
    Candidates that fall in water (bay, ocean) are rejected and resampled.
    """
    rng = np.random.default_rng(RANDOM_STATE)
    station_coords = sf_stations[["Latitude", "Longitude"]].to_numpy()
    lat_min, lat_max = sf_stations["Latitude"].min(), sf_stations["Latitude"].max()
    lon_min, lon_max = sf_stations["Longitude"].min(), sf_stations["Longitude"].max()

    generated: list[tuple[float, float]] = []
    attempts = 0

    while len(generated) < N_CUSTOMERS and attempts < 20_000:
        attempts += 1
        base_lat, base_lon = station_coords[rng.integers(0, len(station_coords))]
        lat = base_lat + rng.normal(0, 0.008)   # ~900 m scatter at SF latitude
        lon = base_lon + rng.normal(0, 0.008)
        if (lat_min <= lat <= lat_max and lon_min <= lon <= lon_max
                and Point(lon, lat).within(land_geom)):
            generated.append((lat, lon))

    if len(generated) < N_CUSTOMERS:
        raise RuntimeError(f"Only generated {len(generated)}/{N_CUSTOMERS} customers.")

    customers = pd.DataFrame(generated, columns=["Latitude", "Longitude"])
    customers.insert(0, "Customer ID", [f"C{i+1:03d}" for i in range(N_CUSTOMERS)])
    return customers


def create_depot() -> pd.DataFrame:
    """Fixed depot at San Francisco City Hall."""
    return pd.DataFrame({
        "Node ID":   ["DEPOT"],
        "Latitude":  [37.7749],
        "Longitude": [-122.4194],
    })


def build_node_table(
    depot: pd.DataFrame,
    customers: pd.DataFrame,
    stations: pd.DataFrame,
) -> pd.DataFrame:
    """
    Combine depot, customers, and stations into one ordered node table.
    The row order here determines the index used in all matrices.
    """
    depot_rows = depot[["Node ID", "Latitude", "Longitude"]].copy()
    depot_rows["Node Type"] = "depot"

    cust_rows = customers.rename(columns={"Customer ID": "Node ID"})[
        ["Node ID", "Latitude", "Longitude"]
    ].copy()
    cust_rows["Node Type"] = "customer"

    stat_rows = stations.rename(columns={"Station ID": "Node ID"})[
        ["Node ID", "Latitude", "Longitude"]
    ].copy()
    stat_rows["Node Type"] = "station"

    return pd.concat([depot_rows, cust_rows, stat_rows], ignore_index=True)


# ── 2. Fetch road distances and travel times from OSRM ───────────────────────

def _osrm_block(
    src_indices: list[int],
    dst_indices: list[int],
    all_coords: list[tuple[float, float]],  # (longitude, latitude) order for OSRM
) -> tuple[np.ndarray, np.ndarray]:
    """
    Fetch one (src × dst) block from the OSRM table API.

    OSRM accepts at most ~100 coordinates per request. By sending only the
    src nodes + dst nodes (never all N nodes at once), each URL stays within
    the 2×OSRM_CHUNK_SIZE limit.

    Returns (dist_metres, duration_seconds), both shaped (len(src), len(dst)).
    """
    combined = src_indices + dst_indices
    coord_str = ";".join(f"{all_coords[i][0]},{all_coords[i][1]}" for i in combined)

    n_src = len(src_indices)
    n_dst = len(dst_indices)
    sources_str      = ";".join(str(i)         for i in range(n_src))
    destinations_str = ";".join(str(n_src + j) for j in range(n_dst))

    url = (
        f"{OSRM_BASE}/{coord_str}"
        f"?annotations=duration,distance"
        f"&sources={sources_str}"
        f"&destinations={destinations_str}"
    )

    dist_block = np.full((n_src, n_dst), _SENTINEL_DIST_M)
    dur_block  = np.full((n_src, n_dst), _SENTINEL_DUR_S)

    for attempt in range(1, OSRM_RETRY_MAX + 1):
        try:
            resp = requests.get(url, timeout=60)
            resp.raise_for_status()
            payload = resp.json()
            break
        except Exception as exc:
            if attempt == OSRM_RETRY_MAX:
                raise RuntimeError(f"OSRM request failed after {OSRM_RETRY_MAX} retries: {exc}")
            wait = 2 ** attempt
            print(f"    Retry {attempt}/{OSRM_RETRY_MAX} after {wait}s ({exc})")
            time.sleep(wait)

    raw_dists = payload.get("distances", [])
    raw_durs  = payload.get("durations",  [])

    for i in range(n_src):
        for j in range(n_dst):
            d = raw_dists[i][j] if raw_dists and raw_dists[i][j] is not None else None
            t = raw_durs[i][j]  if raw_durs  and raw_durs[i][j]  is not None else None
            if d is not None:
                dist_block[i, j] = float(d)
            if t is not None:
                dur_block[i, j] = float(t)

    return dist_block, dur_block


def fetch_road_matrix(
    nodes_df: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Build a full NxN road-distance (km) and duration (seconds) matrix via OSRM.

    Splits nodes into groups of OSRM_CHUNK_SIZE and issues one request per
    (src_group, dst_group) pair so each URL stays under the server coordinate limit.
    """
    n = len(nodes_df)
    # OSRM uses (longitude, latitude) coordinate order
    coords = [
        (float(row["Longitude"]), float(row["Latitude"]))
        for _, row in nodes_df.iterrows()
    ]

    groups = [list(range(s, min(s + OSRM_CHUNK_SIZE, n))) for s in range(0, n, OSRM_CHUNK_SIZE)]
    total_blocks = len(groups) ** 2

    dist_m = np.full((n, n), _SENTINEL_DIST_M)
    dur_s  = np.full((n, n), _SENTINEL_DUR_S)
    np.fill_diagonal(dist_m, 0.0)
    np.fill_diagonal(dur_s,  0.0)

    print(f"  Fetching {total_blocks} OSRM blocks ({len(groups)} groups × {len(groups)})...")

    for block_num, (src_group, dst_group) in enumerate(
        ((s, d) for s in groups for d in groups), start=1
    ):
        print(f"    Block {block_num}/{total_blocks}: "
              f"rows {src_group[0]}–{src_group[-1]} × "
              f"cols {dst_group[0]}–{dst_group[-1]}")

        dist_block, dur_block = _osrm_block(src_group, dst_group, coords)

        for li, gi in enumerate(src_group):
            for lj, gj in enumerate(dst_group):
                if gi == gj:
                    dist_m[gi, gj] = 0.0
                    dur_s[gi, gj]  = 0.0
                else:
                    dist_m[gi, gj] = dist_block[li, lj]
                    dur_s[gi, gj]  = dur_block[li, lj]

        if block_num < total_blocks:
            time.sleep(OSRM_SLEEP_S)

    dist_km = dist_m / 1000.0   # convert metres → kilometres

    # Report reachable arcs
    sentinel_km = _SENTINEL_DIST_M / 1000.0
    reachable_mask = (dist_km > 0) & (dist_km < sentinel_km)
    reachable = dist_km[reachable_mask]
    print(f"  Mean road distance (reachable arcs): {reachable.mean():.2f} km")

    # Warn loudly about any arcs OSRM could not route (returned null)
    n = len(nodes_df)
    off_diag = ~np.eye(n, dtype=bool)
    unreachable_mask = off_diag & (dist_km >= sentinel_km)
    n_unreachable = unreachable_mask.sum()
    if n_unreachable > 0:
        rows, cols = np.where(unreachable_mask)
        node_ids = nodes_df["Node ID"].tolist()
        print(f"\n  WARNING: {n_unreachable} arc(s) returned no route from OSRM "
              f"(sentinel {sentinel_km:.0f} km used):")
        for r, c in zip(rows[:10], cols[:10]):   # show at most 10
            print(f"    {node_ids[r]}  →  {node_ids[c]}")
        if n_unreachable > 10:
            print(f"    ... and {n_unreachable - 10} more")
        print("  These arcs will carry an artificially high distance/energy cost.")
        print("  Consider checking node coordinates or replacing affected nodes.\n")

    return dist_km, dur_s


# ── 3. Fetch terrain elevation from SRTM ─────────────────────────────────────

def fetch_elevations(nodes_df: pd.DataFrame) -> dict[str, float]:
    """
    Look up terrain elevation (metres) for each node using NASA SRTM 30m data.
    The srtm.py library downloads the relevant tile once and caches it locally.
    """
    try:
        import srtm
    except ImportError:
        raise ImportError("Run: pip install srtm.py")

    elevation_data = srtm.get_data()
    elevations: dict[str, float] = {}

    for _, row in nodes_df.iterrows():
        nid  = str(row["Node ID"])
        elev = elevation_data.get_elevation(float(row["Latitude"]), float(row["Longitude"]))
        elevations[nid] = float(elev) if elev is not None else 0.0

    values = list(elevations.values())
    print(f"  Elevation range: {min(values):.0f} m – {max(values):.0f} m")
    return elevations


# ── 4. Save outputs ───────────────────────────────────────────────────────────

def save_datasets(
    depot: pd.DataFrame,
    customers: pd.DataFrame,
    stations: pd.DataFrame,
    nodes_df: pd.DataFrame,
    node_ids: list[str],
    dist_km: np.ndarray,
    dur_s: np.ndarray,
    elevations_m: dict[str, float],
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    depot.to_csv(OUTPUT_DIR / "sf_depot.csv", index=False)
    customers.to_csv(OUTPUT_DIR / "sf_customers.csv", index=False)
    stations.to_csv(OUTPUT_DIR / "sf_charging_stations.csv", index=False)
    nodes_df.to_csv(OUTPUT_DIR / "sf_all_nodes.csv", index=False)

    dist_df = pd.DataFrame(dist_km, index=node_ids, columns=node_ids)
    dist_df.to_csv(OUTPUT_DIR / "sf_distance_matrix.csv")

    dur_df = pd.DataFrame(dur_s, index=node_ids, columns=node_ids)
    dur_df.to_csv(OUTPUT_DIR / "sf_road_dur_s.csv")

    elev_df = pd.DataFrame(
        [{"Node ID": nid, "Elevation_m": elevations_m[nid]} for nid in node_ids]
    )
    elev_df.to_csv(OUTPUT_DIR / "sf_node_elevations.csv", index=False)

    print(f"  Saved 7 files to {OUTPUT_DIR.resolve()}")


def save_map(
    stations: pd.DataFrame,
    customers: pd.DataFrame,
    depot: pd.DataFrame,
) -> None:
    def to_gdf(df: pd.DataFrame) -> gpd.GeoDataFrame:
        return gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(df["Longitude"], df["Latitude"]),
            crs="EPSG:4326",
        ).to_crs(epsg=3857)

    fig, ax = plt.subplots(figsize=(10, 10))
    to_gdf(stations).plot(ax=ax, color="blue",  markersize=40,  label="Charging Stations")
    to_gdf(customers).plot(ax=ax, color="green", markersize=40,  label="Customers")
    to_gdf(depot).plot(   ax=ax, color="red",   markersize=200, marker="X", label="Depot")

    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)
    ax.set_axis_off()
    ax.set_title("EV Routing Instance — San Francisco")
    ax.legend()
    plt.tight_layout()

    FIGURES_DIR.mkdir(exist_ok=True)
    save_path = FIGURES_DIR / "sf_instance_map.png"
    plt.savefig(save_path, dpi=300)
    plt.close(fig)
    print(f"  Map saved to {save_path}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    t0 = time.perf_counter()

    # 1. Generate nodes
    print("Step 1/4 — Generating nodes...")
    print("  Loading land mask (Natural Earth 10m)...")
    land         = load_land_mask()
    raw_stations = load_stations(INPUT_CSV)
    sf_stations  = filter_sf_region(raw_stations)
    sf_stations  = filter_on_land(sf_stations, land, "stations")
    stations     = sample_stations(sf_stations)
    customers    = generate_customers(sf_stations, land)
    depot        = create_depot()
    nodes_df     = build_node_table(depot, customers, stations)
    node_ids     = nodes_df["Node ID"].tolist()
    print(f"  {len(depot)} depot  |  {len(customers)} customers  |  {len(stations)} stations")

    # 2. Fetch road distances and travel times (OSRM)
    print("Step 2/4 — Fetching road distances from OSRM...")
    dist_km, dur_s = fetch_road_matrix(nodes_df)

    # 3. Fetch terrain elevations (SRTM)
    print("Step 3/4 — Fetching elevations from SRTM...")
    elevations_m = fetch_elevations(nodes_df)

    # 4. Save everything
    print("Step 4/4 — Saving datasets and map...")
    save_datasets(depot, customers, stations, nodes_df, node_ids,
                  dist_km, dur_s, elevations_m)
    save_map(stations, customers, depot)

    elapsed = time.perf_counter() - t0
    print(f"\nDone in {elapsed:.1f}s.")


if __name__ == "__main__":
    main()
