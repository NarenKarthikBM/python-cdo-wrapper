# Contributing to Python CDO Wrapper

Thank you for your interest in contributing to python-cdo-wrapper! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## How to Contribute

### Reporting Bugs

1. Check if the issue already exists in [GitHub Issues](https://github.com/NarenKarthikBM/python-cdo-wrapper/issues)
2. If not, create a new issue with:
   - A clear, descriptive title
   - Steps to reproduce the issue
   - Expected vs actual behavior
   - Your environment (OS, Python version, CDO version)
   - Minimal code example if applicable

### Suggesting Features

1. Open a [GitHub Issue](https://github.com/NarenKarthikBM/python-cdo-wrapper/issues/new) with:
   - A clear description of the feature
   - Use cases and benefits
   - Any implementation ideas you have

### Pull Requests

1. Fork the repository
2. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Make your changes following our coding standards
4. Add tests for new functionality
5. Update documentation as needed
6. Run the test suite:
   ```bash
   pytest
   ```
7. Run code quality checks:
   ```bash
   ruff check .
   ruff format .
   mypy python_cdo_wrapper
   ```
8. Commit your changes with a clear message:
   ```bash
   git commit -m "Add feature: description of your changes"
   ```
9. Push and create a Pull Request

## Development Setup

### Prerequisites

- Python 3.9 or higher
- CDO installed on your system
- Git

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/python-cdo-wrapper.git
cd python-cdo-wrapper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev,test,docs]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=python_cdo_wrapper --cov-report=html

# Run only unit tests (no CDO required)
pytest -m "not integration"

# Run specific test file
pytest tests/test_core.py

# Run specific test
pytest tests/test_core.py::test_is_text_command
```

### Code Style

We use:
- **Ruff** for linting and formatting (replaces black, isort, flake8)
- **MyPy** for type checking

```bash
# Format code
ruff format .

# Check for lint errors
ruff check .

# Auto-fix lint errors where possible
ruff check --fix .

# Type checking
mypy python_cdo_wrapper
```

### Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`. To run manually:

```bash
pre-commit run --all-files
```

## Coding Standards

### General Guidelines

1. **Write clear, readable code** - Prioritize clarity over cleverness
2. **Add type hints** - All public functions should have type annotations
3. **Write docstrings** - Use Google-style docstrings for all public APIs
4. **Keep functions focused** - Each function should do one thing well
5. **Handle errors gracefully** - Use specific exception types with helpful messages

### Docstring Format

Use Google-style docstrings:

```python
def my_function(param1: str, param2: int = 10) -> bool:
    """
    Short description of the function.
    
    Longer description if needed, explaining the function's
    behavior, edge cases, etc.
    
    Args:
        param1: Description of param1.
        param2: Description of param2. Defaults to 10.
    
    Returns:
        Description of return value.
    
    Raises:
        ValueError: When param1 is empty.
    
    Example:
        >>> my_function("test", 5)
        True
    """
```

### Testing Guidelines

1. **Test naming**: Use descriptive names like `test_cdo_returns_string_for_sinfo`
2. **One assertion per test** when possible
3. **Use fixtures** for common setup
4. **Mark slow/integration tests** appropriately
5. **Test edge cases** and error conditions

Example test:

```python
import pytest
from python_cdo_wrapper.core import _is_text_command

def test_is_text_command_returns_true_for_sinfo():
    """Test that sinfo is correctly identified as a text command."""
    assert _is_text_command("sinfo data.nc") is True

def test_is_text_command_returns_false_for_yearmean():
    """Test that yearmean is correctly identified as a data command."""
    assert _is_text_command("yearmean data.nc") is False

@pytest.mark.integration
def test_cdo_sinfo_returns_string(sample_nc_file):
    """Integration test requiring CDO to be installed."""
    from python_cdo_wrapper import cdo
    result = cdo(f"sinfo {sample_nc_file}")
    assert isinstance(result, str)
```

## Project Structure

```
python-cdo-wrapper/
├── python_cdo_wrapper/      # Main package
│   ├── __init__.py          # Package exports
│   └── core.py              # Core functionality
├── tests/                   # Test suite
│   ├── conftest.py          # Pytest fixtures
│   ├── test_core.py         # Core module tests
│   └── data/                # Test data files
├── .github/                 # GitHub configuration
│   └── workflows/           # CI/CD workflows
├── pyproject.toml           # Project configuration
├── README.md                # Main documentation
├── CHANGELOG.md             # Version history
├── CONTRIBUTING.md          # This file
└── LICENSE                  # MIT license
```

## Release Process

Releases are managed by maintainers:

1. Update version in `python_cdo_wrapper/__init__.py`
2. Update version in `pyproject.toml`
3. Update `CHANGELOG.md` with release notes
4. Create a git tag: `git tag v0.x.x`
5. Push tag: `git push origin v0.x.x`
6. GitHub Actions will automatically publish to PyPI

## Getting Help

- Open a [GitHub Issue](https://github.com/NarenKarthikBM/python-cdo-wrapper/issues)
- Check existing issues and discussions
- Review the [README](README.md) and documentation

## Recognition

Contributors will be recognized in:
- The CHANGELOG for their specific contributions
- The GitHub contributors page

Thank you for contributing! 🎉
