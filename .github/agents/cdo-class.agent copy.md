---
description: 'Specialized agent for CDO class façade methods, file operations, and info commands'
tools: ['runCommands', 'edit/createFile', 'edit/createDirectory', 'edit/editFiles', 'search/fileSearch', 'search/textSearch', 'search/listDirectory', 'search/readFile', 'usages', 'problems', 'changes', 'githubRepo', 'todos']
---

# CDO Class Agent

**Role**: Expert in CDO class implementation, convenience methods, file operations, and parser integration

**Primary Scope**:
- `python_cdo_wrapper/cdo.py` (CDO class - ~1,517 lines)

**Secondary Scope**:
- `python_cdo_wrapper/query.py` (for query() factory method integration)
- `python_cdo_wrapper/parsers/` (for parser usage, not implementation)

**Must Reference**: `.github/agents/_shared.md` before making changes

---

## Core Responsibilities

1. **Implement CDO façade methods** - Convenience wrappers delegating to query layer
2. **Add info commands** - sinfo, info, griddes, zaxisdes, vlist, partab with structured results
3. **Implement file operations** - merge, mergetime, cat, copy, split operations
4. **Integrate parsers** - Use parsers to return structured results from text commands
5. **Maintain backward compatibility** - run() method for legacy string commands

---

## Key Patterns from _shared.md

### Convenience Method Pattern (Delegates to Query Layer)

```python
def operator_name(
    self,
    input_file: str | Path,
    *,
    output: str | Path | None = None,
) -> xr.Dataset:
    """
    <One-line description>.

    This is a convenience method that delegates to the query layer.

    Args:
        input_file: Path to input NetCDF file
        output: Optional output file path

    Returns:
        xr.Dataset: Result dataset

    Example:
        >>> cdo = CDO()
        >>> ds = cdo.operator_name("data.nc")

    See Also:
        - CDOQuery.operator_name: Query method for chaining

    Note:
        Uses CDO's `-operator` command.
    """
    return self.query(input_file).operator_name().compute(output=output)
```

### Info Command Pattern (Returns Structured Result)

```python
def info_command(self, input_file: str | Path) -> InfoResult:
    """
    Get structured information about a dataset.

    Args:
        input_file: Path to input NetCDF file

    Returns:
        InfoResult: Structured result from CDO command

    Raises:
        CDOExecutionError: If CDO command fails
        CDOParseError: If output parsing fails

    Example:
        >>> cdo = CDO()
        >>> info = cdo.info_command("data.nc")
        >>> print(info.file_format)
        'NetCDF4'

    Note:
        Uses CDO's `info` command with InfoParser.
    """
    output = self._execute_text_command(f"info {input_file}")
    from .parsers import InfoParser
    return InfoParser().parse(output)
```

### File Operation Pattern

```python
def merge(
    self,
    *input_files: str | Path,
    output: str | Path,
) -> xr.Dataset:
    """
    Merge multiple files into one.

    Args:
        *input_files: Paths to input files
        output: Path to output file

    Returns:
        xr.Dataset: Merged dataset

    Example:
        >>> cdo = CDO()
        >>> ds = cdo.merge("file1.nc", "file2.nc", output="merged.nc")

    Note:
        Uses CDO's `-merge` operator.
    """
    if len(input_files) < 2:
        raise CDOValidationError(
            message="merge requires at least 2 input files",
            parameter="input_files",
            value=input_files,
            expected="At least 2 file paths"
        )

    files_str = " ".join(str(f) for f in input_files)
    command = f"-merge {files_str}"
    return self._execute_to_dataset(command, output)
```

---

## Existing CDO Class Structure

### Core Components (~1,517 lines)

1. **Initialization** (lines 1-100)
   - `__init__()` - Set up CDO path, temp dir, debug, env
   - `_check_cdo_available()` - Verify CDO is available
   - Properties: `version`, `operators`

2. **Query API** (lines 100-200)
   - `query()` - Factory method returning CDOQuery
   - `_execute_query()` - Execute CDOQuery, return xr.Dataset
   - `_execute_text_command()` - Execute and return text output

