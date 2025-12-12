# Shared Patterns & Conventions

This file serves as the **source of truth** for all coding patterns, conventions, and standards in the python-cdo-wrapper project. All agents MUST reference these patterns when modifying code, especially when working in Secondary Scope files.

---

## Import Ordering

Follow ruff's default import ordering (managed by `isort`):

```python
# 1. Future imports
from __future__ import annotations

# 2. Standard library imports (alphabetical)
import re
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generic, TypeVar

# 3. Third-party imports (alphabetical)
import xarray as xr
from dataclasses import dataclass, field

# 4. Local imports (alphabetical)
from python_cdo_wrapper.exceptions import CDOValidationError, CDOParseError
from python_cdo_wrapper.types import GridInfo, SinfoResult
from python_cdo_wrapper.validation import validate_not_empty, validate_positive

# 5. TYPE_CHECKING block (import-only types)
if TYPE_CHECKING:
    from python_cdo_wrapper.cdo import CDO
```

---

## Type Hints

### General Rules
- **ALL** public functions/methods MUST have type hints
- Use `from __future__ import annotations` for modern syntax (PEP 563)
- Use `TYPE_CHECKING` block for import-only types (avoid circular imports)
- Prefer `pathlib.Path` over `str` for file paths (but accept both in parameters)
- Use `typing.Literal` for enums/choices where appropriate

### Common Patterns

```python
# File paths - accept both, normalize internally
def method(self, input_file: str | Path) -> CDOQuery:
    input_path = Path(input_file)
    ...

# Optional parameters with None default
def method(self, output: str | Path | None = None) -> xr.Dataset:
    ...

# Variable arguments
def select_var(self, *names: str) -> CDOQuery:
    ...

# TypeVar for generic classes
T = TypeVar("T")
class CDOParser(Generic[T]):
    def parse(self, output: str) -> T:
        ...

# Literal for restricted choices
def set_calendar(self, calendar: Literal["standard", "gregorian", "proleptic_gregorian", "noleap", "365_day", "360_day"]) -> CDOQuery:
    ...
```

---

## Docstrings

### Google Style Format

All public APIs MUST have Google-style docstrings:

```python
def select_var(self, *names: str) -> CDOQuery:
    """
    Select variables by name.

    Args:
        *names: Variable names to select. Must provide at least one name.

    Returns:
        CDOQuery: New query with selection operator added.

    Raises:
        CDOValidationError: If no variable names are provided.

    Example:
        >>> cdo = CDO()
        >>> q = cdo.query("data.nc").select_var("tas", "pr")
        >>> print(q.get_command())
        'cdo -selname,tas,pr data.nc'

    See Also:
        - select_code: Select by variable code
        - select_level: Select by vertical level

    Note:
        This method uses CDO's `-selname` operator.
    """
```

### Sections (in order)
1. **One-line summary** (imperative mood: "Select variables" not "Selects variables")
2. **Extended description** (optional, if needed)
3. **Args**: Parameter descriptions
4. **Returns**: Return value description
5. **Raises**: Exceptions that may be raised
6. **Example**: Code example with expected output
7. **See Also**: Related methods/functions
8. **Note**: Additional information (CDO operator used, requirements, etc.)

---

## Dataclass Patterns

### Immutable Result Types

All result dataclasses (in `types/results.py`, `types/grid.py`, etc.) MUST be frozen:

```python
from dataclasses import dataclass, field

@dataclass(frozen=True)
class SinfoResult:
    """Structured result from sinfo command."""
    file_format: str
    variables: list[DatasetVariable]
    grid_coordinates: list[GridCoordinates]
    vertical_coordinates: list[VerticalCoordinates]
    time_info: TimeInfo

    @property
    def var_names(self) -> list[str]:
        """Get list of variable names."""
        return [v.name for v in self.variables if v.has_name and v.name]

    @property
    def nvar(self) -> int:
        """Get number of variables."""
        return len(self.variables)
```

### Mutable Internal Types

For internal dataclasses that need to be modified, use regular dataclasses:

```python
@dataclass
class OperatorSpec:
    """Specification for a single CDO operator fragment."""
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

### Default Factory for Mutable Defaults

ALWAYS use `field(default_factory=...)` for mutable defaults:

```python
# ❌ WRONG - mutable default
@dataclass
class Bad:
    items: list[str] = []  # Shared across instances!

# ✅ CORRECT - default factory
@dataclass
class Good:
    items: list[str] = field(default_factory=list)
