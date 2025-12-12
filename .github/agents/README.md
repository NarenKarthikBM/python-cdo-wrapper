# GitHub Copilot Agents for python-cdo-wrapper

This directory contains specialized GitHub Copilot agents for maintaining the python-cdo-wrapper project.

## Quick Reference

| Agent | Primary Scope | When to Use |
|-------|---------------|-------------|
| **orchestrator** | Routing & coordination | Complex multi-module tasks |
| **query** | `query.py`, `operators/` | Adding/modifying CDOQuery operators |
| **parser** | `parsers/` | Creating/fixing output parsers |
| **cdo-class** | `cdo.py` | Adding convenience methods, info commands |
| **test** | `tests/`, `conftest.py` | Writing/fixing tests |
| **types** | `types/`, `exceptions.py` | Defining dataclasses, exceptions |
| **docs** | `*.md` files, docstrings | Documentation, changelog, migration guides |
| **refactor** | None (coordinator) | Cross-cutting refactoring |

## How to Use Agents

### Single Agent Task

For tasks confined to one module, mention the agent directly:

```
@query.agent

Add a select_code() operator that selects variables by code number.
Should use CDO's -selcode operator.
```

### Multi-Agent Task

For tasks spanning multiple modules, start with orchestrator:

```
@orchestrator

Add a new info command: showformat
Should return structured ShowformatResult
```

The orchestrator will coordinate with query.agent, parser.agent, types.agent, and test.agent.

### Refactoring Task

For cross-cutting changes:

```
@refactor.agent

Rename _add_operator to _chain_operator throughout codebase.
Ensure all tests still pass.
```

## Agent Coordination

Agents follow a **Primary vs. Secondary Scope** pattern:

- **Primary Scope**: Agent has exclusive authority
- **Secondary Scope**: Agent must consult Primary agent before changes

Example: parser.agent creating a new result type needs types.agent approval.

### Conflict Resolution

If agents disagree:
1. Primary Scope agent has final say
2. Consult `_shared.md` for coding standards
3. Escalate to orchestrator for mediation

## Shared Standards

All agents reference `_shared.md` for:
- Import ordering
- Type hint conventions
- Docstring format (Google style)
- Dataclass patterns
- Validation patterns
- Testing patterns

**Always check `_shared.md` before making changes in Secondary Scope.**

## Agent Architecture

```
┌─────────────────┐
│  orchestrator   │  ← Coordinates multi-agent workflows
└────────┬────────┘
         │
    ┌────┴────┬────────┬──────────┬────────┬────────┬──────────┐
    ▼         ▼        ▼          ▼        ▼        ▼          ▼
┌──────┐ ┌────────┐ ┌─────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐
│query │ │ parser │ │ cdo │ │ test │ │types │ │ docs │ │ refactor │
└──────┘ └────────┘ └─────┘ └──────┘ └──────┘ └──────┘ └──────────┘
    │         │        │        │        │        │          │
    └─────────┴────────┴────────┴────────┴────────┴──────────┘
                            │
                      ┌─────┴──────┐
                      │ _shared.md │  ← Source of truth
                      └────────────┘
```

## Examples

### Example 1: Add Selection Operator

```
@query.agent

Add select_region() operator:
- Takes lon1, lon2, lat1, lat2 parameters
- Uses CDO's -sellonlatbox operator
- Validate longitude range [-180, 180]
- Validate latitude range [-90, 90]
- Add comprehensive tests
```

**Agent Actions**:
1. Add method to CDOQuery in query.py
2. Add validation in validation.py
3. Coordinate with test.agent for tests

### Example 2: Add Info Command

```
@orchestrator

Add a gridtype command that returns grid type information.
```

**Orchestrator Actions**:
1. Route to cdo-class.agent: Add gridtype() method
2. Route to parser.agent: Create GridtypeParser
3. Route to types.agent: Create GridtypeResult dataclass
4. Route to test.agent: Add tests
5. Route to docs.agent: Update CHANGELOG and README

### Example 3: Fix Test Failure

```
@test.agent

Test test_select_var_empty_raises is failing.
CDOValidationError not being raised when names is empty.
```

**Agent Actions**:
1. Read test code
2. Identify validation gap
3. Coordinate with query.agent to add validation
4. Re-run tests

### Example 4: Document New Feature

```
@docs.agent

Just added F() function for binary operations.
Update README with examples and add CHANGELOG entry.
```

**Agent Actions**:
1. Add to CHANGELOG under [Unreleased] → Added
2. Add README section with examples
3. Verify code examples are correct

## Best Practices

### ✅ Do

- **Be specific**: Clearly describe what you want
- **Provide context**: Mention related code/issues
- **One task per request**: Don't combine unrelated tasks
- **Mention agent explicitly**: Use `@agent.name`
- **Check examples**: Refer to existing code patterns

### ❌ Don't

- **Mix concerns**: Feature + refactoring in one request
- **Skip consultation**: Refactoring without agent approval
- **Ignore tests**: Changes without running tests
- **Break API**: Public API changes without deprecation

## Routing Guide

### Task: Add operator/method

```
Is it a query chain method?  → @query.agent
Is it a convenience method?  → @cdo-class.agent
```

### Task: Fix/add parser

```
Parsing CDO output? → @parser.agent
```

### Task: Define types

```
New dataclass/exception? → @types.agent
```

### Task: Write/fix tests

```
Test-related task? → @test.agent
```

### Task: Update documentation

```
README/CHANGELOG/docstrings? → @docs.agent
```

### Task: Refactor code

```
Cross-cutting changes? → @refactor.agent
```

### Task: Complex multi-module

```
Spans multiple agents? → @orchestrator
```

## Advanced Workflows

### Workflow 1: Add Complete Feature

```
@orchestrator

Add complete support for CDO's sellevel operator:
1. Query method: select_level(*levels)
2. Convenience method: cdo.select_level()
3. Tests for both
4. Documentation
```

### Workflow 2: Fix Bug with Tests

```
@test.agent

Bug: select_date() fails with single date.

Steps:
1. Add failing test reproducing bug
2. Coordinate with @query.agent to fix
3. Verify test passes
```

### Workflow 3: Modernize Module

```
@refactor.agent

Modernize type hints in query.py:
- Add 'from __future__ import annotations'
- Replace Union/Optional with | syntax
- Ensure mypy passes
```

## Getting Help

- **Architecture**: See `.github/prompts/plan-agentWorkflowArchitecture.prompt.md`
- **Coding Standards**: See `.github/agents/_shared.md`
- **Instructions**: See `.github/instructions/*.instructions.md`
- **Prompts**: See `.github/prompts/*.prompt.md`

## Maintenance

Agents are living documents. To update:

1. Edit agent markdown file
2. Run tests to verify changes
3. Update this README if routing changes
4. Coordinate with orchestrator.agent if scope changes

---

**Version**: 1.0.0
**Last Updated**: 2025-01-XX
**Status**: Production Ready
