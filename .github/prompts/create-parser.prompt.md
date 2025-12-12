# Create New CDO Output Parser

## Context
Creating a new parser to convert CDO text output into structured Python dataclass.

## Parser Details

**CDO Command**: `{cdo_command}`
**Parser Class**: `{ParserClassName}`
**Result Type**: `{ResultClassName}`
**Output Category**: {category} (e.g., grid info, variable info, file format)
**Purpose**: {brief_description}

## Sample CDO Output

```
{sample_output}
```

## Data Structure Requirements

### Fields to Extract
{fields_list}

### Computed Properties
{properties_list}

## Implementation Requirements

### 1. Result Dataclass (types/results.py)

Add frozen dataclass:
```python
@dataclass(frozen=True)
class {ResultClassName}:
    """
    Structured result from CDO's {cdo_command}.

    {extended_description}

    Attributes:
        {attributes_documentation}

    Example:
        >>> result = {ResultClassName}(
        ...     {example_fields}
        ... )
        >>> print(result.{example_property})
        {example_output}
    """

    {field_definitions}

    {property_methods}
```

### 2. Parser Class (parsers/{category}.py)

Create parser inheriting from CDOParser[T]:
```python
class {ParserClassName}(CDOParser[{ResultClassName}]):
    """
    Parser for CDO's {cdo_command} output.

    {parser_description}

    Example Input:
    \```
    {sample_output}
    \```
    """

    {class_level_patterns}

    def parse(self, output: str) -> {ResultClassName}:
        """
        Parse {cdo_command} output into structured result.

        Args:
            output: Raw text output from CDO {cdo_command}

        Returns:
            {ResultClassName}: Parsed structured result

        Raises:
            CDOParseError: If output format is unexpected

        Example:
            >>> parser = {ParserClassName}()
            >>> result = parser.parse(sample_output)
            >>> print(result.{example_field})
            {example_value}
        """
        lines = output.strip().split('\\n')

        {parsing_initialization}

        # Parse sections
        {parsing_logic}

        # Validate required fields
        {validation_logic}

        return {ResultClassName}({constructor_args})
```

### 3. Parser Tests (tests/test_parsers/test_{category}.py)

Create comprehensive test file:
```python
import pytest
from python_cdo_wrapper.parsers.{category} import {ParserClassName}
from python_cdo_wrapper.types.results import {ResultClassName}
from python_cdo_wrapper.exceptions import CDOParseError


# Sample CDO output fixtures
SAMPLE_OUTPUT = \"\"\"
{sample_output}
\"\"\"

SAMPLE_OUTPUT_MINIMAL = \"\"\"
{minimal_output}
\"\"\"

SAMPLE_OUTPUT_INVALID = \"\"\"
{invalid_output}
\"\"\"


class Test{ParserClassName}:
    @pytest.fixture
    def parser(self):
        return {ParserClassName}()

    def test_parse_valid_output(self, parser):
        """Test parsing valid {cdo_command} output."""
        result = parser.parse(SAMPLE_OUTPUT)

        assert isinstance(result, {ResultClassName})
        {field_assertions}

    def test_parse_minimal_output(self, parser):
        """Test parsing minimal valid output."""
        result = parser.parse(SAMPLE_OUTPUT_MINIMAL)

        assert isinstance(result, {ResultClassName})
        {minimal_assertions}

    def test_parse_missing_required_field_raises(self, parser):
        """Test parsing with missing required field."""
        output = "{output_missing_field}"

        with pytest.raises(CDOParseError) as exc_info:
            parser.parse(output)

        assert "{expected_error_text}" in str(exc_info.value).lower()

    def test_parse_invalid_format_raises(self, parser):
        """Test parsing invalid format raises error."""
        with pytest.raises(CDOParseError):
            parser.parse(SAMPLE_OUTPUT_INVALID)

    def test_parse_empty_output_raises(self, parser):
        """Test parsing empty output raises error."""
        with pytest.raises(CDOParseError):
            parser.parse("")

    {property_tests}
```

### 4. Integration with CDO Class (cdo.py)

