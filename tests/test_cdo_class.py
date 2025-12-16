"""Tests for the CDO master class (v1.0.0+ API)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from python_cdo_wrapper import CDO
from python_cdo_wrapper.exceptions import CDOExecutionError


class TestCDOInitialization:
    """Test CDO class initialization."""

    def test_cdo_init_default(self):
        """Test CDO initialization with default parameters."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()
            assert cdo.cdo_path == "cdo"
            assert cdo.temp_dir is None
            assert cdo.debug is False
            assert cdo.env == {}

    def test_cdo_init_custom_path(self):
        """Test CDO initialization with custom path."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO(cdo_path="/usr/local/bin/cdo")
            assert cdo.cdo_path == "/usr/local/bin/cdo"

    def test_cdo_init_with_temp_dir(self, tmp_path):
        """Test CDO initialization with custom temp directory."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO(temp_dir=str(tmp_path))
            assert cdo.temp_dir == tmp_path

    def test_cdo_init_with_debug(self):
        """Test CDO initialization with debug enabled."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO(debug=True)
            assert cdo.debug is True

    def test_cdo_init_with_env(self):
        """Test CDO initialization with environment variables."""
        env = {"CDO_PCTL_NBINS": "101"}
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO(env=env)
            assert cdo.env == env

    def test_cdo_init_fails_if_not_available(self):
        """Test that initialization fails if CDO is not available."""
        with (
            patch.object(
                CDO,
                "_check_cdo_available",
                side_effect=RuntimeError(
                    "CDO is not available at 'cdo'. Please ensure CDO is installed and accessible."
                ),
            ),
            pytest.raises(RuntimeError, match="CDO is not available"),
        ):
            CDO()

    def test_cdo_repr(self):
        """Test CDO string representation."""
        with (
            patch.object(CDO, "_check_cdo_available"),
            patch(
                "python_cdo_wrapper.utils.get_cdo_version",
                return_value="Climate Data Operators version 2.0.5",
            ),
        ):
            cdo = CDO()
            repr_str = repr(cdo)
            assert "CDO" in repr_str
            assert "cdo_path" in repr_str
            assert "version" in repr_str


class TestCDOVersion:
    """Test CDO version property."""

    def test_version_property(self):
        """Test that version property returns CDO version."""
        with (
            patch.object(
                CDO,
                "version",
                new_callable=MagicMock(return_value="2.0.5"),
            ),
        ):
            cdo = CDO()
            assert "2.0.5" in cdo.version


class TestCDOLegacyRun:
    """Test legacy run() method for backward compatibility."""

    def test_run_method_exists(self):
        """Test that run() method exists for backward compatibility."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()
            assert hasattr(cdo, "run")
            assert callable(cdo.run)

    def test_run_delegates_to_legacy_cdo(self):
        """Test that run() delegates to legacy cdo function."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "test output"
            mock_result.stderr = ""

            with patch(
                "python_cdo_wrapper.core.subprocess.run", return_value=mock_result
            ):
                result = cdo.run("sinfo test.nc", check_files=False)
                assert result == "test output"


class TestCDOExecuteTextCommand:
    """Test _execute_text_command internal method."""

    def test_execute_text_command_success(self):
        """Test successful execution of text command."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "test output"
            mock_result.stderr = ""

            with patch(
                "python_cdo_wrapper.utils.subprocess.run", return_value=mock_result
            ):
                result = cdo._execute_text_command("--version")
                assert result == "test output"

    def test_execute_text_command_failure(self):
        """Test that failed command raises CDOExecutionError."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_result.stderr = "Error message"

            with patch(
                "python_cdo_wrapper.utils.subprocess.run", return_value=mock_result
            ):
                with pytest.raises(CDOExecutionError) as exc_info:
                    cdo._execute_text_command("invalid command")

                assert exc_info.value.returncode == 1
                assert "Error message" in exc_info.value.stderr

    def test_execute_text_command_with_env(self):
        """Test that environment variables are passed to subprocess."""
        env = {"CDO_PCTL_NBINS": "101"}
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO(env=env)

            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "output"

            with patch(
                "python_cdo_wrapper.utils.subprocess.run", return_value=mock_result
            ) as mock_run:
                cdo._execute_text_command("--version")
                # Check that env was passed (it's merged with os.environ)
                call_kwargs = mock_run.call_args[1]
                assert "CDO_PCTL_NBINS" in call_kwargs["env"]


class TestCDOExecuteDataCommand:
    """Test _execute_data_command internal method."""

    @pytest.mark.integration
    def test_execute_data_command_with_output(self, sample_nc_file, temp_output_file):
        """Test data command execution with output file."""
        cdo = CDO()
        # Simple copy operation
        result = cdo._execute_data_command(
            f"copy {sample_nc_file}", output=temp_output_file
        )

        assert result is not None
        assert "tas" in result.data_vars
        assert temp_output_file.exists()

    @pytest.mark.integration
    def test_execute_data_command_creates_temp_file(self, sample_nc_file):
        """Test that data command creates temp file when output not specified."""
        cdo = CDO()
        result = cdo._execute_data_command(f"copy {sample_nc_file}")

        assert result is not None
        assert "tas" in result.data_vars

    def test_execute_data_command_failure(self):
        """Test that failed data command raises CDOExecutionError."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = "Error message"

            with (
                patch(
                    "python_cdo_wrapper.utils.subprocess.run", return_value=mock_result
                ),
                pytest.raises(CDOExecutionError),
            ):
                cdo._execute_data_command("invalid command", output="output.nc")


