# Path Analysis Report - Code Reorganization Findings

## Executive Summary

Analyzed code across `lennard_jones_mc/` and `lennard_jones_mc_rs/` for hardcoded paths and import statements that would be affected by directory reorganization.

**Total Issues Found: 22**

| Severity | Count | Action Required |
|----------|-------|-----------------|
| **HIGH** | 13 | Must fix before reorganization |
| **MEDIUM** | 5 | Should fix for proper organization |
| **LOW** | 4 | Already compatible / self-contained |

---

## HIGH SEVERITY ISSUES (13 total)

### Category 1: Python Module Imports (5 issues)

These files import Python modules assuming they are in the same directory. After moving to `src/`, imports will fail.

#### Issue #1: argon_gemc_run.py
- **File**: `lennard_jones_mc/argon_gemc_run.py`
- **Line**: 17
- **Current**: `import lennard_jones_gemc_3d as gemc`
- **Problem**: Assumes gemc module is in current directory
- **Solution**: Use relative import or update sys.path
- **Impact**: Script won't run after reorganization

#### Issue #2: benchmark_python_rust.py
- **File**: `lennard_jones_mc/benchmark_python_rust.py`
- **Line**: 21
- **Current**: `import lennard_jones_gemc_3d as gemc`
- **Problem**: Same as above - module import assumes same directory
- **Solution**: Update import path
- **Impact**: Benchmark script will fail

#### Issues #3-5: Cross-module imports (lj_core)
- **Files**:
  - `lennard_jones_gemc_3d.py:17`
  - `lennard_jones_mc_3d.py:14`
  - `lennard_jones_mc.py:13`
- **Current Pattern**: `from lj_core import (...)`
- **Problem**: All three files import from lj_core in same directory
- **Solution**: Use relative imports (`from .lj_core import`) or update absolute paths
- **Impact**: Affects entire import chain; breaks all GEMC/3D functionality

---

### Category 2: Rust Binaries - File Output Paths (8 issues)

All Rust binaries currently save results directly to the current working directory. These should be organized into a `results/` subdirectory.

#### Issue #6-7: argon.rs
- **Lines**: 73-74 (CSV), 95-96 (JSON)
- **Current Paths**:
  ```rust
  let csv_path = format!("argon_gemc_density_history_N{}_C{}_cutoff_celllist_rs.csv", ...);
  let json_path = format!("argon_gemc_summary_N{}_C{}_cutoff_celllist_rs.json", ...);
  ```
- **Required Changes**: 
  - Prepend `"results/"` to both paths
  - Add `std::fs::create_dir_all("results")?` before file write
- **Impact**: Results mix with source files

#### Issue #8-9: argon_compare.rs
- **Lines**: 60-61 (CSV), 74-75 (JSON)
- **Current Paths**: Same as argon.rs above
- **Required Changes**: Same as argon.rs
- **Impact**: Results from different variants mix together

#### Issue #10-11: argon_t136k_nocutoff.rs
- **Lines**: 56-57 (CSV), 71-72 (JSON)
- **Current Paths**:
  ```rust
  let csv_path = "argon_gemc_T136K_nocutoff_density_history.csv";
  let json_path = "argon_gemc_T136K_nocutoff_summary.json";
  ```
- **Required Changes**: 
  - Change to: `"results/argon_gemc_T136K_nocutoff_density_history.csv"`
  - Change to: `"results/argon_gemc_T136K_nocutoff_summary.json"`
- **Impact**: Hardcoded filenames save to root directory

#### Issue #12-13: argon_vle.rs
- **Line 21-22**: `let csv_path = "argon_vle_multitemp_rs.csv";`
- **Line 76**: `format!("argon_vle_density_history_T{:.0}K.csv")`
- **Problem**: Main output CSV + per-temperature CSV files save to cwd
- **Required Changes**:
  - Change line 21: `"results/argon_vle_multitemp_rs.csv"`
  - Change line 76: `format!("results/argon_vle_density_history_T{:.0}K.csv")`
  - Add create_dir_all("results")
- **Impact**: Creates many files in root directory for multi-temperature runs

---

## MEDIUM SEVERITY ISSUES (5 total)

### Analysis Scripts Path Problems

