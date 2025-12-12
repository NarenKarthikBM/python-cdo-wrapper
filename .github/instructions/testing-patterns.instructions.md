---
applyTo: "python_cdo_wrapper/tests/**/*.py,python_cdo_wrapper/tests/conftest.py"
---

# Testing Patterns Guide

This instruction guide covers testing patterns for python-cdo-wrapper.

## Test Categories

### Unit Tests
- Mock subprocess calls
- No CDO required
- Fast execution
- Test logic and validation

### Integration Tests
- Use real CDO
- Mark with `@pytest.mark.integration`
- Slower execution
- Test actual execution

## Test File Organization

```
tests/
├── conftest.py           # Fixtures
├── test_query.py         # CDOQuery tests (700+ tests)
├── test_cdo_class.py     # CDO class tests
├── test_parsers_legacy.py # Legacy parser tests
├── test_integration/     # Integration tests
│   └── __init__.py
├── test_parsers/         # New parser tests
│   ├── test_info.py
│   ├── test_grid.py
│   └── test_partab.py
└── test_operators/       # Operator tests
    └── test_info.py
```

## Core Fixtures (conftest.py)

### File Fixtures

```python
@pytest.fixture
def sample_nc_file(tmp_path):
    """Create minimal NetCDF file with temperature data."""
    ds = xr.Dataset({
        'tas': (['time', 'lat', 'lon'], np.random.randn(10, 90, 180))
    })
    file_path = tmp_path / "test_data.nc"
    ds.to_netcdf(file_path)
    return file_path

@pytest.fixture
def sample_nc_file_with_time(tmp_path):
    """Create NetCDF file with proper datetime coordinates."""
    times = pd.date_range('2020-01-01', periods=12, freq='MS')
    ds = xr.Dataset({
        'tas': (['time', 'lat', 'lon'], np.random.randn(12, 90, 180)),
        'time': times
    })
    file_path = tmp_path / "test_data_time.nc"
    ds.to_netcdf(file_path)
    return file_path

@pytest.fixture
def multi_var_nc_file(tmp_path):
    """Create NetCDF file with multiple variables."""
    ds = xr.Dataset({
        'tas': (['time', 'lat', 'lon'], np.random.randn(10, 90, 180)),
        'pr': (['time', 'lat', 'lon'], np.random.randn(10, 90, 180))
    })
    file_path = tmp_path / "test_multi_var.nc"
    ds.to_netcdf(file_path)
    return file_path
```

### Instance Fixtures

```python
@pytest.fixture
def cdo_instance():
    """Return pre-configured CDO instance."""
    return CDO()
```

### Mock Fixtures

```python
@pytest.fixture
def mock_subprocess():
    """Mock subprocess.run for unit tests."""
    with patch("python_cdo_wrapper.core.subprocess.run") as mock:
        mock.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr=""
        )
        yield mock
```

## Test Patterns

### Pattern 1: Command Generation Test

Test that query builds correct CDO command:

```python
def test_select_var_command(self, sample_nc_file):
    """Test select_var generates correct CDO command."""
    q = CDO().query(sample_nc_file).select_var("tas", "pr")

    cmd = q.get_command()
    assert "-selname,tas,pr" in cmd
    assert str(sample_nc_file) in cmd
```

### Pattern 2: Validation Test

Test that validation raises correct errors:

```python
def test_select_var_empty_raises(self, sample_nc_file):
    """Test select_var raises on empty names."""
    with pytest.raises(CDOValidationError) as exc_info:
        CDO().query(sample_nc_file).select_var()

    # Check exception details
    assert exc_info.value.parameter == "names"
    assert "empty" in str(exc_info.value).lower()
```

### Pattern 3: Integration Test

Test actual execution with CDO:

```python
@pytest.mark.integration
def test_select_var_execution(self, sample_nc_file):
    """Test select_var executes successfully."""
    result = (CDO().query(sample_nc_file)
              .select_var("tas")
              .compute())

    assert isinstance(result, xr.Dataset)
    assert "tas" in result.variables
    assert "pr" not in result.variables
```

### Pattern 4: Chaining Test

Test multiple operators chain correctly:

```python
def test_operator_chaining(self, sample_nc_file):
    """Test operators chain in correct order."""
    q = (CDO().query(sample_nc_file)
         .select_var("tas")
         .select_year(2020)
         .year_mean())

    cmd = q.get_command()

    # Verify all operators present
    assert "-selname,tas" in cmd
    assert "-selyear,2020" in cmd
    assert "-yearmean" in cmd

    # Verify order (rightmost first in CDO)
    selname_pos = cmd.find("-selname")
    yearmean_pos = cmd.find("-yearmean")
    assert yearmean_pos < selname_pos  # yearmean comes before selname
```

### Pattern 5: Mocking subprocess

For unit tests without CDO:

```python
def test_cdo_run_success(self, mock_subprocess):
    """Test CDO.run executes successfully."""
    mock_subprocess.return_value.stdout = "output"

    cdo = CDO()
    result, log = cdo.run("-sinfo test.nc", check_files=False)

    # Verify subprocess called correctly
    mock_subprocess.assert_called_once()
    call_args = mock_subprocess.call_args
    assert "cdo" in call_args[0][0]
    assert "-sinfo" in call_args[0][0]
```

