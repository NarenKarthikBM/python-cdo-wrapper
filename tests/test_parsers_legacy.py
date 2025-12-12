"""Tests for CDO output parsers (v0.2.x legacy API).

NOTE: This file tests the legacy parsers from parsers.py (v0.2.x API).
For Phase 2 (v1.0.0+) parser tests, see tests/test_parsers/ directory.

IMPORTANT: This file must have a unique name to avoid conflicts with
the test_parsers/ directory. If pytest shows import errors, this file
should be renamed to test_parsers_legacy.py.
"""

import pytest

# These imports resolve to the legacy parsers.py module via special
# import handling in __init__.py
from python_cdo_wrapper import (
    GriddesParser,
    PartabParser,
    ShowattsParser,
    SinfoParser,
    VctParser,
    VlistParser,
    ZaxisdesParser,
    get_supported_structured_commands,
    parse_cdo_output,
)


class TestGriddesParser:
    """Tests for GriddesParser."""

    def test_parse_lonlat_grid(self):
        """Test parsing a regular lon-lat grid."""
        output = """
gridtype = lonlat
gridsize = 64800
xsize = 360
ysize = 180
xfirst = -179.5
xinc = 1.0
yfirst = -89.5
yinc = 1.0
        """
        parser = GriddesParser()
        result = parser.parse(output)

        assert result["gridtype"] == "lonlat"
        assert result["gridsize"] == 64800
        assert result["xsize"] == 360
        assert result["ysize"] == 180
        assert result["xfirst"] == -179.5
        assert result["xinc"] == 1.0
        assert result["yfirst"] == -89.5
        assert result["yinc"] == 1.0

    def test_parse_grid_with_comments(self):
        """Test parsing grid with comment lines."""
        output = """
# Grid description
gridtype = lonlat
gridsize = 100
xsize = 10
ysize = 10
        """
        parser = GriddesParser()
        result = parser.parse(output)

        assert result["gridtype"] == "lonlat"
        assert result["gridsize"] == 100
        assert "# Grid description" not in result


class TestZaxisdesParser:
    """Tests for ZaxisdesParser."""

    def test_parse_pressure_levels(self):
        """Test parsing pressure level axis."""
        output = """
zaxistype = pressure
size = 4
levels = 1000 850 500 250
        """
        parser = ZaxisdesParser()
        result = parser.parse(output)

        assert result["zaxistype"] == "pressure"
        assert result["size"] == 4
        assert result["levels"] == [1000.0, 850.0, 500.0, 250.0]

    def test_parse_with_vct(self):
        """Test parsing axis with vertical coordinate table."""
        output = """
zaxistype = hybrid
size = 3
vctsize = 6
vct = 0.0 0.1 0.5 1.0 2.0 3.0
        """
        parser = ZaxisdesParser()
        result = parser.parse(output)

        assert result["zaxistype"] == "hybrid"
        assert result["size"] == 3
        assert result["vctsize"] == 6
        assert len(result["vct"]) == 6


