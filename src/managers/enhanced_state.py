"""
Enhanced State Manager that replaces the existing simple state manager.
Provides backward compatibility while using the new comprehensive state management system.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import flet as ft

from .state_integration import StateManagementSystem, StateContext
from .action_creators import ActionCreators

logger = logging.getLogger(__name__)


class EnhancedStateManager:
    """
    Enhanced state manager that provides backward compatibility with the existing interface
    while using the new comprehensive state management system under the hood.
    """
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.client_storage = page.client_storage
        
        # Initialize new state management system
        storage_path = Path.home() / ".canvas_editor" / "state"
        self.state_system = StateManagementSystem(
            storage_path=storage_path,
            enable_debug=True
        )
        
        # Compatibility cache for legacy methods
        self._state_cache: Dict[str, Any] = {}
        
        # Initialize flag
        self._initialized = False
        
        logger.info("EnhancedStateManager created")
    
    async def initialize(self):
        """Initialize the enhanced state management system"""
        if not self._initialized:
            await self.state_system.initialize()
            await self._migrate_legacy_state()
            self._initialized = True
            logger.info("EnhancedStateManager initialized")
    
    async def shutdown(self):
        """Shutdown the state management system"""
        if self._initialized:
            await self.state_system.shutdown()
            self._initialized = False
            logger.info("EnhancedStateManager shutdown")
    
    async def _migrate_legacy_state(self):
        """Migrate any existing legacy state to the new system"""
        try:
            # Check for existing state in client storage
            legacy_keys = [
                "canvas_editor_window_state",
                "canvas_editor_panel_state", 
                "canvas_editor_preferences",
                "canvas_editor_theme"
            ]
            
            for key in legacy_keys:
                try:
                    value = await self.client_storage.get_async(key)
                    if value:
                        self._state_cache[key] = value
                        logger.debug(f"Migrated legacy state: {key}")
                except:
                    pass  # Ignore errors for missing keys
            
            logger.info("Legacy state migration completed")
        except Exception as e:
            logger.error(f"Error during legacy state migration: {e}")
    
    # Backward compatibility methods (maintain existing interface)
    
    async def save_window_state(self):
        """Save window position and size (legacy compatibility)"""
        try:
            if not self._initialized:
                await self.initialize()
            
            # Update new state system
            window_state = {
                "width": self.page.window.width or 1400,
                "height": self.page.window.height or 900,
                "left": self.page.window.left or 100,
                "top": self.page.window.top or 100,
                "maximized": self.page.window.maximized or False
            }
            
            # Dispatch action to update state
            current_state = self.state_system.get_state("window")
            if (current_state.width != window_state["width"] or 
                current_state.height != window_state["height"] or
                current_state.left != window_state["left"] or
                current_state.top != window_state["top"] or
                current_state.maximized != window_state["maximized"]):
                
                # Create update action
                action = ActionCreators.update_preferences({
                    "window": window_state
                })
                await self.state_system.dispatch(action)
            
            logger.debug("Window state saved")
        except Exception as e:
            logger.error(f"Error saving window state: {e}")
    
    async def restore_window_state(self) -> bool:
        """Restore window position and size (legacy compatibility)"""
        try:
            if not self._initialized:
                await self.initialize()
            
            window_state = self.state_system.get_state("window")
            
            if window_state:
                self.page.window.width = window_state.width
                self.page.window.height = window_state.height
                self.page.window.left = window_state.left
                self.page.window.top = window_state.top
                
                if window_state.maximized:
                    self.page.window.maximized = True
                
                logger.debug("Window state restored")
                return True
            
        except Exception as e:
            logger.error(f"Error restoring window state: {e}")
        
        # Set defaults if restoration fails
        self.page.window.width = 1400
        self.page.window.height = 900
        self.page.window.center()
        return False
    
    async def save_panel_state(self, panel_sizes: Dict[str, float]):
        """Save panel sizes (legacy compatibility)"""
        try:
            if not self._initialized:
                await self.initialize()
            
            # Update each panel size through actions
            for panel_name, size in panel_sizes.items():
                current_size = getattr(
                    self.state_system.get_state("panels"), 
                    f"{panel_name}_width", 
                    None
                )
                
                if current_size != size:
                    await self.state_system.resize_panel(panel_name, size)
            
            logger.debug(f"Panel state saved: {panel_sizes}")
        except Exception as e:
            logger.error(f"Error saving panel state: {e}")
    
    async def restore_panel_state(self) -> Dict[str, float]:
        """Restore panel sizes (legacy compatibility)"""
        try:
            if not self._initialized:
                await self.initialize()
            
            panels_state = self.state_system.get_state("panels")
            
            restored_sizes = {
                "sidebar": panels_state.sidebar_width,
                "components": panels_state.components_width,
                "properties": panels_state.properties_width
            }
            
            logger.debug(f"Panel state restored: {restored_sizes}")
            return restored_sizes
            
        except Exception as e:
            logger.error(f"Error restoring panel state: {e}")
            
        # Return defaults on error
        return {
            "sidebar": 80,
            "components": 280,
            "properties": 320
        }
    
    async def save_preferences(self, preferences: Dict[str, Any]):
        """Save user preferences (legacy compatibility)"""
        try:
            if not self._initialized:
                await self.initialize()
            
            # Update preferences through action
            action = ActionCreators.update_preferences(preferences)
            await self.state_system.dispatch(action)
            
            logger.debug(f"Preferences saved: {list(preferences.keys())}")
        except Exception as e:
            logger.error(f"Error saving preferences: {e}")
    
    async def restore_preferences(self) -> Dict[str, Any]:
        """Restore user preferences (legacy compatibility)"""
        try:
            if not self._initialized:
                await self.initialize()
            
            preferences_state = self.state_system.get_state("preferences")
            preferences = preferences_state.to_dict()
            
            logger.debug(f"Preferences restored: {list(preferences.keys())}")
            return preferences
            
        except Exception as e:
            logger.error(f"Error restoring preferences: {e}")
            
        # Return defaults on error
        return {
            "auto_save": True,
            "auto_save_interval": 300,
            "show_grid": False,
            "snap_to_grid": False,
            "grid_size": 20,
            "theme": "light",
            "show_tooltips": True,
            "enable_animations": True
        }
    
    async def save_current_project_id(self, project_id: Optional[str]):
        """Save the ID of the currently open project (legacy compatibility)"""
        try:
            if not self._initialized:
                await self.initialize()
            
            if project_id:
                # Update project state
                current_project = self.state_system.get_state("project")
                if not current_project or current_project.id != project_id:
                    project_data = {"id": project_id, "name": "Current Project"}
                    await self.state_system.open_project(project_id, project_data)
            else:
                # Close current project
                await self.state_system.dispatch(ActionCreators.close_project())
                
        except Exception as e:
            logger.error(f"Error saving current project ID: {e}")
    
    async def get_current_project_id(self) -> Optional[str]:
        """Get the ID of the last opened project (legacy compatibility)"""
        try:
            if not self._initialized:
                await self.initialize()
            
            project_state = self.state_system.get_state("project")
            return project_state.id if project_state else None
            
        except Exception as e:
            logger.error(f"Error getting current project ID: {e}")
            return None
    
    async def save_theme(self, theme: str):
        """Save the current theme (legacy compatibility)"""
        try:
            if not self._initialized:
                await self.initialize()
            
            await self.state_system.change_theme(theme)
            
        except Exception as e:
            logger.error(f"Error saving theme: {e}")
    
    async def get_theme(self) -> str:
        """Get the saved theme (legacy compatibility)"""
        try:
            if not self._initialized:
                await self.initialize()
            
            return self.state_system.get_state("theme.mode")
            
        except Exception as e:
            logger.error(f"Error getting theme: {e}")
            return "light"
    
    async def clear_all_state(self):
        """Clear all saved state (legacy compatibility)"""
        try:
            if not self._initialized:
                await self.initialize()
            
            # Reset to default state
            await self.state_system.dispatch(ActionCreators.close_project())
            await self.state_system.change_theme("light")
            await self.state_system.clear_selection()
            
            # Clear client storage
            keys = [
                "canvas_editor_window_state",
                "canvas_editor_panel_state",
                "canvas_editor_preferences",
                "canvas_editor_current_project",
                "canvas_editor_theme"
            ]
            for key in keys:
                try:
                    await self.client_storage.remove_async(key)
                except:
                    pass
            
            self._state_cache.clear()
            logger.info("All state cleared")
            
        except Exception as e:
            logger.error(f"Error clearing state: {e}")
    
    def get_cached_state(self, key: str) -> Optional[Any]:
        """Get cached state value without async call (legacy compatibility)"""
        return self._state_cache.get(key)
    
    # New enhanced methods
    
    def get_state_system(self) -> StateManagementSystem:
        """Get access to the full state management system"""
        return self.state_system
    
    async def bind_component(self, ui_component, state_path: str, property_name: str, transformer=None):
        """Bind UI component to state"""
        if not self._initialized:
            await self.initialize()
        return self.state_system.bind_component(ui_component, state_path, property_name, transformer)
    
    async def subscribe_to_changes(self, path: str, callback, filter_fn=None):
        """Subscribe to state changes"""
        if not self._initialized:
            await self.initialize()
        return self.state_system.subscribe(path, callback, filter_fn)
    
    async def dispatch_action(self, action):
        """Dispatch an action to the state system"""
        if not self._initialized:
            await self.initialize()
        await self.state_system.dispatch(action)
    
    async def undo(self) -> bool:
        """Undo last action"""
        if not self._initialized:
            await self.initialize()
        return await self.state_system.undo()
    
    async def redo(self) -> bool:
        """Redo next action"""
        if not self._initialized:
            await self.initialize()
        return await self.state_system.redo()
    
    def can_undo(self) -> bool:
        """Check if undo is available"""
        return self.state_system.can_undo() if self._initialized else False
    
    def can_redo(self) -> bool:
        """Check if redo is available"""
        return self.state_system.can_redo() if self._initialized else False
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        if not self._initialized:
            return {}
        return self.state_system.get_performance_metrics()
    
    def export_debug_info(self) -> Dict[str, Any]:
        """Export debug information"""
        if not self._initialized:
            return {}
        return self.state_system.export_debug_info()


# Async context manager for automatic lifecycle management
class ManagedStateManager:
    """Context manager for automatic state manager lifecycle"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.state_manager = None
    
    async def __aenter__(self) -> EnhancedStateManager:
        self.state_manager = EnhancedStateManager(self.page)
        await self.state_manager.initialize()
        return self.state_manager
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.state_manager:
            await self.state_manager.shutdown()


# Factory function for backward compatibility
def create_state_manager(page: ft.Page) -> EnhancedStateManager:
    """Factory function to create enhanced state manager"""
    return EnhancedStateManager(page)