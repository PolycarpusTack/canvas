# Rich Text Editor - Development Plan

## Phase 1: Solution Design Analysis & Validation

### 1. Initial Understanding
- **Goal**: Build WYSIWYG rich text editor with formatting, media, and plugins
- **Stack**: Python/Flet, HTML/Markdown parsing, plugin architecture
- **Components**: RichTextEditor, EditorToolbar, ContentRenderer, PluginSystem
- **User Personas**: Content creators editing text with rich formatting

### 2. Clarity Assessment
- **Editor Architecture**: High (3) - Well-defined block/inline model
- **Toolbar System**: High (3) - Clear command structure
- **Plugin System**: High (3) - Extensible plugin architecture
- **Rendering Logic**: Medium (2) - Complex style merging
- **Serialization**: High (3) - Clear HTML/Markdown conversion
- **Overall Clarity**: High (3)

### 3. Technical Feasibility
- **Basic Text Editing**: Low risk (1) - Standard text operations
- **Style Application**: Medium risk (2) - Complex inline style merging
- **Media Embedding**: Medium risk (2) - File handling complexity
- **Real-time Rendering**: High risk (3) - Performance with large documents
- **Collaborative Features**: High risk (3) - Operational transform complexity

### 4. Security Assessment
- **Content Sanitization**: Prevent XSS in user content
- **File Upload**: Validate media types and sizes
- **Link Validation**: Check URLs for safety
- **HTML Import**: Safe parsing of external content

### 5. Performance Requirements
- **Typing Latency**: < 16ms keystroke response
- **Render Time**: < 100ms for large documents
- **Memory Usage**: < 100MB for 50-page document
- **Save Time**: < 500ms auto-save

**Recommendation**: PROCEEDING with backlog generation

---

## EPIC A: Core Editor System

Implement fundamental rich text editing with block/inline model and basic formatting.

**Definition of Done:**
- ✓ Text input and editing working
- ✓ Basic formatting (bold, italic, etc.)
- ✓ Block elements (paragraphs, headings)
- ✓ Undo/redo functionality

**Business Value:** Essential rich text editing capabilities

**Risk Assessment:**
- Performance with large content (High/3) - Virtual rendering needed
- Style conflict resolution (Medium/2) - Clear precedence rules
- Cross-platform behavior (Medium/2) - Consistent key handling

**Cross-Functional Requirements:**
- Performance: 60fps during typing
- Security: Sanitize all content
- Accessibility: Full keyboard navigation
- Observability: Track editor usage

---

### USER STORY A-1: Editor State and Document Model

**ID & Title:** A-1: Implement Rich Text Document Model
**User Persona Narrative:** As a content creator, I want a reliable editor that preserves my formatting
**Business Value:** High (3)
**Priority Score:** 5
**Story Points:** L

**Acceptance Criteria:**
```gherkin
Given I type text in the editor
When I apply bold formatting
Then the selected text becomes bold
And the formatting persists when saved

Given I have a document with multiple blocks
When I navigate between blocks
Then cursor position is maintained
And block types are preserved

Given I paste formatted content
When the content contains various styles
Then formatting is preserved appropriately
And invalid elements are stripped
```

**External Dependencies:** BeautifulSoup, markdown libraries
**Technical Debt Considerations:** Consider CRDT for future collaborative editing
**Test Data Requirements:** Various formatted documents

---

#### TASK A-1-T1: Create Document Model and State

**Goal:** Implement comprehensive document model with blocks and inline styles

**Token Budget:** 12,000 tokens

