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
    CDO_STRUCTURED_COMMANDS,
    CDO_TEXT_COMMANDS,
    CDOError,
    cdo,
    get_cdo_version,
    list_operators,
)
from python_cdo_wrapper.parsers import (
    CDOParser,
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
from python_cdo_wrapper.types import (
    AttributeDict,
    DatasetInfo,
    GridInfo,
    ParameterInfo,
    StructuredOutput,
    VariableInfo,
    VCTInfo,
    ZAxisInfo,
)

__version__ = "0.2.1"
__author__ = "B M Naren Karthik"
__email__ = "narenkarthikbm@gmail.com"

__all__ = [
    "CDO_STRUCTURED_COMMANDS",
    "CDO_TEXT_COMMANDS",
    "AttributeDict",
    "CDOError",
    "CDOParser",
    "DatasetInfo",
    "GridInfo",
    "GriddesParser",
    "ParameterInfo",
    "PartabParser",
    "ShowattsParser",
    "ShowattsglobParser",
    "SinfoParser",
    "StructuredOutput",
    "VCTInfo",
    "VariableInfo",
    "VctParser",
    "VlistParser",
    "ZAxisInfo",
    "ZaxisdesParser",
    "__version__",
    "cdo",
    "get_cdo_version",
    "get_supported_structured_commands",
    "list_operators",
    "parse_cdo_output",
]
