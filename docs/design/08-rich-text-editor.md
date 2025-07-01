# Rich Text Editor - Solution Design Document

## Overview
The Rich Text Editor provides a WYSIWYG interface for editing text content with formatting options, embedded media, and custom elements within Canvas components.

## Functional Requirements

### 1. Text Formatting
- Bold, italic, underline, strikethrough
- Font family and size selection
- Text color and highlight
- Alignment (left, center, right, justify)
- Lists (ordered, unordered, checklist)
- Indentation control

### 2. Block Elements
- Headings (H1-H6)
- Paragraphs
- Blockquotes
- Code blocks with syntax highlighting
- Horizontal rules
- Tables

### 3. Media Embedding
- Images (upload, URL, drag & drop)
- Videos (YouTube, Vimeo, local)
- Audio files
- Embedded content (tweets, etc.)

### 4. Advanced Features
- Links with preview
- Mentions (@user)
- Hashtags
- Emojis picker
- Math equations (LaTeX)
- Markdown support

### 5. Editing Features
- Undo/redo
- Find and replace
- Word count
- Spell check
- Auto-save
- Collaborative editing markers

## Technical Specifications

### Editor Architecture

```python
@dataclass
class EditorState:
    """Rich text editor state"""
    content: EditorContent
    selection: Selection
    format: FormatState
    history: HistoryStack
    mode: EditorMode
    
@dataclass
class EditorContent:
    """Document model for editor"""
    blocks: List[ContentBlock]
    inline_styles: Dict[str, List[InlineStyle]]
    entities: List[Entity]
    
@dataclass
class ContentBlock:
    """Block-level content element"""
    id: str
    type: BlockType
    text: str
    attributes: Dict[str, Any]
    children: List['ContentBlock']
    
@dataclass
class InlineStyle:
    """Inline text styling"""
    offset: int
    length: int
    style: StyleType
    value: Optional[Any]
    
@dataclass
class Entity:
    """Special entities (links, mentions, etc.)"""
    id: str
    type: EntityType
    offset: int
    length: int
    data: Dict[str, Any]

class BlockType(Enum):
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    LIST_ITEM = "list-item"
    QUOTE = "blockquote"
    CODE = "code-block"
    IMAGE = "image"
    VIDEO = "video"
    TABLE = "table"
    
class StyleType(Enum):
    BOLD = "bold"
    ITALIC = "italic"
    UNDERLINE = "underline"
    STRIKETHROUGH = "strikethrough"
    COLOR = "color"
    BACKGROUND = "background"
    FONT_SIZE = "font-size"
    FONT_FAMILY = "font-family"
```

### Editor Core

```python
class RichTextEditor:
    """Main rich text editor component"""
    
    def __init__(self, initial_content: Optional[str] = None,
                 config: Optional[EditorConfig] = None):
        self.config = config or EditorConfig()
        self.state = self._initialize_state(initial_content)
        self.plugins: List[EditorPlugin] = []
        self.toolbar: EditorToolbar = None
        self._setup_editor()
    
    def _setup_editor(self):
        """Initialize editor components"""
        
        # Create toolbar
        self.toolbar = EditorToolbar(
            config=self.config.toolbar,
            on_command=self.execute_command
        )
        
        # Load plugins
        for plugin_config in self.config.plugins:
            plugin = self._load_plugin(plugin_config)
            self.plugins.append(plugin)
        
        # Set up event handlers
        self._setup_event_handlers()
    
    def execute_command(self, command: EditorCommand, value: Optional[Any] = None):
        """Execute editor command"""
        
        # Check if plugin handles command
        for plugin in self.plugins:
            if plugin.handles_command(command):
                plugin.execute_command(command, value, self.state)
                return
        
        # Built-in command handling
        if command == EditorCommand.BOLD:
            self._toggle_inline_style(StyleType.BOLD)
        elif command == EditorCommand.ITALIC:
            self._toggle_inline_style(StyleType.ITALIC)
        elif command == EditorCommand.INSERT_LINK:
            self._insert_link(value)
        elif command == EditorCommand.INSERT_IMAGE:
            self._insert_image(value)
        # ... more commands
        
        # Update UI
        self._update_ui()
        
        # Record in history
        self._record_history()
    
    def _toggle_inline_style(self, style: StyleType):
        """Toggle inline style for selection"""
        
        selection = self.state.selection
        if selection.is_collapsed:
            # Set style for next input
            self.state.format.toggle_style(style)
        else:
            # Apply to selection
            self._apply_style_to_range(
                selection.start,
                selection.end,
                style
            )
    
    def _apply_style_to_range(self, start: int, end: int, style: StyleType):
        """Apply style to text range"""
        
        # Find affected blocks
        blocks = self._get_blocks_in_range(start, end)
        
        for block in blocks:
            # Calculate offsets within block
            block_start = max(0, start - block.offset)
            block_end = min(len(block.text), end - block.offset)
            
            # Add or update inline style
            self._add_inline_style(
                block.id,
                InlineStyle(
                    offset=block_start,
                    length=block_end - block_start,
                    style=style,
                    value=None
                )
            )
```

