# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Nothing yet

## [0.2.0] - 2025-12-10

### Added
- **Structured Output Support**: New `return_dict` parameter for `cdo()` function to parse text commands into Python dictionaries
- New `parsers.py` module with parsers for various CDO commands:
  - `GriddesParser` - Parse grid descriptions
  - `ZaxisdesParser` - Parse vertical axis information
  - `SinfoParser` - Parse dataset information
  - `VlistParser` - Parse variable lists
  - `ShowattsParser` - Parse variable attributes
  - `ShowattsglobParser` - Parse global attributes
  - `PartabParser` - Parse parameter tables
  - `VctParser` - Parse vertical coordinate tables
- New `types.py` module with TypedDict definitions:
  - `GridInfo`, `ZAxisInfo`, `DatasetInfo`, `VariableInfo`
  - `ParameterInfo`, `VCTInfo`, `AttributeDict`
  - `StructuredOutput` type alias
- `CDO_STRUCTURED_COMMANDS` constant listing all commands that support structured output
- `parse_cdo_output()` function for direct parsing of CDO output
- `get_supported_structured_commands()` function to query supported commands
- Comprehensive test suite for parsers and structured output functionality
- Documentation and examples for structured output in README

### Changed
- Enhanced `cdo()` function with `return_dict` parameter for structured output
- Updated type hints with additional overloads for `return_dict` parameter
- Expanded docstrings with structured output examples

### Features
- Parse `griddes` output into dictionaries with grid metadata
- Parse `sinfo` output into structured dataset information
- Parse `showatts`/`showattsglob` into nested attribute dictionaries
- Parse `zaxisdes` output into vertical coordinate information
- Parse `partab`/`codetab` into parameter lists
- Parse `vct`/`vct2` into numerical arrays
- Automatic fallback to text output if parsing fails
- Full backward compatibility - existing code continues to work unchanged

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

[Unreleased]: https://github.com/NarenKarthikBM/python-cdo-wrapper/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/NarenKarthikBM/python-cdo-wrapper/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/NarenKarthikBM/python-cdo-wrapper/releases/tag/v0.1.0
