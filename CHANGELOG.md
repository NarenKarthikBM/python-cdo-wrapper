# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-12

### Added - Core Architecture

- **Django ORM-style Query API**: Complete architectural overhaul with `CDOQuery` as the primary abstraction
  - Lazy evaluation: build pipelines, inspect commands before execution
  - Chainable methods: fluent API for complex workflows
  - Immutable queries: each operation returns a new query instance
  - Query introspection: `.get_command()`, `.explain()`, `.clone()`

- **F() Function**: Django F-expression pattern for binary operations
  - One-liner anomaly calculations: `query.sub(F("climatology.nc"))`
  - Supports nested operations with CDO bracket notation (requires CDO >= 1.9.8)
  - Process both sides before binary operation: `query.year_mean().sub(F("file").time_mean())`

- **BinaryOpQuery Class**: Specialized query class for binary operations
  - Automatic bracket notation generation for complex pipelines
  - Support for `.sub()`, `.add()`, `.mul()`, `.div()`, `.min()`, `.max()`

- **CDOQueryTemplate**: Reusable query templates with placeholders
  - Create standard analysis workflows
  - Apply to multiple files or parameters

### Added - Selection Operators (18 operators)

Query methods for data selection:
- `.select_var(*names)` - Select variables by name
- `.select_code(*codes)` - Select variables by code
- `.select_level(*levels)` - Select vertical levels
- `.select_level_idx(*indices)` - Select levels by index
- `.select_level_type(ltype)` - Select level type
- `.select_year(*years)` - Select years
- `.select_month(*months)` - Select months
- `.select_day(*days)` - Select days
- `.select_hour(*hours)` - Select hours
- `.select_season(*seasons)` - Select seasons (DJF, MAM, JJA, SON)
- `.select_date(start, end)` - Select date range
- `.select_time(*times)` - Select specific times
- `.select_timestep(*steps)` - Select timesteps by index
- `.select_region(lon1, lon2, lat1, lat2)` - Select lon/lat box
- `.select_index_box(x1, x2, y1, y2)` - Select index box
- `.select_mask(mask_file)` - Apply mask file
- `.select_grid(grid_num)` - Select grid number
- `.select_zaxis(zaxis_num)` - Select z-axis number

### Added - Statistical Operators (50+ operators)

**Time Statistics**: `.time_mean()`, `.time_sum()`, `.time_min()`, `.time_max()`, `.time_std()`, `.time_var()`, `.time_range()`

**Year/Month/Day/Hour/Season Statistics**:
- Yearly: `.year_mean()`, `.year_sum()`, `.year_min()`, `.year_max()`, `.year_std()`, `.year_var()`, `.year_range()`
- Monthly: `.month_mean()`, `.month_sum()`, `.month_min()`, `.month_max()`, `.month_std()`, `.month_var()`, `.month_range()`
- Daily: `.day_mean()`, `.day_sum()`, `.day_min()`, `.day_max()`, `.day_std()`, `.day_var()`, `.day_range()`
- Hourly: `.hour_mean()`, `.hour_sum()`, `.hour_min()`, `.hour_max()`, `.hour_std()`, `.hour_var()`, `.hour_range()`
- Seasonal: `.season_mean()`, `.season_sum()`, `.season_min()`, `.season_max()`, `.season_std()`, `.season_var()`, `.season_range()`

**Field (Spatial) Statistics**: `.field_mean()`, `.field_sum()`, `.field_min()`, `.field_max()`, `.field_std()`, `.field_var()`, `.field_range()`, `.field_percentile(p)`, `.zonal_mean()`, `.zonal_sum()`, `.meridional_mean()`, `.meridional_sum()`

**Vertical Statistics**: `.vert_mean()`, `.vert_sum()`, `.vert_min()`, `.vert_max()`, `.vert_std()`, `.vert_var()`, `.vert_int()`

**Running Statistics**: `.running_mean(n)`, `.running_sum(n)`, `.running_min(n)`, `.running_max(n)`, `.running_std(n)`, `.running_var(n)`

**Ensemble Statistics**: `.ens_mean()`, `.ens_sum()`, `.ens_min()`, `.ens_max()`, `.ens_std()`, `.ens_var()`, `.ens_range()`, `.ens_percentile(p)`

**Percentile Operations**: `.time_percentile(p)`, `.year_percentile(p)`, `.month_percentile(p)`, `.day_percentile(p)`

### Added - Arithmetic Operators (30+ operators)

**Binary Operations (with F())**:
- `.sub(F(file))` - Subtract another file
- `.add(F(file))` - Add another file
- `.mul(F(file))` - Multiply by another file
- `.div(F(file))` - Divide by another file
- `.min(F(file))` - Element-wise minimum
- `.max(F(file))` - Element-wise maximum

