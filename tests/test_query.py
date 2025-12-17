"""
Tests for CDOQuery class (Django ORM-style query builder).

This tests the core lazy query abstraction including:
- Query building and chaining
- Command generation
- Immutability and cloning
- Selection, statistical, and arithmetic operators
- Binary operations with F()
- Explain functionality
"""

from __future__ import annotations

import pytest

from python_cdo_wrapper import CDO, BinaryOpQuery, CDOQuery, F
from python_cdo_wrapper.exceptions import CDOError, CDOValidationError
from python_cdo_wrapper.operators.base import OperatorSpec
from python_cdo_wrapper.types.grid import GridSpec


class TestCDOQueryBasics:
    """Test basic CDOQuery construction and properties."""

    def test_query_creation(self, sample_nc_file):
        """Test creating a query from CDO instance."""
        cdo = CDO()
        q = cdo.query(sample_nc_file)

        assert isinstance(q, CDOQuery)
        assert q._input.name == "test_data.nc"
        assert len(q._operators) == 0
        assert q._cdo is cdo

    def test_query_immutability(self, sample_nc_file):
        """Test that queries are immutable."""
        cdo = CDO()
        q1 = cdo.query(sample_nc_file)
        q2 = q1.select_var("tas")

        # Original should be unchanged
        assert len(q1._operators) == 0
        assert len(q2._operators) == 1
        assert q1 is not q2

    def test_empty_query_command(self, sample_nc_file):
        """Test command generation for query with no operators."""
        cdo = CDO()
        q = cdo.query(sample_nc_file)
        cmd = q.get_command()

        assert "cdo" in cmd
        assert "test_data.nc" in cmd


class TestCDOQuerySelectionOperators:
    """Test selection operators."""

    def test_select_var_single(self, sample_nc_file):
        """Test selecting a single variable."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).select_var("tas")

        assert len(q._operators) == 1
        assert q._operators[0].name == "selname"
        assert q._operators[0].args == ("tas",)

        cmd = q.get_command()
        assert "-selname,tas" in cmd

    def test_select_var_multiple(self, sample_nc_file):
        """Test selecting multiple variables."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).select_var("tas", "pr", "psl")

        cmd = q.get_command()
        assert "-selname,tas,pr,psl" in cmd

    def test_select_var_empty_raises(self, sample_nc_file):
        """Test that empty variable list raises validation error."""
        cdo = CDO()
        with pytest.raises(CDOValidationError) as exc_info:
            cdo.query(sample_nc_file).select_var()

        assert "names" in str(exc_info.value)

    def test_select_level(self, sample_nc_file):
        """Test level selection."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).select_level(1000, 850, 500)

        cmd = q.get_command()
        assert "-sellevel,1000,850,500" in cmd

    def test_select_level_empty_raises(self, sample_nc_file):
        """Test that empty level list raises validation error."""
        cdo = CDO()
        with pytest.raises(CDOValidationError):
            cdo.query(sample_nc_file).select_level()

    def test_select_year(self, sample_nc_file):
        """Test year selection."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).select_year(2020, 2021)

        cmd = q.get_command()
        assert "-selyear,2020,2021" in cmd

    def test_select_month(self, sample_nc_file):
        """Test month selection."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).select_month(6, 7, 8)

        cmd = q.get_command()
        assert "-selmon,6,7,8" in cmd

    def test_select_month_invalid_raises(self, sample_nc_file):
        """Test that invalid month numbers raise validation error."""
        cdo = CDO()
        with pytest.raises(CDOValidationError) as exc_info:
            cdo.query(sample_nc_file).select_month(0, 13)

        assert "month" in str(exc_info.value).lower()

    def test_select_region(self, sample_nc_file):
        """Test geographic region selection."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).select_region(-10, 40, 35, 70)

        cmd = q.get_command()
        assert "-sellonlatbox,-10,40,35,70" in cmd

    def test_select_day(self, sample_nc_file):
        """Test day selection."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).select_day(1, 15)

        cmd = q.get_command()
        assert "-selday,1,15" in cmd

    def test_select_day_empty_raises(self, sample_nc_file):
        """Test that empty day list raises validation error."""
        cdo = CDO()
        with pytest.raises(CDOValidationError):
            cdo.query(sample_nc_file).select_day()

    def test_select_day_invalid_raises(self, sample_nc_file):
        """Test that invalid day numbers raise validation error."""
        cdo = CDO()
        with pytest.raises(CDOValidationError) as exc_info:
            cdo.query(sample_nc_file).select_day(0, 32)
        assert "day" in str(exc_info.value).lower()

    def test_select_hour(self, sample_nc_file):
        """Test hour selection."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).select_hour(0, 6, 12, 18)

        cmd = q.get_command()
        assert "-selhour,0,6,12,18" in cmd

    def test_select_hour_empty_raises(self, sample_nc_file):
        """Test that empty hour list raises validation error."""
        cdo = CDO()
        with pytest.raises(CDOValidationError):
            cdo.query(sample_nc_file).select_hour()

    def test_select_hour_invalid_raises(self, sample_nc_file):
        """Test that invalid hour values raise validation error."""
        cdo = CDO()
        with pytest.raises(CDOValidationError) as exc_info:
            cdo.query(sample_nc_file).select_hour(-1, 24)
        assert "hour" in str(exc_info.value).lower()

    def test_select_season(self, sample_nc_file):
        """Test season selection."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).select_season("DJF", "JJA")

        cmd = q.get_command()
        assert "-selseason,DJF,JJA" in cmd

    def test_select_season_case_insensitive(self, sample_nc_file):
        """Test that season selection is case insensitive."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).select_season("djf", "jja")

        cmd = q.get_command()
        assert "-selseason,DJF,JJA" in cmd

    def test_select_season_empty_raises(self, sample_nc_file):
        """Test that empty season list raises validation error."""
        cdo = CDO()
        with pytest.raises(CDOValidationError):
            cdo.query(sample_nc_file).select_season()

    def test_select_season_invalid_raises(self, sample_nc_file):
        """Test that invalid season codes raise validation error."""
        cdo = CDO()
        with pytest.raises(CDOValidationError) as exc_info:
            cdo.query(sample_nc_file).select_season("WINTER", "SUMMER")
        assert "season" in str(exc_info.value).lower()

    def test_select_date_range(self, sample_nc_file):
        """Test date range selection."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).select_date("2020-01-01", "2020-12-31")

        cmd = q.get_command()
        assert "-seldate,2020-01-01,2020-12-31" in cmd

    def test_select_date_single(self, sample_nc_file):
        """Test single date selection."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).select_date("2020-06-15")

        cmd = q.get_command()
        assert "-seldate,2020-06-15" in cmd

    def test_select_time(self, sample_nc_file):
        """Test time selection."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).select_time("00:00:00", "12:00:00")

        cmd = q.get_command()
        assert "-seltime,00:00:00,12:00:00" in cmd

    def test_select_time_empty_raises(self, sample_nc_file):
        """Test that empty time list raises validation error."""
        cdo = CDO()
        with pytest.raises(CDOValidationError):
            cdo.query(sample_nc_file).select_time()

    def test_select_timestep(self, sample_nc_file):
        """Test timestep selection."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).select_timestep(1, 2, 3)

        cmd = q.get_command()
        assert "-seltimestep,1,2,3" in cmd

    def test_select_timestep_empty_raises(self, sample_nc_file):
        """Test that empty timestep list raises validation error."""
        cdo = CDO()
        with pytest.raises(CDOValidationError):
            cdo.query(sample_nc_file).select_timestep()

    def test_select_timestep_invalid_raises(self, sample_nc_file):
        """Test that non-positive timesteps raise validation error."""
        cdo = CDO()
        with pytest.raises(CDOValidationError) as exc_info:
            cdo.query(sample_nc_file).select_timestep(0, -1)
        assert "timestep" in str(exc_info.value).lower()

    def test_select_code(self, sample_nc_file):
        """Test parameter code selection."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).select_code(130, 131)

        cmd = q.get_command()
        assert "-selcode,130,131" in cmd

    def test_select_code_empty_raises(self, sample_nc_file):
        """Test that empty code list raises validation error."""
        cdo = CDO()
        with pytest.raises(CDOValidationError):
            cdo.query(sample_nc_file).select_code()

    def test_select_level_idx(self, sample_nc_file):
        """Test level index selection."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).select_level_idx(1, 2, 3)

        cmd = q.get_command()
        assert "-sellevidx,1,2,3" in cmd

    def test_select_level_idx_empty_raises(self, sample_nc_file):
        """Test that empty level index list raises validation error."""
        cdo = CDO()
        with pytest.raises(CDOValidationError):
            cdo.query(sample_nc_file).select_level_idx()

    def test_select_level_idx_invalid_raises(self, sample_nc_file):
        """Test that non-positive level indices raise validation error."""
        cdo = CDO()
        with pytest.raises(CDOValidationError) as exc_info:
            cdo.query(sample_nc_file).select_level_idx(0, -1)
        assert "level" in str(exc_info.value).lower()

    def test_select_level_type(self, sample_nc_file):
        """Test level type selection."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).select_level_type(100)

        cmd = q.get_command()
        assert "-selltype,100" in cmd

    def test_select_grid(self, sample_nc_file):
        """Test grid selection."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).select_grid(1)

        cmd = q.get_command()
        assert "-selgrid,1" in cmd

    def test_select_grid_invalid_raises(self, sample_nc_file):
        """Test that non-positive grid number raises validation error."""
        cdo = CDO()
        with pytest.raises(CDOValidationError) as exc_info:
            cdo.query(sample_nc_file).select_grid(0)
        assert "grid" in str(exc_info.value).lower()

    def test_select_zaxis(self, sample_nc_file):
        """Test z-axis selection."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).select_zaxis(1)

        cmd = q.get_command()
        assert "-selzaxis,1" in cmd

    def test_select_zaxis_invalid_raises(self, sample_nc_file):
        """Test that non-positive z-axis number raises validation error."""
        cdo = CDO()
        with pytest.raises(CDOValidationError) as exc_info:
            cdo.query(sample_nc_file).select_zaxis(0)
        assert "z-axis" in str(exc_info.value).lower()

    def test_select_index_box(self, sample_nc_file):
        """Test index box selection."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).select_index_box(1, 100, 1, 50)

        cmd = q.get_command()
        assert "-selindexbox,1,100,1,50" in cmd

    def test_select_index_box_invalid_indices_raises(self, sample_nc_file):
        """Test that non-positive indices raise validation error."""
        cdo = CDO()
        with pytest.raises(CDOValidationError) as exc_info:
            cdo.query(sample_nc_file).select_index_box(0, 100, 1, 50)
        assert (
            "indices" in str(exc_info.value).lower()
            or "index" in str(exc_info.value).lower()
        )

    def test_select_index_box_invalid_x_range_raises(self, sample_nc_file):
        """Test that x1 > x2 raises validation error."""
        cdo = CDO()
        with pytest.raises(CDOValidationError) as exc_info:
            cdo.query(sample_nc_file).select_index_box(100, 1, 1, 50)
        assert "x1" in str(exc_info.value).lower() or "x" in str(exc_info.value).lower()

    def test_select_index_box_invalid_y_range_raises(self, sample_nc_file):
        """Test that y1 > y2 raises validation error."""
        cdo = CDO()
        with pytest.raises(CDOValidationError) as exc_info:
            cdo.query(sample_nc_file).select_index_box(1, 100, 50, 1)
        assert "y1" in str(exc_info.value).lower() or "y" in str(exc_info.value).lower()

    def test_select_mask(self, sample_nc_file, tmp_path):
        """Test mask selection."""
        cdo = CDO()
        mask_file = tmp_path / "mask.nc"
        q = cdo.query(sample_nc_file).select_mask(mask_file)

        cmd = q.get_command()
        assert "-ifthen" in cmd
        assert "mask.nc" in cmd


