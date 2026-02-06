import os
import re
import logging
from pathlib import Path

from dataclasses import dataclass

## setup logger
logging.basicConfig(
    level="INFO",
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S")

## bold format
BOLD = "\033[1m"
RESET = "\033[0m"

## add color
logging.addLevelName(
    logging.WARNING,
    BOLD + "\x1b[33;20m%s\033[1;0m" % logging.getLevelName(logging.WARNING))

logging.addLevelName(
    logging.CRITICAL,
    BOLD + "\x1b[31;20m%s\033[1;0m" % logging.getLevelName(logging.CRITICAL))

logger = logging.getLogger(__name__)


## setup file format
@dataclass
class File:
    file: str
    outdir: str
    format: str

    @property
    def file_name(self) -> str:
        return re.sub(rf'\.{self.format}(.gz)?$', '', os.path.basename(self.file))

    @property
    def sample_name(self) -> str:
        return re.sub(r'(_R1|_R2|_1|_2|_fwd|_rev)$', '', self.file_name)

    @property
    def tmp_16s_fa(self) -> str:
        return os.path.join(self.outdir, self.file_name + '.16s.fa.tmp')

    @property
    def tmp_16s_txt(self) -> str:
        return os.path.join(self.outdir, self.file_name + '.16s.txt.tmp')

    @property
    def tmp_16s_sam(self) -> str:
        return os.path.join(self.outdir, self.file_name + '.16s.sam.tmp')

    @property
    def tmp_cells_txt(self) -> str:
        return os.path.join(self.outdir, self.file_name + '.cells.txt.tmp')

    @property
    def tmp_seqs_fa(self) -> str:
        return os.path.join(self.outdir, self.file_name + '.seqs.fa.tmp')

    @property
    def tmp_seqs_txt(self) -> str:
        return os.path.join(self.outdir, self.file_name + '.seqs.txt.tmp')

    @property
    def tmp_seqs_sam(self) -> str:
        return os.path.join(self.outdir, self.file_name + '.seqs.sam.tmp')


## setup database cache directory
def get_db_cache_dir() -> str:
    """
    Get or create a writable directory for database indices.
    Uses ~/.args_oap/db_cache/ by default, or ARGS_OAP_CACHE env variable.
    """
    cache_dir = os.environ.get('ARGS_OAP_CACHE')
    if cache_dir is None:
        cache_dir = os.path.join(Path.home(), '.args_oap', 'db_cache')
    
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


## setup database
@dataclass
class Setting:
    indir: str
    outdir: str
    db: str = os.path.join(os.path.dirname(__file__), 'db')
    db_cache: str = None
    
    def __post_init__(self):
        """Initialize db_cache after instance creation."""
        if self.db_cache is None:
            self.db_cache = get_db_cache_dir()

    @property
    def sarg(self) -> str:
        return os.path.join(self.db, 'sarg.fasta')

    @property
    def sarg_structure1(self) -> str:
        return os.path.join(self.db, 'single-component_structure.txt')

    @property
    def sarg_structure2(self) -> str:
        return os.path.join(self.db, 'two-component_structure.txt')

    @property
    def sarg_structure3(self) -> str:
        return os.path.join(self.db, 'multi-component_structure.txt')

    @property
    def gg85(self) -> str:
        return os.path.join(self.db, 'gg85.fasta')

    @property
    def ko30(self) -> str:
        return os.path.join(self.db, 'ko30.fasta')

    @property
    def ko30_structure(self) -> str:
        return os.path.join(self.db, 'ko30_structure.txt')
    
    def get_db_index_path(self, db_fasta: str) -> str:
        """
        Get the path where database indices should be stored.
        Uses cache directory for read-only environments, or same dir if writable.
        
        Args:
            db_fasta: Path to the database FASTA file
            
        Returns:
            Base path for database indices (without extension)
        """
        db_dir = os.path.dirname(db_fasta)
        db_basename = os.path.basename(db_fasta)
        
        # Check if the database directory is writable
        if os.access(db_dir, os.W_OK):
            # If writable, use the same directory as the FASTA file
            return db_fasta
        else:
            # If not writable (e.g., in Singularity container), use cache directory
            return os.path.join(self.db_cache, db_basename)
    
    def db_index_exists(self, db_fasta: str) -> tuple:
        """
        Check if database indices exist for a given FASTA file.
        Checks both the original location and cache location.
        
        Args:
            db_fasta: Path to the database FASTA file
            
        Returns:
            tuple: (exists: bool, dbtype: str or None, index_path: str or None)
                   - exists: True if indices found
                   - dbtype: 'prot' or 'nucl' if found, None otherwise
                   - index_path: Path to the indices if found, None otherwise
        """
        index_base = self.get_db_index_path(db_fasta)
        
        # Check for protein database
        if os.path.isfile(f'{index_base}.pdb') or os.path.isfile(f'{db_fasta}.pdb'):
            found_path = index_base if os.path.isfile(f'{index_base}.pdb') else db_fasta
            return (True, 'prot', found_path)
        
        # Check for nucleotide database
        if os.path.isfile(f'{index_base}.ndb') or os.path.isfile(f'{db_fasta}.ndb'):
            found_path = index_base if os.path.isfile(f'{index_base}.ndb') else db_fasta
            return (True, 'nucl', found_path)
        
        return (False, None, None)

    @property
    def extracted(self) -> str:
        if self.indir is None:
            return os.path.join(self.outdir, 'extracted.fa')
        else:
            return os.path.join(self.indir, 'extracted.fa')

    @property
    def metadata(self) -> str:
        if self.indir is None:
            return os.path.join(self.outdir, 'metadata.txt')
        else:
            return os.path.join(self.indir, 'metadata.txt')

    @property
    def blastout(self) -> str:
        return os.path.join(self.outdir, 'blastout.txt')

    @property
    def blastout_filtered(self) -> str:
        return os.path.join(self.outdir, 'blastout.filtered.txt')

    @property
    def extracted_filtered(self) -> str:
        return os.path.join(self.outdir, 'extracted.filtered.fa')

    @property
    def columns(self) -> list:
        return ['qseqid', 'sseqid', 'pident', 'length', 'qlen', 'slen', 'evalue', 'bitscore']
