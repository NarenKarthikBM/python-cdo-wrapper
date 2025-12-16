"""
Unit tests for python_cdo_wrapper.core module.

These tests cover the core functionality of the CDO wrapper,
including command detection, error handling, and basic operations.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from python_cdo_wrapper.core import (
    CDO_TEXT_COMMANDS,
    CDOError,
    _is_text_command,
    _validate_input_files,
    cdo,
)


class TestCDOTextCommands:
    """Tests for CDO_TEXT_COMMANDS constant."""

    def test_text_commands_is_frozenset(self):
        """Verify CDO_TEXT_COMMANDS is immutable."""
        assert isinstance(CDO_TEXT_COMMANDS, frozenset)

    def test_text_commands_contains_common_operators(self):
        """Check that common text operators are included."""
        common_text_ops = [
            "sinfo",
            "info",
            "griddes",
            "showdate",
            "showname",
            "ntime",
            "nvars",
            "tinfo",
            "vlist",
        ]
        for op in common_text_ops:
            assert op in CDO_TEXT_COMMANDS, f"{op} should be in CDO_TEXT_COMMANDS"

    def test_text_commands_excludes_data_operators(self):
        """Check that data operators are not included."""
        data_ops = [
            "yearmean",
            "monmean",
            "selname",
            "remapbil",
            "fldmean",
            "add",
            "sub",
            "mul",
        ]
        for op in data_ops:
            assert op not in CDO_TEXT_COMMANDS, (
                f"{op} should NOT be in CDO_TEXT_COMMANDS"
            )


class TestIsTextCommand:
    """Tests for _is_text_command function."""

    @pytest.mark.parametrize(
        "cmd,expected",
        [
            ("sinfo data.nc", True),
            ("info data.nc", True),
            ("griddes data.nc", True),
            ("showdate data.nc", True),
            ("ntime data.nc", True),
            ("yearmean data.nc", False),
            ("selname,temp data.nc", False),
            ("-selname,temp data.nc", False),
            ("remapbil,grid data.nc", False),
            ("fldmean data.nc", False),
        ],
    )
    def test_is_text_command_detection(self, cmd: str, expected: bool):
        """Test correct detection of text vs data commands."""
        assert _is_text_command(cmd) is expected

    def test_is_text_command_case_insensitive(self):
        """Test that detection is case-insensitive."""
        assert _is_text_command("SINFO data.nc") is True
        assert _is_text_command("Sinfo data.nc") is True

    def test_is_text_command_with_dash_prefix(self):
        """Test commands with leading dash."""
        assert _is_text_command("-sinfo data.nc") is True
        assert _is_text_command("-yearmean data.nc") is False

    def test_is_text_command_empty_string(self):
        """Test empty command string."""
        assert _is_text_command("") is False

    def test_is_text_command_whitespace_handling(self):
        """Test handling of extra whitespace."""
        assert _is_text_command("  sinfo   data.nc  ") is True


class TestValidateInputFiles:
    """Tests for _validate_input_files function."""

    def test_validate_existing_file(self, sample_nc_file: Path):
        """Test validation passes for existing file."""
        # Should not raise
        _validate_input_files(f"sinfo {sample_nc_file}")

    def test_validate_missing_file(self, tmp_path: Path):
        """Test validation raises for missing file."""
        missing_file = tmp_path / "nonexistent.nc"
        with pytest.raises(FileNotFoundError, match="Input file not found"):
            _validate_input_files(f"sinfo {missing_file}")

    def test_validate_multiple_files(self, sample_nc_file: Path, tmp_path: Path):
        """Test validation checks all files."""
        missing = tmp_path / "missing.nc"
        with pytest.raises(FileNotFoundError):
            _validate_input_files(f"cat {sample_nc_file} {missing}")

    def test_validate_non_nc_files_ignored(self):
        """Test that non-NetCDF arguments are ignored."""
        # Should not raise for operators without file extensions
        _validate_input_files("yearmean -selname,temp")


class TestCDOError:
    """Tests for CDOError exception class."""

    def test_error_message_format(self):
        """Test error message contains all relevant info."""
        error = CDOError(
            command="cdo invalid input.nc",
            returncode=1,
            stdout="",
            stderr="Error: invalid operator",
        )

        assert "invalid" in str(error)
        assert "return code 1" in str(error)
        assert "Error: invalid operator" in str(error)

    def test_error_attributes(self):
        """Test error attributes are accessible."""
        error = CDOError(
            command="cdo test",
            returncode=2,
            stdout="out",
            stderr="err",
        )

        assert error.command == "cdo test"
        assert error.returncode == 2
        assert error.stdout == "out"
        assert error.stderr == "err"


class TestCDOFunction:
    """Tests for the main cdo() function."""

    def test_cdo_text_command_returns_string(self):
        """Test that text commands return string."""
        with patch("python_cdo_wrapper.core.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Grid Info Output",
                stderr="",
            )

            result = cdo("sinfo test.nc", check_files=False)

            assert isinstance(result, str)
            assert result == "Grid Info Output"

    def test_cdo_data_command_returns_tuple(self, sample_nc_file: Path):
        """Test that data commands return tuple with Dataset."""
        with patch("python_cdo_wrapper.core.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="",
                stderr="Processing complete",
            )

            # Mock temp file to use our sample file
            with patch(
                "python_cdo_wrapper.core.tempfile.NamedTemporaryFile"
            ) as mock_tmp:
                mock_tmp.return_value.__enter__.return_value.name = str(sample_nc_file)

                # Prevent file deletion since we're using a real file
                with patch("pathlib.Path.unlink"):
                    result = cdo(f"yearmean {sample_nc_file}", check_files=False)

            assert isinstance(result, tuple)
            assert len(result) == 2

    def test_cdo_raises_error_on_failure(self):
        """Test CDOError is raised on non-zero return code."""
        with patch("python_cdo_wrapper.core.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="Error: invalid operator",
            )

            with pytest.raises(CDOError) as exc_info:
                cdo("invalid_command test.nc", check_files=False)

            assert exc_info.value.returncode == 1

    def test_cdo_debug_mode(self, capsys):
        """Test debug mode prints information."""
        with patch("python_cdo_wrapper.core.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="info output",
                stderr="",
            )

            cdo("sinfo test.nc", debug=True, check_files=False)

            captured = capsys.readouterr()
            assert "CDO Command" in captured.out
            assert "Return code: 0" in captured.out

    def test_cdo_file_validation_disabled(self):
        """Test check_files=False skips validation."""
        with patch("python_cdo_wrapper.core.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="output",
                stderr="",
            )

            # Should not raise even with missing file
            result = cdo("sinfo nonexistent.nc", check_files=False)
            assert result == "output"

    def test_cdo_return_xr_false(self):
        """Test return_xr=False returns None for dataset."""
        with patch("python_cdo_wrapper.core.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="",
                stderr="log output",
            )

            with (
                patch(
                    "python_cdo_wrapper.core.tempfile.NamedTemporaryFile"
                ) as mock_tmp,
                patch("pathlib.Path.exists", return_value=True),
                patch("pathlib.Path.unlink"),
            ):
                mock_tmp.return_value.__enter__.return_value.name = "/tmp/test.nc"
                result = cdo("yearmean test.nc", return_xr=False, check_files=False)

            assert result[0] is None
            assert result[1] == "log output"

    def test_cdo_custom_output_file(self):
        """Test custom output file path is used."""
        with patch("python_cdo_wrapper.core.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="",
                stderr="",
            )

            with patch("xarray.open_dataset") as mock_xr:
                mock_xr.return_value = MagicMock()

                cdo(
                    "yearmean test.nc",
                    output_file="/custom/output.nc",
                    check_files=False,
                )

            # Check command includes custom output path
            call_args = mock_run.call_args
            assert "/custom/output.nc" in call_args[0][0]


class TestCDOFunctionIntegration:
    """Integration tests requiring CDO to be installed."""

    @pytest.mark.integration
    def test_cdo_sinfo_real(self, sample_nc_file: Path):
        """Test sinfo with real CDO."""
        result = cdo(f"sinfo {sample_nc_file}")

        assert isinstance(result, str)
        assert "temperature" in result.lower() or "grid" in result.lower()

    @pytest.mark.integration
    def test_cdo_showname_real(self, sample_nc_file: Path):
        """Test showname with real CDO."""
        result = cdo(f"showname {sample_nc_file}")

        assert isinstance(result, str)
        assert "tas" in result

    @pytest.mark.integration
    def test_cdo_nvar_real(self, sample_nc_file: Path):
        """Test nvar with real CDO (returns number of variables as text)."""
        result = cdo(f"-nvar {sample_nc_file}")

        assert isinstance(result, str)
        # Our sample has 1 variable (temperature)
        assert "1" in result

    @pytest.mark.integration
    def test_cdo_fldmean_real(self, sample_nc_file: Path):
        """Test fldmean with real CDO returns dataset."""
        ds, _ = cdo(f"fldmean {sample_nc_file}")

        import xarray as xr

        assert isinstance(ds, xr.Dataset)
        assert "tas" in ds.data_vars

    @pytest.mark.integration
    def test_cdo_invalid_command_raises(self, sample_nc_file: Path):
        """Test invalid CDO command raises CDOError."""
        with pytest.raises(CDOError):
            cdo(f"totally_invalid_operator {sample_nc_file}")

    @pytest.mark.integration
    def test_cdo_missing_input_raises(self, tmp_path: Path):
        """Test missing input file raises FileNotFoundError."""
        missing = tmp_path / "does_not_exist.nc"

        with pytest.raises(FileNotFoundError, match="Input file not found"):
            cdo(f"sinfo {missing}")