**Constant Arithmetic**:
- `.add_constant(c)`, `.sub_constant(c)`, `.mul_constant(c)`, `.div_constant(c)`
- `.pow_constant(c)`, `.mod_constant(c)`

**Math Functions**:
- `.abs()`, `.sqrt()`, `.sqr()`, `.exp()`, `.ln()`, `.log10()`
- `.sin()`, `.cos()`, `.tan()`, `.asin()`, `.acos()`, `.atan()`
- `.ceil()`, `.floor()`, `.round()`, `.trunc()`

**Masking Operations**:
- `.mask()` / `.ifthen()` - Apply mask
- `.where()` / `.ifthenelse()` - Conditional operation
- `.set_missval(val)` - Set missing value indicator
- `.miss_to_const(val)` - Replace missing with constant
- `.set_range_to_miss(min, max)` - Set range to missing

### Added - Interpolation Operators (9 operators)

**Horizontal Interpolation**:
- `.remap_bil(grid)` - Bilinear interpolation
- `.remap_bic(grid)` - Bicubic interpolation
- `.remap_nn(grid)` - Nearest neighbor
- `.remap_dis(grid)` - Distance-weighted average
- `.remap_con(grid)` - First-order conservative remapping
- `.remap_con2(grid)` - Second-order conservative remapping
- `.remap_laf(grid)` - Largest area fraction

**Vertical Interpolation**:
- `.interp_level(*levels)` - Interpolate to pressure levels
- `.ml_to_pl(*levels)` - Model levels to pressure levels

**Grid Specification Support**:
- `GridSpec` dataclass for defining target grids
- Predefined grids: `GridSpec.global_1deg()`, `GridSpec.global_half_deg()`
- `.to_cdo_string()` method for CDO grid description format

### Added - Modification Operators (15+ operators)

**Metadata Modification**:
- `.set_name(name)` - Set variable name
- `.set_code(code)` - Set variable code
- `.set_unit(unit)` - Set units
- `.set_level(*levels)` - Set level values
- `.set_level_type(ltype)` - Set level type
- `.set_grid(grid)` - Set grid
- `.set_grid_type(gtype)` - Set grid type
- `.invert_lat()` - Invert latitudes

**Time Axis Modification**:
- `.set_time_axis(date, time, inc)` - Set time axis
- `.set_ref_time(date, time)` - Set reference time
- `.set_calendar(calendar)` - Set calendar type
- `.shift_time(offset)` - Shift time by offset

**Attribute Modification**:
- `.set_attribute(name, val)` - Set NetCDF attribute
- `.del_attribute(name)` - Delete NetCDF attribute

### Added - Advanced Query Methods

**Django-inspired query shortcuts**:
- `.first()` - Get first timestep only
- `.last()` - Get last timestep only
- `.count()` - Get number of timesteps (returns int)
- `.exists()` - Check if query would return data (returns bool)
- `.values(*vars)` - Alias for `.select_var()`

**Query management**:
- `.get_operations()` - Get list of all operations in pipeline
- `.describe()` - Detailed query description

### Added - Info Commands with Structured Results

**CDO class methods returning dataclasses**:
- `cdo.sinfo(file)` → `SinfoResult` - Complete file information
- `cdo.info(file)` → `InfoResult` - Detailed dataset info
- `cdo.griddes(file)` → `GriddesResult` - Grid description
- `cdo.zaxisdes(file)` → `ZaxisdesResult` - Vertical axis info
- `cdo.vlist(file)` → `VlistResult` - Variable list
- `cdo.partab(file)` → `PartabResult` - Parameter table

**Result type features**:
- Type-safe access to all fields
- Helper methods (e.g., `info.var_names`, `info.time_range`)
- Comprehensive docstrings

### Added - File Operations

**CDO class methods for multi-file operations**:
- `cdo.merge(*files, output=None)` - Merge files (variables)
- `cdo.mergetime(*files, output=None)` - Merge time series
- `cdo.cat(*files, output=None)` - Concatenate files
- `cdo.copy(input, output)` - Copy file
- `cdo.splityear(file, prefix)` - Split by year
- `cdo.splitmon(file, prefix)` - Split by month
- `cdo.splitday(file, prefix)` - Split by day
- `cdo.splithour(file, prefix)` - Split by hour
- `cdo.splitname(file, prefix)` - Split by variable
- `cdo.splitlevel(file, prefix)` - Split by level
- `cdo.splittimestep(file, prefix, n)` - Split by timesteps

