import sqlite3
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import h3raster

def insert_global_data():
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

    conn.close()
