# TODO: error handling, function documentation

import sqlite3
import pandas as pd
import h3raster
import math
import numpy as np
import os
from datetime import datetime
import pycountry
import pytz
from timezonefinder import TimezoneFinder


def query_sqlite(resolution):
    """
    Query the SQLite database for population data at the specified H3 resolution.
    Parameters:
    - resolution: The H3 resolution (4, 5, 6, or 8).
    Returns:
    - DataFrame containing country, population, and h3 columns.
    """

    base_dir = os.path.dirname(__file__)
    db_path = os.path.join(base_dir, "data", "populations", "kontur_population_20231101_COMBINED.db")

    conn = sqlite3.connect(db_path)

    query_r4 = """
    SELECT country, population, h3 FROM hex_pops_r4
    WHERE country IN ('GBR', 'ITA', 'DEU', 'ESP', 'USA', 'DNK', 'FRA', 'PRT',
                    'AUS', 'AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'EST', 'FIN',
                    'GRC', 'HUN', 'IRL', 'LVA', 'LTU', 'LUX', 'MLT', 'NLD', 'POL',
                    'ROU', 'SVK', 'SVN', 'SWE')
    ORDER BY population DESC
    """

    query_r5 = """
    SELECT country, population, h3 FROM hex_pops_r5
    WHERE country IN ('GBR', 'ITA', 'DEU', 'ESP', 'USA', 'DNK', 'FRA', 'PRT',
                    'AUS', 'AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'EST', 'FIN',
                    'GRC', 'HUN', 'IRL', 'LVA', 'LTU', 'LUX', 'MLT', 'NLD', 'POL',
                    'ROU', 'SVK', 'SVN', 'SWE')
    ORDER BY population DESC
    """
    
    query_r6 = """
    SELECT country, population, h3 FROM hex_pops_r6
    WHERE country IN ('GBR', 'ITA', 'DEU', 'ESP', 'USA', 'DNK', 'FRA', 'PRT',
                    'AUS', 'AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'EST', 'FIN',
                    'GRC', 'HUN', 'IRL', 'LVA', 'LTU', 'LUX', 'MLT', 'NLD', 'POL',
                    'ROU', 'SVK', 'SVN', 'SWE')
    ORDER BY population DESC
    """
    query_r8 = """
    SELECT country, population, h3 FROM hex_pops_r8
    WHERE country IN ('GBR', 'ITA', 'DEU', 'ESP', 'USA', 'DNK', 'FRA', 'PRT',
                    'AUS', 'AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'EST', 'FIN',
                    'GRC', 'HUN', 'IRL', 'LVA', 'LTU', 'LUX', 'MLT', 'NLD', 'POL',
                    'ROU', 'SVK', 'SVN', 'SWE')
    ORDER BY population DESC
    """
    if resolution == 4:
        df =  pd.read_sql_query(query_r4, conn)
    elif resolution == 5:
        df =  pd.read_sql_query(query_r5, conn)
    elif resolution == 6:
        df =  pd.read_sql_query(query_r6, conn)
    elif resolution == 8:
        df =  pd.read_sql_query(query_r8, conn)
    else:
        raise ValueError("Unsupported resolution. Only 4, 5, 6, and 8 are currently supported.")
    conn.close()

    return df

def append_timezone(df):
    """
    Appends a timezone column with a utc offset float to a pandas dataframe using a the lat, lng columns.

    Parameters:
    - 'df': a pandas dataframe with 'lat' and 'lng' columns

    Returns:
    - the same pandas dataframe with a 'utc_offset' column containing the lat, lng pair's utc offset
    """
    tf = TimezoneFinder()

    WINTER_DATE = datetime(2024, 1, 1)

    def get_standard_utc_offset(lat, lng):
        tz_name = tf.timezone_at(lat=lat, lng=lng)
        if tz_name:
            tz = pytz.timezone(tz_name)
            offset_seconds = tz.utcoffset(WINTER_DATE).total_seconds()
            return offset_seconds / 3600
        return None

    df["utc_offset"] = df.apply(lambda row: get_standard_utc_offset(row["lat"], row["lng"]), axis=1)

    return df

