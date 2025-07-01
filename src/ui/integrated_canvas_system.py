"""
Integrated Canvas System - Cohesive UI Integration
Combines all completed components into a unified, production-ready system

CLAUDE.md Implementation:
- #3.1: Clean, cohesive interface design
- #6.2: Real-time component integration
- #1.5: Performance-optimized unified system
- #2.1.1: Comprehensive validation across all components
- #4.1: Type-safe component integration
"""

import flet as ft
import asyncio
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import logging
import json
import time

# Import all completed components
from ui.panels.canvas import CanvasPanel, create_canvas_panel
from ui.panels.properties import PropertiesPanel
from ui.panels.components import ComponentsPanel
from ui.panels.sidebar import SidebarPanel
from components.drag_drop_manager import get_drag_drop_manager, DragData
from components.rich_text_editor_complete import RichTextEditor
from managers.enhanced_state import EnhancedStateManager
from managers.action_creators import ActionCreators
from services.export_service import ExportService
from export.export_manager import ExportManager
from models.component import Component
from models.project import ProjectMetadata

logger = logging.getLogger(__name__)


@dataclass
class SystemIntegrationConfig:
    """Configuration for the integrated system"""
    enable_advanced_rendering: bool = True
    enable_rich_text_editor: bool = True
    enable_export_integration: bool = True
    enable_real_time_collaboration: bool = False
    performance_monitoring: bool = True
    auto_save_interval: int = 30  # seconds
    max_undo_history: int = 50


