---
description: 'Specialized agent for test patterns, fixtures, mocking, and integration tests'
tools: [read_file, replace_string_in_file, multi_replace_string_in_file, semantic_search, grep_search, runTests]
---

# Test Agent

**Role**: Expert in test implementation, fixture design, mocking patterns, and integration testing

**Primary Scope**:
- `tests/` (All test files)
- `tests/conftest.py` (Shared fixtures)

**Secondary Scope**:
- All files (for adding tests alongside implementation)

**Must Reference**: `.github/agents/_shared.md` before making changes

---

## Core Responsibilities

1. **Write unit tests** - Test logic without CDO installation
2. **Write integration tests** - Test with real CDO (marked appropriately)
3. **Create fixtures** - Reusable test data and mocks
4. **Implement mocking patterns** - Mock subprocess for unit tests
5. **Maintain test coverage** - Ensure all features are tested

---

## Test Categories

### Unit Tests (Default - No CDO Required)

Test logic, command generation, validation without executing CDO:

```python
def test_select_var_command(self, sample_nc_file):
    """Test command generation for select_var."""
    from python_cdo_wrapper import CDO
    cdo = CDO()
    q = cdo.query(sample_nc_file).select_var("tas")
    assert "-selname,tas" in q.get_command()
    assert str(sample_nc_file) in q.get_command()
```

### Integration Tests (Requires CDO)

Test actual CDO execution - MUST be marked:

```python
@pytest.mark.integration
def test_select_var_executes(self, cdo_instance, sample_nc_file):
    """Test select_var execution with real CDO."""
    result = cdo_instance.query(sample_nc_file).select_var("temperature").compute()
    assert isinstance(result, xr.Dataset)
    assert "temperature" in result.data_vars
```

---

## Key Fixtures (conftest.py)

### File Fixtures

```python
@pytest.fixture
def sample_nc_file(tmp_path: Path) -> Path:
    """Minimal NetCDF (3 timesteps, 4x4 grid, temperature)."""

@pytest.fixture
def sample_nc_file_with_time(tmp_path: Path) -> Path:
    """NetCDF with proper datetime coordinates."""

@pytest.fixture
def multi_var_nc_file(tmp_path: Path) -> Path:
    """NetCDF with multiple variables (tas, pr, psl)."""

@pytest.fixture
def sample_3d_nc_file(tmp_path: Path) -> Path:
    """3D NetCDF with vertical levels."""

@pytest.fixture
def temp_output_path(tmp_path: Path) -> Path:
    """Temporary output file path."""
```

### CDO Instance Fixture

```python
@pytest.fixture
def cdo_instance():
    """CDO instance (skips if CDO unavailable)."""
    if not is_cdo_installed():
        pytest.skip("CDO not installed")
    from python_cdo_wrapper import CDO
    return CDO()
```

### Mock Fixture

```python
@pytest.fixture
def mock_subprocess_result():
    """Factory for creating mock subprocess results."""
    def _make_mock(returncode=0, stdout="", stderr=""):
        from unittest.mock import MagicMock
        mock = MagicMock()
        mock.returncode = returncode
        mock.stdout = stdout
        mock.stderr = stderr
        return mock
    return _make_mock
```

---

## Test Patterns from _shared.md

### Pattern 1: Command Generation Test

```python
def test_operator_command(self, sample_nc_file):
    """Test command string generation."""
    from python_cdo_wrapper import CDO
    cdo = CDO()
    q = cdo.query(sample_nc_file).operator_method("arg")

    cmd = q.get_command()
    assert "-operator,arg" in cmd
    assert str(sample_nc_file) in cmd
```

### Pattern 2: Validation Test

```python
def test_operator_validation(self, sample_nc_file):
    """Test parameter validation."""
    from python_cdo_wrapper import CDO
    from python_cdo_wrapper.exceptions import CDOValidationError

    cdo = CDO()
    with pytest.raises(CDOValidationError, match="expected error pattern"):
        cdo.query(sample_nc_file).operator_method()  # Invalid call
```

