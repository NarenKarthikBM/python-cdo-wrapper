# Add Info Command to CDO Class

## Context
Adding a new info command that queries CDO for file metadata and returns structured result.

## Command Details

**CDO Command**: `{cdo_command}`
**Method Name**: `{method_name}()`
**Purpose**: {brief_description}
**Returns**: {ResultClassName}

## Sample CDO Output

```
{sample_output}
```

## Implementation Requirements

This task spans multiple modules and requires coordination between agents.

### Phase 1: Define Result Type (@types.agent)

Create result dataclass in `types/results.py`:

```python
@dataclass(frozen=True)
class {ResultClassName}:
    """
    Structured result from CDO's {cdo_command} command.

    Attributes:
        {attributes_list}
    """

    {field_definitions}

    {property_methods}
```

### Phase 2: Create Parser (@parser.agent)

Create parser in `parsers/{category}.py`:

```python
class {ParserClassName}(CDOParser[{ResultClassName}]):
    """Parser for {cdo_command} output."""

    def parse(self, output: str) -> {ResultClassName}:
        """
        Parse {cdo_command} output.

        Args:
            output: Raw CDO output

        Returns:
            {ResultClassName}: Parsed result

        Raises:
            CDOParseError: If parsing fails
        """
        {parsing_logic}
```

### Phase 3: Add CDO Method (@cdo-class.agent)

Add method to CDO class in `cdo.py`:

```python
def {method_name}(self, input_file: str | Path) -> {ResultClassName}:
    """
    {method_description}

    This method executes CDO's `{cdo_command}` command and returns
    a structured result with {result_description}.

    Args:
        input_file: Input NetCDF file

    Returns:
        {ResultClassName}: Structured result containing:
            {return_details}

    Raises:
        CDOFileNotFoundError: If input file doesn't exist
        CDOExecutionError: If CDO command fails
        CDOParseError: If output parsing fails

    Example:
        >>> cdo = CDO()
        >>> result = cdo.{method_name}("data.nc")
        >>> print(result.{example_field})
        {example_value}

    See Also:
        - {related_command_1}: {description_1}
        - {related_command_2}: {description_2}

    Note:
        {usage_notes}
    """
    output = self._execute_text_command(f"{cdo_command} {{input_file}}")
    return {ParserClassName}().parse(output)
```

### Phase 4: Add Tests (@test.agent)

#### Parser Tests (tests/test_parsers/test_{category}.py)

```python
SAMPLE_{COMMAND_UPPER}_OUTPUT = \"\"\"
{sample_output}
\"\"\"


class Test{ParserClassName}:
    @pytest.fixture
    def parser(self):
        return {ParserClassName}()

    def test_parse_valid_output(self, parser):
        """Test parsing valid {cdo_command} output."""
        result = parser.parse(SAMPLE_{COMMAND_UPPER}_OUTPUT)

        assert isinstance(result, {ResultClassName})
        {parser_assertions}

    def test_parse_missing_field_raises(self, parser):
        """Test missing required field raises error."""
        output = "{incomplete_output}"

        with pytest.raises(CDOParseError) as exc_info:
            parser.parse(output)

        assert "{expected_error}" in str(exc_info.value).lower()
```

#### Integration Tests (tests/test_operators/test_info.py)

```python
@pytest.mark.integration
def test_{method_name}(self, sample_nc_file):
    """Test {method_name} returns structured result."""
    cdo = CDO()
    result = cdo.{method_name}(sample_nc_file)

    assert isinstance(result, {ResultClassName})
    {integration_assertions}


@pytest.mark.integration
def test_{method_name}_file_not_found(self):
    """Test {method_name} raises on missing file."""
    cdo = CDO()

    with pytest.raises(CDOFileNotFoundError):
        cdo.{method_name}("nonexistent.nc")
```

### Phase 5: Update Documentation (@docs.agent)

#### CHANGELOG.md

```markdown
### Added
- `{method_name}()` info command returning structured `{ResultClassName}` ([#PR-number](link))
- `{ParserClassName}` for parsing {cdo_command} output
- `{ResultClassName}` dataclass in types/results.py
```

#### README.md (Info Commands Section)

```markdown
### {cdo_command}

Get {description}:

\```python
from python_cdo_wrapper import CDO

cdo = CDO()
result = cdo.{method_name}("data.nc")

# Access structured fields
print(result.{field_1})  # {field_1_description}
print(result.{field_2})  # {field_2_description}

# Use computed properties
print(result.{property_1})  # {property_1_description}
\```
```

