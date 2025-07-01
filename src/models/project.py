"""Project-related data models with validation and security"""

import re
import uuid
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import mimetypes


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class ProjectSecurityError(Exception):
    """Custom exception for security violations"""
    pass


@dataclass
class ProjectFile:
    """Represents a file in the project with validation and security"""
    path: str
    relative_path: str
    size: int
    modified: str
    mime_type: str
    is_web_file: bool
    content: Optional[str] = None
    
    def __post_init__(self):
        """Validate file data after initialization (CLAUDE.md #2.1.1)"""
        self._validate_paths()
        self._validate_size()
        self._validate_mime_type()
        self._validate_timestamps()
    
    def _validate_paths(self) -> None:
        """Validate file paths for security (CLAUDE.md #7.1)"""
        if not self.path or not isinstance(self.path, str):
            raise ValidationError("File path is required and must be a string")
        
        if not self.relative_path or not isinstance(self.relative_path, str):
            raise ValidationError("Relative path is required and must be a string")
        
        # Prevent path traversal attacks
        if ".." in self.path or ".." in self.relative_path:
            raise ProjectSecurityError("Path traversal detected in file paths")
        
        # Validate path format
        try:
            Path(self.path)
            Path(self.relative_path)
        except Exception as e:
            raise ValidationError(f"Invalid path format: {e}")
    
    def _validate_size(self) -> None:
        """Validate file size"""
        if not isinstance(self.size, int) or self.size < 0:
            raise ValidationError("File size must be a non-negative integer")
        
        # Warn about large files (100MB)
        if self.size > 100 * 1024 * 1024:
            import logging
            logging.warning(f"Large file detected: {self.path} ({self.size} bytes)")
    
    def _validate_mime_type(self) -> None:
        """Validate MIME type format"""
        if not isinstance(self.mime_type, str):
            raise ValidationError("MIME type must be a string")
        
        # Basic MIME type format validation
        if self.mime_type and not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9!#$&\-\^_]*\/[a-zA-Z0-9][a-zA-Z0-9!#$&\-\^_.]*$', self.mime_type):
            raise ValidationError(f"Invalid MIME type format: {self.mime_type}")
    
    def _validate_timestamps(self) -> None:
        """Validate timestamp format"""
        if not isinstance(self.modified, str):
            raise ValidationError("Modified timestamp must be a string")
        
        try:
            datetime.fromisoformat(self.modified.replace('Z', '+00:00'))
        except ValueError as e:
            raise ValidationError(f"Invalid timestamp format: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectFile':
        """Create from dictionary with validation"""
        if not isinstance(data, dict):
            raise ValidationError("Data must be a dictionary")
        
        try:
            return cls(**data)
        except TypeError as e:
            raise ValidationError(f"Invalid data structure: {e}")
    
    def is_safe_content(self) -> bool:
        """Check if file content is safe to load (CLAUDE.md #7.2)"""
        if not self.content:
            return True
        
        # Basic content safety checks
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'data:text/html',
            r'eval\s*\(',
            r'Function\s*\('
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, self.content, re.IGNORECASE | re.DOTALL):
                return False
        
        return True