**Document Model:**
```python
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

class BlockType(Enum):
    """
    CLAUDE.md #4.1: Explicit block types
    """
    PARAGRAPH = auto()
    HEADING = auto()
    LIST_ITEM = auto()
    BLOCKQUOTE = auto()
    CODE_BLOCK = auto()
    IMAGE = auto()
    VIDEO = auto()
    TABLE = auto()
    HORIZONTAL_RULE = auto()

class StyleType(Enum):
    """Inline style types"""
    BOLD = auto()
    ITALIC = auto()
    UNDERLINE = auto()
    STRIKETHROUGH = auto()
    CODE = auto()
    COLOR = auto()
    BACKGROUND_COLOR = auto()
    FONT_SIZE = auto()
    FONT_FAMILY = auto()
    LINK = auto()

class EntityType(Enum):
    """Special entity types"""
    LINK = auto()
    MENTION = auto()
    HASHTAG = auto()
    EMOJI = auto()
    MATH = auto()

@dataclass
class ContentBlock:
    """
    Block-level content element
    CLAUDE.md #2.1.1: Validate block structure
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: BlockType = BlockType.PARAGRAPH
    text: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)
    children: List[ContentBlock] = field(default_factory=list)
    parent_id: Optional[str] = None
    
    def __post_init__(self):
        """Validate block on creation"""
        if self.type == BlockType.HEADING and "level" not in self.attributes:
            self.attributes["level"] = 2  # Default to H2
        
        if self.type == BlockType.LIST_ITEM and "list_type" not in self.attributes:
            self.attributes["list_type"] = "unordered"
        
        if self.type == BlockType.CODE_BLOCK and "language" not in self.attributes:
            self.attributes["language"] = "plaintext"
    
    def can_contain_text(self) -> bool:
        """Check if block can contain text"""
        return self.type not in [
            BlockType.IMAGE,
            BlockType.VIDEO,
            BlockType.HORIZONTAL_RULE
        ]
    
    def can_have_children(self) -> bool:
        """Check if block can have child blocks"""
        return self.type in [
            BlockType.LIST_ITEM,
            BlockType.TABLE,
            BlockType.BLOCKQUOTE
        ]

@dataclass
class InlineStyle:
    """
    Inline text styling
    CLAUDE.md #1.2: Immutable style ranges
    """
    offset: int
    length: int
    style: StyleType
    value: Optional[Any] = None
    
    def __post_init__(self):
        """Validate style"""
        if self.offset < 0:
            raise ValueError("Offset cannot be negative")
        
        if self.length <= 0:
            raise ValueError("Length must be positive")
        
        # Validate style-specific values
        if self.style == StyleType.COLOR and self.value:
            if not self._is_valid_color(self.value):
                raise ValueError(f"Invalid color value: {self.value}")
    
    def overlaps(self, other: InlineStyle) -> bool:
        """Check if styles overlap"""
        return not (
            self.offset + self.length <= other.offset or
            other.offset + other.length <= self.offset
        )
    
    def merge(self, other: InlineStyle) -> Optional[InlineStyle]:
        """Merge overlapping styles of same type"""
        if self.style != other.style or self.value != other.value:
            return None
        
        if not self.overlaps(other):
            # Check if adjacent
            if self.offset + self.length == other.offset:
                return InlineStyle(
                    offset=self.offset,
                    length=self.length + other.length,
                    style=self.style,
                    value=self.value
                )
            elif other.offset + other.length == self.offset:
                return InlineStyle(
                    offset=other.offset,
                    length=self.length + other.length,
                    style=self.style,
                    value=self.value
                )
        
        return None
    
    def _is_valid_color(self, color: str) -> bool:
        """Validate color format"""
        import re
        patterns = [
            r'^#[0-9A-Fa-f]{3}$',  # #RGB
            r'^#[0-9A-Fa-f]{6}$',  # #RRGGBB
            r'^rgb\(\d{1,3},\s*\d{1,3},\s*\d{1,3}\)$',  # rgb()
            r'^rgba\(\d{1,3},\s*\d{1,3},\s*\d{1,3},\s*[01]?\.?\d*\)$'  # rgba()
        ]
        return any(re.match(pattern, color) for pattern in patterns)

@dataclass
class Entity:
    """
    Special entities in text
    CLAUDE.md #7.2: Safe entity data
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: EntityType = EntityType.LINK
    offset: int = 0
    length: int = 0
    block_id: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate entity"""
        if self.type == EntityType.LINK and "url" not in self.data:
            raise ValueError("Link entity requires URL")
        
        if self.type == EntityType.MENTION and "user_id" not in self.data:
            raise ValueError("Mention entity requires user_id")

@dataclass
class Selection:
    """
    Editor selection/cursor state
    CLAUDE.md #6.1: Clear selection model
    """
    start: int
    end: int
    block_id: str
    direction: str = "forward"  # forward or backward
    
    @property
    def is_collapsed(self) -> bool:
        """Check if selection is just a cursor"""
        return self.start == self.end
    
    @property
    def length(self) -> int:
        """Get selection length"""
        return abs(self.end - self.start)
    
    def normalize(self) -> Selection:
        """Normalize selection to always be forward"""
        if self.start > self.end:
            return Selection(
                start=self.end,
                end=self.start,
                block_id=self.block_id,
                direction="backward"
            )
        return self

@dataclass
class EditorContent:
    """
    Complete document content
    CLAUDE.md #1.4: Extensible content model
    """
    blocks: List[ContentBlock] = field(default_factory=list)
    inline_styles: Dict[str, List[InlineStyle]] = field(default_factory=dict)
    entities: List[Entity] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_block(self, block: ContentBlock, index: Optional[int] = None) -> None:
        """Add block at position"""
        if index is None:
            self.blocks.append(block)
        else:
            self.blocks.insert(index, block)
    
    def remove_block(self, block_id: str) -> Optional[ContentBlock]:
        """Remove block by ID"""
        for i, block in enumerate(self.blocks):
            if block.id == block_id:
                # Remove associated styles and entities
                self.inline_styles.pop(block_id, None)
                self.entities = [e for e in self.entities if e.block_id != block_id]
                return self.blocks.pop(i)
        return None
    
    def get_block(self, block_id: str) -> Optional[ContentBlock]:
        """Get block by ID"""
        for block in self.blocks:
            if block.id == block_id:
                return block
        return None
    
    def add_style(self, block_id: str, style: InlineStyle) -> None:
        """
        Add inline style to block
        CLAUDE.md #1.5: Optimize style storage
        """
        if block_id not in self.inline_styles:
            self.inline_styles[block_id] = []
        
        styles = self.inline_styles[block_id]
        
        # Try to merge with existing styles
        merged = False
        for i, existing in enumerate(styles):
            if existing.style == style.style and existing.value == style.value:
                merged_style = existing.merge(style)
                if merged_style:
                    styles[i] = merged_style
                    merged = True
                    break
        
        if not merged:
            styles.append(style)
        
        # Sort styles by offset for efficient processing
        styles.sort(key=lambda s: s.offset)
        
        # Merge adjacent styles
        self._merge_adjacent_styles(block_id)

@dataclass
class EditorState:
    """
    Complete editor state
    CLAUDE.md #6.1: Single source of truth
    """
    content: EditorContent = field(default_factory=EditorContent)
    selection: Optional[Selection] = None
    format: FormatState = field(default_factory=lambda: FormatState())
    history: HistoryStack = field(default_factory=lambda: HistoryStack())
    mode: EditorMode = EditorMode.EDIT
    is_composing: bool = False
    
    def get_current_block(self) -> Optional[ContentBlock]:
        """Get block containing cursor"""
        if not self.selection:
            return None
        return self.content.get_block(self.selection.block_id)
    
    def get_selected_text(self) -> str:
        """Get currently selected text"""
        if not self.selection or self.selection.is_collapsed:
            return ""
        
        block = self.get_current_block()
        if not block:
            return ""
        
        sel = self.selection.normalize()
        return block.text[sel.start:sel.end]

@dataclass
class FormatState:
    """
    Current format at cursor
    CLAUDE.md #2.1.1: Track active formats
    """
    active_styles: Set[StyleType] = field(default_factory=set)
    style_values: Dict[StyleType, Any] = field(default_factory=dict)
    block_type: BlockType = BlockType.PARAGRAPH
    block_attributes: Dict[str, Any] = field(default_factory=dict)
    
    def toggle_style(self, style: StyleType, value: Optional[Any] = None) -> None:
        """Toggle style on/off"""
        if style in self.active_styles and self.style_values.get(style) == value:
            self.active_styles.remove(style)
            self.style_values.pop(style, None)
        else:
            self.active_styles.add(style)
            if value is not None:
                self.style_values[style] = value
    
    def has_style(self, style: StyleType) -> bool:
        """Check if style is active"""
        return style in self.active_styles
    
    def get_style_value(self, style: StyleType) -> Optional[Any]:
        """Get style value"""
        return self.style_values.get(style)
```

