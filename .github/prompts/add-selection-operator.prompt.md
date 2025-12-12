# Add Selection Operator to CDOQuery

## Context
Adding a new selection operator to CDOQuery class for filtering climate data.

## Operator Details

**CDO Operator**: `-{operator_name}`
**Query Method**: `{method_name}()`
**Purpose**: {brief_description}

## Parameters

{parameter_list}

## Expected Behavior

### Command Generation
```python
q = cdo.query("data.nc").{method_name}({example_args})
print(q.get_command())
# Expected: "cdo -{operator_name},{expected_fragment} data.nc"
```

### Validation Rules
{validation_rules}

## Implementation Requirements

### 1. Query Method (query.py)

Add to CDOQuery class:
```python
def {method_name}(self, {parameters}) -> CDOQuery:
    """
    {docstring_summary}

    Args:
        {args_documentation}

    Returns:
        CDOQuery: New query with selection operator added.

    Raises:
        CDOValidationError: {validation_error_conditions}

    Example:
        >>> cdo = CDO()
        >>> q = cdo.query("data.nc").{method_name}({example_args})
        >>> print(q.get_command())
        'cdo -{operator_name},{expected_fragment} data.nc'

    See Also:
        {related_methods}
    """
    # Validation
    {validation_code}

    return self._add_operator(OperatorSpec("{operator_name}", args={args_spec}))
```

### 2. Tests (tests/test_query.py)

Add test class or extend existing:
```python
class Test{ClassName}:
    def test_{method_name}_command(self, sample_nc_file):
        """Test {method_name} generates correct command."""
        q = CDO().query(sample_nc_file).{method_name}({test_args})
        assert "-{operator_name},{expected_fragment}" in q.get_command()

    def test_{method_name}_validation(self, sample_nc_file):
        """Test {method_name} raises on invalid input."""
        with pytest.raises(CDOValidationError) as exc_info:
            CDO().query(sample_nc_file).{method_name}({invalid_args})

        assert exc_info.value.parameter == "{invalid_parameter}"

    def test_{method_name}_chaining(self, sample_nc_file):
        """Test {method_name} chains with other operators."""
        q = (CDO().query(sample_nc_file)
             .select_var("tas")
             .{method_name}({test_args})
             .year_mean())

        cmd = q.get_command()
        assert "-selname,tas" in cmd
        assert "-{operator_name}" in cmd
        assert "-yearmean" in cmd

    @pytest.mark.integration
    def test_{method_name}_execution(self, {fixture_name}):
        """Test {method_name} executes successfully."""
        result = (CDO().query({fixture_name})
                  .{method_name}({test_args})
                  .compute())

        assert isinstance(result, xr.Dataset)
        {additional_assertions}
```

### 3. Convenience Method (cdo.py) - Optional

If this is a commonly used operator, add convenience method:
```python
def {method_name}(
    self,
    input_file: str | Path,
    {parameters},
    *,
    output: str | Path | None = None,
) -> xr.Dataset:
    """
    Convenience method for {method_name}.

    Args:
        input_file: Input NetCDF file
        {args_documentation}
        output: Optional output file path

    Returns:
        xr.Dataset: Result dataset
    """
    return self.query(input_file).{method_name}({args_only}).compute(output=output)
```

### 4. Documentation Updates

**CHANGELOG.md**:
```markdown
### Added
- `{method_name}()` operator for CDOQuery ([#PR-number](link))
```

**README.md** (if significant):
```markdown
### Selection Operators

#### {method_name}

{brief_description}

\```python
result = cdo.query("data.nc").{method_name}({example_args}).compute()
\```
```

## Acceptance Criteria

- [ ] Query method implemented with validation
- [ ] Command generation test passes
- [ ] Validation test passes
- [ ] Chaining test passes
- [ ] Integration test passes (if applicable)
- [ ] Convenience method added (if applicable)
- [ ] CHANGELOG.md updated
- [ ] All tests pass (`pytest`)
- [ ] Linters pass (`ruff check --fix . && ruff format .`)

## Related Documentation

- **Adding Operators Guide**: `.github/instructions/adding-operators.instructions.md`
- **Shared Patterns**: `.github/agents/_shared.md`
- **Existing Operators**: `python_cdo_wrapper/query.py`

---

**Template Variables to Fill**:
- `{operator_name}`: CDO operator name (e.g., "selcode")
- `{method_name}`: Python method name (e.g., "select_code")
- `{brief_description}`: One-line description
- `{parameter_list}`: List of parameters with types
- `{example_args}`: Example arguments
- `{expected_fragment}`: Expected command fragment
- `{validation_rules}`: Validation requirements
- `{parameters}`: Method parameter signature
- `{docstring_summary}`: Docstring first line
- `{args_documentation}`: Args section content
- `{validation_error_conditions}`: When to raise
- `{related_methods}`: Related query methods
- `{validation_code}`: Validation implementation
- `{args_spec}`: OperatorSpec args
- `{test_args}`: Arguments for testing
- `{invalid_args}`: Invalid arguments for testing
- `{invalid_parameter}`: Expected parameter name in error
- `{fixture_name}`: Test fixture to use
- `{additional_assertions}`: Extra assertions on result
- `{args_only}`: Just argument names for convenience method