class TestCDOShowMethods:
    """Test show* convenience methods that return text output."""

    def test_showname(self, sample_nc_file):
        """Test showname() returns list of variable names."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            with patch.object(
                cdo,
                "_execute_text_command",
                return_value="temperature pressure humidity",
            ):
                result = cdo.showname(sample_nc_file)
                assert result == ["temperature", "pressure", "humidity"]
                cdo._execute_text_command.assert_called_once_with(
                    f"showname {sample_nc_file}"
                )

    def test_showname_single_var(self, sample_nc_file):
        """Test showname() with single variable."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            with patch.object(cdo, "_execute_text_command", return_value="temperature"):
                result = cdo.showname(sample_nc_file)
                assert result == ["temperature"]

    def test_showcode(self, sample_nc_file):
        """Test showcode() returns list of variable codes."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            with patch.object(cdo, "_execute_text_command", return_value="11 33 52"):
                result = cdo.showcode(sample_nc_file)
                assert result == [11, 33, 52]
                cdo._execute_text_command.assert_called_once_with(
                    f"showcode {sample_nc_file}"
                )

    def test_showcode_single(self, sample_nc_file):
        """Test showcode() with single code."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            with patch.object(cdo, "_execute_text_command", return_value="11"):
                result = cdo.showcode(sample_nc_file)
                assert result == [11]

    def test_showunit(self, sample_nc_file):
        """Test showunit() returns list of units."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            with patch.object(cdo, "_execute_text_command", return_value="K Pa %"):
                result = cdo.showunit(sample_nc_file)
                assert result == ["K", "Pa", "%"]
                cdo._execute_text_command.assert_called_once_with(
                    f"showunit {sample_nc_file}"
                )

    def test_showlevel(self, sample_nc_file):
        """Test showlevel() returns list of levels."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            with patch.object(
                cdo, "_execute_text_command", return_value="1000 850 500 250"
            ):
                result = cdo.showlevel(sample_nc_file)
                assert result == [1000.0, 850.0, 500.0, 250.0]
                cdo._execute_text_command.assert_called_once_with(
                    f"showlevel {sample_nc_file}"
                )

    def test_showlevel_float_values(self, sample_nc_file):
        """Test showlevel() with float values."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            with patch.object(
                cdo, "_execute_text_command", return_value="10.5 20.75 35.25"
            ):
                result = cdo.showlevel(sample_nc_file)
                assert result == [10.5, 20.75, 35.25]

    def test_showdate(self, sample_nc_file):
        """Test showdate() returns list of dates."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            with patch.object(
                cdo,
                "_execute_text_command",
                return_value="2020-01-01 2020-01-02 2020-01-03",
            ):
                result = cdo.showdate(sample_nc_file)
                assert result == ["2020-01-01", "2020-01-02", "2020-01-03"]
                cdo._execute_text_command.assert_called_once_with(
                    f"showdate {sample_nc_file}"
                )

    def test_showtime(self, sample_nc_file):
        """Test showtime() returns list of times."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            with patch.object(
                cdo, "_execute_text_command", return_value="00:00:00 06:00:00 12:00:00"
            ):
                result = cdo.showtime(sample_nc_file)
                assert result == ["00:00:00", "06:00:00", "12:00:00"]
                cdo._execute_text_command.assert_called_once_with(
                    f"showtime {sample_nc_file}"
                )

    def test_ntime(self, sample_nc_file):
        """Test ntime() returns number of timesteps."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            with patch.object(cdo, "_execute_text_command", return_value="365"):
                result = cdo.ntime(sample_nc_file)
                assert result == 365
                cdo._execute_text_command.assert_called_once_with(
                    f"ntime {sample_nc_file}"
                )

    def test_nvar(self, sample_nc_file):
        """Test nvar() returns number of variables."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            with patch.object(cdo, "_execute_text_command", return_value="5"):
                result = cdo.nvar(sample_nc_file)
                assert result == 5
                cdo._execute_text_command.assert_called_once_with(
                    f"nvar {sample_nc_file}"
                )

    def test_nlevel(self, sample_nc_file):
        """Test nlevel() returns number of levels."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            with patch.object(cdo, "_execute_text_command", return_value="17"):
                result = cdo.nlevel(sample_nc_file)
                assert result == 17
                cdo._execute_text_command.assert_called_once_with(
                    f"nlevel {sample_nc_file}"
                )