**State Management:**
```python
class EditorStateManager:
    """
    CLAUDE.md #6.1: Centralized state management
    CLAUDE.md #2.1.4: Proper state lifecycle
    """
    
    def __init__(self, initial_content: Optional[str] = None):
        self.state = self._initialize_state(initial_content)
        self.listeners: List[Callable[[EditorState], None]] = []
        self._lock = threading.RLock()
        
    def _initialize_state(self, content: Optional[str]) -> EditorState:
        """Initialize editor state"""
        if content:
            # Parse initial content
            parser = ContentParser()
            editor_content = parser.parse_html(content)
        else:
            # Create default content
            editor_content = EditorContent(
                blocks=[ContentBlock(type=BlockType.PARAGRAPH)]
            )
        
        return EditorState(content=editor_content)
    
    def update_state(self, updater: Callable[[EditorState], None]) -> None:
        """
        Update state atomically
        CLAUDE.md #2.1.4: Thread-safe updates
        """
        with self._lock:
            # Create state snapshot for history
            snapshot = self._create_snapshot()
            
            # Apply update
            updater(self.state)
            
            # Record in history
            self.state.history.push(snapshot)
            
            # Notify listeners
            self._notify_listeners()
    
    def apply_operation(self, operation: EditorOperation) -> None:
        """Apply operation to state"""
        self.update_state(lambda state: operation.apply(state))
    
    def undo(self) -> bool:
        """Undo last operation"""
        with self._lock:
            snapshot = self.state.history.undo()
            if snapshot:
                self._restore_snapshot(snapshot)
                self._notify_listeners()
                return True
            return False
    
    def redo(self) -> bool:
        """Redo operation"""
        with self._lock:
            snapshot = self.state.history.redo()
            if snapshot:
                self._restore_snapshot(snapshot)
                self._notify_listeners()
                return True
            return False
```

**Deliverables:**
- Complete document model implementation
- State management system
- History/undo functionality
- Comprehensive validation

**Quality Gates:**
- ✓ All models strongly typed
- ✓ Thread-safe state updates
- ✓ 100% test coverage
- ✓ Performance benchmarks met

**Unblocks:** [A-1-T2, A-1-T3]
**Confidence Score:** High (3)

---

#### TASK A-1-T2: Implement Text Operations

**Goal:** Create text manipulation operations with proper style handling

**Token Budget:** 10,000 tokens

