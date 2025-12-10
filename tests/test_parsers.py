"""Tests for CDO output parsers."""

import pytest

from python_cdo_wrapper.parsers import (
    GriddesParser,
    PartabParser,
    ShowattsglobParser,
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


class TestShowattsParser:
    """Tests for ShowattsParser."""

    def test_parse_variable_attributes(self):
        """Test parsing variable attributes."""
        output = """
Temperature attributes:
    long_name = "Air Temperature"
    units = "K"
    standard_name = "air_temperature"

Precipitation attributes:
    long_name = "Precipitation"
    units = "mm/day"
        """
        parser = ShowattsParser()
        result = parser.parse(output)

        assert "Temperature" in result
        assert result["Temperature"]["long_name"] == "Air Temperature"
        assert result["Temperature"]["units"] == "K"
        assert "Precipitation" in result
        assert result["Precipitation"]["units"] == "mm/day"

    def test_parse_empty_attributes(self):
        """Test parsing with no attributes."""
        output = ""
        parser = ShowattsParser()
        result = parser.parse(output)

        assert isinstance(result, dict)
        assert len(result) == 0


class TestShowattsglobParser:
    """Tests for ShowattsglobParser."""

    def test_parse_global_attributes(self):
        """Test parsing global attributes."""
        output = """
title = "Climate Model Output"
institution = "Research Institute"
source = "Model v1.0"
        """
        parser = ShowattsglobParser()
        result = parser.parse(output)

        assert result["title"] == "Climate Model Output"
        assert result["institution"] == "Research Institute"
        assert result["source"] == "Model v1.0"

    def test_parse_with_quotes(self):
        """Test parsing attributes with quotes."""
        output = """
title = "Test Data"
comment = 'Single quotes'
        """
        parser = ShowattsglobParser()
        result = parser.parse(output)

        assert result["title"] == "Test Data"
        assert result["comment"] == "Single quotes"


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
