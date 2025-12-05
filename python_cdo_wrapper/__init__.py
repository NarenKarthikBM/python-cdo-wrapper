"""
Python CDO Wrapper - A Pythonic interface to Climate Data Operators.

This package provides a simple, universal wrapper for CDO (Climate Data Operators)
that integrates seamlessly with Jupyter notebooks and xarray workflows.

Example usage:
    >>> from python_cdo_wrapper import cdo
    >>> ds, log = cdo("yearmean input.nc")
    >>> info = cdo("sinfo input.nc")

For more information, see:
    - Documentation: https://github.com/NarenKarthikBM/python-cdo-wrapper
    - CDO Reference: https://code.mpimet.mpg.de/projects/cdo/
"""

from python_cdo_wrapper.core import (
    CDO_TEXT_COMMANDS,
    CDOError,
    cdo,
    get_cdo_version,
    list_operators,
)

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "you@example.com"

__all__ = [
    "CDO_TEXT_COMMANDS",
    "CDOError",
    "__version__",
    "cdo",
    "get_cdo_version",
    "list_operators",
]
