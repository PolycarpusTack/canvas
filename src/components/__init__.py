"""
Component Library System
Comprehensive component library with search, drag-and-drop, and tree management.
"""

# Core types and definitions
from component_types import (
    ComponentDefinition,
    ComponentCategory,
    ComponentSlot,
    ComponentConstraints,
    PropertyDefinition,
    PropertyType,
    PropertyValidation,
    PropertyOption,
    ValidationResult,
    CustomComponent,
    ComponentMap,
    ComponentList
)

# Built-in components
from builtin_components import BuiltInComponents

# Registry system
from component_registry import (
    ComponentRegistry,
    get_component_registry
)

# Factory system
from component_factory import (
    ComponentFactory,
    get_component_factory
)

# Search engine
from component_search import (
    ComponentSearchEngine,
    SearchFilters,
    SearchScope,
    SortOrder,
    SearchResult,
    SearchResults,
    get_component_search_engine
)

# Drag and drop
from drag_drop_manager import (
    DragDropManager,
    DragData,
    DragOperation,
    DropTarget,
    DropZoneType,
    DragDropEvent,
    get_drag_drop_manager
)

# Tree management
from component_tree import (
    ComponentTreeManager,
    TreeNode,
    TreeOperation,
    TreeChange,
    get_component_tree_manager
)

# UI Panel
from component_library_panel import (
    ComponentLibraryPanel,
    get_component_library_panel
)

# Custom component operations
from .custom_component_manager import (
    CustomComponentManager,
    ComponentTemplate,
    get_custom_component_manager
)

# Component preview system
from .component_preview import (
    ComponentPreviewManager,
    ComponentPreview,
    PreviewSize,
    PreviewFormat,
    PreviewVariation,
    PreviewImage,
    ResponsiveBreakpoint,
    CodeFramework,
    get_component_preview_manager
)

# Component analytics
from .component_analytics import (
    ComponentAnalytics,
    UsageAction,
    PerformanceMetric,
    ComponentUsageStats,
    AnalyticsReport,
    get_component_analytics
)


__all__ = [
    # Core types
    'ComponentDefinition',
    'ComponentCategory',
    'ComponentSlot',
    'ComponentConstraints',
    'PropertyDefinition',
    'PropertyType',
    'PropertyValidation',
    'PropertyOption',
    'ValidationResult',
    'CustomComponent',
    'ComponentMap',
    'ComponentList',
    
    # Built-in components
    'BuiltInComponents',
    
    # Registry
    'ComponentRegistry',
    'get_component_registry',
    
    # Factory
    'ComponentFactory',
    'get_component_factory',
    
    # Search
    'ComponentSearchEngine',
    'SearchFilters',
    'SearchScope',
    'SortOrder',
    'SearchResult',
    'SearchResults',
    'get_component_search_engine',
    
    # Drag and drop
    'DragDropManager',
    'DragData',
    'DragOperation',
    'DropTarget',
    'DropZoneType',
    'DragDropEvent',
    'get_drag_drop_manager',
    
    # Tree management
    'ComponentTreeManager',
    'TreeNode',
    'TreeOperation',
    'TreeChange',
    'get_component_tree_manager',
    
    # UI
    'ComponentLibraryPanel',
    'get_component_library_panel',
    
    # Custom components
    'CustomComponentManager',
    'ComponentTemplate',
    'get_custom_component_manager',
    
    # Preview system
    'ComponentPreviewManager',
    'ComponentPreview',
    'PreviewSize',
    'PreviewFormat',
    'PreviewVariation',
    'PreviewImage',
    'ResponsiveBreakpoint',
    'CodeFramework',
    'get_component_preview_manager',
    
    # Analytics
    'ComponentAnalytics',
    'UsageAction',
    'PerformanceMetric',
    'ComponentUsageStats',
    'AnalyticsReport',
    'get_component_analytics',
]


# Version information
__version__ = "1.0.0"
__author__ = "Canvas Editor"


def initialize_component_library():
    """
    Initialize the complete component library system.
    This should be called once during application startup.
    """
    # Initialize all the systems
    registry = get_component_registry()
    factory = get_component_factory()
    search_engine = get_component_search_engine()
    drag_manager = get_drag_drop_manager()
    tree_manager = get_component_tree_manager()
    panel = get_component_library_panel()
    
    # Initialize new systems
    custom_manager = get_custom_component_manager()
    preview_manager = get_component_preview_manager()
    analytics = get_component_analytics()
    
    return {
        'registry': registry,
        'factory': factory,
        'search_engine': search_engine,
        'drag_manager': drag_manager,
        'tree_manager': tree_manager,
        'panel': panel,
        'custom_manager': custom_manager,
        'preview_manager': preview_manager,
        'analytics': analytics
    }