class TestCDOQueryStatisticalOperators:
    """Test statistical operators."""

    def test_year_mean(self, sample_nc_file):
        """Test yearly mean calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).year_mean()

        cmd = q.get_command()
        assert "-yearmean" in cmd

    def test_month_mean(self, sample_nc_file):
        """Test monthly mean calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).month_mean()

        cmd = q.get_command()
        assert "-monmean" in cmd

    def test_time_mean(self, sample_nc_file):
        """Test time mean calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).time_mean()

        cmd = q.get_command()
        assert "-timmean" in cmd

    def test_field_mean(self, sample_nc_file):
        """Test spatial field mean calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).field_mean()

        cmd = q.get_command()
        assert "-fldmean" in cmd

    # Time statistics
    def test_time_sum(self, sample_nc_file):
        """Test time sum calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).time_sum()
        assert "-timsum" in q.get_command()

    def test_time_min(self, sample_nc_file):
        """Test time minimum calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).time_min()
        assert "-timmin" in q.get_command()

    def test_time_max(self, sample_nc_file):
        """Test time maximum calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).time_max()
        assert "-timmax" in q.get_command()

    def test_time_std(self, sample_nc_file):
        """Test time standard deviation calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).time_std()
        assert "-timstd" in q.get_command()

    def test_time_var(self, sample_nc_file):
        """Test time variance calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).time_var()
        assert "-timvar" in q.get_command()

    def test_time_range(self, sample_nc_file):
        """Test time range calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).time_range()
        assert "-timrange" in q.get_command()

    # Year statistics
    def test_year_sum(self, sample_nc_file):
        """Test yearly sum calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).year_sum()
        assert "-yearsum" in q.get_command()

    def test_year_min(self, sample_nc_file):
        """Test yearly minimum calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).year_min()
        assert "-yearmin" in q.get_command()

    def test_year_max(self, sample_nc_file):
        """Test yearly maximum calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).year_max()
        assert "-yearmax" in q.get_command()

    def test_year_std(self, sample_nc_file):
        """Test yearly standard deviation calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).year_std()
        assert "-yearstd" in q.get_command()

    def test_year_var(self, sample_nc_file):
        """Test yearly variance calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).year_var()
        assert "-yearvar" in q.get_command()

    # Month statistics
    def test_month_sum(self, sample_nc_file):
        """Test monthly sum calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).month_sum()
        assert "-monsum" in q.get_command()

    def test_month_min(self, sample_nc_file):
        """Test monthly minimum calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).month_min()
        assert "-monmin" in q.get_command()

    def test_month_max(self, sample_nc_file):
        """Test monthly maximum calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).month_max()
        assert "-monmax" in q.get_command()

    def test_month_std(self, sample_nc_file):
        """Test monthly standard deviation calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).month_std()
        assert "-monstd" in q.get_command()

    # Day and hour statistics
    def test_day_mean(self, sample_nc_file):
        """Test daily mean calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).day_mean()
        assert "-daymean" in q.get_command()

    def test_day_sum(self, sample_nc_file):
        """Test daily sum calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).day_sum()
        assert "-daysum" in q.get_command()

    def test_hour_mean(self, sample_nc_file):
        """Test hourly mean calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).hour_mean()
        assert "-hourmean" in q.get_command()

    # Seasonal statistics
    def test_season_mean(self, sample_nc_file):
        """Test seasonal mean calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).season_mean()
        assert "-seasmean" in q.get_command()

    def test_season_sum(self, sample_nc_file):
        """Test seasonal sum calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).season_sum()
        assert "-seassum" in q.get_command()

    # Field statistics
    def test_field_sum(self, sample_nc_file):
        """Test field sum calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).field_sum()
        assert "-fldsum" in q.get_command()

    def test_field_min(self, sample_nc_file):
        """Test field minimum calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).field_min()
        assert "-fldmin" in q.get_command()

    def test_field_max(self, sample_nc_file):
        """Test field maximum calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).field_max()
        assert "-fldmax" in q.get_command()

    def test_field_std(self, sample_nc_file):
        """Test field standard deviation calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).field_std()
        assert "-fldstd" in q.get_command()

    def test_field_var(self, sample_nc_file):
        """Test field variance calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).field_var()
        assert "-fldvar" in q.get_command()

    def test_field_range(self, sample_nc_file):
        """Test field range calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).field_range()
        assert "-fldrange" in q.get_command()

    def test_field_percentile(self, sample_nc_file):
        """Test field percentile calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).field_percentile(95)
        assert "-fldpctl,95" in q.get_command()

    def test_field_percentile_invalid_raises(self, sample_nc_file):
        """Test that invalid percentile raises validation error."""
        cdo = CDO()
        with pytest.raises(CDOValidationError) as exc_info:
            cdo.query(sample_nc_file).field_percentile(150)
        assert "percentile" in str(exc_info.value).lower()

    # Zonal and meridional statistics
    def test_zonal_mean(self, sample_nc_file):
        """Test zonal mean calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).zonal_mean()
        assert "-zonmean" in q.get_command()

    def test_zonal_sum(self, sample_nc_file):
        """Test zonal sum calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).zonal_sum()
        assert "-zonsum" in q.get_command()

    def test_meridional_mean(self, sample_nc_file):
        """Test meridional mean calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).meridional_mean()
        assert "-mermean" in q.get_command()

    # Vertical statistics
    def test_vert_mean(self, sample_nc_file):
        """Test vertical mean calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).vert_mean()
        assert "-vertmean" in q.get_command()

    def test_vert_sum(self, sample_nc_file):
        """Test vertical sum calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).vert_sum()
        assert "-vertsum" in q.get_command()

    def test_vert_min(self, sample_nc_file):
        """Test vertical minimum calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).vert_min()
        assert "-vertmin" in q.get_command()

    def test_vert_max(self, sample_nc_file):
        """Test vertical maximum calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).vert_max()
        assert "-vertmax" in q.get_command()

    def test_vert_std(self, sample_nc_file):
        """Test vertical standard deviation calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).vert_std()
        assert "-vertstd" in q.get_command()

    def test_vert_int(self, sample_nc_file):
        """Test vertical integration calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).vert_int()
        assert "-vertint" in q.get_command()

    # Running statistics
    def test_running_mean(self, sample_nc_file):
        """Test running mean calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).running_mean(5)
        assert "-runmean,5" in q.get_command()

    def test_running_mean_invalid_raises(self, sample_nc_file):
        """Test that invalid window size raises validation error."""
        cdo = CDO()
        with pytest.raises(CDOValidationError) as exc_info:
            cdo.query(sample_nc_file).running_mean(0)
        assert "window" in str(exc_info.value).lower()

    def test_running_sum(self, sample_nc_file):
        """Test running sum calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).running_sum(3)
        assert "-runsum,3" in q.get_command()

    def test_running_sum_invalid_raises(self, sample_nc_file):
        """Test that invalid window size raises validation error."""
        cdo = CDO()
        with pytest.raises(CDOValidationError):
            cdo.query(sample_nc_file).running_sum(-1)

    def test_running_min(self, sample_nc_file):
        """Test running minimum calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).running_min(5)
        assert "-runmin,5" in q.get_command()

    def test_running_max(self, sample_nc_file):
        """Test running maximum calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).running_max(5)
        assert "-runmax,5" in q.get_command()

    def test_running_std(self, sample_nc_file):
        """Test running standard deviation calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).running_std(5)
        assert "-runstd,5" in q.get_command()

    # Percentile operations
    def test_time_percentile(self, sample_nc_file):
        """Test time percentile calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).time_percentile(90)
        assert "-timpctl,90" in q.get_command()

    def test_time_percentile_invalid_raises(self, sample_nc_file):
        """Test that invalid percentile raises validation error."""
        cdo = CDO()
        with pytest.raises(CDOValidationError):
            cdo.query(sample_nc_file).time_percentile(101)

    def test_year_percentile(self, sample_nc_file):
        """Test yearly percentile calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).year_percentile(75)
        assert "-yearpctl,75" in q.get_command()

    def test_year_percentile_invalid_raises(self, sample_nc_file):
        """Test that invalid percentile raises validation error."""
        cdo = CDO()
        with pytest.raises(CDOValidationError):
            cdo.query(sample_nc_file).year_percentile(-1)

    def test_month_percentile(self, sample_nc_file):
        """Test monthly percentile calculation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).month_percentile(50)
        assert "-monpctl,50" in q.get_command()

    def test_month_percentile_invalid_raises(self, sample_nc_file):
        """Test that invalid percentile raises validation error."""
        cdo = CDO()
        with pytest.raises(CDOValidationError):
            cdo.query(sample_nc_file).month_percentile(150)

    # Test chaining statistical operators
    def test_chained_statistics(self, sample_nc_file):
        """Test chaining multiple statistical operators."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).year_mean().field_mean()
        cmd = q.get_command()
        assert "-fldmean" in cmd
        assert "-yearmean" in cmd

    def test_statistics_with_selection(self, sample_nc_file):
        """Test combining statistics with selection operators."""
        cdo = CDO()
        q = (
            cdo.query(sample_nc_file)
            .select_var("tas")
            .select_year(2020)
            .year_mean()
            .field_sum()
        )
        cmd = q.get_command()
        assert "-selname,tas" in cmd
        assert "-selyear,2020" in cmd
        assert "-yearmean" in cmd
        assert "-fldsum" in cmd


class TestCDOQueryArithmeticOperators:
    """Test constant arithmetic operators."""

    def test_add_constant(self, sample_nc_file):
        """Test adding a constant."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).add_constant(273.15)

        cmd = q.get_command()
        assert "-addc,273.15" in cmd

    def test_multiply_constant(self, sample_nc_file):
        """Test multiplying by a constant."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).multiply_constant(86400)

        cmd = q.get_command()
        assert "-mulc,86400" in cmd

    def test_subtract_constant(self, sample_nc_file):
        """Test subtracting a constant."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).subtract_constant(273.15)

        cmd = q.get_command()
        assert "-subc,273.15" in cmd

    def test_divide_constant(self, sample_nc_file):
        """Test dividing by a constant."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).divide_constant(100)

        cmd = q.get_command()
        assert "-divc,100" in cmd

    def test_divide_by_zero_raises(self, sample_nc_file):
        """Test that dividing by zero raises validation error."""
        cdo = CDO()
        with pytest.raises(CDOValidationError):
            cdo.query(sample_nc_file).divide_constant(0)

    def test_sub_constant_alias(self, sample_nc_file):
        """Test sub_constant alias for subtract_constant."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).sub_constant(273.15)

        cmd = q.get_command()
        assert "-subc,273.15" in cmd

    def test_mul_constant_alias(self, sample_nc_file):
        """Test mul_constant alias for multiply_constant."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).mul_constant(86400)

        cmd = q.get_command()
        assert "-mulc,86400" in cmd

    def test_div_constant_alias(self, sample_nc_file):
        """Test div_constant alias for divide_constant."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).div_constant(100)

        cmd = q.get_command()
        assert "-divc,100" in cmd

    def test_div_constant_alias_zero_raises(self, sample_nc_file):
        """Test div_constant alias raises error on division by zero."""
        cdo = CDO()
        with pytest.raises(CDOValidationError):
            cdo.query(sample_nc_file).div_constant(0)


