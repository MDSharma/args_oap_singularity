# Building and Using ARGs-OAP Singularity Container

This guide shows how to build and use the Singularity container for ARGs-OAP with the compatibility fixes for read-only environments.

## Prerequisites

- Singularity/Apptainer installed (version 3.0 or higher)
- Root/sudo access for building (or use `--fakeroot`)
- At least 4 GB of free disk space

## Building the Container

### Option 1: Build with sudo (recommended)

```bash
sudo singularity build args_oap.sif Singularity.args_oap.def
```

### Option 2: Build with fakeroot (no sudo required)

```bash
singularity build --fakeroot args_oap.sif Singularity.args_oap.def
```

### Option 3: Build remotely (requires Sylabs account)

```bash
singularity build --remote args_oap.sif Singularity.args_oap.def
```

## Using the Container

### Basic Usage

**Stage One:**
```bash
singularity exec args_oap.sif args_oap stage_one \
    -i input_folder \
    -o output_folder \
    -f fq \
    -t 8
```

**Stage Two:**
```bash
singularity exec args_oap.sif args_oap stage_two \
    -i output_folder \
    -t 8
```

### Running as a Command

You can also run the container directly (uses the runscript):
```bash
./args_oap.sif stage_one -i input -o output -f fq -t 8
./args_oap.sif stage_two -i output -t 8
```

## Database Cache Management

The container stores database indices in a writable cache directory to avoid write errors.

### Default Cache Location

By default, indices are stored in `~/.args_oap/db_cache/` on the host system.

### Custom Cache Location

**Option 1: Environment variable**
```bash
singularity exec \
    --env ARGS_OAP_CACHE=/path/to/custom/cache \
    args_oap.sif args_oap stage_one -i input -o output
```

**Option 2: Bind mount with environment variable**
```bash
# For shared/persistent cache across runs
export ARGS_OAP_CACHE=/shared/cache/args_oap
mkdir -p $ARGS_OAP_CACHE

singularity exec \
    --bind $ARGS_OAP_CACHE:$ARGS_OAP_CACHE \
    --env ARGS_OAP_CACHE=$ARGS_OAP_CACHE \
    args_oap.sif args_oap stage_one -i input -o output
```

### Pre-building Database Indices

For better performance, you can pre-build indices once:

```bash
# Set cache location
export ARGS_OAP_CACHE=/shared/cache/args_oap
mkdir -p $ARGS_OAP_CACHE

# First run builds the indices
singularity exec \
    --bind $ARGS_OAP_CACHE:$ARGS_OAP_CACHE \
    --env ARGS_OAP_CACHE=$ARGS_OAP_CACHE \
    args_oap.sif args_oap stage_one -i input -o output -f fq -t 8

# Subsequent runs reuse the cached indices (faster)
singularity exec \
    --bind $ARGS_OAP_CACHE:$ARGS_OAP_CACHE \
    --env ARGS_OAP_CACHE=$ARGS_OAP_CACHE \
    args_oap.sif args_oap stage_one -i input2 -o output2 -f fq -t 8
```

## Binding Directories

Singularity automatically binds your home directory and current working directory. For data in other locations:

```bash
singularity exec \
    --bind /scratch/data:/data \
    --bind /scratch/results:/results \
    args_oap.sif args_oap stage_one -i /data -o /results -f fq -t 8
```

## Using on HPC Systems

### SLURM Example

```bash
#!/bin/bash
#SBATCH --job-name=args_oap
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=24:00:00

# Set cache directory (use scratch or shared filesystem)
export ARGS_OAP_CACHE=/scratch/$USER/args_oap_cache
mkdir -p $ARGS_OAP_CACHE

# Run stage one
singularity exec \
    --bind $ARGS_OAP_CACHE:$ARGS_OAP_CACHE \
    --env ARGS_OAP_CACHE=$ARGS_OAP_CACHE \
    /path/to/args_oap.sif args_oap stage_one \
    -i $INPUT_DIR \
    -o $OUTPUT_DIR \
    -f fq \
    -t 16

# Run stage two
singularity exec \
    --bind $ARGS_OAP_CACHE:$ARGS_OAP_CACHE \
    --env ARGS_OAP_CACHE=$ARGS_OAP_CACHE \
    /path/to/args_oap.sif args_oap stage_two \
    -i $OUTPUT_DIR \
    -t 16
```

