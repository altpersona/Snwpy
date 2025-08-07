"""
NWSync Print command implementation with optional verification.
"""

import logging
from pathlib import Path
import sys
import os
import hashlib

# Add parent directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.nwsync import read_manifest  # type: ignore

logger = logging.getLogger(__name__)


def setup_parser(parser):
    """Setup command line parser for nwsync-print"""
    parser.add_argument('manifest', help='Manifest file to print')
    parser.add_argument('--verify', action='store_true',
                       help='Verify presence and checksum of files (best-effort)')
    parser.add_argument('-r', '--root', help='Repository root for verification lookups')
    parser.set_defaults(func=run)


def run(args):
    """Execute nwsync-print command"""
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        logger.error(f"Manifest not found: {manifest_path}")
        return 1

    try:
        manifest = read_manifest(str(manifest_path))

        print("--")
        print(f"Version:          {manifest.version}")
        print(f"Hash algorithm:   SHA1")
        print(f"Hash tree depth:  {manifest.hash_tree_depth}")
        print(f"Entries:          {len(manifest.entries)}")
        print(f"Size:             {format_size(manifest.total_size())}")
        print("--\n")

        repo_root = Path(args.root) if args.root else None
        verified_ok = 0
        verified_fail = 0

        for entry in manifest.entries:
            resref_full = f"{entry.resref}.{entry.res_type}"
            size_str = format_size(entry.size)
            print(f"{resref_full:<32} {entry.sha1} {size_str:>10}")

            if args.verify and repo_root:
                # Best-effort verification: attempt to find by sha1 path
                # This assumes a content-addressed layout. Adjust if your repo differs.
                data_path = repo_root / "data" / entry.sha1[:2] / entry.sha1
                if data_path.exists():
                    try:
                        data = data_path.read_bytes()
                        sha1 = hashlib.sha1(data).hexdigest()
                        if sha1 == entry.sha1 and len(data) == entry.size:
                            print("  [OK]")
                            verified_ok += 1
                        else:
                            print("  [MISMATCH]")
                            verified_fail += 1
                    except Exception:
                        print("  [ERROR]")
                        verified_fail += 1
                else:
                    print("  [MISSING]")
                    verified_fail += 1

        if args.verify and repo_root:
            print(f"\nVerification: {verified_ok} ok, {verified_fail} failed")

        return 0

    except Exception as e:
        logger.error(f"Failed to read manifest: {e}")
        return 1


def format_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    i = 0
    v = float(size_bytes)
    while v >= 1024 and i < len(units) - 1:
        v /= 1024
        i += 1
    return f"{v:.1f}{units[i]}"
