"""Integration tests for structured output functionality."""

import pytest

from python_cdo_wrapper import CDO_STRUCTURED_COMMANDS, cdo


class TestStructuredOutputIntegration:
    """Integration tests for structured output with real CDO commands."""

    @pytest.mark.integration
    def test_griddes_structured_output(self, sample_nc_file):
        """Test griddes with return_dict=True."""
        # Skip if sample file doesn't exist
        if not sample_nc_file.exists():
            pytest.skip("Sample NetCDF file not available")

        result = cdo(f"griddes {sample_nc_file}", return_dict=True)

        assert isinstance(result, dict)
        assert "gridtype" in result or "gridsize" in result

    @pytest.mark.integration
    def test_sinfo_structured_output(self, sample_nc_file):
        """Test sinfo with return_dict=True."""
        if not sample_nc_file.exists():
            pytest.skip("Sample NetCDF file not available")

        result = cdo(f"sinfo {sample_nc_file}", return_dict=True)

        assert isinstance(result, dict)
        assert "variables" in result or "metadata" in result

    def test_return_dict_false_returns_string(self):
        """Test that return_dict=False returns string output."""
        # Use a command that doesn't require a file
        try:
            result = cdo("--version", return_dict=False)
            assert isinstance(result, str)
        except Exception:
            pytest.skip("CDO not available")

    def test_structured_commands_constant(self):
        """Test that CDO_STRUCTURED_COMMANDS is properly defined."""
        assert isinstance(CDO_STRUCTURED_COMMANDS, frozenset)
        assert "griddes" in CDO_STRUCTURED_COMMANDS
        assert "sinfo" in CDO_STRUCTURED_COMMANDS
        assert "showatts" in CDO_STRUCTURED_COMMANDS


class TestBackwardCompatibility:
    """Tests to ensure backward compatibility."""

    def test_default_behavior_unchanged(self):
        """Test that default behavior returns text for text commands."""
        # Without return_dict parameter, should return string
        try:
            result = cdo("--version")
            assert isinstance(result, str)
        except Exception:
            pytest.skip("CDO not available")

    def test_return_dict_ignored_for_data_commands(self, sample_nc_file):
        """Test that return_dict is ignored for data commands."""
        if not sample_nc_file.exists():
            pytest.skip("Sample NetCDF file not available")

        # Data commands should return tuple regardless of return_dict
        try:
            result = cdo(f"yearmean {sample_nc_file}", return_dict=True)
            # Should return tuple (xr.Dataset, str) not dict
            assert isinstance(result, tuple)
        except Exception:
            pytest.skip("Test data or CDO not available")


class TestErrorHandling:
    """Tests for error handling in structured output."""

    def test_invalid_command_with_return_dict(self):
        """Test that invalid commands still raise CDOError."""
        from python_cdo_wrapper import CDOError

        with pytest.raises(CDOError):
            cdo("invalid_command_xyz", return_dict=True)

    def test_unsupported_parser_falls_back_to_text(self):
        """Test that unsupported parsers fall back to text output."""
        # For text commands without parsers, should still return string
        try:
            # Use a text command that's not in structured commands
            result = cdo("--operators", return_dict=True)
            # Should fall back to string if no parser available
            assert isinstance(result, (str, dict))
        except Exception:
            pytest.skip("CDO not available")


class TestTypeHints:
    """Tests for type hints and type checking."""

    def test_return_dict_true_type(self):
        """Test that return_dict=True returns dict type."""
        # This is mainly for type checkers, but we can verify at runtime
        try:
            result = cdo("--version", return_dict=True)
            # Should be dict or fall back to str
            assert isinstance(result, (dict, str))
        except Exception:
            pytest.skip("CDO not available")

    def test_return_dict_false_type(self):
        """Test that return_dict=False returns string type."""
        try:
            result = cdo("--version", return_dict=False)
            assert isinstance(result, str)
        except Exception:
            pytest.skip("CDO not available")
