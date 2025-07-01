"""Rich text editor component"""

import flet as ft
from typing import Callable, Optional, List, Dict
from config.constants import EDITOR_TOOLBAR_ITEMS


class EditorToolbarButton(ft.Container):
    """Toolbar button for the rich editor"""
    
    def __init__(self, item: Dict[str, str], on_command: Callable[[str], None]):
        self.item = item
        self.on_command = on_command
        
        if item.get("icon"):
            content = ft.Icon(item["icon"], size=14)
        else:
            content = ft.Text(item.get("text", ""), size=10, weight=ft.FontWeight.W_600)
        
        super().__init__(
            width=32,
            height=32,
            bgcolor="white",
            border=ft.border.all(1, "#D1D5DB"),
            border_radius=4,
            content=content,
            alignment=ft.alignment.center,
            on_hover=self._on_hover,
            on_click=lambda e: on_command(item.get("command", "")),
            tooltip=item.get("name", "")
        )
    
    def _on_hover(self, e: ft.ControlEvent):
        """Handle hover effect"""
        if e.data == "true":
            self.bgcolor = "#F3F4F6"
        else:
            self.bgcolor = "white"
        self.update()


class RichTextEditor(ft.Container):
    """Rich text editor with formatting toolbar"""
    
    def __init__(self, 
                 value: str = "",
                 on_change: Optional[Callable[[str], None]] = None,
                 height: int = 200):
        self.value = value
        self.on_change = on_change
        self.height = height
        
        # Create text field for content
        self.text_field = ft.TextField(
            value=value,
            multiline=True,
            min_lines=5,
            max_lines=20,
            border=ft.InputBorder.NONE,
            on_change=self._on_text_change
        )
        
        super().__init__(
            border=ft.border.all(1, "#D1D5DB"),
            border_radius=8,
            content=self._build_content()
        )
    
    def _build_content(self) -> ft.Control:
        """Build editor with toolbar and content area"""
        return ft.Column([
            # Toolbar
            self._build_toolbar(),
            
            # Content area
            ft.Container(
                content=self.text_field,
                padding=16,
                min_height=self.height
            )
        ], spacing=0)
    
    def _build_toolbar(self) -> ft.Control:
        """Build the formatting toolbar"""
        toolbar_items = []
        
        for item in EDITOR_TOOLBAR_ITEMS:
            if item == "separator":
                toolbar_items.append(
                    ft.Container(width=1, height=24, bgcolor="#D1D5DB")
                )
            else:
                toolbar_items.append(
                    EditorToolbarButton(item, self._execute_command)
                )
        
        return ft.Container(
            bgcolor="#F9FAFB",
            border=ft.border.only(bottom=ft.BorderSide(1, "#E5E7EB")),
            padding=8,
            content=ft.Row(toolbar_items, spacing=8, wrap=True)
        )
    
    def _execute_command(self, command: str):
        """Execute editor command"""
        # In a real implementation, this would apply formatting
        # For now, we'll just update the selection or insert text
        if command == "bold":
            self._wrap_selection("**", "**")
        elif command == "italic":
            self._wrap_selection("*", "*")
        elif command == "link":
            self._insert_link()
        # Add more commands as needed
    
    def _wrap_selection(self, prefix: str, suffix: str):
        """Wrap selected text with prefix and suffix"""
        # This is a simplified version - real implementation would need
        # to handle text selection properly
        current_text = self.text_field.value or ""
        # For demo, just append
        self.text_field.value = current_text + f"{prefix}text{suffix}"
        self.text_field.update()
        if self.on_change:
            self.on_change(self.text_field.value)
    
    def _insert_link(self):
        """Insert a link"""
        # Simplified - real implementation would show a dialog
        current_text = self.text_field.value or ""
        self.text_field.value = current_text + "[Link text](https://example.com)"
        self.text_field.update()
        if self.on_change:
            self.on_change(self.text_field.value)
    
    def _on_text_change(self, e: ft.ControlEvent):
        """Handle text change"""
        self.value = e.control.value
        if self.on_change:
            self.on_change(self.value)
    
    def get_value(self) -> str:
        """Get current editor value"""
        return self.value
    
    def set_value(self, value: str):
        """Set editor value"""
        self.value = value
        self.text_field.value = value
        self.text_field.update()