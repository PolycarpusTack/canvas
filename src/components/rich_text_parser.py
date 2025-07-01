"""
HTML/Markdown Parser and Serializer for Rich Text Editor
Implements real content import/export with comprehensive sanitization
Following CLAUDE.md guidelines for secure content processing
"""

import re
import html
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum, auto

# Import BeautifulSoup for HTML parsing
try:
    from bs4 import BeautifulSoup, Tag, NavigableString
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    BeautifulSoup = None

# Import markdown for Markdown parsing
try:
    import markdown
    from markdown.extensions import codehilite, tables, fenced_code
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False
    markdown = None

# Import bleach for HTML sanitization
try:
    import bleach
    HAS_BLEACH = True
except ImportError:
    HAS_BLEACH = False
    bleach = None

from components.rich_text_editor_complete import RichTextDocument, TextBlock, FormatRange, FormatType

logger = logging.getLogger(__name__)


class ParseError(Exception):
    """Content parsing error"""
    pass


class SecurityError(Exception):
    """Content security validation error"""
    pass


@dataclass
class ParseConfig:
    """Configuration for content parsing"""
    # Security settings
    strip_dangerous_tags: bool = True
    allow_external_links: bool = False
    max_document_size: int = 10 * 1024 * 1024  # 10MB
    max_blocks: int = 10000
    
    # HTML parsing
    allowed_html_tags: List[str] = field(default_factory=lambda: [
        'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'strike', 'del',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'blockquote', 'pre', 'code',
        'ul', 'ol', 'li',
        'a', 'img',
        'table', 'thead', 'tbody', 'tr', 'td', 'th'
    ])
    
    allowed_html_attributes: Dict[str, List[str]] = field(default_factory=lambda: {
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
        'pre': ['class'],
        'code': ['class'],
        'table': ['class'],
        'blockquote': ['cite']
    })
    
    # Markdown parsing
    markdown_extensions: List[str] = field(default_factory=lambda: [
        'fenced_code',
        'tables',
        'codehilite',
        'nl2br',
        'toc'
    ])
    
    def __post_init__(self):
        """Validate configuration"""
        if self.max_document_size < 1024:
            raise ValueError("Maximum document size must be at least 1KB")
        
        if self.max_blocks < 1:
            raise ValueError("Maximum blocks must be at least 1")


