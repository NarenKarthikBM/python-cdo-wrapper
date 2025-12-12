"""Tests for information operators."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from python_cdo_wrapper import CDO
from python_cdo_wrapper.exceptions import CDOFileNotFoundError
from python_cdo_wrapper.operators.info import (
    GriddesOperator,
    InfoOperator,
    SinfoOperator,
    VlistOperator,
    ZaxisdesOperator,
)

# Sample CDO outputs for mocking
SAMPLE_SINFO = """   File format : NetCDF4
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
  1981-01-01 00:00:00  2022-12-31 00:00:00
cdo    sinfo: Processed 1 variable over 15340 timesteps [0.02s 44MB]
"""

SAMPLE_INFO = """
    -1 :       Date     Time   Level Gridsize    Miss :     Minimum        Mean     Maximum : Parameter ID
     1 : 1981-01-01 00:00:00       0    17415    5596 :      0.0000     0.67922      91.749 : -1
"""

SAMPLE_GRIDDES = """# gridID 1
#
gridtype  = lonlat
gridsize  = 17415
xsize     = 135
ysize     = 129
xfirst    = 66.625
xinc      = 0.25
yfirst    = 6.625
yinc      = 0.25
"""

SAMPLE_ZAXISDES = """# zaxisID 1
#
zaxistype = surface
size      = 1
name      = sfc
levels    = 0
"""

SAMPLE_VLIST = """# vlistID 29
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
     0 -1           31      32      -1       1      0 precip   Precipitation [mm/day]
