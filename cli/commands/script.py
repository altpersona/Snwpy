"""
NWScript compilation command implementation
"""

import sys
from pathlib import Path
import logging
import subprocess

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


def script_compile(args):
    """Compile NWScript files"""
    input_file = Path(args.input)
    
    if not input_file.exists():
        logger.error(f"Input file does not exist: {input_file}")
        return 1
    
    try:
        output_file = Path(args.output) if args.output else input_file.with_suffix('.ncs')
        
        logger.info(f"Compiling script: {input_file}")
        logger.info(f"Output file: {output_file}")
        
        # Check for includes directory
        includes_dir = None
        if args.includes:
            includes_dir = Path(args.includes)
            if not includes_dir.exists():
                logger.warning(f"Includes directory not found: {includes_dir}")
        
        # Placeholder implementation - would integrate with NWScript compiler
        # In a real implementation, this would call nwnsc or similar
        logger.info("Script compilation not yet implemented")
        
        if args.verbose:
            print(f"Input: {input_file}")
            print(f"Output: {output_file}")
            if includes_dir:
                print(f"Includes: {includes_dir}")
        
        # Create a dummy output file for testing
        if args.dummy:
            with open(output_file, 'wb') as f:
                f.write(b'NCS V1.0B\x00\x00\x00\x00')  # Basic NCS header
            logger.info(f"Created dummy compiled script: {output_file}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Compilation failed: {e}")
        return 1


def script_decompile(args):
    """Decompile NWScript bytecode"""
    input_file = Path(args.input)
    
    if not input_file.exists():
        logger.error(f"Input file does not exist: {input_file}")
        return 1
    
    try:
        output_file = Path(args.output) if args.output else input_file.with_suffix('.nss')
        
        logger.info(f"Decompiling script: {input_file}")
        logger.info(f"Output file: {output_file}")
        
        # Placeholder implementation - would implement NCS decompiler
        logger.info("Script decompilation not yet implemented")
        
        return 0
        
    except Exception as e:
        logger.error(f"Decompilation failed: {e}")
        return 1


def script_disasm(args):
    """Disassemble NWScript bytecode"""
    input_file = Path(args.input)
    
    if not input_file.exists():
        logger.error(f"Input file does not exist: {input_file}")
        return 1
    
    try:
        logger.info(f"Disassembling script: {input_file}")
        
        # Placeholder implementation - would show NCS opcodes
        print(f"Disassembly of: {input_file}")
        print("(NCS disassembly not yet implemented)")
        
        return 0
        
    except Exception as e:
        logger.error(f"Disassembly failed: {e}")
        return 1


def setup_parser(parser):
    """Set up argument parser for script command"""
    
    subcommands = parser.add_subparsers(dest='subcommand', help='Script subcommands')
    
    # Compile subcommand
    compile_parser = subcommands.add_parser('compile', help='Compile NWScript')
    compile_parser.add_argument('input', help='Input NSS file')
    compile_parser.add_argument('-o', '--output', help='Output NCS file')
    compile_parser.add_argument('-i', '--includes', help='Includes directory')
    compile_parser.add_argument('-v', '--verbose', action='store_true',
                               help='Verbose output')
    compile_parser.add_argument('--dummy', action='store_true',
                               help='Create dummy output file for testing')
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
    
    # Default to compile if no subcommand
    parser.add_argument('input', nargs='?', help='Input NSS file')
    parser.add_argument('-o', '--output', help='Output NCS file')
    parser.add_argument('-i', '--includes', help='Includes directory')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    parser.add_argument('--dummy', action='store_true',
                       help='Create dummy output file for testing')
    parser.set_defaults(func=script_compile)
    
    return parser
