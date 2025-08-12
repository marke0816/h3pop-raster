import pandas as pd
import sqlite3
from pathlib import Path

def create_combined_population_db():

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
