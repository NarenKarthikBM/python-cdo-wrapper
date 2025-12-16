# Release Notes: python-cdo-wrapper v1.1.0

**Release Date:** December 16, 2024  
**Type:** Minor Release - New Features

---

## 🎉 What's New

### Shapefile Masking Support

The headline feature of v1.1.0 is **comprehensive shapefile masking** for NetCDF files. Users can now clip climate data to geographic regions defined by shapefiles in a single, chainable operation.

**Key Highlights:**
```python
# One-liner regional masking
masked = cdo.query("global_data.nc").mask_by_shapefile("region.shp").compute()

# Chain with other CDO operators
result = (
    cdo.query("daily_precip.nc")
    .mask_by_shapefile("sahel.shp")
    .year_mean()
    .field_mean()
    .compute()
)
```

**Features:**
- ✅ Complete automated pipeline (load shapefile → create mask → apply → cleanup)
- ✅ Support for both 1D (regular) and 2D (curvilinear) grids
- ✅ Automatic CRS reprojection to WGS84
- ✅ Multi-polygon shapefile support
- ✅ Custom coordinate naming (`lat_name`, `lon_name` parameters)
- ✅ Automatic temporary file cleanup
- ✅ Secure temp file handling (no race conditions)

**Installation:**
```bash
pip install python-cdo-wrapper[shapefiles]
```

This optional dependency group includes `geopandas>=0.10.0` and `shapely>=2.0.0`.

---

## 🔧 Technical Improvements

### Enhanced Binary Operations

**Fixed:** Binary operators (`add`, `sub`, `mul`, `div`, `min`, `max`) no longer generate unnecessary brackets in CDO commands.

- Binary operators take exactly two inputs and CDO assigns them unambiguously right-to-left
- Commands are now cleaner: `cdo -sub -yearmean data.nc clim.nc`
- Previously generated: `cdo -sub [ -yearmean data.nc ] clim.nc`
- Follows CDO best practices and may improve performance

### Security Enhancements

- Replaced unsafe `tempfile.mktemp()` with secure `tempfile.mkstemp()` in shapefile masking
- Prevents race condition vulnerabilities when creating temporary mask files
- Follows Python security best practices

---

## 📋 Complete Feature List

### New Operators

#### Shapefile Masking
- **`mask_by_shapefile(shapefile_path, lat_name="lat", lon_name="lon")`**
  - Clip NetCDF to shapefile polygon extent
  - Chainable with all other CDO operators
  - Returns masked xarray.Dataset

#### Advanced Utilities
- **`create_mask_from_shapefile(shapefile_path, reference_nc, lat_name, lon_name)`**
  - Create reusable binary mask files
  - Useful for processing multiple files with same region
  - Returns xarray.Dataset with mask variable

### Information Operators (Query API)

All CDO information commands are now available as terminating query methods (from v1.0.1, included in this release):

**Variable Information:**
- `.showname()` - List variable names
- `.showcode()` - List variable codes
- `.showunit()` - List variable units
- `.showlevel()` - List vertical levels

**Time Information:**
- `.showdate()` - List timestamps
- `.showtime()` - List time values
- `.ntime()` - Count timesteps

**Dataset Information:**
- `.sinfo()` - Structured file info (returns `SinfoResult`)
- `.info()` - General info (returns `InfoResult`)
- `.vlist()` - Variable list (returns `VlistResult`)
- `.partab()` - Parameter table (returns `PartabResult`)
- `.nvar()` - Count variables
- `.nlevel()` - Count levels

**Grid Information:**
- `.griddes()` - Grid description (returns `GriddesResult`)
- `.zaxisdes()` - Z-axis description (returns `ZaxisdesResult`)

These methods execute immediately and return structured results, making them convenient for pipeline inspection.

---

## 🔄 Migration Guide

### From v1.0.x to v1.1.0

**No breaking changes** - v1.1.0 is fully backward compatible with v1.0.x.

### Optional: Adopt Shapefile Masking

If you currently mask data manually with separate mask files:

**Before (v1.0.x):**
```python
# Manual masking with pre-created mask
result = cdo.query("data.nc").select_mask("region_mask.nc").compute()
```

**After (v1.1.0):**
```python
# Direct shapefile masking
result = cdo.query("data.nc").mask_by_shapefile("region.shp").compute()
```

### Optional: Install Shapefile Support

```bash
# If you need shapefile masking
pip install --upgrade python-cdo-wrapper[shapefiles]

# Or just core package (no shapefile support)
pip install --upgrade python-cdo-wrapper
```

---

## 📦 Installation & Upgrade

### New Installation
```bash
# Core package
pip install python-cdo-wrapper

# With shapefile support
pip install python-cdo-wrapper[shapefiles]

# All optional features
pip install python-cdo-wrapper[shapefiles,dev,test]
```

