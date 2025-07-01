"""
Advanced Property Input Types
Implements missing input types: file upload, icon picker, date picker, range slider
Following CLAUDE.md guidelines for comprehensive input system
"""

import flet as ft
from typing import Any, Callable, Optional, List, Dict
from datetime import datetime, date
import logging
import re

from components.property_definitions import PropertyDefinition, PropertyType
from property_input_base import PropertyInputBase

logger = logging.getLogger(__name__)


class FilePropertyInput(PropertyInputBase):
    """File upload input with validation and preview"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_picker = None
        self.upload_status = "idle"  # idle, uploading, success, error
        self.file_info = None
        
    def _build_input_control(self) -> ft.Control:
        """Build file upload interface"""
        # File picker (would be initialized with actual file picker in real app)
        self.file_picker = ft.FilePicker(
            on_result=self._on_file_picked
        )
        
        # Current file display
        current_file_display = self._build_current_file_display()
        
        # Upload area
        upload_area = ft.Container(
            content=ft.Column([
                ft.Icon(
                    ft.Icons.CLOUD_UPLOAD_OUTLINED,
                    size=32,
                    color="#9CA3AF"
                ),
                ft.Text(
                    "Click to select file or drag and drop",
                    size=14,
                    color="#6B7280",
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    self._get_allowed_types_text(),
                    size=12,
                    color="#9CA3AF",
                    text_align=ft.TextAlign.CENTER
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
            bgcolor="#F9FAFB",
            border=ft.border.all(2, "#E5E7EB", ft.BorderStyle.DASHED),
            border_radius=8,
            padding=20,
            on_click=lambda e: self._open_file_picker(),
            ink=True
        )
        
        # Progress indicator
        progress_indicator = ft.ProgressRing(
            visible=self.upload_status == "uploading",
            width=20,
            height=20
        )
        
        # Action buttons
        action_buttons = ft.Row([
            ft.ElevatedButton(
                text="Select File",
                icon=ft.Icons.FOLDER_OPEN,
                on_click=lambda e: self._open_file_picker()
            ),
            ft.IconButton(
                icon=ft.Icons.CLEAR,
                tooltip="Clear file",
                on_click=lambda e: self._clear_file(),
                visible=bool(self.value)
            ),
            progress_indicator
        ], alignment=ft.MainAxisAlignment.START, spacing=8)
        
        return ft.Column([
            current_file_display,
            upload_area,
            action_buttons
        ], spacing=12)
    
    def _build_current_file_display(self) -> ft.Control:
        """Build display for currently selected file"""
        if not self.value:
            return ft.Container()
        
        # Parse file info
        file_name = str(self.value).split('/')[-1] if isinstance(self.value, str) else "Unknown file"
        file_size = self._get_file_size_display()
        file_type = self._get_file_type()
        
        return ft.Container(
            content=ft.Row([
                ft.Icon(
                    self._get_file_icon(file_type),
                    size=24,
                    color="#5E6AD2"
                ),
                ft.Column([
                    ft.Text(
                        file_name,
                        size=14,
                        weight=ft.FontWeight.W_500,
                        color="#374151"
                    ),
                    ft.Text(
                        f"{file_type} • {file_size}",
                        size=12,
                        color="#6B7280"
                    )
                ], spacing=2, tight=True),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.DOWNLOAD,
                    tooltip="Download file",
                    on_click=lambda e: self._download_file(),
                    icon_size=16
                )
            ], alignment=ft.MainAxisAlignment.START),
            bgcolor="#F3F4F6",
            border_radius=6,
            padding=12,
            visible=bool(self.value)
        )
    
    def _get_allowed_types_text(self) -> str:
        """Get display text for allowed file types"""
        if self.definition.validation and self.definition.validation.allowed_extensions:
            extensions = self.definition.validation.allowed_extensions
            return f"Allowed: {', '.join(extensions)}"
        return "All file types allowed"
    
    def _get_file_size_display(self) -> str:
        """Get human-readable file size"""
        # In real implementation, would get actual file size
        return "Unknown size"
    
    def _get_file_type(self) -> str:
        """Get file type from value"""
        if isinstance(self.value, str):
            extension = self.value.split('.')[-1].lower()
            return extension.upper()
        return "Unknown"
    
    def _get_file_icon(self, file_type: str) -> str:
        """Get appropriate icon for file type"""
        icon_map = {
            "PDF": ft.Icons.PICTURE_AS_PDF,
            "DOC": ft.Icons.DESCRIPTION,
            "DOCX": ft.Icons.DESCRIPTION,
            "XLS": ft.Icons.TABLE_CHART,
            "XLSX": ft.Icons.TABLE_CHART,
            "JPG": ft.Icons.IMAGE,
            "JPEG": ft.Icons.IMAGE,
            "PNG": ft.Icons.IMAGE,
            "GIF": ft.Icons.IMAGE,
            "SVG": ft.Icons.IMAGE,
            "MP4": ft.Icons.VIDEO_FILE,
            "AVI": ft.Icons.VIDEO_FILE,
            "MP3": ft.Icons.AUDIO_FILE,
            "WAV": ft.Icons.AUDIO_FILE,
            "TXT": ft.Icons.TEXT_SNIPPET,
            "ZIP": ft.Icons.ARCHIVE,
            "RAR": ft.Icons.ARCHIVE
        }
        return icon_map.get(file_type, ft.Icons.INSERT_DRIVE_FILE)
    
    def _open_file_picker(self) -> None:
        """Open file picker dialog"""
        # In real implementation, would use the file picker
        logger.info("File picker would open here")
        
        # Simulate file selection for demo
        self._simulate_file_selection()
    
    def _simulate_file_selection(self) -> None:
        """Simulate file selection for demo purposes"""
        # This would be replaced with actual file picker logic
        demo_file = "example_document.pdf"
        self._handle_change(demo_file)
    
    def _on_file_picked(self, e) -> None:
        """Handle file picker result"""
        if e.files:
            file_path = e.files[0].path
            self._validate_and_set_file(file_path)
    
    def _validate_and_set_file(self, file_path: str) -> None:
        """Validate and set selected file"""
        # Validate file extension
        if self.definition.validation and self.definition.validation.allowed_extensions:
            extension = file_path.split('.')[-1].lower()
            if extension not in [ext.lower() for ext in self.definition.validation.allowed_extensions]:
                self.validation_result = ValidationResult(
                    is_valid=False,
                    errors=[f"File type .{extension} is not allowed"]
                )
                self._update_validation_ui()
                return
        
        # Validate file size (would check actual file size in real implementation)
        if self.definition.validation and self.definition.validation.max_file_size:
            # Simulated file size check
            pass
        
        self._handle_change(file_path)
    
    def _clear_file(self) -> None:
        """Clear selected file"""
        self._handle_change("")
    
    def _download_file(self) -> None:
        """Download/view current file"""
        if self.value:
            logger.info(f"Would download file: {self.value}")
    
    def _update_input_value(self, value: Any) -> None:
        """Update the input control's value"""
        # Rebuild the file display
        self.content = self._build_input_control()