class TestSinfoParser:
    """Tests for SinfoParser."""

    def test_parse_basic_info(self):
        """Test parsing basic dataset information."""
        output = """
File format: NetCDF
   -1 : Date     Time   Level Gridsize    Num    Dtype : Parameter name
    1 : 2020-01-01 00:00:00       0   518400      1  F64    : tas
    2 : 2020-01-01 00:00:00       0   518400      2  F64    : pr
        """
        parser = SinfoParser()
        result = parser.parse(output)

        assert "metadata" in result
        assert result["metadata"]["format"] == "NetCDF"
        assert "variables" in result
        assert len(result["variables"]) == 2

        # Test first variable (tas)
        assert result["variables"][0]["name"] == "tas"
        assert result["variables"][0]["date"] == "2020-01-01"
        assert result["variables"][0]["time"] == "00:00:00"
        assert result["variables"][0]["level"] == 0
        assert result["variables"][0]["gridsize"] == 518400
        assert result["variables"][0]["num"] == 1
        assert result["variables"][0]["dtype"] == "F64"

        # Test second variable (pr)
        assert result["variables"][1]["name"] == "pr"
        assert result["variables"][1]["date"] == "2020-01-01"
        assert result["variables"][1]["time"] == "00:00:00"
        assert result["variables"][1]["level"] == 0
        assert result["variables"][1]["gridsize"] == 518400
        assert result["variables"][1]["num"] == 2
        assert result["variables"][1]["dtype"] == "F64"

    def test_parse_empty_variables(self):
        """Test parsing info with no variables."""
        output = """
File format: NetCDF
   -1 : Date     Time   Level Gridsize    Num    Dtype : Parameter name
        """
        parser = SinfoParser()
        result = parser.parse(output)

        assert "variables" in result
        assert len(result["variables"]) == 0

    def test_parse_temporal_data(self):
        """Test parsing temporal information from multiple timesteps."""
        output = """
File format: NetCDF4
   -1 : Date     Time   Level Gridsize    Num    Dtype : Parameter name
    1 : 1901-01-01 00:00:00       0   135360      1  F32    : rf
    2 : 1901-01-02 00:00:00       0   135360      1  F32    : rf
    3 : 1901-01-03 00:00:00       0   135360      1  F32    : rf
    4 : 2019-12-31 00:00:00       0   135360      1  F32    : rf
        """
        parser = SinfoParser()
        result = parser.parse(output)

        assert "metadata" in result
        assert result["metadata"]["format"] == "NetCDF4"
        assert "variables" in result
        assert len(result["variables"]) == 4

        # Test first timestep
        assert result["variables"][0]["name"] == "rf"
        assert result["variables"][0]["date"] == "1901-01-01"
        assert result["variables"][0]["time"] == "00:00:00"

        # Test last timestep
        assert result["variables"][3]["name"] == "rf"
        assert result["variables"][3]["date"] == "2019-12-31"
        assert result["variables"][3]["time"] == "00:00:00"

        # Verify all have consistent gridsize and dtype
        for var in result["variables"]:
            assert var["gridsize"] == 135360
            assert var["dtype"] == "F32"

    def test_parse_with_string_level(self):
        """Test parsing when level is a string (e.g., 'surface')."""
        output = """
File format: NetCDF
   -1 : Date     Time   Level Gridsize    Num    Dtype : Parameter name
    1 : 2020-01-01 00:00:00 surface 10000      1  F64    : tas
        """
        parser = SinfoParser()
        result = parser.parse(output)

        assert len(result["variables"]) == 1
        var = result["variables"][0]
        assert var["name"] == "tas"
        assert var["level"] == "surface"
        assert var["gridsize"] == 10000
        assert var["dtype"] == "F64"

    def test_parse_complete_sinfo_output(self):
        """Test parsing complete sinfo output with all sections."""
        output = """File format : NetCDF4
    -1 : Institut Source   T Steptype Levels Num    Points Num Dtype : Parameter ID
     1 : unknown  unknown  v instant       1   1     17415   1  F32  : 260
   Grid coordinates :
     1 : lonlat                   : points=17415 (135x129)
                              lon : 66.5 to 100 by 0.25 [degrees_east]
                              lat : 6.5 to 38.5 by 0.25 [degrees_north]
   Vertical coordinates :
     1 : surface                  : levels=1
   Time coordinate :
                             time : 43464 steps
     RefTime =  1901-01-01 00:00:00  Units = hours  Calendar = standard
  YYYY-MM-DD hh:mm:ss  YYYY-MM-DD hh:mm:ss  YYYY-MM-DD hh:mm:ss  YYYY-MM-DD hh:mm:ss
  1901-01-01 00:00:00  1901-01-02 00:00:00  1901-01-03 00:00:00  1901-01-04 00:00:00
  1901-01-05 00:00:00  1901-01-06 00:00:00  1901-01-07 00:00:00  1901-01-08 00:00:00
  ................................................................................
  2019-12-28 00:00:00  2019-12-29 00:00:00  2019-12-30 00:00:00  2019-12-31 00:00:00
        """
        parser = SinfoParser()
        result = parser.parse(output)

        # Test metadata
        assert result["metadata"]["format"] == "NetCDF4"

        # Test variables
        assert len(result["variables"]) == 1
        var = result["variables"][0]
        assert var["name"] == "260"
        assert var["institut"] == "unknown"
        assert var["source"] == "unknown"
        assert var["table"] == "v"
        assert var["steptype"] == "instant"
        assert var["levels"] == 1
        assert var["points"] == 17415
        assert var["dtype"] == "F32"

        # Test grid information
        assert result["grid"]["id"] == 1
        assert result["grid"]["type"] == "lonlat"
        assert result["grid"]["points"] == 17415
        assert result["grid"]["xsize"] == 135
        assert result["grid"]["ysize"] == 129
        assert result["grid"]["lon_start"] == 66.5
        assert result["grid"]["lon_end"] == 100.0
        assert result["grid"]["lon_resolution"] == 0.25
        assert result["grid"]["lon_units"] == "degrees_east"
        assert result["grid"]["lat_start"] == 6.5
        assert result["grid"]["lat_end"] == 38.5
        assert result["grid"]["lat_resolution"] == 0.25
        assert result["grid"]["lat_units"] == "degrees_north"

        # Test vertical coordinates
        assert result["vertical"]["id"] == 1
        assert result["vertical"]["type"] == "surface"
        assert result["vertical"]["levels"] == 1

        # Test time coordinates
        assert result["time"]["steps"] == 43464
        assert result["time"]["reftime"] == "1901-01-01 00:00:00"
        assert result["time"]["units"] == "hours"
        assert result["time"]["calendar"] == "standard"
        assert result["time"]["first_timestep"] == "1901-01-01 00:00:00"
        assert result["time"]["last_timestep"] == "2019-12-31 00:00:00"
        assert result["time"]["has_omitted_timesteps"] is True
        assert "time_resolution" in result["time"]
        assert result["time"]["time_resolution"]["regular"] is True
        assert result["time"]["time_resolution"]["interval"] == "1 day"

    def test_parse_grid_coordinates_only(self):
        """Test parsing just grid coordinates section."""
        output = """
   Grid coordinates :
     1 : lonlat                   : points=64800 (360x180)
                              lon : -179.5 to 179.5 by 1.0 [degrees_east]
                              lat : -89.5 to 89.5 by 1.0 [degrees_north]
        """
        parser = SinfoParser()
        result = parser.parse(output)

        assert result["grid"]["id"] == 1
        assert result["grid"]["type"] == "lonlat"
        assert result["grid"]["points"] == 64800
        assert result["grid"]["xsize"] == 360
        assert result["grid"]["ysize"] == 180
        assert result["grid"]["lon_resolution"] == 1.0
        assert result["grid"]["lat_resolution"] == 1.0

    def test_parse_time_coordinates_with_resolution(self):
        """Test parsing time coordinates and calculating resolution."""
        output = """
   Time coordinate :
                             time : 365 steps
     RefTime =  2020-01-01 00:00:00  Units = days  Calendar = gregorian
  YYYY-MM-DD hh:mm:ss  YYYY-MM-DD hh:mm:ss  YYYY-MM-DD hh:mm:ss  YYYY-MM-DD hh:mm:ss
  2020-01-01 00:00:00  2020-01-02 00:00:00  2020-01-03 00:00:00  2020-01-04 00:00:00
  2020-01-05 00:00:00  2020-01-06 00:00:00  2020-01-07 00:00:00  2020-01-08 00:00:00
        """
        parser = SinfoParser()
        result = parser.parse(output)

        assert result["time"]["steps"] == 365
        assert result["time"]["reftime"] == "2020-01-01 00:00:00"
        assert result["time"]["units"] == "days"
        assert result["time"]["calendar"] == "gregorian"
        assert result["time"]["first_timestep"] == "2020-01-01 00:00:00"
        assert "time_resolution" in result["time"]
        assert result["time"]["time_resolution"]["regular"] is True
        assert result["time"]["time_resolution"]["interval"] == "1 day"

    def test_parse_time_coordinates_hourly(self):
        """Test parsing hourly time resolution."""
        output = """
   Time coordinate :
                             time : 24 steps
     RefTime =  2020-01-01 00:00:00  Units = hours  Calendar = standard
  YYYY-MM-DD hh:mm:ss  YYYY-MM-DD hh:mm:ss  YYYY-MM-DD hh:mm:ss  YYYY-MM-DD hh:mm:ss
  2020-01-01 00:00:00  2020-01-01 01:00:00  2020-01-01 02:00:00  2020-01-01 03:00:00
  2020-01-01 04:00:00  2020-01-01 05:00:00  2020-01-01 06:00:00  2020-01-01 07:00:00
        """
        parser = SinfoParser()
        result = parser.parse(output)

        assert result["time"]["steps"] == 24
        assert result["time"]["time_resolution"]["regular"] is True
        assert result["time"]["time_resolution"]["interval"] == "1 hour"
        assert result["time"]["time_resolution"]["interval_seconds"] == 3600

    def test_parse_time_coordinates_6hourly(self):
        """Test parsing 6-hourly time resolution."""
        output = """
   Time coordinate :
                             time : 4 steps
     RefTime =  2020-01-01 00:00:00  Units = hours  Calendar = standard
  YYYY-MM-DD hh:mm:ss  YYYY-MM-DD hh:mm:ss  YYYY-MM-DD hh:mm:ss  YYYY-MM-DD hh:mm:ss
  2020-01-01 00:00:00  2020-01-01 06:00:00  2020-01-01 12:00:00  2020-01-01 18:00:00
        """
        parser = SinfoParser()
        result = parser.parse(output)

        assert result["time"]["time_resolution"]["regular"] is True
        assert result["time"]["time_resolution"]["interval"] == "6 hours"
        assert result["time"]["time_resolution"]["interval_seconds"] == 21600

    def test_parse_vertical_coordinates_surface(self):
        """Test parsing surface vertical coordinates."""
        output = """
   Vertical coordinates :
     1 : surface                  : levels=1
        """
        parser = SinfoParser()
        result = parser.parse(output)

        assert result["vertical"]["id"] == 1
        assert result["vertical"]["type"] == "surface"
        assert result["vertical"]["levels"] == 1

    def test_parse_vertical_coordinates_pressure(self):
        """Test parsing pressure level vertical coordinates."""
        output = """
   Vertical coordinates :
     1 : pressure                 : levels=4
        """
        parser = SinfoParser()
        result = parser.parse(output)

        assert result["vertical"]["id"] == 1
        assert result["vertical"]["type"] == "pressure"
        assert result["vertical"]["levels"] == 4

    def test_parse_new_format_variable_line(self):
        """Test parsing new format variable line with institut/source fields."""
        output = """
File format : NetCDF4
    -1 : Institut Source   T Steptype Levels Num    Points Num Dtype : Parameter ID
     1 : ECMWF    ERA5    v instant       1   1     259920   1  F64  : tas
        """
        parser = SinfoParser()
        result = parser.parse(output)

        assert len(result["variables"]) == 1
        var = result["variables"][0]
        assert var["name"] == "tas"
        assert var["institut"] == "ECMWF"
        assert var["source"] == "ERA5"
        assert var["table"] == "v"
        assert var["steptype"] == "instant"
        assert var["levels"] == 1
        assert var["points"] == 259920
        assert var["dtype"] == "F64"

    def test_empty_sections(self):
        """Test that empty sections are handled gracefully."""
        output = """
File format : NetCDF
   -1 : Institut Source   T Steptype Levels Num    Points Num Dtype : Parameter ID
        """
        parser = SinfoParser()
        result = parser.parse(output)

        assert result["metadata"]["format"] == "NetCDF"
        assert len(result["variables"]) == 0
        assert result["grid"] == {}
        assert result["vertical"] == {}
        assert result["time"] == {}


