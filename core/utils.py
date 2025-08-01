"""
Error handling and validation utilities
"""

import logging
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)


class NWPYError(Exception):
    """Base exception for NWPY errors"""
    pass


class FileNotFoundError(NWPYError):
    """File not found error"""
    pass


class InvalidFormatError(NWPYError):
    """Invalid file format error"""
    pass


class ValidationError(NWPYError):
    """Validation error"""
    pass


def validate_file_exists(file_path: str) -> Path:
    """Validate that a file exists and return Path object"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if not path.is_file():
        raise ValidationError(f"Path is not a file: {file_path}")
    return path


def validate_directory_exists(dir_path: str) -> Path:
    """Validate that a directory exists and return Path object"""
    path = Path(dir_path)
    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    if not path.is_dir():
        raise ValidationError(f"Path is not a directory: {dir_path}")
    return path


def ensure_directory(dir_path: str) -> Path:
    """Ensure directory exists, create if necessary"""
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_execute(func, *args, **kwargs):
    """Safely execute a function with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        raise


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(size_bytes)
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)}{units[unit_index]}"
    else:
        return f"{size:.1f}{units[unit_index]}"


def get_resource_type_from_extension(extension: str) -> int:
    """Get NWN resource type from file extension"""
    ext_map = {
        'bmp': 1, 'tga': 3, 'wav': 4, 'plt': 6, 'ini': 7, 'txt': 10,
        'mdl': 2002, 'nss': 2009, 'ncs': 2010, 'are': 2012, 'set': 2013,
        'ifo': 2014, 'bic': 2015, 'wok': 2016, 'utc': 2017, 'utd': 2018,
        'ute': 2019, 'utg': 2020, 'uti': 2021, 'utm': 2022, 'utp': 2023,
        'uts': 2024, 'utt': 2025, 'utw': 2026, 'git': 2027, 'gic': 2028,
        'gff': 2037, 'fac': 2038, 'dlg': 2029, 'itp': 2030, 'bak': 2031,
        'dat': 2032, 'shd': 2033, 'xbc': 2034, 'wbm': 2035, 'mtr': 2036,
        'ktx': 2040, 'ttf': 2041, 'sql': 2042, 'tml': 2043, 'sq3': 2044,
        'lod': 2045, 'gif': 2046, 'png': 2047, 'jpg': 2048, 'caf': 2049,
        'jui': 9996, 'gui': 9997, 'css': 9998, 'ccs': 9999, 'xml': 10000,
        'htm': 10001, 'ltr': 10002, 'json': 10004
    }
    return ext_map.get(extension.lower().lstrip('.'), 2037)  # Default to GFF


def get_extension_from_resource_type(res_type: int) -> str:
    """Get file extension from NWN resource type"""
    type_map = {
        1: 'bmp', 3: 'tga', 4: 'wav', 6: 'plt', 7: 'ini', 10: 'txt',
        2002: 'mdl', 2009: 'nss', 2010: 'ncs', 2012: 'are', 2013: 'set',
        2014: 'ifo', 2015: 'bic', 2016: 'wok', 2017: 'utc', 2018: 'utd',
        2019: 'ute', 2020: 'utg', 2021: 'uti', 2022: 'utm', 2023: 'utp',
        2024: 'uts', 2025: 'utt', 2026: 'utw', 2027: 'git', 2028: 'gic',
        2029: 'dlg', 2030: 'itp', 2031: 'bak', 2032: 'dat', 2033: 'shd',
        2034: 'xbc', 2035: 'wbm', 2036: 'mtr', 2037: 'gff', 2038: 'fac',
        2040: 'ktx', 2041: 'ttf', 2042: 'sql', 2043: 'tml', 2044: 'sq3',
        2045: 'lod', 2046: 'gif', 2047: 'png', 2048: 'jpg', 2049: 'caf',
        9996: 'jui', 9997: 'gui', 9998: 'css', 9999: 'ccs', 10000: 'xml',
        10001: 'htm', 10002: 'ltr', 10004: 'json'
    }
    return type_map.get(res_type, f'res{res_type}')
