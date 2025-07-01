"""Data models for Canvas Editor"""

# Legacy models
from .project import ProjectFile, ProjectMetadata, ProjectSettings
from .component import Component as BaseComponent, ComponentStyle, ComponentCategory, ComponentTemplate

# Enhanced models for export system compatibility
from .component_enhanced import ExportCompatibleComponent, Component
from .project_enhanced import ExportCompatibleProject, Project, ProjectPage
from .asset import Asset, AssetMetadata, AssetProcessingResult

# Export enhanced models by default for new code
__all__ = [
    # Legacy models (for backward compatibility)
    'ProjectFile',
    'ProjectMetadata', 
    'ProjectSettings',
    'BaseComponent',
    'ComponentStyle',
    'ComponentCategory',
    'ComponentTemplate',
    
    # Enhanced models (for export system and new features)
    'Component',               # ExportCompatibleComponent
    'ExportCompatibleComponent',
    'Project',                 # ExportCompatibleProject
    'ExportCompatibleProject',
    'ProjectPage',
    'Asset',
    'AssetMetadata',
    'AssetProcessingResult'
]