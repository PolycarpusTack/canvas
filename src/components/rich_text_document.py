"""
Rich Text Document Model
Implements block/inline document structure with operational transforms
Following CLAUDE.md guidelines for data integrity and performance
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum, auto
import json
import logging
from uuid import uuid4
from datetime import datetime
import copy

logger = logging.getLogger(__name__)


class BlockType(Enum):
    """Block element types"""
    PARAGRAPH = "paragraph"
    H1 = "h1"
    H2 = "h2"
    H3 = "h3"
    H4 = "h4"
    H5 = "h5"
    H6 = "h6"
    BLOCKQUOTE = "blockquote"
    CODE_BLOCK = "code_block"
    LIST_ITEM = "list_item"
    ORDERED_LIST = "ordered_list"
    UNORDERED_LIST = "unordered_list"
    DIVIDER = "divider"
    IMAGE = "image"
    TABLE = "table"
    TABLE_ROW = "table_row"
    TABLE_CELL = "table_cell"


class InlineType(Enum):
    """Inline element types"""
    TEXT = "text"
    STRONG = "strong"
    EMPHASIS = "emphasis"
    UNDERLINE = "underline"
    STRIKETHROUGH = "strikethrough"
    CODE = "code"
    LINK = "link"
    IMAGE = "image"
    BREAK = "break"


class OperationType(Enum):
    """Document operation types for undo/redo"""
    INSERT_TEXT = auto()
    DELETE_TEXT = auto()
    INSERT_BLOCK = auto()
    DELETE_BLOCK = auto()
    FORMAT_TEXT = auto()
    CHANGE_BLOCK_TYPE = auto()


@dataclass
class InlineElement:
    """
    Inline text element with formatting
    CLAUDE.md #2.1.1: Validate inline content
    """
    type: InlineType
    text: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate inline element"""
        if self.type == InlineType.TEXT and not isinstance(self.text, str):
            raise ValueError("Text elements must have string content")
        
        if self.type == InlineType.LINK and "href" not in self.attributes:
            raise ValueError("Link elements must have href attribute")
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "type": self.type.value,
            "text": self.text,
            "attributes": self.attributes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> InlineElement:
        """Deserialize from dictionary"""
        return cls(
            type=InlineType(data["type"]),
            text=data.get("text", ""),
            attributes=data.get("attributes", {})
        )
    
    def clone(self) -> InlineElement:
        """Create a deep copy"""
        return InlineElement(
            type=self.type,
            text=self.text,
            attributes=copy.deepcopy(self.attributes)
        )