class TestVlistParser:
    """Tests for VlistParser."""

    def test_parse_variable_list(self):
        """Test parsing variable list."""
        output = """
temperature 500 hPa
precipitation surface
wind_speed 10m
        """
        parser = VlistParser()
        result = parser.parse(output)

        assert isinstance(result, list)
        assert len(result) == 3


class TestPartabParser:
    """Tests for PartabParser."""

    def test_parse_parameter_table(self):
        """Test parsing parameter table."""
        output = """
1 | temperature | K | Air temperature
2 | pressure | Pa | Air pressure
        """
        parser = PartabParser()
        result = parser.parse(output)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["code"] == "1"
        assert result[0]["name"] == "temperature"
        assert result[0]["units"] == "K"

    def test_parse_space_separated(self):
        """Test parsing space-separated format."""
        output = """
101 temp K
102 pres Pa
        """
        parser = PartabParser()
        result = parser.parse(output)

        assert isinstance(result, list)
        assert len(result) == 2


class TestVctParser:
    """Tests for VctParser."""

    def test_parse_vct_values(self):
        """Test parsing VCT values."""
        output = """
0.0 0.1 0.2 0.5
1.0 2.0 3.0 5.0
        """
        parser = VctParser()
        result = parser.parse(output)

        assert "vct" in result
        assert len(result["vct"]) == 8
        assert result["vct"][0] == 0.0
        assert result["vct"][-1] == 5.0

    def test_parse_single_line_vct(self):
        """Test parsing VCT on single line."""
        output = "0.0 1.0 2.0 3.0"
        parser = VctParser()
        result = parser.parse(output)

        assert len(result["vct"]) == 4


