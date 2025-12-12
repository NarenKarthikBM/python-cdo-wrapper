# Agent Scope Validation Matrix

This file defines the scope boundaries for each agent to enable automated conflict detection in CI.

## Primary Scope (Exclusive Authority)

```yaml
agents:
  query:
    primary:
      - "python_cdo_wrapper/query.py"
      - "python_cdo_wrapper/operators/**/*.py"
    description: "CDOQuery implementation and operator definitions"

  parser:
    primary:
      - "python_cdo_wrapper/parsers/**/*.py"
      - "!python_cdo_wrapper/parsers/__init__.py"  # Shared
    description: "CDO output parsing logic"

  cdo-class:
    primary:
      - "python_cdo_wrapper/cdo.py"
    description: "CDO façade class and convenience methods"

  test:
    primary:
      - "tests/**/*.py"
      - "!tests/conftest.py"  # Shared
    description: "Test implementations (not fixtures)"

  types:
    primary:
      - "python_cdo_wrapper/types/**/*.py"
      - "python_cdo_wrapper/exceptions.py"
    description: "Type definitions and exceptions"

  docs:
    primary:
      - "*.md"
      - "!.github/**/*.md"  # Agent docs are shared
    description: "User-facing documentation"

  refactor:
    primary: []
    description: "No exclusive scope - coordinator only"
```

## Secondary Scope (Consultation Required)

```yaml
secondary_access:
  query:
    - "python_cdo_wrapper/validation.py"  # Can add validation utilities
    - "python_cdo_wrapper/parsers/__init__.py"  # Can import parsers
    consult: ["types"]  # Must consult types for new exceptions

  parser:
    - "python_cdo_wrapper/types/results.py"  # Can read types
    - "python_cdo_wrapper/parsers/__init__.py"  # Can export parsers
    consult: ["types"]  # Must consult for new result types

  cdo-class:
    - "python_cdo_wrapper/query.py"  # Can call query methods
    - "python_cdo_wrapper/parsers/**/*.py"  # Can use parsers
    consult: ["query", "parser"]  # Delegates to these

  test:
    - "tests/conftest.py"  # Can add fixtures
    - "python_cdo_wrapper/**/*.py"  # Can test all code
    consult: ["query", "parser", "cdo-class", "types"]  # Tests all

  types:
    - "python_cdo_wrapper/parsers/**/*.py"  # Types used by parsers
    consult: ["parser"]  # Parsers use types

  docs:
    - "**/*.py"  # Can update docstrings
    - ".github/**/*.md"  # Can update agent docs
    consult: ["all"]  # Documents all agents

  refactor:
    - "**/*.py"
    - "**/*.md"
    consult: ["all"]  # Must consult all for changes
```

## Shared Files (Multi-Agent Authority)

```yaml
shared:
  - ".github/agents/_shared.md"  # Source of truth - all agents
  - "tests/conftest.py"  # Test fixtures - test + specialists
  - "python_cdo_wrapper/__init__.py"  # Public API exports
  - "python_cdo_wrapper/parsers/__init__.py"  # Parser exports
  - "python_cdo_wrapper/types/__init__.py"  # Type exports
  - "pyproject.toml"  # Dependencies - orchestrator approval
  - "CHANGELOG.md"  # Version history - docs + orchestrator
```

## Conflict Resolution Rules

```yaml
conflict_resolution:
  rule_1:
    description: "Primary scope agent has final authority"
    example: "parser.agent creating new result type must consult types.agent, but types.agent has final say on dataclass design"

  rule_2:
    description: "Shared files require coordination"
    example: "Changes to conftest.py need test.agent approval, but other agents can propose fixtures"

  rule_3:
    description: "Cross-cutting changes require refactor.agent"
    example: "Renaming a symbol across multiple files requires refactor.agent coordination"

  rule_4:
    description: "Breaking changes require orchestrator approval"
    example: "Public API changes need orchestrator to coordinate deprecation"
```

## CI Validation

This matrix enables automated checks:

### Check 1: Primary Scope Violation
```bash
# Detect if agent modifies another agent's primary scope without approval
./scripts/check-agent-scope.sh --check-primary
```

### Check 2: Missing Consultation
```bash
# Detect if agent modifies secondary scope without consulting primary agent
./scripts/check-agent-scope.sh --check-consultation
```

### Check 3: Shared File Conflicts
```bash
# Detect if multiple agents modify shared files simultaneously
./scripts/check-agent-scope.sh --check-shared
```

## Usage in CI

```yaml
# .github/workflows/agent-validation.yml

name: Agent Scope Validation

on: [pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Check Primary Scope
        run: python scripts/validate_agent_scope.py --matrix .github/agents/matrix.yml
```

## Updating This Matrix

When adding a new agent:
1. Add to `agents` section with primary scope
2. Add to `secondary_access` with consultation rules
3. Update conflict resolution rules if needed
4. Update CI validation scripts

When changing file organization:
1. Update glob patterns in primary/secondary scopes
2. Update shared files list
3. Test validation scripts
4. Update agent documentation

---

**Note**: This is a specification file, not executable YAML. It documents the scope boundaries for human understanding and can be used as input to validation scripts.
