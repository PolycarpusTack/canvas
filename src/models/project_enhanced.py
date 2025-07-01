"""
Enhanced Project Model for Export System Compatibility

CLAUDE.md Implementation:
- #2.1.1: Comprehensive validation
- #4.1: Strong typing
- #7.1: Secure project handling
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from uuid import uuid4
from datetime import datetime
from pathlib import Path

from .project import ProjectMetadata, ProjectSettings
from .component_enhanced import ExportCompatibleComponent
from .asset import Asset


@dataclass
class ProjectPage:
    """
    Represents a page within a project for multi-page exports
    
    CLAUDE.md #4.1: Explicit typing
    """
    
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = "Page"
    title: str = ""
    path: str = "/"
    description: Optional[str] = None
    
    # Page content
    root_component_id: Optional[str] = None
    components: List[ExportCompatibleComponent] = field(default_factory=list)
    
    # SEO and metadata
    meta_tags: Dict[str, str] = field(default_factory=dict)
    og_tags: Dict[str, str] = field(default_factory=dict)  # Open Graph
    
    # Page-specific settings
    layout: Optional[str] = None
    template: Optional[str] = None
    custom_css: Optional[str] = None
    custom_js: Optional[str] = None
    
    # State
    is_default: bool = False
    is_published: bool = True
    
    def __post_init__(self):
        """Initialize page after creation"""
        if not self.title:
            self.title = self.name
        
        # Set default meta tags
        if 'title' not in self.meta_tags:
            self.meta_tags['title'] = self.title
        
        if 'description' not in self.meta_tags and self.description:
            self.meta_tags['description'] = self.description
    
    def get_root_component(self) -> Optional[ExportCompatibleComponent]:
        """Get the root component for this page"""
        if self.root_component_id:
            for component in self.components:
                if component.id == self.root_component_id:
                    return component
        
        # If no root component ID set, return first component
        return self.components[0] if self.components else None
    
    def set_root_component(self, component: ExportCompatibleComponent):
        """Set the root component for this page"""
        self.root_component_id = component.id
        if component not in self.components:
            self.components.append(component)
    
    def add_component(self, component: ExportCompatibleComponent):
        """Add a component to this page"""
        if component not in self.components:
            self.components.append(component)
    
    def remove_component(self, component_id: str) -> bool:
        """Remove a component from this page"""
        for i, component in enumerate(self.components):
            if component.id == component_id:
                self.components.pop(i)
                if self.root_component_id == component_id:
                    self.root_component_id = None
                return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'title': self.title,
            'path': self.path,
            'description': self.description,
            'root_component_id': self.root_component_id,
            'components': [comp.to_dict() for comp in self.components],
            'meta_tags': self.meta_tags,
            'og_tags': self.og_tags,
            'layout': self.layout,
            'template': self.template,
            'custom_css': self.custom_css,
            'custom_js': self.custom_js,
            'is_default': self.is_default,
            'is_published': self.is_published
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectPage':
        """Create from dictionary"""
        components_data = data.pop('components', [])
        
        page = cls(**data)
        page.components = [
            ExportCompatibleComponent.from_dict(comp_data) 
            for comp_data in components_data
        ]
        
        return page


@dataclass
class ExportCompatibleProject:
    """
    Enhanced Project model compatible with export system
    
    CLAUDE.md #2.1.1: Comprehensive validation
    """
    
    # Core identification
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = "Untitled Project"
    description: str = ""
    version: str = "1.0.0"
    
    # Content structure
    components: List[ExportCompatibleComponent] = field(default_factory=list)
    pages: List[ProjectPage] = field(default_factory=list)
    assets: List[Asset] = field(default_factory=list)
    
    # Metadata and settings
    metadata: Dict[str, Any] = field(default_factory=dict)
    settings: Optional[ProjectSettings] = None
    
    # Framework and technology info
    framework: Optional[str] = None
    tech_stack: List[str] = field(default_factory=list)
    
    # Timestamps
    created_at: Optional[str] = None
    modified_at: Optional[str] = None
    
    # Export-specific properties
    export_configs: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize project after creation"""
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        
        self.modified_at = datetime.now().isoformat()
        
        if not self.settings:
            self.settings = ProjectSettings()
        
        # Ensure at least one page exists
        if not self.pages and self.components:
            self._create_default_page()
        
        self._validate_project()
    
    def _create_default_page(self):
        """Create default page from components"""
        default_page = ProjectPage(
            name="Home",
            title=self.name,
            path="/",
            is_default=True,
            components=self.components.copy()
        )
        
        # Set root component if there's a container
        root_containers = [c for c in self.components if c.type == "container" and not c.parent_id]
        if root_containers:
            default_page.set_root_component(root_containers[0])
        
        self.pages.append(default_page)
    
    def _validate_project(self):
        """
        Validate project structure
        
        CLAUDE.md #2.1.1: Comprehensive validation
        """
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Project name must be a non-empty string")
        
        if not self.id or not isinstance(self.id, str):
            raise ValueError("Project ID must be a non-empty string")
        
        # Validate component IDs are unique
        component_ids = set()
        for component in self.components:
            if component.id in component_ids:
                raise ValueError(f"Duplicate component ID: {component.id}")
            component_ids.add(component.id)
        
        # Validate asset IDs are unique
        asset_ids = set()
        for asset in self.assets:
            if asset.id in asset_ids:
                raise ValueError(f"Duplicate asset ID: {asset.id}")
            asset_ids.add(asset.id)
        
        # Validate page paths are unique
        page_paths = set()
        for page in self.pages:
            if page.path in page_paths:
                raise ValueError(f"Duplicate page path: {page.path}")
            page_paths.add(page.path)
    
    def get_default_page(self) -> Optional[ProjectPage]:
        """Get the default/home page"""
        for page in self.pages:
            if page.is_default:
                return page
        return self.pages[0] if self.pages else None
    
    def get_page_by_path(self, path: str) -> Optional[ProjectPage]:
        """Get page by URL path"""
        for page in self.pages:
            if page.path == path:
                return page
        return None
    
    def get_page_by_id(self, page_id: str) -> Optional[ProjectPage]:
        """Get page by ID"""
        for page in self.pages:
            if page.id == page_id:
                return page
        return None
    
    def add_page(self, page: ProjectPage):
        """Add a page to the project"""
        # Ensure path uniqueness
        existing_paths = {p.path for p in self.pages}
        if page.path in existing_paths:
            base_path = page.path.rstrip('/')
            counter = 1
            while f"{base_path}-{counter}" in existing_paths:
                counter += 1
            page.path = f"{base_path}-{counter}"
        
        self.pages.append(page)
        self.touch()
    
    def remove_page(self, page_id: str) -> bool:
        """Remove a page from the project"""
        for i, page in enumerate(self.pages):
            if page.id == page_id:
                # Don't remove if it's the only page
                if len(self.pages) <= 1:
                    return False
                
                # Don't remove default page without reassigning
                if page.is_default and len(self.pages) > 1:
                    # Make another page default
                    other_pages = [p for p in self.pages if p.id != page_id]
                    other_pages[0].is_default = True
                
                self.pages.pop(i)
                self.touch()
                return True
        return False
    
    def get_component_by_id(self, component_id: str) -> Optional[ExportCompatibleComponent]:
        """Find component by ID across all pages"""
        # Search in main components list
        for component in self.components:
            if component.id == component_id:
                return component
            found = component.find_child_by_id(component_id)
            if found:
                return found
        
        # Search in page components
        for page in self.pages:
            for component in page.components:
                if component.id == component_id:
                    return component
                found = component.find_child_by_id(component_id)
                if found:
                    return found
        
        return None
    
    def get_all_components(self) -> List[ExportCompatibleComponent]:
        """Get all components from all pages"""
        all_components = self.components.copy()
        
        for page in self.pages:
            all_components.extend(page.components)
        
        return all_components
    
    def get_asset_by_id(self, asset_id: str) -> Optional[Asset]:
        """Find asset by ID"""
        for asset in self.assets:
            if asset.id == asset_id:
                return asset
        return None
    
    def add_asset(self, asset: Asset):
        """Add an asset to the project"""
        if asset not in self.assets:
            self.assets.append(asset)
            self.touch()
    
    def remove_asset(self, asset_id: str) -> bool:
        """Remove an asset from the project"""
        for i, asset in enumerate(self.assets):
            if asset.id == asset_id:
                self.assets.pop(i)
                self.touch()
                return True
        return False
    
    def get_referenced_assets(self) -> List[Asset]:
        """Get all assets that are referenced by components"""
        referenced_ids = set()
        
        # Collect asset references from all components
        all_components = self.get_all_components()
        for component in all_components:
            if component.asset_id:
                referenced_ids.add(component.asset_id)
            
            # Check properties for asset references
            for prop_value in component.get_all_properties().values():
                if isinstance(prop_value, str) and prop_value.startswith('asset:'):
                    asset_id = prop_value.replace('asset:', '')
                    referenced_ids.add(asset_id)
        
        # Return referenced assets
        return [asset for asset in self.assets if asset.id in referenced_ids]
    
    def get_unreferenced_assets(self) -> List[Asset]:
        """Get assets that are not referenced by any component"""
        referenced_assets = self.get_referenced_assets()
        referenced_ids = {asset.id for asset in referenced_assets}
        
        return [asset for asset in self.assets if asset.id not in referenced_ids]
    
    def cleanup_unused_assets(self) -> int:
        """Remove unreferenced assets and return count removed"""
        unreferenced = self.get_unreferenced_assets()
        for asset in unreferenced:
            self.remove_asset(asset.id)
        return len(unreferenced)
    
    def get_project_statistics(self) -> Dict[str, Any]:
        """Get comprehensive project statistics"""
        all_components = self.get_all_components()
        
        component_types = {}
        for component in all_components:
            component_types[component.type] = component_types.get(component.type, 0) + 1
        
        asset_types = {}
        total_asset_size = 0
        for asset in self.assets:
            asset_types[asset.metadata.asset_type] = asset_types.get(asset.metadata.asset_type, 0) + 1
            total_asset_size += asset.metadata.size
        
        return {
            'total_components': len(all_components),
            'component_types': component_types,
            'total_pages': len(self.pages),
            'total_assets': len(self.assets),
            'asset_types': asset_types,
            'total_asset_size': total_asset_size,
            'referenced_assets': len(self.get_referenced_assets()),
            'unreferenced_assets': len(self.get_unreferenced_assets()),
            'max_component_depth': max(
                [comp.get_descendant_count() for comp in all_components], 
                default=0
            )
        }
    
    def touch(self):
        """Update the modified timestamp"""
        self.modified_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'components': [comp.to_dict() for comp in self.components],
            'pages': [page.to_dict() for page in self.pages],
            'assets': [asset.to_dict() for asset in self.assets],
            'metadata': self.metadata,
            'settings': self.settings.to_dict() if self.settings else None,
            'framework': self.framework,
            'tech_stack': self.tech_stack,
            'created_at': self.created_at,
            'modified_at': self.modified_at,
            'export_configs': self.export_configs
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExportCompatibleProject':
        """Create project from dictionary"""
        # Extract complex objects
        components_data = data.pop('components', [])
        pages_data = data.pop('pages', [])
        assets_data = data.pop('assets', [])
        settings_data = data.pop('settings', None)
        
        # Create project
        project = cls(**data)
        
        # Restore complex objects
        project.components = [
            ExportCompatibleComponent.from_dict(comp_data) 
            for comp_data in components_data
        ]
        
        project.pages = [
            ProjectPage.from_dict(page_data) 
            for page_data in pages_data
        ]
        
        project.assets = [
            Asset.from_dict(asset_data) 
            for asset_data in assets_data
        ]
        
        if settings_data:
            project.settings = ProjectSettings.from_dict(settings_data)
        
        return project
    
    @classmethod
    def create_sample_project(cls) -> 'ExportCompatibleProject':
        """Create a sample project for testing and demos"""
        
        # Create sample components
        header = ExportCompatibleComponent(
            type="heading",
            name="MainTitle",
            content="Welcome to Canvas",
            properties={"level": 1},
            styles={"fontSize": "32px", "marginBottom": "20px", "textAlign": "center"}
        )
        
        paragraph = ExportCompatibleComponent(
            type="text",
            name="IntroText",
            content="This is a sample project created by the Canvas export system.",
            styles={"fontSize": "16px", "lineHeight": "1.6", "marginBottom": "20px"}
        )
        
        button = ExportCompatibleComponent(
            type="button",
            name="CTAButton",
            content="Get Started",
            properties={"onClick": "handleClick"},
            styles={
                "padding": "12px 24px",
                "backgroundColor": "#007bff",
                "color": "white",
                "border": "none",
                "borderRadius": "6px",
                "fontSize": "16px",
                "cursor": "pointer"
            }
        )
        
        container = ExportCompatibleComponent(
            type="container",
            name="MainContainer",
            properties={"class": "main-container"},
            styles={
                "maxWidth": "800px",
                "margin": "0 auto",
                "padding": "40px 20px",
                "fontFamily": "Arial, sans-serif"
            },
            children=[header, paragraph, button]
        )
        
        # Create sample page
        home_page = ProjectPage(
            name="Home",
            title="Canvas Sample Project",
            path="/",
            description="A sample project demonstrating Canvas export capabilities",
            is_default=True,
            components=[container]
        )
        home_page.set_root_component(container)
        
        # Create project
        project = cls(
            name="Sample Canvas Project",
            description="A demonstration project showing Canvas export capabilities",
            components=[container],
            pages=[home_page],
            framework="HTML",
            tech_stack=["HTML5", "CSS3", "JavaScript"],
            metadata={
                "title": "Canvas Sample Project",
                "author": "Canvas Export System",
                "keywords": ["canvas", "export", "sample", "demo"]
            }
        )
        
        return project


# Type alias for backward compatibility
Project = ExportCompatibleProject