@dataclass
class ProjectMetadata:
    """Project metadata structure with comprehensive validation"""
    id: str
    name: str
    path: str
    created: str
    modified: str
    description: str
    version: str
    files_count: int
    main_file: Optional[str] = None
    framework: Optional[str] = None
    tags: Optional[List[str]] = None
    settings: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate metadata after initialization (CLAUDE.md #2.1.1)"""
        self._validate_id()
        self._validate_name()
        self._validate_path()
        self._validate_timestamps()
        self._validate_version()
        self._validate_files_count()
        self._validate_framework()
        self._validate_tags()
        self._sanitize_description()
    
    def _validate_id(self) -> None:
        """Validate project ID format"""
        if not self.id or not isinstance(self.id, str):
            raise ValidationError("Project ID is required and must be a string")
        
        # Validate UUID format
        try:
            uuid.UUID(self.id)
        except ValueError:
            raise ValidationError(f"Project ID must be a valid UUID: {self.id}")
    
    def _validate_name(self) -> None:
        """Validate and sanitize project name (CLAUDE.md #7.2)"""
        if not self.name or not isinstance(self.name, str):
            raise ValidationError("Project name is required and must be a string")
        
        # Remove leading/trailing whitespace
        self.name = self.name.strip()
        
        if not self.name:
            raise ValidationError("Project name cannot be empty")
        
        if len(self.name) > 100:
            raise ValidationError("Project name cannot exceed 100 characters")
        
        # Check for dangerous characters
        if re.search(r'[<>:"/\\|?*\x00-\x1f]', self.name):
            raise ValidationError("Project name contains invalid characters")
    
    def _validate_path(self) -> None:
        """Validate project path for security (CLAUDE.md #7.1)"""
        if not self.path or not isinstance(self.path, str):
            raise ValidationError("Project path is required and must be a string")
        
        # Prevent path traversal
        if ".." in self.path:
            raise ProjectSecurityError("Path traversal detected in project path")
        
        # Validate path format
        try:
            path_obj = Path(self.path)
            if not path_obj.is_absolute():
                raise ValidationError("Project path must be absolute")
        except Exception as e:
            raise ValidationError(f"Invalid path format: {e}")
    
    def _validate_timestamps(self) -> None:
        """Validate timestamp formats"""
        for field_name, timestamp in [("created", self.created), ("modified", self.modified)]:
            if not isinstance(timestamp, str):
                raise ValidationError(f"{field_name} timestamp must be a string")
            
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                # Ensure timestamp is not in the future
                if dt > datetime.now():
                    raise ValidationError(f"{field_name} timestamp cannot be in the future")
            except ValueError as e:
                raise ValidationError(f"Invalid {field_name} timestamp format: {e}")
    
    def _validate_version(self) -> None:
        """Validate version format"""
        if not isinstance(self.version, str):
            raise ValidationError("Version must be a string")
        
        # Basic semantic version validation
        if not re.match(r'^\d+\.\d+\.\d+([.-]\w+)*$', self.version):
            raise ValidationError(f"Invalid version format: {self.version}")
    
    def _validate_files_count(self) -> None:
        """Validate files count"""
        if not isinstance(self.files_count, int) or self.files_count < 0:
            raise ValidationError("Files count must be a non-negative integer")
    
    def _validate_framework(self) -> None:
        """Validate framework name"""
        if self.framework is not None:
            if not isinstance(self.framework, str):
                raise ValidationError("Framework must be a string")
            
            # Whitelist of supported frameworks
            supported_frameworks = {"React", "Vue", "Angular", "Svelte", "HTML", "Vanilla"}
            if self.framework not in supported_frameworks:
                import logging
                logging.warning(f"Unknown framework: {self.framework}")
    
    def _validate_tags(self) -> None:
        """Validate tags list"""
        if self.tags is not None:
            if not isinstance(self.tags, list):
                raise ValidationError("Tags must be a list")
            
            for i, tag in enumerate(self.tags):
                if not isinstance(tag, str):
                    raise ValidationError(f"Tag {i} must be a string")
                
                if len(tag.strip()) == 0:
                    raise ValidationError(f"Tag {i} cannot be empty")
                
                if len(tag) > 50:
                    raise ValidationError(f"Tag {i} cannot exceed 50 characters")
    
    def _sanitize_description(self) -> None:
        """Sanitize description content (CLAUDE.md #7.2)"""
        if self.description:
            # Remove potentially dangerous HTML/script content
            self.description = re.sub(r'<script[^>]*>.*?</script>', '', self.description, flags=re.IGNORECASE | re.DOTALL)
            self.description = re.sub(r'<[^>]+>', '', self.description)  # Remove all HTML tags
            
            # Limit description length
            if len(self.description) > 1000:
                self.description = self.description[:1000] + "..."
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectMetadata':
        """Create from dictionary with validation"""
        if not isinstance(data, dict):
            raise ValidationError("Data must be a dictionary")
        
        try:
            return cls(**data)
        except TypeError as e:
            raise ValidationError(f"Invalid data structure: {e}")
    
    def update_modified(self) -> None:
        """Update the modified timestamp with validation"""
        self.modified = datetime.now().isoformat()
    
    def is_valid_project_structure(self) -> bool:
        """Check if project has valid structure"""
        try:
            project_path = Path(self.path)
            return project_path.exists() and project_path.is_dir()
        except Exception:
            return False
    
    def get_safe_name(self) -> str:
        """Get filesystem-safe project name"""
        # Replace unsafe characters with underscores
        safe_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', self.name)
        return safe_name.strip('_')[:100]  # Limit length and trim underscores


@dataclass
class ProjectSettings:
    """Project-specific settings with validation"""
    auto_save: bool = True
    auto_save_interval: int = 300
    theme: str = "light"
    show_grid: bool = False
    snap_to_grid: bool = False
    grid_size: int = 20
    default_device: str = "desktop"
    enable_collaboration: bool = False
    
    def __post_init__(self):
        """Validate settings after initialization (CLAUDE.md #2.1.1)"""
        self._validate_auto_save_interval()
        self._validate_theme()
        self._validate_grid_size()
        self._validate_default_device()
    
    def _validate_auto_save_interval(self) -> None:
        """Validate auto-save interval"""
        if not isinstance(self.auto_save_interval, int):
            raise ValidationError("Auto-save interval must be an integer")
        
        if self.auto_save_interval < 30:
            raise ValidationError("Auto-save interval cannot be less than 30 seconds")
        
        if self.auto_save_interval > 3600:
            raise ValidationError("Auto-save interval cannot exceed 1 hour")
    
    def _validate_theme(self) -> None:
        """Validate theme setting"""
        if not isinstance(self.theme, str):
            raise ValidationError("Theme must be a string")
        
        valid_themes = {"light", "dark", "auto"}
        if self.theme not in valid_themes:
            raise ValidationError(f"Invalid theme: {self.theme}. Must be one of {valid_themes}")
    
    def _validate_grid_size(self) -> None:
        """Validate grid size"""
        if not isinstance(self.grid_size, int):
            raise ValidationError("Grid size must be an integer")
        
        if self.grid_size < 1 or self.grid_size > 100:
            raise ValidationError("Grid size must be between 1 and 100 pixels")
    
    def _validate_default_device(self) -> None:
        """Validate default device"""
        if not isinstance(self.default_device, str):
            raise ValidationError("Default device must be a string")
        
        valid_devices = {"desktop", "laptop", "tablet", "mobile"}
        if self.default_device not in valid_devices:
            raise ValidationError(f"Invalid default device: {self.default_device}. Must be one of {valid_devices}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectSettings':
        """Create from dictionary with validation"""
        if not isinstance(data, dict):
            raise ValidationError("Data must be a dictionary")
        
        try:
            return cls(**data)
        except TypeError as e:
            raise ValidationError(f"Invalid settings data structure: {e}")
    
    def update_auto_save_interval(self, interval: int) -> None:
        """Safely update auto-save interval with validation"""
        old_interval = self.auto_save_interval
        self.auto_save_interval = interval
        try:
            self._validate_auto_save_interval()
        except ValidationError:
            self.auto_save_interval = old_interval  # Rollback
            raise