def iso3_to_iso2(df):
    """
    Convert iso3 country codes to their corresponding iso2 formats in a pandas dataframe with a 'country' column.

    Parameters:
    - 'df': a pandas dataframe with a 'country' column.

    Returns:
    - a pandas dataframe
    """
    def iso3_to_iso2(iso3):
        try:
            return pycountry.countries.get(alpha_3=iso3).alpha_2
        except AttributeError:
            return None
    
    df["country"] = df["country"].apply(iso3_to_iso2)

    return df

def get_top_centroids(count, resolution, plot=False):
    """
    Get the top populated hexes and their centroids.
    Parameters:
    - count: Number of top populated hexes to retrieve.
    - resolution: The H3 resolution (6 or 8).
    - plot: If True, plot the hexes on a Folium map (default is False).
    Returns:
    - List of tuples containing latitude and longitude of the top count populated hexes.
    - Dictionary with country counts.
    - DataFrame with columns ['country', 'h3', 'lat', 'lng', 'population', 'utc_offset'] of selected hexes.
    """

    df = query_sqlite(resolution)

    top_count = df.sort_values(by='population', ascending=False).head(count)
    h3_list = top_count['h3'].tolist()

    country_counts_dict = top_count['country'].value_counts().to_dict()

    top_count['lat'], top_count['lng'] = zip(*h3raster.h3list_to_centroids(h3_list))

    top_count = iso3_to_iso2(append_timezone(top_count))

    if plot:
        h3raster.folium_plot_cells(h3_list)

    return h3raster.h3list_to_centroids(h3_list), country_counts_dict, top_count[['country', 'h3', 'lat', 'lng', 'population']]

def get_top_centroids_US_EUR_choose_count(US_count, EUR_count, resolution, plot=False):
    """
    Get the top populated hexes from the US and Europe.
    Parameters:
    - US_count: Number of top populated hexes to retrieve from the US.
    - EUR_count: Number of top populated hexes to retrieve from Europe.
    - resolution: The H3 resolution (6 or 8).
    - plot: If True, plot the hexes on a Folium map (default is False).
    Returns:
    - List of tuples containing latitude and longitude of the top populated hexes.
    - Dictionary with country counts.
    - DataFrame with columns ['country', 'h3', 'lat', 'lng', 'population', 'utc_offset'] of selected hexes.
    """

    df = query_sqlite(resolution)

    us_df = df[df['country'] == 'US'].nlargest(US_count, 'population')
    eur_df = df[df['country'] != 'US'].nlargest(EUR_count, 'population')

    combined_df = pd.concat([us_df, eur_df], ignore_index=True)
    
    h3_list = combined_df['h3'].tolist()

    country_counts_dict = combined_df['country'].value_counts().to_dict()

    combined_df['lat'], combined_df['lng'] = zip(*h3raster.h3list_to_centroids(combined_df['h3'].tolist()))

    combined_df = iso3_to_iso2(append_timezone(combined_df))

    if plot:
        h3raster.folium_plot_cells(h3_list)

    return h3raster.h3list_to_centroids(h3_list), country_counts_dict, combined_df[['country', 'h3', 'lat', 'lng', 'population', 'utc_offset']]

