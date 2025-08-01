"""
NWSync implementation
Based on neverwinter.nim/neverwinter/nwsync.nim
"""

import struct
import hashlib
import json
import sqlite3
import os
import time
from typing import Dict, List, Optional, BinaryIO
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ManifestEntry:
    """Single entry in a NWSync manifest"""
    
    def __init__(self, resref: str, res_type: int, sha1: str, size: int):
        self.resref = resref
        self.res_type = res_type
        self.sha1 = sha1
        self.size = size
        
    def __str__(self):
        return f"{self.resref}.{self.res_type} ({self.size} bytes, {self.sha1})"
        
    def __lt__(self, other):
        """For sorting entries"""
        if not isinstance(other, ManifestEntry):
            return NotImplemented
        return (self.resref, self.res_type) < (other.resref, other.res_type)


class Manifest:
    """NWSync manifest"""
    
    def __init__(self):
        self.version = 3
        self.sha1 = ""
        self.hash_tree_depth = 2
        self.module_name = ""
        self.description = ""
        self.includes_module_contents = False
        self.includes_client_contents = True
        self.entries: List[ManifestEntry] = []
        self.created = int(time.time())
        self.created_with = "nwpy 1.0.0"
        self.group_id = 0
        
    def add_entry(self, entry: ManifestEntry):
        """Add an entry to the manifest"""
        self.entries.append(entry)
        
    def calculate_hash(self) -> str:
        """Calculate manifest SHA1 hash"""
        # Sort entries for reproducible hash
        sorted_entries = sorted(self.entries)
        
        # Create hash input
        hash_input = []
        for entry in sorted_entries:
            hash_input.append(f"{entry.resref}.{entry.res_type}:{entry.sha1}:{entry.size}")
            
        combined = "\n".join(hash_input).encode('utf-8')
        self.sha1 = hashlib.sha1(combined).hexdigest()
        return self.sha1
        
    def total_size(self) -> int:
        """Calculate total size of all entries"""
        return sum(entry.size for entry in self.entries)
        
    def total_files(self) -> int:
        """Get total number of files"""
        return len(self.entries)