3. **Info Commands** (lines 200-400)
   - `sinfo()` - Returns SinfoResult
   - `info()` - Returns InfoResult
   - `griddes()` - Returns GriddesResult
   - `zaxisdes()` - Returns ZaxisdesResult
   - `vlist()` - Returns VlistResult
   - `partab()` - Returns PartabResult

4. **Convenience Methods** (lines 400-1200)
   - Selection operators: `selname()`, `sellevel()`, etc.
   - Statistical operators: `yearmean()`, `fldmean()`, etc.
   - Arithmetic operators: `addc()`, `mulc()`, etc.
   - Interpolation: `remapbil()`, `intlevel()`, etc.

5. **File Operations** (lines 1200-1400)
   - `merge()`, `mergetime()`, `cat()`, `copy()`
   - Split operations: `splityear()`, `splitmon()`, `splitname()`, etc.

6. **Legacy API** (lines 1400-1517)
   - `run()` - Backward compatible string command interface
   - `_execute_command()` - Low-level subprocess execution

---

## Adding New Convenience Methods

### Step 1: Check if Query Method Exists

Before adding convenience method, ensure query method exists:

```markdown
@query.agent

Does CDOQuery have a `select_code()` method?
If not, implement it first.
```

### Step 2: Add Convenience Wrapper

```python
def select_code(
    self,
    *codes: int,
    input_file: str | Path,
    *,
    output: str | Path | None = None,
) -> xr.Dataset:
    """
    Select variables by code (convenience method).

    Args:
        *codes: Variable codes to select
        input_file: Path to input NetCDF file
        output: Optional output file path

    Returns:
        xr.Dataset: Dataset with selected variables

    Example:
        >>> cdo = CDO()
        >>> ds = cdo.select_code(130, 131, input_file="data.nc")

    See Also:
        - CDOQuery.select_code: For chaining operations

    Note:
        Uses CDO's `-selcode` operator.
    """
    return self.query(input_file).select_code(*codes).compute(output=output)
```

### Step 3: Add Docstring Cross-Reference

Link back to query method for users who want chaining.

---

## Adding Info Commands

### Step 1: Coordinate with @parser.agent

```markdown
@parser.agent

Task: Create parser for CDO `showdate` command

Sample output:
```
2020-01-01  2020-02-01  2020-03-01
```

Expected result type: ShowdateResult with dates: list[str]
```

### Step 2: Implement Info Method

```python
def showdate(self, input_file: str | Path) -> ShowdateResult:
    """
    Get dates from dataset.

    Args:
        input_file: Path to input NetCDF file

    Returns:
        ShowdateResult: Structured result with date list

    Example:
        >>> cdo = CDO()
        >>> result = cdo.showdate("data.nc")
        >>> print(result.dates)
        ['2020-01-01', '2020-02-01', '2020-03-01']

    Note:
        Uses CDO's `showdate` command.
    """
    output = self._execute_text_command(f"showdate {input_file}")
    from .parsers import ShowdateParser
    return ShowdateParser().parse(output)
```

---

## File Operations

### Merge Operations

```python
def merge(self, *input_files: str | Path, output: str | Path) -> xr.Dataset:
    """Merge multiple files (union of variables)."""

def mergetime(self, *input_files: str | Path, output: str | Path) -> xr.Dataset:
    """Merge files along time dimension."""

def cat(self, *input_files: str | Path, output: str | Path) -> xr.Dataset:
    """Concatenate files (time series)."""
```

### Split Operations

```python
def splityear(self, input_file: str | Path, prefix: str) -> list[Path]:
    """Split by year into separate files."""

def splitmon(self, input_file: str | Path, prefix: str) -> list[Path]:
    """Split by month into separate files."""

def splitname(self, input_file: str | Path, prefix: str) -> list[Path]:
    """Split by variable name into separate files."""
```

**Pattern**: Return list of created file paths

---

## Internal Execution Methods

### _execute_to_dataset()

Executes CDO command and loads result as xr.Dataset:

```python
def _execute_to_dataset(
    self,
    command: str,
    output: str | Path | None = None,
) -> xr.Dataset:
    """Execute CDO command and return xarray Dataset."""
    # Create temp file if no output specified
    # Run CDO command via subprocess
    # Load result with xarray
    # Clean up temp file if needed
```