**Text Operations:**
```python
class TextOperation:
    """
    Base class for text operations
    CLAUDE.md #3.3: Command pattern
    """
    
    @abstractmethod
    def apply(self, state: EditorState) -> None:
        """Apply operation to state"""
        pass
    
    @abstractmethod
    def inverse(self) -> TextOperation:
        """Get inverse operation for undo"""
        pass

class InsertTextOperation(TextOperation):
    """
    Insert text at position
    CLAUDE.md #2.1.1: Validate text input
    """
    
    def __init__(
        self,
        block_id: str,
        offset: int,
        text: str,
        format_state: Optional[FormatState] = None
    ):
        self.block_id = block_id
        self.offset = offset
        self.text = text
        self.format_state = format_state
        
        # Validate
        if not text:
            raise ValueError("Text cannot be empty")
        
        if offset < 0:
            raise ValueError("Offset cannot be negative")
    
    def apply(self, state: EditorState) -> None:
        """Insert text and apply formatting"""
        
        block = state.content.get_block(self.block_id)
        if not block:
            raise ValueError(f"Block not found: {self.block_id}")
        
        if not block.can_contain_text():
            raise ValueError(f"Block type {block.type} cannot contain text")
        
        # Validate offset
        if self.offset > len(block.text):
            raise ValueError(f"Offset {self.offset} exceeds text length {len(block.text)}")
        
        # Insert text
        block.text = (
            block.text[:self.offset] +
            self.text +
            block.text[self.offset:]
        )
        
        # Adjust existing styles
        self._adjust_styles_after_insert(state.content, self.block_id)
        
        # Apply formatting to inserted text
        if self.format_state and self.format_state.active_styles:
            for style in self.format_state.active_styles:
                value = self.format_state.get_style_value(style)
                state.content.add_style(
                    self.block_id,
                    InlineStyle(
                        offset=self.offset,
                        length=len(self.text),
                        style=style,
                        value=value
                    )
                )
        
        # Update selection
        if state.selection and state.selection.block_id == self.block_id:
            new_position = self.offset + len(self.text)
            state.selection = Selection(
                start=new_position,
                end=new_position,
                block_id=self.block_id
            )
    
    def _adjust_styles_after_insert(
        self,
        content: EditorContent,
        block_id: str
    ) -> None:
        """
        Adjust style offsets after text insertion
        CLAUDE.md #1.5: Efficient style adjustment
        """
        if block_id not in content.inline_styles:
            return
        
        styles = content.inline_styles[block_id]
        adjusted_styles = []
        
        for style in styles:
            if style.offset >= self.offset:
                # Style starts after insertion point
                adjusted_styles.append(InlineStyle(
                    offset=style.offset + len(self.text),
                    length=style.length,
                    style=style.style,
                    value=style.value
                ))
            elif style.offset + style.length <= self.offset:
                # Style ends before insertion point
                adjusted_styles.append(style)
            else:
                # Style spans insertion point - split it
                before_length = self.offset - style.offset
                after_offset = self.offset + len(self.text)
                after_length = (style.offset + style.length) - self.offset
                
                if before_length > 0:
                    adjusted_styles.append(InlineStyle(
                        offset=style.offset,
                        length=before_length,
                        style=style.style,
                        value=style.value
                    ))
                
                if after_length > 0:
                    adjusted_styles.append(InlineStyle(
                        offset=after_offset,
                        length=after_length,
                        style=style.style,
                        value=style.value
                    ))
        
        content.inline_styles[block_id] = adjusted_styles
    
    def inverse(self) -> TextOperation:
        """Get delete operation to undo this insert"""
        return DeleteTextOperation(
            block_id=self.block_id,
            offset=self.offset,
            length=len(self.text)
        )

class DeleteTextOperation(TextOperation):
    """
    Delete text from position
    CLAUDE.md #2.1.2: Handle edge cases
    """
    
    def __init__(self, block_id: str, offset: int, length: int):
        self.block_id = block_id
        self.offset = offset
        self.length = length
        self.deleted_text = ""  # Will be set during apply
        self.deleted_styles = []  # Will be set during apply
    
    def apply(self, state: EditorState) -> None:
        """Delete text and adjust styles"""
        
        block = state.content.get_block(self.block_id)
        if not block:
            raise ValueError(f"Block not found: {self.block_id}")
        
        # Validate range
        if self.offset < 0 or self.offset + self.length > len(block.text):
            raise ValueError("Invalid delete range")
        
        # Store deleted content for undo
        self.deleted_text = block.text[self.offset:self.offset + self.length]
        self.deleted_styles = self._get_styles_in_range(
            state.content,
            self.block_id,
            self.offset,
            self.offset + self.length
        )
        
        # Delete text
        block.text = (
            block.text[:self.offset] +
            block.text[self.offset + self.length:]
        )
        
        # Adjust styles
        self._adjust_styles_after_delete(state.content, self.block_id)
        
        # Update selection
        if state.selection and state.selection.block_id == self.block_id:
            state.selection = Selection(
                start=self.offset,
                end=self.offset,
                block_id=self.block_id
            )

class FormatTextOperation(TextOperation):
    """
    Apply formatting to text range
    CLAUDE.md #1.2: DRY formatting logic
    """
    
    def __init__(
        self,
        block_id: str,
        start: int,
        end: int,
        style: StyleType,
        value: Optional[Any] = None,
        remove: bool = False
    ):
        self.block_id = block_id
        self.start = start
        self.end = end
        self.style = style
        self.value = value
        self.remove = remove
    
    def apply(self, state: EditorState) -> None:
        """Apply or remove formatting"""
        
        block = state.content.get_block(self.block_id)
        if not block:
            raise ValueError(f"Block not found: {self.block_id}")
        
        # Normalize range
        start = max(0, min(self.start, len(block.text)))
        end = max(start, min(self.end, len(block.text)))
        
        if start == end:
            return  # Nothing to format
        
        if self.remove:
            self._remove_style(state.content, self.block_id, start, end)
        else:
            # Add new style
            state.content.add_style(
                self.block_id,
                InlineStyle(
                    offset=start,
                    length=end - start,
                    style=self.style,
                    value=self.value
                )
            )
    
    def _remove_style(
        self,
        content: EditorContent,
        block_id: str,
        start: int,
        end: int
    ) -> None:
        """Remove style from range"""
        if block_id not in content.inline_styles:
            return
        
        styles = content.inline_styles[block_id]
        remaining_styles = []
        
        for style in styles:
            if style.style != self.style:
                remaining_styles.append(style)
                continue
            
            # Check if style overlaps with range
            if style.offset >= end or style.offset + style.length <= start:
                # No overlap
                remaining_styles.append(style)
            else:
                # Partial overlap - split style
                if style.offset < start:
                    # Part before range
                    remaining_styles.append(InlineStyle(
                        offset=style.offset,
                        length=start - style.offset,
                        style=style.style,
                        value=style.value
                    ))
                
                if style.offset + style.length > end:
                    # Part after range
                    remaining_styles.append(InlineStyle(
                        offset=end,
                        length=(style.offset + style.length) - end,
                        style=style.style,
                        value=style.value
                    ))
        
        content.inline_styles[block_id] = remaining_styles
```

**Block Operations:**
```python
class BlockOperation(TextOperation):
    """Base class for block-level operations"""
    pass

class InsertBlockOperation(BlockOperation):
    """
    Insert new block
    CLAUDE.md #2.1.1: Validate block insertion
    """
    
    def __init__(
        self,
        block: ContentBlock,
        index: int,
        split_from: Optional[Tuple[str, int]] = None
    ):
        self.block = block
        self.index = index
        self.split_from = split_from  # (block_id, offset) if splitting
    
    def apply(self, state: EditorState) -> None:
        """Insert block at position"""
        
        # Validate index
        if self.index < 0 or self.index > len(state.content.blocks):
            raise ValueError(f"Invalid block index: {self.index}")
        
        if self.split_from:
            # Handle block split (e.g., Enter key in middle of paragraph)
            source_block_id, offset = self.split_from
            source_block = state.content.get_block(source_block_id)
            
            if source_block and offset < len(source_block.text):
                # Move text after offset to new block
                self.block.text = source_block.text[offset:]
                source_block.text = source_block.text[:offset]
                
                # Move applicable styles
                self._split_styles(
                    state.content,
                    source_block_id,
                    self.block.id,
                    offset
                )
        
        # Insert block
        state.content.add_block(self.block, self.index)
        
        # Update selection to new block
        state.selection = Selection(
            start=0,
            end=0,
            block_id=self.block.id
        )

class ChangeBlockTypeOperation(BlockOperation):
    """Change block type while preserving content"""
    
    def __init__(self, block_id: str, new_type: BlockType, attributes: Dict[str, Any] = None):
        self.block_id = block_id
        self.new_type = new_type
        self.attributes = attributes or {}
        self.old_type = None
        self.old_attributes = None
    
    def apply(self, state: EditorState) -> None:
        """Change block type"""
        
        block = state.content.get_block(self.block_id)
        if not block:
            raise ValueError(f"Block not found: {self.block_id}")
        
        # Store old values for undo
        self.old_type = block.type
        self.old_attributes = block.attributes.copy()
        
        # Validate type change
        if not self._can_change_type(block, self.new_type):
            raise ValueError(f"Cannot change {block.type} to {self.new_type}")
        
        # Change type
        block.type = self.new_type
        block.attributes = self.attributes.copy()
        
        # Apply type-specific initialization
        if self.new_type == BlockType.HEADING:
            if "level" not in block.attributes:
                block.attributes["level"] = 2
        elif self.new_type == BlockType.LIST_ITEM:
            if "list_type" not in block.attributes:
                block.attributes["list_type"] = "unordered"
```

