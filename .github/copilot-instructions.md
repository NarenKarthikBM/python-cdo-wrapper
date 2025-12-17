# GitHub Copilot Instructions for python-cdo-wrapper

This document provides context and guidelines for GitHub Copilot to assist with development, maintenance, and contribution to the `python-cdo-wrapper` package.

> **Note**: The v1.0.0 overhaul is **COMPLETE**. See `v1.0.0 Major Overhaul.md` and `IMPLEMENTATION_TRACKER.md` for the full architecture and implementation status.

## 🤖 Agent System (NEW!)

This project uses specialized GitHub Copilot agents for maintaining different modules. See [`.github/agents/README.md`](.github/agents/README.md) for complete documentation.

### Quick Agent Reference

| Agent | Use When | Example |
|-------|----------|---------|
| **@orchestrator** | Complex multi-module tasks | `@orchestrator Add new info command: gridtype` |
| **@query.agent** | Adding/modifying CDOQuery operators | `@query.agent Add select_code() operator` |
| **@parser.agent** | Creating/fixing output parsers | `@parser.agent Create GridtypeParser` |
| **@cdo-class.agent** | Adding convenience methods | `@cdo-class.agent Add gridtype() method` |
| **@test.agent** | Writing/fixing tests | `@test.agent Fix test_select_var_empty_raises` |
| **@types.agent** | Defining dataclasses/exceptions | `@types.agent Create GridtypeResult` |
| **@docs.agent** | Documentation updates | `@docs.agent Update README with F() examples` |
| **@refactor.agent** | Cross-cutting refactoring | `@refactor.agent Modernize type hints` |

### Agent Resources

- **Shared Patterns**: [`.github/agents/_shared.md`](.github/agents/_shared.md) - Source of truth for all coding patterns
- **Instructions**: [`.github/instructions/`](.github/instructions/) - Module-specific guides
- **Prompts**: [`.github/prompts/`](.github/prompts/) - Structured prompt templates
- **Scope Matrix**: [`.github/agents/matrix.yml`](.github/agents/matrix.yml) - Agent scope boundaries

### Example Workflows

**Adding a new operator**:
```
@query.agent

Add select_code() operator:
- Takes *codes: int parameters
- Uses CDO's -selcode operator
- Validate codes are positive
- Add comprehensive tests
```

**Multi-module feature**:
```
@orchestrator

Add complete support for showformat info command:
1. Parser for showformat output
2. ShowformatResult dataclass
3. showformat() method in CDO class
4. Tests and documentation
```

## Project Overview

