import os
import subprocess
import sys

from .settings import logger, get_db_cache_dir


def make_db(file, output_base=None):
    '''
    Make database, also determine the type.
    
    Args:
        file: Input FASTA file path
        output_base: Base path for output indices (without extension).
                    If None, determined automatically based on write permissions.
    
    Returns:
        dbtype: 'prot' or 'nucl' based on successful database creation
    '''
    if not os.path.isfile(file):
        logger.critical(f'File <{file}> cannot be found. Please check input file (-i/--infile).')
        sys.exit(2)

    logger.info(f'Building database of <{file}> ...')
    
    # Determine output location if not specified
    if output_base is None:
        db_dir = os.path.dirname(file)
        if os.access(db_dir, os.W_OK):
            # If writable, use the same directory as the FASTA file
            output_base = file
        else:
            # If not writable (e.g., in Singularity container), use cache directory
            cache_dir = get_db_cache_dir()
            output_base = os.path.join(cache_dir, os.path.basename(file))
            logger.info(f'Database directory is read-only, using cache directory: {cache_dir}')
    
    dbtype = None  # Initialize to avoid UnboundLocalError

    ## try making db using diamond, if fail use bwa
    try:
        subprocess.run([
            'diamond', 'makedb',
            '--in', file,
            '--db', output_base,
            '--quiet'], check=True, stderr=subprocess.DEVNULL)
        dbtype = 'prot'

    except subprocess.CalledProcessError:
        try:
            # Use -p flag only when output_base differs from input file
            if output_base != file:
                subprocess.run([
                    'bwa', 'index',
                    '-p', output_base,
                    file], check=True, stderr=subprocess.DEVNULL)
            else:
                subprocess.run([
                    'bwa', 'index',
                    file], check=True, stderr=subprocess.DEVNULL)
            dbtype = 'nucl'

        except subprocess.CalledProcessError:
            pass

    ## if both diamond and bwa failed, dbtype will be None
    if dbtype is None:
        logger.critical(f'Cannot build database of <{file}> using diamond or bwa. Please verify the file format and ensure diamond/bwa are installed and accessible.')
        sys.exit(2)

    ## if makeblastdb fail then stop
    try:
        subprocess.run([
            'makeblastdb',
            '-in', file,
            '-dbtype', dbtype,
            '-out', output_base], check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

    except subprocess.CalledProcessError:
        logger.critical(f'Failed to create BLAST database indices for <{file}>. Please verify the file format.')
        sys.exit(2)

    logger.info('Finished.')
    return dbtype


def run_make_db(options):
    make_db(vars(options).get('infile'))
