# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Nothing yet

## [0.1.0] - 2024-12-05

### Added
- Initial release of python-cdo-wrapper
- Core `cdo()` function with automatic text/data command detection
- Full xarray.Dataset integration for data commands
- Automatic temporary file management
- Custom `CDOError` exception with detailed error information
- `get_cdo_version()` utility function
- `list_operators()` utility function
- Comprehensive documentation and examples
- Full type hints with mypy support
- pytest test suite with integration tests
- GitHub Actions CI/CD pipeline
- Pre-commit hooks configuration

### Features
- Automatic detection of text-output vs data-output CDO commands
- Returns `str` for info commands (sinfo, griddes, etc.)
- Returns `tuple[xr.Dataset, str]` for data commands (yearmean, selname, etc.)
- Debug mode for troubleshooting
- Input file validation
- Support for custom output file paths

[Unreleased]: https://github.com/NarenKarthikBM/python-cdo-wrapper/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/NarenKarthikBM/python-cdo-wrapper/releases/tag/v0.1.0
