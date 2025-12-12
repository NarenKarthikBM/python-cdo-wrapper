"""Tests for exception hierarchy (v1.0.0+ API)."""

from __future__ import annotations

import pytest

from python_cdo_wrapper.exceptions import (
    CDOError,
    CDOExecutionError,
    CDOFileNotFoundError,
    CDOParseError,
    CDOValidationError,
)


class TestExceptionHierarchy:
    """Test exception class hierarchy."""

    def test_all_exceptions_inherit_from_cdo_error(self):
        """Test that all custom exceptions inherit from CDOError."""
        assert issubclass(CDOExecutionError, CDOError)
        assert issubclass(CDOValidationError, CDOError)
        assert issubclass(CDOFileNotFoundError, CDOError)
        assert issubclass(CDOParseError, CDOError)

    def test_cdo_error_is_exception(self):
        """Test that CDOError inherits from Exception."""
        assert issubclass(CDOError, Exception)


class TestCDOExecutionError:
    """Test CDOExecutionError."""

    def test_initialization(self):
        """Test CDOExecutionError initialization."""
        err = CDOExecutionError(
            message="Command failed",
            command="cdo sinfo test.nc",
            returncode=1,
            stdout="",
            stderr="File not found",
        )

        assert err.command == "cdo sinfo test.nc"
        assert err.returncode == 1
        assert err.stdout == ""
        assert err.stderr == "File not found"

    def test_string_representation(self):
        """Test CDOExecutionError string representation."""
        err = CDOExecutionError(
            message="Command failed",
            command="cdo sinfo test.nc",
            returncode=1,
            stdout="",
            stderr="File not found",
        )

        err_str = str(err)
        assert "Command failed" in err_str
        assert "cdo sinfo test.nc" in err_str
        assert "Return code: 1" in err_str
        assert "File not found" in err_str

    def test_can_be_raised_and_caught(self):
        """Test that exception can be raised and caught."""
        with pytest.raises(CDOExecutionError) as exc_info:
            raise CDOExecutionError(
                message="Test error",
                command="test",
                returncode=1,
                stdout="",
                stderr="error",
            )

        assert exc_info.value.command == "test"


class TestCDOValidationError:
    """Test CDOValidationError."""

    def test_initialization(self):
        """Test CDOValidationError initialization."""
        err = CDOValidationError(
            message="Invalid parameter",
            parameter="latitude",
            value=100,
            expected="Value between -90 and 90",
        )

        assert err.parameter == "latitude"
        assert err.value == 100
        assert err.expected == "Value between -90 and 90"

    def test_string_representation(self):
        """Test CDOValidationError string representation."""
        err = CDOValidationError(
            message="Invalid parameter",
            parameter="latitude",
            value=100,
            expected="Value between -90 and 90",
        )

        err_str = str(err)
        assert "Invalid parameter" in err_str
        assert "latitude" in err_str
        assert "100" in err_str
        assert "Value between -90 and 90" in err_str


class TestCDOFileNotFoundError:
    """Test CDOFileNotFoundError."""

    def test_initialization(self):
        """Test CDOFileNotFoundError initialization."""
        err = CDOFileNotFoundError(
            message="File not found",
            file_path="/path/to/missing.nc",
        )

        assert err.file_path == "/path/to/missing.nc"

    def test_string_representation(self):
        """Test CDOFileNotFoundError string representation."""
        err = CDOFileNotFoundError(
            message="File not found",
            file_path="/path/to/missing.nc",
        )

        err_str = str(err)
        assert "File not found" in err_str
        assert "/path/to/missing.nc" in err_str


class TestCDOParseError:
    """Test CDOParseError."""

    def test_initialization(self):
        """Test CDOParseError initialization."""
        err = CDOParseError(
            message="Failed to parse output",
            raw_output="Invalid output format",
        )

        assert err.raw_output == "Invalid output format"

    def test_string_representation(self):
        """Test CDOParseError string representation."""
        err = CDOParseError(
            message="Failed to parse output",
            raw_output="Invalid output format",
        )

        err_str = str(err)
        assert "Failed to parse output" in err_str
        assert "Invalid output format" in err_str

    def test_string_representation_truncates_long_output(self):
        """Test that long output is truncated in string representation."""
        long_output = "x" * 500
        err = CDOParseError(
            message="Failed to parse",
            raw_output=long_output,
        )

        err_str = str(err)
        # Should be truncated to 200 chars + "..."
        assert len(err_str) < len(long_output)
        assert "..." in err_str
