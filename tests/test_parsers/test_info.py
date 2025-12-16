"""Tests for info parsers."""

from __future__ import annotations

import pytest

from python_cdo_wrapper.exceptions import CDOParseError
from python_cdo_wrapper.parsers.info import InfoParser, SinfoParser, VlistParser

# Sample outputs from user
SAMPLE_SINFO_OUTPUT = """
   File format : NetCDF4
    -1 : Institut Source   T Steptype Levels Num    Points Num Dtype : Parameter ID
     1 : unknown  unknown  v instant       1   1     17415   1  F32  : -1
   Grid coordinates :
     1 : lonlat                   : points=17415 (135x129)
                        longitude : 66.625 to 100.125 by 0.25 [degrees_east]
                         latitude : 6.625 to 38.625 by 0.25 [degrees_north]
   Vertical coordinates :
     1 : surface                  : levels=1
   Time coordinate :
                             time : 15340 steps
     RefTime =  1980-01-01 00:00:00  Units = days  Calendar = gregorian
  YYYY-MM-DD hh:mm:ss  YYYY-MM-DD hh:mm:ss  YYYY-MM-DD hh:mm:ss  YYYY-MM-DD hh:mm:ss
  1981-01-01 00:00:00  1981-01-02 00:00:00  1981-01-03 00:00:00  1981-01-04 00:00:00
  1981-01-05 00:00:00  1981-01-06 00:00:00  1981-01-07 00:00:00  1981-01-08 00:00:00
  2022-12-24 00:00:00  2022-12-25 00:00:00  2022-12-26 00:00:00  2022-12-27 00:00:00
  2022-12-28 00:00:00  2022-12-29 00:00:00  2022-12-30 00:00:00  2022-12-31 00:00:00
cdo    sinfo: Processed 1 variable over 15340 timesteps [0.02s 44MB]
"""

SAMPLE_INFO_OUTPUT = """      :       Date     Time   Level Gridsize    Miss :     Minimum        Mean     Maximum : Parameter ID
 15336 : 2022-12-27 00:00:00       0    17415       0 :      0.0000      0.0000      0.0000 : -1
 15337 : 2022-12-28 00:00:00       0    17415       0 :      0.0000      0.0000      0.0000 : -1
 15338 : 2022-12-29 00:00:00       0    17415       0 :      0.0000      0.0000      0.0000 : -1
 15339 : 2022-12-30 00:00:00       0    17415       0 :      0.0000      0.0000      0.0000 : -1
 15340 : 2022-12-31 00:00:00       0    17415       0 :      0.0000      0.0000      0.0000 : -1
"""

SAMPLE_VLIST_OUTPUT = """# vlistID 29
#
nvars    : 1
ngrids   : 1
nzaxis   : 1
nsubtypes: 0
taxisID  : 33
instID   : -1
modelID  : -1
tableID  : -1
 varID param    gridID zaxisID stypeID tsteptype flag name     longname         units
     0 -1           31      32      -1       1      0 precip   Climate Hazards group InfraRed Precipitation with Stations [mm/day]

 varID  levID fvarID flevID mvarID mlevID  index  dtype  flag  level
     0      0      0      0      0      0     -1    132     0  0

 varID  size
  0    17415
cdo    vlist: Processed 1 variable [0.02s 44MB]
"""


