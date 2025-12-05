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
            "temperature": (
                ["time", "lat", "lon"],
                temp,
                {
                    "units": "K",
                    "long_name": "Temperature",
                },
            ),
        },
        coords={
            "time": times,
            "lat": lats,
            "lon": lons,
        },
        attrs={
            "title": "Test dataset",
            "history": "Created by pytest",
        },
    )

    filepath = tmp_path / "test_data.nc"
    ds.to_netcdf(filepath)

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
            "temperature": (
                ["time", "lat", "lon"],
                temp,
                {
                    "units": "K",
                    "long_name": "Temperature",
                },
            ),
        },
        coords={
            "time": times,
            "lat": ("lat", lats, {"units": "degrees_north"}),
            "lon": ("lon", lons, {"units": "degrees_east"}),
        },
    )

    filepath = tmp_path / "test_data_time.nc"
    ds.to_netcdf(filepath)

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