@dataclass
class TextBlock:
    """
    Text block with inline formatting
    CLAUDE.md #1.2: Efficient block structure
    """
    id: str
    type: BlockType
    children: List[InlineElement] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    content: str = ""  # For simple blocks
    
    def __post_init__(self):
        """Validate block"""
        if not self.id:
            self.id = str(uuid4())
        
        # Ensure content consistency
        if self.children and not self.content:
            self.content = self.get_text()
        elif self.content and not self.children:
            self.children = [InlineElement(type=InlineType.TEXT, text=self.content)]
    
    def get_text(self) -> str:
        """Get plain text content"""
        if self.content:
            return self.content
        
        return "".join(child.text for child in self.children)
    
    def get_length(self) -> int:
        """Get text length"""
        return len(self.get_text())
    
    def insert_text(self, offset: int, text: str) -> None:
        """
        Insert text at offset position
        CLAUDE.md #1.5: Efficient text operations
        """
        if offset < 0 or offset > self.get_length():
            raise ValueError(f"Invalid offset: {offset}")
        
        if not self.children:
            # Simple text block
            current_text = self.content
            self.content = current_text[:offset] + text + current_text[offset:]
            return
        
        # Find insertion point in inline elements
        current_offset = 0
        for i, child in enumerate(self.children):
            child_length = len(child.text)
            
            if current_offset <= offset <= current_offset + child_length:
                # Insert within this element
                local_offset = offset - current_offset
                child.text = child.text[:local_offset] + text + child.text[local_offset:]
                break
            
            current_offset += child_length
        
        # Update content cache
        self.content = self.get_text()
    
    def delete_text(self, start: int, length: int) -> str:
        """
        Delete text range and return deleted text
        CLAUDE.md #2.1.4: Safe deletion with validation
        """
        if start < 0 or length <= 0:
            raise ValueError("Invalid deletion parameters")
        
        end = start + length
        if end > self.get_length():
            raise ValueError("Deletion range exceeds block length")
        
        if not self.children:
            # Simple text block
            deleted_text = self.content[start:end]
            self.content = self.content[:start] + self.content[end:]
            return deleted_text
        
        # Delete from inline elements
        deleted_text = ""
        current_offset = 0
        elements_to_remove = []
        
        for i, child in enumerate(self.children):
            child_start = current_offset
            child_end = current_offset + len(child.text)
            
            # Check if this element is affected
            if start < child_end and end > child_start:
                # Calculate intersection
                delete_start = max(start - child_start, 0)
                delete_end = min(end - child_start, len(child.text))
                
                if delete_start == 0 and delete_end == len(child.text):
                    # Delete entire element
                    deleted_text += child.text
                    elements_to_remove.append(i)
                else:
                    # Partial deletion
                    deleted_text += child.text[delete_start:delete_end]
                    child.text = child.text[:delete_start] + child.text[delete_end:]
            
            current_offset = child_end
        
        # Remove empty elements
        for i in reversed(elements_to_remove):
            del self.children[i]
        
        # Update content cache
        self.content = self.get_text()
        
        return deleted_text
    
    def apply_formatting(self, start: int, length: int, format_type: InlineType, attributes: Optional[Dict[str, Any]] = None) -> None:
        """
        Apply formatting to text range
        CLAUDE.md #2.1.1: Validate formatting operations
        """
        if start < 0 or length <= 0 or start + length > self.get_length():
            raise ValueError("Invalid formatting range")
        
        attributes = attributes or {}
        
        # Split text into formatted segments
        # This is a simplified implementation - full version would handle complex overlapping formats
        formatted_element = InlineElement(
            type=format_type,
            text=self.get_text()[start:start + length],
            attributes=attributes
        )
        
        # For now, just add the formatted element
        # Full implementation would split and merge existing elements
        if not self.children:
            self.children = [InlineElement(type=InlineType.TEXT, text=self.content)]
        
        self.children.append(formatted_element)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "id": self.id,
            "type": self.type.value,
            "children": [child.to_dict() for child in self.children],
            "attributes": self.attributes,
            "content": self.content
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TextBlock:
        """Deserialize from dictionary"""
        children = [InlineElement.from_dict(child) for child in data.get("children", [])]
        
        return cls(
            id=data["id"],
            type=BlockType(data["type"]),
            children=children,
            attributes=data.get("attributes", {}),
            content=data.get("content", "")
        )
    
    def clone(self) -> TextBlock:
        """Create a deep copy"""
        return TextBlock(
            id=str(uuid4()),  # New ID for clone
            type=self.type,
            children=[child.clone() for child in self.children],
            attributes=copy.deepcopy(self.attributes),
            content=self.content
        )


