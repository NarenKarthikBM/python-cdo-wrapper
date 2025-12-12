"""
Core CDO wrapper functionality.

This module provides the main `cdo()` function that serves as a Pythonic
interface to the Climate Data Operators (CDO) command-line tool.

The wrapper automatically detects whether a CDO command returns text output
(like `sinfo`, `griddes`) or data output (like `yearmean`, `selname`), and
returns the appropriate Python object.

Example:
    >>> from python_cdo_wrapper import cdo
    >>>
    >>> # Text commands return strings
    >>> info = cdo("sinfo data.nc")
    >>> print(info)
    >>>
    >>> # Data commands return xarray.Dataset
    >>> ds, log = cdo("yearmean data.nc")
    >>> print(ds)
"""

from __future__ import annotations

import subprocess
import tempfile
from typing import TYPE_CHECKING, Any, Literal, overload

if TYPE_CHECKING:
    from pathlib import Path

    import xarray as xr

__all__ = [
    "CDO_STRUCTURED_COMMANDS",
    "CDO_TEXT_COMMANDS",
    "CDOError",
    "cdo",
    "execute_cdo",
]


class CDOError(Exception):
    """
    Exception raised when a CDO command fails.

    Attributes:
        command: The CDO command that failed.
        returncode: The return code from CDO.
        stdout: Standard output from CDO.
        stderr: Standard error output from CDO.

    Example:
        >>> try:
        ...     cdo("invalid_command data.nc")
        ... except CDOError as e:
        ...     print(f"CDO failed with code {e.returncode}")
        ...     print(f"Error: {e.stderr}")
    """

    def __init__(
        self,
        command: str,
        returncode: int,
        stdout: str = "",
        stderr: str = "",
    ) -> None:
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

        message = f"CDO command failed with return code {returncode}\n"
        message += f"Command: {command}\n"
        if stderr:
            message += f"Error: {stderr}"

        super().__init__(message)


# Complete list of CDO operators that return text output (read-only info operators)
# These commands print information to stdout rather than producing NetCDF output
CDO_TEXT_COMMANDS: frozenset[str] = frozenset(
    {
        # Grid information
        "griddes",
        "griddes2",
        "showgrid",
        "showgriddef",
        "showprojection",
        # File/variable information
        "sinfo",
        "sinfon",
        "sinfov",
        "info",
        "infon",
        "infov",
        "ninfo",
        "tinfo",
        "vlist",
        "showformat",
        "showcode",
        "showname",
        "showstdname",
        "showvar",
        "showparam",
        "showunit",
        "showltype",
        "showlevel",
        # Time information
        "showtimestamp",
        "showdate",
        "showtime",
        "showyear",
        "showmon",
        "showmonth",
        "showday",
        "showhour",
        "showminute",
        "showsecond",
        "showseason",
        # Axis information
        "showzaxis",
        "showzgrid",
        "showzrule",
        # Count operators
        "ntime",
        "nvar",
        "ngrids",
        "nvars",
        "nzaxis",
        "ntaxis",
        "nlevels",
        "nlevel",
        "npar",
        "ncode",
        "nyear",
        "nmon",
        "ndate",
        # Other info operators
        "partab",
        "codetab",
        "filedes",
        "pardes",
        "zaxisdes",
        "vct",
        "vct2",
        "showattribute",
        "showatts",
        "showattsglob",
        # Diff/comparison (text output)
        "diff",
        "diffn",
        "diffv",
        "diffc",
        # Version/help
        "version",
        "operators",
    }
)

# Subset of CDO_TEXT_COMMANDS that support structured output parsing
CDO_STRUCTURED_COMMANDS: frozenset[str] = frozenset(
    {
        "griddes",
        "griddes2",
        "zaxisdes",
        "sinfo",
        "sinfon",
        "sinfov",
        "info",
        "infon",
        "infov",
        "vlist",
        "showatts",
        "partab",
        "codetab",
        "vct",
        "vct2",
    }
)