def get_component_library_api():
    """
    Get a simplified API object for the component library.
    Provides the most commonly used functions in a single interface.
    """
    
    class ComponentLibraryAPI:
        """Simplified API for the component library system"""
        
        def __init__(self):
            self.registry = get_component_registry()
            self.factory = get_component_factory()
            self.search = get_component_search_engine()
            self.drag_drop = get_drag_drop_manager()
            self.tree = get_component_tree_manager()
            self.panel = get_component_library_panel()
            self.custom = get_custom_component_manager()
            self.preview = get_component_preview_manager()
            self.analytics = get_component_analytics()
        
        # Registry operations
        def get_component(self, component_id: str) -> ComponentDefinition:
            """Get a component definition by ID"""
            return self.registry.get(component_id)
        
        def list_components(self, category: ComponentCategory = None) -> ComponentList:
            """List all components or components in a category"""
            if category:
                return self.registry.get_by_category(category)
            return list(self.registry.get_all().values())
        
        def get_categories(self) -> List[ComponentCategory]:
            """Get all available categories"""
            return self.registry.get_categories()
        
        def get_favorites(self) -> ComponentList:
            """Get favorite components"""
            return self.registry.get_favorites()
        
        def add_favorite(self, component_id: str) -> bool:
            """Add component to favorites"""
            return self.registry.add_favorite(component_id)
        
        def remove_favorite(self, component_id: str) -> bool:
            """Remove component from favorites"""
            return self.registry.remove_favorite(component_id)
        
        # Factory operations
        def create_component(self, component_id: str, properties: dict = None):
            """Create a component instance"""
            return self.factory.create_component(component_id, properties)
        
        def create_component_tree(self, component_id: str, properties: dict = None, children: list = None):
            """Create a component with children"""
            return self.factory.create_component_tree(component_id, properties, children)
        
        def validate_component(self, component) -> ValidationResult:
            """Validate a component tree"""
            return self.factory.validate_component_tree(component)
        
        # Search operations
        def search_components(self, query: str = "", filters: SearchFilters = None, limit: int = None) -> SearchResults:
            """Search for components"""
            return self.search.search(query, filters, limit=limit)
        
        def search_by_tag(self, tag: str) -> ComponentList:
            """Search components by tag"""
            return self.search.search_by_tag(tag)
        
        def get_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
            """Get search suggestions"""
            return self.search.get_suggestions(partial_query, limit)
        
        # Tree operations
        def create_tree(self, root_component, tree_id: str = None) -> str:
            """Create a component tree"""
            return self.tree.create_tree(root_component, tree_id)
        
        def add_to_tree(self, parent_id: str, component, position: int = None) -> ValidationResult:
            """Add component to tree"""
            return self.tree.add_component(parent_id, component, position)
        
        def move_in_tree(self, component_id: str, new_parent_id: str, position: int = None) -> ValidationResult:
            """Move component in tree"""
            return self.tree.move_component(component_id, new_parent_id, position)
        
        def remove_from_tree(self, component_id: str) -> ValidationResult:
            """Remove component from tree"""
            return self.tree.remove_component(component_id)
        
        def get_tree_node(self, component_id: str) -> TreeNode:
            """Get tree node for component"""
            return self.tree.get_node(component_id)
        
        # UI operations
        def get_panel(self) -> ComponentLibraryPanel:
            """Get the UI panel"""
            return self.panel
        
        def refresh_ui(self):
            """Refresh the UI panel"""
            self.panel.refresh_components()
        
        def set_search_query(self, query: str):
            """Set search query in UI"""
            self.panel.set_search_query(query)
        
        def set_category_filter(self, category: ComponentCategory):
            """Set category filter in UI"""
            self.panel.set_category_filter(category)
        
        # Custom component operations
        def create_custom_component(self, name: str, description: str, category: ComponentCategory):
            """Start creating a custom component"""
            return self.custom.start_component_creation(name, description, category)
        
        def finalize_custom_component(self, session_id: str):
            """Finalize custom component creation"""
            return self.custom.finalize_custom_component(session_id)
        
        def get_custom_components(self):
            """Get all custom components"""
            return self.custom.get_all_custom_components()
        
        def export_custom_component(self, component_id: str):
            """Export a custom component"""
            return self.custom.export_custom_component(component_id)
        
        def import_custom_component(self, import_data: dict):
            """Import a custom component"""
            return self.custom.import_custom_component(import_data)
        
        def create_template(self, name: str, description: str, base_component):
            """Create a component template"""
            return self.custom.create_component_template(name, description, base_component)
        
        def get_templates(self):
            """Get all component templates"""
            return self.custom.get_component_templates()
        
        # Preview operations
        def generate_preview(self, component_id: str, size=None, format=None):
            """Generate component preview"""
            return self.preview.generate_preview(component_id, size, format)
        
        def get_preview_variations(self, component_id: str):
            """Get preview variations for a component"""
            return self.preview.get_preview_variations(component_id)
        
        def generate_code_snippets(self, component_id: str):
            """Generate code snippets for a component"""
            return self.preview.generate_code_snippets(component_id)
        
        def get_accessibility_info(self, component_id: str):
            """Get accessibility information for a component"""
            return self.preview.get_accessibility_info(component_id)
        
        def clear_preview_cache(self, component_id: str = None):
            """Clear preview cache"""
            self.preview.clear_cache(component_id)
        
        # Analytics operations
        def track_component_usage(self, component_id: str, action: str, **kwargs):
            """Track component usage"""
            from .component_analytics import UsageAction
            action_enum = UsageAction(action) if isinstance(action, str) else action
            self.analytics.track_usage(component_id, action_enum, **kwargs)
        
        def track_performance(self, metric: str, value: float, **kwargs):
            """Track performance metric"""
            from .component_analytics import PerformanceMetric
            metric_enum = PerformanceMetric(metric) if isinstance(metric, str) else metric
            self.analytics.track_performance(metric_enum, value, **kwargs)
        
        def get_usage_stats(self, component_id: str = None):
            """Get usage statistics"""
            if component_id:
                return self.analytics.get_component_stats(component_id)
            return self.analytics.get_dashboard_data()
        
        def generate_analytics_report(self, start_date=None, end_date=None):
            """Generate analytics report"""
            from datetime import datetime, timedelta
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            return self.analytics.generate_report(start_date, end_date)
    
    return ComponentLibraryAPI()


# Create global API instance
_api_instance = None

def get_api():
    """Get the global component library API instance"""
    global _api_instance
    if _api_instance is None:
        _api_instance = get_component_library_api()
    return _api_instance