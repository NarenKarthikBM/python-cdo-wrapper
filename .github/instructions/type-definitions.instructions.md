---
applyTo: "python_cdo_wrapper/types/**/*.py"
---

# Type Definitions Guide

This instruction guide covers type definition patterns in python-cdo-wrapper.

## Type System Overview

```
types/
├── __init__.py           # Public exports
├── results.py            # Frozen result dataclasses
├── grid.py               # Grid-related types
└── variable.py           # Variable-related types
```

## Frozen vs. Mutable Dataclasses

### Frozen (Immutable) - For Results

Use `frozen=True` for result types returned to users:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class ResultType:
    """
    Result from CDO command (immutable).

    Attributes:
        field1: Description of field1
        field2: Description of field2
    """

    field1: str
    field2: int

    @property
    def computed_property(self) -> str:
        """Compute derived value."""
        return f"{self.field1}_{self.field2}"
```

**When to use**:
- CDO command results (SinfoResult, GriddesResult, etc.)
- Public API return types
- Data that should never change after creation

### Mutable - For Internal Specs

Use plain dataclass for internal specifications:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OperatorSpec:
    """
    Internal specification for CDO operator (mutable).

    Attributes:
        name: CDO operator name
        args: Positional arguments
        kwargs: Keyword arguments
    """

    name: str
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] = field(default_factory=dict)

    def to_cdo_fragment(self) -> str:
        """Convert to CDO command fragment."""
        if self.args:
            args_str = ",".join(str(arg) for arg in self.args)
            return f"-{self.name},{args_str}"
        return f"-{self.name}"
```

**When to use**:
- Internal data structures (OperatorSpec)
- Builder patterns
- Data that needs to be modified

## Type Hint Conventions

### Modern Python 3.9+ Syntax

Always use modern syntax with `from __future__ import annotations`:

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from xarray import Dataset


def function(
    param1: str | None,              # Not Optional[str]
    param2: list[int],               # Not List[int]
    param3: dict[str, Any],          # Not Dict[str, Any]
    param4: tuple[int, ...],         # Variable-length tuple
    param5: Path | Dataset,          # Union of types
) -> str | None:                     # Return type
    pass
```

### TYPE_CHECKING Block

Import types only needed for type hints in `TYPE_CHECKING` block:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from xarray import Dataset
    # Avoid circular imports
    from .other_module import OtherType


@dataclass(frozen=True)
class MyType:
    path: Path                    # Type hint works
    dataset: Dataset | None       # Even though imported in TYPE_CHECKING
```

### Collection Types

Use built-in types (Python 3.9+):

```python
# ✅ GOOD - Modern syntax
def func(
    items: list[str],
    mapping: dict[str, int],
    coords: tuple[float, float],
    values: set[int],
) -> list[dict[str, Any]]:
    pass

# ❌ BAD - Old syntax
from typing import List, Dict, Tuple, Set

def func(
    items: List[str],
    mapping: Dict[str, int],
    coords: Tuple[float, float],
    values: Set[int],
) -> List[Dict[str, Any]]:
    pass
```

## Dataclass Patterns

### Basic Dataclass

```python
@dataclass(frozen=True)
class BasicType:
    """Simple dataclass with fields."""
    field1: str
    field2: int
    field3: float | None = None  # Optional with default
```

### Dataclass with Properties

```python
@dataclass(frozen=True)
class TypeWithProperties:
    """Dataclass with computed properties."""
    values: list[int]
    name: str

    @property
    def count(self) -> int:
        """Number of values."""
        return len(self.values)

    @property
    def average(self) -> float | None:
        """Average of values, or None if empty."""
        return sum(self.values) / len(self.values) if self.values else None
```

### Dataclass with Validation

```python
@dataclass(frozen=True)
class ValidatedType:
    """Dataclass with post-init validation."""
    value: int

    def __post_init__(self) -> None:
        """Validate fields after initialization."""
        if self.value < 0:
            raise ValueError(f"value must be non-negative, got {self.value}")
```

### Dataclass with Factory

```python
@dataclass(frozen=True)
class GridSpec:
    """Grid specification with factory methods."""
    gridtype: str
    xsize: int
    ysize: int
    xfirst: float
    xinc: float

    @classmethod
    def global_1deg(cls) -> GridSpec:
        """Create global 1-degree grid."""
        return cls(
            gridtype="lonlat",
            xsize=360,
            ysize=180,
            xfirst=-179.5,
            xinc=1.0
        )

    @classmethod
    def global_half_deg(cls) -> GridSpec:
        """Create global 0.5-degree grid."""
        return cls(
            gridtype="lonlat",
            xsize=720,
            ysize=360,
            xfirst=-179.75,
            xinc=0.5
        )
```

## Result Type Pattern

All CDO command results follow this pattern:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .variable import DatasetVariable
    from .grid import GridInfo


