"""
Resource manager (resman) command implementations with functional behavior.

This module uses core.resman APIs to provide:
- cat:    print a resource's data to stdout
- extract: extract matching resources to a directory
- grep:   search resources by name pattern and/or type
- stats:  print simple counts/bytes
- diff:   compare two containers (names only)

All commands return 0 on success, 1 on error.
"""

import sys
from pathlib import Path
import logging
import fnmatch

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.resman import ResMan, ResRef  # type: ignore

logger = logging.getLogger(__name__)


def _open_resman() -> ResMan:
    # ResMan may need additional roots; for now construct default
    return ResMan()


def _matches(name: str, pattern: str | None) -> bool:
    if not pattern:
        return True
    return fnmatch.fnmatch(name.lower(), pattern.lower())


def _type_matches(resref: ResRef, typ: str | None) -> bool:
    if not typ:
        return True
    return resref.res_type.lower() == typ.lower()


def resman_cat(args):
    """Print resource to stdout"""
    try:
        rm = _open_resman()
        rr = ResRef.from_filename(args.resource) if "." in args.resource else ResRef(args.resource, "")
        data = rm.read(rr)
        if data is None:
            logger.error(f"Resource not found: {args.resource}")
            return 1
        # Write raw bytes to stdout.buffer
        sys.stdout.buffer.write(data)
        return 0
    except Exception as e:
        logger.error(f"Cat failed: {e}")
        return 1


def resman_extract(args):
    """Extract resources from game data"""
    try:
        output_dir = Path(args.output) if args.output else Path.cwd() / "extracted"
        output_dir.mkdir(parents=True, exist_ok=True)

        rm = _open_resman()
        count = 0
        for rr in rm.iter():
            name = f"{rr.name}.{rr.res_type}" if rr.res_type else rr.name
            if not _matches(name, args.pattern) or not _type_matches(rr, args.type):
                continue
            data = rm.read(rr)
            if data is None:
                continue
            out_path = output_dir / name
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with out_path.open("wb") as f:
                f.write(data)
            count += 1

        logger.info(f"Extracted {count} resources to {output_dir}")
        return 0
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return 1


def resman_grep(args):
    """Search for patterns in resources"""
    try:
        rm = _open_resman()
        matches = []
        for rr in rm.iter():
            name = f"{rr.name}.{rr.res_type}" if rr.res_type else rr.name
            if _matches(name, args.pattern) and _type_matches(rr, args.type):
                matches.append(name)

        for m in sorted(matches):
            print(m)
        return 0
    except Exception as e:
        logger.error(f"Grep failed: {e}")
        return 1


def resman_stats(args):
    """Show resource statistics"""
    try:
        rm = _open_resman()
        total = 0
        by_type: dict[str, int] = {}
        for rr in rm.iter():
            total += 1
            by_type[rr.res_type] = by_type.get(rr.res_type, 0) + 1

        print("Resource Statistics:")
        print(f"  Total: {total}")
        for t, n in sorted(by_type.items()):
            print(f"  {t or '(none)'}: {n}")
        return 0
    except Exception as e:
        logger.error(f"Stats failed: {e}")
        return 1


def resman_diff(args):
    """Compare resource containers"""
    try:
        left_root = Path(args.first)
        right_root = Path(args.second)

        left = set()
        right = set()

        # Use ResRef.from_filename on file listings for both directories
        for p in left_root.rglob("*"):
            if p.is_file():
                left.add(p.name.lower())
        for p in right_root.rglob("*"):
            if p.is_file():
                right.add(p.name.lower())

        only_left = sorted(left - right)
        only_right = sorted(right - left)
        common = sorted(left & right)

        print(f"Only in {left_root}:")
        for n in only_left:
            print(f"  {n}")
        print(f"\nOnly in {right_root}:")
        for n in only_right:
            print(f"  {n}")
        print(f"\nCommon:")
        for n in common:
            print(f"  {n}")

        return 0
    except Exception as e:
        logger.error(f"Diff failed: {e}")
        return 1


def setup_parser(parser):
    """Set up argument parser for resman command"""
    subcommands = parser.add_subparsers(dest='subcommand', help='Resource manager subcommands', required=True)

    # Cat subcommand
    cat_parser = subcommands.add_parser('cat', help='Print resource to stdout')
    cat_parser.add_argument('resource', help='Resource name (e.g., filename.ext)')
    cat_parser.set_defaults(func=resman_cat)

    # Extract subcommand
    extract_parser = subcommands.add_parser('extract', help='Extract resources')
    extract_parser.add_argument('-o', '--output', help='Output directory')
    extract_parser.add_argument('-p', '--pattern', help='Resource name pattern')
    extract_parser.add_argument('--type', help='Resource type filter')
    extract_parser.set_defaults(func=resman_extract)

    # Grep subcommand
    grep_parser = subcommands.add_parser('grep', help='Search for patterns in resources')
    grep_parser.add_argument('pattern', help='Pattern to search for')
    grep_parser.add_argument('--type', help='Resource type filter')
    grep_parser.set_defaults(func=resman_grep)

    # Stats subcommand
    stats_parser = subcommands.add_parser('stats', help='Show resource statistics')
    stats_parser.set_defaults(func=resman_stats)

    # Diff subcommand
    diff_parser = subcommands.add_parser('diff', help='Compare resource containers')
    diff_parser.add_argument('first', help='First resource container path')
    diff_parser.add_argument('second', help='Second resource container path')
    diff_parser.set_defaults(func=resman_diff)

    return parser
