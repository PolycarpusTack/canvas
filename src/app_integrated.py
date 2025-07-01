"""
Enhanced Canvas Editor Application with Integrated System
Uses the cohesive UI integration for production-ready functionality

CLAUDE.md Implementation:
- #3.1: Clean, cohesive application architecture
- #6.2: Unified state management across all components
- #1.5: Performance-optimized application structure
- #2.1.1: Comprehensive error handling and validation
"""

import flet as ft
import asyncio
import logging
from typing import Optional, Dict, Any
from pathlib import Path

# Import integrated system
from ui.integrated_canvas_system import IntegratedCanvasSystem, SystemIntegrationConfig
from managers.enhanced_state import EnhancedStateManager
from managers.project_state_integrated import StateIntegratedProjectManager
from services.component_service import ComponentService
from services.export_service import ExportService
from ui.dialogs.project_dialog import NewProjectDialog, ImportProjectDialog, ProjectErrorDialog

logger = logging.getLogger(__name__)


class EnhancedCanvasEditor:
    """
    Enhanced Canvas Editor with integrated component system
    
    CLAUDE.md Implementation:
    - #3.1: Clean, unified application design
    - #6.2: Centralized state management
    - #1.5: Performance-optimized initialization
    - #2.1.1: Robust error handling throughout
    """
    
    def __init__(self, page: ft.Page):
        self.page = page
        
        # Core managers
        self.state_manager = EnhancedStateManager(page)
        self.project_manager: Optional[StateIntegratedProjectManager] = None
        
        # Services
        self.component_service = ComponentService()
        self.export_service = ExportService()
        
        # Integrated UI system
        self.integrated_system: Optional[IntegratedCanvasSystem] = None
        
        # Application state
        self.is_initialized = False
        self.current_project_path: Optional[Path] = None
        
        # Configuration
        self.system_config = SystemIntegrationConfig(
            enable_advanced_rendering=True,
            enable_rich_text_editor=True,
            enable_export_integration=True,
            enable_real_time_collaboration=False,
            performance_monitoring=True,
            auto_save_interval=30,
            max_undo_history=50
        )
    
    async def initialize(self):
        """
        Initialize the enhanced application
        
        CLAUDE.md Implementation:
        - #6.2: Async initialization with proper error handling
        - #1.5: Performance-optimized startup sequence
        """
        try:
            logger.info("Initializing Enhanced Canvas Editor...")
            
            # Set up page properties
            self._configure_page()
            
            # Initialize state management system
            await self.state_manager.initialize()
            logger.info("State management system initialized")
            
            # Create integrated project manager
            self.project_manager = StateIntegratedProjectManager(self.state_manager)
            logger.info("Project manager initialized")
            
            # Create integrated UI system
            self.integrated_system = IntegratedCanvasSystem(
                page=self.page,
                state_manager=self.state_manager,
                config=self.system_config
            )
            
            # Initialize the integrated system
            await self.integrated_system.initialize_async()
            logger.info("Integrated UI system initialized")
            
            # Set up event handlers
            self._setup_event_handlers()
            
            # Restore application state
            await self._restore_application_state()
            
            # Build and display UI
            self._build_application_ui()
            
            # Set initialization flag
            self.is_initialized = True
            
            logger.info("Enhanced Canvas Editor initialization complete")
            
        except Exception as e:
            logger.error(f"Error initializing Enhanced Canvas Editor: {e}")
            await self._handle_initialization_error(e)
    
    def _configure_page(self):
        """
        Configure page properties for enhanced experience
        
        CLAUDE.md Implementation:
        - #3.1: Consistent visual design
        - #9.1: Accessible page configuration
        """
        try:
            self.page.title = "Canvas Editor - Enhanced"
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self.page.padding = 0
            self.page.spacing = 0
            
            # Set window properties
            self.page.window.width = 1400
            self.page.window.height = 900
            self.page.window.min_width = 1200
            self.page.window.min_height = 700
            self.page.window.maximizable = True
            self.page.window.resizable = True
            
            # Set theme colors
            self.page.theme = ft.Theme(
                color_scheme_seed="#5E6AD2",
                use_material3=True
            )
            
        except Exception as e:
            logger.error(f"Error configuring page: {e}")
    
    def _setup_event_handlers(self):
        """
        Set up application-level event handlers
        
        CLAUDE.md Implementation:
        - #6.2: Centralized event handling
        - #2.1.1: Error handling in event callbacks
        """
        try:
            # Window event handlers
            self.page.window.on_resize = self._on_window_resize
            self.page.window.on_close = self._on_window_close
            
            # Integrated system event handlers
            if self.integrated_system:
                self.integrated_system.on_project_change = self._on_project_change
                self.integrated_system.on_export_complete = self._on_export_complete
                self.integrated_system.on_error = self._on_system_error
            
            # Keyboard shortcuts
            self.page.on_keyboard_event = self._on_keyboard_event
            
        except Exception as e:
            logger.error(f"Error setting up event handlers: {e}")
    
    async def _restore_application_state(self):
        """
        Restore previous application state
        
        CLAUDE.md Implementation:
        - #6.2: State persistence and restoration
        - #1.5: Optimized state loading
        """
        try:
            # Restore window state
            await self.state_manager.restore_window_state()
            
            # Restore last project if any
            last_project_id = await self.state_manager.get_current_project_id()
            if last_project_id and self.project_manager:
                try:
                    project_loaded = await self.project_manager.load_project_by_id(last_project_id)
                    if project_loaded:
                        logger.info(f"Restored last project: {last_project_id}")
                        self.page.title = f"Canvas Editor - {self.project_manager.current_project.name}"
                except Exception as e:
                    logger.warning(f"Failed to restore last project: {e}")
            
        except Exception as e:
            logger.error(f"Error restoring application state: {e}")
    
    def _build_application_ui(self):
        """
        Build the main application UI using integrated system
        
        CLAUDE.md Implementation:
        - #3.1: Clean, unified UI layout
        - #9.1: Accessible application structure
        """
        try:
            if not self.integrated_system:
                raise Exception("Integrated system not initialized")
            
            # Create application layout with integrated system
            self.page.add(self.integrated_system)
            
            # Show welcome dialog for new users (optional)
            if not self._has_existing_projects():
                self._show_welcome_dialog()
            
            logger.info("Application UI built successfully")
            
        except Exception as e:
            logger.error(f"Error building application UI: {e}")
            self._show_fallback_ui(str(e))
    
    def _show_fallback_ui(self, error_message: str):
        """
        Show fallback UI in case of system failure
        
        CLAUDE.md Implementation:
        - #2.1.1: Graceful degradation
        - #9.1: Accessible error state
        """
        try:
            error_container = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.ERROR_OUTLINE, size=64, color="#EF4444"),
                    ft.Text(
                        "Canvas Editor Initialization Failed",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color="#374151"
                    ),
                    ft.Text(
                        f"Error: {error_message}",
                        size=16,
                        color="#6B7280",
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.ElevatedButton(
                        "Reload Application",
                        on_click=lambda e: self.page.window.close()
                    ),
                    ft.TextButton(
                        "View Error Details",
                        on_click=lambda e: self._show_error_details(error_message)
                    )
                ], 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=16
                ),
                alignment=ft.alignment.center,
                expand=True,
                padding=40
            )
            
            self.page.add(error_container)
            
        except Exception as e:
            logger.error(f"Error showing fallback UI: {e}")
    
    def _show_welcome_dialog(self):
        """
        Show welcome dialog for new users
        
        CLAUDE.md Implementation:
        - #3.1: Welcoming user experience
        - #9.1: Accessible welcome interface
        """
        try:
            welcome_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Welcome to Canvas Editor"),
                content=ft.Container(
                    width=400,
                    content=ft.Column([
                        ft.Text(
                            "Create beautiful, responsive designs with our visual editor.",
                            size=16,
                            color="#6B7280"
                        ),
                        ft.Divider(),
                        ft.Text("Getting Started:", weight=ft.FontWeight.W_500),
                        ft.Text("• Drag components from the library", size=14),
                        ft.Text("• Customize properties in the panel", size=14),
                        ft.Text("• Export to your favorite framework", size=14),
                        ft.Text("• Use keyboard shortcuts for efficiency", size=14)
                    ], spacing=8)
                ),
                actions=[
                    ft.TextButton("Skip", on_click=lambda e: self._close_welcome_dialog()),
                    ft.ElevatedButton(
                        "Create New Project",
                        on_click=lambda e: self._show_new_project_dialog()
                    )
                ]
            )
            
            self.page.overlay.append(welcome_dialog)
            welcome_dialog.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error showing welcome dialog: {e}")
    
    def _close_welcome_dialog(self):
        """Close welcome dialog"""
        try:
            if self.page.overlay:
                self.page.overlay.clear()
                self.page.update()
        except Exception as e:
            logger.error(f"Error closing welcome dialog: {e}")
    
    async def _show_new_project_dialog(self):
        """
        Show new project creation dialog
        
        CLAUDE.md Implementation:
        - #3.1: Clean dialog design
        - #2.1.1: Project validation
        """
        try:
            self._close_welcome_dialog()
            
            dialog = NewProjectDialog(self._on_create_project)
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error showing new project dialog: {e}")
    
    async def _on_create_project(self, name: str, description: str, location: str):
        """
        Handle project creation
        
        CLAUDE.md Implementation:
        - #6.2: State-managed project creation
        - #2.1.1: Project validation and error handling
        """
        try:
            if not self.project_manager:
                raise Exception("Project manager not initialized")
            
            # Validate project data
            if not name or not name.strip():
                raise ValueError("Project name is required")
            
            # Create new project
            success = await self.project_manager.create_new_project(name, description, location)
            
            if success:
                # Update page title
                self.page.title = f"Canvas Editor - {name}"
                
                # Save current project ID
                await self.state_manager.save_current_project_id(
                    self.project_manager.current_project.id
                )
                
                # Close dialog
                if self.page.overlay:
                    self.page.overlay.clear()
                    self.page.update()
                
                # Show success message
                await self._show_success_message(f"Project '{name}' created successfully")
                
            else:
                raise Exception("Failed to create project")
                
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            await self._show_error_message(f"Failed to create project: {str(e)}")
    
    async def _on_window_resize(self, e):
        """Handle window resize events"""
        try:
            if self.is_initialized:
                await self.state_manager.save_window_state()
        except Exception as e:
            logger.error(f"Error handling window resize: {e}")
    
    async def _on_window_close(self, e):
        """
        Handle window close with proper cleanup
        
        CLAUDE.md Implementation:
        - #1.5: Proper resource cleanup
        - #6.2: State persistence on close
        """
        try:
            logger.info("Application closing, performing cleanup...")
            
            # Save current state
            if self.is_initialized:
                await self.state_manager.save_window_state()
                
                # Save current project if any
                if self.project_manager and self.project_manager.current_project:
                    await self.project_manager.save_project()
            
            # Cleanup integrated system
            if self.integrated_system:
                await self.integrated_system.cleanup()
            
            # Shutdown state management
            if self.state_manager:
                await self.state_manager.shutdown()
            
            logger.info("Application cleanup complete")
            
        except Exception as e:
            logger.error(f"Error during application shutdown: {e}")
    
    def _on_project_change(self, project_data):
        """Handle project changes from integrated system"""
        try:
            if project_data and hasattr(project_data, 'name'):
                self.page.title = f"Canvas Editor - {project_data.name}"
                self.page.update()
        except Exception as e:
            logger.error(f"Error handling project change: {e}")
    
    def _on_export_complete(self, export_result):
        """Handle export completion from integrated system"""
        try:
            logger.info(f"Export completed: {export_result}")
            # Additional export completion handling can be added here
        except Exception as e:
            logger.error(f"Error handling export completion: {e}")
    
    def _on_system_error(self, error_message: str):
        """Handle system errors from integrated system"""
        try:
            logger.error(f"System error: {error_message}")
            asyncio.create_task(self._show_error_message(error_message))
        except Exception as e:
            logger.error(f"Error handling system error: {e}")
    
    async def _on_keyboard_event(self, e: ft.KeyboardEvent):
        """
        Handle keyboard shortcuts
        
        CLAUDE.md Implementation:
        - #9.1: Accessible keyboard navigation
        - #1.5: Performance-optimized shortcut handling
        """
        try:
            if not self.is_initialized:
                return
            
            # Ctrl+S - Save
            if e.key == "s" and e.ctrl:
                if self.project_manager:
                    await self.project_manager.save_project()
                    await self._show_success_message("Project saved")
            
            # Ctrl+Z - Undo
            elif e.key == "z" and e.ctrl and not e.shift:
                await self.state_manager.undo()
            
            # Ctrl+Shift+Z or Ctrl+Y - Redo
            elif (e.key == "z" and e.ctrl and e.shift) or (e.key == "y" and e.ctrl):
                await self.state_manager.redo()
            
            # Ctrl+N - New Project
            elif e.key == "n" and e.ctrl:
                await self._show_new_project_dialog()
            
            # F11 - Toggle fullscreen
            elif e.key == "F11":
                self.page.window.full_screen = not self.page.window.full_screen
                self.page.update()
            
        except Exception as e:
            logger.error(f"Error handling keyboard event: {e}")
    
    async def _show_success_message(self, message: str):
        """Show success message to user"""
        try:
            if self.integrated_system:
                await self.integrated_system._show_success_feedback(message)
        except Exception as e:
            logger.error(f"Error showing success message: {e}")
    
    async def _show_error_message(self, message: str):
        """Show error message to user"""
        try:
            if self.integrated_system:
                await self.integrated_system._show_error_feedback(message)
        except Exception as e:
            logger.error(f"Error showing error message: {e}")
    
    def _has_existing_projects(self) -> bool:
        """Check if user has existing projects"""
        try:
            # This would check for existing projects in the user's data directory
            # For now, return False to always show welcome dialog
            return False
        except Exception as e:
            logger.error(f"Error checking existing projects: {e}")
            return False
    
    async def _handle_initialization_error(self, error: Exception):
        """
        Handle initialization errors gracefully
        
        CLAUDE.md Implementation:
        - #2.1.1: Comprehensive error handling
        - #9.1: Accessible error reporting
        """
        try:
            logger.error(f"Initialization error: {error}")
            
            # Show error dialog
            error_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Initialization Error"),
                content=ft.Container(
                    width=400,
                    content=ft.Column([
                        ft.Text(
                            "Failed to initialize Canvas Editor. This might be due to:",
                            size=14,
                            color="#6B7280"
                        ),
                        ft.Text("• Missing required dependencies", size=12),
                        ft.Text("• Corrupted application data", size=12),
                        ft.Text("• Insufficient system resources", size=12),
                        ft.Divider(),
                        ft.Text(f"Error details: {str(error)}", size=12, color="#EF4444")
                    ], spacing=8)
                ),
                actions=[
                    ft.TextButton("Close", on_click=lambda e: self.page.window.close()),
                    ft.ElevatedButton(
                        "Reset Application",
                        on_click=lambda e: self._reset_application_data()
                    )
                ]
            )
            
            self.page.overlay.append(error_dialog)
            error_dialog.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error handling initialization error: {e}")
    
    def _reset_application_data(self):
        """Reset application data (for error recovery)"""
        try:
            # In a real implementation, this would clear user data
            # For now, just close the application
            self.page.window.close()
        except Exception as e:
            logger.error(f"Error resetting application data: {e}")
    
    def _show_error_details(self, error_message: str):
        """Show detailed error information"""
        try:
            details_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Error Details"),
                content=ft.Container(
                    width=500,
                    height=300,
                    content=ft.TextField(
                        value=error_message,
                        multiline=True,
                        read_only=True,
                        min_lines=10,
                        max_lines=10
                    )
                ),
                actions=[
                    ft.TextButton("Close", on_click=lambda e: self._close_error_details())
                ]
            )
            
            self.page.overlay.append(details_dialog)
            details_dialog.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error showing error details: {e}")
    
    def _close_error_details(self):
        """Close error details dialog"""
        try:
            if self.page.overlay:
                self.page.overlay.clear()
                self.page.update()
        except Exception as e:
            logger.error(f"Error closing error details: {e}")


# Factory function for creating the enhanced editor
def create_enhanced_canvas_editor(page: ft.Page) -> EnhancedCanvasEditor:
    """
    Create enhanced Canvas Editor instance
    
    CLAUDE.md Implementation:
    - #3.1: Clean factory pattern
    - #4.1: Type-safe editor creation
    """
    try:
        return EnhancedCanvasEditor(page)
    except Exception as e:
        logger.error(f"Error creating enhanced canvas editor: {e}")
        raise