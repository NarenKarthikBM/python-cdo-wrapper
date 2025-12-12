"""Base class for all CDO output parsers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class CDOParser(ABC, Generic[T]):
    """
    Abstract base class for CDO output parsers.

    Each parser implementation should inherit from this class and implement
    the parse method. The type parameter T represents the return type of
    the parser (e.g., SinfoResult, GridInfo, list[str], etc.).

    Example:
        >>> class GriddesParser(CDOParser[GridInfo]):
        ...     def parse(self, output: str) -> GridInfo:
        ...         # Parse griddes output
        ...         lines = output.strip().split("\\n")
        ...         # ... parsing logic ...
        ...         return GridInfo(...)
    """

    @abstractmethod
    def parse(self, output: str) -> T:
        """
        Parse CDO text output into structured data.

        Args:
            output: Raw text output from a CDO command.

        Returns:
            Parsed data in the appropriate structured format.

        Raises:
            CDOParseError: If the output cannot be parsed.

        Example:
            >>> parser = SinfoParser()
            >>> result = parser.parse(cdo_output)
            >>> print(result.var_names)
            ['tas', 'pr', 'psl']
        """
        pass
