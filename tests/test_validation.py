"""Tests for validation utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from python_cdo_wrapper.exceptions import CDOFileNotFoundError, CDOValidationError
from python_cdo_wrapper.validation import (
    validate_file_exists,
    validate_latitude,
    validate_longitude,
    validate_non_empty,
    validate_positive,
    validate_range,
)


class TestValidateFileExists:
    """Test validate_file_exists function."""

    def test_valid_file(self, tmp_path):
        """Test with existing file."""
        test_file = tmp_path / "test.nc"
        test_file.touch()

        result = validate_file_exists(test_file)
        assert isinstance(result, Path)
        assert result.exists()

    def test_missing_file(self, tmp_path):
        """Test with missing file."""
        test_file = tmp_path / "missing.nc"

        with pytest.raises(CDOFileNotFoundError) as exc_info:
            validate_file_exists(test_file)

        assert "missing.nc" in exc_info.value.file_path


class TestValidateLatitude:
    """Test validate_latitude function."""

    @pytest.mark.parametrize("lat", [-90, -45, 0, 45, 90])
    def test_valid_latitudes(self, lat):
        """Test with valid latitude values."""
        validate_latitude(lat)  # Should not raise

    @pytest.mark.parametrize("lat", [-100, -91, 91, 100, 180])
    def test_invalid_latitudes(self, lat):
        """Test with invalid latitude values."""
        with pytest.raises(CDOValidationError) as exc_info:
            validate_latitude(lat)

        assert exc_info.value.value == lat
        assert "-90" in exc_info.value.expected
        assert "90" in exc_info.value.expected


class TestValidateLongitude:
    """Test validate_longitude function."""

    @pytest.mark.parametrize("lon", [-180, -90, 0, 90, 180, 270, 360])
    def test_valid_longitudes(self, lon):
        """Test with valid longitude values."""
        validate_longitude(lon)  # Should not raise

    @pytest.mark.parametrize("lon", [-200, -181, 361, 400])
    def test_invalid_longitudes(self, lon):
        """Test with invalid longitude values."""
        with pytest.raises(CDOValidationError) as exc_info:
            validate_longitude(lon)

        assert exc_info.value.value == lon


class TestValidateNonEmpty:
    """Test validate_non_empty function."""

    def test_non_empty_list(self):
        """Test with non-empty sequence."""
        validate_non_empty(["a", "b", "c"])  # Should not raise

    def test_empty_list(self):
        """Test with empty sequence."""
        with pytest.raises(CDOValidationError) as exc_info:
            validate_non_empty([])

        assert "Non-empty" in exc_info.value.expected

    def test_non_empty_tuple(self):
        """Test with non-empty tuple."""
        validate_non_empty(("a", "b"))  # Should not raise


class TestValidatePositive:
    """Test validate_positive function."""

    @pytest.mark.parametrize("value", [1, 5, 100, 0.1, 1e-10])
    def test_positive_values(self, value):
        """Test with positive values."""
        validate_positive(value)  # Should not raise

    @pytest.mark.parametrize("value", [0, -1, -100, -0.1])
    def test_non_positive_values(self, value):
        """Test with non-positive values."""
        with pytest.raises(CDOValidationError) as exc_info:
            validate_positive(value)

        assert exc_info.value.value == value


class TestValidateRange:
    """Test validate_range function."""

    def test_value_in_range(self):
        """Test with value in valid range."""
        validate_range(50, 0, 100)  # Should not raise
        validate_range(0, 0, 100)  # Boundary
        validate_range(100, 0, 100)  # Boundary

    def test_value_out_of_range(self):
        """Test with value out of range."""
        with pytest.raises(CDOValidationError) as exc_info:
            validate_range(150, 0, 100)

        assert exc_info.value.value == 150

        with pytest.raises(CDOValidationError):
            validate_range(-10, 0, 100)