Scripts in `lennard_jones_mc_rs/analysis/` assume CSV files are in their own directory. After Rust binaries are updated to save to `results/`, these scripts won't find the data.

#### Issue #14-15: plot_argon_density.py
- **File**: `lennard_jones_mc_rs/analysis/plot_argon_density.py`
- **Lines**: 19-20
- **Current**:
  ```python
  CSV_PATH = Path(__file__).parent / "argon_vle_density_history_T148K.csv"
  OUTPUT_PATH = Path(__file__).parent / "argon_vle_density_history_T148K.png"
  ```
- **Problem**: Looks for CSV in `analysis/` directory, not `results/`
- **Solution**: Update to `Path(__file__).parent.parent / "results" / "..."`
- **Impact**: Cannot find generated CSV files

#### Issue #16-17: plot_production_average.py
- **File**: `lennard_jones_mc_rs/analysis/plot_production_average.py`
- **Lines**: 38 (glob), 81 (save)
- **Current**:
  ```python
  history_files = sorted(script_dir.glob("argon_vle_density_history_T*K.csv"))
  output_path = script_dir / "argon_vle_production_average.png"
  ```
- **Problem**: Globs in `analysis/` directory, saves there too
- **Solution**: Update glob to search in `results/` or parent/results
- **Impact**: Won't find temperature-specific density files

#### Issue #18: plot_vapor_pressure_curve.py
- **File**: `lennard_jones_mc_rs/analysis/plot_vapor_pressure_curve.py`
- **Line**: 39
- **Current**:
  ```python
  history_files = sorted(SCRIPT_DIR.glob("argon_vle_density_history_T*K.csv"))
  ```
- **Problem**: Globs in current script directory
- **Solution**: Update glob path pattern to include results/ or parent path
- **Impact**: Won't find data files for vapor pressure curve generation

---

## LOW SEVERITY ISSUES (4 total)

These files are already compatible with reorganization due to relative path usage.

### Already Compatible Files

1. **lennard_jones_mc/argon_gemc_run.py** (Lines 107, 121)
   - Uses `out_dir = Path(__file__).resolve().parent`
   - Will work as-is (saves to script directory)
   - ✓ No changes needed

2. **lennard_jones_mc/benchmark_python_rust.py** (Lines 164-165)
   - Uses `script_dir = Path(__file__).resolve().parent`
   - Will work as-is (saves to script directory)
   - ✓ No changes needed

3. **lennard_jones_mc_rs/results/N200000/plot_argon_density.py**
   - Self-contained in results subdirectory
   - Uses relative paths for local CSV files
   - ✓ No changes needed

4. **lennard_jones_mc_rs/results/temperature_variation/plot_argon_density.py**
   - Self-contained in results subdirectory
   - Uses relative paths for local CSV files
   - ✓ No changes needed

---

## Files Scanned Summary

### Python Core Modules (lennard_jones_mc/)
- ✓ `lj_core.py` - No hardcoded paths (core module)
- ✓ `lennard_jones_mc.py` - Imports lj_core (ISSUE)
- ✓ `lennard_jones_mc_3d.py` - Imports lj_core (ISSUE)
- ✓ `lennard_jones_gemc_3d.py` - Imports lj_core (ISSUE)
- ✓ `argon_gemc_run.py` - Imports gemc + saves CSV/JSON (ISSUE)
- ✓ `benchmark_python_rust.py` - Imports gemc + saves PNG (ISSUE)

### Rust Binaries (lennard_jones_mc_rs/src/bin/)
- ✓ `argon.rs` - Saves CSV + JSON (ISSUE)
- ✓ `argon_compare.rs` - Saves CSV + JSON (ISSUE)
- ✓ `argon_t136k_nocutoff.rs` - Saves CSV + JSON (ISSUE)
- ✓ `argon_vle.rs` - Saves multiple CSV + JSON files (ISSUE)
- ✓ `argon_bench.rs` - No file I/O (OK)

### Python Analysis Scripts
- ✓ `lennard_jones_mc_rs/analysis/plot_argon_density.py` (ISSUE)
- ✓ `lennard_jones_mc_rs/analysis/plot_production_average.py` (ISSUE)
- ✓ `lennard_jones_mc_rs/analysis/plot_vapor_pressure_curve.py` (ISSUE)
- ✓ `lennard_jones_mc_rs/results/*/plot_*.py` (multiple) - Self-contained (OK)

