"""Main canvas area for visual editing"""

import flet as ft
from typing import Optional, List, Dict, Any, Callable, Tuple
from models.component import Component
from config.constants import DEVICE_PRESETS
from components.drag_drop_manager import get_drag_drop_manager, DragData, DropTarget, DropZoneType

# Import advanced rendering system
try:
    from ui.panels.enhanced_canvas import EnhancedCanvasPanel
    from rendering.canvas_integration import CanvasRenderingSystem
    ADVANCED_RENDERING_AVAILABLE = True
except ImportError:
    ADVANCED_RENDERING_AVAILABLE = False
    print("Advanced rendering system not available, using basic implementation")


class CanvasHeader(ft.Container):
    """Canvas header with device switcher and actions"""
    
    def __init__(self, 
                 on_device_change: Callable[[str], None],
                 on_action: Callable[[str], None]):
        self.on_device_change = on_device_change
        self.on_action = on_action
        self.current_device = "desktop"
        
        super().__init__(
            bgcolor="white",
            border=ft.border.only(bottom=ft.BorderSide(1, "#E5E7EB")),
            padding=ft.padding.symmetric(horizontal=32, vertical=16),
            content=self._build_content()
        )
    
    def _build_content(self) -> ft.Control:
        """Build header content"""
        return ft.Row([
            # Left side - Title and device switcher
            ft.Row([
                ft.Text("OC2 Dashboard", size=20, weight=ft.FontWeight.W_600),
                self._build_device_switcher()
            ], spacing=32),
            
            # Right side - Actions
            ft.Row([
                self._create_action_button("grid_view", "Show Grid", "grid"),
                self._create_action_button("undo", "Undo", "undo"),
                self._create_action_button("redo", "Redo", "redo"),
                self._create_action_button("visibility", "Preview", "preview"),
                self._create_action_button("save", "Save", "save", primary=True),
                self._create_action_button("publish", "Publish", "publish", primary=True),
            ], spacing=16)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    
    def _build_device_switcher(self) -> ft.Control:
        """Build device switcher buttons"""
        buttons = []
        for device_id, device in DEVICE_PRESETS.items():
            is_active = device_id == self.current_device
            buttons.append(
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=16, vertical=8),
                    bgcolor="white" if is_active else None,
                    border_radius=6,
                    on_click=lambda e, d=device_id: self._on_device_click(d),
                    content=ft.Row([
                        ft.Icon(device["icon"], size=16),
                        ft.Text(device_id.capitalize(), size=14)
                    ], spacing=8),
                    shadow=ft.BoxShadow(
                        spread_radius=0,
                        blur_radius=3,
                        color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                        offset=ft.Offset(0, 1)
                    ) if is_active else None
                )
            )
        
        return ft.Container(
            bgcolor="#F3F4F6",  # Gray-100
            padding=4,
            border_radius=8,
            content=ft.Row(buttons, spacing=8)
        )
    
    def _create_action_button(self, icon: str, tooltip: str, action: str, primary: bool = False) -> ft.Control:
        """Create an action button"""
        return ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(icon, size=16),
                ft.Text(tooltip, size=14)
            ], spacing=8, tight=True),
            style=ft.ButtonStyle(
                bgcolor="#5E6AD2" if primary else "white",
                color="white" if primary else "#374151",
                padding=ft.padding.symmetric(horizontal=16, vertical=8),
                shape=ft.RoundedRectangleBorder(radius=6),
                elevation=0 if not primary else 2,
                side=ft.BorderSide(1, "#D1D5DB") if not primary else None
            ),
            on_click=lambda e: self.on_action(action)
        )
    
    def _on_device_click(self, device: str):
        """Handle device selection"""
        self.current_device = device
        self.content = self._build_content()
        self.update()
        self.on_device_change(device)


