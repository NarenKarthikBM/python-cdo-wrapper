"""Result type definitions for CDO information operators."""

from __future__ import annotations

from dataclasses import dataclass

from .grid import GridInfo, ZaxisInfo  # noqa: TC001
from .variable import (  # noqa: TC001
    DatasetVariable,
    GridCoordinates,
    PartabInfo,
    TimeInfo,
    VariableInfo,
    VerticalCoordinates,
)


@dataclass
class SinfoResult:
    """
    Structured result from sinfo command.

    Contains comprehensive dataset information including format,
    variables, grid, vertical coordinates, and time information.
    """

    file_format: str
    variables: list[DatasetVariable]
    grid_coordinates: list[GridCoordinates]
    vertical_coordinates: list[VerticalCoordinates]
    time_info: TimeInfo

    @property
    def var_names(self) -> list[str]:
        """Get list of variable names (excluding unnamed variables)."""
        return [v.name for v in self.variables if v.has_name and v.name is not None]

    @property
    def nvar(self) -> int:
        """Get number of variables."""
        return len(self.variables)

    @property
    def time_range(self) -> tuple[str, str] | None:
        """Get first and last timestep."""
        return self.time_info.time_range

    @property
    def primary_grid(self) -> GridCoordinates | None:
        """Get primary grid (first grid if multiple)."""
        return self.grid_coordinates[0] if self.grid_coordinates else None

    @property
    def primary_vertical(self) -> VerticalCoordinates | None:
        """Get primary vertical coordinates (first if multiple)."""
        return self.vertical_coordinates[0] if self.vertical_coordinates else None


@dataclass
class InfoResult:
    """
    Result from info command.

    Contains timestep-by-timestep statistics for variables.
    """

    timesteps: list[TimestepInfo]

    @property
    def ntimesteps(self) -> int:
        """Get number of timesteps."""
        return len(self.timesteps)

    @property
    def first_timestep(self) -> TimestepInfo | None:
        """Get first timestep info."""
        return self.timesteps[0] if self.timesteps else None

    @property
    def last_timestep(self) -> TimestepInfo | None:
        """Get last timestep info."""
        return self.timesteps[-1] if self.timesteps else None


@dataclass
class TimestepInfo:
    """Information for a single timestep from info output."""

    timestep: int
    date: str
    time: str
    level: int
    gridsize: int
    miss: int
    minimum: float
    mean: float
    maximum: float
    param_id: int

    @property
    def datetime(self) -> str:
        """Get combined date and time string."""
        return f"{self.date} {self.time}"


@dataclass
class GriddesResult:
    """
    Result from griddes command.

    Contains detailed grid description for one or more grids.
    """

    grids: list[GridInfo]

    @property
    def ngrids(self) -> int:
        """Get number of grids."""
        return len(self.grids)

    @property
    def primary_grid(self) -> GridInfo | None:
        """Get primary grid (first grid if multiple)."""
        return self.grids[0] if self.grids else None


@dataclass
class ZaxisdesResult:
    """
    Result from zaxisdes command.

    Contains vertical axis descriptions.
    """

    zaxes: list[ZaxisInfo]

    @property
    def nzaxes(self) -> int:
        """Get number of vertical axes."""
        return len(self.zaxes)

    @property
    def primary_zaxis(self) -> ZaxisInfo | None:
        """Get primary vertical axis (first if multiple)."""
        return self.zaxes[0] if self.zaxes else None


@dataclass
class VlistResult:
    """
    Result from vlist command.

    Contains complete variable list with metadata.
    """

    vlist_id: int
    nvars: int
    ngrids: int
    nzaxis: int
    nsubtypes: int
    taxis_id: int
    inst_id: int
    model_id: int
    table_id: int
    variables: list[VariableInfo]

    @property
    def var_names(self) -> list[str]:
        """Get list of variable names."""
        return [v.name for v in self.variables if v.name is not None]

    def get_variable(self, name: str) -> VariableInfo | None:
        """
        Get variable information by name.

        Args:
            name: Variable name.

        Returns:
            VariableInfo if found, None otherwise.
        """
        for var in self.variables:
            if var.name == name:
                return var
        return None


@dataclass
class PartabResult:
    """
    Result from partab/codetab command.

    Contains parameter table entries.

    Attributes:
        parameters: List of parameter information.
        table_name: Optional name of the parameter table.
    """

    parameters: list[PartabInfo]
    table_name: str | None = None

    @property
    def nparams(self) -> int:
        """Get the number of parameters."""
        return len(self.parameters)

    @property
    def param_codes(self) -> list[str]:
        """Get list of all parameter codes."""
        return [p.code for p in self.parameters]

    @property
    def param_names(self) -> list[str]:
        """Get list of all parameter names."""
        return [p.name for p in self.parameters]

    def get_parameter(self, code: str | int) -> PartabInfo | None:
        """
        Get parameter by code.

        Args:
            code: Parameter code to search for.

        Returns:
            PartabInfo if found, None otherwise.
        """
        code_str = str(code)
        for param in self.parameters:
            if param.code == code_str:
                return param
        return None

    def get_parameter_by_name(self, name: str) -> PartabInfo | None:
        """
        Get parameter by name.

        Args:
            name: Parameter name to search for.

        Returns:
            PartabInfo if found, None otherwise.
        """
        for param in self.parameters:
            if param.name == name:
                return param
        return None