**Unblocks:** [A-1-T3, A-2-T1]
**Confidence Score:** High (3)

---

#### TASK A-1-T3: Implement Content Renderer

**Goal:** Create efficient content rendering system

**Token Budget:** 10,000 tokens

**Rendering System:**
```python
class ContentRenderer:
    """
    CLAUDE.md #1.5: Optimized rendering
    CLAUDE.md #9.1: Accessible output
    """
    
    def __init__(self, config: RenderConfig = None):
        self.config = config or RenderConfig()
        self.style_cache = StyleCache()
        self.block_renderers = self._init_block_renderers()
        
    def render(
        self,
        content: EditorContent,
        selection: Optional[Selection] = None,
        viewport: Optional[Rectangle] = None
    ) -> ft.Control:
        """
        Render content to UI
        CLAUDE.md #1.5: Virtual rendering for performance
        """
        if viewport:
            # Only render visible blocks
            visible_blocks = self._get_visible_blocks(content.blocks, viewport)
        else:
            visible_blocks = content.blocks
        
        rendered_blocks = []
        
        for block in visible_blocks:
            block_control = self._render_block(
                block,
                content,
                selection if selection and selection.block_id == block.id else None
            )
            rendered_blocks.append(block_control)
        
        return ft.Column(
            controls=rendered_blocks,
            spacing=0,
            scroll=ft.ScrollMode.AUTO
        )
    
    def _render_block(
        self,
        block: ContentBlock,
        content: EditorContent,
        selection: Optional[Selection]
    ) -> ft.Control:
        """Render individual block"""
        
        renderer = self.block_renderers.get(block.type)
        if not renderer:
            logger.warning(f"No renderer for block type: {block.type}")
            renderer = self.block_renderers[BlockType.PARAGRAPH]
        
        return renderer.render(block, content, selection)

class BlockRenderer(ABC):
    """Base class for block renderers"""
    
    @abstractmethod
    def render(
        self,
        block: ContentBlock,
        content: EditorContent,
        selection: Optional[Selection]
    ) -> ft.Control:
        """Render block to control"""
        pass

class ParagraphRenderer(BlockRenderer):
    """
    Render paragraph blocks
    CLAUDE.md #7.2: Safe text rendering
    """
    
    def render(
        self,
        block: ContentBlock,
        content: EditorContent,
        selection: Optional[Selection]
    ) -> ft.Control:
        """Render paragraph with inline styles"""
        
        # Get styles for this block
        styles = content.inline_styles.get(block.id, [])
        entities = [e for e in content.entities if e.block_id == block.id]
        
        # Build text spans
        spans = self._build_text_spans(
            block.text,
            styles,
            entities,
            selection
        )
        
        # Wrap in container
        return ft.Container(
            content=ft.Row(
                controls=spans,
                wrap=True,
                spacing=0
            ),
            padding=ft.padding.symmetric(vertical=8, horizontal=0),
            data={"block_id": block.id, "block_type": "paragraph"},
            on_click=self._handle_click,
            animate_opacity=300
        )
    
    def _build_text_spans(
        self,
        text: str,
        styles: List[InlineStyle],
        entities: List[Entity],
        selection: Optional[Selection]
    ) -> List[ft.Control]:
        """
        Build styled text spans
        CLAUDE.md #1.2: DRY span building
        """
        if not text:
            # Empty paragraph - show placeholder
            return [ft.Text(
                "Type something...",
                size=16,
                color="#999999",
                italic=True
            )]
        
        spans = []
        boundaries = self._calculate_style_boundaries(text, styles, entities)
        
        for boundary in boundaries:
            segment_text = text[boundary.start:boundary.end]
            
            # Calculate text style
            text_style = self._merge_styles(boundary.styles)
            
            # Check if segment contains selection
            if selection and not selection.is_collapsed:
                sel_start = max(boundary.start, selection.start)
                sel_end = min(boundary.end, selection.end)
                
                if sel_start < sel_end:
                    # Split into three parts: before, selected, after
                    if boundary.start < sel_start:
                        spans.append(ft.Text(
                            text[boundary.start:sel_start],
                            **text_style
                        ))
                    
                    # Selected part
                    selected_style = text_style.copy()
                    selected_style["bgcolor"] = "#B4D5FE"  # Selection color
                    spans.append(ft.Text(
                        text[sel_start:sel_end],
                        **selected_style
                    ))
                    
                    if sel_end < boundary.end:
                        spans.append(ft.Text(
                            text[sel_end:boundary.end],
                            **text_style
                        ))
                    continue
            
            # Handle entities
            if boundary.entity:
                span = self._create_entity_span(
                    segment_text,
                    boundary.entity,
                    text_style
                )
            else:
                span = ft.Text(segment_text, **text_style)
            
            spans.append(span)
        
        # Add cursor if needed
        if selection and selection.is_collapsed:
            cursor_index = self._find_cursor_position(spans, selection.start)
            if cursor_index is not None:
                spans.insert(cursor_index, self._create_cursor())
        
        return spans

    def _merge_styles(self, styles: List[InlineStyle]) -> Dict[str, Any]:
        """
        Merge multiple styles into text properties
        CLAUDE.md #1.5: Efficient style merging
        """
        result = {
            "size": 16,
            "color": "#000000",
            "weight": ft.FontWeight.NORMAL,
            "italic": False
        }
        
        for style in styles:
            if style.style == StyleType.BOLD:
                result["weight"] = ft.FontWeight.BOLD
            elif style.style == StyleType.ITALIC:
                result["italic"] = True
            elif style.style == StyleType.UNDERLINE:
                result["decoration"] = ft.TextDecoration.UNDERLINE
            elif style.style == StyleType.COLOR:
                result["color"] = style.value
            elif style.style == StyleType.FONT_SIZE:
                result["size"] = style.value
            # ... more styles
        
        return result

class HeadingRenderer(BlockRenderer):
    """Render heading blocks"""
    
    def render(
        self,
        block: ContentBlock,
        content: EditorContent,
        selection: Optional[Selection]
    ) -> ft.Control:
        """Render heading with appropriate size"""
        
        level = block.attributes.get("level", 2)
        size_map = {
            1: 32,
            2: 28,
            3: 24,
            4: 20,
            5: 18,
            6: 16
        }
        
        # Use paragraph renderer logic for inline styles
        paragraph_renderer = ParagraphRenderer()
        spans = paragraph_renderer._build_text_spans(
            block.text,
            content.inline_styles.get(block.id, []),
            [e for e in content.entities if e.block_id == block.id],
            selection
        )
        
        # Override size for all spans
        for span in spans:
            if isinstance(span, ft.Text):
                span.size = size_map.get(level, 20)
                span.weight = ft.FontWeight.BOLD
        
        return ft.Container(
            content=ft.Row(controls=spans, wrap=True),
            padding=ft.padding.only(top=16, bottom=12),
            data={"block_id": block.id, "block_type": f"heading-{level}"}
        )

class ListRenderer(BlockRenderer):
    """Render list items"""
    
    def render(
        self,
        block: ContentBlock,
        content: EditorContent,
        selection: Optional[Selection]
    ) -> ft.Control:
        """Render list item with bullet/number"""
        
        list_type = block.attributes.get("list_type", "unordered")
        list_index = block.attributes.get("index", 1)
        indent_level = block.attributes.get("indent", 0)
        
        # Create bullet/number
        if list_type == "unordered":
            marker = "•"
        elif list_type == "ordered":
            marker = f"{list_index}."
        else:  # checklist
            checked = block.attributes.get("checked", False)
            marker = ft.Checkbox(
                value=checked,
                on_change=lambda e: self._toggle_checklist(block.id, e.control.value)
            )
        
        # Render text content
        paragraph_renderer = ParagraphRenderer()
        text_content = paragraph_renderer.render(block, content, selection)
        
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=marker if isinstance(marker, ft.Control) else ft.Text(marker),
                    width=30,
                    alignment=ft.alignment.center_right
                ),
                ft.Container(
                    content=text_content,
                    expand=True
                )
            ]),
            padding=ft.padding.only(left=indent_level * 20),
            data={"block_id": block.id, "block_type": "list-item"}
        )
```

