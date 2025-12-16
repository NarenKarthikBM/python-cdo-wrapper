# Shapefile Masking Feature

## Overview

The `mask_by_shapefile()` operator provides a complete pipeline for clipping NetCDF data to shapefile polygon extents in a single line of code.

## Installation

```bash
# Install with shapefile support
pip install python-cdo-wrapper[shapefiles]
```

This installs the optional `geopandas` and `shapely` dependencies required for shapefile handling.

## Quick Start

```python
from python_cdo_wrapper import CDO

cdo = CDO()

# Mask global data to a specific region
regional_data = cdo.query("global_temperature.nc").mask_by_shapefile(
    "amazon_basin.shp"
).compute()
```

## Features

### ✅ Complete Automated Pipeline

The operator handles the entire workflow automatically:
1. Load shapefile and extract polygon geometries
2. Create binary mask using NumPy point-in-polygon tests
3. Save mask to temporary NetCDF file
4. Apply mask using CDO's `ifthen` operator
5. Clean up temporary files after execution

### ✅ Chainable with Other Operators

```python
# Calculate yearly mean for masked region
yearly_regional = (
    cdo.query("daily_data.nc")
    .mask_by_shapefile("west_africa.shp")
    .year_mean()
    .compute()
)

# Multiple operations after masking
timeseries = (
    cdo.query("global_precip.nc")
    .mask_by_shapefile("sahel.shp")
    .field_mean()
    .year_mean()
    .compute()
)
```

### ✅ Flexible Grid Support

Works with both regular (1D lat/lon) and curvilinear (2D) grids:

```python
# Regular grid (1D coordinates)
masked = cdo.query("regular_grid.nc").mask_by_shapefile("region.shp").compute()

# Curvilinear grid (2D coordinates)
masked = cdo.query("curvilinear_grid.nc").mask_by_shapefile("region.shp").compute()
```

### ✅ Custom Coordinate Names

```python
# Handle non-standard coordinate names
masked = cdo.query("data.nc").mask_by_shapefile(
    "region.shp",
    lat_name="latitude",
    lon_name="longitude"
).compute()
```

### ✅ Automatic CRS Handling

Shapefiles are automatically reprojected to WGS84 (EPSG:4326) if needed:

```python
# Shapefile in any CRS - automatically handled
masked = cdo.query("data.nc").mask_by_shapefile(
    "region_utm.shp"  # Will be reprojected to WGS84
).compute()
```

### ✅ Multi-Polygon Support

```python
# Works with complex multi-polygon shapefiles
island_data = cdo.query("pacific_data.nc").mask_by_shapefile(
    "pacific_islands.shp"  # Multiple island polygons
).compute()
```

## Advanced Usage

### Create Mask Separately

For advanced users who need to reuse masks:

```python
from python_cdo_wrapper import create_mask_from_shapefile

# Create and save mask
mask_ds = create_mask_from_shapefile(
    shapefile_path="region.shp",
    reference_nc="data.nc",
    lat_name="lat",
    lon_name="lon"
)
mask_ds.to_netcdf("region_mask.nc")
mask_ds.close()

# Reuse the saved mask
masked1 = cdo.query("data1.nc").select_mask("region_mask.nc").compute()
masked2 = cdo.query("data2.nc").select_mask("region_mask.nc").compute()
```

## Method Signature

```python
def mask_by_shapefile(
    self,
    shapefile_path: str | Path,
    lat_name: str = "lat",
    lon_name: str = "lon",
) -> CDOQuery
```

**Parameters:**
- `shapefile_path`: Path to ESRI shapefile (.shp)
- `lat_name`: Latitude coordinate name (default: "lat")
- `lon_name`: Longitude coordinate name (default: "lon")

**Returns:**
- `CDOQuery`: New query with masking applied

**Raises:**
- `CDOError`: If geopandas not installed or input file not set
- `CDOFileNotFoundError`: If shapefile doesn't exist
- `CDOValidationError`: If coordinates not found

## Implementation Details

### Masking Approach

- Uses **NumPy point-in-polygon** tests for mask creation (pure Python, no GDAL required)
- Uses **CDO ifthen** operator for applying mask (standard CDO approach)
- Values outside polygons are set to **NaN** (standard climate data convention)
- Temporary files are **automatically cleaned up** after compute()

### Grid Alignment

The mask grid is automatically aligned to the data grid, ensuring cell-by-cell correspondence.

### Performance Considerations

- Mask creation is done in Python (one-time cost per query)
- Large grids may take longer for point-in-polygon tests
- Masks can be pre-created and saved for reuse (see Advanced Usage)

## Error Handling

```python
# Missing geopandas
try:
    masked = cdo.query("data.nc").mask_by_shapefile("region.shp").compute()
except CDOError as e:
    if "geopandas" in str(e).lower():
        print("Install geopandas: pip install python-cdo-wrapper[shapefiles]")

# Missing shapefile
try:
    masked = cdo.query("data.nc").mask_by_shapefile("missing.shp").compute()
except CDOFileNotFoundError as e:
    print(f"Shapefile not found: {e.file_path}")

# Invalid coordinates
try:
    masked = cdo.query("data.nc").mask_by_shapefile(
        "region.shp",
        lat_name="wrong_name"
    ).compute()
except CDOValidationError as e:
    print(f"Coordinate '{e.parameter}' not found")
```

## Examples

See `examples/shapefile_masking_example.py` for comprehensive examples including:
- Simple masking
- Chaining with other operators
- Custom coordinate names
- Multi-polygon shapefiles
- Advanced mask reuse
- Error handling

## Requirements

- **CDO**: Climate Data Operators (>= 1.9.8 recommended)
- **geopandas**: >= 0.10.0 (for shapefile handling)
- **shapely**: >= 2.0.0 (for geometry operations)
- **xarray**: >= 2023.1.0 (already required by python-cdo-wrapper)
- **numpy**: >= 1.22.0 (already required by python-cdo-wrapper)

## Limitations

- Shapefile CRS must be geographic (lat/lon based) or will be reprojected
- Large grids with complex polygons may be slow due to point-in-polygon tests
- Requires CDO to be installed and available in PATH

## See Also

- [CDO Documentation](https://code.mpimet.mpg.de/projects/cdo/)
- [GeoPandas Documentation](https://geopandas.org/)
- [Shapely Documentation](https://shapely.readthedocs.io/)