class RichTextParser:
    """
    Complete HTML/Markdown parser with security validation
    CLAUDE.md #7.2: Secure content processing
    CLAUDE.md #2.1.1: Comprehensive input validation
    """
    
    def __init__(self, config: Optional[ParseConfig] = None):
        """Initialize parser with configuration"""
        self.config = config or ParseConfig()
        
        # Check dependencies
        if not HAS_BS4:
            logger.warning("BeautifulSoup not available - HTML parsing disabled")
        
        if not HAS_MARKDOWN:
            logger.warning("markdown library not available - Markdown parsing disabled")
        
        if not HAS_BLEACH:
            logger.warning("bleach library not available - HTML sanitization disabled")
        
        # Initialize markdown parser if available
        self._markdown_parser = None
        if HAS_MARKDOWN:
            try:
                self._markdown_parser = markdown.Markdown(
                    extensions=self.config.markdown_extensions,
                    extension_configs={
                        'codehilite': {
                            'css_class': 'highlight',
                            'use_pygments': True
                        }
                    }
                )
            except Exception as e:
                logger.error(f"Failed to initialize Markdown parser: {e}")
        
        logger.info("Rich text parser initialized")
    
    def parse_html(self, html_content: str) -> RichTextDocument:
        """
        Parse HTML content into rich text document
        CLAUDE.md #7.2: Safe HTML parsing with sanitization
        """
        try:
            if not HAS_BS4:
                raise ParseError("BeautifulSoup not available for HTML parsing")
            
            # Validate input size
            if len(html_content) > self.config.max_document_size:
                raise ParseError(f"HTML content exceeds maximum size ({self.config.max_document_size} bytes)")
            
            # Sanitize HTML if bleach is available
            if HAS_BLEACH and self.config.strip_dangerous_tags:
                html_content = self._sanitize_html(html_content)
            
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Create document
            document = RichTextDocument()
            document.blocks.clear()  # Remove default block
            
            # Process HTML elements
            self._process_html_elements(soup, document)
            
            # Ensure at least one block
            if not document.blocks:
                document.blocks.append(TextBlock(
                    id=str(uuid4()),
                    text="",
                    block_type="paragraph"
                ))
            
            # Validate result
            if len(document.blocks) > self.config.max_blocks:
                raise ParseError(f"Document exceeds maximum blocks ({self.config.max_blocks})")
            
            logger.info(f"Parsed HTML into {len(document.blocks)} blocks")
            return document
            
        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            raise ParseError(f"Failed to parse HTML: {e}")
    
    def parse_markdown(self, markdown_content: str) -> RichTextDocument:
        """
        Parse Markdown content into rich text document
        CLAUDE.md #2.1.1: Validate Markdown input
        """
        try:
            if not HAS_MARKDOWN:
                raise ParseError("Markdown library not available")
            
            # Validate input size
            if len(markdown_content) > self.config.max_document_size:
                raise ParseError(f"Markdown content exceeds maximum size ({self.config.max_document_size} bytes)")
            
            # Convert Markdown to HTML first
            if not self._markdown_parser:
                raise ParseError("Markdown parser not initialized")
            
            html_content = self._markdown_parser.convert(markdown_content)
            
            # Parse the resulting HTML
            return self.parse_html(html_content)
            
        except Exception as e:
            logger.error(f"Error parsing Markdown: {e}")
            raise ParseError(f"Failed to parse Markdown: {e}")
    
    def parse_plain_text(self, text_content: str) -> RichTextDocument:
        """Parse plain text into rich text document"""
        try:
            # Validate input size
            if len(text_content) > self.config.max_document_size:
                raise ParseError(f"Text content exceeds maximum size ({self.config.max_document_size} bytes)")
            
            # Create document
            document = RichTextDocument()
            document.blocks.clear()  # Remove default block
            
            # Split text into paragraphs
            paragraphs = text_content.split('\n\n')
            
            for paragraph in paragraphs:
                paragraph = paragraph.strip()
                if paragraph:  # Skip empty paragraphs
                    # Replace single newlines with spaces
                    paragraph = re.sub(r'\n', ' ', paragraph)
                    
                    document.blocks.append(TextBlock(
                        id=str(uuid4()),
                        text=paragraph,
                        block_type="paragraph"
                    ))
            
            # Ensure at least one block
            if not document.blocks:
                document.blocks.append(TextBlock(
                    id=str(uuid4()),
                    text="",
                    block_type="paragraph"
                ))
            
            # Validate result
            if len(document.blocks) > self.config.max_blocks:
                raise ParseError(f"Document exceeds maximum blocks ({self.config.max_blocks})")
            
            logger.info(f"Parsed plain text into {len(document.blocks)} blocks")
            return document
            
        except Exception as e:
            logger.error(f"Error parsing plain text: {e}")
            raise ParseError(f"Failed to parse plain text: {e}")
    
    def _sanitize_html(self, html_content: str) -> str:
        """
        Sanitize HTML content to remove dangerous elements
        CLAUDE.md #7.2: Comprehensive HTML sanitization
        """
        try:
            if not HAS_BLEACH:
                logger.warning("Bleach not available - skipping HTML sanitization")
                return html_content
            
            # Sanitize with bleach
            sanitized = bleach.clean(
                html_content,
                tags=self.config.allowed_html_tags,
                attributes=self.config.allowed_html_attributes,
                strip=True,
                strip_comments=True
            )
            
            # Additional custom sanitization
            sanitized = self._custom_sanitization(sanitized)
            
            return sanitized
            
        except Exception as e:
            logger.error(f"Error sanitizing HTML: {e}")
            return html.escape(html_content)  # Fallback to escaping
    
    def _custom_sanitization(self, content: str) -> str:
        """Apply custom sanitization rules"""
        try:
            # Remove javascript: URLs
            content = re.sub(r'javascript:[^"\']*', '', content, flags=re.IGNORECASE)
            
            # Remove data: URLs (except images if allowed)
            content = re.sub(r'data:(?!image/)[^"\']*', '', content, flags=re.IGNORECASE)
            
            # Validate external links if not allowed
            if not self.config.allow_external_links:
                # Replace external links with text
                content = re.sub(r'<a\s+href=["\']?https?://[^"\']*["\']?[^>]*>(.*?)</a>', r'\1', content, flags=re.IGNORECASE)
            
            return content
            
        except Exception as e:
            logger.error(f"Error in custom sanitization: {e}")
            return content
    
    def _process_html_elements(self, soup: BeautifulSoup, document: RichTextDocument) -> None:
        """Process HTML elements into document blocks"""
        try:
            # Find all block-level elements
            block_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'pre', 'div'])
            
            if not block_elements:
                # No block elements found, treat as single paragraph
                text_content = soup.get_text().strip()
                if text_content:
                    document.blocks.append(TextBlock(
                        id=str(uuid4()),
                        text=text_content,
                        block_type="paragraph"
                    ))
                return
            
            # Process each block element
            for element in block_elements:
                block = self._process_html_block(element)
                if block:
                    document.blocks.append(block)
            
        except Exception as e:
            logger.error(f"Error processing HTML elements: {e}")
            raise
    
    def _process_html_block(self, element: Tag) -> Optional[TextBlock]:
        """Process a single HTML block element"""
        try:
            # Determine block type
            tag_name = element.name.lower()
            
            if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                block_type = tag_name
            elif tag_name == 'blockquote':
                block_type = 'blockquote'
            elif tag_name == 'pre':
                block_type = 'code_block'
            else:
                block_type = 'paragraph'
            
            # Extract text and formatting
            text_content, formats = self._extract_text_and_formats(element)
            
            if not text_content.strip():
                return None  # Skip empty blocks
            
            # Create block
            from uuid import uuid4
            block = TextBlock(
                id=str(uuid4()),
                text=text_content,
                block_type=block_type,
                formats=formats
            )
            
            return block
            
        except Exception as e:
            logger.error(f"Error processing HTML block: {e}")
            return None
    
    def _extract_text_and_formats(self, element: Tag) -> Tuple[str, List[FormatRange]]:
        """Extract text content and formatting from HTML element"""
        try:
            text_content = ""
            formats = []
            
            # Process all child nodes
            for child in element.children:
                if isinstance(child, NavigableString):
                    # Plain text
                    text_content += str(child)
                elif isinstance(child, Tag):
                    # Formatted text
                    child_text = child.get_text()
                    start_pos = len(text_content)
                    text_content += child_text
                    end_pos = len(text_content)
                    
                    # Determine format type
                    format_type = self._get_format_type_from_tag(child)
                    if format_type:
                        formats.append(FormatRange(
                            start=start_pos,
                            end=end_pos,
                            format_type=format_type,
                            value=self._get_format_value_from_tag(child, format_type)
                        ))
            
            return text_content, formats
            
        except Exception as e:
            logger.error(f"Error extracting text and formats: {e}")
            return "", []
    
    def _get_format_type_from_tag(self, tag: Tag) -> Optional[FormatType]:
        """Get format type from HTML tag"""
        tag_name = tag.name.lower()
        
        format_map = {
            'strong': FormatType.BOLD,
            'b': FormatType.BOLD,
            'em': FormatType.ITALIC,
            'i': FormatType.ITALIC,
            'u': FormatType.UNDERLINE,
            'strike': FormatType.STRIKETHROUGH,
            'del': FormatType.STRIKETHROUGH,
            'code': FormatType.CODE,
            'a': FormatType.LINK
        }
        
        return format_map.get(tag_name)
    
    def _get_format_value_from_tag(self, tag: Tag, format_type: FormatType) -> Optional[str]:
        """Get format value from HTML tag (e.g., URL for links)"""
        if format_type == FormatType.LINK:
            return tag.get('href')
        return None


