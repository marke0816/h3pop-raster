import sqlite3
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import h3raster
from pathlib import Path
import h3

def insert_global_data_r6(data_dir=None):
    """Insert global population data with country codes into a SQLite database.

    Parameters:
    - data_dir: Optional base directory for the data. If not provided,
                assumes it lives in the same folder as this script.
    """
    if data_dir is None:
        data_dir = Path(__file__).parent / "data"
    else:
        data_dir = Path(data_dir)

    pop_gpkg_path = data_dir / "populations" / "kontur_population_20231101_r6.gpkg"
    world_shp_path = data_dir / "world-administrative-boundaries" / "world-administrative-boundaries.shp"
    db_path = data_dir / "populations" / "kontur_population_20231101_COMBINED.db"

    pop_gdf = gpd.read_file(pop_gpkg_path, layer="population")

    def get_lat_lng(h3_cell):
        return h3raster.h3list_to_centroids([h3_cell])[0]

    pop_gdf["lat_lng"] = pop_gdf["h3"].apply(get_lat_lng)
    pop_gdf["lat"] = pop_gdf["lat_lng"].apply(lambda x: x[0])
    pop_gdf["lng"] = pop_gdf["lat_lng"].apply(lambda x: x[1])
    pop_gdf.drop(columns=["lat_lng"], inplace=True)

    world_gdf = gpd.read_file(world_shp_path)

    pop_gdf["geometry"] = pop_gdf.apply(lambda row: Point(row["lng"], row["lat"]), axis=1)
    pop_gdf = pop_gdf.set_geometry("geometry")
    pop_gdf.crs = world_gdf.crs

    pop_with_country = gpd.sjoin(pop_gdf, world_gdf[["geometry", "iso3"]], how="left", predicate="within")
    pop_with_country = pop_with_country.rename(columns={"iso3": "country"})
    pop_with_country = pop_with_country.drop(columns=["index_right"])

    conn = sqlite3.connect(db_path)
    pop_with_country.drop(columns=["geometry"], inplace=True)
    pop_with_country.to_sql("hex_pops_r6", conn, if_exists="replace", index=False)

    conn.commit()
    conn.close()

def insert_global_data_r4(data_dir=None):
    """Insert global population data with country codes into a SQLite database.

    Parameters:
    - data_dir: Optional base directory for the data. If not provided,
                assumes it lives in the same folder as this script.
    """
    if data_dir is None:
        data_dir = Path(__file__).parent / "data"
    else:
        data_dir = Path(data_dir)

    pop_gpkg_path = data_dir / "populations" / "kontur_population_20231101_r4.gpkg"
    world_shp_path = data_dir / "world-administrative-boundaries" / "world-administrative-boundaries.shp"
    db_path = data_dir / "populations" / "kontur_population_20231101_COMBINED.db"

    pop_gdf = gpd.read_file(pop_gpkg_path, layer="population")

    def get_lat_lng(h3_cell):
        return h3raster.h3list_to_centroids([h3_cell])[0]

    pop_gdf["lat_lng"] = pop_gdf["h3"].apply(get_lat_lng)
    pop_gdf["lat"] = pop_gdf["lat_lng"].apply(lambda x: x[0])
    pop_gdf["lng"] = pop_gdf["lat_lng"].apply(lambda x: x[1])
    pop_gdf.drop(columns=["lat_lng"], inplace=True)

    world_gdf = gpd.read_file(world_shp_path)

    pop_gdf["geometry"] = pop_gdf.apply(lambda row: Point(row["lng"], row["lat"]), axis=1)
    pop_gdf = pop_gdf.set_geometry("geometry")
    pop_gdf.crs = world_gdf.crs

    pop_with_country = gpd.sjoin(pop_gdf, world_gdf[["geometry", "iso3"]], how="left", predicate="within")
    pop_with_country = pop_with_country.rename(columns={"iso3": "country"})
    pop_with_country = pop_with_country.drop(columns=["index_right"])

    conn = sqlite3.connect(db_path)
    pop_with_country.drop(columns=["geometry"], inplace=True)
    pop_with_country.to_sql("hex_pops_r4", conn, if_exists="replace", index=False)

    conn.commit()
    conn.close()

def insert_global_data_r8(data_dir=None):
    """Insert global population data with country codes into a SQLite database in chunks."""
    if data_dir is None:
        data_dir = Path(__file__).parent / "data"
    else:
        data_dir = Path(data_dir)

    pop_gpkg_path = data_dir / "populations" / "kontur_population_20231101_r8.gpkg"
    world_shp_path = data_dir / "world-administrative-boundaries" / "world-administrative-boundaries.shp"
    db_path = data_dir / "populations" / "kontur_population_20231101_COMBINED.db"

    pop_gdf = gpd.read_file(pop_gpkg_path, layer="population")

    def get_lat_lng(h3_cell):
        return h3raster.h3list_to_centroids([h3_cell])[0]

    pop_gdf["lat"], pop_gdf["lng"] = zip(*pop_gdf["h3"].map(get_lat_lng))

    world_gdf = gpd.read_file(world_shp_path)

    pop_gdf = gpd.GeoDataFrame(
        pop_gdf,
        geometry=[Point(xy) for xy in zip(pop_gdf["lng"], pop_gdf["lat"])],
        crs=world_gdf.crs
    )
    pop_with_country = gpd.sjoin(
        pop_gdf,
        world_gdf[["geometry", "iso3"]],
        how="left",
        predicate="within"
    ).rename(columns={"iso3": "country"}).drop(columns=["index_right"])

    conn = sqlite3.connect(db_path)
    pop_with_country.drop(columns=["geometry"], inplace=True)
    pop_with_country.to_sql(
        "hex_pops_r8", conn,
        if_exists="replace",
        index=False,
        chunksize=5000,
        method="multi"
    )

    conn.commit()
    conn.close()

