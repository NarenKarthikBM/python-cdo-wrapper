"""
Type definitions for structured CDO output.

This module defines TypedDict classes for various CDO command outputs
to provide type hints and documentation for structured data.
"""

from __future__ import annotations

from typing import Any, TypedDict, Union


class GridInfo(TypedDict, total=False):
    """
    Grid information from griddes command.

    Attributes:
        gridtype: Type of grid (e.g., 'lonlat', 'curvilinear', 'unstructured').
        gridsize: Total number of grid points.
        xsize: Number of points in x/longitude direction.
        ysize: Number of points in y/latitude direction.
        xvals: Array of x/longitude coordinate values.
        yvals: Array of y/latitude coordinate values.
        xfirst: First x/longitude coordinate value.
        xlast: Last x/longitude coordinate value.
        xinc: Increment in x/longitude direction.
        yfirst: First y/latitude coordinate value.
        ylast: Last y/latitude coordinate value.
        yinc: Increment in y/latitude direction.
        xunits: Units of x coordinates.
        yunits: Units of y coordinates.
        xname: Name of x coordinate.
        yname: Name of y coordinate.
    """

    gridtype: str
    gridsize: int
    xsize: int
    ysize: int
    xvals: list[float]
    yvals: list[float]
    xfirst: float
    xlast: float
    xinc: float
    yfirst: float
    ylast: float
    yinc: float
    xunits: str
    yunits: str
    xname: str
    yname: str


class ZAxisInfo(TypedDict, total=False):
    """
    Vertical axis information from zaxisdes command.

    Attributes:
        zaxistype: Type of vertical axis (e.g., 'pressure', 'height', 'hybrid').
        size: Number of vertical levels.
        levels: Array of level values.
        lbounds: Lower bounds of levels.
        ubounds: Upper bounds of levels.
        vctsize: Size of vertical coordinate table.
        vct: Vertical coordinate table values.
        name: Name of the vertical axis.
        longname: Long name/description.
        units: Units of the vertical coordinate.
    """

    zaxistype: str
    size: int
    levels: list[float]
    lbounds: list[float]
    ubounds: list[float]
    vctsize: int
    vct: list[float]
    name: str
    longname: str
    units: str


class VariableInfo(TypedDict, total=False):
    """
    Variable information from vlist or sinfo commands.

    Attributes:
        name: Variable name.
        code: Variable code number.
        longname: Long descriptive name.
        units: Units of measurement.
        grid: Grid identifier or description.
        levels: Number of vertical levels.
        datatype: Data type (e.g., 'float', 'double').
        raw: Raw text line from output.
        parts: Parsed parts of the output line.
        date: Date from sinfo output (e.g., '2020-01-01').
        time: Time from sinfo output (e.g., '00:00:00').
        level: Level value from sinfo output.
        gridsize: Grid size from sinfo output.
        num: Number identifier from sinfo output.
        dtype: Data type from sinfo output (e.g., 'F64', 'F32').
    """

    name: str
    code: int
    longname: str
    units: str
    grid: str
    levels: int
    datatype: str
    raw: str
    parts: list[str]
    date: str
    time: str
    level: int | str
    gridsize: int | str
    num: int | str
    dtype: str


class DatasetInfo(TypedDict, total=False):
    """
    Dataset information from sinfo/info commands.

    Attributes:
        metadata: General file metadata.
        variables: List of variables in the dataset.
        format: File format (e.g., 'netCDF', 'GRIB').
        dimensions: Dictionary of dimension information.
        attributes: Global attributes.
    """

    metadata: dict[str, Any]
    variables: list[VariableInfo]
    format: str
    dimensions: dict[str, int]
    attributes: dict[str, Any]


class ParameterInfo(TypedDict, total=False):
    """
    Parameter information from partab/codetab commands.

    Attributes:
        code: Parameter code.
        name: Short parameter name.
        units: Units of measurement.
        description: Full parameter description.
        raw: Raw text line from output.
    """

    code: str
    name: str
    units: str
    description: str
    raw: str


class VCTInfo(TypedDict):
    """
    Vertical coordinate table from vct/vct2 commands.

    Attributes:
        vct: Array of vertical coordinate table values.
    """

    vct: list[float]


class AttributeDict(TypedDict):
    """
    Dictionary of attributes.

    This is a flexible dictionary type for variable or global attributes.
    Keys are attribute names, values can be strings, numbers, or other types.
    """

    pass  # Intentionally empty - allows any string keys with Any values


# Type alias for structured output from CDO commands
StructuredOutput = Union[
    GridInfo,
    ZAxisInfo,
    DatasetInfo,
    list[VariableInfo],
    list[ParameterInfo],
    VCTInfo,
    dict[str, AttributeDict],
    dict[str, Any],
]