**Performance Optimizations:**
```python
class VirtualRenderer:
    """
    CLAUDE.md #1.5: Virtual rendering for large documents
    """
    
    def __init__(self, viewport_height: int, overscan: int = 100):
        self.viewport_height = viewport_height
        self.overscan = overscan
        self.block_heights: Dict[str, int] = {}
        self.block_positions: Dict[str, int] = {}
        
    def calculate_visible_blocks(
        self,
        blocks: List[ContentBlock],
        scroll_top: int
    ) -> Tuple[List[ContentBlock], int, int]:
        """Calculate which blocks are visible"""
        
        visible_blocks = []
        current_y = 0
        start_index = None
        end_index = None
        
        viewport_top = scroll_top - self.overscan
        viewport_bottom = scroll_top + self.viewport_height + self.overscan
        
        for i, block in enumerate(blocks):
            block_height = self._estimate_block_height(block)
            self.block_positions[block.id] = current_y
            
            if current_y + block_height >= viewport_top and current_y <= viewport_bottom:
                if start_index is None:
                    start_index = i
                end_index = i
                visible_blocks.append(block)
            elif current_y > viewport_bottom:
                break
            
            current_y += block_height
        
        return visible_blocks, start_index or 0, end_index or 0
    
    def _estimate_block_height(self, block: ContentBlock) -> int:
        """Estimate block height for virtual scrolling"""
        
        # Use cached height if available
        if block.id in self.block_heights:
            return self.block_heights[block.id]
        
        # Estimate based on content
        base_height = 40  # Minimum block height
        
        if block.type == BlockType.PARAGRAPH:
            # Estimate based on text length and line wrapping
            chars_per_line = 80
            lines = max(1, len(block.text) / chars_per_line)
            height = base_height + (lines - 1) * 20
        elif block.type == BlockType.HEADING:
            level = block.attributes.get("level", 2)
            height = 60 - (level - 1) * 5
        elif block.type == BlockType.IMAGE:
            height = block.attributes.get("height", 300)
        else:
            height = base_height
        
        self.block_heights[block.id] = int(height)
        return int(height)
```

**Unblocks:** [A-2-T1]
**Confidence Score:** High (3)

---

### USER STORY A-2: Toolbar and Commands

**ID & Title:** A-2: Implement Editor Toolbar System
**User Persona Narrative:** As a content creator, I want easy access to formatting tools
**Business Value:** High (3)
**Priority Score:** 4
**Story Points:** M

---

#### TASK A-2-T1: Implement Toolbar and Command System

**Goal:** Create flexible toolbar with command execution

**Token Budget:** 8,000 tokens

