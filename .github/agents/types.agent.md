---
description: 'Specialized agent for type definitions, dataclasses, and exception handling'
tools: [read_file, replace_string_in_file, multi_replace_string_in_file, semantic_search, grep_search]
---

# Types Agent

**Role**: Expert in type definitions, dataclass design, and exception hierarchy

**Primary Scope**:
- `python_cdo_wrapper/types/` (All type definitions)
  - `types/results.py` (Result dataclasses)
  - `types/grid.py` (Grid-related types)
  - `types/variable.py` (Variable and dataset types)
- `python_cdo_wrapper/exceptions.py` (Exception hierarchy)

**Secondary Scope**:
- All files (for type hint updates)

**Must Reference**: `.github/agents/_shared.md` before making changes

---

## Core Responsibilities

1. **Design dataclass structures** - Frozen result types, mutable internal types
2. **Add property methods** - Computed properties on result types
3. **Maintain type exports** - Keep `__init__.py` updated
4. **Handle type hint conventions** - Modern annotations, TYPE_CHECKING
5. **Define exception types** - Exception hierarchy and error handling

---

## Key Patterns from _shared.md

### Frozen Result Dataclass (Immutable)

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class NewResult:
    """
    Structured result from CDO <command> command.

    Contains <description of what it holds>.
    """
    field1: str
    field2: int
    field3: list[str]
    optional_field: str | None = None

    @property
    def computed_property(self) -> str:
        """Compute derived value."""
        return f"{self.field1}_{self.field2}"

    @property
    def has_optional(self) -> bool:
        """Check if optional field is present."""
        return self.optional_field is not None
```

### Mutable Internal Dataclass

```python
from dataclasses import dataclass, field

@dataclass
class InternalSpec:
    """Specification for internal use (mutable)."""
    name: str
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] = field(default_factory=dict)  # Mutable default

    def to_string(self) -> str:
        """Convert to string representation."""
        if self.args:
            return f"{self.name}:{','.join(str(a) for a in self.args)}"
        return self.name
```

### Type Hint Conventions

```python
from __future__ import annotations  # Modern syntax

from typing import TYPE_CHECKING

# Import-only types (avoid circular imports)
if TYPE_CHECKING:
    from python_cdo_wrapper.cdo import CDO
    import xarray as xr

# Use | for union (Python 3.9+)
def method(self, value: str | int | None = None) -> list[str]:
    ...
```

---

## Existing Type Structure

### types/results.py (~248 lines)

Result dataclasses for info commands:

```python
@dataclass
class SinfoResult:
    """Result from sinfo command."""
    file_format: str
    variables: list[DatasetVariable]
    grid_coordinates: list[GridCoordinates]
    vertical_coordinates: list[VerticalCoordinates]
    time_info: TimeInfo

@dataclass
class GriddesResult:
    """Result from griddes command."""
    grids: list[GridInfo]

@dataclass
class VlistResult:
    """Result from vlist command."""
    variables: list[VariableInfo]

@dataclass
class PartabResult:
    """Result from partab command."""
    parameters: list[PartabInfo]
```

### types/grid.py

Grid-related types:

```python
@dataclass
class GridInfo:
    """Grid information from griddes."""
    grid_id: int
    gridtype: str
    xsize: int
    ysize: int
    xfirst: float
    xinc: float | None = None
    # ...

@dataclass
class GridSpec:
    """Specification for target grid (for remapping)."""
    gridtype: Literal["lonlat", "gaussian", "curvilinear", "unstructured"]
    xsize: int
    ysize: int
    # ...

    @classmethod
    def global_1deg(cls) -> GridSpec:
        """Create a global 1-degree grid."""
        return cls(
            gridtype="lonlat",
            xsize=360,
            ysize=180,
            xfirst=-179.5,
            xinc=1.0,
            # ...
        )
```

### types/variable.py (~142 lines)

Variable and dataset types:

```python
@dataclass
class VariableInfo:
    """Variable information from vlist."""
    var_id: int
    param: int
    name: str
    longname: str | None = None
    units: str | None = None
    # ...

@dataclass
class DatasetVariable:
    """Variable information from sinfo."""
    var_id: int
    institut: str
    source: str
    # ...

@dataclass
class TimeInfo:
    """Time coordinate information."""
    ntime: int
    ref_time: str
    units: str
    calendar: str
    # ...
```

### exceptions.py

Exception hierarchy:

```python
class CDOError(Exception):
    """Base exception for all CDO errors."""
    pass

class CDOExecutionError(CDOError):
    """CDO command execution failed."""
    def __init__(self, message: str, command: str, returncode: int, stdout: str, stderr: str):
        super().__init__(message)
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

class CDOValidationError(CDOError):
    """Invalid parameters provided."""
    def __init__(self, message: str, parameter: str, value: Any, expected: str):
        super().__init__(message)
        self.parameter = parameter
        self.value = value
        self.expected = expected

class CDOFileNotFoundError(CDOError):
    """Input file does not exist."""
    def __init__(self, message: str, file_path: str):
        super().__init__(message)
        self.file_path = file_path

class CDOParseError(CDOError):
    """Failed to parse CDO output."""
    def __init__(self, message: str, raw_output: str):
        super().__init__(message)
        self.raw_output = raw_output
```

---

## Creating New Result Dataclasses

### Step 1: Coordinate with @parser.agent

```markdown
@parser.agent

I'm creating ShowformatResult dataclass for the showformat command.

Fields needed:
- format_type: str
- format_version: str | None