class TestCDOQueryInterpolationOperators:
    """Test interpolation and regridding operators."""

    def test_remap_bil_string(self, sample_nc_file):
        """Test bilinear remapping with grid string."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).remap_bil("r360x180")

        cmd = q.get_command()
        assert "-remapbil,r360x180" in cmd

    def test_remap_bil_gridspec(self, sample_nc_file):
        """Test bilinear remapping with GridSpec."""
        cdo = CDO()
        grid = GridSpec.global_1deg()
        q = cdo.query(sample_nc_file).remap_bil(grid)

        cmd = q.get_command()
        assert "-remapbil" in cmd
        # The argument will be a temp file path, so we check if it ends with .txt
        # and contains "cdo_grid_"
        parts = cmd.split()
        # Find the part that starts with -remapbil
        remap_arg = next(p for p in parts if "-remapbil" in p)
        # It might be "-remapbil,path" or inside brackets
        if "," in remap_arg:
            grid_file = remap_arg.split(",")[1]
            assert "cdo_grid_" in grid_file
            assert grid_file.endswith(".txt")

    def test_remap_bic(self, sample_nc_file):
        """Test bicubic remapping."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).remap_bic("r180x90")
        assert "-remapbic,r180x90" in q.get_command()

    def test_remap_nn(self, sample_nc_file):
        """Test nearest neighbor remapping."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).remap_nn("r180x90")
        assert "-remapnn,r180x90" in q.get_command()

    def test_remap_dis(self, sample_nc_file):
        """Test distance-weighted remapping."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).remap_dis("r180x90")
        assert "-remapdis,r180x90" in q.get_command()

    def test_remap_con(self, sample_nc_file):
        """Test conservative remapping."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).remap_con("r180x90")
        assert "-remapcon,r180x90" in q.get_command()

    def test_remap_con2(self, sample_nc_file):
        """Test second-order conservative remapping."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).remap_con2("r180x90")
        assert "-remapcon2,r180x90" in q.get_command()

    def test_remap_laf(self, sample_nc_file):
        """Test largest area fraction remapping."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).remap_laf("r180x90")
        assert "-remaplaf,r180x90" in q.get_command()

    def test_interp_level(self, sample_nc_file):
        """Test vertical interpolation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).interp_level(1000, 850, 500)
        assert "-intlevel,1000,850,500" in q.get_command()

    def test_interp_level_empty_raises(self, sample_nc_file):
        """Test that empty levels raise validation error."""
        cdo = CDO()
        with pytest.raises(CDOValidationError):
            cdo.query(sample_nc_file).interp_level()

    def test_ml_to_pl(self, sample_nc_file):
        """Test model to pressure level interpolation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).ml_to_pl(100000, 85000, 50000)
        assert "-ml2pl,100000,85000,50000" in q.get_command()

    def test_ml_to_pl_empty_raises(self, sample_nc_file):
        """Test that empty pressure levels raise validation error."""
        cdo = CDO()
        with pytest.raises(CDOValidationError):
            cdo.query(sample_nc_file).ml_to_pl()


class TestCDOQueryBinaryMinMax:
    """Test binary min/max operations."""

    def test_min_operation(self, sample_nc_file):
        """Test element-wise minimum."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).min("upper_bound.nc")

        assert isinstance(q, BinaryOpQuery)
        cmd = q.get_command()
        assert "cdo -min" in cmd
        assert "upper_bound.nc" in cmd

    def test_max_operation(self, sample_nc_file):
        """Test element-wise maximum."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).max("lower_bound.nc")

        assert isinstance(q, BinaryOpQuery)
        cmd = q.get_command()
        assert "cdo -max" in cmd
        assert "lower_bound.nc" in cmd

    def test_min_with_f(self, sample_nc_file):
        """Test min using F() function."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).min(F("bound.nc"))

        cmd = q.get_command()
        assert "cdo -min" in cmd

    def test_max_with_pipeline(self, sample_nc_file):
        """Test max with operator pipeline using brackets."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).year_mean().max(F("threshold.nc"))

        cmd = q.get_command()
        assert "cdo -max" in cmd
        assert "-yearmean" in cmd


class TestCDOQueryMathFunctions:
    """Test unary math functions."""

    def test_abs(self, sample_nc_file):
        """Test absolute value."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).abs()

        cmd = q.get_command()
        assert "-abs" in cmd

    def test_sqrt(self, sample_nc_file):
        """Test square root."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).sqrt()

        cmd = q.get_command()
        assert "-sqrt" in cmd

    def test_sqr(self, sample_nc_file):
        """Test square."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).sqr()

        cmd = q.get_command()
        assert "-sqr" in cmd

    def test_exp(self, sample_nc_file):
        """Test exponential."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).exp()

        cmd = q.get_command()
        assert "-exp" in cmd

    def test_ln(self, sample_nc_file):
        """Test natural logarithm."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).ln()

        cmd = q.get_command()
        assert "-ln" in cmd

    def test_log10(self, sample_nc_file):
        """Test base-10 logarithm."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).log10()

        cmd = q.get_command()
        assert "-log10" in cmd

    def test_chained_math_functions(self, sample_nc_file):
        """Test chaining multiple math functions."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).abs().sqrt()

        cmd = q.get_command()
        assert "-sqrt" in cmd
        assert "-abs" in cmd


