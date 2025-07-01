#!/usr/bin/env python3
"""
Simplified Canvas Editor without state management - to identify blank screen issue
"""

import flet as ft
import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

class SimpleCanvasEditor:
    def __init__(self):
        self.page = None
    
    async def main(self, page: ft.Page):
        """Simplified main without state management"""
        self.page = page
        page.title = "Simple Canvas Editor"
        page.padding = 0
        page.theme_mode = ft.ThemeMode.LIGHT
        
        # Simple 4-panel layout without resize handles
        page.add(
            ft.Row(
                controls=[
                    # Sidebar
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Tools", size=12, weight=ft.FontWeight.BOLD),
                            ft.IconButton(ft.Icons.DASHBOARD, tooltip="Home"),
                            ft.IconButton(ft.Icons.ARTICLE, tooltip="Pages"),
                            ft.IconButton(ft.Icons.SETTINGS, tooltip="Settings")
                        ], spacing=5),
                        width=80,
                        height=600,
                        bgcolor=ft.Colors.GREY_50,
                        padding=10
                    ),
                    
                    # Components Panel
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Components", size=14, weight=ft.FontWeight.BOLD),
                            ft.Divider(),
                            ft.Text("Layout", size=12, weight=ft.FontWeight.W_500),
                            ft.ListTile(
                                leading=ft.Icon(ft.Icons.VIEW_AGENDA),
                                title=ft.Text("Section")
                            ),
                            ft.ListTile(
                                leading=ft.Icon(ft.Icons.TEXT_FIELDS),
                                title=ft.Text("Text")
                            ),
                            ft.ListTile(
                                leading=ft.Icon(ft.Icons.CHECK_BOX),
                                title=ft.Text("Button")
                            )
                        ]),
                        width=280,
                        height=600,
                        bgcolor=ft.Colors.WHITE,
                        padding=10
                    ),
                    
                    # Canvas Area
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text("Canvas", size=14, weight=ft.FontWeight.BOLD),
                                ft.Spacer(),
                                ft.IconButton(ft.Icons.VISIBILITY, tooltip="Preview"),
                                ft.IconButton(ft.Icons.SAVE, tooltip="Save")
                            ]),
                            ft.Divider(),
                            ft.Container(
                                content=ft.Text("Drop components here", 
                                               size=16, 
                                               color=ft.Colors.GREY_500),
                                width=600,
                                height=500,
                                bgcolor=ft.Colors.GREY_100,
                                border=ft.border.all(2, ft.Colors.GREY_300),
                                border_radius=8,
                                alignment=ft.alignment.center
                            )
                        ]),
                        expand=True,
                        height=600,
                        bgcolor=ft.Colors.WHITE,
                        padding=10
                    ),
                    
                    # Properties Panel
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Properties", size=14, weight=ft.FontWeight.BOLD),
                            ft.Divider(),
                            ft.Text("Width"),
                            ft.TextField(value="100", suffix_text="px"),
                            ft.Text("Height"),
                            ft.TextField(value="50", suffix_text="px"),
                            ft.Text("Background"),
                            ft.Dropdown(
                                options=[
                                    ft.DropdownOption("White"),
                                    ft.DropdownOption("Grey"),
                                    ft.DropdownOption("Blue")
                                ]
                            )
                        ]),
                        width=320,
                        height=600,
                        bgcolor=ft.Colors.WHITE,
                        padding=10
                    )
                ],
                spacing=0,
                expand=True
            )
        )
        
        # Show success message
        page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text("Simple Canvas Editor loaded successfully!"),
                duration=3000
            )
        )

def main():
    print("🚀 Starting Simple Canvas Editor...")
    editor = SimpleCanvasEditor()
    
    ft.app(
        target=editor.main,
        view=ft.AppView.WEB_BROWSER,
        port=8553,
        assets_dir=None
    )

if __name__ == "__main__":
    main()