class CanvasViewport(ft.Container):
    """Main canvas viewport where components are displayed"""
    
    def __init__(self,
                 on_component_drop: Callable[[Dict[str, str], ft.Offset], None],
                 on_component_select: Callable[[str], None]):
        self.on_component_drop = on_component_drop
        self.on_component_select = on_component_select
        self.components: List[Component] = []
        self.selected_component_id: Optional[str] = None
        self.show_grid = False
        self.device = "desktop"
        
        # Enhanced drag & drop integration
        self.drag_manager = get_drag_drop_manager()
        self._setup_drag_handlers()
        
        # Canvas content container
        self.canvas_content = ft.Container(
            bgcolor="white",
            border_radius=12,
            width=self._get_device_width(),
            min_height=600,
            alignment=ft.alignment.top_center,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                offset=ft.Offset(0, 4)
            ),
            content=self._build_canvas_content()
        )
        
        super().__init__(
            bgcolor="#F8F9FA",
            padding=32,
            content=ft.Column([
                self.canvas_content
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO),
            expand=True,
            # Enable dropping
            on_will_accept=self._on_will_accept,
            on_accept=self._on_accept,
            on_leave=self._on_leave
        )
    
    def _get_device_width(self) -> int:
        """Get width based on current device"""
        if self.device == "mobile":
            return 375
        elif self.device == "tablet":
            return 768
        else:
            return 1200  # Max width for desktop
    
    def _build_canvas_content(self) -> ft.Control:
        """Build the canvas content area"""
        if not self.components:
            # Empty state with drop zone
            return ft.Container(
                border=ft.border.all(2, "#D1D5DB", style=ft.BorderStyle.DASHED),
                border_radius=8,
                padding=48,
                margin=32,
                alignment=ft.alignment.center,
                content=ft.Column([
                    ft.Icon(ft.Icons.CLOUD_UPLOAD, size=48, color="#9CA3AF"),
                    ft.Text(
                        "Drop components here or click the + button to add content",
                        size=16,
                        color="#6B7280",
                        text_align=ft.TextAlign.CENTER
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=16)
            )
        
        # Build component tree
        return ft.Stack([
            # Grid overlay
            ft.Container(
                expand=True,
                visible=self.show_grid,
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=["transparent", "transparent"],
                    tile_mode=ft.GradientTileMode.REPEATED
                ),
                # TODO: Implement actual grid pattern
            ),
            # Components
            ft.Column([
                self._render_component(comp) for comp in self.components
            ])
        ])
    
    def _render_component(self, component: Component) -> ft.Control:
        """Render a component"""
        is_selected = component.id == self.selected_component_id
        
        return ft.Container(
            key=component.id,
            padding=16,
            border=ft.border.all(2, "#5E6AD2" if is_selected else "transparent"),
            border_radius=4,
            on_click=lambda e: self.on_component_select(component.id),
            content=ft.Column([
                ft.Text(component.name, weight=ft.FontWeight.BOLD),
                ft.Text(f"Type: {component.type}", size=12, color="#6B7280"),
                # Render children recursively
                ft.Column([
                    self._render_component(child) for child in component.children
                ]) if component.children else None
            ])
        )
    
    def _setup_drag_handlers(self):
        """
        Setup enhanced drag handlers with DragDropManager integration
        
        CLAUDE.md Implementation:
        - #1.5: Performance-optimized drag operations
        - #9.1: Accessible drag operations
        """
        try:
            # Register this canvas as a drop zone in the spatial index
            from managers.spatial_index import BoundingBox
            from spatial_drag_index import DropZone
            
            # Create canvas drop zone
            canvas_bounds = BoundingBox(
                x=0, y=0, 
                width=self._get_device_width(), 
                height=600
            )
            
            canvas_drop_zone = DropZone(
                zone_id="main_canvas",
                bounds=canvas_bounds,
                target=DropTarget(
                    zone_type=DropZoneType.CANVAS,
                    target_id="canvas",
                    accepts=["*"]  # Accept all component types
                ),
                accepts=["*"],
                depth=0
            )
            
            # Register with spatial index
            self.drag_manager.spatial_index.add_drop_zone(canvas_drop_zone)
            
            # Add event handlers to drag manager
            self.drag_manager.add_drop_handler(self._handle_enhanced_drop)
            
        except Exception as e:
            print(f"Error setting up drag handlers: {e}")
            # Fallback to basic handlers if enhanced setup fails
    
    def _on_will_accept(self, e: ft.DragTargetEvent):
        """Enhanced drag over canvas with visual feedback"""
        try:
            # Get mouse position if available
            mouse_position = (e.x, e.y) if hasattr(e, 'x') and hasattr(e, 'y') else None
            
            # Use drag manager for enhanced handling
            if mouse_position and self.drag_manager.is_dragging():
                is_valid = self.drag_manager.handle_drag_over(mouse_position)
                
                # Update visual feedback based on validation
                self.bgcolor = "#F3F4F6" if is_valid else "#FEF2F2"  # Light red for invalid
            else:
                # Fallback visual feedback
                self.bgcolor = "#F3F4F6"
            
            self.update()
            
        except Exception as e:
            print(f"Error in enhanced will_accept: {e}")
            # Fallback to basic behavior
            self.bgcolor = "#F3F4F6"
            self.update()
    
    def _on_accept(self, e: ft.DragTargetEvent):
        """Enhanced component drop with DragDropManager"""
        try:
            # Reset background color
            self.bgcolor = "#F8F9FA"
            
            # Get drop position
            mouse_position = (e.x, e.y) if hasattr(e, 'x') and hasattr(e, 'y') else None
            
            # Use drag manager for enhanced drop handling
            if self.drag_manager.is_dragging():
                success = self.drag_manager.handle_drop(mouse_position)
                
                if not success:
                    # If enhanced drop failed, try fallback
                    position = ft.Offset(e.x, e.y) if hasattr(e, 'x') else ft.Offset(0, 0)
                    self.on_component_drop(e.data, position)
            else:
                # Fallback to basic drop handling
                position = ft.Offset(e.x, e.y) if hasattr(e, 'x') else ft.Offset(0, 0)
                self.on_component_drop(e.data, position)
            
            self.update()
            
        except Exception as e:
            print(f"Error in enhanced accept: {e}")
            # Fallback to basic behavior
            self.bgcolor = "#F8F9FA"
            position = ft.Offset(e.x, e.y) if hasattr(e, 'x') else ft.Offset(0, 0)
            self.on_component_drop(e.data, position)
            self.update()
    
    def _on_leave(self, e: ft.DragTargetEvent):
        """Enhanced drag leave with cleanup"""
        try:
            # Reset background color
            self.bgcolor = "#F8F9FA"
            
            # Clear any visual feedback from drag manager
            if self.drag_manager.is_dragging():
                # The drag manager will handle clearing feedback automatically
                pass
            
            self.update()
            
        except Exception as e:
            print(f"Error in enhanced leave: {e}")
            # Fallback to basic behavior
            self.bgcolor = "#F8F9FA"
            self.update()
    
    def _handle_enhanced_drop(self, event) -> bool:
        """
        Handle enhanced drop events from DragDropManager
        
        CLAUDE.md Implementation:
        - #2.1.1: Validate all drop operations
        - #4.1: Type-safe component creation
        """
        try:
            drag_data = event.drag_data
            drop_target = event.drop_target
            
            # Only handle canvas drops
            if drop_target.zone_type != DropZoneType.CANVAS:
                return False
            
            # Handle library component drops
            if drag_data.source_type == "library" and drag_data.component_id:
                # Parse component data
                try:
                    import json
                    if isinstance(drag_data.properties, str):
                        component_data = json.loads(drag_data.properties)
                    else:
                        component_data = drag_data.properties or {}
                    
                    # Create position data
                    position = ft.Offset(
                        event.mouse_position[0] if event.mouse_position else 100,
                        event.mouse_position[1] if event.mouse_position else 100
                    )
                    
                    # Call the original drop handler
                    self.on_component_drop(component_data, position)
                    return True
                    
                except Exception as e:
                    print(f"Error processing library component drop: {e}")
                    return False
            
            # Handle canvas component moves
            elif drag_data.source_type == "canvas" and drag_data.instance_id:
                # This would be handled by the canvas component tree
                # For now, just log the operation
                print(f"Canvas component move: {drag_data.instance_id}")
                return True
            
            return False
            
        except Exception as e:
            print(f"Error in enhanced drop handler: {e}")
            return False
    
    def add_component(self, component: Component):
        """Add a component to the canvas"""
        self.components.append(component)
        self.canvas_content.content = self._build_canvas_content()
        self.update()
    
    def select_component(self, component_id: str):
        """Select a component"""
        self.selected_component_id = component_id
        self.canvas_content.content = self._build_canvas_content()
        self.update()
    
    def toggle_grid(self):
        """Toggle grid visibility"""
        self.show_grid = not self.show_grid
        self.canvas_content.content = self._build_canvas_content()
        self.update()
    
    def set_device(self, device: str):
        """Set the device preview mode"""
        self.device = device
        self.canvas_content.width = self._get_device_width()
        self.update()


class CanvasPanel(ft.Container):
    """Complete canvas panel with header and viewport"""
    
    def __init__(self,
                 on_component_drop: Callable[[Dict[str, str], ft.Offset], None],
                 on_component_select: Callable[[str], None],
                 on_action: Callable[[str], None]):
        self.viewport = CanvasViewport(on_component_drop, on_component_select)
        self.header = CanvasHeader(self._on_device_change, on_action)
        
        super().__init__(
            content=ft.Column([
                self.header,
                self.viewport
            ], spacing=0, expand=True),
            expand=True
        )
    
    def _on_device_change(self, device: str):
        """Handle device change from header"""
        self.viewport.set_device(device)
    
    def add_component(self, component: Component):
        """Add a component to the canvas"""
        self.viewport.add_component(component)
    
    def select_component(self, component_id: str):
        """Select a component"""
        self.viewport.select_component(component_id)
    
    def handle_action(self, action: str):
        """Handle canvas actions"""
        if action == "grid":
            self.viewport.toggle_grid()
        # Other actions handled by parent
    
    async def refresh_from_state(self, components_state):
        """
        Refresh canvas from state management system
        
        CLAUDE.md Implementation:
        - #6.2: Real-time state synchronization
        - #4.1: Type-safe state handling
        """
        try:
            # Convert state data to Component objects if needed
            if isinstance(components_state, dict):
                # State might be a dict with component data
                components = []
                for comp_id, comp_data in components_state.items():
                    if isinstance(comp_data, dict):
                        # Convert dict to Component if needed
                        from models.component import Component
                        component = Component(**comp_data) if comp_data else None
                        if component:
                            components.append(component)
                    elif hasattr(comp_data, 'id'):
                        # Already a Component object
                        components.append(comp_data)
                
                self.viewport.components = components
            elif isinstance(components_state, list):
                # State is a list of components
                self.viewport.components = components_state
            else:
                # Handle other state formats
                self.viewport.components = []
            
            # Refresh the viewport display
            self.viewport.canvas_content.content = self.viewport._build_canvas_content()
            self.viewport.update()
            
        except Exception as e:
            print(f"Error refreshing canvas from state: {e}")
            # Ensure viewport doesn't break
            self.viewport.components = []
            self.viewport.canvas_content.content = self.viewport._build_canvas_content()
            self.viewport.update()
    
    async def update_selection(self, selected_ids: List[str]):
        """
        Update component selection from state management
        
        CLAUDE.md Implementation:
        - #6.2: Real-time selection synchronization
        - #9.1: Accessible selection indicators
        """
        try:
            # Update viewport selection
            if selected_ids:
                # Select the first component (single selection for now)
                self.viewport.selected_component_id = selected_ids[0]
            else:
                self.viewport.selected_component_id = None
            
            # Refresh canvas to show selection
            self.viewport.canvas_content.content = self.viewport._build_canvas_content()
            self.viewport.update()
            
        except Exception as e:
            print(f"Error updating selection: {e}")
            # Ensure selection state doesn't break
            self.viewport.selected_component_id = None
            self.viewport.update()


def create_canvas_panel(
    on_component_drop: Callable[[Dict[str, str], ft.Offset], None],
    on_component_select: Callable[[str], None],
    on_action: Callable[[str], None],
    state_manager: Optional[Any] = None,
    advanced_features: bool = True
) -> ft.Control:
    """
    Factory function to create canvas panel with best available rendering
    
    CLAUDE.md Implementation:
    - #3.1: Clean interface design
    - #1.5: Performance optimization when available
    """
    if ADVANCED_RENDERING_AVAILABLE and advanced_features and state_manager:
        try:
            # Create advanced canvas with sophisticated rendering
            drag_manager = get_drag_drop_manager()
            
            enhanced_canvas = EnhancedCanvasPanel(
                state_manager=state_manager,
                drag_drop_manager=drag_manager,
                component_library=None,  # Will be connected later
                on_save=lambda: on_action("save"),
                on_preview=lambda: on_action("preview")
            )
            
            # Wrap with performance monitor
            return ft.Column([
                enhanced_canvas,
                _build_performance_monitor(enhanced_canvas)
            ], expand=True)
            
        except Exception as e:
            print(f"Failed to create advanced canvas: {e}")
            # Fall back to basic implementation
    
    # Create basic canvas panel
    return CanvasPanel(on_component_drop, on_component_select, on_action)


def _build_performance_monitor(enhanced_canvas: Any) -> ft.Control:
    """
    Build performance monitoring widget for advanced canvas
    
    CLAUDE.md Implementation:
    - #12.1: Performance monitoring
    - #9.1: Accessible performance data
    """
    performance_text = ft.Text(
        "",
        size=12,
        color="#6B7280"
    )
    
    def update_performance():
        """Update performance display"""
        try:
            stats = enhanced_canvas.get_performance_stats()
            if stats:
                renderer_stats = stats.get("renderer", {})
                avg_frame_time = renderer_stats.get("avg_frame_time", 0)
                cache_hit_rate = renderer_stats.get("cache_hit_rate", 0)
                
                performance_text.value = (
                    f"Frame: {avg_frame_time:.1f}ms | "
                    f"Cache: {cache_hit_rate:.1%} | "
                    f"Components: {renderer_stats.get('culled_components', 0)} culled"
                )
            else:
                performance_text.value = "Performance data unavailable"
                
            performance_text.update()
        except Exception as e:
            performance_text.value = f"Performance monitor error: {e}"
            performance_text.update()
    
    # Create performance container
    performance_container = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.SPEED, size=16, color="#6B7280"),
            performance_text,
            ft.IconButton(
                icon=ft.Icons.REFRESH,
                icon_size=16,
                tooltip="Refresh performance stats",
                on_click=lambda e: update_performance()
            )
        ], spacing=8),
        padding=ft.padding.symmetric(horizontal=12, vertical=4),
        bgcolor="#F9FAFB",
        border=ft.border.only(top=ft.BorderSide(1, "#E5E7EB")),
        visible=False  # Hidden by default
    )
    
    # Auto-update performance stats every 2 seconds
    import threading
    import time
    
    def auto_update():
        while True:
            try:
                if performance_container.visible:
                    update_performance()
                time.sleep(2)
            except Exception:
                break
    
    # Start background thread for performance updates
    performance_thread = threading.Thread(target=auto_update, daemon=True)
    performance_thread.start()
    
    return performance_container


