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
            Dictionary containing dataset information.
        """
        info: dict[str, Any] = {"variables": [], "metadata": {}}
        lines = output.strip().split("\n")

        current_section = None
        for line in lines:
            line_stripped = line.strip()

            # Detect file format
            if "File format" in line:
                info["metadata"]["format"] = line.split(":")[-1].strip()
                continue

            # Detect variable table header (skip -1 line)
            if "-1 :" in line_stripped or "Code" in line:
                current_section = "variables"
                continue

            # Detect grid section
            if "Grid coordinates" in line:
                current_section = "grid"
                continue

            # Parse variable lines in the variables section
            if current_section == "variables" and re.match(r"^\s*\d+\s*:", line):
                var_info = self._parse_variable_line(line_stripped)
                if var_info:
                    info["variables"].append(var_info)

        return info

    @staticmethod
    def _parse_variable_line(line: str) -> dict[str, Any] | None:
        """Parse a single variable line from sinfo output.

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


class ShowattsglobParser(CDOParser):
    """Parser for showattsglob output."""

    def parse(self, output: str) -> dict[str, Any]:
        """
        Parse showattsglob output into a dictionary.

        Args:
            output: Raw showattsglob output text.

        Returns:
            Dictionary containing global attributes.
        """
        attributes: dict[str, Any] = {}
        lines = output.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                attributes[key] = value

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
    "showattsglob": ShowattsglobParser,
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