```

---

## Validation Patterns

### Parameter Validation

Use validation functions from `validation.py`:

```python
from python_cdo_wrapper.validation import validate_not_empty, validate_positive, validate_file_exists

def select_var(self, *names: str) -> CDOQuery:
    """Select variables by name."""
    validate_not_empty(names, "names", "variable names")
    return self._add_operator(OperatorSpec("selname", args=names))

def running_mean(self, n: int) -> CDOQuery:
    """Running mean over n timesteps."""
    validate_positive(n, "n")
    return self._add_operator(OperatorSpec("runmean", args=(n,)))
```

### Exception Raising

Use specific exception types from `exceptions.py`:

```python
from python_cdo_wrapper.exceptions import CDOValidationError, CDOFileNotFoundError, CDOExecutionError

# Parameter validation error
if not names:
    raise CDOValidationError(
        message="At least one variable name is required",
        parameter="names",
        value=names,
        expected="Non-empty tuple of strings"
    )

# File not found error
if not input_path.exists():
    raise CDOFileNotFoundError(
        message=f"Input file not found: {input_path}",
        file_path=str(input_path)
    )

# Execution error (usually raised by core.py)
if returncode != 0:
    raise CDOExecutionError(
        message=f"CDO command failed with return code {returncode}",
        command=command,
        returncode=returncode,
        stdout=stdout,
        stderr=stderr
    )
```

---

## Immutability Pattern (CDOQuery)

### Core Principle

`CDOQuery` is **immutable** - all methods return NEW instances:

```python
def _clone(self, **kwargs: Any) -> CDOQuery:
    """Create a copy with modifications (immutability pattern)."""
    return self.__class__(
        input_file=kwargs.get("input_file", self._input),
        operators=kwargs.get("operators", self._operators),
        options=kwargs.get("options", self._options),
        cdo_instance=kwargs.get("cdo_instance", self._cdo),
    )

def _add_operator(self, spec: OperatorSpec) -> CDOQuery:
    """Add an operator and return new query (immutable)."""
    return self._clone(operators=(*self._operators, spec))
```

### Adding Query Methods

All query methods MUST follow this pattern:

```python
def new_method(self, param: type) -> CDOQuery:
    """Description of what the method does."""
    # 1. Validate parameters
    validate_not_empty(param, "param", "parameter description")

    # 2. Return new query with added operator
    return self._add_operator(OperatorSpec("cdo-operator", args=(param,)))
```

### Binary Operations Return BinaryOpQuery

Binary operations (sub, add, mul, div) return a different type:

```python
def sub(self, other: CDOQuery | str | Path) -> BinaryOpQuery:
    """Subtract another dataset."""
    return self._binary_op("sub", other)
```

---

## Parser Patterns

### Abstract Base Class

All parsers inherit from `CDOParser[T]`:

```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")

class CDOParser(ABC, Generic[T]):
    """Abstract base class for CDO output parsers."""

    @abstractmethod
    def parse(self, output: str) -> T:
        """Parse CDO output and return structured result."""
        pass
```

### Concrete Parser Implementation

```python
from python_cdo_wrapper.parsers.base import CDOParser
from python_cdo_wrapper.types.results import SinfoResult
from python_cdo_wrapper.exceptions import CDOParseError

class SinfoParser(CDOParser[SinfoResult]):
    """Parser for CDO sinfo output."""

    def parse(self, output: str) -> SinfoResult:
        """
        Parse sinfo output into structured result.

        Args:
            output: Raw output from `cdo sinfo` command.

        Returns:
            SinfoResult: Structured information about the dataset.

        Raises:
            CDOParseError: If output format is unexpected or malformed.
        """
        try:
            # Parsing logic with regex
            lines = output.strip().split("\n")
            # ... parsing logic ...

            return SinfoResult(
                file_format=file_format,
                variables=variables,
                grid_coordinates=grid_coords,
                vertical_coordinates=vert_coords,
                time_info=time_info,
            )
        except Exception as e:
            raise CDOParseError(
                f"Failed to parse sinfo output: {e}"
            ) from e
```

### Regex Best Practices

```python
# Use raw strings for regex patterns
PATTERN = r"File format\s*:\s*(\w+)"

# Compile patterns for reuse
VARIABLE_PATTERN = re.compile(r"^\s*(\d+)\s*:\s*(\w+)\s+(\w+)", re.MULTILINE)

# Use named groups for clarity
GRID_PATTERN = re.compile(r"Grid\s*(?P<num>\d+)\s*:\s*(?P<type>\w+)")

