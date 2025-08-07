"""
Command modules for CLI interface
"""

# Import all command modules here for easier access
from . import (
    nwsync_write,
    nwsync_print,
    gff,
    tlk,
    twoda,
    key,
    resman,
    script,
)

# Import remaining placeholders
from .placeholders import (
    nwsync_fetch,
    nwsync_prune,
)

# New ERF commands live in commands/erf.py (pack/unpack/info). Ensure they are imported.
from . import erf  # provides pack/unpack/info setup in its own module

__all__ = [
    'nwsync_write', 'nwsync_print', 'nwsync_fetch', 'nwsync_prune',
    'erf', 'gff', 'tlk', 'twoda', 'key', 'resman', 'script'
]

# Available commands mapping (descriptive only)
AVAILABLE_COMMANDS = {
    'erf': 'ERF archive operations',
    'gff': 'GFF file operations',
    'nwsync': 'NWSync operations',
    'tlk': 'TLK (Talk Table) operations',
    'twoda': '2DA (Two-Dimensional Array) operations',
    'key': 'KEY file operations',
    'resman': 'Resource manager operations',
    'script': 'NWScript compilation operations',
}
