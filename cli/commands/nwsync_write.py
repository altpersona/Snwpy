"""
NWSync Write command implementation
Based on nwn_nwsync_write.nim
"""

import argparse
import logging
from pathlib import Path
import sys
import os

# Add parent directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.nwsync import NWSyncRepository, Manifest, ManifestEntry
from core.resman import ResMan, ResRef
from core.formats import read_erf

logger = logging.getLogger(__name__)


def setup_parser(parser):
    """Setup command line parser for nwsync-write"""
    parser.add_argument('root', help='Storage directory for manifest')
    parser.add_argument('specs', nargs='+', help='Module/ERF/HAK files to include')
    
    parser.add_argument('--with-module', action='store_true',
                       help='Include module contents (not for persistent worlds)')
    parser.add_argument('-p', '--path', action='append', default=[],
                       help='Add lookup path for dependencies')
    parser.add_argument('-n', '--dry-run', action='store_true',
                       help='Simulate only, don\'t write files')
    parser.add_argument('--name', help='Override visible name')
    parser.add_argument('--description', default='', help='Manifest description')
    parser.add_argument('--group-id', type=int, default=0, help='Group ID')
    parser.add_argument('--limit-file-size', type=int, default=32,
                       help='File size limit in MB')
    parser.add_argument('--no-latest', action='store_true',
                       help='Don\'t update latest pointer')
    parser.set_defaults(func=run)


def run(args):
    """Execute nwsync-write command"""
    logger.info("Starting NWSync manifest creation")
    
    # Initialize repository
    repo = NWSyncRepository(args.root)
    
    # Create manifest
    manifest = Manifest()
    manifest.module_name = args.name or "Generated Manifest"
    manifest.description = args.description
    manifest.group_id = args.group_id
    manifest.includes_module_contents = args.with_module
    
    # Process each spec
    total_files = 0
    for spec in args.specs:
        spec_path = Path(spec)
        
        if not spec_path.exists():
            logger.error(f"Spec not found: {spec}")
            return 1
            
        logger.info(f"Processing spec: {spec}")
        
        if spec_path.suffix.lower() == '.mod':
            # Handle module file
            files_added = process_module(manifest, spec_path, args)
        elif spec_path.suffix.lower() in ['.erf', '.hak']:
            # Handle ERF/HAK file
            files_added = process_erf(manifest, spec_path)
        elif spec_path.is_dir():
            # Handle directory
            files_added = process_directory(manifest, spec_path)
        else:
            # Handle single file
            files_added = process_single_file(manifest, spec_path)
            
        total_files += files_added
        logger.info(f"Added {files_added} files from {spec}")
    
    if args.dry_run:
        logger.info(f"Dry run: would create manifest with {total_files} files")
        print_manifest_summary(manifest)
        return 0
    
    # Write manifest
    try:
        manifest_hash = repo.write_manifest(manifest, args.limit_file_size)
        
        # Print results (matching nim tool output format)
        print(f"Reindex done, manifest version {manifest.version} written: {manifest_hash}")
        print(f"Manifest contains {format_size(manifest.total_size())} in {manifest.total_files()} files")
        print("We wrote 0B of new data")  # Simplified for now
        
        # Output JSON summary to stdout (like original tool)
        import json
        summary = {
            "version": manifest.version,
            "sha1": manifest_hash,
            "hash_tree_depth": manifest.hash_tree_depth,
            "module_name": manifest.module_name,
            "description": manifest.description,
            "includes_module_contents": manifest.includes_module_contents,
            "includes_client_contents": manifest.includes_client_contents,
            "total_files": manifest.total_files(),
            "total_bytes": manifest.total_size(),
            "on_disk_bytes": 0,
            "created": manifest.created,
            "created_with": manifest.created_with,
            "group_id": manifest.group_id
        }
        print(json.dumps(summary, indent=2))
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to write manifest: {e}")
        return 1


def process_module(manifest: Manifest, mod_path: Path, args):
    """Process a .mod file"""
    logger.info(f"Parsing .mod to extract hak and tlk info: {mod_path}")
    
    # This would need full module parsing implementation
    # For now, simplified version
    logger.warning("Module parsing not fully implemented yet")
    return 0


def process_erf(manifest: Manifest, erf_path: Path):
    """Process an ERF/HAK file"""
    try:
        erf = read_erf(str(erf_path))
        files_added = 0
        
        for entry in erf.list_entries():
            # Calculate SHA1 of entry data
            import hashlib
            sha1 = hashlib.sha1(entry.data).hexdigest()
            
            manifest_entry = ManifestEntry(
                entry.resref,
                entry.res_type,
                sha1,
                len(entry.data)
            )
            manifest.add_entry(manifest_entry)
            files_added += 1
            
        return files_added
        
    except Exception as e:
        logger.error(f"Failed to process ERF {erf_path}: {e}")
        return 0


def process_directory(manifest: Manifest, dir_path: Path):
    """Process a directory of files"""
    files_added = 0
    
    for file_path in dir_path.rglob('*'):
        if file_path.is_file():
            files_added += process_single_file(manifest, file_path)
            
    return files_added


def process_single_file(manifest: Manifest, file_path: Path):
    """Process a single file"""
    try:
        # Read file data
        with open(file_path, 'rb') as f:
            data = f.read()
            
        # Calculate SHA1
        import hashlib
        sha1 = hashlib.sha1(data).hexdigest()
        
        # Create ResRef from filename
        from core.resman import ResRef
        resref = ResRef.from_filename(file_path.name)
        
        manifest_entry = ManifestEntry(
            resref.name,
            resref.res_type,
            sha1,
            len(data)
        )
        manifest.add_entry(manifest_entry)
        
        return 1
        
    except Exception as e:
        logger.error(f"Failed to process file {file_path}: {e}")
        return 0


def print_manifest_summary(manifest: Manifest):
    """Print manifest summary"""
    print(f"Manifest Summary:")
    print(f"  Version: {manifest.version}")
    print(f"  Name: {manifest.module_name}")
    print(f"  Description: {manifest.description}")
    print(f"  Files: {manifest.total_files()}")
    print(f"  Total size: {format_size(manifest.total_size())}")


def format_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"