class TestParseCdoOutput:
    """Tests for parse_cdo_output function."""

    def test_parse_griddes_command(self):
        """Test parsing griddes command output."""
        output = """
gridtype = lonlat
gridsize = 100
        """
        result = parse_cdo_output("griddes data.nc", output)

        assert isinstance(result, dict)
        assert result["gridtype"] == "lonlat"

    def test_parse_with_command_prefix(self):
        """Test parsing with command prefix."""
        output = """
gridtype = lonlat
        """
        result = parse_cdo_output("-griddes data.nc", output)

        assert isinstance(result, dict)

    def test_parse_unsupported_command(self):
        """Test parsing unsupported command raises error."""
        with pytest.raises(ValueError, match="No parser available"):
            parse_cdo_output("unsupported_cmd data.nc", "some output")

    def test_parse_empty_command(self):
        """Test parsing empty command raises error."""
        with pytest.raises(ValueError, match="Empty command"):
            parse_cdo_output("", "some output")


class TestGetSupportedStructuredCommands:
    """Tests for get_supported_structured_commands function."""

    def test_returns_frozenset(self):
        """Test that function returns a frozenset."""
        commands = get_supported_structured_commands()
        assert isinstance(commands, frozenset)

    def test_contains_expected_commands(self):
        """Test that expected commands are included."""
        commands = get_supported_structured_commands()
        expected = {"griddes", "sinfo", "showatts", "zaxisdes", "vct"}
        assert expected.issubset(commands)

    def test_immutable(self):
        """Test that returned set is immutable."""
        commands = get_supported_structured_commands()
        with pytest.raises(AttributeError):
            commands.add("new_command")  # type: ignore


class TestGriddesParserEdgeCases:
    """Edge case tests for GriddesParser helper methods."""

    def test_is_float_with_integer_string(self):
        """Test _is_float with integer string."""
        assert GriddesParser._is_float("42") is True

    def test_is_float_with_negative(self):
        """Test _is_float with negative number."""
        assert GriddesParser._is_float("-3.14") is True

    def test_is_float_with_scientific_notation(self):
        """Test _is_float with scientific notation."""
        assert GriddesParser._is_float("1.5e-10") is True

    def test_is_float_with_invalid_string(self):
        """Test _is_float with non-numeric string."""
        assert GriddesParser._is_float("not_a_number") is False
        assert GriddesParser._is_float("") is False

    def test_parse_array_with_mixed_values(self):
        """Test _parse_array with mixed valid and invalid values."""
        result = GriddesParser._parse_array("1.0 invalid 2.5 3.0")
        assert result == [1.0, 2.5, 3.0]

    def test_parse_array_empty_string(self):
        """Test _parse_array with empty string."""
        result = GriddesParser._parse_array("")
        assert result == []

    def test_parse_array_all_invalid(self):
        """Test _parse_array with all invalid values."""
        result = GriddesParser._parse_array("not valid at all")
        assert result == []

    def test_parse_empty_lines_and_whitespace(self):
        """Test parsing with empty lines and extra whitespace."""
        output = """

gridtype = lonlat

gridsize = 100

        """
        parser = GriddesParser()
        result = parser.parse(output)
        assert result["gridtype"] == "lonlat"
        assert result["gridsize"] == 100


