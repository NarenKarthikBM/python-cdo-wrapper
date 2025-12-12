---
applyTo: "python_cdo_wrapper/parsers/**/*.py,python_cdo_wrapper/types/results.py"
---

# Parser Development Guide

This instruction guide covers how to create new parsers for CDO text output.

## Parser Architecture

```
CDOParser[T]  (Abstract Base)
    ├── SinfoParser -> SinfoResult
    ├── InfoParser -> InfoResult
    ├── GriddesParser -> GriddesResult
    ├── ZaxisdesParser -> ZaxisdesResult
    ├── VlistParser -> VlistResult
    └── PartabParser -> PartabResult
```

## Creating a New Parser

### Step 1: Define Result Dataclass

In `python_cdo_wrapper/types/results.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass  # Import types only needed for type checking


@dataclass(frozen=True)
class NewCommandResult:
    """
    Structured result from CDO's newcommand.

    Attributes:
        field1: Description of field1
        field2: Description of field2
    """

    field1: str
    field2: int
    # ... more fields

    @property
    def computed_property(self) -> str:
        """Compute derived value from fields."""
        return f"{self.field1}_{self.field2}"
```

**Key Points**:
- Use `@dataclass(frozen=True)` for immutability
- Document all fields in docstring
- Add `@property` methods for computed values
- Keep dataclass simple (no complex logic)

### Step 2: Create Parser Class

In `python_cdo_wrapper/parsers/category.py`:

```python
from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .base import CDOParser
from ..types.results import NewCommandResult

if TYPE_CHECKING:
    pass


class NewCommandParser(CDOParser[NewCommandResult]):
    """
    Parser for CDO's newcommand output.

    Example Input:
    ```
    Field1 : value1
    Field2 : 123
    ```
    """

    def parse(self, output: str) -> NewCommandResult:
        """
        Parse newcommand output into structured result.

        Args:
            output: Raw text output from CDO newcommand

        Returns:
            NewCommandResult: Parsed structured result

        Raises:
            CDOParseError: If output format is unexpected
        """
        lines = output.strip().split('\n')

        # Initialize fields
        field1 = None
        field2 = None

        # Parse each line
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Match patterns
            if match := re.match(r'Field1\s*:\s*(.+)', line):
                field1 = match.group(1).strip()
            elif match := re.match(r'Field2\s*:\s*(\d+)', line):
                field2 = int(match.group(1))

        # Validate required fields
        if field1 is None:
            self._raise_parse_error(output, "Missing Field1")
        if field2 is None:
            self._raise_parse_error(output, "Missing Field2")

        return NewCommandResult(field1=field1, field2=field2)
```

## Parsing Patterns

### Pattern 1: Key-Value Pairs

```
Field1 : value1
Field2 : value2
```

```python
for line in lines:
    if ':' in line:
        key, value = line.split(':', 1)
        key = key.strip()
        value = value.strip()

        if key == "Field1":
            field1 = value
```

### Pattern 2: Tabular Data

```
Name    Type    Size
var1    float   1000
var2    int     500
```

```python
# Skip header
data_lines = [l for l in lines[1:] if l.strip()]

results = []
for line in data_lines:
    parts = line.split()
    if len(parts) >= 3:
        results.append({
            'name': parts[0],
            'type': parts[1],
            'size': int(parts[2])
        })
```

### Pattern 3: Sections with Headers

```
Section1:
  Item1: value1
  Item2: value2

Section2:
  Item3: value3
```

```python
current_section = None
sections = {}

for line in lines:
    if line.endswith(':') and not line.startswith(' '):
        # Section header
        current_section = line[:-1].strip()
        sections[current_section] = {}
    elif current_section and ':' in line:
        # Item in section
        key, value = line.strip().split(':', 1)
        sections[current_section][key.strip()] = value.strip()
```

### Pattern 4: Key=Value Blocks

```
gridtype = lonlat
xsize = 360
ysize = 180
```

```python
params = {}
for line in lines:
    if '=' in line:
        key, value = line.split('=', 1)
        params[key.strip()] = value.strip()
```

## Regex Best Practices

### Use Named Groups

```python
# ❌ BAD
match = re.match(r'(\w+)\s*:\s*(.+)', line)
field = match.group(1)
value = match.group(2)

# ✅ GOOD
match = re.match(r'(?P<field>\w+)\s*:\s*(?P<value>.+)', line)
field = match.group('field')
value = match.group('value')
```

### Use Walrus Operator

```python
# ❌ BAD
match = re.match(pattern, line)
if match:
    value = match.group(1)

# ✅ GOOD
if match := re.match(pattern, line):
    value = match.group(1)
```

