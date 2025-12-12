# Plan: Optimal GitHub Copilot Agent Workflow Architecture

Create a comprehensive, interconnected agent ecosystem with specialized agents, contextual instructions, and reusable prompts that mirror the modular architecture of python-cdo-wrapper for effective AI-assisted maintenance.

## Steps

1. **Create 7 specialized agents** in `.github/agents/` — `query.agent.md`, `parser.agent.md`, `cdo-class.agent.md`, `test.agent.md`, `types.agent.md`, `docs.agent.md`, and `refactor.agent.md` — each with defined tools, file scopes, and cross-agent references.

2. **Build contextual instructions** in `.github/instructions/` — `adding-operators.instructions.md`, `testing-patterns.instructions.md`, `type-definitions.instructions.md`, and `exception-handling.instructions.md` — with applyTo globs for automatic context injection.

3. **Design reusable prompt templates** in `.github/prompts/` — `add-selection-operator.prompt.md`, `add-statistical-operator.prompt.md`, `create-parser.prompt.md`, `add-info-command.prompt.md`, `fix-test-failure.prompt.md`, and `add-query-method.prompt.md` — following a structured input/output format.

4. **Enhance the existing** `copilot-instructions.md` with cross-references to agents/instructions/prompts and add an "Agent Routing" section to guide which agent handles which task.

5. **Create an orchestrator agent** (`orchestrator.agent.md`) that routes complex multi-module tasks to appropriate specialized agents and coordinates cross-cutting changes.

6. **Add agent metadata files** — `agents/README.md` for documentation, `agents/_shared.md` for common patterns, and an `agents/matrix.yml` for CI validation of agent consistency.

## Further Considerations

1. **Agent granularity**: Should `validation.agent.md` be separate or merged into `types.agent.md`? Recommend keeping separate for clearer ownership.

2. **Prompt versioning**: Should prompts include version numbers for tracking effectiveness? Recommend yes — e.g., `create-parser.v1.prompt.md`.

3. **Instruction activation**: Use `applyTo` globs vs manual `#file` references? Recommend `applyTo` for automatic context + explicit `#file` for complex tasks.

4. **Testing the agents**: Should we add a `.github/agents/tests/` directory with example inputs/outputs for validating agent behavior? Recommend yes for critical agents like `query.agent.md`.

---

## Detailed Architecture

### Directory Structure

```
.github/
├── agents/
│   ├── README.md                    # Agent documentation & usage guide
│   ├── _shared.md                   # Shared patterns across all agents
│   ├── orchestrator.agent.md        # Routes tasks to specialized agents
│   ├── query.agent.md               # CDOQuery, operators, chaining
│   ├── parser.agent.md              # Output parsing, result types
│   ├── cdo-class.agent.md           # CDO façade, file ops, info methods
│   ├── test.agent.md                # Test patterns, fixtures, mocking
│   ├── types.agent.md               # Type definitions, dataclasses
│   ├── docs.agent.md                # Documentation, README, CHANGELOG
│   └── refactor.agent.md            # Cross-cutting refactoring tasks
│
├── instructions/
│   ├── adding-operators.instructions.md      # applyTo: python_cdo_wrapper/query.py
│   ├── parser-development.instructions.md    # applyTo: parsers/**
│   ├── testing-patterns.instructions.md      # applyTo: tests/**
│   ├── type-definitions.instructions.md      # applyTo: python_cdo_wrapper/types/**
│   └── exception-handling.instructions.md    # applyTo: python_cdo_wrapper/exceptions.py
│
├── prompts/
│   ├── add-selection-operator.prompt.md      # Template for selection operators
│   ├── add-statistical-operator.prompt.md    # Template for statistical operators
│   ├── create-parser.prompt.md               # Template for new parsers
│   ├── add-info-command.prompt.md            # Template for CDO info commands
│   ├── fix-test-failure.prompt.md            # Structured debugging approach
│   └── add-query-method.prompt.md            # Generic query method template
│
├── copilot-instructions.md                   # Enhanced with agent routing
└── workflows/
    ├── tests.yml
    └── publish.yml
```