class TestCDOBinaryOperators:
    """Test binary arithmetic operators (add, sub, mul, div, min, max, atan2)."""

    def test_add(self, sample_nc_file, tmp_path):
        """Test add() delegates to _execute_multi_file_op."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            with patch.object(cdo, "_execute_multi_file_op", return_value=mock_dataset):
                file1 = sample_nc_file
                file2 = tmp_path / "file2.nc"
                result = cdo.add(file1, file2)

                assert result is mock_dataset
                cdo._execute_multi_file_op.assert_called_once_with(
                    "add", (file1, file2), None
                )

    def test_add_with_output(self, sample_nc_file, tmp_path):
        """Test add() with output file specified."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            with patch.object(cdo, "_execute_multi_file_op", return_value=mock_dataset):
                file1 = sample_nc_file
                file2 = tmp_path / "file2.nc"
                output = tmp_path / "output.nc"
                result = cdo.add(file1, file2, output=output)

                assert result is mock_dataset
                cdo._execute_multi_file_op.assert_called_once_with(
                    "add", (file1, file2), output
                )

    def test_sub(self, sample_nc_file, tmp_path):
        """Test sub() delegates to _execute_multi_file_op."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            with patch.object(cdo, "_execute_multi_file_op", return_value=mock_dataset):
                file1 = sample_nc_file
                file2 = tmp_path / "file2.nc"
                result = cdo.sub(file1, file2)

                assert result is mock_dataset
                cdo._execute_multi_file_op.assert_called_once_with(
                    "sub", (file1, file2), None
                )

    def test_mul(self, sample_nc_file, tmp_path):
        """Test mul() delegates to _execute_multi_file_op."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            with patch.object(cdo, "_execute_multi_file_op", return_value=mock_dataset):
                file1 = sample_nc_file
                file2 = tmp_path / "file2.nc"
                result = cdo.mul(file1, file2)

                assert result is mock_dataset
                cdo._execute_multi_file_op.assert_called_once_with(
                    "mul", (file1, file2), None
                )

    def test_div(self, sample_nc_file, tmp_path):
        """Test div() delegates to _execute_multi_file_op."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            with patch.object(cdo, "_execute_multi_file_op", return_value=mock_dataset):
                file1 = sample_nc_file
                file2 = tmp_path / "file2.nc"
                result = cdo.div(file1, file2)

                assert result is mock_dataset
                cdo._execute_multi_file_op.assert_called_once_with(
                    "div", (file1, file2), None
                )

    def test_min(self, sample_nc_file, tmp_path):
        """Test min() delegates to _execute_multi_file_op."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            with patch.object(cdo, "_execute_multi_file_op", return_value=mock_dataset):
                file1 = sample_nc_file
                file2 = tmp_path / "file2.nc"
                result = cdo.min(file1, file2)

                assert result is mock_dataset
                cdo._execute_multi_file_op.assert_called_once_with(
                    "min", (file1, file2), None
                )

    def test_max(self, sample_nc_file, tmp_path):
        """Test max() delegates to _execute_multi_file_op."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            with patch.object(cdo, "_execute_multi_file_op", return_value=mock_dataset):
                file1 = sample_nc_file
                file2 = tmp_path / "file2.nc"
                result = cdo.max(file1, file2)

                assert result is mock_dataset
                cdo._execute_multi_file_op.assert_called_once_with(
                    "max", (file1, file2), None
                )

    def test_atan2(self, sample_nc_file, tmp_path):
        """Test atan2() delegates to _execute_multi_file_op."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            with patch.object(cdo, "_execute_multi_file_op", return_value=mock_dataset):
                file1 = sample_nc_file
                file2 = tmp_path / "file2.nc"
                result = cdo.atan2(file1, file2)

                assert result is mock_dataset
                cdo._execute_multi_file_op.assert_called_once_with(
                    "atan2", (file1, file2), None
                )


