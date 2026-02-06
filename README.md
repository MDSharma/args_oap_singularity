# ARGs_OAP - Singularity Compatible Fork

This is a fork of ARGs-OAP with **Singularity container compatibility fixes**. It addresses issues that cause the tool to fail inside Singularity containers where the file system is read-only.

**Original repository:** [xinehc/args_oap](https://github.com/xinehc/args_oap)  
**This fork:** [MDSharma/args_oap_singularity](https://github.com/MDSharma/args_oap_singularity)

## What's New in This Fork

✅ **Singularity Container Support** - Works seamlessly in read-only environments  
✅ **Fixed UnboundLocalError** - The misleading `dbtype` error is now resolved  
✅ **Database Index Caching** - Indices stored in user-writable cache directory  
✅ **Backward Compatible** - Works exactly as before in normal Conda environments  
✅ **Better Error Messages** - More helpful diagnostics when things go wrong

See [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for technical details.

---

## Installation

### Option 1: Singularity Container (Recommended for HPC/Read-only Systems)

Build the Singularity container:
```bash
sudo singularity build args_oap.sif Singularity.args_oap.def
# or with fakeroot: singularity build --fakeroot args_oap.sif Singularity.args_oap.def
```

Use the container:
```bash
singularity exec args_oap.sif args_oap stage_one -i input -o output -f fq -t 8
singularity exec args_oap.sif args_oap stage_two -i output -t 8
```

📖 **Full Singularity guide:** [SINGULARITY_USAGE.md](SINGULARITY_USAGE.md)

### Option 2: Conda (macOS/Linux)

Install from this repository:
```bash
git clone https://github.com/MDSharma/args_oap_singularity.git
cd args_oap_singularity
# Note: After PR is merged, checkout main branch or a release tag
# For now, during development: git checkout copilot/refactor-args-oap-for-singularity

# Create conda environment with dependencies
conda create -n args_oap -c bioconda -c conda-forge \
    python>=3.7 diamond>=2.0.15 bwa>=0.7.17 blast>=2.12 samtools>=1.15 pandas

conda activate args_oap
pip install .
```

Or use the original bioconda package (without Singularity fixes):
```bash
conda install -c bioconda -c conda-forge args_oap
```

### Option 3: From Source

If your OS has all dependencies (`python>=3.7`, `diamond>=2.0.15`, `bwa>=0.7.17`, `blast>=2.12`, `samtools>=1.15`):
```bash
git clone https://github.com/MDSharma/args_oap_singularity.git
cd args_oap_singularity
# Note: After PR is merged, checkout main branch or a release tag
# For now, during development: git checkout copilot/refactor-args-oap-for-singularity
python setup.py install  # use python3 if needed
```

---

## About ARGs-OAP

This repository was originally created by Xiaole Yin (_xiaole99_) and is currently maintained by Xi Chen (_xinhec_). The goal is to make args_oap faster, and easier to run. 

If you have questions about the original ARGs-OAP, please create an [issue](https://github.com/xinehc/args_oap/issues/new/choose), or contact Xiaole Yin ([yinlele99@gmail.com](yinlele99@gmail.com)).

**For Singularity-specific issues**, please use [this repository's issue tracker](https://github.com/MDSharma/args_oap_singularity/issues).

More about the SARG database: [https://smile.hku.hk/ARGs/Indexing](https://smile.hku.hk/ARGs/Indexing), and the change logs: [CHANGELOG.md](https://github.com/xinehc/args_oap/blob/main/CHANGELOG.md).

---

## Example
Two example fasta files (100k paired-end reads, 100 bp each) can be found [here](https://dl.dropboxusercontent.com/s/pqgftlo24rfc2rd/example.tar.gz). The zipped file can be downloaded manually or using `wget`:

```bash
# conda install wget
wget https://dl.dropboxusercontent.com/s/pqgftlo24rfc2rd/example.tar.gz
tar -xvf example.tar.gz
cd example

# conda activate args_oap
args_oap stage_one -i input -o output -f fa -t 8
args_oap stage_two -i output -t 8
```

After `stage_one`, a `metadata.txt` file can be found in `output`. It summarizes the estimated 16S and cell copy numbers in each sample, for example:

| sample   | nRead  | n16S              | nCell              |
|----------|--------|-------------------|--------------------|
| STAS     | 200000 | 8.229297879794053 | 3.1472376316269055 |
| SWHAS104 | 200000 | 7.009547807125172 | 3.487830355315917  |

After `stage_two`, the normalized ARGs copies per 16S/cells or hits per million reads will be shown in several `*_normalized_*.txt` files. 
For example, `normalized_cell.type` means:
+ `normalized_cell` - normalized against cell number
+ `type` - type of ARGs (the hierarchy in the SARG database is type -> subtype -> gene)

| type                                | STAS                 | SWHAS104             |
|-------------------------------------|----------------------|----------------------|
| aminoglycoside                      | 0.04236519416057223  | 0.1411521328969608   |
| bacitracin                          | 0.03724412673456899  | 0.07331127852930945  |
| beta_lactam                         | 0.0                  | 0.14920548807040623  |
| macrolide-lincosamide-streptogramin | 0.0                  | 0.02404226144950743  |
| multidrug                           | 0.012948920209830746 | 0.19382414709324317  |
| mupirocin                           | 0.007757298735456341 | 0.009159215245515702 |
| quinolone                           | 0.37832158835366747  | 0.08842494718334318  |
| sulfonamide                         | 0.035174054192357015 | 0.1368367904789564   |
| tetracycline                        | 0.012183242185747383 | 0.09987284037027115  |

Output file `extracted.filtered.fa` contains all filtered ARG-like sequences after `stage_two`. `blastout.filtered.txt` is the metadata of these sequences.

## Database Cache (New in This Fork)

This fork introduces automatic database index caching to support read-only environments like Singularity containers.

**How it works:**
- On first run, database indices (`.pdb`, `.ndb`, `.dmnd`) are created
- In writable environments (Conda): indices stored next to FASTA files (backward compatible)
- In read-only environments (Singularity): indices stored in `~/.args_oap/db_cache/`

**Custom cache location:**
```bash
# Set custom cache directory
export ARGS_OAP_CACHE=/path/to/custom/cache

# Then run normally
args_oap stage_one -i input -o output -f fq -t 8
```

**For Singularity users:**
```bash
# Use custom cache location
singularity exec --env ARGS_OAP_CACHE=/scratch/cache args_oap.sif args_oap stage_one -i input -o output

# Or bind your cache directory
singularity exec --bind $HOME/.args_oap:/root/.args_oap args_oap.sif args_oap stage_one -i input -o output
```

See [SINGULARITY_COMPAT.md](SINGULARITY_COMPAT.md) for more details.

### De-contamination: 
Before running ARGs-OAP, a de-contamination processes is recommended to secure clean prokaryotic reads. This includes the removal of genomic sequences from hosts (e.g., human), and from fungal sources. This step is critical to avoid potential biases in the calculation of cell numbers which relies on the identification of essential single copy marker genes.


## Notes
### (optional) Single/Paired end files
If you use paired-end files, please make sure the forward/reverse reads end with `_1|_2`, `_R1|_R2` or `_fwd|_rev` (followed by `.format`, see -f, `.gz` optional), otherwise they will not be considered as a single sample. Example for fasta format files (`-f fa`):
```
STAS
   ├── STAS_1.fa
   └── STAS_2.fa.gz
SWHAS104
   ├── SWHAS104_R1.fa
   └── SWHAS104_R2.fa.gz
```   

### (optional) Customized database/structures
To use customized databases (e.g. mobile genetic elements or heave metal resistant genes), you need to prepare two files:
1. nucleotide sequences or amino acid (protein) sequences database (e.g. `database.fasta`)
2. hierarchical structure file (e.g. `structure.txt`)

The database should be indexed manually (protein or nucleotide, in fasta):
```bash
## protein or nucleotide
args_oap make_db -i database.fasta
```

The structure file `structure.txt` should be tab-separated and the first column the sequences ID of `database.fasta` (**please note that the sequence ID cannot contain space, tab and other irregular char such as forward slash**). At lease one column (level 1) is required. For the one column (level 1) case, you may construct the structure file using:
```bash
echo '>level1' | cat - database.fasta | grep '^>' | cut -d ' ' -f 1 | cut -c2- > structure.txt
```

One example of the `database.fasta` and `structure.txt` is :

```
database.fasta:

    >seq1
    ACGT...
    >seq2
    TGCA...

structure.txt:

    level1    level2    level3
    seq1    subtype1    type1
    seq2    subtype2    type2
```

To run args_oap with customized database:
```bash
args_oap stage_one -i input -o output -f fa -t 8 --database database.fasta
args_oap stage_two -i output -t 8 --database database.fasta --structure1 structure.txt
```

### (optional) Stage two pipeline on Galaxy system and download results
(**The online version currently does not support SARG v3.0, please use the local version at this moment.**)

Go to http://smile.hku.hk/SARGs  and using the module ARG_OAP.    
  
1. Using **ARG_OAP** -> **Upload Files** module to upload the extracted fasta file and meta_data_online.txt file generated in stage one into Galaxy
2. Click **ARG_OAP** and **Ublast_stagetwo**, select your uploaded files    
3. For \"Column in Metadata:\" chose the column you want to classify your samples (default: 3)  
  
Click **Execute** and you can find four output files for your information  
  
After a while or so, you will notice that their are four files generated for your information.    
   
**File 1 and 2**: PcoA figures of your samples and other environment samples generated by ARGs abundance matrix normalization to 16S reads number and cell number    
**File 3 and 4**: Other tabular mother tables which including the profile of ARGs type and sub type information, as long as with other environment samples mother table. File3 results of ARGs abundance normalization against 16S reads number; File 4 results of ARGs abundance normalization against cell number  
  
There are some questions raised by users, please refer to the [FAQ](https://github.com/biofuture/Ublastx_stageone/wiki/FAQ) for details. To run ARG OAP locally, users should download the source code into local computer system (Unix/Linux). Users can upload the generated files for stage two onto our Galaxy analysis platform (http://smile.hku.hk/SARGs) or use the local version of stage two script.

---
**Notice:**  
  
This tools only provide the required scripts for ARGs-OAP 3.0 pipeline

This pipeline is distributed in the hope to achieve the aim of management of antibiotic resistant genes in environment, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.This pipeline is only allowed to be used for non-commercial and academic purpose.

**The SARG database is distributed only freely used for academic purpose, any commercial use should require the agreement from the developer team.**
