"""
ERF Pack command implementation
"""

import os
import sys
from pathlib import Path
import logging

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.formats.erf import Erf, ErfEntry, write_erf, RESOURCE_TYPES

logger = logging.getLogger(__name__)


def get_resource_type(file_extension: str) -> int:
    """Get resource type ID from file extension"""
    ext = file_extension.lower().lstrip('.')
    return RESOURCE_TYPES.get(ext, 2037)  # Default to GFF


def erf_pack(args):
    """Pack directory contents into ERF file"""
    input_dir = Path(args.input_dir)
    output_erf = Path(args.output_erf)
    
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return 1
        
    if not input_dir.is_dir():
        logger.error(f"Input path is not a directory: {input_dir}")
        return 1
    
    # Create ERF container
    erf = Erf("ERF")
    
    # Add all files from input directory
    file_count = 0
    for file_path in input_dir.rglob('*'):
        if file_path.is_file():
            # Calculate relative path
            rel_path = file_path.relative_to(input_dir)
            
            # Get resref (filename without extension)
            resref = file_path.stem
            if len(resref) > 16:
                logger.warning(f"Truncating resref '{resref}' to 16 characters")
                resref = resref[:16]
            
            # Get resource type from extension
            res_type = get_resource_type(file_path.suffix)
            
            # Read file data
            try:
                with open(file_path, 'rb') as f:
                    data = f.read()
                    
                entry = ErfEntry(resref, res_type, data)
                erf.add_entry(entry)
                file_count += 1
                
                logger.debug(f"Added: {resref}.{res_type} ({len(data)} bytes)")
                
            except Exception as e:
                logger.error(f"Failed to read {file_path}: {e}")
                return 1
    
    # Write ERF file
    try:
        output_erf.parent.mkdir(parents=True, exist_ok=True)
        write_erf(erf, str(output_erf))
        logger.info(f"Created ERF with {file_count} files: {output_erf}")
        return 0
        
    except Exception as e:
        logger.error(f"Failed to write ERF file: {e}")
        return 1


def setup_parser(parser):
    """Set up argument parser for erf-pack command"""
    parser.add_argument('input_dir', help='Input directory')
    parser.add_argument('output_erf', help='Output ERF file')
    parser.add_argument('--type', choices=['ERF', 'HAK', 'MOD'], default='ERF',
                       help='ERF file type')
    parser.set_defaults(func=erf_pack)
    return parser
