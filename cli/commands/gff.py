"""
GFF command implementation
"""

import sys
from pathlib import Path
import json
import logging

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.formats.gff import read_gff, write_gff, GffRoot

logger = logging.getLogger(__name__)


def gff_to_json(gff_root: GffRoot) -> dict:
    """Convert GFF structure to JSON-serializable dict"""
    result = {
        'file_type': gff_root.file_type,
        'file_version': gff_root.file_version,
        'fields': {}
    }
    
    # Convert fields to JSON format
    for field_name, field in gff_root.fields.items():
        result['fields'][field_name] = {
            'type': field.field_kind.name,
            'value': field.value
        }
    
    return result


def json_to_gff(json_data: dict) -> GffRoot:
    """Convert JSON dict to GFF structure"""
    gff_root = GffRoot(
        json_data.get('file_type', 'GFF '),
        json_data.get('file_version', 'V3.2')
    )
    
    # Convert fields from JSON format
    for field_name, field_data in json_data.get('fields', {}).items():
        gff_root[field_name] = field_data['value']
    
    return gff_root


def gff_convert(args):
    """Convert GFF files to/from JSON"""
    input_file = Path(args.input)
    
    if not input_file.exists():
        logger.error(f"Input file does not exist: {input_file}")
        return 1
    
    try:
        if args.to_json:
            # Convert GFF to JSON
            gff_root = read_gff(str(input_file))
            json_data = gff_to_json(gff_root)
            
            if args.output:
                output_file = Path(args.output)
            else:
                output_file = input_file.with_suffix('.json')
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Converted GFF to JSON: {output_file}")
            
        else:
            # Convert JSON to GFF
            with open(input_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            gff_root = json_to_gff(json_data)
            
            if args.output:
                output_file = Path(args.output)
            else:
                output_file = input_file.with_suffix('.gff')
            
            write_gff(gff_root, str(output_file))
            
            logger.info(f"Converted JSON to GFF: {output_file}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        return 1


def gff_info(args):
    """Display GFF file information"""
    input_file = Path(args.input)
    
    if not input_file.exists():
        logger.error(f"Input file does not exist: {input_file}")
        return 1
    
    try:
        gff_root = read_gff(str(input_file))
        
        print(f"File: {input_file}")
        print(f"Type: {gff_root.file_type.strip()}")
        print(f"Version: {gff_root.file_version}")
        print(f"Fields: {len(gff_root.fields)}")
        
        if args.verbose:
            print("\nFields:")
            for field_name, field in gff_root.fields.items():
                print(f"  {field_name}: {field.field_kind.name} = {field.value}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to read GFF: {e}")
        return 1


def setup_parser(parser):
    """Set up argument parser for gff command"""
    
    subcommands = parser.add_subparsers(dest='subcommand', help='GFF subcommands')
    
    # Convert subcommand
    convert_parser = subcommands.add_parser('convert', help='Convert GFF to/from JSON')
    convert_parser.add_argument('input', help='Input file')
    convert_parser.add_argument('-o', '--output', help='Output file')
    convert_parser.add_argument('--to-json', action='store_true',
                               help='Convert GFF to JSON (default: JSON to GFF)')
    convert_parser.set_defaults(func=gff_convert)
    
    # Info subcommand
    info_parser = subcommands.add_parser('info', help='Display GFF information')
    info_parser.add_argument('input', help='Input GFF file')
    info_parser.add_argument('-v', '--verbose', action='store_true',
                            help='Show detailed field information')
    info_parser.set_defaults(func=gff_info)
    
    # Default to convert if no subcommand
    parser.add_argument('input', nargs='?', help='Input file')
    parser.add_argument('-o', '--output', help='Output file')
    parser.add_argument('--to-json', action='store_true',
                       help='Convert GFF to JSON (default: JSON to GFF)')
    parser.set_defaults(func=gff_convert)
    
    return parser
