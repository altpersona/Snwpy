"""
KEY file management command implementation with Nim parity.

Subcommands:
- pack:    Pack directory into KEY/BIF pair
- unpack:  Unpack KEY/BIF into a directory
- list:    List archive contents
- shadows: Show shadow information (overrides across multiple archives)

Relies on core.formats.key if available; otherwise logs errors.
"""

import sys
from pathlib import Path
import logging

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

try:
    # Expected helper API
    from core.formats.key import (
        read_key_bif,
        write_key_bif,
        KeyArchive,
        list_key,
        compute_shadows,
    )  # type: ignore
except Exception:
    read_key_bif = None
    write_key_bif = None
    KeyArchive = None  # type: ignore
    list_key = None
    compute_shadows = None


def key_unpack(args):
    """Unpack KEY/BIF contents into directory."""
    input_file = Path(args.input)
    if not input_file.exists():
        logger.error(f"Input file does not exist: {input_file}")
        return 1

    output_dir = Path(args.output) if args.output else input_file.parent / f"{input_file.stem}_unpacked"
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        if read_key_bif is None:
            logger.error("KEY reader not available in core.formats.key")
            return 1

        logger.info(f"Unpacking KEY: {input_file}")
        logger.info(f"Output directory: {output_dir}")

        arch = read_key_bif(str(input_file))  # type: ignore
        for name, data in arch.iter_items():  # type: ignore
            out = output_dir / name
            out.parent.mkdir(parents=True, exist_ok=True)
            with out.open("wb") as f:
                f.write(data)

        logger.info("Unpack completed")
        return 0
    except Exception as e:
        logger.error(f"Unpacking failed: {e}")
        return 1


def key_pack(args):
    """Pack directory into KEY/BIF pair."""
    input_dir = Path(args.input)
    if not input_dir.exists() or not input_dir.is_dir():
        logger.error(f"Input directory does not exist: {input_dir}")
        return 1

    output_file = Path(args.output) if args.output else input_dir.with_suffix(".key")

    try:
        if write_key_bif is None or KeyArchive is None:
            logger.error("KEY writer not available in core.formats.key")
            return 1

        logger.info(f"Packing directory: {input_dir}")
        logger.info(f"Output KEY: {output_file}")

        arch = KeyArchive()  # type: ignore
        for p in input_dir.rglob("*"):
            if p.is_file():
                rel = p.relative_to(input_dir).as_posix()
                with p.open("rb") as f:
                    arch.add(rel, f.read())  # type: ignore

        write_key_bif(arch, str(output_file))  # type: ignore
        logger.info(f"Wrote KEY: {output_file}")
        return 0
    except Exception as e:
        logger.error(f"Packing failed: {e}")
        return 1


def key_list(args):
    """List contents of KEY archive."""
    input_file = Path(args.input)
    if not input_file.exists():
        logger.error(f"Input file does not exist: {input_file}")
        return 1

    try:
        if list_key is None:
            logger.error("KEY lister not available in core.formats.key")
            return 1

        entries = list_key(str(input_file))  # type: ignore
        print(f"KEY: {input_file}")
        for e in entries:
            if isinstance(e, (tuple, list)) and len(e) >= 2:
                name, size = e[0], e[1]
                print(f"  {name} ({size} bytes)")
            else:
                print(f"  {e}")
        print(f"Entries: {len(entries)}")
        return 0
    except Exception as e:
        logger.error(f"Listing failed: {e}")
        return 1


def key_shadows(args):
    """Show shadowing information across KEY archives."""
    input_file = Path(args.input)
    if not input_file.exists():
        logger.error(f"Input file does not exist: {input_file}")
        return 1

    try:
        if compute_shadows is None:
            logger.error("KEY shadows not available in core.formats.key")
            return 1

        print(f"Shadows for: {input_file}")
        report = compute_shadows(str(input_file))  # type: ignore
        for line in report:
            print(line)
        return 0
    except Exception as e:
        logger.error(f"Shadow analysis failed: {e}")
        return 1


def setup_parser(parser):
    """Set up argument parser for key command"""
    subcommands = parser.add_subparsers(dest="subcommand", help="KEY subcommands", required=True)

    # Unpack subcommand
    unpack_parser = subcommands.add_parser("unpack", help="Unpack KEY file")
    unpack_parser.add_argument("input", help="Input KEY file")
    unpack_parser.add_argument("-o", "--output", help="Output directory")
    unpack_parser.set_defaults(func=key_unpack)

    # Pack subcommand
    pack_parser = subcommands.add_parser("pack", help="Pack directory into KEY file")
    pack_parser.add_argument("input", help="Input directory")
    pack_parser.add_argument("-o", "--output", help="Output KEY file")
    pack_parser.set_defaults(func=key_pack)

    # List subcommand
    list_parser = subcommands.add_parser("list", help="List KEY file contents")
    list_parser.add_argument("input", help="Input KEY file")
    list_parser.set_defaults(func=key_list)

    # Shadows subcommand
    shadows_parser = subcommands.add_parser("shadows", help="Show shadow information")
    shadows_parser.add_argument("input", help="Input KEY file")
    shadows_parser.set_defaults(func=key_shadows)

    return parser
