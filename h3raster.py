# TODO: error handling

import h3
import geopandas
import contextily as cx
import matplotlib.pyplot as plt
import folium
from shapely.geometry import shape, mapping, Point 

def plot_df(df, column=None, ax=None):
    "Plot based on the `geometry` column of a GeoPandas dataframe"
    df = df.copy()
    df = df.to_crs(epsg=3857)

    if ax is None:
        _, ax = plt.subplots(figsize=(8,8))
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)

    df.plot(
        ax=ax,
        alpha=0.5, edgecolor='k',
        column=column, categorical=True,
        legend=True, legend_kwds={'loc': 'upper left'},
    )
    cx.add_basemap(ax, crs=df.crs, source=cx.providers.CartoDB.Positron)

def plot_shape(shape, ax=None):
    df = geopandas.GeoDataFrame({'geometry': [shape]}, crs='EPSG:4326')
    plot_df(df, ax=ax)

def plot_cells(cells, ax=None):
    shape = h3.cells_to_h3shape(cells)
    plot_shape(shape, ax=ax)

def plot_shape_and_cells(shape, res=9):
    fig, axs = plt.subplots(1,2, figsize=(10,5), sharex=True, sharey=True)
    plot_shape(shape, ax=axs[0])
    plot_cells(h3.h3shape_to_cells(shape, res), ax=axs[1])
    fig.tight_layout()

def folium_plot_cells(cells):
    """
    Plot H3 cells on a Folium map.
    Parameters:
    - cells: List of H3 cell IDs.
    Returns:
    - Folium map object with H3 cells plotted.
    """
    geojson = mapping(shape(h3.cells_to_geo(cells)))
    m = folium.Map(location=[55.7, 12.5], zoom_start=11)
    folium.GeoJson(geojson, 
                   style_function=lambda x: {
                       'fillColor': 'blue',
                       'color': 'blue',
                       'weight': 2,
                       'fillOpacity': 0.4
                   }).add_to(m)
    m.show_in_browser()

def h3list_to_centroids(cells):
    """
    Convert a list of H3 cell IDs to their centroid coordinates.
    Parameters:
    - cells: List of H3 cell IDs.
    Returns:
    - List of tuples containing latitude and longitude of each cell centroid.
    """

    return [h3.cell_to_latlng(cell) for cell in cells]

def zips_to_cells(zip_codes, resolution=8):
    """
    Convert one or more ZIP codes to H3 cell IDs at a specified resolution.
    Parameters:
    - zip_codes: A single ZIP code or a list of ZIP codes.
    - resolution: The H3 resolution (default is 8).
    Returns:
    - List of H3 cell IDs covering the areas of the ZIP codes.
    """
    if isinstance(zip_codes, (str, int)):
        zip_codes = [str(zip_codes)]
    else:
        zip_codes = [str(z) for z in zip_codes]

    zcta = geopandas.read_file('h3_raster/data/tl_2020_us_zcta510.shp')
    zcta_filtered = zcta[zcta['ZCTA5CE10'].isin(zip_codes)]

    if zcta_filtered.empty:
        raise ValueError(f"None of the provided ZIP codes were found in the dataset.")
    
    cells = []
    for polygon in zcta_filtered.geometry.values:
        cells.append(h3.geo_to_cells(polygon, res=resolution))
    flat_cells = [cell for sublist in cells for cell in sublist]

    return list(dict.fromkeys(flat_cells))

def zip_to_centroid(zip_code, resolution=8):
    """
    Convert a ZIP code to its centroid coordinates at a specified H3 resolution.
    Parameters:
    - zip_code: A single ZIP code.
    - resolution: The H3 resolution (default is 8).
    Returns:
    - Tuple containing latitude and longitude of the ZIP code centroid.
    """
    cells = zips_to_cells(zip_code, resolution)
    if not cells:
        raise ValueError(f"ZIP code {zip_code} not found.")
    
    geo = shape(h3.cells_to_geo(cells))

    return (geo.centroid.x, geo.centroid.y)

def latlng_to_cell(lat, lng, resolution=8):
    """
    Convert latitude and longitude to an H3 cell ID at a specified resolution.
    Parameters:
    - lat: Latitude of the point.
    - lng: Longitude of the point.
    - resolution: The H3 resolution (default is 8).
    Returns:
    - H3 cell ID corresponding to the given latitude and longitude.
    """

    return h3.latlng_to_cell(lat, lng, resolution)

def latlng_to_zip_centroid(lat, lng, resolution=8):
    """
    Convert latitude and longitude to the centroid of the ZIP code at a specified H3 resolution.
    Parameters:
    - lat: Latitude of the point.
    - lng: Longitude of the point.
    - resolution: The H3 resolution (default is 8).
    Returns:
    - Dict containing (lat, lng) of the ZIP code centroid.
    """
    zip_gdf = geopandas.read_file('h3_raster/data/tl_2020_us_zcta510.shp')
    zip_gdf = zip_gdf.to_crs(epsg=4326)

    point = Point(lng, lat)

    match = zip_gdf[zip_gdf.intersects(point)]

    if not match.empty:
        zip_code = match.iloc[0]['ZCTA5CE10']
    else:
        raise ValueError(f"No ZIP code found for the coordinates ({lat}, {lng}).")
    
    return {zip_code: zip_to_centroid(zip_code, resolution=resolution)}