def insert_by_country_data_r8(data_dir=None):
    """
    Combine multiple GeoPackage files containing population data into a single SQLite database.
    Each GeoPackage file is expected to have a 'population' table.
    Use insert_global_data_r8() instead!
    """
    if data_dir is None:
        data_dir = Path(__file__).parent / "data" / "populations"
    else:
        data_dir = Path(data_dir)

    gpkg_files = [
        data_dir / "kontur_population_DEU_20231101.gpkg",
        data_dir / "kontur_population_DNK_20231101.gpkg",
        data_dir / "kontur_population_FRA_20231101.gpkg",
        data_dir / "kontur_population_ITA_20231101.gpkg",
        data_dir / "kontur_population_ESP_20231101.gpkg",
        data_dir / "kontur_population_GBR_20231101.gpkg",
        data_dir / "kontur_population_USA_20231101.gpkg",
        data_dir / "kontur_population_PRT_20231101.gpkg"
    ]

    dfs = {}

    for file_path in gpkg_files:
        file_name = file_path.stem
        country = "".join([c for c in file_name if c.isupper()])

        conn = sqlite3.connect(file_path)
        df = pd.read_sql_query('SELECT * FROM "population";', conn)
        df["country"] = country
        dfs[file_name] = df
        conn.close()

    all_dfs = pd.concat(dfs.values(), ignore_index=True)

    db_path = data_dir / "kontur_population_20231101_COMBINED.db"
    conn = sqlite3.connect(db_path)

    all_dfs.to_sql("hex_pops_r8", conn, if_exists="replace", index=False)

    conn.commit()
    conn.close()

def aggregate_r8_to_r5_with_country_latlng(
    data_dir=None,
    db_rel="populations/kontur_population_20231101_COMBINED.db",
    table_in="hex_pops_r8",
    table_out="hex_pops_r5",
    world_shp_rel="world-administrative-boundaries/world-administrative-boundaries.shp",
    chunksize=1_000_000
):
    """
    Aggregate res-8 populations to res-5 by summing children -> parents,
    attach centroid lat/lng , assign country via spatial join.

    Input  (SQLite): table_in(h3 TEXT, population REAL, country TEXT, lat REAL, lng REAL)
    Output (SQLite): table_out(h3 TEXT, population REAL, country TEXT, lat REAL, lng REAL)
    """

    data_dir = Path(__file__).parent / "data" if data_dir is None else Path(data_dir)
    db_path = data_dir / db_rel
    world_shp_path = data_dir / world_shp_rel

    def get_lat_lng(h3_cell):
        return h3raster.h3list_to_centroids([h3_cell])[0]

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute(f"PRAGMA table_info('{table_in}')")
    cols = {r[1] for r in cur.fetchall()}
    required = {"h3", "population"}
    missing = required - cols
    if missing:
        conn.close()
        raise ValueError(f"{table_in} missing columns: {missing}")

    # aggregation
    parent_sums = {}
    for chunk in pd.read_sql_query(
        f"SELECT h3, population FROM {table_in}",
        conn,
        chunksize=chunksize
    ):
        # map each r8 cell to its r5 parent
        chunk["h3_r5"] = chunk["h3"].map(lambda h: h3.cell_to_parent(h, 5))
        summed = chunk.groupby("h3_r5", as_index=True)["population"].sum()
        for parent, s in summed.items():
            parent_sums[parent] = parent_sums.get(parent, 0.0) + float(s)

    # build r5 df
    parents = pd.DataFrame(
        {"h3": list(parent_sums.keys()), "population": list(parent_sums.values())}
    )

    # centroid lat/lng
    parents["lat"], parents["lng"] = zip(*parents["h3"].map(get_lat_lng))

    # assign country via spatial join
    world_gdf = gpd.read_file(world_shp_path)
    parents_gdf = gpd.GeoDataFrame(
        parents,
        geometry=[Point(xy) for xy in zip(parents["lng"], parents["lat"])],
        crs=world_gdf.crs
    )
    joined = gpd.sjoin(
        parents_gdf,
        world_gdf[["geometry", "iso3"]],
        how="left",
        predicate="within"
    ).rename(columns={"iso3": "country"}).drop(columns=["index_right"])

    # write to sqlite
    cur.execute(f"DROP TABLE IF EXISTS {table_out}")
    conn.commit()

    joined[["h3", "population", "country", "lat", "lng"]].to_sql(
        table_out, conn, if_exists="replace", index=False
    )
    cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_out}_h3 ON {table_out}(h3)")
    cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_out}_country ON {table_out}(country)")
    conn.commit()
    conn.close()

    print(f"Wrote {len(joined):,} r5 cells with population, country, lat, lng to '{table_out}'")

aggregate_r8_to_r5_with_country_latlng()