class TestZaxisdesParserEdgeCases:
    """Edge case tests for ZaxisdesParser."""

    def test_parse_with_lbounds(self):
        """Test parsing with lbounds array."""
        output = """
zaxistype = hybrid
lbounds = 0.0 100.0 500.0 1000.0
        """
        parser = ZaxisdesParser()
        result = parser.parse(output)
        assert "lbounds" in result
        assert len(result["lbounds"]) == 4

    def test_parse_with_ubounds(self):
        """Test parsing with ubounds array."""
        output = """
zaxistype = hybrid
ubounds = 100.0 500.0 1000.0 1500.0
        """
        parser = ZaxisdesParser()
        result = parser.parse(output)
        assert "ubounds" in result
        assert len(result["ubounds"]) == 4

    def test_parse_with_all_arrays(self):
        """Test parsing with levels, vct, lbounds, and ubounds."""
        output = """
zaxistype = hybrid
size = 2
levels = 1 2
vct = 0.0 0.5 1.0
lbounds = 0.5 1.5
ubounds = 1.5 2.5
        """
        parser = ZaxisdesParser()
        result = parser.parse(output)
        assert result["size"] == 2
        assert len(result["levels"]) == 2
        assert len(result["vct"]) == 3
        assert len(result["lbounds"]) == 2
        assert len(result["ubounds"]) == 2

    def test_is_float_edge_cases(self):
        """Test _is_float with edge cases."""
        assert ZaxisdesParser._is_float("0.0") is True
        assert ZaxisdesParser._is_float("-0.0") is True
        assert ZaxisdesParser._is_float("inf") is True
        assert ZaxisdesParser._is_float("nan") is True
        assert ZaxisdesParser._is_float("") is False
        assert ZaxisdesParser._is_float("abc") is False

    def test_parse_array_with_invalid_values(self):
        """Test _parse_array skips invalid values."""
        result = ZaxisdesParser._parse_array("1.0 bad 2.0 invalid 3.0")
        assert result == [1.0, 2.0, 3.0]

    def test_parse_empty_output(self):
        """Test parsing empty zaxisdes output."""
        output = ""
        parser = ZaxisdesParser()
        result = parser.parse(output)
        assert isinstance(result, dict)
        assert len(result) == 0


