"""
Example: Masking NetCDF data with shapefiles

This example demonstrates how to use the mask_by_shapefile() operator
to clip climate data to specific geographic regions defined by shapefiles.

Requirements:
    pip install python-cdo-wrapper[shapefiles]

This installs geopandas and shapely for shapefile handling.
"""

from python_cdo_wrapper import CDO, create_mask_from_shapefile

# Initialize CDO
cdo = CDO()

# ============================================================
# Example 1: Simple masking to a region
# ============================================================
# Mask global temperature data to a specific region
masked_data = cdo.query("global_temperature.nc").mask_by_shapefile(
    "amazon_basin.shp"
).compute()

print("Masked data shape:", masked_data.dims)
print("Variables:", list(masked_data.variables))

# ============================================================
# Example 2: Chain with other operators
# ============================================================
# Calculate yearly mean for masked region
yearly_regional = (
    cdo.query("daily_temperature.nc")
    .mask_by_shapefile("west_africa.shp")
    .year_mean()
    .compute()
)

print("Yearly regional mean shape:", yearly_regional.dims)

# ============================================================
# Example 3: Multiple operations after masking
# ============================================================
# Mask → Calculate field mean → Extract time series
regional_timeseries = (
    cdo.query("global_precipitation.nc")
    .mask_by_shapefile("sahel.shp")
    .field_mean()
    .compute()
)

print("Regional time series shape:", regional_timeseries.dims)

# ============================================================
# Example 4: Custom coordinate names
# ============================================================
# Some NetCDF files use different coordinate names
masked_custom = cdo.query("data_custom_coords.nc").mask_by_shapefile(
    "region.shp",
    lat_name="latitude",  # Default is "lat"
    lon_name="longitude",  # Default is "lon"
).compute()

# ============================================================
# Example 5: Save to file
# ============================================================
# Mask and save directly to output file
output_path = (
    cdo.query("global_data.nc")
    .mask_by_shapefile("european_union.shp")
    .to_file("eu_data.nc")
)

print(f"Saved masked data to: {output_path}")

# ============================================================
# Example 6: Advanced - Create mask separately
# ============================================================
# For advanced users: create mask file separately for reuse
# Note: create_mask_from_shapefile was imported at the top

# Create mask dataset
mask_ds = create_mask_from_shapefile(
    shapefile_path="india.shp",
    reference_nc="asia_data.nc",
    lat_name="lat",
    lon_name="lon",
)

# Save for later use
mask_ds.to_netcdf("india_mask.nc")
mask_ds.close()

# Use the saved mask with select_mask
masked_with_saved = cdo.query("asia_data.nc").select_mask("india_mask.nc").compute()

# ============================================================
# Example 7: Multi-polygon shapefiles
# ============================================================
# Works automatically with multi-polygon shapefiles
# e.g., a shapefile with multiple countries or islands
island_nations = cdo.query("pacific_data.nc").mask_by_shapefile(
    "pacific_islands.shp"  # Shapefile with multiple island polygons
).compute()

# ============================================================
# Notes:
# ============================================================
# 1. Shapefile CRS is automatically reprojected to WGS84 (EPSG:4326) if needed
# 2. Works with both 1D (regular) and 2D (curvilinear) grids
# 3. Temporary mask files are automatically cleaned up after compute()
# 4. Values outside the shapefile region are set to NaN
# 5. Grid alignment is handled automatically
# 6. Supports complex regional boundaries with multiple polygons

print("\nAll examples completed successfully!")