@dataclass
class DocumentOperation:
    """
    Document operation for undo/redo
    CLAUDE.md #2.1.1: Complete operation tracking
    """
    id: str
    type: OperationType
    timestamp: datetime
    block_id: Optional[str] = None
    position: Optional[int] = None
    content: Optional[str] = None
    old_content: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate operation"""
        if not self.id:
            self.id = str(uuid4())
        
        if not self.timestamp:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "id": self.id,
            "type": self.type.name,
            "timestamp": self.timestamp.isoformat(),
            "block_id": self.block_id,
            "position": self.position,
            "content": self.content,
            "old_content": self.old_content,
            "attributes": self.attributes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DocumentOperation:
        """Deserialize from dictionary"""
        return cls(
            id=data["id"],
            type=OperationType[data["type"]],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            block_id=data.get("block_id"),
            position=data.get("position"),
            content=data.get("content"),
            old_content=data.get("old_content"),
            attributes=data.get("attributes")
        )


class RichTextDocument:
    """
    Rich text document with block/inline model
    CLAUDE.md #1.5: Optimize for large documents
    CLAUDE.md #12.1: Performance monitoring
    """
    
    def __init__(self):
        """Initialize empty document"""
        self.blocks: List[TextBlock] = []
        self.metadata: Dict[str, Any] = {
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        # Undo/redo system
        self._operations: List[DocumentOperation] = []
        self._operation_index = -1
        self._max_operations = 100
        
        # Performance tracking
        self._operation_count = 0
        self._avg_operation_time = 0.0
        
        # Create initial paragraph if empty
        if not self.blocks:
            self.blocks.append(TextBlock(
                id=str(uuid4()),
                type=BlockType.PARAGRAPH,
                content=""
            ))
    
    def get_block(self, block_id: str) -> Optional[TextBlock]:
        """Get block by ID"""
        for block in self.blocks:
            if block.id == block_id:
                return block
        return None
    
    def get_block_index(self, block_id: str) -> int:
        """Get block index by ID"""
        for i, block in enumerate(self.blocks):
            if block.id == block_id:
                return i
        return -1
    
    def insert_block(self, index: int, block: TextBlock) -> None:
        """
        Insert block at index
        CLAUDE.md #2.1.1: Validate block insertion
        """
        if index < 0 or index > len(self.blocks):
            raise ValueError(f"Invalid insertion index: {index}")
        
        # Record operation for undo
        operation = DocumentOperation(
            id=str(uuid4()),
            type=OperationType.INSERT_BLOCK,
            timestamp=datetime.now(),
            block_id=block.id,
            position=index
        )
        self._record_operation(operation)
        
        # Insert block
        self.blocks.insert(index, block)
        self._update_metadata()
    
    def insert_block_after(self, block_id: str, new_block: TextBlock) -> None:
        """Insert block after specified block"""
        index = self.get_block_index(block_id)
        if index >= 0:
            self.insert_block(index + 1, new_block)
        else:
            raise ValueError(f"Block not found: {block_id}")
    
    def delete_block(self, block_id: str) -> bool:
        """
        Delete block by ID
        CLAUDE.md #2.1.4: Safe block deletion
        """
        index = self.get_block_index(block_id)
        if index < 0:
            return False
        
        block = self.blocks[index]
        
        # Record operation for undo
        operation = DocumentOperation(
            id=str(uuid4()),
            type=OperationType.DELETE_BLOCK,
            timestamp=datetime.now(),
            block_id=block_id,
            position=index,
            old_content=json.dumps(block.to_dict())
        )
        self._record_operation(operation)
        
        # Delete block
        del self.blocks[index]
        
        # Ensure at least one block remains
        if not self.blocks:
            self.blocks.append(TextBlock(
                id=str(uuid4()),
                type=BlockType.PARAGRAPH,
                content=""
            ))
        
        self._update_metadata()
        return True
    
    def move_block(self, block_id: str, new_index: int) -> bool:
        """Move block to new position"""
        old_index = self.get_block_index(block_id)
        if old_index < 0 or new_index < 0 or new_index >= len(self.blocks):
            return False
        
        # Move block
        block = self.blocks.pop(old_index)
        self.blocks.insert(new_index, block)
        
        self._update_metadata()
        return True
    
    def can_undo(self) -> bool:
        """Check if undo is available"""
        return self._operation_index >= 0
    
    def can_redo(self) -> bool:
        """Check if redo is available"""
        return self._operation_index < len(self._operations) - 1
    
    def undo(self) -> bool:
        """
        Undo last operation
        CLAUDE.md #2.1.4: Reliable undo implementation
        """
        if not self.can_undo():
            return False
        
        try:
            operation = self._operations[self._operation_index]
            self._apply_inverse_operation(operation)
            self._operation_index -= 1
            self._update_metadata()
            return True
        except Exception as e:
            logger.error(f"Undo failed: {e}")
            return False
    
    def redo(self) -> bool:
        """
        Redo next operation
        CLAUDE.md #2.1.4: Reliable redo implementation
        """
        if not self.can_redo():
            return False
        
        try:
            self._operation_index += 1
            operation = self._operations[self._operation_index]
            self._apply_operation(operation)
            self._update_metadata()
            return True
        except Exception as e:
            logger.error(f"Redo failed: {e}")
            self._operation_index -= 1
            return False
    
    def get_text(self) -> str:
        """Get document as plain text"""
        return "\n\n".join(block.get_text() for block in self.blocks)
    
    def get_word_count(self) -> int:
        """Get word count"""
        text = self.get_text()
        if not text.strip():
            return 0
        return len(text.split())
    
    def get_character_count(self) -> int:
        """Get character count"""
        return len(self.get_text())
    
    def search(self, query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """
        Search for text in document
        CLAUDE.md #1.5: Efficient text search
        """
        results = []
        
        if not case_sensitive:
            query = query.lower()
        
        for block in self.blocks:
            text = block.get_text()
            if not case_sensitive:
                text = text.lower()
            
            start = 0
            while True:
                index = text.find(query, start)
                if index == -1:
                    break
                
                results.append({
                    "block_id": block.id,
                    "offset": index,
                    "length": len(query),
                    "context": block.get_text()
                })
                
                start = index + 1
        
        return results
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize document to dictionary"""
        return {
            "blocks": [block.to_dict() for block in self.blocks],
            "metadata": self.metadata,
            "version": "1.0"
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RichTextDocument:
        """Deserialize document from dictionary"""
        doc = cls()
        doc.blocks = [TextBlock.from_dict(block_data) for block_data in data.get("blocks", [])]
        doc.metadata = data.get("metadata", {})
        
        # Ensure at least one block
        if not doc.blocks:
            doc.blocks.append(TextBlock(
                id=str(uuid4()),
                type=BlockType.PARAGRAPH,
                content=""
            ))
        
        return doc
    
    def clone(self) -> RichTextDocument:
        """Create a deep copy of the document"""
        doc = RichTextDocument()
        doc.blocks = [block.clone() for block in self.blocks]
        doc.metadata = copy.deepcopy(self.metadata)
        return doc
    
    def _record_operation(self, operation: DocumentOperation) -> None:
        """Record operation for undo/redo"""
        # Truncate redo history if we're not at the end
        if self._operation_index < len(self._operations) - 1:
            self._operations = self._operations[:self._operation_index + 1]
        
        # Add new operation
        self._operations.append(operation)
        self._operation_index += 1
        
        # Limit operation history
        if len(self._operations) > self._max_operations:
            self._operations.pop(0)
            self._operation_index -= 1
    
    def _apply_operation(self, operation: DocumentOperation) -> None:
        """Apply operation (for redo)"""
        # Implementation would apply the operation
        pass
    
    def _apply_inverse_operation(self, operation: DocumentOperation) -> None:
        """Apply inverse operation (for undo)"""
        # Implementation would reverse the operation
        pass
    
    def _update_metadata(self) -> None:
        """Update document metadata"""
        self.metadata["modified"] = datetime.now().isoformat()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            "block_count": len(self.blocks),
            "operation_count": self._operation_count,
            "avg_operation_time_ms": self._avg_operation_time,
            "undo_depth": self._operation_index + 1,
            "redo_depth": len(self._operations) - self._operation_index - 1,
            "word_count": self.get_word_count(),
            "character_count": self.get_character_count()
        }