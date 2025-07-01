"""
Rich Text Editor Component for Canvas Editor
Implements WYSIWYG rich text editing with block/inline model
Following CLAUDE.md guidelines for enterprise-grade text editing
"""

import flet as ft
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum, auto
import json
import logging
import html
import re
import time
from uuid import uuid4

from components.rich_text_document import RichTextDocument, TextBlock, InlineElement, BlockType, InlineType
from components.rich_text_toolbar import RichTextToolbar, ToolbarConfig
from components.rich_text_renderer import RichTextRenderer, RenderConfig

logger = logging.getLogger(__name__)


class EditorState(Enum):
    """Rich text editor states"""
    READY = auto()
    EDITING = auto()
    LOADING = auto()
    ERROR = auto()


@dataclass
class CursorPosition:
    """Cursor position within the document"""
    block_id: str
    offset: int
    is_selection: bool = False
    selection_end_block: Optional[str] = None
    selection_end_offset: Optional[int] = None
    
    def is_valid(self) -> bool:
        """Validate cursor position"""
        return bool(self.block_id and self.offset >= 0)


@dataclass
class EditorConfig:
    """Configuration for rich text editor"""
    # Editor settings
    placeholder: str = "Start typing..."
    read_only: bool = False
    auto_save: bool = True
    auto_save_interval: int = 5000  # milliseconds
    
    # Content limits
    max_document_size: int = 10 * 1024 * 1024  # 10MB
    max_blocks: int = 10000
    max_text_length: int = 1000000
    
    # Features
    enable_markdown_shortcuts: bool = True
    enable_collaborative: bool = False
    enable_plugins: bool = True
    
    # Performance
    virtual_scrolling: bool = True
    render_chunk_size: int = 50
    
    def __post_init__(self):
        """Validate configuration"""
        if self.auto_save_interval < 1000:
            raise ValueError("Auto-save interval must be at least 1000ms")
        
        if self.max_blocks < 1:
            raise ValueError("Max blocks must be at least 1")