**python-cdo-wrapper** is a Pythonic wrapper for [CDO (Climate Data Operators)](https://code.mpimet.mpg.de/projects/cdo/), designed for seamless integration with Jupyter notebooks and xarray workflows in climate science research.

### Key Features (v1.0.0 - Current)

The package now provides a **Django ORM-style `CDOQuery`** as the primary abstraction:

- **`CDOQuery` class**: Lazy, chainable query builder (like Django's `QuerySet`)
- **`CDO` class**: Factory + façade providing `.query()` and convenience methods
- **`F()` function**: Django F-expression pattern for binary operations (anomaly calculations!)
- **`BinaryOpQuery`**: Handles binary arithmetic with operator chaining (no brackets)
- **`CDOQueryTemplate`**: Reusable query templates with placeholders
- **Lazy evaluation**: Build pipelines, inspect commands, execute when ready
- **Query composition**: Clone and branch queries for variations
- **Full type safety**: Complete type hints with autocompletion
- **Structured parsers**: All info commands return typed dataclasses
- **Backward compatibility**: String-based `cdo.run()` and legacy `cdo()` function still work

### CDO Version Requirements

- **Minimum**: CDO >= 1.9.8
- **Recommended**: CDO >= 2.0.0

### Python Version Support

- **Minimum**: Python 3.9
- **Tested**: Python 3.9, 3.10, 3.11, 3.12

```python
from python_cdo_wrapper import CDO, F

cdo = CDO()

# ============================================================
# PRIMARY API: Django ORM-style lazy query chaining
# ============================================================
ds = (
    cdo.query("data.nc")
    .select_var("tas")
    .select_year(2020)
    .year_mean()
    .field_mean()
    .compute()
)

# Inspect command before execution
q = cdo.query("data.nc").select_var("tas").year_mean()
print(q.get_command())  # "cdo -yearmean -selname,tas data.nc"
print(q.explain())      # Human-readable pipeline description

# Branch queries for variations
base = cdo.query("data.nc").select_var("tas")
yearly = base.clone().year_mean().compute()
monthly = base.clone().month_mean().compute()

# ============================================================
# BINARY OPERATIONS: F() for anomalies & climatologies
# ============================================================
# One-liner anomaly calculation!
anomaly = cdo.query("data.nc").sub(F("climatology.nc")).compute()

# Standardized anomaly: (data - mean) / std
std_anomaly = (
    cdo.query("data.nc")
    .sub(F("climatology.nc"))
    .div(F("std_dev.nc"))
    .compute()
)

# Process both sides before subtraction
temp_diff = (
    cdo.query("data.nc")
    .select_var("tas")
    .select_level(1000)
    .sub(
        F("data.nc").select_var("tas").select_level(500)
    )
    .compute()
)

# ============================================================
# ADVANCED QUERY METHODS (Django-inspired)
# ============================================================
q = cdo.query("data.nc")
q.first()    # Get first timestep only
q.last()     # Get last timestep only
q.count()    # Get number of timesteps (returns int)
q.exists()   # Check if query would return data (returns bool)
q.values("tas", "pr")  # Alias for select_var()

# ============================================================
# CONVENIENCE API: Direct methods (built on query layer)
# ============================================================
info = cdo.sinfo("data.nc")           # Returns SinfoResult
grid = cdo.griddes("data.nc")         # Returns GriddesResult
ds = cdo.yearmean("data.nc")          # Returns xr.Dataset

# ============================================================
# LEGACY API: Raw string commands (backward compatible)
# ============================================================
ds, log = cdo.run("-yearmean -selname,tas data.nc")

# Original cdo() function still works
from python_cdo_wrapper import cdo as cdo_func
result = cdo_func("sinfo data.nc")
```

## Package Structure (v1.0.0 - Current)

```
python-cdo-wrapper/
├── python_cdo_wrapper/
│   ├── __init__.py              # Public API exports (CDO, CDOQuery, F, BinaryOpQuery, exceptions)
│   ├── cdo.py                   # CDO class: factory + façade (~1500 lines)
│   ├── query.py                 # CDOQuery, BinaryOpQuery, F(), CDOQueryTemplate (~2400 lines)
│   ├── core.py                  # Low-level execution & legacy cdo() function
│   ├── exceptions.py            # Exception hierarchy (CDOError, CDOExecutionError, etc.)
│   ├── validation.py            # Parameter validation utilities
│   ├── utils.py                 # Utility functions (check_cdo_available, etc.)
│   ├── parsers.py               # Legacy parsers (v0.2.x compatibility)
│   ├── types.py                 # Legacy TypedDict definitions (v0.2.x compatibility)
│   ├── py.typed                 # PEP 561 type marker
│   ├── operators/               # Operator implementations
│   │   ├── __init__.py
│   │   ├── base.py              # OperatorSpec dataclass, CDOOperator ABC
│   │   └── info.py              # Info operator classes
│   ├── parsers/                 # Output parsers (v1.0.0+)
│   │   ├── __init__.py
│   │   ├── base.py              # CDOParser abstract base class
│   │   ├── grid.py              # Grid parsers (GriddesParser, ZaxisdesParser)
│   │   └── info.py              # Info parsers (SinfoParser, InfoParser, VlistParser, PartabParser)
│   └── types/                   # Type definitions (v1.0.0+)
│       ├── __init__.py
│       ├── grid.py              # GridInfo, GridSpec, ZaxisInfo
│       ├── variable.py          # VariableInfo, DatasetVariable, TimeInfo
│       └── results.py           # SinfoResult, InfoResult, GriddesResult, VlistResult, etc.
├── tests/
│   ├── conftest.py              # Test fixtures
│   ├── test_query.py            # CDOQuery tests (~700+ tests)
│   ├── test_advanced_query.py   # Advanced query features
│   ├── test_cdo_class.py        # CDO class tests
│   ├── test_file_ops.py         # File operation tests
│   ├── test_core_legacy.py      # Legacy API tests
│   ├── test_exceptions.py       # Exception tests
│   ├── test_utils.py            # Utility function tests
│   ├── test_validation.py       # Validation tests
│   ├── test_package.py          # Package import tests
│   ├── test_operators/          # Operator tests
│   │   ├── __init__.py
│   │   └── test_info.py
│   ├── test_parsers/            # Parser tests
│   │   ├── __init__.py
│   │   ├── test_grid.py
│   │   ├── test_info.py
│   │   └── test_partab.py
│   ├── test_integration/        # Integration tests
│   │   └── __init__.py
│   └── data/                    # Test data directory
├── .github/
│   ├── workflows/               # CI/CD
│   │   ├── tests.yml            # Run tests on push/PR
│   │   └── publish.yml          # Auto-publish to PyPI on release
│   └── copilot-instructions.md  # This file
├── pyproject.toml               # Build config, dependencies
├── Pipfile                      # Pipenv configuration
├── README.md                    # User documentation
├── CHANGELOG.md                 # Version history
├── CONTRIBUTING.md              # Contribution guidelines
├── MIGRATION_GUIDE.md           # v0.x to v1.0 migration guide
├── IMPLEMENTATION_TRACKER.md    # Implementation progress tracker
├── v1.0.0 Major Overhaul.md     # Architecture specification
└── LICENSE                      # MIT license
```

## Development Workflow

### Environment Setup
```bash
# Using pipenv (preferred)
pipenv install --dev
pipenv shell

# Or using venv
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,test]"
```

### Running Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=python_cdo_wrapper

# Skip integration tests (no CDO required)
pytest -m "not integration"

# Only integration tests
pytest -m integration

# Test specific file
pytest tests/test_query.py -v

# Test specific class/function
pytest tests/test_query.py::TestCDOQuerySelection -v
```

### Code Quality
```bash
# Lint and format
ruff check .
ruff check --fix .
ruff format .

# Type checking
mypy python_cdo_wrapper

# Pre-commit (runs all checks)
pre-commit run --all-files
```

### Building
```bash
# Build package
python -m build

# Check package
twine check dist/*

# Test install
pip install dist/python_cdo_wrapper-*.whl
```

---

## v1.0.0 Architecture Details

### CDOQuery Class (`query.py`) - Primary Abstraction

The `CDOQuery` class is the core abstraction, inspired by Django's QuerySet. It's lazy, chainable, and immutable:

```python
class CDOQuery:
    """
    Lazy, chainable CDO query builder (Django QuerySet pattern).

    Operations are added by chaining methods, and execution happens
    only when terminal methods like compute() are called.

    The query is immutable - each method returns a new CDOQuery instance.
    """

    _input: Path | None
    _operators: tuple[OperatorSpec, ...]
    _options: tuple[str, ...]  # Global options like -f nc4
    _cdo: CDO | None

    def __init__(
        self,
        input_file: str | Path | None,
        operators: tuple[OperatorSpec, ...] = (),
        options: tuple[str, ...] = (),
        cdo_instance: CDO | None = None,
    ):
        """Initialize a CDO query."""
        object.__setattr__(self, "_input", Path(input_file) if input_file else None)
        object.__setattr__(self, "_operators", operators)
        object.__setattr__(self, "_options", options)
        object.__setattr__(self, "_cdo", cdo_instance)

    def _clone(self, **kwargs: Any) -> CDOQuery:
        """Create a copy with modifications (immutability pattern)."""
        return self.__class__(
            input_file=kwargs.get("input_file", self._input),
            operators=kwargs.get("operators", self._operators),
            options=kwargs.get("options", self._options),
            cdo_instance=kwargs.get("cdo_instance", self._cdo),
        )

    def _add_operator(self, spec: OperatorSpec) -> CDOQuery:
        """Add an operator and return new query (immutable)."""
        return self._clone(operators=(*self._operators, spec))
```

### F() Function and BinaryOpQuery (`query.py`)

The `F()` function enables Django F-expression style binary operations:

```python
def F(input_file: str | Path) -> CDOQuery:
    """
    Create an unbound CDOQuery for binary operations (Django F-expression pattern).

    Use F() to reference another file in arithmetic operations like sub(), add(), etc.

    Example:
        >>> anomaly = cdo.query("data.nc").sub(F("climatology.nc")).compute()
        >>> diff = cdo.query("a.nc").year_mean().sub(F("b.nc").year_mean()).compute()
    """
    return CDOQuery(input_file=input_file, operators=(), options=(), cdo_instance=None)


class BinaryOpQuery(CDOQuery):
    """
    Query for binary operations (sub, add, mul, div, min, max).

    Uses CDO's operator chaining (no bracket notation):
        cdo -sub -yearmean data.nc -fldmean other.nc output.nc

    Binary operators apply operators left-to-right to their respective input files.
    Supports nested binary operations (e.g., ifthen inside sub).
    """

    def __init__(
        self,
        operator: str,
        left: CDOQuery,
        right: CDOQuery,
        cdo_instance: CDO | None = None,
    ):
        self._operator = operator
        self._left = left
        self._right = right
        # ... initialization ...

    def get_command(self) -> str:
        """
        Build CDO command with operator chaining.

        Examples:
            - Simple: cdo -sub a.nc b.nc
            - Left has ops: cdo -sub -yearmean a.nc b.nc
            - Both have ops: cdo -sub -yearmean a.nc -fldmean b.nc
            - Nested binary: cdo -sub -ifthen mask.nc data.nc clim.nc
        """
        # Build command using operator chaining (no brackets)
        left_expr = self._build_expression(self._left)
        right_expr = self._build_expression(self._right)
        return f"cdo -{self._operator} {left_expr} {right_expr}"
```

### CDOQueryTemplate (`query.py`)

Reusable query templates with placeholders:

```python
class CDOQueryTemplate:
    """
    Template for creating reusable query patterns.

    Example:
        >>> template = CDOQueryTemplate().select_var("{var}").year_mean()
        >>> q1 = template.bind(cdo, "data.nc", var="tas")
        >>> q2 = template.bind(cdo, "data.nc", var="pr")
    """
```

### OperatorSpec Dataclass (`operators/base.py`)

```python
@dataclass(frozen=True)
class OperatorSpec:
    """
    Specification for a single CDO operator fragment.

    This immutable dataclass represents one operator in a CDO pipeline.
    """
    name: str
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] = field(default_factory=dict)

    def to_cdo_fragment(self) -> str:
        """Convert to CDO command fragment, e.g., '-selname,tas,pr'."""
        if self.args:
            args_str = ",".join(str(arg) for arg in self.args)
            return f"-{self.name},{args_str}"
        return f"-{self.name}"
```

### Exception Hierarchy (`exceptions.py`)

```python
class CDOError(Exception):
    """Base exception for all CDO errors."""
    pass

class CDOExecutionError(CDOError):
    """CDO command execution failed."""
    def __init__(self, message: str, command: str, returncode: int, stdout: str, stderr: str):
        super().__init__(message)
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

class CDOValidationError(CDOError):
    """Invalid parameters provided to an operator."""
    def __init__(self, message: str, parameter: str, value: Any, expected: str):
        super().__init__(message)
        self.parameter = parameter
        self.value = value
        self.expected = expected

class CDOFileNotFoundError(CDOError):
    """Input file does not exist."""
    def __init__(self, message: str, file_path: str):
        super().__init__(message)
        self.file_path = file_path

class CDOParseError(CDOError):
    """Failed to parse CDO output."""
    pass
```

### Result Types (`types/results.py`)

```python
@dataclass
class SinfoResult:
    """Structured result from sinfo command."""
    file_format: str
    variables: list[DatasetVariable]
    grid_coordinates: list[GridCoordinates]
    vertical_coordinates: list[VerticalCoordinates]
    time_info: TimeInfo

    @property
    def var_names(self) -> list[str]:
        """Get list of variable names."""
        return [v.name for v in self.variables if v.has_name and v.name]

    @property
    def nvar(self) -> int:
        """Get number of variables."""
        return len(self.variables)

    @property
    def time_range(self) -> tuple[str, str] | None:
        """Get first and last timestep."""
        return self.time_info.time_range

@dataclass
class GriddesResult:
    """Structured result from griddes command."""
    grids: list[GridInfo]
    # ... additional fields ...

@dataclass
class GridSpec:
    """Specification for a target grid (for remapping)."""
    gridtype: Literal["lonlat", "gaussian", "curvilinear", "unstructured"]
    xsize: int
    ysize: int
    xfirst: float = -180.0
    xinc: float | None = None
    yfirst: float = -90.0
    yinc: float | None = None

    def to_cdo_string(self) -> str:
        """Convert to CDO grid description format."""
        ...

    @classmethod
    def global_1deg(cls) -> GridSpec:
        """Create a global 1-degree grid."""
        return cls(gridtype="lonlat", xsize=360, ysize=180, xfirst=-179.5, xinc=1.0, yfirst=-89.5, yinc=1.0)

    @classmethod
    def global_half_deg(cls) -> GridSpec:
        """Create a global 0.5-degree grid."""
        return cls(gridtype="lonlat", xsize=720, ysize=360, xfirst=-179.75, xinc=0.5, yfirst=-89.75, yinc=0.5)
```

---

## Implemented Operators (All Phases Complete)

### Selection Operators (Phase 3) ✅

| Query Method | CDO Operator | Parameters |
|--------------|--------------|------------|
| `select_var()` | `-selname` | `*names: str` |
| `select_level()` | `-sellevel` | `*levels: float` |
| `select_year()` | `-selyear` | `*years: int` |
| `select_month()` | `-selmon` | `*months: int` |
| `select_day()` | `-selday` | `*days: int` |
| `select_hour()` | `-selhour` | `*hours: int` |
| `select_season()` | `-selseason` | `*seasons: str` |
| `select_date()` | `-seldate` | `start: str, end: str \| None` |
| `select_time()` | `-seltime` | `*times: str` |
| `select_timestep()` | `-seltimestep` | `*steps: int` |
| `select_code()` | `-selcode` | `*codes: int` |
| `select_level_idx()` | `-sellevidx` | `*indices: int` |
| `select_level_type()` | `-selltype` | `ltype: int` |
| `select_grid()` | `-selgrid` | `grid_num: int` |
| `select_zaxis()` | `-selzaxis` | `zaxis_num: int` |
| `select_region()` | `-sellonlatbox` | `lon1, lon2, lat1, lat2: float` |
| `select_index_box()` | `-selindexbox` | `x1, x2, y1, y2: int` |
| `select_mask()` | `-ifthen` | `mask_file: str \| Path` |

### Statistical Operators (Phase 4) ✅

#### Time Statistics
| Query Method | CDO Operator |
|--------------|--------------|
| `time_mean()` | `-timmean` |
| `time_sum()` | `-timsum` |
| `time_min()` | `-timmin` |
| `time_max()` | `-timmax` |
| `time_std()` | `-timstd` |
| `time_var()` | `-timvar` |
| `time_range()` | `-timrange` |

#### Year/Month/Day/Hour Statistics
| Query Method | CDO Operator |
|--------------|--------------|
| `year_mean()`, `year_sum()`, `year_min()`, `year_max()`, `year_std()`, `year_var()` | `-yearmean`, etc. |
| `month_mean()`, `month_sum()`, `month_min()`, `month_max()`, `month_std()` | `-monmean`, etc. |
| `day_mean()`, `day_sum()` | `-daymean`, `-daysum` |
| `hour_mean()` | `-hourmean` |
| `season_mean()`, `season_sum()` | `-seasmean`, `-seassum` |

#### Field Statistics
| Query Method | CDO Operator |
|--------------|--------------|
| `field_mean()` | `-fldmean` |
| `field_sum()` | `-fldsum` |
| `field_min()` | `-fldmin` |
| `field_max()` | `-fldmax` |
| `field_std()` | `-fldstd` |
| `field_var()` | `-fldvar` |
| `field_range()` | `-fldrange` |
| `field_percentile(p)` | `-fldpctl,p` |
| `zonal_mean()`, `zonal_sum()` | `-zonmean`, `-zonsum` |
| `meridional_mean()` | `-mermean` |

#### Vertical Statistics
| Query Method | CDO Operator |
|--------------|--------------|
| `vert_mean()` | `-vertmean` |
| `vert_sum()` | `-vertsum` |
| `vert_min()` | `-vertmin` |
| `vert_max()` | `-vertmax` |
| `vert_std()` | `-vertstd` |
| `vert_int()` | `-vertint` |

#### Running Statistics
| Query Method | CDO Operator |
|--------------|--------------|
| `running_mean(n)` | `-runmean,n` |
| `running_sum(n)` | `-runsum,n` |
| `running_min(n)` | `-runmin,n` |
| `running_max(n)` | `-runmax,n` |
| `running_std(n)` | `-runstd,n` |

#### Percentile Operations
| Query Method | CDO Operator |
|--------------|--------------|
| `time_percentile(p)` | `-timpctl,p` |
| `year_percentile(p)` | `-yearpctl,p` |
| `month_percentile(p)` | `-monpctl,p` |

### Arithmetic Operators (Phase 5) ✅

#### Constant Arithmetic
| Query Method | CDO Operator |
|--------------|--------------|
| `add_constant(c)` | `-addc,c` |
| `subtract_constant(c)` | `-subc,c` |
| `multiply_constant(c)` | `-mulc,c` |
| `divide_constant(c)` | `-divc,c` |

#### Binary Arithmetic (via F())
| Query Method | CDO Operator |
|--------------|--------------|
| `sub(F(...))` | `-sub` |
| `add(F(...))` | `-add` |
| `mul(F(...))` | `-mul` |
| `div(F(...))` | `-div` |
| `min(F(...))` | `-min` |
| `max(F(...))` | `-max` |

#### Math Functions
| Query Method | CDO Operator |
|--------------|--------------|
| `abs()` | `-abs` |
| `sqrt()` | `-sqrt` |
| `sqr()` | `-sqr` |
| `exp()` | `-exp` |
| `ln()` | `-ln` |
| `log10()` | `-log10` |
| `sin()`, `cos()`, `tan()` | `-sin`, `-cos`, `-tan` |

#### Masking Operations
| Query Method | CDO Operator |
|--------------|--------------|
| `ifthen()` / `mask()` | `-ifthen` |
| `ifthenelse()` / `where()` | `-ifthenelse` |
| `set_missval()` | `-setmissval` |
| `setmisstoc()` / `miss_to_const()` | `-setmisstoc` |

### Interpolation Operators (Phase 6) ✅

#### Horizontal Interpolation
| Query Method | CDO Operator |
|--------------|--------------|
| `remap_bil(grid)` | `-remapbil,grid` |
| `remap_bic(grid)` | `-remapbic,grid` |
| `remap_nn(grid)` | `-remapnn,grid` |
| `remap_dis(grid)` | `-remapdis,grid` |
| `remap_con(grid)` | `-remapcon,grid` |
| `remap_con2(grid)` | `-remapcon2,grid` |
| `remap_laf(grid)` | `-remaplaf,grid` |

#### Vertical Interpolation
| Query Method | CDO Operator |
|--------------|--------------|
| `interp_level(*levels)` | `-intlevel,levels` |
| `interp_level3d(file)` | `-intlevel3d,file` |
| `ml_to_pl(*levels)` | `-ml2pl,levels` |

### Modification Operators (Phase 7) ✅

| Query Method | CDO Operator |
|--------------|--------------|
| `set_name(name)` | `-setname,name` |
| `set_code(code)` | `-setcode,code` |
| `set_unit(unit)` | `-setunit,unit` |
| `set_grid(grid)` | `-setgrid,grid` |
| `set_grid_type(type)` | `-setgridtype,type` |
| `invert_lat()` | `-invertlat` |
| `set_level(*levels)` | `-setlevel,levels` |
| `set_level_type(ltype)` | `-setltype,ltype` |
| `set_time_axis(date, time, inc)` | `-settaxis,date,time,inc` |
| `set_ref_time(date, time)` | `-setreftime,date,time` |
| `set_calendar(calendar)` | `-setcalendar,calendar` |
| `shift_time(offset)` | `-shifttime,offset` |
| `set_range_to_miss(min, max)` | `-setrtomiss,min,max` |
| `set_attribute(att, val)` | `-setattribute,att=val` |
| `del_attribute(att)` | `-delattribute,att` |

### File Operations (Phase 8) ✅

CDO class methods (not query chain methods):

| CDO Method | CDO Operator |
|------------|--------------|
| `merge(*files)` | `-merge` |
| `mergetime(*files)` | `-mergetime` |
| `cat(*files)` | `-cat` |
| `copy(input, output)` | `-copy` |
| `split_year(input, prefix)` | `-splityear` |
| `split_month(input, prefix)` | `-splitmon` |
| `split_day(input, prefix)` | `-splitday` |
| `split_hour(input, prefix)` | `-splithour` |
| `split_name(input, prefix)` | `-splitname` |
| `split_level(input, prefix)` | `-splitlevel` |
| `split_timestep(input, prefix, n)` | `-splitsel,n` |

Query option for output format:
| Query Method | CDO Option |
|--------------|------------|
| `output_format(fmt)` | `-f format` |

### Info Operators (Phase 2) ✅

CDO class methods returning structured results:

| CDO Method | CDO Operator | Return Type |
|------------|--------------|-------------|
| `sinfo(file)` | `sinfo` | `SinfoResult` |
| `info(file)` | `info` | `InfoResult` |
| `griddes(file)` | `griddes` | `GriddesResult` |
| `zaxisdes(file)` | `zaxisdes` | `ZaxisdesResult` |
| `vlist(file)` | `vlist` | `VlistResult` |
| `partab(file)` | `partab` | `PartabResult` |

### Advanced Query Methods (Phase 9) ✅

| Method | Description |
|--------|-------------|
| `first()` | Get first timestep only |
| `last()` | Get last timestep only |
| `exists()` | Check if query would return data |
| `count()` | Get number of timesteps |
| `values(*vars)` | Alias for select_var() |

---

## Code Style Guidelines

### General Rules
- **Python version**: Support 3.9+
- **Line length**: 88 characters (ruff default)
- **Formatter**: ruff format
- **Linter**: ruff check
- **Type checker**: mypy with strict settings

### Import Order (handled by ruff)
1. Standard library imports
2. Third-party imports
3. Local imports

### Type Hints
- All public functions MUST have type hints
- Use `from __future__ import annotations` for modern syntax
- Use `TYPE_CHECKING` block for import-only types
- Use `pathlib.Path` over `os.path` operations
- Use `TypeVar` and `Generic` for operator base classes
- Prefer `dataclass` over `TypedDict` for result types

### Docstrings
Use Google-style docstrings for all public APIs:

```python
def select_var(self, *names: str) -> CDOQuery:
    """
    Select variables by name.

    Args:
        *names: Variable names to select.

    Returns:
        CDOQuery: New query with selection operator added.

    Raises:
        CDOValidationError: If no variable names are provided.

    Example:
        >>> cdo = CDO()
        >>> q = cdo.query("data.nc").select_var("tas", "pr")
        >>> print(q.get_command())
        'cdo -selname,tas,pr data.nc'

    See Also:
        - select_code: Select by variable code
        - select_level: Select by vertical level
    """
```

### Operator Method Signature Conventions

#### Query Methods (Chainable - Returns CDOQuery)
```python
def operator_method(self, *args, **kwargs) -> CDOQuery:
    """Adds operator to query chain (lazy). Returns new query."""
    return self._add_operator(OperatorSpec("operator_name", args=args))
```

#### Binary Operations (Returns BinaryOpQuery)
```python
def sub(self, other: CDOQuery | str | Path) -> BinaryOpQuery:
    """Subtract another dataset. Use with F() for file references."""
    return self._binary_op("sub", other)
```

#### CDO Convenience Methods (Returns xr.Dataset)
```python
def operator_name(
    self,
    input_file: str | Path,
    *,
    output: str | Path | None = None,
) -> xr.Dataset:
    """Convenience method - delegates to query layer."""
    return self.query(input_file).operator_method().compute(output=output)
```

#### Info Methods (Returns Structured Result)
```python
def sinfo(self, input_file: str | Path) -> SinfoResult:
    """Get structured info about a file."""
    output = self._execute_text_command(f"sinfo {input_file}")
    return SinfoParser().parse(output)
```

---

## Testing Guidelines

### Test Categories
- **Unit tests**: Mock subprocess, test logic (no CDO required)
- **Integration tests**: Mark with `@pytest.mark.integration` (requires CDO)
- **Query tests**: Test CDOQuery building, cloning, command generation
- **Parser tests**: Test output parsing with sample CDO output

### Key Test Files
- `tests/test_query.py`: Main CDOQuery tests (700+ tests)
- `tests/test_advanced_query.py`: Advanced query features
- `tests/test_cdo_class.py`: CDO class tests
- `tests/test_file_ops.py`: File operation tests
- `tests/test_parsers/`: Parser tests

### Fixtures (in `conftest.py`)
- `sample_nc_file`: Creates minimal NetCDF with temperature data
- `sample_nc_file_with_time`: NetCDF with datetime coordinates
- `multi_var_nc_file`: NetCDF with multiple variables
- `cdo_instance`: Pre-configured CDO class instance

### Test Naming
```python
class TestCDOQuerySelection:
    def test_select_var_single(self):
        """Test selecting a single variable."""
        ...

    def test_select_var_multiple(self):
        """Test selecting multiple variables."""
        ...

    def test_select_var_empty_raises(self):
        """Test that empty names raises CDOValidationError."""
        ...


class TestBinaryOperations:
    def test_sub_simple(self):
        """Test simple subtraction with F()."""
        ...

    def test_sub_with_pipeline(self):
        """Test subtraction with pipelines on both sides."""
        ...
```

### Mocking Pattern
```python
with patch("python_cdo_wrapper.core.subprocess.run") as mock_run:
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout="output",
        stderr="",
    )
    result = cdo.run("sinfo test.nc", check_files=False)
```

---

## Adding New Features

### Adding a New Operator

1. **Add query method** to `CDOQuery` class in `query.py`
```python
def new_operator(self, param: type) -> CDOQuery:
    """Description of operator."""
    if not param:
        raise CDOValidationError(...)
    return self._add_operator(OperatorSpec("cdooperator", args=(param,)))
```

2. **Write tests** in `tests/test_query.py`
```python
def test_new_operator_command(self, sample_nc_file):
    q = cdo.query(sample_nc_file).new_operator("value")
    assert "-cdooperator,value" in q.get_command()

def test_new_operator_validation(self, sample_nc_file):
    with pytest.raises(CDOValidationError):
        cdo.query(sample_nc_file).new_operator("")
```

3. **Add convenience method** to `CDO` class in `cdo.py` (optional)
```python
def new_operator(self, param: type, input_file: str | Path, *, output: str | Path | None = None) -> xr.Dataset:
    return self.query(input_file).new_operator(param).compute(output=output)
```

4. **Update documentation** (README, CHANGELOG)

### Adding a New Parser

1. Create parser class in `parsers/*.py` inheriting from `CDOParser`
2. Create result dataclass in `types/results.py`
3. Implement `parse()` method
4. Add tests with sample CDO output
5. Export from `parsers/__init__.py`

---

## Version Management

### Version Locations (keep in sync)
1. `python_cdo_wrapper/__init__.py`: `__version__ = "X.Y.Z"`
2. `pyproject.toml`: `version = "X.Y.Z"`

### Versioning Scheme (SemVer)
- **MAJOR**: Breaking API changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

### Release Process
1. Update version in both locations
2. Update `CHANGELOG.md` with release notes
3. Commit: `git commit -m "Release vX.Y.Z"`
4. Tag: `git tag vX.Y.Z`
5. Push: `git push origin main --tags`
6. GitHub Actions publishes to PyPI automatically

---

## Key Architectural Decisions

1. **Frozen/immutable CDOQuery** - Each operation returns a new query instance
2. **Query methods first** - All operators implemented as CDOQuery methods
3. **CDO class delegates** to query layer for convenience methods
4. **F() function** for Django F-expression pattern in binary operations
5. **Operator chaining for binary operations** - No bracket notation, standard CDO syntax
6. **Dataclasses for results** - SinfoResult, GriddesResult, etc.
7. **Lazy evaluation** - Queries build commands, only execute on compute()

---

## Common Tasks

### Fix All Linting Issues
```bash
ruff check --fix . && ruff format .
```

### Debug a Test
```bash
pytest tests/test_query.py::TestClassName::test_name -v -s
```

### Check Package Before Release
```bash
rm -rf dist/ build/
python -m build
twine check dist/*
pip install dist/*.whl
python -c "from python_cdo_wrapper import CDO; print(CDO)"
```

---

## Notes for Copilot

1. **Always run ruff** after making changes: `ruff check --fix . && ruff format .`
2. **Keep type hints** accurate and complete
3. **Update tests** when modifying functionality
4. **Use pathlib.Path** instead of os.path operations
5. **Maintain backward compatibility** with v0.x legacy API
6. **Document all public APIs** with Google-style docstrings
7. **Mark integration tests** with `@pytest.mark.integration`
8. **Keep CHANGELOG.md updated** for notable changes
9. **Test locally** before pushing: `pytest && ruff check .`
10. **Query methods are immutable** - always return new CDOQuery
11. **Use dataclasses** for result types, not TypedDict
12. **Binary operations use operator chaining** - no brackets, standard CDO syntax
13. **Reference IMPLEMENTATION_TRACKER.md** for implementation status
14. **F() creates unbound queries** - can be used with any CDO instance

---

## External Resources

- [CDO Documentation](https://code.mpimet.mpg.de/projects/cdo/embedded/index.html)
- [CDO Operators Reference](https://code.mpimet.mpg.de/projects/cdo/embedded/cdo_refcard.pdf)
- [CDO User Guide (PDF)](https://code.mpimet.mpg.de/projects/cdo/embedded/cdo.pdf)
- [xarray Documentation](https://docs.xarray.dev/)
- [Python Packaging Guide](https://packaging.python.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Semantic Versioning](https://semver.org/)
- [NetCDF Climate Data Conventions](https://cfconventions.org/)
- [Django QuerySet API Reference](https://docs.djangoproject.com/en/stable/ref/models/querysets/)
