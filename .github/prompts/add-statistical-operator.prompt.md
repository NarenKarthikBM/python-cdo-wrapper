# Add Statistical Operator to CDOQuery

## Context
Adding a new statistical operator to CDOQuery class for climate data analysis.

## Operator Details

**CDO Operator**: `-{operator_name}`
**Query Method**: `{method_name}()`
**Category**: {category} (e.g., time statistics, field statistics, vertical statistics, running statistics)
**Purpose**: {brief_description}

## Parameters

{parameter_list}

## Expected Behavior

### Command Generation
```python
q = cdo.query("data.nc").{method_name}({example_args})
print(q.get_command())
# Expected: "cdo -{operator_name}{args_fragment} data.nc"
```

### Result Characteristics
{result_description}

## Implementation Requirements

### 1. Query Method (query.py)

Add to appropriate section in CDOQuery class:
```python
# ============================================================
# {CATEGORY_COMMENT}
# ============================================================

def {method_name}(self{parameters}) -> CDOQuery:
    """
    {docstring_summary}

    {extended_description}

    {parameters_doc}

    Returns:
        CDOQuery: New query with statistical operator added.

    {raises_doc}

    Example:
        >>> cdo = CDO()
        >>> # {example_description}
        >>> q = cdo.query("data.nc").{method_name}({example_args})
        >>> print(q.get_command())
        'cdo -{operator_name}{args_fragment} data.nc'

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
```python
class Test{CategoryName}Statistics:
    """Tests for {category} statistical operators."""

    def test_{method_name}_command(self, sample_nc_file):
        """Test {method_name} generates correct command."""
        q = CDO().query(sample_nc_file).{method_name}({test_args})
        assert "-{operator_name}" in q.get_command()

    {parameter_test}

    def test_{method_name}_chaining(self, sample_nc_file):
        """Test {method_name} chains with selection operators."""
        q = (CDO().query(sample_nc_file)
             .select_var("tas")
             .{method_name}({test_args}))

        cmd = q.get_command()
        assert "-selname,tas" in cmd
        assert "-{operator_name}" in cmd

    @pytest.mark.integration
    def test_{method_name}_execution(self, sample_nc_file_with_time):
        """Test {method_name} executes and reduces data."""
        result = (CDO().query(sample_nc_file_with_time)
                  .{method_name}({test_args})
                  .compute())

        assert isinstance(result, xr.Dataset)
        {dimension_assertions}
```

### 3. Convenience Method (cdo.py)

Add convenience method to CDO class:
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
        xr.Dataset: Result dataset with {dimension_reduction}

    Example:
        >>> result = cdo.{method_name}("data.nc"{example_call_args})
    """
    return self.query(input_file).{method_name}({args_only}).compute(output=output)
```

### 4. Documentation Updates

**CHANGELOG.md**:
```markdown
### Added
- `{method_name}()` {category} statistical operator ([#PR-number](link))
```

**README.md** (add to Statistical Operators section):
```markdown
#### {Category} Statistics

| Query Method | CDO Operator | Description |
|--------------|--------------|-------------|
| `{method_name}()` | `-{operator_name}` | {brief_description} |
```

## Test Data Requirements

{test_data_requirements}

## Common Use Cases

### Use Case 1: {use_case_1_name}
```python
# {use_case_1_description}
result = cdo.query("data.nc").{method_name}({use_case_1_args}).compute()
```

### Use Case 2: {use_case_2_name}
```python
# {use_case_2_description}
result = (cdo.query("data.nc")
          .select_var("tas")
          .{method_name}({use_case_2_args})
          .compute())
```

## Acceptance Criteria

- [ ] Query method implemented in correct category section
- [ ] Validation implemented (if parameters)
- [ ] Command generation test passes
- [ ] Parameter test passes (if applicable)
- [ ] Chaining test passes
- [ ] Integration test passes with dimension check
- [ ] Convenience method added to CDO class
- [ ] CHANGELOG.md updated
- [ ] README.md statistical operators table updated
- [ ] All tests pass (`pytest`)
- [ ] Linters pass (`ruff check --fix . && ruff format .`)

## Related Operators

{related_operators_table}

## Reference

- **Adding Operators Guide**: `.github/instructions/adding-operators.instructions.md`
- **Statistical Operators**: Lines 1200-2000 in `python_cdo_wrapper/query.py`
- **Test Patterns**: `tests/test_query.py` - `TestTimeStatistics`, `TestFieldStatistics`, etc.

---

**Template Variables to Fill**:
- `{operator_name}`: CDO operator (e.g., "yearmean", "fldstd")
- `{method_name}`: Python method (e.g., "year_mean", "field_std")
- `{category}`: time/field/vertical/running statistics
- `{brief_description}`: One-line description
- `{parameter_list}`: Parameters if any (many stats have none)
- `{example_args}`: Example arguments (empty string if none)
- `{args_fragment}`: Command fragment after operator (empty if no args)
- `{result_description}`: What dimensions are reduced
- `{CATEGORY_COMMENT}`: Section comment (e.g., "TIME STATISTICS")
- `{parameters}`: Method signature parameters (empty if none)
- `{docstring_summary}`: First line of docstring
- `{extended_description}`: Multi-line description if needed
- `{parameters_doc}`: Args section (omit if no params)
- `{raises_doc}`: Raises section (if validation)
- `{example_description}`: Description of example
- `{related_methods}`: Related statistical methods
- `{usage_notes}`: CDO-specific notes
- `{validation_code}`: Validation if parameters (omit if none)
- `{args_spec}`: OperatorSpec args (e.g., `, args=(n,)`)
- `{parameter_test}`: Test for parameters (omit if none)
- `{test_args}`: Test arguments (empty if none)
- `{dimension_assertions}`: Assert dimension reduction
- `{convenience_parameters}`: Params for convenience method
- `{convenience_docstring}`: Convenience method docstring
- `{convenience_args_doc}`: Args doc for convenience
- `{dimension_reduction}`: Description of reduced dimensions
- `{example_call_args}`: Args in example call
- `{args_only}`: Just arg names
- `{test_data_requirements}`: Fixture requirements
- `{use_case_N_name/description/args}`: Example use cases
- `{related_operators_table}`: Table of related operators