Add method to CDO class:
```python
def {method_name}(self, input_file: str | Path) -> {ResultClassName}:
    """
    Get {description} using CDO's {cdo_command}.

    {extended_method_description}

    Args:
        input_file: Input NetCDF file

    Returns:
        {ResultClassName}: Structured result with {result_contents}

    Raises:
        CDOExecutionError: If CDO command fails
        CDOParseError: If output parsing fails

    Example:
        >>> cdo = CDO()
        >>> result = cdo.{method_name}("data.nc")
        >>> print(result.{example_field})
        {example_value}

    See Also:
        - {related_method_1}: {description_1}
        - {related_method_2}: {description_2}
    """
    output = self._execute_text_command(f"{cdo_command} {{input_file}}")
    return {ParserClassName}().parse(output)
```

### 5. Update Exports

**parsers/__init__.py**:
```python
from .{category} import {ParserClassName}

__all__ = [
    # ... existing exports ...
    "{ParserClassName}",
]
```

**types/results.py** (if new file):
```python
# Add to __all__
__all__ = [
    # ... existing exports ...
    "{ResultClassName}",
]
```

## Parsing Patterns

### Pattern: {pattern_1_name}
```python
{pattern_1_code}
```

### Pattern: {pattern_2_name}
```python
{pattern_2_code}
```

## Documentation Updates

**CHANGELOG.md**:
```markdown
### Added
- `{method_name}()` method returning structured `{ResultClassName}` ([#PR-number](link))
- `{ParserClassName}` for parsing CDO {cdo_command} output
```

**README.md** (Info Commands section):
```markdown
#### {cdo_command}

\```python
result = cdo.{method_name}("data.nc")
print(result.{example_field})  # {example_output}
\```
```

## Edge Cases to Handle

{edge_cases_list}

## Acceptance Criteria

- [ ] Result dataclass created in types/results.py
- [ ] Parser class created in parsers/{category}.py
- [ ] Parser inherits from CDOParser[{ResultClassName}]
- [ ] All required fields extracted
- [ ] Optional fields handled with defaults
- [ ] Property methods implemented
- [ ] Test file created with 5+ tests
- [ ] Test valid output parsing
- [ ] Test missing field error
- [ ] Test invalid format error
- [ ] Test empty output error
- [ ] Integration method added to CDO class
- [ ] Exports updated
- [ ] CHANGELOG.md updated
- [ ] README.md updated
- [ ] All tests pass (`pytest`)
- [ ] Linters pass (`ruff check --fix . && ruff format .`)

## Reference

- **Parser Development Guide**: `.github/instructions/parser-development.instructions.md`
- **Existing Parsers**: `python_cdo_wrapper/parsers/*.py`
- **Result Types**: `python_cdo_wrapper/types/results.py`
- **Parser Tests**: `tests/test_parsers/*.py`

---

**Template Variables to Fill**:
- `{cdo_command}`: CDO command (e.g., "griddes", "showformat")
- `{ParserClassName}`: Parser class name (e.g., "GriddesParser")
- `{ResultClassName}`: Result class name (e.g., "GriddesResult")
- `{category}`: Parser category (grid, info, format)
- `{brief_description}`: One-line description
- `{sample_output}`: Actual CDO output example
- `{fields_list}`: Fields to extract from output
- `{properties_list}`: Computed properties to add
- `{extended_description}`: Multi-line description
- `{attributes_documentation}`: Docstring for attributes
- `{example_fields}`: Example field values
- `{example_property}`: Property name for example
- `{example_output}`: Expected property output
- `{field_definitions}`: Dataclass field definitions
- `{property_methods}`: @property method definitions
- `{parser_description}`: Parser docstring
- `{class_level_patterns}`: Compiled regex patterns
- `{parsing_initialization}`: Initialize variables
- `{parsing_logic}`: Main parsing code
- `{validation_logic}`: Field validation
- `{constructor_args}`: Result constructor arguments
- `{minimal_output}`: Minimal valid output
- `{invalid_output}`: Invalid output example
- `{field_assertions}`: Assertions for fields
- `{minimal_assertions}`: Assertions for minimal case
- `{output_missing_field}`: Output with missing field
- `{expected_error_text}`: Expected error message
- `{property_tests}`: Tests for properties
- `{method_name}`: CDO class method name
- `{description}`: Method description
- `{extended_method_description}`: Extended description
- `{result_contents}`: What result contains
- `{example_field}`: Field for example
- `{example_value}`: Expected value
- `{related_method_N}`: Related methods
- `{pattern_N_name/code}`: Parsing patterns
- `{edge_cases_list}`: Edge cases to handle