def _check_cdo_installed() -> None:
    """
    Verify that CDO is installed and accessible.

    Raises:
        FileNotFoundError: If CDO is not found in PATH.
    """
    try:
        result = subprocess.run(
            ["cdo", "-V"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise FileNotFoundError("CDO returned non-zero exit code")
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            "CDO (Climate Data Operators) is not installed or not in PATH.\n"
            "Install CDO via:\n"
            "  - conda: conda install -c conda-forge cdo\n"
            "  - apt: sudo apt install cdo\n"
            "  - brew: brew install cdo"
        ) from exc


def _is_text_command(cmd: str) -> bool:
    """
    Determine if a CDO command returns text output.

    Args:
        cmd: The CDO command string.

    Returns:
        True if the command is a text-output command, False otherwise.
    """
    # Extract the operator name (first word, handle chained operators)
    # For chained operators like "-sinfo -selname,var", check first operator
    parts = cmd.strip().split()
    if not parts:
        return False

    # Get the first operator, stripping leading dash if present
    first_op = parts[0].lstrip("-").split(",")[0].lower()
    return first_op in CDO_TEXT_COMMANDS


def _validate_input_files(cmd: str) -> None:
    """
    Validate that input files in the command exist.

    Args:
        cmd: The CDO command string.

    Raises:
        FileNotFoundError: If any input NetCDF file doesn't exist.
    """
    from pathlib import Path

    parts = cmd.strip().split()
    for part in parts:
        # Check if it looks like a file path (ends with common extensions)
        if (
            any(
                part.endswith(ext) for ext in (".nc", ".nc4", ".grb", ".grib", ".grib2")
            )
            and not Path(part).exists()
        ):
            raise FileNotFoundError(f"Input file not found: {part}")


@overload
def cdo(
    cmd: str,
    *,
    output_file: str | Path | None = None,
    return_xr: Literal[True] = True,
    return_dict: Literal[True],
    debug: bool = False,
    check_files: bool = True,
) -> dict[str, Any] | list[dict[str, Any]]: ...


@overload
def cdo(
    cmd: str,
    *,
    output_file: str | Path | None = None,
    return_xr: Literal[True] = True,
    return_dict: Literal[False] = False,
    debug: bool = False,
    check_files: bool = True,
) -> str | tuple[xr.Dataset, str]: ...


@overload
def cdo(
    cmd: str,
    *,
    output_file: str | Path | None = None,
    return_xr: Literal[False],
    return_dict: Literal[False] = False,
    debug: bool = False,
    check_files: bool = True,
) -> str | tuple[None, str]: ...


@overload
def cdo(
    cmd: str,
    *,
    output_file: str | Path | None = None,
    return_xr: bool = True,
    return_dict: bool = False,
    debug: bool = False,
    check_files: bool = True,
) -> str | tuple[xr.Dataset | None, str] | dict[str, Any] | list[dict[str, Any]]: ...


def cdo(
    cmd: str,
    *,
    output_file: str | Path | None = None,
    return_xr: bool = True,
    return_dict: bool = False,
    debug: bool = False,
    check_files: bool = True,
) -> str | tuple[xr.Dataset | None, str] | dict[str, Any] | list[dict[str, Any]]:
    """
    Execute a CDO command and return results as Python objects.

    This wrapper intelligently handles both text-output commands (like `sinfo`,
    `griddes`) and data-output commands (like `yearmean`, `selname`), returning
    appropriate Python objects for each.

    Args:
        cmd: CDO command string (without the leading "cdo").
            Examples: "yearmean input.nc", "sinfo data.nc", "-selname,temp input.nc"

        output_file: Optional path for output NetCDF file. If None (default),
            a temporary file is created and cleaned up automatically.
            Only used for data-output commands.

        return_xr: If True (default), return an xarray.Dataset for data commands.
            If False, only return the log output without loading data.

        return_dict: If True, parse text command output into a structured dictionary
            (only works for supported text commands like griddes, sinfo, etc.).
            If False (default), return raw text output for text commands.

        debug: If True, print detailed command execution information including
            the full command, return code, stdout, and stderr.

        check_files: If True (default), validate that input files exist before
            running the command.

    Returns:
        For text commands (sinfo, griddes, etc.):
            str: The text output from CDO (if return_dict=False).
            dict | list[dict]: Parsed structured data (if return_dict=True).

        For data commands (yearmean, selname, etc.):
            tuple[xr.Dataset, str]: A tuple of (dataset, log_output) if return_xr=True.
            tuple[None, str]: A tuple of (None, log_output) if return_xr=False.

    Raises:
        CDOError: If the CDO command fails (non-zero return code).
        FileNotFoundError: If CDO is not installed or input files don't exist.
        ImportError: If xarray is not installed (for data commands with return_xr=True).

    Examples:
        Basic usage with text commands:

        >>> # Get file information
        >>> info = cdo("sinfo data.nc")
        >>> print(info)

        >>> # Get grid description
        >>> grid = cdo("griddes data.nc")

        >>> # Get structured grid information
        >>> grid_dict = cdo("griddes data.nc", return_dict=True)
        >>> print(grid_dict["gridtype"])
        >>> print(grid_dict["xsize"], grid_dict["ysize"])

        Data processing commands:

        >>> # Calculate yearly mean, returns xarray.Dataset
        >>> ds, log = cdo("yearmean input.nc")
        >>> print(ds.data_vars)

        >>> # Select a variable
        >>> ds, log = cdo("-selname,temperature input.nc")

        >>> # Chain operators
        >>> ds, log = cdo("-yearmean -selname,temp input.nc")

        Save output to specific file:

        >>> ds, log = cdo("yearmean input.nc", output_file="output.nc")
        >>> # output.nc is preserved (not deleted)

        Debugging:

        >>> ds, log = cdo("yearmean input.nc", debug=True)
        CDO Command: cdo yearmean input.nc /tmp/xxx.nc
        Return code: 0
        ...

    Notes:
        - CDO must be installed and available in PATH
        - For data commands, temporary files are automatically cleaned up
        - The wrapper uses shell=True, so be cautious with untrusted input
        - xarray is imported lazily only when needed for data commands

    See Also:
        - CDO documentation: https://code.mpimet.mpg.de/projects/cdo/
        - xarray documentation: https://docs.xarray.dev/
    """
    import xarray as xr  # Lazy import for text-only usage

    # Validate inputs
    if check_files:
        _validate_input_files(cmd)

    # Build the full command
    full_cmd = f"cdo {cmd}"

    # Determine command type
    is_text_cmd = _is_text_command(cmd)

    # For data commands, handle output file
    temp_output: str | None = None
    if not is_text_cmd and output_file is None:
        with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as tmp:
            temp_output = tmp.name
            output_file = temp_output
        full_cmd += f" {output_file}"
    elif not is_text_cmd and output_file is not None:
        full_cmd += f" {output_file}"

    # Execute CDO command
    result = subprocess.run(
        full_cmd,
        shell=True,
        capture_output=True,
        text=True,
    )

    # Debug output
    if debug:
        print(f"CDO Command: {full_cmd}")
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"Stdout:\n{result.stdout}")
        if result.stderr:
            print(f"Stderr:\n{result.stderr}")

    # Handle errors
    if result.returncode != 0:
        # Clean up temp file on error
        if temp_output:
            from pathlib import Path

            temp_path = Path(temp_output)
            if temp_path.exists():
                temp_path.unlink()

        raise CDOError(
            command=full_cmd,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )

    # Return appropriate result based on command type
    if is_text_cmd:
        # Text commands: return stdout directly or as structured dict
        output = result.stdout.strip()
        if return_dict:
            # Parse output into structured dictionary
            from python_cdo_wrapper.parsers_legacy import parse_cdo_output

            try:
                parsed: dict[str, object] | list[dict[str, object]] = parse_cdo_output(
                    cmd, output
                )
                return parsed
            except ValueError:
                # If parsing fails, return raw text
                return output
        return output

    elif return_xr:
        # Data commands with xarray: load and return dataset
        try:
            ds = xr.open_dataset(output_file)
        finally:
            # Clean up temp file after loading
            if temp_output:
                from pathlib import Path

                temp_path = Path(temp_output)
                if temp_path.exists():
                    temp_path.unlink()

        return ds, result.stderr.strip() or result.stdout.strip()

    else:
        # Data commands without xarray: just return log
        if temp_output:
            from pathlib import Path

            temp_path = Path(temp_output)
            if temp_path.exists():
                temp_path.unlink()

        return None, result.stderr.strip() or result.stdout.strip()


