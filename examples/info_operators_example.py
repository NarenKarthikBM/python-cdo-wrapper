"""
Example: Information Operators as Terminating Query Methods

This example demonstrates how to use CDO information operators
as terminating methods on CDOQuery.

These methods execute immediately (like .compute()) but return
parsed metadata instead of xarray.Dataset objects.
"""

from python_cdo_wrapper import CDO

# Initialize CDO
cdo = CDO()

# Example file (replace with your own)
data_file = "data.nc"

# ============================================================
# BASIC USAGE: Get info without processing
# ============================================================

# Get variable names
variables = cdo.query(data_file).showname()
print(f"Variables: {variables}")

# Get number of timesteps
n_times = cdo.query(data_file).ntime()
print(f"Number of timesteps: {n_times}")

# Get number of variables
n_vars = cdo.query(data_file).nvar()
print(f"Number of variables: {n_vars}")

# ============================================================
# ADVANCED USAGE: Get info after processing
# ============================================================

# Get variable names after selecting subset
selected_vars = (
    cdo.query(data_file)
    .select_var("tas", "pr")
    .showname()
)
print(f"Selected variables: {selected_vars}")

# Get number of timesteps after year selection
n_times_2020 = (
    cdo.query(data_file)
    .select_year(2020)
    .ntime()
)
print(f"Timesteps in 2020: {n_times_2020}")

# Get dates after processing
dates = (
    cdo.query(data_file)
    .select_var("tas")
    .select_year(2020, 2021)
    .showdate()
)
print(f"Dates: {dates[:5]}...")  # Show first 5

# ============================================================
# STRUCTURED INFO: Get detailed metadata after processing
# ============================================================

# Get comprehensive dataset info after processing
info = (
    cdo.query(data_file)
    .year_mean()
    .sinfo()
)
print(f"Variables after year_mean: {info.var_names}")
print(f"Number of variables: {info.nvar}")
print(f"Time range: {info.time_range}")

# Get grid description after remapping
grid = (
    cdo.query(data_file)
    .remap_bil("r180x90")
    .griddes()
)
print(f"Grid type after remapping: {grid.grids[0].gridtype}")
print(f"Grid size: {grid.grids[0].xsize} x {grid.grids[0].ysize}")

# ============================================================
# COMPARISON: Query method vs CDO class method
# ============================================================

# Old way: CDO class method (requires file)
vars_old = cdo.showname(data_file)

# New way: Query terminating method (can include processing)
vars_new = cdo.query(data_file).year_mean().showname()

print(f"Old way (no processing): {vars_old}")
print(f"New way (with processing): {vars_new}")

# ============================================================
# KEY BENEFITS
# ============================================================
print("""
Key Benefits of Info Operators as Query Terminators:
1. No intermediate files needed
2. Chain processing and metadata extraction
3. More intuitive API (everything in Query API)
4. Consistent with Django ORM pattern
5. Less boilerplate code
""")
