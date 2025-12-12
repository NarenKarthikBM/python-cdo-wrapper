# Add Query Method (Any Category)

## Context
Adding a new method to CDOQuery class for {category}.

## Method Details

**CDO Operator**: `-{operator_name}`
**Query Method**: `{method_name}()`
**Category**: {category}
**Purpose**: {brief_description}

## Parameters

{parameter_specifications}

## Expected Behavior

### Command Generation
```python
q = cdo.query("data.nc").{method_name}({example_args})
print(q.get_command())
# Expected: "cdo -{operator_name}{args_fragment} data.nc"
```

### Chaining Behavior
```python
q = (cdo.query("data.nc")
     .select_var("tas")
     .{method_name}({example_args})
     .year_mean())

# Operators applied right-to-left in CDO
# Result: cdo -yearmean -{operator_name} -selname,tas data.nc
```

## Implementation Requirements

### 1. Query Method (query.py)

Add to appropriate section in CDOQuery class:

**Location**: {section_location} (e.g., "Lines 800-1200: Selection Operators")

```python
def {method_name}(self{parameters}) -> CDOQuery:
    """
    {docstring_summary}

    {extended_description}

    Args:
        {args_documentation}

    Returns:
        CDOQuery: New query with {operator_name} operator added.

    Raises:
        {raises_documentation}

    Example:
        >>> cdo = CDO()
        >>> # {example_description}
        >>> q = cdo.query("data.nc").{method_name}({example_args})
        >>> print(q.get_command())
        'cdo -{operator_name}{args_fragment} data.nc'

        >>> # Chaining example
        >>> q = (cdo.query("data.nc")
        ...      .select_var("tas")
        ...      .{method_name}({example_args}))

    See Also:
        {related_methods}

    Note:
        {usage_notes}
    """
    {validation_code}

    return self._add_operator(OperatorSpec("{operator_name}"{args_spec}))
```

### 2. Tests (tests/test_query.py)

Add to appropriate test class:

**Test Class**: `Test{CategoryName}` or create new if doesn't exist

```python
class Test{CategoryName}:
    """Tests for {category} operators."""

    def test_{method_name}_command(self, sample_nc_file):
        """Test {method_name} generates correct CDO command."""
        q = CDO().query(sample_nc_file).{method_name}({test_args})

        cmd = q.get_command()
        assert "-{operator_name}" in cmd
        {additional_command_assertions}

    {parameter_tests}

    def test_{method_name}_validation(self, sample_nc_file):
        """Test {method_name} validates parameters."""
        with pytest.raises(CDOValidationError) as exc_info:
            CDO().query(sample_nc_file).{method_name}({invalid_args})

        assert exc_info.value.parameter == "{expected_parameter}"
        {additional_validation_assertions}

    def test_{method_name}_chaining(self, sample_nc_file):
        """Test {method_name} chains correctly with other operators."""
        q = (CDO().query(sample_nc_file)
             .select_var("tas")
             .{method_name}({test_args})
             .year_mean())

        cmd = q.get_command()
        assert "-selname,tas" in cmd
        assert "-{operator_name}" in cmd
        assert "-yearmean" in cmd

        # Verify order (yearmean before operator before selname)
        {order_assertions}

    def test_{method_name}_clone(self, sample_nc_file):
        """Test {method_name} returns new query (immutability)."""
        q1 = CDO().query(sample_nc_file)
        q2 = q1.{method_name}({test_args})

        assert q1 is not q2
        assert len(q1._operators) == 0
        assert len(q2._operators) == 1

    {integration_test}
```

### 3. Convenience Method (cdo.py) - Optional

If commonly used, add convenience method:

```python
def {method_name}(
    self,
    input_file: str | Path,
    {convenience_parameters}
    *,
    output: str | Path | None = None,
) -> xr.Dataset:
    """
    {convenience_docstring}

    Args:
        input_file: Input NetCDF file
        {convenience_args_doc}
        output: Optional output file path

    Returns:
        xr.Dataset: Result dataset

    Example:
        >>> cdo = CDO()
        >>> result = cdo.{method_name}("data.nc"{example_call_args})
    """
    return self.query(input_file).{method_name}({args_only}).compute(output=output)
```

### 4. Documentation Updates

**CHANGELOG.md**:
```markdown
### Added
- `{method_name}()` {category} operator for CDOQuery ([#PR-number](link))
```