### Upgrading from v1.0.x
```bash
pip install --upgrade python-cdo-wrapper
# Or with shapefiles:
pip install --upgrade python-cdo-wrapper[shapefiles]
```

### Prerequisites
- Python >= 3.9
- CDO >= 1.9.8 (recommended: >= 2.0.0)
- For shapefile masking: geopandas >= 0.10.0, shapely >= 2.0.0

---

## 📚 Documentation

### Updated Documentation
- **README.md** - Added comprehensive shapefile masking section
- **CHANGELOG.md** - Detailed changelog for v1.1.0
- **examples/shapefile_masking_example.py** - 7 usage scenarios

### Key Examples

#### Example 1: Simple Regional Analysis
```python
from python_cdo_wrapper import CDO

cdo = CDO()

# Analyze temperature over Amazon basin
regional_temp = (
    cdo.query("global_temperature.nc")
    .mask_by_shapefile("amazon_basin.shp")
    .year_mean()
    .field_mean()
    .compute()
)
```

#### Example 2: Multi-step Climate Analysis
```python
# Calculate regional precipitation anomaly
anomaly = (
    cdo.query("monthly_precip.nc")
    .mask_by_shapefile("sahel.shp")
    .sub(F("climatology.nc"))
    .year_mean()
    .compute()
)
```

#### Example 3: Reusable Masks for Multiple Files
```python
from python_cdo_wrapper import create_mask_from_shapefile

# Create mask once
mask_ds = create_mask_from_shapefile(
    shapefile_path="europe.shp",
    reference_nc="template.nc"
)
mask_ds.to_netcdf("europe_mask.nc")

# Reuse for multiple files
file1 = cdo.query("data1.nc").select_mask("europe_mask.nc").compute()
file2 = cdo.query("data2.nc").select_mask("europe_mask.nc").compute()
```

---

## ⚡ Performance Notes

### Shapefile Masking Performance

**For small to medium grids** (< 100k points): Masking is fast, typically < 1 second.

**For large grids** (e.g., global 0.5° = ~260k points): The point-in-polygon test loop can take several seconds.

**Optimization strategies:**
1. **Pre-create and reuse masks** for multiple files with the same region
2. **Use coarser grids** when high resolution isn't needed
3. **Consider CDO's native region selection** (`.select_region()`) for simple rectangular boxes

Example of mask reuse:
```python
# Create mask once (may be slow for large grids)
mask_ds = create_mask_from_shapefile("region.shp", "data.nc")
mask_ds.to_netcdf("region_mask.nc")

# Reuse for many files (fast)
for file in file_list:
    result = cdo.query(file).select_mask("region_mask.nc").year_mean().compute()
```

---

## 🧪 Testing

### Test Coverage
- **9 unit tests** for shapefile masking (all passing)
- **4 integration tests** (require CDO installation)
- **Security test** verifying secure temp file creation
- **Cleanup test** verifying automatic temp file deletion

### Running Tests
```bash
# Install with test dependencies
pip install python-cdo-wrapper[test,shapefiles]

# Run shapefile masking tests
pytest tests/test_shapefile_masking.py -v

# Run all tests
pytest
```

---

## 🐛 Known Issues & Limitations

### Shapefile Masking
1. **Large grids**: Point-in-polygon tests can be slow (see Performance Notes above)
2. **Complex polygons**: Very complex multi-polygon shapefiles may take longer to process
3. **CRS requirements**: Shapefile must be in geographic coordinates or reprojectable to WGS84

### Workarounds
- For repeated analyses on the same region, create and reuse mask files
- For simple rectangular regions, use `.select_region()` instead
- For very large grids, consider downsampling before masking

---

## 🔗 Resources

- **GitHub Repository:** https://github.com/NarenKarthikBM/python-cdo-wrapper
- **PyPI Package:** https://pypi.org/project/python-cdo-wrapper/
- **CDO Documentation:** https://code.mpimet.mpg.de/projects/cdo/
- **GeoPandas Documentation:** https://geopandas.org/

---

## 🙏 Acknowledgments

Special thanks to:
- The CDO team for the excellent climate data operators
- The geopandas and shapely communities for robust geospatial tools
- All contributors and users providing feedback

---

## 📝 Full Changelog

For complete details, see [CHANGELOG.md](CHANGELOG.md).

### v1.1.0 Summary
- ✅ Added shapefile masking with `mask_by_shapefile()` operator
- ✅ Fixed binary operation bracket generation
- ✅ Enhanced security with secure temp file creation
- ✅ Improved performance documentation
- ✅ Enhanced test coverage for temp file cleanup
- ✅ Updated documentation and examples

---

**Questions or Issues?** Please open an issue on GitHub: https://github.com/NarenKarthikBM/python-cdo-wrapper/issues