class TestCDOQueryTrigFunctions:
    """Test trigonometric functions."""

    def test_sin(self, sample_nc_file):
        """Test sine function."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).sin()

        cmd = q.get_command()
        assert "-sin" in cmd

    def test_cos(self, sample_nc_file):
        """Test cosine function."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).cos()

        cmd = q.get_command()
        assert "-cos" in cmd

    def test_tan(self, sample_nc_file):
        """Test tangent function."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).tan()

        cmd = q.get_command()
        assert "-tan" in cmd

    def test_trig_chain(self, sample_nc_file):
        """Test chaining trigonometric operations."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).multiply_constant(3.14159 / 180).sin()

        cmd = q.get_command()
        assert "-sin" in cmd
        assert "-mulc" in cmd


class TestCDOQueryMaskingOperations:
    """Test masking and conditional operations."""

    def test_ifthen(self, sample_nc_file):
        """Test ifthen masking operation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).ifthen(F("mask.nc"))

        assert isinstance(q, BinaryOpQuery)
        cmd = q.get_command()
        assert "cdo -ifthen" in cmd
        assert "mask.nc" in cmd

    def test_mask_alias(self, sample_nc_file):
        """Test mask() as alias for ifthen()."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).mask("mask.nc")

        cmd = q.get_command()
        assert "cdo -ifthen" in cmd

    def test_ifthen_with_pipeline(self, sample_nc_file):
        """Test ifthen with operator pipeline."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).year_mean().ifthen(F("land_mask.nc"))

        cmd = q.get_command()
        assert "cdo -ifthen" in cmd
        assert "-yearmean" in cmd

    def test_ifthenelse(self, sample_nc_file):
        """Test ifthenelse conditional selection."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).ifthenelse(F("condition.nc"), F("fallback.nc"))

        assert isinstance(q, BinaryOpQuery)
        cmd = q.get_command()
        assert "cdo -ifthenelse" in cmd
        # Simple file references should not have brackets
        assert "[" not in cmd
        assert "]" not in cmd

    def test_ifthenelse_with_operators(self, sample_nc_file):
        """Test ifthenelse with operators on operands requires compute()."""
        cdo = CDO()
        q = (
            cdo.query(sample_nc_file)
            .year_mean()
            .ifthenelse(F("condition.nc"), F("fallback.nc").field_mean())
        )

        assert isinstance(q, BinaryOpQuery)
        # ifthenelse with operators still requires temporary files (special case)
        with pytest.raises(CDOError, match=r"temporary file handling|ifthenelse"):
            q.get_command()

    def test_where_alias(self, sample_nc_file):
        """Test where() as alias for ifthenelse()."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).where("condition.nc", "fallback.nc")

        cmd = q.get_command()
        assert "cdo -ifthenelse" in cmd


class TestCDOQueryMissingValueHandling:
    """Test missing value operations."""

    def test_set_missval(self, sample_nc_file):
        """Test setting missing value indicator."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).set_missval(-999.0)

        cmd = q.get_command()
        assert "-setmissval,-999" in cmd

    def test_setmisstoc(self, sample_nc_file):
        """Test replacing missing values with constant."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).setmisstoc(0.0)

        cmd = q.get_command()
        assert "-setmisstoc,0" in cmd

    def test_miss_to_const_alias(self, sample_nc_file):
        """Test miss_to_const() as alias."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).miss_to_const(0.0)

        cmd = q.get_command()
        assert "-setmisstoc,0" in cmd


