"""Tests for utility functions."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from python_cdo_wrapper.utils import (
    check_cdo_available,
    cleanup_temp_file,
    create_temp_file,
    format_cdo_command,
    get_cdo_version,
)


class TestCreateTempFile:
    """Test create_temp_file function."""

    def test_creates_file_with_default_suffix(self):
        """Test creating temp file with default .nc suffix."""
        temp_path = create_temp_file()
        assert temp_path.exists()
        assert temp_path.suffix == ".nc"
        temp_path.unlink()  # Cleanup

    def test_creates_file_with_custom_suffix(self):
        """Test creating temp file with custom suffix."""
        temp_path = create_temp_file(suffix=".grb")
        assert temp_path.exists()
        assert temp_path.suffix == ".grb"
        temp_path.unlink()

    def test_creates_file_with_custom_prefix(self):
        """Test creating temp file with custom prefix."""
        temp_path = create_temp_file(prefix="test_")
        assert temp_path.exists()
        assert "test_" in temp_path.name
        temp_path.unlink()

    def test_creates_file_in_custom_dir(self, tmp_path):
        """Test creating temp file in custom directory."""
        temp_path = create_temp_file(dir=tmp_path)
        assert temp_path.exists()
        assert temp_path.parent == tmp_path
        temp_path.unlink()


class TestCleanupTempFile:
    """Test cleanup_temp_file function."""

    def test_removes_existing_file(self, tmp_path):
        """Test removing existing file."""
        test_file = tmp_path / "test.nc"
        test_file.touch()
        assert test_file.exists()

        cleanup_temp_file(test_file)
        assert not test_file.exists()

    def test_handles_missing_file(self, tmp_path):
        """Test that cleanup doesn't fail for missing file."""
        test_file = tmp_path / "missing.nc"
        cleanup_temp_file(test_file)  # Should not raise


class TestCheckCDOAvailable:
    """Test check_cdo_available function."""

    def test_returns_true_when_cdo_available(self):
        """Test returns True when CDO is available."""
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("python_cdo_wrapper.utils.subprocess.run", return_value=mock_result):
            assert check_cdo_available() is True

    def test_returns_false_when_cdo_not_available(self):
        """Test returns False when CDO is not available."""
        with patch(
            "python_cdo_wrapper.utils.subprocess.run",
            side_effect=FileNotFoundError,
        ):
            assert check_cdo_available() is False

    def test_returns_false_on_subprocess_error(self):
        """Test returns False on subprocess error."""
        mock_result = MagicMock()
        mock_result.returncode = 1

        with patch("python_cdo_wrapper.utils.subprocess.run", return_value=mock_result):
            assert check_cdo_available() is False


class TestGetCDOVersion:
    """Test get_cdo_version function."""

    def test_returns_version_string(self):
        """Test returns CDO version string."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Climate Data Operators version 2.0.5\nExtra info"

        with patch("python_cdo_wrapper.utils.subprocess.run", return_value=mock_result):
            version = get_cdo_version()
            assert "Climate Data Operators version 2.0.5" in version

    def test_raises_on_cdo_not_available(self):
        """Test raises RuntimeError when CDO not available."""
        with (
            patch(
                "python_cdo_wrapper.utils.subprocess.run",
                side_effect=FileNotFoundError,
            ),
            pytest.raises(RuntimeError, match="CDO is not available"),
        ):
            get_cdo_version()


class TestFormatCDOCommand:
    """Test format_cdo_command function."""

    def test_format_operator_with_args(self):
        """Test formatting operator with arguments."""
        cmd = format_cdo_command("selname", "tas", "pr")
        assert cmd == "-selname,tas,pr"

    def test_format_operator_with_numeric_args(self):
        """Test formatting operator with numeric arguments."""
        cmd = format_cdo_command("sellonlatbox", 0, 360, -90, 90)
        assert cmd == "-sellonlatbox,0,360,-90,90"

    def test_format_operator_without_args(self):
        """Test formatting operator without arguments."""
        cmd = format_cdo_command("yearmean")
        assert cmd == "-yearmean"

    def test_format_operator_with_mixed_args(self):
        """Test formatting operator with mixed argument types."""
        cmd = format_cdo_command("sellevel", 1000, 850, 500)
        assert cmd == "-sellevel,1000,850,500"
