"""
Enhanced Canvas Panel with High-Performance Rendering
Integrates the new rendering system with the existing UI
Following CLAUDE.md guidelines for clean architecture
"""

import flet as ft
from typing import Optional, Callable, Dict, Any
import logging

from rendering.canvas_integration import CanvasRenderingSystem
from components.drag_drop_manager import DragDropManager, DropHandler, ComponentLibrary

logger = logging.getLogger(__name__)


class EnhancedCanvasPanel(ft.UserControl):
    """
    Enhanced canvas panel with the new rendering system
    Drop-in replacement for the existing canvas panel
    CLAUDE.md #3.1: Clean interface design
    """
    
    def __init__(
        self,
        state_manager: Any,
        drag_drop_manager: DragDropManager,
        component_library: ComponentLibrary,
        on_save: Optional[Callable[[], None]] = None,
        on_preview: Optional[Callable[[], None]] = None
    ):
        """Initialize enhanced canvas panel"""
        super().__init__()
        self.state_manager = state_manager
        self.drag_drop_manager = drag_drop_manager
        self.component_library = component_library
        self.on_save = on_save
        self.on_preview = on_preview
        
        # Canvas dimensions
        self.canvas_width = 1200
        self.canvas_height = 800
        
        # UI components
        self.device_selector: Optional[ft.Dropdown] = None
        self.zoom_display: Optional[ft.Text] = None
        self.grid_toggle: Optional[ft.IconButton] = None
        self.canvas_container: Optional[ft.Container] = None
        
        # Rendering system (initialized in build)
        self.rendering_system: Optional[CanvasRenderingSystem] = None
        
        logger.info("Enhanced canvas panel initialized")
    
    def build(self) -> ft.Control:
        """Build the canvas panel UI"""
        # Create header
        header = self._build_header()
        
        # Create canvas viewport
        self.canvas_container = self._build_canvas_viewport()
        
        # Initialize rendering system
        self.rendering_system = CanvasRenderingSystem(
            canvas_container=self.canvas_container,
            state_manager=self.state_manager,
            drag_drop_manager=self.drag_drop_manager
        )
        
        # Start rendering
        self.rendering_system.start()
        
        # Main panel layout
        return ft.Container(
            content=ft.Column([
                header,
                ft.Container(
                    content=self.canvas_container,
                    expand=True,
                    bgcolor="#F9FAFB",
                    border=ft.border.all(1, "#E5E7EB")
                )
            ], spacing=0),
            expand=True
        )
    
    def _build_header(self) -> ft.Control:
        """Build canvas header with controls"""
        # Device selector
        self.device_selector = ft.Dropdown(
            value="desktop",
            options=[
                ft.dropdown.Option("desktop", "Desktop"),
                ft.dropdown.Option("tablet", "Tablet"),
                ft.dropdown.Option("mobile", "Mobile"),
            ],
            width=120,
            height=36,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=8),
            on_change=self._on_device_change
        )
        
        # Zoom controls
        zoom_controls = ft.Row([
            ft.IconButton(
                icon=ft.Icons.ZOOM_OUT,
                tooltip="Zoom out",
                on_click=lambda e: self._adjust_zoom(-0.1)
            ),
            self.zoom_display := ft.Text(
                "100%",
                size=14,
                weight=ft.FontWeight.W_500,
                color="#374151"
            ),
            ft.IconButton(
                icon=ft.Icons.ZOOM_IN,
                tooltip="Zoom in",
                on_click=lambda e: self._adjust_zoom(0.1)
            ),
            ft.IconButton(
                icon=ft.Icons.FIT_SCREEN,
                tooltip="Fit to screen",
                on_click=lambda e: self._fit_to_content()
            )
        ], spacing=0)
        
        # Grid toggle
        self.grid_toggle = ft.IconButton(
            icon=ft.Icons.GRID_ON,
            tooltip="Toggle grid",
            selected=False,
            on_click=self._toggle_grid
        )
        
        # Action buttons
        action_buttons = ft.Row([
            ft.IconButton(
                icon=ft.Icons.UNDO,
                tooltip="Undo (Ctrl+Z)",
                on_click=lambda e: self._undo()
            ),
            ft.IconButton(
                icon=ft.Icons.REDO,
                tooltip="Redo (Ctrl+Y)",
                on_click=lambda e: self._redo()
            ),
            ft.Container(width=8),  # Spacer
            ft.IconButton(
                icon=ft.Icons.VISIBILITY,
                tooltip="Preview",
                on_click=lambda e: self._preview()
            ),
            ft.IconButton(
                icon=ft.Icons.SAVE,
                tooltip="Save (Ctrl+S)",
                on_click=lambda e: self._save()
            )
        ], spacing=4)
        
        # Header layout
        return ft.Container(
            content=ft.Row([
                self.device_selector,
                ft.Container(width=16),  # Spacer
                zoom_controls,
                ft.Container(width=16),  # Spacer
                self.grid_toggle,
                ft.Container(expand=True),  # Flexible spacer
                action_buttons
            ], alignment=ft.MainAxisAlignment.START),
            padding=12,
            bgcolor="white",
            border=ft.border.only(bottom=ft.BorderSide(1, "#E5E7EB"))
        )
    
    def _build_canvas_viewport(self) -> ft.Container:
        """Build the main canvas viewport"""
        # Canvas container
        canvas = ft.Container(
            width=self.canvas_width,
            height=self.canvas_height,
            bgcolor="white",
            border_radius=8,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color="#0000000D",
                offset=ft.Offset(0, 4)
            ),
            # Event handlers
            on_click=self._handle_canvas_click,
            on_hover=self._handle_canvas_hover,
            on_scroll=self._handle_canvas_scroll
        )
        
        # Viewport container with scrolling
        viewport = ft.Container(
            content=ft.Row([
                ft.Container(expand=True),  # Center horizontally
                canvas,
                ft.Container(expand=True)
            ]),
            padding=40,
            alignment=ft.alignment.center,
            expand=True
        )
        
        # Setup drop zone
        self._setup_drop_zone(canvas)
        
        return viewport
    
    def _setup_drop_zone(self, canvas: ft.Container) -> None:
        """Setup canvas as a drop zone"""
        drop_handler = DropHandler(
            container=canvas,
            on_drop=self._handle_component_drop,
            on_drag_over=self._handle_drag_over,
            on_drag_leave=self._handle_drag_leave
        )
        
        self.drag_drop_manager.register_drop_zone("canvas", drop_handler)
    
    def _handle_component_drop(self, component_type: str, x: float, y: float) -> None:
        """Handle component drop on canvas"""
        logger.info(f"Component dropped: {component_type} at ({x}, {y})")
        
        # Convert to world coordinates
        if self.rendering_system:
            world_x, world_y = self.rendering_system.viewport_manager.screen_to_world(x, y)
            
            # Create component through state manager
            from managers.state_types import Action, ActionType
            action = Action(
                type=ActionType.ADD_COMPONENT,
                payload={
                    "component_data": {
                        "type": component_type,
                        "style": {
                            "left": str(int(world_x)),
                            "top": str(int(world_y))
                        }
                    }
                }
            )
            self.state_manager.dispatch(action)
    
    def _handle_drag_over(self, x: float, y: float) -> None:
        """Handle drag over canvas"""
        # Future: Show drop preview
        pass
    
    def _handle_drag_leave(self) -> None:
        """Handle drag leave canvas"""
        # Future: Hide drop preview
        pass
    
    # Event Handlers
    
    def _handle_canvas_click(self, e: ft.TapEvent) -> None:
        """Handle canvas click"""
        if self.rendering_system:
            self.rendering_system.handle_pointer_down(e)
    
    def _handle_canvas_hover(self, e: ft.HoverEvent) -> None:
        """Handle canvas hover/drag"""
        if self.rendering_system:
            self.rendering_system.handle_pointer_move(e)
    
    def _handle_canvas_scroll(self, e: ft.ScrollEvent) -> None:
        """Handle canvas scroll (zoom)"""
        if self.rendering_system:
            self.rendering_system.handle_scroll(e)
    
    def _on_device_change(self, e) -> None:
        """Handle device selection change"""
        device = self.device_selector.value
        
        # Update canvas size based on device
        sizes = {
            "mobile": (375, 667),
            "tablet": (768, 1024),
            "desktop": (1200, 800)
        }
        
        width, height = sizes.get(device, (1200, 800))
        self._resize_canvas(width, height)
    
    def _resize_canvas(self, width: int, height: int) -> None:
        """Resize canvas"""
        self.canvas_width = width
        self.canvas_height = height
        
        if self.canvas_container:
            self.canvas_container.width = width
            self.canvas_container.height = height
            self.canvas_container.update()
        
        if self.rendering_system:
            self.rendering_system.resize(width, height)
    
    def _adjust_zoom(self, delta: float) -> None:
        """Adjust zoom level"""
        if self.rendering_system:
            current_zoom = self.rendering_system.viewport_manager.zoom
            new_zoom = max(0.1, min(10.0, current_zoom + delta))
            
            # Apply zoom centered on canvas
            center_x = self.canvas_width / 2
            center_y = self.canvas_height / 2
            
            self.rendering_system.viewport_manager.apply_zoom(
                new_zoom - current_zoom,
                center_x,
                center_y
            )
            
            # Update state
            from managers.state_types import Action, ActionType
            self.state_manager.dispatch(Action(
                type=ActionType.ZOOM_CANVAS,
                payload={
                    "zoom": new_zoom,
                    "pan_x": self.rendering_system.viewport_manager.pan_x,
                    "pan_y": self.rendering_system.viewport_manager.pan_y
                }
            ))
            
            # Update zoom display
            self._update_zoom_display()
    
    def _fit_to_content(self) -> None:
        """Fit viewport to content"""
        if self.rendering_system:
            self.rendering_system.fit_to_content()
            self._update_zoom_display()
    
    def _update_zoom_display(self) -> None:
        """Update zoom percentage display"""
        if self.rendering_system and self.zoom_display:
            zoom_percent = self.rendering_system.viewport_manager.get_zoom_percentage()
            self.zoom_display.value = f"{zoom_percent}%"
            self.zoom_display.update()
    
    def _toggle_grid(self, e) -> None:
        """Toggle grid visibility"""
        if self.rendering_system and self.grid_toggle:
            enabled = not self.grid_toggle.selected
            self.grid_toggle.selected = enabled
            self.grid_toggle.icon = ft.Icons.GRID_ON if enabled else ft.Icons.GRID_OFF
            self.grid_toggle.update()
            
            self.rendering_system.toggle_grid(enabled)
    
    def _undo(self) -> None:
        """Undo last action"""
        from managers.state_types import Action, ActionType
        self.state_manager.dispatch(Action(type=ActionType.UNDO))
    
    def _redo(self) -> None:
        """Redo last action"""
        from managers.state_types import Action, ActionType
        self.state_manager.dispatch(Action(type=ActionType.REDO))
    
    def _preview(self) -> None:
        """Preview design"""
        if self.on_preview:
            self.on_preview()
    
    def _save(self) -> None:
        """Save design"""
        if self.on_save:
            self.on_save()
    
    # Public API
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get rendering performance statistics"""
        if self.rendering_system:
            return self.rendering_system.get_performance_stats()
        return {}
    
    def export_canvas(self, format: str = "png") -> Optional[bytes]:
        """Export canvas to image"""
        # Future: Implement canvas export
        logger.info(f"Export canvas as {format}")
        return None
    
    def did_mount(self) -> None:
        """Called when control is added to page"""
        super().did_mount()
        logger.info("Enhanced canvas panel mounted")
    
    def will_unmount(self) -> None:
        """Called when control is removed from page"""
        if self.rendering_system:
            self.rendering_system.stop()
        super().will_unmount()
        logger.info("Enhanced canvas panel unmounted")