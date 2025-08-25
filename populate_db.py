import sqlite3
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import h3raster
from pathlib import Path

def insert_global_data_r6():
    """ Insert global population data with country codes into a SQLite database. """

    pop_gpkg_path = "/Users/mesposito/Desktop/yext_research/h3_raster/data/populations/kontur_population_20231101_r6.gpkg"
    pop_gdf = gpd.read_file(pop_gpkg_path, layer='population')

    def get_lat_lng(h3_cell):
        return h3raster.h3list_to_centroids([h3_cell])[0]

    pop_gdf['lat_lng'] = pop_gdf['h3'].apply(get_lat_lng)
    pop_gdf['lat'] = pop_gdf['lat_lng'].apply(lambda x: x[0])
    pop_gdf['lng'] = pop_gdf['lat_lng'].apply(lambda x: x[1])
    pop_gdf.drop(columns=['lat_lng'], inplace=True)

    world_shp_path = "/Users/mesposito/Desktop/yext_research/h3_raster/data/world-administrative-boundaries/world-administrative-boundaries.shp"
    world_gdf = gpd.read_file(world_shp_path)

    pop_gdf['geometry'] = pop_gdf.apply(lambda row: Point(row['lng'], row['lat']), axis=1)
    pop_gdf = pop_gdf.set_geometry('geometry')
    pop_gdf.crs = world_gdf.crs

    pop_with_country = gpd.sjoin(pop_gdf, world_gdf[['geometry', 'iso3']], how='left', predicate='within')

    pop_with_country = pop_with_country.rename(columns={'iso3': 'country'})

    pop_with_country = pop_with_country.drop(columns=['index_right'])

    db_path = '/Users/mesposito/Desktop/yext_research/h3_raster/data/populations/kontur_population_20231101_COMBINED.db'


    conn = sqlite3.connect(db_path)

    pop_with_country.drop(columns=['geometry'], inplace=True)
    pop_with_country.to_sql('hex_pops_r6', conn, if_exists='replace', index=False)

    conn.commit()
    conn.close()

def insert_global_data_r4():
    """ Insert global population data with country codes into a SQLite database. """

    pop_gpkg_path = "/Users/mesposito/Desktop/yext_research/h3_raster/data/populations/kontur_population_20231101_r4.gpkg"
    pop_gdf = gpd.read_file(pop_gpkg_path, layer='population')

    def get_lat_lng(h3_cell):
        return h3raster.h3list_to_centroids([h3_cell])[0]

    pop_gdf['lat_lng'] = pop_gdf['h3'].apply(get_lat_lng)
    pop_gdf['lat'] = pop_gdf['lat_lng'].apply(lambda x: x[0])
    pop_gdf['lng'] = pop_gdf['lat_lng'].apply(lambda x: x[1])
    pop_gdf.drop(columns=['lat_lng'], inplace=True)

    world_shp_path = "/Users/mesposito/Desktop/yext_research/h3_raster/data/world-administrative-boundaries/world-administrative-boundaries.shp"
    world_gdf = gpd.read_file(world_shp_path)

    pop_gdf['geometry'] = pop_gdf.apply(lambda row: Point(row['lng'], row['lat']), axis=1)
    pop_gdf = pop_gdf.set_geometry('geometry')
    pop_gdf.crs = world_gdf.crs

    pop_with_country = gpd.sjoin(pop_gdf, world_gdf[['geometry', 'iso3']], how='left', predicate='within')

    pop_with_country = pop_with_country.rename(columns={'iso3': 'country'})

    pop_with_country = pop_with_country.drop(columns=['index_right'])

    db_path = '/Users/mesposito/Desktop/yext_research/h3_raster/data/populations/kontur_population_20231101_COMBINED.db'


    conn = sqlite3.connect(db_path)

    pop_with_country.drop(columns=['geometry'], inplace=True)
    pop_with_country.to_sql('hex_pops_r4', conn, if_exists='replace', index=False)

    conn.commit()
    conn.close()

def insert_global_data_r8():
    """Insert global population data with country codes into a SQLite database in chunks."""

    pop_gpkg_path = "/Users/mesposito/Desktop/yext_research/h3_raster/data/populations/kontur_population_20231101_r8.gpkg"
    pop_gdf = gpd.read_file(pop_gpkg_path, layer='population')

    def get_lat_lng(h3_cell):
        return h3raster.h3list_to_centroids([h3_cell])[0]

    pop_gdf['lat'], pop_gdf['lng'] = zip(*pop_gdf['h3'].map(get_lat_lng))

    world_shp_path = "/Users/mesposito/Desktop/yext_research/h3_raster/data/world-administrative-boundaries/world-administrative-boundaries.shp"
    world_gdf = gpd.read_file(world_shp_path)

    pop_gdf = gpd.GeoDataFrame(
        pop_gdf,
        geometry=[Point(xy) for xy in zip(pop_gdf['lng'], pop_gdf['lat'])],
        crs=world_gdf.crs
    )
    pop_with_country = gpd.sjoin(
        pop_gdf, 
        world_gdf[['geometry', 'iso3']], 
        how='left', 
        predicate='within'
    ).rename(columns={'iso3': 'country'}).drop(columns=['index_right'])

    db_path = '/Users/mesposito/Desktop/yext_research/h3_raster/data/populations/kontur_population_20231101_COMBINED.db'
    conn = sqlite3.connect(db_path)

    pop_with_country.drop(columns=['geometry'], inplace=True)

    pop_with_country.to_sql(
        'hex_pops_r8', conn, 
        if_exists='replace', 
        index=False, 
        chunksize=5000,
        method="multi"
    )

    conn.commit()
    conn.close()

def insert_by_country_data_r8():

    """
    Combine multiple GeoPackage files containing population data into a single SQLite database.
    Each GeoPackage file is expected to have a 'population' table.
    """

    gpkg_files = [
        "/Users/mesposito/Desktop/yext_research/h3_raster/data/populations/kontur_population_DEU_20231101.gpkg",
        "/Users/mesposito/Desktop/yext_research/h3_raster/data/populations/kontur_population_DNK_20231101.gpkg",
        "/Users/mesposito/Desktop/yext_research/h3_raster/data/populations/kontur_population_FRA_20231101.gpkg",
        "/Users/mesposito/Desktop/yext_research/h3_raster/data/populations/kontur_population_ITA_20231101.gpkg",
        "/Users/mesposito/Desktop/yext_research/h3_raster/data/populations/kontur_population_ESP_20231101.gpkg",
        "/Users/mesposito/Desktop/yext_research/h3_raster/data/populations/kontur_population_GBR_20231101.gpkg",
        "/Users/mesposito/Desktop/yext_research/h3_raster/data/populations/kontur_population_USA_20231101.gpkg",
        "/Users/mesposito/Desktop/yext_research/h3_raster/data/populations/kontur_population_PRT_20231101.gpkg"
    ]

    dfs = {}

    for file_path in gpkg_files:
        file_name = Path(file_path).stem
        country = "".join([c for c in file_name if c.isupper()])

        conn = sqlite3.connect(file_path)

        df = pd.read_sql_query('SELECT * FROM "population";', conn)
        df["country"] = country

        dfs[file_name] = df

        conn.close()

    all_dfs = pd.concat(dfs.values(), ignore_index=True)

    conn = sqlite3.connect('/Users/mesposito/Desktop/yext_research/h3_raster/data/populations/kontur_population_20231101_COMBINED.db')

    all_dfs.to_sql('hex_pops_r8', conn, if_exists='replace', index=False)

    conn.commit()
    conn.close()

insert_global_data_r8()