# Fix Test Failure

## Context
Debugging and fixing a failing test in the test suite.

## Test Information

**Test File**: `{test_file}`
**Test Name**: `{test_name}`
**Test Class**: `{test_class}` (if applicable)
**Failure Type**: {failure_type} (e.g., AssertionError, CDOValidationError not raised, Integration failure)

## Failure Output

```
{failure_output}
```

## Test Code

```python
{test_code}
```

## Analysis Steps

### Step 1: Understand Test Intent

**What is the test checking?**
{test_intent}

**Expected behavior:**
{expected_behavior}

**Actual behavior:**
{actual_behavior}

### Step 2: Identify Root Cause

{root_cause_analysis}

## Fix Strategy

### Option 1: {fix_option_1_name}

**Approach**: {fix_option_1_approach}

**Implementation**:
```python
{fix_option_1_code}
```

**Pros**: {fix_option_1_pros}
**Cons**: {fix_option_1_cons}

### Option 2: {fix_option_2_name}

**Approach**: {fix_option_2_approach}

**Implementation**:
```python
{fix_option_2_code}
```

**Pros**: {fix_option_2_pros}
**Cons**: {fix_option_2_cons}

### Recommended Fix: {recommended_option}

{recommendation_rationale}

## Implementation

### Files to Change

#### 1. {file_1} - {change_1_description}

**Location**: Lines {start_line}-{end_line} or function `{function_name}`

**Current Code**:
```python
{current_code_1}
```

**Fixed Code**:
```python
{fixed_code_1}
```

**Explanation**: {explanation_1}

#### 2. {file_2} - {change_2_description} (if applicable)

**Location**: {location_2}

**Current Code**:
```python
{current_code_2}
```

**Fixed Code**:
```python
{fixed_code_2}
```

**Explanation**: {explanation_2}

## Verification Steps

### 1. Run Specific Test

```bash
pytest {test_file}::{test_class}::{test_name} -v
```

**Expected Output**:
```
{expected_test_output}
```

### 2. Run Related Tests

```bash
# Run all tests in test class
pytest {test_file}::{test_class} -v

# Run all tests in file
pytest {test_file} -v
```

### 3. Run Full Test Suite

```bash
pytest
```

### 4. Check Integration Tests (if applicable)

```bash
pytest -m integration
```

## Regression Check

Ensure fix doesn't break related functionality:

**Related Tests to Verify**:
- [ ] `{related_test_1}`
- [ ] `{related_test_2}`
- [ ] `{related_test_3}`

**Related Functionality**:
- [ ] {functionality_1}
- [ ] {functionality_2}

## Common Test Failure Patterns

### Pattern: AssertionError on Command Generation

**Symptom**: `assert "-operator,args" in cmd` fails

**Common Causes**:
1. Operator not added to query
2. Incorrect operator name
3. Arguments not formatted correctly

**Fix**: Check OperatorSpec and to_cdo_fragment()

### Pattern: Validation Error Not Raised

**Symptom**: `with pytest.raises(CDOValidationError)` fails

**Common Causes**:
1. Missing validation in method
2. Validation condition incorrect
3. Wrong exception type raised

**Fix**: Add/correct validation logic

### Pattern: Integration Test Failure

**Symptom**: Test works locally but fails in CI

**Common Causes**:
1. CDO not installed in CI
2. CDO version mismatch
3. File path issues

**Fix**: Check `@pytest.mark.integration`, use tmp_path

### Pattern: Mock Not Working

**Symptom**: Real subprocess called instead of mock

**Common Causes**:
1. Patching wrong location
2. Mock not in scope
3. Import order issues

**Fix**: Patch where used: `@patch("python_cdo_wrapper.core.subprocess.run")`

## Documentation Updates (if needed)

If test revealed documentation bug:

**CHANGELOG.md**:
```markdown
### Fixed
- Fixed {issue_description} ([#issue-number](link))
```

**Docstring Updates** (if applicable):
```python
def method():
    """
    {updated_docstring}
    """
```

## Acceptance Criteria

- [ ] Root cause identified
- [ ] Fix implemented
- [ ] Failing test now passes
- [ ] Related tests still pass
- [ ] Full test suite passes
- [ ] No new warnings or errors
- [ ] Integration tests pass (if applicable)
- [ ] Linters pass (`ruff check --fix . && ruff format .`)
- [ ] Type checker passes (if type-related)
- [ ] Documentation updated (if needed)

## Agent Coordination

### If Fix Requires Multiple Modules

**Coordinate with appropriate agents**:

```
@query.agent (if query.py change needed)
Fix validation in select_var() - should raise on empty names

@test.agent (if test itself is wrong)
Update test to match correct behavior

@docs.agent (if docstring fix needed)
Update docstring to match actual behavior
```

## Debugging Commands

### Print Debugging

```python
# Add to code
print(f"DEBUG: value = {value}")
print(f"DEBUG: command = {command}")

# Run with -s to see output
pytest {test_file}::{test_name} -v -s
```

### PDB Debugging

```python
# Add to code
import pdb; pdb.set_trace()

# Run test
pytest {test_file}::{test_name} -v -s
```

### Verbose Test Output

```bash
# Maximum verbosity
pytest {test_file}::{test_name} -vv -s

# Show local variables on failure
pytest {test_file}::{test_name} -vv --showlocals
```

## Reference

- **Testing Patterns**: `.github/instructions/testing-patterns.instructions.md`
- **Test Fixtures**: `tests/conftest.py`
- **Existing Tests**: `tests/test_query.py`, `tests/test_cdo_class.py`
- **pytest docs**: https://docs.pytest.org/

---

**Template Variables to Fill**:
- `{test_file}`: Test file path (e.g., "tests/test_query.py")
- `{test_name}`: Test function name
- `{test_class}`: Test class name (if applicable)
- `{failure_type}`: Type of failure
- `{failure_output}`: Actual test failure output
- `{test_code}`: Code of failing test
- `{test_intent}`: What test is checking
- `{expected_behavior}`: What should happen
- `{actual_behavior}`: What actually happens
- `{root_cause_analysis}`: Analysis of why test fails
- `{fix_option_N_name}`: Name of fix option
- `{fix_option_N_approach}`: Description of approach
- `{fix_option_N_code}`: Implementation code
- `{fix_option_N_pros}`: Advantages
- `{fix_option_N_cons}`: Disadvantages
- `{recommended_option}`: Which fix to use
- `{recommendation_rationale}`: Why this fix
- `{file_N}`: File to change
- `{change_N_description}`: What changes in file
- `{start_line}`, `{end_line}`: Line numbers
- `{function_name}`: Function to modify
- `{current_code_N}`: Current code
- `{fixed_code_N}`: Fixed code
- `{explanation_N}`: Why this fixes it
- `{expected_test_output}`: Expected test output after fix
- `{related_test_N}`: Related tests
- `{functionality_N}`: Related functionality
- `{issue_description}`: Description for changelog
- `{updated_docstring}`: Updated docstring if needed