### PBS Example

```bash
#!/bin/bash
#PBS -N args_oap
#PBS -l nodes=1:ppn=16
#PBS -l mem=32gb
#PBS -l walltime=24:00:00

cd $PBS_O_WORKDIR

export ARGS_OAP_CACHE=/scratch/$USER/args_oap_cache
mkdir -p $ARGS_OAP_CACHE

singularity exec \
    --bind $ARGS_OAP_CACHE:$ARGS_OAP_CACHE \
    --env ARGS_OAP_CACHE=$ARGS_OAP_CACHE \
    /path/to/args_oap.sif args_oap stage_one \
    -i input -o output -f fq -t 16
```

## Verifying the Installation

Test the container:

```bash
# Check version
singularity exec args_oap.sif args_oap --version

# Run container tests
singularity test args_oap.sif

# Check that cache directory works
singularity exec args_oap.sif python3 -c "
from args_oap.settings import get_db_cache_dir
print('Cache directory:', get_db_cache_dir())
"
```

## Troubleshooting

### Issue: "Permission denied" when writing

**Solution:** The container uses a cache directory. Ensure it's writable:
```bash
mkdir -p ~/.args_oap/db_cache
chmod 755 ~/.args_oap/db_cache
```

### Issue: Database indices not found

**Solution:** On first run, indices are built automatically. This takes a few minutes. To check cache location:
```bash
singularity exec args_oap.sif python3 -c "
from args_oap.settings import get_db_cache_dir
import os
cache = get_db_cache_dir()
print('Cache directory:', cache)
print('Contents:', os.listdir(cache) if os.path.exists(cache) else 'empty')
"
```

### Issue: Container build fails

**Solution:** Ensure you have enough disk space and a good internet connection. Try building with `--fakeroot` if you don't have sudo access.

### Issue: Slow performance on shared filesystem

**Solution:** Use a local scratch directory for cache:
```bash
export ARGS_OAP_CACHE=/tmp/args_oap_cache_$USER
mkdir -p $ARGS_OAP_CACHE
# Then run with --env ARGS_OAP_CACHE=$ARGS_OAP_CACHE
```

## Advanced Usage

### Using Custom Databases

```bash
# Index your custom database first
singularity exec args_oap.sif args_oap make_db -i /path/to/custom_db.fasta

# Use it in stage_one
singularity exec args_oap.sif args_oap stage_one \
    -i input -o output -f fq -t 8 \
    --database /path/to/custom_db.fasta
```

### Parallel Processing Multiple Samples

```bash
#!/bin/bash
# Process multiple samples in parallel using GNU parallel

export ARGS_OAP_CACHE=/shared/cache/args_oap
mkdir -p $ARGS_OAP_CACHE

find input_samples -type d -maxdepth 1 -mindepth 1 | parallel -j 4 \
    'singularity exec \
        --bind $ARGS_OAP_CACHE:$ARGS_OAP_CACHE \
        --env ARGS_OAP_CACHE=$ARGS_OAP_CACHE \
        args_oap.sif args_oap stage_one \
        -i {} -o output/{/} -f fq -t 4'
```

## Performance Tips

1. **Use local scratch for cache** on HPC systems instead of network filesystems
2. **Pre-build indices** once and reuse across all jobs
3. **Adjust thread count** (`-t`) based on available CPUs
4. **Bind only necessary directories** to reduce overhead
5. **Use SSD storage** for cache directory when possible

## Getting Help

- Container-specific issues: https://github.com/MDSharma/args_oap_singularity/issues
- ARGs-OAP general questions: https://github.com/xinehc/args_oap/issues
- Singularity documentation: https://sylabs.io/docs/

## References

- ARGs-OAP: https://github.com/xinehc/args_oap
- Singularity: https://sylabs.io/singularity/
- SARG Database: https://smile.hku.hk/ARGs/Indexing
