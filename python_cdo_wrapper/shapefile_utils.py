"""
Utility functions for shapefile-based masking operations.

This module provides helper functions for creating binary masks from
ESRI shapefiles for use in NetCDF masking operations.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import xarray as xr

from .exceptions import CDOError, CDOFileNotFoundError, CDOValidationError


def create_mask_from_shapefile(
    shapefile_path: str | Path,
    reference_nc: str | Path,
    lat_name: str = "lat",
    lon_name: str = "lon",
) -> xr.Dataset:
    """
    Create a binary mask NetCDF from a shapefile.

    This function loads a shapefile, reads the grid from a reference NetCDF file,
    and creates a binary mask (1 inside polygons, 0 outside) using NumPy
    point-in-polygon tests.

    Args:
        shapefile_path: Path to ESRI shapefile (.shp)
        reference_nc: Path to reference NetCDF file for grid coordinates
        lat_name: Name of latitude coordinate in NetCDF (default: "lat")
        lon_name: Name of longitude coordinate in NetCDF (default: "lon")

    Returns:
        xr.Dataset: Binary mask dataset with same grid as reference

    Raises:
        CDOFileNotFoundError: If shapefile or reference file doesn't exist
        CDOValidationError: If required coordinates not found
        CDOError: If geopandas is not installed or other processing errors

    Example:
        >>> mask_ds = create_mask_from_shapefile(
        ...     "region.shp",
        ...     "data.nc",
        ...     lat_name="latitude",
        ...     lon_name="longitude"
        ... )
    """
    # Validate files exist
    shapefile_path = Path(shapefile_path)
    reference_nc = Path(reference_nc)

    if not shapefile_path.exists():
        raise CDOFileNotFoundError(
            message=f"Shapefile not found: {shapefile_path}",
            file_path=str(shapefile_path),
        )

    if not reference_nc.exists():
        raise CDOFileNotFoundError(
            message=f"Reference NetCDF file not found: {reference_nc}",
            file_path=str(reference_nc),
        )

    # Check if geopandas is available
    try:
        import geopandas as gpd
        import shapely.geometry
        from shapely.prepared import prep
    except ImportError as e:
        raise CDOError(
            "geopandas is required for shapefile masking. "
            "Install with: pip install python-cdo-wrapper[shapefiles]"
        ) from e

    # Load shapefile
    try:
        gdf = gpd.read_file(shapefile_path)
    except Exception as e:
        raise CDOError(f"Failed to read shapefile: {e}") from e

    # Ensure CRS is WGS84 (EPSG:4326)
    if gdf.crs is not None and not gdf.crs.equals("EPSG:4326"):
        gdf = gdf.to_crs("EPSG:4326")

    # Load reference NetCDF to get grid
    try:
        ds = xr.open_dataset(reference_nc)
    except Exception as e:
        raise CDOError(f"Failed to open reference NetCDF: {e}") from e

    # Get lat/lon coordinates
    if lat_name not in ds.coords and lat_name not in ds.dims:
        raise CDOValidationError(
            message=f"Latitude coordinate '{lat_name}' not found in NetCDF",
            parameter="lat_name",
            value=lat_name,
            expected=f"One of: {list(ds.coords.keys())}",
        )

    if lon_name not in ds.coords and lon_name not in ds.dims:
        raise CDOValidationError(
            message=f"Longitude coordinate '{lon_name}' not found in NetCDF",
            parameter="lon_name",
            value=lon_name,
            expected=f"One of: {list(ds.coords.keys())}",
        )

    # Extract lat/lon arrays
    lat = ds[lat_name].values
    lon = ds[lon_name].values

    # Handle 1D vs 2D coordinates
    if lat.ndim == 1 and lon.ndim == 1:
        # Regular lat/lon grid
        lon_2d, lat_2d = np.meshgrid(lon, lat)
    elif lat.ndim == 2 and lon.ndim == 2:
        # Curvilinear grid
        lat_2d = lat
        lon_2d = lon
    else:
        raise CDOValidationError(
            message="Invalid coordinate dimensions",
            parameter="coordinates",
            value=f"lat: {lat.shape}, lon: {lon.shape}",
            expected="Both 1D or both 2D",
        )

    # Create binary mask
    mask = np.zeros(lat_2d.shape, dtype=np.int16)

    # Combine all geometries into one for efficiency
    try:
        # Use union_all() if available (geopandas >= 0.13), else unary_union
        if hasattr(gdf.geometry, "union_all"):
            combined_geom = gdf.geometry.union_all()
        else:
            combined_geom = gdf.geometry.unary_union
        prepared_geom = prep(combined_geom)
    except Exception as e:
        raise CDOError(f"Failed to process geometries: {e}") from e

    # Perform point-in-polygon tests
    # Note: This nested loop can be slow for large grids (e.g., global 0.5° = ~260k points).
    # For better performance on very large grids, consider pre-creating and reusing masks.
    for i in range(lat_2d.shape[0]):
        for j in range(lat_2d.shape[1]):
            point = shapely.geometry.Point(lon_2d[i, j], lat_2d[i, j])
            if prepared_geom.contains(point):
                mask[i, j] = 1

    # Create xarray Dataset for mask
    if lat.ndim == 1 and lon.ndim == 1:
        # 1D coordinates
        mask_da = xr.DataArray(
            mask,
            coords={lat_name: lat, lon_name: lon},
            dims=[lat_name, lon_name],
            name="mask",
        )
    else:
        # 2D coordinates
        mask_da = xr.DataArray(
            mask,
            coords={
                lat_name: ([lat_name, lon_name], lat_2d),
                lon_name: ([lat_name, lon_name], lon_2d),
            },
            dims=[lat_name, lon_name],
            name="mask",
        )

    mask_ds = mask_da.to_dataset()

    # Add metadata
    mask_ds["mask"].attrs["long_name"] = "Binary mask from shapefile"
    mask_ds["mask"].attrs["units"] = "1"
    mask_ds["mask"].attrs["comment"] = "1=inside polygon, 0=outside polygon"

    ds.close()

    return mask_ds
