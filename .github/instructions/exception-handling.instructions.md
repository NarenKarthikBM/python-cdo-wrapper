---
applyTo: "python_cdo_wrapper/exceptions.py,python_cdo_wrapper/**/*.py"
---

# Exception Handling Guide

This instruction guide covers exception patterns in python-cdo-wrapper.

## Exception Hierarchy

```
CDOError (base)
├── CDOValidationError    # Invalid parameters
├── CDOExecutionError     # Command failed
├── CDOFileNotFoundError  # Input file missing
└── CDOParseError         # Output parsing failed
```

## Exception Definitions

### CDOError (Base)

```python
class CDOError(Exception):
    """Base exception for all CDO-related errors."""
    pass
```

### CDOValidationError

```python
class CDOValidationError(CDOError):
    """Invalid parameters provided to an operator."""

    def __init__(
        self,
        message: str,
        parameter: str,
        value: Any,
        expected: str
    ) -> None:
        """
        Initialize validation error.

        Args:
            message: Human-readable error message
            parameter: Name of invalid parameter
            value: Actual value provided
            expected: Description of expected value
        """
        super().__init__(message)
        self.parameter = parameter
        self.value = value
        self.expected = expected
```

**When to use**: Parameter validation failures

### CDOExecutionError

```python
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
        """
        Initialize execution error.

        Args:
            message: Human-readable error message
            command: CDO command that failed
            returncode: Process exit code
            stdout: Process stdout
            stderr: Process stderr
        """
        super().__init__(message)
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
```

**When to use**: CDO subprocess execution failures

### CDOFileNotFoundError

```python
class CDOFileNotFoundError(CDOError):
    """Input file does not exist."""

    def __init__(self, message: str, file_path: str) -> None:
        """
        Initialize file not found error.

        Args:
            message: Human-readable error message
            file_path: Path to missing file
        """
        super().__init__(message)
        self.file_path = file_path
```

**When to use**: Input file validation

### CDOParseError

```python
class CDOParseError(CDOError):
    """Failed to parse CDO output."""
    pass
```

**When to use**: Parser failures

## Raising Exceptions

### Validation Errors

```python
def select_var(self, *names: str) -> CDOQuery:
    """Select variables by name."""
    if not names:
        raise CDOValidationError(
            message="Variable names cannot be empty",
            parameter="names",
            value=names,
            expected="Non-empty collection of variable names"
        )

    return self._add_operator(OperatorSpec("selname", args=names))
```

### Range Validation

```python
def select_level(self, *levels: float) -> CDOQuery:
    """Select vertical levels."""
    if not levels:
        raise CDOValidationError(
            message="At least one level must be specified",
            parameter="levels",
            value=levels,
            expected="Non-empty collection of float values"
        )

    for level in levels:
        if level < 0:
            raise CDOValidationError(
                message=f"Level must be non-negative, got {level}",
                parameter="levels",
                value=level,
                expected="Non-negative float"
            )

    return self._add_operator(OperatorSpec("sellevel", args=levels))
```

### Execution Errors

```python
def _execute_command(self, command: list[str]) -> subprocess.CompletedProcess:
    """Execute CDO command."""
    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise CDOExecutionError(
            message=f"CDO command failed: {' '.join(command)}",
            command=" ".join(command),
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr
        )

    return result
```

### File Not Found Errors

```python
def query(self, input_file: str | Path) -> CDOQuery:
    """Create query for input file."""
    path = Path(input_file)

    if not path.exists():
        raise CDOFileNotFoundError(
            message=f"Input file not found: {path}",
            file_path=str(path)
        )

    return CDOQuery(input_file=path)
```

### Parse Errors

```python
def parse(self, output: str) -> ResultType:
    """Parse CDO output."""
    if not output.strip():
        raise CDOParseError("CDO output is empty")

    # Try to parse
    try:
        # ... parsing logic ...
        pass
    except Exception as e:
        raise CDOParseError(
            f"Failed to parse CDO output: {e}"
        ) from e
```

## Catching Exceptions

### Specific Exception

```python
try:
    result = cdo.query("data.nc").select_var("tas").compute()
except CDOValidationError as e:
    print(f"Validation failed: {e}")
    print(f"Parameter: {e.parameter}")
    print(f"Value: {e.value}")
    print(f"Expected: {e.expected}")
```

### Multiple Exceptions

```python
try:
    result = cdo.query("data.nc").select_var("tas").compute()
except CDOFileNotFoundError as e:
    print(f"File not found: {e.file_path}")
except CDOValidationError as e:
    print(f"Invalid parameter: {e.parameter}")
except CDOExecutionError as e:
    print(f"CDO command failed: {e.command}")
    print(f"Error: {e.stderr}")
```

### Base Exception

```python
try:
    result = cdo.query("data.nc").select_var("tas").compute()
except CDOError as e:
    # Catch any CDO-related error
    print(f"CDO error: {e}")
```

