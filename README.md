# Python CDO Wrapper

[![PyPI version](https://badge.fury.io/py/python-cdo-wrapper.svg)](https://badge.fury.io/py/python-cdo-wrapper)
[![Python versions](https://img.shields.io/pypi/pyversions/python-cdo-wrapper.svg)](https://pypi.org/project/python-cdo-wrapper/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/NarenKarthikBM/python-cdo-wrapper/workflows/Tests/badge.svg)](https://github.com/NarenKarthikBM/python-cdo-wrapper/actions)

A **Django ORM-inspired**, type-safe Python wrapper for [CDO (Climate Data Operators)](https://code.mpimet.mpg.de/projects/cdo/) with seamless xarray integration. Build complex CDO pipelines with **lazy evaluation**, **chainable queries**, and **one-liner anomaly calculations**.

## ✨ What's New in v1.0.0

**Complete architectural overhaul** with Django ORM-style query API:

```python
from python_cdo_wrapper import CDO, F

cdo = CDO()

# 🔗 Chainable query building (lazy evaluation)
ds = (
    cdo.query("data.nc")
    .select_var("tas")
    .select_year(2020, 2021, 2022)
    .year_mean()
    .field_mean()
    .compute()
)

# 🎯 One-liner anomaly calculation with F()
anomaly = cdo.query("monthly_data.nc").sub(F("climatology.nc")).compute()

# 🔍 Inspect before execution
query = cdo.query("data.nc").select_var("tas").year_mean()
print(query.get_command())  # "cdo -yearmean -selname,tas data.nc"
```

**See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for upgrading from v0.x**

## Features

### v1.0.0 - Django ORM-Style Query API (NEW!)

- 🔗 **Lazy Query Chaining**: Build complex pipelines with readable, chainable methods
- 🎯 **F() Function**: Django F-expression pattern for binary operations (anomalies in one line!)
- 🔍 **Query Introspection**: `.get_command()`, `.explain()`, `.clone()` before execution
- 🌲 **Query Branching**: Clone base queries for multiple analyses
- 📋 **Query Templates**: Reusable pipeline patterns with placeholders
- ✅ **Full Type Safety**: Complete IDE autocompletion for all operators
- 📊 **Structured Results**: All info commands return typed dataclasses
- 🔁 **Immutable Queries**: Each operation returns a new query instance

### v0.2.x - Legacy API (Still Supported!)

- 🚀 **Simple API**: Single function to handle all CDO operations
- 📊 **Auto-detection**: Automatically detects text vs. data commands
- 🔄 **xarray Integration**: Returns xarray.Dataset for data operations
- 📖 **Structured Output**: Parse text commands into Python dictionaries
- 🧹 **Clean Output**: Automatic temp file management
- 🐛 **Debug Mode**: Easy troubleshooting with detailed output

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

### v1.0.0 API (Recommended)

```python
from python_cdo_wrapper import CDO, F

cdo = CDO()

# ============================================================
# PRIMARY API: Django ORM-style lazy query chaining
# ============================================================

# Build a lazy query - nothing executed yet
query = (
    cdo.query("data.nc")
    .select_var("tas")
    .select_year(2020, 2021, 2022)
    .year_mean()
    .field_mean()
)

# Inspect before running
print(query.get_command())
# Output: "cdo -fldmean -yearmean -selyear,2020,2021,2022 -selname,tas data.nc"

# Execute and get xarray.Dataset
ds = query.compute()

# ============================================================
# ONE-LINER ANOMALY CALCULATION with F()
# ============================================================
anomaly = cdo.query("monthly_data.nc").sub(F("climatology.nc")).compute()

# Standardized anomaly: (data - mean) / std
std_anomaly = (
    cdo.query("data.nc")
    .sub(F("climatology.nc"))
    .div(F("std_dev.nc"))
    .compute()
)

# ============================================================
# STRUCTURED INFO COMMANDS (CDO class methods)
# ============================================================
info = cdo.sinfo("data.nc")  # Returns SinfoResult dataclass
print(info.var_names)        # ['tas', 'pr', 'psl']
print(info.nvar)             # 3
print(info.time_range)       # ('2020-01-01', '2022-12-31')

grid = cdo.griddes("data.nc")  # Returns GriddesResult
print(grid.grids[0].gridtype)  # 'lonlat'

# ============================================================
# INFO OPERATORS AS QUERY TERMINATORS (NEW!)
# ============================================================
# Get info about processed data - no need for intermediate files!
vars = cdo.query("data.nc").year_mean().showname()  # ['tas', 'pr']
n_times = cdo.query("data.nc").select_year(2020).ntime()  # 12
grid = cdo.query("data.nc").remap_bil("r180x90").griddes()  # GriddesResult

# Chain processing and get metadata in one line
dates = (
    cdo.query("data.nc")
    .select_var("tas")
    .select_year(2020, 2021)
    .showdate()  # Returns list of dates after selection
)
```

### v0.2.x API (Legacy - Still Works!)

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

### v1.0.0 API - Query Chaining

#### Selection and Statistical Operations

```python
from python_cdo_wrapper import CDO

cdo = CDO()

# Select variables and compute statistics
ds = (
    cdo.query("era5_global.nc")
    .select_var("tas", "pr")
    .select_year(2020, 2021, 2022)
    .select_region(lon1=-10, lon2=40, lat1=35, lat2=70)  # Europe
    .year_mean()
    .compute()
)

# Multiple temporal selections
winter_data = (
    cdo.query("data.nc")
    .select_season("DJF")
    .select_hour(0, 6, 12, 18)
    .time_mean()
    .compute()
)

# Vertical selection
upper_air = (
    cdo.query("pressure_data.nc")
    .select_var("ta")
    .select_level(500, 700, 850)  # hPa
    .vert_mean()
    .compute()
)
```

#### Binary Operations with F()

Binary operations use CDO's operator chaining (not bracket notation):

```python
from python_cdo_wrapper import CDO, F

cdo = CDO()

# Simple anomaly (ONE LINE!)
anomaly = cdo.query("monthly_data.nc").sub(F("climatology.nc")).compute()
# Generates: cdo -sub monthly_data.nc climatology.nc

# Standardized anomaly: (data - mean) / std
std_anomaly = (
    cdo.query("data.nc")
    .sub(F("climatology.nc"))
    .div(F("std_dev.nc"))
    .compute()
)
# Generates: cdo -div -sub data.nc climatology.nc std_dev.nc

# With operators: CDO chains operators to their respective files
# No temporary files or brackets needed!
temp_diff = (
    cdo.query("data.nc")
    .select_var("tas")
    .year_mean()
    .sub(F("climatology.nc").time_mean())
    .compute()
)
# Generates: cdo -sub -yearmean -selname,tas data.nc -timmean climatology.nc

# Model bias calculation with operators on both sides - single command!
bias = (
    cdo.query("model_output.nc")
    .select_var("tas")
    .year_mean()
    .sub(
        F("observations.nc").select_var("tas").year_mean()
    )
    .compute()
)
# Generates: cdo -sub -yearmean -selname,tas model_output.nc -yearmean -selname,tas observations.nc
```

**Note**: CDO applies operators to files from left to right. Binary operators (sub, add, mul, div) use operator chaining, not bracket notation - that's only for variadic operators like merge/cat.
```

#### Query Introspection and Branching

```python
from python_cdo_wrapper import CDO

cdo = CDO()

# Build base query
base = (
    cdo.query("era5_global.nc")
    .select_var("tas")
    .select_year(2020, 2021, 2022)
)

# Inspect command before execution
print(base.get_command())
# Output: "cdo -selyear,2020,2021,2022 -selname,tas era5_global.nc"

print(base.explain())
# Output: Human-readable description of pipeline

# Branch for different analyses
annual_mean = base.clone().year_mean().compute()
monthly_clim = base.clone().month_mean().compute()
spatial_std = base.clone().time_std().compute()

# Advanced query methods (Django-like)
first_timestep = base.first()  # Get first timestep only
last_timestep = base.last()    # Get last timestep only
num_timesteps = base.count()   # Get number of timesteps
has_data = base.exists()       # Check if data exists
```

#### Interpolation and Regridding

```python
from python_cdo_wrapper import CDO
from python_cdo_wrapper.types import GridSpec

cdo = CDO()

# Regrid to standard grid
ds = (
    cdo.query("high_res_data.nc")
    .select_var("tas")
    .remap_bil(GridSpec.global_1deg())  # Bilinear to 1° grid
    .year_mean()
    .compute()
)

# Conservative remapping for flux variables
flux = (
    cdo.query("model_output.nc")
    .select_var("pr")
    .remap_con("r360x180")  # First-order conservative
    .compute()
)

# Regrid to match another file's grid
matched = (
    cdo.query("source.nc")
    .remap_bil("target_grid.nc")
    .compute()
)
```

#### Modification Operations

```python
from python_cdo_wrapper import CDO

cdo = CDO()

# Metadata modification
cleaned = (
    cdo.query("raw_data.nc")
    .set_name("temperature")
    .set_unit("Celsius")
    .set_missval(-999.0)
    .compute("cleaned.nc")
)

# Convert Kelvin to Celsius in pipeline
celsius = (
    cdo.query("tas_kelvin.nc")
    .sub_constant(273.15)
    .set_unit("Celsius")
    .compute()
)
```

#### Shapefile Masking

Clip NetCDF data to shapefile polygon extents in a single chainable method.

**Installation with shapefile support:**
```bash
pip install python-cdo-wrapper[shapefiles]
```

**Basic usage:**
```python
from python_cdo_wrapper import CDO

cdo = CDO()

# Mask to a region
regional_data = cdo.query("global_temperature.nc").mask_by_shapefile(
    "amazon_basin.shp"
).compute()

# Chain with other operators
yearly_regional = (
    cdo.query("daily_data.nc")
    .mask_by_shapefile("west_africa.shp")
    .year_mean()
    .field_mean()
    .compute()
)

# Custom coordinate names
masked = cdo.query("data.nc").mask_by_shapefile(
    "region.shp",
    lat_name="latitude",
    lon_name="longitude"
).compute()
```

**Features:**
- Complete automated pipeline: load shapefile → create mask → apply → cleanup
- Supports 1D (regular) and 2D (curvilinear) grids
- Automatic CRS reprojection to WGS84 if needed
- Multi-polygon shapefile support
- Temporary files automatically cleaned up

**Advanced usage - reusable masks:**
```python
from python_cdo_wrapper import create_mask_from_shapefile

# Create and save mask for reuse
mask_ds = create_mask_from_shapefile(
    shapefile_path="region.shp",
    reference_nc="data.nc"
)
mask_ds.to_netcdf("region_mask.nc")

# Reuse saved mask
masked = cdo.query("data.nc").select_mask("region_mask.nc").compute()
```

#### Structured Info Commands (v1.0.0)

```python
from python_cdo_wrapper import CDO

cdo = CDO()

# Get structured file information
info = cdo.sinfo("data.nc")  # Returns SinfoResult dataclass
print(info.var_names)        # ['tas', 'pr', 'psl']
print(info.nvar)             # 3
print(info.time_range)       # ('2020-01-01', '2022-12-31')
print(info.file_format)      # 'NetCDF'

# Grid information
grid = cdo.griddes("data.nc")  # Returns GriddesResult
print(grid.grids[0].gridtype)  # 'lonlat'
print(grid.grids[0].xsize)     # 360
print(grid.grids[0].ysize)     # 180

# Variable list
vlist = cdo.vlist("data.nc")  # Returns VlistResult
for var in vlist.variables:
    print(f"{var.name}: {var.longname} [{var.units}]")

# Parameter table
partab = cdo.partab("data.nc")  # Returns PartabResult
for param in partab.parameters:
    print(f"{param.code}: {param.name}")
```

#### File Operations

```python
from python_cdo_wrapper import CDO

cdo = CDO()

# Merge multiple files (variables)
merged = cdo.merge("tas.nc", "pr.nc", "psl.nc", output="combined.nc")

# Merge time series
full_series = cdo.mergetime(
    "data_2020.nc", "data_2021.nc", "data_2022.nc",
    output="data_2020-2022.nc"
)

# Concatenate files
combined = cdo.cat("file1.nc", "file2.nc", "file3.nc")

# Split operations
cdo.split_year("long_timeseries.nc", prefix="yearly_")
# Creates: yearly_2020.nc, yearly_2021.nc, ...

cdo.split_name("multi_var.nc", prefix="var_")
# Creates: var_tas.nc, var_pr.nc, ...

# Format conversion with query
ds = (
    cdo.query("data.nc")
    .select_var("tas")
    .year_mean()
    .output_format("nc4")  # NetCDF4 output
    .compute("output.nc")
)
```

### v0.2.x API - Legacy (Still Supported!)

#### Getting File Information

```python
from python_cdo_wrapper import cdo

# File structure info
info = cdo("sinfo data.nc")
print(info)

# Grid description
grid = cdo("griddes data.nc")
print(grid)

# Structured output (v0.2.x feature)
grid_dict = cdo("griddes data.nc", return_dict=True)
print(grid_dict["gridtype"])  # 'lonlat'
```

#### Data Processing

```python
from python_cdo_wrapper import cdo

# Calculate yearly mean
ds, log = cdo("yearmean input.nc")

# Chain operators
ds, log = cdo("-yearmean -selname,temp -sellonlatbox,-10,30,35,70 input.nc")

# Save to file
ds, log = cdo("yearmean input.nc", output_file="output.nc")
```

#### Error Handling

```python
from python_cdo_wrapper import cdo, CDOError

try:
    ds, log = cdo("invalid_command data.nc")
except CDOError as e:
    print(f"CDO failed: {e.stderr}")
except FileNotFoundError as e:
    print(f"File or CDO not found: {e}")
```

## Implemented Operators (v1.0.0)

All operators are implemented as **query methods first**, with optional convenience methods on the `CDO` class.

### Selection Operators

| Query Method | CDO Operator | Description |
|--------------|--------------|-------------|
| `.select_var(*names)` | `-selname` | Select variables by name |
| `.select_code(*codes)` | `-selcode` | Select variables by code |
| `.select_level(*levels)` | `-sellevel` | Select vertical levels |
| `.select_level_idx(*indices)` | `-sellevidx` | Select levels by index |
| `.select_level_type(ltype)` | `-selltype` | Select level type |
| `.select_year(*years)` | `-selyear` | Select years |
| `.select_month(*months)` | `-selmon` | Select months |
| `.select_day(*days)` | `-selday` | Select days |
| `.select_hour(*hours)` | `-selhour` | Select hours |
| `.select_season(*seasons)` | `-selseason` | Select seasons (DJF, MAM, JJA, SON) |
| `.select_date(start, end)` | `-seldate` | Select date range |
| `.select_time(*times)` | `-seltime` | Select specific times |
| `.select_timestep(*steps)` | `-seltimestep` | Select timesteps by index |
| `.select_region(lon1, lon2, lat1, lat2)` | `-sellonlatbox` | Select lon/lat box |
| `.select_index_box(x1, x2, y1, y2)` | `-selindexbox` | Select index box |
| `.select_mask(mask_file)` | `-ifthen` | Apply mask file |
| `.mask_by_shapefile(shp, lat, lon)` | `-ifthen` | Mask by shapefile polygon (requires `[shapefiles]` extra) |
| `.select_grid(grid_num)` | `-selgrid` | Select grid number |
| `.select_zaxis(zaxis_num)` | `-selzaxis` | Select z-axis number |

### Statistical Operators

| Query Method | CDO Operator | Description |
|--------------|--------------|-------------|
| **Time Statistics** | | |
| `.time_mean()` | `-timmean` | Time mean |
| `.time_sum()` | `-timsum` | Time sum |
| `.time_min()` | `-timmin` | Time minimum |
| `.time_max()` | `-timmax` | Time maximum |
| `.time_std()` | `-timstd` | Time std deviation |
| `.time_var()` | `-timvar` | Time variance |
| **Year/Month/Day Statistics** | | |
| `.year_mean()` | `-yearmean` | Yearly mean |
| `.year_sum()` | `-yearsum` | Yearly sum |
| `.year_min()` | `-yearmin` | Yearly minimum |
| `.year_max()` | `-yearmax` | Yearly maximum |
| `.year_std()` | `-yearstd` | Yearly std deviation |
| `.month_mean()` | `-monmean` | Monthly mean |
| `.month_sum()` | `-monsum` | Monthly sum |
| `.month_min()` | `-monmin` | Monthly minimum |
| `.month_max()` | `-monmax` | Monthly maximum |
| `.day_mean()` | `-daymean` | Daily mean |
| `.hour_mean()` | `-hourmean` | Hourly mean |
| `.season_mean()` | `-seasmean` | Seasonal mean |
| **Field Statistics** | | |
| `.field_mean()` | `-fldmean` | Field (spatial) mean |
| `.field_sum()` | `-fldsum` | Field sum |
| `.field_min()` | `-fldmin` | Field minimum |
| `.field_max()` | `-fldmax` | Field maximum |
| `.field_std()` | `-fldstd` | Field std deviation |
| `.field_percentile(p)` | `-fldpctl,p` | Field percentile |
| `.zonal_mean()` | `-zonmean` | Zonal mean |
| `.meridional_mean()` | `-mermean` | Meridional mean |
| **Vertical Statistics** | | |
| `.vert_mean()` | `-vertmean` | Vertical mean |
| `.vert_sum()` | `-vertsum` | Vertical sum |
| `.vert_min()` | `-vertmin` | Vertical minimum |
| `.vert_max()` | `-vertmax` | Vertical maximum |
| `.vert_int()` | `-vertint` | Vertical integration |
| **Running Statistics** | | |
| `.running_mean(n)` | `-runmean,n` | Running mean over n timesteps |
| `.running_sum(n)` | `-runsum,n` | Running sum over n timesteps |

### Arithmetic Operators

| Query Method | CDO Operator | Description |
|--------------|--------------|-------------|
| **Binary Operations (with F())** | | |
| `.sub(F(file))` | `-sub` | Subtract another file |
| `.add(F(file))` | `-add` | Add another file |
| `.mul(F(file))` | `-mul` | Multiply by another file |
| `.div(F(file))` | `-div` | Divide by another file |
| `.min(F(file))` | `-min` | Element-wise minimum |
| `.max(F(file))` | `-max` | Element-wise maximum |
| **Constant Arithmetic** | | |
| `.add_constant(c)` | `-addc,c` | Add constant |
| `.sub_constant(c)` | `-subc,c` | Subtract constant |
| `.mul_constant(c)` | `-mulc,c` | Multiply by constant |
| `.div_constant(c)` | `-divc,c` | Divide by constant |
| **Math Functions** | | |
| `.abs()` | `-abs` | Absolute value |
| `.sqrt()` | `-sqrt` | Square root |
| `.sqr()` | `-sqr` | Square |
| `.exp()` | `-exp` | Exponential |
| `.ln()` | `-ln` | Natural logarithm |
| `.log10()` | `-log10` | Base-10 logarithm |
| `.sin()`, `.cos()`, `.tan()` | `-sin`, `-cos`, `-tan` | Trigonometric |

### Interpolation Operators

| Query Method | CDO Operator | Description |
|--------------|--------------|-------------|
| `.remap_bil(grid)` | `-remapbil,grid` | Bilinear interpolation |
| `.remap_bic(grid)` | `-remapbic,grid` | Bicubic interpolation |
| `.remap_nn(grid)` | `-remapnn,grid` | Nearest neighbor |
| `.remap_dis(grid)` | `-remapdis,grid` | Distance-weighted average |
| `.remap_con(grid)` | `-remapcon,grid` | First-order conservative |
| `.remap_con2(grid)` | `-remapcon2,grid` | Second-order conservative |
| `.remap_laf(grid)` | `-remaplaf,grid` | Largest area fraction |
| `.interp_level(*levels)` | `-intlevel` | Interpolate to pressure levels |
| `.ml_to_pl(*levels)` | `-ml2pl` | Model levels to pressure levels |

### Modification Operators

| Query Method | CDO Operator | Description |
|--------------|--------------|-------------|
| `.set_name(name)` | `-setname,name` | Set variable name |
| `.set_code(code)` | `-setcode,code` | Set variable code |
| `.set_unit(unit)` | `-setunit,unit` | Set units |
| `.set_level(*levels)` | `-setlevel` | Set level values |
| `.set_missval(val)` | `-setmissval,val` | Set missing value |
| `.set_range_to_miss(min, max)` | `-setrtomiss` | Set range to missing |
| `.miss_to_const(val)` | `-setmisstoc,val` | Set missing to constant |
| `.set_grid(grid)` | `-setgrid,grid` | Set grid |
| `.set_grid_type(gtype)` | `-setgridtype` | Set grid type |
| `.invert_lat()` | `-invertlat` | Invert latitudes |

### Advanced Query Methods (Django-Inspired)

| Method | Description |
|--------|-------------|
| `.first()` | Get first timestep only |
| `.last()` | Get last timestep only |
| `.count()` | Get number of timesteps (returns int) |
| `.exists()` | Check if query returns data (returns bool) |
| `.values(*vars)` | Alias for `.select_var()` |
| `.get_command()` | Get CDO command string |
| `.explain()` | Get human-readable pipeline description |
| `.clone()` | Create a copy for branching |

### Info Operators (CDO Class Methods)

| CDO Method | CDO Operator | Return Type |
|------------|--------------|-------------|
| `cdo.sinfo(file)` | `sinfo` | `SinfoResult` |
| `cdo.info(file)` | `info` | `InfoResult` |
| `cdo.griddes(file)` | `griddes` | `GriddesResult` |
| `cdo.zaxisdes(file)` | `zaxisdes` | `ZaxisdesResult` |
| `cdo.vlist(file)` | `vlist` | `VlistResult` |
| `cdo.partab(file)` | `partab` | `PartabResult` |

### File Operations (CDO Class Methods)

| CDO Method | CDO Operator | Description |
|------------|--------------|-------------|
| `cdo.merge(*files)` | `-merge` | Merge files (variables) |
| `cdo.mergetime(*files)` | `-mergetime` | Merge time series |
| `cdo.cat(*files)` | `-cat` | Concatenate files |
| `cdo.copy(input, output)` | `-copy` | Copy file |
| `cdo.split_year(file, prefix)` | `-splityear` | Split by year |
| `cdo.split_mon(file, prefix)` | `-splitmon` | Split by month |
| `cdo.split_day(file, prefix)` | `-splitday` | Split by day |
| `cdo.split_hour(file, prefix)` | `-splithour` | Split by hour |
| `cdo.split_name(file, prefix)` | `-splitname` | Split by variable |
| `cdo.split_level(file, prefix)` | `-splitlevel` | Split by level |

## API Reference

### v1.0.0 API

#### CDO Class

**Factory and Façade for CDO operations**

```python
from python_cdo_wrapper import CDO

cdo = CDO(cdo_path="cdo", temp_dir=None)
```

**Parameters:**
- `cdo_path` (str): Path to CDO executable (default: "cdo")
- `temp_dir` (str | Path | None): Directory for temporary files (default: system temp)

**Query Factory:**
- `cdo.query(input_file)` → `CDOQuery`: Create lazy query builder

**Info Methods:**
- `cdo.sinfo(file)` → `SinfoResult`: Get structured file info
- `cdo.griddes(file)` → `GriddesResult`: Get grid description
- `cdo.vlist(file)` → `VlistResult`: Get variable list
- `cdo.partab(file)` → `PartabResult`: Get parameter table

**File Operations:**
- `cdo.merge(*files, output=None)` → `xr.Dataset`: Merge files
- `cdo.mergetime(*files, output=None)` → `xr.Dataset`: Merge time series
- `cdo.cat(*files, output=None)` → `xr.Dataset`: Concatenate files
- `cdo.split_year(file, prefix)`: Split by year
- `cdo.split_name(file, prefix)`: Split by variable

**Legacy Compatibility:**
- `cdo.run(cmd, output=None, return_xr=True)` → `tuple[xr.Dataset | None, str]`: Execute string command

#### CDOQuery Class

**Django ORM-style lazy query builder**

```python
query = cdo.query("data.nc")
```

**Selection Methods:**
- `.select_var(*names)` → `CDOQuery`: Select variables
- `.select_level(*levels)` → `CDOQuery`: Select vertical levels
- `.select_year(*years)` → `CDOQuery`: Select years
- `.select_month(*months)` → `CDOQuery`: Select months
- `.select_region(lon1, lon2, lat1, lat2)` → `CDOQuery`: Select spatial region
- See [Implemented Operators](#implemented-operators-v100) for full list

**Statistical Methods:**
- `.year_mean()` → `CDOQuery`: Yearly mean
- `.month_mean()` → `CDOQuery`: Monthly mean
- `.time_mean()` → `CDOQuery`: Time mean
- `.field_mean()` → `CDOQuery`: Spatial mean
- See [Implemented Operators](#implemented-operators-v100) for full list

**Arithmetic Methods:**
- `.sub(F(file))` → `BinaryOpQuery`: Subtract file
- `.add(F(file))` → `BinaryOpQuery`: Add file
- `.add_constant(c)` → `CDOQuery`: Add constant
- `.sub_constant(c)` → `CDOQuery`: Subtract constant
- See [Implemented Operators](#implemented-operators-v100) for full list

**Interpolation Methods:**
- `.remap_bil(grid)` → `CDOQuery`: Bilinear interpolation
- `.remap_con(grid)` → `CDOQuery`: Conservative remapping
- See [Implemented Operators](#implemented-operators-v100) for full list

**Terminal Methods:**
- `.compute(output=None)` → `xr.Dataset`: Execute query and return dataset
- `.to_file(output)` → `Path`: Execute and save to file
- `.get_command()` → `str`: Get CDO command string (no execution)
- `.explain()` → `str`: Get human-readable description
- `.clone()` → `CDOQuery`: Create copy for branching

**Advanced Query Methods:**
- `.first()` → `xr.Dataset`: Get first timestep
- `.last()` → `xr.Dataset`: Get last timestep
- `.count()` → `int`: Get number of timesteps
- `.exists()` → `bool`: Check if data exists

#### F() Function

**Create unbound query for binary operations (Django F-expression pattern)**

```python
from python_cdo_wrapper import F

# Use F() to reference files in binary operations
anomaly = cdo.query("data.nc").sub(F("climatology.nc")).compute()
```

**Parameters:**
- `input_file` (str | Path): File to reference in binary operation

**Returns:**
- `CDOQuery`: Unbound query that can be used with `.sub()`, `.add()`, etc.

#### BinaryOpQuery Class

**Query subclass for binary operations** (automatically created by `.sub(F(...))`, etc.)

Supports nested operations using CDO bracket notation (requires CDO >= 1.9.8):
```python
# Both sides processed before subtraction
result = (
    cdo.query("a.nc").year_mean()
    .sub(F("b.nc").time_mean())
    .compute()
)
# Generates: cdo -sub [ -yearmean a.nc ] [ -timmean b.nc ]
```

#### Result Types

**Structured dataclasses for info commands:**

- `SinfoResult`: File info with var_names, nvar, time_range, etc.
- `GriddesResult`: Grid information
- `VlistResult`: Variable list
- `PartabResult`: Parameter table
- `InfoResult`: Detailed file info
- `ZaxisdesResult`: Vertical axis info

All result types provide structured access to CDO output with proper types and helper methods.

#### Exceptions

```python
from python_cdo_wrapper import (
    CDOError,              # Base exception
    CDOExecutionError,     # Command execution failed
    CDOValidationError,    # Invalid parameters
    CDOFileNotFoundError,  # File not found
    CDOParseError,         # Output parsing failed
)
```

**CDOExecutionError attributes:**
- `.command`: The CDO command that failed
- `.returncode`: Exit code
- `.stdout`: Standard output
- `.stderr`: Standard error

**CDOValidationError attributes:**
- `.parameter`: Parameter name
- `.value`: Invalid value
- `.expected`: Expected type/format

### v0.2.x API (Legacy)

#### cdo() function

Execute a CDO command and return results as Python objects.

```python
from python_cdo_wrapper import cdo

result = cdo(cmd, output_file=None, return_xr=True, return_dict=False, debug=False, check_files=True)
```

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

## Requirements

### CDO Version

- **Minimum**: CDO >= 1.9.8
- **Recommended**: CDO >= 2.0.0

All features are compatible with CDO >= 1.9.8. Binary operations use standard operator chaining syntax supported by all modern CDO versions.

### Python Version

- **Minimum**: Python 3.9
- **Tested**: Python 3.9, 3.10, 3.11, 3.12

## Configuration

### Environment Variables

The wrapper uses the system CDO installation. You can configure CDO behavior with standard environment variables:

```bash
# Set CDO temp directory
export CDO_TMPDIR=/path/to/tmp

# Set number of OpenMP threads
export OMP_NUM_THREADS=4
```

### Custom CDO Path

```python
from python_cdo_wrapper import CDO

# Use specific CDO installation
cdo = CDO(cdo_path="/usr/local/bin/cdo")

# Use custom temp directory
cdo = CDO(temp_dir="/path/to/temp")
```

## Key Features Explained

### Why Django ORM-Style?

The v1.0.0 query API is inspired by Django's QuerySet pattern because climate data processing naturally fits this paradigm:

| Benefit | Climate Science Use Case |
|---------|--------------------------|
| **Lazy Evaluation** | Build complex pipelines, inspect commands, optimize before execution |
| **Readable Chaining** | `select_var("tas").year_mean().field_mean()` reads like natural language |
| **Composability** | Create base queries, branch for different analyses (annual, seasonal, regional) |
| **Type Safety** | IDE autocomplete prevents typos, discovers available operators |
| **Reusability** | Query templates for standard analysis workflows |

### F() Function (Anomaly Calculations)

Climate science frequently requires calculating anomalies: deviations from climatology. The `F()` function makes this trivial:

```python
# Traditional approach (multiple steps)
# 1. Create climatology file separately
# 2. Calculate anomaly with CDO -sub
# 3. Manage intermediate files

# v1.0.0 approach (ONE LINE!)
anomaly = cdo.query("monthly_data.nc").sub(F("climatology.nc")).compute()
# Generates: cdo -sub monthly_data.nc climatology.nc

# With preprocessing - operators chain to respective files!
processed_anomaly = (
    cdo.query("data.nc")
    .select_var("tas")
    .year_mean()
    .sub(F("climatology.nc").time_mean())
    .compute()
)
# Generates: cdo -sub -yearmean -selname,tas data.nc -timmean climatology.nc
```

The `F()` function references another file in the operation, enabling:
- **Anomaly calculations**: `data.sub(F("climatology"))`
- **Bias corrections**: `model.sub(F("observations"))`
- **Standardization**: `data.sub(F("mean")).div(F("std"))`
- **Difference fields**: `level1000.sub(F("level500"))`

**Technical Note**: Binary operations use CDO's operator chaining syntax. Operators are applied directly to their respective input files from left to right, without bracket notation. This allows all operations to execute in a single CDO command.

### Query Introspection

Before executing expensive operations on large files, inspect what will happen:

```python
query = (
    cdo.query("era5_global.nc")
    .select_var("tas")
    .select_region(-10, 40, 35, 70)
    .year_mean()
)

# See exact CDO command
print(query.get_command())
# "cdo -yearmean -sellonlatbox,-10,40,35,70 -selname,tas era5_global.nc"

# Human-readable description
print(query.explain())

# Execute when ready
ds = query.compute()
```

### Query Branching

Create base queries and branch for different analyses without duplicating code:

```python
# Base query: European temperature 2020-2022
base = (
    cdo.query("era5.nc")
    .select_var("tas")
    .select_region(-10, 40, 35, 70)
    .select_year(2020, 2021, 2022)
)

# Branch for different temporal aggregations
annual = base.clone().year_mean().compute()
seasonal = base.clone().season_mean().compute()
monthly = base.clone().month_mean().compute()

# Branch for different spatial aggregations
field_mean = base.clone().field_mean().compute()
zonal_mean = base.clone().zonal_mean().compute()
```

## Comparison with Other Libraries

| Feature | python-cdo-wrapper v1.0 | python-cdo | cdo-bindings |
|---------|-------------------------|------------|--------------|
| **Query Chaining** | ✅ Django ORM-style | ❌ | ❌ |
| **Lazy Evaluation** | ✅ Build before execute | ❌ Immediate | ❌ Immediate |
| **F() for Anomalies** | ✅ One-liner | ❌ Manual | ❌ Manual |
| **Query Introspection** | ✅ `.get_command()`, `.explain()` | ❌ | ❌ |
| **Type Safety** | ✅ Full type hints | ❌ | ❌ |
| **Structured Results** | ✅ Dataclasses | ❌ Strings | ❌ Strings |
| **xarray Integration** | ✅ Native | ⚠️ Manual | ⚠️ Manual |
| **Temp File Cleanup** | ✅ Automatic | ⚠️ Manual | ⚠️ Manual |
| **Legacy API Support** | ✅ v0.2.x still works | N/A | N/A |
| **Dependencies** | Minimal | Heavy | Heavy |

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

## Real-World Climate Science Examples

### Example 1: Multi-Model Ensemble Analysis

```python
from python_cdo_wrapper import CDO

cdo = CDO()

# Process multiple models consistently
models = ["model_a.nc", "model_b.nc", "model_c.nc"]

# Create reusable processing pipeline
def process_model(filename):
    return (
        cdo.query(filename)
        .select_var("tas")
        .select_region(-180, 180, -60, 60)  # Exclude poles
        .year_mean()
        .field_mean()
        .compute()
    )

ensemble = [process_model(m) for m in models]
```

### Example 2: Seasonal Climatology and Anomalies

```python
from python_cdo_wrapper import CDO, F

cdo = CDO()

# Step 1: Create seasonal climatology
climatology = (
    cdo.query("historical_1981-2010.nc")
    .select_var("tas")
    .season_mean()
    .time_mean()  # Average over all years
    .to_file("seasonal_clim.nc")
)

# Step 2: Calculate seasonal anomalies (ONE LINE!)
anomalies = (
    cdo.query("current_data.nc")
    .select_var("tas")
    .season_mean()
    .sub(F("seasonal_clim.nc"))
    .compute("seasonal_anomalies.nc")
)
```

### Example 3: Vertical Cross-Section

```python
from python_cdo_wrapper import CDO

cdo = CDO()

# Extract zonal mean temperature profile
zonal_profile = (
    cdo.query("3d_temperature.nc")
    .select_var("ta")
    .select_region(-180, 180, 30, 60)  # Northern mid-latitudes
    .zonal_mean()
    .time_mean()
    .compute()
)
```

### Example 4: Regional Climate Index

```python
from python_cdo_wrapper import CDO

cdo = CDO()

# Define region and compute standardized index
base_query = (
    cdo.query("temperature.nc")
    .select_var("tas")
    .select_region(-10, 30, 35, 70)  # Mediterranean
    .field_mean()
)

# Get climatology
clim_mean = base_query.clone().time_mean().compute()
clim_std = base_query.clone().time_std().compute()

# Calculate standardized index
from python_cdo_wrapper import F
index = (
    base_query
    .sub(F(clim_mean))
    .div(F(clim_std))
    .compute("mediterranean_index.nc")
)
```

### Example 5: Model-Observation Comparison

```python
from python_cdo_wrapper import CDO, F

cdo = CDO()

# Regrid model to observation grid and calculate bias
bias = (
    cdo.query("model_output.nc")
    .select_var("tas")
    .remap_bil("observations.nc")  # Match obs grid
    .year_mean()
    .sub(
        F("observations.nc").select_var("tas").year_mean()
    )
    .compute("model_bias.nc")
)

# Root mean square error field
rmse = (
    cdo.query("model_output.nc")
    .select_var("tas")
    .remap_bil("observations.nc")
    .sub(F("observations.nc").select_var("tas"))
    .sqr()
    .time_mean()
    .sqrt()
    .compute("rmse.nc")
)
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Priorities for v1.0.0+

We welcome contributions in these areas:

- Additional CDO operators as query methods
- Enhanced parser support for more info commands
- Query optimization and performance improvements
- Documentation and examples
- Integration tests with real climate datasets

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

## Migration from v0.x

The v1.0.0 release introduces a **major architectural change** while maintaining full backward compatibility. See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for detailed upgrade instructions.

**Quick Summary:**

```python
# v0.x - String-based API (STILL WORKS!)
from python_cdo_wrapper import cdo
ds, log = cdo("yearmean -selname,tas data.nc")

# v1.0 - Django ORM-style API (RECOMMENDED)
from python_cdo_wrapper import CDO
cdo = CDO()
ds = cdo.query("data.nc").select_var("tas").year_mean().compute()

# v1.0 - Anomaly calculation made easy
from python_cdo_wrapper import F
anomaly = cdo.query("data.nc").sub(F("climatology.nc")).compute()
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

### v1.0.0 Highlights (December 2025)

- **Django ORM-style Query API**: Lazy, chainable query builder as primary interface
- **F() Function**: One-liner anomaly calculations with binary operations
- **Query Introspection**: `.get_command()`, `.explain()`, `.clone()`
- **Structured Result Types**: All info commands return typed dataclasses
- **Complete Operator Coverage**: Selection, statistics, arithmetic, interpolation, modification
- **Advanced Query Methods**: `.first()`, `.last()`, `.count()`, `.exists()`
- **Query Templates**: Reusable pipeline patterns
- **Full Type Safety**: Complete type hints with IDE autocompletion
- **Backward Compatibility**: v0.2.x string-based API still fully supported

---

Made with ❤️ for the climate science community
