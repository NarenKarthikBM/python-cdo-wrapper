"""Grid-related parsers for CDO output."""

from __future__ import annotations

import re

from ..exceptions import CDOParseError
from ..types.grid import GridInfo, ZaxisInfo
from ..types.results import GriddesResult, ZaxisdesResult
from .base import CDOParser


class GriddesParser(CDOParser[GriddesResult]):
    """
    Parser for griddes command output.

    Parses CDO grid description format into structured GridInfo objects.

    Supported Grid Types:
    ---------------------
    - **lonlat**: Regular latitude-longitude grids with uniform spacing
    - **gaussian**: Gaussian grids with regular longitude, irregular latitude
    - **gaussian_reduced**: Reduced Gaussian grids with variable longitude points per row
    - **generic**: Generic grids with minimal metadata
    - **projection**: Rotated pole and other CF Conventions projections
    - **curvilinear**: Structured grids with 2D coordinate arrays
    - **unstructured**: Irregular meshes and point clouds

    For grid types with unrecognized attributes, the parser stores them in the
    `raw_attributes` dictionary field for inspection and debugging.

    Example:
        >>> parser = GriddesParser()
        >>> result = parser.parse(cdo_griddes_output)
        >>> grid = result.primary_grid
        >>> print(f"Grid type: {grid.gridtype}, Size: {grid.gridsize}")
    """

    def parse(self, output: str) -> GriddesResult:
        """
        Parse griddes output.

        Args:
            output: Raw output from CDO griddes command.

        Returns:
            GriddesResult containing parsed grid information.

        Raises:
            CDOParseError: If parsing fails.
        """
        grids: list[GridInfo] = []

        # Split by grid sections (# gridID N)
        grid_sections = re.split(r"#\s*gridID\s+(\d+)", output)

        # Skip first empty section, then process pairs (id, content)
        for i in range(1, len(grid_sections), 2):
            if i + 1 >= len(grid_sections):
                break

            grid_id = int(grid_sections[i])
            content = grid_sections[i + 1]

            try:
                grid_info = self._parse_grid_section(grid_id, content)
                grids.append(grid_info)
            except Exception as e:
                raise CDOParseError(
                    message=f"Failed to parse grid {grid_id}",
                    raw_output=content[:200],
                ) from e

        if not grids:
            raise CDOParseError(
                message="No grids found in griddes output",
                raw_output=output[:200],
            )

        return GriddesResult(grids=grids)

    def _parse_grid_section(self, grid_id: int, content: str) -> GridInfo:
        """
        Parse a single grid section.

        Supports all CDO grid types:
        - lonlat: Regular latitude-longitude grids
        - gaussian: Gaussian grids with regular longitude spacing
        - gaussian_reduced: Reduced Gaussian grids with variable longitude points
        - generic: Generic grids with minimal metadata
        - projection: Rotated pole and other projections (CF Conventions)
        - curvilinear: 2D coordinate arrays
        - unstructured: Irregular meshes/point clouds

        For unknown formats, stores all attributes in raw_attributes dictionary.
        """
        grid_data: dict[
            str,
            str
            | int
            | float
            | list[int]
            | list[float]
            | dict[str, str | int | float | list[int] | list[float]],
        ] = {"grid_id": grid_id}
        raw_attrs: dict[str, str | int | float | list[int] | list[float]] = {}

        # Define known attribute keys that map to GridInfo fields
        known_keys = {
            "grid_id",
            "gridtype",
            "gridsize",
            "datatype",
            "xsize",
            "ysize",
            "xname",
            "xlongname",
            "xunits",
            "yname",
            "ylongname",
            "yunits",
            "xfirst",
            "xinc",
            "yfirst",
            "yinc",
            "xvals",
            "yvals",
            "scanningMode",
            "grid_mapping",
            "grid_mapping_name",
            "grid_north_pole_longitude",
            "grid_north_pole_latitude",
            "np",
            "rowlon",
            "points",
            "nvertex",
        }

        for line in content.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("cdo"):
                continue

            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"')

                # Parse and type-convert based on key
                try:
                    parsed_value = self._parse_grid_attribute(key, value)

                    # Only add known keys to grid_data, unknown keys go to raw_attributes
                    if key in known_keys:
                        grid_data[key] = parsed_value
                    else:
                        # Unknown keys stored in raw_attributes for inspection
                        raw_attrs[key] = parsed_value

                except Exception:
                    # If parsing fails, store as string in raw_attributes
                    raw_attrs[key] = value

        # Add raw_attributes if any unrecognized attributes were found
        if raw_attrs:
            grid_data["raw_attributes"] = raw_attrs

        return GridInfo(**grid_data)  # type: ignore

    def _parse_grid_attribute(
        self, key: str, value: str
    ) -> str | int | float | list[int] | list[float]:
        """
        Parse a grid attribute based on its key.

        Args:
            key: Attribute key name.
            value: String value to parse.

        Returns:
            Parsed value with appropriate type.
        """
        # Integer fields
        if key in ["gridsize", "xsize", "ysize", "np", "points", "nvertex"]:
            return int(value)

        # Float fields
        elif key in [
            "xfirst",
            "xinc",
            "yfirst",
            "yinc",
            "scanningMode",
            "grid_north_pole_longitude",
            "grid_north_pole_latitude",
        ]:
            return float(value)

        # Float list fields (space-separated)
        elif key in ["xvals", "yvals", "levels"]:
            return [float(v) for v in value.split() if v]

        # Integer list fields (space-separated)
        elif key == "rowlon":
            return [int(v) for v in value.split() if v]

        # String fields (already stripped of quotes)
        else:
            return value