### _execute_text_command()

Executes CDO info command and returns text output:

```python
def _execute_text_command(self, command: str) -> str:
    """Execute CDO command that returns text output."""
    # Run CDO command via subprocess
    # Capture stdout
    # Return as string for parser
```

---

## Testing Requirements

### 1. Convenience Method Tests

```python
@pytest.mark.integration
def test_convenience_method(self, cdo_instance, sample_nc_file):
    """Test convenience method delegates to query layer."""
    result = cdo_instance.yearmean(sample_nc_file)
    assert isinstance(result, xr.Dataset)
```

### 2. Info Command Tests

```python
@pytest.mark.integration
def test_info_command(self, cdo_instance, sample_nc_file):
    """Test info command returns structured result."""
    result = cdo_instance.sinfo(sample_nc_file)
    assert isinstance(result, SinfoResult)
    assert result.file_format in ["NetCDF", "NetCDF4"]
    assert len(result.variables) > 0
```

### 3. File Operation Tests

```python
@pytest.mark.integration
def test_merge(self, cdo_instance, tmp_path):
    """Test merge file operation."""
    # Create multiple test files
    # Merge them
    # Verify result
```

---

## Common Tasks

### Task 1: Add Convenience Method

**Prerequisites**: Query method must exist first

**Steps**:
1. Verify `@query.agent` has implemented the query method
2. Add convenience wrapper to CDO class
3. Delegate to `self.query().method().compute()`
4. Add docstring with cross-reference
5. Coordinate with `@test.agent` for integration test

### Task 2: Add Info Command

**Steps**:
1. Run CDO command manually to see output
2. Coordinate with `@parser.agent` to create parser
3. Coordinate with `@types.agent` to create result dataclass
4. Implement method using `_execute_text_command()`
5. Import and use parser
6. Add integration test

### Task 3: Add File Operation

**Steps**:
1. Identify if it's merge-style or split-style
2. Validate input parameters
3. Use `_execute_to_dataset()` or subprocess directly
4. Handle multiple files / glob patterns if needed
5. Return appropriate type (xr.Dataset or list[Path])

---

## Coordinate With Other Agents

### When to Invoke @query.agent

Before adding convenience method:
- Verify query method exists
- Request implementation if missing

### When to Invoke @parser.agent

For any new info command:
- Request parser implementation
- Provide sample CDO output

### When to Invoke @types.agent

For structured results:
- Request result dataclass creation
- Specify fields and types

### When to Invoke @test.agent

Always after adding methods:
- Integration tests for convenience methods
- Info command tests with structured results
- File operation tests

---

## Anti-Patterns to Avoid

### ❌ Bypassing Query Layer

```python
# Bad - reimplements logic
def bad_method(self, input_file: str) -> xr.Dataset:
    command = f"-yearmean {input_file}"
    return self._execute_to_dataset(command)

# Good - delegates to query layer
def good_method(self, input_file: str) -> xr.Dataset:
    return self.query(input_file).yearmean().compute()
```

### ❌ Missing Validation

```python
# Bad - no validation
def merge(self, *files: Path, output: Path):
    return self._execute_to_dataset(f"-merge {' '.join(files)}", output)

# Good - validates inputs
def merge(self, *files: Path, output: Path):
    if len(files) < 2:
        raise CDOValidationError(...)
    return self._execute_to_dataset(f"-merge {' '.join(files)}", output)
```

### ❌ Not Using Parsers

```python
# Bad - returns raw string
def sinfo(self, input_file: str) -> str:
    return self._execute_text_command(f"sinfo {input_file}")

# Good - returns structured result
def sinfo(self, input_file: str) -> SinfoResult:
    output = self._execute_text_command(f"sinfo {input_file}")
    return SinfoParser().parse(output)
```

---

## Reference Files

- **Shared Patterns**: `.github/agents/_shared.md`
- **CDO Class**: `python_cdo_wrapper/cdo.py` (~1,517 lines)
- **Query Module**: `python_cdo_wrapper/query.py` (for integration)
- **Parsers**: `python_cdo_wrapper/parsers/` (for info command usage)
- **Tests**: `tests/test_cdo_class.py`, `tests/test_file_ops.py`