**Command System:**
```python
class EditorCommand(Enum):
    """
    CLAUDE.md #4.1: Explicit command types
    """
    # Text formatting
    BOLD = auto()
    ITALIC = auto()
    UNDERLINE = auto()
    STRIKETHROUGH = auto()
    
    # Block formatting
    HEADING_1 = auto()
    HEADING_2 = auto()
    HEADING_3 = auto()
    PARAGRAPH = auto()
    BLOCKQUOTE = auto()
    CODE_BLOCK = auto()
    
    # Lists
    UNORDERED_LIST = auto()
    ORDERED_LIST = auto()
    CHECKLIST = auto()
    INDENT = auto()
    OUTDENT = auto()
    
    # Insert
    INSERT_LINK = auto()
    INSERT_IMAGE = auto()
    INSERT_TABLE = auto()
    INSERT_HORIZONTAL_RULE = auto()
    
    # Alignment
    ALIGN_LEFT = auto()
    ALIGN_CENTER = auto()
    ALIGN_RIGHT = auto()
    ALIGN_JUSTIFY = auto()
    
    # History
    UNDO = auto()
    REDO = auto()
    
    # Other
    CLEAR_FORMATTING = auto()
    FIND_REPLACE = auto()

class CommandExecutor:
    """
    CLAUDE.md #3.3: Command pattern implementation
    CLAUDE.md #2.1.2: Comprehensive command handling
    """
    
    def __init__(self, state_manager: EditorStateManager):
        self.state_manager = state_manager
        self.command_handlers: Dict[EditorCommand, CommandHandler] = {}
        self._register_handlers()
    
    def execute(
        self,
        command: EditorCommand,
        value: Optional[Any] = None
    ) -> bool:
        """
        Execute editor command
        Returns True if handled
        """
        handler = self.command_handlers.get(command)
        if not handler:
            logger.warning(f"No handler for command: {command}")
            return False
        
        try:
            # Check if command is enabled
            if not handler.is_enabled(self.state_manager.state):
                logger.info(f"Command {command} is disabled")
                return False
            
            # Execute command
            operation = handler.create_operation(
                self.state_manager.state,
                value
            )
            
            if operation:
                self.state_manager.apply_operation(operation)
                
                # Log command execution
                logger.info(
                    f"Executed command",
                    extra={
                        "command": command.name,
                        "has_value": value is not None
                    }
                )
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Command execution failed: {e}", exc_info=True)
            return False
    
    def _register_handlers(self):
        """Register all command handlers"""
        
        # Text formatting
        self.command_handlers[EditorCommand.BOLD] = ToggleStyleHandler(StyleType.BOLD)
        self.command_handlers[EditorCommand.ITALIC] = ToggleStyleHandler(StyleType.ITALIC)
        self.command_handlers[EditorCommand.UNDERLINE] = ToggleStyleHandler(StyleType.UNDERLINE)
        
        # Block formatting
        self.command_handlers[EditorCommand.PARAGRAPH] = ChangeBlockTypeHandler(BlockType.PARAGRAPH)
        self.command_handlers[EditorCommand.HEADING_1] = ChangeBlockTypeHandler(
            BlockType.HEADING,
            {"level": 1}
        )
        
        # History
        self.command_handlers[EditorCommand.UNDO] = UndoHandler()
        self.command_handlers[EditorCommand.REDO] = RedoHandler()
        
        # ... register more handlers

class EditorToolbar:
    """
    CLAUDE.md #9.1: Accessible toolbar
    """
    
    def __init__(
        self,
        config: ToolbarConfig,
        command_executor: CommandExecutor,
        state_manager: EditorStateManager
    ):
        self.config = config
        self.command_executor = command_executor
        self.state_manager = state_manager
        self.groups: List[ToolbarGroup] = []
        self.items: Dict[EditorCommand, ToolbarItem] = {}
        
    def build(self) -> ft.Control:
        """Build toolbar UI"""
        
        toolbar_content = []
        
        for group_config in self.config.groups:
            if toolbar_content:  # Add separator between groups
                toolbar_content.append(self._create_separator())
            
            group_items = []
            for item_config in group_config.items:
                item = self._create_toolbar_item(item_config)
                if item:
                    group_items.append(item)
                    if item_config.command:
                        self.items[item_config.command] = item
            
            toolbar_content.extend(group_items)
        
        # Subscribe to state changes
        self.state_manager.add_listener(self._update_toolbar_state)
        
        return ft.Container(
            content=ft.Row(
                controls=toolbar_content,
                spacing=4
            ),
            bgcolor="#F5F5F5",
            padding=8,
            border_radius=4,
            height=48
        )
    
    def _create_toolbar_item(self, config: ToolbarItemConfig) -> Optional[ft.Control]:
        """Create individual toolbar item"""
        
        if config.type == ToolbarItemType.BUTTON:
            return self._create_button(config)
        elif config.type == ToolbarItemType.DROPDOWN:
            return self._create_dropdown(config)
        elif config.type == ToolbarItemType.COLOR_PICKER:
            return self._create_color_picker(config)
        
        return None
    
    def _create_button(self, config: ToolbarItemConfig) -> ft.Control:
        """
        Create toolbar button
        CLAUDE.md #9.3: Keyboard shortcuts
        """
        button = ft.IconButton(
            icon=config.icon,
            tooltip=f"{config.tooltip} ({config.shortcut})" if config.shortcut else config.tooltip,
            on_click=lambda e: self.command_executor.execute(config.command),
            icon_size=20,
            style=ft.ButtonStyle(
                padding=8,
            ),
            data={"command": config.command}
        )
        
        # Add keyboard shortcut
        if config.shortcut:
            self._register_shortcut(config.shortcut, config.command)
        
        return button
    
    def _update_toolbar_state(self, state: EditorState):
        """Update toolbar to reflect current state"""
        
        # Update toggle buttons
        for command, item in self.items.items():
            if isinstance(item, ft.IconButton):
                # Check if command represents active state
                is_active = self._is_command_active(command, state)
                
                # Update button appearance
                if is_active:
                    item.bgcolor = "#E3E4E6"
                    item.icon_color = "#5E6AD2"
                else:
                    item.bgcolor = None
                    item.icon_color = None
                
                item.update()
```