### Agent Specifications

#### 1. orchestrator.agent.md
**Purpose**: Route complex multi-module tasks to appropriate specialized agents

**Routing Rules**:
| Task Pattern | Route To |
|--------------|----------|
| "Add operator", "Add method to CDOQuery" | @query.agent.md |
| "Create parser", "Parse CDO output" | @parser.agent.md |
| "Add info command", "File operation" | @cdo-class.agent.md |
| "Write test", "Fix failing test" | @test.agent.md |
| "Add type", "Create dataclass" | @types.agent.md |
| "Update docs", "Write changelog" | @docs.agent.md |
| "Refactor code", "Clean up" | @refactor.agent.md |

#### 2. query.agent.md
**Scope**: `python_cdo_wrapper/query.py`, `python_cdo_wrapper/operators/`

**Responsibilities**:
- Maintain CDOQuery immutability pattern
- Implement new operator methods (selection, statistical, arithmetic, etc.)
- Handle BinaryOpQuery and bracket notation for binary ops
- Ensure proper `_add_operator()` usage
- Validate CDO command generation

**Key Patterns**:
```python
def new_operator(self, param: type) -> CDOQuery:
    """Description of operator."""
    if not param:
        raise CDOValidationError(...)
    return self._add_operator(OperatorSpec("cdooperator", args=(param,)))
```

#### 3. parser.agent.md
**Scope**: `python_cdo_wrapper/parsers/`, `python_cdo_wrapper/types/results.py`

**Responsibilities**:
- Implement CDOParser subclasses
- Design regex patterns for CDO output
- Create corresponding result dataclasses
- Handle edge cases in CDO output formats
- Maintain parser exports in `__init__.py`

**Key Patterns**:
```python
class NewParser(CDOParser[NewResult]):
    def parse(self, output: str) -> NewResult:
        # Regex parsing logic
        return NewResult(...)
```

#### 4. cdo-class.agent.md
**Scope**: `python_cdo_wrapper/cdo.py`

**Responsibilities**:
- Implement CDO façade methods
- Add info commands (sinfo, griddes, etc.)
- Implement file operations (merge, split, copy)
- Integrate parsers for structured output
- Maintain backward compatibility

#### 5. test.agent.md
**Scope**: `tests/`, `tests/conftest.py`

**Responsibilities**:
- Write unit tests (no CDO required)
- Write integration tests (mark with `@pytest.mark.integration`)
- Create fixtures for test scenarios
- Implement mocking patterns for subprocess
- Validate command generation

**Key Patterns**:
```python
# Command generation test (no CDO)
def test_method_command(self, sample_nc_file):
    q = cdo.query(sample_nc_file).method("arg")
    assert "-operator,arg" in q.get_command()

# Validation test
def test_method_validation(self, sample_nc_file):
    with pytest.raises(CDOValidationError):
        cdo.query(sample_nc_file).method()

# Integration test (requires CDO)
@pytest.mark.integration
def test_method_executes(self, cdo_instance, sample_nc_file):
    result = cdo_instance.query(sample_nc_file).method().compute()
    assert isinstance(result, xr.Dataset)
```

#### 6. types.agent.md
**Scope**: `python_cdo_wrapper/types/`, `python_cdo_wrapper/exceptions.py`

**Responsibilities**:
- Design dataclass structures for results
- Add property methods on result types
- Maintain type exports in `__init__.py`
- Handle type hint conventions
- Define exception types

#### 7. docs.agent.md
**Scope**: `README.md`, `CHANGELOG.md`, `MIGRATION_GUIDE.md`, docstrings

**Responsibilities**:
- Update README with new features
- Write CHANGELOG entries (Keep a Changelog format)
- Update migration guides
- Write Google-style docstrings
- Maintain API documentation

#### 8. refactor.agent.md
**Scope**: Entire workspace

