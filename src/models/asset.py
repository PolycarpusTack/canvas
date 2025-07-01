"""
Asset Management Models for Export System

CLAUDE.md Implementation:
- #7.1: Secure file handling
- #2.1.1: Comprehensive validation
- #1.5: Performance optimization
"""

import mimetypes
import hashlib
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from pathlib import Path
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


@dataclass
class AssetMetadata:
    """Metadata for asset files with validation"""
    
    # Core identification
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    # File information
    original_filename: Optional[str] = None
    file_extension: Optional[str] = None
    mime_type: str = "application/octet-stream"
    size: int = 0
    checksum: Optional[str] = None
    
    # Asset type classification
    asset_type: str = "file"  # file, image, video, audio, font, document
    category: Optional[str] = None
    
    # Processing information
    is_optimized: bool = False
    optimization_applied: List[str] = field(default_factory=list)
    variants: List[Dict[str, Any]] = field(default_factory=list)
    
    # Usage tracking
    usage_count: int = 0
    last_used: Optional[str] = None
    
    def __post_init__(self):
        """Validate and process metadata after creation"""
        self._validate_metadata()
        self._classify_asset_type()
    
    def _validate_metadata(self):
        """
        Validate asset metadata
        
        CLAUDE.md #2.1.1: Comprehensive validation
        """
        if not self.id or not isinstance(self.id, str):
            raise ValueError("Asset ID must be a non-empty string")
        
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Asset name must be a non-empty string")
        
        if self.size < 0:
            raise ValueError("Asset size cannot be negative")
        
        # Validate MIME type format
        if self.mime_type and not self._is_valid_mime_type(self.mime_type):
            logger.warning(f"Invalid MIME type format: {self.mime_type}")
    
    def _is_valid_mime_type(self, mime_type: str) -> bool:
        """Validate MIME type format"""
        import re
        pattern = r'^[a-zA-Z0-9][a-zA-Z0-9!#$&\-\^_]*\/[a-zA-Z0-9][a-zA-Z0-9!#$&\-\^_.]*$'
        return bool(re.match(pattern, mime_type))
    
    def _classify_asset_type(self):
        """Automatically classify asset type based on MIME type"""
        if self.mime_type.startswith('image/'):
            self.asset_type = 'image'
        elif self.mime_type.startswith('video/'):
            self.asset_type = 'video'
        elif self.mime_type.startswith('audio/'):
            self.asset_type = 'audio'
        elif self.mime_type.startswith('font/') or self.mime_type in [
            'application/font-woff', 'application/font-woff2',
            'application/vnd.ms-fontobject', 'application/x-font-ttf'
        ]:
            self.asset_type = 'font'
        elif self.mime_type in [
            'application/pdf', 'text/plain', 'text/csv',
            'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]:
            self.asset_type = 'document'
        else:
            self.asset_type = 'file'


@dataclass
class Asset:
    """
    Complete asset representation with content and processing capabilities
    
    CLAUDE.md #7.1: Secure asset handling
    """
    
    # Core properties
    id: str = field(default_factory=lambda: str(uuid4()))
    path: Optional[Union[str, Path]] = None
    url: Optional[str] = None
    content: Optional[bytes] = None
    
    # Metadata
    metadata: AssetMetadata = field(default_factory=AssetMetadata)
    
    # Processing state
    is_loaded: bool = False
    is_processed: bool = False
    processing_error: Optional[str] = None
    
    # Export-specific properties
    export_path: Optional[str] = None
    relative_url: Optional[str] = None
    
    def __post_init__(self):
        """Initialize asset after creation"""
        if self.metadata.id != self.id:
            self.metadata.id = self.id
        
        if self.path:
            self._initialize_from_path()
    
    def _initialize_from_path(self):
        """Initialize asset metadata from file path"""
        if isinstance(self.path, str):
            self.path = Path(self.path)
        
        if not isinstance(self.path, Path):
            return
        
        # Validate path security
        self._validate_path_security()
        
        # Extract file information
        if self.path.exists():
            self.metadata.name = self.metadata.name or self.path.name
            self.metadata.original_filename = self.path.name
            self.metadata.file_extension = self.path.suffix
            self.metadata.size = self.path.stat().st_size
            
            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(str(self.path))
            if mime_type:
                self.metadata.mime_type = mime_type
    
    def _validate_path_security(self):
        """
        Validate file path for security
        
        CLAUDE.md #7.1: Path traversal prevention
        """
        if not self.path:
            return
        
        path_str = str(self.path)
        
        # Check for path traversal
        if '..' in path_str:
            raise ValueError("Path traversal detected in asset path")
        
        # Check for absolute paths outside allowed directories
        if self.path.is_absolute():
            # In production, validate against allowed directories
            pass
        
        # Validate file extension
        if self.metadata.file_extension:
            dangerous_extensions = {
                '.exe', '.bat', '.cmd', '.com', '.scr', '.pif',
                '.vbs', '.js', '.jar', '.app', '.deb', '.rpm'
            }
            if self.metadata.file_extension.lower() in dangerous_extensions:
                raise ValueError(f"Dangerous file extension: {self.metadata.file_extension}")
    
    async def load_content(self) -> bool:
        """
        Load asset content from file
        
        CLAUDE.md #7.2: Safe content loading
        """
        if self.is_loaded or not self.path:
            return self.is_loaded
        
        try:
            if isinstance(self.path, str):
                self.path = Path(self.path)
            
            if not self.path.exists():
                self.processing_error = f"Asset file does not exist: {self.path}"
                return False
            
            # Check file size limits (100MB)
            if self.metadata.size > 100 * 1024 * 1024:
                self.processing_error = f"Asset file too large: {self.metadata.size} bytes"
                return False
            
            # Load content
            with open(self.path, 'rb') as f:
                self.content = f.read()
            
            # Verify content matches expected size
            if len(self.content) != self.metadata.size:
                logger.warning(f"Asset size mismatch: expected {self.metadata.size}, got {len(self.content)}")
                self.metadata.size = len(self.content)
            
            # Calculate checksum
            self.metadata.checksum = hashlib.md5(self.content).hexdigest()
            
            self.is_loaded = True
            return True
            
        except Exception as e:
            self.processing_error = f"Failed to load asset: {e}"
            logger.error(self.processing_error)
            return False
    
    def get_content_as_data_url(self) -> Optional[str]:
        """Convert content to data URL for embedding"""
        if not self.is_loaded or not self.content:
            return None
        
        import base64
        
        try:
            encoded = base64.b64encode(self.content).decode('ascii')
            return f"data:{self.metadata.mime_type};base64,{encoded}"
        except Exception as e:
            logger.error(f"Failed to create data URL: {e}")
            return None
    
    def get_export_url(self, base_path: str = "assets") -> str:
        """Get URL for use in exported content"""
        if self.relative_url:
            return self.relative_url
        
        # Generate relative URL
        if self.metadata.name:
            filename = self.metadata.name
        elif self.metadata.original_filename:
            filename = self.metadata.original_filename
        else:
            extension = self.metadata.file_extension or ""
            filename = f"{self.id}{extension}"
        
        # Sanitize filename
        safe_filename = self._sanitize_filename(filename)
        self.relative_url = f"{base_path}/{safe_filename}"
        
        return self.relative_url
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for safe use in URLs
        
        CLAUDE.md #7.2: Output sanitization
        """
        import re
        
        # Remove or replace unsafe characters
        safe_filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
        safe_filename = re.sub(r'[^\w\-_.]', '_', safe_filename)
        safe_filename = re.sub(r'_{2,}', '_', safe_filename)  # Collapse multiple underscores
        
        # Ensure reasonable length
        if len(safe_filename) > 100:
            name, ext = safe_filename.rsplit('.', 1) if '.' in safe_filename else (safe_filename, '')
            safe_filename = f"{name[:95]}.{ext}" if ext else name[:100]
        
        return safe_filename
    
    def add_variant(self, variant_info: Dict[str, Any]):
        """Add a processed variant of this asset"""
        self.metadata.variants.append(variant_info)
    
    def get_variant(self, variant_type: str) -> Optional[Dict[str, Any]]:
        """Get specific variant by type"""
        for variant in self.metadata.variants:
            if variant.get('type') == variant_type:
                return variant
        return None
    
    def get_responsive_variants(self) -> List[Dict[str, Any]]:
        """Get all responsive image variants"""
        return [v for v in self.metadata.variants if v.get('responsive', False)]
    
    def mark_used(self):
        """Mark asset as used and update usage statistics"""
        from datetime import datetime
        self.metadata.usage_count += 1
        self.metadata.last_used = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'path': str(self.path) if self.path else None,
            'url': self.url,
            'metadata': {
                'id': self.metadata.id,
                'name': self.metadata.name,
                'description': self.metadata.description,
                'tags': self.metadata.tags,
                'original_filename': self.metadata.original_filename,
                'file_extension': self.metadata.file_extension,
                'mime_type': self.metadata.mime_type,
                'size': self.metadata.size,
                'checksum': self.metadata.checksum,
                'asset_type': self.metadata.asset_type,
                'category': self.metadata.category,
                'is_optimized': self.metadata.is_optimized,
                'optimization_applied': self.metadata.optimization_applied,
                'variants': self.metadata.variants,
                'usage_count': self.metadata.usage_count,
                'last_used': self.metadata.last_used
            },
            'is_loaded': self.is_loaded,
            'is_processed': self.is_processed,
            'processing_error': self.processing_error,
            'export_path': self.export_path,
            'relative_url': self.relative_url
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Asset':
        """Create asset from dictionary"""
        metadata_data = data.pop('metadata', {})
        
        asset = cls(**data)
        
        # Restore metadata
        if metadata_data:
            asset.metadata = AssetMetadata(**metadata_data)
        
        return asset
    
    @classmethod
    def from_file(cls, file_path: Union[str, Path], name: Optional[str] = None) -> 'Asset':
        """Create asset from file path"""
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        asset = cls(path=file_path)
        
        if name:
            asset.metadata.name = name
        
        return asset
    
    @classmethod
    def from_url(cls, url: str, name: Optional[str] = None) -> 'Asset':
        """Create asset from URL"""
        asset = cls(url=url)
        
        if name:
            asset.metadata.name = name
        else:
            # Extract name from URL
            from urllib.parse import urlparse
            parsed = urlparse(url)
            asset.metadata.name = Path(parsed.path).name or "unnamed_asset"
        
        return asset


@dataclass
class AssetProcessingResult:
    """Result of asset processing operations"""
    
    # Processing outcome
    success: bool = False
    original_path: str = ""
    processed_path: str = ""
    
    # Size information
    original_size: int = 0
    processed_size: int = 0
    compression_ratio: float = 0.0
    
    # Format information
    original_format: str = ""
    processed_format: str = ""
    
    # Processing details
    optimization_applied: bool = False
    processing_time: float = 0.0
    variants: List[Dict[str, Any]] = field(default_factory=list)
    
    # Error information
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    
    def calculate_metrics(self):
        """Calculate processing metrics"""
        if self.original_size > 0:
            savings = self.original_size - self.processed_size
            self.compression_ratio = savings / self.original_size
        else:
            self.compression_ratio = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'success': self.success,
            'original_path': self.original_path,
            'processed_path': self.processed_path,
            'original_size': self.original_size,
            'processed_size': self.processed_size,
            'compression_ratio': self.compression_ratio,
            'original_format': self.original_format,
            'processed_format': self.processed_format,
            'optimization_applied': self.optimization_applied,
            'processing_time': self.processing_time,
            'variants': self.variants,
            'error': self.error,
            'warnings': self.warnings
        }