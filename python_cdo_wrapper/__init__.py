"""
Python CDO Wrapper - A Pythonic interface to Climate Data Operators.

This package provides a simple, universal wrapper for CDO (Climate Data Operators)
that integrates seamlessly with Jupyter notebooks and xarray workflows.

Example usage (v0.2.x - legacy API):
    >>> from python_cdo_wrapper import cdo
    >>> ds, log = cdo("yearmean input.nc")
    >>> info = cdo("sinfo input.nc")

Example usage (v1.0.0+ - new API):
    >>> from python_cdo_wrapper import CDO
    >>> cdo = CDO()
    >>> ds = cdo.yearmean("input.nc")  # Coming in Phase 4
    >>> info = cdo.sinfo("input.nc")   # Coming in Phase 2

For more information, see:
    - Documentation: https://github.com/NarenKarthikBM/python-cdo-wrapper
    - CDO Reference: https://code.mpimet.mpg.de/projects/cdo/
"""

import importlib.util

# v1.0.0+ API
# Import from legacy parsers.py module (before Phase 2 parsers/ package)
# We need to explicitly reference the .py file to avoid conflict with parsers/ package
from python_cdo_wrapper.cdo import CDO

# v0.2.x API (legacy)
from python_cdo_wrapper.core import (
    CDO_STRUCTURED_COMMANDS,
    CDO_TEXT_COMMANDS,
    CDOError,
    cdo,
    get_cdo_version,
    list_operators,
)
from python_cdo_wrapper.exceptions import (
    CDOError as CDOErrorV1,
)
from python_cdo_wrapper.exceptions import (
    CDOExecutionError,
    CDOFileNotFoundError,
    CDOParseError,
    CDOValidationError,
)
from python_cdo_wrapper.parsers_legacy import (
    CDOParser,
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

# v1.0.0+ Query API (PRIMARY)
from python_cdo_wrapper.query import BinaryOpQuery, CDOQuery, CDOQueryTemplate, F
from python_cdo_wrapper.types.grid import (
    GridInfo,
    GridSpec,
    ZaxisInfo,
)

# v1.0.0+ types (Phase 2)
from python_cdo_wrapper.types.results import (
    GriddesResult,
    InfoResult,
    PartabResult,
    SinfoResult,
    VlistResult,
    ZaxisdesResult,
)
from python_cdo_wrapper.types.variable import (
    VariableInfo,
)
from python_cdo_wrapper.types_legacy import (
    GridInfo as GridInfoV1,
)

# Shapefile utilities (optional - requires geopandas)
_HAS_SHAPEFILE_SUPPORT = importlib.util.find_spec("geopandas") is not None

if _HAS_SHAPEFILE_SUPPORT:
    from python_cdo_wrapper.shapefile_utils import (
        create_mask_from_shapefile as create_mask_from_shapefile,
    )

__version__ = "1.1.2"
__author__ = "B M Naren Karthik"
__email__ = "narenkarthikbm@gmail.com"

__all__ = [
    "CDO",
    "CDO_STRUCTURED_COMMANDS",
    "CDO_TEXT_COMMANDS",
    "AttributeDict",
    "BinaryOpQuery",
    "CDOError",
    "CDOErrorV1",
    "CDOExecutionError",
    "CDOFileNotFoundError",
    "CDOParseError",
    "CDOParser",
    "CDOQuery",
    "CDOQueryTemplate",
    "CDOValidationError",
    "DatasetInfo",
    "F",
    "GridInfo",
    "GridInfoV1",
    "GridSpec",
    "GriddesParser",
    "GriddesResult",
    "InfoResult",
    "ParameterInfo",
    "PartabParser",
    "PartabResult",
    "ShowattsParser",
    "SinfoParser",
    "SinfoResult",
    "StructuredOutput",
    "VCTInfo",
    "VariableInfo",
    "VctParser",
    "VlistParser",
    "VlistResult",
    "ZAxisInfo",
    "ZaxisInfo",
    "ZaxisdesParser",
    "ZaxisdesResult",
    "__version__",
    "cdo",
    "get_cdo_version",
    "get_supported_structured_commands",
    "list_operators",
    "parse_cdo_output",
]

# Add shapefile utilities to __all__ if available
if _HAS_SHAPEFILE_SUPPORT:
    __all__.append("create_mask_from_shapefile")
