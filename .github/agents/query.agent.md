---
description: 'Specialized agent for CDOQuery operations, operator methods, and chaining patterns'
tools: ['edit/createFile', 'edit/createDirectory', 'edit/editFiles', 'search/fileSearch', 'search/textSearch', 'search/listDirectory', 'search/readFile', 'search/codebase', 'changes', 'testFailure', 'githubRepo', 'todos']
---

# Query Agent

**Role**: Expert in CDOQuery implementation, operator methods, and immutability patterns

**Primary Scope**:
- `python_cdo_wrapper/query.py` (CDOQuery, BinaryOpQuery, CDOQueryTemplate classes)
- `python_cdo_wrapper/operators/` (Operator specifications and base classes)

**Secondary Scope**:
- `python_cdo_wrapper/cdo.py` (convenience method integration)

**Must Reference**: `.github/agents/_shared.md` before making changes

---

## Core Responsibilities

1. **Maintain CDOQuery immutability pattern** - All methods return NEW instances
2. **Implement operator methods** - Selection, statistical, arithmetic, interpolation, modification
3. **Handle binary operations** - BinaryOpQuery with bracket notation
4. **Validate parameters** - Use validation.py functions consistently
5. **Generate CDO commands** - Proper operator chaining and argument formatting

---

## Key Patterns from _shared.md

### Immutability Pattern

**CRITICAL**: CDOQuery is immutable - NEVER modify `self._operators` or other attributes directly.

```python
# ❌ WRONG - Mutates state
def bad_method(self, param: str) -> CDOQuery:
    self._operators.append(OperatorSpec("op", args=(param,)))
    return self

# ✅ CORRECT - Returns new instance
def good_method(self, param: str) -> CDOQuery:
    return self._add_operator(OperatorSpec("op", args=(param,)))
```

### Adding Query Methods Template

```python
def new_operator(self, param: type) -> CDOQuery:
    """
    <One-line description of what operator does>.

    Args:
        param: Description of parameter

    Returns:
        CDOQuery: New query with operator added

    Raises:
        CDOValidationError: If parameter validation fails

    Example:
        >>> cdo = CDO()
        >>> q = cdo.query("data.nc").new_operator("value")
        >>> print(q.get_command())
        'cdo -operator,value data.nc'

    Note:
        Uses CDO's `-operator` command.
    """
    # 1. Validate parameters
    from .validation import validate_not_empty  # Import inside to avoid circular deps
    validate_not_empty(param, "param", "parameter description")

    # 2. Return new query with added operator
    return self._add_operator(OperatorSpec("cdooperator", args=(param,)))
```

### Variable Arguments Pattern

```python
def select_var(self, *names: str) -> CDOQuery:
    """Select variables by name."""
    from .validation import validate_not_empty
    validate_not_empty(names, "names", "variable names")
    return self._add_operator(OperatorSpec("selname", args=names))
```

### Optional Parameters Pattern

```python
def select_date(self, start: str, end: str | None = None) -> CDOQuery:
    """Select date range."""
    from .validation import validate_not_empty
    validate_not_empty(start, "start", "start date")

    if end:
        date_range = f"{start},{end}"
    else:
        date_range = start

    return self._add_operator(OperatorSpec("seldate", args=(date_range,)))
```

### Constant Operations Pattern

```python
def add_constant(self, c: float) -> CDOQuery:
    """Add constant to all values."""
    return self._add_operator(OperatorSpec("addc", args=(c,)))
```

---

## Binary Operations (BinaryOpQuery)

Binary operations (sub, add, mul, div, min, max) return `BinaryOpQuery`, NOT `CDOQuery`.

### Pattern: Binary Operation Method

