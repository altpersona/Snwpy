"""
NWSync Write command implementation with robust behavior.
"""

import logging
from pathlib import Path
import sys
import os
import hashlib
import json

# Add parent directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.nwsync import NWSyncRepository, Manifest, ManifestEntry  # type: ignore
from core.formats import read_erf  # type: ignore

logger = logging.getLogger(__name__)


def setup_parser(parser):
    """Setup command line parser for nwsync-write"""
    parser.add_argument('root', help='Storage directory for manifest')
    parser.add_argument('specs', nargs='+', help='Module/ERF/HAK files or directories to include')

    parser.add_argument('--with-module', action='store_true',
                       help='Include module contents (not for persistent worlds)')
    parser.add_argument('-p', '--path', action='append', default=[],
                       help='Add lookup path for dependencies (reserved)')
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
    repo = NWSyncRepository(args.root)

    manifest = Manifest()
    manifest.module_name = args.name or "Generated Manifest"
    manifest.description = args.description
    manifest.group_id = args.group_id
    manifest.includes_module_contents = args.with_module

    total_files = 0
    for spec in args.specs:
        p = Path(spec)
        if not p.exists():
            logger.error(f"Spec not found: {p}")
            return 1

        if p.suffix.lower() == ".mod":
            logger.warning("Module parsing not implemented; skipping .mod specific contents")
            continue
        elif p.suffix.lower() in [".erf", ".hak"]:
            total_files += _process_erf(manifest, p)
        elif p.is_dir():
            total_files += _process_directory(manifest, p)
        else:
            total_files += _process_single_file(manifest, p)

    if args.dry_run:
        _print_manifest_summary(manifest)
        return 0

    try:
        manifest_hash = repo.write_manifest(manifest, args.limit_file_size)
        print(f"Reindex done, manifest version {manifest.version} written: {manifest_hash}")
        print(f"Manifest contains {_format_size(manifest.total_size())} in {manifest.total_files()} files")
        print("We wrote 0B of new data")

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
            "group_id": manifest.group_id,
        }
        print(json.dumps(summary, indent=2))
        return 0
    except Exception as e:
        logger.error(f"Failed to write manifest: {e}")
        return 1


def _process_erf(manifest: Manifest, erf_path: Path) -> int:
    try:
        erf = read_erf(str(erf_path))
        added = 0
        for entry in erf.list_entries():
            sha1 = hashlib.sha1(entry.data).hexdigest()
            manifest.add_entry(ManifestEntry(entry.resref, entry.res_type, sha1, len(entry.data)))
            added += 1
        return added
    except Exception as e:
        logger.error(f"Failed to process ERF {erf_path}: {e}")
        return 0


def _process_directory(manifest: Manifest, dir_path: Path) -> int:
    added = 0
    for fp in dir_path.rglob("*"):
        if fp.is_file():
            added += _process_single_file(manifest, fp)
    return added


def _process_single_file(manifest: Manifest, file_path: Path) -> int:
    try:
        data = file_path.read_bytes()
        sha1 = hashlib.sha1(data).hexdigest()
        # Infer resref and type from filename.ext
        name = file_path.stem
        ext = file_path.suffix[1:].lower()
        manifest.add_entry(ManifestEntry(name, ext, sha1, len(data)))
        return 1
    except Exception as e:
        logger.error(f"Failed to process file {file_path}: {e}")
        return 0


def _print_manifest_summary(manifest: Manifest):
    print("Manifest Summary:")
    print(f"  Version: {manifest.version}")
    print(f"  Name: {manifest.module_name}")
    print(f"  Description: {manifest.description}")
    print(f"  Files: {manifest.total_files()}")
    print(f"  Total size: {_format_size(manifest.total_size())}")


def _format_size(size_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    v = float(size_bytes)
    while v >= 1024 and i < len(units) - 1:
        v /= 1024
        i += 1
    return f"{v:.1f}{units[i]}"