**Responsibilities**:
- Perform cross-cutting refactoring tasks
- Rename variables/methods across multiple files
- Extract common logic into utility functions
- Clean up unused imports and dead code
- Standardize code style and formatting
- Update type hints to modern standards

---

### Instruction Specifications

#### adding-operators.instructions.md
```yaml
---
applyTo: "python_cdo_wrapper/query.py"
---
```
**Content**: Step-by-step guide for adding new operators to CDOQuery, including:
- Method signature conventions
- Validation requirements
- CDO operator mapping
- Test requirements
- Documentation requirements

#### parser-development.instructions.md
```yaml
---
applyTo: "python_cdo_wrapper/parsers/**"
---
```
**Content**: Guide for implementing CDO output parsers, including:
- CDOParser ABC pattern
- Regex best practices for CDO output
- Result dataclass design
- Error handling for malformed output
- Export checklist

#### testing-patterns.instructions.md
```yaml
---
applyTo: "tests/**"
---
```
**Content**: Testing conventions for the project, including:
- Test categories (unit vs integration)
- Fixture usage guide
- Mocking patterns
- Marker usage (@pytest.mark.integration)
- Coverage requirements

---

### Prompt Specifications

#### add-selection-operator.prompt.md
**Input Variables**:
- `$OPERATOR_NAME`: CDO operator name (e.g., "selcode")
- `$METHOD_NAME`: Python method name (e.g., "select_code")
- `$PARAMETERS`: Parameter spec (e.g., "*codes: int")
- `$DESCRIPTION`: What the operator does

**Output**: Complete implementation including:
1. Method in `query.py`
2. Unit test in `test_query.py`
3. Docstring with example
4. CHANGELOG entry

#### create-parser.prompt.md
**Input Variables**:
- `$CDO_COMMAND`: CDO command to parse (e.g., "partab")
- `$SAMPLE_OUTPUT`: Example CDO output
- `$RESULT_FIELDS`: Expected result structure

**Output**: Complete implementation including:
1. Parser class in `parsers/`
2. Result dataclass in `types/results.py`
3. Tests with sample output
4. Export in `__init__.py`

---

## Implementation Priority

### Phase 1: Foundation (Do First)
1. `_shared.md` - Common patterns all agents reference
2. `orchestrator.agent.md` - Task routing
3. `testing-patterns.instructions.md` - Most frequently needed

### Phase 2: Core Agents
4. `query.agent.md` - Primary abstraction
5. `parser.agent.md` - Complex parsing logic
6. `test.agent.md` - Validation layer

### Phase 3: Supporting Agents
7. `cdo-class.agent.md` - Façade methods
8. `types.agent.md` - Type definitions
9. `docs.agent.md` - Documentation

### Phase 4: Prompts & Instructions
10. All instruction files
11. All prompt templates
12. Update `copilot-instructions.md` with routing

---

## Governance & Conflict Resolution

### Handling Agent Conflicts

**Problem**: Multiple agents may need to modify the same files (e.g., `parser.agent` creates parsers, but `types.agent` owns the result dataclasses in `types/results.py`).

**Solution: Primary vs. Secondary Scope Pattern**

| Agent | Primary Scope (Exclusive Ownership) | Secondary Scope (Integration Only) |
|-------|-------------------------------------|-------------------------------------|
| **query.agent** | `query.py`, `operators/` | `cdo.py` (for convenience methods) |
| **parser.agent** | `parsers/*.py` | `types/results.py` (dataclasses) |
| **types.agent** | `types/`, `exceptions.py` | All files (type hints updates) |
| **test.agent** | `tests/`, `conftest.py` | All files (test additions) |
| **cdo-class.agent** | `cdo.py` | `query.py` (integration), `parsers/` (usage) |
| **refactor.agent** | None (coordinator only) | All files (cross-cutting changes) |
| **docs.agent** | `README.md`, `CHANGELOG.md`, `*.md` | All files (docstrings) |

