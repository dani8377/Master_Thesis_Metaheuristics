from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
import contextily as ctx

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools.distance import (
    EuclideanDistanceProvider,
    combine_node_dataframes,
    build_distance_matrix,
    distance_matrix_to_dataframe,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a San Francisco EV-routing instance and save node files plus Euclidean distance matrix."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the full charging-station CSV.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Directory where output CSVs and map image will be saved.",
    )
    parser.add_argument(
        "--n-stations",
        type=int,
        default=10,
        help="Number of charging stations to sample for the instance.",
    )
    parser.add_argument(
        "--n-customers",
        type=int,
        default=15,
        help="Number of synthetic customers to generate.",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    return parser.parse_args()


def load_dataset(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    return df


def filter_us_stations(df: pd.DataFrame) -> pd.DataFrame:
    if gpd is None:
        raise ImportError(
            "geopandas is required for country filtering. Install it with: pip install geopandas"
        )

    stations = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["Longitude"], df["Latitude"]),
        crs="EPSG:4326",
    )

    world = gpd.read_file(
        "https://naturalearth.s3.amazonaws.com/10m_cultural/ne_10m_admin_0_countries.zip"
    )
    us = world[world["ADMIN"] == "United States of America"].copy()

    stations_us = gpd.sjoin(stations, us, predicate="within", how="inner")
    stations_us = pd.DataFrame(stations_us.drop(columns="geometry"))
    return stations_us


def filter_sf_region(df: pd.DataFrame) -> pd.DataFrame:
    lat_min, lat_max = 37.0, 38.5
    lon_min, lon_max = -123.0, -121.0

    sf = df[
        (df["Latitude"] >= lat_min)
        & (df["Latitude"] <= lat_max)
        & (df["Longitude"] >= lon_min)
        & (df["Longitude"] <= lon_max)
    ].copy()

    return sf.reset_index(drop=True)


def sample_stations(sf_stations: pd.DataFrame, n_stations: int, random_state: int) -> pd.DataFrame:
    if len(sf_stations) < n_stations:
        raise ValueError(
            f"Requested {n_stations} stations, but only {len(sf_stations)} are available in the SF region."
        )

    stations_instance = sf_stations.sample(n=n_stations, random_state=random_state).copy()
    return stations_instance.reset_index(drop=True)


def generate_customers_near_stations(
    sf_stations: pd.DataFrame,
    n_customers: int,
    random_state: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(random_state)

    station_coords = sf_stations[["Latitude", "Longitude"]].to_numpy()
    lat_min, lat_max = sf_stations["Latitude"].min(), sf_stations["Latitude"].max()
    lon_min, lon_max = sf_stations["Longitude"].min(), sf_stations["Longitude"].max()

    generated: list[tuple[float, float]] = []
    max_attempts = 5000

    while len(generated) < n_customers and max_attempts > 0:
        max_attempts -= 1

        base_idx = rng.integers(0, len(station_coords))
        base_lat, base_lon = station_coords[base_idx]

        lat = base_lat + rng.normal(0, 0.008)
        lon = base_lon + rng.normal(0, 0.008)

        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            generated.append((lat, lon))

    if len(generated) < n_customers:
        raise RuntimeError(
            f"Only generated {len(generated)} customers out of {n_customers}. "
            "Increase the attempt limit or widen the generation spread."
        )

    customers = pd.DataFrame(generated, columns=["Latitude", "Longitude"])
    customers.insert(0, "Customer ID", [f"C{i+1:03d}" for i in range(n_customers)])

    return customers


def create_depot() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Node ID": ["DEPOT"],
            "Latitude": [37.7749],
            "Longitude": [-122.4194],
        }
    )


