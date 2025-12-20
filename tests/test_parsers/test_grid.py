"""Tests for grid parsers."""

from __future__ import annotations

import pytest

from python_cdo_wrapper.exceptions import CDOParseError
from python_cdo_wrapper.parsers.grid import GriddesParser, ZaxisdesParser

# Sample outputs from user
SAMPLE_GRIDDES_OUTPUT = """
# gridID 1
#
gridtype  = lonlat
gridsize  = 17415
datatype  = float
xsize     = 135
ysize     = 129
xname     = longitude
xlongname = "longitude"
xunits    = "degrees_east"
yname     = latitude
ylongname = "latitude"
yunits    = "degrees_north"
xfirst    = 66.625
xinc      = 0.25
yfirst    = 6.625
yinc      = 0.25
cdo    griddes: Processed 1 variable [0.02s 44MB]
"""

SAMPLE_ZAXISDES_OUTPUT = """
# zaxisID 1
#
zaxistype = surface
size      = 1
name      = sfc
longname  = "surface"
levels    = 0
cdo    zaxisdes: Processed 1 variable [0.02s 44MB]
"""

SAMPLE_ZAXISDES_PRESSURE = """
# zaxisID 1
#
zaxistype = pressure
size      = 3
name      = pressure
longname  = "Pressure"
units     = "Pa"
levels    = 100000 85000 50000
cdo    zaxisdes: Processed 1 variable [0.02s 44MB]
"""

SAMPLE_GRIDDES_ROTATED = """
# gridID 1
#
gridtype  = projection
gridsize  = 32767
xsize     = 217
ysize     = 151
xname     = rlon
xlongname = "longitude in rotated pole grid"
xunits    = "degrees"
yname     = rlat
ylongname = "latitude in rotated pole grid"
yunits    = "degrees"
xfirst    = -36.52
xinc      = 0.44
yfirst    = -26.4
yinc      = 0.44
grid_mapping = rotated_pole
grid_mapping_name = rotated_latitude_longitude
grid_north_pole_longitude = -123.34
grid_north_pole_latitude  = 79.95
cdo    griddes: Processed 1 variable [0.02s 44MB]
"""


class TestGriddesParser:
    """Test GriddesParser."""

    def test_parse_grid_info(self):
        """Test parsing grid description."""
        parser = GriddesParser()
        result = parser.parse(SAMPLE_GRIDDES_OUTPUT)

        assert result.ngrids == 1
        assert result.primary_grid is not None

    def test_parse_grid_details(self):
        """Test parsing grid details."""
        parser = GriddesParser()
        result = parser.parse(SAMPLE_GRIDDES_OUTPUT)

        grid = result.primary_grid
        assert grid.grid_id == 1
        assert grid.gridtype == "lonlat"
        assert grid.gridsize == 17415
        assert grid.datatype == "float"
        assert grid.xsize == 135
        assert grid.ysize == 129
        assert grid.xname == "longitude"
        assert grid.xlongname == "longitude"
        assert grid.xunits == "degrees_east"
        assert grid.yname == "latitude"
        assert grid.ylongname == "latitude"
        assert grid.yunits == "degrees_north"
        assert grid.xfirst == 66.625
        assert grid.xinc == 0.25
        assert grid.yfirst == 6.625
        assert grid.yinc == 0.25

    def test_grid_info_properties(self):
        """Test GridInfo properties."""
        parser = GriddesParser()
        result = parser.parse(SAMPLE_GRIDDES_OUTPUT)

        grid = result.primary_grid
        lon_range = grid.lon_range
        lat_range = grid.lat_range

        assert lon_range is not None
        assert lon_range[0] == 66.625
        assert abs(lon_range[1] - 100.125) < 0.01  # Account for floating point

        assert lat_range is not None
        assert lat_range[0] == 6.625
        assert abs(lat_range[1] - 38.625) < 0.01

    def test_parse_invalid_output_raises(self):
        """Test that invalid output raises CDOParseError."""
        parser = GriddesParser()

        with pytest.raises(CDOParseError):
            parser.parse("Invalid griddes output with no grids")

    def test_parse_rotated_grid(self):
        """Test parsing rotated projection grid."""
        parser = GriddesParser()
        result = parser.parse(SAMPLE_GRIDDES_ROTATED)

        assert result.ngrids == 1
        assert result.primary_grid is not None

        grid = result.primary_grid
        assert grid.grid_id == 1
        assert grid.gridtype == "projection"
        assert grid.gridsize == 32767
        assert grid.xsize == 217
        assert grid.ysize == 151
        assert grid.xname == "rlon"
        assert grid.xlongname == "longitude in rotated pole grid"
        assert grid.xunits == "degrees"
        assert grid.yname == "rlat"
        assert grid.ylongname == "latitude in rotated pole grid"
        assert grid.yunits == "degrees"
        assert grid.xfirst == -36.52
        assert grid.xinc == 0.44
        assert grid.yfirst == -26.4
        assert grid.yinc == 0.44

    def test_parse_rotated_grid_projection_params(self):
        """Test parsing rotated grid projection parameters."""
        parser = GriddesParser()
        result = parser.parse(SAMPLE_GRIDDES_ROTATED)

        grid = result.primary_grid
        assert grid.grid_mapping == "rotated_pole"
        assert grid.grid_mapping_name == "rotated_latitude_longitude"
        assert grid.grid_north_pole_longitude == -123.34
        assert grid.grid_north_pole_latitude == 79.95


class TestZaxisdesParser:
    """Test ZaxisdesParser."""

    def test_parse_surface_zaxis(self):
        """Test parsing surface vertical axis."""
        parser = ZaxisdesParser()
        result = parser.parse(SAMPLE_ZAXISDES_OUTPUT)

        assert result.nzaxes == 1
        assert result.primary_zaxis is not None

        zaxis = result.primary_zaxis
        assert zaxis.zaxis_id == 1
        assert zaxis.zaxistype == "surface"
        assert zaxis.size == 1
        assert zaxis.name == "sfc"
        assert zaxis.longname == "surface"
        assert zaxis.is_surface is True

    def test_parse_pressure_zaxis(self):
        """Test parsing pressure vertical axis."""
        parser = ZaxisdesParser()
        result = parser.parse(SAMPLE_ZAXISDES_PRESSURE)

        zaxis = result.primary_zaxis
        assert zaxis.zaxis_id == 1
        assert zaxis.zaxistype == "pressure"
        assert zaxis.size == 3
        assert zaxis.name == "pressure"
        assert zaxis.longname == "Pressure"
        assert zaxis.units == "Pa"
        assert zaxis.levels == [100000.0, 85000.0, 50000.0]
        assert zaxis.is_surface is False

    def test_zaxis_info_properties(self):
        """Test ZaxisInfo properties."""
        parser = ZaxisdesParser()
        result = parser.parse(SAMPLE_ZAXISDES_PRESSURE)

        zaxis = result.primary_zaxis
        level_range = zaxis.level_range

        assert level_range is not None
        assert level_range == (50000.0, 100000.0)

    def test_parse_invalid_output_raises(self):
        """Test that invalid output raises CDOParseError."""
        parser = ZaxisdesParser()

        with pytest.raises(CDOParseError):
            parser.parse("Invalid zaxisdes output")