class TestCDOConstantOperators:
    """Test constant arithmetic operators (addc, subc, mulc, divc)."""

    def test_addc(self, sample_nc_file):
        """Test addc() delegates to query layer."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            mock_query = MagicMock()
            mock_query.add_constant.return_value = mock_query
            mock_query.compute.return_value = mock_dataset

            with patch.object(cdo, "query", return_value=mock_query):
                result = cdo.addc(10.5, sample_nc_file)

                assert result is mock_dataset
                cdo.query.assert_called_once_with(sample_nc_file)
                mock_query.add_constant.assert_called_once_with(10.5)
                mock_query.compute.assert_called_once_with(None)

    def test_addc_with_output(self, sample_nc_file, tmp_path):
        """Test addc() with output file."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            mock_query = MagicMock()
            mock_query.add_constant.return_value = mock_query
            mock_query.compute.return_value = mock_dataset

            output = tmp_path / "output.nc"
            with patch.object(cdo, "query", return_value=mock_query):
                result = cdo.addc(5.0, sample_nc_file, output=output)

                assert result is mock_dataset
                mock_query.compute.assert_called_once_with(output)

    def test_subc(self, sample_nc_file):
        """Test subc() delegates to query layer."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            mock_query = MagicMock()
            mock_query.subtract_constant.return_value = mock_query
            mock_query.compute.return_value = mock_dataset

            with patch.object(cdo, "query", return_value=mock_query):
                result = cdo.subc(273.15, sample_nc_file)

                assert result is mock_dataset
                cdo.query.assert_called_once_with(sample_nc_file)
                mock_query.subtract_constant.assert_called_once_with(273.15)
                mock_query.compute.assert_called_once_with(None)

    def test_mulc(self, sample_nc_file):
        """Test mulc() delegates to query layer."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            mock_query = MagicMock()
            mock_query.multiply_constant.return_value = mock_query
            mock_query.compute.return_value = mock_dataset

            with patch.object(cdo, "query", return_value=mock_query):
                result = cdo.mulc(2.0, sample_nc_file)

                assert result is mock_dataset
                cdo.query.assert_called_once_with(sample_nc_file)
                mock_query.multiply_constant.assert_called_once_with(2.0)
                mock_query.compute.assert_called_once_with(None)

    def test_divc(self, sample_nc_file):
        """Test divc() delegates to query layer."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            mock_query = MagicMock()
            mock_query.divide_constant.return_value = mock_query
            mock_query.compute.return_value = mock_dataset

            with patch.object(cdo, "query", return_value=mock_query):
                result = cdo.divc(100.0, sample_nc_file)

                assert result is mock_dataset
                cdo.query.assert_called_once_with(sample_nc_file)
                mock_query.divide_constant.assert_called_once_with(100.0)
                mock_query.compute.assert_called_once_with(None)


class TestCDOTimeStatisticalOperators:
    """Test time-based statistical operators."""

    def test_timmean(self, sample_nc_file):
        """Test timmean() delegates to query layer."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            mock_query = MagicMock()
            mock_query.time_mean.return_value = mock_query
            mock_query.compute.return_value = mock_dataset

            with patch.object(cdo, "query", return_value=mock_query):
                result = cdo.timmean(sample_nc_file)

                assert result is mock_dataset
                cdo.query.assert_called_once_with(sample_nc_file)
                mock_query.time_mean.assert_called_once_with()
                mock_query.compute.assert_called_once_with(None)

    def test_timsum(self, sample_nc_file):
        """Test timsum() delegates to query layer."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            mock_query = MagicMock()
            mock_query.time_sum.return_value = mock_query
            mock_query.compute.return_value = mock_dataset

            with patch.object(cdo, "query", return_value=mock_query):
                result = cdo.timsum(sample_nc_file)

                assert result is mock_dataset
                mock_query.time_sum.assert_called_once_with()

    def test_timmin(self, sample_nc_file):
        """Test timmin() delegates to query layer."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            mock_query = MagicMock()
            mock_query.time_min.return_value = mock_query
            mock_query.compute.return_value = mock_dataset

            with patch.object(cdo, "query", return_value=mock_query):
                result = cdo.timmin(sample_nc_file)

                assert result is mock_dataset
                mock_query.time_min.assert_called_once_with()

    def test_timmax(self, sample_nc_file):
        """Test timmax() delegates to query layer."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            mock_query = MagicMock()
            mock_query.time_max.return_value = mock_query
            mock_query.compute.return_value = mock_dataset

            with patch.object(cdo, "query", return_value=mock_query):
                result = cdo.timmax(sample_nc_file)

                assert result is mock_dataset
                mock_query.time_max.assert_called_once_with()

    def test_timstd(self, sample_nc_file):
        """Test timstd() delegates to query layer."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            mock_query = MagicMock()
            mock_query.time_std.return_value = mock_query
            mock_query.compute.return_value = mock_dataset

            with patch.object(cdo, "query", return_value=mock_query):
                result = cdo.timstd(sample_nc_file)

                assert result is mock_dataset
                mock_query.time_std.assert_called_once_with()