**Toolbar Configuration:**
```python
@dataclass
class ToolbarConfig:
    """
    CLAUDE.md #1.4: Extensible toolbar configuration
    """
    groups: List[ToolbarGroupConfig] = field(default_factory=list)
    
    @classmethod
    def default(cls) -> ToolbarConfig:
        """Get default toolbar configuration"""
        return cls(groups=[
            ToolbarGroupConfig(
                name="history",
                items=[
                    ToolbarItemConfig(
                        type=ToolbarItemType.BUTTON,
                        command=EditorCommand.UNDO,
                        icon=ft.icons.UNDO,
                        tooltip="Undo",
                        shortcut="Ctrl+Z"
                    ),
                    ToolbarItemConfig(
                        type=ToolbarItemType.BUTTON,
                        command=EditorCommand.REDO,
                        icon=ft.icons.REDO,
                        tooltip="Redo",
                        shortcut="Ctrl+Y"
                    )
                ]
            ),
            ToolbarGroupConfig(
                name="formatting",
                items=[
                    ToolbarItemConfig(
                        type=ToolbarItemType.BUTTON,
                        command=EditorCommand.BOLD,
                        icon=ft.icons.FORMAT_BOLD,
                        tooltip="Bold",
                        shortcut="Ctrl+B"
                    ),
                    ToolbarItemConfig(
                        type=ToolbarItemType.BUTTON,
                        command=EditorCommand.ITALIC,
                        icon=ft.icons.FORMAT_ITALIC,
                        tooltip="Italic",
                        shortcut="Ctrl+I"
                    ),
                    ToolbarItemConfig(
                        type=ToolbarItemType.BUTTON,
                        command=EditorCommand.UNDERLINE,
                        icon=ft.icons.FORMAT_UNDERLINED,
                        tooltip="Underline",
                        shortcut="Ctrl+U"
                    )
                ]
            ),
            ToolbarGroupConfig(
                name="blocks",
                items=[
                    ToolbarItemConfig(
                        type=ToolbarItemType.DROPDOWN,
                        command=None,
                        options=[
                            DropdownOption("Paragraph", EditorCommand.PARAGRAPH),
                            DropdownOption("Heading 1", EditorCommand.HEADING_1),
                            DropdownOption("Heading 2", EditorCommand.HEADING_2),
                            DropdownOption("Heading 3", EditorCommand.HEADING_3),
                            DropdownOption("Quote", EditorCommand.BLOCKQUOTE),
                            DropdownOption("Code", EditorCommand.CODE_BLOCK)
                        ],
                        tooltip="Block type"
                    )
                ]
            )
        ])
```

**Unblocks:** [B-1-T1]
**Confidence Score:** High (3)

---

## EPIC B: Advanced Features and Plugins

Implement media handling, plugins, and serialization.

**Definition of Done:**
- ✓ Image/video embedding working
- ✓ Plugin system functional
- ✓ HTML/Markdown conversion accurate
- ✓ Performance optimized

**Business Value:** Full-featured rich text editing

---

### Technical Debt Management

```yaml
# Rich Text Editor Debt Tracking
editor_debt:
  items:
    - id: RTE-001
      description: "Implement collaborative editing with CRDTs"
      impact: "Enable real-time collaboration"
      effort: "XL"
      priority: 1
      
    - id: RTE-002
      description: "Add virtual scrolling for large documents"
      impact: "Better performance with 100+ page documents"
      effort: "L"
      priority: 2
      
    - id: RTE-003
      description: "Create custom block plugin API"
      impact: "Third-party block types"
      effort: "M"
      priority: 3
```

---

## Testing Strategy

### Unit Tests
```python
def test_text_insertion():
    """CLAUDE.md #6.2: Test text operations"""
    state = EditorState()
    state.content.blocks = [ContentBlock(id="b1", text="Hello")]
    
    operation = InsertTextOperation(
        block_id="b1",
        offset=5,
        text=" World"
    )
    
    operation.apply(state)
    
    assert state.content.blocks[0].text == "Hello World"

def test_style_application():
    """Test inline style application"""
    state = EditorState()
    block = ContentBlock(id="b1", text="Hello World")
    state.content.blocks = [block]
    
    # Apply bold to "World"
    operation = FormatTextOperation(
        block_id="b1",
        start=6,
        end=11,
        style=StyleType.BOLD
    )
    
    operation.apply(state)
    
    styles = state.content.inline_styles["b1"]
    assert len(styles) == 1
    assert styles[0].offset == 6
    assert styles[0].length == 5
    assert styles[0].style == StyleType.BOLD
```

### Integration Tests
```python
@pytest.mark.integration
async def test_complete_editing_flow():
    """Test full editing workflow"""
    
    # Initialize editor
    editor = RichTextEditor()
    
    # Type text
    await editor.insert_text("Hello World")
    
    # Select "World"
    editor.set_selection(6, 11)
    
    # Apply bold
    editor.execute_command(EditorCommand.BOLD)
    
    # Get HTML output
    html = editor.get_html()
    assert "Hello <strong>World</strong>" in html
```

---

## Performance Optimization

```python
class EditorOptimizations:
    """CLAUDE.md #1.5: Performance optimizations"""
    
    @staticmethod
    def debounce_operations(delay: float = 0.3):
        """Debounce rapid operations"""
        def decorator(func):
            timer = None
            
            def debounced(*args, **kwargs):
                nonlocal timer
                if timer:
                    timer.cancel()
                timer = Timer(delay, lambda: func(*args, **kwargs))
                timer.start()
            
            return debounced
        return decorator
    
    @staticmethod
    def batch_style_operations(operations: List[FormatTextOperation]) -> FormatTextOperation:
        """Batch multiple format operations"""
        if not operations:
            return None
        
        # Group by block and style
        grouped = defaultdict(list)
        for op in operations:
            key = (op.block_id, op.style, op.value)
            grouped[key].append(op)
        
        # Merge ranges
        batched = []
        for (block_id, style, value), ops in grouped.items():
            ranges = [(op.start, op.end) for op in ops]
            merged_ranges = merge_ranges(ranges)
            
            for start, end in merged_ranges:
                batched.append(FormatTextOperation(
                    block_id=block_id,
                    start=start,
                    end=end,
                    style=style,
                    value=value
                ))
        
        return batched
```

---

## Security Checklist

- [ ] Sanitize all HTML input/output
- [ ] Validate file uploads (type, size)
- [ ] Escape special characters in text
- [ ] Validate URLs in links
- [ ] Prevent script injection
- [ ] Limit paste content size

---

## Rich Text Editor Architecture Summary

1. **Document Model**: Block-based with inline styles
2. **State Management**: Centralized with operations
3. **Rendering**: Efficient with virtual scrolling
4. **Commands**: Flexible command/toolbar system
5. **Plugins**: Extensible architecture
6. **Serialization**: HTML/Markdown conversion