### Conflict Resolution Rules

#### Rule 1: Primary Scope Wins
- When conflict occurs, the agent with **Primary Scope** has final say on implementation patterns.
- Example: If `parser.agent` needs a new result dataclass, it can create it in `types/results.py`, but must follow `types.agent` conventions from `_shared.md`.

#### Rule 2: Orchestrator Sequencing for Dependencies
- For tasks involving multiple Primary Scopes, the Orchestrator breaks them into sequential phases:

**Example: "Add new parser for `showformat` command"**
```
Phase 1: @types.agent - Create `ShowformatResult` dataclass in `types/results.py`
Phase 2: @parser.agent - Implement `ShowformatParser` using the new result type
Phase 3: @cdo-class.agent - Add `showformat()` method to CDO class
Phase 4: @test.agent - Write tests for all new components
Phase 5: @docs.agent - Update README and CHANGELOG
```

#### Rule 3: Shared Patterns via `_shared.md`
- All cross-cutting patterns are defined in `.github/agents/_shared.md` (the "constitution"):
  - Import ordering (ruff rules)
  - Type hint conventions
  - Docstring format (Google style)
  - Dataclass patterns (frozen, slots)
  - Exception handling patterns
  - Validation patterns

- Agents MUST reference `_shared.md` before modifying Secondary Scope files.

#### Rule 4: Refactor Agent as Coordinator
- `refactor.agent` has NO Primary Scope but can touch all files.
- It MUST consult other agents' patterns before making changes.
- For large refactors, it creates a refactoring plan and invokes specialized agents sequentially.

**Example: "Rename `_add_operator` to `_chain_operator`"**
```
refactor.agent:
  1. Analyze impact (query.py, 80+ method calls)
  2. Consult @query.agent for semantic correctness
  3. Execute rename across all files
  4. Invoke @test.agent to verify no breakage
```

### Preventing Style Conflicts

**Problem**: Agents may have different opinions on code formatting (e.g., line length, quote style).

**Solution**:
1. All agents MUST reference `_shared.md` which mirrors `pyproject.toml` ruff config.
2. Agents produce code, but final formatting is delegated to automated tools (`ruff format`).
3. Agent outputs are "semantically correct" not "perfectly formatted".

### Handling Circular Dependencies

**Problem**: `parser.agent` needs `types.agent`, but `types.agent` might need parser updates.

**Solution: Interface-First Development**
1. When creating interdependent features, the Orchestrator follows this order:
   - Step 1: Define interfaces/types (abstract)
   - Step 2: Implement concrete logic
   - Step 3: Wire up integration points

**Example: "Add new grid type with parser"**
```
Step 1: @types.agent - Define `GridType` enum, `GridSpec` dataclass
Step 2: @parser.agent - Implement parsing logic using new types
Step 3: @query.agent - Add grid manipulation methods
```

### Conflict Detection Mechanism

Add to `agents/matrix.yml` (CI validation):
```yaml
conflicts:
  - files: ["python_cdo_wrapper/types/results.py"]
    primary_owner: types.agent
    secondary_allowed: [parser.agent, cdo-class.agent]
    pattern_source: "_shared.md#dataclass-patterns"

  - files: ["python_cdo_wrapper/query.py"]
    primary_owner: query.agent
    secondary_allowed: [cdo-class.agent, refactor.agent]
    pattern_source: "_shared.md#immutability-pattern"
```

This allows automated checks: "Did `parser.agent` follow `types.agent` patterns when modifying `results.py`?"

---

## Success Metrics

1. **Reduced context switching**: Agents should contain all necessary context for their domain
2. **Consistent outputs**: Same prompt should produce structurally similar code
3. **Faster onboarding**: New contributors can use agents immediately
4. **Fewer review iterations**: Generated code follows project conventions
5. **Test coverage maintained**: Every agent-generated feature includes tests
6. **Zero agent conflicts**: Automated CI checks validate scope adherence

---
