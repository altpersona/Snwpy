"""
CLI main interface
Provides command-line access to all NWN tools
"""

import sys
import argparse
import logging
from pathlib import Path

# Import all CLI modules
try:
    from .commands import nwsync_write, nwsync_print, gff, tlk, twoda, key, resman, script, erf
    from .commands.placeholders import (
        nwsync_fetch, nwsync_prune
    )
except ImportError as e:
    # Handle import errors gracefully
    print(f"Warning: Failed to import commands: {e}")
    sys.exit(1)


def setup_logging(verbose: bool = False, quiet: bool = False):
    """Setup logging configuration"""
    if quiet:
        level = logging.WARNING
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
        
    logging.basicConfig(
        level=level,
        format='%(levelname)s [%(asctime)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="NeverWinter Python Tools - Command Line Interface",
        prog="nwpy"
    )
    
    # Global options
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--quiet', action='store_true', help='Quiet mode (warnings only)')
    parser.add_argument('--version', action='version', version='NWPY 1.0.0')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # NWSync commands
    nwsync_write.setup_parser(subparsers.add_parser(
        'nwsync-write', 
        help='Create NWSync manifests'
    ))
    
    nwsync_print.setup_parser(subparsers.add_parser(
        'nwsync-print',
        help='Print manifest contents'
    ))
    
    nwsync_fetch.setup_parser(subparsers.add_parser(
        'nwsync-fetch',
        help='Fetch NWSync data'
    ))
    
    nwsync_prune.setup_parser(subparsers.add_parser(
        'nwsync-prune',
        help='Prune NWSync repository'
    ))
    
    # ERF commands
    erf_pack_parser = subparsers.add_parser('erf-pack', help='Pack ERF archives')
    erf_pack.setup_parser(erf_pack_parser)
    
    erf_unpack_parser = subparsers.add_parser('erf-unpack', help='Unpack ERF archives')
    erf_unpack.setup_parser(erf_unpack_parser)
    
    # GFF commands
    gff_parser = subparsers.add_parser('gff', help='Convert GFF files')
    gff.setup_parser(gff_parser)
    
    # TLK commands
    tlk_parser = subparsers.add_parser('tlk', help='TLK operations')
    tlk.setup_parser(tlk_parser)
    
    # 2DA commands
    twoda_parser = subparsers.add_parser('twoda', help='2DA operations')
    twoda.setup_parser(twoda_parser)
    
    # Key file commands
    key_parser = subparsers.add_parser('key', help='KEY file operations')
    key.setup_parser(key_parser)

    # ERF commands
    erf_parser = subparsers.add_parser('erf', help='ERF archive operations')
    erf.setup_parser(erf_parser)
    
    # Resource manager commands
    resman_parser = subparsers.add_parser('resman', help='Resource manager operations')
    resman.setup_parser(resman_parser)
    
    # Script commands
    script_parser = subparsers.add_parser('script', help='NWScript operations')
    script.setup_parser(script_parser)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose, args.quiet)
    
    # Route to appropriate command
    if not args.command:
        parser.print_help()
        return 1
        
    # Command dispatch - call func from args (set by setup_parser)
    if hasattr(args, 'func'):
        try:
            return args.func(args)
        except Exception as e:
            logging.error(f"Command failed: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1
    else:
        logging.error(f"No function assigned to command: {args.command}")
        logging.debug(f"Available args: {vars(args)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