class NWSyncRepository:
    """NWSync repository manager"""
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.manifests_path = self.root_path / "manifests"
        self.data_path = self.root_path / "data"
        self.meta_db_path = self.root_path / "nwsyncmeta.sqlite3"
        
        # Ensure directories exist
        self.manifests_path.mkdir(parents=True, exist_ok=True)
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize database if needed
        self._init_database()
        
    def _init_database(self):
        """Initialize the metadata database"""
        if not self.meta_db_path.exists():
            conn = sqlite3.connect(str(self.meta_db_path))
            conn.execute('''
                CREATE TABLE manifests (
                    sha1 TEXT PRIMARY KEY,
                    created INTEGER,
                    version INTEGER,
                    name TEXT,
                    description TEXT,
                    group_id INTEGER
                )
            ''')
            conn.execute('''
                CREATE TABLE shards (
                    id INTEGER PRIMARY KEY,
                    serial TEXT
                )
            ''')
            conn.commit()
            conn.close()
            
    def write_manifest(self, manifest: Manifest, limit_file_size: int = 32) -> str:
        """Write a manifest to the repository"""
        # Calculate hash first
        manifest_hash = manifest.calculate_hash()
        
        # Write binary manifest
        manifest_path = self.manifests_path / manifest_hash
        self._write_binary_manifest(manifest, manifest_path)
        
        # Write JSON metadata
        json_path = self.manifests_path / f"{manifest_hash}.json"
        self._write_json_manifest(manifest, json_path)
        
        # Update database
        self._update_database(manifest)
        
        # Update latest pointer
        self._update_latest(manifest_hash)
        
        logger.info(f"Wrote manifest {manifest_hash} with {len(manifest.entries)} entries")
        return manifest_hash
        
    def _write_binary_manifest(self, manifest: Manifest, path: Path):
        """Write binary manifest file"""
        with open(path, 'wb') as f:
            writer = ManifestWriter(f)
            writer.write(manifest)
            
    def _write_json_manifest(self, manifest: Manifest, path: Path):
        """Write JSON metadata file"""
        data = {
            "version": manifest.version,
            "sha1": manifest.sha1,
            "hash_tree_depth": manifest.hash_tree_depth,
            "module_name": manifest.module_name,
            "description": manifest.description,
            "includes_module_contents": manifest.includes_module_contents,
            "includes_client_contents": manifest.includes_client_contents,
            "total_files": manifest.total_files(),
            "total_bytes": manifest.total_size(),
            "on_disk_bytes": 0,  # Would need actual calculation
            "created": manifest.created,
            "created_with": manifest.created_with,
            "group_id": manifest.group_id
        }
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
            
    def _update_database(self, manifest: Manifest):
        """Update metadata database"""
        conn = sqlite3.connect(str(self.meta_db_path))
        conn.execute('''
            INSERT OR REPLACE INTO manifests 
            (sha1, created, version, name, description, group_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            manifest.sha1,
            manifest.created,
            manifest.version,
            manifest.module_name,
            manifest.description,
            manifest.group_id
        ))
        conn.commit()
        conn.close()
        
    def _update_latest(self, manifest_hash: str):
        """Update the latest pointer"""
        latest_path = self.root_path / "latest"
        with open(latest_path, 'w') as f:
            f.write(manifest_hash)
            
    def read_manifest(self, manifest_hash: str) -> Optional[Manifest]:
        """Read a manifest from the repository"""
        manifest_path = self.manifests_path / manifest_hash
        if not manifest_path.exists():
            return None
            
        with open(manifest_path, 'rb') as f:
            reader = ManifestReader(f)
            return reader.read()


class ManifestWriter:
    """Binary manifest writer"""
    
    def __init__(self, stream: BinaryIO):
        self.stream = stream
        
    def write(self, manifest: Manifest):
        """Write binary manifest"""
        # Magic header
        self.stream.write(b'NWSM')  # NWSync Manifest
        
        # Version
        self.stream.write(struct.pack('<I', manifest.version))
        
        # Entry count
        self.stream.write(struct.pack('<I', len(manifest.entries)))
        
        # Write entries
        for entry in sorted(manifest.entries):
            # ResRef (16 bytes, null-padded)
            resref_bytes = entry.resref.encode('ascii')[:16].ljust(16, b'\x00')
            self.stream.write(resref_bytes)
            
            # Resource type
            self.stream.write(struct.pack('<I', entry.res_type))
            
            # SHA1 (as bytes)
            sha1_bytes = bytes.fromhex(entry.sha1)
            self.stream.write(sha1_bytes)
            
            # Size
            self.stream.write(struct.pack('<I', entry.size))


class ManifestReader:
    """Binary manifest reader"""
    
    def __init__(self, stream: BinaryIO):
        self.stream = stream
        
    def read(self) -> Manifest:
        """Read binary manifest"""
        manifest = Manifest()
        
        # Check magic
        magic = self.stream.read(4)
        if magic != b'NWSM':
            raise ValueError("Invalid manifest magic")
            
        # Version
        manifest.version = struct.unpack('<I', self.stream.read(4))[0]
        
        # Entry count
        entry_count = struct.unpack('<I', self.stream.read(4))[0]
        
        # Read entries
        for _ in range(entry_count):
            # ResRef
            resref = self.stream.read(16).rstrip(b'\x00').decode('ascii')
            
            # Resource type
            res_type = struct.unpack('<I', self.stream.read(4))[0]
            
            # SHA1
            sha1_bytes = self.stream.read(20)
            sha1 = sha1_bytes.hex()
            
            # Size
            size = struct.unpack('<I', self.stream.read(4))[0]
            
            entry = ManifestEntry(resref, res_type, sha1, size)
            manifest.add_entry(entry)
            
        return manifest


def read_manifest(file_path: str) -> Manifest:
    """Read manifest from file"""
    with open(file_path, 'rb') as f:
        reader = ManifestReader(f)
        return reader.read()


def write_manifest(manifest: Manifest, file_path: str):
    """Write manifest to file"""
    with open(file_path, 'wb') as f:
        writer = ManifestWriter(f)
        writer.write(manifest)
