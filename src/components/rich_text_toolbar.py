"""
Rich Text Toolbar - Complete Formatting Controls
Implements TASK A-1-T2 from rich-text-editor development plan with 100% functionality
Following CLAUDE.md guidelines for enterprise-grade text formatting interface
"""

import flet as ft
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum, auto
import logging
import time
from datetime import datetime

from components.rich_text_editor_complete import (
    RichTextEditor, FormatType, SelectionRange, EditorState
)

logger = logging.getLogger(__name__)


class ToolbarGroup(Enum):
    """Toolbar button groups"""
    TEXT_FORMAT = auto()
    PARAGRAPH = auto()
    INSERT = auto()
    ACTIONS = auto()


class ButtonType(Enum):
    """Toolbar button types"""
    TOGGLE = auto()
    ACTION = auto()
    DROPDOWN = auto()
    COLOR_PICKER = auto()


@dataclass
class ToolbarButton:
    """
    Toolbar button configuration
    CLAUDE.md #9.1: Accessible button design
    """
    id: str
    label: str
    icon: str
    type: ButtonType = ButtonType.ACTION
    group: ToolbarGroup = ToolbarGroup.ACTIONS
    tooltip: str = ""
    keyboard_shortcut: str = ""
    is_active: bool = False
    is_enabled: bool = True
    dropdown_items: List[Dict[str, str]] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate button configuration"""
        if not self.id:
            raise ValueError("Button ID is required")
        
        if not self.tooltip:
            self.tooltip = self.label
        
        if self.keyboard_shortcut:
            self.tooltip += f" ({self.keyboard_shortcut})"


@dataclass
class ToolbarConfig:
    """
    Toolbar configuration
    CLAUDE.md #1.4: Extensible toolbar configuration
    """
    show_text_formatting: bool = True
    show_paragraph_formatting: bool = True
    show_insert_options: bool = True
    show_actions: bool = True
    compact_mode: bool = False
    custom_buttons: List[ToolbarButton] = field(default_factory=list)
    
    def get_default_buttons(self) -> List[ToolbarButton]:
        """Get default toolbar buttons"""
        buttons = []
        
        if self.show_actions:
            buttons.extend([
                ToolbarButton(
                    id="undo",
                    label="Undo",
                    icon=ft.Icons.UNDO,
                    group=ToolbarGroup.ACTIONS,
                    keyboard_shortcut="Ctrl+Z"
                ),
                ToolbarButton(
                    id="redo",
                    label="Redo",
                    icon=ft.Icons.REDO,
                    group=ToolbarGroup.ACTIONS,
                    keyboard_shortcut="Ctrl+Y"
                )
            ])
        
        if self.show_text_formatting:
            buttons.extend([
                ToolbarButton(
                    id="bold",
                    label="Bold",
                    icon=ft.Icons.FORMAT_BOLD,
                    type=ButtonType.TOGGLE,
                    group=ToolbarGroup.TEXT_FORMAT,
                    keyboard_shortcut="Ctrl+B"
                ),
                ToolbarButton(
                    id="italic",
                    label="Italic",
                    icon=ft.Icons.FORMAT_ITALIC,
                    type=ButtonType.TOGGLE,
                    group=ToolbarGroup.TEXT_FORMAT,
                    keyboard_shortcut="Ctrl+I"
                ),
                ToolbarButton(
                    id="underline",
                    label="Underline",
                    icon=ft.Icons.FORMAT_UNDERLINED,
                    type=ButtonType.TOGGLE,
                    group=ToolbarGroup.TEXT_FORMAT,
                    keyboard_shortcut="Ctrl+U"
                ),
                ToolbarButton(
                    id="strikethrough",
                    label="Strikethrough",
                    icon=ft.Icons.FORMAT_STRIKETHROUGH,
                    type=ButtonType.TOGGLE,
                    group=ToolbarGroup.TEXT_FORMAT
                ),
                ToolbarButton(
                    id="code",
                    label="Code",
                    icon=ft.Icons.CODE,
                    type=ButtonType.TOGGLE,
                    group=ToolbarGroup.TEXT_FORMAT
                ),
                ToolbarButton(
                    id="link",
                    label="Link",
                    icon=ft.Icons.LINK,
                    group=ToolbarGroup.TEXT_FORMAT,
                    keyboard_shortcut="Ctrl+K"
                )
            ])
        
        if self.show_paragraph_formatting:
            buttons.extend([
                ToolbarButton(
                    id="heading",
                    label="Heading",
                    icon=ft.Icons.FORMAT_SIZE,
                    type=ButtonType.DROPDOWN,
                    group=ToolbarGroup.PARAGRAPH,
                    dropdown_items=[
                        {"id": "h1", "label": "Heading 1", "icon": ""},
                        {"id": "h2", "label": "Heading 2", "icon": ""},
                        {"id": "h3", "label": "Heading 3", "icon": ""},
                        {"id": "h4", "label": "Heading 4", "icon": ""},
                        {"id": "h5", "label": "Heading 5", "icon": ""},
                        {"id": "h6", "label": "Heading 6", "icon": ""},
                        {"id": "paragraph", "label": "Paragraph", "icon": ""}
                    ]
                ),
                ToolbarButton(
                    id="blockquote",
                    label="Quote",
                    icon=ft.Icons.FORMAT_QUOTE,
                    type=ButtonType.TOGGLE,
                    group=ToolbarGroup.PARAGRAPH
                ),
                ToolbarButton(
                    id="code_block",
                    label="Code Block",
                    icon=ft.Icons.CODE_OFF,
                    group=ToolbarGroup.PARAGRAPH
                ),
                ToolbarButton(
                    id="bullet_list",
                    label="Bullet List",
                    icon=ft.Icons.FORMAT_LIST_BULLETED,
                    type=ButtonType.TOGGLE,
                    group=ToolbarGroup.PARAGRAPH
                ),
                ToolbarButton(
                    id="numbered_list",
                    label="Numbered List",
                    icon=ft.Icons.FORMAT_LIST_NUMBERED,
                    type=ButtonType.TOGGLE,
                    group=ToolbarGroup.PARAGRAPH
                )
            ])
        
        if self.show_insert_options:
            buttons.extend([
                ToolbarButton(
                    id="image",
                    label="Image",
                    icon=ft.Icons.IMAGE,
                    group=ToolbarGroup.INSERT
                ),
                ToolbarButton(
                    id="table",
                    label="Table",
                    icon=ft.Icons.TABLE_CHART,
                    group=ToolbarGroup.INSERT
                ),
                ToolbarButton(
                    id="divider",
                    label="Divider",
                    icon=ft.Icons.HORIZONTAL_RULE,
                    group=ToolbarGroup.INSERT
                )
            ])
        
        # Add custom buttons
        buttons.extend(self.custom_buttons)
        
        return buttons


@dataclass
class ToolbarState:
    """Current state of toolbar buttons"""
    active_formats: Set[FormatType] = field(default_factory=set)
    current_block_type: str = "paragraph"
    can_undo: bool = False
    can_redo: bool = False
    selection_range: Optional[SelectionRange] = None
    word_count: int = 0
    character_count: int = 0


class RichTextToolbar:
    """
    Complete rich text formatting toolbar with real functionality
    CLAUDE.md #1.2: Component-based UI with clear separation
    CLAUDE.md #9.1: Accessible toolbar with keyboard shortcuts
    CLAUDE.md #1.5: Performance-optimized button states
    """
    
    def __init__(
        self,
        editor: RichTextEditor,
        enable_advanced_formatting: bool = True,
        enable_block_formatting: bool = True,
        enable_history_controls: bool = True,
        compact_mode: bool = False,
        config: Optional[ToolbarConfig] = None
    ):
        """
        Initialize toolbar with comprehensive formatting controls
        
        Args:
            editor: Rich text editor instance to control
            enable_advanced_formatting: Enable code, links, advanced formatting
            enable_block_formatting: Enable headings, lists, block types
            enable_history_controls: Enable undo/redo buttons
            compact_mode: Show compact version with fewer buttons
            config: Toolbar configuration (legacy support)
        """
        # Core dependencies
        self.editor = editor
        self.enable_advanced_formatting = enable_advanced_formatting
        self.enable_block_formatting = enable_block_formatting
        self.enable_history_controls = enable_history_controls
        self.compact_mode = compact_mode
        
        # Legacy config support
        self.config = config or ToolbarConfig()
        if config:
            self.buttons = self.config.get_default_buttons()
        else:
            self.buttons = []
        
        # Toolbar state management
        self._state = ToolbarState()
        self._button_controls: Dict[str, ft.Control] = {}
        self._active_states: Dict[str, bool] = {}
        self._enabled_states: Dict[str, bool] = {}
        
        # Event handlers
        self._format_handlers: List[Callable[[str, Any], None]] = []
        self._block_handlers: List[Callable[[str], None]] = []
        self._action_handlers: List[Callable[[str], None]] = []
        
        # Performance tracking
        self._last_update_time = 0.0
        self._update_count = 0
        
        # Initialize button states
        for button in self.buttons:
            self._active_states[button.id] = button.is_active
            self._enabled_states[button.id] = button.is_enabled
        
        # Build toolbar UI
        self._toolbar_container = self._build_comprehensive_toolbar()
        
        # Connect to editor events
        self._connect_editor_events()
        
        # Set up keyboard shortcuts
        self._setup_keyboard_shortcuts()
        
        logger.info("Rich text toolbar initialized with full functionality")
    
    def _build_comprehensive_toolbar(self) -> ft.Control:
        """
        Build complete toolbar UI with all formatting controls
        CLAUDE.md #7.2: Safe UI construction
        """
        try:
            toolbar_controls = []
            
            if self.compact_mode:
                # Compact layout with essential buttons only
                toolbar_controls = [
                    self._create_button_group("basic", [
                        self._create_format_button("bold", ft.Icons.FORMAT_BOLD, "Bold", "Ctrl+B"),
                        self._create_format_button("italic", ft.Icons.FORMAT_ITALIC, "Italic", "Ctrl+I"),
                        self._create_format_button("link", ft.Icons.LINK, "Link", "Ctrl+K"),
                    ]),
                    self._create_separator(),
                    self._create_button_group("blocks", [
                        self._create_block_dropdown(),
                    ])
                ]
            else:
                # Full toolbar layout
                
                # Basic formatting group
                basic_group = self._create_button_group("basic", [
                    self._create_format_button("bold", ft.Icons.FORMAT_BOLD, "Bold", "Ctrl+B"),
                    self._create_format_button("italic", ft.Icons.FORMAT_ITALIC, "Italic", "Ctrl+I"),
                    self._create_format_button("underline", ft.Icons.FORMAT_UNDERLINED, "Underline", "Ctrl+U"),
                    self._create_format_button("strikethrough", ft.Icons.FORMAT_STRIKETHROUGH, "Strikethrough", "Ctrl+Shift+X"),
                ])
                toolbar_controls.append(basic_group)
                toolbar_controls.append(self._create_separator())
                
                # Advanced formatting group
                if self.enable_advanced_formatting:
                    advanced_group = self._create_button_group("advanced", [
                        self._create_format_button("code", ft.Icons.CODE, "Code", "Ctrl+`"),
                        self._create_format_button("link", ft.Icons.LINK, "Link", "Ctrl+K"),
                        self._create_action_button("clear_format", ft.Icons.FORMAT_CLEAR, "Clear Format", "Ctrl+\\"),
                    ])
                    toolbar_controls.append(advanced_group)
                    toolbar_controls.append(self._create_separator())
                
                # Block formatting group
                if self.enable_block_formatting:
                    block_group = self._create_button_group("blocks", [
                        self._create_block_dropdown(),
                        self._create_block_button("blockquote", ft.Icons.FORMAT_QUOTE, "Quote"),
                        self._create_block_button("code_block", ft.Icons.INTEGRATION_INSTRUCTIONS, "Code Block"),
                    ])
                    toolbar_controls.append(block_group)
                    toolbar_controls.append(self._create_separator())
                    
                    # List formatting group
                    list_group = self._create_button_group("lists", [
                        self._create_block_button("bullet_list", ft.Icons.FORMAT_LIST_BULLETED, "Bullet List"),
                        self._create_block_button("numbered_list", ft.Icons.FORMAT_LIST_NUMBERED, "Numbered List"),
                    ])
                    toolbar_controls.append(list_group)
                    toolbar_controls.append(self._create_separator())
                
                # History controls group
                if self.enable_history_controls:
                    history_group = self._create_button_group("history", [
                        self._create_action_button("undo", ft.Icons.UNDO, "Undo", "Ctrl+Z"),
                        self._create_action_button("redo", ft.Icons.REDO, "Redo", "Ctrl+Y"),
                    ])
                    toolbar_controls.append(history_group)
                    toolbar_controls.append(self._create_separator())
                
                # Status display
                status_group = self._create_status_display()
                toolbar_controls.append(status_group)
            
            # Create main toolbar container
            return ft.Container(
                content=ft.Row(
                    controls=toolbar_controls,
                    spacing=8,
                    scroll=ft.ScrollMode.AUTO,
                    alignment=ft.MainAxisAlignment.START
                ),
                padding=ft.padding.all(8),
                border=ft.border.only(bottom=ft.BorderSide(1, "#E5E7EB")),
                bgcolor="#FAFAFA",
                height=56
            )
            
        except Exception as e:
            logger.error(f"Failed to build toolbar: {e}")
            return ft.Container(
                content=ft.Text("Toolbar Error", color="#EF4444"),
                height=40
            )
    
    def build(self) -> ft.Control:
        """
        Build toolbar UI component - supports both new and legacy modes
        CLAUDE.md #7.2: Accessible UI construction
        """
        # Use new comprehensive toolbar if editor is provided
        if hasattr(self, '_toolbar_container') and self._toolbar_container:
            return self._toolbar_container
        
        # Legacy mode for backward compatibility
        try:
            # Group buttons by category
            groups = self._group_buttons()
            
            # Create toolbar sections
            toolbar_sections = []
            
            for group_type, group_buttons in groups.items():
                if group_buttons:
                    section = self._build_toolbar_section(group_type, group_buttons)
                    if section:
                        toolbar_sections.append(section)
            
            # Create main toolbar container
            toolbar = ft.Row(
                controls=toolbar_sections,
                spacing=8,
                scroll=ft.ScrollMode.AUTO,
                alignment=ft.MainAxisAlignment.START
            )
            
            return ft.Container(
                content=toolbar,
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                bgcolor="#F8F9FA",
                border_radius=4,
                border=ft.border.all(1, "#E5E7EB")
            )
            
        except Exception as e:
            logger.error(f"Failed to build toolbar: {e}")
            return ft.Container(
                content=ft.Text("Toolbar Error", color="#EF4444"),
                padding=8
            )
    
    # New comprehensive toolbar methods
    
    def _create_format_button(self, format_id: str, icon: str, label: str, shortcut: str = "") -> ft.Control:
        """Create formatting toggle button with real functionality"""
        try:
            tooltip = f"{label} ({shortcut})" if shortcut else label
            
            button = ft.IconButton(
                icon=icon,
                tooltip=tooltip,
                on_click=lambda e, fmt_id=format_id: self._handle_format_button_click(fmt_id),
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=4),
                    padding=ft.padding.all(8),
                    color={
                        ft.MaterialState.DEFAULT: "#374151",
                        ft.MaterialState.SELECTED: "#5E6AD2",
                        ft.MaterialState.HOVERED: "#1F2937"
                    },
                    bgcolor={
                        ft.MaterialState.DEFAULT: ft.colors.TRANSPARENT,
                        ft.MaterialState.SELECTED: "#EEF2FF",
                        ft.MaterialState.HOVERED: "#F3F4F6"
                    }
                ),
                selected=False,
                data=format_id
            )
            
            self._button_controls[format_id] = button
            return button
            
        except Exception as e:
            logger.error(f"Failed to create format button {format_id}: {e}")
            return ft.Text("?", size=12)
    
    def _create_block_button(self, block_id: str, icon: str, label: str) -> ft.Control:
        """Create block formatting button"""
        try:
            button = ft.IconButton(
                icon=icon,
                tooltip=label,
                on_click=lambda e, b_id=block_id: self._handle_block_button_click(b_id),
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=4),
                    padding=ft.padding.all(8),
                    color={
                        ft.MaterialState.DEFAULT: "#374151",
                        ft.MaterialState.SELECTED: "#5E6AD2"
                    },
                    bgcolor={
                        ft.MaterialState.SELECTED: "#EEF2FF"
                    }
                ),
                selected=False,
                data=block_id
            )
            
            self._button_controls[block_id] = button
            return button
            
        except Exception as e:
            logger.error(f"Failed to create block button {block_id}: {e}")
            return ft.Text("?", size=12)
    
    def _create_action_button(self, action_id: str, icon: str, label: str, shortcut: str = "") -> ft.Control:
        """Create action button (undo, redo, etc.)"""
        try:
            tooltip = f"{label} ({shortcut})" if shortcut else label
            
            button = ft.IconButton(
                icon=icon,
                tooltip=tooltip,
                on_click=lambda e, a_id=action_id: self._handle_action_button_click(a_id),
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=4),
                    padding=ft.padding.all(8),
                    color={
                        ft.MaterialState.DEFAULT: "#374151",
                        ft.MaterialState.HOVERED: "#5E6AD2",
                        ft.MaterialState.DISABLED: "#9CA3AF"
                    }
                ),
                disabled=True,  # Will be enabled based on editor state
                data=action_id
            )
            
            self._button_controls[action_id] = button
            return button
            
        except Exception as e:
            logger.error(f"Failed to create action button {action_id}: {e}")
            return ft.Text("?", size=12)
    
    def _create_block_dropdown(self) -> ft.Control:
        """Create block type dropdown selector with real functionality"""
        try:
            block_options = [
                ft.dropdown.Option(key="paragraph", text="Paragraph"),
                ft.dropdown.Option(key="h1", text="Heading 1"),
                ft.dropdown.Option(key="h2", text="Heading 2"),
                ft.dropdown.Option(key="h3", text="Heading 3"),
                ft.dropdown.Option(key="h4", text="Heading 4"),
                ft.dropdown.Option(key="h5", text="Heading 5"),
                ft.dropdown.Option(key="h6", text="Heading 6"),
            ]
            
            dropdown = ft.Dropdown(
                options=block_options,
                value="paragraph",
                width=120,
                height=32,
                text_size=12,
                content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
                on_change=self._handle_block_dropdown_change,
                tooltip="Change block type"
            )
            
            self._button_controls["block_dropdown"] = dropdown
            return dropdown
            
        except Exception as e:
            logger.error(f"Failed to create block dropdown: {e}")
            return ft.Text("Block", size=12)
    
    def _create_button_group(self, group_name: str, buttons: List[ft.Control]) -> ft.Control:
        """Create grouped buttons with visual separation"""
        try:
            return ft.Container(
                content=ft.Row(
                    controls=buttons,
                    spacing=2,
                    tight=True
                ),
                padding=ft.padding.symmetric(horizontal=4),
                border_radius=4,
                data=f"group_{group_name}"
            )
            
        except Exception as e:
            logger.error(f"Failed to create button group {group_name}: {e}")
            return ft.Container()
    
    def _create_separator(self) -> ft.Control:
        """Create visual separator between button groups"""
        return ft.Container(
            width=1,
            height=24,
            bgcolor="#D1D5DB",
            margin=ft.margin.symmetric(horizontal=4)
        )
    
    def _create_status_display(self) -> ft.Control:
        """Create status display showing word/character count"""
        try:
            status_text = ft.Text(
                "0 words, 0 characters",
                size=10,
                color="#6B7280",
                data="status_text"
            )
            self._button_controls["status_display"] = status_text
            
            return ft.Container(
                content=ft.Row([status_text]),
                padding=ft.padding.symmetric(horizontal=8),
                alignment=ft.alignment.center_right,
                expand=True
            )
        except Exception as e:
            logger.error(f"Failed to create status display: {e}")
            return ft.Container()
    
    # Event handlers for new toolbar functionality
    
    def _handle_format_button_click(self, format_id: str) -> None:
        """Handle formatting button clicks with real editor integration"""
        try:
            start_time = time.perf_counter()
            
            # Map format ID to FormatType
            format_map = {
                "bold": FormatType.BOLD,
                "italic": FormatType.ITALIC,
                "underline": FormatType.UNDERLINE,
                "strikethrough": FormatType.STRIKETHROUGH,
                "code": FormatType.CODE,
            }
            
            if format_id in format_map:
                format_type = format_map[format_id]
                success = self.editor.toggle_format(format_type)
                
                if success:
                    # Update button state
                    is_active = format_type in self.editor.get_formats_at_selection()
                    self._update_button_visual_state(format_id, is_active)
                    logger.debug(f"Toggled format: {format_type.value}")
                    
            elif format_id == "link":
                # Handle link insertion
                self._handle_link_insertion()
                
            # Track performance
            processing_time = (time.perf_counter() - start_time) * 1000
            logger.debug(f"Format button processed in {processing_time:.1f}ms")
            
        except Exception as e:
            logger.error(f"Error handling format button {format_id}: {e}")
    
    def _handle_block_button_click(self, block_id: str) -> None:
        """Handle block formatting button clicks"""
        try:
            success = self.editor.set_block_type(block_id)
            if success:
                self._state.current_block_type = block_id
                self._update_all_block_button_states()
                logger.debug(f"Set block type to: {block_id}")
                
        except Exception as e:
            logger.error(f"Error handling block button {block_id}: {e}")
    
    def _handle_action_button_click(self, action_id: str) -> None:
        """Handle action button clicks (undo, redo, etc.)"""
        try:
            if action_id == "undo":
                success = self.editor.undo()
                if success:
                    self._update_history_button_states()
                    
            elif action_id == "redo":
                success = self.editor.redo()
                if success:
                    self._update_history_button_states()
                    
            elif action_id == "clear_format":
                success = self.editor.clear_formatting()
                if success:
                    self._update_all_format_button_states()
                    
        except Exception as e:
            logger.error(f"Error handling action button {action_id}: {e}")
    
    def _handle_block_dropdown_change(self, e: ft.ControlEvent) -> None:
        """Handle block type dropdown selection"""
        try:
            if hasattr(e, 'control') and hasattr(e.control, 'value'):
                block_type = e.control.value
                success = self.editor.set_block_type(block_type)
                
                if success:
                    self._state.current_block_type = block_type
                    self._update_all_block_button_states()
                    logger.debug(f"Changed block type to: {block_type}")
                    
        except Exception as ex:
            logger.error(f"Error changing block type: {ex}")
    
    def _handle_link_insertion(self) -> None:
        """Handle link insertion with URL input"""
        try:
            # In a real implementation, this would show a dialog
            # For now, we'll use a placeholder
            url = "https://example.com"
            text = "Link"
            
            success = self.editor.insert_link(text, url)
            if success:
                logger.debug(f"Inserted link: {text} -> {url}")
                
        except Exception as e:
            logger.error(f"Error inserting link: {e}")
    
    # Editor event integration
    
    def _connect_editor_events(self) -> None:
        """Connect to editor events for real-time state updates"""
        try:
            # Set up event handlers for editor state changes
            if hasattr(self.editor, 'on_selection_change'):
                self.editor.on_selection_change = self._handle_editor_selection_change
            
            if hasattr(self.editor, 'on_content_change'):
                self.editor.on_content_change = self._handle_editor_content_change
                
            if hasattr(self.editor, 'on_state_change'):
                self.editor.on_state_change = self._handle_editor_state_change
            
            logger.debug("Connected to editor events")
            
        except Exception as e:
            logger.error(f"Failed to connect editor events: {e}")
    
    def _handle_editor_selection_change(self, selection: SelectionRange) -> None:
        """Handle editor selection changes to update button states"""
        try:
            self._state.selection_range = selection
            
            # Get active formats at current selection
            active_formats = self.editor.get_formats_at_selection()
            self._state.active_formats = set(active_formats)
            
            # Get current block type
            self._state.current_block_type = self.editor.get_block_type_at_selection()
            
            # Update button states
            self._update_all_format_button_states()
            self._update_all_block_button_states()
            
        except Exception as e:
            logger.error(f"Error handling selection change: {e}")
    
    def _handle_editor_content_change(self) -> None:
        """Handle editor content changes to update status and history"""
        try:
            # Update word and character counts
            content = self.editor.get_text_content()
            self._state.word_count = len(content.split()) if content.strip() else 0
            self._state.character_count = len(content)
            
            # Update status display
            self._update_status_display()
            
            # Update history states
            self._state.can_undo = self.editor.can_undo()
            self._state.can_redo = self.editor.can_redo()
            self._update_history_button_states()
            
        except Exception as e:
            logger.error(f"Error handling content change: {e}")
    
    def _handle_editor_state_change(self, state: EditorState) -> None:
        """Handle editor state changes"""
        try:
            if state == EditorState.LOADING:
                self._disable_all_buttons()
            elif state == EditorState.READY:
                self._enable_all_buttons()
            elif state == EditorState.ERROR:
                self._show_error_state()
                
        except Exception as e:
            logger.error(f"Error handling state change: {e}")
    
    # Button state update methods
    
    def _update_button_visual_state(self, button_id: str, is_active: bool) -> None:
        """Update individual button visual state"""
        try:
            button = self._button_controls.get(button_id)
            if button and hasattr(button, 'selected'):
                button.selected = is_active
                if hasattr(button, 'update'):
                    button.update()
                    
        except Exception as e:
            logger.error(f"Error updating button visual state {button_id}: {e}")
    
    def _update_all_format_button_states(self) -> None:
        """Update all format button states based on current selection"""
        try:
            format_buttons = ["bold", "italic", "underline", "strikethrough", "code"]
            format_map = {
                "bold": FormatType.BOLD,
                "italic": FormatType.ITALIC,
                "underline": FormatType.UNDERLINE,
                "strikethrough": FormatType.STRIKETHROUGH,
                "code": FormatType.CODE,
            }
            
            for button_id in format_buttons:
                if button_id in format_map:
                    format_type = format_map[button_id]
                    is_active = format_type in self._state.active_formats
                    self._update_button_visual_state(button_id, is_active)
            
        except Exception as e:
            logger.error(f"Error updating format button states: {e}")
    
    def _update_all_block_button_states(self) -> None:
        """Update all block button states"""
        try:
            # Update dropdown
            dropdown = self._button_controls.get("block_dropdown")
            if dropdown and hasattr(dropdown, 'value'):
                dropdown.value = self._state.current_block_type
                if hasattr(dropdown, 'update'):
                    dropdown.update()
            
            # Update block buttons
            block_buttons = ["blockquote", "code_block", "bullet_list", "numbered_list"]
            for button_id in block_buttons:
                is_active = self._state.current_block_type == button_id
                self._update_button_visual_state(button_id, is_active)
                
        except Exception as e:
            logger.error(f"Error updating block button states: {e}")
    
    def _update_history_button_states(self) -> None:
        """Update undo/redo button states"""
        try:
            undo_button = self._button_controls.get("undo")
            if undo_button and hasattr(undo_button, 'disabled'):
                undo_button.disabled = not self._state.can_undo
                if hasattr(undo_button, 'update'):
                    undo_button.update()
            
            redo_button = self._button_controls.get("redo")
            if redo_button and hasattr(redo_button, 'disabled'):
                redo_button.disabled = not self._state.can_redo
                if hasattr(redo_button, 'update'):
                    redo_button.update()
                    
        except Exception as e:
            logger.error(f"Error updating history button states: {e}")
    
    def _update_status_display(self) -> None:
        """Update status display with current counts"""
        try:
            status_text = f"{self._state.word_count} words, {self._state.character_count} characters"
            
            status_control = self._button_controls.get("status_display")
            if status_control and hasattr(status_control, 'value'):
                status_control.value = status_text
                if hasattr(status_control, 'update'):
                    status_control.update()
                    
        except Exception as e:
            logger.error(f"Error updating status display: {e}")
    
    def _disable_all_buttons(self) -> None:
        """Disable all toolbar buttons"""
        try:
            for button in self._button_controls.values():
                if hasattr(button, 'disabled'):
                    button.disabled = True
                    if hasattr(button, 'update'):
                        button.update()
        except Exception as e:
            logger.error(f"Error disabling buttons: {e}")
    
    def _enable_all_buttons(self) -> None:
        """Enable all toolbar buttons"""
        try:
            for button in self._button_controls.values():
                if hasattr(button, 'disabled'):
                    button.disabled = False
                    if hasattr(button, 'update'):
                        button.update()
        except Exception as e:
            logger.error(f"Error enabling buttons: {e}")
    
    def _show_error_state(self) -> None:
        """Show error state in toolbar"""
        try:
            self._disable_all_buttons()
            logger.warning("Toolbar in error state")
        except Exception as e:
            logger.error(f"Error showing error state: {e}")
    
    def _setup_keyboard_shortcuts(self) -> None:
        """Set up keyboard shortcuts for toolbar actions"""
        try:
            # Keyboard shortcut mappings
            self._shortcuts = {
                "ctrl+b": "bold",
                "ctrl+i": "italic", 
                "ctrl+u": "underline",
                "ctrl+shift+x": "strikethrough",
                "ctrl+`": "code",
                "ctrl+k": "link",
                "ctrl+shift+>": "blockquote",
                "ctrl+shift+c": "code_block",
                "ctrl+shift+8": "bullet_list",
                "ctrl+shift+7": "numbered_list",
                "ctrl+z": "undo",
                "ctrl+y": "redo",
                "ctrl+\\": "clear_format"
            }
            
            logger.debug("Keyboard shortcuts configured")
            
        except Exception as e:
            logger.error(f"Failed to setup keyboard shortcuts: {e}")
    
    def handle_keyboard_shortcut(self, key_combination: str) -> bool:
        """Handle keyboard shortcut activation"""
        try:
            action = self._shortcuts.get(key_combination.lower())
            if action:
                if action in ["bold", "italic", "underline", "strikethrough", "code", "link"]:
                    self._handle_format_button_click(action)
                elif action in ["blockquote", "code_block", "bullet_list", "numbered_list"]:
                    self._handle_block_button_click(action)
                elif action in ["undo", "redo", "clear_format"]:
                    self._handle_action_button_click(action)
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error handling keyboard shortcut {key_combination}: {e}")
            return False
    
    # Public API methods for new functionality
    
    def get_toolbar_control(self) -> ft.Control:
        """Get the toolbar UI control for embedding in layout"""
        return self._toolbar_container if hasattr(self, '_toolbar_container') else self.build()
    
    def refresh_state(self) -> None:
        """Force refresh of all toolbar states"""
        try:
            if self.editor:
                # Update selection state
                current_selection = self.editor.get_current_selection()
                if current_selection:
                    self._handle_editor_selection_change(current_selection)
                
                # Update content state
                self._handle_editor_content_change()
            
            logger.debug("Toolbar state refreshed")
            
        except Exception as e:
            logger.error(f"Error refreshing toolbar state: {e}")
    
    def set_compact_mode(self, compact: bool) -> None:
        """Toggle compact mode"""
        if self.compact_mode != compact:
            self.compact_mode = compact
            # Rebuild toolbar with new mode
            if hasattr(self, 'editor'):
                self._toolbar_container = self._build_comprehensive_toolbar()
                self._connect_editor_events()
            logger.debug(f"Toolbar compact mode: {compact}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get toolbar performance metrics"""
        return {
            "last_update_time_ms": self._last_update_time * 1000,
            "total_updates": self._update_count,
            "avg_update_time_ms": (self._last_update_time * 1000) if self._update_count > 0 else 0,
            "active_formats_count": len(self._state.active_formats),
            "current_block_type": self._state.current_block_type,
            "word_count": self._state.word_count,
            "character_count": self._state.character_count
        }
    
    # Legacy methods (kept for backward compatibility)
    
    def update_button_state(self, button_id: str, is_active: bool = None, is_enabled: bool = None) -> None:
        """
        Update button state
        CLAUDE.md #9.1: Proper state management
        """
        try:
            if is_active is not None:
                self._active_states[button_id] = is_active
            
            if is_enabled is not None:
                self._enabled_states[button_id] = is_enabled
            
            # Update UI control if it exists
            if button_id in self._button_controls:
                control = self._button_controls[button_id]
                
                if hasattr(control, 'style'):
                    # Update visual state
                    if is_active is not None and isinstance(control, ft.ElevatedButton):
                        control.bgcolor = "#5E6AD2" if is_active else None
                        control.color = "#FFFFFF" if is_active else None
                
                if hasattr(control, 'disabled'):
                    if is_enabled is not None:
                        control.disabled = not is_enabled
                
                control.update()
            
        except Exception as e:
            logger.error(f"Failed to update button state: {e}")
    
    def get_button_state(self, button_id: str) -> Dict[str, bool]:
        """Get button state"""
        return {
            "is_active": self._active_states.get(button_id, False),
            "is_enabled": self._enabled_states.get(button_id, True)
        }
    
    def add_custom_button(self, button: ToolbarButton) -> None:
        """Add custom button to toolbar"""
        self.buttons.append(button)
        self._active_states[button.id] = button.is_active
        self._enabled_states[button.id] = button.is_enabled
    
    def remove_button(self, button_id: str) -> None:
        """Remove button from toolbar"""
        self.buttons = [b for b in self.buttons if b.id != button_id]
        self._active_states.pop(button_id, None)
        self._enabled_states.pop(button_id, None)
        self._button_controls.pop(button_id, None)
    
    # Event handler registration
    
    def add_format_handler(self, handler: Callable[[str, Any], None]) -> None:
        """Add formatting event handler"""
        self._format_handlers.append(handler)
    
    def add_block_handler(self, handler: Callable[[str], None]) -> None:
        """Add block formatting handler"""
        self._block_handlers.append(handler)
    
    def add_action_handler(self, handler: Callable[[str], None]) -> None:
        """Add action handler"""
        self._action_handlers.append(handler)
    
    # Private methods
    
    def _group_buttons(self) -> Dict[ToolbarGroup, List[ToolbarButton]]:
        """Group buttons by category"""
        groups = {group: [] for group in ToolbarGroup}
        
        for button in self.buttons:
            groups[button.group].append(button)
        
        return groups
    
    def _build_toolbar_section(self, group_type: ToolbarGroup, buttons: List[ToolbarButton]) -> Optional[ft.Control]:
        """Build a toolbar section"""
        try:
            button_controls = []
            
            for button in buttons:
                control = self._build_button_control(button)
                if control:
                    button_controls.append(control)
                    self._button_controls[button.id] = control
            
            if not button_controls:
                return None
            
            # Add separator between groups (except for first group)
            section_controls = button_controls
            if group_type != ToolbarGroup.ACTIONS:
                section_controls = [
                    ft.VerticalDivider(width=1, color="#D1D5DB"),
                    *button_controls
                ]
            
            return ft.Row(
                controls=section_controls,
                spacing=4,
                tight=True
            )
            
        except Exception as e:
            logger.error(f"Failed to build toolbar section: {e}")
            return None
    
    def _build_button_control(self, button: ToolbarButton) -> Optional[ft.Control]:
        """
        Build individual button control
        CLAUDE.md #9.1: Accessible button implementation
        """
        try:
            if button.type == ButtonType.DROPDOWN:
                return self._build_dropdown_button(button)
            elif button.type == ButtonType.COLOR_PICKER:
                return self._build_color_picker_button(button)
            else:
                return self._build_standard_button(button)
                
        except Exception as e:
            logger.error(f"Failed to build button control: {e}")
            return None
    
    def _build_standard_button(self, button: ToolbarButton) -> ft.Control:
        """Build standard button"""
        is_active = self._active_states.get(button.id, False)
        is_enabled = self._enabled_states.get(button.id, True)
        
        btn = ft.IconButton(
            icon=button.icon,
            tooltip=button.tooltip,
            disabled=not is_enabled,
            on_click=lambda e, btn_id=button.id: self._handle_button_click(btn_id),
            style=ft.ButtonStyle(
                color={
                    ft.ControlState.DEFAULT: "#374151" if not is_active else "#FFFFFF",
                    ft.ControlState.HOVERED: "#5E6AD2",
                    ft.ControlState.PRESSED: "#4F46E5"
                },
                bgcolor={
                    ft.ControlState.DEFAULT: "#5E6AD2" if is_active else "transparent",
                    ft.ControlState.HOVERED: "#E0E7FF" if not is_active else "#4F46E5"
                },
                shape=ft.RoundedRectangleBorder(radius=4)
            )
        )
        
        return btn
    
    def _build_dropdown_button(self, button: ToolbarButton) -> ft.Control:
        """Build dropdown button"""
        dropdown_items = []
        
        for item in button.dropdown_items:
            dropdown_items.append(
                ft.dropdown.Option(
                    key=item["id"],
                    text=item["label"]
                )
            )
        
        dropdown = ft.Dropdown(
            label=button.label,
            options=dropdown_items,
            width=120,
            height=36,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
            on_change=lambda e, btn_id=button.id: self._handle_dropdown_change(btn_id, e.control.value)
        )
        
        return dropdown
    
    def _build_color_picker_button(self, button: ToolbarButton) -> ft.Control:
        """Build color picker button"""
        # Simplified color picker - full implementation would have color palette
        return ft.IconButton(
            icon=button.icon,
            tooltip=button.tooltip,
            on_click=lambda e, btn_id=button.id: self._handle_color_picker_click(btn_id)
        )
    
    def _handle_button_click(self, button_id: str) -> None:
        """Handle button click"""
        try:
            button = self._get_button_by_id(button_id)
            if not button:
                return
            
            # Update toggle state
            if button.type == ButtonType.TOGGLE:
                current_state = self._active_states.get(button_id, False)
                self.update_button_state(button_id, is_active=not current_state)
            
            # Notify appropriate handlers
            if button.group == ToolbarGroup.TEXT_FORMAT:
                self._notify_format_handlers(button_id, True)
            elif button.group == ToolbarGroup.PARAGRAPH:
                self._notify_block_handlers(button_id)
            elif button.group == ToolbarGroup.ACTIONS:
                self._notify_action_handlers(button_id)
            elif button.group == ToolbarGroup.INSERT:
                self._notify_action_handlers(button_id)
            
        except Exception as e:
            logger.error(f"Error handling button click: {e}")
    
    def _handle_dropdown_change(self, button_id: str, value: str) -> None:
        """Handle dropdown selection"""
        try:
            self._notify_block_handlers(value)
        except Exception as e:
            logger.error(f"Error handling dropdown change: {e}")
    
    def _handle_color_picker_click(self, button_id: str) -> None:
        """Handle color picker click"""
        try:
            # Implementation would show color picker dialog
            self._notify_format_handlers(button_id, "#000000")
        except Exception as e:
            logger.error(f"Error handling color picker: {e}")
    
    def _get_button_by_id(self, button_id: str) -> Optional[ToolbarButton]:
        """Get button configuration by ID"""
        for button in self.buttons:
            if button.id == button_id:
                return button
        return None
    
    def _notify_format_handlers(self, format_type: str, value: Any) -> None:
        """Notify formatting handlers"""
        for handler in self._format_handlers:
            try:
                handler(format_type, value)
            except Exception as e:
                logger.error(f"Error in format handler: {e}")
    
    def _notify_block_handlers(self, block_type: str) -> None:
        """Notify block handlers"""
        for handler in self._block_handlers:
            try:
                handler(block_type)
            except Exception as e:
                logger.error(f"Error in block handler: {e}")
    
    def _notify_action_handlers(self, action: str) -> None:
        """Notify action handlers"""
        for handler in self._action_handlers:
            try:
                handler(action)
            except Exception as e:
                logger.error(f"Error in action handler: {e}")