class TestCDOQueryArithmeticChaining:
    """Test chaining arithmetic with other operators."""

    def test_selection_with_math(self, sample_nc_file):
        """Test chaining selection with math functions."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).select_var("tas").abs().sqrt()

        cmd = q.get_command()
        assert "-selname,tas" in cmd
        assert "-abs" in cmd
        assert "-sqrt" in cmd

    def test_stats_with_arithmetic(self, sample_nc_file):
        """Test chaining statistics with arithmetic."""
        cdo = CDO()
        q = (
            cdo.query(sample_nc_file)
            .year_mean()
            .subtract_constant(273.15)
            .multiply_constant(1.8)
            .add_constant(32)
        )

        cmd = q.get_command()
        assert "-yearmean" in cmd
        assert "-subc,273.15" in cmd
        assert "-mulc,1.8" in cmd
        assert "-addc,32" in cmd

    def test_binary_with_math_functions(self, sample_nc_file):
        """Test binary operations combined with math functions."""
        cdo = CDO()
        q = (
            cdo.query(sample_nc_file)
            .sub(F("mean.nc").day_mean())
            .sub(F("fun.nc"))
            .abs()
            .sqrt()
        )

        cmd = q.get_command()
        assert "cdo -sqrt" in cmd or "-sqrt" in cmd
        assert "cdo -abs" in cmd or "-abs" in cmd
        assert "-sub" in cmd

    def test_complex_arithmetic_workflow(self, sample_nc_file):
        """Test complex arithmetic workflow: normalized anomaly."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).sub(F("mean.nc").day_mean()).div(F("std.nc"))

        assert isinstance(q, BinaryOpQuery)
        cmd = q.get_command()
        assert "-div" in cmd
        assert "-sub" in cmd

    def test_masking_with_arithmetic(self, sample_nc_file):
        """Test masking combined with arithmetic operations."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).abs().mask("land_mask.nc")

        cmd = q.get_command()
        assert "cdo -ifthen" in cmd
        assert "-abs" in cmd


class TestCDOQueryChaining:
    """Test chaining multiple operators."""

    def test_simple_chain(self, sample_nc_file):
        """Test chaining selection and statistical operators."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).select_var("tas").year_mean()

        assert len(q._operators) == 2
        cmd = q.get_command()
        assert "-yearmean" in cmd
        assert "-selname,tas" in cmd

    def test_complex_chain(self, sample_nc_file):
        """Test complex multi-operator chain."""
        cdo = CDO()
        q = (
            cdo.query(sample_nc_file)
            .select_var("tas")
            .select_year(2020)
            .select_month(6, 7, 8)
            .year_mean()
            .field_mean()
        )

        assert len(q._operators) == 5
        cmd = q.get_command()
        # CDO applies operators right-to-left in command
        assert "-fldmean" in cmd
        assert "-yearmean" in cmd
        assert "-selmon,6,7,8" in cmd
        assert "-selyear,2020" in cmd
        assert "-selname,tas" in cmd

    def test_operator_order(self, sample_nc_file):
        """Test that operators are correctly ordered in command."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).select_var("tas").year_mean().field_mean()

        cmd = q.get_command()
        # Command should have operators in reverse order (CDO syntax)
        assert cmd.index("-fldmean") < cmd.index("-yearmean")
        assert cmd.index("-yearmean") < cmd.index("-selname")


class TestCDOQueryCloning:
    """Test query cloning and branching."""

    def test_clone(self, sample_nc_file):
        """Test cloning a query."""
        cdo = CDO()
        q1 = cdo.query(sample_nc_file).select_var("tas")
        q2 = q1.clone()

        assert q1 is not q2
        assert q1._input == q2._input
        assert len(q1._operators) == len(q2._operators)
        assert q1._operators == q2._operators

    def test_branching_pipelines(self, sample_nc_file):
        """Test branching queries for different analyses."""
        cdo = CDO()
        base = cdo.query(sample_nc_file).select_var("tas")

        # Create two different branches
        yearly = base.clone().year_mean()
        monthly = base.clone().month_mean()

        # Base should be unchanged
        assert len(base._operators) == 1
        assert len(yearly._operators) == 2
        assert len(monthly._operators) == 2

        # Commands should be different
        yearly_cmd = yearly.get_command()
        monthly_cmd = monthly.get_command()
        assert "-yearmean" in yearly_cmd
        assert "-monmean" in monthly_cmd
        assert "-yearmean" not in monthly_cmd
        assert "-monmean" not in yearly_cmd


class TestCDOQueryExplain:
    """Test query explanation functionality."""

    def test_explain_empty(self, sample_nc_file):
        """Test explaining an empty query."""
        cdo = CDO()
        q = cdo.query(sample_nc_file)
        explanation = q.explain()

        assert "Input:" in explanation
        assert "test_data.nc" in explanation

    def test_explain_single_operator(self, sample_nc_file):
        """Test explaining a query with one operator."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).select_var("tas")
        explanation = q.explain()

        assert "Input:" in explanation
        assert "1. selname(tas)" in explanation

    def test_explain_multiple_operators(self, sample_nc_file):
        """Test explaining a complex query."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).select_var("tas").select_year(2020).year_mean()
        explanation = q.explain()

        assert "Input:" in explanation
        assert "1. selname(tas)" in explanation
        assert "2. selyear(2020)" in explanation
        assert "3. yearmean()" in explanation


class TestFFunction:
    """Test F() function for creating unbound queries."""

    def test_f_creates_query(self, sample_nc_file):
        """Test that F() creates a CDOQuery."""
        q = F(sample_nc_file)

        assert isinstance(q, CDOQuery)
        assert q._cdo is None
        assert len(q._operators) == 0

    def test_f_with_string_path(self):
        """Test F() with string path."""
        q = F("data.nc")
        assert q._input.name == "data.nc"

    def test_f_with_path_object(self):
        """Test F() with Path object."""
        from pathlib import Path

        q = F(Path("data.nc"))
        assert q._input.name == "data.nc"


class TestBinaryOperations:
    """Test binary arithmetic operations."""

    def test_simple_subtraction(self, sample_nc_file):
        """Test simple file subtraction."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).sub("climatology.nc")

        assert isinstance(q, BinaryOpQuery)
        assert q._operator == "sub"

        cmd = q.get_command()
        assert "cdo -sub" in cmd
        assert "test_data.nc" in cmd
        assert "climatology.nc" in cmd

    def test_subtraction_with_f(self, sample_nc_file):
        """Test subtraction using F() function."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).sub(F("climatology.nc"))

        cmd = q.get_command()
        print(cmd)
        assert "cdo -sub" in cmd

    def test_anomaly_calculation_with_operator_chaining(self, sample_nc_file):
        """Test anomaly calculation using operator chaining (no brackets)."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).year_mean().sub(F("climatology.nc"))

        cmd = q.get_command()
        # Should use operator chaining for left operand (NO brackets)
        assert "cdo -sub" in cmd
        assert "[" not in cmd
        assert "]" not in cmd
        assert "-yearmean" in cmd

    def test_addition(self, sample_nc_file):
        """Test addition operation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).add("other.nc")

        cmd = q.get_command()
        assert "cdo -add" in cmd

    def test_multiplication(self, sample_nc_file):
        """Test multiplication operation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).mul("mask.nc")

        cmd = q.get_command()
        assert "cdo -mul" in cmd

    def test_division(self, sample_nc_file):
        """Test division operation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).div("reference.nc")

        cmd = q.get_command()
        assert "cdo -div" in cmd

    def test_complex_binary_with_both_sides_having_operators(self, sample_nc_file):
        """Test binary operation where both sides have operators."""
        cdo = CDO()
        left = cdo.query(sample_nc_file).select_var("tas").year_mean()
        right = F("clim.nc")  # Could also have operators
        q = left.sub(right)

        cmd = q.get_command()
        assert "-yearmean" in cmd
        assert "-selname,tas" in cmd

    def test_chained_binary_operations(self, sample_nc_file):
        """Test chaining binary operations."""
        cdo = CDO()
        # Normalized anomaly: (data - clim) / std
        q = cdo.query(sample_nc_file).sub(F("clim.nc")).div(F("std.nc"))

        # Second binary operation should work on result of first
        assert isinstance(q, BinaryOpQuery)
        assert q._operator == "div"

    def test_binary_operation_with_operators_uses_chaining(self, sample_nc_file):
        """Test that binary operations with operators on left operand use operator chaining."""
        cdo = CDO()
        # Left operand has operators, right is simple file
        q = cdo.query(sample_nc_file).select_var("tas").year_mean().sub(F("clim.nc"))

        cmd = q.get_command()
        # Should use operator chaining (NO brackets)
        assert "[" not in cmd
        assert "]" not in cmd
        assert "-yearmean" in cmd
        assert "-selname,tas" in cmd
        assert "clim.nc" in cmd

    def test_binary_operation_right_operand_with_operators(self, sample_nc_file):
        """Test binary operation where right operand has operators."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).sub(F("clim.nc").year_mean())

        cmd = q.get_command()
        # Should have: cdo -sub file1.nc -yearmean clim.nc
        assert "cdo -sub" in cmd
        assert "-yearmean" in cmd
        assert "clim.nc" in cmd
        # Should NOT have brackets
        assert "[" not in cmd
        assert "]" not in cmd

    def test_binary_operation_both_operands_with_operators(self, sample_nc_file):
        """Test binary operation where both operands have operators generates correct command."""
        cdo = CDO()
        left = cdo.query(sample_nc_file).select_var("tas").year_mean()
        right = F("clim.nc").field_mean()
        q = left.sub(right)

        # get_command() should work - CDO handles both operators in one command
        cmd = q.get_command()
        # Should have: cdo -sub -yearmean -selname,tas file1.nc -fldmean clim.nc
        assert "cdo -sub" in cmd
        assert "-yearmean" in cmd
        assert "-selname,tas" in cmd
        assert "-fldmean" in cmd
        assert "clim.nc" in cmd
        # Should NOT have brackets
        assert "[" not in cmd
        assert "]" not in cmd

    def test_simple_binary_no_brackets(self, sample_nc_file):
        """Test simple binary operation without operators doesn't use brackets."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).sub(F("clim.nc"))

        cmd = q.get_command()
        # Simple file references don't need brackets
        assert "[" not in cmd
        assert "]" not in cmd

    def test_nested_binary_operations_generate_correct_command(self, sample_nc_file):
        """Test nested binary operations (ifthen inside sub) generate correct command."""
        cdo = CDO()
        # Create inner binary operation (ifthen)
        inner = cdo.query(sample_nc_file).ifthen(F("mask.nc"))
        # Create outer binary operation (sub)
        q = inner.sub(F("clim.nc"))

        cmd = q.get_command()
        # Should generate: cdo -sub -ifthen mask.nc data.nc clim.nc
        assert "cdo -sub" in cmd
        assert "-ifthen" in cmd
        assert "mask.nc" in cmd
        assert "clim.nc" in cmd
        # Should NOT have brackets
        assert "[" not in cmd
        assert "]" not in cmd

    def test_complex_binary_with_nested_ifthen_both_sides(self, sample_nc_file):
        """Test complex binary with nested ifthen on both operands generates correct command."""
        cdo = CDO()
        # Simulate the issue from the bug report
        left = (
            cdo.query(sample_nc_file)
            .select_var("t")
            .select_level(100000)
            .ifthen(F("mask.nc"))
        )
        right = (
            F("data2.nc")
            .select_var("t")
            .select_level(100000)
            .ifthen(F("mask2.nc"))
            .time_mean()
        )
        q = left.sub(right).time_mean()

        # Should now generate correct command without errors
        cmd = q.get_command()
        assert "cdo -timmean -sub" in cmd
        assert "-selname,t" in cmd
        assert "-sellevel,100000" in cmd
        assert "-ifthen" in cmd
        # Should NOT have brackets
        assert "[" not in cmd
        assert "]" not in cmd

        # Verify the query structure is correct
        assert isinstance(q, BinaryOpQuery)
        assert q._operator == "sub"

    def test_nested_binary_with_operators_on_both_sides(self, sample_nc_file):
        """Test nested binary where both sides have complex operations."""
        cdo = CDO()
        # Left side: ifthen with operators before it
        left = cdo.query(sample_nc_file).select_var("tas").ifthen(F("mask.nc"))
        # Right side: simple operators
        right = F("clim.nc").time_mean()
        q = left.sub(right)

        cmd = q.get_command()
        # Should chain all operators correctly
        assert "cdo -sub" in cmd
        assert "-selname,tas" in cmd
        assert "-ifthen" in cmd
        assert "-timmean" in cmd
        assert "[" not in cmd  # No brackets
        assert "]" not in cmd


class TestBinaryOpQueryExplain:
    """Test explain functionality for binary operations."""

    def test_explain_simple_binary(self, sample_nc_file):
        """Test explaining a simple binary operation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).sub(F("clim.nc"))

        explanation = q.explain()
        assert "Binary Operation: sub" in explanation
        assert "Left operand:" in explanation
        assert "Right operand:" in explanation
        assert "test_data.nc" in explanation
        assert "clim.nc" in explanation

    def test_explain_complex_binary(self, sample_nc_file):
        """Test explaining a complex binary operation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).select_var("tas").year_mean().sub(F("clim.nc"))

        explanation = q.explain()
        assert "Binary Operation: sub" in explanation
        assert "selname" in explanation
        assert "yearmean" in explanation


class TestCDOQueryErrorHandling:
    """Test error handling in queries."""

    def test_compute_without_cdo_instance_raises(self, sample_nc_file):
        """Test that computing unbound query raises error."""
        q = F(sample_nc_file)

        with pytest.raises(CDOError) as exc_info:
            q.compute()

        assert "not bound" in str(exc_info.value).lower()

    def test_validation_errors_raised_early(self, sample_nc_file):
        """Test that validation errors are raised during query building."""
        cdo = CDO()

        # Should raise immediately, not during compute()
        with pytest.raises(CDOValidationError):
            cdo.query(sample_nc_file).select_var()


class TestOperatorSpec:
    """Test OperatorSpec dataclass."""

    def test_operator_spec_creation(self):
        """Test creating operator specs."""
        spec = OperatorSpec("yearmean")
        assert spec.name == "yearmean"
        assert spec.args == ()

    def test_operator_spec_with_args(self):
        """Test operator spec with arguments."""
        spec = OperatorSpec("selname", args=("tas", "pr"))
        assert spec.name == "selname"
        assert spec.args == ("tas", "pr")

    def test_operator_spec_to_fragment_no_args(self):
        """Test converting spec to CDO fragment without args."""
        spec = OperatorSpec("yearmean")
        fragment = spec.to_cdo_fragment()
        assert fragment == "-yearmean"

    def test_operator_spec_to_fragment_with_args(self):
        """Test converting spec to CDO fragment with args."""
        spec = OperatorSpec("selname", args=("tas", "pr"))
        fragment = spec.to_cdo_fragment()
        assert fragment == "-selname,tas,pr"

    def test_operator_spec_immutable(self):
        """Test that OperatorSpec is immutable (frozen)."""
        spec = OperatorSpec("yearmean")
        with pytest.raises(
            (AttributeError, TypeError)
        ):  # Frozen dataclass raises these
            spec.name = "monmean"  # type: ignore[misc]


class TestCDOQueryModificationOperators:
    """Test modification operators (metadata changes)."""

    def test_set_name(self, sample_nc_file):
        """Test setting variable name."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).set_name("new_var")
        assert "-setname,new_var" in q.get_command()

    def test_set_code(self, sample_nc_file):
        """Test setting variable code."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).set_code(123)
        assert "-setcode,123" in q.get_command()

    def test_set_unit(self, sample_nc_file):
        """Test setting variable unit."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).set_unit("K")
        assert "-setunit,K" in q.get_command()

    def test_set_level(self, sample_nc_file):
        """Test setting level values."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).set_level(100, 200)
        assert "-setlevel,100,200" in q.get_command()

    def test_set_level_type(self, sample_nc_file):
        """Test setting level type."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).set_level_type(100)
        assert "-setltype,100" in q.get_command()

    def test_set_grid(self, sample_nc_file):
        """Test setting grid."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).set_grid("r360x180")
        assert "-setgrid,r360x180" in q.get_command()

    def test_set_grid_type(self, sample_nc_file):
        """Test setting grid type."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).set_grid_type("lonlat")
        assert "-setgridtype,lonlat" in q.get_command()

    def test_invert_lat(self, sample_nc_file):
        """Test inverting latitude."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).invert_lat()
        assert "-invertlat" in q.get_command()

    def test_set_calendar(self, sample_nc_file):
        """Test setting calendar."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).set_calendar("standard")
        assert "-setcalendar,standard" in q.get_command()

    def test_set_time_axis(self, sample_nc_file):
        """Test setting time axis."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).set_time_axis("2000-01-01", "12:00:00", "1day")
        assert "-settaxis,2000-01-01,12:00:00,1day" in q.get_command()

    def test_set_ref_time(self, sample_nc_file):
        """Test setting reference time."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).set_ref_time("2000-01-01", "00:00:00")
        assert "-setreftime,2000-01-01,00:00:00" in q.get_command()

    def test_shift_time(self, sample_nc_file):
        """Test shifting time."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).shift_time("-6hour")
        assert "-shifttime,-6hour" in q.get_command()

    def test_set_missval(self, sample_nc_file):
        """Test setting missing value."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).set_missval(-999.0)
        assert "-setmissval,-999.0" in q.get_command()

    def test_set_const_to_miss(self, sample_nc_file):
        """Test setting constant to missing."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).set_const_to_miss(0.0)
        assert "-setctomiss,0.0" in q.get_command()

    def test_set_miss_to_const(self, sample_nc_file):
        """Test setting missing to constant."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).set_miss_to_const(0.0)
        assert "-setmisstoc,0.0" in q.get_command()

    def test_set_range_to_miss(self, sample_nc_file):
        """Test setting range to missing."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).set_range_to_miss(0.0, 100.0)
        assert "-setrtomiss,0.0,100.0" in q.get_command()

    def test_set_attribute(self, sample_nc_file):
        """Test setting attribute."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).set_attribute("tas", "units", "K")
        # Note: The quotes around the value are part of the argument
        assert '-setattribute,tas@units="K"' in q.get_command()

    def test_del_attribute(self, sample_nc_file):
        """Test deleting attribute."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).del_attribute("tas", "units")
        assert "-delattribute,tas@units" in q.get_command()


class TestCDOQueryFormatConversion:
    """Test format conversion options."""

    def test_output_format(self, sample_nc_file):
        """Test setting output format."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).output_format("nc4")
        cmd = q.get_command()
        assert "-f nc4" in cmd
        assert cmd.startswith("cdo -f nc4")

    def test_output_format_chaining(self, sample_nc_file):
        """Test output format with other operators."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).year_mean().output_format("nc4")
        cmd = q.get_command()
        assert "-f nc4" in cmd
        assert "-yearmean" in cmd
        # Options should be before operators
        assert cmd.index("-f nc4") < cmd.index("-yearmean")


@pytest.mark.integration
class TestBinaryOperationsIntegration:
    """Integration tests for binary operations with proper temp file handling.

    These tests require CDO to be installed and execute actual queries
    to verify the fix works correctly (no brackets, operator chaining + temp files).
    """

    def test_binary_sub_with_operators_executes(self, sample_nc_file_with_time):
        """Test binary subtraction with operators on left operand executes successfully."""
        import xarray as xr

        cdo = CDO()
        # Left operand has operators, right is simple file reference
        # This uses operator chaining: cdo -sub -yearmean file1 file2
        result = (
            cdo.query(sample_nc_file_with_time)
            .select_var("tas")
            .year_mean()
            .sub(F(sample_nc_file_with_time))
            .compute()
        )

        assert isinstance(result, xr.Dataset)
        # Result should have the variable
        assert "tas" in result.data_vars

    def test_binary_sub_with_operators_both_sides_executes(
        self, sample_nc_file_with_time
    ):
        """Test binary subtraction with operators on both operands executes successfully."""
        import xarray as xr

        cdo = CDO()
        # Both operands have operators
        # This uses temporary files for right operand (no brackets!)
        result = (
            cdo.query(sample_nc_file_with_time)
            .select_var("tas")
            .year_mean()
            .sub(F(sample_nc_file_with_time).select_var("tas").time_mean())
            .compute()
        )

        assert isinstance(result, xr.Dataset)
        assert "tas" in result.data_vars

    def test_nested_binary_ifthen_inside_sub_executes(self, sample_nc_file_with_time):
        """Test nested binary operations (ifthen inside sub) execute successfully.

        This specifically tests the fix for the issue where ifthen inside sub
        caused 'too many inputs' errors without proper bracket notation.
        """
        import numpy as np
        import xarray as xr

        cdo = CDO()

        # Create a mask file (all 1s to keep all data)
        mask_ds = xr.open_dataset(sample_nc_file_with_time)
        mask_data = xr.Dataset(
            {
                "mask": (
                    ["time", "lat", "lon"],
                    np.ones_like(mask_ds["tas"].values),
                )
            },
            coords=mask_ds.coords,
        )

        # Save mask to temporary file
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as mask_file:
            mask_data.to_netcdf(mask_file.name)

        try:
            # Create query with ifthen (creates BinaryOpQuery) then sub
            # This tests: cdo -sub -ifthen mask.nc data.nc other.nc
            masked_query = cdo.query(sample_nc_file_with_time).ifthen(F(mask_file.name))
            result = masked_query.sub(F(sample_nc_file_with_time)).compute()

            assert isinstance(result, xr.Dataset)
        finally:
            # Cleanup
            from pathlib import Path

            Path(mask_file.name).unlink()

    def test_anomaly_calculation_with_time_mean_executes(
        self, sample_nc_file_with_time
    ):
        """Test calculating anomalies (data minus climatology) executes successfully.

        This is a common climate science use case where bracket notation is required.
        """
        import xarray as xr

        cdo = CDO()
        # Calculate anomaly: data - time_mean(data)
        # This tests: cdo -sub data.nc -timmean data.nc
        result = (
            cdo.query(sample_nc_file_with_time)
            .select_var("tas")
            .sub(F(sample_nc_file_with_time).select_var("tas").time_mean())
            .compute()
        )

        assert isinstance(result, xr.Dataset)
        assert "tas" in result.data_vars
        # Anomalies should have some variation (not all zeros unless data is constant)

    def test_chained_binary_operations_execute(self, sample_nc_file_with_time):
        """Test chained binary operations (sub then div) execute successfully."""
        import xarray as xr

        cdo = CDO()
        # Normalized anomaly: (data - mean) / std
        # First subtract mean, then divide by a reference
        # This creates nested BinaryOpQuery structures
        result = (
            cdo.query(sample_nc_file_with_time)
            .select_var("tas")
            .sub(F(sample_nc_file_with_time).select_var("tas").time_mean())
            .div(F(sample_nc_file_with_time).select_var("tas").time_std())
            .compute()
        )

        assert isinstance(result, xr.Dataset)
        assert "tas" in result.data_vars