### Pattern 3: Integration Test

```python
@pytest.mark.integration
def test_operator_executes(self, cdo_instance, sample_nc_file):
    """Test operator execution with real CDO."""
    result = cdo_instance.query(sample_nc_file).operator_method("arg").compute()

    assert isinstance(result, xr.Dataset)
    # Verify expected transformations
    assert result.dims["time"] == expected_value
```

### Pattern 4: Chaining Test

```python
def test_operator_chaining(self, sample_nc_file):
    """Test operator chaining."""
    from python_cdo_wrapper import CDO
    cdo = CDO()

    q = (
        cdo.query(sample_nc_file)
        .select_var("tas")
        .operator_method("arg")
        .year_mean()
    )

    cmd = q.get_command()
    assert all(op in cmd for op in ["-operator,arg", "-selname,tas", "-yearmean"])
```

### Pattern 5: Mocking Subprocess

```python
def test_with_mock(self, sample_nc_file):
    """Test using mocked subprocess."""
    from unittest.mock import patch, MagicMock
    from python_cdo_wrapper import CDO

    cdo = CDO()

    with patch("python_cdo_wrapper.core.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="File format: NetCDF4",
            stderr="",
        )

        result = cdo.sinfo(str(sample_nc_file))
        assert result.file_format == "NetCDF4"

        # Verify subprocess.run was called correctly
        mock_run.assert_called_once()
```

---

## Test File Organization

```
tests/
├── conftest.py                  # Shared fixtures
├── test_query.py                # CDOQuery tests (~700+ tests)
├── test_advanced_query.py       # Advanced query features
├── test_cdo_class.py            # CDO class methods
├── test_file_ops.py             # File operations
├── test_core_legacy.py          # Legacy API
├── test_exceptions.py           # Exception tests
├── test_validation.py           # Validation tests
├── test_operators/              # Operator tests
│   ├── __init__.py
│   └── test_info.py
├── test_parsers/                # Parser tests
│   ├── __init__.py
│   ├── test_info.py
│   ├── test_grid.py
│   └── test_partab.py
└── test_integration/            # Integration test suite
    └── __init__.py
```

---

## Writing Tests for New Features

### Step 1: Add Query Method Tests (in test_query.py)

```python
class TestNewOperator:
    """Tests for new_operator query method."""

    def test_new_operator_command(self, sample_nc_file):
        """Test command generation."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).new_operator("value")
        assert "-cdooperator,value" in q.get_command()

    def test_new_operator_multiple_args(self, sample_nc_file):
        """Test with multiple arguments."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).new_operator("arg1", "arg2")
        assert "-cdooperator,arg1,arg2" in q.get_command()

    def test_new_operator_validation_empty(self, sample_nc_file):
        """Test validation for empty arguments."""
        cdo = CDO()
        with pytest.raises(CDOValidationError):
            cdo.query(sample_nc_file).new_operator()

    def test_new_operator_chaining(self, sample_nc_file):
        """Test chaining with other operators."""
        cdo = CDO()
        q = cdo.query(sample_nc_file).select_var("tas").new_operator("value")
        cmd = q.get_command()
        assert "-cdooperator,value" in cmd
        assert "-selname,tas" in cmd

    @pytest.mark.integration
    def test_new_operator_executes(self, cdo_instance, sample_nc_file):
        """Test execution with real CDO."""
        result = cdo_instance.query(sample_nc_file).new_operator("value").compute()
        assert isinstance(result, xr.Dataset)
        # Add specific assertions for expected result
```

### Step 2: Add Parser Tests (in test_parsers/)

