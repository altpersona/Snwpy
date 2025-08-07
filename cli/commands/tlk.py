"""
TLK (Talk table) command implementation
Mirrors the Nim tool behaviour and JSON schema.
"""

import sys
from pathlib import Path
import json
import logging
import struct
from typing import BinaryIO, Dict, Any, List

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

# TLK constants per neverwinter.nim/neverwinter/tlk.nim
TLK_MAGIC = b"TLK "
TLK_VERSION = b"V3.0"
HEADER_SIZE = 20
ENTRY_SIZE = 40


def _read_exact(f: BinaryIO, n: int) -> bytes:
    b = f.read(n)
    if len(b) != n:
        raise EOFError(f"Unexpected EOF while reading {n} bytes")
    return b


def _decode_resref(raw: bytes) -> str:
    # Nim strips whitespace and 0x00/0xC0 padding around the soundResRef
    s = raw.decode("latin-1", errors="ignore")
    return s.strip().strip("\x00").strip("\xC0").strip()


def _from_nwn_encoding(raw: bytes) -> str:
    # Mirror Nim's fromNwnEncoding (cp1252 fallback)
    try:
        return raw.decode("cp1252")
    except Exception:
        return raw.decode("latin-1", errors="replace")


def read_tlk_to_json(path: Path) -> Dict[str, Any]:
    with path.open("rb") as f:
        magic = _read_exact(f, 4)
        if magic != TLK_MAGIC:
            raise ValueError(f"Invalid TLK magic: {magic!r}")
        ver = _read_exact(f, 4)
        if ver != TLK_VERSION:
            raise ValueError(f"Unsupported TLK version: {ver!r}")

        language_id = struct.unpack("<i", _read_exact(f, 4))[0]
        string_count = struct.unpack("<I", _read_exact(f, 4))[0]
        entries_offset = struct.unpack("<I", _read_exact(f, 4))[0]

        entries: List[Dict[str, Any]] = []
        for idx in range(string_count):
            f.seek(HEADER_SIZE + ENTRY_SIZE * idx, 0)
            flags = struct.unpack("<i", _read_exact(f, 4))[0]
            sound_resref = _decode_resref(_read_exact(f, 16))
            _ = struct.unpack("<i", _read_exact(f, 4))[0]  # vol variance (unused)
            _ = struct.unpack("<i", _read_exact(f, 4))[0]  # pitch variance (unused)
            off = struct.unpack("<i", _read_exact(f, 4))[0]
            length = struct.unpack("<i", _read_exact(f, 4))[0]
            sound_length = struct.unpack("<f", _read_exact(f, 4))[0]

            text = ""
            if length > 0:
                f.seek(entries_offset + off, 0)
                text_bytes = _read_exact(f, length)
                text = _from_nwn_encoding(text_bytes).replace("\r", "")

            # hasValue exactly as Nim: text != "" or soundResRef != ""
            if text != "" or sound_resref != "":
                entries.append(
                    {
                        "id": idx,
                        "text": text,
                        "soundResRef": sound_resref,
                        "soundLength": round(max(float(sound_length), 0.0), 4),
                    }
                )

        return {"language": int(language_id), "entries": entries}


def tlk_convert(args):
    """Convert TLK files to/from various formats"""
    input_file = Path(args.input)

    if not input_file.exists():
        logger.error(f"Input file does not exist: {input_file}")
        return 1

    try:
        if args.to_json:
            logger.info(f"Converting TLK to JSON: {input_file}")
            output_file = Path(args.output) if args.output else input_file.with_suffix(".json")
            data = read_tlk_to_json(input_file)
            with output_file.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Converted TLK to JSON: {output_file}")
        else:
            logger.error("JSON -> TLK not implemented yet (parity reader completed).")
            return 1

        return 0
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        return 1


def tlk_info(args):
    """Display TLK file information"""
    input_file = Path(args.input)

    if not input_file.exists():
        logger.error(f"Input file does not exist: {input_file}")
        return 1

    try:
        data = read_tlk_to_json(input_file)
        print(json.dumps({"file": str(input_file), **data}, indent=2))
        return 0
    except Exception as e:
        logger.error(f"Failed to read TLK: {e}")
        return 1


def setup_parser(parser):
    """Set up argument parser for tlk command"""
    # Make subcommand optional; default to 'convert' to be friendlier to GUI
    subcommands = parser.add_subparsers(dest="subcommand", help="TLK subcommands")

    # Convert subcommand
    convert_parser = subcommands.add_parser("convert", help="Convert TLK to/from JSON")
    convert_parser.add_argument("input", help="Input file")
    convert_parser.add_argument("-o", "--output", help="Output file")
    convert_parser.add_argument(
        "--to-json",
        action="store_true",
        help="Convert TLK to JSON (default: JSON to TLK)",
    )
    convert_parser.set_defaults(func=tlk_convert)

    # Info subcommand
    info_parser = subcommands.add_parser("info", help="Display TLK information")
    info_parser.add_argument("input", help="Input TLK file")
    info_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show detailed information"
    )
    info_parser.set_defaults(func=tlk_info)

    # Default behavior: if no subcommand is specified, route to convert
    parser.set_defaults(func=tlk_convert)
    parser.add_argument("input", nargs="?", help="Input file")
    parser.add_argument("-o", "--output", help="Output file")
    parser.add_argument(
        "--to-json",
        action="store_true",
        help="Convert TLK to JSON (default: JSON to TLK)",
    )

    return parser