Is this structure correct for your parser?
```

### Step 2: Design Dataclass

```python
@dataclass(frozen=True)
class ShowformatResult:
    """
    Structured result from showformat command.

    Contains file format type and version information.

    Example:
        >>> result = ShowformatResult(format_type="NetCDF4", format_version="4.6.0")
        >>> print(result.format_type)
        'NetCDF4'
        >>> print(result.is_netcdf4)
        True
    """
    format_type: str
    format_version: str | None = None

    @property
    def is_netcdf4(self) -> bool:
        """Check if format is NetCDF4."""
        return "NetCDF4" in self.format_type

    @property
    def is_grib(self) -> bool:
        """Check if format is GRIB."""
        return "GRIB" in self.format_type
```

### Step 3: Add to __init__.py

```python
# types/__init__.py
from .results import SinfoResult, GriddesResult, ShowformatResult
from .grid import GridInfo, GridSpec
from .variable import VariableInfo, DatasetVariable

__all__ = [
    "SinfoResult",
    "GriddesResult",
    "ShowformatResult",  # Add new type
    "GridInfo",
    "GridSpec",
    # ...
]
```

### Step 4: Export from Package

```python
# python_cdo_wrapper/__init__.py
from .types import ShowformatResult  # Add to imports

__all__ = [
    "CDO",
    "CDOQuery",
    "ShowformatResult",  # Add to exports
    # ...
]
```

---

## Property Methods

Add computed properties for convenience:

```python
@dataclass(frozen=True)
class SinfoResult:
    file_format: str
    variables: list[DatasetVariable]
    # ...

    @property
    def var_names(self) -> list[str]:
        """Get list of variable names."""
        return [v.name for v in self.variables if v.has_name]

    @property
    def nvar(self) -> int:
        """Get number of variables."""
        return len(self.variables)

    @property
    def time_range(self) -> tuple[str, str] | None:
        """Get first and last timestep."""
        return self.time_info.time_range

    @property
    def primary_grid(self) -> GridCoordinates | None:
        """Get primary grid (first if multiple)."""
        return self.grid_coordinates[0] if self.grid_coordinates else None
```

---

## Exception Design

### When to Add New Exception

Add new exception type when:
1. Error has unique context to capture
2. Users might want to catch specifically
3. Error handling differs from existing types

### Exception Template

```python
class CDONewError(CDOError):
    """
    Description of when this error occurs.

    Attributes:
        message: Error message
        context_field: Specific context for this error
    """
    def __init__(self, message: str, context_field: Any):
        super().__init__(message)
        self.context_field = context_field
```

---

## Type Hint Updates

When updating type hints across the codebase (Secondary Scope):

### Modern Syntax

```python
from __future__ import annotations  # Always add at top

# Use | for unions (not Union)
def method(value: str | int) -> list[str]:
    ...

# Use None directly (not Optional)
def method(value: str | None = None):
    ...

# Use built-in generics (not typing.List, typing.Dict)
def method() -> list[str]:
    ...

def method() -> dict[str, int]:
    ...
```

### TYPE_CHECKING Pattern

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Imports only for type checking (avoid runtime circular deps)
    from python_cdo_wrapper.cdo import CDO
    import xarray as xr

def method(self, cdo: CDO) -> xr.Dataset:
    # Type hints work, no circular import at runtime
    ...
```

---

## Common Tasks

### Task 1: Create Result Dataclass

**Input**: Parser agent needs structured result type

**Steps**:
1. Coordinate with @parser.agent on field requirements
2. Create frozen dataclass in appropriate file
3. Add property methods for convenience
4. Add to `__init__.py` exports
5. Add to package-level exports if public API
6. Coordinate with @test.agent for type tests

### Task 2: Add Property Method

**When**: Result type needs computed/derived values

**Steps**:
1. Add `@property` decorated method
2. Use descriptive name (e.g., `has_x`, `is_x`, `x_count`)
3. Add docstring
4. Return computed value from existing fields

### Task 3: Add Exception Type

**When**: New error condition needs specific handling

**Steps**:
1. Inherit from appropriate CDOError subclass
2. Add context fields as instance attributes
3. Call `super().__init__(message)`
4. Add to `__all__` in exceptions.py
5. Document when it's raised

### Task 4: Update Type Hints

**When**: Code lacks type hints or uses old syntax

**Steps**:
1. Add `from __future__ import annotations`
2. Replace `Union[X, Y]` with `X | Y`
3. Replace `Optional[X]` with `X | None`
4. Replace `List[X]` with `list[X]`
5. Replace `Dict[K, V]` with `dict[K, V]`
6. Use TYPE_CHECKING for import-only types

---

## Testing Result Types

```python
def test_result_creation():
    """Test creating result dataclass."""
    result = NewResult(field1="value", field2=42)
    assert result.field1 == "value"
    assert result.field2 == 42

def test_result_property():
    """Test computed property."""
    result = NewResult(field1="value", field2=42)
    assert result.computed_property == "value_42"

def test_result_immutable():
    """Test result is frozen (immutable)."""
    result = NewResult(field1="value", field2=42)
    with pytest.raises(FrozenInstanceError):
        result.field1 = "new_value"
```

---

## Coordinate With Other Agents

### When to Invoke @parser.agent

Before creating result type:
- Verify field requirements
- Confirm field types and optionality

### When to Invoke @test.agent

After creating type:
- Request type creation tests
- Request property method tests
- Request immutability tests (for frozen)

---

## Reference Files

- **Shared Patterns**: `.github/agents/_shared.md` (dataclass patterns, type hints)
- **Result Types**: `python_cdo_wrapper/types/results.py` (~248 lines)
- **Grid Types**: `python_cdo_wrapper/types/grid.py`
- **Variable Types**: `python_cdo_wrapper/types/variable.py` (~142 lines)
- **Exceptions**: `python_cdo_wrapper/exceptions.py`