class TestSinfoParserEdgeCases:
    """Edge case tests for SinfoParser."""

    def test_parse_variable_line_insufficient_fields(self):
        """Test _parse_variable_line with insufficient fields."""
        # Line with too few fields
        result = SinfoParser._parse_variable_line("1 : field1 : varname")
        # Should still extract varname
        assert result is not None
        assert result["name"] == "varname"

    def test_parse_variable_line_no_colons(self):
        """Test _parse_variable_line with no colons."""
        result = SinfoParser._parse_variable_line("no colons here")
        assert result is None

    def test_parse_variable_line_empty_parameter(self):
        """Test _parse_variable_line with empty parameter name."""
        result = SinfoParser._parse_variable_line("1 : fields : ")
        assert result is None

    def test_parse_variable_line_parameter_name_header(self):
        """Test _parse_variable_line skips header lines."""
        result = SinfoParser._parse_variable_line("1 : fields : Parameter name")
        assert result is None
        result2 = SinfoParser._parse_variable_line("1 : fields : Parameter ID")
        assert result2 is None

    def test_parse_variable_line_old_format_insufficient_fields(self):
        """Test old format with too few fields."""
        result = SinfoParser._parse_variable_line("1 : field1 field2 : varname")
        assert result is not None
        assert result["name"] == "varname"

    def test_parse_variable_line_non_numeric_values(self):
        """Test variable line with non-numeric values where numbers expected."""
        line = "1 : inst src t step N/A N/A N/A N/A dtype : var"
        result = SinfoParser._parse_variable_line(line)
        assert result is not None
        assert result["name"] == "var"
        assert result["levels"] == "N/A"

    def test_parse_grid_line_empty(self):
        """Test _parse_grid_line with empty line."""
        grid_info = {}
        SinfoParser._parse_grid_line("", grid_info, None)
        assert grid_info == {}

    def test_parse_grid_line_section_header(self):
        """Test _parse_grid_line with section header."""
        grid_info = {}
        SinfoParser._parse_grid_line("Grid coordinates :", grid_info, None)
        # Should not crash, just return without changes
        assert grid_info == {}

    def test_parse_grid_line_malformed_coord(self):
        """Test _parse_grid_line with malformed coordinate line."""
        grid_info = {}
        # Missing 'by' keyword
        SinfoParser._parse_grid_line("lon : 0 to 360 degrees", grid_info, None)
        # Should not crash, grid_info remains unchanged
        assert "lon_start" not in grid_info

    def test_parse_grid_line_incomplete_points_info(self):
        """Test _parse_grid_line without dimensions."""
        grid_info = {}
        SinfoParser._parse_grid_line("1 : lonlat : points=1000", grid_info, 1)
        assert grid_info.get("points") == 1000
        assert "xsize" not in grid_info

    def test_parse_vertical_line_empty(self):
        """Test _parse_vertical_line with empty line."""
        vertical_info = {}
        SinfoParser._parse_vertical_line("", vertical_info, None)
        assert vertical_info == {}

    def test_parse_vertical_line_section_header(self):
        """Test _parse_vertical_line with section header."""
        vertical_info = {}
        SinfoParser._parse_vertical_line("Vertical coordinates :", vertical_info, None)
        assert vertical_info == {}

    def test_parse_vertical_line_no_levels_info(self):
        """Test _parse_vertical_line without levels info."""
        vertical_info = {}
        SinfoParser._parse_vertical_line("1 : pressure", vertical_info, 1)
        assert vertical_info.get("id") == 1
        assert vertical_info.get("type") == "pressure"
        assert "levels" not in vertical_info

    def test_parse_time_line_empty(self):
        """Test _parse_time_line with empty line."""
        time_info = {}
        time_buffer = []
        SinfoParser._parse_time_line("", time_info, time_buffer)
        assert time_info == {}
        assert time_buffer == []

    def test_parse_time_line_section_header(self):
        """Test _parse_time_line with section header."""
        time_info = {}
        time_buffer = []
        SinfoParser._parse_time_line("Time coordinate :", time_info, time_buffer)
        assert time_info == {}

    def test_parse_time_line_partial_reftime(self):
        """Test _parse_time_line with only RefTime (no Units/Calendar)."""
        time_info = {}
        time_buffer = []
        SinfoParser._parse_time_line(
            "RefTime = 2020-01-01 12:00:00", time_info, time_buffer
        )
        assert time_info.get("reftime") == "2020-01-01 12:00:00"
        assert "units" not in time_info
        assert "calendar" not in time_info

    def test_parse_time_line_dots_indicator(self):
        """Test _parse_time_line with dots indicating omitted timesteps."""
        time_info = {}
        time_buffer = []
        SinfoParser._parse_time_line("..................", time_info, time_buffer)
        assert time_info.get("has_omitted_timesteps") is True

    def test_parse_time_line_mixed_content(self):
        """Test _parse_time_line with timesteps on same line as other text."""
        time_info = {}
        time_buffer = []
        line = "Some text 2020-01-01 00:00:00 more text 2020-01-02 00:00:00"
        SinfoParser._parse_time_line(line, time_info, time_buffer)
        assert len(time_buffer) == 1
        assert "2020-01-01 00:00:00" in time_buffer[0]

    def test_finalize_time_parsing_empty_buffer(self):
        """Test _finalize_time_parsing with empty buffer."""
        time_info = {}
        time_buffer = []
        SinfoParser._finalize_time_parsing(time_info, time_buffer)
        assert "timesteps" not in time_info

    def test_finalize_time_parsing_single_timestep(self):
        """Test _finalize_time_parsing with single timestep."""
        time_info = {}
        time_buffer = ["2020-01-01 00:00:00"]
        SinfoParser._finalize_time_parsing(time_info, time_buffer)
        assert time_info["first_timestep"] == "2020-01-01 00:00:00"
        assert time_info["last_timestep"] == "2020-01-01 00:00:00"
        # No resolution with single timestep
        assert "time_resolution" not in time_info

    def test_calculate_time_resolution_irregular(self):
        """Test _calculate_time_resolution with irregular spacing."""
        timesteps = [
            "2020-01-01 00:00:00",
            "2020-01-01 01:00:00",
            "2020-01-01 03:00:00",  # 2-hour gap
            "2020-01-01 04:00:00",
        ]
        result = SinfoParser._calculate_time_resolution(timesteps)
        assert result["regular"] is False
        assert result["interval"] == "irregular"

    def test_calculate_time_resolution_12hourly(self):
        """Test _calculate_time_resolution with 12-hour interval."""
        timesteps = [
            "2020-01-01 00:00:00",
            "2020-01-01 12:00:00",
            "2020-01-02 00:00:00",
            "2020-01-02 12:00:00",
        ]
        result = SinfoParser._calculate_time_resolution(timesteps)
        assert result["regular"] is True
        assert result["interval"] == "12 hours"
        assert result["interval_seconds"] == 43200

    def test_calculate_time_resolution_multi_day(self):
        """Test _calculate_time_resolution with multi-day interval."""
        timesteps = [
            "2020-01-01 00:00:00",
            "2020-01-03 00:00:00",  # 2 days
            "2020-01-05 00:00:00",
        ]
        result = SinfoParser._calculate_time_resolution(timesteps)
        assert result["regular"] is True
        assert result["interval"] == "2 days"

    def test_calculate_time_resolution_invalid_dates(self):
        """Test _calculate_time_resolution with invalid date format."""
        timesteps = ["invalid-date", "also-invalid"]
        result = SinfoParser._calculate_time_resolution(timesteps)
        assert result["regular"] is False
        assert result["interval"] == "unknown"

    def test_calculate_time_resolution_single_timestep(self):
        """Test _calculate_time_resolution with single timestep."""
        timesteps = ["2020-01-01 00:00:00"]
        result = SinfoParser._calculate_time_resolution(timesteps)
        # Should handle gracefully with insufficient data
        assert result == {}

    def test_calculate_time_resolution_custom_seconds(self):
        """Test _calculate_time_resolution with custom interval."""
        timesteps = [
            "2020-01-01 00:00:00",
            "2020-01-01 00:05:00",  # 300 seconds
            "2020-01-01 00:10:00",
        ]
        result = SinfoParser._calculate_time_resolution(timesteps)
        assert result["regular"] is True
        assert result["interval"] == "300.0 seconds"


