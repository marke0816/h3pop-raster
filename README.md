# H3 Centroid Selection CLI tool

This tool provides a command-line interface for selecting the top populated H3 hexagons by country using different allocation strategies. It wraps the get_top_centroids_by_strategy function into a flexible CLI so you can run sampling experiments directly from the terminal.

## Usage

Run the CLI tool with 

```
python samplecells.py <total_count> <resolution> [options]
```

### Required Arguments

- total_count – total number of hexagons to select.

- resolution – H3 resolution (4, 5, 6, or 8).

### Options

- --method {population,uniform,sqrt,log,threshold}
  - Allocation strategy (default: population).

- --min-per-country N
  - Minimum hexes per country (default: 0).

- --threshold N
  - Population threshold for the threshold method.

- --urban-fraction F
  - Fraction of hexes chosen from top-population cells (0.0–1.0, default: 1.0).

- --plot
  
  - Plot selected hexes on an interactive Folium map.

- --fixed-country CODE

  - ISO country code to fix allocation for.

- --fixed-count N

  - Number of hexes to allocate to the fixed country (requires --fixed-country).

- --output-csv PATH
  - Save the resulting DataFrame to a CSV file at the specified path.

### Examples

Select 3,000 hexes at resolution 6 using the default population allocation:
```
python samplecells.py 3000 6 --method population
```

Fix 50 hexes for Denmark (DNK), with the rest allocated proportionally:
```
python samplecells.py 3000 6 --fixed-country DNK --fixed-count 50
```
Use the threshold method to only consider countries with population ≥ 1,000,000:
```
python samplecells.py 1000 8 --method threshold --threshold 1000000
```
Plot results on an interactive map:
```
python samplecells.py 500 6 --plot
```
Save results to a CSV file:
```
python samplecells.py 3000 6 --output-csv top_hexes.csv
```
Combine plotting and CSV output:
```
python samplecells.py 1000 8 --plot --output-csv results.csv
```

### Output

The CLI prints:

A dictionary with allocation counts by country.

A preview of the DataFrame of selected hexes (country, H3 index, lat, lng, population, UTC offset).

If `--output-csv` is provided, the full DataFrame is saved to the specified CSV file.