"""
Tests for shapefile masking functionality.

This tests the mask_by_shapefile() operator and shapefile_utils module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import numpy as np
import pytest
import xarray as xr

from python_cdo_wrapper import CDO
from python_cdo_wrapper.exceptions import (
    CDOError,
    CDOFileNotFoundError,
    CDOValidationError,
)

if TYPE_CHECKING:
    from pathlib import Path

# Check if geopandas is available
try:
    import geopandas as gpd
    import shapely.geometry

    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False

# Skip all tests if geopandas not available
pytestmark = pytest.mark.skipif(
    not GEOPANDAS_AVAILABLE, reason="geopandas not installed"
)


@pytest.fixture
def sample_shapefile(tmp_path: Path) -> Path:
    """
    Create a simple test shapefile with a polygon.

    Creates a polygon covering the region:
    lon: -10 to 10
    lat: -5 to 5
    """
    if not GEOPANDAS_AVAILABLE:
        pytest.skip("geopandas not available")

    # Create a simple polygon
    polygon = shapely.geometry.box(-10, -5, 10, 5)

    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame({"geometry": [polygon]}, crs="EPSG:4326")

    # Save to shapefile
    shapefile_path = tmp_path / "test_region.shp"
    gdf.to_file(shapefile_path)

    return shapefile_path


@pytest.fixture
def sample_nc_for_masking(tmp_path: Path) -> Path:
    """
    Create a NetCDF file for masking tests.

    Creates a simple file with:
    - 1 variable (temperature)
    - lat/lon grid from -20 to 20 (5-degree resolution)
    """
    lats = np.arange(-20, 21, 5)
    lons = np.arange(-20, 21, 5)

    # Create temperature data (just a gradient)
    temp = np.zeros((len(lats), len(lons)))
    for i, lat in enumerate(lats):
        for j, lon in enumerate(lons):
            temp[i, j] = 20 + lat + lon  # Simple gradient

    ds = xr.Dataset(
        {
            "tas": (
                ["lat", "lon"],
                temp,
                {"units": "degC", "long_name": "Temperature"},
            ),
        },
        coords={"lat": lats, "lon": lons},
    )

    file_path = tmp_path / "test_data_mask.nc"
    ds.to_netcdf(file_path)
    return file_path


class TestShapefileUtils:
    """Test shapefile_utils module functions."""

    def test_create_mask_from_shapefile_basic(
        self, sample_shapefile, sample_nc_for_masking
    ):
        """Test creating a mask from shapefile."""
        from python_cdo_wrapper.shapefile_utils import create_mask_from_shapefile

        mask_ds = create_mask_from_shapefile(
            shapefile_path=sample_shapefile,
            reference_nc=sample_nc_for_masking,
            lat_name="lat",
            lon_name="lon",
        )

        # Check that mask was created
        assert "mask" in mask_ds.variables
        assert mask_ds["mask"].dims == ("lat", "lon")

        # Check that mask has correct shape
        ref_ds = xr.open_dataset(sample_nc_for_masking)
        assert mask_ds["mask"].shape == ref_ds["tas"].shape

        # Check that mask contains 0 and 1
        mask_values = np.unique(mask_ds["mask"].values)
        assert set(mask_values).issubset({0, 1})

        # Check that some points are inside (1) and some outside (0)
        assert 0 in mask_values
        assert 1 in mask_values

    def test_shapefile_not_found_raises(self, sample_nc_for_masking, tmp_path):
        """Test that missing shapefile raises error."""
        from python_cdo_wrapper.shapefile_utils import create_mask_from_shapefile

        fake_shapefile = tmp_path / "nonexistent.shp"

        with pytest.raises(CDOFileNotFoundError) as exc_info:
            create_mask_from_shapefile(
                shapefile_path=fake_shapefile,
                reference_nc=sample_nc_for_masking,
            )

        assert "not found" in str(exc_info.value).lower()

    def test_reference_nc_not_found_raises(self, sample_shapefile, tmp_path):
        """Test that missing reference NC raises error."""
        from python_cdo_wrapper.shapefile_utils import create_mask_from_shapefile

        fake_nc = tmp_path / "nonexistent.nc"

        with pytest.raises(CDOFileNotFoundError) as exc_info:
            create_mask_from_shapefile(
                shapefile_path=sample_shapefile,
                reference_nc=fake_nc,
            )

        assert "not found" in str(exc_info.value).lower()

    def test_invalid_lat_name_raises(self, sample_shapefile, sample_nc_for_masking):
        """Test that invalid lat name raises validation error."""
        from python_cdo_wrapper.shapefile_utils import create_mask_from_shapefile

        with pytest.raises(CDOValidationError) as exc_info:
            create_mask_from_shapefile(
                shapefile_path=sample_shapefile,
                reference_nc=sample_nc_for_masking,
                lat_name="latitude",  # Wrong name
                lon_name="lon",
            )

        assert "latitude" in str(exc_info.value).lower()

    def test_invalid_lon_name_raises(self, sample_shapefile, sample_nc_for_masking):
        """Test that invalid lon name raises validation error."""
        from python_cdo_wrapper.shapefile_utils import create_mask_from_shapefile

        with pytest.raises(CDOValidationError) as exc_info:
            create_mask_from_shapefile(
                shapefile_path=sample_shapefile,
                reference_nc=sample_nc_for_masking,
                lat_name="lat",
                lon_name="longitude",  # Wrong name
            )

        assert "longitude" in str(exc_info.value).lower()


class TestMaskByShapefileOperator:
    """Test mask_by_shapefile() query operator."""

    def test_mask_by_shapefile_command(self, sample_shapefile, sample_nc_for_masking):
        """Test that mask_by_shapefile generates correct command structure."""
        from python_cdo_wrapper.query import CDOQuery

        # Create query directly without CDO instance (for unit testing)
        q = CDOQuery(input_file=sample_nc_for_masking)
        q = q.mask_by_shapefile(sample_shapefile)

        # Check that ifthen operator is present
        cmd = q.get_command()
        assert "-ifthen" in cmd

        # Check that query has temp files tracked
        assert hasattr(q, "_temp_files")
        assert len(q._temp_files) > 0

    def test_mask_by_shapefile_shapefile_not_found_raises(
        self, sample_nc_for_masking, tmp_path
    ):
        """Test that missing shapefile raises error."""
        from python_cdo_wrapper.query import CDOQuery

        fake_shapefile = tmp_path / "nonexistent.shp"

        q = CDOQuery(input_file=sample_nc_for_masking)
        with pytest.raises(CDOFileNotFoundError):
            q.mask_by_shapefile(fake_shapefile)

    def test_mask_by_shapefile_no_input_raises(self, sample_shapefile):
        """Test that mask_by_shapefile without input raises error."""
        from python_cdo_wrapper.query import CDOQuery

        # Create query without input
        q = CDOQuery(input_file=None)

        with pytest.raises(CDOError) as exc_info:
            q.mask_by_shapefile(sample_shapefile)

        assert "no input file" in str(exc_info.value).lower()

    @pytest.mark.integration
    def test_mask_by_shapefile_execution(self, sample_shapefile, sample_nc_for_masking):
        """Test full execution of mask_by_shapefile."""
        cdo = CDO()

        # Execute masking
        result = (
            cdo.query(sample_nc_for_masking)
            .mask_by_shapefile(sample_shapefile)
            .compute()
        )

        # Check result is xarray Dataset
        assert isinstance(result, xr.Dataset)
        assert "tas" in result.variables

        # Check that some values are NaN (outside polygon)
        assert np.isnan(result["tas"].values).any()

        # Check that some values are not NaN (inside polygon)
        assert (~np.isnan(result["tas"].values)).any()

    @pytest.mark.integration
    def test_mask_by_shapefile_temp_file_cleanup(
        self, sample_shapefile, sample_nc_for_masking
    ):
        """Test that temporary mask files are cleaned up after execution."""
        cdo = CDO()

        # Create query and capture temp file path
        query = cdo.query(sample_nc_for_masking).mask_by_shapefile(sample_shapefile)

        # Verify temp file was created and tracked
        assert hasattr(query, "_temp_files")
        assert len(query._temp_files) == 1
        temp_file = query._temp_files[0]
        assert temp_file.exists(), "Temp file should exist after mask creation"

        # Execute the query
        result = query.compute()

        # Verify result is valid
        assert isinstance(result, xr.Dataset)

        # Verify temp file was cleaned up
        assert not temp_file.exists(), "Temp file should be deleted after compute()"

    @pytest.mark.integration
    def test_mask_by_shapefile_chaining(self, sample_shapefile, sample_nc_for_masking):
        """Test chaining mask_by_shapefile with other operators."""
        cdo = CDO()

        # Chain with field_mean
        result = (
            cdo.query(sample_nc_for_masking)
            .mask_by_shapefile(sample_shapefile)
            .field_mean()
            .compute()
        )

        # Check result
        assert isinstance(result, xr.Dataset)
        assert "tas" in result.variables

    @pytest.mark.integration
    def test_mask_by_shapefile_custom_coord_names(self, sample_shapefile, tmp_path):
        """Test mask_by_shapefile with custom coordinate names."""
        # Create NC file with custom coordinate names
        lats = np.arange(-20, 21, 5)
        lons = np.arange(-20, 21, 5)
        temp = np.random.rand(len(lats), len(lons)) * 30

        ds = xr.Dataset(
            {"tas": (["latitude", "longitude"], temp)},
            coords={"latitude": lats, "longitude": lons},
        )

        nc_path = tmp_path / "custom_coords.nc"
        ds.to_netcdf(nc_path)

        # Test masking with custom names
        cdo = CDO()
        result = (
            cdo.query(nc_path)
            .mask_by_shapefile(
                sample_shapefile, lat_name="latitude", lon_name="longitude"
            )
            .compute()
        )

        assert isinstance(result, xr.Dataset)
        assert "tas" in result.variables


class TestMaskByShapefileWithoutGeopandas:
    """Test behavior when geopandas is not installed."""

    def test_mask_by_shapefile_no_geopandas_raises(
        self, sample_nc_for_masking, tmp_path
    ):
        """Test that mask_by_shapefile raises error without geopandas."""
        cdo = CDO()

        # Create a fake shapefile path
        fake_shapefile = tmp_path / "fake.shp"
        fake_shapefile.touch()

        # Mock builtins.__import__ to simulate geopandas not being installed
        import builtins

        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name in ("geopandas", "shapely"):
                raise ImportError(f"No module named '{name}'")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            with pytest.raises(CDOError) as exc_info:
                cdo.query(sample_nc_for_masking).mask_by_shapefile(
                    fake_shapefile
                ).compute()

            assert "geopandas" in str(exc_info.value).lower()
            assert "pip install" in str(exc_info.value).lower()
