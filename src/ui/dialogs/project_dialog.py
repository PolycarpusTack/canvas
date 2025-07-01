"""Project creation and import dialogs"""

import flet as ft
from typing import Callable, Optional
from pathlib import Path


class NewProjectDialog(ft.AlertDialog):
    """Dialog for creating a new project"""
    
    def __init__(self, on_create: Callable[[str, str, str], None]):
        self.on_create = on_create
        
        # Form fields
        self.name_field = ft.TextField(
            label="Project Name",
            hint_text="My Awesome Project",
            autofocus=True,
            on_submit=lambda e: self._on_submit()
        )
        
        self.description_field = ft.TextField(
            label="Description (optional)",
            hint_text="A brief description of your project",
            multiline=True,
            min_lines=2,
            max_lines=3
        )
        
        self.location_field = ft.TextField(
            label="Location",
            hint_text="Leave empty for default location",
            suffix=ft.IconButton(
                icon=ft.Icons.FOLDER_OPEN,
                on_click=self._browse_location
            )
        )
        
        super().__init__(
            modal=True,
            title=ft.Text("Create New Project"),
            content=ft.Container(
                width=400,
                content=ft.Column([
                    self.name_field,
                    self.description_field,
                    self.location_field
                ], spacing=16, tight=True)
            ),
            actions=[
                ft.TextButton("Cancel", on_click=self._on_cancel),
                ft.ElevatedButton("Create", on_click=self._on_submit)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
    
    def _browse_location(self, e):
        """Browse for project location"""
        # In a real implementation, this would open a folder picker
        # For now, we'll just show a message
        self.location_field.value = str(Path.home() / "CanvasEditor" / "Projects")
        self.location_field.update()
    
    def _on_submit(self, e=None):
        """Handle form submission"""
        name = self.name_field.value.strip()
        if not name:
            self.name_field.error_text = "Project name is required"
            self.name_field.update()
            return
        
        description = self.description_field.value.strip()
        location = self.location_field.value.strip()
        
        self.open = False
        self.page.update()
        
        self.on_create(name, description, location)
    
    def _on_cancel(self, e):
        """Handle cancel"""
        self.open = False
        self.page.update()


class ImportProjectDialog(ft.AlertDialog):
    """Dialog for importing an existing project"""
    
    def __init__(self, on_import: Callable[[str], None]):
        self.on_import = on_import
        
        self.path_field = ft.TextField(
            label="Project Folder",
            hint_text="Select the folder containing your web project",
            suffix=ft.IconButton(
                icon=ft.Icons.FOLDER_OPEN,
                on_click=self._browse_folder
            )
        )
        
        self.info_text = ft.Text(
            "Canvas will scan the folder for web files and create a project.",
            size=12,
            color="#6B7280"
        )
        
        super().__init__(
            modal=True,
            title=ft.Text("Import Existing Project"),
            content=ft.Container(
                width=400,
                content=ft.Column([
                    self.path_field,
                    self.info_text,
                    ft.Container(
                        bgcolor="#F3F4F6",
                        border_radius=8,
                        padding=16,
                        content=ft.Column([
                            ft.Text("Supported frameworks:", weight=ft.FontWeight.W_500),
                            ft.Text("• React, Vue, Angular, Svelte", size=12),
                            ft.Text("• Plain HTML/CSS/JS", size=12),
                            ft.Text("• Any web project structure", size=12)
                        ], spacing=4)
                    )
                ], spacing=16, tight=True)
            ),
            actions=[
                ft.TextButton("Cancel", on_click=self._on_cancel),
                ft.ElevatedButton("Import", on_click=self._on_submit)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
    
    def _browse_folder(self, e):
        """Browse for folder"""
        # In a real implementation, this would open a folder picker
        # For now, we'll show a placeholder
        self.path_field.value = str(Path.home() / "Documents" / "my-web-project")
        self.path_field.update()
    
    def _on_submit(self, e=None):
        """Handle form submission"""
        path = self.path_field.value.strip()
        if not path:
            self.path_field.error_text = "Please select a folder"
            self.path_field.update()
            return
        
        self.open = False
        self.page.update()
        
        self.on_import(path)
    
    def _on_cancel(self, e):
        """Handle cancel"""
        self.open = False
        self.page.update()


class ProjectErrorDialog(ft.AlertDialog):
    """Dialog for showing project-related errors"""
    
    def __init__(self, error_message: str):
        super().__init__(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.ERROR_OUTLINE, color="#EF4444"),
                ft.Text("Project Error")
            ]),
            content=ft.Container(
                width=400,
                content=ft.Text(error_message)
            ),
            actions=[
                ft.ElevatedButton("OK", on_click=self._on_close)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
    
    def _on_close(self, e):
        """Close dialog"""
        self.open = False
        self.page.update()