"""Application state management"""

import json
from datetime import datetime
from typing import Dict, Any, Optional
import flet as ft

from config.constants import (
    STORAGE_KEY_WINDOW, STORAGE_KEY_PANELS, STORAGE_KEY_PREFERENCES,
    STORAGE_KEY_CURRENT_PROJECT, STORAGE_KEY_THEME,
    SIDEBAR_WIDTH, COMPONENTS_WIDTH, PROPERTIES_WIDTH
)


class StateManager:
    """Manages application state persistence"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.client_storage = page.client_storage
        self._state_cache: Dict[str, Any] = {}
    
    async def save_window_state(self):
        """Save window position and size"""
        try:
            state = {
                "width": self.page.window.width,
                "height": self.page.window.height,
                "left": self.page.window.left,
                "top": self.page.window.top,
                "maximized": self.page.window.maximized,
                "timestamp": datetime.now().isoformat()
            }
            await self.client_storage.set_async(STORAGE_KEY_WINDOW, json.dumps(state))
            self._state_cache[STORAGE_KEY_WINDOW] = state
        except Exception as e:
            print(f"Error saving window state: {e}")
    
    async def restore_window_state(self) -> bool:
        """Restore window position and size"""
        try:
            state_str = await self.client_storage.get_async(STORAGE_KEY_WINDOW)
            if state_str:
                state = json.loads(state_str)
                
                # Validate state
                if self._validate_window_state(state):
                    self.page.window.width = state.get("width", 1400)
                    self.page.window.height = state.get("height", 900)
                    self.page.window.left = state.get("left", 100)
                    self.page.window.top = state.get("top", 100)
                    
                    if state.get("maximized", False):
                        self.page.window.maximized = True
                    
                    self._state_cache[STORAGE_KEY_WINDOW] = state
                    return True
        except Exception as e:
            print(f"Error restoring window state: {e}")
        
        # Set defaults if restoration fails
        self.page.window.width = 1400
        self.page.window.height = 900
        self.page.window.center()
        return False
    
    def _validate_window_state(self, state: Dict[str, Any]) -> bool:
        """Validate window state values"""
        try:
            width = state.get("width", 0)
            height = state.get("height", 0)
            left = state.get("left", 0)
            top = state.get("top", 0)
            
            # Basic validation
            if width < 800 or height < 600:
                return False
            
            # Check if window would be visible (basic check)
            # TODO: Enhance with actual screen bounds detection
            if left < -width or top < -height:
                return False
            
            # Check timestamp (ignore if too old - 30 days)
            if "timestamp" in state:
                saved_time = datetime.fromisoformat(state["timestamp"])
                age = datetime.now() - saved_time
                if age.days > 30:
                    return False
            
            return True
            
        except:
            return False
    
    async def save_panel_state(self, panel_sizes: Dict[str, float]):
        """Save panel sizes"""
        try:
            state = {
                "sidebar_width": panel_sizes.get("sidebar", SIDEBAR_WIDTH),
                "components_width": panel_sizes.get("components", COMPONENTS_WIDTH),
                "properties_width": panel_sizes.get("properties", PROPERTIES_WIDTH),
                "timestamp": datetime.now().isoformat()
            }
            await self.client_storage.set_async(STORAGE_KEY_PANELS, json.dumps(state))
            self._state_cache[STORAGE_KEY_PANELS] = state
        except Exception as e:
            print(f"Error saving panel state: {e}")
    
    async def restore_panel_state(self) -> Dict[str, float]:
        """Restore panel sizes"""
        default_sizes = {
            "sidebar": SIDEBAR_WIDTH,
            "components": COMPONENTS_WIDTH,
            "properties": PROPERTIES_WIDTH
        }
        
        try:
            state_str = await self.client_storage.get_async(STORAGE_KEY_PANELS)
            if state_str:
                state = json.loads(state_str)
                restored_sizes = {
                    "sidebar": state.get("sidebar_width", SIDEBAR_WIDTH),
                    "components": state.get("components_width", COMPONENTS_WIDTH),
                    "properties": state.get("properties_width", PROPERTIES_WIDTH)
                }
                self._state_cache[STORAGE_KEY_PANELS] = state
                return restored_sizes
        except Exception as e:
            print(f"Error restoring panel state: {e}")
        
        return default_sizes
    
    async def save_preferences(self, preferences: Dict[str, Any]):
        """Save user preferences"""
        try:
            preferences["timestamp"] = datetime.now().isoformat()
            await self.client_storage.set_async(STORAGE_KEY_PREFERENCES, json.dumps(preferences))
            self._state_cache[STORAGE_KEY_PREFERENCES] = preferences
        except Exception as e:
            print(f"Error saving preferences: {e}")
    
    async def restore_preferences(self) -> Dict[str, Any]:
        """Restore user preferences"""
        default_preferences = {
            "auto_save": True,
            "auto_save_interval": 300,
            "show_grid": False,
            "snap_to_grid": False,
            "grid_size": 20,
            "theme": "light",
            "show_tooltips": True,
            "enable_animations": True
        }
        
        try:
            pref_str = await self.client_storage.get_async(STORAGE_KEY_PREFERENCES)
            if pref_str:
                preferences = json.loads(pref_str)
                # Merge with defaults to ensure all keys exist
                default_preferences.update(preferences)
                self._state_cache[STORAGE_KEY_PREFERENCES] = default_preferences
                return default_preferences
        except Exception as e:
            print(f"Error restoring preferences: {e}")
        
        return default_preferences
    
    async def save_current_project_id(self, project_id: Optional[str]):
        """Save the ID of the currently open project"""
        try:
            if project_id:
                await self.client_storage.set_async(STORAGE_KEY_CURRENT_PROJECT, project_id)
            else:
                await self.client_storage.remove_async(STORAGE_KEY_CURRENT_PROJECT)
        except Exception as e:
            print(f"Error saving current project ID: {e}")
    
    async def get_current_project_id(self) -> Optional[str]:
        """Get the ID of the last opened project"""
        try:
            return await self.client_storage.get_async(STORAGE_KEY_CURRENT_PROJECT)
        except:
            return None
    
    async def save_theme(self, theme: str):
        """Save the current theme"""
        try:
            await self.client_storage.set_async(STORAGE_KEY_THEME, theme)
            self._state_cache[STORAGE_KEY_THEME] = theme
        except Exception as e:
            print(f"Error saving theme: {e}")
    
    async def get_theme(self) -> str:
        """Get the saved theme"""
        try:
            theme = await self.client_storage.get_async(STORAGE_KEY_THEME)
            return theme or "light"
        except:
            return "light"
    
    async def clear_all_state(self):
        """Clear all saved state (for debugging/reset)"""
        try:
            keys = [
                STORAGE_KEY_WINDOW,
                STORAGE_KEY_PANELS,
                STORAGE_KEY_PREFERENCES,
                STORAGE_KEY_CURRENT_PROJECT,
                STORAGE_KEY_THEME
            ]
            for key in keys:
                await self.client_storage.remove_async(key)
            self._state_cache.clear()
        except Exception as e:
            print(f"Error clearing state: {e}")
    
    def get_cached_state(self, key: str) -> Optional[Any]:
        """Get cached state value without async call"""
        return self._state_cache.get(key)