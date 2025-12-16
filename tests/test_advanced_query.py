from pathlib import Path

import pytest

from python_cdo_wrapper import CDO
from python_cdo_wrapper.query import CDOQueryTemplate


@pytest.mark.integration
class TestAdvancedQuery:
    """Tests for advanced query methods and templates."""

    def test_first(self, sample_nc_file):
        cdo = CDO()
        ds = cdo.query(sample_nc_file).first()
        assert ds.sizes["time"] == 1

    def test_last(self, sample_nc_file):
        cdo = CDO()
        ds = cdo.query(sample_nc_file).last()
        assert ds.sizes["time"] == 1

    def test_exists(self, sample_nc_file):
        cdo = CDO()
        assert cdo.query(sample_nc_file).exists()

        # Test with non-existent file (should return False or raise error depending on implementation)
        # The implementation catches Exception and returns False
        assert not cdo.query("non_existent_file.nc").exists()

    def test_count(self, sample_nc_file):
        cdo = CDO()
        # sample_nc_file has 5 timesteps (defined in conftest.py usually)
        # Let's check conftest.py to be sure, but assuming it has some timesteps
        count = cdo.query(sample_nc_file).count()
        assert count > 0

        # Test with operators
        # Selecting 2 timesteps
        count_sel = cdo.query(sample_nc_file).select_timestep(1, 2).count()
        assert count_sel == 2

    def test_values(self, sample_nc_file):
        cdo = CDO()
        q = cdo.query(sample_nc_file).values("tas")
        cmd = q.get_command()
        assert "-selname,tas" in cmd


class TestCDOQueryTemplate:
    """Tests for CDOQueryTemplate."""

    def test_template_creation(self):
        template = CDOQueryTemplate().select_var("tas").year_mean()
        assert template._input is None
        assert len(template._operators) == 2
        assert template._operators[0].name == "selname"
        assert template._operators[1].name == "yearmean"

    def test_template_apply(self, multi_var_nc_file):
        cdo = CDO()
        template = CDOQueryTemplate().select_var("tas")

        q = template.apply(multi_var_nc_file, cdo)
        assert q._input == Path(multi_var_nc_file)
        assert q._cdo is cdo
        assert len(q._operators) == 1
        assert q._operators[0].name == "selname"

        # Execute
        ds = q.compute()
        assert "tas" in ds.data_vars


