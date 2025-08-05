"""
ERF (Encapsulated Resource File) implementation
Based on neverwinter.nim/neverwinter/erf.nim
"""

import struct
import io
import time
from typing import Dict, List, Optional, BinaryIO
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# Common NWN resource types
RESOURCE_TYPES = {
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


class ErfVersion(Enum):
    """ERF file version"""
    V1 = "V1.0"
    E1 = "E1.0"  # Enhanced Edition


class ErfEntry:
    """Single entry in an ERF file"""
    
    def __init__(self, resref: str, res_type: int, data: bytes = b''):
        self.resref = resref
        self.res_type = res_type
        self.data = data
        self.offset = 0
        self.size = len(data)
        
    def __str__(self):
        return f"{self.resref}.{self.res_type} ({self.size} bytes)"


class Erf:
    """ERF archive container"""
    
    def __init__(self, file_type: str = "ERF", version: ErfVersion = ErfVersion.V1):
        self.file_type = file_type
        self.version = version
        self.entries: Dict[str, ErfEntry] = {}
        self.localized_strings: Dict[int, str] = {}
        self.description_str_ref = 0
        
    def add_entry(self, entry: ErfEntry):
        """Add an entry to the ERF"""
        key = f"{entry.resref}.{entry.res_type}"
        self.entries[key] = entry
        
    def get_entry(self, resref: str, res_type: int) -> Optional[ErfEntry]:
        """Get an entry by resref and type"""
        key = f"{resref}.{res_type}"
        return self.entries.get(key)
        
    def remove_entry(self, resref: str, res_type: int) -> bool:
        """Remove an entry"""
        key = f"{resref}.{res_type}"
        if key in self.entries:
            del self.entries[key]
            return True
        return False
        
    def list_entries(self) -> List[ErfEntry]:
        """Get all entries"""
        return list(self.entries.values())
        
    def __len__(self):
        return len(self.entries)
        
    def __contains__(self, key):
        if isinstance(key, tuple) and len(key) == 2:
            resref, res_type = key
            return f"{resref}.{res_type}" in self.entries
        return key in self.entries


class ErfReader:
    """ERF file reader"""
    
    def __init__(self, stream: BinaryIO):
        self.stream = stream
        
    def read(self) -> Erf:
        """Read ERF from stream"""
        # Read header
        file_type = self.stream.read(4).decode('ascii')
        version_str = self.stream.read(4).decode('ascii')
        
        version = ErfVersion.V1 if version_str == "V1.0" else ErfVersion.E1
        erf = Erf(file_type, version)
        
        # Read header fields
        header_data = struct.unpack('<LLLLLLLLLL', self.stream.read(40))
        (loc_string_count, loc_string_size, entry_count,
         offset_to_loc_strings, offset_to_key_list, offset_to_resource_list,
         build_year, build_day, description_str_ref, reserved) = header_data
         
        erf.description_str_ref = description_str_ref
        
        logger.debug(f"ERF Header: {file_type} {version_str}, "
                    f"{entry_count} entries, {loc_string_count} localized strings")
        
        # Skip remaining header padding
        if version == ErfVersion.V1:
            self.stream.read(116)  # Reserved space
        else:  # E1
            self.stream.read(92)   # Different padding for enhanced
            
        # Read localized strings
        if loc_string_count > 0:
            self._read_localized_strings(erf, offset_to_loc_strings, loc_string_count)
            
        # Read key list
        keys = self._read_key_list(offset_to_key_list, entry_count)
        
        # Read resource list
        resources = self._read_resource_list(offset_to_resource_list, entry_count)
        
        # Create entries
        for i in range(entry_count):
            key = keys[i]
            resource = resources[i]
            
            # Read the actual data
            self.stream.seek(resource['offset'])
            data = self.stream.read(resource['size'])
            
            entry = ErfEntry(key['resref'], key['res_type'], data)
            entry.offset = resource['offset']
            entry.size = resource['size']
            
            erf.add_entry(entry)
            
        return erf
        
    def _read_localized_strings(self, erf: Erf, offset: int, count: int):
        """Read localized strings"""
        self.stream.seek(offset)
        for _ in range(count):
            lang_id, string_size = struct.unpack('<LL', self.stream.read(8))
            string_data = self.stream.read(string_size).decode('utf-8', errors='ignore')
            erf.localized_strings[lang_id] = string_data
            
    def _read_key_list(self, offset: int, count: int) -> List[Dict]:
        """Read key list"""
        self.stream.seek(offset)
        keys = []
        for _ in range(count):
            resref = self.stream.read(16).rstrip(b'\x00').decode('ascii')
            res_id, res_type = struct.unpack('<LL', self.stream.read(8))
            keys.append({
                'resref': resref,
                'res_id': res_id,
                'res_type': res_type
            })
        return keys
        
    def _read_resource_list(self, offset: int, count: int) -> List[Dict]:
        """Read resource list"""
        self.stream.seek(offset)
        resources = []
        for _ in range(count):
            res_offset, res_size = struct.unpack('<LL', self.stream.read(8))
            resources.append({
                'offset': res_offset,
                'size': res_size
            })
        return resources


class ErfWriter:
    """ERF file writer"""
    
    def __init__(self, stream: BinaryIO):
        self.stream = stream
        
    def write(self, erf: Erf):
        """Write ERF to stream"""
        entries = list(erf.entries.values())
        entries.sort(key=lambda e: e.resref)  # Sort for reproducible builds
        
        # Calculate offsets
        header_size = 160  # Fixed header size
        loc_string_size = sum(len(s.encode('utf-8')) + 8 for s in erf.localized_strings.values())
        key_list_size = len(entries) * 24  # 16 + 4 + 4 per entry
        resource_list_size = len(entries) * 8  # 4 + 4 per entry
        
        offset_to_loc_strings = header_size
        offset_to_key_list = offset_to_loc_strings + loc_string_size
        offset_to_resource_list = offset_to_key_list + key_list_size
        data_offset = offset_to_resource_list + resource_list_size
        
        # Write header
        self.stream.write(erf.file_type.ljust(4)[:4].encode('ascii'))
        self.stream.write(erf.version.value.encode('ascii'))
        
        # Write header fields
        header_data = struct.pack('<LLLLLLLLLL',
            len(erf.localized_strings),    # loc_string_count
            loc_string_size,               # loc_string_size
            len(entries),                  # entry_count
            offset_to_loc_strings,         # offset_to_loc_strings
            offset_to_key_list,           # offset_to_key_list
            offset_to_resource_list,      # offset_to_resource_list
            time.gmtime().tm_year - 1900, # build_year
            time.gmtime().tm_yday,        # build_day
            erf.description_str_ref,      # description_str_ref
            0                             # reserved
        )
        self.stream.write(header_data)
        
        # Write padding based on version
        if erf.version == ErfVersion.V1:
            self.stream.write(b'\x00' * 116)
        else:  # E1
            self.stream.write(b'\x00' * 92)
            
        # Write localized strings
        for lang_id, string in erf.localized_strings.items():
            string_bytes = string.encode('utf-8')
            self.stream.write(struct.pack('<LL', lang_id, len(string_bytes)))
            self.stream.write(string_bytes)
            
        # Write key list
        for entry in entries:
            resref_bytes = entry.resref.encode('ascii')[:16].ljust(16, b'\x00')
            self.stream.write(resref_bytes)
            self.stream.write(struct.pack('<LL', 0, entry.res_type))  # res_id=0
            
        # Write resource list and calculate data offsets
        current_data_offset = data_offset
        for entry in entries:
            self.stream.write(struct.pack('<LL', current_data_offset, len(entry.data)))
            current_data_offset += len(entry.data)
            
        # Write actual data
        for entry in entries:
            self.stream.write(entry.data)
            
        logger.info(f"Wrote ERF with {len(entries)} entries")


def read_erf(file_path: str) -> Erf:
    """Read ERF file from path"""
    with open(file_path, 'rb') as f:
        reader = ErfReader(f)
        return reader.read()


def write_erf(erf: Erf, file_path: str):
    """Write ERF file to path"""
    with open(file_path, 'wb') as f:
        writer = ErfWriter(f)
        writer.write(erf)
