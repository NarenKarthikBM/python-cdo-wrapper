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
        """Parse a single grid section."""
        grid_data: dict[str, str | int | float] = {"grid_id": grid_id}

        for line in content.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("cdo"):
                continue

            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"')

                # Convert numeric values
                if key in ["gridsize", "xsize", "ysize"]:
                    grid_data[key] = int(value)
                elif key in ["xfirst", "xinc", "yfirst", "yinc"]:
                    grid_data[key] = float(value)
                else:
                    grid_data[key] = value

        return GridInfo(**grid_data)  # type: ignore


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