def get_top_centroids_by_strategy(total_count, resolution, method='population', 
                                   min_per_country=0, threshold=None, 
                                   urban_fraction=1.0, plot=False,
                                   fixed_country=None, fixed_count=None):
    """
    Select top populated hexes from each country using different allocation strategies.

    Parameters:
    - total_count: Total number of hexes to select.
    - resolution: The H3 resolution (4, 5, 6, or 8).
    - method: Allocation method:
        'population' - proportional to country population (default)
        'uniform'    - same count for each country
        'sqrt'       - proportional to sqrt of country population
        'log'        - proportional to log of country population
        'threshold'  - only countries above given threshold in population are considered
    - min_per_country: Minimum hexes per country (default=1).
    - threshold: Population threshold (used only if method='threshold').
    - urban_fraction: Fraction of selection per country from top-population hexes (0.0 to 1.0).
                      Remaining fraction is random within that country. (default=1.0)
    - plot: If True, plot the hexes on a Folium map. (default = False)
    - fixed_country: If provided, this country will receive a fixed number of hexes.
    - fixed_count: Number of hexes to allocate to fixed_country. Must be provided if fixed_country is set.

    Returns:
    - Tuple:
        1. List of (lat, lon) tuples of selected hexes.
        2. Dictionary {country: count_of_hexes}.
        3. DataFrame with columns ['country', 'h3', 'lat', 'lng', 'population', 'utc_offset] of selected hexes.
    """


    df = query_sqlite(resolution)

    country_pop = df.groupby('country')['population'].sum()
    countries = country_pop.index.tolist()

    if method == 'population':
        weights = country_pop
    elif method == 'uniform':
        weights = pd.Series(1, index=countries)
    elif method == 'sqrt':
        weights = np.sqrt(country_pop)
    elif method == 'log':
        weights = np.log1p(country_pop)
    elif method == 'threshold':
        if threshold is None:
            raise ValueError("Must provide 'threshold' for method='threshold'")
        country_pop = country_pop[country_pop >= threshold]
        countries = country_pop.index.tolist()
        weights = country_pop
    else:
        raise ValueError(f"Unknown method '{method}'")

    if fixed_country and fixed_count is not None:
        if fixed_country not in countries:
            raise ValueError(f"{fixed_country} not found in data")
        remaining_total = total_count - fixed_count
        other_weights = weights.drop(fixed_country)
        allocation = (other_weights / other_weights.sum() * remaining_total).apply(math.floor)
        allocation = allocation.apply(lambda x: max(min_per_country, x))
        while allocation.sum() < remaining_total:
            extra_country = ((other_weights / other_weights.sum() * remaining_total) - allocation).idxmax()
            allocation.loc[extra_country] += 1
        allocation[fixed_country] = fixed_count
    else:
        allocation = (weights / weights.sum() * total_count).apply(math.floor)
        allocation = allocation.apply(lambda x: max(min_per_country, x))
        while allocation.sum() < total_count:
            extra_country = ((weights / weights.sum() * total_count) - allocation).idxmax()
            allocation.loc[extra_country] += 1


    selected_rows = []
    used_h3 = set()

    for country, n in allocation.items():
        country_df = df[df['country'] == country].sort_values(by='population', ascending=False)
        urban_count = math.floor(n * urban_fraction)
        rural_count = n - urban_count

        chosen_rows = country_df.head(urban_count)
        if rural_count > 0:
            rural_pool = country_df.iloc[urban_count:]
            if not rural_pool.empty:
                rural_sample = rural_pool.sample(min(rural_count, len(rural_pool)))
                chosen_rows = pd.concat([chosen_rows, rural_sample])

        used_h3.update(chosen_rows['h3'])
        selected_rows.append(chosen_rows)

    final_df = pd.concat(selected_rows).copy()

    if len(final_df) < total_count:
        missing = total_count - len(final_df)
        remaining_pool = df[~df['h3'].isin(used_h3)].sort_values(by='population', ascending=False)
        if not remaining_pool.empty:
            extra_rows = remaining_pool.head(missing)
            final_df = pd.concat([final_df, extra_rows])

    final_df['lat'], final_df['lng'] = zip(*h3raster.h3list_to_centroids(final_df['h3'].tolist()))
    h3_list = final_df['h3'].tolist()

    final_df = append_timezone(final_df)


    if plot:
        h3raster.folium_plot_cells(h3_list)

    return h3raster.h3list_to_centroids(h3_list), allocation.to_dict(), final_df[['country', 'h3', 'lat', 'lng', 'population', 'utc_offset']]