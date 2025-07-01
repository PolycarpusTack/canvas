"""Main Canvas Editor application"""

import flet as ft
import asyncio
from typing import Optional, Dict, Any

from ui.panels.sidebar import SidebarPanel
from ui.panels.components import ComponentsPanel
from ui.panels.canvas import CanvasPanel
from ui.panels.properties import PropertiesPanel
from ui.components.resize_handle import ResizeHandle
from ui.dialogs.project_dialog import NewProjectDialog, ImportProjectDialog, ProjectErrorDialog

from managers.enhanced_state import EnhancedStateManager
from managers.project_state_integrated import StateIntegratedProjectManager
from managers.action_creators import ActionCreators

from services.component_service import ComponentService
from services.export_service import ExportService

from models.component import Component
from config.constants import (
    SIDEBAR_WIDTH, SIDEBAR_MIN_WIDTH, SIDEBAR_MAX_WIDTH,
    COMPONENTS_WIDTH, COMPONENTS_MIN_WIDTH, COMPONENTS_MAX_WIDTH,
    PROPERTIES_WIDTH, PROPERTIES_MIN_WIDTH, PROPERTIES_MAX_WIDTH,
    CANVAS_MIN_WIDTH
)


class CanvasEditor:
    """Main Canvas Editor application class"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        
        # Managers - Initialize state manager first
        self.state_manager = EnhancedStateManager(page)
        self.project_manager = None  # Will be initialized after state manager
        
        # Services
        self.component_service = ComponentService()
        self.export_service = ExportService()
        
        # UI Panels
        self.sidebar: Optional[SidebarPanel] = None
        self.components_panel: Optional[ComponentsPanel] = None
        self.canvas_panel: Optional[CanvasPanel] = None
        self.properties_panel: Optional[PropertiesPanel] = None
        
        # Panel sizes
        self.panel_sizes = {
            "sidebar": SIDEBAR_WIDTH,
            "components": COMPONENTS_WIDTH,
            "properties": PROPERTIES_WIDTH
        }
        
        # Current state
        self.selected_component: Optional[Component] = None
        self.components_tree: list[Component] = []
        
    async def initialize(self):
        """Initialize the application"""
        # Initialize enhanced state manager first
        await self.state_manager.initialize()
        
        # Create integrated project manager with state management
        self.project_manager = StateIntegratedProjectManager(self.state_manager)
        
        # Set up page properties
        self.page.title = "Canvas Editor"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        
        # Restore window state
        await self.state_manager.restore_window_state()
        
        # Restore panel sizes
        self.panel_sizes = await self.state_manager.restore_panel_state()
        
        # Set up window event handlers
        self.page.window.on_resize = self._on_window_resize
        self.page.window.on_close = self._on_window_close
        
        # Subscribe to state changes for real-time UI updates
        await self._setup_state_subscriptions()
        
        # Build UI
        self._build_ui()
        
        # Restore last project if any
        last_project_id = await self.state_manager.get_current_project_id()
        if last_project_id:
            # TODO: Load last project
            pass
    
    async def _setup_state_subscriptions(self):
        """Set up state change subscriptions for real-time UI updates"""
        # Subscribe to component changes for canvas updates
        await self.state_manager.subscribe_to_changes(
            "components", 
            self._on_components_changed
        )
        
        # Subscribe to selection changes
        await self.state_manager.subscribe_to_changes(
            "selection", 
            self._on_selection_changed
        )
        
        # Subscribe to theme changes
        await self.state_manager.subscribe_to_changes(
            "theme.mode", 
            self._on_theme_changed
        )
    
    async def _on_components_changed(self, old_value, new_value):
        """Handle components state changes"""
        # Update canvas with new components
        if self.canvas_panel:
            # Trigger canvas refresh
            await asyncio.create_task(self.canvas_panel.refresh_from_state(new_value))
    
    async def _on_selection_changed(self, old_value, new_value):
        """Handle selection state changes"""
        # Update UI to reflect new selection
        if self.canvas_panel and hasattr(new_value, 'selected_ids'):
            selected_ids = list(new_value.selected_ids)
            if selected_ids:
                await asyncio.create_task(self.canvas_panel.update_selection(selected_ids))
    
    async def _on_theme_changed(self, old_value, new_value):
        """Handle theme changes"""
        # Update page theme
        if new_value == "dark":
            self.page.theme_mode = ft.ThemeMode.DARK
        else:
            self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.update()
    
    def _build_ui(self):
        """Build the main UI layout"""
        # Create panels
        self.sidebar = SidebarPanel(self._on_navigation)
        self.components_panel = ComponentsPanel(self._on_component_drag)
        self.canvas_panel = CanvasPanel(
            self._on_component_drop,
            self._on_component_select,
            self._on_canvas_action
        )
        self.properties_panel = PropertiesPanel(self._on_property_change)
        
        # Create resize handles
        sidebar_handle = ResizeHandle(
            on_drag=lambda w: self._resize_panel("sidebar", w),
            min_value=SIDEBAR_MIN_WIDTH,
            max_value=SIDEBAR_MAX_WIDTH
        )
        sidebar_handle.set_start_value(self.panel_sizes["sidebar"])
        
        components_handle = ResizeHandle(
            on_drag=lambda w: self._resize_panel("components", w),
            min_value=COMPONENTS_MIN_WIDTH,
            max_value=COMPONENTS_MAX_WIDTH
        )
        components_handle.set_start_value(self.panel_sizes["components"])
        
        properties_handle = ResizeHandle(
            on_drag=lambda w: self._resize_panel("properties", w),
            min_value=PROPERTIES_MIN_WIDTH,
            max_value=PROPERTIES_MAX_WIDTH
        )
        properties_handle.set_start_value(self.panel_sizes["properties"])
        
        # Build layout
        layout = ft.Row([
            ft.Container(self.sidebar, width=self.panel_sizes["sidebar"]),
            sidebar_handle,
            ft.Container(self.components_panel, width=self.panel_sizes["components"]),
            components_handle,
            ft.Container(self.canvas_panel, expand=True),
            properties_handle,
            ft.Container(self.properties_panel, width=self.panel_sizes["properties"])
        ], spacing=0, expand=True)
        
        # Add to page
        self.page.add(layout)
    
    def _resize_panel(self, panel: str, width: float):
        """Handle panel resize"""
        self.panel_sizes[panel] = width
        
        # Update UI
        if panel == "sidebar":
            self.page.controls[0].controls[0].width = width
        elif panel == "components":
            self.page.controls[0].controls[2].width = width
        elif panel == "properties":
            self.page.controls[0].controls[6].width = width
        
        self.page.update()
        
        # Save state (debounced)
        asyncio.create_task(self._save_panel_state_debounced())
    
    async def _save_panel_state_debounced(self):
        """Save panel state with debouncing"""
        await asyncio.sleep(0.5)  # Debounce
        await self.state_manager.save_panel_state(self.panel_sizes)
    
    def _on_navigation(self, view: str):
        """Handle sidebar navigation"""
        print(f"Navigate to: {view}")
        # TODO: Implement view switching
    
    def _on_component_drag(self, component_data: Dict[str, str]):
        """Handle component drag start"""
        print(f"Dragging component: {component_data}")
    
    async def _on_component_drop(self, component_data: Dict[str, str], position: ft.Offset):
        """Handle component drop on canvas using enhanced state management"""
        try:
            # Create new component with position
            component = self.component_service.create_component_from_data(component_data)
            component_dict = component.to_dict()
            
            # Set position from drop location
            if 'style' not in component_dict:
                component_dict['style'] = {}
            component_dict['style']['left'] = str(position.x)
            component_dict['style']['top'] = str(position.y)
            
            # Dispatch add component action (includes spatial indexing)
            action = ActionCreators.add_component(component_dict)
            await self.state_manager.dispatch_action(action)
            
            # Select the new component
            select_action = ActionCreators.select_component(component.id)
            await self.state_manager.dispatch_action(select_action)
            
        except Exception as e:
            print(f"Error adding component: {e}")
            # TODO: Show error dialog
    
    async def _on_component_select(self, component_id: str):
        """Handle component selection using enhanced state management"""
        try:
            # Dispatch selection action
            action = ActionCreators.select_component(component_id)
            await self.state_manager.dispatch_action(action)
            
            # Get component from state for properties panel
            components_state = self.state_manager.get_state_system().get_state("components")
            if component_id in components_state.component_map:
                component_data = components_state.component_map[component_id]
                # Update properties panel (converted from dict)
                if self.properties_panel:
                    self.properties_panel.set_component_data(component_data)
                    
        except Exception as e:
            print(f"Error selecting component: {e}")
    
    async def _on_property_change(self, component_id: str, property_path: str, value: Any):
        """Handle property change using enhanced state management"""
        try:
            # Build update dict from property path
            updates = {}
            path_parts = property_path.split('.')
            current = updates
            
            # Build nested dict structure
            for i, part in enumerate(path_parts):
                if i == len(path_parts) - 1:
                    current[part] = value
                else:
                    current[part] = {}
                    current = current[part]
            
            # Dispatch update action (includes spatial index updates if position/size changed)
            action = ActionCreators.update_component(component_id, updates)
            await self.state_manager.dispatch_action(action)
            
        except Exception as e:
            print(f"Error updating component property: {e}")
    
    def _on_canvas_action(self, action: str):
        """Handle canvas toolbar actions with enhanced state management"""
        if action == "save":
            asyncio.create_task(self._save_project())
        elif action == "undo":
            asyncio.create_task(self._perform_undo())
        elif action == "redo":
            asyncio.create_task(self._perform_redo())
        elif action == "clear_selection":
            asyncio.create_task(self._clear_selection())
        elif action == "delete_selected":
            asyncio.create_task(self._delete_selected_components())
        elif action == "copy":
            asyncio.create_task(self._copy_selected_components())
        elif action == "paste":
            asyncio.create_task(self._paste_components())
        elif action == "preview":
            # TODO: Implement preview
            pass
        elif action == "publish":
            # TODO: Implement publish
            pass
    
    async def _perform_undo(self):
        """Perform undo operation"""
        try:
            success = await self.state_manager.undo()
            if success:
                # Show success feedback
                await self._show_action_feedback("Undo successful")
            else:
                await self._show_action_feedback("Nothing to undo")
        except Exception as e:
            print(f"Error performing undo: {e}")
    
    async def _perform_redo(self):
        """Perform redo operation"""
        try:
            success = await self.state_manager.redo()
            if success:
                await self._show_action_feedback("Redo successful")
            else:
                await self._show_action_feedback("Nothing to redo")
        except Exception as e:
            print(f"Error performing redo: {e}")
    
    async def _clear_selection(self):
        """Clear component selection"""
        try:
            action = ActionCreators.clear_selection()
            await self.state_manager.dispatch_action(action)
        except Exception as e:
            print(f"Error clearing selection: {e}")
    
    async def _delete_selected_components(self):
        """Delete selected components"""
        try:
            # Get selected components
            selection_state = self.state_manager.get_state_system().get_state("selection")
            selected_ids = list(selection_state.selected_ids)
            
            # Delete each selected component
            for component_id in selected_ids:
                action = ActionCreators.delete_component(component_id)
                await self.state_manager.dispatch_action(action)
                
            await self._show_action_feedback(f"Deleted {len(selected_ids)} component(s)")
        except Exception as e:
            print(f"Error deleting components: {e}")
    
    async def _copy_selected_components(self):
        """Copy selected components to clipboard"""
        try:
            selection_state = self.state_manager.get_state_system().get_state("selection")
            selected_ids = list(selection_state.selected_ids)
            
            if selected_ids:
                # TODO: Implement clipboard copy action
                await self._show_action_feedback(f"Copied {len(selected_ids)} component(s)")
        except Exception as e:
            print(f"Error copying components: {e}")
    
    async def _paste_components(self):
        """Paste components from clipboard"""
        try:
            # TODO: Implement clipboard paste action
            await self._show_action_feedback("Paste not yet implemented")
        except Exception as e:
            print(f"Error pasting components: {e}")
    
    async def _show_action_feedback(self, message: str):
        """Show feedback message to user"""
        snack = ft.SnackBar(
            content=ft.Text(message),
            duration=2000
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()
        
        # Auto-remove after duration
        await asyncio.sleep(2)
        if snack in self.page.overlay:
            self.page.overlay.remove(snack)
            self.page.update()
    
    def _find_component(self, component_id: str) -> Optional[Component]:
        """Find component by ID in the tree"""
        def search(components: list[Component]) -> Optional[Component]:
            for comp in components:
                if comp.id == component_id:
                    return comp
                if comp.children:
                    found = search(comp.children)
                    if found:
                        return found
            return None
        
        return search(self.components_tree)
    
    async def _save_project(self):
        """Save current project"""
        if self.project_manager.current_project:
            success = await self.project_manager.save_project()
            if success:
                # Show success message
                snack = ft.SnackBar(
                    content=ft.Text("Project saved successfully"),
                    action="OK"
                )
                self.page.overlay.append(snack)
                snack.open = True
                self.page.update()
        else:
            # No project open, show create dialog
            await self._show_new_project_dialog()
    
    async def _show_new_project_dialog(self):
        """Show new project dialog"""
        dialog = NewProjectDialog(self._on_create_project)
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    async def _on_create_project(self, name: str, description: str, location: str):
        """Handle project creation"""
        success = await self.project_manager.create_new_project(name, description, location)
        if success:
            # Update UI
            self.page.title = f"Canvas Editor - {name}"
            await self.state_manager.save_current_project_id(
                self.project_manager.current_project.id
            )
        else:
            # Show error
            error_dialog = ProjectErrorDialog("Failed to create project")
            self.page.overlay.append(error_dialog)
            error_dialog.open = True
        
        self.page.update()
    
    async def _on_window_resize(self, e):
        """Handle window resize"""
        await self.state_manager.save_window_state()
    
    async def _on_window_close(self, e):
        """Handle window close with enhanced state management"""
        try:
            # Save state
            await self.state_manager.save_window_state()
            await self.state_manager.save_panel_state(self.panel_sizes)
            
            # Shutdown enhanced state management system
            await self.state_manager.shutdown()
            
            # Clean up project manager
            if self.project_manager.auto_save_timer:
                self.project_manager.auto_save_timer.cancel()
                
        except Exception as e:
            print(f"Error during shutdown: {e}")