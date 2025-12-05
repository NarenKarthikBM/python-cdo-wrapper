"""
Tests for the package-level API.
"""

import python_cdo_wrapper


class TestPackageAPI:
    """Tests for package-level exports and attributes."""

    def test_version_exists(self):
        """Test __version__ is defined."""
        assert hasattr(python_cdo_wrapper, "__version__")
        assert isinstance(python_cdo_wrapper.__version__, str)

    def test_version_format(self):
        """Test version follows semver format."""
        version = python_cdo_wrapper.__version__
        parts = version.split(".")
        assert len(parts) >= 2, "Version should have at least major.minor"

    def test_cdo_function_exported(self):
        """Test cdo function is accessible from package."""
        assert hasattr(python_cdo_wrapper, "cdo")
        assert callable(python_cdo_wrapper.cdo)

    def test_text_commands_exported(self):
        """Test CDO_TEXT_COMMANDS is accessible from package."""
        assert hasattr(python_cdo_wrapper, "CDO_TEXT_COMMANDS")
        assert isinstance(python_cdo_wrapper.CDO_TEXT_COMMANDS, frozenset)

    def test_all_exports(self):
        """Test __all__ contains expected exports."""
        expected = ["cdo", "CDO_TEXT_COMMANDS", "__version__"]
        for item in expected:
            assert item in python_cdo_wrapper.__all__

    def test_import_from_package(self):
        """Test imports work correctly."""
        from python_cdo_wrapper import CDO_TEXT_COMMANDS, cdo

        assert callable(cdo)
        assert isinstance(CDO_TEXT_COMMANDS, frozenset)
