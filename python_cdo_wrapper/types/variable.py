"""Variable and dataset type definitions for CDO operations."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VariableInfo:
    """Information about a variable from vlist output."""

    var_id: int
    param: int
    grid_id: int
    zaxis_id: int
    stype_id: int
    tstep_type: int
    flag: int
    name: str
    longname: str | None = None
    units: str | None = None
    lev_id: int | None = None
    fvar_id: int | None = None
    flev_id: int | None = None
    mvar_id: int | None = None
    mlev_id: int | None = None
    index: int | None = None
    dtype: int | None = None
    level: float | None = None
    size: int | None = None

    @property
    def display_name(self) -> str:
        """Get display name (longname if available, else name)."""
        return self.longname if self.longname else self.name


@dataclass
class TimeInfo:
    """Time coordinate information."""

    ntime: int
    ref_time: str
    units: str
    calendar: str
    first_timestep: str | None = None
    last_timestep: str | None = None
    all_timesteps: list[str] | None = None

    @property
    def time_range(self) -> tuple[str, str] | None:
        """Get time range (first, last)."""
        if self.first_timestep and self.last_timestep:
            return (self.first_timestep, self.last_timestep)
        return None


@dataclass
class GridCoordinates:
    """Grid coordinate information from sinfo."""

    grid_id: int
    gridtype: str
    points: int
    xsize: int | None = None
    ysize: int | None = None
    longitude_start: float | None = None
    longitude_end: float | None = None
    longitude_inc: float | None = None
    longitude_units: str | None = None
    latitude_start: float | None = None
    latitude_end: float | None = None
    latitude_inc: float | None = None
    latitude_units: str | None = None

    @property
    def resolution(self) -> tuple[float, float] | None:
        """Get grid resolution (lon_inc, lat_inc)."""
        if self.longitude_inc is not None and self.latitude_inc is not None:
            return (self.longitude_inc, self.latitude_inc)
        return None


@dataclass
class VerticalCoordinates:
    """Vertical coordinate information from sinfo."""

    zaxis_id: int
    zaxistype: str
    levels: int
    level_values: list[float] | None = None


@dataclass
class DatasetVariable:
    """Variable information from sinfo output."""

    var_id: int
    institut: str
    source: str
    table_code: str
    steptype: str
    levels: int
    num: int
    points: int
    num2: int
    dtype: str
    param_id: int
    name: str | None = None

    @property
    def has_name(self) -> bool:
        """Check if variable has a name."""
        return self.name is not None and self.name != ""


@dataclass
class PartabInfo:
    """
    Parameter table entry information.

    Attributes:
        code: Parameter code (numeric or string).
        name: Short parameter name.
        units: Units of measurement.
        description: Full parameter description.
        longname: Optional long name of the parameter.
        raw: Raw text line from output.
    """

    code: str
    name: str
    units: str | None = None
    description: str | None = None
    longname: str | None = None
    raw: str | None = None

    @property
    def display_name(self) -> str:
        """Get a display name (longname if available, else name)."""
        return self.longname or self.name
