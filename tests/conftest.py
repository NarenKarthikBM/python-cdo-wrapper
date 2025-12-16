"""
Pytest configuration and fixtures for python-cdo-wrapper tests.
"""

import subprocess
from pathlib import Path

import numpy as np
import pytest
import xarray as xr


def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as requiring CDO installation"
    )
    config.addinivalue_line("markers", "slow: mark test as slow running")


def is_cdo_installed() -> bool:
    """Check if CDO is installed on the system."""
    try:
        result = subprocess.run(
            ["cdo", "-V"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


# Skip integration tests if CDO is not installed
def pytest_collection_modifyitems(config, items):  # noqa: ARG001
    """Skip integration tests if CDO is not available."""
    if not is_cdo_installed():
        skip_integration = pytest.mark.skip(reason="CDO not installed")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)


@pytest.fixture
def sample_nc_file(tmp_path: Path) -> Path:
    """
    Create a minimal NetCDF file for testing.

    Creates a simple NetCDF file with:
    - 1 variable (temperature)
    - 3 time steps
    - 4x4 lat/lon grid

    Returns:
        Path to the temporary NetCDF file.
    """
    # Create sample data
    times = np.arange(3)
    lats = np.linspace(-90, 90, 4)
    lons = np.linspace(-180, 180, 4)

    # Random temperature data
    np.random.seed(42)
    temp = np.random.rand(3, 4, 4) * 30 + 270  # 270-300 K

    ds = xr.Dataset(
        {
            "tas": (  # Changed from "temperature" to standard CF name "tas"
                ["time", "lat", "lon"],
                temp,
                {
                    "units": "K",
                    "long_name": "Near-Surface Air Temperature",
                    "standard_name": "air_temperature",
                    "code": 167,  # GRIB parameter code for 2m temperature
                },
            ),
        },
        coords={
            "time": ("time", times, {"axis": "T", "standard_name": "time"}),
            "lat": (
                "lat",
                lats,
                {
                    "axis": "Y",
                    "units": "degrees_north",
                    "standard_name": "latitude",
                },
            ),
            "lon": (
                "lon",
                lons,
                {
                    "axis": "X",
                    "units": "degrees_east",
                    "standard_name": "longitude",
                },
            ),
        },
        attrs={
            "title": "Test dataset",
            "history": "Created by pytest",
            "Conventions": "CF-1.8",
        },
    )

    # Define encoding for proper CDO compatibility
    encoding = {
        "tas": {
            "dtype": "float32",
            "zlib": False,
            "_FillValue": None,
        },
        "time": {"dtype": "float64"},
        "lat": {"dtype": "float32"},
        "lon": {"dtype": "float32"},
    }

    filepath = tmp_path / "test_data.nc"
    ds.to_netcdf(filepath, format="NETCDF4_CLASSIC", encoding=encoding)

    return filepath


@pytest.fixture
def sample_nc_file_with_time(tmp_path: Path) -> Path:
    """
    Create a NetCDF file with proper datetime coordinates.

    Creates a NetCDF file suitable for CDO time operations with:
    - 12 monthly time steps
    - Proper datetime coordinates

    Returns:
        Path to the temporary NetCDF file.
    """
    import pandas as pd

    # Create sample data with proper dates
    times = pd.date_range("2020-01-01", periods=12, freq="MS")
    lats = np.linspace(-90, 90, 4)
    lons = np.linspace(-180, 180, 4)

    # Random temperature data
    np.random.seed(42)
    temp = np.random.rand(12, 4, 4) * 30 + 270

    ds = xr.Dataset(
        {
            "tas": (  # Changed from "temperature" to standard CF name "tas"
                ["time", "lat", "lon"],
                temp,
                {
                    "units": "K",
                    "long_name": "Near-Surface Air Temperature",
                    "standard_name": "air_temperature",
                    "code": 167,  # GRIB parameter code for 2m temperature
                },
            ),
        },
        coords={
            "time": ("time", times, {"axis": "T", "standard_name": "time"}),
            "lat": (
                "lat",
                lats,
                {
                    "axis": "Y",
                    "units": "degrees_north",
                    "standard_name": "latitude",
                },
            ),
            "lon": (
                "lon",
                lons,
                {
                    "axis": "X",
                    "units": "degrees_east",
                    "standard_name": "longitude",
                },
            ),
        },
        attrs={
            "title": "Test dataset with time",
            "Conventions": "CF-1.8",
        },
    )

    # Define encoding for proper CDO compatibility
    encoding = {
        "tas": {
            "dtype": "float32",
            "zlib": False,
            "_FillValue": None,
        },
        "time": {"dtype": "float64", "units": "days since 1850-01-01"},
        "lat": {"dtype": "float32"},
        "lon": {"dtype": "float32"},
    }

    filepath = tmp_path / "test_data_time.nc"
    ds.to_netcdf(filepath, format="NETCDF4_CLASSIC", encoding=encoding)

    return filepath


@pytest.fixture
def temp_output_file(tmp_path: Path) -> Path:
    """
    Provide a path for temporary output file.

    Returns:
        Path object for a temporary output file.
    """
    return tmp_path / "output.nc"


@pytest.fixture
def mock_cdo_result():
    """
    Factory fixture to create mock subprocess results.

    Returns:
        A factory function to create mock CompletedProcess objects.
    """

    def _create_result(
        returncode: int = 0,
        stdout: str = "",
        stderr: str = "",
    ):
        class MockResult:
            def __init__(self):
                self.returncode = returncode
                self.stdout = stdout
                self.stderr = stderr

        return MockResult()

    return _create_result


# v1.0.0+ fixtures


@pytest.fixture
def cdo_instance():
    """
    Create a CDO instance for testing (v1.0.0+ API).

    Returns:
        CDO instance if CDO is available, otherwise skips the test.
    """
    if not is_cdo_installed():
        pytest.skip("CDO not installed")

    from python_cdo_wrapper import CDO

    return CDO()


@pytest.fixture
def multi_var_nc_file(tmp_path: Path) -> Path:
    """
    Create a NetCDF file with multiple variables for testing.

    Creates a NetCDF file with:
    - 3 variables (tas, pr, psl)
    - 12 monthly time steps
    - 4x4 lat/lon grid

    Returns:
        Path to the temporary NetCDF file.
    """
    import pandas as pd

    # Create sample data with proper dates
    times = pd.date_range("2020-01-01", periods=12, freq="MS")
    lats = np.linspace(-90, 90, 4)
    lons = np.linspace(-180, 180, 4)

    # Random data for multiple variables
    np.random.seed(42)
    tas = np.random.rand(12, 4, 4) * 30 + 270  # Temperature (K)
    pr = np.random.rand(12, 4, 4) * 10  # Precipitation (mm/day)
    psl = np.random.rand(12, 4, 4) * 5000 + 98000  # Sea level pressure (Pa)

    ds = xr.Dataset(
        {
            "tas": (
                ["time", "lat", "lon"],
                tas,
                {
                    "units": "K",
                    "long_name": "Near-Surface Air Temperature",
                    "standard_name": "air_temperature",
                    "code": 167,  # GRIB parameter code for 2m temperature
                },
            ),
            "pr": (
                ["time", "lat", "lon"],
                pr,
                {
                    "units": "mm day-1",
                    "long_name": "Precipitation",
                    "standard_name": "precipitation_flux",
                    "code": 228,  # GRIB parameter code for precipitation
                },
            ),
            "psl": (
                ["time", "lat", "lon"],
                psl,
                {
                    "units": "Pa",
                    "long_name": "Sea Level Pressure",
                    "standard_name": "air_pressure_at_mean_sea_level",
                    "code": 151,  # GRIB parameter code for pressure
                },
            ),
        },
        coords={
            "time": ("time", times, {"axis": "T", "standard_name": "time"}),
            "lat": (
                "lat",
                lats,
                {
                    "axis": "Y",
                    "units": "degrees_north",
                    "standard_name": "latitude",
                },
            ),
            "lon": (
                "lon",
                lons,
                {
                    "axis": "X",
                    "units": "degrees_east",
                    "standard_name": "longitude",
                },
            ),
        },
        attrs={
            "title": "Multi-variable test dataset",
            "institution": "Test Institute",
            "source": "pytest fixture",
            "Conventions": "CF-1.8",
        },
    )

    # Define encoding for proper CDO compatibility
    encoding = {
        "tas": {
            "dtype": "float32",
            "zlib": False,
            "_FillValue": None,
        },
        "pr": {
            "dtype": "float32",
            "zlib": False,
            "_FillValue": None,
        },
        "psl": {
            "dtype": "float32",
            "zlib": False,
            "_FillValue": None,
        },
        "time": {"dtype": "float64", "units": "days since 1850-01-01"},
        "lat": {"dtype": "float32"},
        "lon": {"dtype": "float32"},
    }

    filepath = tmp_path / "test_multi_var.nc"
    ds.to_netcdf(filepath, format="NETCDF4_CLASSIC", encoding=encoding)

    return filepath


@pytest.fixture
def sample_3d_nc_file(tmp_path: Path) -> Path:
    """
    Create a 3D NetCDF file with vertical levels for testing.

    Creates a NetCDF file with:
    - 1 variable with vertical levels
    - 3 time steps
    - 3 vertical levels
    - 4x4 lat/lon grid

    Returns:
        Path to the temporary NetCDF file.
    """
    times = np.arange(3)
    levels = np.array([1000.0, 850.0, 500.0])  # Pressure levels in hPa
    lats = np.linspace(-90, 90, 4)
    lons = np.linspace(-180, 180, 4)

    # Random temperature data
    np.random.seed(42)
    temp = np.random.rand(3, 3, 4, 4) * 30 + 250  # Temperature varies with height

    ds = xr.Dataset(
        {
            "ta": (
                ["time", "level", "lat", "lon"],
                temp,
                {
                    "units": "K",
                    "long_name": "Air Temperature",
                    "standard_name": "air_temperature",
                },
            ),
        },
        coords={
            "time": times,
            "level": ("level", levels, {"units": "hPa", "positive": "down"}),
            "lat": ("lat", lats, {"units": "degrees_north"}),
            "lon": ("lon", lons, {"units": "degrees_east"}),
        },
        attrs={
            "title": "3D test dataset with vertical levels",
        },
    )

    filepath = tmp_path / "test_3d.nc"
    ds.to_netcdf(filepath)

    return filepath
