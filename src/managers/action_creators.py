"""
Action creators for generating typed actions in the state management system.
Provides factory functions for creating consistent, validated actions.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .state_types import Action, ActionType, Change, ChangeType


class ActionCreators:
    """Factory functions for creating actions with proper validation and typing"""
    
    @staticmethod
    def add_component(
        component_data: Dict[str, Any], 
        parent_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> Action:
        """Create action for adding a new component"""
        component_name = component_data.get('name', 'Component')
        
        return Action(
            id=str(uuid4()),
            type=ActionType.ADD_COMPONENT,
            timestamp=datetime.now(),
            description=description or f"Add {component_name}",
            payload={
                "component_data": component_data,
                "parent_id": parent_id
            },
            changes=[
                Change(
                    path=f"components.component_map.{component_data.get('id')}",
                    type=ChangeType.CREATE,
                    new_value=component_data
                )
            ],
            metadata={
                "component_id": component_data.get('id'),
                "component_type": component_data.get('type'),
                "parent_id": parent_id
            }
        )
    
    @staticmethod
    def update_component(
        component_id: str,
        updates: Dict[str, Any],
        description: Optional[str] = None
    ) -> Action:
        """Create action for updating component properties"""
        return Action(
            id=str(uuid4()),
            type=ActionType.UPDATE_COMPONENT,
            timestamp=datetime.now(),
            description=description or f"Update component {component_id}",
            payload={
                "component_id": component_id,
                "updates": updates
            },
            metadata={
                "component_id": component_id,
                "updated_properties": list(updates.keys())
            }
        )
    
    @staticmethod
    def update_component_property(
        component_id: str,
        property_path: str,
        value: Any,
        old_value: Any = None
    ) -> Action:
        """Create action for updating a specific component property"""
        return Action(
            id=str(uuid4()),
            type=ActionType.UPDATE_COMPONENT,
            timestamp=datetime.now(),
            description=f"Update {property_path}",
            payload={
                "component_id": component_id,
                "updates": {property_path: value}
            },
            changes=[
                Change(
                    path=f"components.component_map.{component_id}.{property_path}",
                    type=ChangeType.UPDATE,
                    old_value=old_value,
                    new_value=value
                )
            ],
            metadata={
                "component_id": component_id,
                "property": property_path
            }
        )
    
    @staticmethod
    def delete_component(component_id: str, description: Optional[str] = None) -> Action:
        """Create action for deleting a component"""
        return Action(
            id=str(uuid4()),
            type=ActionType.DELETE_COMPONENT,
            timestamp=datetime.now(),
            description=description or f"Delete component {component_id}",
            payload={
                "component_id": component_id
            },
            changes=[
                Change(
                    path=f"components.component_map.{component_id}",
                    type=ChangeType.DELETE,
                    old_value=None  # Will be filled by state manager
                )
            ],
            metadata={
                "component_id": component_id
            }
        )
    
    @staticmethod
    def move_component(
        component_id: str,
        new_parent_id: Optional[str],
        new_index: Optional[int] = None,
        description: Optional[str] = None
    ) -> Action:
        """Create action for moving a component to a new parent"""
        return Action(
            id=str(uuid4()),
            type=ActionType.MOVE_COMPONENT,
            timestamp=datetime.now(),
            description=description or f"Move component {component_id}",
            payload={
                "component_id": component_id,
                "new_parent_id": new_parent_id,
                "new_index": new_index
            },
            metadata={
                "component_id": component_id,
                "new_parent_id": new_parent_id
            }
        )
    
    @staticmethod
    def duplicate_component(
        component_id: str,
        new_component_data: Dict[str, Any],
        description: Optional[str] = None
    ) -> Action:
        """Create action for duplicating a component"""
        return Action(
            id=str(uuid4()),
            type=ActionType.DUPLICATE_COMPONENT,
            timestamp=datetime.now(),
            description=description or f"Duplicate component {component_id}",
            payload={
                "original_component_id": component_id,
                "new_component_data": new_component_data
            },
            metadata={
                "original_component_id": component_id,
                "new_component_id": new_component_data.get('id')
            }
        )
    
    @staticmethod
    def select_component(
        component_id: str,
        multi_select: bool = False,
        description: Optional[str] = None
    ) -> Action:
        """Create action for selecting a component"""
        return Action(
            id=str(uuid4()),
            type=ActionType.SELECT_COMPONENT,
            timestamp=datetime.now(),
            description=description or f"Select component {component_id}",
            payload={
                "component_id": component_id,
                "multi_select": multi_select
            },
            changes=[
                Change(
                    path="selection.selected_ids",
                    type=ChangeType.UPDATE,
                    new_value=component_id
                ),
                Change(
                    path="selection.last_selected",
                    type=ChangeType.UPDATE,
                    new_value=component_id
                )
            ],
            metadata={
                "component_id": component_id,
                "multi_select": multi_select
            }
        )
    
    @staticmethod
    def deselect_component(component_id: str, description: Optional[str] = None) -> Action:
        """Create action for deselecting a component"""
        return Action(
            id=str(uuid4()),
            type=ActionType.DESELECT_COMPONENT,
            timestamp=datetime.now(),
            description=description or f"Deselect component {component_id}",
            payload={
                "component_id": component_id
            },
            metadata={
                "component_id": component_id
            }
        )
    
    @staticmethod
    def select_all(description: Optional[str] = None) -> Action:
        """Create action for selecting all components"""
        return Action(
            id=str(uuid4()),
            type=ActionType.SELECT_ALL,
            timestamp=datetime.now(),
            description=description or "Select all components",
            payload={}
        )
    
    @staticmethod
    def clear_selection(description: Optional[str] = None) -> Action:
        """Create action for clearing selection"""
        return Action(
            id=str(uuid4()),
            type=ActionType.CLEAR_SELECTION,
            timestamp=datetime.now(),
            description=description or "Clear selection",
            payload={},
            changes=[
                Change(
                    path="selection.selected_ids",
                    type=ChangeType.UPDATE,
                    new_value=set()
                ),
                Change(
                    path="selection.last_selected",
                    type=ChangeType.UPDATE,
                    new_value=None
                )
            ]
        )
    
    @staticmethod
    def create_project(
        project_data: Dict[str, Any],
        description: Optional[str] = None
    ) -> Action:
        """Create action for creating a new project"""
        project_name = project_data.get('name', 'New Project')
        
        return Action(
            id=str(uuid4()),
            type=ActionType.CREATE_PROJECT,
            timestamp=datetime.now(),
            description=description or f"Create project: {project_name}",
            payload={
                "project_data": project_data
            },
            metadata={
                "project_id": project_data.get('id'),
                "project_name": project_name
            }
        )
    
    @staticmethod
    def open_project(
        project_id: str,
        name: str,
        path: str,
        metadata: Dict[str, Any],
        description: Optional[str] = None
    ) -> Action:
        """Create action for opening an existing project"""
        return Action(
            id=str(uuid4()),
            type=ActionType.OPEN_PROJECT,
            timestamp=datetime.now(),
            description=description or f"Open project: {name}",
            payload={
                "project_id": project_id,
                "name": name,
                "path": path,
                "metadata": metadata
            },
            metadata={
                "project_id": project_id,
                "project_name": name
            }
        )
    
    @staticmethod
    def create_project(
        project_id: str,
        name: str,
        path: str,
        metadata: Dict[str, Any],
        description: Optional[str] = None
    ) -> Action:
        """Create action for creating a new project"""
        return Action(
            id=str(uuid4()),
            type=ActionType.CREATE_PROJECT,
            timestamp=datetime.now(),
            description=description or f"Create project: {name}",
            payload={
                "project_id": project_id,
                "name": name,
                "path": path,
                "metadata": metadata
            },
            metadata={
                "project_id": project_id,
                "project_name": name
            }
        )
    
    @staticmethod
    def save_project(description: Optional[str] = None) -> Action:
        """Create action for saving current project"""
        return Action(
            id=str(uuid4()),
            type=ActionType.SAVE_PROJECT,
            timestamp=datetime.now(),
            description=description or "Save project",
            payload={}
        )
    
    @staticmethod
    def close_project(description: Optional[str] = None) -> Action:
        """Create action for closing current project"""
        return Action(
            id=str(uuid4()),
            type=ActionType.CLOSE_PROJECT,
            timestamp=datetime.now(),
            description=description or "Close project",
            payload={},
            changes=[
                Change(
                    path="project",
                    type=ChangeType.UPDATE,
                    new_value=None
                )
            ]
        )
    
    @staticmethod
    def update_project_meta(updates: Dict[str, Any], description: Optional[str] = None) -> Action:
        """Create action for updating project metadata"""
        return Action(
            id=str(uuid4()),
            type=ActionType.UPDATE_PROJECT_META,
            timestamp=datetime.now(),
            description=description or "Update project metadata",
            payload={
                "updates": updates
            },
            metadata={
                "updated_properties": list(updates.keys())
            }
        )
    
    @staticmethod
    def add_recent_project(project_data: Dict[str, Any], description: Optional[str] = None) -> Action:
        """Create action for adding project to recent projects"""
        project_name = project_data.get('name', 'Project')
        
        return Action(
            id=str(uuid4()),
            type=ActionType.UPDATE_PROJECT_META,  # Reuse for recent projects
            timestamp=datetime.now(),
            description=description or f"Add {project_name} to recent projects",
            payload={
                "action": "add_recent",
                "project_data": project_data
            },
            metadata={
                "project_id": project_data.get('id'),
                "project_name": project_name
            }
        )
    
    @staticmethod
    def project_saved(saved_time: datetime, description: Optional[str] = None) -> Action:
        """Create action for marking project as saved"""
        return Action(
            id=str(uuid4()),
            type=ActionType.UPDATE_PROJECT_META,
            timestamp=datetime.now(),
            description=description or "Project saved",
            payload={
                "updates": {
                    "last_saved": saved_time,
                    "has_unsaved_changes": False
                }
            }
        )
    
    @staticmethod
    def clear_components(description: Optional[str] = None) -> Action:
        """Create action for clearing all components"""
        return Action(
            id=str(uuid4()),
            type=ActionType.DELETE_COMPONENT,  # Reuse for clearing
            timestamp=datetime.now(),
            description=description or "Clear all components",
            payload={
                "action": "clear_all"
            }
        )
    
    @staticmethod
    def update_canvas_state(canvas_data: Dict[str, Any], description: Optional[str] = None) -> Action:
        """Create action for updating canvas state"""
        return Action(
            id=str(uuid4()),
            type=ActionType.ZOOM_CANVAS,  # Reuse for canvas updates
            timestamp=datetime.now(),
            description=description or "Update canvas state",
            payload={
                "action": "update_state",
                "canvas_data": canvas_data
            }
        )
    
    @staticmethod
    def reset_canvas(description: Optional[str] = None) -> Action:
        """Create action for resetting canvas to default state"""
        return Action(
            id=str(uuid4()),
            type=ActionType.ZOOM_CANVAS,  # Reuse for canvas updates
            timestamp=datetime.now(),
            description=description or "Reset canvas",
            payload={
                "action": "reset"
            }
        )
    
    @staticmethod
    def update_preferences(updates: Dict[str, Any], description: Optional[str] = None) -> Action:
        """Create action for updating user preferences"""
        return Action(
            id=str(uuid4()),
            type=ActionType.UPDATE_PREFERENCES,
            timestamp=datetime.now(),
            description=description or "Update preferences",
            payload={
                "updates": updates
            }
        )
    
    @staticmethod
    def save_project(
        project_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> Action:
        """Create action for saving the current project"""
        return Action(
            id=str(uuid4()),
            type=ActionType.SAVE_PROJECT,
            timestamp=datetime.now(),
            description=description or "Save project",
            payload={
                "project_id": project_id
            },
            metadata={
                "project_id": project_id
            }
        )
    
    @staticmethod
    def close_project(description: Optional[str] = None) -> Action:
        """Create action for closing the current project"""
        return Action(
            id=str(uuid4()),
            type=ActionType.CLOSE_PROJECT,
            timestamp=datetime.now(),
            description=description or "Close project",
            payload={}
        )
    
    @staticmethod
    def resize_panel(
        panel_name: str,
        new_width: float,
        old_width: Optional[float] = None,
        description: Optional[str] = None
    ) -> Action:
        """Create action for resizing a panel"""
        return Action(
            id=str(uuid4()),
            type=ActionType.RESIZE_PANEL,
            timestamp=datetime.now(),
            description=description or f"Resize {panel_name} panel",
            payload={
                "panel": panel_name,
                "width": new_width
            },
            changes=[
                Change(
                    path=f"panels.{panel_name}_width",
                    type=ChangeType.UPDATE,
                    old_value=old_width,
                    new_value=new_width
                )
            ],
            metadata={
                "panel": panel_name
            }
        )
    
    @staticmethod
    def toggle_panel(
        panel_name: str,
        visible: bool,
        description: Optional[str] = None
    ) -> Action:
        """Create action for toggling panel visibility"""
        action_desc = "Show" if visible else "Hide"
        
        return Action(
            id=str(uuid4()),
            type=ActionType.TOGGLE_PANEL,
            timestamp=datetime.now(),
            description=description or f"{action_desc} {panel_name} panel",
            payload={
                "panel": panel_name,
                "visible": visible
            },
            changes=[
                Change(
                    path=f"panels.{panel_name}_visible",
                    type=ChangeType.UPDATE,
                    new_value=visible
                )
            ],
            metadata={
                "panel": panel_name,
                "visible": visible
            }
        )
    
    @staticmethod
    def change_theme(
        theme_mode: str,
        description: Optional[str] = None
    ) -> Action:
        """Create action for changing the theme"""
        return Action(
            id=str(uuid4()),
            type=ActionType.CHANGE_THEME,
            timestamp=datetime.now(),
            description=description or f"Change theme to {theme_mode}",
            payload={
                "mode": theme_mode
            },
            changes=[
                Change(
                    path="theme.mode",
                    type=ChangeType.UPDATE,
                    new_value=theme_mode
                )
            ],
            metadata={
                "theme_mode": theme_mode
            }
        )
    
    @staticmethod
    def update_preferences(
        preferences: Dict[str, Any],
        description: Optional[str] = None
    ) -> Action:
        """Create action for updating user preferences"""
        return Action(
            id=str(uuid4()),
            type=ActionType.UPDATE_PREFERENCES,
            timestamp=datetime.now(),
            description=description or "Update preferences",
            payload={
                "preferences": preferences
            },
            metadata={
                "updated_keys": list(preferences.keys())
            }
        )
    
    @staticmethod
    def zoom_canvas(
        zoom_delta: float,
        zoom_center: Optional[Dict[str, float]] = None,
        description: Optional[str] = None
    ) -> Action:
        """Create action for zooming the canvas"""
        zoom_action = "Zoom in" if zoom_delta > 0 else "Zoom out"
        
        return Action(
            id=str(uuid4()),
            type=ActionType.ZOOM_CANVAS,
            timestamp=datetime.now(),
            description=description or zoom_action,
            payload={
                "delta": zoom_delta,
                "center": zoom_center
            },
            metadata={
                "zoom_delta": zoom_delta
            }
        )
    
    @staticmethod
    def pan_canvas(
        delta_x: float,
        delta_y: float,
        description: Optional[str] = None
    ) -> Action:
        """Create action for panning the canvas"""
        return Action(
            id=str(uuid4()),
            type=ActionType.PAN_CANVAS,
            timestamp=datetime.now(),
            description=description or "Pan canvas",
            payload={
                "delta_x": delta_x,
                "delta_y": delta_y
            },
            metadata={
                "pan_delta": {"x": delta_x, "y": delta_y}
            }
        )
    
    @staticmethod
    def toggle_grid(
        show_grid: bool,
        description: Optional[str] = None
    ) -> Action:
        """Create action for toggling grid visibility"""
        action_desc = "Show grid" if show_grid else "Hide grid"
        
        return Action(
            id=str(uuid4()),
            type=ActionType.TOGGLE_GRID,
            timestamp=datetime.now(),
            description=description or action_desc,
            payload={
                "show_grid": show_grid
            },
            changes=[
                Change(
                    path="canvas.show_grid",
                    type=ChangeType.UPDATE,
                    new_value=show_grid
                )
            ],
            metadata={
                "show_grid": show_grid
            }
        )
    
    @staticmethod
    def toggle_guides(
        show_guides: bool,
        description: Optional[str] = None
    ) -> Action:
        """Create action for toggling guide visibility"""
        action_desc = "Show guides" if show_guides else "Hide guides"
        
        return Action(
            id=str(uuid4()),
            type=ActionType.TOGGLE_GUIDES,
            timestamp=datetime.now(),
            description=description or action_desc,
            payload={
                "show_guides": show_guides
            },
            changes=[
                Change(
                    path="canvas.show_guides",
                    type=ChangeType.UPDATE,
                    new_value=show_guides
                )
            ],
            metadata={
                "show_guides": show_guides
            }
        )
    
    @staticmethod
    def start_batch(description: str = "Batch Operation") -> Action:
        """Create action for starting a batch operation"""
        batch_id = str(uuid4())
        
        return Action(
            id=str(uuid4()),
            type=ActionType.BATCH_START,
            timestamp=datetime.now(),
            description=f"Start batch: {description}",
            payload={
                "batch_id": batch_id,
                "description": description
            },
            metadata={
                "batch_id": batch_id
            }
        )
    
    @staticmethod
    def end_batch(batch_id: str, description: Optional[str] = None) -> Action:
        """Create action for ending a batch operation"""
        return Action(
            id=str(uuid4()),
            type=ActionType.BATCH_END,
            timestamp=datetime.now(),
            description=description or f"End batch: {batch_id}",
            payload={
                "batch_id": batch_id
            },
            metadata={
                "batch_id": batch_id
            }
        )