class RichTextSerializer:
    """
    Complete rich text document serializer
    CLAUDE.md #1.4: Support multiple output formats
    """
    
    def __init__(self):
        """Initialize serializer"""
        self._markdown_available = HAS_MARKDOWN
        logger.info("Rich text serializer initialized")
    
    def to_html(self, document: RichTextDocument, include_styles: bool = True) -> str:
        """
        Export document as HTML
        CLAUDE.md #7.2: Generate safe HTML output
        """
        try:
            html_parts = []
            
            if include_styles:
                html_parts.append(self._get_html_styles())
            
            for block in document.blocks:
                html_parts.append(self._block_to_html(block))
            
            return '\n'.join(html_parts)
            
        except Exception as e:
            logger.error(f"Error exporting to HTML: {e}")
            return f"<!-- Error exporting to HTML: {e} -->"
    
    def to_markdown(self, document: RichTextDocument) -> str:
        """
        Export document as Markdown
        CLAUDE.md #1.4: Clean Markdown output
        """
        try:
            markdown_parts = []
            
            for block in document.blocks:
                markdown_parts.append(self._block_to_markdown(block))
            
            # Join with double newlines for proper block separation
            return '\n\n'.join(filter(None, markdown_parts))
            
        except Exception as e:
            logger.error(f"Error exporting to Markdown: {e}")
            return f"<!-- Error exporting to Markdown: {e} -->"
    
    def to_plain_text(self, document: RichTextDocument) -> str:
        """Export document as plain text"""
        try:
            text_parts = []
            
            for block in document.blocks:
                text_parts.append(block.text)
            
            return '\n\n'.join(filter(None, text_parts))
            
        except Exception as e:
            logger.error(f"Error exporting to plain text: {e}")
            return f"Error exporting to plain text: {e}"
    
    def to_json(self, document: RichTextDocument) -> str:
        """Export document as JSON"""
        try:
            import json
            return json.dumps(document.to_dict(), indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            return f'{{"error": "Failed to export to JSON: {e}"}}'
    
    def _get_html_styles(self) -> str:
        """Get default HTML styles"""
        return """<style>
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }
h1, h2, h3, h4, h5, h6 { margin-top: 24px; margin-bottom: 16px; font-weight: 600; line-height: 1.25; }
h1 { font-size: 2em; border-bottom: 1px solid #eaecef; padding-bottom: 10px; }
h2 { font-size: 1.5em; }
h3 { font-size: 1.25em; }
p { margin-bottom: 16px; }
blockquote { margin: 0; padding: 0 16px; color: #6a737d; border-left: 4px solid #dfe2e5; }
pre, code { font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace; }
pre { padding: 16px; overflow: auto; background-color: #f6f8fa; border-radius: 6px; }
code { padding: 2px 4px; background-color: rgba(175,184,193,0.2); border-radius: 3px; }
a { color: #0366d6; text-decoration: none; }
a:hover { text-decoration: underline; }
strong, b { font-weight: 600; }
em, i { font-style: italic; }
u { text-decoration: underline; }
strike, del { text-decoration: line-through; }
</style>"""
    
    def _block_to_html(self, block: TextBlock) -> str:
        """Convert text block to HTML"""
        try:
            # Apply inline formatting
            formatted_text = self._apply_html_formatting(block.text, block.formats)
            
            # Wrap in appropriate block tag
            if block.block_type.startswith('h') and len(block.block_type) == 2:
                return f"<{block.block_type}>{formatted_text}</{block.block_type}>"
            elif block.block_type == 'blockquote':
                return f"<blockquote><p>{formatted_text}</p></blockquote>"
            elif block.block_type == 'code_block':
                return f"<pre><code>{html.escape(block.text)}</code></pre>"
            else:  # paragraph
                return f"<p>{formatted_text}</p>"
                
        except Exception as e:
            logger.error(f"Error converting block to HTML: {e}")
            return f"<p>{html.escape(block.text)}</p>"
    
    def _block_to_markdown(self, block: TextBlock) -> str:
        """Convert text block to Markdown"""
        try:
            # Apply inline formatting
            formatted_text = self._apply_markdown_formatting(block.text, block.formats)
            
            # Apply block formatting
            if block.block_type == 'h1':
                return f"# {formatted_text}"
            elif block.block_type == 'h2':
                return f"## {formatted_text}"
            elif block.block_type == 'h3':
                return f"### {formatted_text}"
            elif block.block_type == 'h4':
                return f"#### {formatted_text}"
            elif block.block_type == 'h5':
                return f"##### {formatted_text}"
            elif block.block_type == 'h6':
                return f"###### {formatted_text}"
            elif block.block_type == 'blockquote':
                return f"> {formatted_text}"
            elif block.block_type == 'code_block':
                return f"```\n{block.text}\n```"
            else:  # paragraph
                return formatted_text
                
        except Exception as e:
            logger.error(f"Error converting block to Markdown: {e}")
            return block.text
    
    def _apply_html_formatting(self, text: str, formats: List[FormatRange]) -> str:
        """Apply inline formatting to text for HTML output"""
        try:
            if not formats:
                return html.escape(text)
            
            # Sort formats by start position
            sorted_formats = sorted(formats, key=lambda f: (f.start, -f.end))
            
            result = ""
            last_pos = 0
            
            for fmt in sorted_formats:
                # Add text before format
                result += html.escape(text[last_pos:fmt.start])
                
                # Add formatted text
                formatted_text = html.escape(text[fmt.start:fmt.end])
                
                if fmt.format_type == FormatType.BOLD:
                    formatted_text = f"<strong>{formatted_text}</strong>"
                elif fmt.format_type == FormatType.ITALIC:
                    formatted_text = f"<em>{formatted_text}</em>"
                elif fmt.format_type == FormatType.UNDERLINE:
                    formatted_text = f"<u>{formatted_text}</u>"
                elif fmt.format_type == FormatType.STRIKETHROUGH:
                    formatted_text = f"<del>{formatted_text}</del>"
                elif fmt.format_type == FormatType.CODE:
                    formatted_text = f"<code>{formatted_text}</code>"
                elif fmt.format_type == FormatType.LINK:
                    url = html.escape(fmt.value or "#")
                    formatted_text = f'<a href="{url}">{formatted_text}</a>'
                
                result += formatted_text
                last_pos = fmt.end
            
            # Add remaining text
            result += html.escape(text[last_pos:])
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying HTML formatting: {e}")
            return html.escape(text)
    
    def _apply_markdown_formatting(self, text: str, formats: List[FormatRange]) -> str:
        """Apply inline formatting to text for Markdown output"""
        try:
            if not formats:
                return text
            
            # Sort formats by start position
            sorted_formats = sorted(formats, key=lambda f: (f.start, -f.end))
            
            result = ""
            last_pos = 0
            
            for fmt in sorted_formats:
                # Add text before format
                result += text[last_pos:fmt.start]
                
                # Add formatted text
                formatted_text = text[fmt.start:fmt.end]
                
                if fmt.format_type == FormatType.BOLD:
                    formatted_text = f"**{formatted_text}**"
                elif fmt.format_type == FormatType.ITALIC:
                    formatted_text = f"*{formatted_text}*"
                elif fmt.format_type == FormatType.CODE:
                    formatted_text = f"`{formatted_text}`"
                elif fmt.format_type == FormatType.LINK:
                    url = fmt.value or "#"
                    formatted_text = f"[{formatted_text}]({url})"
                # Note: Markdown doesn't have native underline or strikethrough
                # Could use HTML tags if needed: <u>, <del>
                
                result += formatted_text
                last_pos = fmt.end
            
            # Add remaining text
            result += text[last_pos:]
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying Markdown formatting: {e}")
            return text


# Factory functions for easy use
def create_parser(config: Optional[ParseConfig] = None) -> RichTextParser:
    """Create a new rich text parser"""
    return RichTextParser(config)


def create_serializer() -> RichTextSerializer:
    """Create a new rich text serializer"""
    return RichTextSerializer()


def parse_content(content: str, content_type: str = "auto") -> RichTextDocument:
    """
    Parse content with automatic type detection
    CLAUDE.md #1.2: Simple interface for common use cases
    """
    parser = create_parser()
    
    if content_type == "auto":
        # Auto-detect content type
        content_stripped = content.strip()
        if content_stripped.startswith('<') and content_stripped.endswith('>'):
            content_type = "html"
        elif re.search(r'[#*`\[\]_~]', content_stripped):
            content_type = "markdown"
        else:
            content_type = "text"
    
    if content_type == "html":
        return parser.parse_html(content)
    elif content_type == "markdown":
        return parser.parse_markdown(content)
    elif content_type == "text":
        return parser.parse_plain_text(content)
    else:
        raise ValueError(f"Unsupported content type: {content_type}")


def export_content(document: RichTextDocument, format: str = "html") -> str:
    """
    Export document with format selection
    CLAUDE.md #1.2: Simple interface for common use cases
    """
    serializer = create_serializer()
    
    if format == "html":
        return serializer.to_html(document)
    elif format == "markdown":
        return serializer.to_markdown(document)
    elif format == "text":
        return serializer.to_plain_text(document)
    elif format == "json":
        return serializer.to_json(document)
    else:
        raise ValueError(f"Unsupported export format: {format}")


# Add missing import
from uuid import uuid4
from typing import Tuple