## Exception Context

### Add Context with `from`

```python
def parse(self, output: str) -> ResultType:
    """Parse CDO output."""
    try:
        value = int(output.strip())
    except ValueError as e:
        raise CDOParseError(
            f"Expected integer, got: {output}"
        ) from e  # Preserve original exception
```

### Re-raise with Additional Context

```python
def process_file(self, file_path: str) -> xr.Dataset:
    """Process NetCDF file."""
    try:
        return self.query(file_path).compute()
    except CDOExecutionError as e:
        # Add context and re-raise
        raise CDOExecutionError(
            message=f"Failed to process {file_path}: {e}",
            command=e.command,
            returncode=e.returncode,
            stdout=e.stdout,
            stderr=e.stderr
        ) from e
```

## Testing Exceptions

### Test Exception Raised

```python
def test_select_var_empty_raises():
    """Test select_var raises on empty names."""
    with pytest.raises(CDOValidationError) as exc_info:
        CDO().query("data.nc").select_var()

    # Check exception type
    assert isinstance(exc_info.value, CDOValidationError)
```

### Test Exception Attributes

```python
def test_validation_error_attributes():
    """Test CDOValidationError has correct attributes."""
    with pytest.raises(CDOValidationError) as exc_info:
        CDO().query("data.nc").select_var()

    error = exc_info.value
    assert error.parameter == "names"
    assert error.value == ()
    assert "empty" in error.expected.lower()
```

### Test Exception Message

```python
def test_execution_error_message():
    """Test CDOExecutionError has command in message."""
    with pytest.raises(CDOExecutionError) as exc_info:
        # Code that raises CDOExecutionError
        pass

    error_msg = str(exc_info.value)
    assert "cdo" in error_msg.lower()
```

### Test Exception Chaining

```python
def test_parse_error_chaining():
    """Test CDOParseError preserves original exception."""
    with pytest.raises(CDOParseError) as exc_info:
        # Code that raises CDOParseError from ValueError
        pass

    # Check original exception preserved
    assert exc_info.value.__cause__ is not None
    assert isinstance(exc_info.value.__cause__, ValueError)
```

## Common Patterns

### Pattern: Validate Before Processing

```python
def method(self, param: str) -> ResultType:
    """Process parameter."""
    # Validate first
    if not param:
        raise CDOValidationError(
            message="Parameter cannot be empty",
            parameter="param",
            value=param,
            expected="Non-empty string"
        )

    # Then process
    return self._process(param)
```

### Pattern: Try-Except with Cleanup

```python
def process_with_temp_file(self, data: xr.Dataset) -> xr.Dataset:
    """Process data using temporary file."""
    temp_file = None
    try:
        temp_file = Path(tempfile.mktemp(suffix=".nc"))
        data.to_netcdf(temp_file)
        return self.query(temp_file).compute()
    except CDOError as e:
        # Handle CDO errors
        raise
    finally:
        # Cleanup
        if temp_file and temp_file.exists():
            temp_file.unlink()
```

### Pattern: Convert External Exceptions

```python
def read_config(self, config_path: str) -> dict:
    """Read configuration file."""
    try:
        with open(config_path) as f:
            return json.load(f)
    except FileNotFoundError:
        raise CDOFileNotFoundError(
            message=f"Config file not found: {config_path}",
            file_path=config_path
        )
    except json.JSONDecodeError as e:
        raise CDOParseError(
            f"Invalid JSON in config: {e}"
        ) from e
```

## Error Messages

### Good Error Messages

```python
# ✅ GOOD - Specific, actionable
raise CDOValidationError(
    message="Variable name 'tas' not found in dataset. Available: ['temp', 'precip']",
    parameter="name",
    value="tas",
    expected="One of: temp, precip"
)

# ✅ GOOD - Include context
raise CDOExecutionError(
    message=f"CDO command failed: sellevel requires NetCDF file with vertical levels",
    command=command,
    returncode=returncode,
    stdout=stdout,
    stderr=stderr
)
```

### Bad Error Messages

```python
# ❌ BAD - Vague
raise CDOValidationError(
    message="Invalid input",
    parameter="param",
    value=value,
    expected="Valid input"
)

# ❌ BAD - No context
raise CDOExecutionError(
    message="Command failed",
    command=command,
    returncode=1,
    stdout="",
    stderr=""
)
```

## Checklist

- [ ] Use appropriate exception type
- [ ] Include all required attributes
- [ ] Write descriptive error messages
- [ ] Add context with `from` when converting
- [ ] Test exception is raised
- [ ] Test exception attributes
- [ ] Document exceptions in docstring (Raises section)

## Reference

- **Exception definitions**: `python_cdo_wrapper/exceptions.py`
- **Exception tests**: `tests/test_exceptions.py`
- **Validation patterns**: `python_cdo_wrapper/validation.py`