class IconPropertyInput(PropertyInputBase):
    """Icon picker with search and categories"""
    
    # Common icon sets
    ICON_CATEGORIES = {
        "Actions": [
            "add", "edit", "delete", "save", "cancel", "check", "close", "search",
            "filter", "sort", "refresh", "download", "upload", "share", "print"
        ],
        "Navigation": [
            "home", "menu", "arrow_back", "arrow_forward", "arrow_upward", "arrow_downward",
            "chevron_left", "chevron_right", "expand_more", "expand_less"
        ],
        "Content": [
            "text_fields", "image", "video_file", "audio_file", "folder", "description",
            "link", "attach_file", "calendar_today", "schedule"
        ],
        "Communication": [
            "email", "phone", "chat", "message", "notifications", "campaign",
            "contact_mail", "contact_phone", "group", "person"
        ],
        "Media": [
            "play_arrow", "pause", "stop", "skip_next", "skip_previous", "volume_up",
            "volume_down", "volume_off", "mic", "mic_off"
        ]
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_query = ""
        self.selected_category = "Actions"
        
    def _build_input_control(self) -> ft.Control:
        """Build icon picker interface"""
        # Current icon display
        current_icon_display = self._build_current_icon_display()
        
        # Search field
        search_field = ft.TextField(
            hint_text="Search icons...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=lambda e: self._filter_icons(e.control.value),
            border_radius=6,
            height=36,
            text_size=12
        )
        
        # Category tabs
        category_tabs = self._build_category_tabs()
        
        # Icon grid
        icon_grid = self._build_icon_grid()
        
        # Quick actions
        quick_actions = ft.Row([
            ft.TextButton(
                text="Clear",
                icon=ft.Icons.CLEAR,
                on_click=lambda e: self._clear_icon()
            ),
            ft.TextButton(
                text="Custom",
                icon=ft.Icons.CODE,
                on_click=lambda e: self._open_custom_icon_input()
            )
        ], spacing=8)
        
        return ft.Column([
            current_icon_display,
            search_field,
            category_tabs,
            ft.Container(
                content=icon_grid,
                height=200,
                border=ft.border.all(1, "#E5E7EB"),
                border_radius=6,
                padding=8
            ),
            quick_actions
        ], spacing=8)
    
    def _build_current_icon_display(self) -> ft.Control:
        """Build display for currently selected icon"""
        if not self.value:
            icon_display = ft.Icon(ft.Icons.WIDGETS, size=32, color="#9CA3AF")
            icon_name = "No icon selected"
        else:
            # Try to get the icon from the value
            try:
                icon_display = ft.Icon(getattr(ft.Icons, self.value.upper()), size=32, color="#5E6AD2")
                icon_name = str(self.value)
            except AttributeError:
                icon_display = ft.Icon(ft.Icons.HELP_OUTLINE, size=32, color="#EF4444")
                icon_name = f"Invalid icon: {self.value}"
        
        return ft.Container(
            content=ft.Row([
                icon_display,
                ft.Column([
                    ft.Text("Selected Icon", size=12, color="#6B7280"),
                    ft.Text(icon_name, size=14, weight=ft.FontWeight.W_500)
                ], spacing=2, tight=True)
            ], spacing=12, alignment=ft.MainAxisAlignment.START),
            bgcolor="#F9FAFB",
            border_radius=6,
            padding=12
        )
    
    def _build_category_tabs(self) -> ft.Control:
        """Build category selection tabs"""
        chips = []
        for category in self.ICON_CATEGORIES.keys():
            chip = ft.FilterChip(
                label=ft.Text(category, size=12),
                selected=category == self.selected_category,
                on_select=lambda e, cat=category: self._select_category(cat),
                show_checkmark=False,
                bgcolor="#F9FAFB",
                selected_color="#E0E7FF"
            )
            chips.append(chip)
        
        return ft.Row(chips, spacing=4, scroll=ft.ScrollMode.AUTO)
    
    def _build_icon_grid(self) -> ft.Control:
        """Build grid of available icons"""
        icons = self._get_filtered_icons()
        
        # Create icon buttons in a grid
        icon_buttons = []
        for icon_name in icons:
            try:
                icon_attr = getattr(ft.Icons, icon_name.upper())
                button = ft.IconButton(
                    icon=icon_attr,
                    tooltip=icon_name,
                    on_click=lambda e, name=icon_name: self._select_icon(name),
                    icon_size=20,
                    style=ft.ButtonStyle(
                        bgcolor={"": "#F9FAFB", "hovered": "#E5E7EB"},
                        shape=ft.RoundedRectangleBorder(radius=4)
                    )
                )
                icon_buttons.append(button)
            except AttributeError:
                continue
        
        # Arrange in rows of 8
        rows = []
        for i in range(0, len(icon_buttons), 8):
            row = ft.Row(
                icon_buttons[i:i+8],
                spacing=4,
                alignment=ft.MainAxisAlignment.START
            )
            rows.append(row)
        
        return ft.Column(
            rows,
            spacing=4,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
    
    def _get_filtered_icons(self) -> List[str]:
        """Get icons for current category and search"""
        category_icons = self.ICON_CATEGORIES.get(self.selected_category, [])
        
        if self.search_query:
            query_lower = self.search_query.lower()
            return [icon for icon in category_icons if query_lower in icon.lower()]
        
        return category_icons
    
    def _filter_icons(self, query: str) -> None:
        """Filter icons based on search query"""
        self.search_query = query
        self._refresh_icon_grid()
    
    def _select_category(self, category: str) -> None:
        """Select icon category"""
        self.selected_category = category
        self._refresh_icon_grid()
    
    def _refresh_icon_grid(self) -> None:
        """Refresh the icon grid display"""
        # Rebuild the control
        self.content = self._build_input_control()
        self.update()
    
    def _select_icon(self, icon_name: str) -> None:
        """Select an icon"""
        self._handle_change(icon_name)
        logger.info(f"Selected icon: {icon_name}")
    
    def _clear_icon(self) -> None:
        """Clear selected icon"""
        self._handle_change("")
    
    def _open_custom_icon_input(self) -> None:
        """Open custom icon input dialog"""
        # In real implementation, would show a dialog for custom icon input
        logger.info("Custom icon input dialog would open here")
    
    def _update_input_value(self, value: Any) -> None:
        """Update the input control's value"""
        self.content = self._build_input_control()


class DatePropertyInput(PropertyInputBase):
    """Date picker with calendar interface"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.date_picker = None
        
    def _build_input_control(self) -> ft.Control:
        """Build date picker interface"""
        # Parse current date
        current_date = self._parse_date_value()
        
        # Date display
        date_display = ft.TextField(
            value=self._format_date_display(current_date),
            read_only=True,
            suffix_icon=ft.Icons.CALENDAR_TODAY,
            on_click=lambda e: self._open_date_picker(),
            border_radius=6,
            height=40,
            text_size=14
        )
        
        # Quick date buttons
        quick_dates = ft.Row([
            ft.TextButton(
                text="Today",
                on_click=lambda e: self._set_date(datetime.now().date())
            ),
            ft.TextButton(
                text="Tomorrow", 
                on_click=lambda e: self._set_date(datetime.now().date().replace(day=datetime.now().day + 1))
            ),
            ft.TextButton(
                text="Clear",
                on_click=lambda e: self._clear_date()
            )
        ], spacing=4)
        
        return ft.Column([
            date_display,
            quick_dates
        ], spacing=8)
    
    def _parse_date_value(self) -> Optional[date]:
        """Parse the current date value"""
        if not self.value:
            return None
        
        if isinstance(self.value, date):
            return self.value
        
        if isinstance(self.value, datetime):
            return self.value.date()
        
        if isinstance(self.value, str):
            try:
                # Try common date formats
                for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"]:
                    try:
                        return datetime.strptime(self.value, fmt).date()
                    except ValueError:
                        continue
            except Exception:
                pass
        
        return None
    
    def _format_date_display(self, date_value: Optional[date]) -> str:
        """Format date for display"""
        if date_value:
            return date_value.strftime("%B %d, %Y")
        return "Select a date..."
    
    def _open_date_picker(self) -> None:
        """Open date picker dialog"""
        # Create date picker
        self.date_picker = ft.DatePicker(
            first_date=datetime(1900, 1, 1),
            last_date=datetime(2100, 12, 31),
            on_change=self._on_date_picked
        )
        
        # In real implementation, would add to page and open
        logger.info("Date picker would open here")
        
        # Simulate date selection for demo
        self._simulate_date_selection()
    
    def _simulate_date_selection(self) -> None:
        """Simulate date selection for demo"""
        today = datetime.now().date()
        self._set_date(today)
    
    def _on_date_picked(self, e) -> None:
        """Handle date picker result"""
        if e.date:
            self._set_date(e.date)
    
    def _set_date(self, date_value: date) -> None:
        """Set the date value"""
        # Format as ISO string for storage
        iso_string = date_value.isoformat()
        self._handle_change(iso_string)
    
    def _clear_date(self) -> None:
        """Clear the date value"""
        self._handle_change("")
    
    def _update_input_value(self, value: Any) -> None:
        """Update the input control's value"""
        self.content = self._build_input_control()


class RangePropertyInput(PropertyInputBase):
    """Range slider with numeric input"""
    
    def _build_input_control(self) -> ft.Control:
        """Build range slider interface"""
        # Parse current value
        current_value = float(self.value) if self.value is not None else (self.definition.min_value or 0)
        min_val = self.definition.min_value or 0
        max_val = self.definition.max_value or 100
        step = self.definition.step or 1
        
        # Value display
        value_display = ft.Text(
            f"{current_value}{getattr(self.definition, 'default_unit', '')}",
            size=14,
            weight=ft.FontWeight.W_500,
            color="#374151"
        )
        
        # Slider
        self.slider = ft.Slider(
            min=min_val,
            max=max_val,
            value=current_value,
            divisions=int((max_val - min_val) / step) if step > 0 else None,
            on_change=lambda e: self._on_slider_change(e.control.value)
        )
        
        # Min/max labels
        min_max_labels = ft.Row([
            ft.Text(str(min_val), size=12, color="#6B7280"),
            ft.Container(expand=True),
            ft.Text(str(max_val), size=12, color="#6B7280")
        ])
        
        # Numeric input for precise control
        numeric_input = ft.TextField(
            value=str(current_value),
            width=80,
            height=36,
            text_size=12,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda e: self._on_numeric_change(e.control.value),
            border_radius=4,
            text_align=ft.TextAlign.CENTER
        )
        
        return ft.Column([
            ft.Row([
                ft.Text("Value:", size=12, color="#6B7280"),
                value_display,
                ft.Container(expand=True),
                numeric_input
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            self.slider,
            min_max_labels
        ], spacing=8)
    
    def _on_slider_change(self, value: float) -> None:
        """Handle slider value change"""
        # Apply step rounding
        if self.definition.step:
            value = round(value / self.definition.step) * self.definition.step
        
        self._handle_change(value)
        self._update_displays(value)
    
    def _on_numeric_change(self, value_str: str) -> None:
        """Handle numeric input change"""
        try:
            value = float(value_str)
            
            # Clamp to min/max
            if self.definition.min_value is not None:
                value = max(value, self.definition.min_value)
            if self.definition.max_value is not None:
                value = min(value, self.definition.max_value)
            
            self._handle_change(value)
            self._update_displays(value)
        except ValueError:
            # Invalid number, ignore
            pass
    
    def _update_displays(self, value: float) -> None:
        """Update slider and text displays"""
        self.slider.value = value
        # Update other displays
        self.update()
    
    def _update_input_value(self, value: Any) -> None:
        """Update the input control's value"""
        self.content = self._build_input_control()


# Update the factory function to include new input types
def create_advanced_property_input(
    definition: PropertyDefinition,
    value: Any,
    on_change: Callable[[str, Any], None],
    **kwargs
) -> PropertyInputBase:
    """Factory function for advanced property input types"""
    
    input_classes = {
        PropertyType.FILE: FilePropertyInput,
        PropertyType.ICON: IconPropertyInput,
        PropertyType.DATE: DatePropertyInput,
        PropertyType.RANGE: RangePropertyInput
    }
    
    input_class = input_classes.get(definition.type)
    if input_class:
        return input_class(definition, value, on_change, **kwargs)
    
    # Fall back to base factory
    from property_input_base import create_property_input
    return create_property_input(definition, value, on_change, **kwargs)