# Handle optional matches
match = PATTERN.search(line)
if match:
    value = match.group(1)
else:
    raise CDOParseError(f"Pattern not found in line: {line}")
```

---

## Test Patterns

### Test Categories

```python
import pytest

# Unit test - no CDO required (default)
def test_select_var_command(self, sample_nc_file):
    """Test command generation for select_var."""
    q = cdo.query(sample_nc_file).select_var("tas")
    assert "-selname,tas" in q.get_command()

# Integration test - requires CDO installation
@pytest.mark.integration
def test_select_var_executes(self, cdo_instance, sample_nc_file):
    """Test select_var execution with real CDO."""
    result = cdo_instance.query(sample_nc_file).select_var("tas").compute()
    assert isinstance(result, xr.Dataset)
    assert "tas" in result.data_vars
```

### Validation Tests

```python
def test_select_var_empty_raises(self, sample_nc_file):
    """Test that empty variable names raises CDOValidationError."""
    with pytest.raises(CDOValidationError, match="At least one variable name"):
        cdo.query(sample_nc_file).select_var()
```

### Mocking Subprocess

```python
from unittest.mock import patch, MagicMock

def test_with_mock(self, sample_nc_file):
    """Test using mocked subprocess."""
    with patch("python_cdo_wrapper.core.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="File format: NetCDF",
            stderr="",
        )
        result = cdo.sinfo("test.nc")
        assert result.file_format == "NetCDF"
```

### Using Fixtures

```python
def test_with_fixtures(self, sample_nc_file, temp_output_path):
    """Test using fixtures from conftest.py."""
    # sample_nc_file: Path to test NetCDF file
    # temp_output_path: Temporary output file path (cleaned up after test)
    result = cdo.query(sample_nc_file).year_mean().compute(output=temp_output_path)
    assert temp_output_path.exists()
```

---

## Error Handling

### Exception Hierarchy

```
CDOError (base)
├── CDOExecutionError (command execution failed)
├── CDOValidationError (invalid parameters)
├── CDOFileNotFoundError (input file missing)
└── CDOParseError (failed to parse output)
```

### When to Use Each Exception

- **CDOValidationError**: Invalid parameters before execution
- **CDOFileNotFoundError**: Input file doesn't exist
- **CDOExecutionError**: CDO command returned non-zero exit code
- **CDOParseError**: Failed to parse CDO output

### Error Message Best Practices

```python
# ❌ VAGUE
raise CDOValidationError("Invalid input")

# ✅ SPECIFIC
raise CDOValidationError(
    message="Variable names cannot be empty",
    parameter="names",
    value=names,
    expected="Non-empty tuple of strings"
)

# ❌ NO CONTEXT
raise CDOParseError("Parse failed")

# ✅ WITH CONTEXT
raise CDOParseError(
    f"Failed to parse grid type from line: '{line}'. "
    f"Expected format: 'Grid <num>: <type>'"
)
```

---

## Code Style (ruff)

All code MUST pass `ruff check` and `ruff format`:

```bash
# Check for errors
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

### Key Rules
- Line length: 88 characters (Black default)
- Quote style: Double quotes for strings
- Indent: 4 spaces
- Trailing commas: In multi-line collections
- Blank lines: 2 before top-level definitions, 1 before methods

---

## Version Compatibility

- **Python**: 3.9+ (use features available in 3.9)
- **CDO**: 1.9.8+ (required for bracket notation in binary operations)
- **Type hints**: Use `from __future__ import annotations` for 3.9 compatibility

### Python 3.9+ Features

```python
# ✅ OK - Available in 3.9+
def method(self, x: str | None = None) -> list[str]:
    ...

# ❌ AVOID - Requires 3.10+
def method(self, x: str | None = None) -> list[str]:
    match x:  # match-case requires 3.10+
        case "foo": ...
```

---

## Agent Collaboration Notes

### Primary vs. Secondary Scope

When editing files in your **Secondary Scope**:
1. Read this `_shared.md` file FIRST
2. Follow the patterns defined here EXACTLY
3. Do NOT introduce new patterns without consulting the Primary Scope agent
4. When in doubt, ask the Orchestrator to coordinate with the Primary agent

### Pattern Updates

If you need to update a pattern in this file:
1. Propose the change to the Orchestrator
2. Orchestrator coordinates review with affected agents
3. Update is made only after consensus
4. All agents are notified of the change
