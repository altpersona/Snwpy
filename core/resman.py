"""
Resource Manager implementation
Based on neverwinter.nim resman functionality
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union, BinaryIO
from abc import ABC, abstractmethod
import logging

from .formats import Erf, read_erf
from .nwsync import NWSyncRepository, read_manifest

logger = logging.getLogger(__name__)


class ResRef:
    """Resource reference (filename + type)"""
    
    def __init__(self, name: str, res_type: int):
        self.name = name.lower()  # Case insensitive
        self.res_type = res_type
        
    def __str__(self):
        return f"{self.name}.{self.res_type}"
        
    def __eq__(self, other):
        if not isinstance(other, ResRef):
            return False
        return self.name == other.name and self.res_type == other.res_type
        
    def __hash__(self):
        return hash((self.name, self.res_type))
        
    @classmethod
    def from_filename(cls, filename: str, default_type: int = 0):
        """Create ResRef from filename"""
        if '.' in filename:
            name, ext = filename.rsplit('.', 1)
            # Map common extensions to types (simplified)
            ext_map = {
                'are': 2012, 'gic': 2013, 'git': 2014, 'gff': 2021,
                'fac': 2022, 'ifo': 2023, 'bic': 2025, 'dlg': 2029,
                'itp': 2030, 'bmp': 1, 'dds': 1, 'tga': 3, 'wav': 4,
                'plt': 6, 'ini': 7, 'txt': 10, 'mdl': 2002, 'nss': 2009,
                'ncs': 2010, 'utc': 2027, 'utd': 2028, 'ute': 2032,
                'uti': 2033, 'utm': 2035, 'utp': 2042, 'uts': 2043,
                'utt': 2044, 'utw': 2058
            }
            res_type = ext_map.get(ext.lower(), default_type)
            return cls(name, res_type)
        return cls(filename, default_type)


class ResContainer(ABC):
    """Abstract base class for resource containers"""
    
    @abstractmethod
    def contains(self, resref: ResRef) -> bool:
        """Check if container has the resource"""
        pass
        
    @abstractmethod
    def get_data(self, resref: ResRef) -> Optional[bytes]:
        """Get resource data"""
        pass
        
    @abstractmethod
    def list_resources(self) -> List[ResRef]:
        """List all resources in container"""
        pass


class ResDir(ResContainer):
    """Directory-based resource container"""
    
    def __init__(self, path: str):
        self.path = Path(path)
        self._cache: Optional[Dict[ResRef, Path]] = None
        self._build_cache()
        
    def _build_cache(self):
        """Build cache of available resources"""
        self._cache = {}
        if not self.path.exists():
            logger.warning(f"ResDir path does not exist: {self.path}")
            return
            
        for file_path in self.path.rglob('*'):
            if file_path.is_file():
                resref = ResRef.from_filename(file_path.name)
                self._cache[resref] = file_path
                
        logger.debug(f"ResDir loaded {len(self._cache)} resources from {self.path}")
        
    def contains(self, resref: ResRef) -> bool:
        return resref in self._cache
        
    def get_data(self, resref: ResRef) -> Optional[bytes]:
        if resref not in self._cache:
            return None
        try:
            with open(self._cache[resref], 'rb') as f:
                return f.read()
        except IOError as e:
            logger.error(f"Failed to read {resref}: {e}")
            return None
            
    def list_resources(self) -> List[ResRef]:
        return list(self._cache.keys())


class ResErf(ResContainer):
    """ERF-based resource container"""
    
    def __init__(self, erf: Erf):
        self.erf = erf
        
    @classmethod
    def from_file(cls, file_path: str):
        """Create from ERF file"""
        erf = read_erf(file_path)
        return cls(erf)
        
    def contains(self, resref: ResRef) -> bool:
        return (resref.name, resref.res_type) in self.erf
        
    def get_data(self, resref: ResRef) -> Optional[bytes]:
        entry = self.erf.get_entry(resref.name, resref.res_type)
        return entry.data if entry else None
        
    def list_resources(self) -> List[ResRef]:
        resources = []
        for entry in self.erf.list_entries():
            resources.append(ResRef(entry.resref, entry.res_type))
        return resources


class ResNWSync(ResContainer):
    """NWSync manifest-based resource container"""
    
    def __init__(self, repository: NWSyncRepository, manifest_hash: str):
        self.repository = repository
        self.manifest_hash = manifest_hash
        self.manifest = repository.read_manifest(manifest_hash)
        if not self.manifest:
            raise ValueError(f"Manifest not found: {manifest_hash}")
            
    def contains(self, resref: ResRef) -> bool:
        for entry in self.manifest.entries:
            if entry.resref == resref.name and entry.res_type == resref.res_type:
                return True
        return False
        
    def get_data(self, resref: ResRef) -> Optional[bytes]:
        # This would need to implement actual data retrieval from NWSync
        # For now, return None as placeholder
        logger.warning("NWSync data retrieval not yet implemented")
        return None
        
    def list_resources(self) -> List[ResRef]:
        resources = []
        for entry in self.manifest.entries:
            resources.append(ResRef(entry.resref, entry.res_type))
        return resources


class ResMan:
    """Resource Manager - combines multiple containers with priority"""
    
    def __init__(self, cache_size: int = 1000):
        self.containers: List[ResContainer] = []
        self.cache_size = cache_size
        self._cache: Dict[ResRef, bytes] = {}
        
    def add_container(self, container: ResContainer):
        """Add a resource container (higher priority containers should be added last)"""
        self.containers.append(container)
        logger.debug(f"Added container: {type(container).__name__}")
        
    def add_directory(self, path: str):
        """Add a directory as a resource container"""
        self.add_container(ResDir(path))
        
    def add_erf(self, file_path: str):
        """Add an ERF file as a resource container"""
        self.add_container(ResErf.from_file(file_path))
        
    def add_nwsync(self, repository_path: str, manifest_hash: str):
        """Add a NWSync manifest as a resource container"""
        repo = NWSyncRepository(repository_path)
        self.add_container(ResNWSync(repo, manifest_hash))
        
    def contains(self, resref: ResRef) -> bool:
        """Check if any container has the resource"""
        for container in reversed(self.containers):  # Check highest priority first
            if container.contains(resref):
                return True
        return False
        
    def get_data(self, resref: ResRef) -> Optional[bytes]:
        """Get resource data from highest priority container"""
        # Check cache first
        if resref in self._cache:
            return self._cache[resref]
            
        # Check containers in reverse order (highest priority first)
        for container in reversed(self.containers):
            if container.contains(resref):
                data = container.get_data(resref)
                if data is not None:
                    # Cache the result
                    if len(self._cache) >= self.cache_size:
                        # Simple cache eviction (remove oldest)
                        oldest_key = next(iter(self._cache))
                        del self._cache[oldest_key]
                    self._cache[resref] = data
                    return data
                    
        return None
        
    def list_all_resources(self) -> List[ResRef]:
        """List all resources from all containers"""
        all_resources = set()
        for container in self.containers:
            all_resources.update(container.list_resources())
        return list(all_resources)
        
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about the resource manager"""
        stats = {
            'containers': len(self.containers),
            'cached_resources': len(self._cache),
            'total_resources': len(self.list_all_resources())
        }
        return stats
        
    def grep(self, pattern: str, case_sensitive: bool = False) -> List[ResRef]:
        """Find resources matching a pattern"""
        import re
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)
        
        matches = []
        for resref in self.list_all_resources():
            if regex.search(str(resref)):
                matches.append(resref)
                
        return matches
        
    def extract_to_directory(self, output_dir: str, pattern: str = "*"):
        """Extract resources to a directory"""
        import fnmatch
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        extracted = 0
        for resref in self.list_all_resources():
            if fnmatch.fnmatch(str(resref), pattern):
                data = self.get_data(resref)
                if data:
                    file_path = output_path / str(resref)
                    with open(file_path, 'wb') as f:
                        f.write(data)
                    extracted += 1
                    
        logger.info(f"Extracted {extracted} resources to {output_dir}")
        return extracted