class ZaxisdesParser(CDOParser[ZaxisdesResult]):
    """
    Parser for zaxisdes command output.

    Parses CDO vertical axis description into structured ZaxisInfo objects.
    """

    def parse(self, output: str) -> ZaxisdesResult:
        """
        Parse zaxisdes output.

        Args:
            output: Raw output from CDO zaxisdes command.

        Returns:
            ZaxisdesResult containing parsed vertical axis information.

        Raises:
            CDOParseError: If parsing fails.
        """
        zaxes: list[ZaxisInfo] = []

        # Split by zaxis sections (# zaxisID N)
        zaxis_sections = re.split(r"#\s*zaxisID\s+(\d+)", output)

        # Skip first empty section, then process pairs (id, content)
        for i in range(1, len(zaxis_sections), 2):
            if i + 1 >= len(zaxis_sections):
                break

            zaxis_id = int(zaxis_sections[i])
            content = zaxis_sections[i + 1]

            try:
                zaxis_info = self._parse_zaxis_section(zaxis_id, content)
                zaxes.append(zaxis_info)
            except Exception as e:
                raise CDOParseError(
                    message=f"Failed to parse zaxis {zaxis_id}",
                    raw_output=content[:200],
                ) from e

        if not zaxes:
            raise CDOParseError(
                message="No vertical axes found in zaxisdes output",
                raw_output=output[:200],
            )

        return ZaxisdesResult(zaxes=zaxes)

    def _parse_zaxis_section(self, zaxis_id: int, content: str) -> ZaxisInfo:
        """Parse a single zaxis section."""
        zaxis_data: dict[str, str | int | list[float]] = {"zaxis_id": zaxis_id}

        for line in content.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("cdo"):
                continue

            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"')

                # Convert values based on key
                if key == "size":
                    zaxis_data[key] = int(value)
                elif key in ["levels", "lbounds", "ubounds"]:
                    # Parse space-separated level values
                    try:
                        zaxis_data[key] = [float(v) for v in value.split() if v]
                    except ValueError:
                        zaxis_data[key] = []
                else:
                    zaxis_data[key] = value

        return ZaxisInfo(**zaxis_data)  # type: ignore