@pytest.mark.integration
class TestInfoOperatorsQuery:
    """Tests for information operators as terminating query methods."""

    def test_showname_without_operators(self, sample_nc_file):
        """Test showname() on query without operators."""
        cdo = CDO()
        names = cdo.query(sample_nc_file).showname()

        assert isinstance(names, list)
        assert len(names) > 0
        assert all(isinstance(name, str) for name in names)

    def test_showname_with_operators(self, multi_var_nc_file):
        """Test showname() on query with selection operators."""
        cdo = CDO()
        # Select only 'tas' variable
        names = cdo.query(multi_var_nc_file).select_var("tas").showname()

        assert isinstance(names, list)
        assert "tas" in names
        # Should only have selected variable(s)

    def test_showcode_without_operators(self, sample_nc_file):
        """Test showcode() on query without operators."""
        cdo = CDO()
        codes = cdo.query(sample_nc_file).showcode()

        assert isinstance(codes, list)
        # Codes might be empty for some files, so just check type
        assert all(isinstance(code, int) for code in codes)

    def test_showunit_without_operators(self, sample_nc_file):
        """Test showunit() on query without operators."""
        cdo = CDO()
        units = cdo.query(sample_nc_file).showunit()

        assert isinstance(units, list)
        assert len(units) > 0
        assert all(isinstance(unit, str) for unit in units)

    def test_showlevel_without_operators(self, sample_nc_file):
        """Test showlevel() on query without operators."""
        cdo = CDO()
        levels = cdo.query(sample_nc_file).showlevel()

        assert isinstance(levels, list)
        # Levels might be empty for some files
        assert all(isinstance(level, float) for level in levels)

    def test_showdate_without_operators(self, sample_nc_file_with_time):
        """Test showdate() on query without operators."""
        cdo = CDO()
        dates = cdo.query(sample_nc_file_with_time).showdate()

        assert isinstance(dates, list)
        assert len(dates) > 0
        assert all(isinstance(date, str) for date in dates)

    def test_showtime_without_operators(self, sample_nc_file_with_time):
        """Test showtime() on query without operators."""
        cdo = CDO()
        times = cdo.query(sample_nc_file_with_time).showtime()

        assert isinstance(times, list)
        assert len(times) > 0
        assert all(isinstance(time, str) for time in times)

    def test_ntime_without_operators(self, sample_nc_file):
        """Test ntime() on query without operators."""
        cdo = CDO()
        n = cdo.query(sample_nc_file).ntime()

        assert isinstance(n, int)
        assert n > 0

    def test_ntime_with_operators(self, sample_nc_file):
        """Test ntime() on query with selection operators."""
        cdo = CDO()
        # Select first 2 timesteps
        n = cdo.query(sample_nc_file).select_timestep(1, 2).ntime()

        assert isinstance(n, int)
        assert n == 2

    def test_nvar_without_operators(self, multi_var_nc_file):
        """Test nvar() on query without operators."""
        cdo = CDO()
        n = cdo.query(multi_var_nc_file).nvar()

        assert isinstance(n, int)
        assert n >= 2  # multi_var_nc_file has at least 2 variables

    def test_nvar_with_operators(self, multi_var_nc_file):
        """Test nvar() on query with variable selection."""
        cdo = CDO()
        # Select only 'tas' variable
        n = cdo.query(multi_var_nc_file).select_var("tas").nvar()

        assert isinstance(n, int)
        assert n == 1

    def test_nlevel_without_operators(self, sample_nc_file):
        """Test nlevel() on query without operators."""
        cdo = CDO()
        n = cdo.query(sample_nc_file).nlevel()

        assert isinstance(n, int)
        # May be 0 for 2D data, or > 0 for 3D data

    def test_sinfo_without_operators(self, sample_nc_file):
        """Test sinfo() on query without operators."""
        cdo = CDO()
        from python_cdo_wrapper.types.results import SinfoResult

        result = cdo.query(sample_nc_file).sinfo()

        assert isinstance(result, SinfoResult)
        assert result.nvar > 0
        # sinfo doesn't provide variable names, only parameter IDs
        assert len(result.variables) > 0
        assert result.variables[0].param_id == 167  # Check parameter ID instead

    def test_sinfo_with_operators(self, multi_var_nc_file):
        """Test sinfo() on query with operators."""
        cdo = CDO()
        from python_cdo_wrapper.types.results import SinfoResult

        result = cdo.query(multi_var_nc_file).select_var("tas").sinfo()

        assert isinstance(result, SinfoResult)
        # After selecting 'tas', should have 1 variable
        assert result.nvar == 1
        assert len(result.variables) == 1
        # Check parameter ID (tas has code 167)
        assert result.variables[0].param_id == 167

    def test_info_without_operators(self, sample_nc_file):
        """Test info() on query without operators."""
        cdo = CDO()
        from python_cdo_wrapper.types.results import InfoResult

        result = cdo.query(sample_nc_file).info()

        assert isinstance(result, InfoResult)
        assert len(result.timesteps) > 0

    def test_griddes_without_operators(self, sample_nc_file):
        """Test griddes() on query without operators."""
        cdo = CDO()
        from python_cdo_wrapper.types.results import GriddesResult

        result = cdo.query(sample_nc_file).griddes()

        assert isinstance(result, GriddesResult)
        assert len(result.grids) > 0
        assert result.grids[0].gridtype is not None

    def test_zaxisdes_without_operators(self, sample_nc_file):
        """Test zaxisdes() on query without operators."""
        cdo = CDO()
        from python_cdo_wrapper.types.results import ZaxisdesResult

        result = cdo.query(sample_nc_file).zaxisdes()

        assert isinstance(result, ZaxisdesResult)
        assert len(result.zaxes) > 0

    def test_vlist_without_operators(self, sample_nc_file):
        """Test vlist() on query without operators."""
        cdo = CDO()
        from python_cdo_wrapper.types.results import VlistResult

        result = cdo.query(sample_nc_file).vlist()

        assert isinstance(result, VlistResult)
        assert len(result.variables) > 0

    def test_partab_without_operators(self, sample_nc_file):
        """Test partab() on query without operators."""
        cdo = CDO()
        from python_cdo_wrapper.types.results import PartabResult

        result = cdo.query(sample_nc_file).partab()

        assert isinstance(result, PartabResult)
        # partab might have empty parameters for some files
        assert result.parameters is not None

    def test_chaining_info_operators(self, multi_var_nc_file):
        """Test that info operators work after data processing operators."""
        cdo = CDO()

        # Process data then get info
        names = (
            cdo.query(multi_var_nc_file).select_var("tas", "pr").year_mean().showname()
        )

        assert isinstance(names, list)
        assert set(names) <= {"tas", "pr"}  # Subset of original selection
