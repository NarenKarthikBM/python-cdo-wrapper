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

SAMPLE_GRIDDES_GAUSSIAN = """
# gridID 1
#
gridtype  = gaussian
gridsize  = 819200
xsize     = 1280
ysize     = 640
xname     = lon
xlongname = "longitude"
xunits    = "degrees_east"
yname     = lat
ylongname = "latitude"
yunits    = "degrees_north"
np        = 320
cdo    griddes: Processed 1 variable [0.02s 44MB]
"""

SAMPLE_GRIDDES_GAUSSIAN_REDUCED = """
# gridID 1
#
gridtype  = gaussian_reduced
gridsize  = 542080
xsize     = 2
ysize     = 640
xname     = lon
yname     = lat
yunits    = "degrees_north"
cdo    griddes: Processed 1 variable [0.02s 44MB]
"""

SAMPLE_GRIDDES_GENERIC = """
# gridID 1
#
gridtype  = generic
gridsize  = 64800
xsize     = 180
ysize     = 360
xname     = x
xunits    = "degrees"
yname     = y
yunits    = "degrees"
cdo    griddes: Processed 1 variable [0.02s 44MB]
"""

SAMPLE_GRIDDES_CURVILINEAR = """
# gridID 1
#
gridtype  = curvilinear
gridsize  = 48000
xsize     = 250
ysize     = 192
xname     = lon
xlongname = "longitude"
xunits    = "degrees_east"
yname     = lat
ylongname = "latitude"
yunits    = "degrees_north"
cdo    griddes: Processed 1 variable [0.02s 44MB]
"""

SAMPLE_GRIDDES_UNSTRUCTURED = """
# gridID 1
#
gridtype  = unstructured
gridsize  = 6599680
points    = 6599680
xname     = lon
xlongname = "longitude"
xunits    = "degrees_east"
yname     = lat
ylongname = "latitude"
yunits    = "degrees_north"
nvertex   = 3
cdo    griddes: Processed 1 variable [0.02s 44MB]
"""

SAMPLE_GRIDDES_UNKNOWN_ATTRS = """
# gridID 1
#
gridtype  = lonlat
gridsize  = 1000
xsize     = 50
ysize     = 20
custom_attr1 = "special_value"
custom_number = 42
custom_float = 3.14159
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

    def test_parse_gaussian_grid(self):
        """Test parsing Gaussian grid."""
        parser = GriddesParser()
        result = parser.parse(SAMPLE_GRIDDES_GAUSSIAN)

        assert result.ngrids == 1
        grid = result.primary_grid
        assert grid.gridtype == "gaussian"
        assert grid.gridsize == 819200
        assert grid.xsize == 1280
        assert grid.ysize == 640
        assert grid.np == 320
        assert grid.is_gaussian is True
        assert grid.is_regular is False

    def test_parse_gaussian_reduced_grid(self):
        """Test parsing reduced Gaussian grid."""
        parser = GriddesParser()
        result = parser.parse(SAMPLE_GRIDDES_GAUSSIAN_REDUCED)

        grid = result.primary_grid
        assert grid.gridtype == "gaussian_reduced"
        assert grid.gridsize == 542080
        assert grid.xsize == 2
        assert grid.ysize == 640
        assert grid.is_gaussian is True

    def test_parse_generic_grid(self):
        """Test parsing generic grid."""
        parser = GriddesParser()
        result = parser.parse(SAMPLE_GRIDDES_GENERIC)

        grid = result.primary_grid
        assert grid.gridtype == "generic"
        assert grid.gridsize == 64800
        assert grid.xsize == 180
        assert grid.ysize == 360
        assert grid.xname == "x"
        assert grid.yname == "y"
        assert grid.is_regular is True

    def test_parse_curvilinear_grid(self):
        """Test parsing curvilinear grid."""
        parser = GriddesParser()
        result = parser.parse(SAMPLE_GRIDDES_CURVILINEAR)

        grid = result.primary_grid
        assert grid.gridtype == "curvilinear"
        assert grid.gridsize == 48000
        assert grid.xsize == 250
        assert grid.ysize == 192
        assert grid.is_structured is True

    def test_parse_unstructured_grid(self):
        """Test parsing unstructured grid."""
        parser = GriddesParser()
        result = parser.parse(SAMPLE_GRIDDES_UNSTRUCTURED)

        grid = result.primary_grid
        assert grid.gridtype == "unstructured"
        assert grid.gridsize == 6599680
        assert grid.points == 6599680
        assert grid.nvertex == 3
        assert grid.is_unstructured is True
        assert grid.is_structured is False

    def test_parse_unknown_attributes_fallback(self):
        """Test that unknown attributes are stored in raw_attributes."""
        parser = GriddesParser()
        result = parser.parse(SAMPLE_GRIDDES_UNKNOWN_ATTRS)

        grid = result.primary_grid
        assert grid.gridtype == "lonlat"
        assert grid.gridsize == 1000

        # Check known attributes are parsed correctly
        assert grid.xsize == 50
        assert grid.ysize == 20

        # Check unknown attributes are in raw_attributes
        assert grid.raw_attributes is not None
        assert "custom_attr1" in grid.raw_attributes
        assert grid.raw_attributes["custom_attr1"] == "special_value"
        assert "custom_number" in grid.raw_attributes
        assert grid.raw_attributes["custom_number"] == "42"
        assert "custom_float" in grid.raw_attributes
        assert grid.raw_attributes["custom_float"] == "3.14159"

    def test_grid_info_properties_lonlat(self):
        """Test GridInfo convenience properties for lonlat grid."""
        parser = GriddesParser()
        result = parser.parse(SAMPLE_GRIDDES_OUTPUT)

        grid = result.primary_grid
        assert grid.is_regular is True
        assert grid.is_gaussian is False
        assert grid.is_structured is True
        assert grid.is_unstructured is False
        assert grid.is_rotated is False
        assert grid.has_projection is False

    def test_grid_info_properties_rotated(self):
        """Test GridInfo convenience properties for rotated grid."""
        parser = GriddesParser()
        result = parser.parse(SAMPLE_GRIDDES_ROTATED)

        grid = result.primary_grid
        assert grid.is_regular is True
        assert grid.is_rotated is True
        assert grid.has_projection is True


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
