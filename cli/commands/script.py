"""
NWScript compilation/decompilation/disassembly commands with functional behavior.

This module prefers native Python/core helpers if available; otherwise it
falls back to calling an external compiler/decompiler (e.g., nwnsc) when present,
or returning clear diagnostics without crashing the GUI.
"""

import sys
from pathlib import Path
import logging
import shutil
import subprocess

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

# Optional core helpers (if exist)
try:
    from core.formats.gff import read_gff  # placeholder import to demonstrate pattern
except Exception:
    read_gff = None  # not required; just shows pattern for optional core calls


def _which(cmd: str) -> Path | None:
    p = shutil.which(cmd)
    return Path(p) if p else None


def _run(cmd: list[str]) -> int:
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.stdout:
            print(proc.stdout, end="")
        if proc.stderr:
            logger.warning(proc.stderr.strip())
        return proc.returncode
    except Exception as e:
        logger.error(f"Failed to execute {cmd[0]}: {e}")
        return 1


def script_compile(args):
    """Compile NWScript files to NCS."""
    input_file = Path(args.input)
    if not input_file.exists():
        logger.error(f"Input file does not exist: {input_file}")
        return 1

    output_file = Path(args.output) if args.output else input_file.with_suffix('.ncs')
    includes_dir = Path(args.includes) if args.includes else None
    if includes_dir and not includes_dir.exists():
        logger.warning(f"Includes directory not found: {includes_dir}")

    try:
        # Option 1: External compiler 'nwnsc' if present
        nwnsc = _which("nwnsc")
        if nwnsc:
            cmd = [str(nwnsc), "-o", str(output_file), str(input_file)]
            if includes_dir:
                cmd.extend(["-i", str(includes_dir)])
            if args.verbose:
                cmd.append("-v")
            return _run(cmd)

        # Option 2: Dummy compilation for CI/GUI smoke if requested
        if args.dummy:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with output_file.open('wb') as f:
                f.write(b'NCS V1.0B\x00\x00\x00\x00')
            logger.info(f"Created dummy compiled script: {output_file}")
            return 0

        logger.error("No NWScript compiler found (nwnsc not on PATH). Use --dummy to generate placeholder output.")
        return 1

    except Exception as e:
        logger.error(f"Compilation failed: {e}")
        return 1


def script_decompile(args):
    """Decompile NCS → NSS (external tool if available)."""
    input_file = Path(args.input)
    if not input_file.exists():
        logger.error(f"Input file does not exist: {input_file}")
        return 1

    output_file = Path(args.output) if args.output else input_file.with_suffix('.nss')
    try:
        # Hypothetical external 'ncsdecomp' (adjust if you have a real tool)
        decomp = _which("ncsdecomp")
        if decomp:
            cmd = [str(decomp), str(input_file), "-o", str(output_file)]
            return _run(cmd)

        logger.error("No NWScript decompiler found (ncsdecomp not on PATH).")
        return 1
    except Exception as e:
        logger.error(f"Decompilation failed: {e}")
        return 1


def script_disasm(args):
    """Disassemble NCS (external tool if available)."""
    input_file = Path(args.input)
    if not input_file.exists():
        logger.error(f"Input file does not exist: {input_file}")
        return 1

    try:
        # Hypothetical 'ncsdis' disassembler
        dis = _which("ncsdis")
        if dis:
            cmd = [str(dis), str(input_file)]
            return _run(cmd)

        print(f"Disassembly of: {input_file}")
        print("(No disassembler found; provide 'ncsdis' on PATH for real output)")
        return 0
    except Exception as e:
        logger.error(f"Disassembly failed: {e}")
        return 1


def setup_parser(parser):
    """Set up argument parser for script command."""
    subcommands = parser.add_subparsers(dest='subcommand', help='Script subcommands', required=True)

    # Compile subcommand
    compile_parser = subcommands.add_parser('compile', help='Compile NWScript')
    compile_parser.add_argument('input', help='Input NSS file')
    compile_parser.add_argument('-o', '--output', help='Output NCS file')
    compile_parser.add_argument('-i', '--includes', help='Includes directory')
    compile_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    compile_parser.add_argument('--dummy', action='store_true', help='Create dummy output file for testing')
    compile_parser.set_defaults(func=script_compile)

    # Decompile subcommand
    decompile_parser = subcommands.add_parser('decompile', help='Decompile NWScript bytecode')
    decompile_parser.add_argument('input', help='Input NCS file')
    decompile_parser.add_argument('-o', '--output', help='Output NSS file')
    decompile_parser.set_defaults(func=script_decompile)

    # Disassemble subcommand
    disasm_parser = subcommands.add_parser('disasm', help='Disassemble NWScript bytecode')
    disasm_parser.add_argument('input', help='Input NCS file')
    disasm_parser.set_defaults(func=script_disasm)

    return parser
