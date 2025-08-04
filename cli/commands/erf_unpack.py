"""
ERF Unpack command implementation
"""

import os
import sys
from pathlib import Path
import logging

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.formats.erf import read_erf

logger = logging.getLogger(__name__)

# Reverse lookup for resource types
RESOURCE_EXTENSIONS = {
    1: 'bmp', 3: 'tga', 4: 'wav', 6: 'plt', 7: 'ini', 10: 'txt',
    2002: 'mdl', 2009: 'nss', 2010: 'ncs', 2012: 'are', 2013: 'set',
    2014: 'ifo', 2015: 'bic', 2016: 'wok', 2017: 'utc', 2018: 'utd',
    2019: 'ute', 2020: 'utg', 2021: 'uti', 2022: 'utm', 2023: 'utp',
    2024: 'uts', 2025: 'utt', 2026: 'utw', 2027: 'git', 2028: 'gic',
    2029: 'dlg', 2030: 'itp', 2031: 'bak', 2032: 'dat', 2033: 'shd',
    2034: 'xbc', 2035: 'wbm', 2036: 'mtr', 2037: 'gff', 2038: 'fac',
    2040: 'ktx', 2041: 'ttf', 2042: 'sql', 2043: 'tml', 2044: 'sq3',
    2045: 'lod', 2046: 'gif', 2047: 'png', 2048: 'jpg', 2049: 'caf',
    9996: 'jui', 9997: 'gui', 9998: 'css', 9999: 'ccs', 10000: 'xml',
    10001: 'htm', 10002: 'ltr', 10003: 'gff', 10004: 'json'
}


def get_extension(res_type: int) -> str:
    """Get file extension from resource type"""
    return RESOURCE_EXTENSIONS.get(res_type, f'res{res_type}')


def erf_unpack(args):
    """Unpack ERF file to directory"""
    input_erf = Path(args.input_erf)
    output_dir = Path(args.output_dir)
    
    if not input_erf.exists():
        logger.error(f"ERF file does not exist: {input_erf}")
        return 1
    
    try:
        # Read ERF file
        erf = read_erf(str(input_erf))
        logger.info(f"Read ERF with {len(erf)} entries")
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract all entries
        extracted_count = 0
        for entry in erf.list_entries():
            extension = get_extension(entry.res_type)
            # Sanitize resref - remove null characters and limit length
            clean_resref = entry.resref.replace('\x00', '').strip()
            if not clean_resref:
                clean_resref = f"entry_{extracted_count}"
            filename = f"{clean_resref}.{extension}"
            output_path = output_dir / filename
            
            try:
                with open(output_path, 'wb') as f:
                    f.write(entry.data)
                    
                extracted_count += 1
                logger.debug(f"Extracted: {filename} ({len(entry.data)} bytes)")
                
            except Exception as e:
                logger.error(f"Failed to extract {filename}: {e}")
                return 1
        
        logger.info(f"Extracted {extracted_count} files to: {output_dir}")
        return 0
        
    except Exception as e:
        logger.error(f"Failed to read ERF file: {e}")
        return 1


def setup_parser(parser):
    """Set up argument parser for erf-unpack command"""
    parser.add_argument('input_erf', help='Input ERF file')
    parser.add_argument('output_dir', help='Output directory')
    parser.add_argument('--list-only', action='store_true',
                       help='List contents without extracting')
    parser.set_defaults(func=erf_unpack)
    return parser
