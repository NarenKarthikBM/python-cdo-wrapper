"""Base class for all CDO operators."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class OperatorSpec:
    """
    Specification for a single CDO operator fragment.

    This immutable dataclass represents one operator in a CDO pipeline,
    along with its arguments. It can convert itself to CDO command syntax.

    Example:
        >>> spec = OperatorSpec("selname", args=("tas", "pr"))
        >>> spec.to_cdo_fragment()
        '-selname,tas,pr'
    """

    name: str
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] = field(default_factory=dict)

    def to_cdo_fragment(self) -> str:
        """
        Convert operator spec to CDO command fragment.

        Returns:
            CDO command fragment (e.g., '-selname,tas,pr')

        Example:
            >>> OperatorSpec("yearmean").to_cdo_fragment()
            '-yearmean'
            >>> OperatorSpec("selname", ("tas", "pr")).to_cdo_fragment()
            '-selname,tas,pr'
            >>> OperatorSpec("sellevel", (1000, 850, 500)).to_cdo_fragment()
            '-sellevel,1000,850,500'
        """
        if self.args:
            args_str = ",".join(str(arg) for arg in self.args)
            return f"-{self.name},{args_str}"
        return f"-{self.name}"

    def __repr__(self) -> str:
        """Return string representation."""
        if self.args:
            args_repr = ", ".join(repr(arg) for arg in self.args)
            return f"OperatorSpec('{self.name}', ({args_repr}))"
        return f"OperatorSpec('{self.name}')"


class CDOOperator(ABC, Generic[T]):
    """
    Abstract base class for all CDO operators.

    Each operator implementation should inherit from this class and implement
    the required abstract methods. The type parameter T represents the return
    type of the operator (e.g., xr.Dataset, str, SinfoResult, etc.).

    Attributes:
        name: CDO operator name (e.g., "yearmean", "selname").
        category: Operator category (e.g., "statistics", "selection").
        returns_data: True if operator produces NetCDF/data output, False for text.

    Example:
        >>> class YearmeanOperator(CDOOperator[xr.Dataset]):
        ...     name = "yearmean"
        ...     category = "statistics"
        ...     returns_data = True
        ...
        ...     def build_command(self, input: str) -> str:
        ...         return f"-yearmean {input}"
        ...
        ...     def validate_params(self, **kwargs) -> None:
        ...         pass  # No parameters to validate
        ...
        ...     def parse_output(self, output: str) -> xr.Dataset:
        ...         raise NotImplementedError("Data operators don't parse text")
    """

    name: str
    category: str
    returns_data: bool = True

    @abstractmethod
    def build_command(self, input: str | Path) -> str:
        """
        Build the CDO command string from input file.

        Args:
            input: Path to input file

        Returns:
            Complete CDO command string (without 'cdo' prefix).

        Example:
            >>> op = SinfoOperator()
            >>> op.build_command("data.nc")
            'sinfo data.nc'
        """
        pass

    def validate_params(self, *args: object, **kwargs: object) -> None:
        """
        Validate input parameters before execution.

        Override this method to implement custom validation logic.
        Raise CDOValidationError if parameters are invalid.

        Args:
            *args: Positional arguments to validate.
            **kwargs: Keyword arguments to validate.

        Raises:
            CDOValidationError: If parameters are invalid.

        Example:
            >>> def validate_params(self, *names, **kwargs):
            ...     if not names:
            ...         raise CDOValidationError(
            ...             "At least one variable name required",
            ...             parameter="names",
            ...             value=names,
            ...             expected="Non-empty tuple of strings"
            ...         )
        """
        pass

    @abstractmethod
    def parse_output(self, output: str) -> T:
        """
        Parse the command output into structured data.

        For data operators (returns_data=True), this method typically raises
        NotImplementedError since xarray handles the output directly.

        For info operators (returns_data=False), this method should parse
        the text output into structured data.

        Args:
            output: Raw text output from CDO command.

        Returns:
            Parsed output in the appropriate type.

        Raises:
            CDOParseError: If output cannot be parsed.
            NotImplementedError: For data operators.

        Example:
            >>> def parse_output(self, output: str) -> SinfoResult:
            ...     parser = SinfoParser()
            ...     return parser.parse(output)
        """
        pass
