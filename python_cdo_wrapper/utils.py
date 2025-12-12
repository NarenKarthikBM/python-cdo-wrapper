"""Utility functions for python-cdo-wrapper."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


def create_temp_file(
    suffix: str = ".nc", prefix: str = "cdo_", dir: str | Path | None = None
) -> Path:
    """
    Create a temporary file for CDO operations.

    Args:
        suffix: File suffix (default: ".nc").
        prefix: File prefix (default: "cdo_").
        dir: Directory for temp file (default: system temp dir).

    Returns:
        Path to the temporary file.

    Example:
        >>> temp = create_temp_file()
        >>> print(temp)
        PosixPath('/tmp/cdo_a1b2c3.nc')
    """
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=dir)
    # Close the file descriptor since we just need the path
    import os

    os.close(fd)
    return Path(path)


def cleanup_temp_file(file_path: str | Path) -> None:
    """
    Remove a temporary file if it exists.

    Args:
        file_path: Path to the file to remove.

    Example:
        >>> cleanup_temp_file("/tmp/cdo_temp.nc")
    """
    path = Path(file_path)
    if path.exists():
        path.unlink()


def check_cdo_available(cdo_path: str = "cdo") -> bool:
    """
    Check if CDO is available and executable.

    Args:
        cdo_path: Path to CDO executable (default: "cdo").

    Returns:
        True if CDO is available, False otherwise.

    Example:
        >>> check_cdo_available()
        True
        >>> check_cdo_available("/nonexistent/cdo")
        False
    """
    try:
        result = subprocess.run(
            [cdo_path, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def get_cdo_version(cdo_path: str = "cdo") -> str:
    """
    Get the CDO version string.

    Args:
        cdo_path: Path to CDO executable (default: "cdo").

    Returns:
        CDO version string.

    Raises:
        RuntimeError: If CDO is not available.

    Example:
        >>> get_cdo_version()
        'Climate Data Operators version 2.0.5'
    """
    try:
        result = subprocess.run(
            [cdo_path, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        # First line usually contains the version
        first_line = result.stdout.split("\n")[0]
        return first_line.strip()
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        raise RuntimeError(f"CDO is not available at '{cdo_path}'") from e


def format_cdo_command(operator: str, *args: Any, **_kwargs: Any) -> str:
    """
    Format a CDO command string from operator and arguments.

    Args:
        operator: CDO operator name.
        *args: Positional arguments.
        **kwargs: Keyword arguments.

    Returns:
        Formatted CDO command string.

    Example:
        >>> format_cdo_command("selname", "tas", "pr")
        '-selname,tas,pr'
        >>> format_cdo_command("sellonlatbox", 0, 360, -90, 90)
        '-sellonlatbox,0,360,-90,90'
    """
    if args:
        args_str = ",".join(str(arg) for arg in args)
        return f"-{operator},{args_str}"
    return f"-{operator}"
