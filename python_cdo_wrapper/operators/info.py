"""Information operators for CDO."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from ..types.results import (
    GriddesResult,
    InfoResult,
    PartabResult,
    SinfoResult,
    VlistResult,
    ZaxisdesResult,
)
from .base import CDOOperator


class SinfoOperator(CDOOperator[SinfoResult]):
    """sinfo operator - Dataset summary information."""

    name = "sinfo"
    category = "info"
    returns_data = False

    def build_command(self, input: str | Path) -> str:
        """
        Build sinfo command.

        Args:
            input: Input file path.

        Returns:
            CDO command string.
        """
        return f"-sinfo {input}"

    def parse_output(self, output: str) -> SinfoResult:
        """
        Parse sinfo output.

        Args:
            output: Raw CDO output.

        Returns:
            Parsed SinfoResult.
        """
        from ..parsers.info import SinfoParser

        parser = SinfoParser()
        return parser.parse(output)


class InfoOperator(CDOOperator[InfoResult]):
    """info operator - Timestep-by-timestep statistics."""

    name = "info"
    category = "info"
    returns_data = False

    def build_command(self, input: str | Path) -> str:
        """
        Build info command.

        Args:
            input: Input file path.

        Returns:
            CDO command string.
        """
        return f"-info {input}"

    def parse_output(self, output: str) -> InfoResult:
        """
        Parse info output.

        Args:
            output: Raw CDO output.

        Returns:
            Parsed InfoResult.
        """
        from ..parsers.info import InfoParser

        parser = InfoParser()
        return parser.parse(output)


class GriddesOperator(CDOOperator[GriddesResult]):
    """griddes operator - Grid description."""

    name = "griddes"
    category = "info"
    returns_data = False

    def build_command(self, input: str | Path) -> str:
        """
        Build griddes command.

        Args:
            input: Input file path.

        Returns:
            CDO command string.
        """
        return f"-griddes {input}"

    def parse_output(self, output: str) -> GriddesResult:
        """
        Parse griddes output.

        Args:
            output: Raw CDO output.

        Returns:
            Parsed GriddesResult.
        """
        from ..parsers.grid import GriddesParser

        parser = GriddesParser()
        return parser.parse(output)


class ZaxisdesOperator(CDOOperator[ZaxisdesResult]):
    """zaxisdes operator - Vertical axis description."""

    name = "zaxisdes"
    category = "info"
    returns_data = False

    def build_command(self, input: str | Path) -> str:
        """
        Build zaxisdes command.

        Args:
            input: Input file path.

        Returns:
            CDO command string.
        """
        return f"-zaxisdes {input}"

    def parse_output(self, output: str) -> ZaxisdesResult:
        """
        Parse zaxisdes output.

        Args:
            output: Raw CDO output.

        Returns:
            Parsed ZaxisdesResult.
        """
        from ..parsers.grid import ZaxisdesParser

        parser = ZaxisdesParser()
        return parser.parse(output)


class VlistOperator(CDOOperator[VlistResult]):
    """vlist operator - Variable list with metadata."""

    name = "vlist"
    category = "info"
    returns_data = False

    def build_command(self, input: str | Path) -> str:
        """
        Build vlist command.

        Args:
            input: Input file path.

        Returns:
            CDO command string.
        """
        return f"-vlist {input}"

    def parse_output(self, output: str) -> VlistResult:
        """
        Parse vlist output.

        Args:
            output: Raw CDO output.

        Returns:
            Parsed VlistResult.
        """
        from ..parsers.info import VlistParser

        parser = VlistParser()
        return parser.parse(output)


class PartabOperator(CDOOperator["PartabResult"]):
    """partab operator - Parameter table information."""

    name = "partab"
    category = "info"
    returns_data = False

    def build_command(self, input: str | Path) -> str:
        """
        Build partab command.

        Args:
            input: Input file path.

        Returns:
            CDO command string.
        """
        return f"-partab {input}"

    def parse_output(self, output: str) -> PartabResult:
        """
        Parse partab output.

        Args:
            output: Raw CDO output.

        Returns:
            Parsed PartabResult.
        """
        from ..parsers.info import PartabParser

        parser = PartabParser()
        return parser.parse(output)
