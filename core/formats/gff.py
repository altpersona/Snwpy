"""
GFF (Game Format File) implementation
Based on neverwinter.nim/neverwinter/gff.nim
"""

import struct
import io
from typing import Dict, List, Any, Union, Optional
from enum import IntEnum
import logging

logger = logging.getLogger(__name__)


class GffFieldKind(IntEnum):
    """GFF field type enumeration"""
    BYTE = 0
    CHAR = 1
    WORD = 2
    SHORT = 3
    DWORD = 4
    INT = 5
    DWORD64 = 6
    INT64 = 7
    FLOAT = 8
    DOUBLE = 9
    CEXOSTRING = 10
    RESREF = 11
    CEXOLOCSTRING = 12
    VOID = 13
    STRUCT = 14
    LIST = 15


class GffField:
    """Represents a single GFF field"""
    
    def __init__(self, field_kind: GffFieldKind, value: Any = None):
        self.field_kind = field_kind
        self.value = value
        self.data_or_offset = 0
        
    def get_value(self, expected_type=None):
        """Get the field value, optionally checking type"""
        if expected_type and not isinstance(self.value, expected_type):
            raise TypeError(f"Expected {expected_type}, got {type(self.value)}")
        return self.value
        
    def set_value(self, value: Any):
        """Set the field value"""
        self.value = value


class GffStruct:
    """Represents a GFF structure"""
    
    def __init__(self, struct_id: int = -1):
        self.id = struct_id
        self.fields: Dict[str, GffField] = {}
        
    def __getitem__(self, key: str) -> GffField:
        return self.fields[key]
        
    def __setitem__(self, key: str, value: Union[GffField, Any]):
        if isinstance(value, GffField):
            self.fields[key] = value
        else:
            # Auto-detect field type based on value
            field_kind = self._detect_field_kind(value)
            self.fields[key] = GffField(field_kind, value)
            
    def __contains__(self, key: str) -> bool:
        return key in self.fields
        
    def get(self, key: str, default=None):
        """Get field value or default"""
        if key in self.fields:
            return self.fields[key].get_value()
        return default
        
    def _detect_field_kind(self, value: Any) -> GffFieldKind:
        """Auto-detect GFF field kind from Python value"""
        if isinstance(value, bool):
            return GffFieldKind.BYTE
        elif isinstance(value, int):
            if -128 <= value <= 127:
                return GffFieldKind.CHAR
            elif 0 <= value <= 255:
                return GffFieldKind.BYTE
            elif -32768 <= value <= 32767:
                return GffFieldKind.SHORT
            elif 0 <= value <= 65535:
                return GffFieldKind.WORD
            elif -2147483648 <= value <= 2147483647:
                return GffFieldKind.INT
            elif 0 <= value <= 4294967295:
                return GffFieldKind.DWORD
            else:
                return GffFieldKind.INT64
        elif isinstance(value, float):
            return GffFieldKind.FLOAT
        elif isinstance(value, str):
            if len(value) <= 16:
                return GffFieldKind.RESREF
            else:
                return GffFieldKind.CEXOSTRING
        elif isinstance(value, list):
            return GffFieldKind.LIST
        elif isinstance(value, dict):
            return GffFieldKind.STRUCT
        else:
            return GffFieldKind.VOID


class GffRoot(GffStruct):
    """Root GFF structure"""
    
    def __init__(self, file_type: str = "GFF ", file_version: str = "V3.2"):
        super().__init__()
        self.file_type = file_type
        self.file_version = file_version


class GffReader:
    """GFF file reader"""
    
    def __init__(self, stream: io.IOBase):
        self.stream = stream
        
    def read(self) -> GffRoot:
        """Read GFF from stream"""
        # Read header
        file_type = self.stream.read(4).decode('ascii')
        file_version = self.stream.read(4).decode('ascii')
        
        # Read header data
        header_data = struct.unpack('<LLLLLLLL', self.stream.read(32))
        (struct_offset, struct_count, field_offset, field_count,
         label_offset, label_count, field_data_offset, field_data_count) = header_data
         
        logger.debug(f"GFF Header: {file_type}{file_version}, "
                    f"{struct_count} structs, {field_count} fields")
        
        # Create root structure
        root = GffRoot(file_type, file_version)
        
        # Read structures, fields, labels, and field data
        structs = self._read_structs(struct_offset, struct_count)
        fields = self._read_fields(field_offset, field_count)
        labels = self._read_labels(label_offset, label_count)
        
        # Build the structure hierarchy
        self._build_structure(root, structs, fields, labels, field_data_offset)
        
        return root
        
    def _read_structs(self, offset: int, count: int) -> List:
        """Read structure entries"""
        self.stream.seek(offset)
        structs = []
        for _ in range(count):
            struct_data = struct.unpack('<LLL', self.stream.read(12))
            structs.append(struct_data)
        return structs
        
    def _read_fields(self, offset: int, count: int) -> List:
        """Read field entries"""
        self.stream.seek(offset)
        fields = []
        for _ in range(count):
            field_data = struct.unpack('<LLL', self.stream.read(12))
            fields.append(field_data)
        return fields
        
    def _read_labels(self, offset: int, count: int) -> List[str]:
        """Read label strings"""
        self.stream.seek(offset)
        labels = []
        for _ in range(count):
            label = self.stream.read(16).rstrip(b'\x00').decode('ascii')
            labels.append(label)
        return labels
        
    def _build_structure(self, root: GffRoot, structs, fields, labels, field_data_offset):
        """Build the complete structure hierarchy"""
        # Implementation would continue here with full structure building
        # For now, this is a basic framework
        pass


class GffWriter:
    """GFF file writer"""
    
    def __init__(self, stream: io.IOBase):
        self.stream = stream
        
    def write(self, root: GffRoot):
        """Write GFF to stream"""
        # Write header
        self.stream.write(root.file_type.encode('ascii'))
        self.stream.write(root.file_version.encode('ascii'))
        
        # This would continue with full implementation
        # For now, basic framework
        logger.info(f"Writing GFF {root.file_type}{root.file_version}")


def read_gff(file_path: str) -> GffRoot:
    """Read GFF file from path"""
    with open(file_path, 'rb') as f:
        reader = GffReader(f)
        return reader.read()


def write_gff(root: GffRoot, file_path: str):
    """Write GFF file to path"""
    with open(file_path, 'wb') as f:
        writer = GffWriter(f)
        writer.write(root)