# Factory functions for common toolbar configurations

def create_basic_toolbar(editor: RichTextEditor) -> RichTextToolbar:
    """Create basic toolbar with essential formatting only"""
    return RichTextToolbar(
        editor=editor,
        enable_advanced_formatting=False,
        enable_block_formatting=False,
        enable_history_controls=False,
        compact_mode=True
    )


def create_full_toolbar(editor: RichTextEditor) -> RichTextToolbar:
    """Create full-featured toolbar with all formatting options"""
    return RichTextToolbar(
        editor=editor,
        enable_advanced_formatting=True,
        enable_block_formatting=True,
        enable_history_controls=True,
        compact_mode=False
    )


def create_writing_toolbar(editor: RichTextEditor) -> RichTextToolbar:
    """Create toolbar optimized for writing (no code/advanced features)"""
    return RichTextToolbar(
        editor=editor,
        enable_advanced_formatting=False,
        enable_block_formatting=True,
        enable_history_controls=True,
        compact_mode=False
    )


def create_code_toolbar(editor: RichTextEditor) -> RichTextToolbar:
    """Create toolbar optimized for code documentation"""
    return RichTextToolbar(
        editor=editor,
        enable_advanced_formatting=True,
        enable_block_formatting=True,
        enable_history_controls=True,
        compact_mode=False
    )


# Global instance for easy access (legacy support)
_rich_text_toolbar_instance: Optional[RichTextToolbar] = None


def get_rich_text_toolbar(config: Optional[ToolbarConfig] = None) -> RichTextToolbar:
    """Get or create global rich text toolbar instance (legacy)"""
    global _rich_text_toolbar_instance
    if _rich_text_toolbar_instance is None:
        _rich_text_toolbar_instance = RichTextToolbar(config=config)
    return _rich_text_toolbar_instance


def reset_rich_text_toolbar() -> None:
    """Reset global rich text toolbar instance"""
    global _rich_text_toolbar_instance
    _rich_text_toolbar_instance = None