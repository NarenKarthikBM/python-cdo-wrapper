"""Parameter validation utilities for CDO operators."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .exceptions import CDOFileNotFoundError, CDOValidationError

if TYPE_CHECKING:
    from collections.abc import Sequence


def validate_file_exists(file_path: str | Path, _parameter_name: str = "input") -> Path:
    """
    Validate that a file exists.

    Args:
        file_path: Path to the file to check.
        parameter_name: Name of the parameter (for error messages).

    Returns:
        Path object of the validated file.

    Raises:
        CDOFileNotFoundError: If file does not exist.

    Example:
        >>> validate_file_exists("data.nc")
        PosixPath('data.nc')
        >>> validate_file_exists("missing.nc")
        CDOFileNotFoundError: File not found: missing.nc
    """
    path = Path(file_path)
    if not path.exists():
        raise CDOFileNotFoundError(
            f"File not found: {file_path}",
            file_path=str(file_path),
        )
    return path


def validate_latitude(lat: float, parameter_name: str = "latitude") -> None:
    """
    Validate latitude is in valid range [-90, 90].

    Args:
        lat: Latitude value to validate.
        parameter_name: Name of the parameter (for error messages).

    Raises:
        CDOValidationError: If latitude is out of range.

    Example:
        >>> validate_latitude(45.0)  # OK
        >>> validate_latitude(100.0)
        CDOValidationError: Latitude must be between -90 and 90
    """
    if not -90 <= lat <= 90:
        raise CDOValidationError(
            f"Latitude must be between -90 and 90, got {lat}",
            parameter=parameter_name,
            value=lat,
            expected="-90 <= lat <= 90",
        )


def validate_longitude(lon: float, parameter_name: str = "longitude") -> None:
    """
    Validate longitude is in valid range [-180, 360].

    Args:
        lon: Longitude value to validate.
        parameter_name: Name of the parameter (for error messages).

    Raises:
        CDOValidationError: If longitude is out of range.

    Example:
        >>> validate_longitude(180.0)  # OK
        >>> validate_longitude(400.0)
        CDOValidationError: Longitude must be between -180 and 360
    """
    if not -180 <= lon <= 360:
        raise CDOValidationError(
            f"Longitude must be between -180 and 360, got {lon}",
            parameter=parameter_name,
            value=lon,
            expected="-180 <= lon <= 360",
        )


def validate_non_empty(
    values: Sequence[object],
    parameter_name: str = "values",
) -> None:
    """
    Validate that a sequence is not empty.

    Args:
        values: Sequence to validate.
        parameter_name: Name of the parameter (for error messages).

    Raises:
        CDOValidationError: If sequence is empty.

    Example:
        >>> validate_non_empty(["tas", "pr"])  # OK
        >>> validate_non_empty([])
        CDOValidationError: At least one value required
    """
    if not values:
        raise CDOValidationError(
            f"At least one value required for {parameter_name}",
            parameter=parameter_name,
            value=values,
            expected="Non-empty sequence",
        )


def validate_positive(value: float | int, parameter_name: str = "value") -> None:
    """
    Validate that a number is positive.

    Args:
        value: Number to validate.
        parameter_name: Name of the parameter (for error messages).

    Raises:
        CDOValidationError: If value is not positive.

    Example:
        >>> validate_positive(5)  # OK
        >>> validate_positive(-1)
        CDOValidationError: Value must be positive
    """
    if value <= 0:
        raise CDOValidationError(
            f"{parameter_name} must be positive, got {value}",
            parameter=parameter_name,
            value=value,
            expected="value > 0",
        )


def validate_range(
    value: float | int,
    min_val: float | int,
    max_val: float | int,
    parameter_name: str = "value",
) -> None:
    """
    Validate that a number is within a range.

    Args:
        value: Number to validate.
        min_val: Minimum allowed value (inclusive).
        max_val: Maximum allowed value (inclusive).
        parameter_name: Name of the parameter (for error messages).

    Raises:
        CDOValidationError: If value is out of range.

    Example:
        >>> validate_range(50, 0, 100)  # OK
        >>> validate_range(150, 0, 100)
        CDOValidationError: value must be between 0 and 100
    """
    if not min_val <= value <= max_val:
        raise CDOValidationError(
            f"{parameter_name} must be between {min_val} and {max_val}, got {value}",
            parameter=parameter_name,
            value=value,
            expected=f"{min_val} <= {parameter_name} <= {max_val}",
        )