class TestCDOYearStatisticalOperators:
    """Test year-based statistical operators."""

    def test_yearmean(self, sample_nc_file):
        """Test yearmean() delegates to query layer."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            mock_query = MagicMock()
            mock_query.year_mean.return_value = mock_query
            mock_query.compute.return_value = mock_dataset

            with patch.object(cdo, "query", return_value=mock_query):
                result = cdo.yearmean(sample_nc_file)

                assert result is mock_dataset
                cdo.query.assert_called_once_with(sample_nc_file)
                mock_query.year_mean.assert_called_once_with()
                mock_query.compute.assert_called_once_with(None)

    def test_yearsum(self, sample_nc_file):
        """Test yearsum() delegates to query layer."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            mock_query = MagicMock()
            mock_query.year_sum.return_value = mock_query
            mock_query.compute.return_value = mock_dataset

            with patch.object(cdo, "query", return_value=mock_query):
                result = cdo.yearsum(sample_nc_file)

                assert result is mock_dataset
                mock_query.year_sum.assert_called_once_with()

    def test_yearmin(self, sample_nc_file):
        """Test yearmin() delegates to query layer."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            mock_query = MagicMock()
            mock_query.year_min.return_value = mock_query
            mock_query.compute.return_value = mock_dataset

            with patch.object(cdo, "query", return_value=mock_query):
                result = cdo.yearmin(sample_nc_file)

                assert result is mock_dataset
                mock_query.year_min.assert_called_once_with()

    def test_yearmax(self, sample_nc_file):
        """Test yearmax() delegates to query layer."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            mock_query = MagicMock()
            mock_query.year_max.return_value = mock_query
            mock_query.compute.return_value = mock_dataset

            with patch.object(cdo, "query", return_value=mock_query):
                result = cdo.yearmax(sample_nc_file)

                assert result is mock_dataset
                mock_query.year_max.assert_called_once_with()

    def test_yearstd(self, sample_nc_file):
        """Test yearstd() delegates to query layer."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            mock_query = MagicMock()
            mock_query.year_std.return_value = mock_query
            mock_query.compute.return_value = mock_dataset

            with patch.object(cdo, "query", return_value=mock_query):
                result = cdo.yearstd(sample_nc_file)

                assert result is mock_dataset
                mock_query.year_std.assert_called_once_with()


class TestCDOMonthStatisticalOperators:
    """Test month-based statistical operators."""

    def test_monmean(self, sample_nc_file):
        """Test monmean() delegates to query layer."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            mock_query = MagicMock()
            mock_query.month_mean.return_value = mock_query
            mock_query.compute.return_value = mock_dataset

            with patch.object(cdo, "query", return_value=mock_query):
                result = cdo.monmean(sample_nc_file)

                assert result is mock_dataset
                cdo.query.assert_called_once_with(sample_nc_file)
                mock_query.month_mean.assert_called_once_with()
                mock_query.compute.assert_called_once_with(None)

    def test_monsum(self, sample_nc_file):
        """Test monsum() delegates to query layer."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            mock_query = MagicMock()
            mock_query.month_sum.return_value = mock_query
            mock_query.compute.return_value = mock_dataset

            with patch.object(cdo, "query", return_value=mock_query):
                result = cdo.monsum(sample_nc_file)

                assert result is mock_dataset
                mock_query.month_sum.assert_called_once_with()

    def test_monmin(self, sample_nc_file):
        """Test monmin() delegates to query layer."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            mock_query = MagicMock()
            mock_query.month_min.return_value = mock_query
            mock_query.compute.return_value = mock_dataset

            with patch.object(cdo, "query", return_value=mock_query):
                result = cdo.monmin(sample_nc_file)

                assert result is mock_dataset
                mock_query.month_min.assert_called_once_with()

    def test_monmax(self, sample_nc_file):
        """Test monmax() delegates to query layer."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            mock_query = MagicMock()
            mock_query.month_max.return_value = mock_query
            mock_query.compute.return_value = mock_dataset

            with patch.object(cdo, "query", return_value=mock_query):
                result = cdo.monmax(sample_nc_file)

                assert result is mock_dataset
                mock_query.month_max.assert_called_once_with()

    def test_monstd(self, sample_nc_file):
        """Test monstd() delegates to query layer."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            mock_query = MagicMock()
            mock_query.month_std.return_value = mock_query
            mock_query.compute.return_value = mock_dataset

            with patch.object(cdo, "query", return_value=mock_query):
                result = cdo.monstd(sample_nc_file)

                assert result is mock_dataset
                mock_query.month_std.assert_called_once_with()