@dataclass(frozen=True)
class CommandResult:
    """
    Structured result from CDO command.

    Attributes:
        field1: Description
        field2: Description
        nested: Nested dataclass
    """

    field1: str
    field2: list[str]
    nested: GridInfo

    @property
    def summary(self) -> str:
        """Human-readable summary."""
        return f"{self.field1}: {len(self.field2)} items"

    @property
    def first_item(self) -> str | None:
        """First item in field2, or None."""
        return self.field2[0] if self.field2 else None
```

**Key elements**:
- `@dataclass(frozen=True)` for immutability
- Complete docstring with attributes
- Public fields (no underscore prefix)
- `@property` methods for computed values
- No complex logic (keep simple)

## Exception Types

Define exceptions in `exceptions.py`:

```python
from __future__ import annotations

from typing import Any


class CDOError(Exception):
    """Base exception for all CDO errors."""
    pass


class CDOValidationError(CDOError):
    """Invalid parameters provided."""

    def __init__(
        self,
        message: str,
        parameter: str,
        value: Any,
        expected: str
    ) -> None:
        super().__init__(message)
        self.parameter = parameter
        self.value = value
        self.expected = expected


class CDOExecutionError(CDOError):
    """CDO command execution failed."""

    def __init__(
        self,
        message: str,
        command: str,
        returncode: int,
        stdout: str,
        stderr: str
    ) -> None:
        super().__init__(message)
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
```

**Pattern**:
- Inherit from CDOError
- Store context as attributes
- Pass message to super().__init__()

## Type Aliases

Define type aliases for complex types:

```python
from __future__ import annotations

from pathlib import Path
from typing import TypeAlias

# Type alias for file paths
FilePath: TypeAlias = str | Path

# Type alias for operator arguments
OperatorArgs: TypeAlias = tuple[Any, ...]
```

## Generic Types

Use TypeVar for generic classes:

```python
from __future__ import annotations

from typing import Generic, TypeVar

T = TypeVar('T')


class CDOParser(Generic[T]):
    """Generic parser base class."""

    def parse(self, output: str) -> T:
        """Parse output into type T."""
        raise NotImplementedError
```

## Literal Types

Use Literal for fixed string choices:

```python
from typing import Literal

GridType = Literal["lonlat", "gaussian", "curvilinear", "unstructured"]

@dataclass(frozen=True)
class GridSpec:
    gridtype: GridType  # Must be one of 4 values
    xsize: int
```

## Documentation for Types

### Dataclass Docstring

```python
@dataclass(frozen=True)
class VariableInfo:
    """
    Information about a variable in a dataset.

    This represents metadata about a single variable, including
    its name, type, dimensions, and attributes.

    Attributes:
        name: Variable name (e.g., "tas", "pr")
        var_type: Data type (e.g., "float", "int")
        dimensions: List of dimension names
        n_values: Total number of values
        missing_value: Missing/fill value, or None

    Example:
        >>> var = VariableInfo(
        ...     name="tas",
        ...     var_type="float",
        ...     dimensions=["time", "lat", "lon"],
        ...     n_values=1000,
        ...     missing_value=-999.0
        ... )
        >>> print(var.name)
        'tas'
    """
    name: str
    var_type: str
    dimensions: list[str]
    n_values: int
    missing_value: float | None = None
```

## Testing Types

### Test Type Instantiation

```python
def test_result_type_creation():
    """Test creating result type."""
    result = ResultType(field1="value", field2=42)

    assert result.field1 == "value"
    assert result.field2 == 42


def test_result_type_immutable():
    """Test result type is immutable."""
    result = ResultType(field1="value", field2=42)

    with pytest.raises(AttributeError):
        result.field1 = "new_value"  # Should fail - frozen
```

### Test Properties

```python
def test_result_computed_property():
    """Test computed property returns correct value."""
    result = ResultType(field1="test", field2=42)

    assert result.computed_property == "test_42"
```

## Common Patterns

### Pattern: Optional Field with Default

```python
@dataclass(frozen=True)
class MyType:
    required_field: str
    optional_field: str | None = None
```

### Pattern: List Field with Default

```python
from dataclasses import field

@dataclass(frozen=True)
class MyType:
    items: list[str] = field(default_factory=list)
```

### Pattern: Nested Dataclass

```python
@dataclass(frozen=True)
class Outer:
    inner: Inner
    value: str

@dataclass(frozen=True)
class Inner:
    field: int
```

## Checklist

- [ ] Use `from __future__ import annotations`
- [ ] Use `frozen=True` for result types
- [ ] Use modern type syntax (| not Union, list not List)
- [ ] Import types only for hints in TYPE_CHECKING
- [ ] Add complete docstring with attributes
- [ ] Add @property methods for computed values
- [ ] Add tests for instantiation
- [ ] Add tests for immutability (frozen types)
- [ ] Export from types/__init__.py

## Reference

- **Result types**: `python_cdo_wrapper/types/results.py`
- **Grid types**: `python_cdo_wrapper/types/grid.py`
- **Variable types**: `python_cdo_wrapper/types/variable.py`
- **Exceptions**: `python_cdo_wrapper/exceptions.py`
