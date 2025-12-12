"""
Parsers for converting CDO text output into structured dictionaries.

This module provides parser classes that convert text output from various
CDO commands into structured Python dictionaries for easier programmatic access.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any


class CDOParser(ABC):
    """Abstract base class for CDO output parsers."""

    @abstractmethod
    def parse(self, output: str) -> dict[str, Any] | list[dict[str, Any]]:
        """
        Parse CDO text output into structured data.

        Args:
            output: Raw text output from a CDO command.

        Returns:
            Parsed structured data as dict or list of dicts.
        """
        pass


class GriddesParser(CDOParser):
    """Parser for griddes output."""

    def parse(self, output: str) -> dict[str, Any]:
        """
        Parse griddes output into a structured dictionary.

        Args:
            output: Raw griddes output text.

        Returns:
            Dictionary containing grid information.
        """
        grid_info: dict[str, Any] = {}
        lines = output.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Handle key = value pairs
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                # Try to convert to appropriate type
                if value.isdigit():
                    grid_info[key] = int(value)
                elif self._is_float(value):
                    grid_info[key] = float(value)
                else:
                    grid_info[key] = value

            # Handle multi-value lines (like xvals, yvals)
            elif line.startswith(("xvals", "yvals", "xbounds", "ybounds")):
                parts = line.split("=", 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    values_str = parts[1].strip()
                    # Parse array values
                    grid_info[key] = self._parse_array(values_str)

        return grid_info

    @staticmethod
    def _is_float(value: str) -> bool:
        """Check if a string represents a float."""
        try:
            float(value)
            return True
        except ValueError:
            return False

    @staticmethod
    def _parse_array(values_str: str) -> list[float]:
        """Parse array values from string."""
        values = []
        for val in values_str.split():
            try:
                values.append(float(val))
            except ValueError:
                continue
        return values


class ZaxisdesParser(CDOParser):
    """Parser for zaxisdes output."""

    def parse(self, output: str) -> dict[str, Any]:
        """
        Parse zaxisdes output into a structured dictionary.

        Args:
            output: Raw zaxisdes output text.

        Returns:
            Dictionary containing z-axis information.
        """
        zaxis_info: dict[str, Any] = {}
        lines = output.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                # Handle arrays (levels, vct)
                if key in ("levels", "vct", "lbounds", "ubounds"):
                    zaxis_info[key] = self._parse_array(value)
                elif value.isdigit():
                    zaxis_info[key] = int(value)
                elif self._is_float(value):
                    zaxis_info[key] = float(value)
                else:
                    zaxis_info[key] = value

        return zaxis_info

    @staticmethod
    def _is_float(value: str) -> bool:
        """Check if a string represents a float."""
        try:
            float(value)
            return True
        except ValueError:
            return False

    @staticmethod
    def _parse_array(values_str: str) -> list[float]:
        """Parse array values from string."""
        values = []
        for val in values_str.split():
            try:
                values.append(float(val))
            except ValueError:
                continue
        return values


class SinfoParser(CDOParser):
    """Parser for sinfo/info output."""

    def parse(self, output: str) -> dict[str, Any]:
        """
        Parse sinfo output into a structured dictionary.

        Args:
            output: Raw sinfo output text.

        Returns:
            Dictionary containing dataset information with sections:
            - metadata: File format and variable table header info
            - variables: List of variables with their properties
            - grid: Grid coordinate information with resolution
            - vertical: Vertical coordinate information
            - time: Time coordinate information with resolution and timesteps
        """
        info: dict[str, Any] = {
            "variables": [],
            "metadata": {},
            "grid": {},
            "vertical": {},
            "time": {},
        }
        lines = output.strip().split("\n")

        current_section = None
        grid_id = None
        vertical_id = None
        time_buffer: list[str] = []

        i = 0
        while i < len(lines):
            line = lines[i]
            line_stripped = line.strip()

            # Detect file format
            if "File format" in line:
                info["metadata"]["format"] = line.split(":")[-1].strip()
                i += 1
                continue

            # Detect variable table header with metadata fields
            if "-1 :" in line_stripped:
                current_section = "variables"
                # Parse the header line for field names
                header_parts = line_stripped.split(":")
                if len(header_parts) >= 2:
                    # Extract field names from header
                    fields = header_parts[1].strip()
                    if fields:
                        info["metadata"]["variable_fields"] = fields
                i += 1
                continue

            # Detect grid section
            if "Grid coordinates" in line:
                current_section = "grid"
                # Extract grid ID if present
                match = re.search(r"^\s*(\d+)\s*:", line)
                if match:
                    grid_id = int(match.group(1))
                i += 1
                continue

            # Detect vertical coordinates section
            if "Vertical coordinates" in line:
                current_section = "vertical"
                # Extract vertical ID if present
                match = re.search(r"^\s*(\d+)\s*:", line)
                if match:
                    vertical_id = int(match.group(1))
                i += 1
                continue

            # Detect time coordinate section
            if "Time coordinate" in line:
                current_section = "time"
                i += 1
                continue

            # Parse sections based on current context
            if current_section == "variables" and re.match(r"^\s*\d+\s*:", line):
                var_info = SinfoParser._parse_variable_line(line_stripped)
                if var_info:
                    info["variables"].append(var_info)
            elif current_section == "grid":
                SinfoParser._parse_grid_line(line_stripped, info["grid"], grid_id)
            elif current_section == "vertical":
                SinfoParser._parse_vertical_line(
                    line_stripped, info["vertical"], vertical_id
                )
            elif current_section == "time":
                # Time section can span multiple lines
                SinfoParser._parse_time_line(line_stripped, info["time"], time_buffer)

            i += 1

        # Finalize time parsing (process buffered timesteps)
        if time_buffer:
            SinfoParser._finalize_time_parsing(info["time"], time_buffer)

        return info

    @staticmethod
    def _parse_variable_line(line: str) -> dict[str, Any] | None:
        """Parse a single variable line from sinfo output.

        Example input: "1 : unknown  unknown  v instant       1   1     17415   1  F32  : 260"
        Format: "Index : Institut Source T Steptype Levels Num Points Num Dtype : Parameter"
        """
        # Find the last colon which separates the parameter name
        last_colon_idx = line.rfind(":")
        if last_colon_idx == -1:
            return None

        var_name = line[last_colon_idx + 1 :].strip()
        if not var_name or var_name in ("Parameter name", "Parameter ID", ""):
            return None

        # Find the first colon which separates the index
        first_colon_idx = line.find(":")
        if first_colon_idx == -1 or first_colon_idx == last_colon_idx:
            return None

        # Extract the middle section between first and last colons
        middle_section = line[first_colon_idx + 1 : last_colon_idx].strip()
        fields = middle_section.split()

        result: dict[str, Any] = {"name": var_name}

        # Parse based on field count - format can vary
        # Typical format: Institut Source T Steptype Levels Num Points Num Dtype
        if len(fields) >= 9:
            result["institut"] = fields[0]
            result["source"] = fields[1]
            result["table"] = fields[2]
            result["steptype"] = fields[3]
            try:
                result["levels"] = int(fields[4])
            except ValueError:
                result["levels"] = fields[4]
            try:
                result["num"] = int(fields[5])
            except ValueError:
                result["num"] = fields[5]
            try:
                result["points"] = int(fields[6])
            except ValueError:
                result["points"] = fields[6]
            try:
                result["num2"] = int(fields[7])
            except ValueError:
                result["num2"] = fields[7]
            result["dtype"] = fields[8]
        # Older format: Date Time Level Gridsize Num Dtype
        elif len(fields) >= 6:
            result["date"] = fields[0]
            result["time"] = fields[1]
            try:
                result["level"] = int(fields[2])
            except ValueError:
                result["level"] = fields[2]
            try:
                result["gridsize"] = int(fields[3])
            except ValueError:
                result["gridsize"] = fields[3]
            try:
                result["num"] = int(fields[4])
            except ValueError:
                result["num"] = fields[4]
            result["dtype"] = fields[5]

        return result

    @staticmethod
    def _parse_grid_line(
        line_stripped: str, grid_info: dict[str, Any], grid_id: int | None
    ) -> None:
        """Parse a single line from the grid coordinates section."""
        # Skip empty lines and section headers
        if not line_stripped or "Grid coordinates" in line_stripped:
            return

        # Parse grid ID and type (e.g., "1 : lonlat : points=17415 (135x129)")
        if ":" in line_stripped and re.match(r"^\s*\d+\s*:", line_stripped):
            parts = line_stripped.split(":")
            if len(parts) >= 2:
                grid_id = int(parts[0].strip())
                grid_info["id"] = grid_id
                grid_type = parts[1].strip()
                grid_info["type"] = grid_type

                # Parse points and dimensions if present
                if len(parts) >= 3:
                    points_info = parts[2].strip()
                    # Extract points count (e.g., "points=17415 (135x129)")
                    points_match = re.search(r"points=(\d+)", points_info)
                    if points_match:
                        grid_info["points"] = int(points_match.group(1))

                    # Extract dimensions (e.g., "135x129")
                    dims_match = re.search(r"\((\d+)x(\d+)\)", points_info)
                    if dims_match:
                        grid_info["xsize"] = int(dims_match.group(1))
                        grid_info["ysize"] = int(dims_match.group(2))
            return

        # Parse coordinate details (lon/lat lines)
        coord_match = re.match(
            r"^\s*(lon|lat)\s*:\s*([-\d.]+)\s+to\s+([-\d.]+)\s+by\s+([-\d.]+)\s*\[([^\]]+)\]",
            line_stripped,
        )
        if coord_match:
            coord_name = coord_match.group(1)
            start = float(coord_match.group(2))
            end = float(coord_match.group(3))
            step = float(coord_match.group(4))
            units = coord_match.group(5)

            grid_info[f"{coord_name}_start"] = start
            grid_info[f"{coord_name}_end"] = end
            grid_info[f"{coord_name}_resolution"] = step
            grid_info[f"{coord_name}_units"] = units

    @staticmethod
    def _parse_vertical_line(
        line_stripped: str,
        vertical_info: dict[str, Any],
        vertical_id: int | None,
    ) -> None:
        """Parse a single line from the vertical coordinates section."""
        # Skip empty lines and section headers
        if not line_stripped or "Vertical coordinates" in line_stripped:
            return

        # Parse vertical axis (e.g., "1 : surface : levels=1")
        if ":" in line_stripped and re.match(r"^\s*\d+\s*:", line_stripped):
            parts = line_stripped.split(":")
            if len(parts) >= 2:
                vertical_id = int(parts[0].strip())
                vertical_info["id"] = vertical_id
                vertical_type = parts[1].strip()
                vertical_info["type"] = vertical_type

                # Parse levels count if present
                if len(parts) >= 3:
                    levels_info = parts[2].strip()
                    levels_match = re.search(r"levels=(\d+)", levels_info)
                    if levels_match:
                        vertical_info["levels"] = int(levels_match.group(1))

    @staticmethod
    def _parse_time_line(
        line_stripped: str,
        time_info: dict[str, Any],
        time_buffer: list[str],
    ) -> None:
        """Parse a single line from the time coordinate section."""
        # Skip empty lines and section headers
        if not line_stripped or "Time coordinate" in line_stripped:
            return

        # Parse timestep count (e.g., "time : 43464 steps")
        steps_match = re.match(r"^\s*time\s*:\s*(\d+)\s+steps", line_stripped)
        if steps_match:
            time_info["steps"] = int(steps_match.group(1))
            return

        # Parse RefTime, Units, Calendar (e.g., "RefTime = 1901-01-01 00:00:00  Units = hours  Calendar = standard")
        if "RefTime" in line_stripped:
            # Extract RefTime
            reftime_match = re.search(r"RefTime\s*=\s*([\d-]+ [\d:]+)", line_stripped)
            if reftime_match:
                time_info["reftime"] = reftime_match.group(1)

            # Extract Units
            units_match = re.search(r"Units\s*=\s*(\w+)", line_stripped)
            if units_match:
                time_info["units"] = units_match.group(1)

            # Extract Calendar
            calendar_match = re.search(r"Calendar\s*=\s*(\w+)", line_stripped)
            if calendar_match:
                time_info["calendar"] = calendar_match.group(1)
            return

        # Check if line contains timesteps (date-time values)
        # Pattern: YYYY-MM-DD hh:mm:ss
        if re.search(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}", line_stripped):
            # Add to buffer for later processing
            time_buffer.append(line_stripped)
            return

        # Check for dots indicating omitted timesteps
        if re.match(r"^\.+$", line_stripped):
            time_info["has_omitted_timesteps"] = True
            return

    @staticmethod
    def _finalize_time_parsing(
        time_info: dict[str, Any], time_buffer: list[str]
    ) -> None:
        """Process buffered timestep lines and extract time resolution."""
        if not time_buffer:
            return

        timesteps = []
        for line in time_buffer:
            # Extract all date-time patterns from the line
            matches = re.findall(r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", line)
            timesteps.extend(matches)

        if timesteps:
            time_info["timesteps"] = timesteps
            time_info["first_timestep"] = timesteps[0]
            time_info["last_timestep"] = timesteps[-1]

            # Calculate time resolution from first few timesteps
            if len(timesteps) >= 2:
                time_info["time_resolution"] = SinfoParser._calculate_time_resolution(
                    timesteps[: min(10, len(timesteps))]
                )

    @staticmethod
    def _calculate_time_resolution(timesteps: list[str]) -> dict[str, Any]:
        """Calculate time resolution from a sample of timesteps."""
        from datetime import datetime

        resolution_info: dict[str, Any] = {}

        try:
            # Parse first few timesteps
            dates = [datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") for ts in timesteps[:5]]

            if len(dates) >= 2:
                # Calculate differences between consecutive timesteps
                deltas = [
                    (dates[i + 1] - dates[i]).total_seconds()
                    for i in range(len(dates) - 1)
                ]

                # Check if all deltas are the same (regular spacing)
                if len(set(deltas)) == 1:
                    delta_seconds = deltas[0]
                    resolution_info["regular"] = True
                    resolution_info["interval_seconds"] = delta_seconds

                    # Convert to human-readable format
                    if delta_seconds == 3600:
                        resolution_info["interval"] = "1 hour"
                    elif delta_seconds == 86400:
                        resolution_info["interval"] = "1 day"
                    elif delta_seconds == 21600:
                        resolution_info["interval"] = "6 hours"
                    elif delta_seconds == 43200:
                        resolution_info["interval"] = "12 hours"
                    elif delta_seconds % 86400 == 0:
                        days = int(delta_seconds / 86400)
                        resolution_info["interval"] = f"{days} days"
                    elif delta_seconds % 3600 == 0:
                        hours = int(delta_seconds / 3600)
                        resolution_info["interval"] = f"{hours} hours"
                    else:
                        resolution_info["interval"] = f"{delta_seconds} seconds"
                else:
                    resolution_info["regular"] = False
                    resolution_info["interval"] = "irregular"

        except (ValueError, IndexError):
            # If parsing fails, mark as unknown
            resolution_info["regular"] = False
            resolution_info["interval"] = "unknown"

        return resolution_info

    @staticmethod
    def _parse_variable_line_old(line: str) -> dict[str, Any] | None:
        """DEPRECATED: Old parse method for backward compatibility.

        Parse a single variable line from sinfo output (old format).

        Example input: "1 : 2020-01-01 00:00:00  0  518400  1  F64 : tas"
        Format: "Index : Date Time Level Gridsize Num Dtype : Parameter name"
        """
        # Find the last colon which separates the parameter name
        last_colon_idx = line.rfind(":")
        if last_colon_idx == -1:
            return None

        var_name = line[last_colon_idx + 1 :].strip()
        if not var_name or var_name in ("Parameter name", ""):
            return None

        # Find the first colon which separates the index
        first_colon_idx = line.find(":")
        if first_colon_idx == -1 or first_colon_idx == last_colon_idx:
            return None

        # Extract the middle section between first and last colons
        middle_section = line[first_colon_idx + 1 : last_colon_idx].strip()
        fields = middle_section.split()

        result: dict[str, Any] = {"name": var_name}

        # Expected format: Date Time Level Gridsize Num Dtype
        # Example: 2020-01-01 00:00:00 0 518400 1 F64
        if len(fields) >= 6:
            result["date"] = fields[0]
            result["time"] = fields[1]
            # Parse level (can be integer or string like "surface")
            try:
                result["level"] = int(fields[2])
            except ValueError:
                result["level"] = fields[2]
            # Parse gridsize (typically an integer)
            try:
                result["gridsize"] = int(fields[3])
            except ValueError:
                result["gridsize"] = fields[3]
            # Parse num (typically an integer)
            try:
                result["num"] = int(fields[4])
            except ValueError:
                result["num"] = fields[4]
            result["dtype"] = fields[5]

        return result


class VlistParser(CDOParser):
    """Parser for vlist output."""

    def parse(self, output: str) -> list[dict[str, Any]]:
        """
        Parse vlist output into a list of variable dictionaries.

        Args:
            output: Raw vlist output text.

        Returns:
            List of dictionaries, each containing variable information.
        """
        variables = []
        lines = output.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Parse variable info lines
            # Example format varies, but typically contains variable attributes
            var_info = self._parse_variable_info(line)
            if var_info:
                variables.append(var_info)

        return variables

    @staticmethod
    def _parse_variable_info(line: str) -> dict[str, Any] | None:
        """Parse variable information from a line."""
        # This is a simplified parser - actual vlist format varies
        parts = line.split()
        if not parts:
            return None

        return {"raw": line, "parts": parts}


class ShowattsParser(CDOParser):
    """Parser for showatts output."""

    def parse(self, output: str) -> dict[str, dict[str, Any]]:
        """
        Parse showatts output into a nested dictionary.

        Args:
            output: Raw showatts output text.

        Returns:
            Dictionary mapping variable names to their attributes.
        """
        attributes: dict[str, dict[str, Any]] = {}
        lines = output.strip().split("\n")

        current_var = None
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detect variable section headers (e.g., "Temperature attributes:")
            if "attributes:" in line.lower() or line.endswith(":"):
                current_var = line.rstrip(":").strip()
                if "attributes" in current_var.lower():
                    current_var = current_var.replace("attributes", "").strip()
                attributes[current_var] = {}
                continue

            # Parse attribute lines
            if current_var and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                attributes[current_var][key] = value

        return attributes


class PartabParser(CDOParser):
    """Parser for partab/codetab output."""

    def parse(self, output: str) -> list[dict[str, Any]]:
        """
        Parse partab output into a list of parameter dictionaries.

        Args:
            output: Raw partab output text.

        Returns:
            List of dictionaries containing parameter information.
        """
        parameters = []
        lines = output.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Parse parameter table lines
            param_info = self._parse_parameter_line(line)
            if param_info:
                parameters.append(param_info)

        return parameters

    @staticmethod
    def _parse_parameter_line(line: str) -> dict[str, Any] | None:
        """Parse a parameter line from partab output."""
        # Example format: code | name | units | description
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 2:
            # Try space-separated
            parts = line.split()
            if not parts:
                return None

        result: dict[str, Any] = {"raw": line}
        if len(parts) >= 1:
            result["code"] = parts[0]
        if len(parts) >= 2:
            result["name"] = parts[1]
        if len(parts) >= 3:
            result["units"] = parts[2]
        if len(parts) >= 4:
            result["description"] = " ".join(parts[3:])

        return result


class VctParser(CDOParser):
    """Parser for vct/vct2 output."""

    def parse(self, output: str) -> dict[str, list[float]]:
        """
        Parse vct output into arrays.

        Args:
            output: Raw vct output text.

        Returns:
            Dictionary with VCT values as arrays.
        """
        vct_values = []
        lines = output.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Parse numeric values
            for part in line.split():
                try:
                    vct_values.append(float(part))
                except ValueError:
                    continue

        return {"vct": vct_values}


# Registry of parsers for each command
PARSER_REGISTRY: dict[str, type[CDOParser]] = {
    "griddes": GriddesParser,
    "griddes2": GriddesParser,
    "zaxisdes": ZaxisdesParser,
    "sinfo": SinfoParser,
    "sinfon": SinfoParser,
    "sinfov": SinfoParser,
    "info": SinfoParser,
    "infon": SinfoParser,
    "infov": SinfoParser,
    "vlist": VlistParser,
    "showatts": ShowattsParser,
    "partab": PartabParser,
    "codetab": PartabParser,
    "vct": VctParser,
    "vct2": VctParser,
}


def parse_cdo_output(
    command: str, output: str
) -> dict[str, Any] | list[dict[str, Any]]:
    """
    Parse CDO command output into structured data.

    Args:
        command: The CDO command that was executed.
        output: The raw text output from the command.

    Returns:
        Parsed structured data as dict or list of dicts.

    Raises:
        ValueError: If no parser is available for the command.

    Example:
        >>> output = cdo("griddes data.nc")
        >>> parsed = parse_cdo_output("griddes", output)
        >>> print(parsed["gridtype"])
        lonlat
    """
    # Extract the operator name from the command
    cmd_parts = command.strip().split()
    if not cmd_parts:
        raise ValueError("Empty command")

    operator = cmd_parts[0].lstrip("-").split(",")[0].lower()

    # Get the appropriate parser
    parser_class = PARSER_REGISTRY.get(operator)
    if parser_class is None:
        raise ValueError(f"No parser available for command: {operator}")

    parser = parser_class()
    return parser.parse(output)


def get_supported_structured_commands() -> frozenset[str]:
    """
    Get the set of commands that support structured output parsing.

    Returns:
        Frozenset of command names that can be parsed into dictionaries.

    Example:
        >>> commands = get_supported_structured_commands()
        >>> "griddes" in commands
        True
    """
    return frozenset(PARSER_REGISTRY.keys())