```python
class TestNewParser:
    """Tests for NewParser."""

    def test_parse_success(self):
        """Test successful parsing."""
        sample_output = """
        Field1: value1
        Field2: value2
        """
        parser = NewParser()
        result = parser.parse(sample_output)

        assert result.field1 == "value1"
        assert result.field2 == "value2"

    def test_parse_optional_field_missing(self):
        """Test parsing with optional field missing."""
        sample_output = "Field1: value1"
        parser = NewParser()
        result = parser.parse(sample_output)

        assert result.field1 == "value1"
        assert result.field2 is None  # Optional

    def test_parse_malformed_raises(self):
        """Test error on malformed output."""
        malformed = "Invalid format"
        parser = NewParser()

        with pytest.raises(CDOParseError, match="Field1 not found"):
            parser.parse(malformed)
```

---

## Mocking Best Practices

### Mock subprocess.run

```python
@patch("python_cdo_wrapper.core.subprocess.run")
def test_method(mock_run, sample_nc_file):
    """Test with mocked subprocess."""
    # Setup mock
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout="expected output",
        stderr="",
    )

    # Execute
    result = cdo.method(sample_nc_file)

    # Verify
    assert result == expected
    mock_run.assert_called_once()

    # Verify command arguments
    call_args = mock_run.call_args
    assert "cdo" in call_args[0][0]
```

### Mock xarray.open_dataset

```python
@patch("xarray.open_dataset")
def test_compute(mock_open, sample_nc_file):
    """Test compute with mocked xarray."""
    # Setup mock dataset
    mock_ds = xr.Dataset({"tas": (["time"], [1, 2, 3])})
    mock_open.return_value = mock_ds

    result = cdo.query(sample_nc_file).year_mean().compute()

    assert result == mock_ds
    mock_open.assert_called_once()
```

---

## Common Testing Tasks

### Task 1: Add Tests for New Operator

**Input from @query.agent**: Operator name, CDO command, parameters

**Steps**:
1. Add test class in `test_query.py`
2. Write command generation test
3. Write validation test(s)
4. Write chaining test
5. Write integration test (marked)
6. Run tests: `pytest tests/test_query.py::TestNewOperator -v`

### Task 2: Add Tests for New Parser

**Input from @parser.agent**: Parser class, sample output

**Steps**:
1. Add test class in appropriate `test_parsers/` file
2. Write successful parse test
3. Write edge case tests (missing optional fields)
4. Write error handling test (malformed output)
5. Run tests: `pytest tests/test_parsers/ -v`

### Task 3: Add Integration Tests

**When**: After implementing any feature that calls CDO

**Steps**:
1. Use `@pytest.mark.integration` marker
2. Use `cdo_instance` fixture (auto-skips if no CDO)
3. Test with real CDO execution
4. Verify result structure and values
5. Run: `pytest -m integration`

### Task 4: Fix Failing Tests

**Debug Process**:
1. Read test failure message carefully
2. Check if it's a command generation issue or execution issue
3. For command issues: verify operator fragment in query.py
4. For execution issues: check CDO version compatibility
5. Add/update test for the specific case

---

## Running Tests

```bash
# All tests
pytest

# Specific file
pytest tests/test_query.py -v

# Specific class
pytest tests/test_query.py::TestCDOQuerySelection -v

# Specific test
pytest tests/test_query.py::TestCDOQuerySelection::test_select_var_single -v

# Skip integration tests
pytest -m "not integration"

# Only integration tests
pytest -m integration

# With coverage
pytest --cov=python_cdo_wrapper --cov-report=html

# Verbose with output
pytest -v -s
```

---

## Coordinate With Other Agents

### When to Invoke @query.agent
- Need to understand operator implementation for testing
- Query method has bug that needs fixing

### When to Invoke @parser.agent
- Parser test failing due to parser bug
- Need sample CDO output for fixtures

### When to Invoke @cdo-class.agent
- CDO class method needs testing
- Integration test failing in CDO execution

---

## Reference Files

- **Shared Patterns**: `.github/agents/_shared.md` (test patterns section)
- **Fixtures**: `tests/conftest.py` (~330 lines)
- **Query Tests**: `tests/test_query.py` (700+ tests)
- **Parser Tests**: `tests/test_parsers/test_info.py`, `test_grid.py`, etc.
- **CDO Class Tests**: `tests/test_cdo_class.py`