"""


class TestSinfoOperator:
    """Test SinfoOperator."""

    def test_build_command(self):
        """Test command building."""
        op = SinfoOperator()
        cmd = op.build_command("test.nc")
        assert cmd == "-sinfo test.nc"

    def test_parse_output(self):
        """Test output parsing."""
        op = SinfoOperator()
        result = op.parse_output(SAMPLE_SINFO)

        assert result.file_format == "NetCDF4"
        assert result.nvar == 1
        assert len(result.grid_coordinates) == 1

    def test_cdo_sinfo_method_with_mock(self):
        """Test CDO.sinfo() method with mocked subprocess."""
        cdo = CDO()

        with patch("python_cdo_wrapper.core.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=SAMPLE_SINFO,
                stderr="",
            )

            with patch("python_cdo_wrapper.validation.Path.exists", return_value=True):
                result = cdo.sinfo("test.nc")

                assert result.file_format == "NetCDF4"
                assert result.nvar == 1

    def test_sinfo_validates_file_exists(self, tmp_path):
        """Test that sinfo validates file existence."""
        cdo = CDO()
        missing_file = tmp_path / "missing.nc"

        with pytest.raises(CDOFileNotFoundError):
            cdo.sinfo(missing_file)


class TestInfoOperator:
    """Test InfoOperator."""

    def test_build_command(self):
        """Test command building."""
        op = InfoOperator()
        cmd = op.build_command("test.nc")
        assert cmd == "-info test.nc"

    def test_parse_output(self):
        """Test output parsing."""
        op = InfoOperator()
        result = op.parse_output(SAMPLE_INFO)

        assert result.ntimesteps == 1
        assert result.first_timestep is not None

    def test_cdo_info_method_with_mock(self):
        """Test CDO.info() method with mocked subprocess."""
        cdo = CDO()

        with patch("python_cdo_wrapper.core.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=SAMPLE_INFO,
                stderr="",
            )

            with patch("python_cdo_wrapper.validation.Path.exists", return_value=True):
                result = cdo.info("test.nc")

                assert result.ntimesteps == 1


class TestGriddesOperator:
    """Test GriddesOperator."""

    def test_build_command(self):
        """Test command building."""
        op = GriddesOperator()
        cmd = op.build_command("test.nc")
        assert cmd == "-griddes test.nc"

    def test_parse_output(self):
        """Test output parsing."""
        op = GriddesOperator()
        result = op.parse_output(SAMPLE_GRIDDES)

        assert result.ngrids == 1
        grid = result.primary_grid
        assert grid.gridtype == "lonlat"
        assert grid.xsize == 135
        assert grid.ysize == 129

    def test_cdo_griddes_method_with_mock(self):
        """Test CDO.griddes() method with mocked subprocess."""
        cdo = CDO()

        with patch("python_cdo_wrapper.core.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=SAMPLE_GRIDDES,
                stderr="",
            )

            with patch("python_cdo_wrapper.validation.Path.exists", return_value=True):
                result = cdo.griddes("test.nc")

                assert result.ngrids == 1
                assert result.primary_grid.gridtype == "lonlat"


class TestZaxisdesOperator:
    """Test ZaxisdesOperator."""

    def test_build_command(self):
        """Test command building."""
        op = ZaxisdesOperator()
        cmd = op.build_command("test.nc")
        assert cmd == "-zaxisdes test.nc"

    def test_parse_output(self):
        """Test output parsing."""
        op = ZaxisdesOperator()
        result = op.parse_output(SAMPLE_ZAXISDES)

        assert result.nzaxes == 1
        zaxis = result.primary_zaxis
        assert zaxis.zaxistype == "surface"
        assert zaxis.size == 1

    def test_cdo_zaxisdes_method_with_mock(self):
        """Test CDO.zaxisdes() method with mocked subprocess."""
        cdo = CDO()

        with patch("python_cdo_wrapper.core.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=SAMPLE_ZAXISDES,
                stderr="",
            )

            with patch("python_cdo_wrapper.validation.Path.exists", return_value=True):
                result = cdo.zaxisdes("test.nc")

                assert result.nzaxes == 1
                assert result.primary_zaxis.is_surface


class TestVlistOperator:
    """Test VlistOperator."""

    def test_build_command(self):
        """Test command building."""
        op = VlistOperator()
        cmd = op.build_command("test.nc")
        assert cmd == "-vlist test.nc"

    def test_parse_output(self):
        """Test output parsing."""
        op = VlistOperator()
        result = op.parse_output(SAMPLE_VLIST)

        assert result.nvars == 1
        assert result.var_names == ["precip"]

    def test_cdo_vlist_method_with_mock(self):
        """Test CDO.vlist() method with mocked subprocess."""
        cdo = CDO()

        with patch("python_cdo_wrapper.core.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=SAMPLE_VLIST,
                stderr="",
            )

            with patch("python_cdo_wrapper.validation.Path.exists", return_value=True):
                result = cdo.vlist("test.nc")

                assert result.nvars == 1
                assert "precip" in result.var_names


# Integration tests (require CDO installation)
@pytest.mark.integration
class TestInfoOperatorsIntegration:
    """Integration tests for info operators (require CDO)."""

    def test_sinfo_with_real_file(self, sample_nc_file, cdo_instance):
        """Test sinfo with real NetCDF file."""
        result = cdo_instance.sinfo(sample_nc_file)

        assert result.file_format in ["NetCDF", "NetCDF4", "NetCDF4 classic"]
        assert result.nvar >= 1
        assert len(result.grid_coordinates) >= 1

    def test_info_with_real_file(self, sample_nc_file, cdo_instance):
        """Test info with real NetCDF file."""
        result = cdo_instance.info(sample_nc_file)

        assert result.ntimesteps >= 1
        assert result.first_timestep is not None

    def test_griddes_with_real_file(self, sample_nc_file, cdo_instance):
        """Test griddes with real NetCDF file."""
        result = cdo_instance.griddes(sample_nc_file)

        assert result.ngrids >= 1
        grid = result.primary_grid
        assert grid.gridtype in [
            "lonlat",
            "gaussian",
            "curvilinear",
            "unstructured",
            "generic",
        ]

    def test_zaxisdes_with_real_file(self, sample_nc_file, cdo_instance):
        """Test zaxisdes with real NetCDF file."""
        result = cdo_instance.zaxisdes(sample_nc_file)

        assert result.nzaxes >= 1
        zaxis = result.primary_zaxis
        assert zaxis.zaxistype in ["surface", "pressure", "height", "hybrid", "sigma"]

    def test_vlist_with_real_file(self, sample_nc_file, cdo_instance):
        """Test vlist with real NetCDF file."""
        result = cdo_instance.vlist(sample_nc_file)

        assert result.nvars >= 1
        assert len(result.var_names) >= 1


class TestPartabOperator:
    """Tests for PartabOperator class."""

    def test_build_command(self):
        """Test building partab command."""
        from python_cdo_wrapper.operators.info import PartabOperator

        op = PartabOperator()
        cmd = op.build_command("data.nc")
        assert cmd == "-partab data.nc"

    def test_parse_output(self):
        """Test parsing partab output."""
        from python_cdo_wrapper.operators.info import PartabOperator

        op = PartabOperator()
        sample_output = """
1 | temperature | K | Air temperature
2 | pressure | Pa | Air pressure
        """
        result = op.parse_output(sample_output)

        assert result.nparams == 2
        assert result.param_codes == ["1", "2"]


class TestPartabCDOMethod:
    """Tests for CDO.partab() method."""

    def test_partab_mocked(self, sample_nc_file, cdo_instance):
        """Test partab method with mocked subprocess."""
        from unittest.mock import MagicMock, patch

        sample_output = """
1 | tas | K | Near-Surface Air Temperature
2 | pr | kg m-2 s-1 | Precipitation
        """

        with patch("python_cdo_wrapper.core.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=sample_output,
                stderr="",
            )

            result = cdo_instance.partab(sample_nc_file)

            assert result.nparams == 2
            assert "tas" in result.param_names
            assert "pr" in result.param_names

            # Test get_parameter
            tas = result.get_parameter("1")
            assert tas is not None
            assert tas.name == "tas"
            assert tas.units == "K"