### Compile Complex Patterns

```python
class NewCommandParser(CDOParser[NewCommandResult]):
    # Class-level compiled patterns
    FIELD_PATTERN = re.compile(r'Field\s*:\s*(?P<value>.+)')

    def parse(self, output: str) -> NewCommandResult:
        for line in lines:
            if match := self.FIELD_PATTERN.match(line):
                field = match.group('value')
```

## Error Handling

### Validate Required Fields

```python
# Check all required fields are present
if field1 is None:
    self._raise_parse_error(output, "Missing required field: field1")
```

### Handle Optional Fields

```python
# Optional field with default
field_optional = None
if match := re.match(r'OptionalField\s*:\s*(.+)', line):
    field_optional = match.group(1)

# Use default in dataclass
return NewCommandResult(
    field1=field1,
    field_optional=field_optional or "default_value"
)
```

### Provide Context in Errors

```python
try:
    value = int(match.group(1))
except ValueError as e:
    self._raise_parse_error(
        output,
        f"Expected integer for Field2, got: {match.group(1)}"
    )
```

## Testing Parsers

### Test Structure

```python
# tests/test_parsers/test_newcommand.py

import pytest
from python_cdo_wrapper.parsers.category import NewCommandParser
from python_cdo_wrapper.types.results import NewCommandResult
from python_cdo_wrapper.exceptions import CDOParseError


class TestNewCommandParser:
    @pytest.fixture
    def parser(self):
        return NewCommandParser()

    def test_parse_valid_output(self, parser):
        """Test parsing valid newcommand output."""
        output = """
        Field1 : value1
        Field2 : 123
        """

        result = parser.parse(output)

        assert isinstance(result, NewCommandResult)
        assert result.field1 == "value1"
        assert result.field2 == 123

    def test_parse_missing_field_raises(self, parser):
        """Test parsing with missing required field raises error."""
        output = "Field1 : value1"

        with pytest.raises(CDOParseError) as exc_info:
            parser.parse(output)

        assert "Field2" in str(exc_info.value)

    def test_parse_invalid_format_raises(self, parser):
        """Test parsing invalid format raises error."""
        output = "Invalid output format"

        with pytest.raises(CDOParseError):
            parser.parse(output)
```

### Sample Output Files

Create sample CDO output for testing:

```python
# tests/test_parsers/test_newcommand.py

SAMPLE_OUTPUT = """
Field1 : value1
Field2 : 123
Field3 : optional_value
"""

SAMPLE_OUTPUT_MINIMAL = """
Field1 : value1
Field2 : 123
"""
```

## Integration with CDO Class

After creating parser, add method to CDO class:

```python
# In python_cdo_wrapper/cdo.py

def newcommand(self, input_file: str | Path) -> NewCommandResult:
    """
    Get information from CDO's newcommand.

    Args:
        input_file: Input NetCDF file

    Returns:
        NewCommandResult: Structured result

    Example:
        >>> result = cdo.newcommand("data.nc")
        >>> print(result.field1)
        'value1'
    """
    output = self._execute_text_command(f"newcommand {input_file}")
    return NewCommandParser().parse(output)
```

## Documentation Updates

1. **Add to types/results.py docstring** listing result types
2. **Update CHANGELOG.md** with new command support
3. **Add README example** if significant feature

## Checklist

- [ ] Result dataclass created in types/results.py
- [ ] Parser class created in parsers/category.py
- [ ] Parser inherits from CDOParser[T]
- [ ] parse() method implemented
- [ ] Error handling with _raise_parse_error
- [ ] Test file created in tests/test_parsers/
- [ ] Test valid output parsing
- [ ] Test missing field error
- [ ] Test invalid format error
- [ ] Integration method added to CDO class
- [ ] CHANGELOG.md updated
- [ ] All tests pass

## Common Issues

### Issue: CDOParseError on valid output

**Cause**: Regex pattern too strict

**Fix**: Test regex with actual CDO output

### Issue: Fields None when expected

**Cause**: Pattern doesn't match actual format

**Fix**: Print `repr(line)` to see whitespace/formatting

### Issue: Integer parsing fails

**Cause**: Value contains non-digit characters

**Fix**: Strip whitespace, handle edge cases

```python
# ✅ GOOD
value_str = match.group(1).strip()
value = int(value_str)
```

## Reference

- **Parser base class**: `python_cdo_wrapper/parsers/base.py`
- **Existing parsers**: `python_cdo_wrapper/parsers/*.py`
- **Result types**: `python_cdo_wrapper/types/results.py`
- **Test examples**: `tests/test_parsers/*.py`