class TestSinfoParser:
    """Test SinfoParser."""

    def test_parse_file_format(self):
        """Test parsing file format."""
        parser = SinfoParser()
        result = parser.parse(SAMPLE_SINFO_OUTPUT)

        assert result.file_format == "NetCDF4"

    def test_parse_variables(self):
        """Test parsing variables."""
        parser = SinfoParser()
        result = parser.parse(SAMPLE_SINFO_OUTPUT)

        assert len(result.variables) == 1
        var = result.variables[0]
        assert var.var_id == 1
        assert var.institut == "unknown"
        assert var.source == "unknown"
        assert var.steptype == "instant"
        assert var.levels == 1
        assert var.points == 17415
        assert var.dtype == "F32"
        assert var.param_id == -1
        assert var.name is None  # sinfo doesn't provide variable names
        assert (
            result.var_names == []
        )  # Should return empty list when no names available

    def test_parse_grid_coordinates(self):
        """Test parsing grid coordinates."""
        parser = SinfoParser()
        result = parser.parse(SAMPLE_SINFO_OUTPUT)

        assert len(result.grid_coordinates) == 1
        grid = result.grid_coordinates[0]
        assert grid.grid_id == 1
        assert grid.gridtype == "lonlat"
        assert grid.points == 17415
        assert grid.xsize == 135
        assert grid.ysize == 129
        assert grid.longitude_start == 66.625
        assert grid.longitude_end == 100.125
        assert grid.longitude_inc == 0.25
        assert grid.longitude_units == "degrees_east"
        assert grid.latitude_start == 6.625
        assert grid.latitude_end == 38.625
        assert grid.latitude_inc == 0.25
        assert grid.latitude_units == "degrees_north"

    def test_parse_vertical_coordinates(self):
        """Test parsing vertical coordinates."""
        parser = SinfoParser()
        result = parser.parse(SAMPLE_SINFO_OUTPUT)

        assert len(result.vertical_coordinates) == 1
        vert = result.vertical_coordinates[0]
        assert vert.zaxis_id == 1
        assert vert.zaxistype == "surface"
        assert vert.levels == 1

    def test_parse_time_coordinates(self):
        """Test parsing time coordinates."""
        parser = SinfoParser()
        result = parser.parse(SAMPLE_SINFO_OUTPUT)

        time_info = result.time_info
        assert time_info.ntime == 15340
        assert time_info.ref_time == "1980-01-01 00:00:00"
        assert time_info.units == "days"
        assert time_info.calendar == "gregorian"
        assert time_info.first_timestep == "1981-01-01 00:00:00"
        assert time_info.last_timestep == "2022-12-31 00:00:00"

    def test_sinfo_result_properties(self):
        """Test SinfoResult properties."""
        parser = SinfoParser()
        result = parser.parse(SAMPLE_SINFO_OUTPUT)

        assert result.nvar == 1
        assert result.time_range == ("1981-01-01 00:00:00", "2022-12-31 00:00:00")
        assert result.primary_grid is not None
        assert result.primary_grid.gridtype == "lonlat"
        assert result.primary_vertical is not None
        assert result.primary_vertical.zaxistype == "surface"

    def test_parse_invalid_output_raises(self):
        """Test that invalid output raises CDOParseError."""
        parser = SinfoParser()

        with pytest.raises(CDOParseError):
            parser.parse("Invalid output with no structure")


class TestInfoParser:
    """Test InfoParser."""

    def test_parse_timesteps(self):
        """Test parsing timestep information."""
        parser = InfoParser()
        result = parser.parse(SAMPLE_INFO_OUTPUT)

        assert len(result.timesteps) == 5
        assert result.ntimesteps == 5

    def test_parse_timestep_details(self):
        """Test parsing individual timestep details."""
        parser = InfoParser()
        result = parser.parse(SAMPLE_INFO_OUTPUT)

        ts = result.timesteps[0]
        assert ts.timestep == 15336
        assert ts.date == "2022-12-27"
        assert ts.time == "00:00:00"
        assert ts.level == 0
        assert ts.gridsize == 17415
        assert ts.miss == 0
        assert ts.minimum == 0.0
        assert ts.mean == 0.0
        assert ts.maximum == 0.0
        assert ts.param_id == -1

    def test_info_result_properties(self):
        """Test InfoResult properties."""
        parser = InfoParser()
        result = parser.parse(SAMPLE_INFO_OUTPUT)

        first = result.first_timestep
        last = result.last_timestep

        assert first is not None
        assert first.timestep == 15336
        assert first.datetime == "2022-12-27 00:00:00"

        assert last is not None
        assert last.timestep == 15340
        assert last.datetime == "2022-12-31 00:00:00"

    def test_parse_empty_output_raises(self):
        """Test that empty output raises CDOParseError."""
        parser = InfoParser()

        with pytest.raises(CDOParseError):
            parser.parse("No valid timestep data")


class TestVlistParser:
    """Test VlistParser."""

    def test_parse_header(self):
        """Test parsing vlist header."""
        parser = VlistParser()
        result = parser.parse(SAMPLE_VLIST_OUTPUT)

        assert result.vlist_id == 29
        assert result.nvars == 1
        assert result.ngrids == 1
        assert result.nzaxis == 1
        assert result.nsubtypes == 0
        assert result.taxis_id == 33
        assert result.inst_id == -1
        assert result.model_id == -1
        assert result.table_id == -1

    def test_parse_variables(self):
        """Test parsing variable information."""
        parser = VlistParser()
        result = parser.parse(SAMPLE_VLIST_OUTPUT)

        assert len(result.variables) == 1
        var = result.variables[0]
        assert var.var_id == 0
        assert var.param == -1
        assert var.grid_id == 31
        assert var.zaxis_id == 32
        assert var.stype_id == -1
        assert var.tstep_type == 1
        assert var.flag == 0
        assert var.name == "precip"
        assert "Climate Hazards" in var.longname
        assert var.units == "mm/day"

    def test_vlist_result_properties(self):
        """Test VlistResult properties."""
        parser = VlistParser()
        result = parser.parse(SAMPLE_VLIST_OUTPUT)

        assert result.var_names == ["precip"]

        var = result.get_variable("precip")
        assert var is not None
        assert var.name == "precip"
        assert var.display_name == var.longname

        missing = result.get_variable("nonexistent")
        assert missing is None

    def test_parse_invalid_output_raises(self):
        """Test that invalid output raises CDOParseError."""
        parser = VlistParser()

        with pytest.raises(CDOParseError):
            parser.parse("Invalid vlist output")
