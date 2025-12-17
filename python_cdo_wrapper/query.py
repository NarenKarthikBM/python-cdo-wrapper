"""
Django ORM-style query builder for CDO operations.

This module provides the core CDOQuery abstraction that enables lazy,
chainable construction of CDO pipelines.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    import xarray as xr

    from .cdo import CDO
    from .types.grid import GridSpec
    from .types.results import (
        GriddesResult,
        InfoResult,
        PartabResult,
        SinfoResult,
        VlistResult,
        ZaxisdesResult,
    )

from .exceptions import CDOError, CDOFileNotFoundError, CDOValidationError
from .operators.base import OperatorSpec


# @dataclass(frozen=True)
class CDOQuery:
    """
    Lazy, chainable CDO query builder (Django QuerySet pattern).

    CDOQuery represents a CDO pipeline that hasn't been executed yet.
    Operations are added by chaining methods, and execution happens
    only when terminal methods like compute() are called.

    The query is immutable - each method returns a new CDOQuery instance.

    Example:
        >>> from python_cdo_wrapper import CDO
        >>> cdo = CDO()
        >>> q = (
        ...     cdo.query("data.nc")
        ...     .select_var("tas")
        ...     .select_year(2020)
        ...     .year_mean()
        ...     .field_mean()
        ... )
        >>> print(q.get_command())
        'cdo -fldmean -yearmean -selyear,2020 -selname,tas data.nc'
        >>> ds = q.compute()  # Execute now

    Attributes:
        _input: Input file path
        _operators: Tuple of OperatorSpec objects (immutable)
        _options: Tuple of global options (immutable)
        _cdo: Reference to parent CDO instance
    """

    _input: Path | None
    _operators: tuple[OperatorSpec, ...]
    _options: tuple[str, ...]
    _cdo: CDO | None
    _temp_files: tuple[Path, ...]

    def __init__(
        self,
        input_file: str | Path | None,
        operators: tuple[OperatorSpec, ...] = (),
        options: tuple[str, ...] = (),
        cdo_instance: CDO | None = None,
        temp_files: tuple[Path, ...] = (),
    ):
        """
        Initialize a CDO query.

        Args:
            input_file: Path to input NetCDF file (or None for templates)
            operators: Tuple of operator specs (immutable)
            options: Tuple of global options (immutable)
            cdo_instance: Parent CDO instance for execution
            temp_files: Tuple of temporary file paths to cleanup (immutable)

        Note:
            Use object.__setattr__ for frozen dataclass initialization
        """
        object.__setattr__(self, "_input", Path(input_file) if input_file else None)
        object.__setattr__(self, "_operators", operators)
        object.__setattr__(self, "_options", options)
        object.__setattr__(self, "_cdo", cdo_instance)
        object.__setattr__(self, "_temp_files", temp_files)

    def _clone(self, **kwargs: Any) -> CDOQuery:
        """
        Create a copy with modifications (immutability pattern).

        Args:
            **kwargs: Attributes to override (input_file, operators, options, cdo_instance, temp_files)

        Returns:
            New CDOQuery (or subclass) with modifications
        """
        return self.__class__(
            input_file=kwargs.get("input_file", self._input),
            operators=kwargs.get("operators", self._operators),
            options=kwargs.get("options", self._options),
            cdo_instance=kwargs.get("cdo_instance", self._cdo),
            temp_files=kwargs.get("temp_files", self._temp_files),
        )

    def _add_operator(self, spec: OperatorSpec) -> CDOQuery:
        """
        Add an operator and return new query (immutable).

        Args:
            spec: Operator specification to add

        Returns:
            New CDOQuery with operator appended
        """
        return self._clone(operators=(*self._operators, spec))

    # ========== Query Introspection ==========

    def __repr__(self) -> str:
        """Rich representation showing query pipeline."""
        ops = " → ".join(op.name for op in self._operators) or "(empty)"
        return f"<CDOQuery: {self._input.name if self._input else 'unbound'} | {ops}>"

    def __len__(self) -> int:
        """Number of operations in the query."""
        return len(self._operators)

    def get_operations(self) -> list[OperatorSpec]:
        """
        Get list of operations in this query.

        Returns:
            List of OperatorSpec objects
        """
        return list(self._operators)

    # ========== Selection Operators ==========

    def select_var(self, *names: str) -> CDOQuery:
        """
        Select variables by name.

        Args:
            *names: Variable names to select

        Returns:
            New query with selname operator

        Raises:
            CDOValidationError: If no variable names provided

        Example:
            >>> q = cdo.query("data.nc").select_var("tas", "pr")
            >>> q.get_command()
            'cdo -selname,tas,pr data.nc'
        """
        if not names:
            raise CDOValidationError(
                message="No variable names provided",
                parameter="names",
                value=names,
                expected="At least one variable name",
            )
        return self._add_operator(OperatorSpec("selname", args=names))

    def select_level(self, *levels: float) -> CDOQuery:
        """
        Select vertical levels.

        Args:
            *levels: Level values to select

        Returns:
            New query with sellevel operator

        Raises:
            CDOValidationError: If no levels provided

        Example:
            >>> q = cdo.query("data.nc").select_level(1000, 850, 500)
        """
        if not levels:
            raise CDOValidationError(
                message="No levels provided",
                parameter="levels",
                value=levels,
                expected="At least one level",
            )
        return self._add_operator(OperatorSpec("sellevel", args=levels))

    def select_year(self, *years: int) -> CDOQuery:
        """
        Select specific years.

        Args:
            *years: Years to select

        Returns:
            New query with selyear operator

        Example:
            >>> q = cdo.query("data.nc").select_year(2020, 2021)
        """
        if not years:
            raise CDOValidationError(
                message="No years provided",
                parameter="years",
                value=years,
                expected="At least one year",
            )
        return self._add_operator(OperatorSpec("selyear", args=years))

    def select_month(self, *months: int) -> CDOQuery:
        """
        Select specific months.

        Args:
            *months: Month numbers (1-12)

        Returns:
            New query with selmon operator

        Raises:
            CDOValidationError: If invalid month numbers

        Example:
            >>> q = cdo.query("data.nc").select_month(6, 7, 8)  # JJA
        """
        if not months:
            raise CDOValidationError(
                message="No months provided",
                parameter="months",
                value=months,
                expected="At least one month",
            )
        if any(m < 1 or m > 12 for m in months):
            raise CDOValidationError(
                message="Invalid month numbers",
                parameter="months",
                value=months,
                expected="Month numbers between 1 and 12",
            )
        return self._add_operator(OperatorSpec("selmon", args=months))

    def select_region(
        self, lon1: float, lon2: float, lat1: float, lat2: float
    ) -> CDOQuery:
        """
        Select rectangular geographic region.

        Args:
            lon1: Western longitude
            lon2: Eastern
            lat1: Southern latitude
            lat2: Northern latitude

        Returns:
            New query with sellonlatbox operator

        Example:
            >>> q = cdo.query("data.nc").select_region(-10, 40, 35, 70)  # Europe
        """
        return self._add_operator(
            OperatorSpec("sellonlatbox", args=(lon1, lon2, lat1, lat2))
        )

    def select_day(self, *days: int) -> CDOQuery:
        """
        Select specific days of the month.

        Args:
            *days: Day numbers (1-31)

        Returns:
            New query with selday operator

        Raises:
            CDOValidationError: If no days provided or invalid day numbers

        Example:
            >>> q = cdo.query("data.nc").select_day(1, 15)  # 1st and 15th of each month
        """
        if not days:
            raise CDOValidationError(
                message="No days provided",
                parameter="days",
                value=days,
                expected="At least one day",
            )
        if any(d < 1 or d > 31 for d in days):
            raise CDOValidationError(
                message="Invalid day numbers",
                parameter="days",
                value=days,
                expected="Day numbers between 1 and 31",
            )
        return self._add_operator(OperatorSpec("selday", args=days))

    def select_hour(self, *hours: int) -> CDOQuery:
        """
        Select specific hours.

        Args:
            *hours: Hour values (0-23)

        Returns:
            New query with selhour operator

        Raises:
            CDOValidationError: If no hours provided or invalid hour values

        Example:
            >>> q = cdo.query("data.nc").select_hour(0, 6, 12, 18)  # 6-hourly
        """
        if not hours:
            raise CDOValidationError(
                message="No hours provided",
                parameter="hours",
                value=hours,
                expected="At least one hour",
            )
        if any(h < 0 or h > 23 for h in hours):
            raise CDOValidationError(
                message="Invalid hour values",
                parameter="hours",
                value=hours,
                expected="Hour values between 0 and 23",
            )
        return self._add_operator(OperatorSpec("selhour", args=hours))

    def select_season(self, *seasons: str) -> CDOQuery:
        """
        Select specific seasons.

        Args:
            *seasons: Season codes ("DJF", "MAM", "JJA", "SON") - case insensitive

        Returns:
            New query with selseason operator

        Raises:
            CDOValidationError: If no seasons provided or invalid season codes

        Example:
            >>> q = cdo.query("data.nc").select_season("DJF", "JJA")  # Winter and summer
        """
        if not seasons:
            raise CDOValidationError(
                message="No seasons provided",
                parameter="seasons",
                value=seasons,
                expected="At least one season (DJF, MAM, JJA, SON)",
            )
        valid_seasons = {"DJF", "MAM", "JJA", "SON"}
        seasons_upper = tuple(s.upper() for s in seasons)
        if any(s not in valid_seasons for s in seasons_upper):
            raise CDOValidationError(
                message="Invalid season codes",
                parameter="seasons",
                value=seasons,
                expected="Valid seasons: DJF, MAM, JJA, SON",
            )
        return self._add_operator(OperatorSpec("selseason", args=seasons_upper))

    def select_date(self, start: str, end: str | None = None) -> CDOQuery:
        """
        Select date range or specific date.

        Args:
            start: Start date in "YYYY-MM-DD" or "YYYY-MM-DDThh:mm:ss" format
            end: Optional end date (if omitted, selects only start date)

        Returns:
            New query with seldate operator

        Example:
            >>> q = cdo.query("data.nc").select_date("2020-01-01", "2020-12-31")
            >>> q = cdo.query("data.nc").select_date("2020-06-15")  # Single date
        """
        if end is None:
            return self._add_operator(OperatorSpec("seldate", args=(start,)))
        return self._add_operator(OperatorSpec("seldate", args=(start, end)))

    def select_time(self, *times: str) -> CDOQuery:
        """
        Select specific times of day.

        Args:
            *times: Time values in "HH:MM:SS" or "HH:MM" format

        Returns:
            New query with seltime operator

        Raises:
            CDOValidationError: If no times provided

        Example:
            >>> q = cdo.query("data.nc").select_time("00:00:00", "12:00:00")
        """
        if not times:
            raise CDOValidationError(
                message="No times provided",
                parameter="times",
                value=times,
                expected="At least one time value (HH:MM:SS or HH:MM)",
            )
        return self._add_operator(OperatorSpec("seltime", args=times))

    def select_timestep(self, *steps: int) -> CDOQuery:
        """
        Select specific timesteps by index (1-based).

        Args:
            *steps: Timestep indices (1-based, positive integers)

        Returns:
            New query with seltimestep operator

        Raises:
            CDOValidationError: If no steps provided or invalid step values

        Example:
            >>> q = cdo.query("data.nc").select_timestep(1, 2, 3)  # First 3 timesteps
        """
        if not steps:
            raise CDOValidationError(
                message="No timesteps provided",
                parameter="steps",
                value=steps,
                expected="At least one timestep index",
            )
        if any(s < 1 for s in steps):
            raise CDOValidationError(
                message="Invalid timestep indices",
                parameter="steps",
                value=steps,
                expected="Positive timestep indices (1-based)",
            )
        return self._add_operator(OperatorSpec("seltimestep", args=steps))

    def select_code(self, *codes: int) -> CDOQuery:
        """
        Select variables by parameter code number.

        Args:
            *codes: Parameter code numbers (e.g., GRIB codes)

        Returns:
            New query with selcode operator

        Raises:
            CDOValidationError: If no codes provided

        Example:
            >>> q = cdo.query("data.nc").select_code(130, 131)  # T and U by GRIB code
        """
        if not codes:
            raise CDOValidationError(
                message="No codes provided",
                parameter="codes",
                value=codes,
                expected="At least one parameter code",
            )
        return self._add_operator(OperatorSpec("selcode", args=codes))

    def select_level_idx(self, *indices: int) -> CDOQuery:
        """
        Select vertical levels by index (1-based).

        Args:
            *indices: Level indices (1-based, positive integers)

        Returns:
            New query with sellevidx operator

        Raises:
            CDOValidationError: If no indices provided or invalid values

        Example:
            >>> q = cdo.query("data.nc").select_level_idx(1, 2, 3)  # First 3 levels
        """
        if not indices:
            raise CDOValidationError(
                message="No level indices provided",
                parameter="indices",
                value=indices,
                expected="At least one level index",
            )
        if any(i < 1 for i in indices):
            raise CDOValidationError(
                message="Invalid level indices",
                parameter="indices",
                value=indices,
                expected="Positive level indices (1-based)",
            )
        return self._add_operator(OperatorSpec("sellevidx", args=indices))

    def select_level_type(self, ltype: int) -> CDOQuery:
        """
        Select by level type code.

        Args:
            ltype: Level type code (e.g., 100 for pressure levels in GRIB)

        Returns:
            New query with selltype operator

        Example:
            >>> q = cdo.query("data.nc").select_level_type(100)  # Pressure levels
        """
        return self._add_operator(OperatorSpec("selltype", args=(ltype,)))

    def select_grid(self, grid_num: int) -> CDOQuery:
        """
        Select a specific grid from a file with multiple grids.

        Args:
            grid_num: Grid number (1-based)

        Returns:
            New query with selgrid operator

        Raises:
            CDOValidationError: If grid_num is not positive

        Example:
            >>> q = cdo.query("data.nc").select_grid(1)  # First grid
        """
        if grid_num < 1:
            raise CDOValidationError(
                message="Invalid grid number",
                parameter="grid_num",
                value=grid_num,
                expected="Positive grid number (1-based)",
            )
        return self._add_operator(OperatorSpec("selgrid", args=(grid_num,)))

    def select_zaxis(self, zaxis_num: int) -> CDOQuery:
        """
        Select a specific vertical axis from a file with multiple z-axes.

        Args:
            zaxis_num: Z-axis number (1-based)

        Returns:
            New query with selzaxis operator

        Raises:
            CDOValidationError: If zaxis_num is not positive

        Example:
            >>> q = cdo.query("data.nc").select_zaxis(1)  # First z-axis
        """
        if zaxis_num < 1:
            raise CDOValidationError(
                message="Invalid z-axis number",
                parameter="zaxis_num",
                value=zaxis_num,
                expected="Positive z-axis number (1-based)",
            )
        return self._add_operator(OperatorSpec("selzaxis", args=(zaxis_num,)))

    def select_index_box(self, x1: int, x2: int, y1: int, y2: int) -> CDOQuery:
        """
        Select a box by grid indices.

        Args:
            x1: First x index (1-based)
            x2: Last x index
            y1: First y index (1-based)
            y2: Last y index

        Returns:
            New query with selindexbox operator

        Raises:
            CDOValidationError: If indices are invalid

        Example:
            >>> q = cdo.query("data.nc").select_index_box(1, 100, 1, 50)
        """
        if any(i < 1 for i in (x1, x2, y1, y2)):
            raise CDOValidationError(
                message="Invalid index values",
                parameter="indices",
                value=(x1, x2, y1, y2),
                expected="Positive indices (1-based)",
            )
        if x1 > x2:
            raise CDOValidationError(
                message="Invalid x index range",
                parameter="x1, x2",
                value=(x1, x2),
                expected="x1 <= x2",
            )
        if y1 > y2:
            raise CDOValidationError(
                message="Invalid y index range",
                parameter="y1, y2",
                value=(y1, y2),
                expected="y1 <= y2",
            )
        return self._add_operator(OperatorSpec("selindexbox", args=(x1, x2, y1, y2)))

    def select_mask(self, mask_file: str | Path) -> CDOQuery:
        """
        Apply a mask from another file.

        The mask file should contain a field with 0s (masked) and 1s (valid).
        Grid points where the mask is 0 are set to missing value.

        Args:
            mask_file: Path to mask file

        Returns:
            New query with ifthen operator (masking operation)

        Example:
            >>> q = cdo.query("data.nc").select_mask("land_mask.nc")
        """
        # Note: CDO uses 'ifthen' for masking, not 'selmask'
        # ifthen,mask_file input_file - keeps values where mask != 0
        return self._add_operator(OperatorSpec("ifthen", args=(str(mask_file),)))

    def mask_by_shapefile(
        self,
        shapefile_path: str | Path,
        lat_name: str = "lat",
        lon_name: str = "lon",
    ) -> BinaryOpQuery:
        """
        Mask data by shapefile polygon extent (complete pipeline).

        This is a high-level operator that encapsulates the complete workflow:
        1. Load shapefile and extract polygon geometries
        2. Create binary mask (1=inside, 0=outside) using NumPy point-in-polygon
        3. Save mask as temporary NetCDF file
        4. Apply mask using CDO ifthen operator
        5. Auto-cleanup temporary files after compute()

        Requires: geopandas (install with: pip install python-cdo-wrapper[shapefiles])

        Args:
            shapefile_path: Path to ESRI shapefile (.shp)
            lat_name: Latitude coordinate name in NetCDF (default: "lat")
            lon_name: Longitude coordinate name in NetCDF (default: "lon")

        Returns:
            BinaryOpQuery with masking applied (ifthen operation)

        Raises:
            CDOError: If geopandas not installed or input file not set
            CDOFileNotFoundError: If shapefile doesn't exist
            CDOValidationError: If coordinates not found

        Example:
            >>> # Simple usage - mask to shapefile region
            >>> masked = cdo.query("data.nc").mask_by_shapefile("region.shp").compute()
            >>>
            >>> # Chain with other operators
            >>> result = (
            ...     cdo.query("data.nc")
            ...     .mask_by_shapefile("amazon.shp")
            ...     .year_mean()
            ...     .compute()
            ... )
            >>>
            >>> # Custom coordinate names
            >>> masked = cdo.query("data.nc").mask_by_shapefile(
            ...     "region.shp",
            ...     lat_name="latitude",
            ...     lon_name="longitude"
            ... ).compute()

        Note:
            - Shapefile CRS is automatically reprojected to WGS84 (EPSG:4326) if needed
            - Works with both 1D (regular) and 2D (curvilinear) grids
            - Handles multi-polygon shapefiles
            - Temporary mask file is automatically cleaned up after compute()
            - Uses ifthen for masking (sets outside values to NaN)
        """
        from .shapefile_utils import create_mask_from_shapefile

        # Validate shapefile exists
        shapefile_path = Path(shapefile_path)
        if not shapefile_path.exists():
            raise CDOFileNotFoundError(
                message=f"Shapefile not found: {shapefile_path}",
                file_path=str(shapefile_path),
            )

        # Check that query has input file
        if self._input is None:
            raise CDOError("Query has no input file - cannot create mask")

        # Create mask from shapefile
        # This happens immediately (not lazily) because we need the mask file
        mask_ds = create_mask_from_shapefile(
            shapefile_path=shapefile_path,
            reference_nc=self._input,
            lat_name=lat_name,
            lon_name=lon_name,
        )

        # Save mask to temporary file (securely)
        fd, temp_path = tempfile.mkstemp(suffix="_mask.nc")
        import os

        os.close(fd)  # Close the file descriptor, xarray will handle the file
        mask_path = Path(temp_path)
        mask_ds.to_netcdf(mask_path)
        mask_ds.close()

        # Create mask query (unbound, just references the file)
        mask_query = CDOQuery._create_unbound(mask_path)

        # Apply mask using ifthen binary operator
        # CDO syntax: cdo -ifthen mask.nc data.nc output.nc
        # The mask is the left operand (condition), data is the right operand
        binary_query = BinaryOpQuery(
            operator="ifthen",
            left=mask_query,
            right=self,
            cdo_instance=self._cdo,
        )

        # Store temp file path for cleanup (immutable pattern)
        # Merge temp files from both operands
        all_temp_files = (*self._temp_files, mask_path)

        # Update the binary query's temp files using object.__setattr__ (frozen dataclass pattern)
        object.__setattr__(binary_query, "_temp_files", all_temp_files)

        return binary_query

    # ========== Statistical Operators ==========

    def year_mean(self) -> CDOQuery:
        """
        Calculate yearly mean.

        Returns:
            New query with yearmean operator

        Example:
            >>> q = cdo.query("data.nc").year_mean()
        """
        return self._add_operator(OperatorSpec("yearmean"))

    def month_mean(self) -> CDOQuery:
        """
        Calculate monthly mean.

        Returns:
            New query with monmean operator
        """
        return self._add_operator(OperatorSpec("monmean"))

    def time_mean(self) -> CDOQuery:
        """
        Calculate time mean (average over all timesteps).

        Returns:
            New query with timmean operator
        """
        return self._add_operator(OperatorSpec("timmean"))

    def field_mean(self) -> CDOQuery:
        """
        Calculate spatial field mean (area-weighted if grid has cell areas).

        Returns:
            New query with fldmean operator

        Example:
            >>> q = cdo.query("data.nc").year_mean().field_mean()
        """
        return self._add_operator(OperatorSpec("fldmean"))

    # ========== Time Statistics ==========

    def time_sum(self) -> CDOQuery:
        """Calculate sum over all timesteps."""
        return self._add_operator(OperatorSpec("timsum"))

    def time_min(self) -> CDOQuery:
        """Calculate minimum over all timesteps."""
        return self._add_operator(OperatorSpec("timmin"))

    def time_max(self) -> CDOQuery:
        """Calculate maximum over all timesteps."""
        return self._add_operator(OperatorSpec("timmax"))

    def time_std(self) -> CDOQuery:
        """Calculate standard deviation over all timesteps."""
        return self._add_operator(OperatorSpec("timstd"))

    def time_var(self) -> CDOQuery:
        """Calculate variance over all timesteps."""
        return self._add_operator(OperatorSpec("timvar"))

    def time_range(self) -> CDOQuery:
        """Calculate range (max - min) over all timesteps."""
        return self._add_operator(OperatorSpec("timrange"))

    # ========== Year Statistics ==========

    def year_sum(self) -> CDOQuery:
        """Calculate yearly sum."""
        return self._add_operator(OperatorSpec("yearsum"))

    def year_min(self) -> CDOQuery:
        """Calculate yearly minimum."""
        return self._add_operator(OperatorSpec("yearmin"))

    def year_max(self) -> CDOQuery:
        """Calculate yearly maximum."""
        return self._add_operator(OperatorSpec("yearmax"))

    def year_std(self) -> CDOQuery:
        """Calculate yearly standard deviation."""
        return self._add_operator(OperatorSpec("yearstd"))

    def year_var(self) -> CDOQuery:
        """Calculate yearly variance."""
        return self._add_operator(OperatorSpec("yearvar"))

    # ========== Month Statistics ==========

    def month_sum(self) -> CDOQuery:
        """Calculate monthly sum."""
        return self._add_operator(OperatorSpec("monsum"))

    def month_min(self) -> CDOQuery:
        """Calculate monthly minimum."""
        return self._add_operator(OperatorSpec("monmin"))

    def month_max(self) -> CDOQuery:
        """Calculate monthly maximum."""
        return self._add_operator(OperatorSpec("monmax"))

    def month_std(self) -> CDOQuery:
        """Calculate monthly standard deviation."""
        return self._add_operator(OperatorSpec("monstd"))

    # ========== Day and Hour Statistics ==========

    def day_mean(self) -> CDOQuery:
        """Calculate daily mean."""
        return self._add_operator(OperatorSpec("daymean"))

    def day_sum(self) -> CDOQuery:
        """Calculate daily sum."""
        return self._add_operator(OperatorSpec("daysum"))

    def hour_mean(self) -> CDOQuery:
        """Calculate hourly mean."""
        return self._add_operator(OperatorSpec("hourmean"))

    # ========== Seasonal Statistics ==========

    def season_mean(self) -> CDOQuery:
        """
        Calculate seasonal mean (aggregates by DJF, MAM, JJA, SON).

        Returns:
            New query with seasmean operator

        Example:
            >>> q = cdo.query("data.nc").season_mean()
        """
        return self._add_operator(OperatorSpec("seasmean"))

    def season_sum(self) -> CDOQuery:
        """Calculate seasonal sum."""
        return self._add_operator(OperatorSpec("seassum"))

    # ========== Field Statistics ==========

    def field_sum(self) -> CDOQuery:
        """Calculate spatial field sum."""
        return self._add_operator(OperatorSpec("fldsum"))

    def field_min(self) -> CDOQuery:
        """Calculate spatial field minimum."""
        return self._add_operator(OperatorSpec("fldmin"))

    def field_max(self) -> CDOQuery:
        """Calculate spatial field maximum."""
        return self._add_operator(OperatorSpec("fldmax"))

    def field_std(self) -> CDOQuery:
        """Calculate spatial field standard deviation."""
        return self._add_operator(OperatorSpec("fldstd"))

    def field_var(self) -> CDOQuery:
        """Calculate spatial field variance."""
        return self._add_operator(OperatorSpec("fldvar"))

    def field_range(self) -> CDOQuery:
        """Calculate spatial field range (max - min)."""
        return self._add_operator(OperatorSpec("fldrange"))

    def field_percentile(self, p: float) -> CDOQuery:
        """
        Calculate spatial field percentile.

        Args:
            p: Percentile value (0-100)

        Returns:
            New query with fldpctl operator

        Raises:
            CDOValidationError: If p is not between 0 and 100

        Example:
            >>> q = cdo.query("data.nc").field_percentile(95)  # 95th percentile
        """
        if not 0 <= p <= 100:
            raise CDOValidationError(
                message="Invalid percentile value",
                parameter="p",
                value=p,
                expected="Percentile between 0 and 100",
            )
        return self._add_operator(OperatorSpec("fldpctl", args=(p,)))

    # ========== Zonal and Meridional Statistics ==========

    def zonal_mean(self) -> CDOQuery:
        """Calculate zonal mean (average along longitude)."""
        return self._add_operator(OperatorSpec("zonmean"))

    def zonal_sum(self) -> CDOQuery:
        """Calculate zonal sum (sum along longitude)."""
        return self._add_operator(OperatorSpec("zonsum"))

    def meridional_mean(self) -> CDOQuery:
        """Calculate meridional mean (average along latitude)."""
        return self._add_operator(OperatorSpec("mermean"))

    # ========== Vertical Statistics ==========

    def vert_mean(self) -> CDOQuery:
        """Calculate vertical mean."""
        return self._add_operator(OperatorSpec("vertmean"))

    def vert_sum(self) -> CDOQuery:
        """Calculate vertical sum."""
        return self._add_operator(OperatorSpec("vertsum"))

    def vert_min(self) -> CDOQuery:
        """Calculate vertical minimum."""
        return self._add_operator(OperatorSpec("vertmin"))

    def vert_max(self) -> CDOQuery:
        """Calculate vertical maximum."""
        return self._add_operator(OperatorSpec("vertmax"))

    def vert_std(self) -> CDOQuery:
        """Calculate vertical standard deviation."""
        return self._add_operator(OperatorSpec("vertstd"))

    def vert_int(self) -> CDOQuery:
        """Calculate vertical integration."""
        return self._add_operator(OperatorSpec("vertint"))

    # ========== Running/Moving Statistics ==========

    def running_mean(self, n: int) -> CDOQuery:
        """
        Calculate running mean with window size n.

        Args:
            n: Window size (positive integer)

        Returns:
            New query with runmean operator

        Raises:
            CDOValidationError: If n is not positive

        Example:
            >>> q = cdo.query("data.nc").running_mean(5)  # 5-timestep running mean
        """
        if n < 1:
            raise CDOValidationError(
                message="Invalid window size",
                parameter="n",
                value=n,
                expected="Positive integer",
            )
        return self._add_operator(OperatorSpec("runmean", args=(n,)))

    def running_sum(self, n: int) -> CDOQuery:
        """
        Calculate running sum with window size n.

        Args:
            n: Window size (positive integer)

        Raises:
            CDOValidationError: If n is not positive
        """
        if n < 1:
            raise CDOValidationError(
                message="Invalid window size",
                parameter="n",
                value=n,
                expected="Positive integer",
            )
        return self._add_operator(OperatorSpec("runsum", args=(n,)))

    def running_min(self, n: int) -> CDOQuery:
        """
        Calculate running minimum with window size n.

        Args:
            n: Window size (positive integer)

        Raises:
            CDOValidationError: If n is not positive
        """
        if n < 1:
            raise CDOValidationError(
                message="Invalid window size",
                parameter="n",
                value=n,
                expected="Positive integer",
            )
        return self._add_operator(OperatorSpec("runmin", args=(n,)))

    def running_max(self, n: int) -> CDOQuery:
        """
        Calculate running maximum with window size n.

        Args:
            n: Window size (positive integer)

        Raises:
            CDOValidationError: If n is not positive
        """
        if n < 1:
            raise CDOValidationError(
                message="Invalid window size",
                parameter="n",
                value=n,
                expected="Positive integer",
            )
        return self._add_operator(OperatorSpec("runmax", args=(n,)))

    def running_std(self, n: int) -> CDOQuery:
        """
        Calculate running standard deviation with window size n.

        Args:
            n: Window size (positive integer)

        Raises:
            CDOValidationError: If n is not positive
        """
        if n < 1:
            raise CDOValidationError(
                message="Invalid window size",
                parameter="n",
                value=n,
                expected="Positive integer",
            )
        return self._add_operator(OperatorSpec("runstd", args=(n,)))

    # ========== Percentile Operations ==========

    def time_percentile(self, p: float) -> CDOQuery:
        """
        Calculate percentile over time.

        Args:
            p: Percentile value (0-100)

        Raises:
            CDOValidationError: If p is not between 0 and 100

        Example:
            >>> q = cdo.query("data.nc").time_percentile(95)
        """
        if not 0 <= p <= 100:
            raise CDOValidationError(
                message="Invalid percentile value",
                parameter="p",
                value=p,
                expected="Percentile between 0 and 100",
            )
        return self._add_operator(OperatorSpec("timpctl", args=(p,)))

    def year_percentile(self, p: float) -> CDOQuery:
        """
        Calculate yearly percentile.

        Args:
            p: Percentile value (0-100)

        Raises:
            CDOValidationError: If p is not between 0 and 100
        """
        if not 0 <= p <= 100:
            raise CDOValidationError(
                message="Invalid percentile value",
                parameter="p",
                value=p,
                expected="Percentile between 0 and 100",
            )
        return self._add_operator(OperatorSpec("yearpctl", args=(p,)))

    def month_percentile(self, p: float) -> CDOQuery:
        """
        Calculate monthly percentile.

        Args:
            p: Percentile value (0-100)

        Raises:
            CDOValidationError: If p is not between 0 and 100
        """
        if not 0 <= p <= 100:
            raise CDOValidationError(
                message="Invalid percentile value",
                parameter="p",
                value=p,
                expected="Percentile between 0 and 100",
            )
        return self._add_operator(OperatorSpec("monpctl", args=(p,)))

    # ========== Arithmetic Operators (Constant) ==========

    @classmethod
    def _create_unbound(cls, input_file: Path) -> CDOQuery:
        """
        Create an unbound query for F() expressions.

        Unbound queries don't have a CDO instance attached and are used
        as operands in binary operations.
        """
        query = cls.__new__(cls)
        object.__setattr__(query, "_input", input_file)
        object.__setattr__(query, "_options", ())
        object.__setattr__(query, "_operators", ())
        object.__setattr__(query, "_cdo", None)
        object.__setattr__(query, "_temp_files", ())
        return query

    def add_constant(self, value: float) -> CDOQuery:
        """
        Add constant to all values.

        Args:
            value: Constant to add

        Returns:
            New query with addc operator

        Example:
            >>> q = cdo.query("temp_C.nc").add_constant(273.15)  # Convert to Kelvin
        """
        return self._add_operator(OperatorSpec("addc", args=(value,)))

    def multiply_constant(self, value: float) -> CDOQuery:
        """
        Multiply all values by constant.

        Args:
            value: Constant multiplier

        Returns:
            New query with mulc operator

        Example:
            >>> q = cdo.query("precip.nc").multiply_constant(86400)  # kg/m²/s to mm/day
        """
        return self._add_operator(OperatorSpec("mulc", args=(value,)))

    def subtract_constant(self, value: float) -> CDOQuery:
        """
        Subtract constant from all values.

        Args:
            value: Constant to subtract

        Returns:
            New query with subc operator

        Example:
            >>> q = cdo.query("temp_K.nc").subtract_constant(273.15)  # Convert Kelvin to Celsius
        """
        return self._add_operator(OperatorSpec("subc", args=(value,)))

    def divide_constant(self, value: float) -> CDOQuery:
        """
        Divide all values by constant.

        Args:
            value: Constant divisor

        Returns:
            New query with divc operator

        Raises:
            CDOValidationError: If value is zero

        Example:
            >>> q = cdo.query("precip.nc").divide_constant(100)  # Convert cm to m
        """
        if value == 0:
            raise CDOValidationError(
                message="Cannot divide by zero",
                parameter="value",
                value=value,
                expected="Non-zero divisor",
            )
        return self._add_operator(OperatorSpec("divc", args=(value,)))

    # Shorter aliases for constant arithmetic (match README docs)
    def sub_constant(self, value: float) -> CDOQuery:
        """Alias for subtract_constant(). Subtract constant from all values."""
        return self.subtract_constant(value)

    def mul_constant(self, value: float) -> CDOQuery:
        """Alias for multiply_constant(). Multiply all values by constant."""
        return self.multiply_constant(value)

    def div_constant(self, value: float) -> CDOQuery:
        """Alias for divide_constant(). Divide all values by constant."""
        return self.divide_constant(value)

    # ========== Binary Arithmetic Operators ==========

    def sub(self, other: CDOQuery | str | Path) -> BinaryOpQuery:
        """
        Subtract another dataset from this query.

        Args:
            other: Another CDOQuery (via F()), file path, or string path

        Returns:
            BinaryOpQuery representing the subtraction

        Example:
            >>> # Calculate anomaly (one-liner!)
            >>> anomaly = cdo.query("data.nc").sub(F("climatology.nc")).compute()

            >>> # Process both sides before subtraction
            >>> diff = (
            ...     cdo.query("data1.nc").select_var("tas").year_mean()
            ...     .sub(F("data2.nc").select_var("tas").year_mean())
            ... )
        """
        return self._binary_op("sub", other)

    def add(self, other: CDOQuery | str | Path) -> BinaryOpQuery:
        """Add another dataset to this query."""
        return self._binary_op("add", other)

    def mul(self, other: CDOQuery | str | Path) -> BinaryOpQuery:
        """Multiply this query by another dataset."""
        return self._binary_op("mul", other)

    def div(self, other: CDOQuery | str | Path) -> BinaryOpQuery:
        """Divide this query by another dataset."""
        return self._binary_op("div", other)

    def min(self, other: CDOQuery | str | Path) -> BinaryOpQuery:
        """
        Element-wise minimum with another dataset.

        Args:
            other: Query or file to compare with

        Returns:
            BinaryOpQuery for minimum operation

        Example:
            >>> # Cap values at upper bound
            >>> q = cdo.query("data.nc").min("upper_bound.nc")
        """
        return self._binary_op("min", other)

    def max(self, other: CDOQuery | str | Path) -> BinaryOpQuery:
        """
        Element-wise maximum with another dataset.

        Args:
            other: Query or file to compare with

        Returns:
            BinaryOpQuery for maximum operation

        Example:
            >>> # Enforce lower bound
            >>> q = cdo.query("data.nc").max("lower_bound.nc")
        """
        return self._binary_op("max", other)

    def _binary_op(self, op: str, other: CDOQuery | str | Path) -> BinaryOpQuery:
        """Internal helper for binary operations."""
        # Convert string/Path to CDOQuery if needed
        if isinstance(other, (str, Path)):
            other = CDOQuery._create_unbound(Path(other))

        # Inherit CDO instance
        other_cdo = other._cdo or self._cdo

        return BinaryOpQuery(
            operator=op,
            left=self,
            right=other,
            cdo_instance=self._cdo or other_cdo,
        )

    # ========== Math Functions ==========

    def abs(self) -> CDOQuery:
        """
        Absolute value of all data values.

        Returns:
            New query with abs operator

        Example:
            >>> q = cdo.query("anomalies.nc").abs()
        """
        return self._add_operator(OperatorSpec("abs"))

    def sqrt(self) -> CDOQuery:
        """
        Square root of all data values.

        Returns:
            New query with sqrt operator

        Example:
            >>> q = cdo.query("variance.nc").sqrt()  # Get standard deviation
        """
        return self._add_operator(OperatorSpec("sqrt"))

    def sqr(self) -> CDOQuery:
        """
        Square of all data values.

        Returns:
            New query with sqr operator

        Example:
            >>> q = cdo.query("data.nc").sqr()
        """
        return self._add_operator(OperatorSpec("sqr"))

    def exp(self) -> CDOQuery:
        """
        Exponential (e^x) of all data values.

        Returns:
            New query with exp operator

        Example:
            >>> q = cdo.query("log_data.nc").exp()
        """
        return self._add_operator(OperatorSpec("exp"))

    def ln(self) -> CDOQuery:
        """
        Natural logarithm of all data values.

        Returns:
            New query with ln operator

        Example:
            >>> q = cdo.query("data.nc").ln()
        """
        return self._add_operator(OperatorSpec("ln"))

    def log10(self) -> CDOQuery:
        """
        Base-10 logarithm of all data values.

        Returns:
            New query with log10 operator

        Example:
            >>> q = cdo.query("data.nc").log10()
        """
        return self._add_operator(OperatorSpec("log10"))

    # ========== Trigonometric Functions ==========

    def sin(self) -> CDOQuery:
        """
        Sine of all data values (in radians).

        Returns:
            New query with sin operator

        Example:
            >>> q = cdo.query("angles.nc").sin()
        """
        return self._add_operator(OperatorSpec("sin"))

    def cos(self) -> CDOQuery:
        """
        Cosine of all data values (in radians).

        Returns:
            New query with cos operator

        Example:
            >>> q = cdo.query("angles.nc").cos()
        """
        return self._add_operator(OperatorSpec("cos"))

    def tan(self) -> CDOQuery:
        """
        Tangent of all data values (in radians).

        Returns:
            New query with tan operator

        Example:
            >>> q = cdo.query("angles.nc").tan()
        """
        return self._add_operator(OperatorSpec("tan"))

    # ========== Masking & Conditional Operations ==========

    def ifthen(self, mask: CDOQuery | str | Path) -> CDOQuery:
        """
        Apply mask: set values to missing where mask is 0.

        Args:
            mask: Mask file or query (values where mask=0 become missing)

        Returns:
            BinaryOpQuery for ifthen operation

        Example:
            >>> # Keep only land values
            >>> q = cdo.query("data.nc").ifthen(F("land_mask.nc"))
        """
        return BinaryOpQuery(
            operator="ifthen",
            left=mask if isinstance(mask, CDOQuery) else F(mask),
            right=self,
            cdo_instance=self._cdo,
        )

    def mask(self, mask: CDOQuery | str | Path) -> CDOQuery:
        """
        Alias for ifthen() - apply mask to data.

        Args:
            mask: Mask file or query

        Returns:
            BinaryOpQuery for ifthen operation

        Example:
            >>> q = cdo.query("data.nc").mask("ocean_mask.nc")
        """
        return self.ifthen(mask)

    def ifthenelse(
        self, condition: CDOQuery | str | Path, else_val: CDOQuery | str | Path
    ) -> CDOQuery:
        """
        Conditional selection: if condition then self else else_val.

        Note: This creates a nested binary operation.

        Args:
            condition: Condition file or query
            else_val: Alternative values file or query

        Returns:
            BinaryOpQuery for ifthenelse operation

        Example:
            >>> # If condition: use data.nc, else use fallback.nc
            >>> q = cdo.query("data.nc").ifthenelse(F("condition.nc"), F("fallback.nc"))
        """
        # CDO syntax: -ifthenelse condition then else
        # We need to create a special structure for this
        cond = condition if isinstance(condition, CDOQuery) else F(condition)
        else_query = else_val if isinstance(else_val, CDOQuery) else F(else_val)

        # Create intermediate query that represents ifthenelse
        # CDO expects: -ifthenelse cond then else
        return BinaryOpQuery(
            operator="ifthenelse",
            left=cond,
            right=BinaryOpQuery(
                operator="_ifthenelse_args",  # Internal marker
                left=self,
                right=else_query,
                cdo_instance=self._cdo,
            ),
            cdo_instance=self._cdo,
        )

    def where(
        self, condition: CDOQuery | str | Path, else_val: CDOQuery | str | Path
    ) -> CDOQuery:
        """
        Alias for ifthenelse() - conditional selection.

        Args:
            condition: Condition file or query
            else_val: Alternative values file or query

        Returns:
            BinaryOpQuery for conditional selection

        Example:
            >>> q = cdo.query("data.nc").where("condition.nc", "default.nc")
        """
        return self.ifthenelse(condition, else_val)

    # ========== Missing Value Handling ==========

    def set_missval(self, value: float) -> CDOQuery:
        """
        Set the missing value indicator.

        Args:
            value: Missing value indicator to set

        Returns:
            New query with setmissval operator

        Example:
            >>> q = cdo.query("data.nc").set_missval(-999.0)
        """
        return self._add_operator(OperatorSpec("setmissval", args=(value,)))

    def set_const_to_miss(self, value: float) -> CDOQuery:
        """
        Set constant value to missing value.

        Args:
            value: Constant value to replace with missing value

        Returns:
            New query with setctomiss operator

        Example:
            >>> q = cdo.query("data.nc").set_const_to_miss(0.0)
        """
        return self._add_operator(OperatorSpec("setctomiss", args=(value,)))

    def set_miss_to_const(self, value: float) -> CDOQuery:
        """
        Set missing value to constant value.

        Args:
            value: Constant value to replace missing value with

        Returns:
            New query with setmisstoc operator

        Example:
            >>> q = cdo.query("data.nc").set_miss_to_const(0.0)
        """
        return self._add_operator(OperatorSpec("setmisstoc", args=(value,)))

    def setmisstoc(self, value: float) -> CDOQuery:
        """
        Replace missing values with a constant.

        Args:
            value: Constant to replace missing values with

        Returns:
            New query with setmisstoc operator

        Example:
            >>> q = cdo.query("data.nc").setmisstoc(0.0)  # Replace missing with 0
        """
        return self._add_operator(OperatorSpec("setmisstoc", args=(value,)))

    def miss_to_const(self, value: float) -> CDOQuery:
        """
        Alias for setmisstoc() - replace missing values with constant.

        Args:
            value: Constant to replace missing values with

        Returns:
            New query with setmisstoc operator

        Example:
            >>> q = cdo.query("data.nc").miss_to_const(0.0)
        """
        return self.setmisstoc(value)

    # ========== Modification Operators ==========

    def set_name(self, new_name: str) -> CDOQuery:
        """
        Set variable name.

        Args:
            new_name: New name for the variable

        Returns:
            New query with setname operator

        Example:
            >>> q = cdo.query("tas.nc").set_name("temperature")
        """
        return self._add_operator(OperatorSpec("setname", args=(new_name,)))

    def set_code(self, code: int) -> CDOQuery:
        """
        Set variable code.

        Args:
            code: New code for the variable

        Returns:
            New query with setcode operator

        Example:
            >>> q = cdo.query("data.nc").set_code(167)  # Temperature
        """
        return self._add_operator(OperatorSpec("setcode", args=(code,)))

    def set_unit(self, unit: str) -> CDOQuery:
        """
        Set variable unit.

        Args:
            unit: New unit string (e.g., "K", "degC", "mm/day")

        Returns:
            New query with setunit operator

        Example:
            >>> q = cdo.query("precip.nc").set_unit("mm/day")
        """
        return self._add_operator(OperatorSpec("setunit", args=(unit,)))

    def set_grid(self, grid: str | Path) -> CDOQuery:
        """
        Set grid description.

        Args:
            grid: Grid description file or name

        Returns:
            New query with setgrid operator

        Example:
            >>> q = cdo.query("data.nc").set_grid("r360x180")
        """
        return self._add_operator(OperatorSpec("setgrid", args=(str(grid),)))

    def set_grid_type(self, gtype: str) -> CDOQuery:
        """
        Set grid type.

        Args:
            gtype: Grid type (e.g., "lonlat", "gaussian", "curvilinear")

        Returns:
            New query with setgridtype operator

        Example:
            >>> q = cdo.query("data.nc").set_grid_type("lonlat")
        """
        return self._add_operator(OperatorSpec("setgridtype", args=(gtype,)))

    def invert_lat(self) -> CDOQuery:
        """
        Invert latitude coordinate.

        Returns:
            New query with invertlat operator

        Example:
            >>> q = cdo.query("data.nc").invert_lat()
        """
        return self._add_operator(OperatorSpec("invertlat"))

    def set_range_to_miss(self, min_val: float, max_val: float) -> CDOQuery:
        """
        Set values in range to missing.

        Args:
            min_val: Minimum value of range
            max_val: Maximum value of range

        Returns:
            New query with setrtomiss operator

        Example:
            >>> # Remove values between -1e30 and -1e20 (bad values)
            >>> q = cdo.query("data.nc").set_range_to_miss(-1e30, -1e20)
        """
        return self._add_operator(OperatorSpec("setrtomiss", args=(min_val, max_val)))

    def set_level(self, *levels: float) -> CDOQuery:
        """
        Set level values for the vertical coordinate.

        Args:
            *levels: New level values

        Returns:
            New query with setlevel operator

        Example:
            >>> q = cdo.query("data.nc").set_level(1000, 850, 500)
        """
        if not levels:
            raise CDOValidationError(
                message="No levels provided",
                parameter="levels",
                value=levels,
                expected="At least one level",
            )
        return self._add_operator(OperatorSpec("setlevel", args=levels))

    def set_level_type(self, ltype: int) -> CDOQuery:
        """
        Set level type code.

        Args:
            ltype: Level type code (e.g., 100 for pressure levels in GRIB)

        Returns:
            New query with setltype operator

        Example:
            >>> q = cdo.query("data.nc").set_level_type(100)  # Pressure levels
        """
        return self._add_operator(OperatorSpec("setltype", args=(ltype,)))

    def set_calendar(self, calendar: str) -> CDOQuery:
        """
        Set calendar type.

        Args:
            calendar: Calendar type (e.g., "standard", "proleptic_gregorian",
                     "360_day", "365_day", "noleap")

        Returns:
            New query with setcalendar operator

        Example:
            >>> q = cdo.query("data.nc").set_calendar("standard")
        """
        return self._add_operator(OperatorSpec("setcalendar", args=(calendar,)))

    def set_time_axis(self, date: str, time: str, inc: str | None = None) -> CDOQuery:
        """
        Set the time axis.

        Args:
            date: Start date (e.g., "2000-01-01")
            time: Start time (e.g., "12:00:00")
            inc: Optional time increment (e.g., "1day", "6hour")

        Returns:
            New query with settaxis operator

        Example:
            >>> q = cdo.query("data.nc").set_time_axis("2000-01-01", "00:00:00", "1day")
        """
        args = [date, time]
        if inc:
            args.append(inc)
        return self._add_operator(OperatorSpec("settaxis", args=tuple(args)))

    def set_ref_time(self, date: str, time: str) -> CDOQuery:
        """
        Set the reference time.

        Args:
            date: Reference date (e.g., "2000-01-01")
            time: Reference time (e.g., "00:00:00")

        Returns:
            New query with setreftime operator

        Example:
            >>> q = cdo.query("data.nc").set_ref_time("1950-01-01", "00:00:00")
        """
        return self._add_operator(OperatorSpec("setreftime", args=(date, time)))

    def shift_time(self, shift_value: str) -> CDOQuery:
        """
        Shift time steps.

        Args:
            shift_value: Time shift string (e.g., "1hour", "-1day")

        Returns:
            New query with shifttime operator

        Example:
            >>> q = cdo.query("data.nc").shift_time("-6hour")
        """
        return self._add_operator(OperatorSpec("shifttime", args=(shift_value,)))

    def set_attribute(self, var_name: str, attr_name: str, value: str) -> CDOQuery:
        """
        Set a variable attribute.

        Args:
            var_name: Variable name (use "global" for global attributes)
            attr_name: Attribute name
            value: Attribute value

        Returns:
            New query with setattribute operator

        Example:
            >>> q = cdo.query("data.nc").set_attribute("tas", "long_name", "Temperature")
        """
        attr_spec = f'{var_name}@{attr_name}="{value}"'
        return self._add_operator(OperatorSpec("setattribute", args=(attr_spec,)))

    def del_attribute(self, var_name: str, attr_name: str) -> CDOQuery:
        """
        Delete a variable attribute.

        Args:
            var_name: Variable name (use "global" for global attributes)
            attr_name: Attribute name

        Returns:
            New query with delattribute operator

        Example:
            >>> q = cdo.query("data.nc").del_attribute("tas", "units")
        """
        attr_spec = f"{var_name}@{attr_name}"
        return self._add_operator(OperatorSpec("delattribute", args=(attr_spec,)))

    # ========== Interpolation/Regridding Operators ==========

    def _resolve_grid(self, grid: str | Path | GridSpec) -> str:
        """
        Resolve grid argument to a string (path or name).

        If a GridSpec is provided, it is written to a temporary file.
        """
        if isinstance(grid, (str, Path)):
            return str(grid)

        # It's a GridSpec
        # Use CDO temp dir if available
        dir_path = self._cdo.temp_dir if self._cdo and self._cdo.temp_dir else None

        # Create a named temporary file
        # We use delete=False so it persists for CDO to read it
        with tempfile.NamedTemporaryFile(
            mode="w", dir=dir_path, delete=False, prefix="cdo_grid_", suffix=".txt"
        ) as f:
            f.write(grid.to_cdo_string())
            return f.name

    def remap_bil(self, grid: str | Path | GridSpec) -> CDOQuery:
        """
        Bilinear interpolation to target grid.

        Args:
            grid: Target grid (name, path, or GridSpec)

        Returns:
            New query with remapbil operator

        Example:
            >>> q = cdo.query("high_res.nc").remap_bil("r360x180")
        """
        grid_arg = self._resolve_grid(grid)
        return self._add_operator(OperatorSpec("remapbil", args=(grid_arg,)))

    def remap_bic(self, grid: str | Path | GridSpec) -> CDOQuery:
        """
        Bicubic interpolation to target grid.

        Args:
            grid: Target grid (name, path, or GridSpec)

        Returns:
            New query with remapbic operator

        Example:
            >>> q = cdo.query("data.nc").remap_bic("target_grid.nc")
        """
        grid_arg = self._resolve_grid(grid)
        return self._add_operator(OperatorSpec("remapbic", args=(grid_arg,)))

    def remap_nn(self, grid: str | Path | GridSpec) -> CDOQuery:
        """
        Nearest neighbor remapping to target grid.

        Args:
            grid: Target grid (name, path, or GridSpec)

        Returns:
            New query with remapnn operator

        Example:
            >>> q = cdo.query("data.nc").remap_nn("r180x90")
        """
        grid_arg = self._resolve_grid(grid)
        return self._add_operator(OperatorSpec("remapnn", args=(grid_arg,)))

    def remap_dis(self, grid: str | Path | GridSpec) -> CDOQuery:
        """
        Distance-weighted average remapping to target grid.

        Args:
            grid: Target grid (name, path, or GridSpec)

        Returns:
            New query with remapdis operator

        Example:
            >>> q = cdo.query("data.nc").remap_dis("r360x180")
        """
        grid_arg = self._resolve_grid(grid)
        return self._add_operator(OperatorSpec("remapdis", args=(grid_arg,)))

    def remap_con(self, grid: str | Path | GridSpec) -> CDOQuery:
        """
        First-order conservative remapping to target grid.

        Args:
            grid: Target grid (name, path, or GridSpec)

        Returns:
            New query with remapcon operator

        Example:
            >>> q = cdo.query("data.nc").remap_con("r180x90")
        """
        grid_arg = self._resolve_grid(grid)
        return self._add_operator(OperatorSpec("remapcon", args=(grid_arg,)))

    def remap_con2(self, grid: str | Path | GridSpec) -> CDOQuery:
        """
        Second-order conservative remapping to target grid.

        Args:
            grid: Target grid (name, path, or GridSpec)

        Returns:
            New query with remapcon2 operator

        Example:
            >>> q = cdo.query("data.nc").remap_con2("r360x180")
        """
        grid_arg = self._resolve_grid(grid)
        return self._add_operator(OperatorSpec("remapcon2", args=(grid_arg,)))

    def remap_laf(self, grid: str | Path | GridSpec) -> CDOQuery:
        """
        Largest area fraction remapping (for categorical data).

        Args:
            grid: Target grid (name, path, or GridSpec)

        Returns:
            New query with remaplaf operator

        Example:
            >>> q = cdo.query("land_cover.nc").remap_laf("r180x90")
        """
        grid_arg = self._resolve_grid(grid)
        return self._add_operator(OperatorSpec("remaplaf", args=(grid_arg,)))

    # Vertical interpolation

    def interp_level(self, *levels: float) -> CDOQuery:
        """
        Linear interpolation to specific vertical levels.

        Args:
            *levels: Target levels

        Returns:
            New query with intlevel operator
        """
        if not levels:
            raise CDOValidationError(
                message="No levels provided",
                parameter="levels",
                value=levels,
                expected="At least one level",
            )
        return self._add_operator(OperatorSpec("intlevel", args=levels))

    def interp_level3d(self, target_grid: str | Path) -> CDOQuery:
        """
        Interpolate to 3D vertical levels from another file.

        Args:
            target_grid: File containing target vertical levels

        Returns:
            New query with intlevel3d operator
        """
        return self._add_operator(OperatorSpec("intlevel3d", args=(str(target_grid),)))

    def ml_to_pl(self, *pressure_levels: float) -> CDOQuery:
        """
        Interpolate from model levels to pressure levels.

        Args:
            *pressure_levels: Target pressure levels

        Returns:
            New query with ml2pl operator
        """
        if not pressure_levels:
            raise CDOValidationError(
                message="No pressure levels provided",
                parameter="pressure_levels",
                value=pressure_levels,
                expected="At least one pressure level",
            )
        return self._add_operator(OperatorSpec("ml2pl", args=pressure_levels))

    # ========== Django-like Query Shortcuts ==========

    def first(self) -> xr.Dataset:
        """
        Get first timestep only and execute.

        Similar to Django's QuerySet.first().

        Returns:
            xarray.Dataset with first timestep

        Example:
            >>> ds = cdo.query("data.nc").select_var("tas").first()
        """
        return (
            self.clone()._add_operator(OperatorSpec("seltimestep", args=(1,))).compute()
        )

    def last(self) -> xr.Dataset:
        """
        Get last timestep only and execute.

        Similar to Django's QuerySet.last().

        Returns:
            xarray.Dataset with last timestep

        Example:
            >>> ds = cdo.query("data.nc").select_var("tas").last()
        """
        # CDO doesn't have a direct "last" operator, use -1 index
        return (
            self.clone()
            ._add_operator(OperatorSpec("seltimestep", args=(-1,)))
            .compute()
        )

    def exists(self) -> bool:
        """
        Check if the query would return any data.

        Similar to Django's QuerySet.exists(). Executes immediately.

        Returns:
            True if query would return data, False otherwise

        Example:
            >>> if cdo.query("data.nc").select_var("tas").exists():
            ...     print("Variable exists!")
        """
        if self._cdo is None:
            raise CDOError("Query not bound to a CDO instance")
        try:
            if self._input is None:
                raise CDOError("Query has no input file (is it a template?)")
            # Check number of timesteps
            nsteps = self._cdo.ntime(self._input)
            return nsteps > 0
        except CDOError:
            return False

    def values(self, *var_names: str) -> CDOQuery:
        """
        Select specific variables (alias for select_var).

        Similar to Django's QuerySet.values(). Does NOT execute.

        Args:
            *var_names: Variable names to select

        Returns:
            New query with variable selection

        Example:
            >>> q = cdo.query("data.nc").values("tas", "pr")
        """
        return self.select_var(*var_names)

    def output_format(self, fmt: str) -> CDOQuery:
        """
        Set the output format (e.g., 'grb', 'nc', 'nc2', 'nc4', 'nc4c', 'nc5').
        Adds '-f format' to the beginning of the command.

        Args:
            fmt: Format string (e.g., 'nc4')

        Returns:
            New query with output format set
        """
        return self._clone(options=(*self._options, f"-f {fmt}"))

    # ========== Terminal Methods ==========

    def get_command(self) -> str:
        """
        Build the CDO command string (for inspection/debugging).

        Returns:
            Complete CDO command string

        Example:
            >>> q = cdo.query("data.nc").select_var("tas").year_mean()
            >>> q.get_command()
            'cdo -yearmean -selname,tas data.nc'
        """
        parts = ["cdo"]
        if self._options:
            parts.extend(self._options)

        if self._operators:
            # Operators in CDO are applied right-to-left in command,
            # but we build left-to-right in chain
            parts.extend(op.to_cdo_fragment() for op in reversed(self._operators))

        parts.append(str(self._input) if self._input else "<input>")
        return " ".join(parts)

    def compute(self, output: str | Path | None = None) -> xr.Dataset:
        """
        Execute the query and return xarray Dataset.

        Args:
            output: Optional output file path. If not provided, uses temp file.

        Returns:
            xarray.Dataset with results

        Raises:
            CDOError: If query not bound to CDO instance or input file

        Example:
            >>> ds = cdo.query("data.nc").year_mean().compute()
            >>> # Save to file
            >>> ds = cdo.query("data.nc").year_mean().compute(output="result.nc")
        """
        if self._cdo is None:
            raise CDOError("Query not bound to a CDO instance")
        if self._input is None:
            raise CDOError("Query has no input file (is it a template?)")
        return self._cdo._execute_query(self, output)

    def execute(self, output: str | Path | None = None) -> xr.Dataset:
        """Alias for compute() for Django-style familiarity."""
        return self.compute(output=output)

    def to_file(self, output: str | Path) -> Path:
        """
        Execute and write to file, return the output path.

        Args:
            output: Output file path

        Returns:
            Path object for output file

        Example:
            >>> path = cdo.query("data.nc").year_mean().to_file("result.nc")
        """
        self.compute(output=output)
        return Path(output)

    def clone(self) -> CDOQuery:
        """
        Create an independent copy for branching pipelines.

        Returns:
            New CDOQuery with same state

        Example:
            >>> base = cdo.query("data.nc").select_var("tas")
            >>> yearly = base.clone().year_mean().compute()
            >>> monthly = base.clone().month_mean().compute()
        """
        return self._clone()

    def explain(self) -> str:
        """
        Return human-readable explanation of query pipeline.

        Returns:
            Multi-line string describing the pipeline

        Example:
            >>> q = cdo.query("data.nc").select_var("tas").year_mean()
            >>> print(q.explain())
            Input: data.nc
              1. selname(tas)
              2. yearmean()
        """
        lines = [f"Input: {self._input}"]
        for i, op in enumerate(self._operators, 1):
            if op.args:
                args_str = ", ".join(str(arg) for arg in op.args)
                lines.append(f"  {i}. {op.name}({args_str})")
            else:
                lines.append(f"  {i}. {op.name}()")
        return "\n".join(lines)

    def count(self) -> int:
        """
        Get number of timesteps.

        Similar to Django's QuerySet.count(). Executes immediately.

        Returns:
            Number of timesteps

        Example:
            >>> n = cdo.query("data.nc").count()
        """
        if self._cdo is None:
            raise CDOError("Query not bound to a CDO instance")

        from .core import execute_cdo

        # We need to construct the command up to this point
        # But ntime takes a file, not a stream usually, unless piped
        # If we have operators, we might need to pipe

        if not self._operators:
            cmd = f"ntime {self._input}"
            result = execute_cdo(
                cmd, cdo_path=self._cdo.cdo_path, debug=self._cdo.debug
            )
            return int(result.strip()) if result.strip() else 0
        else:
            # If we have operators, we need to run the query and pipe to ntime
            # Or use the output file if we computed it.
            # But count() shouldn't necessarily compute the whole dataset if possible.
            # However, CDO pipes are efficient.

            # Construct command: cdo -ntime [operators] input
            # Note: ntime is an operator itself.

            # We can clone and add ntime operator, but ntime returns text, not dataset.
            # So we can't use compute().

            # Let's build the command manually
            ops = " ".join(op.to_cdo_fragment() for op in reversed(self._operators))
            full_cmd = f"-ntime {ops} {self._input}"

            result = execute_cdo(
                full_cmd, cdo_path=self._cdo.cdo_path, debug=self._cdo.debug
            )
            return int(result.strip()) if result.strip() else 0

    # ========== Information Operators (Terminating) ==========

    def _execute_info_with_pipeline(self, info_method_name: str) -> Any:
        """
        Execute query pipeline and run info operator on result.

        Helper method for info operators when pipeline has operators.

        Args:
            info_method_name: Name of CDO method to call (e.g., 'showname', 'griddes')

        Returns:
            Result from the info method
        """
        import os
        import tempfile

        if self._cdo is None:
            raise CDOError("Query not bound to a CDO instance")
        if self._input is None:
            raise CDOError("Query has no input file (is it a template?)")

        # Create temp file for pipeline output
        fd, temp_path = tempfile.mkstemp(suffix=".nc", dir=self._cdo.temp_dir)
        os.close(fd)

        try:
            # Execute pipeline to temp file
            self.compute(output=temp_path)

            # Run info command on temp file
            info_method = getattr(self._cdo, info_method_name)
            result = info_method(temp_path)

            return result
        finally:
            # Clean up temp file
            temp_file = Path(temp_path)
            if temp_file.exists():
                temp_file.unlink()

    def showname(self) -> list[str]:
        """
        Get list of variable names (executes immediately).

        This is a terminating method that runs the query pipeline (if any)
        and returns the variable names from the result.

        Returns:
            List of variable names

        Example:
            >>> # Without operators
            >>> vars = cdo.query("data.nc").showname()
            >>> print(vars)
            ['tas', 'pr', 'psl']

            >>> # With operators
            >>> vars = cdo.query("data.nc").select_var("tas", "pr").showname()
            >>> print(vars)
            ['tas', 'pr']

        See Also:
            - showcode: Get variable codes
            - showunit: Get variable units
        """
        if self._cdo is None:
            raise CDOError("Query not bound to a CDO instance")
        if self._input is None:
            raise CDOError("Query has no input file (is it a template?)")

        if not self._operators:
            # No operators - just run showname on input file
            return self._cdo.showname(self._input)
        else:
            # Has operators - execute pipeline first
            return cast("list[str]", self._execute_info_with_pipeline("showname"))

    def showcode(self) -> list[int]:
        """
        Get list of variable codes (executes immediately).

        Returns:
            List of variable codes

        Example:
            >>> codes = cdo.query("data.nc").showcode()
            >>> print(codes)
            [11, 228, 134]
        """
        if self._cdo is None:
            raise CDOError("Query not bound to a CDO instance")
        if self._input is None:
            raise CDOError("Query has no input file (is it a template?)")

        if not self._operators:
            return self._cdo.showcode(self._input)
        else:
            return cast("list[int]", self._execute_info_with_pipeline("showcode"))

    def showunit(self) -> list[str]:
        """
        Get list of variable units (executes immediately).

        Returns:
            List of variable units

        Example:
            >>> units = cdo.query("data.nc").showunit()
            >>> print(units)
            ['K', 'kg m-2 s-1', 'Pa']
        """
        if self._cdo is None:
            raise CDOError("Query not bound to a CDO instance")
        if self._input is None:
            raise CDOError("Query has no input file (is it a template?)")

        if not self._operators:
            return self._cdo.showunit(self._input)
        else:
            return cast("list[str]", self._execute_info_with_pipeline("showunit"))

    def showlevel(self) -> list[float]:
        """
        Get list of vertical levels (executes immediately).

        Returns:
            List of vertical levels

        Example:
            >>> levels = cdo.query("data.nc").showlevel()
            >>> print(levels)
            [1000.0, 850.0, 500.0, 200.0]
        """
        if self._cdo is None:
            raise CDOError("Query not bound to a CDO instance")
        if self._input is None:
            raise CDOError("Query has no input file (is it a template?)")

        if not self._operators:
            return self._cdo.showlevel(self._input)
        else:
            return cast("list[float]", self._execute_info_with_pipeline("showlevel"))

    def showdate(self) -> list[str]:
        """
        Get list of dates (executes immediately).

        Returns:
            List of dates in YYYY-MM-DD format

        Example:
            >>> dates = cdo.query("data.nc").showdate()
            >>> print(dates)
            ['2020-01-01', '2020-02-01', '2020-03-01']
        """
        if self._cdo is None:
            raise CDOError("Query not bound to a CDO instance")
        if self._input is None:
            raise CDOError("Query has no input file (is it a template?)")

        if not self._operators:
            return self._cdo.showdate(self._input)
        else:
            return cast("list[str]", self._execute_info_with_pipeline("showdate"))

    def showtime(self) -> list[str]:
        """
        Get list of times (executes immediately).

        Returns:
            List of times in HH:MM:SS format

        Example:
            >>> times = cdo.query("data.nc").showtime()
            >>> print(times)
            ['00:00:00', '06:00:00', '12:00:00', '18:00:00']
        """
        if self._cdo is None:
            raise CDOError("Query not bound to a CDO instance")
        if self._input is None:
            raise CDOError("Query has no input file (is it a template?)")

        if not self._operators:
            return self._cdo.showtime(self._input)
        else:
            return cast("list[str]", self._execute_info_with_pipeline("showtime"))

    def ntime(self) -> int:
        """
        Get number of timesteps (executes immediately).

        Alias for count() method. Returns the number of timesteps
        in the dataset after applying any operators in the pipeline.

        Returns:
            Number of timesteps

        Example:
            >>> n = cdo.query("data.nc").ntime()
            >>> print(n)
            120

            >>> # With selection
            >>> n = cdo.query("data.nc").select_year(2020).ntime()
            >>> print(n)
            12

        See Also:
            - count: Equivalent method following Django QuerySet pattern
        """
        return self.count()

    def nvar(self) -> int:
        """
        Get number of variables (executes immediately).

        Returns:
            Number of variables

        Example:
            >>> n = cdo.query("data.nc").nvar()
            >>> print(n)
            3

            >>> # After selecting variables
            >>> n = cdo.query("data.nc").select_var("tas").nvar()
            >>> print(n)
            1
        """
        if self._cdo is None:
            raise CDOError("Query not bound to a CDO instance")
        if self._input is None:
            raise CDOError("Query has no input file (is it a template?)")

        if not self._operators:
            return self._cdo.nvar(self._input)
        else:
            return cast("int", self._execute_info_with_pipeline("nvar"))

    def nlevel(self) -> int:
        """
        Get number of vertical levels (executes immediately).

        Returns:
            Number of vertical levels

        Example:
            >>> n = cdo.query("data.nc").nlevel()
            >>> print(n)
            4

            >>> # After selecting levels
            >>> n = cdo.query("data.nc").select_level(1000, 850).nlevel()
            >>> print(n)
            2
        """
        if self._cdo is None:
            raise CDOError("Query not bound to a CDO instance")
        if self._input is None:
            raise CDOError("Query has no input file (is it a template?)")

        if not self._operators:
            return self._cdo.nlevel(self._input)
        else:
            return cast("int", self._execute_info_with_pipeline("nlevel"))

    def sinfo(self) -> SinfoResult:
        """
        Get comprehensive dataset summary information (executes immediately).

        Returns structured information about file format, variables,
        grid coordinates, vertical coordinates, and time information.

        Returns:
            SinfoResult with structured dataset information

        Example:
            >>> info = cdo.query("data.nc").sinfo()
            >>> print(info.var_names)
            ['tas', 'pr', 'psl']
            >>> print(info.nvar)
            3
            >>> print(info.time_range)
            ('2020-01-01', '2022-12-31')

            >>> # After processing
            >>> info = cdo.query("data.nc").year_mean().sinfo()

        See Also:
            - info: Timestep-by-timestep statistics
            - vlist: Variable list with metadata
        """
        if self._cdo is None:
            raise CDOError("Query not bound to a CDO instance")
        if self._input is None:
            raise CDOError("Query has no input file (is it a template?)")

        if not self._operators:
            return self._cdo.sinfo(self._input)
        else:
            return cast("SinfoResult", self._execute_info_with_pipeline("sinfo"))

    def info(self) -> InfoResult:
        """
        Get timestep-by-timestep statistics (executes immediately).

        Returns:
            InfoResult with timestep statistics

        Example:
            >>> info = cdo.query("data.nc").info()
            >>> print(len(info.timesteps))
            120

        See Also:
            - sinfo: Comprehensive dataset summary
        """
        if self._cdo is None:
            raise CDOError("Query not bound to a CDO instance")
        if self._input is None:
            raise CDOError("Query has no input file (is it a template?)")

        if not self._operators:
            return self._cdo.info(self._input)
        else:
            return cast("InfoResult", self._execute_info_with_pipeline("info"))

    def griddes(self) -> GriddesResult:
        """
        Get grid description (executes immediately).

        Returns:
            GriddesResult with grid information

        Example:
            >>> grid = cdo.query("data.nc").griddes()
            >>> print(grid.grids[0].gridtype)
            'lonlat'
            >>> print(grid.grids[0].xsize, grid.grids[0].ysize)
            360 180

            >>> # After remapping
            >>> grid = cdo.query("data.nc").remap_bil("r180x90").griddes()

        See Also:
            - zaxisdes: Vertical axis description
        """
        if self._cdo is None:
            raise CDOError("Query not bound to a CDO instance")
        if self._input is None:
            raise CDOError("Query has no input file (is it a template?)")

        if not self._operators:
            return self._cdo.griddes(self._input)
        else:
            return cast("GriddesResult", self._execute_info_with_pipeline("griddes"))

    def zaxisdes(self) -> ZaxisdesResult:
        """
        Get vertical axis description (executes immediately).

        Returns:
            ZaxisdesResult with vertical axis information

        Example:
            >>> zaxis = cdo.query("data.nc").zaxisdes()
            >>> print(zaxis.axes[0].zaxistype)
            'pressure'

        See Also:
            - griddes: Grid description
        """
        if self._cdo is None:
            raise CDOError("Query not bound to a CDO instance")
        if self._input is None:
            raise CDOError("Query has no input file (is it a template?)")

        if not self._operators:
            return self._cdo.zaxisdes(self._input)
        else:
            return cast("ZaxisdesResult", self._execute_info_with_pipeline("zaxisdes"))

    def vlist(self) -> VlistResult:
        """
        Get variable list with metadata (executes immediately).

        Returns:
            VlistResult with variable metadata

        Example:
            >>> vlist = cdo.query("data.nc").vlist()
            >>> for var in vlist.variables:
            ...     print(f"{var.name}: {var.units}")
            tas: K
            pr: kg m-2 s-1

        See Also:
            - sinfo: Comprehensive dataset summary
            - showname: Just get variable names
        """
        if self._cdo is None:
            raise CDOError("Query not bound to a CDO instance")
        if self._input is None:
            raise CDOError("Query has no input file (is it a template?)")

        if not self._operators:
            return self._cdo.vlist(self._input)
        else:
            return cast("VlistResult", self._execute_info_with_pipeline("vlist"))

    def partab(self) -> PartabResult:
        """
        Get parameter table information (executes immediately).

        Returns:
            PartabResult with parameter table information

        Example:
            >>> partab = cdo.query("data.nc").partab()
            >>> for param in partab.parameters:
            ...     print(f"{param.code}: {param.name}")

        See Also:
            - vlist: Variable list with metadata
        """
        if self._cdo is None:
            raise CDOError("Query not bound to a CDO instance")
        if self._input is None:
            raise CDOError("Query has no input file (is it a template?)")

        if not self._operators:
            return self._cdo.partab(self._input)
        else:
            return cast("PartabResult", self._execute_info_with_pipeline("partab"))


@dataclass(frozen=True)
class BinaryOpQuery(CDOQuery):
    """
    Query for binary arithmetic operations in CDO.

    BinaryOpQuery handles operations between two datasets using CDO's operator
    chaining syntax (no bracket notation). Operators are applied to their
    respective input files from left to right.

    Binary operators (add, sub, mul, div) do NOT use bracket notation - that's
    only for variadic operators (merge, cat). CDO applies operators directly
    to their input files using operator chaining.

    Example:
        >>> # Simple case
        >>> q = cdo.query("data.nc").sub(F("climatology.nc"))
        >>> print(q.get_command())
        'cdo -sub data.nc climatology.nc'

        >>> # Operators on left
        >>> q = cdo.query("data.nc").year_mean().sub(F("climatology.nc"))
        >>> print(q.get_command())
        'cdo -sub -yearmean data.nc climatology.nc'

        >>> # Operators on both sides - single command!
        >>> q = cdo.query("data.nc").year_mean().sub(F("clim.nc").time_mean())
        >>> print(q.get_command())
        'cdo -sub -yearmean data.nc -timmean clim.nc'

        >>> # Nested binary operations
        >>> masked = cdo.query("data.nc").ifthen(F("mask.nc"))
        >>> q = masked.sub(F("clim.nc"))
        >>> print(q.get_command())
        'cdo -sub -ifthen mask.nc data.nc clim.nc'

    See Also:
        CDO Tutorial on operator chaining:
        https://code.mpimet.mpg.de/projects/cdo/wiki/Tutorial#Combining-Operators
    """

    _operator: str  # Binary operator: sub, add, mul, div, max, min
    _left: CDOQuery  # Left operand
    _right: CDOQuery  # Right operand
    _post_operators: tuple[OperatorSpec, ...]  # Operators applied AFTER the binary op

    def __init__(
        self,
        operator: str,
        left: CDOQuery,
        right: CDOQuery,
        cdo_instance: CDO | None = None,
        post_operators: tuple[OperatorSpec, ...] = (),
    ):
        """
        Initialize binary operation query.

        Args:
            operator: Binary operator name (sub, add, mul, div, min, max, etc.)
            left: Left operand query
            right: Right operand query
            cdo_instance: Parent CDO instance
            post_operators: Operators to apply after the binary operation
        """
        object.__setattr__(self, "_operator", operator)
        object.__setattr__(self, "_left", left)
        object.__setattr__(self, "_right", right)
        object.__setattr__(self, "_cdo", cdo_instance)
        object.__setattr__(
            self, "_operators", ()
        )  # Not used directly, kept for compatibility
        object.__setattr__(self, "_input", None)  # Not used for binary ops
        object.__setattr__(self, "_options", ())  # Not used for binary ops
        object.__setattr__(self, "_post_operators", post_operators)
        # Merge temp files from left and right queries
        left_temps = getattr(left, "_temp_files", ())
        right_temps = getattr(right, "_temp_files", ())
        object.__setattr__(self, "_temp_files", (*left_temps, *right_temps))

    def _clone(self, **kwargs: Any) -> BinaryOpQuery:
        """
        Create a copy with modifications (immutability pattern).

        Args:
            **kwargs: Attributes to override

        Returns:
            New BinaryOpQuery with modifications
        """
        return BinaryOpQuery(
            operator=kwargs.get("operator", self._operator),
            left=kwargs.get("left", self._left),
            right=kwargs.get("right", self._right),
            cdo_instance=kwargs.get("cdo_instance", self._cdo),
            post_operators=kwargs.get("post_operators", self._post_operators),
        )

    def _add_operator(self, spec: OperatorSpec) -> BinaryOpQuery:
        """
        Add an operator to apply after the binary operation (immutable).

        This allows chaining unary operations like .abs().sqrt() after
        binary operations like .sub(F("mean.nc")).

        Args:
            spec: Operator specification to add

        Returns:
            New BinaryOpQuery with operator appended to post_operators
        """
        return self._clone(post_operators=(*self._post_operators, spec))

    def get_command(self, output: str | Path | None = None) -> str:
        """
        Build CDO command for binary operation WITHOUT bracket notation.

        CDO binary operators can handle operators on both operands in a single command.

        Correct CDO syntax:
        1. Neither has operators: cdo -sub file1.nc file2.nc out.nc
        2. Left has operators: cdo -sub -yearmean -selname,tas file1.nc file2.nc out.nc
        3. Right has operators: cdo -sub file1.nc -timmean -selname,tas file2.nc out.nc
        4. Both have operators: cdo -sub -yearmean file1.nc -timmean file2.nc out.nc

        Args:
            output: Optional output file path

        Returns:
            CDO command string

        Examples:
            >>> # Simple case
            >>> q = cdo.query("a.nc").sub(F("b.nc"))
            >>> q.get_command()  # "cdo -sub a.nc b.nc"

            >>> # Left has operators
            >>> q = cdo.query("a.nc").select_var("tas").sub(F("b.nc"))
            >>> q.get_command()  # "cdo -sub -selname,tas a.nc b.nc"

            >>> # Right has operators
            >>> q = cdo.query("a.nc").sub(F("b.nc").year_mean())
            >>> q.get_command()  # "cdo -sub a.nc -yearmean b.nc"

            >>> # Both have operators
            >>> q = cdo.query("a.nc").year_mean().sub(F("b.nc").time_mean())
            >>> q.get_command()  # "cdo -sub -yearmean a.nc -timmean b.nc"
        """
        # Check if operands have operators
        left_has_ops = bool(self._left._operators) or isinstance(
            self._left, BinaryOpQuery
        )
        right_has_ops = bool(self._right._operators) or isinstance(
            self._right, BinaryOpQuery
        )

        # Special handling for ifthenelse which needs all three operands
        if (
            self._operator == "ifthenelse"
            and isinstance(self._right, BinaryOpQuery)
            and self._right._operator == "_ifthenelse_args"
        ):
            # All three operands need evaluation - requires temp files if any have ops
            if (
                left_has_ops
                or bool(self._right._left._operators)
                or isinstance(self._right._left, BinaryOpQuery)
                or bool(self._right._right._operators)
                or isinstance(self._right._right, BinaryOpQuery)
            ):
                raise CDOError(
                    "ifthenelse with operators on any operand requires "
                    "temporary file handling (call compute() instead of get_command())"
                )
            # Simple case - all three are just files
            cmd = (
                f"cdo -ifthenelse {self._left._input} "
                f"{self._right._left._input} {self._right._right._input}"
            )
            if output:
                cmd = f"{cmd} {output}"
            return cmd

        # Build command based on which operands have operators
        if not left_has_ops and not right_has_ops:
            # Case 1: cdo -sub file1.nc file2.nc
            cmd = f"cdo -{self._operator} {self._left._input} {self._right._input}"

        elif left_has_ops and not right_has_ops:
            # Case 2: cdo -sub -yearmean file1.nc file2.nc
            left_chain = self._get_operator_chain(self._left)
            cmd = f"cdo -{self._operator} {left_chain} {self._right._input}"

        elif not left_has_ops and right_has_ops:
            # Case 3: cdo -sub file1.nc -timmean file2.nc
            right_chain = self._get_operator_chain(self._right)
            cmd = f"cdo -{self._operator} {self._left._input} {right_chain}"

        else:
            # Case 4: cdo -sub -yearmean file1.nc -timmean file2.nc
            left_chain = self._get_operator_chain(self._left)
            right_chain = self._get_operator_chain(self._right)
            cmd = f"cdo -{self._operator} {left_chain} {right_chain}"

        # Apply post_operators (operations after the binary op)
        if self._post_operators:
            post_ops = " ".join(
                op.to_cdo_fragment() for op in reversed(self._post_operators)
            )
            cmd = f"cdo {post_ops} {cmd[4:]}"  # Remove 'cdo ' and prepend post_ops

        if output:
            cmd = f"{cmd} {output}"
        return cmd

    def _get_operator_chain(self, query: CDOQuery) -> str:
        """
        Get operator chain for operands in binary operation.

        Binary operations support operator chaining on both operands:
        - Left: cdo -sub -yearmean -selname,tas file1.nc file2.nc
        - Right: cdo -sub file1.nc -timmean -selname,tas file2.nc
        - Both: cdo -sub -yearmean file1.nc -timmean file2.nc

        This allows processing without temporary files.

        Args:
            query: Operand query (left or right)

        Returns:
            Operator chain string like "-yearmean -selname,tas file.nc"

        Note:
            For nested BinaryOpQuery, this will recursively build the command.
        """
        if isinstance(query, BinaryOpQuery):
            # Nested binary operation - recursively build its command
            # CDO supports this: cdo -sub -ifthen mask.nc data.nc climatology.nc
            nested_op = f"-{query._operator}"

            # Build chains for its operands
            nested_left = self._get_operator_chain(query._left)
            nested_right = self._get_operator_chain(query._right)

            # Apply any post_operators from the nested query
            if query._post_operators:
                post_ops = " ".join(
                    op.to_cdo_fragment() for op in reversed(query._post_operators)
                )
                return f"{post_ops} {nested_op} {nested_left} {nested_right}"

            return f"{nested_op} {nested_left} {nested_right}"

        if not query._operators:
            # Simple file reference
            return str(query._input)

        # Build operator chain: operators in reverse order, then input file
        ops = " ".join(op.to_cdo_fragment() for op in reversed(query._operators))
        return f"{ops} {query._input}"

    def compute(self, output: str | Path | None = None) -> xr.Dataset:
        """
        Execute binary operation (no temporary files needed).

        CDO natively handles operators on both operands in a single command.

        Args:
            output: Optional output file path

        Returns:
            xarray.Dataset with results

        Raises:
            CDOError: If query not bound to CDO instance
        """
        if self._cdo is None:
            raise CDOError("Query not bound to a CDO instance")

        import os
        import subprocess
        import tempfile
        from pathlib import Path

        import xarray as xr

        from .exceptions import CDOExecutionError
        from .validation import validate_file_exists

        # Validate input files exist
        if self._left._input:
            validate_file_exists(self._left._input)
        if self._right._input:
            validate_file_exists(self._right._input)

        # Build command using get_command()
        cmd = self.get_command()

        # Determine output file
        if output:
            output_path = Path(output)
            use_temp = False
        else:
            fd, temp_path = tempfile.mkstemp(suffix=".nc", dir=self._cdo.temp_dir)
            os.close(fd)
            output_path = Path(temp_path)
            use_temp = True

        try:
            full_cmd = f"{cmd} {output_path}"

            if self._cdo.debug:
                print(f"[CDO] Executing: {full_cmd}")

            result = subprocess.run(
                full_cmd,
                shell=True,
                capture_output=True,
                text=True,
                env={**os.environ, **self._cdo.env},
            )

            if result.returncode != 0:
                raise CDOExecutionError(
                    message=f"CDO command failed with return code {result.returncode}",
                    command=full_cmd,
                    returncode=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr,
                )

            ds = xr.open_dataset(output_path)

            if use_temp:
                ds = ds.load()
                output_path.unlink()

            # Clean up tracked temp files before return
            if self._temp_files:
                import contextlib

                for temp_file in self._temp_files:
                    if temp_file and temp_file.exists():
                        with contextlib.suppress(Exception):
                            temp_file.unlink()

            return ds

        except Exception:
            if use_temp and output_path.exists():
                output_path.unlink()

            # Clean up tracked temp files even on error
            if self._temp_files:
                import contextlib

                for temp_file in self._temp_files:
                    if temp_file and temp_file.exists():
                        with contextlib.suppress(Exception):
                            temp_file.unlink()

            raise

    def explain(self) -> str:
        """
        Return human-readable explanation of binary operation.

        Returns:
            Multi-line string describing the operation
        """
        lines = [f"Binary Operation: {self._operator}"]
        lines.append("Left operand:")
        for line in self._left.explain().split("\n"):
            lines.append(f"  {line}")
        lines.append("Right operand:")
        for line in self._right.explain().split("\n"):
            lines.append(f"  {line}")
        if self._post_operators:
            lines.append("Post-operations:")
            for i, op in enumerate(self._post_operators, 1):
                args_str = ", ".join(str(a) for a in op.args) if op.args else ""
                lines.append(f"  {i}. {op.name}({args_str})")
        return "\n".join(lines)


def F(input_file: str | Path) -> CDOQuery:
    """
    Create a CDOQuery for use in binary operations (F-expression style).

    Inspired by Django's F() for referencing fields in database queries.
    Use this to reference additional input files in binary arithmetic.

    Args:
        input_file: Path to NetCDF file

    Returns:
        CDOQuery that can be chained and used in binary operations

    Example:
        >>> # Simple anomaly
        >>> anomaly = cdo.query("data.nc").sub(F("climatology.nc")).compute()

        >>> # Process both sides
        >>> diff = (
        ...     cdo.query("data1.nc").select_var("tas").year_mean()
        ...     .sub(F("data2.nc").select_var("tas").year_mean())
        ...     .compute()
        ... )

    Note:
        F() creates queries without CDO instance binding. They are only
        used as operands in binary operations, not executed directly.
    """
    return CDOQuery._create_unbound(Path(input_file))


class CDOQueryTemplate(CDOQuery):
    """
    Reusable query template for CDO operations.

    Allows building a pipeline of operators that can be applied to different
    input files.

    Example:
        >>> from python_cdo_wrapper import CDO, CDOQueryTemplate
        >>> cdo = CDO()
        >>> template = CDOQueryTemplate().select_var("tas").year_mean()
        >>> ds1 = template.apply("data_2020.nc", cdo).compute()
        >>> ds2 = template.apply("data_2021.nc", cdo).compute()
    """

    def __init__(
        self,
        operators: tuple[OperatorSpec, ...] = (),
        options: tuple[str, ...] = (),
    ):
        super().__init__(
            input_file=None, operators=operators, options=options, cdo_instance=None
        )

    def _clone(self, **kwargs: Any) -> CDOQueryTemplate:
        """
        Create a copy with modifications (template-specific).

        Templates always have input_file=None and cdo_instance=None,
        so we ignore those parameters.

        Args:
            **kwargs: Attributes to override (operators, options only)

        Returns:
            New CDOQueryTemplate with modifications
        """
        return CDOQueryTemplate(
            operators=kwargs.get("operators", self._operators),
            options=kwargs.get("options", self._options),
        )

    def apply(self, input_file: str | Path, cdo_instance: CDO) -> CDOQuery:
        """
        Apply the template to an input file.

        Args:
            input_file: Path to input NetCDF file
            cdo_instance: CDO instance to use for execution

        Returns:
            Bound CDOQuery ready for execution
        """
        return CDOQuery(
            input_file=input_file,
            operators=self._operators,
            options=self._options,
            cdo_instance=cdo_instance,
        )