class TestVlistParserEdgeCases:
    """Edge case tests for VlistParser."""

    def test_parse_with_comments(self):
        """Test parsing with comment lines."""
        output = """
# This is a comment
variable1 info
# Another comment
variable2 info
        """
        parser = VlistParser()
        result = parser.parse(output)
        assert len(result) == 2

    def test_parse_empty_output(self):
        """Test parsing empty output."""
        parser = VlistParser()
        result = parser.parse("")
        assert isinstance(result, list)
        assert len(result) == 0

    def test_parse_variable_info_empty_line(self):
        """Test _parse_variable_info with empty line."""
        result = VlistParser._parse_variable_info("")
        assert result is None

    def test_parse_variable_info_whitespace_only(self):
        """Test _parse_variable_info with whitespace."""
        result = VlistParser._parse_variable_info("   ")
        assert result is None

    def test_parse_variable_info_normal(self):
        """Test _parse_variable_info with normal input."""
        result = VlistParser._parse_variable_info("temp 500hPa data")
        assert result is not None
        assert result["raw"] == "temp 500hPa data"
        assert len(result["parts"]) == 3


class TestShowattsParserEdgeCases:
    """Edge case tests for ShowattsParser."""

    def test_parse_with_quoted_values(self):
        """Test parsing attributes with quoted values."""
        output = """
temperature attributes:
long_name = "Air Temperature"
units = "K"
description = 'Temperature in Kelvin'
        """
        parser = ShowattsParser()
        result = parser.parse(output)
        assert "temperature" in result
        assert result["temperature"]["long_name"] == "Air Temperature"
        assert result["temperature"]["units"] == "K"
        assert result["temperature"]["description"] == "Temperature in Kelvin"

    def test_parse_multiple_variables(self):
        """Test parsing attributes for multiple variables."""
        output = """
temperature attributes:
units = K
long_name = Temperature

pressure attributes:
units = Pa
long_name = Pressure
        """
        parser = ShowattsParser()
        result = parser.parse(output)
        assert "temperature" in result
        assert "pressure" in result
        assert result["temperature"]["units"] == "K"
        assert result["pressure"]["units"] == "Pa"

    def test_parse_with_empty_lines(self):
        """Test parsing with empty lines."""
        output = """
temperature attributes:
units = K

long_name = Temperature

        """
        parser = ShowattsParser()
        result = parser.parse(output)
        assert result["temperature"]["units"] == "K"
        assert result["temperature"]["long_name"] == "Temperature"

    def test_parse_attribute_without_equals(self):
        """Test parsing line without equals sign (should skip)."""
        output = """
temperature attributes:
units = K
invalid line without equals
long_name = Temperature
        """
        parser = ShowattsParser()
        result = parser.parse(output)
        # Should skip invalid line
        assert "units" in result["temperature"]
        assert "long_name" in result["temperature"]

    def test_parse_malformed_section_header(self):
        """Test parsing with various section header formats."""
        output = """
Temperature Attributes:
units = K

Pressure:
units = Pa
        """
        parser = ShowattsParser()
        result = parser.parse(output)
        # Should handle case variations
        assert len(result) >= 1

    def test_parse_empty_output(self):
        """Test parsing empty output."""
        parser = ShowattsParser()
        result = parser.parse("")
        assert isinstance(result, dict)
        assert len(result) == 0