### Toolbar System

```python
class EditorToolbar:
    """Customizable editor toolbar"""
    
    def __init__(self, config: ToolbarConfig, on_command: Callable):
        self.config = config
        self.on_command = on_command
        self.groups: List[ToolbarGroup] = []
        self._build_toolbar()
    
    def _build_toolbar(self):
        """Build toolbar from config"""
        
        for group_config in self.config.groups:
            group = ToolbarGroup(name=group_config.name)
            
            for item_config in group_config.items:
                if item_config.type == "button":
                    item = ToolbarButton(
                        command=item_config.command,
                        icon=item_config.icon,
                        tooltip=item_config.tooltip,
                        on_click=lambda cmd=item_config.command: self.on_command(cmd)
                    )
                elif item_config.type == "dropdown":
                    item = ToolbarDropdown(
                        command=item_config.command,
                        options=item_config.options,
                        on_change=lambda val, cmd=item_config.command: self.on_command(cmd, val)
                    )
                elif item_config.type == "color_picker":
                    item = ToolbarColorPicker(
                        command=item_config.command,
                        on_change=lambda color, cmd=item_config.command: self.on_command(cmd, color)
                    )
                
                group.add_item(item)
            
            self.groups.append(group)
    
    def update_state(self, format_state: FormatState):
        """Update toolbar to reflect current format"""
        
        for group in self.groups:
            for item in group.items:
                if isinstance(item, ToolbarButton):
                    # Update toggle state
                    item.set_active(format_state.has_style(item.command))
                elif isinstance(item, ToolbarDropdown):
                    # Update selected value
                    item.set_value(format_state.get_style_value(item.command))
```

### Content Rendering

```python
class EditorRenderer:
    """Renders editor content to UI"""
    
    def render(self, content: EditorContent) -> ft.Control:
        """Render content to Flet controls"""
        
        container = ft.Column(spacing=0)
        
        for block in content.blocks:
            block_ui = self._render_block(block, content)
            container.controls.append(block_ui)
        
        return ft.Container(
            content=container,
            on_click=self._handle_click,
            on_key=self._handle_key
        )
    
    def _render_block(self, block: ContentBlock, content: EditorContent) -> ft.Control:
        """Render a single block"""
        
        if block.type == BlockType.PARAGRAPH:
            return self._render_paragraph(block, content)
        elif block.type == BlockType.HEADING:
            return self._render_heading(block, content)
        elif block.type == BlockType.LIST_ITEM:
            return self._render_list_item(block, content)
        elif block.type == BlockType.CODE:
            return self._render_code_block(block, content)
        elif block.type == BlockType.IMAGE:
            return self._render_image(block)
        # ... more block types
    
    def _render_paragraph(self, block: ContentBlock, content: EditorContent) -> ft.Control:
        """Render paragraph with inline styles"""
        
        # Get inline styles for this block
        styles = content.inline_styles.get(block.id, [])
        entities = [e for e in content.entities if e.block_id == block.id]
        
        # Build styled text spans
        spans = self._build_text_spans(block.text, styles, entities)
        
        return ft.Container(
            content=ft.Row(spans, wrap=True),
            padding=ft.padding.symmetric(vertical=8),
            data={"block_id": block.id}
        )
    
    def _build_text_spans(self, text: str, styles: List[InlineStyle], 
                          entities: List[Entity]) -> List[ft.Control]:
        """Build text spans with styling"""
        
        spans = []
        current_pos = 0
        
        # Merge and sort all style boundaries
        boundaries = self._get_style_boundaries(text, styles, entities)
        
        for boundary in boundaries:
            # Add unstyled text before boundary
            if boundary.offset > current_pos:
                spans.append(ft.Text(text[current_pos:boundary.offset]))
            
            # Add styled text
            segment_text = text[boundary.offset:boundary.end]
            text_style = self._merge_styles(boundary.styles)
            
            if boundary.entity:
                # Special handling for entities
                span = self._create_entity_span(segment_text, boundary.entity, text_style)
            else:
                span = ft.Text(segment_text, **text_style)
            
            spans.append(span)
            current_pos = boundary.end
        
        # Add remaining text
        if current_pos < len(text):
            spans.append(ft.Text(text[current_pos:]))
        
        return spans
```