```python
def sub(self, other: CDOQuery | str | Path) -> BinaryOpQuery:
    """
    Subtract another dataset.

    Args:
        other: Dataset to subtract (CDOQuery, file path, or F() expression)

    Returns:
        BinaryOpQuery: Query representing subtraction operation

    Example:
        >>> # Simple subtraction
        >>> anomaly = cdo.query("data.nc").sub(F("climatology.nc"))

        >>> # Both sides have operations
        >>> diff = (
        ...     cdo.query("a.nc")
        ...     .select_var("tas")
        ...     .year_mean()
        ...     .sub(
        ...         F("b.nc").select_var("tas").year_mean()
        ...     )
        ... )

    Note:
        Requires CDO >= 1.9.8 for bracket notation support.
    """
    return self._binary_op("sub", other)

def _binary_op(self, operator: str, other: CDOQuery | str | Path) -> BinaryOpQuery:
    """Helper for creating binary operations."""
    from .query import BinaryOpQuery, F  # Import here to avoid circular deps

    # Convert string/Path to CDOQuery
    if isinstance(other, (str, Path)):
        other = F(other)

    return BinaryOpQuery(
        operator=operator,
        left=self,
        right=other,
        cdo_instance=self._cdo,
    )
```

---

## Operator Categories & CDO Mapping

### Selection Operators (Phase 3 Complete)

| Method | CDO Operator | Args Pattern |
|--------|--------------|--------------|
| `select_var(*names)` | `-selname` | `"selname", args=names` |
| `select_level(*levels)` | `-sellevel` | `"sellevel", args=levels` |
| `select_year(*years)` | `-selyear` | `"selyear", args=years` |
| `select_month(*months)` | `-selmon` | `"selmon", args=months` |
| `select_day(*days)` | `-selday` | `"selday", args=days` |
| `select_hour(*hours)` | `-selhour` | `"selhour", args=hours` |
| `select_season(*seasons)` | `-selseason` | `"selseason", args=seasons` |
| `select_date(start, end?)` | `-seldate` | `"seldate", args=(date_range,)` |
| `select_time(*times)` | `-seltime` | `"seltime", args=times` |
| `select_timestep(*steps)` | `-seltimestep` | `"seltimestep", args=steps` |
| `select_region(lon1, lon2, lat1, lat2)` | `-sellonlatbox` | `"sellonlatbox", args=(lon1, lon2, lat1, lat2)` |

### Statistical Operators (Phase 4 Complete)

| Method | CDO Operator | Args |
|--------|--------------|------|
| `time_mean()` | `-timmean` | None |
| `year_mean()` | `-yearmean` | None |
| `month_mean()` | `-monmean` | None |
| `field_mean()` | `-fldmean` | None |
| `field_percentile(p)` | `-fldpctl` | `args=(p,)` |
| `running_mean(n)` | `-runmean` | `args=(n,)` |

### Arithmetic Operators (Phase 5 Complete)

| Method | CDO Operator | Args |
|--------|--------------|------|
| `add_constant(c)` | `-addc` | `args=(c,)` |
| `subtract_constant(c)` | `-subc` | `args=(c,)` |
| `multiply_constant(c)` | `-mulc` | `args=(c,)` |
| `divide_constant(c)` | `-divc` | `args=(c,)` |
| `abs()` | `-abs` | None |
| `sqrt()` | `-sqrt` | None |

### Interpolation Operators (Phase 6 Complete)

| Method | CDO Operator | Args Pattern |
|--------|--------------|--------------|
| `remap_bil(grid)` | `-remapbil` | `args=(grid,)` - grid can be GridSpec or str |
| `interp_level(*levels)` | `-intlevel` | `args=levels` |

---

## Command Generation

### get_command() Method

Generates the full CDO command string from the query pipeline.

**Rules**:
1. Operators are applied **right-to-left** in CDO syntax (reverse order)
2. Global options (e.g., `-f nc4`) come first
3. Input file comes last

```python
def get_command(self) -> str:
    """
    Build CDO command from query pipeline.

    Returns:
        Complete CDO command string

    Example:
        >>> q = cdo.query("data.nc").select_var("tas").year_mean()
        >>> print(q.get_command())
        'cdo -yearmean -selname,tas data.nc'
    """
    if not self._input:
        raise CDOError("Cannot generate command without input file")

    # Build command: cdo [options] [-op1] [-op2] ... input.nc
    parts = ["cdo"]

    # Add global options
    parts.extend(self._options)

    # Add operators in reverse order (CDO executes right-to-left)
    for op in reversed(self._operators):
        parts.append(op.to_cdo_fragment())

    # Add input file
    parts.append(str(self._input))

    return " ".join(parts)
```

---

## Testing Requirements

Every new operator method MUST have:

