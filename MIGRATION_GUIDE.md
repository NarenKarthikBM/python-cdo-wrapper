# Migration Guide: v0.x to v1.0.0

This guide will help you migrate from python-cdo-wrapper v0.x to v1.0.0, which introduces a major architectural change with the Django ORM-style query API.

## Table of Contents

- [Overview](#overview)
- [Good News: Full Backward Compatibility](#good-news-full-backward-compatibility)
- [Why Migrate?](#why-migrate)
- [Quick Migration Summary](#quick-migration-summary)
- [Step-by-Step Migration](#step-by-step-migration)
  - [1. Import Changes](#1-import-changes)
  - [2. Basic Operations](#2-basic-operations)
  - [3. Chained Operations](#3-chained-operations)
  - [4. Info Commands](#4-info-commands)
  - [5. File Operations](#5-file-operations)
  - [6. Binary Operations (NEW!)](#6-binary-operations-new)
- [New v1.0.0 Features](#new-v100-features)
- [Breaking Changes](#breaking-changes)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

---

## Overview

**v1.0.0** introduces a complete architectural overhaul inspired by Django's ORM QuerySet pattern:

| v0.x | v1.0.0 |
|------|--------|
| String-based commands | Django ORM-style query chaining |
| Immediate execution | Lazy evaluation |
| Text output parsing | Structured dataclass results |
| Manual anomaly calculations | One-liner with `F()` function |

**Key Point**: v0.x string-based API still works! You can migrate incrementally.

---

## Good News: Full Backward Compatibility

**Your existing v0.x code will continue to work without any changes!**

```python
# v0.x code still works in v1.0.0
from python_cdo_wrapper import cdo

ds, log = cdo("yearmean input.nc")
info = cdo("sinfo input.nc")
```

You can migrate to the new API at your own pace, file by file, or even mix both styles in the same project.

---

## Why Migrate?

Benefits of migrating to the v1.0.0 API:

### 1. **Lazy Evaluation**
```python
# v1.0.0: Build first, execute later
query = cdo.query("data.nc").select_var("tas").year_mean()
print(query.get_command())  # Inspect before running
ds = query.compute()  # Execute when ready
```

### 2. **Readable Chaining**
```python
# v0.x: Hard to read string
ds, log = cdo("-fldmean -yearmean -selyear,2020,2021,2022 -selname,tas data.nc")

# v1.0.0: Self-documenting
ds = (
    cdo.query("data.nc")
    .select_var("tas")
    .select_year(2020, 2021, 2022)
    .year_mean()
    .field_mean()
    .compute()
)
```

### 3. **One-Liner Anomaly Calculations**
```python
# v0.x: Multiple steps
# 1. Create climatology file
# 2. Calculate difference
# 3. Manage intermediate files

# v1.0.0: One line!
anomaly = cdo.query("data.nc").sub(F("climatology.nc")).compute()
```

### 4. **Type Safety & IDE Autocompletion**
```python
# v1.0.0: Full IDE support
ds = cdo.query("data.nc").select_var(  # IDE suggests all methods
```

### 5. **Query Reusability**
```python
# v1.0.0: Create base query, branch for different analyses
base = cdo.query("data.nc").select_var("tas")
annual = base.clone().year_mean().compute()
monthly = base.clone().month_mean().compute()
```

### 6. **Structured Results**
```python
# v0.x: Parse strings manually
info = cdo("sinfo data.nc")
# Parse text output...

# v1.0.0: Typed dataclasses
info = cdo.sinfo("data.nc")  # Returns SinfoResult
print(info.var_names)  # ['tas', 'pr']
print(info.nvar)       # 2
```

---

## Quick Migration Summary

| Operation | v0.x | v1.0.0 |
|-----------|------|--------|
| **Import** | `from python_cdo_wrapper import cdo` | `from python_cdo_wrapper import CDO` |
| **Initialize** | N/A (function) | `cdo = CDO()` |
| **Simple operation** | `ds, log = cdo("yearmean data.nc")` | `ds = cdo.query("data.nc").year_mean().compute()` |
| **Chained operations** | `ds, log = cdo("-yearmean -selname,tas data.nc")` | `ds = cdo.query("data.nc").select_var("tas").year_mean().compute()` |
| **Info command** | `info = cdo("sinfo data.nc")` | `info = cdo.sinfo("data.nc")  # Returns dataclass` |
| **Structured output** | `dict = cdo("sinfo data.nc", return_dict=True)` | `info = cdo.sinfo("data.nc")  # Native dataclass` |
| **File operations** | N/A | `cdo.merge("f1.nc", "f2.nc")` |
| **Anomaly calc** | Multi-step with temp files | `query.sub(F("climatology.nc"))` |

---

## Step-by-Step Migration

### 1. Import Changes

#### v0.x
```python
from python_cdo_wrapper import cdo
```

#### v1.0.0
```python
from python_cdo_wrapper import CDO

cdo = CDO()
```

**Optional**: Import `F` for binary operations
```python
from python_cdo_wrapper import CDO, F

cdo = CDO()
```

---

### 2. Basic Operations

#### Simple Statistical Operation

**v0.x**:
```python
from python_cdo_wrapper import cdo

ds, log = cdo("yearmean input.nc")
```

**v1.0.0 (Option A - Query API)**:
```python
from python_cdo_wrapper import CDO

cdo = CDO()
ds = cdo.query("input.nc").year_mean().compute()
```

**v1.0.0 (Option B - Convenience method)**:
```python
from python_cdo_wrapper import CDO

cdo = CDO()
ds = cdo.yearmean("input.nc")
```

---

#### Selection Operation

**v0.x**:
```python
ds, log = cdo("-selname,tas,pr input.nc")
```

**v1.0.0**:
```python
ds = cdo.query("input.nc").select_var("tas", "pr").compute()
```

---

#### Saving to File

**v0.x**:
```python
ds, log = cdo("yearmean input.nc", output_file="output.nc")
```

**v1.0.0 (Option A)**:
```python
ds = cdo.query("input.nc").year_mean().compute(output="output.nc")
```

**v1.0.0 (Option B)**:
```python
cdo.query("input.nc").year_mean().to_file("output.nc")
```

---

### 3. Chained Operations

#### Multiple Operators

**v0.x**:
```python
ds, log = cdo("-yearmean -selname,tas -sellevel,500 input.nc")
```

**v1.0.0**:
```python
ds = (
    cdo.query("input.nc")
    .select_var("tas")
    .select_level(500)
    .year_mean()
    .compute()
)
```

---

#### Regional Selection with Statistics

**v0.x**:
```python
ds, log = cdo("-fldmean -yearmean -sellonlatbox,-10,30,35,70 -selname,tas input.nc")
```

**v1.0.0**:
```python
ds = (
    cdo.query("input.nc")
    .select_var("tas")
    .select_region(lon1=-10, lon2=30, lat1=35, lat2=70)
    .year_mean()
    .field_mean()
    .compute()
)
```

**Benefits**:
- Named parameters (no need to remember order!)
- Self-documenting code
- Type checking

---

### 4. Info Commands

#### File Information

**v0.x**:
```python
# Text output
info = cdo("sinfo data.nc")
print(info)  # Parse text manually

# Or structured dict
info_dict = cdo("sinfo data.nc", return_dict=True)
print(info_dict["variables"])
```

**v1.0.0**:
```python
# Structured dataclass (native)
info = cdo.sinfo("data.nc")  # Returns SinfoResult

# Type-safe access
print(info.var_names)    # ['tas', 'pr', 'psl']
print(info.nvar)         # 3
print(info.time_range)   # ('2020-01-01', '2022-12-31')
print(info.file_format)  # 'NetCDF'

# Access variables
for var in info.variables:
    print(f"{var.name}: {var.longname} [{var.units}]")
```

---

#### Grid Information

**v0.x**:
```python
grid = cdo("griddes data.nc")
# Parse text output

# Or
grid_dict = cdo("griddes data.nc", return_dict=True)
print(grid_dict["gridtype"])
```

**v1.0.0**:
```python
grid = cdo.griddes("data.nc")  # Returns GriddesResult

print(grid.grids[0].gridtype)  # 'lonlat'
print(grid.grids[0].xsize)     # 360
print(grid.grids[0].ysize)     # 180
print(grid.grids[0].xinc)      # 1.0
```

---

#### Variable List

**v0.x**:
```python
vlist = cdo("vlist data.nc")
# Parse text output
```

**v1.0.0**:
```python
vlist = cdo.vlist("data.nc")  # Returns VlistResult

for var in vlist.variables:
    print(f"{var.name}: {var.longname}")
    print(f"  Units: {var.units}")
    print(f"  Code: {var.code}")
```

---

### 5. File Operations

#### Merging Files

**v0.x**:
```python
# Merge variables
ds, log = cdo("merge tas.nc pr.nc psl.nc")

# Merge time series
ds, log = cdo("mergetime data_2020.nc data_2021.nc data_2022.nc")
```

**v1.0.0**:
```python
# Merge variables
merged = cdo.merge("tas.nc", "pr.nc", "psl.nc")

# Merge time series
timeseries = cdo.mergetime("data_2020.nc", "data_2021.nc", "data_2022.nc")

# Save to file
cdo.mergetime("data_2020.nc", "data_2021.nc", output="combined.nc")
```

---

#### Splitting Files

**v0.x**:
```python
# Not directly supported, use command string
_, log = cdo("splityear input.nc output_", return_xr=False)
```

**v1.0.0**:
```python
# Native method
cdo.splityear("input.nc", prefix="yearly_")
# Creates: yearly_2020.nc, yearly_2021.nc, ...

cdo.splitname("multi_var.nc", prefix="var_")
# Creates: var_tas.nc, var_pr.nc, ...
```

---

### 6. Binary Operations (NEW!)

This is one of the most powerful new features in v1.0.0!

#### Simple Anomaly Calculation

**v0.x** (multi-step):
```python
# Step 1: Create climatology (separate script/cell)
clim, _ = cdo("timmean historical_data.nc", output_file="climatology.nc")

# Step 2: Calculate anomaly
anomaly, _ = cdo("sub current_data.nc climatology.nc", output_file="anomaly.nc")
```

**v1.0.0** (one line!):
```python
from python_cdo_wrapper import F

# One-liner!
anomaly = cdo.query("current_data.nc").sub(F("climatology.nc")).compute()

# Or save to file
cdo.query("current_data.nc").sub(F("climatology.nc")).to_file("anomaly.nc")
```

---

#### Standardized Anomaly

**v0.x** (multi-step):
```python
# Step 1: Calculate mean
mean, _ = cdo("timmean data.nc", output_file="mean.nc")

# Step 2: Calculate std
std, _ = cdo("timstd data.nc", output_file="std.nc")

# Step 3: Calculate (data - mean)
diff, _ = cdo("sub data.nc mean.nc", output_file="diff.nc")

# Step 4: Divide by std
std_anomaly, _ = cdo("div diff.nc std.nc", output_file="std_anomaly.nc")

# Clean up intermediate files...
```

**v1.0.0** (one pipeline!):
```python
std_anomaly = (
    cdo.query("data.nc")
    .sub(F("mean.nc"))
    .div(F("std.nc"))
    .compute()
)
```

---

#### Model Bias Calculation

**v0.x** (complex multi-step):
```python
# Process model
model_mean, _ = cdo("-fldmean -yearmean -selname,tas model.nc",
                    output_file="model_mean.nc")

# Process observations
obs_mean, _ = cdo("-fldmean -yearmean -selname,tas observations.nc",
                  output_file="obs_mean.nc")

# Calculate bias
bias, _ = cdo("sub model_mean.nc obs_mean.nc", output_file="bias.nc")
```

**v1.0.0** (single readable pipeline!):
```python
bias = (
    cdo.query("model.nc")
    .select_var("tas")
    .year_mean()
    .field_mean()
    .sub(
        F("observations.nc")
        .select_var("tas")
        .year_mean()
        .field_mean()
    )
    .compute()
)
```

---

#### Processing Both Sides Before Subtraction

**v1.0.0** (powerful nested operations):
```python
# Temperature difference between pressure levels
temp_diff = (
    cdo.query("data.nc")
    .select_var("ta")
    .select_level(1000)
    .sub(
        F("data.nc")
        .select_var("ta")
        .select_level(500)
    )
    .compute()
)

# Generates CDO command with operator chaining:
# cdo -sub -sellevel,1000 -selname,ta data.nc -sellevel,500 -selname,ta data.nc
```

**Note**: All CDO operations execute in a single command using operator chaining.

---

## New v1.0.0 Features

### Query Introspection

**Before executing expensive operations, inspect what will happen:**

```python
# Build query
query = (
    cdo.query("era5_global.nc")
    .select_var("tas")
    .select_region(-10, 40, 35, 70)
    .year_mean()
    .field_mean()
)

# Inspect command
print(query.get_command())
# Output: "cdo -fldmean -yearmean -sellonlatbox,-10,40,35,70 -selname,tas era5_global.nc"

# Human-readable explanation
print(query.explain())
# Output: Detailed description of what the query does

# Execute when ready
ds = query.compute()
```

---

### Query Branching

**Create base queries and branch for different analyses:**

```python
# Base query
base = (
    cdo.query("era5.nc")
    .select_var("tas")
    .select_region(-10, 40, 35, 70)
    .select_year(2020, 2021, 2022)
)

# Branch for different temporal aggregations
annual_mean = base.clone().year_mean().compute()
seasonal_mean = base.clone().season_mean().compute()
monthly_mean = base.clone().month_mean().compute()

# Branch for different spatial aggregations
field_mean = base.clone().field_mean().compute()
zonal_mean = base.clone().zonal_mean().compute()
spatial_std = base.clone().field_std().compute()
```

---

### Advanced Query Methods (Django-Inspired)

```python
query = cdo.query("data.nc").select_var("tas")

# Get first timestep only
first = query.first()

# Get last timestep only
last = query.last()

# Count timesteps (returns int)
n_timesteps = query.count()

# Check if data exists (returns bool)
has_data = query.exists()
```

---

### Query Templates

**Create reusable analysis patterns:**

```python
from python_cdo_wrapper import CDOQueryTemplate

# Define template
annual_global_mean = (
    CDOQueryTemplate()
    .select_var("{var}")
    .year_mean()
    .field_mean()
)

# Apply to multiple files/variables
tas_mean = annual_global_mean.bind(cdo, "era5.nc", var="tas").compute()
pr_mean = annual_global_mean.bind(cdo, "era5.nc", var="pr").compute()
```

---

### Grid Specifications

**Type-safe grid definitions:**

```python
from python_cdo_wrapper.types import GridSpec

# Use predefined grids
ds = (
    cdo.query("high_res_data.nc")
    .remap_bil(GridSpec.global_1deg())
    .compute()
)

# Or create custom grid
custom_grid = GridSpec(
    gridtype="lonlat",
    xsize=720,
    ysize=360,
    xfirst=-179.75,
    xinc=0.5,
    yfirst=-89.75,
    yinc=0.5
)

ds = cdo.query("data.nc").remap_con(custom_grid).compute()
```

---

## Breaking Changes

### None! (Backward Compatible)

The v0.x string-based API continues to work:

```python
# v0.x code still works in v1.0.0
from python_cdo_wrapper import cdo

ds, log = cdo("yearmean input.nc")
info = cdo("sinfo data.nc")
grid_dict = cdo("griddes data.nc", return_dict=True)
```

### Recommended Changes (Not Breaking)

1. **Import**: Change from `cdo` function to `CDO` class
2. **API**: Use query chaining for new code
3. **Info commands**: Use structured dataclass results instead of `return_dict=True`

---

## Common Patterns

### Pattern 1: Regional Analysis Workflow

**v0.x**:
```python
# Multiple steps, intermediate files
ds1, _ = cdo("-sellonlatbox,-10,30,35,70 input.nc", output_file="europe.nc")
ds2, _ = cdo("-selname,tas europe.nc", output_file="europe_tas.nc")
ds3, _ = cdo("-yearmean europe_tas.nc", output_file="europe_tas_annual.nc")
result, _ = cdo("-fldmean europe_tas_annual.nc")
```

**v1.0.0**:
```python
# Single readable pipeline
result = (
    cdo.query("input.nc")
    .select_var("tas")
    .select_region(-10, 30, 35, 70)
    .year_mean()
    .field_mean()
    .compute()
)
```

---

### Pattern 2: Multi-Model Ensemble

**v0.x**:
```python
models = ["model_a.nc", "model_b.nc", "model_c.nc"]
results = []

for model in models:
    ds, _ = cdo(f"-fldmean -yearmean -selname,tas {model}")
    results.append(ds)
```

**v1.0.0**:
```python
models = ["model_a.nc", "model_b.nc", "model_c.nc"]

def process_model(filename):
    return (
        cdo.query(filename)
        .select_var("tas")
        .year_mean()
        .field_mean()
        .compute()
    )

results = [process_model(m) for m in models]
```

---

### Pattern 3: Seasonal Climatology & Anomalies

**v0.x** (complex multi-step):
```python
# Create climatology
clim, _ = cdo("-seasmean historical.nc", output_file="clim.nc")
clim_mean, _ = cdo("timmean clim.nc", output_file="clim_mean.nc")

# Calculate anomalies
current_seas, _ = cdo("-seasmean current.nc", output_file="current_seas.nc")
anomaly, _ = cdo("sub current_seas.nc clim_mean.nc", output_file="anomaly.nc")
```

**v1.0.0** (clean and clear):
```python
# Create climatology
climatology = (
    cdo.query("historical.nc")
    .season_mean()
    .time_mean()
    .to_file("clim_mean.nc")
)

# Calculate anomalies (one line!)
anomaly = (
    cdo.query("current.nc")
    .season_mean()
    .sub(F("clim_mean.nc"))
    .compute("anomaly.nc")
)
```

---

### Pattern 4: Vertical Profile Analysis

**v0.x**:
```python
# Extract zonal mean
zonal, _ = cdo("-zonmean -sellonlatbox,-180,180,30,60 data.nc",
               output_file="zonal.nc")
profile, _ = cdo("-timmean zonal.nc")
```

**v1.0.0**:
```python
profile = (
    cdo.query("data.nc")
    .select_region(-180, 180, 30, 60)
    .zonal_mean()
    .time_mean()
    .compute()
)
```

---

## Troubleshooting

### Issue: "CDO not found"

**Solution**: Ensure CDO is installed and in PATH, or specify path:

```python
cdo = CDO(cdo_path="/usr/local/bin/cdo")
```

---

### Issue: Binary operations not working as expected

**Error**: Binary operations produce unexpected results

**Solution**: Ensure CDO >= 1.9.8 and review command with `.get_command()`:

```bash
# macOS
brew upgrade cdo

# Conda
conda update -c conda-forge cdo

# Check version
cdo --version
```

---

### Issue: "Query doesn't return expected result"

**Solution**: Use `.get_command()` to inspect the generated CDO command:

```python
query = cdo.query("data.nc").select_var("tas").year_mean()
print(query.get_command())
# Verify the command is correct before executing
ds = query.compute()
```

---

### Issue: "Want to keep using v0.x API"

**Solution**: No problem! v0.x API is fully supported:

```python
from python_cdo_wrapper import cdo  # Note: lowercase 'cdo'

# All v0.x code works unchanged
ds, log = cdo("yearmean input.nc")
```

---

### Issue: "How to mix v0.x and v1.0.0 APIs?"

**Solution**: Import both:

```python
from python_cdo_wrapper import cdo as cdo_legacy  # v0.x function
from python_cdo_wrapper import CDO  # v1.0.0 class

# Use v0.x for quick commands
info = cdo_legacy("sinfo data.nc")

# Use v1.0.0 for complex pipelines
cdo = CDO()
ds = cdo.query("data.nc").select_var("tas").year_mean().compute()
```

---

## Migration Checklist

### Phase 1: Setup (No Code Changes)
- [ ] Install python-cdo-wrapper v1.0.0
- [ ] Ensure CDO >= 1.9.8 (for binary operations)
- [ ] Run existing tests (v0.x API still works!)

### Phase 2: New Code (Use v1.0.0)
- [ ] Import `CDO` class for new scripts
- [ ] Use query chaining for complex operations
- [ ] Use `F()` for anomaly calculations
- [ ] Use structured info commands (`.sinfo()`, `.griddes()`)

### Phase 3: Gradual Migration (Optional)
- [ ] Identify complex string-based commands in existing code
- [ ] Migrate to query chaining for better readability
- [ ] Replace multi-step anomaly calculations with `F()`
- [ ] Update info command parsing to use dataclasses

### Phase 4: Optimization (Optional)
- [ ] Add query introspection before expensive operations
- [ ] Use query branching for multiple analyses
- [ ] Create query templates for repeated patterns
- [ ] Leverage type hints for better IDE support

---

## Summary

### Keep Using v0.x If:
- ✅ Simple one-off commands
- ✅ Existing scripts work fine
- ✅ Don't need new features

### Migrate to v1.0.0 If:
- ✅ Complex multi-step pipelines
- ✅ Need anomaly calculations
- ✅ Want type safety & IDE support
- ✅ Need query introspection
- ✅ Want reusable analysis patterns
- ✅ Working with structured metadata

### Best Practice:
**Use v1.0.0 for new code, keep v0.x code as-is until you need to modify it.**

---

## Getting Help

- **Documentation**: [README.md](README.md)
- **Examples**: See [Real-World Climate Science Examples](README.md#real-world-climate-science-examples)
- **API Reference**: [API Reference](README.md#api-reference)
- **Issues**: [GitHub Issues](https://github.com/NarenKarthikBM/python-cdo-wrapper/issues)

---

**Welcome to v1.0.0! 🎉**

The Django ORM-style API makes climate data processing more intuitive, type-safe, and powerful than ever before.