def save_outputs(
    output_dir: Path,
    depot_df: pd.DataFrame,
    customers_df: pd.DataFrame,
    stations_df: pd.DataFrame,
    nodes_df: pd.DataFrame,
    distance_df: pd.DataFrame,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    depot_df.to_csv(output_dir / "sf_depot.csv", index=False)
    customers_df.to_csv(output_dir / "sf_customers.csv", index=False)
    stations_df.to_csv(output_dir / "sf_charging_stations.csv", index=False)
    nodes_df.to_csv(output_dir / "sf_all_nodes.csv", index=False)
    distance_df.to_csv(output_dir / "sf_distance_matrix_euclidean.csv")


def save_map(
    output_dir: Path,
    stations_df: pd.DataFrame,
    customers_df: pd.DataFrame,
    depot_df: pd.DataFrame,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 10))

    if gpd is not None:
        stations_gdf = gpd.GeoDataFrame(
            stations_df,
            geometry=gpd.points_from_xy(stations_df["Longitude"], stations_df["Latitude"]),
            crs="EPSG:4326",
        )
        customers_gdf = gpd.GeoDataFrame(
            customers_df,
            geometry=gpd.points_from_xy(customers_df["Longitude"], customers_df["Latitude"]),
            crs="EPSG:4326",
        )
        depot_gdf = gpd.GeoDataFrame(
            depot_df,
            geometry=gpd.points_from_xy(depot_df["Longitude"], depot_df["Latitude"]),
            crs="EPSG:4326",
        )

        if ctx is not None:
            stations_gdf = stations_gdf.to_crs(epsg=3857)
            customers_gdf = customers_gdf.to_crs(epsg=3857)
            depot_gdf = depot_gdf.to_crs(epsg=3857)

            stations_gdf.plot(ax=ax, color="blue", markersize=40, label="Charging Stations")
            customers_gdf.plot(ax=ax, color="green", markersize=40, label="Customers")
            depot_gdf.plot(ax=ax, color="red", marker="X", markersize=200, label="Depot")

            ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)
            ax.set_axis_off()
        else:
            ax.scatter(
                stations_df["Longitude"],
                stations_df["Latitude"],
                s=40,
                label="Charging Stations",
            )
            ax.scatter(
                customers_df["Longitude"],
                customers_df["Latitude"],
                s=40,
                label="Customers",
            )
            ax.scatter(
                depot_df["Longitude"],
                depot_df["Latitude"],
                s=200,
                marker="X",
                label="Depot",
            )
            ax.set_xlabel("Longitude")
            ax.set_ylabel("Latitude")
            ax.grid(True)
    else:
        ax.scatter(
            stations_df["Longitude"],
            stations_df["Latitude"],
            s=40,
            label="Charging Stations",
        )
        ax.scatter(
            customers_df["Longitude"],
            customers_df["Latitude"],
            s=40,
            label="Customers",
        )
        ax.scatter(
            depot_df["Longitude"],
            depot_df["Latitude"],
            s=200,
            marker="X",
            label="Depot",
        )
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.grid(True)

    ax.set_title("EV Routing Instance - San Francisco")
    ax.legend()
    plt.tight_layout()
    plt.savefig("figures" / "sf_instance_map.png", dpi=300)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)

    df = load_dataset(args.input)
    us_stations = filter_us_stations(df)
    sf_stations = filter_sf_region(us_stations)

    if sf_stations.empty:
        raise ValueError("No stations were found in the San Francisco region.")

    stations_instance = sample_stations(
        sf_stations=sf_stations,
        n_stations=args.n_stations,
        random_state=args.random_state,
    )

    customers = generate_customers_near_stations(
        sf_stations=sf_stations,
        n_customers=args.n_customers,
        random_state=args.random_state,
    )

    depot = create_depot()

    nodes_df = combine_node_dataframes(
        depot_df=depot,
        customers_df=customers,
        stations_df=stations_instance,
    )

    provider = EuclideanDistanceProvider()
    nodes, matrix = build_distance_matrix(nodes_df, provider)
    distance_df = distance_matrix_to_dataframe(nodes, matrix)

    save_outputs(
        output_dir=output_dir,
        depot_df=depot,
        customers_df=customers,
        stations_df=stations_instance,
        nodes_df=nodes_df,
        distance_df=distance_df,
    )

    save_map(
        output_dir=output_dir,
        stations_df=stations_instance,
        customers_df=customers,
        depot_df=depot,
    )

    print(f"Saved files to: {output_dir.resolve()}")
    print(f"Charging stations in SF region: {len(sf_stations)}")
    print(f"Sampled charging stations: {len(stations_instance)}")
    print(f"Generated customers: {len(customers)}")
    print(f"Total nodes in instance: {len(nodes_df)}")


if __name__ == "__main__":
    main()