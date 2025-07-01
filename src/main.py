"""Canvas Editor - Entry point"""

import flet as ft
import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app import CanvasEditor


async def main(page: ft.Page):
    """Main entry point for Canvas Editor"""
    try:
        # Create and initialize the editor
        editor = CanvasEditor(page)
        await editor.initialize()
        
    except Exception as e:
        print(f"Error initializing Canvas Editor: {e}")
        # Show error dialog
        error_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Initialization Error"),
            content=ft.Text(f"Failed to initialize Canvas Editor:\n{str(e)}"),
            actions=[
                ft.TextButton("OK", on_click=lambda e: page.window.close())
            ]
        )
        page.overlay.append(error_dialog)
        error_dialog.open = True
        page.update()


if __name__ == "__main__":
    # Run the application
    ft.app(
        target=main,
        view=ft.AppView.FLET_APP,
        port=8550
    )