## Testing Exceptions

### Test Exception Raised

```python
def test_validation_error_raised(self):
    """Test CDOValidationError is raised."""
    with pytest.raises(CDOValidationError) as exc_info:
        # Code that should raise
        pass

    # Check exception fields
    assert exc_info.value.parameter == "expected_param"
    assert exc_info.value.value == "actual_value"
```

### Test Exception Message

```python
def test_error_message_content(self):
    """Test exception message contains expected text."""
    with pytest.raises(CDOExecutionError) as exc_info:
        # Code that should raise
        pass

    error_msg = str(exc_info.value)
    assert "expected text" in error_msg.lower()
```

## Testing Parsers

### Parser Test Template

```python
class TestNewParser:
    @pytest.fixture
    def parser(self):
        return NewParser()

    def test_parse_valid_output(self, parser):
        """Test parsing valid output."""
        output = "sample output"
        result = parser.parse(output)

        assert isinstance(result, ExpectedResult)
        assert result.field == "expected_value"

    def test_parse_missing_field_raises(self, parser):
        """Test parsing with missing field raises."""
        output = "incomplete output"

        with pytest.raises(CDOParseError) as exc_info:
            parser.parse(output)

        assert "missing" in str(exc_info.value).lower()

    def test_parse_invalid_format_raises(self, parser):
        """Test parsing invalid format raises."""
        output = "invalid"

        with pytest.raises(CDOParseError):
            parser.parse(output)
```

## Parameterized Tests

Use `@pytest.mark.parametrize` for multiple inputs:

```python
@pytest.mark.parametrize("year,expected", [
    (2020, "-selyear,2020"),
    (2021, "-selyear,2021"),
    (1999, "-selyear,1999"),
])
def test_select_year_values(self, sample_nc_file, year, expected):
    """Test select_year with different years."""
    q = CDO().query(sample_nc_file).select_year(year)
    assert expected in q.get_command()
```

## Running Tests

### All Tests
```bash
pytest
```

### Specific File
```bash
pytest tests/test_query.py -v
```

### Specific Test
```bash
pytest tests/test_query.py::TestCDOQuerySelection::test_select_var -v
```

### Skip Integration Tests
```bash
pytest -m "not integration"
```

### Only Integration Tests
```bash
pytest -m integration
```

### With Coverage
```bash
pytest --cov=python_cdo_wrapper --cov-report=html
```

### Verbose Output
```bash
pytest -v -s
```

## Test Organization Best Practices

### Group Related Tests in Classes

```python
class TestCDOQuerySelection:
    """Tests for selection operators."""

    def test_select_var(self, sample_nc_file):
        pass

    def test_select_level(self, sample_nc_file):
        pass


class TestCDOQueryStatistics:
    """Tests for statistical operators."""

    def test_year_mean(self, sample_nc_file):
        pass

    def test_field_mean(self, sample_nc_file):
        pass
```

### Use Descriptive Test Names

```python
# ❌ BAD
def test_1(self):
    pass

# ✅ GOOD
def test_select_var_single_variable(self):
    """Test selecting a single variable by name."""
    pass
```

### One Assert Per Concept

```python
# ❌ BAD - multiple unrelated assertions
def test_query(self):
    assert query.get_command() == expected
    assert query.input_file == file
    assert len(query.operators) == 1

# ✅ GOOD - focused assertion
def test_query_command_generation(self):
    """Test query generates correct command."""
    assert query.get_command() == expected
```

## Common Testing Issues

### Issue: Test passes locally but fails in CI

**Cause**: File path differences, CDO version differences

**Fix**: Use `tmp_path` fixture, mark as integration test

### Issue: Test flakiness

**Cause**: Race conditions, file cleanup issues

**Fix**: Use proper fixtures, ensure cleanup

### Issue: Tests too slow

**Cause**: Too many integration tests

**Fix**: Mock subprocess for unit tests

### Issue: Mock not working

**Cause**: Patching wrong location

**Fix**: Patch where used, not where defined

```python
# ❌ BAD
@patch("subprocess.run")

# ✅ GOOD
@patch("python_cdo_wrapper.core.subprocess.run")
```

## Test Coverage Goals

- **Query methods**: 100% command generation tests
- **Validation**: 100% validation error tests
- **Parsers**: 100% valid + invalid input tests
- **Integration**: Key workflows tested

## Checklist for New Feature

- [ ] Command generation test
- [ ] Validation test (if applicable)
- [ ] Chaining test
- [ ] Integration test (if appropriate)
- [ ] Edge case tests
- [ ] Error condition tests
- [ ] All tests pass locally
- [ ] All tests pass in CI

## Reference

- **Fixtures**: `tests/conftest.py`
- **Query tests**: `tests/test_query.py`
- **Parser tests**: `tests/test_parsers/*.py`
- **pytest docs**: https://docs.pytest.org/
