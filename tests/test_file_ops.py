"""Tests for CDO file operations."""

import pytest

from python_cdo_wrapper import CDO


@pytest.mark.integration
class TestCDOFileOperations:
    """Test multi-file operations."""

    def test_merge(self, sample_nc_file, tmp_path):
        """Test merge operation."""
        cdo = CDO()
        f1 = tmp_path / "f1.nc"
        f2 = tmp_path / "f2.nc"

        # Create two files with different variables
        cdo.query(sample_nc_file).set_name("var1").to_file(f1)
        cdo.query(sample_nc_file).set_name("var2").to_file(f2)

        ds = cdo.merge(f1, f2)
        assert "var1" in ds.data_vars
        assert "var2" in ds.data_vars

    def test_cat(self, sample_nc_file, tmp_path):
        """Test cat operation."""
        cdo = CDO()
        f1 = tmp_path / "f1.nc"
        f2 = tmp_path / "f2.nc"

        # Create input files
        cdo.copy(sample_nc_file, output=f1)
        cdo.copy(sample_nc_file, output=f2)

        ds = cdo.cat(f1, f2)
        # Original has 3 steps. Cat 2 files -> 6 steps.
        assert ds.sizes["time"] == 6

    def test_copy(self, sample_nc_file, tmp_path):
        """Test copy operation."""
        cdo = CDO()
        out = tmp_path / "copy.nc"
        ds = cdo.copy(sample_nc_file, output=out)
        assert out.exists()
        assert "tas" in ds.data_vars


@pytest.mark.integration
class TestCDOSplitOperations:
    """Test split operations."""

    def test_split_name(self, sample_nc_file, tmp_path):
        """Test split_name."""
        cdo = CDO()
        # Create file with 2 vars
        f_multi = tmp_path / "multi.nc"
        f1 = tmp_path / "f1.nc"
        f2 = tmp_path / "f2.nc"
        cdo.query(sample_nc_file).set_name("var1").to_file(f1)
        cdo.query(sample_nc_file).set_name("var2").to_file(f2)
        cdo.merge(f1, f2, output=f_multi)

        prefix = str(tmp_path / "split_var_")
        files = cdo.split_name(f_multi, prefix)

        assert len(files) >= 2
        # Check if files exist
        assert any("var1" in f.name for f in files)
        assert any("var2" in f.name for f in files)

    def test_split_timestep(self, sample_nc_file, tmp_path):
        """Test split_timestep."""
        cdo = CDO()
        # sample has 3 steps. Split by 1.
        prefix = str(tmp_path / "step_")
        files = cdo.split_timestep(sample_nc_file, 1, prefix)

        assert len(files) == 3
