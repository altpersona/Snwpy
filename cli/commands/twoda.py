"""
2DA (Two-Dimensional Array) command implementation
Mirrors Nim nwn_twoda behavior:
- Parse and write 2DA V2.0
- Handle "****" as empty cells
- Preserve column order and row indices
- CSV writer uses a stable dialect; JSON mirrors Nim schema
- Minify option compacts spacing while preserving correctness
"""

import sys
from pathlib import Path
import json
import csv
import logging
from typing import List, Dict, Any, Tuple

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

TWODA_MAGIC = "2DA"
TWODA_VERSION = "V2.0"
EMPTY = "****"


def _read_text(path: Path) -> List[str]:
    with path.open("r", encoding="utf-8", errors="replace") as f:
        return f.read().splitlines()


def _strip_bom(line: str) -> str:
    return line[1:] if line and ord(line[0]) == 0xFEFF else line


def parse_2da(lines: List[str]) -> Tuple[List[str], List[Dict[str, Any]]]:
    if not lines:
        raise ValueError("Empty 2DA file")
    lines = [_strip_bom(l.rstrip("\n\r")) for l in lines]

    # Header
    if len(lines) < 3:
        raise ValueError("Invalid 2DA: missing header lines")
    hdr_magic = lines[0].strip()
    hdr_version = lines[1].strip()
    if hdr_magic != TWODA_MAGIC or hdr_version != TWODA_VERSION:
        raise ValueError(f"Invalid 2DA header: {hdr_magic} {hdr_version}")

    # Column header line (skip potential comment/blank line)
    idx = 2
    while idx < len(lines) and lines[idx].strip() == "":
        idx += 1
    if idx >= len(lines):
        raise ValueError("Invalid 2DA: no column header line")
    columns = [c for c in lines[idx].split() if c]
    idx += 1

    # Rows: first token is row index, then columns in order
    rows: List[Dict[str, Any]] = []
    while idx < len(lines):
        line = lines[idx].strip()
        idx += 1
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if not parts:
            continue
        row_idx_str = parts[0]
        try:
            row_idx = int(row_idx_str)
        except Exception:
            row_idx = row_idx_str

        row_values = parts[1:]
        if len(row_values) < len(columns):
            row_values += [EMPTY] * (len(columns) - len(row_values))

        row: Dict[str, Any] = {"Row": row_idx}
        for c, v in zip(columns, row_values):
            row[c] = None if v == EMPTY else v
        rows.append(row)

    return columns, rows


def write_2da(columns: List[str], rows: List[Dict[str, Any]], minify: bool = False) -> str:
    # Header
    out_lines: List[str] = [TWODA_MAGIC, TWODA_VERSION, ""]
    # Columns
    out_lines.append(" ".join(columns))

    # Determine spacing if not minify (tabular alignment)
    if not minify:
        widths = [len(col) for col in columns]
        for row in rows:
            for i, col in enumerate(columns):
                val = row.get(col, None)
                s = EMPTY if val in (None, "") else str(val)
                widths[i] = max(widths[i], len(s))

        def fmt_row(values: List[str]) -> str:
            parts = []
            parts.append(values[0])
            for i, v in enumerate(values[1:]):
                parts.append(v.ljust(widths[i]))
            return " ".join(parts)
    else:
        def fmt_row(values: List[str]) -> str:
            return " ".join(values)

    for row in rows:
        row_id = str(row.get("Row", "0"))
        values = [row_id]
        for col in columns:
            val = row.get(col, None)
            values.append(EMPTY if val in (None, "") else str(val))
        out_lines.append(fmt_row(values))

    return "\n".join(out_lines) + "\n"


def twoda_to_csv(columns: List[str], rows: List[Dict[str, Any]], output: Path) -> None:
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, dialect="excel")
        writer.writerow(["Row"] + columns)
        for row in rows:
            writer.writerow([row.get("Row", "")] + [(row.get(c, None) if row.get(c, None) is not None else "") for c in columns])


