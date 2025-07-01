"""
Component Library UI Panel
Main UI interface for the component library system.
"""

from typing import Dict, List, Optional, Any, Callable
import json
import logging
from pathlib import Path

try:
    import flet as ft
except ImportError:
    # Mock flet for development/testing
    class MockFlet:
        def __getattr__(self, name):
            return type(name, (), {})()
    ft = MockFlet()

from component_types import ComponentCategory, ComponentDefinition
from component_registry import ComponentRegistry, get_component_registry
from component_search import (
    ComponentSearchEngine, SearchFilters, SearchScope, SortOrder,
    get_component_search_engine
)
from component_factory import ComponentFactory, get_component_factory
from drag_drop_manager import (
    DragDropManager, DragData, DragOperation, DropTarget, DropZoneType,
    get_drag_drop_manager
)


logger = logging.getLogger(__name__)


class ComponentLibraryPanel:
    """
    Main UI panel for the component library.
    Provides search, filtering, categorization, and drag-and-drop.
    """
    
    def __init__(
        self,
        registry: Optional[ComponentRegistry] = None,
        search_engine: Optional[ComponentSearchEngine] = None,
        factory: Optional[ComponentFactory] = None,
        drag_manager: Optional[DragDropManager] = None
    ):
        """Initialize the component library panel"""
        self.registry = registry or get_component_registry()
        self.search_engine = search_engine or get_component_search_engine()
        self.factory = factory or get_component_factory()
        self.drag_manager = drag_manager or get_drag_drop_manager()
        
        # UI state
        self.selected_category: Optional[ComponentCategory] = None
        self.search_query: str = ""
        self.current_scope: SearchScope = SearchScope.ALL
        self.sort_order: SortOrder = SortOrder.RELEVANCE
        self.show_favorites_only: bool = False
        
        # UI components
        self.search_field: Optional[ft.TextField] = None
        self.category_tabs: Optional[ft.Tabs] = None
        self.component_grid: Optional[ft.GridView] = None
        self.filter_chips: Optional[ft.Row] = None
        self.toolbar: Optional[ft.Row] = None
        
        # Event handlers
        self.on_component_selected: Optional[Callable[[str], None]] = None
        self.on_component_drag_start: Optional[Callable[[str], None]] = None
        
        # Favorites and settings
        self.favorites_file = Path("user_data/component_favorites.json")
        self.settings_file = Path("user_data/library_settings.json")
        self._load_user_data()
        
        logger.info("Component library panel initialized")
    
    def build(self) -> ft.Control:
        """Build the main UI control"""
        return ft.Container(
            width=320,
            height=600,
            padding=10,
            content=ft.Column([
                self._build_header(),
                self._build_toolbar(),
                self._build_search_bar(),
                self._build_filter_chips(),
                self._build_category_tabs(),
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                self._build_component_grid(),
            ], tight=True, spacing=8)
        )
    
    def _build_header(self) -> ft.Control:
        """Build the panel header"""
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.WIDGETS, size=24, color=ft.Colors.PRIMARY),
                ft.Text(
                    "Component Library",
                    style=ft.TextThemeStyle.TITLE_MEDIUM,
                    weight=ft.FontWeight.W_600
                ),
                ft.Spacer(),
                ft.IconButton(
                    icon=ft.Icons.SETTINGS,
                    icon_size=20,
                    tooltip="Settings",
                    on_click=self._show_settings
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.only(bottom=8)
        )
    
    def _build_toolbar(self) -> ft.Control:
        """Build the toolbar with view options"""
        self.toolbar = ft.Row([
            ft.SegmentedButton(
                segments=[
                    ft.Segment(
                        value=SearchScope.ALL,
                        label=ft.Text("All"),
                        icon=ft.Icons.APPS
                    ),
                    ft.Segment(
                        value=SearchScope.FAVORITES,
                        label=ft.Text("★"),
                        icon=ft.Icons.STAR
                    ),
                    ft.Segment(
                        value=SearchScope.RECENT,
                        label=ft.Text("Recent"),
                        icon=ft.Icons.HISTORY
                    )
                ],
                selected={self.current_scope},
                on_change=self._on_scope_changed
            ),
            ft.Spacer(),
            ft.PopupMenuButton(
                icon=ft.Icons.SORT,
                tooltip="Sort order",
                items=[
                    ft.PopupMenuItem(
                        text="Relevance",
                        checked=self.sort_order == SortOrder.RELEVANCE,
                        on_click=lambda _: self._set_sort_order(SortOrder.RELEVANCE)
                    ),
                    ft.PopupMenuItem(
                        text="Name A-Z",
                        checked=self.sort_order == SortOrder.NAME_ASC,
                        on_click=lambda _: self._set_sort_order(SortOrder.NAME_ASC)
                    ),
                    ft.PopupMenuItem(
                        text="Name Z-A",
                        checked=self.sort_order == SortOrder.NAME_DESC,
                        on_click=lambda _: self._set_sort_order(SortOrder.NAME_DESC)
                    ),
                    ft.PopupMenuItem(
                        text="Category",
                        checked=self.sort_order == SortOrder.CATEGORY,
                        on_click=lambda _: self._set_sort_order(SortOrder.CATEGORY)
                    ),
                    ft.PopupMenuItem(
                        text="Most Used",
                        checked=self.sort_order == SortOrder.USAGE,
                        on_click=lambda _: self._set_sort_order(SortOrder.USAGE)
                    )
                ]
            )
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        return self.toolbar
    
    def _build_search_bar(self) -> ft.Control:
        """Build the search input"""
        self.search_field = ft.TextField(
            hint_text="Search components...",
            prefix_icon=ft.Icons.SEARCH,
            value=self.search_query,
            on_change=self._on_search_changed,
            on_submit=self._on_search_submit,
            dense=True,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=8)
        )
        
        return self.search_field
    
    def _build_filter_chips(self) -> ft.Control:
        """Build filter chips for quick filtering"""
        chips = []
        
        # Category chips
        categories = self.registry.get_categories()
        for category in categories[:6]:  # Limit visible categories
            chips.append(
                ft.FilterChip(
                    label=ft.Text(category.display_name),
                    leading=ft.Icon(category.icon, size=16),
                    selected=self.selected_category == category,
                    on_click=lambda e, cat=category: self._toggle_category_filter(cat)
                )
            )
        
        # Add more filters chip
        if len(categories) > 6:
            chips.append(
                ft.ActionChip(
                    label=ft.Text("More..."),
                    icon=ft.Icons.MORE_HORIZ,
                    on_click=self._show_advanced_filters
                )
            )
        
        self.filter_chips = ft.Row(
            chips,
            spacing=4,
            wrap=True
        )
        
        return ft.Container(
            content=self.filter_chips,
            height=40 if chips else 0
        )
    
    def _build_category_tabs(self) -> ft.Control:
        """Build category tabs"""
        categories = self.registry.get_categories()
        tabs = []
        
        # All tab
        tabs.append(ft.Tab(
            text="All",
            icon=ft.Icons.APPS
        ))
        
        # Category tabs
        for category in categories:
            component_count = len(self.registry.get_by_category(category))
            tabs.append(ft.Tab(
                text=f"{category.display_name} ({component_count})",
                icon=category.icon
            ))
        
        self.category_tabs = ft.Tabs(
            tabs=tabs,
            selected_index=0,
            on_change=self._on_tab_changed,
            scrollable=True,
            label_padding=ft.padding.symmetric(horizontal=8, vertical=4)
        )
        
        return self.category_tabs
    
    def _build_component_grid(self) -> ft.Control:
        """Build the component grid"""
        # Get components based on current filters
        components = self._get_filtered_components()
        
        # Create component cards
        cards = []
        for component in components:
            card = self._create_component_card(component)
            cards.append(card)
        
        # Create grid
        self.component_grid = ft.GridView(
            controls=cards,
            runs_count=2,
            max_extent=140,
            child_aspect_ratio=1.0,
            spacing=8,
            run_spacing=8,
            expand=True
        )
        
        return ft.Container(
            content=self.component_grid,
            expand=True
        )
    
    def _create_component_card(self, definition: ComponentDefinition) -> ft.Control:
        """Create a draggable component card"""
        is_favorite = self.registry.is_favorite(definition.id)
        
        # Create drag data
        drag_data = DragData(
            operation=DragOperation.COPY,
            source_type="library",
            component_id=definition.id
        )
        
        return ft.Draggable(
            group="components",
            data=drag_data.to_json(),
            content=ft.Container(
                width=130,
                height=130,
                bgcolor=ft.Colors.SURFACE_VARIANT,
                border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=8,
                padding=8,
                content=ft.Column([
                    # Icon
                    ft.Container(
                        content=ft.Icon(
                            definition.icon,
                            size=32,
                            color=ft.Colors.PRIMARY
                        ),
                        alignment=ft.alignment.center,
                        height=50
                    ),
                    
                    # Name
                    ft.Text(
                        definition.name,
                        size=12,
                        weight=ft.FontWeight.W_500,
                        text_align=ft.TextAlign.CENTER,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS
                    ),
                    
                    # Actions
                    ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.STAR if is_favorite else ft.Icons.STAR_OUTLINE,
                            icon_size=16,
                            icon_color=ft.Colors.YELLOW if is_favorite else ft.Colors.OUTLINE,
                            tooltip="Toggle favorite",
                            on_click=lambda e, comp_id=definition.id: self._toggle_favorite(comp_id)
                        ),
                        ft.IconButton(
                            icon=ft.Icons.INFO_OUTLINE,
                            icon_size=16,
                            tooltip="Show details",
                            on_click=lambda e, comp_id=definition.id: self._show_component_details(comp_id)
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    
                ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                
                # Hover effect
                on_hover=lambda e: self._on_card_hover(e, definition),
                on_click=lambda e: self._on_card_click(definition)
            ),
            content_feedback=ft.Container(
                width=130,
                height=130,
                bgcolor=ft.Colors.PRIMARY_CONTAINER,
                border_radius=8,
                content=ft.Icon(
                    definition.icon,
                    size=48,
                    color=ft.Colors.PRIMARY
                ),
                alignment=ft.alignment.center
            )
        )
    
    def _get_filtered_components(self) -> List[ComponentDefinition]:
        """Get components based on current filters"""
        # Create search filters
        filters = SearchFilters(
            categories=[self.selected_category] if self.selected_category else None,
            scope=self.current_scope
        )
        
        # Perform search
        results = self.search_engine.search(
            query=self.search_query,
            filters=filters,
            sort_order=self.sort_order,
            limit=50  # Limit for performance
        )
        
        return [result.component for result in results.results]
    
    def refresh_components(self):
        """Refresh the component grid"""
        # Rebuild the component grid
        if self.component_grid:
            components = self._get_filtered_components()
            cards = [self._create_component_card(comp) for comp in components]
            self.component_grid.controls = cards
            self.component_grid.update()
    
    def set_search_query(self, query: str):
        """Set the search query programmatically"""
        self.search_query = query
        if self.search_field:
            self.search_field.value = query
            self.search_field.update()
        self.refresh_components()
    
    def set_category_filter(self, category: Optional[ComponentCategory]):
        """Set the category filter"""
        self.selected_category = category
        self.refresh_components()
    
    # Event handlers
    
    def _on_search_changed(self, e):
        """Handle search input change"""
        self.search_query = e.control.value
        self.refresh_components()
    
    def _on_search_submit(self, e):
        """Handle search submit"""
        self.refresh_components()
    
    def _on_scope_changed(self, e):
        """Handle scope change"""
        self.current_scope = list(e.control.selected)[0]
        self.refresh_components()
    
    def _on_tab_changed(self, e):
        """Handle category tab change"""
        tab_index = e.control.selected_index
        
        if tab_index == 0:
            # All tab
            self.selected_category = None
        else:
            # Category tab
            categories = self.registry.get_categories()
            if tab_index - 1 < len(categories):
                self.selected_category = categories[tab_index - 1]
        
        self.refresh_components()
    
    def _toggle_category_filter(self, category: ComponentCategory):
        """Toggle category filter"""
        if self.selected_category == category:
            self.selected_category = None
        else:
            self.selected_category = category
        
        self.refresh_components()
        
        # Update filter chips
        if self.filter_chips:
            for chip in self.filter_chips.controls:
                if hasattr(chip, 'selected'):
                    chip.selected = False
            self.filter_chips.update()
    
    def _set_sort_order(self, sort_order: SortOrder):
        """Set sort order"""
        self.sort_order = sort_order
        self.refresh_components()
    
    def _toggle_favorite(self, component_id: str):
        """Toggle component favorite status"""
        if self.registry.is_favorite(component_id):
            self.registry.remove_favorite(component_id)
        else:
            self.registry.add_favorite(component_id)
        
        self.refresh_components()
        self._save_user_data()
    
    def _on_card_hover(self, e, definition: ComponentDefinition):
        """Handle component card hover"""
        if e.data == "true":
            # Show preview tooltip
            pass
    
    def _on_card_click(self, definition: ComponentDefinition):
        """Handle component card click"""
        if self.on_component_selected:
            self.on_component_selected(definition.id)
    
    def _show_component_details(self, component_id: str):
        """Show component details dialog"""
        definition = self.registry.get(component_id)
        if not definition:
            return
        
        # Create details dialog
        dialog = ft.AlertDialog(
            title=ft.Text(f"{definition.name} Details"),
            content=ft.Column([
                ft.Text(f"Category: {definition.category.display_name}"),
                ft.Text(f"Description: {definition.description}"),
                ft.Text(f"Tags: {', '.join(definition.tags)}"),
                ft.Text(f"Version: {definition.version}"),
                ft.Text(f"Author: {definition.author}"),
                ft.Text(f"Properties: {len(definition.properties)}"),
                ft.Text(f"Accepts Children: {'Yes' if definition.accepts_children else 'No'}"),
            ], spacing=8, tight=True),
            actions=[
                ft.TextButton("Close", on_click=lambda e: self._close_dialog(dialog))
            ]
        )
        
        # Show dialog (this would need to be handled by the parent page)
        # page.dialog = dialog
        # dialog.open = True
        # page.update()
    
    def _show_settings(self, e):
        """Show settings dialog"""
        # Settings dialog implementation
        pass
    
    def _show_advanced_filters(self, e):
        """Show advanced filters dialog"""
        # Advanced filters dialog implementation
        pass
    
    def _close_dialog(self, dialog):
        """Close a dialog"""
        dialog.open = False
        # dialog.page.update()
    
    def _load_user_data(self):
        """Load user favorites and settings"""
        try:
            # Load favorites
            if self.favorites_file.exists():
                with open(self.favorites_file, 'r') as f:
                    favorites = json.load(f)
                    for fav_id in favorites:
                        self.registry.add_favorite(fav_id)
            
            # Load settings
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.current_scope = SearchScope(settings.get('scope', SearchScope.ALL.value))
                    self.sort_order = SortOrder(settings.get('sort_order', SortOrder.RELEVANCE.value))
                    
        except Exception as e:
            logger.error(f"Failed to load user data: {e}")
    
    def _save_user_data(self):
        """Save user favorites and settings"""
        try:
            # Ensure directory exists
            self.favorites_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save favorites
            favorites = list(self.registry.get_favorites())
            with open(self.favorites_file, 'w') as f:
                json.dump([comp.id for comp in favorites], f)
            
            # Save settings
            settings = {
                'scope': self.current_scope.value,
                'sort_order': self.sort_order.value
            }
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f)
                
        except Exception as e:
            logger.error(f"Failed to save user data: {e}")


# Global panel instance
_panel_instance: Optional[ComponentLibraryPanel] = None


def get_component_library_panel() -> ComponentLibraryPanel:
    """Get the global component library panel instance"""
    global _panel_instance
    if _panel_instance is None:
        _panel_instance = ComponentLibraryPanel()
    return _panel_instance