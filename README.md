# Python CDO Wrapper

[![PyPI version](https://badge.fury.io/py/python-cdo-wrapper.svg)](https://badge.fury.io/py/python-cdo-wrapper)
[![Python versions](https://img.shields.io/pypi/pyversions/python-cdo-wrapper.svg)](https://pypi.org/project/python-cdo-wrapper/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/NarenKarthikBM/python-cdo-wrapper/workflows/Tests/badge.svg)](https://github.com/NarenKarthikBM/python-cdo-wrapper/actions)

A simple, universal Python wrapper for [CDO (Climate Data Operators)](https://code.mpimet.mpg.de/projects/cdo/) with seamless xarray integration. Perfect for Jupyter notebooks and climate data analysis workflows.

## Features

- 🚀 **Simple API**: Single function to handle all CDO operations
- 📊 **Auto-detection**: Automatically detects text vs. data commands
- 🔄 **xarray Integration**: Returns xarray.Dataset for data operations
- 📖 **Structured Output**: Parse text commands into Python dictionaries
- 🧹 **Clean Output**: Automatic temp file management
- 🐛 **Debug Mode**: Easy troubleshooting with detailed output
- 📝 **Type Hints**: Full typing support for IDE autocompletion
- ⚡ **Zero Config**: Works out of the box

## Installation

```bash
pip install python-cdo-wrapper
```

### Prerequisites

CDO must be installed on your system:

```bash
# macOS (Homebrew)
brew install cdo

# Ubuntu/Debian
sudo apt install cdo

# Conda (recommended for HPC)
conda install -c conda-forge cdo
```

## Quick Start

```python
from python_cdo_wrapper import cdo

# Text commands return strings
info = cdo("sinfo data.nc")
print(info)

# Data commands return xarray.Dataset
ds, log = cdo("yearmean data.nc")
print(ds)

# Chain operators
ds, log = cdo("-yearmean -selname,temperature input.nc")
```

## Usage Examples

### Getting File Information

```python
from python_cdo_wrapper import cdo

# File structure info
info = cdo("sinfo data.nc")
print(info)

# Grid description
grid = cdo("griddes data.nc")
print(grid)

# Time information
times = cdo("showtimestamp data.nc")
print(times)

# Variable names
vars = cdo("showname data.nc")
print(vars)
```

### Structured Output (New in v0.2.0!)

Get structured dictionaries instead of raw text for easier programmatic access:

```python
from python_cdo_wrapper import cdo

# Get grid information as a dictionary
grid_dict = cdo("griddes data.nc", return_dict=True)
print(grid_dict["gridtype"])  # 'lonlat'
print(f"{grid_dict['xsize']} x {grid_dict['ysize']}")  # '360 x 180'
print(f"Resolution: {grid_dict['xinc']}°")  # 'Resolution: 1.0°'

# Get dataset information as structured data
info_dict = cdo("sinfo data.nc", return_dict=True)
print(info_dict["metadata"]["format"])  # 'NetCDF'
for var in info_dict["variables"]:
    print(f"Variable: {var['name']}")

# Get variable attributes
attrs = cdo("showatts data.nc", return_dict=True)
for var_name, var_attrs in attrs.items():
    print(f"{var_name}: {var_attrs.get('units', 'no units')}")

# Get global attributes
global_attrs = cdo("showattsglob data.nc", return_dict=True)
print(global_attrs.get("title", "No title"))

# Get vertical axis information
zaxis = cdo("zaxisdes data.nc", return_dict=True)
print(f"Levels: {zaxis['levels']}")
```

**Supported structured commands:**
- `griddes`, `griddes2` - Grid information
- `zaxisdes` - Vertical axis information
- `sinfo`, `info`, `infon`, `infov`, `sinfon`, `sinfov` - Dataset information
- `vlist` - Variable list
- `showatts` - Variable attributes
- `showattsglob` - Global attributes
- `partab`, `codetab` - Parameter tables
- `vct`, `vct2` - Vertical coordinate tables

### Data Processing

```python
from python_cdo_wrapper import cdo

# Calculate yearly mean
ds, log = cdo("yearmean input.nc")

# Select specific variable
ds, log = cdo("-selname,temperature input.nc")

# Select time range
ds, log = cdo("-seldate,2020-01-01,2020-12-31 input.nc")

# Regrid to different resolution
ds, log = cdo("-remapbil,r360x180 input.nc")

# Calculate field mean
ds, log = cdo("fldmean input.nc")

# Chain multiple operators
ds, log = cdo("-yearmean -selname,temp -sellonlatbox,-10,30,35,70 input.nc")
```

### Saving Output

```python
from python_cdo_wrapper import cdo

# Save to specific file (file persists)
ds, log = cdo("yearmean input.nc", output_file="output.nc")

# Without loading into xarray (useful for large files)
_, log = cdo("yearmean input.nc", output_file="output.nc", return_xr=False)
```

### Debugging

```python
from python_cdo_wrapper import cdo

# Enable debug mode for detailed output
ds, log = cdo("yearmean input.nc", debug=True)
# Output:
# CDO Command: cdo yearmean input.nc /tmp/xxx.nc
# Return code: 0
# Stdout: ...
# Stderr: ...
```

### Error Handling

```python
from python_cdo_wrapper import cdo, CDOError

try:
    ds, log = cdo("invalid_command data.nc")
except CDOError as e:
    print(f"CDO failed with code {e.returncode}")
    print(f"Command: {e.command}")
    print(f"Error: {e.stderr}")
except FileNotFoundError as e:
    print(f"File or CDO not found: {e}")
```

### Utility Functions

```python
from python_cdo_wrapper.core import get_cdo_version, list_operators

# Get CDO version
version = get_cdo_version()
print(version)

# List available operators
ops = list_operators()
print(ops)
```

## Text vs Data Commands

The wrapper automatically detects command types:

### Text Commands (return `str`)
These operators print information and don't produce NetCDF output:

| Category | Operators |
|----------|-----------|
| **File Info** | `sinfo`, `info`, `ninfo`, `tinfo`, `vlist` |
| **Grid** | `griddes`, `showgrid`, `showprojection` |
| **Variables** | `showname`, `showvar`, `showcode`, `showunit` |
| **Time** | `showdate`, `showtimestamp`, `showyear`, `showmonth` |
| **Counts** | `ntsteps`, `nvars`, `nlevels`, `ngrids` |

### Data Commands (return `tuple[xr.Dataset, str]`)
All other operators that produce NetCDF output:

| Category | Example Operators |
|----------|-------------------|
| **Statistics** | `yearmean`, `monmean`, `daymean`, `fldmean` |
| **Selection** | `selname`, `seldate`, `sellevel`, `sellonlatbox` |
| **Remapping** | `remapbil`, `remapcon`, `remapnn` |
| **Arithmetic** | `add`, `sub`, `mul`, `div`, `expr` |
| **Comparison** | `eq`, `ne`, `gt`, `lt` |

## API Reference

### `cdo(cmd, *, output_file=None, return_xr=True, return_dict=False, debug=False, check_files=True)`

Execute a CDO command and return results as Python objects.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cmd` | `str` | required | CDO command (without leading "cdo") |
| `output_file` | `str \| Path \| None` | `None` | Output file path (temp file if None) |
| `return_xr` | `bool` | `True` | Return xarray.Dataset for data commands |
| `return_dict` | `bool` | `False` | Parse text output into structured dict |
| `debug` | `bool` | `False` | Print detailed execution info |
| `check_files` | `bool` | `True` | Validate input files exist |

**Returns:**
- Text commands: `str` (default) or `dict | list[dict]` (with `return_dict=True`)
- Data commands: `tuple[xr.Dataset, str]` or `tuple[None, str]`

**Raises:**
- `CDOError`: CDO command failed
- `FileNotFoundError`: CDO not installed or input file missing

## Configuration

### Environment Variables

The wrapper uses the system CDO installation. You can configure CDO behavior with standard environment variables:

```bash
# Set CDO temp directory
export CDO_TMPDIR=/path/to/tmp

# Set number of OpenMP threads
export OMP_NUM_THREADS=4
```

## Comparison with Other Libraries

| Feature | python-cdo-wrapper | python-cdo | cdo-bindings |
|---------|-------------------|------------|--------------|
| Simple API | ✅ Single function | ❌ Object-oriented | ❌ Complex |
| Auto text detection | ✅ | ❌ | ❌ |
| xarray integration | ✅ Native | ⚠️ Manual | ⚠️ Manual |
| Temp file cleanup | ✅ Automatic | ⚠️ Manual | ⚠️ Manual |
| Type hints | ✅ Full | ❌ | ❌ |
| Dependencies | Minimal | Heavy | Heavy |

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/NarenKarthikBM/python-cdo-wrapper.git
cd python-cdo-wrapper

# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=python_cdo_wrapper

# Run only unit tests (no CDO required)
pytest -m "not integration"

# Run integration tests (requires CDO)
pytest -m integration
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type check
mypy python_cdo_wrapper
```

### Building

```bash
# Build package
hatch build

# Check package
twine check dist/*
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [CDO (Climate Data Operators)](https://code.mpimet.mpg.de/projects/cdo/) by MPI-M
- [xarray](https://docs.xarray.dev/) for N-dimensional labeled arrays
- Climate research community for feedback and testing

## Citation

If you use this package in your research, please consider citing:

```bibtex
@software{python_cdo_wrapper,
  title = {Python CDO Wrapper},
  author = {B M Naren Karthik},
  year = {2024},
  url = {https://github.com/NarenKarthikBM/python-cdo-wrapper},
}
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes.

---

Made with ❤️ for the climate science community