class AdvancedCanvasFeatures:
    """
    Additional advanced canvas features
    
    CLAUDE.md Implementation:
    - #1.5: Performance optimization
    - #6.2: Real-time updates
    """
    
    @staticmethod
    def add_component_resize_handles(
        component: Component,
        canvas_container: ft.Container,
        on_resize: Callable[[str, float, float], None]
    ) -> ft.Control:
        """
        Add resize handles to a component
        
        CLAUDE.md Implementation:
        - #9.1: Accessible resize controls
        - #6.2: Real-time resize feedback
        """
        handles = []
        
        # Create resize handles for each corner and edge
        handle_positions = [
            ("nw", -4, -4),      # Top-left
            ("ne", "calc(100% - 4px)", -4),  # Top-right
            ("sw", -4, "calc(100% - 4px)"),  # Bottom-left
            ("se", "calc(100% - 4px)", "calc(100% - 4px)"),  # Bottom-right
            ("n", "calc(50% - 4px)", -4),    # Top
            ("s", "calc(50% - 4px)", "calc(100% - 4px)"),  # Bottom
            ("w", -4, "calc(50% - 4px)"),    # Left
            ("e", "calc(100% - 4px)", "calc(50% - 4px)")   # Right
        ]
        
        for position, left, top in handle_positions:
            cursor_map = {
                "nw": "nw-resize", "ne": "ne-resize", "sw": "sw-resize", "se": "se-resize",
                "n": "n-resize", "s": "s-resize", "w": "w-resize", "e": "e-resize"
            }
            
            handle = ft.Container(
                width=8,
                height=8,
                bgcolor="#5E6AD2",
                border_radius=2,
                border=ft.border.all(1, "#FFFFFF"),
                left=left,
                top=top,
                # Note: Flet doesn't have cursor property, so this is for documentation
                # cursor=cursor_map[position],
                on_pan_start=lambda e, pos=position: _start_resize(component.id, pos, e),
                on_pan_update=lambda e, pos=position: _update_resize(component.id, pos, e, on_resize),
                on_pan_end=lambda e, pos=position: _end_resize(component.id, pos, e)
            )
            handles.append(handle)
        
        # Return component with handles overlay
        return ft.Stack([
            ft.Container(content=component),  # Original component
            ft.Stack(handles)  # Resize handles
        ])
    
    @staticmethod
    def add_selection_indicators(
        selected_ids: List[str],
        component_map: Dict[str, Component]
    ) -> List[ft.Control]:
        """
        Add visual selection indicators for selected components
        
        CLAUDE.md Implementation:
        - #9.1: Clear visual feedback
        - #6.2: Real-time selection updates
        """
        indicators = []
        
        for component_id in selected_ids:
            component = component_map.get(component_id)
            if not component:
                continue
            
            # Get component position and size
            x = float(component.style.left or 0)
            y = float(component.style.top or 0)
            width = float(component.style.width or 100)
            height = float(component.style.height or 50)
            
            # Create selection indicator
            indicator = ft.Container(
                width=width + 4,
                height=height + 4,
                left=x - 2,
                top=y - 2,
                border=ft.border.all(2, "#5E6AD2"),
                border_radius=4,
                # Transparent background to not interfere with content
                bgcolor="transparent"
            )
            indicators.append(indicator)
        
        return indicators
    
    @staticmethod
    def create_component_preview(
        component_type: str,
        mouse_position: Tuple[float, float]
    ) -> ft.Control:
        """
        Create preview of component being dragged
        
        CLAUDE.md Implementation:
        - #9.1: Visual drag feedback
        - #1.5: Lightweight preview rendering
        """
        # Get component definition
        component_defs = {
            "text": {"icon": ft.Icons.TEXT_FIELDS, "name": "Text"},
            "button": {"icon": ft.Icons.SMART_BUTTON, "name": "Button"},
            "image": {"icon": ft.Icons.IMAGE, "name": "Image"},
            "container": {"icon": ft.Icons.CROP_SQUARE, "name": "Container"}
        }
        
        definition = component_defs.get(component_type, {"icon": ft.Icons.WIDGETS, "name": "Component"})
        
        return ft.Container(
            content=ft.Row([
                ft.Icon(definition["icon"], size=16, color="#5E6AD2"),
                ft.Text(definition["name"], size=12, color="#374151")
            ], spacing=8, tight=True),
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            bgcolor="#FFFFFF",
            border=ft.border.all(1, "#5E6AD2"),
            border_radius=4,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=8,
                color="#0000001A",
                offset=ft.Offset(0, 2)
            ),
            left=mouse_position[0] + 10,
            top=mouse_position[1] - 20
        )


# Helper functions for resize handles
def _start_resize(component_id: str, position: str, event):
    """Start component resize operation"""
    print(f"Start resize {component_id} from {position}")

def _update_resize(component_id: str, position: str, event, on_resize: Callable):
    """Update component size during resize"""
    # Calculate new dimensions based on drag delta
    # This is a simplified implementation
    delta_x = getattr(event, 'delta_x', 0)
    delta_y = getattr(event, 'delta_y', 0)
    
    if position in ['e', 'ne', 'se']:  # Right edge
        new_width = max(50, delta_x)  # Minimum width
        on_resize(component_id, new_width, None)
    
    if position in ['s', 'se', 'sw']:  # Bottom edge
        new_height = max(30, delta_y)  # Minimum height
        on_resize(component_id, None, new_height)

def _end_resize(component_id: str, position: str, event):
    """End component resize operation"""
    print(f"End resize {component_id}")