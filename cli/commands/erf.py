"""
ERF/Mod archive commands with Nim parity.

Provides:
- erf pack: Pack a directory of resources into an ERF/ERF-like archive
- erf unpack: Unpack an ERF archive into a directory
- info: Show archive metadata/contents (lightweight)

Note:
- This module relies on core.formats.erf read/write helpers if present.
- If core.formats.erf is minimal, we keep thin wrappers and logging consistent
  with other commands, mirroring CLI semantics from Nim tools.
"""

import sys
from pathlib import Path
import logging

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    # Expected helpers in core.formats.erf
    from core.formats.erf import read_erf, write_erf, ErfArchive  # type: ignore
except Exception:  # Fallback placeholders if not available
    read_erf = None
    write_erf = None
    ErfArchive = None  # type: ignore

logger = logging.getLogger(__name__)


def erf_pack(args):
    """Pack a directory into an ERF archive."""
    input_dir = Path(args.input)
    if not input_dir.exists() or not input_dir.is_dir():
        logger.error(f"Input directory does not exist: {input_dir}")
        return 1

    output_file = Path(args.output) if args.output else input_dir.with_suffix(".erf")

    try:
        if write_erf is None:
            logger.error("ERF writer not available in core.formats.erf")
            return 1

        logger.info(f"Packing ERF from directory: {input_dir}")
        logger.info(f"Output: {output_file}")

        # Gather files recursively preserving relative paths
        files = []
        for p in input_dir.rglob("*"):
            if p.is_file():
                rel = p.relative_to(input_dir).as_posix()
                files.append((rel, p))

        # Construct archive in expected structure for write_erf
        archive = ErfArchive()  # type: ignore
        for rel, p in files:
            with p.open("rb") as f:
                data = f.read()
            # The archive API is assumed; if different, adapt mapping here
            archive.add(rel, data)  # type: ignore

        write_erf(archive, str(output_file))  # type: ignore
        logger.info(f"Wrote ERF: {output_file}")
        return 0
    except Exception as e:
        logger.error(f"ERF pack failed: {e}")
        return 1


def erf_unpack(args):
    """Unpack an ERF archive into a directory."""
    input_file = Path(args.input)
    if not input_file.exists():
        logger.error(f"Input file does not exist: {input_file}")
        return 1

    output_dir = Path(args.output) if args.output else input_file.parent / f"{input_file.stem}_unpacked"
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        if read_erf is None:
            logger.error("ERF reader not available in core.formats.erf")
            return 1

        logger.info(f"Unpacking ERF: {input_file}")
        logger.info(f"Output directory: {output_dir}")

        archive = read_erf(str(input_file))  # type: ignore
        # Expect archive to provide iterable of (name, bytes)
        for name, data in archive.iter_items():  # type: ignore
            out_path = output_dir / name
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with out_path.open("wb") as f:
                f.write(data)

        logger.info("Unpack completed")
        return 0
    except Exception as e:
        logger.error(f"ERF unpack failed: {e}")
        return 1


def erf_info(args):
    """Display ERF archive information and list of files."""
    input_file = Path(args.input)
    if not input_file.exists():
        logger.error(f"Input file does not exist: {input_file}")
        return 1

    try:
        if read_erf is None:
            logger.error("ERF reader not available in core.formats.erf")
            return 1

        archive = read_erf(str(input_file))  # type: ignore

        # Best-effort information dump
        print(f"Archive: {input_file}")
        if hasattr(archive, "metadata"):
            print("Metadata:")
            for k, v in getattr(archive, "metadata").items():  # type: ignore
                print(f"  {k}: {v}")

        print("Contents:")
        total = 0
        for name, data in archive.iter_items():  # type: ignore
            size = len(data)
            total += 1
            print(f"  {name} ({size} bytes)")
        print(f"Entries: {total}")
        return 0
    except Exception as e:
        logger.error(f"ERF info failed: {e}")
        return 1


def setup_parser(parser):
    """Set up argument parser for erf command (pack/unpack/info)."""
    subcommands = parser.add_subparsers(dest="subcommand", help="ERF subcommands", required=True)

    # Pack
    pack_parser = subcommands.add_parser("pack", help="Pack directory into ERF archive")
    pack_parser.add_argument("input", help="Input directory")
    pack_parser.add_argument("-o", "--output", help="Output ERF file")
    pack_parser.set_defaults(func=erf_pack)

    # Unpack
    unpack_parser = subcommands.add_parser("unpack", help="Unpack ERF archive")
    unpack_parser.add_argument("input", help="Input ERF file")
    unpack_parser.add_argument("-o", "--output", help="Output directory")
    unpack_parser.set_defaults(func=erf_unpack)

    # Info
    info_parser = subcommands.add_parser("info", help="Show ERF archive information")
    info_parser.add_argument("input", help="Input ERF file")
    info_parser.set_defaults(func=erf_info)

    return parser