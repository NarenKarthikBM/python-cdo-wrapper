"""Master CDO class for v1.0.0+ API."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .query import BinaryOpQuery, CDOQuery

# Import legacy cdo function for backward compatibility
from .core import cdo as legacy_cdo
from .exceptions import CDOError, CDOExecutionError
from .utils import check_cdo_available, get_cdo_version

if TYPE_CHECKING:
    import xarray as xr

    from .types.results import (
        GriddesResult,
        InfoResult,
        PartabResult,
        SinfoResult,
        VlistResult,
        ZaxisdesResult,
    )


class CDO:
    """
    Main interface to Climate Data Operators (v1.0.0+ API).

    This class provides a Pythonic, type-safe interface to CDO operations
    with dedicated methods for all common operators, full type hints,
    and parameter validation.

    Attributes:
        cdo_path: Path to the CDO executable.
        temp_dir: Directory for temporary files (None = system default).
        debug: Enable debug output.
        env: Environment variables to pass to CDO processes.

    Example:
        >>> cdo = CDO()
        >>> info = cdo.sinfo("data.nc")  # Will be implemented in Phase 2
        >>> ds = cdo.yearmean("data.nc")  # Will be implemented in Phase 4

        >>> # Custom CDO path
        >>> cdo = CDO(cdo_path="/usr/local/bin/cdo")

        >>> # With environment variables
        >>> cdo = CDO(env={"CDO_PCTL_NBINS": "101"})

        >>> # Legacy string interface (backward compatibility)
        >>> ds, log = cdo.run("-yearmean data.nc")
    """

    def __init__(
        self,
        cdo_path: str | None = None,
        temp_dir: str | Path | None = None,
        debug: bool = False,
        env: dict[str, str] | None = None,
    ):
        """
        Initialize the CDO interface.

        Args:
            cdo_path: Path to CDO executable. If None, uses "cdo" from PATH.
            temp_dir: Directory for temporary files. If None, uses system default.
            debug: If True, prints debug information during execution.
            env: Environment variables to set for CDO processes.

        Raises:
            RuntimeError: If CDO is not available at the specified path.

        Example:
            >>> cdo = CDO()
            >>> print(cdo.version)
            Climate Data Operators version 2.0.5

            >>> cdo = CDO(cdo_path="/opt/cdo/bin/cdo", debug=True)
        """
        self.cdo_path = cdo_path or "cdo"
        self.temp_dir = Path(temp_dir) if temp_dir else None
        self.debug = debug
        self.env = env or {}

        self._check_cdo_available()

    # ========== Query API (Primary - Django ORM-style) ==========

    def query(self, input_file: str | Path) -> CDOQuery:
        """
        Create a lazy CDO query for chaining operations (PRIMARY API).

        This is the primary v1.0.0 API, providing Django ORM-style lazy
        evaluation with chainable methods.

        Args:
            input_file: Path to input NetCDF file

        Returns:
            CDOQuery object for building pipeline

        Example:
            >>> cdo = CDO()
            >>> # Build and execute query
            >>> ds = (
            ...     cdo.query("data.nc")
            ...     .select_var("tas")
            ...     .select_year(2020)
            ...     .year_mean()
            ...     .field_mean()
            ...     .compute()
            ... )
            >>> # Inspect before execution
            >>> q = cdo.query("data.nc").select_var("tas").year_mean()
            >>> print(q.get_command())
            'cdo -yearmean -selname,tas data.nc'
            >>> # Branch queries for variations
            >>> base = cdo.query("data.nc").select_var("tas")
            >>> yearly = base.clone().year_mean().compute()
            >>> monthly = base.clone().month_mean().compute()

        See Also:
            - CDOQuery: Query builder class
            - F(): Create unbound queries for binary operations
        """
        from .query import CDOQuery

        return CDOQuery(input_file=input_file, operators=(), cdo_instance=self)

    def _execute_query(
        self, query: CDOQuery, output: str | Path | None = None
    ) -> xr.Dataset:
        """
        Execute a CDOQuery and return xarray Dataset.

        Args:
            query: Query to execute
            output: Optional output file path

        Returns:
            xarray.Dataset with results

        Raises:
            CDOExecutionError: If CDO command fails
        """
        import os
        import tempfile

        import xarray as xr

        from .validation import validate_file_exists

        # Validate input file exists
        if query._input is None:
            raise CDOError("Query has no input file (is it a template?)")
        validate_file_exists(query._input)

        # Build command
        cmd = query.get_command()

        # Determine output file
        if output:
            output_path = Path(output)
            use_temp = False
        else:
            fd, temp_path = tempfile.mkstemp(suffix=".nc", dir=self.temp_dir)
            os.close(fd)
            output_path = Path(temp_path)
            use_temp = True

        try:
            # Add output to command
            full_cmd = f"{cmd} {output_path}"

            if self.debug:
                print(f"[CDO] Executing: {full_cmd}")

            # Execute
            result = subprocess.run(
                full_cmd,
                shell=True,
                capture_output=True,
                text=True,
                env={**os.environ, **self.env},
            )

            if result.returncode != 0:
                raise CDOExecutionError(
                    message=f"CDO command failed with return code {result.returncode}",
                    command=full_cmd,
                    returncode=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr,
                )

            # Load result
            ds = xr.open_dataset(output_path)

            return ds

        finally:
            # Clean up temp file if used
            if use_temp and output_path.exists():
                output_path.unlink()

            # Clean up query temp files (e.g., shapefile masks)
            if hasattr(query, "_temp_files"):
                import contextlib

                for temp_file in query._temp_files:
                    if temp_file and temp_file.exists():
                        with contextlib.suppress(Exception):
                            temp_file.unlink()

    def _execute_binary_query(
        self, query: BinaryOpQuery, output: str | Path | None = None
    ) -> xr.Dataset:
        """
        Execute a BinaryOpQuery (binary arithmetic operation).

        Args:
            query: Binary operation query to execute
            output: Optional output file path

        Returns:
            xarray.Dataset with results

        Raises:
            CDOExecutionError: If CDO command fails
        """
        import tempfile

        import xarray as xr

        from .validation import validate_file_exists

        # Validate input files exist
        if query._left._input is None or query._right._input is None:
            raise CDOError("Binary query has unbound input files")
        validate_file_exists(query._left._input)
        validate_file_exists(query._right._input)

        # Build command
        cmd = query.get_command()

        # Determine output file
        if output:
            output_path = Path(output)
            use_temp = False
        else:
            fd, temp_path = tempfile.mkstemp(suffix=".nc", dir=self.temp_dir)
            import os

            os.close(fd)
            output_path = Path(temp_path)
            use_temp = True

        try:
            # Add output to command
            full_cmd = f"{cmd} {output_path}"

            if self.debug:
                print(f"[CDO] Executing: {full_cmd}")

            # Execute
            result = subprocess.run(
                full_cmd,
                shell=True,
                capture_output=True,
                text=True,
                env={**os.environ, **self.env},
            )

            if result.returncode != 0:
                raise CDOExecutionError(
                    message=f"CDO command failed with return code {result.returncode}",
                    command=full_cmd,
                    returncode=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr,
                )

            # Load result
            ds = xr.open_dataset(output_path)

            return ds

        finally:
            # Clean up temp file if used
            if use_temp and output_path.exists():
                output_path.unlink()

            # Clean up query temp files (e.g., shapefile masks)
            if hasattr(query, "_temp_files"):
                import contextlib

                print(query._temp_files)

                for temp_file in query._temp_files:
                    if temp_file and temp_file.exists():
                        with contextlib.suppress(Exception):
                            temp_file.unlink()

    def _check_cdo_available(self) -> None:
        """
        Check if CDO is available and executable.

        Raises:
            RuntimeError: If CDO is not available.
        """
        if not check_cdo_available(self.cdo_path):
            raise RuntimeError(
                f"CDO is not available at '{self.cdo_path}'. "
                "Please ensure CDO is installed and accessible."
            )

    @property
    def version(self) -> str:
        """
        Get the CDO version string.

        Returns:
            CDO version string.

        Example:
            >>> cdo = CDO()
            >>> print(cdo.version)
            Climate Data Operators version 2.0.5
        """
        return get_cdo_version(self.cdo_path)

    def run(
        self,
        cmd: str,
        *,
        output_file: str | Path | None = None,
        return_xr: bool = True,
        debug: bool | None = None,
        check_files: bool = True,
    ) -> str | tuple[xr.Dataset | None, str]:
        """
        Execute a raw CDO command string (legacy/backward compatibility).

        This method provides backward compatibility with the v0.x string-based
        interface. For new code, prefer using the dedicated operator methods
        like cdo.yearmean(), cdo.selname(), etc.

        Args:
            cmd: CDO command string (e.g., "sinfo data.nc" or "-yearmean data.nc").
            output_file: Optional output file path for data commands.
            return_xr: If True, return xarray.Dataset for data commands.
            debug: Enable debug output (overrides instance setting).
            check_files: If True, validate input files exist.

        Returns:
            For text commands: string output.
            For data commands: tuple of (xr.Dataset or None, log string).

        Raises:
            CDOExecutionError: If CDO command fails.

        Example:
            >>> cdo = CDO()
            >>> # Text command
            >>> info = cdo.run("sinfo data.nc")
            >>> # Data command
            >>> ds, log = cdo.run("-yearmean data.nc")
        """
        # Import the legacy cdo function for backward compatibility
        from typing import cast

        result = legacy_cdo(
            cmd,
            output_file=output_file,
            return_xr=return_xr,
            return_dict=False,
            debug=debug if debug is not None else self.debug,
            check_files=check_files,
        )
        # Cast to help mypy understand the return type
        return cast("str | tuple[xr.Dataset | None, str]", result)

    def _execute_text_command(self, cmd: str) -> str:
        """
        Execute a CDO command that returns text output.

        Args:
            cmd: CDO command string (without 'cdo' prefix).

        Returns:
            Text output from CDO.

        Raises:
            CDOExecutionError: If command execution fails.
        """
        full_cmd = [self.cdo_path, *cmd.split()]

        if self.debug:
            print(f"Executing: {' '.join(full_cmd)}")

        try:
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                env={**os.environ, **self.env},
                check=False,
            )

            if result.returncode != 0:
                raise CDOExecutionError(
                    f"CDO command failed: {cmd}",
                    command=cmd,
                    returncode=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr,
                )

            return result.stdout

        except FileNotFoundError as e:
            raise RuntimeError(f"CDO executable not found: {self.cdo_path}") from e

    def _execute_data_command(
        self,
        cmd: str,
        output: str | Path | None = None,
    ) -> xr.Dataset:
        """
        Execute a CDO command that produces data output.

        Args:
            cmd: CDO command string (without 'cdo' prefix).
            output: Optional output file path. If None, creates temp file.

        Returns:
            xarray.Dataset with the result.

        Raises:
            CDOExecutionError: If command execution fails.
        """
        import xarray as xr

        from .utils import cleanup_temp_file, create_temp_file

        # Create output file if not provided
        temp_created = False
        if output is None:
            output = create_temp_file(suffix=".nc", dir=self.temp_dir)
            temp_created = True

        try:
            # Build full command with output
            full_cmd = [self.cdo_path, *cmd.split(), str(output)]

            if self.debug:
                print(f"Executing: {' '.join(full_cmd)}")

            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                env={**os.environ, **self.env},
                check=False,
            )

            if result.returncode != 0:
                raise CDOExecutionError(
                    message=f"CDO command failed: {cmd}",
                    command=cmd,
                    returncode=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr,
                )

            # Load the result with xarray
            ds = xr.open_dataset(output)

            # Clean up temp file if we created it
            if temp_created:
                cleanup_temp_file(output)

            return ds

        except FileNotFoundError as e:
            raise RuntimeError(f"CDO executable not found: {self.cdo_path}") from e
        except Exception:
            # Clean up temp file on error
            if temp_created:
                cleanup_temp_file(output)
            raise

    def __repr__(self) -> str:
        """Return string representation of CDO instance."""
        return f"CDO(cdo_path='{self.cdo_path}', version='{self.version}')"

    # ========================================================================
    # Information Operators (Phase 2)
    # ========================================================================

    def sinfo(self, input: str | Path) -> SinfoResult:
        """
        Get comprehensive dataset summary information.

        Returns structured information about file format, variables,
        grid coordinates, vertical coordinates, and time information.

        Args:
            input: Input file path.

        Returns:
            SinfoResult with structured dataset information.

        Raises:
            CDOFileNotFoundError: If input file does not exist.
            CDOExecutionError: If CDO command fails.
            CDOParseError: If output parsing fails.

        Example:
            >>> cdo = CDO()
            >>> info = cdo.sinfo("data.nc")
            >>> print(info.file_format)
            NetCDF4
            >>> print(info.var_names)
            ['precip']
            >>> print(info.time_range)
            ('1981-01-01 00:00:00', '2022-12-31 00:00:00')
        """
        from .operators.info import SinfoOperator
        from .validation import validate_file_exists

        validate_file_exists(input)
        op = SinfoOperator()
        cmd = op.build_command(input)
        output = self._execute_text_command(cmd)
        return op.parse_output(output)

    def info(self, input: str | Path) -> InfoResult:
        """
        Get timestep-by-timestep statistics.

        Returns detailed statistics (min, mean, max) for each timestep.

        Args:
            input: Input file path.

        Returns:
            InfoResult with timestep information.

        Raises:
            CDOFileNotFoundError: If input file does not exist.
            CDOExecutionError: If CDO command fails.
            CDOParseError: If output parsing fails.

        Example:
            >>> cdo = CDO()
            >>> info = cdo.info("data.nc")
            >>> print(info.ntimesteps)
            15340
            >>> first = info.first_timestep
            >>> print(f"{first.datetime}: min={first.minimum}, mean={first.mean}")
        """
        from .operators.info import InfoOperator
        from .validation import validate_file_exists

        validate_file_exists(input)
        op = InfoOperator()
        cmd = op.build_command(input)
        output = self._execute_text_command(cmd)
        return op.parse_output(output)

    def griddes(self, input: str | Path) -> GriddesResult:
        """
        Get detailed grid description.

        Returns complete grid specification including type, dimensions,
        coordinates, and coordinate system information.

        Args:
            input: Input file path.

        Returns:
            GriddesResult with grid information.

        Raises:
            CDOFileNotFoundError: If input file does not exist.
            CDOExecutionError: If CDO command fails.
            CDOParseError: If output parsing fails.

        Example:
            >>> cdo = CDO()
            >>> grid = cdo.griddes("data.nc")
            >>> g = grid.primary_grid
            >>> print(f"{g.gridtype}: {g.xsize}x{g.ysize}")
            lonlat: 135x129
            >>> print(f"Resolution: {g.xinc}°x{g.yinc}°")
            Resolution: 0.25°x0.25°
        """
        from .operators.info import GriddesOperator
        from .validation import validate_file_exists

        validate_file_exists(input)
        op = GriddesOperator()
        cmd = op.build_command(input)
        output = self._execute_text_command(cmd)
        return op.parse_output(output)

    def zaxisdes(self, input: str | Path) -> ZaxisdesResult:
        """
        Get vertical axis description.

        Returns information about vertical coordinate system including
        axis type, number of levels, and level values.

        Args:
            input: Input file path.

        Returns:
            ZaxisdesResult with vertical axis information.

        Raises:
            CDOFileNotFoundError: If input file does not exist.
            CDOExecutionError: If CDO command fails.
            CDOParseError: If output parsing fails.

        Example:
            >>> cdo = CDO()
            >>> zaxis = cdo.zaxisdes("data.nc")
            >>> z = zaxis.primary_zaxis
            >>> print(f"{z.zaxistype}: {z.size} levels")
            surface: 1 levels
        """
        from .operators.info import ZaxisdesOperator
        from .validation import validate_file_exists

        validate_file_exists(input)
        op = ZaxisdesOperator()
        cmd = op.build_command(input)
        output = self._execute_text_command(cmd)
        return op.parse_output(output)

    def vlist(self, input: str | Path) -> VlistResult:
        """
        Get complete variable list with metadata.

        Returns comprehensive information about all variables including
        names, dimensions, data types, and associated grids/axes.

        Args:
            input: Input file path.

        Returns:
            VlistResult with variable information.

        Raises:
            CDOFileNotFoundError: If input file does not exist.
            CDOExecutionError: If CDO command fails.
            CDOParseError: If output parsing fails.

        Example:
            >>> cdo = CDO()
            >>> vlist = cdo.vlist("data.nc")
            >>> print(vlist.var_names)
            ['precip']
            >>> var = vlist.get_variable('precip')
            >>> print(var.longname)
            Climate Hazards group InfraRed Precipitation with Stations
        """
        from .operators.info import VlistOperator
        from .validation import validate_file_exists

        validate_file_exists(input)
        op = VlistOperator()
        cmd = op.build_command(input)
        output = self._execute_text_command(cmd)
        return op.parse_output(output)

    def partab(
        self,
        input: str | Path,
    ) -> PartabResult:
        """
        Get parameter table information.

        Returns the parameter table used by the dataset, showing
        parameter codes, names, units, and descriptions.

        Args:
            input: Input file path.

        Returns:
            PartabResult containing parameter table entries.

        Raises:
            CDOFileNotFoundError: If input file does not exist.
            CDOExecutionError: If CDO command fails.
            CDOParseError: If output parsing fails.

        Example:
            >>> cdo = CDO()
            >>> partab = cdo.partab("data.nc")
            >>> print(f"{partab.nparams} parameters")
            >>> for param in partab.parameters:
            ...     print(f"{param.code}: {param.name} [{param.units}]")
            >>> # Get specific parameter
            >>> temp = partab.get_parameter_by_name('temperature')
            >>> if temp:
            ...     print(f"Code {temp.code}: {temp.description}")
        """
        from .operators.info import PartabOperator
        from .validation import validate_file_exists

        validate_file_exists(input)
        op = PartabOperator()
        cmd = op.build_command(input)
        output = self._execute_text_command(cmd)
        return op.parse_output(output)

    # ========== File Operations (Phase 8) ==========

    def merge(self, *files: str | Path, output: str | Path | None = None) -> xr.Dataset:
        """
        Merge datasets with different fields.

        Args:
            *files: Input files to merge
            output: Optional output file path

        Returns:
            Merged dataset

        Example:
            >>> ds = cdo.merge("temp.nc", "precip.nc")
        """
        return self._execute_multi_file_op("merge", files, output)

    def mergetime(
        self, *files: str | Path, output: str | Path | None = None
    ) -> xr.Dataset:
        """
        Merge datasets sorted by date and time.

        Args:
            *files: Input files to merge
            output: Optional output file path

        Returns:
            Merged dataset

        Example:
            >>> ds = cdo.mergetime("data_2000.nc", "data_2001.nc")
        """
        return self._execute_multi_file_op("mergetime", files, output)

    def cat(self, *files: str | Path, output: str | Path | None = None) -> xr.Dataset:
        """
        Concatenate datasets.

        Args:
            *files: Input files to concatenate
            output: Optional output file path

        Returns:
            Concatenated dataset

        Example:
            >>> ds = cdo.cat("data_*.nc")
        """
        return self._execute_multi_file_op("cat", files, output)

    def copy(self, *files: str | Path, output: str | Path | None = None) -> xr.Dataset:
        """
        Copy datasets.

        Args:
            *files: Input files to copy
            output: Optional output file path

        Returns:
            Copied dataset

        Example:
            >>> ds = cdo.copy("data.nc", output="copy.nc")
        """
        return self._execute_multi_file_op("copy", files, output)

    def split_year(self, input: str | Path, prefix: str = "") -> list[Path]:
        """
        Split dataset into yearly files.

        Args:
            input: Input file path
            prefix: Optional prefix for output files

        Returns:
            List of generated file paths

        Example:
            >>> files = cdo.split_year("data.nc", "year_")
        """
        return self._execute_split_op("splityear", input, prefix)

    def split_month(self, input: str | Path, prefix: str = "") -> list[Path]:
        """
        Split dataset into monthly files.

        Args:
            input: Input file path
            prefix: Optional prefix for output files

        Returns:
            List of generated file paths

        Example:
            >>> files = cdo.split_month("data.nc", "mon_")
        """
        return self._execute_split_op("splitmon", input, prefix)

    def split_day(self, input: str | Path, prefix: str = "") -> list[Path]:
        """
        Split dataset into daily files.

        Args:
            input: Input file path
            prefix: Optional prefix for output files

        Returns:
            List of generated file paths

        Example:
            >>> files = cdo.split_day("data.nc", "day_")
        """
        return self._execute_split_op("splitday", input, prefix)

    def split_hour(self, input: str | Path, prefix: str = "") -> list[Path]:
        """
        Split dataset into hourly files.

        Args:
            input: Input file path
            prefix: Optional prefix for output files

        Returns:
            List of generated file paths

        Example:
            >>> files = cdo.split_hour("data.nc", "hour_")
        """
        return self._execute_split_op("splithour", input, prefix)

    def split_name(self, input: str | Path, prefix: str = "") -> list[Path]:
        """
        Split dataset by variable name.

        Args:
            input: Input file path
            prefix: Optional prefix for output files

        Returns:
            List of generated file paths

        Example:
            >>> files = cdo.split_name("data.nc", "var_")
        """
        return self._execute_split_op("splitname", input, prefix)

    def split_level(self, input: str | Path, prefix: str = "") -> list[Path]:
        """
        Split dataset by level.

        Args:
            input: Input file path
            prefix: Optional prefix for output files

        Returns:
            List of generated file paths

        Example:
            >>> files = cdo.split_level("data.nc", "lev_")
        """
        return self._execute_split_op("splitlevel", input, prefix)

    def split_timestep(
        self, input: str | Path, n: int = 1, prefix: str = ""
    ) -> list[Path]:
        """
        Split dataset into chunks of n timesteps.

        Args:
            input: Input file path
            n: Number of timesteps per chunk
            prefix: Optional prefix for output files

        Returns:
            List of generated file paths

        Example:
            >>> files = cdo.split_timestep("data.nc", 12, "year_chunk_")
        """
        return self._execute_split_op(f"splitsel,{n}", input, prefix)

    # ========== Helper Methods for File Operations ==========

    def _execute_multi_file_op(
        self, operator: str, files: tuple[str | Path, ...], output: str | Path | None
    ) -> xr.Dataset:
        """Execute an operator that takes multiple input files."""
        import tempfile

        import xarray as xr

        from .validation import validate_file_exists

        if not files:
            raise ValueError("At least one input file is required")

        # Validate inputs
        for f in files:
            validate_file_exists(f)

        # Determine output file
        if output:
            output_path = Path(output)
            use_temp = False
        else:
            fd, temp_path = tempfile.mkstemp(suffix=".nc", dir=self.temp_dir)
            os.close(fd)
            output_path = Path(temp_path)
            use_temp = True

        try:
            # Build command: cdo -operator file1 file2 ... output
            inputs = " ".join(str(Path(f)) for f in files)
            full_cmd = f"cdo -{operator} {inputs} {output_path}"

            if self.debug:
                print(f"[CDO] Executing: {full_cmd}")

            result = subprocess.run(
                full_cmd,
                shell=True,
                capture_output=True,
                text=True,
                env={**os.environ, **self.env},
            )

            if result.returncode != 0:
                raise CDOExecutionError(
                    message=f"CDO command failed with return code {result.returncode}",
                    command=full_cmd,
                    returncode=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr,
                )

            return xr.open_dataset(output_path)

        finally:
            if use_temp and output_path.exists():
                output_path.unlink()

    def _execute_split_op(
        self, operator: str, input_file: str | Path, prefix: str
    ) -> list[Path]:
        """Execute a split operator."""

        from .validation import validate_file_exists

        validate_file_exists(input_file)
        input_path = Path(input_file)

        # If prefix is not absolute, make it relative to current dir or temp dir?
        # CDO creates files in current directory if prefix doesn't have path.
        # Let's assume prefix is just a string or path.

        # We need to know where files are created to return them.
        # If prefix has a directory component, CDO puts them there.

        # Construct command: cdo -operator input prefix
        full_cmd = f"cdo -{operator} {input_path} {prefix}"

        if self.debug:
            print(f"[CDO] Executing: {full_cmd}")

        result = subprocess.run(
            full_cmd,
            shell=True,
            capture_output=True,
            text=True,
            env={**os.environ, **self.env},
        )

        if result.returncode != 0:
            raise CDOExecutionError(
                message=f"CDO command failed with return code {result.returncode}",
                command=full_cmd,
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )

        # Find generated files
        # This is tricky because we don't know exactly what CDO generated.
        # But we know the prefix.
        # If prefix is empty, CDO uses variable names or something else depending on operator.
        # If prefix is provided, files start with prefix.

        # NOTE: This implementation assumes the user handles the output files location via prefix
        # or they are in current directory.
        # We try to find them to return the list.

        if not prefix:
            # If no prefix, it's harder. For splitname it uses var names.
            # For splityear it uses input filename + year? No, actually just year if no prefix?
            # Actually cdo splityear input output_prefix
            # If output_prefix is missing, it might default to something.
            # But we passed prefix (even if empty string).
            pass

        # To be safe and robust, we might want to list files that match the pattern
        # created by CDO.
        # For now, let's return a list of Paths found matching the prefix pattern if provided.

        if prefix:
            parent_dir = Path(prefix).parent
            pattern = Path(prefix).name + "*"
            return list(parent_dir.glob(pattern))

        return []

    def showname(self, input: str | Path) -> list[str]:
        """
        Get list of variable names.

        Args:
            input: Input file path.

        Returns:
            List of variable names.
        """
        from .validation import validate_file_exists

        validate_file_exists(input)
        output = self._execute_text_command(f"showname {input}")
        return output.strip().split()

    def showcode(self, input: str | Path) -> list[int]:
        """
        Get list of variable codes.

        Args:
            input: Input file path.

        Returns:
            List of variable codes.
        """
        from .validation import validate_file_exists

        validate_file_exists(input)
        output = self._execute_text_command(f"showcode {input}")
        return [int(code) for code in output.strip().split()]

    def showunit(self, input: str | Path) -> list[str]:
        """
        Get list of variable units.

        Args:
            input: Input file path.

        Returns:
            List of variable units.
        """
        from .validation import validate_file_exists

        validate_file_exists(input)
        output = self._execute_text_command(f"showunit {input}")
        return output.strip().split()

    def showlevel(self, input: str | Path) -> list[float]:
        """
        Get list of vertical levels.

        Args:
            input: Input file path.

        Returns:
            List of vertical levels.
        """
        from .validation import validate_file_exists

        validate_file_exists(input)
        output = self._execute_text_command(f"showlevel {input}")
        return [float(level) for level in output.strip().split()]

    def showdate(self, input: str | Path) -> list[str]:
        """
        Get list of dates.

        Args:
            input: Input file path.

        Returns:
            List of dates (YYYY-MM-DD).
        """
        from .validation import validate_file_exists

        validate_file_exists(input)
        output = self._execute_text_command(f"showdate {input}")
        return output.strip().split()

    def showtime(self, input: str | Path) -> list[str]:
        """
        Get list of times.

        Args:
            input: Input file path.

        Returns:
            List of times (HH:MM:SS).
        """
        from .validation import validate_file_exists

        validate_file_exists(input)
        output = self._execute_text_command(f"showtime {input}")
        return output.strip().split()

    def ntime(self, input: str | Path) -> int:
        """
        Get number of timesteps.

        Args:
            input: Input file path.

        Returns:
            Number of timesteps.
        """
        from .validation import validate_file_exists

        validate_file_exists(input)
        output = self._execute_text_command(f"ntime {input}")
        return int(output.strip())

    def nvar(self, input: str | Path) -> int:
        """
        Get number of variables.

        Args:
            input: Input file path.

        Returns:
            Number of variables.
        """
        from .validation import validate_file_exists

        validate_file_exists(input)
        output = self._execute_text_command(f"nvar {input}")
        return int(output.strip())

    def nlevel(self, input: str | Path) -> int:
        """
        Get number of levels.

        Args:
            input: Input file path.

        Returns:
            Number of levels.
        """
        from .validation import validate_file_exists

        validate_file_exists(input)
        output = self._execute_text_command(f"nlevel {input}")
        return int(output.strip())

    # ========== Binary Operators (Convenience) ==========

    def add(
        self,
        input1: str | Path,
        input2: str | Path,
        output: str | Path | None = None,
    ) -> xr.Dataset:
        """
        Add two datasets.

        Args:
            input1: First input file.
            input2: Second input file.
            output: Optional output file.

        Returns:
            Resulting dataset.
        """
        return self._execute_multi_file_op("add", (input1, input2), output)

    def sub(
        self,
        input1: str | Path,
        input2: str | Path,
        output: str | Path | None = None,
    ) -> xr.Dataset:
        """
        Subtract two datasets.

        Args:
            input1: First input file.
            input2: Second input file.
            output: Optional output file.

        Returns:
            Resulting dataset.
        """
        return self._execute_multi_file_op("sub", (input1, input2), output)

    def mul(
        self,
        input1: str | Path,
        input2: str | Path,
        output: str | Path | None = None,
    ) -> xr.Dataset:
        """
        Multiply two datasets.

        Args:
            input1: First input file.
            input2: Second input file.
            output: Optional output file.

        Returns:
            Resulting dataset.
        """
        return self._execute_multi_file_op("mul", (input1, input2), output)

    def div(
        self,
        input1: str | Path,
        input2: str | Path,
        output: str | Path | None = None,
    ) -> xr.Dataset:
        """
        Divide two datasets.

        Args:
            input1: First input file.
            input2: Second input file.
            output: Optional output file.

        Returns:
            Resulting dataset.
        """
        return self._execute_multi_file_op("div", (input1, input2), output)

    def min(
        self,
        input1: str | Path,
        input2: str | Path,
        output: str | Path | None = None,
    ) -> xr.Dataset:
        """
        Minimum of two datasets.

        Args:
            input1: First input file.
            input2: Second input file.
            output: Optional output file.

        Returns:
            Resulting dataset.
        """
        return self._execute_multi_file_op("min", (input1, input2), output)

    def max(
        self,
        input1: str | Path,
        input2: str | Path,
        output: str | Path | None = None,
    ) -> xr.Dataset:
        """
        Maximum of two datasets.

        Args:
            input1: First input file.
            input2: Second input file.
            output: Optional output file.

        Returns:
            Resulting dataset.
        """
        return self._execute_multi_file_op("max", (input1, input2), output)

    def atan2(
        self,
        input1: str | Path,
        input2: str | Path,
        output: str | Path | None = None,
    ) -> xr.Dataset:
        """
        Arc tangent of two datasets.

        Args:
            input1: First input file.
            input2: Second input file.
            output: Optional output file.

        Returns:
            Resulting dataset.
        """
        return self._execute_multi_file_op("atan2", (input1, input2), output)

    # ========== Constant Operators (Convenience) ==========

    def addc(
        self,
        constant: float,
        input: str | Path,
        output: str | Path | None = None,
    ) -> xr.Dataset:
        """
        Add constant to dataset.

        Args:
            constant: Constant value.
            input: Input file.
            output: Optional output file.

        Returns:
            Resulting dataset.
        """
        return self.query(input).add_constant(constant).compute(output)

    def subc(
        self,
        constant: float,
        input: str | Path,
        output: str | Path | None = None,
    ) -> xr.Dataset:
        """
        Subtract constant from dataset.

        Args:
            constant: Constant value.
            input: Input file.
            output: Optional output file.

        Returns:
            Resulting dataset.
        """
        return self.query(input).subtract_constant(constant).compute(output)

    def mulc(
        self,
        constant: float,
        input: str | Path,
        output: str | Path | None = None,
    ) -> xr.Dataset:
        """
        Multiply dataset by constant.

        Args:
            constant: Constant value.
            input: Input file.
            output: Optional output file.

        Returns:
            Resulting dataset.
        """
        return self.query(input).multiply_constant(constant).compute(output)

    def divc(
        self,
        constant: float,
        input: str | Path,
        output: str | Path | None = None,
    ) -> xr.Dataset:
        """
        Divide dataset by constant.

        Args:
            constant: Constant value.
            input: Input file.
            output: Optional output file.

        Returns:
            Resulting dataset.
        """
        return self.query(input).divide_constant(constant).compute(output)

    # ========== Statistical Operators (Convenience) ==========

    def timmean(
        self, input: str | Path, output: str | Path | None = None
    ) -> xr.Dataset:
        """Calculate time mean."""
        return self.query(input).time_mean().compute(output)

    def timsum(self, input: str | Path, output: str | Path | None = None) -> xr.Dataset:
        """Calculate time sum."""
        return self.query(input).time_sum().compute(output)

    def timmin(self, input: str | Path, output: str | Path | None = None) -> xr.Dataset:
        """Calculate time minimum."""
        return self.query(input).time_min().compute(output)

    def timmax(self, input: str | Path, output: str | Path | None = None) -> xr.Dataset:
        """Calculate time maximum."""
        return self.query(input).time_max().compute(output)

    def timstd(self, input: str | Path, output: str | Path | None = None) -> xr.Dataset:
        """Calculate time standard deviation."""
        return self.query(input).time_std().compute(output)

    def yearmean(
        self, input: str | Path, output: str | Path | None = None
    ) -> xr.Dataset:
        """Calculate yearly mean."""
        return self.query(input).year_mean().compute(output)

    def yearsum(
        self, input: str | Path, output: str | Path | None = None
    ) -> xr.Dataset:
        """Calculate yearly sum."""
        return self.query(input).year_sum().compute(output)

    def yearmin(
        self, input: str | Path, output: str | Path | None = None
    ) -> xr.Dataset:
        """Calculate yearly minimum."""
        return self.query(input).year_min().compute(output)

    def yearmax(
        self, input: str | Path, output: str | Path | None = None
    ) -> xr.Dataset:
        """Calculate yearly maximum."""
        return self.query(input).year_max().compute(output)

    def yearstd(
        self, input: str | Path, output: str | Path | None = None
    ) -> xr.Dataset:
        """Calculate yearly standard deviation."""
        return self.query(input).year_std().compute(output)

    def monmean(
        self, input: str | Path, output: str | Path | None = None
    ) -> xr.Dataset:
        """Calculate monthly mean."""
        return self.query(input).month_mean().compute(output)

    def monsum(self, input: str | Path, output: str | Path | None = None) -> xr.Dataset:
        """Calculate monthly sum."""
        return self.query(input).month_sum().compute(output)

    def monmin(self, input: str | Path, output: str | Path | None = None) -> xr.Dataset:
        """Calculate monthly minimum."""
        return self.query(input).month_min().compute(output)

    def monmax(self, input: str | Path, output: str | Path | None = None) -> xr.Dataset:
        """Calculate monthly maximum."""
        return self.query(input).month_max().compute(output)

    def monstd(self, input: str | Path, output: str | Path | None = None) -> xr.Dataset:
        """Calculate monthly standard deviation."""
        return self.query(input).month_std().compute(output)

    def daymean(
        self, input: str | Path, output: str | Path | None = None
    ) -> xr.Dataset:
        """Calculate daily mean."""
        return self.query(input).day_mean().compute(output)

    def daysum(self, input: str | Path, output: str | Path | None = None) -> xr.Dataset:
        """Calculate daily sum."""
        return self.query(input).day_sum().compute(output)

    def fldmean(
        self, input: str | Path, output: str | Path | None = None
    ) -> xr.Dataset:
        """Calculate field mean."""
        return self.query(input).field_mean().compute(output)

    def fldsum(self, input: str | Path, output: str | Path | None = None) -> xr.Dataset:
        """Calculate field sum."""
        return self.query(input).field_sum().compute(output)

    def fldmin(self, input: str | Path, output: str | Path | None = None) -> xr.Dataset:
        """Calculate field minimum."""
        return self.query(input).field_min().compute(output)

    def fldmax(self, input: str | Path, output: str | Path | None = None) -> xr.Dataset:
        """Calculate field maximum."""
        return self.query(input).field_max().compute(output)

    def fldstd(self, input: str | Path, output: str | Path | None = None) -> xr.Dataset:
        """Calculate field standard deviation."""
        return self.query(input).field_std().compute(output)

    def zonmean(
        self, input: str | Path, output: str | Path | None = None
    ) -> xr.Dataset:
        """Calculate zonal mean."""
        return self.query(input).zonal_mean().compute(output)

    def mermean(
        self, input: str | Path, output: str | Path | None = None
    ) -> xr.Dataset:
        """Calculate meridional mean."""
        return self.query(input).meridional_mean().compute(output)
