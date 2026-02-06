# Singularity Container Compatibility Changes

## Summary

This document describes the changes made to make ARGs-OAP work properly in Singularity containers and other read-only environments.

## Problem

When running `args_oap stage_one` inside a Singularity container (SIF file), the program would fail early with misleading errors such as:
```
UnboundLocalError: local variable 'dbtype' referenced before assignment
```

The actual root cause was that ARGs-OAP tried to write database index files (`.pdb`, `.ndb`, `.dmnd`) to the `site-packages/args_oap/db/` directory, which is read-only inside a Singularity container.

## Solution

### 1. Database Index Caching

Database indices are now stored in a user-writable cache directory instead of alongside the FASTA files in site-packages.

**Default cache location:** `~/.args_oap/db_cache/`
**Override via environment variable:** `ARGS_OAP_CACHE`

The code automatically detects whether the database directory is writable:
- **Writable (Conda environment):** Indices are stored next to FASTA files as before
- **Read-only (Singularity container):** Indices are stored in the cache directory

### 2. Fixed UnboundLocalError in make_db.py

The `dbtype` variable is now properly initialized to `None` before the try/except blocks, preventing the UnboundLocalError when both diamond and bwa fail.

### 3. Updated Database References

All code that references database indices now uses the new `get_db_index_path()` method which automatically determines the correct location.

## Files Modified

1. **src/args_oap/settings.py**
   - Added `get_db_cache_dir()` function to get/create cache directory
   - Added `db_cache` field to `Setting` dataclass
   - Added `get_db_index_path()` method to determine database index locations
   - Added `__post_init__()` to initialize cache directory

2. **src/args_oap/make_db.py**
   - Fixed `dbtype` UnboundLocalError by initializing to `None`
   - Added `output_base` parameter to control where indices are written
   - Auto-detects read-only directories and uses cache instead
   - Returns `dbtype` for downstream use

3. **src/args_oap/stage_one.py**
   - Updated database index checking to look in both original and cache locations
   - Updated `count_16s()` to use cache-aware database paths
   - Updated `count_cells()` to use cache-aware database paths
   - Updated `extract_seqs()` to use cache-aware database paths
   - Stores `self.db_index` for the actual index location

4. **src/args_oap/stage_two.py**
   - Updated database index checking to look in both original and cache locations
   - Updated `extract_seqs()` to use cache-aware database paths
   - Stores `self.db_index` for the actual index location

## Usage

### Standard Usage (No Changes Required)

For most users, no changes are needed. The code works transparently in both environments:

```bash
# In a Conda environment (writable)
args_oap stage_one -i input -o output -f fq -t 8
args_oap stage_two -i output -t 8

# In a Singularity container (read-only)
singularity exec args_oap.sif args_oap stage_one -i input -o output -f fq -t 8
singularity exec args_oap.sif args_oap stage_two -i output -t 8
```

### Custom Cache Location

To use a custom cache directory (e.g., for shared filesystem or specific mount points):

```bash
# Set environment variable
export ARGS_OAP_CACHE=/path/to/cache

# Or in Singularity
singularity exec --env ARGS_OAP_CACHE=/path/to/cache args_oap.sif args_oap stage_one ...
```

### Pre-building Database Indices

For better performance in shared Singularity environments, you can pre-build the indices once:

```bash
# On first run or in a writable environment
export ARGS_OAP_CACHE=/shared/cache/args_oap
args_oap stage_one -i input -o output -f fq -t 8

# Subsequent runs will use the cached indices
```

## Testing

The changes were validated with unit tests covering:
1. Cache directory creation and permissions
2. Database index path selection (writable vs read-only)
3. UnboundLocalError fix in make_db
4. Proper handling of environment variables

All tests pass successfully.

## Backward Compatibility

These changes are fully backward compatible:
- Existing Conda installations continue to work as before
- Database indices in writable locations are used as before
- No changes to command-line interface or user workflows
- Works with custom databases via `--database` flag

## Notes for Singularity Container Builds

When building Singularity containers, consider:

1. **Mount the cache directory** for better performance across runs:
   ```bash
   singularity exec --bind $HOME/.args_oap:/home/user/.args_oap args_oap.sif ...
   ```

2. **Pre-built indices** can be included in the container build if desired, though not required.

3. **Environment variable** can be set in the container definition file:
   ```
   %environment
       export ARGS_OAP_CACHE=/opt/args_oap_cache
   ```