class TestCDODayStatisticalOperators:
    """Test day-based statistical operators."""

    def test_daymean(self, sample_nc_file):
        """Test daymean() delegates to query layer."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            mock_query = MagicMock()
            mock_query.day_mean.return_value = mock_query
            mock_query.compute.return_value = mock_dataset

            with patch.object(cdo, "query", return_value=mock_query):
                result = cdo.daymean(sample_nc_file)

                assert result is mock_dataset
                cdo.query.assert_called_once_with(sample_nc_file)
                mock_query.day_mean.assert_called_once_with()
                mock_query.compute.assert_called_once_with(None)

    def test_daysum(self, sample_nc_file):
        """Test daysum() delegates to query layer."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            mock_query = MagicMock()
            mock_query.day_sum.return_value = mock_query
            mock_query.compute.return_value = mock_dataset

            with patch.object(cdo, "query", return_value=mock_query):
                result = cdo.daysum(sample_nc_file)

                assert result is mock_dataset
                mock_query.day_sum.assert_called_once_with()


class TestCDOFieldStatisticalOperators:
    """Test field-based statistical operators."""

    def test_fldmean(self, sample_nc_file):
        """Test fldmean() delegates to query layer."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            mock_query = MagicMock()
            mock_query.field_mean.return_value = mock_query
            mock_query.compute.return_value = mock_dataset

            with patch.object(cdo, "query", return_value=mock_query):
                result = cdo.fldmean(sample_nc_file)

                assert result is mock_dataset
                cdo.query.assert_called_once_with(sample_nc_file)
                mock_query.field_mean.assert_called_once_with()
                mock_query.compute.assert_called_once_with(None)

    def test_fldsum(self, sample_nc_file):
        """Test fldsum() delegates to query layer."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            mock_query = MagicMock()
            mock_query.field_sum.return_value = mock_query
            mock_query.compute.return_value = mock_dataset

            with patch.object(cdo, "query", return_value=mock_query):
                result = cdo.fldsum(sample_nc_file)

                assert result is mock_dataset
                mock_query.field_sum.assert_called_once_with()

    def test_fldmin(self, sample_nc_file):
        """Test fldmin() delegates to query layer."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            mock_query = MagicMock()
            mock_query.field_min.return_value = mock_query
            mock_query.compute.return_value = mock_dataset

            with patch.object(cdo, "query", return_value=mock_query):
                result = cdo.fldmin(sample_nc_file)

                assert result is mock_dataset
                mock_query.field_min.assert_called_once_with()

    def test_fldmax(self, sample_nc_file):
        """Test fldmax() delegates to query layer."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            mock_query = MagicMock()
            mock_query.field_max.return_value = mock_query
            mock_query.compute.return_value = mock_dataset

            with patch.object(cdo, "query", return_value=mock_query):
                result = cdo.fldmax(sample_nc_file)

                assert result is mock_dataset
                mock_query.field_max.assert_called_once_with()

    def test_fldstd(self, sample_nc_file):
        """Test fldstd() delegates to query layer."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            mock_query = MagicMock()
            mock_query.field_std.return_value = mock_query
            mock_query.compute.return_value = mock_dataset

            with patch.object(cdo, "query", return_value=mock_query):
                result = cdo.fldstd(sample_nc_file)

                assert result is mock_dataset
                mock_query.field_std.assert_called_once_with()


class TestCDOZonalMeridionalOperators:
    """Test zonal and meridional mean operators."""

    def test_zonmean(self, sample_nc_file):
        """Test zonmean() delegates to query layer."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            mock_query = MagicMock()
            mock_query.zonal_mean.return_value = mock_query
            mock_query.compute.return_value = mock_dataset

            with patch.object(cdo, "query", return_value=mock_query):
                result = cdo.zonmean(sample_nc_file)

                assert result is mock_dataset
                cdo.query.assert_called_once_with(sample_nc_file)
                mock_query.zonal_mean.assert_called_once_with()
                mock_query.compute.assert_called_once_with(None)

    def test_mermean(self, sample_nc_file):
        """Test mermean() delegates to query layer."""
        with patch.object(CDO, "_check_cdo_available"):
            cdo = CDO()

            mock_dataset = MagicMock()
            mock_query = MagicMock()
            mock_query.meridional_mean.return_value = mock_query
            mock_query.compute.return_value = mock_dataset

            with patch.object(cdo, "query", return_value=mock_query):
                result = cdo.mermean(sample_nc_file)

                assert result is mock_dataset
                cdo.query.assert_called_once_with(sample_nc_file)
                mock_query.meridional_mean.assert_called_once_with()
                mock_query.compute.assert_called_once_with(None)