**README.md** (if significant):
```markdown
### {Category} Operators

| Query Method | CDO Operator | Description |
|--------------|--------------|-------------|
| `{method_name}()` | `-{operator_name}` | {brief_description} |

#### Example

\```python
result = cdo.query("data.nc").{method_name}({example_args}).compute()
\```
```

## Validation Requirements

{validation_requirements}

## Test Data Requirements

**Fixtures Needed**:
- [ ] `{fixture_1}` - {fixture_1_description}
- [ ] `{fixture_2}` - {fixture_2_description}

**Create New Fixture** (if needed):
```python
@pytest.fixture
def {new_fixture_name}(tmp_path):
    """{new_fixture_description}"""
    {fixture_implementation}
```

## Common Patterns

### Pattern: Variable-Length Arguments

```python
def {method_name}(self, *args: type) -> CDOQuery:
    """Method accepting multiple arguments."""
    if not args:
        raise CDOValidationError(...)
    return self._add_operator(OperatorSpec("{operator_name}", args=args))
```

### Pattern: Optional Parameter

```python
def {method_name}(self, param: type | None = None) -> CDOQuery:
    """Method with optional parameter."""
    if param is None:
        # Use default behavior
        return self._add_operator(OperatorSpec("{operator_name}"))
    return self._add_operator(OperatorSpec("{operator_name}", args=(param,)))
```

### Pattern: Range Validation

```python
def {method_name}(self, value: float) -> CDOQuery:
    """Method with range validation."""
    if not (min_val <= value <= max_val):
        raise CDOValidationError(
            message=f"Value must be between {min_val} and {max_val}, got {value}",
            parameter="value",
            value=value,
            expected=f"Value in range [{min_val}, {max_val}]"
        )
    return self._add_operator(OperatorSpec("{operator_name}", args=(value,)))
```

## Acceptance Criteria

- [ ] Query method implemented in correct section
- [ ] Comprehensive docstring with examples
- [ ] Validation implemented
- [ ] Command generation test passes
- [ ] Validation test passes
- [ ] Chaining test passes
- [ ] Immutability test passes
- [ ] Integration test passes (if applicable)
- [ ] Convenience method added (if appropriate)
- [ ] CHANGELOG.md updated
- [ ] README.md updated (if significant)
- [ ] All tests pass (`pytest`)
- [ ] Linters pass (`ruff check --fix . && ruff format .`)
- [ ] Type checker passes (`mypy python_cdo_wrapper`)

## Reference

- **Adding Operators Guide**: `.github/instructions/adding-operators.instructions.md`
- **Shared Patterns**: `.github/agents/_shared.md`
- **Query Class**: `python_cdo_wrapper/query.py`
- **Existing Tests**: `tests/test_query.py`

---

**Template Variables to Fill**:
- `{category}`: Operator category (selection, statistical, arithmetic, etc.)
- `{operator_name}`: CDO operator name
- `{method_name}`: Python method name
- `{brief_description}`: One-line description
- `{parameter_specifications}`: Detailed parameter specs
- `{example_args}`: Example arguments
- `{args_fragment}`: Command fragment after operator
- `{section_location}`: Where in query.py to add
- `{parameters}`: Method signature parameters
- `{docstring_summary}`: First line of docstring
- `{extended_description}`: Extended description
- `{args_documentation}`: Args section
- `{raises_documentation}`: Raises section
- `{example_description}`: Description of example
- `{related_methods}`: See Also section
- `{usage_notes}`: Note section
- `{validation_code}`: Validation implementation
- `{args_spec}`: OperatorSpec args
- `{CategoryName}`: Test class name
- `{test_args}`: Arguments for testing
- `{additional_command_assertions}`: Extra command checks
- `{parameter_tests}`: Additional parameter tests
- `{invalid_args}`: Invalid arguments
- `{expected_parameter}`: Parameter name in error
- `{additional_validation_assertions}`: Extra validation checks
- `{order_assertions}`: Operator order assertions
- `{integration_test}`: Integration test if needed
- `{convenience_parameters}`: Convenience method params
- `{convenience_docstring}`: Convenience method docstring
- `{convenience_args_doc}`: Convenience args docs
- `{example_call_args}`: Example call arguments
- `{args_only}`: Just argument names
- `{validation_requirements}`: What to validate
- `{fixture_N}`: Fixture names
- `{fixture_N_description}`: Fixture descriptions
- `{new_fixture_name}`: New fixture name if needed
- `{new_fixture_description}`: New fixture description
- `{fixture_implementation}`: New fixture code