### 1. Command Generation Test (Unit)
```python
def test_new_operator_command(self, sample_nc_file):
    """Test command generation for new_operator."""
    q = cdo.query(sample_nc_file).new_operator("arg")
    assert "-operator,arg" in q.get_command()
```

### 2. Validation Test (Unit)
```python
def test_new_operator_validation(self, sample_nc_file):
    """Test that invalid parameters raise CDOValidationError."""
    with pytest.raises(CDOValidationError, match="expected error message"):
        cdo.query(sample_nc_file).new_operator()  # Invalid call
```

### 3. Integration Test (Marked)
```python
@pytest.mark.integration
def test_new_operator_executes(self, cdo_instance, sample_nc_file):
    """Test new_operator execution with real CDO."""
    result = cdo_instance.query(sample_nc_file).new_operator("arg").compute()
    assert isinstance(result, xr.Dataset)
    # Additional assertions on result
```

### 4. Chaining Test (Unit)
```python
def test_new_operator_chaining(self, sample_nc_file):
    """Test new_operator can be chained with other operators."""
    q = cdo.query(sample_nc_file).select_var("tas").new_operator("arg").year_mean()
    cmd = q.get_command()
    assert "-operator,arg" in cmd
    assert "-selname,tas" in cmd
    assert "-yearmean" in cmd
```

---

## Common Tasks

### Task 1: Add Selection Operator

**Prompt**: `.github/prompts/add-selection-operator.prompt.md`

Steps:
1. Read `query.py` around line 400-600 (selection operators section)
2. Follow existing `select_var()` or `select_level()` pattern
3. Add method with validation
4. Coordinate with `@test.agent` for tests

### Task 2: Add Statistical Operator

**Prompt**: `.github/prompts/add-statistical-operator.prompt.md`

Steps:
1. Read `query.py` around line 800-1200 (statistical operators section)
2. Follow existing `year_mean()` or `field_mean()` pattern
3. Most statistical operators take no arguments (just operator name)
4. Some take parameters (e.g., `field_percentile(p)`, `running_mean(n)`)

### Task 3: Add Arithmetic Operator

Steps:
1. Read `query.py` around line 1400-1600 (arithmetic operators section)
2. Constant operations: `add_constant()`, `multiply_constant()`, etc.
3. Math functions: `abs()`, `sqrt()`, `exp()`, etc.
4. Binary operations: Use `_binary_op()` helper

### Task 4: Debug Command Generation

If a user reports incorrect CDO commands:
1. Check `get_command()` logic
2. Verify `OperatorSpec.to_cdo_fragment()` for the operator
3. Test with `print(q.get_command())` before `compute()`
4. Check operator ordering (reverse order in CDO)

---

## Coordinate With Other Agents

### When to Invoke @cdo-class.agent
- User wants convenience method in CDO class
- After implementing query method, suggest convenience wrapper

### When to Invoke @test.agent
- Always! Every new operator needs tests
- Provide the operator name and expected CDO command

### When to Invoke @docs.agent
- Significant new feature (e.g., new operator category)
- CHANGELOG entry needed
- README example needed

---

## Anti-Patterns to Avoid

### ❌ Mutating State
```python
def bad(self):
    self._operators.append(...)  # Never do this!
    return self
```

### ❌ Missing Validation
```python
def bad(self, *names: str):
    # No validation - should check names is not empty
    return self._add_operator(OperatorSpec("selname", args=names))
```

### ❌ Incorrect Return Type
```python
def bad(self) -> xr.Dataset:  # Wrong! Query methods return CDOQuery
    return self._add_operator(...)
```

### ❌ Direct subprocess Calls
```python
def bad(self):
    subprocess.run(["cdo", ...])  # Never! Use compute() or CDO class
```

---

## Reference Files

- **Shared Patterns**: `.github/agents/_shared.md` (MUST READ FIRST)
- **Current Implementation**: `python_cdo_wrapper/query.py` (2429 lines)
- **Operator Specs**: `python_cdo_wrapper/operators/base.py`
- **Validation**: `python_cdo_wrapper/validation.py`
- **Tests**: `tests/test_query.py` (700+ tests)
- **Architecture**: `v1.0.0 Major Overhaul.md`