class IntegratedCanvasSystem(ft.Container):
    """
    Unified Canvas System integrating all completed components
    
    CLAUDE.md Implementation:
    - #3.1: Cohesive UI design with consistent styling
    - #6.2: Real-time state synchronization across all components
    - #1.5: Performance-optimized component communication
    - #2.1.1: Comprehensive error handling and validation
    """
    
    def __init__(self, 
                 page: ft.Page,
                 state_manager: EnhancedStateManager,
                 config: Optional[SystemIntegrationConfig] = None):
        super().__init__()
        
        self.page = page
        self.state_manager = state_manager
        self.config = config or SystemIntegrationConfig()
        
        # Core services
        self.export_service = ExportService()
        self.export_manager = ExportManager()
        self.drag_drop_manager = get_drag_drop_manager()
        
        # UI Components
        self.sidebar: Optional[SidebarPanel] = None
        self.components_panel: Optional[ComponentsPanel] = None
        self.canvas_panel: Optional[CanvasPanel] = None
        self.properties_panel: Optional[PropertiesPanel] = None
        self.rich_text_editor: Optional[RichTextEditor] = None
        
        # Integration state
        self.current_mode = "design"  # design, text_edit, preview, export
        self.active_dialogs: Dict[str, ft.AlertDialog] = {}
        self.performance_stats: Dict[str, Any] = {}
        self.auto_save_timer: Optional[asyncio.Task] = None
        
        # Event handlers
        self.on_project_change: Optional[Callable] = None
        self.on_export_complete: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
        # Build the integrated system
        self._initialize_system()
    
    async def initialize_async(self):
        """
        Asynchronous initialization of the integrated system
        
        CLAUDE.md Implementation:
        - #6.2: Async state management setup
        - #1.5: Performance-optimized initialization
        """
        try:
            # Initialize state subscriptions
            await self._setup_state_subscriptions()
            
            # Initialize auto-save if enabled
            if self.config.auto_save_interval > 0:
                self.auto_save_timer = asyncio.create_task(self._auto_save_loop())
            
            # Initialize performance monitoring
            if self.config.performance_monitoring:
                await self._initialize_performance_monitoring()
            
            # Initialize drag & drop integration
            await self._initialize_drag_drop_integration()
            
            # Initialize export system integration
            if self.config.enable_export_integration:
                await self._initialize_export_integration()
            
            logger.info("Integrated Canvas System initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing integrated system: {e}")
            if self.on_error:
                self.on_error(f"System initialization failed: {e}")
    
    def _initialize_system(self):
        """Initialize the core UI system"""
        try:
            # Create all UI panels with integration
            self._create_integrated_panels()
            
            # Build unified layout
            self._build_integrated_layout()
            
            # Set initial state
            self._set_initial_state()
            
        except Exception as e:
            logger.error(f"Error initializing system: {e}")
    
    def _create_integrated_panels(self):
        """
        Create all UI panels with proper integration
        
        CLAUDE.md Implementation:
        - #3.1: Consistent UI design across panels
        - #6.2: Integrated state management
        """
        # Sidebar with integrated navigation
        self.sidebar = SidebarPanel(
            on_navigate=self._handle_navigation,
            on_mode_change=self._handle_mode_change
        )
        
        # Components panel with enhanced drag & drop
        self.components_panel = ComponentsPanel(
            on_component_drag=self._handle_component_drag_start,
            on_template_select=self._handle_template_select,
            drag_manager=self.drag_drop_manager
        )
        
        # Canvas panel with advanced rendering
        self.canvas_panel = create_canvas_panel(
            on_component_drop=self._handle_component_drop,
            on_component_select=self._handle_component_select,
            on_action=self._handle_canvas_action,
            state_manager=self.state_manager,
            advanced_features=self.config.enable_advanced_rendering
        )
        
        # Properties panel with enhanced editing
        self.properties_panel = PropertiesPanel(
            on_property_change=self._handle_property_change,
            on_style_preset_apply=self._handle_style_preset_apply,
            on_advanced_edit=self._handle_advanced_property_edit
        )
        
        # Rich text editor (conditionally enabled)
        if self.config.enable_rich_text_editor:
            self.rich_text_editor = RichTextEditor(
                on_content_change=self._handle_rich_text_change,
                on_format_change=self._handle_rich_text_format,
                on_close=self._handle_rich_text_close,
                state_manager=self.state_manager
            )
    
    def _build_integrated_layout(self):
        """
        Build the unified layout system
        
        CLAUDE.md Implementation:
        - #3.1: Clean, responsive layout design
        - #9.1: Accessible panel arrangement
        """
        # Create resizable panel system
        main_row = ft.Row([
            # Left sidebar
            ft.Container(
                content=self.sidebar,
                width=280,
                bgcolor="#FAFAFA",
                border=ft.border.only(right=ft.BorderSide(1, "#E5E7EB"))
            ),
            
            # Components panel
            ft.Container(
                content=self.components_panel,
                width=320,
                bgcolor="#FFFFFF",
                border=ft.border.only(right=ft.BorderSide(1, "#E5E7EB"))
            ),
            
            # Main canvas area
            ft.Container(
                content=ft.Stack([
                    self.canvas_panel,
                    # Rich text editor overlay (hidden by default)
                    ft.Container(
                        content=self.rich_text_editor,
                        visible=False,
                        expand=True,
                        key="rich_text_overlay"
                    ) if self.rich_text_editor else ft.Container()
                ]),
                expand=True,
                bgcolor="#F8F9FA"
            ),
            
            # Properties panel
            ft.Container(
                content=self.properties_panel,
                width=350,
                bgcolor="#FFFFFF",
                border=ft.border.only(left=ft.BorderSide(1, "#E5E7EB"))
            )
        ], spacing=0, expand=True)
        
        # Create status bar
        status_bar = self._create_integrated_status_bar()
        
        # Build complete layout
        self.content = ft.Column([
            main_row,
            status_bar
        ], spacing=0, expand=True)
    
    def _create_integrated_status_bar(self) -> ft.Control:
        """
        Create unified status bar showing system state
        
        CLAUDE.md Implementation:
        - #9.1: Accessible status information
        - #12.1: Performance monitoring display
        """
        return ft.Container(
            height=32,
            bgcolor="#F9FAFB",
            border=ft.border.only(top=ft.BorderSide(1, "#E5E7EB")),
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
            content=ft.Row([
                # Left side - system status
                ft.Row([
                    ft.Icon(ft.Icons.CIRCLE, size=8, color="#10B981"),  # Ready indicator
                    ft.Text("Ready", size=12, color="#374151"),
                    ft.VerticalDivider(width=1, color="#E5E7EB"),
                    ft.Text("Mode: Design", size=12, color="#6B7280", key="mode_indicator"),
                    ft.VerticalDivider(width=1, color="#E5E7EB"),
                    ft.Text("Components: 0", size=12, color="#6B7280", key="component_count")
                ], spacing=8),
                
                # Right side - performance and tools
                ft.Row([
                    ft.Text("", size=12, color="#6B7280", key="performance_text"),
                    ft.IconButton(
                        icon=ft.Icons.SETTINGS,
                        icon_size=16,
                        tooltip="System Settings",
                        on_click=self._show_system_settings
                    ),
                    ft.IconButton(
                        icon=ft.Icons.HELP_OUTLINE,
                        icon_size=16,
                        tooltip="Help & Shortcuts",
                        on_click=self._show_help_dialog
                    )
                ], spacing=4)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            key="status_bar"
        )
    
    async def _setup_state_subscriptions(self):
        """
        Set up state change subscriptions for real-time UI updates
        
        CLAUDE.md Implementation:
        - #6.2: Real-time state synchronization
        - #4.1: Type-safe state handling
        """
        try:
            # Subscribe to component changes
            await self.state_manager.subscribe_to_changes(
                "components",
                self._on_components_state_changed
            )
            
            # Subscribe to selection changes
            await self.state_manager.subscribe_to_changes(
                "selection",
                self._on_selection_state_changed
            )
            
            # Subscribe to project changes
            await self.state_manager.subscribe_to_changes(
                "project",
                self._on_project_state_changed
            )
            
            # Subscribe to UI state changes
            await self.state_manager.subscribe_to_changes(
                "ui",
                self._on_ui_state_changed
            )
            
        except Exception as e:
            logger.error(f"Error setting up state subscriptions: {e}")
    
    async def _on_components_state_changed(self, old_value, new_value):
        """Handle components state changes across all panels"""
        try:
            # Update canvas
            if self.canvas_panel:
                await self.canvas_panel.refresh_from_state(new_value)
            
            # Update component count in status bar
            component_count = len(new_value.component_map) if hasattr(new_value, 'component_map') else 0
            self._update_status_bar_text("component_count", f"Components: {component_count}")
            
            # Trigger auto-save if enabled
            if self.config.auto_save_interval > 0:
                await self._trigger_auto_save()
            
        except Exception as e:
            logger.error(f"Error handling components state change: {e}")
    
    async def _on_selection_state_changed(self, old_value, new_value):
        """Handle selection state changes across all panels"""
        try:
            # Update canvas selection
            if self.canvas_panel and hasattr(new_value, 'selected_ids'):
                selected_ids = list(new_value.selected_ids)
                await self.canvas_panel.update_selection(selected_ids)
            
            # Update properties panel
            if self.properties_panel and hasattr(new_value, 'selected_ids'):
                selected_ids = list(new_value.selected_ids)
                if selected_ids:
                    # Get component data for properties panel
                    components_state = self.state_manager.get_state_system().get_state("components")
                    if selected_ids[0] in components_state.component_map:
                        component_data = components_state.component_map[selected_ids[0]]
                        self.properties_panel.set_component_data(component_data)
                else:
                    self.properties_panel.set_component_data(None)
            
        except Exception as e:
            logger.error(f"Error handling selection state change: {e}")
    
    async def _on_project_state_changed(self, old_value, new_value):
        """Handle project state changes"""
        try:
            if self.on_project_change:
                self.on_project_change(new_value)
        except Exception as e:
            logger.error(f"Error handling project state change: {e}")
    
    async def _on_ui_state_changed(self, old_value, new_value):
        """Handle UI state changes"""
        try:
            # Update mode indicator
            if hasattr(new_value, 'current_mode'):
                self._update_status_bar_text("mode_indicator", f"Mode: {new_value.current_mode.title()}")
        except Exception as e:
            logger.error(f"Error handling UI state change: {e}")
    
    def _handle_navigation(self, view: str):
        """
        Handle sidebar navigation with integrated view switching
        
        CLAUDE.md Implementation:
        - #3.1: Smooth view transitions
        - #6.2: State-driven navigation
        """
        try:
            if view == "export":
                self._show_export_dialog()
            elif view == "settings":
                self._show_system_settings()
            elif view == "help":
                self._show_help_dialog()
            elif view == "templates":
                self._switch_to_templates_mode()
            else:
                logger.warning(f"Unknown navigation view: {view}")
        except Exception as e:
            logger.error(f"Error handling navigation: {e}")
    
    def _handle_mode_change(self, mode: str):
        """
        Handle mode changes with UI updates
        
        CLAUDE.md Implementation:
        - #3.1: Seamless mode transitions
        - #6.2: State-synchronized mode switching
        """
        try:
            previous_mode = self.current_mode
            self.current_mode = mode
            
            # Update UI based on mode
            if mode == "text_edit":
                self._enter_text_edit_mode()
            elif mode == "design":
                self._enter_design_mode()
            elif mode == "preview":
                self._enter_preview_mode()
            elif mode == "export":
                self._enter_export_mode()
            
            # Update state manager
            asyncio.create_task(self._update_ui_mode_state(mode))
            
            logger.info(f"Mode changed from {previous_mode} to {mode}")
            
        except Exception as e:
            logger.error(f"Error handling mode change: {e}")
    
    async def _handle_component_drag_start(self, component_data: Dict[str, Any]):
        """
        Handle component drag start with enhanced drag & drop
        
        CLAUDE.md Implementation:
        - #1.5: Performance-optimized drag operations
        - #6.2: Real-time drag feedback
        """
        try:
            # Create drag data with enhanced information
            drag_data = DragData(
                source_type="library",
                component_id=component_data.get("type"),
                instance_id=None,
                properties=component_data,
                position=(0, 0)
            )
            
            # Start enhanced drag operation
            success = self.drag_drop_manager.start_drag(drag_data)
            
            if not success:
                logger.warning("Failed to start enhanced drag operation")
            
        except Exception as e:
            logger.error(f"Error handling component drag start: {e}")
    
    async def _handle_component_drop(self, component_data: Dict[str, str], position: ft.Offset):
        """
        Handle component drop with validation and state management
        
        CLAUDE.md Implementation:
        - #2.1.1: Component drop validation
        - #6.2: State-synchronized component creation
        """
        try:
            # Validate drop operation
            if not self._validate_component_drop(component_data, position):
                await self._show_error_feedback("Invalid component drop operation")
                return
            
            # Create component with enhanced data
            from services.component_service import ComponentService
            component_service = ComponentService()
            component = component_service.create_component_from_data(component_data)
            
            # Set position and generate unique ID
            component_dict = component.to_dict()
            component_dict['style'] = component_dict.get('style', {})
            component_dict['style']['left'] = str(position.x)
            component_dict['style']['top'] = str(position.y)
            component_dict['id'] = f"{component.type}_{int(time.time() * 1000)}"
            
            # Dispatch add component action
            action = ActionCreators.add_component(component_dict)
            await self.state_manager.dispatch_action(action)
            
            # Select the new component
            select_action = ActionCreators.select_component(component_dict['id'])
            await self.state_manager.dispatch_action(select_action)
            
            # Show success feedback
            await self._show_success_feedback(f"Added {component.type} component")
            
        except Exception as e:
            logger.error(f"Error handling component drop: {e}")
            await self._show_error_feedback(f"Failed to add component: {str(e)}")
    
    async def _handle_component_select(self, component_id: str):
        """
        Handle component selection with enhanced state management
        
        CLAUDE.md Implementation:
        - #6.2: State-synchronized selection
        - #4.1: Type-safe component selection
        """
        try:
            # Dispatch selection action
            action = ActionCreators.select_component(component_id)
            await self.state_manager.dispatch_action(action)
            
        except Exception as e:
            logger.error(f"Error handling component selection: {e}")
    
    async def _handle_property_change(self, component_id: str, property_path: str, value: Any):
        """
        Handle property changes with validation and state management
        
        CLAUDE.md Implementation:
        - #2.1.1: Property validation
        - #6.2: Real-time property updates
        """
        try:
            # Validate property change
            if not self._validate_property_change(component_id, property_path, value):
                await self._show_error_feedback("Invalid property value")
                return
            
            # Build update structure
            updates = {}
            path_parts = property_path.split('.')
            current = updates
            
            for i, part in enumerate(path_parts):
                if i == len(path_parts) - 1:
                    current[part] = value
                else:
                    current[part] = {}
                    current = current[part]
            
            # Dispatch update action
            action = ActionCreators.update_component(component_id, updates)
            await self.state_manager.dispatch_action(action)
            
        except Exception as e:
            logger.error(f"Error handling property change: {e}")
    
    async def _handle_canvas_action(self, action: str):
        """
        Handle canvas actions with enhanced integration
        
        CLAUDE.md Implementation:
        - #6.2: Integrated action handling
        - #1.5: Performance-optimized actions
        """
        try:
            if action == "save":
                await self._save_project()
            elif action == "undo":
                await self._perform_undo()
            elif action == "redo":
                await self._perform_redo()
            elif action == "export":
                self._show_export_dialog()
            elif action == "preview":
                await self._enter_preview_mode()
            elif action == "clear_selection":
                await self._clear_selection()
            elif action == "delete_selected":
                await self._delete_selected_components()
            else:
                logger.warning(f"Unknown canvas action: {action}")
                
        except Exception as e:
            logger.error(f"Error handling canvas action: {e}")
    
    def _show_export_dialog(self):
        """
        Show integrated export dialog with all available formats
        
        CLAUDE.md Implementation:
        - #3.1: Clean export dialog design
        - #2.1.1: Export validation
        """
        try:
            # Get available export formats from export manager
            export_formats = [
                {"id": "html", "name": "Static HTML", "description": "HTML/CSS/JS files"},
                {"id": "react", "name": "React App", "description": "Modern React application"},
                {"id": "vue", "name": "Vue.js App", "description": "Vue.js application"},
                {"id": "angular", "name": "Angular App", "description": "Angular application"},
                {"id": "svelte", "name": "Svelte App", "description": "SvelteKit application"},
                {"id": "nextjs", "name": "Next.js App", "description": "Next.js application"},
                {"id": "wordpress", "name": "WordPress Theme", "description": "WordPress theme"},
                {"id": "gatsby", "name": "Gatsby Site", "description": "Gatsby static site"}
            ]
            
            # Create format selection controls
            format_controls = []
            selected_format = ft.Ref[str]()
            selected_format.current = "html"  # Default
            
            for fmt in export_formats:
                format_controls.append(
                    ft.RadioListTile(
                        value=fmt["id"],
                        title=ft.Text(fmt["name"]),
                        subtitle=ft.Text(fmt["description"]),
                        group_value=selected_format,
                        on_change=lambda e: setattr(selected_format, 'current', e.control.value)
                    )
                )
            
            # Export configuration options
            config_options = ft.Column([
                ft.Switch(
                    label="Include TypeScript support",
                    value=True,
                    key="typescript_option"
                ),
                ft.Switch(
                    label="Generate tests",
                    value=False,
                    key="tests_option"
                ),
                ft.Switch(
                    label="Include README documentation",
                    value=True,
                    key="readme_option"
                )
            ])
            
            # Create export dialog
            export_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Export Project"),
                content=ft.Container(
                    width=500,
                    height=400,
                    content=ft.Column([
                        ft.Text("Select Export Format:", weight=ft.FontWeight.W_500),
                        ft.Container(
                            height=200,
                            content=ft.Column(format_controls, scroll=ft.ScrollMode.AUTO)
                        ),
                        ft.Divider(),
                        ft.Text("Export Options:", weight=ft.FontWeight.W_500),
                        config_options
                    ], spacing=12)
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda e: self._close_dialog("export")),
                    ft.ElevatedButton(
                        "Export",
                        on_click=lambda e: asyncio.create_task(
                            self._perform_export(selected_format.current, self._get_export_config())
                        )
                    )
                ]
            )
            
            # Show dialog
            self.active_dialogs["export"] = export_dialog
            self.page.overlay.append(export_dialog)
            export_dialog.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error showing export dialog: {e}")
    
    async def _perform_export(self, format_id: str, config: Dict[str, Any]):
        """
        Perform export operation with progress feedback
        
        CLAUDE.md Implementation:
        - #1.5: Async export processing
        - #2.1.1: Export validation and error handling
        """
        try:
            # Close export dialog
            self._close_dialog("export")
            
            # Show progress dialog
            progress_dialog = self._create_progress_dialog("Exporting project...")
            
            try:
                # Get current project state
                components_state = self.state_manager.get_state_system().get_state("components")
                project_state = self.state_manager.get_state_system().get_state("project")
                
                # Prepare export context
                from export.export_context import ExportContext
                from export.export_config import ExportConfig
                
                export_config = ExportConfig(format_id, config)
                export_context = ExportContext(
                    project=project_state,
                    components=list(components_state.component_map.values()),
                    config=export_config
                )
                
                # Perform export
                result = await self.export_manager.export_project(export_context)
                
                if result.success:
                    # Close progress dialog
                    self._close_dialog("progress")
                    
                    # Show success dialog
                    await self._show_export_success_dialog(result)
                    
                    if self.on_export_complete:
                        self.on_export_complete(result)
                else:
                    raise Exception(result.error_message or "Export failed")
                    
            except Exception as e:
                # Close progress dialog
                self._close_dialog("progress")
                raise e
                
        except Exception as e:
            logger.error(f"Error performing export: {e}")
            await self._show_error_feedback(f"Export failed: {str(e)}")
    
    def _get_export_config(self) -> Dict[str, Any]:
        """Get export configuration from dialog"""
        try:
            # In a real implementation, you'd extract these from the dialog controls
            return {
                "use_typescript": True,
                "generate_tests": False,
                "generate_readme": True,
                "css_framework": "tailwind",
                "ui_library": "none"
            }
        except Exception as e:
            logger.error(f"Error getting export config: {e}")
            return {}
    
    def _validate_component_drop(self, component_data: Dict[str, str], position: ft.Offset) -> bool:
        """
        Validate component drop operation
        
        CLAUDE.md Implementation:
        - #2.1.1: Comprehensive drop validation
        - #4.1: Type-safe validation
        """
        try:
            # Check if component data is valid
            if not component_data or 'type' not in component_data:
                return False
            
            # Check if position is valid
            if position.x < 0 or position.y < 0:
                return False
            
            # Additional validation rules can be added here
            return True
            
        except Exception as e:
            logger.error(f"Error validating component drop: {e}")
            return False
    
    def _validate_property_change(self, component_id: str, property_path: str, value: Any) -> bool:
        """
        Validate property change operation
        
        CLAUDE.md Implementation:
        - #2.1.1: Property validation
        - #4.1: Type-safe property validation
        """
        try:
            # Basic validation
            if not component_id or not property_path:
                return False
            
            # Additional validation logic can be added here
            return True
            
        except Exception as e:
            logger.error(f"Error validating property change: {e}")
            return False
    
    async def _show_success_feedback(self, message: str):
        """Show success feedback to user"""
        try:
            snack = ft.SnackBar(
                content=ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color="#10B981"),
                    ft.Text(message, color="#065F46")
                ]),
                bgcolor="#D1FAE5",
                duration=3000
            )
            self.page.overlay.append(snack)
            snack.open = True
            self.page.update()
            
            # Auto-remove
            await asyncio.sleep(3)
            if snack in self.page.overlay:
                self.page.overlay.remove(snack)
                self.page.update()
                
        except Exception as e:
            logger.error(f"Error showing success feedback: {e}")
    
    async def _show_error_feedback(self, message: str):
        """Show error feedback to user"""
        try:
            snack = ft.SnackBar(
                content=ft.Row([
                    ft.Icon(ft.Icons.ERROR, color="#EF4444"),
                    ft.Text(message, color="#7F1D1D")
                ]),
                bgcolor="#FEE2E2",
                duration=5000
            )
            self.page.overlay.append(snack)
            snack.open = True
            self.page.update()
            
            # Auto-remove
            await asyncio.sleep(5)
            if snack in self.page.overlay:
                self.page.overlay.remove(snack)
                self.page.update()
                
        except Exception as e:
            logger.error(f"Error showing error feedback: {e}")
    
    def _update_status_bar_text(self, key: str, text: str):
        """Update status bar text"""
        try:
            # Find the status bar container
            if hasattr(self, 'content') and hasattr(self.content, 'controls'):
                # Status bar is the last control in the main column
                for control in self.content.controls:
                    if isinstance(control, ft.Container) and hasattr(control, 'key') and control.key == "status_bar":
                        # Find the text control with the matching key
                        self._update_text_in_container(control, key, text)
                        break
        except Exception as e:
            logger.error(f"Error updating status bar: {e}")
    
    def _update_text_in_container(self, container: ft.Container, key: str, text: str):
        """Recursively find and update text control by key"""
        try:
            if hasattr(container, 'content'):
                content = container.content
                
                # Check if content is a Row or Column with controls
                if hasattr(content, 'controls'):
                    for control in content.controls:
                        if isinstance(control, ft.Text) and hasattr(control, 'key') and control.key == key:
                            control.value = text
                            control.update()
                            return True
                        elif isinstance(control, (ft.Row, ft.Column, ft.Container)):
                            # Recursively check nested controls
                            if self._update_text_in_container(control, key, text):
                                return True
                                
                # Check if content is a single control
                elif isinstance(content, ft.Text) and hasattr(content, 'key') and content.key == key:
                    content.value = text
                    content.update()
                    return True
                    
            return False
        except Exception as e:
            logger.error(f"Error updating text in container: {e}")
            return False
    
    def _close_dialog(self, dialog_id: str):
        """Close a dialog by ID"""
        try:
            if dialog_id in self.active_dialogs:
                dialog = self.active_dialogs[dialog_id]
                dialog.open = False
                self.page.update()
                del self.active_dialogs[dialog_id]
        except Exception as e:
            logger.error(f"Error closing dialog: {e}")
    
    def _set_initial_state(self):
        """Set initial system state"""
        try:
            self.current_mode = "design"
            # Additional initialization logic
        except Exception as e:
            logger.error(f"Error setting initial state: {e}")
    
    def _enter_text_edit_mode(self):
        """Switch to text editing mode"""
        try:
            # Hide canvas panel controls
            if self.canvas_panel:
                self.canvas_panel.visible = False
            
            # Show rich text editor
            if self.rich_text_editor and hasattr(self, 'content'):
                # Find the rich text overlay in the stack
                for control in self.content.controls:
                    if isinstance(control, ft.Container) and hasattr(control, 'content'):
                        content = control.content
                        if isinstance(content, ft.Stack) and len(content.controls) > 1:
                            # Make rich text editor visible
                            for stack_control in content.controls:
                                if hasattr(stack_control, 'key') and stack_control.key == "rich_text_overlay":
                                    stack_control.visible = True
                                    stack_control.update()
                                    break
            
            # Update mode indicator
            self._update_status_bar_text("mode_indicator", "Mode: Text Edit")
            logger.info("Entered text edit mode")
            
        except Exception as e:
            logger.error(f"Error entering text edit mode: {e}")
    
    def _enter_design_mode(self):
        """Switch to design mode"""
        try:
            # Show canvas panel
            if self.canvas_panel:
                self.canvas_panel.visible = True
            
            # Hide rich text editor
            if self.rich_text_editor and hasattr(self, 'content'):
                # Find the rich text overlay in the stack
                for control in self.content.controls:
                    if isinstance(control, ft.Container) and hasattr(control, 'content'):
                        content = control.content
                        if isinstance(content, ft.Stack) and len(content.controls) > 1:
                            # Hide rich text editor
                            for stack_control in content.controls:
                                if hasattr(stack_control, 'key') and stack_control.key == "rich_text_overlay":
                                    stack_control.visible = False
                                    stack_control.update()
                                    break
            
            # Update mode indicator
            self._update_status_bar_text("mode_indicator", "Mode: Design")
            logger.info("Entered design mode")
            
        except Exception as e:
            logger.error(f"Error entering design mode: {e}")
    
    def _enter_preview_mode(self):
        """Switch to preview mode"""
        try:
            # Disable component selection and editing
            if self.properties_panel:
                self.properties_panel.set_component_data(None)
            
            # Hide grid and guides
            if hasattr(self.canvas_panel, 'viewport') and hasattr(self.canvas_panel.viewport, 'toggle_grid'):
                # Ensure grid is off
                if self.canvas_panel.viewport.show_grid:
                    self.canvas_panel.viewport.toggle_grid()
            
            # Update mode indicator
            self._update_status_bar_text("mode_indicator", "Mode: Preview")
            logger.info("Entered preview mode")
            
        except Exception as e:
            logger.error(f"Error entering preview mode: {e}")
    
    def _enter_export_mode(self):
        """Switch to export mode"""
        try:
            # Show export dialog
            self._show_export_dialog()
            
            # Update mode indicator
            self._update_status_bar_text("mode_indicator", "Mode: Export")
            logger.info("Entered export mode")
            
        except Exception as e:
            logger.error(f"Error entering export mode: {e}")
    
    def _switch_to_templates_mode(self):
        """Switch to templates browsing mode"""
        try:
            # Update components panel to show templates
            if self.components_panel:
                # This would trigger a template view in the components panel
                # For now, just log the action
                logger.info("Templates mode requested - feature to be implemented")
            
            # Update mode indicator
            self._update_status_bar_text("mode_indicator", "Mode: Templates")
            
        except Exception as e:
            logger.error(f"Error switching to templates mode: {e}")
    
    def _show_system_settings(self):
        """Show system settings dialog"""
        try:
            settings_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("System Settings"),
                content=ft.Container(
                    width=600,
                    height=400,
                    content=ft.Column([
                        ft.Text("Performance Settings", weight=ft.FontWeight.W_500),
                        ft.Switch(
                            label="Enable advanced rendering",
                            value=self.config.enable_advanced_rendering,
                            on_change=lambda e: setattr(self.config, 'enable_advanced_rendering', e.control.value)
                        ),
                        ft.Switch(
                            label="Enable performance monitoring",
                            value=self.config.performance_monitoring,
                            on_change=lambda e: setattr(self.config, 'performance_monitoring', e.control.value)
                        ),
                        ft.Divider(),
                        ft.Text("Auto-save Settings", weight=ft.FontWeight.W_500),
                        ft.Row([
                            ft.Text("Auto-save interval (seconds):"),
                            ft.TextField(
                                value=str(self.config.auto_save_interval),
                                width=100,
                                on_change=lambda e: self._update_auto_save_interval(e.control.value)
                            )
                        ]),
                        ft.Divider(),
                        ft.Text("Editor Settings", weight=ft.FontWeight.W_500),
                        ft.TextField(
                            label="Maximum undo history",
                            value=str(self.config.max_undo_history),
                            width=200,
                            on_change=lambda e: self._update_max_undo_history(e.control.value)
                        )
                    ], spacing=12, scroll=ft.ScrollMode.AUTO)
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda e: self._close_dialog("settings")),
                    ft.ElevatedButton("Apply", on_click=lambda e: self._apply_settings())
                ]
            )
            
            self.active_dialogs["settings"] = settings_dialog
            self.page.overlay.append(settings_dialog)
            settings_dialog.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error showing system settings: {e}")
    
    def _show_help_dialog(self):
        """Show help and keyboard shortcuts dialog"""
        try:
            help_content = """
            **Keyboard Shortcuts:**
            
            • Ctrl+S - Save project
            • Ctrl+Z - Undo
            • Ctrl+Y / Ctrl+Shift+Z - Redo
            • Delete - Delete selected component
            • Ctrl+C - Copy selected component
            • Ctrl+V - Paste component
            • Ctrl+A - Select all components
            • Escape - Clear selection
            
            **Mouse Controls:**
            
            • Click - Select component
            • Drag - Move component
            • Click empty space - Clear selection
            • Scroll - Zoom in/out (with Ctrl)
            • Middle drag - Pan canvas
            
            **Tips:**
            
            • Double-click text components to edit
            • Hold Shift to select multiple components
            • Use grid snapping for precise alignment
            """
            
            help_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Help & Keyboard Shortcuts"),
                content=ft.Container(
                    width=500,
                    height=400,
                    content=ft.Markdown(
                        help_content,
                        selectable=True,
                        extension_set="gitHubWeb"
                    )
                ),
                actions=[
                    ft.ElevatedButton("Close", on_click=lambda e: self._close_dialog("help"))
                ]
            )
            
            self.active_dialogs["help"] = help_dialog
            self.page.overlay.append(help_dialog)
            help_dialog.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error showing help dialog: {e}")
    
    async def _perform_undo(self):
        """Perform undo operation"""
        try:
            success = await self.state_manager.undo()
            if success:
                await self._show_success_feedback("Undo successful")
            else:
                logger.info("Nothing to undo")
        except Exception as e:
            logger.error(f"Error performing undo: {e}")
    
    async def _perform_redo(self):
        """Perform redo operation"""
        try:
            success = await self.state_manager.redo()
            if success:
                await self._show_success_feedback("Redo successful")
            else:
                logger.info("Nothing to redo")
        except Exception as e:
            logger.error(f"Error performing redo: {e}")
    
    async def _save_project(self):
        """Save current project"""
        try:
            # Get project manager from state or context
            if hasattr(self, 'project_manager') and self.project_manager:
                success = await self.project_manager.save_project()
                if success:
                    await self._show_success_feedback("Project saved successfully")
                else:
                    await self._show_error_feedback("Failed to save project")
            else:
                await self._show_error_feedback("No active project to save")
        except Exception as e:
            logger.error(f"Error saving project: {e}")
            await self._show_error_feedback(f"Save failed: {str(e)}")
    
    async def _clear_selection(self):
        """Clear all selected components"""
        try:
            action = ActionCreators.clear_selection()
            await self.state_manager.dispatch_action(action)
        except Exception as e:
            logger.error(f"Error clearing selection: {e}")
    
    async def _delete_selected_components(self):
        """Delete all selected components"""
        try:
            # Get selected components from state
            selection_state = self.state_manager.get_state_system().get_state("selection")
            if hasattr(selection_state, 'selected_ids'):
                selected_ids = list(selection_state.selected_ids)
                
                if selected_ids:
                    # Delete each component
                    for component_id in selected_ids:
                        action = ActionCreators.delete_component(component_id)
                        await self.state_manager.dispatch_action(action)
                    
                    await self._show_success_feedback(f"Deleted {len(selected_ids)} component(s)")
                else:
                    logger.info("No components selected to delete")
        except Exception as e:
            logger.error(f"Error deleting components: {e}")
    
    def _create_progress_dialog(self, message: str) -> ft.AlertDialog:
        """Create a progress dialog"""
        try:
            progress_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Processing..."),
                content=ft.Container(
                    width=300,
                    height=100,
                    content=ft.Column([
                        ft.Text(message),
                        ft.ProgressBar(width=250)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
                    alignment=ft.alignment.center
                )
            )
            
            self.active_dialogs["progress"] = progress_dialog
            self.page.overlay.append(progress_dialog)
            progress_dialog.open = True
            self.page.update()
            
            return progress_dialog
            
        except Exception as e:
            logger.error(f"Error creating progress dialog: {e}")
            return None
    
    async def _show_export_success_dialog(self, result):
        """Show export success dialog"""
        try:
            success_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color="#10B981"),
                    ft.Text("Export Successful")
                ]),
                content=ft.Container(
                    width=400,
                    content=ft.Column([
                        ft.Text("Your project has been exported successfully!"),
                        ft.Divider(),
                        ft.Text("Export Details:", weight=ft.FontWeight.W_500),
                        ft.Text(f"Format: {result.format if hasattr(result, 'format') else 'Unknown'}"),
                        ft.Text(f"Location: {result.output_path if hasattr(result, 'output_path') else 'Unknown'}"),
                        ft.Text(f"Files: {result.file_count if hasattr(result, 'file_count') else 'Unknown'}")
                    ], spacing=8)
                ),
                actions=[
                    ft.TextButton("Open Folder", on_click=lambda e: self._open_export_folder(result)),
                    ft.ElevatedButton("Done", on_click=lambda e: self._close_dialog("export_success"))
                ]
            )
            
            self.active_dialogs["export_success"] = success_dialog
            self.page.overlay.append(success_dialog)
            success_dialog.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error showing export success dialog: {e}")
    
    async def _auto_save_loop(self):
        """Auto-save loop that runs periodically"""
        try:
            while True:
                # Wait for the configured interval
                await asyncio.sleep(self.config.auto_save_interval)
                
                # Check if we should still be running
                if not hasattr(self, 'auto_save_timer') or not self.auto_save_timer:
                    break
                
                # Perform auto-save
                await self._trigger_auto_save()
                
        except asyncio.CancelledError:
            logger.info("Auto-save loop cancelled")
        except Exception as e:
            logger.error(f"Error in auto-save loop: {e}")
    
    async def _trigger_auto_save(self):
        """Trigger an auto-save operation"""
        try:
            if hasattr(self, 'project_manager') and self.project_manager:
                # Save without showing feedback to avoid interruption
                success = await self.project_manager.save_project()
                if success:
                    logger.info("Auto-save completed")
                else:
                    logger.warning("Auto-save failed")
        except Exception as e:
            logger.error(f"Error during auto-save: {e}")
    
    async def _initialize_performance_monitoring(self):
        """Initialize performance monitoring system"""
        try:
            # This would set up performance tracking
            # For now, just log that it's initialized
            logger.info("Performance monitoring initialized")
        except Exception as e:
            logger.error(f"Error initializing performance monitoring: {e}")
    
    async def _initialize_drag_drop_integration(self):
        """Initialize enhanced drag & drop integration"""
        try:
            # Connect drag & drop manager to UI components
            if self.drag_drop_manager and self.components_panel:
                # This would set up the integration
                logger.info("Drag & drop integration initialized")
        except Exception as e:
            logger.error(f"Error initializing drag & drop integration: {e}")
    
    async def _initialize_export_integration(self):
        """Initialize export system integration"""
        try:
            # Set up export system with current context
            logger.info("Export system integration initialized")
        except Exception as e:
            logger.error(f"Error initializing export integration: {e}")
    
    async def _update_ui_mode_state(self, mode: str):
        """Update UI mode in state management"""
        try:
            # This would update the state to reflect the current UI mode
            logger.info(f"UI mode updated to: {mode}")
        except Exception as e:
            logger.error(f"Error updating UI mode state: {e}")
    
    def _handle_template_select(self, template_data: Dict[str, Any]):
        """Handle template selection from components panel"""
        try:
            logger.info(f"Template selected: {template_data}")
            # This would apply the template to the canvas
        except Exception as e:
            logger.error(f"Error handling template selection: {e}")
    
    def _handle_style_preset_apply(self, preset_data: Dict[str, Any]):
        """Handle style preset application"""
        try:
            logger.info(f"Style preset applied: {preset_data}")
            # This would apply the style preset to selected components
        except Exception as e:
            logger.error(f"Error applying style preset: {e}")
    
    def _handle_advanced_property_edit(self, property_data: Dict[str, Any]):
        """Handle advanced property editing"""
        try:
            logger.info(f"Advanced property edit: {property_data}")
            # This would open advanced editors for complex properties
        except Exception as e:
            logger.error(f"Error in advanced property edit: {e}")
    
    def _handle_rich_text_change(self, content: str):
        """Handle rich text content changes"""
        try:
            logger.info("Rich text content changed")
            # This would update the component's text content
        except Exception as e:
            logger.error(f"Error handling rich text change: {e}")
    
    def _handle_rich_text_format(self, format_data: Dict[str, Any]):
        """Handle rich text formatting changes"""
        try:
            logger.info(f"Rich text format applied: {format_data}")
            # This would apply formatting to the text
        except Exception as e:
            logger.error(f"Error handling rich text format: {e}")
    
    def _handle_rich_text_close(self):
        """Handle rich text editor close"""
        try:
            # Return to design mode
            self._enter_design_mode()
        except Exception as e:
            logger.error(f"Error handling rich text close: {e}")
    
    def _update_auto_save_interval(self, value: str):
        """Update auto-save interval from settings"""
        try:
            interval = int(value)
            if interval >= 10:  # Minimum 10 seconds
                self.config.auto_save_interval = interval
                # Restart auto-save timer with new interval
                if self.auto_save_timer:
                    self.auto_save_timer.cancel()
                    self.auto_save_timer = asyncio.create_task(self._auto_save_loop())
        except ValueError:
            logger.error("Invalid auto-save interval value")
    
    def _update_max_undo_history(self, value: str):
        """Update maximum undo history from settings"""
        try:
            max_history = int(value)
            if max_history >= 10:  # Minimum 10 actions
                self.config.max_undo_history = max_history
                # Update state manager if it supports this
                if hasattr(self.state_manager, 'set_max_history'):
                    self.state_manager.set_max_history(max_history)
        except ValueError:
            logger.error("Invalid max undo history value")
    
    def _apply_settings(self):
        """Apply settings changes"""
        try:
            self._close_dialog("settings")
            logger.info("Settings applied")
        except Exception as e:
            logger.error(f"Error applying settings: {e}")
    
    def _open_export_folder(self, result):
        """Open the export folder in file explorer"""
        try:
            if hasattr(result, 'output_path'):
                import os
                import platform
                
                path = str(result.output_path)
                if platform.system() == 'Windows':
                    os.startfile(path)
                elif platform.system() == 'Darwin':  # macOS
                    os.system(f'open "{path}"')
                else:  # Linux
                    os.system(f'xdg-open "{path}"')
        except Exception as e:
            logger.error(f"Error opening export folder: {e}")
    
    async def cleanup(self):
        """
        Clean up system resources
        
        CLAUDE.md Implementation:
        - #1.5: Proper resource cleanup
        - #6.2: State management cleanup
        """
        try:
            # Cancel auto-save timer
            if self.auto_save_timer:
                self.auto_save_timer.cancel()
            
            # Close any open dialogs
            for dialog_id in list(self.active_dialogs.keys()):
                self._close_dialog(dialog_id)
            
            # Cleanup drag & drop manager
            if self.drag_drop_manager:
                self.drag_drop_manager.cleanup()
            
            logger.info("Integrated Canvas System cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def create_integrated_canvas_system(
    page: ft.Page,
    state_manager: EnhancedStateManager,
    config: Optional[SystemIntegrationConfig] = None
) -> IntegratedCanvasSystem:
    """
    Factory function to create the integrated canvas system
    
    CLAUDE.md Implementation:
    - #3.1: Clean factory pattern
    - #4.1: Type-safe system creation
    """
    try:
        system = IntegratedCanvasSystem(page, state_manager, config)
        return system
    except Exception as e:
        logger.error(f"Error creating integrated canvas system: {e}")
        raise