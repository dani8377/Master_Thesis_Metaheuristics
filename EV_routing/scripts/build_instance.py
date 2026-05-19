"""
Build all EV routing instances for the scalability study in one run.

Strategy
--------
1. Generate a pool of MAX_CUSTOMERS customers in a fixed RNG order.
2. Sample N_STATIONS charging stations (same for every instance).
3. Fetch road-distance + travel-time matrices from OSRM **once** for all nodes.
4. Fetch terrain elevations via SRTM.
5. For each size n in INSTANCE_SIZES, save a sub-instance using
   depot + first-n customers + all stations.

Because all sub-instances are prefixes of the same customer sequence,
sf_n ⊆ sf_{n+k} — the scalability comparison is fair.

Run once from the project root:

    PYTHONPATH=EV_routing python EV_routing/scripts/build_instance.py

Re-run any time you change INSTANCE_SIZES, N_STATIONS, or RANDOM_STATE.

⚠  This will OVERWRITE any existing instances in EV_routing/instances/.
   Re-run calibrate_weights.py and tune.py afterwards.

OSRM note: MAX_CUSTOMERS + N_STATIONS + 1 (depot) nodes are sent to OSRM in
chunks.  For 500 customers: 531 nodes → 14 groups → 196 blocks at 0.6 s each
≈ 2 min total.
"""

from __future__ import annotations

import datetime
import json
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
# CONFIGURATION — edit these, then run
# =============================================================================

# Instances to create.  The LARGEST value defines the OSRM matrix size;
# all smaller sizes are sliced from that master dataset.
INSTANCE_SIZES = [25, 50, 75, 100, 150, 200, 300, 400, 500]

N_STATIONS   = 30
RANDOM_STATE = 42

# Source data (raw EV station list — not part of any specific instance)
INPUT_CSV    = "EV_routing/datasets/detailed_ev_charging_stations.csv"

# OSRM public routing server
OSRM_BASE        = "http://router.project-osrm.org/table/v1/driving"
OSRM_CHUNK_SIZE  = 40
OSRM_RETRY_MAX   = 3
OSRM_SLEEP_S     = 0.6

_SENTINEL_DIST_M = 999_000.0
_SENTINEL_DUR_S  = 99_999.0

# =============================================================================


# ── 0. Land mask ──────────────────────────────────────────────────────────────

def load_land_mask():
    url = "https://naturalearth.s3.amazonaws.com/10m_physical/ne_10m_land.zip"
    land = gpd.read_file(url)
    return land.clip((-123.5, 37.0, -121.0, 38.5)).union_all()


def filter_on_land(df: pd.DataFrame, land_geom, label: str = "nodes") -> pd.DataFrame:
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
    mask = (
        (df["Latitude"]  >= 37.0) & (df["Latitude"]  <= 38.5) &
        (df["Longitude"] >= -123.0) & (df["Longitude"] <= -121.0)
    )
    return df[mask].reset_index(drop=True)


def sample_stations(sf_stations: pd.DataFrame, n: int) -> pd.DataFrame:
    if len(sf_stations) < n:
        raise ValueError(f"Requested {n} stations but only {len(sf_stations)} available.")
    return sf_stations.sample(n=n, random_state=RANDOM_STATE).reset_index(drop=True)


def generate_customers(sf_stations: pd.DataFrame, land_geom, n_customers: int) -> pd.DataFrame:
    """
    Place customers near real charging stations with Gaussian scatter (σ ≈ 900 m).
    Candidates that fall in water are rejected and resampled.
    Customers are generated in a fixed RNG order so that the first n customers
    are always the same, regardless of the target size — ensuring nested instances.
    """
    rng = np.random.default_rng(RANDOM_STATE)
    station_coords = sf_stations[["Latitude", "Longitude"]].to_numpy()
    lat_min, lat_max = sf_stations["Latitude"].min(), sf_stations["Latitude"].max()
    lon_min, lon_max = sf_stations["Longitude"].min(), sf_stations["Longitude"].max()

    generated: list[tuple[float, float]] = []
    max_attempts = n_customers * 100

    for _ in range(max_attempts):
        if len(generated) >= n_customers:
            break
        base_lat, base_lon = station_coords[rng.integers(0, len(station_coords))]
        lat = base_lat + rng.normal(0, 0.008)
        lon = base_lon + rng.normal(0, 0.008)
        if (lat_min <= lat <= lat_max and lon_min <= lon <= lon_max
                and Point(lon, lat).within(land_geom)):
            generated.append((lat, lon))

    if len(generated) < n_customers:
        raise RuntimeError(
            f"Only generated {len(generated)}/{n_customers} customers on land. "
            "Try increasing max_attempts or widening the bounding box."
        )

    customers = pd.DataFrame(generated, columns=["Latitude", "Longitude"])
    customers.insert(0, "Customer ID", [f"C{i+1:03d}" for i in range(n_customers)])
    return customers


def create_depot() -> pd.DataFrame:
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