**Query option for format conversion**:
- `.output_format(fmt)` - Set output format (nc, nc4, nc4c, grb, grb2)

### Added - Type System

**Complete type hints throughout**:
- Full type coverage for all public APIs
- Generic types for query builders
- Literal types for specific values (e.g., seasons, calendar types)
- `py.typed` marker for PEP 561 compliance

**Exception hierarchy**:
- `CDOError` - Base exception
- `CDOExecutionError` - Command execution failed (with command, returncode, stdout, stderr)
- `CDOValidationError` - Invalid parameters (with parameter, value, expected)
- `CDOFileNotFoundError` - File not found (with file_path)
- `CDOParseError` - Output parsing failed

### Changed

- **Primary API**: `CDOQuery` is now the recommended interface (v0.2.x string API still fully supported)
- **CDO Class**: Now acts as factory and façade
  - `cdo.query(file)` creates lazy queries
  - Convenience methods delegate to query layer
  - Info methods return structured dataclasses
- **Minimum CDO version**: 1.9.8 for binary operations (bracket notation)
- **Operator implementation pattern**: All operators implemented as query methods first, then convenience wrappers
- **Result types**: Info commands return dataclasses instead of strings

### Deprecated

- Direct string commands with `cdo.run()` are legacy but still supported
- Use `CDOQuery` API for new code

### Fixed

- Proper handling of nested binary operations with bracket notation
- Consistent parameter validation across all operators
- Thread-safe temporary file management
- Memory-efficient handling of large files in query pipelines

### Documentation

- Complete README overhaul with Django ORM-style examples
- MIGRATION_GUIDE.md for upgrading from v0.x
- Real-world climate science examples
- API reference for all new classes and methods
- Comprehensive docstrings with examples for all operators

### Testing

- 700+ unit tests covering all query operations
- Integration tests for all operators (requires CDO)
- Parser tests with sample CDO output
- Binary operation tests with bracket notation
- Query introspection tests
- Type checking with mypy

### Performance

- Lazy evaluation: build complex pipelines without intermediate execution
- Query optimization: inspect and refine before running
- Efficient bracket notation for binary operations
- Minimal memory overhead for query building

## [0.2.1] - 2025-12-10

### Enhanced
- **SinfoParser Major Enhancement**: Complete parsing of all CDO sinfo output sections
  - Added comprehensive grid coordinates parsing with spatial resolution extraction
  - Added vertical coordinates parsing (surface, pressure, hybrid levels)
  - Added time coordinates parsing with temporal resolution calculation
  - Added metadata extraction (Institut, Source, Table, Steptype fields)
  - Automatic time resolution detection (hourly, daily, etc.)
  - Grid resolution extraction (lon/lat spacing)
  - Support for both new format (Institut/Source) and old format (Date/Time) variable lines

### Added
- Grid coordinate parsing:
  - Grid type, dimensions (xsize, ysize), and total points
  - Longitude/latitude start, end, resolution, and units
- Vertical coordinate parsing:
  - Vertical axis type and number of levels
- Time coordinate parsing:
  - Total timesteps, reference time, units, and calendar
  - Complete list of all timestep values
  - First and last timestep identification
  - Automatic time resolution calculation (regular/irregular intervals)
  - Human-readable interval descriptions ("1 day", "6 hours", etc.)
- Helper methods: `_parse_grid_line()`, `_parse_vertical_line()`, `_parse_time_line()`, `_finalize_time_parsing()`, `_calculate_time_resolution()`
- Comprehensive test coverage for all new parsing capabilities

### Changed
- SinfoParser now returns structured dictionary with sections: `metadata`, `variables`, `grid`, `vertical`, `time`
- Variable parsing supports both format variations in CDO output
- Enhanced numeric field parsing with proper type conversion and error handling

### Fixed
- Removed unused parameters in static parser methods (linting fixes)
- Removed commented-out code

## [0.2.0] - 2025-12-10

### Added
- **Structured Output Support**: New `return_dict` parameter for `cdo()` function to parse text commands into Python dictionaries
- New `parsers.py` module with parsers for various CDO commands:
  - `GriddesParser` - Parse grid descriptions
  - `ZaxisdesParser` - Parse vertical axis information
  - `SinfoParser` - Parse dataset information
  - `VlistParser` - Parse variable lists
  - `ShowattsParser` - Parse variable attributes
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
- Parse `showatts` into nested attribute dictionaries
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

[Unreleased]: https://github.com/NarenKarthikBM/python-cdo-wrapper/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/NarenKarthikBM/python-cdo-wrapper/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/NarenKarthikBM/python-cdo-wrapper/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/NarenKarthikBM/python-cdo-wrapper/releases/tag/v0.1.0
