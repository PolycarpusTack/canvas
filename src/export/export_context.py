"""
Export Context

CLAUDE.md Implementation:
- #6.1: Clear context ownership
- #4.1: Explicit types for all fields
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Set

from ..models.project_enhanced import Project
from ..models.component_enhanced import Component
from .export_config import ExportConfig


@dataclass
class ExportContext:
    """
    Context object containing all data needed for export
    
    CLAUDE.md #6.1: Clear data ownership
    """
    # Core data
    project: Project
    config: ExportConfig
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Processed data
    component_tree: Dict[str, Any] = field(default_factory=dict)
    reusable_components: List[Component] = field(default_factory=list)
    asset_map: Dict[str, Any] = field(default_factory=dict)
    
    # Responsive data
    breakpoints: List[int] = field(default_factory=list)
    
    # Routing data
    routes: Dict[str, Any] = field(default_factory=dict)
    
    # Export metadata
    export_id: str = field(default_factory=lambda: f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    warnings: List[str] = field(default_factory=list)
    
    # Performance metrics
    component_count: int = 0
    asset_count: int = 0
    total_size: int = 0
    
    def __post_init__(self):
        """Initialize computed fields"""
        if self.project:
            self.component_count = len(self.project.components)
            self.asset_count = len(getattr(self.project, 'assets', []))
    
    def add_warning(self, warning: str):
        """Add export warning"""
        self.warnings.append(warning)
    
    def get_components_by_type(self, component_type: str) -> List[Component]:
        """Get all components of a specific type"""
        return [
            comp for comp in self.project.components
            if comp.type == component_type
        ]
    
    def get_component_by_id(self, component_id: str) -> Optional[Component]:
        """Get component by ID"""
        for comp in self.project.components:
            if comp.id == component_id:
                return comp
        return None
    
    def get_image_assets(self, asset_id: str) -> List[Any]:
        """Get processed image assets for responsive images"""
        # This would return different sizes/formats of the same image
        if asset_id in self.asset_map:
            asset = self.asset_map[asset_id]
            if hasattr(asset, 'variants'):
                return asset.variants
        return []
    
    def has_responsive_components(self) -> bool:
        """Check if project has responsive components"""
        return any(
            hasattr(comp, 'responsive_styles') and comp.responsive_styles
            for comp in self.project.components
        )
    
    def get_used_fonts(self) -> Set[str]:
        """Get all fonts used in the project"""
        fonts = set()
        for comp in self.project.components:
            if hasattr(comp, 'styles') and 'fontFamily' in comp.styles:
                fonts.add(comp.styles['fontFamily'])
        return fonts
    
    def get_used_colors(self) -> Set[str]:
        """Get all colors used in the project"""
        colors = set()
        for comp in self.project.components:
            if hasattr(comp, 'styles'):
                for prop, value in comp.styles.items():
                    if 'color' in prop.lower() and isinstance(value, str):
                        colors.add(value)
        return colors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'export_id': self.export_id,
            'timestamp': self.timestamp.isoformat(),
            'project_name': self.project.name,
            'format': self.config.format.value,
            'component_count': self.component_count,
            'asset_count': self.asset_count,
            'warnings': self.warnings
        }