## Coordination Workflow

### Step 1: Create Result Type

```
@types.agent

Create {ResultClassName} dataclass in types/results.py with these fields:
{field_specifications}

Add properties:
{property_specifications}
```

### Step 2: Create Parser

```
@parser.agent

Create {ParserClassName} in parsers/{category}.py to parse:
{sample_output}

Extract fields for {ResultClassName}.
```

### Step 3: Add CDO Method

```
@cdo-class.agent

Add {method_name}() method to CDO class that:
1. Calls _execute_text_command(f"{cdo_command} {{input_file}}")
2. Parses with {ParserClassName}
3. Returns {ResultClassName}
```

### Step 4: Add Tests

```
@test.agent

Add tests for {method_name}():
1. Parser test in tests/test_parsers/test_{category}.py
2. Integration test in tests/test_operators/test_info.py
3. File not found test
```

### Step 5: Update Documentation

```
@docs.agent

Update docs for {method_name}():
1. CHANGELOG.md entry
2. README.md info commands section with example
```

## Expected Files Changed

- [ ] `python_cdo_wrapper/types/results.py` - Add {ResultClassName}
- [ ] `python_cdo_wrapper/parsers/{category}.py` - Add {ParserClassName}
- [ ] `python_cdo_wrapper/parsers/__init__.py` - Export {ParserClassName}
- [ ] `python_cdo_wrapper/cdo.py` - Add {method_name}()
- [ ] `tests/test_parsers/test_{category}.py` - Add parser tests
- [ ] `tests/test_operators/test_info.py` - Add integration tests
- [ ] `CHANGELOG.md` - Add entry
- [ ] `README.md` - Add example

## Acceptance Criteria

- [ ] {ResultClassName} dataclass created
- [ ] {ParserClassName} created and tested
- [ ] {method_name}() method added to CDO class
- [ ] Parser tests pass (valid, invalid, missing field)
- [ ] Integration test passes
- [ ] File not found test passes
- [ ] CHANGELOG.md updated
- [ ] README.md updated with example
- [ ] All exports updated
- [ ] All tests pass (`pytest`)
- [ ] Linters pass (`ruff check --fix . && ruff format .`)
- [ ] Type checker passes (`mypy python_cdo_wrapper`)

## Testing Checklist

```bash
# Run parser tests
pytest tests/test_parsers/test_{category}.py -v

# Run integration tests
pytest tests/test_operators/test_info.py::{test_method_name} -m integration -v

# Run all tests
pytest

# Check linting
ruff check --fix . && ruff format .

# Check types
mypy python_cdo_wrapper
```

## Reference

- **Adding Info Commands**: See `cdo.py` lines 500-800
- **Existing Parsers**: `parsers/info.py`, `parsers/grid.py`
- **Parser Guide**: `.github/instructions/parser-development.instructions.md`
- **Test Patterns**: `.github/instructions/testing-patterns.instructions.md`

---

**Template Variables to Fill**:
- `{cdo_command}`: CDO command name (e.g., "showformat", "gridtype")
- `{method_name}`: Python method name (e.g., "showformat", "gridtype")
- `{brief_description}`: One-line description
- `{ResultClassName}`: Result dataclass name (e.g., "ShowformatResult")
- `{sample_output}`: Example CDO output
- `{attributes_list}`: List of attributes with descriptions
- `{field_definitions}`: Dataclass field definitions
- `{property_methods}`: @property method definitions
- `{ParserClassName}`: Parser class name (e.g., "ShowformatParser")
- `{category}`: Parser category (info, grid, format)
- `{parsing_logic}`: Implementation of parse() method
- `{method_description}`: Method docstring first line
- `{result_description}`: What the result contains
- `{return_details}`: Bullet points of return value contents
- `{example_field}`: Field for example
- `{example_value}`: Expected value
- `{related_command_N}`: Related CDO methods
- `{description_N}`: Description of related command
- `{usage_notes}`: Special notes about usage
- `{COMMAND_UPPER}`: Command name in UPPER_CASE
- `{parser_assertions}`: Assertions for parser test
- `{incomplete_output}`: Output with missing field
- `{expected_error}`: Expected error message
- `{integration_assertions}`: Assertions for integration test
- `{field_N}`: Field names
- `{field_N_description}`: Field descriptions
- `{property_N}`: Property names
- `{property_N_description}`: Property descriptions
- `{field_specifications}`: Detailed field specs
- `{property_specifications}`: Detailed property specs
