"""Grid type definitions for CDO operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class GridInfo:
    """Information about a grid from griddes output."""

    grid_id: int
    gridtype: str
    gridsize: int
    datatype: str | None = None
    xsize: int | None = None
    ysize: int | None = None
    xname: str | None = None
    xlongname: str | None = None
    xunits: str | None = None
    yname: str | None = None
    ylongname: str | None = None
    yunits: str | None = None
    xfirst: float | None = None
    xinc: float | None = None
    yfirst: float | None = None
    yinc: float | None = None
    xvals: list[float] | None = None
    yvals: list[float] | None = None
    scanningMode: float | None = None
    # Rotated grid projection fields
    grid_mapping: str | None = None
    grid_mapping_name: str | None = None
    grid_north_pole_longitude: float | None = None
    grid_north_pole_latitude: float | None = None

    @property
    def lon_range(self) -> tuple[float, float] | None:
        """Get longitude range (start, end)."""
        if self.xfirst is not None and self.xinc is not None and self.xsize is not None:
            return (self.xfirst, self.xfirst + (self.xsize - 1) * self.xinc)
        return None

    @property
    def lat_range(self) -> tuple[float, float] | None:
        """Get latitude range (start, end)."""
        if self.yfirst is not None and self.yinc is not None and self.ysize is not None:
            return (self.yfirst, self.yfirst + (self.ysize - 1) * self.yinc)
        return None


@dataclass
class ZaxisInfo:
    """Information about vertical axis from zaxisdes output."""

    zaxis_id: int
    zaxistype: str
    size: int
    name: str | None = None
    longname: str | None = None
    units: str | None = None
    levels: list[float] | None = None
    lbounds: list[float] | None = None
    ubounds: list[float] | None = None

    @property
    def is_surface(self) -> bool:
        """Check if this is a surface level."""
        return self.zaxistype.lower() == "surface"

    @property
    def level_range(self) -> tuple[float, float] | None:
        """Get level range (min, max)."""
        if self.levels and len(self.levels) > 0:
            return (min(self.levels), max(self.levels))
        return None


@dataclass
class GridSpec:
    """
    Specification for creating a target grid.

    Used for interpolation and regridding operations.
    """

    gridtype: Literal["lonlat", "gaussian", "curvilinear", "unstructured"]
    xsize: int
    ysize: int
    xfirst: float = -180.0
    xinc: float | None = None
    yfirst: float = -90.0
    yinc: float | None = None
    xvals: list[float] | None = None
    yvals: list[float] | None = None

    def to_cdo_string(self) -> str:
        """
        Convert to CDO grid description format.

        Returns:
            String representation for CDO grid description file.

        Example:
            >>> spec = GridSpec.global_1deg()
            >>> print(spec.to_cdo_string())
            gridtype = lonlat
            xsize = 360
            ysize = 180
            xfirst = -180.0
            xinc = 1.0
            yfirst = -90.0
            yinc = 1.0
        """
        lines = [
            f"gridtype = {self.gridtype}",
            f"xsize = {self.xsize}",
            f"ysize = {self.ysize}",
        ]

        if self.xfirst is not None:
            lines.append(f"xfirst = {self.xfirst}")
        if self.xinc is not None:
            lines.append(f"xinc = {self.xinc}")
        if self.yfirst is not None:
            lines.append(f"yfirst = {self.yfirst}")
        if self.yinc is not None:
            lines.append(f"yinc = {self.yinc}")

        if self.xvals:
            lines.append(f"xvals = {' '.join(map(str, self.xvals))}")
        if self.yvals:
            lines.append(f"yvals = {' '.join(map(str, self.yvals))}")

        return "\n".join(lines)

    @classmethod
    def global_1deg(cls) -> GridSpec:
        """
        Create a global 1-degree regular lonlat grid.

        Returns:
            GridSpec for 360x180 global grid at 1-degree resolution.
        """
        return cls(
            gridtype="lonlat",
            xsize=360,
            ysize=180,
            xfirst=-180.0,
            xinc=1.0,
            yfirst=-90.0,
            yinc=1.0,
        )

    @classmethod
    def global_half_deg(cls) -> GridSpec:
        """
        Create a global 0.5-degree regular lonlat grid.

        Returns:
            GridSpec for 720x360 global grid at 0.5-degree resolution.
        """
        return cls(
            gridtype="lonlat",
            xsize=720,
            ysize=360,
            xfirst=-180.0,
            xinc=0.5,
            yfirst=-90.0,
            yinc=0.5,
        )

    @classmethod
    def global_quarter_deg(cls) -> GridSpec:
        """
        Create a global 0.25-degree regular lonlat grid.

        Returns:
            GridSpec for 1440x720 global grid at 0.25-degree resolution.
        """
        return cls(
            gridtype="lonlat",
            xsize=1440,
            ysize=720,
            xfirst=-180.0,
            xinc=0.25,
            yfirst=-90.0,
            yinc=0.25,
        )

    @classmethod
    def regional(
        cls,
        lon_start: float,
        lon_end: float,
        lat_start: float,
        lat_end: float,
        resolution: float,
    ) -> GridSpec:
        """
        Create a regional lonlat grid.

        Args:
            lon_start: Starting longitude.
            lon_end: Ending longitude.
            lat_start: Starting latitude.
            lat_end: Ending latitude.
            resolution: Grid resolution in degrees.

        Returns:
            GridSpec for regional grid.

        Example:
            >>> # India region at 0.25 degree
            >>> spec = GridSpec.regional(66, 100, 6, 38, 0.25)
        """
        xsize = int((lon_end - lon_start) / resolution) + 1
        ysize = int((lat_end - lat_start) / resolution) + 1

        return cls(
            gridtype="lonlat",
            xsize=xsize,
            ysize=ysize,
            xfirst=lon_start,
            xinc=resolution,
            yfirst=lat_start,
            yinc=resolution,
        )
