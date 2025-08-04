"""
Command modules for CLI interface
"""

# Import all command modules here for easier access
from . import (
    nwsync_write,
    nwsync_print,
    erf_pack,
    erf_unpack,
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

__all__ = [
    'nwsync_write', 'nwsync_print', 'nwsync_fetch', 'nwsync_prune',
    'erf_pack', 'erf_unpack', 'gff', 'tlk', 'twoda', 'key', 'resman', 'script'
]

# Available commands mapping
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
