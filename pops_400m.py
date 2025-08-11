import pandas as pd
import sqlite3
from pathlib import Path

def create_combined_population_db():
    """
    Combine multiple GeoPackage files containing population data into a single SQLite database.
    Each GeoPackage file is expected to have a 'population' table.
    """

    gpkg_files = [
        "h3_raster/data/populations/kontur_population_DE_20231101.gpkg",
        "h3_raster/data/populations/kontur_population_DK_20231101.gpkg",
        "h3_raster/data/populations/kontur_population_FR_20231101.gpkg",
        "h3_raster/data/populations/kontur_population_IT_20231101.gpkg",
        "h3_raster/data/populations/kontur_population_ES_20231101.gpkg",
        "h3_raster/data/populations/kontur_population_GB_20231101.gpkg",
        "h3_raster/data/populations/kontur_population_US_20231101.gpkg",
        "h3_raster/data/populations/kontur_population_PT_20231101.gpkg"
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

    conn = sqlite3.connect('h3_raster/data/populations/kontur_population_20231101_COMBINED.db')

    all_dfs.to_sql('hex_pops', conn, if_exists='replace', index=False)

    conn.commit()
    conn.close()