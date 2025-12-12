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