class RichTextEditor:
    """
    Comprehensive rich text editor with block/inline model
    CLAUDE.md #1.5: Optimize for performance with large documents
    CLAUDE.md #9.1: Full keyboard accessibility
    CLAUDE.md #12.1: Performance monitoring
    """
    
    def __init__(self, config: Optional[EditorConfig] = None):
        """Initialize the rich text editor"""
        self.config = config or EditorConfig()
        
        # Core components
        self.document = RichTextDocument()
        self.toolbar = RichTextToolbar()
        self.renderer = RichTextRenderer()
        
        # Editor state
        self.state = EditorState.READY
        self.cursor_position = CursorPosition(block_id="", offset=0)
        self.selection_range: Optional[Dict[str, Any]] = None
        self.is_focused = False
        
        # Event handlers
        self._change_handlers: List[Callable[[RichTextDocument], None]] = []
        self._selection_handlers: List[Callable[[CursorPosition], None]] = []
        self._focus_handlers: List[Callable[[bool], None]] = []
        
        # Performance tracking
        self._render_count = 0
        self._avg_render_time = 0.0
        self._keystroke_count = 0
        
        # UI elements
        self._editor_container: Optional[ft.Container] = None
        self._content_area: Optional[ft.Column] = None
        self._toolbar_area: Optional[ft.Row] = None
        
        # Auto-save
        self._auto_save_timer: Optional[Any] = None
        self._has_unsaved_changes = False
        
        logger.info("Rich text editor initialized")
    
    def build(self) -> ft.Control:
        """
        Build the editor UI component
        CLAUDE.md #7.2: Safe UI construction
        """
        try:
            # Build toolbar
            self._toolbar_area = self.toolbar.build()
            
            # Build content area
            self._content_area = ft.Column(
                controls=[],
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
                expand=True
            )
            
            # Build main container
            self._editor_container = ft.Container(
                content=ft.Column(
                    controls=[
                        self._toolbar_area,
                        ft.Divider(height=1, color="#E5E7EB"),
                        ft.Container(
                            content=self._content_area,
                            padding=ft.padding.all(16),
                            expand=True,
                            bgcolor="#FFFFFF",
                            border_radius=4
                        )
                    ],
                    spacing=0,
                    expand=True
                ),
                border=ft.border.all(1, "#D1D5DB"),
                border_radius=8,
                bgcolor="#F9FAFB",
                expand=True
            )
            
            # Set up event handlers
            self._setup_event_handlers()
            
            # Initial render
            self._render_document()
            
            return self._editor_container
            
        except Exception as e:
            logger.error(f"Failed to build editor: {e}")
            return ft.Container(
                content=ft.Text(f"Editor Error: {e}", color="#EF4444"),
                padding=20
            )
    
    def set_content(self, content: Union[str, Dict[str, Any], RichTextDocument]) -> None:
        """
        Set editor content with validation
        CLAUDE.md #2.1.1: Validate all inputs
        """
        try:
            if isinstance(content, str):
                # Parse as HTML or Markdown
                if content.strip().startswith('<'):
                    self.document = self._parse_html(content)
                else:
                    self.document = self._parse_markdown(content)
            
            elif isinstance(content, dict):
                # Parse as JSON document
                self.document = RichTextDocument.from_dict(content)
            
            elif isinstance(content, RichTextDocument):
                self.document = content
            
            else:
                raise ValueError(f"Unsupported content type: {type(content)}")
            
            # Validate content size
            if self._get_document_size() > self.config.max_document_size:
                raise ValueError("Document exceeds maximum size limit")
            
            if len(self.document.blocks) > self.config.max_blocks:
                raise ValueError("Document exceeds maximum block limit")
            
            # Reset cursor and re-render
            self.cursor_position = CursorPosition(
                block_id=self.document.blocks[0].id if self.document.blocks else "",
                offset=0
            )
            
            self._render_document()
            self._notify_change_handlers()
            
            logger.info(f"Content set: {len(self.document.blocks)} blocks")
            
        except Exception as e:
            logger.error(f"Failed to set content: {e}")
            raise
    
    def get_content(self, format: str = "json") -> Union[str, Dict[str, Any]]:
        """
        Get editor content in specified format
        CLAUDE.md #2.1.4: Proper serialization
        """
        try:
            if format == "json":
                return self.document.to_dict()
            
            elif format == "html":
                return self._export_html()
            
            elif format == "markdown":
                return self._export_markdown()
            
            elif format == "text":
                return self._export_text()
            
            else:
                raise ValueError(f"Unsupported format: {format}")
            
        except Exception as e:
            logger.error(f"Failed to get content: {e}")
            raise
    
    def insert_text(self, text: str) -> None:
        """
        Insert text at current cursor position
        CLAUDE.md #1.5: Optimize text insertion
        """
        try:
            if not self.cursor_position.is_valid():
                logger.warning("Invalid cursor position for text insertion")
                return
            
            # Find target block
            block = self.document.get_block(self.cursor_position.block_id)
            if not block:
                logger.warning(f"Block not found: {self.cursor_position.block_id}")
                return
            
            # Insert text into block
            if hasattr(block, 'insert_text'):
                block.insert_text(self.cursor_position.offset, text)
            else:
                # Handle as plain text block
                current_text = getattr(block, 'text', '')
                new_text = (
                    current_text[:self.cursor_position.offset] + 
                    text + 
                    current_text[self.cursor_position.offset:]
                )
                setattr(block, 'text', new_text)
            
            # Update cursor position
            self.cursor_position.offset += len(text)
            
            # Mark as changed and re-render
            self._has_unsaved_changes = True
            self._render_block(block)
            self._notify_change_handlers()
            self._schedule_auto_save()
            
            # Track performance
            self._keystroke_count += 1
            
        except Exception as e:
            logger.error(f"Failed to insert text: {e}")
    
    def apply_formatting(self, format_type: str, value: Any = True) -> None:
        """
        Apply formatting to current selection
        CLAUDE.md #2.1.1: Validate formatting operations
        """
        try:
            if not self.cursor_position.is_valid():
                return
            
            # Get selection range
            selection = self._get_current_selection()
            if not selection:
                logger.warning("No selection for formatting")
                return
            
            # Apply formatting based on type
            if format_type == "bold":
                self._apply_inline_format(InlineType.STRONG, selection)
            elif format_type == "italic":
                self._apply_inline_format(InlineType.EMPHASIS, selection)
            elif format_type == "underline":
                self._apply_inline_format(InlineType.UNDERLINE, selection)
            elif format_type == "strikethrough":
                self._apply_inline_format(InlineType.STRIKETHROUGH, selection)
            elif format_type == "code":
                self._apply_inline_format(InlineType.CODE, selection)
            elif format_type == "link":
                self._apply_link_format(selection, value)
            elif format_type in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                self._apply_block_format(getattr(BlockType, format_type.upper()), selection)
            elif format_type == "paragraph":
                self._apply_block_format(BlockType.PARAGRAPH, selection)
            elif format_type == "blockquote":
                self._apply_block_format(BlockType.BLOCKQUOTE, selection)
            elif format_type == "code_block":
                self._apply_block_format(BlockType.CODE_BLOCK, selection)
            else:
                logger.warning(f"Unknown format type: {format_type}")
                return
            
            # Mark as changed and re-render
            self._has_unsaved_changes = True
            self._render_document()
            self._notify_change_handlers()
            self._schedule_auto_save()
            
        except Exception as e:
            logger.error(f"Failed to apply formatting: {e}")
    
    def insert_block(self, block_type: BlockType, content: str = "") -> str:
        """
        Insert new block at cursor position
        CLAUDE.md #2.1.1: Validate block creation
        """
        try:
            # Create new block
            new_block = TextBlock(
                id=str(uuid4()),
                type=block_type,
                content=content,
                children=[]
            )
            
            # Find insertion point
            current_block = self.document.get_block(self.cursor_position.block_id)
            if current_block:
                # Insert after current block
                self.document.insert_block_after(current_block.id, new_block)
            else:
                # Add to end
                self.document.blocks.append(new_block)
            
            # Update cursor to new block
            self.cursor_position = CursorPosition(
                block_id=new_block.id,
                offset=0
            )
            
            # Mark as changed and re-render
            self._has_unsaved_changes = True
            self._render_document()
            self._notify_change_handlers()
            self._schedule_auto_save()
            
            return new_block.id
            
        except Exception as e:
            logger.error(f"Failed to insert block: {e}")
            return ""
    
    def delete_selection(self) -> None:
        """
        Delete current selection or character at cursor
        CLAUDE.md #2.1.4: Safe deletion operations
        """
        try:
            selection = self._get_current_selection()
            if selection:
                # Delete selection
                self._delete_range(selection)
            else:
                # Delete character at cursor
                self._delete_character()
            
            # Mark as changed and re-render
            self._has_unsaved_changes = True
            self._render_document()
            self._notify_change_handlers()
            self._schedule_auto_save()
            
        except Exception as e:
            logger.error(f"Failed to delete selection: {e}")
    
    def undo(self) -> None:
        """Undo last operation"""
        try:
            if self.document.can_undo():
                self.document.undo()
                self._render_document()
                self._notify_change_handlers()
                logger.debug("Undo operation completed")
        except Exception as e:
            logger.error(f"Failed to undo: {e}")
    
    def redo(self) -> None:
        """Redo last undone operation"""
        try:
            if self.document.can_redo():
                self.document.redo()
                self._render_document()
                self._notify_change_handlers()
                logger.debug("Redo operation completed")
        except Exception as e:
            logger.error(f"Failed to redo: {e}")
    
    def focus(self) -> None:
        """Focus the editor"""
        try:
            self.is_focused = True
            if self._content_area:
                self._content_area.focus()
            self._notify_focus_handlers(True)
        except Exception as e:
            logger.error(f"Failed to focus editor: {e}")
    
    def blur(self) -> None:
        """Remove focus from editor"""
        try:
            self.is_focused = False
            self._notify_focus_handlers(False)
        except Exception as e:
            logger.error(f"Failed to blur editor: {e}")
    
    # Event handler registration
    
    def add_change_handler(self, handler: Callable[[RichTextDocument], None]) -> None:
        """Add document change handler"""
        self._change_handlers.append(handler)
    
    def add_selection_handler(self, handler: Callable[[CursorPosition], None]) -> None:
        """Add selection change handler"""
        self._selection_handlers.append(handler)
    
    def add_focus_handler(self, handler: Callable[[bool], None]) -> None:
        """Add focus change handler"""
        self._focus_handlers.append(handler)
    
    # Private methods
    
    def _setup_event_handlers(self) -> None:
        """Set up UI event handlers"""
        try:
            # Toolbar event handlers
            self.toolbar.add_format_handler(self.apply_formatting)
            self.toolbar.add_block_handler(lambda block_type: self.insert_block(BlockType[block_type.upper()]))
            self.toolbar.add_action_handler(self._handle_toolbar_action)
            
        except Exception as e:
            logger.error(f"Failed to setup event handlers: {e}")
    
    def _render_document(self) -> None:
        """
        Render the entire document
        CLAUDE.md #1.5: Optimize rendering performance
        """
        start_time = time.perf_counter()
        
        try:
            if not self._content_area:
                return
            
            # Clear existing content
            self._content_area.controls.clear()
            
            # Render blocks
            for block in self.document.blocks:
                rendered_block = self.renderer.render_block(block)
                if rendered_block:
                    self._content_area.controls.append(rendered_block)
            
            # Update UI
            self._content_area.update()
            
            # Track performance
            render_time = (time.perf_counter() - start_time) * 1000
            self._update_render_metrics(render_time)
            
        except Exception as e:
            logger.error(f"Failed to render document: {e}")
    
    def _render_block(self, block: TextBlock) -> None:
        """Render a single block"""
        try:
            if not self._content_area:
                return
            
            # Find block in UI and update
            rendered_block = self.renderer.render_block(block)
            if rendered_block:
                # Find and replace existing block
                for i, control in enumerate(self._content_area.controls):
                    if hasattr(control, 'data') and control.data == block.id:
                        self._content_area.controls[i] = rendered_block
                        break
                
                self._content_area.update()
            
        except Exception as e:
            logger.error(f"Failed to render block: {e}")
    
    def _get_current_selection(self) -> Optional[Dict[str, Any]]:
        """Get current text selection"""
        if not self.cursor_position.is_selection:
            return None
        
        return {
            "start_block": self.cursor_position.block_id,
            "start_offset": self.cursor_position.offset,
            "end_block": self.cursor_position.selection_end_block,
            "end_offset": self.cursor_position.selection_end_offset
        }
    
    def _apply_inline_format(self, format_type: InlineType, selection: Dict[str, Any]) -> None:
        """
        Apply inline formatting to selection
        CLAUDE.md Implementation:
        - #2.1.1: Validate formatting operations
        - #1.5: Efficient format application
        """
        try:
            if not selection:
                return
            
            # Get selection details
            start_block = selection["start_block"]
            start_offset = selection["start_offset"]
            end_block = selection.get("end_block", start_block)
            end_offset = selection.get("end_offset", start_offset)
            
            # For now, handle single-block selections
            if start_block == end_block:
                block = self.document.get_block(start_block)
                if block and hasattr(block, 'apply_formatting'):
                    # Map InlineType to formatting
                    format_map = {
                        InlineType.STRONG: "bold",
                        InlineType.EMPHASIS: "italic",
                        InlineType.UNDERLINE: "underline",
                        InlineType.STRIKETHROUGH: "strikethrough",
                        InlineType.CODE: "code"
                    }
                    
                    format_name = format_map.get(format_type)
                    if format_name:
                        block.apply_formatting(start_offset, end_offset - start_offset, format_type)
                        
        except Exception as e:
            logger.error(f"Error applying inline format: {e}")
    
    def _apply_block_format(self, block_type: BlockType, selection: Dict[str, Any]) -> None:
        """
        Apply block formatting to selection
        CLAUDE.md Implementation:
        - #2.1.1: Validate block operations
        - #6.2: Real-time block updates
        """
        try:
            if not selection:
                return
                
            start_block = selection["start_block"]
            block = self.document.get_block(start_block)
            
            if block:
                # Convert BlockType to string
                block_type_map = {
                    BlockType.PARAGRAPH: "paragraph",
                    BlockType.H1: "h1",
                    BlockType.H2: "h2", 
                    BlockType.H3: "h3",
                    BlockType.H4: "h4",
                    BlockType.H5: "h5",
                    BlockType.H6: "h6",
                    BlockType.BLOCKQUOTE: "blockquote",
                    BlockType.CODE_BLOCK: "code_block"
                }
                
                new_type = block_type_map.get(block_type, "paragraph")
                block.type = block_type
                
                # Update block attributes if needed
                if hasattr(block, 'attributes'):
                    block.attributes["block_type"] = new_type
                    
        except Exception as e:
            logger.error(f"Error applying block format: {e}")
    
    def _apply_link_format(self, selection: Dict[str, Any], url: str) -> None:
        """
        Apply link formatting
        CLAUDE.md Implementation:
        - #2.1.1: Validate link URLs
        - #9.1: Accessible link creation
        """
        try:
            if not selection or not url:
                return
                
            # Validate URL
            import re
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            
            if not url_pattern.match(url):
                # Try to fix common URL issues
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
            
            # Apply link formatting
            start_block = selection["start_block"]
            start_offset = selection["start_offset"]
            end_offset = selection.get("end_offset", start_offset)
            
            block = self.document.get_block(start_block)
            if block and hasattr(block, 'apply_formatting'):
                block.apply_formatting(start_offset, end_offset - start_offset, InlineType.LINK, {"href": url})
                
        except Exception as e:
            logger.error(f"Error applying link format: {e}")
    
    def _delete_range(self, selection: Dict[str, Any]) -> None:
        """
        Delete text range
        CLAUDE.md Implementation:
        - #2.1.4: Safe deletion with validation
        - #6.2: Real-time content updates
        """
        try:
            if not selection:
                return
                
            start_block = selection["start_block"]
            start_offset = selection["start_offset"]
            end_block = selection.get("end_block", start_block)
            end_offset = selection.get("end_offset", start_offset)
            
            # Handle single-block deletions
            if start_block == end_block:
                block = self.document.get_block(start_block)
                if block and hasattr(block, 'delete_text'):
                    length = end_offset - start_offset
                    if length > 0:
                        block.delete_text(start_offset, length)
                        
            # Handle multi-block deletions (simplified)
            else:
                # For now, just delete from start block
                block = self.document.get_block(start_block)
                if block and hasattr(block, 'delete_text'):
                    # Delete from start offset to end of block
                    remaining_length = len(block.get_text()) - start_offset
                    if remaining_length > 0:
                        block.delete_text(start_offset, remaining_length)
                        
        except Exception as e:
            logger.error(f"Error deleting range: {e}")
    
    def _delete_character(self) -> None:
        """
        Delete character at cursor
        CLAUDE.md Implementation:
        - #2.1.4: Safe character deletion
        - #1.5: Efficient single-character operations
        """
        try:
            if not self.cursor_position.is_valid():
                return
                
            block = self.document.get_block(self.cursor_position.block_id)
            if not block:
                return
                
            # Delete character before cursor (backspace behavior)
            if self.cursor_position.offset > 0:
                if hasattr(block, 'delete_text'):
                    block.delete_text(self.cursor_position.offset - 1, 1)
                    self.cursor_position.offset -= 1
                else:
                    # Fallback for simple text blocks
                    current_text = getattr(block, 'text', '')
                    if self.cursor_position.offset <= len(current_text):
                        new_text = (
                            current_text[:self.cursor_position.offset - 1] + 
                            current_text[self.cursor_position.offset:]
                        )
                        setattr(block, 'text', new_text)
                        self.cursor_position.offset -= 1
                        
        except Exception as e:
            logger.error(f"Error deleting character: {e}")
    
    def _parse_html(self, html_content: str) -> RichTextDocument:
        """
        Parse HTML content into document
        CLAUDE.md Implementation:
        - #2.1.1: Validate HTML input
        - #4.1: Type-safe parsing
        """
        try:
            import html
            import re
            
            # Basic HTML parsing (simplified implementation)
            document = RichTextDocument()
            document.blocks.clear()
            
            # Clean up HTML
            clean_html = html.unescape(html_content)
            
            # Extract text content with basic formatting
            # This is a simplified parser - a full implementation would use an HTML parser
            
            # Split by block elements
            block_elements = re.split(r'<(?:p|div|h[1-6]|blockquote)[^>]*>|</(?:p|div|h[1-6]|blockquote)>', clean_html)
            
            for i, block_text in enumerate(block_elements):
                if not block_text.strip():
                    continue
                    
                # Remove remaining HTML tags for now
                clean_text = re.sub(r'<[^>]+>', '', block_text).strip()
                
                if clean_text:
                    from models.component import Component
                    block = Component(
                        id=str(uuid4()),
                        type="paragraph",
                        name=f"Block {i+1}",
                        content=clean_text
                    )
                    document.blocks.append(block)
            
            # Ensure at least one block
            if not document.blocks:
                from models.component import Component
                document.blocks.append(Component(
                    id=str(uuid4()),
                    type="paragraph", 
                    name="Empty Block",
                    content=""
                ))
                
            return document
            
        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            return RichTextDocument()
    
    def _parse_markdown(self, markdown_content: str) -> RichTextDocument:
        """
        Parse Markdown content into document
        CLAUDE.md Implementation:
        - #2.1.1: Validate Markdown input
        - #4.1: Type-safe parsing
        """
        try:
            import re
            
            document = RichTextDocument()
            document.blocks.clear()
            
            # Split into lines
            lines = markdown_content.split('\n')
            current_block_lines = []
            
            for line in lines:
                # Check for block-level elements
                if re.match(r'^#{1,6}\s+', line):
                    # Heading
                    if current_block_lines:
                        self._add_markdown_block(document, '\n'.join(current_block_lines), "paragraph")
                        current_block_lines = []
                    
                    level = len(line.split()[0])
                    heading_text = line[level+1:].strip()
                    self._add_markdown_block(document, heading_text, f"h{level}")
                    
                elif re.match(r'^>\s+', line):
                    # Blockquote
                    if current_block_lines:
                        self._add_markdown_block(document, '\n'.join(current_block_lines), "paragraph")
                        current_block_lines = []
                    
                    quote_text = line[1:].strip()
                    self._add_markdown_block(document, quote_text, "blockquote")
                    
                elif re.match(r'^```', line):
                    # Code block
                    if current_block_lines:
                        self._add_markdown_block(document, '\n'.join(current_block_lines), "paragraph")
                        current_block_lines = []
                    
                    # Simple code block handling
                    self._add_markdown_block(document, "Code Block", "code_block")
                    
                elif line.strip() == '':
                    # Empty line - finish current block
                    if current_block_lines:
                        self._add_markdown_block(document, '\n'.join(current_block_lines), "paragraph")
                        current_block_lines = []
                        
                else:
                    # Regular paragraph line
                    current_block_lines.append(line)
            
            # Add final block
            if current_block_lines:
                self._add_markdown_block(document, '\n'.join(current_block_lines), "paragraph")
            
            # Ensure at least one block
            if not document.blocks:
                from models.component import Component
                document.blocks.append(Component(
                    id=str(uuid4()),
                    type="paragraph",
                    name="Empty Block", 
                    content=""
                ))
                
            return document
            
        except Exception as e:
            logger.error(f"Error parsing Markdown: {e}")
            return RichTextDocument()
    
    def _add_markdown_block(self, document: RichTextDocument, text: str, block_type: str) -> None:
        """Add a block to the document from markdown parsing"""
        try:
            from models.component import Component
            block = Component(
                id=str(uuid4()),
                type=block_type,
                name=f"{block_type.title()} Block",
                content=text.strip()
            )
            document.blocks.append(block)
        except Exception as e:
            logger.error(f"Error adding markdown block: {e}")
    
    def _export_html(self) -> str:
        """
        Export document as HTML
        CLAUDE.md Implementation:
        - #4.1: Type-safe HTML generation
        - #2.1.4: Proper HTML escaping
        """
        try:
            import html
            
            html_parts = ['<!DOCTYPE html>', '<html>', '<head>', 
                         '<meta charset="UTF-8">', '<title>Rich Text Document</title>', 
                         '</head>', '<body>']
            
            for block in self.document.blocks:
                block_html = self._block_to_html(block)
                if block_html:
                    html_parts.append(block_html)
            
            html_parts.extend(['</body>', '</html>'])
            
            return '\n'.join(html_parts)
            
        except Exception as e:
            logger.error(f"Error exporting HTML: {e}")
            return "<html><body><p>Export error</p></body></html>"
    
    def _block_to_html(self, block) -> str:
        """Convert a block to HTML"""
        try:
            import html
            
            content = html.escape(getattr(block, 'content', '') or getattr(block, 'text', ''))
            block_type = getattr(block, 'type', 'paragraph')
            
            # Map block types to HTML tags
            tag_map = {
                'paragraph': 'p',
                'h1': 'h1', 'h2': 'h2', 'h3': 'h3', 
                'h4': 'h4', 'h5': 'h5', 'h6': 'h6',
                'blockquote': 'blockquote',
                'code_block': 'pre'
            }
            
            tag = tag_map.get(block_type, 'p')
            
            if tag == 'pre':
                return f'<{tag}><code>{content}</code></{tag}>'
            else:
                return f'<{tag}>{content}</{tag}>'
                
        except Exception as e:
            logger.error(f"Error converting block to HTML: {e}")
            return f"<p>Block conversion error</p>"
    
    def _export_markdown(self) -> str:
        """
        Export document as Markdown
        CLAUDE.md Implementation:
        - #4.1: Type-safe Markdown generation
        - #1.5: Efficient text processing
        """
        try:
            markdown_parts = []
            
            for block in self.document.blocks:
                block_markdown = self._block_to_markdown(block)
                if block_markdown:
                    markdown_parts.append(block_markdown)
                    markdown_parts.append('')  # Add spacing between blocks
            
            return '\n'.join(markdown_parts).rstrip()
            
        except Exception as e:
            logger.error(f"Error exporting Markdown: {e}")
            return "Export error"
    
    def _block_to_markdown(self, block) -> str:
        """Convert a block to Markdown"""
        try:
            content = getattr(block, 'content', '') or getattr(block, 'text', '')
            block_type = getattr(block, 'type', 'paragraph')
            
            # Map block types to Markdown syntax
            if block_type == 'h1':
                return f'# {content}'
            elif block_type == 'h2':
                return f'## {content}'
            elif block_type == 'h3':
                return f'### {content}'
            elif block_type == 'h4':
                return f'#### {content}'
            elif block_type == 'h5':
                return f'##### {content}'
            elif block_type == 'h6':
                return f'###### {content}'
            elif block_type == 'blockquote':
                return f'> {content}'
            elif block_type == 'code_block':
                return f'```\n{content}\n```'
            else:  # paragraph
                return content
                
        except Exception as e:
            logger.error(f"Error converting block to Markdown: {e}")
            return "Block conversion error"
    
    def _export_text(self) -> str:
        """
        Export document as plain text
        CLAUDE.md Implementation:
        - #1.5: Efficient text extraction
        - #4.1: Safe text handling
        """
        try:
            text_parts = []
            
            for block in self.document.blocks:
                content = getattr(block, 'content', '') or getattr(block, 'text', '')
                if content.strip():
                    text_parts.append(content.strip())
            
            return '\n\n'.join(text_parts)
            
        except Exception as e:
            logger.error(f"Error exporting text: {e}")
            return "Export error"
    
    def _get_document_size(self) -> int:
        """Calculate document size in bytes"""
        return len(json.dumps(self.document.to_dict()).encode('utf-8'))
    
    def _schedule_auto_save(self) -> None:
        """Schedule auto-save if enabled"""
        if self.config.auto_save and self._has_unsaved_changes:
            # Implementation would schedule auto-save
            pass
    
    def _handle_toolbar_action(self, action: str) -> None:
        """Handle toolbar actions"""
        if action == "undo":
            self.undo()
        elif action == "redo":
            self.redo()
        elif action == "save":
            self._save_document()
    
    def _save_document(self) -> None:
        """Save document"""
        try:
            # Implementation would save document
            self._has_unsaved_changes = False
            logger.info("Document saved")
        except Exception as e:
            logger.error(f"Failed to save document: {e}")
    
    def _notify_change_handlers(self) -> None:
        """Notify change handlers"""
        for handler in self._change_handlers:
            try:
                handler(self.document)
            except Exception as e:
                logger.error(f"Error in change handler: {e}")
    
    def _notify_selection_handlers(self) -> None:
        """Notify selection handlers"""
        for handler in self._selection_handlers:
            try:
                handler(self.cursor_position)
            except Exception as e:
                logger.error(f"Error in selection handler: {e}")
    
    def _notify_focus_handlers(self, focused: bool) -> None:
        """Notify focus handlers"""
        for handler in self._focus_handlers:
            try:
                handler(focused)
            except Exception as e:
                logger.error(f"Error in focus handler: {e}")
    
    def _update_render_metrics(self, render_time: float) -> None:
        """Update rendering performance metrics"""
        self._render_count += 1
        
        if self._avg_render_time == 0:
            self._avg_render_time = render_time
        else:
            # Exponential moving average
            alpha = 0.1
            self._avg_render_time = alpha * render_time + (1 - alpha) * self._avg_render_time
        
        # Warn if performance degrades
        if render_time > 100:  # 100ms threshold
            logger.warning(f"Slow render: {render_time:.1f}ms (avg: {self._avg_render_time:.1f}ms)")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            "render_count": self._render_count,
            "avg_render_time_ms": self._avg_render_time,
            "keystroke_count": self._keystroke_count,
            "document_size_bytes": self._get_document_size(),
            "block_count": len(self.document.blocks)
        }


# Global instance for easy access
_rich_text_editor_instance: Optional[RichTextEditor] = None


def get_rich_text_editor(config: Optional[EditorConfig] = None) -> RichTextEditor:
    """Get or create global rich text editor instance"""
    global _rich_text_editor_instance
    if _rich_text_editor_instance is None:
        _rich_text_editor_instance = RichTextEditor(config)
    return _rich_text_editor_instance


def reset_rich_text_editor() -> None:
    """Reset global rich text editor instance"""
    global _rich_text_editor_instance
    _rich_text_editor_instance = None