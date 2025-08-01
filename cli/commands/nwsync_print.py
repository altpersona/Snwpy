"""
NWSync Print command implementation
Based on nwn_nwsync_print.nim
"""

import argparse
import logging
from pathlib import Path
import sys
import os

# Add parent directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.nwsync import read_manifest

logger = logging.getLogger(__name__)


def setup_parser(parser):
    """Setup command line parser for nwsync-print"""
    parser.add_argument('manifest', help='Manifest file to print')
    parser.add_argument('--verify', action='store_true',
                       help='Verify presence and checksum of files')
    parser.set_defaults(func=run)


def run(args):
    """Execute nwsync-print command"""
    manifest_path = Path(args.manifest)
    
    if not manifest_path.exists():
        logger.error(f"Manifest not found: {manifest_path}")
        return 1
    
    try:
        # Read manifest
        manifest = read_manifest(str(manifest_path))
        
        # Print header information
        print("--")
        print(f"Version:          {manifest.version}")
        print(f"Hash algorithm:   SHA1")  # Fixed for now
        print(f"Hash tree depth:  {manifest.hash_tree_depth}")
        print(f"Entries:          {len(manifest.entries)}")
        print(f"Size:             {format_size(manifest.total_size())}")
        print("--")
        print("")
        
        # Print each entry
        for entry in manifest.entries:
            resref_full = f"{entry.resref}.{entry.res_type}"
            size_str = format_size(entry.size)
            
            print(f"{resref_full:<32} {entry.sha1} {size_str:>10}")
            
            if args.verify:
                # This would implement actual verification
                # For now, just indicate verification status
                print(f"  [VERIFY] File verification not yet implemented")
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to read manifest: {e}")
        return 1


def format_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"