def csv_to_twoda(input_csv: Path) -> Tuple[List[str], List[Dict[str, Any]]]:
    with input_csv.open("r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
    if not rows:
        raise ValueError("Empty CSV")
    header = rows[0]
    if not header or header[0].strip().lower() != "row":
        raise ValueError("CSV must have first column named 'Row'")
    columns = header[1:]
    data_rows: List[Dict[str, Any]] = []
    for r in rows[1:]:
        if not r:
            continue
        row_id = r[0]
        try:
            row_id = int(row_id)
        except Exception:
            pass
        values = r[1:] + [""] * max(0, len(columns) - (len(r) - 1))
        row_dict: Dict[str, Any]] = {"Row": row_id}  # type: ignore
        for c, v in zip(columns, values):
            row_dict[c] = None if v == "" else v
        data_rows.append(row_dict)
    return columns, data_rows


def json_to_twoda(input_json: Path) -> Tuple[List[str], List[Dict[str, Any]]]:
    with input_json.open("r", encoding="utf-8") as f:
        data = json.load(f)
    columns = data.get("columns", [])
    rows = data.get("rows", [])
    if not isinstance(columns, list) or not isinstance(rows, list):
        raise ValueError("Invalid JSON schema for 2DA")
    return columns, rows


def twoda_convert(args):
    """Convert 2DA files to/from various formats"""
    input_file = Path(args.input)

    if not input_file.exists():
        logger.error(f"Input file does not exist: {input_file}")
        return 1

    try:
        if args.to_csv or args.to_json:
            # Source is 2DA text
            columns, rows = parse_2da(_read_text(input_file))

            if args.to_csv:
                output_file = Path(args.output) if args.output else input_file.with_suffix(".csv")
                twoda_to_csv(columns, rows, output_file)
                logger.info(f"Converted 2DA to CSV: {output_file}")
            else:
                output_file = Path(args.output) if args.output else input_file.with_suffix(".json")
                with output_file.open("w", encoding="utf-8") as f:
                    json.dump({"columns": columns, "rows": rows}, f, ensure_ascii=False, indent=2)
                logger.info(f"Converted 2DA to JSON: {output_file}")
        else:
            # Convert into 2DA from CSV/JSON, or minify existing 2DA
            output_file = Path(args.output) if args.output else input_file.with_suffix(".2da")

            if input_file.suffix.lower() == ".csv":
                columns, rows = csv_to_twoda(input_file)
            elif input_file.suffix.lower() == ".json":
                columns, rows = json_to_twoda(input_file)
            else:
                # Input already 2DA; parse and rewrite (minify possibly)
                columns, rows = parse_2da(_read_text(input_file))

            text = write_2da(columns, rows, minify=args.minify)
            with output_file.open("w", encoding="utf-8") as f:
                f.write(text)
            logger.info(f"Wrote 2DA: {output_file}")

        return 0

    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        return 1


def twoda_info(args):
    """Display 2DA file information"""
    input_file = Path(args.input)

    if not input_file.exists():
        logger.error(f"Input file does not exist: {input_file}")
        return 1

    try:
        columns, rows = parse_2da(_read_text(input_file))
        print(f"File: {input_file}")
        print(f"Type: 2DA")
        print(f"Version: {TWODA_VERSION}")
        print(f"Columns: {len(columns)}")
        print(f"Rows: {len(rows)}")

        if args.verbose:
            print("\nColumns:")
            print("  " + ", ".join(columns))

        return 0

    except Exception as e:
        logger.error(f"Failed to read 2DA: {e}")
        return 1


def setup_parser(parser):
    """Set up argument parser for twoda command"""
    subcommands = parser.add_subparsers(dest='subcommand', help='2DA subcommands', required=True)

    # Convert subcommand
    convert_parser = subcommands.add_parser('convert', help='Convert 2DA to/from various formats')
    convert_parser.add_argument('input', help='Input file (2DA/CSV/JSON)')
    convert_parser.add_argument('-o', '--output', help='Output file')
    convert_parser.add_argument('--to-csv', action='store_true', help='Convert 2DA to CSV')
    convert_parser.add_argument('--to-json', action='store_true', help='Convert 2DA to JSON')
    convert_parser.add_argument('--minify', action='store_true', help='Minify the 2DA output')
    convert_parser.set_defaults(func=twoda_convert)

    # Info subcommand
    info_parser = subcommands.add_parser('info', help='Display 2DA information')
    info_parser.add_argument('input', help='Input 2DA file')
    info_parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed information')
    info_parser.set_defaults(func=twoda_info)

    return parser