---

## Implementation Recommendations

### Phase 1: Fix Python Imports (BLOCKING)
**Priority**: CRITICAL - Must complete before moving files

**Files to update**: 5 Python files
- `argon_gemc_run.py`
- `benchmark_python_rust.py`
- `lennard_jones_gemc_3d.py`
- `lennard_jones_mc_3d.py`
- `lennard_jones_mc.py`

**Approach options**:
1. **Option A (Relative Imports)**: Use `from .lj_core import` and `from .gemc import`
   - Simplest, most Pythonic
   - Works if all files are in same package

2. **Option B (sys.path manipulation)**: Add `sys.path.insert(0, str(Path(__file__).parent))`
   - Less elegant but more flexible
   - Allows importing from other directories

3. **Option C (Add __init__.py)**: Create `__init__.py` in src/ directory
   - Enables proper package structure
   - Requires updating to absolute imports

**Recommendation**: Use Option A (relative imports) for simplicity.

---

### Phase 2: Update Rust Binaries (File Organization)
**Priority**: HIGH

**Files to update**: 4 binaries, 8 file paths

**Changes required**:
1. Add `use std::fs;` import at top
2. Add `std::fs::create_dir_all("results")?;` before first file write
3. Update all 8 file path strings to prepend `"results/"`

**Example change**:
```rust
// Before
let csv_path = format!("argon_gemc_density_history_N{}_C{}_cutoff_celllist_rs.csv", ...);

// After
std::fs::create_dir_all("results")?;
let csv_path = format!("results/argon_gemc_density_history_N{}_C{}_cutoff_celllist_rs.csv", ...);
```

---

### Phase 3: Update Analysis Scripts (Functionality)
**Priority**: MEDIUM

**Files to update**: 3 analysis scripts

**Changes required**:
1. Update 5 glob/path patterns to search `results/` directory
2. Update 2 output paths to save to `results/` directory
3. Handle both old and new data locations (optional, for backward compatibility)

**Example changes**:
```python
# Before
history_files = sorted(script_dir.glob("argon_vle_density_history_T*K.csv"))

# After
results_dir = script_dir.parent / "results"
history_files = sorted(results_dir.glob("argon_vle_density_history_T*K.csv"))
```

---

### Phase 4: Testing & Verification
**Priority**: MEDIUM

1. **Test Python imports**:
   - Run all Python scripts
   - Verify modules import correctly

2. **Test Rust binaries**:
   - Build all binaries
   - Run each binary
   - Verify results/ directory is created
   - Verify CSV and JSON files save to results/

3. **Test analysis scripts**:
   - Run each analysis script
   - Verify they find generated CSV files
   - Verify plots are generated and saved correctly

4. **Directory structure check**:
   - Verify no stray result files in root directory
   - Verify all results organized in results/ subdirectory

---

## Analysis Methodology

### Search Patterns Used
- **Python imports**: `grep -n "^from|^import" filename.py`
- **Python file operations**: `grep -n "open|Path|save|load" filename.py`
- **Rust file output**: `grep -n "csv_path|json_path|File::create" filename.rs`
- **Path patterns**: `grep -n "\.glob|\.parent" filename.py`

### Scope
- ✓ All Python files in lennard_jones_mc/
- ✓ All Rust binaries in lennard_jones_mc_rs/src/bin/
- ✓ All Python analysis scripts in lennard_jones_mc_rs/analysis/
- ✓ Python scripts in lennard_jones_mc_rs/results/ subdirectories

### Exclusions
- Skipped Rust library code (src/lib.rs, src/*.rs)
- Did not analyze test files
- Did not analyze configuration files (Cargo.toml, etc.)

---

## Notes

- **No changes were made** to any files during this analysis (as requested)
- All findings are documented for implementation planning
- Multiple solutions are provided for import issues to allow flexibility
- File path changes in Rust are straightforward string modifications
- Analysis scripts can be updated incrementally without breaking other code

---

**Report Generated**: 2024-03-08
**Analysis Status**: Complete - Ready for Implementation Planning
