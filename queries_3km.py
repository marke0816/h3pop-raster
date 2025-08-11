import sqlite3
import pandas as pd
import h3raster
import math
import numpy as np

db_path = 'h3_raster/data/populations/kontur_population_20231101_COMBINED.db'

conn = sqlite3.connect(db_path)

query = """
SELECT country, population, h3 FROM population_with_country
WHERE country IN ('GBR', 'ITA', 'DEU', 'ESP', 'USA', 'DNK', 'FRA', 'PRT')
ORDER BY population DESC
"""

df = pd.read_sql_query(query, conn)

conn.close()

def get_top_centroids(count, plot=False):
    """
    Get the top populated hexes and their centroids.
    Parameters:
    - count: Number of top populated hexes to retrieve.
    - plot: If True, plot the hexes on a Folium map (default is False).
    Returns:
    - List of tuples containing latitude and longitude of the top count populated hexes.
    - Dictionary with country counts.
    - DataFrame with columns ['country', 'h3', 'lat', 'lng', 'population'] of selected hexes.
    """
    top_count = df.sort_values(by='population', ascending=False).head(count)
    h3_list = top_count['h3'].tolist()

    country_counts_dict = top_count['country'].value_counts().to_dict()

    top_count['lat'], top_count['lng'] = zip(*h3raster.h3list_to_centroids(h3_list))

    if plot:
        h3raster.folium_plot_cells(h3_list)

    return h3raster.h3list_to_centroids(h3_list), country_counts_dict, top_count[['country', 'h3', 'lat', 'lng', 'population']]

def get_top_centroids_US_EUR_choose_count(US_count, EUR_count, plot=False):
    """
    Get the top populated hexes from the US and Europe.
    Parameters:
    - US_count: Number of top populated hexes to retrieve from the US.
    - EUR_count: Number of top populated hexes to retrieve from Europe.
    - plot: If True, plot the hexes on a Folium map (default is False).
    Returns:
    - List of tuples containing latitude and longitude of the top populated hexes.
    - Dictionary with country counts.
    - DataFrame with columns ['country', 'h3', 'lat', 'lng', 'population'] of selected hexes.
    """
    us_df = df[df['country'] == 'US'].nlargest(US_count, 'population')
    eur_df = df[df['country'] != 'US'].nlargest(EUR_count, 'population')

    combined_df = pd.concat([us_df, eur_df], ignore_index=True)
    
    h3_list = combined_df['h3'].tolist()

    country_counts_dict = combined_df['country'].value_counts().to_dict()

    combined_df['lat'], combined_df['lng'] = zip(*h3raster.h3list_to_centroids(combined_df['h3'].tolist()))

    if plot:
        h3raster.folium_plot_cells(h3_list)

    return h3raster.h3list_to_centroids(h3_list), country_counts_dict, combined_df[['country', 'h3', 'lat', 'lng', 'population']]

def get_top_centroids_by_strategy(total_count, method='population', 
                                   min_per_country=1, threshold=None, 
                                   urban_fraction=1.0, plot=False):
    """
    Select top populated hexes from each country using different allocation strategies.

    Parameters:
    - total_count: Total number of hexes to select.
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

    Returns:
    - Tuple:
        1. List of (lat, lon) tuples of selected hexes.
        2. Dictionary {country: count_of_hexes}.
        3. DataFrame with columns ['country', 'h3', 'lat', 'lng', 'population'] of selected hexes.
    """
    country_pop = df.groupby('country')['population'].sum()
    countries = country_pop.index.tolist()

    if method == 'population':
        weights = country_pop
    elif method == 'uniform':
        weights = pd.Series(1, index=countries)
    elif method == 'sqrt':
        weights = np.sqrt(country_pop)
    elif method == 'log':
        weights = np.log1p(country_pop)  # log1p to avoid log(0)
    elif method == 'threshold':
        if threshold is None:
            raise ValueError("Must provide 'threshold' for method='threshold'")
        country_pop = country_pop[country_pop >= threshold]
        countries = country_pop.index.tolist()
        weights = country_pop
    else:
        raise ValueError(f"Unknown method '{method}'")

    allocation = (weights / weights.sum() * total_count).apply(math.floor)

    allocation = allocation.apply(lambda x: max(min_per_country, x))

    while allocation.sum() < total_count:
        extra_country = ((weights / weights.sum() * total_count) - allocation).idxmax()
        allocation.loc[extra_country] += 1

    selected_rows = []
    for country, n in allocation.items():
        country_df = df[df['country'] == country].sort_values(by='population', ascending=False)
        urban_count = math.floor(n * urban_fraction)
        rural_count = n - urban_count

        chosen_rows = country_df.head(urban_count)

        if rural_count > 0:
            rural_pool = country_df.iloc[urban_count:]
            if not rural_pool.empty:
                chosen_rows = pd.concat([chosen_rows, rural_pool.sample(min(rural_count, len(rural_pool)))])
        
        selected_rows.append(chosen_rows)

    final_df = pd.concat(selected_rows).copy()
    
    final_df['lat'], final_df['lng'] = zip(*h3raster.h3list_to_centroids(final_df['h3'].tolist()))
    h3_list = final_df['h3'].tolist()

    if plot:
        h3raster.folium_plot_cells(h3_list)

    return h3raster.h3list_to_centroids(h3_list), allocation.to_dict(), final_df[['country', 'h3', 'lat', 'lng', 'population']]