### Plugin System

```python
class EditorPlugin:
    """Base class for editor plugins"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def initialize(self, editor: RichTextEditor):
        """Initialize plugin with editor instance"""
        self.editor = editor
    
    def handles_command(self, command: EditorCommand) -> bool:
        """Check if plugin handles command"""
        return False
    
    def execute_command(self, command: EditorCommand, value: Any, state: EditorState):
        """Execute plugin command"""
        pass
    
    def on_key_down(self, event: KeyEvent) -> bool:
        """Handle key events. Return True to prevent default"""
        return False
    
    def get_toolbar_items(self) -> List[ToolbarItem]:
        """Get custom toolbar items"""
        return []

class LinkPlugin(EditorPlugin):
    """Plugin for handling links"""
    
    def handles_command(self, command: EditorCommand) -> bool:
        return command in [EditorCommand.INSERT_LINK, EditorCommand.EDIT_LINK]
    
    def execute_command(self, command: EditorCommand, value: Any, state: EditorState):
        if command == EditorCommand.INSERT_LINK:
            self._insert_link(value, state)
        elif command == EditorCommand.EDIT_LINK:
            self._edit_link(value, state)
    
    def _insert_link(self, url: str, state: EditorState):
        """Insert a link at current position"""
        
        selection = state.selection
        
        # Create link entity
        entity = Entity(
            id=str(uuid.uuid4()),
            type=EntityType.LINK,
            offset=selection.start,
            length=selection.end - selection.start,
            data={"url": url, "title": self._fetch_title(url)}
        )
        
        # Add to state
        state.content.entities.append(entity)
        
        # Style as link
        self.editor._apply_style_to_range(
            selection.start,
            selection.end,
            StyleType.LINK
        )

class ImagePlugin(EditorPlugin):
    """Plugin for image handling"""
    
    def handles_command(self, command: EditorCommand) -> bool:
        return command in [EditorCommand.INSERT_IMAGE, EditorCommand.RESIZE_IMAGE]
    
    def execute_command(self, command: EditorCommand, value: Any, state: EditorState):
        if command == EditorCommand.INSERT_IMAGE:
            self._insert_image(value, state)
    
    def _insert_image(self, image_data: Dict, state: EditorState):
        """Insert image block"""
        
        # Create image block
        image_block = ContentBlock(
            id=str(uuid.uuid4()),
            type=BlockType.IMAGE,
            text="",
            attributes={
                "src": image_data["url"],
                "alt": image_data.get("alt", ""),
                "width": image_data.get("width"),
                "height": image_data.get("height"),
                "alignment": image_data.get("alignment", "left")
            },
            children=[]
        )
        
        # Insert at current position
        current_block_index = self._get_current_block_index(state)
        state.content.blocks.insert(current_block_index + 1, image_block)
```

### Serialization

```python
class EditorSerializer:
    """Serialize/deserialize editor content"""
    
    def to_html(self, content: EditorContent) -> str:
        """Convert to HTML"""
        
        html_parts = []
        
        for block in content.blocks:
            html_parts.append(self._block_to_html(block, content))
        
        return "\n".join(html_parts)
    
    def _block_to_html(self, block: ContentBlock, content: EditorContent) -> str:
        """Convert block to HTML"""
        
        if block.type == BlockType.PARAGRAPH:
            inner_html = self._styled_text_to_html(block, content)
            return f"<p>{inner_html}</p>"
        
        elif block.type == BlockType.HEADING:
            level = block.attributes.get("level", 2)
            inner_html = self._styled_text_to_html(block, content)
            return f"<h{level}>{inner_html}</h{level}>"
        
        elif block.type == BlockType.CODE:
            language = block.attributes.get("language", "")
            return f'<pre><code class="language-{language}">{html.escape(block.text)}</code></pre>'
        
        # ... more block types
    
    def from_html(self, html_string: str) -> EditorContent:
        """Parse HTML to editor content"""
        
        soup = BeautifulSoup(html_string, 'html.parser')
        blocks = []
        
        for element in soup.body.children if soup.body else soup.children:
            if isinstance(element, Tag):
                block = self._html_element_to_block(element)
                if block:
                    blocks.append(block)
        
        return EditorContent(blocks=blocks, inline_styles={}, entities=[])
    
    def to_markdown(self, content: EditorContent) -> str:
        """Convert to Markdown"""
        
        md_parts = []
        
        for block in content.blocks:
            md_parts.append(self._block_to_markdown(block, content))
        
        return "\n\n".join(md_parts)
```