class TestPartabParserEdgeCases:
    """Edge case tests for PartabParser."""

    def test_parse_with_comments(self):
        """Test parsing with comment lines."""
        output = """
# Parameter table
1 | temp | K | Temperature
# More comments
2 | pres | Pa | Pressure
        """
        parser = PartabParser()
        result = parser.parse(output)
        assert len(result) == 2

    def test_parse_parameter_line_single_part(self):
        """Test _parse_parameter_line with single field."""
        result = PartabParser._parse_parameter_line("code_only")
        assert result is not None
        assert result["code"] == "code_only"
        assert "name" not in result

    def test_parse_parameter_line_two_parts(self):
        """Test _parse_parameter_line with two fields."""
        result = PartabParser._parse_parameter_line("1 | temp")
        assert result["code"] == "1"
        assert result["name"] == "temp"
        assert "units" not in result

    def test_parse_parameter_line_three_parts(self):
        """Test _parse_parameter_line with three fields."""
        result = PartabParser._parse_parameter_line("1 | temp | K")
        assert result["code"] == "1"
        assert result["name"] == "temp"
        assert result["units"] == "K"
        assert "description" not in result

    def test_parse_parameter_line_long_description(self):
        """Test _parse_parameter_line with multi-word description."""
        result = PartabParser._parse_parameter_line(
            "1 | temp | K | Air temperature at 2m"
        )
        assert result["description"] == "Air temperature at 2m"

    def test_parse_parameter_line_empty(self):
        """Test _parse_parameter_line with empty string."""
        result = PartabParser._parse_parameter_line("")
        assert result is None

    def test_parse_space_separated_no_pipes(self):
        """Test space-separated format without pipes."""
        output = """
101 temperature K
102 pressure Pa
        """
        parser = PartabParser()
        result = parser.parse(output)
        assert len(result) == 2
        assert result[0]["code"] == "101"

    def test_parse_empty_output(self):
        """Test parsing empty output."""
        parser = PartabParser()
        result = parser.parse("")
        assert isinstance(result, list)
        assert len(result) == 0


class TestVctParserEdgeCases:
    """Edge case tests for VctParser."""

    def test_parse_with_comments(self):
        """Test parsing with comment lines."""
        output = """
# VCT values
0.0 1.0 2.0
# More data
3.0 4.0 5.0
        """
        parser = VctParser()
        result = parser.parse(output)
        assert len(result["vct"]) == 6

    def test_parse_with_invalid_values(self):
        """Test parsing with some invalid values."""
        output = """
0.0 invalid 1.0 bad 2.0
        """
        parser = VctParser()
        result = parser.parse(output)
        # Should skip invalid values
        assert len(result["vct"]) == 3
        assert result["vct"] == [0.0, 1.0, 2.0]

    def test_parse_empty_output(self):
        """Test parsing empty output."""
        parser = VctParser()
        result = parser.parse("")
        assert isinstance(result, dict)
        assert "vct" in result
        assert len(result["vct"]) == 0

    def test_parse_negative_values(self):
        """Test parsing negative VCT values."""
        output = "-1.0 -0.5 0.0 0.5 1.0"
        parser = VctParser()
        result = parser.parse(output)
        assert result["vct"][0] == -1.0
        assert result["vct"][-1] == 1.0

    def test_parse_scientific_notation(self):
        """Test parsing values in scientific notation."""
        output = "1.0e-5 1.5e-3 2.0e-1"
        parser = VctParser()
        result = parser.parse(output)
        assert len(result["vct"]) == 3
        assert result["vct"][0] < 1e-4


class TestParseCdoOutputEdgeCases:
    """Edge case tests for parse_cdo_output function."""

    def test_parse_command_with_parameters(self):
        """Test parsing command with parameters like selname,var1,var2."""
        output = "gridtype = lonlat"
        result = parse_cdo_output("griddes,123 data.nc", output)
        # Should extract 'griddes' operator
        assert isinstance(result, dict)

    def test_parse_command_with_dash_prefix(self):
        """Test parsing command with dash prefix."""
        output = "gridtype = lonlat"
        result = parse_cdo_output("-griddes data.nc", output)
        assert isinstance(result, dict)

    def test_parse_command_case_insensitive(self):
        """Test that command parsing is case insensitive."""
        output = "gridtype = lonlat"
        result = parse_cdo_output("GRIDDES data.nc", output)
        assert isinstance(result, dict)

    def test_parse_command_sinfo_variant(self):
        """Test parsing sinfo variants (sinfo, sinfon, sinfov)."""
        output = "File format: NetCDF"
        result1 = parse_cdo_output("sinfo data.nc", output)
        result2 = parse_cdo_output("sinfon data.nc", output)
        result3 = parse_cdo_output("sinfov data.nc", output)
        assert isinstance(result1, dict)
        assert isinstance(result2, dict)
        assert isinstance(result3, dict)

    def test_parse_command_info_variant(self):
        """Test parsing info variants (info, infon, infov)."""
        output = "File format: NetCDF"
        result = parse_cdo_output("infon data.nc", output)
        assert isinstance(result, dict)

    def test_parse_command_griddes2(self):
        """Test parsing griddes2 command."""
        output = "gridtype = lonlat"
        result = parse_cdo_output("griddes2 data.nc", output)
        assert isinstance(result, dict)

    def test_parse_command_codetab(self):
        """Test parsing codetab command (alias for partab)."""
        output = "1 | temp | K"
        result = parse_cdo_output("codetab data.nc", output)
        assert isinstance(result, list)

    def test_parse_command_vct2(self):
        """Test parsing vct2 command."""
        output = "0.0 1.0 2.0"
        result = parse_cdo_output("vct2 data.nc", output)
        assert isinstance(result, dict)
        assert "vct" in result
