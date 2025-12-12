"""Tests for PartabParser."""

from __future__ import annotations

import pytest

from python_cdo_wrapper.exceptions import CDOParseError
from python_cdo_wrapper.parsers.info import PartabParser


class TestPartabParser:
    """Tests for PartabParser class."""

    def test_parse_pipe_separated_format(self):
        """Test parsing pipe-separated parameter table."""
        output = """
1 | temperature | K | Air temperature
2 | pressure | Pa | Air pressure
3 | humidity | % | Relative humidity
        """
        parser = PartabParser()
        result = parser.parse(output)

        assert result.nparams == 3
        assert result.param_codes == ["1", "2", "3"]
        assert result.param_names == ["temperature", "pressure", "humidity"]

        # Check first parameter
        temp = result.parameters[0]
        assert temp.code == "1"
        assert temp.name == "temperature"
        assert temp.units == "K"
        assert temp.description == "Air temperature"

    def test_parse_space_separated_format(self):
        """Test parsing space-separated format."""
        output = """
101 temp K Temperature
102 pres Pa Pressure
        """
        parser = PartabParser()
        result = parser.parse(output)

        assert result.nparams == 2
        assert result.parameters[0].code == "101"
        assert result.parameters[0].name == "temp"
        assert result.parameters[0].units == "K"
        assert result.parameters[0].description == "Temperature"

    def test_parse_tab_separated_format(self):
        """Test parsing tab-separated format."""
        output = (
            "11\ttas\tK\tNear-Surface Air Temperature\n22\tpr\tmm/day\tPrecipitation"
        )
        parser = PartabParser()
        result = parser.parse(output)

        assert result.nparams == 2
        assert result.parameters[0].code == "11"
        assert result.parameters[0].name == "tas"
        assert result.parameters[1].description == "Precipitation"

    def test_parse_with_table_name(self):
        """Test parsing output with table name."""
        output = """
Parameter table: CMIP6
1 | tas | K | Near-Surface Air Temperature
2 | pr | kg m-2 s-1 | Precipitation
        """
        parser = PartabParser()
        result = parser.parse(output)

        assert result.table_name == "CMIP6"
        assert result.nparams == 2

    def test_skip_comment_lines(self):
        """Test that comment lines are skipped."""
        output = """
# This is a comment
1 | temp | K | Temperature
# Another comment
2 | pres | Pa | Pressure
        """
        parser = PartabParser()
        result = parser.parse(output)

        assert result.nparams == 2

    def test_skip_header_lines(self):
        """Test that header lines are skipped."""
        output = """
code | name | units | description
1 | temp | K | Temperature
2 | pres | Pa | Pressure
        """
        parser = PartabParser()
        result = parser.parse(output)

        assert result.nparams == 2

    def test_skip_cdo_lines(self):
        """Test that CDO command lines are skipped."""
        output = """
cdo partab: Starting
1 | temp | K | Temperature
cdo partab: Processed 1 parameter
2 | pres | Pa | Pressure
        """
        parser = PartabParser()
        result = parser.parse(output)

        assert result.nparams == 2

    def test_get_parameter_by_code(self):
        """Test retrieving parameter by code."""
        output = """
1 | temp | K | Temperature
2 | pres | Pa | Pressure
        """
        parser = PartabParser()
        result = parser.parse(output)

        temp = result.get_parameter("1")
        assert temp is not None
        assert temp.name == "temp"

        # Test with integer code
        pres = result.get_parameter(2)
        assert pres is not None
        assert pres.name == "pres"

        # Test non-existent
        none_param = result.get_parameter("999")
        assert none_param is None

    def test_get_parameter_by_name(self):
        """Test retrieving parameter by name."""
        output = """
1 | temp | K | Temperature
2 | pres | Pa | Pressure
        """
        parser = PartabParser()
        result = parser.parse(output)

        temp = result.get_parameter_by_name("temp")
        assert temp is not None
        assert temp.code == "1"

        # Test non-existent
        none_param = result.get_parameter_by_name("nonexistent")
        assert none_param is None

    def test_param_codes_property(self):
        """Test param_codes property."""
        output = """
1 | temp | K | Temperature
2 | pres | Pa | Pressure
3 | hum | % | Humidity
        """
        parser = PartabParser()
        result = parser.parse(output)

        codes = result.param_codes
        assert codes == ["1", "2", "3"]

    def test_param_names_property(self):
        """Test param_names property."""
        output = """
1 | temp | K | Temperature
2 | pres | Pa | Pressure
3 | hum | % | Humidity
        """
        parser = PartabParser()
        result = parser.parse(output)

        names = result.param_names
        assert names == ["temp", "pres", "hum"]

    def test_display_name_property(self):
        """Test PartabInfo display_name property."""
        output = """
1 | temp | K | Temperature | Air Temperature
        """
        parser = PartabParser()
        result = parser.parse(output)

        param = result.parameters[0]
        assert param.display_name == "Air Temperature"

        # Test without longname
        output2 = "2 | pres | Pa | Pressure"
        result2 = parser.parse(output2)
        assert result2.parameters[0].display_name == "pres"

    def test_raw_line_preserved(self):
        """Test that raw line is preserved in PartabInfo."""
        output = "1 | temp | K | Temperature"
        parser = PartabParser()
        result = parser.parse(output)

        assert result.parameters[0].raw == "1 | temp | K | Temperature"

    def test_empty_output_raises_error(self):
        """Test that empty output raises CDOParseError."""
        output = "\n\n\n"
        parser = PartabParser()

        with pytest.raises(CDOParseError) as exc_info:
            parser.parse(output)

        assert "No parameters found" in str(exc_info.value)

    def test_only_comments_raises_error(self):
        """Test that output with only comments raises error."""
        output = """
# Comment 1
# Comment 2
        """
        parser = PartabParser()

        with pytest.raises(CDOParseError):
            parser.parse(output)

    def test_multiword_description(self):
        """Test parsing multiword descriptions."""
        output = "1 temp K This is a long temperature description with many words"
        parser = PartabParser()
        result = parser.parse(output)

        assert (
            result.parameters[0].description
            == "This is a long temperature description with many words"
        )

    def test_missing_optional_fields(self):
        """Test parsing with missing optional fields."""
        output = "1 temp"
        parser = PartabParser()
        result = parser.parse(output)

        param = result.parameters[0]
        assert param.code == "1"
        assert param.name == "temp"
        assert param.units is None
        assert param.description is None

    def test_string_code(self):
        """Test parsing with string code (not numeric)."""
        output = "ABC temp K Temperature"
        parser = PartabParser()
        result = parser.parse(output)

        assert result.parameters[0].code == "ABC"

    def test_mixed_formats(self):
        """Test that parser handles mixed formats gracefully."""
        output = """
1 | temp | K | Temperature
2 pres Pa Pressure
3\thum\t%\tHumidity
        """
        parser = PartabParser()
        result = parser.parse(output)

        # Should parse all three despite different formats
        assert result.nparams == 3
        assert result.param_names == ["temp", "pres", "hum"]
