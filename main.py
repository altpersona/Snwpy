#!/usr/bin/env python3
"""
NeverWinter Python Tools (NWPY)
Main entry point for CLI and GUI applications
"""

import sys
import argparse
from pathlib import Path

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent))

from core import __version__
from cli.main import main as cli_main
from gui.main import main as gui_main


def main():
    # Check if we have any arguments
    if len(sys.argv) < 2:
        print("Usage: nwpy {cli|gui} [args...]")
        return 1
    
    mode = sys.argv[1]
    
    if mode == "cli":
        # Pass remaining args to CLI (skip 'cli' argument)
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        return cli_main()
    elif mode == "gui":
        return gui_main()
    elif mode in ["--help", "-h"]:
        print("NeverWinter Python Tools - CLI and GUI for NWN file formats")
        print("")
        print("Usage:")
        print("  nwpy cli [command] [args...]    Run CLI interface")
        print("  nwpy gui                        Run GUI interface")
        print("")
        print("CLI Commands:")
        print("  erf pack/unpack   ✅ ERF archive operations")
        print("  gff convert/info  ✅ GFF file operations")
        print("  nwsync write/print ✅ NWSync operations")
        print("  tlk convert/info  ✅ TLK (Talk Table) operations")
        print("  twoda convert/info ✅ 2DA operations (includes --minify)")
        print("  key pack/unpack/list ✅ KEY file operations")
        print("  resman extract/stats/grep ✅ Resource manager operations")
        print("  script compile/decompile ✅ NWScript operations")
        print("")
        print("Use 'nwpy cli --help' for full command list")
        return 0
    elif mode == "--version":
        print(f"NWPY {__version__}")
        return 0
    else:
        print(f"Unknown mode: {mode}")
        print("Use 'nwpy --help' for usage information")
        return 1


if __name__ == "__main__":
    sys.exit(main())
