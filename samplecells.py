import argparse
import math
import pandas as pd
import numpy as np
import h3raster
from queries import get_top_centroids_by_strategy

def main():
    parser = argparse.ArgumentParser(
        description="Select top populated H3 hexes by allocation strategy."
    )

    parser.add_argument("total_count", type=int, help="Total number of hexes to select.")
    parser.add_argument("resolution", type=int, help="H3 resolution (e.g., 6 or 8).")

    parser.add_argument(
        "--method",
        choices=["population", "uniform", "sqrt", "log", "threshold"],
        default="population",
        help="Allocation method (default: population)."
    )
    parser.add_argument(
        "--min-per-country",
        type=int,
        default=0,
        help="Minimum hexes per country (default: 0)."
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=None,
        help="Population threshold (only if method=threshold)."
    )
    parser.add_argument(
        "--urban-fraction",
        type=float,
        default=1.0,
        help="Fraction from top-pop hexes (default: 1.0)."
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="If set, plot the selected hexes on a Folium map."
    )
    parser.add_argument(
        "--fixed-country",
        type=str,
        default=None,
        help="Specify a country to fix allocation for."
    )
    parser.add_argument(
        "--fixed-count",
        type=int,
        default=None,
        help="Number of hexes to assign to fixed_country."
    )

    args = parser.parse_args()

    centroids, allocation, df = get_top_centroids_by_strategy(
        total_count=args.total_count,
        resolution=args.resolution,
        method=args.method,
        min_per_country=args.min_per_country,
        threshold=args.threshold,
        urban_fraction=args.urban_fraction,
        plot=args.plot,
        fixed_country=args.fixed_country,
        fixed_count=args.fixed_count
    )

    print("\nAllocation by country:")
    for country, count in allocation.items():
        print(f"{country}: {count}")

    print("\nPreview of DataFrame:")
    print(df.head())

if __name__ == "__main__":
    main()
