---
applyTo: "python_cdo_wrapper/query.py,python_cdo_wrapper/operators/**/*.py"
---

# Adding Operators to CDOQuery

This instruction guide covers how to add new operators to the CDOQuery class.

## Operator Categories

CDO operators fall into these categories:
- **Selection** (selname, sellevel, selyear, etc.)
- **Statistical** (yearmean, fldmean, timstd, etc.)
- **Arithmetic** (addc, subc, mulc, etc.)
- **Interpolation** (remapbil, intlevel, etc.)
- **Modification** (setname, setgrid, etc.)

## Adding a Query Method

### 1. Basic Operator (No Parameters)

```python
def operator_name(self) -> CDOQuery:
    """
    Brief description of what operator does.

    Returns:
        CDOQuery: New query with operator added.

    Example:
        >>> cdo = CDO()
        >>> q = cdo.query("data.nc").operator_name()
        >>> print(q.get_command())
        'cdo -cdooperator data.nc'

    See Also:
        - related_operator: Related functionality
    """
    return self._add_operator(OperatorSpec("cdooperator"))
```

### 2. Operator with Positional Arguments

```python
def operator_name(self, *args: type) -> CDOQuery:
    """
    Brief description.

    Args:
        *args: Description of arguments

    Returns:
        CDOQuery: New query with operator added.

    Raises:
        CDOValidationError: If args is empty

    Example:
        >>> q = cdo.query("data.nc").operator_name("arg1", "arg2")
        >>> print(q.get_command())
        'cdo -cdooperator,arg1,arg2 data.nc'
    """
    if not args:
        raise CDOValidationError(
            message="operator_name requires at least one argument",
            parameter="args",
            value=args,
            expected="Non-empty collection"
        )
    return self._add_operator(OperatorSpec("cdooperator", args=args))
```

### 3. Operator with Keyword Arguments

```python
def operator_name(
    self,
    param1: type,
    param2: type | None = None,
) -> CDOQuery:
    """
    Brief description.

    Args:
        param1: Description
        param2: Description. If None, uses default.

    Returns:
        CDOQuery: New query with operator added.

    Raises:
        CDOValidationError: If param1 is invalid
    """
    # Validation
    if not param1:
        raise CDOValidationError(
            message="param1 cannot be empty",
            parameter="param1",
            value=param1,
            expected="Non-empty value"
        )

    return self._add_operator(
        OperatorSpec("cdooperator", kwargs={"param1": param1, "param2": param2})
    )
```

## Validation Patterns

### Validate Non-Empty Collection

```python
if not values:
    raise CDOValidationError(
        message=f"{parameter_name} cannot be empty",
        parameter=parameter_name,
        value=values,
        expected="Non-empty collection"
    )
```

### Validate Range

```python
from .validation import validate_range

validate_range(
    value=longitude,
    name="longitude",
    min_val=-180.0,
    max_val=180.0,
    inclusive=True
)
```

### Validate Type

```python
if not isinstance(value, expected_type):
    raise CDOValidationError(
        message=f"{name} must be {expected_type.__name__}",
        parameter=name,
        value=value,
        expected=f"Instance of {expected_type.__name__}"
    )
```

## Binary Operations (F() Pattern)

For operations involving two datasets:

```python
def subtract(self, other: CDOQuery | str | Path) -> BinaryOpQuery:
    """
    Subtract another dataset (anomaly calculation pattern).

    Args:
        other: CDOQuery (from F()), file path, or CDOQuery to subtract

    Returns:
        BinaryOpQuery: Binary operation query

    Example:
        >>> # Anomaly calculation
        >>> anomaly = cdo.query("data.nc").subtract(F("climatology.nc"))
        >>>
        >>> # With processing on both sides
        >>> diff = (cdo.query("a.nc").year_mean()
        ...            .subtract(F("b.nc").year_mean()))
    """
    return self._binary_op("sub", other)
```

## Testing Requirements

Every operator method needs tests:

### 1. Command Generation Test

```python
def test_operator_name_command(self, sample_nc_file):
    """Test operator generates correct CDO command."""
    q = CDO().query(sample_nc_file).operator_name("arg1", "arg2")
    assert "-cdooperator,arg1,arg2" in q.get_command()
```

### 2. Validation Test

```python
def test_operator_name_empty_raises(self, sample_nc_file):
    """Test operator raises on empty arguments."""
    with pytest.raises(CDOValidationError) as exc_info:
        CDO().query(sample_nc_file).operator_name()

    assert exc_info.value.parameter == "args"
    assert "empty" in str(exc_info.value).lower()
```

### 3. Chaining Test

```python
def test_operator_name_chaining(self, sample_nc_file):
    """Test operator can be chained with other operators."""
    q = (CDO().query(sample_nc_file)
         .select_var("tas")
         .operator_name("arg")
         .year_mean())

    cmd = q.get_command()
    assert "-selname,tas" in cmd
    assert "-cdooperator,arg" in cmd
    assert "-yearmean" in cmd
```

### 4. Integration Test (if applicable)

```python
@pytest.mark.integration
def test_operator_name_execution(self, sample_nc_file):
    """Test operator executes successfully with CDO."""
    result = (CDO().query(sample_nc_file)
              .operator_name("arg")
              .compute())

    assert isinstance(result, xr.Dataset)
    # Additional assertions on result
```

## Adding Convenience Method to CDO Class

After adding query method, add convenience method to CDO class:

```python
# In python_cdo_wrapper/cdo.py

def operator_name(
    self,
    input_file: str | Path,
    *args,
    output: str | Path | None = None,
) -> xr.Dataset:
    """
    Convenience method for operator_name (delegates to query layer).

    Args:
        input_file: Input NetCDF file
        *args: Arguments for operator
        output: Optional output file path

    Returns:
        xr.Dataset: Result dataset

    Example:
        >>> result = cdo.operator_name("data.nc", "arg1", "arg2")
    """
    return self.query(input_file).operator_name(*args).compute(output=output)
```

## Documentation Updates

1. **CHANGELOG.md**: Add entry under [Unreleased] → Added
```markdown
### Added
- `operator_name()` method for CDOQuery ([#PR-number](link))
```

2. **README.md**: Add example if significant feature

3. **Docstrings**: Ensure complete Google-style docstrings

## Checklist

- [ ] Query method added to CDOQuery class
- [ ] Validation implemented
- [ ] Command generation test added
- [ ] Validation test added
- [ ] Chaining test added
- [ ] Integration test added (if applicable)
- [ ] Convenience method added to CDO class
- [ ] CHANGELOG.md updated
- [ ] README.md updated (if significant)
- [ ] All tests pass (`pytest`)
- [ ] Linters pass (`ruff check --fix . && ruff format .`)

## Common Issues

### Issue: Operator not appearing in command

**Cause**: Forgot to call `_add_operator`

**Fix**: Ensure `return self._add_operator(...)`

### Issue: Validation error not raised

**Cause**: Missing validation logic

**Fix**: Add validation before `_add_operator` call

### Issue: Test fails with "command not found"

**Cause**: Missing `@pytest.mark.integration` marker

**Fix**: Add marker or mock subprocess

## Reference

- **Query patterns**: `.github/agents/_shared.md`
- **Existing operators**: `python_cdo_wrapper/query.py`
- **Validation utilities**: `python_cdo_wrapper/validation.py`
- **Test patterns**: `tests/test_query.py`
