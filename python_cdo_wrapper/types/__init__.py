"""Type definitions for v1.0.0+ API."""

from __future__ import annotations

from .grid import GridInfo, GridSpec, ZaxisInfo
from .results import (
    GriddesResult,
    InfoResult,
    PartabResult,
    SinfoResult,
    TimestepInfo,
    VlistResult,
    ZaxisdesResult,
)
from .variable import (
    DatasetVariable,
    GridCoordinates,
    PartabInfo,
    TimeInfo,
    VariableInfo,
    VerticalCoordinates,
)

__all__ = [
    "DatasetVariable",
    "GridCoordinates",
    "GridInfo",
    "GridSpec",
    "GriddesResult",
    "InfoResult",
    "PartabInfo",
    "PartabResult",
    "SinfoResult",
    "TimeInfo",
    "TimestepInfo",
    "VariableInfo",
    "VerticalCoordinates",
    "VlistResult",
    "ZaxisInfo",
    "ZaxisdesResult",
]