### Collaborative Features

```python
class CollaborativeEditor:
    """Collaborative editing support"""
    
    def __init__(self, editor: RichTextEditor, user_id: str):
        self.editor = editor
        self.user_id = user_id
        self.collaborators: Dict[str, Collaborator] = {}
        self.operation_transformer = OperationalTransform()
    
    def apply_remote_operation(self, operation: Operation, from_user: str):
        """Apply operation from remote user"""
        
        # Transform against local operations
        transformed = self.operation_transformer.transform(
            operation,
            self.editor.get_pending_operations()
        )
        
        # Apply to editor
        self.editor.apply_operation(transformed)
        
        # Update collaborator cursor
        if from_user in self.collaborators:
            self.collaborators[from_user].cursor_position = operation.cursor_after
    
    def broadcast_operation(self, operation: Operation):
        """Send operation to other users"""
        
        # This would connect to a real-time service
        message = {
            "type": "operation",
            "operation": operation.to_dict(),
            "user_id": self.user_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send via WebSocket, Firebase, etc.
        self._send_message(message)
```

## Performance Optimization

### 1. Virtual Rendering
```python
def render_visible_blocks(viewport: Rectangle, blocks: List[ContentBlock]):
    """Only render blocks in viewport"""
    
    visible_blocks = []
    current_y = 0
    
    for block in blocks:
        block_height = estimate_block_height(block)
        
        if current_y + block_height >= viewport.top and current_y <= viewport.bottom:
            visible_blocks.append(block)
        
        current_y += block_height
        
        if current_y > viewport.bottom:
            break  # No more visible blocks
    
    return visible_blocks
```

### 2. Debounced Operations
```python
class DebouncedFormatter:
    """Debounce formatting operations"""
    
    def __init__(self, delay: float = 0.3):
        self.delay = delay
        self.pending_operations: List[Operation] = []
        self.timer: Optional[Timer] = None
    
    def add_operation(self, operation: Operation):
        self.pending_operations.append(operation)
        
        if self.timer:
            self.timer.cancel()
        
        self.timer = Timer(self.delay, self._apply_operations)
        self.timer.start()
```

## Testing Requirements

### Unit Tests
- Block creation and manipulation
- Style application and merging
- Entity management
- Serialization accuracy

### Integration Tests
- Full editing workflow
- Plugin integration
- Toolbar interactions
- Copy/paste operations

### Performance Tests
- Large document handling
- Many inline styles
- Rapid typing
- Collaborative editing

## Future Enhancements

1. **AI Writing Assistant**: Content suggestions and completion
2. **Voice Input**: Speech-to-text editing
3. **Advanced Tables**: Spreadsheet-like functionality
4. **Code Editor**: Full syntax highlighting and completion
5. **Drawing Tools**: Inline sketches and diagrams
6. **Version Tracking**: See document history
7. **Export Options**: PDF, DOCX, etc.
8. **Custom Blocks**: User-defined block types

## Example Usage

```python
# Initialize editor
editor = RichTextEditor(
    initial_content="<p>Welcome to Canvas Editor!</p>",
    config=EditorConfig(
        toolbar=ToolbarConfig(
            groups=[
                ToolbarGroup(
                    name="text",
                    items=[
                        ToolbarButton(EditorCommand.BOLD, "format_bold"),
                        ToolbarButton(EditorCommand.ITALIC, "format_italic"),
                        ToolbarDropdown(
                            EditorCommand.FONT_SIZE,
                            options=["12px", "14px", "16px", "18px", "24px"]
                        )
                    ]
                )
            ]
        ),
        plugins=[
            LinkPlugin({}),
            ImagePlugin({"upload_endpoint": "/api/upload"}),
            EmojiPlugin({})
        ]
    )
)

# Handle content changes
editor.on_change = lambda content: save_content(content)

# Get content
html_content = editor.get_html()
markdown_content = editor.get_markdown()
```