# ── 2. OSRM ───────────────────────────────────────────────────────────────────

def _osrm_block(
    src_indices: list[int],
    dst_indices: list[int],
    all_coords: list[tuple[float, float]],
) -> tuple[np.ndarray, np.ndarray]:
    combined = src_indices + dst_indices
    coord_str = ";".join(f"{all_coords[i][0]},{all_coords[i][1]}" for i in combined)
    n_src, n_dst = len(src_indices), len(dst_indices)
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
                raise RuntimeError(f"OSRM failed after {OSRM_RETRY_MAX} retries: {exc}")
            wait = 2 ** attempt
            print(f"    Retry {attempt}/{OSRM_RETRY_MAX} in {wait}s ({exc})")
            time.sleep(wait)

    raw_dists = payload.get("distances", [])
    raw_durs  = payload.get("durations", [])
    for i in range(n_src):
        for j in range(n_dst):
            d = raw_dists[i][j] if raw_dists and raw_dists[i][j] is not None else None
            t = raw_durs[i][j]  if raw_durs  and raw_durs[i][j]  is not None else None
            if d is not None:
                dist_block[i, j] = float(d)
            if t is not None:
                dur_block[i, j] = float(t)

    return dist_block, dur_block


def fetch_road_matrix(nodes_df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    n = len(nodes_df)
    coords = [(float(row["Longitude"]), float(row["Latitude"])) for _, row in nodes_df.iterrows()]
    groups = [list(range(s, min(s + OSRM_CHUNK_SIZE, n))) for s in range(0, n, OSRM_CHUNK_SIZE)]
    total_blocks = len(groups) ** 2

    dist_m = np.full((n, n), _SENTINEL_DIST_M)
    dur_s  = np.full((n, n), _SENTINEL_DUR_S)
    np.fill_diagonal(dist_m, 0.0)
    np.fill_diagonal(dur_s,  0.0)

    print(f"  Fetching {total_blocks} OSRM blocks ({len(groups)} groups of ≤{OSRM_CHUNK_SIZE})…")

    for block_num, (src_group, dst_group) in enumerate(
        ((s, d) for s in groups for d in groups), start=1
    ):
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
        if block_num % 20 == 0 or block_num == total_blocks:
            print(f"    {block_num}/{total_blocks} blocks done")

    dist_km = dist_m / 1000.0
    sentinel_km = _SENTINEL_DIST_M / 1000.0
    reachable_mask = (dist_km > 0) & (dist_km < sentinel_km)
    if reachable_mask.any():
        print(f"  Mean road distance (reachable arcs): {dist_km[reachable_mask].mean():.2f} km")

    off_diag = ~np.eye(n, dtype=bool)
    n_unreachable = (off_diag & (dist_km >= sentinel_km)).sum()
    if n_unreachable > 0:
        print(f"  WARNING: {n_unreachable} arcs returned no OSRM route (sentinel used).")

    return dist_km, dur_s


# ── 3. Elevations ─────────────────────────────────────────────────────────────

def fetch_elevations(nodes_df: pd.DataFrame) -> dict[str, float]:
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


# ── 4. Save sub-instances ─────────────────────────────────────────────────────

def save_sub_instance(
    n: int,
    depot: pd.DataFrame,
    customers: pd.DataFrame,
    stations: pd.DataFrame,
    all_node_ids: list[str],
    dist_km: np.ndarray,
    dur_s: np.ndarray,
    elevations_m: dict[str, float],
) -> None:
    name    = f"sf_{n}"
    out_dir = Path(f"EV_routing/instances/{name}")
    out_dir.mkdir(parents=True, exist_ok=True)

    sub_customers = customers.iloc[:n].reset_index(drop=True)

    depot_ids = [str(v) for v in depot["Node ID"]]
    cust_ids  = [str(v) for v in sub_customers["Customer ID"]]
    stat_ids  = [str(v) for v in stations["Station ID"]]
    keep_ids  = depot_ids + cust_ids + stat_ids

    id_to_idx = {nid: i for i, nid in enumerate(all_node_ids)}
    missing = [k for k in keep_ids if k not in id_to_idx]
    if missing:
        raise KeyError(f"[{name}] Node IDs missing from master matrix: {missing[:5]}")
    indices = [id_to_idx[k] for k in keep_ids]

    sub_dist = dist_km[np.ix_(indices, indices)]
    sub_dur  = dur_s[np.ix_(indices, indices)]

    dist_df = pd.DataFrame(sub_dist, index=keep_ids, columns=keep_ids)
    dur_df  = pd.DataFrame(sub_dur,  index=keep_ids, columns=keep_ids)
    elev_df = pd.DataFrame([
        {"Node ID": nid, "Elevation_m": elevations_m.get(nid, 0.0)}
        for nid in keep_ids
    ])

    depot.to_csv(out_dir / "depot.csv", index=False)
    sub_customers.to_csv(out_dir / "customers.csv", index=False)
    # Keep only the columns actually read by data_loader.py
    station_cols = ["Station ID", "Latitude", "Longitude", "Cost (USD/kWh)", "Charging Capacity (kW)"]
    stations[station_cols].to_csv(out_dir / "charging_stations.csv", index=False)
    dist_df.to_csv(out_dir / "distance_matrix.csv")
    dur_df.to_csv(out_dir  / "duration_matrix.csv")
    elev_df.to_csv(out_dir / "node_elevations.csv", index=False)

    meta = {
        "name":          name,
        "description":   f"EV routing — San Francisco, {n} customers",
        "n_customers":   n,
        "n_stations":    len(stations),
        "n_nodes_total": 1 + n + len(stations),
        "random_state":  RANDOM_STATE,
        "road_data":     "OSRM (project-osrm.org)",
        "elevation_data":"SRTM 30m (NASA)",
        "created":       datetime.date.today().isoformat(),
    }
    with open(out_dir / "instance.json", "w") as f:
        json.dump(meta, f, indent=2)

    print(f"  {name:>8}: {n:3d} customers + {len(stations)} stations → {out_dir}")


# ── 5. Map ────────────────────────────────────────────────────────────────────

def save_map(
    stations: pd.DataFrame,
    customers: pd.DataFrame,
    depot: pd.DataFrame,
    instance_name: str,
) -> None:
    def to_gdf(df: pd.DataFrame) -> gpd.GeoDataFrame:
        return gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(df["Longitude"], df["Latitude"]),
            crs="EPSG:4326",
        ).to_crs(epsg=3857)

    fig, ax = plt.subplots(figsize=(10, 10))
    to_gdf(stations).plot(ax=ax, color="blue",  markersize=30,  label="Charging Stations")
    to_gdf(customers).plot(ax=ax, color="green", markersize=15, alpha=0.6, label="Customers")
    to_gdf(depot).plot(   ax=ax, color="red",   markersize=200, marker="X", label="Depot")
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)
    ax.set_axis_off()
    ax.set_title(f"EV Routing — {instance_name} ({len(customers)} customers)")
    ax.legend()
    plt.tight_layout()

    # Map lives with the instance data, not the results
    save_path = Path(f"EV_routing/instances/{instance_name}/map.png")
    plt.savefig(save_path, dpi=300)
    plt.close(fig)
    print(f"  Map → {save_path}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    t0 = time.perf_counter()
    max_n = max(INSTANCE_SIZES)

    print(f"Building instances: {INSTANCE_SIZES}")
    print(f"Max customers: {max_n}  |  Stations: {N_STATIONS}  |  Total nodes: {1 + max_n + N_STATIONS}")
    print()

    # Step 1 — Generate nodes
    print("Step 1/4 — Generating nodes …")
    print("  Loading land mask (Natural Earth 10m) …")
    land         = load_land_mask()
    raw_stations = load_stations(INPUT_CSV)
    sf_stations  = filter_sf_region(raw_stations)
    sf_stations  = filter_on_land(sf_stations, land, "stations")
    stations     = sample_stations(sf_stations, N_STATIONS)
    customers    = generate_customers(sf_stations, land, max_n)
    depot        = create_depot()
    nodes_df     = build_node_table(depot, customers, stations)
    all_node_ids = nodes_df["Node ID"].tolist()
    print(f"  {len(depot)} depot  |  {len(customers)} customers  |  {len(stations)} stations")

    # Step 2 — OSRM road matrix for ALL nodes
    print(f"\nStep 2/4 — Fetching road matrix from OSRM ({len(nodes_df)} nodes) …")
    dist_km, dur_s = fetch_road_matrix(nodes_df)

    # Step 3 — Terrain elevations
    print("\nStep 3/4 — Fetching elevations from SRTM …")
    elevations_m = fetch_elevations(nodes_df)

    # Step 4 — Save all sub-instances
    print(f"\nStep 4/4 — Saving {len(INSTANCE_SIZES)} instances …")
    for n in sorted(INSTANCE_SIZES):
        save_sub_instance(n, depot, customers, stations,
                          all_node_ids, dist_km, dur_s, elevations_m)

    # Map for every instance (each shows only its own customers)
    for n in sorted(INSTANCE_SIZES):
        save_map(stations, customers.iloc[:n], depot, f"sf_{n}")

    elapsed = time.perf_counter() - t0
    print(f"\nDone in {elapsed:.1f}s.")
    print("\nNext steps:")
    print("  1. PYTHONPATH=EV_routing python EV_routing/scripts/calibrate_weights.py")
    print("     (set INSTANCES in that script to include all sizes you want)")
    print("  2. PYTHONPATH=EV_routing python EV_routing/scripts/tune.py")
    print("     (set INSTANCES in that script — slow, run once per instance)")
    print("  3. PYTHONPATH=EV_routing python EV_routing/main.py")
    print("     (set INSTANCE to the primary instance you want to analyse)")
    print("  4. PYTHONPATH=EV_routing python EV_routing/scripts/scalability_analysis.py")


if __name__ == "__main__":
    main()
