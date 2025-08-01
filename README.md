# NeverWinter Python Tools (NWPY)

A comprehensive Python implementation of the Neverwinter.nim toolkit, providing both command-line interface (CLI) and graphical user interface (GUI) for working with Neverwinter Nights Enhanced Edition file formats.

## Features

- **Complete NWN Toolkit**: Python reimplementation of all Neverwinter.nim tools
- **CLI Support**: Command-line interface matching the original Nim tools
- **GUI Support**: Modern graphical interface for visual interaction with NWN files
- **File Format Support**: Handle ERF, HAK, KEY, GFF, TLK, 2DA, MOD files and more
- **NWSync Support**: Full NWSync repository management and manifest operations
- **Resource Manager**: Complete resource management with container hierarchy
- **Cross-Platform**: Works on Windows, Linux, and macOS

## Installation

### From Source

```bash
git clone <repository-url>
cd nwpy
python setup.py install
```

### Development Install

```bash
pip install -e .
```

## Usage

### Command-Line Interface

```bash
# Run CLI mode
python main.py cli

# Available commands:
python main.py cli nwsync-write --help
python main.py cli nwsync-print manifest.json
python main.py cli erf-unpack file.hak output/
python main.py cli gff input.gff --format json
```

### Graphical User Interface

```bash
# Run GUI mode
python main.py gui
```

The GUI provides a user-friendly interface with:

- Tool selection dropdown organized by category
- Dynamic configuration forms for each tool
- Real-time output display with logging
- File browsers for easy file selection

## Supported Tools

### Archive & Resource Management

- `nwsync-write` - Create NWSync manifests
- `nwsync-print` - Display manifest contents
- `nwsync-fetch` - Fetch NWSync data
- `nwsync-prune` - Prune NWSync repository
- `erf-pack` - Pack ERF archives
- `erf-unpack` - Unpack ERF archives
- `key-pack` - Pack KEY files
- `key-unpack` - Unpack KEY files
- `resman-extract` - Extract resources
- `resman-stats` - Show resource statistics
- `resman-grep` - Search resources

### File Format Tools

- `gff` - Convert GFF files to/from JSON/XML
- `tlk` - Convert TLK files to/from various formats
- `twoda` - Convert 2DA files to/from various formats

### Development Tools

- `script-compile` - Compile NWScript files

## Python API

The toolkit can also be used as a Python library:

```python
from nwpy.core.formats import read_gff, read_erf
from nwpy.core.nwsync import NWSyncRepository
from nwpy.core.resman import ResMan

# Read GFF file
gff_root = read_gff("character.bic")
print(f"Character name: {gff_root.get('FirstName', 'Unknown')}")

# Read ERF archive
erf = read_erf("tileset.hak")
print(f"HAK contains {len(erf)} files")

# Work with NWSync
repo = NWSyncRepository("/path/to/nwsync")
manifest = repo.read_manifest("abc123...")

# Use Resource Manager
resman = ResMan()
resman.add_directory("override/")
resman.add_erf("module.mod")
data = resman.get_data(ResRef("area001", 2012))
```

## Architecture

The project is organized into several key modules:

- **core/formats/** - File format implementations (GFF, ERF, etc.)
- **core/nwsync.py** - NWSync manifest and repository management
- **core/resman.py** - Resource manager with container hierarchy
- **cli/** - Command-line interface implementation
- **gui/** - Tkinter-based graphical interface

## Compatibility

This implementation aims for 100% compatibility with the original Neverwinter.nim tools:

- Same command-line arguments and options
- Identical file format handling
- Compatible NWSync repository structure
- Matching output formats and error messages

## Development Status

- ✅ Core architecture and project structure
- ✅ Basic GFF, ERF, and NWSync implementations
- ✅ Resource manager with container hierarchy
- ✅ CLI framework with argument parsing
- ✅ GUI framework with tool selection and configuration
- ✅ NWSync write and print commands (basic implementation)
- 🔄 Complete file format implementations
- 🔄 All remaining CLI commands
- 🔄 Advanced NWSync features
- 🔄 Module file parsing
- 🔄 Script compilation
- 🔄 Full test suite

## Contributing

Contributions are welcome! This project reimplements the excellent work done in Neverwinter.nim. Please:

1. Follow the existing code style and patterns
2. Add tests for new functionality
3. Update documentation for any API changes
4. Ensure compatibility with the original Nim tools

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Neverwinter.nim](https://github.com/niv/neverwinter.nim) - The original toolkit this project reimplements
- The Neverwinter Nights Enhanced Edition community
- BioWare for creating the original game and file formats