def execute_cdo(cmd: str, cdo_path: str = "cdo", debug: bool = False) -> str:
    """
    Execute a raw CDO command and return stdout.

    Args:
        cmd: Command string (without 'cdo ' prefix if cdo_path is used)
        cdo_path: Path to CDO executable
        debug: Whether to print debug info

    Returns:
        Standard output string
    """
    import os

    full_cmd = f"{cdo_path} {cmd}"
    if debug:
        print(f"[CDO] Executing: {full_cmd}")

    result = subprocess.run(
        full_cmd,
        shell=True,
        capture_output=True,
        text=True,
        env=os.environ,
    )

    if result.returncode != 0:
        raise CDOError(
            command=full_cmd,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )

    return result.stdout


def get_cdo_version() -> str:
    """
    Get the installed CDO version.

    Returns:
        str: The CDO version string.

    Raises:
        FileNotFoundError: If CDO is not installed.

    Example:
        >>> print(get_cdo_version())
        Climate Data Operators version 2.2.0 ...
    """
    _check_cdo_installed()
    result = subprocess.run(
        ["cdo", "-V"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stderr.strip() or result.stdout.strip()


def list_operators() -> list[str]:
    """
    List all available CDO operators.

    Returns:
        list[str]: A list of available CDO operator names.

    Example:
        >>> ops = list_operators()
        >>> "yearmean" in ops
        True
    """
    result = subprocess.run(
        ["cdo", "-h"],
        capture_output=True,
        text=True,
        check=False,
    )
    output = result.stderr or result.stdout

    # Parse operators from help output
    operators = []
    for line in output.split("\n"):
        line = line.strip()
        if line and not line.startswith(("CDO", "Usage", "Options", "-")):
            # Extract operator names
            for word in line.split():
                if word.isalnum() and word.islower():
                    operators.append(word)

    return sorted(set(operators))
