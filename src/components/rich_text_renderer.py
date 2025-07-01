"""
Rich Text Content Renderer
Renders rich text blocks and inline elements to Flet controls
Following CLAUDE.md guidelines for safe and performant rendering
"""

import flet as ft
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import logging
import html
import re
import time

from components.rich_text_document import TextBlock, InlineElement, BlockType, InlineType

logger = logging.getLogger(__name__)


@dataclass
class RenderConfig:
    """
    Rendering configuration
    CLAUDE.md #1.4: Configurable rendering options
    """
    # Typography
    base_font_size: int = 16
    line_height: float = 1.5
    font_family: str = "Segoe UI, system-ui, sans-serif"
    
    # Colors
    text_color: str = "#1F2937"
    background_color: str = "#FFFFFF"
    selection_color: str = "#DBEAFE"
    link_color: str = "#2563EB"
    
    # Spacing
    paragraph_spacing: int = 16
    heading_spacing: int = 24
    list_spacing: int = 8
    
    # Code styling
    code_font_family: str = "Consolas, Monaco, monospace"
    code_background: str = "#F3F4F6"
    code_border_radius: int = 4
    
    # Performance
    virtual_rendering: bool = True
    max_render_time_ms: float = 16.0  # 60fps budget
    
    def __post_init__(self):
        """Validate configuration"""
        if self.base_font_size < 8 or self.base_font_size > 72:
            raise ValueError("Base font size must be between 8 and 72")
        
        if self.line_height < 1.0 or self.line_height > 3.0:
            raise ValueError("Line height must be between 1.0 and 3.0")


class RichTextRenderer:
    """
    Rich text content renderer
    CLAUDE.md #1.5: Optimize rendering performance
    CLAUDE.md #7.2: Safe content rendering
    CLAUDE.md #12.1: Performance monitoring
    """
    
    def __init__(self, config: Optional[RenderConfig] = None):
        """Initialize renderer"""
        self.config = config or RenderConfig()
        
        # Performance tracking
        self._render_count = 0
        self._total_render_time = 0.0
        self._avg_render_time = 0.0
        
        # Style cache for performance
        self._style_cache: Dict[str, ft.TextStyle] = {}
        self._container_cache: Dict[str, ft.Container] = {}
        
        # Initialize base styles
        self._init_base_styles()
        
        logger.info("Rich text renderer initialized")
    
    def render_block(self, block: TextBlock) -> Optional[ft.Control]:
        """
        Render a text block to Flet control
        CLAUDE.md #1.5: Efficient block rendering
        """
        start_time = time.perf_counter()
        
        try:
            # Validate block
            if not block:
                return None
            
            # Route to appropriate renderer
            if block.type == BlockType.PARAGRAPH:
                result = self._render_paragraph(block)
            elif block.type in [BlockType.H1, BlockType.H2, BlockType.H3, 
                              BlockType.H4, BlockType.H5, BlockType.H6]:
                result = self._render_heading(block)
            elif block.type == BlockType.BLOCKQUOTE:
                result = self._render_blockquote(block)
            elif block.type == BlockType.CODE_BLOCK:
                result = self._render_code_block(block)
            elif block.type in [BlockType.UNORDERED_LIST, BlockType.ORDERED_LIST]:
                result = self._render_list(block)
            elif block.type == BlockType.LIST_ITEM:
                result = self._render_list_item(block)
            elif block.type == BlockType.DIVIDER:
                result = self._render_divider(block)
            elif block.type == BlockType.IMAGE:
                result = self._render_image(block)
            elif block.type == BlockType.TABLE:
                result = self._render_table(block)
            else:
                logger.warning(f"Unknown block type: {block.type}")
                result = self._render_paragraph(block)  # Fallback
            
            # Add block metadata
            if result and hasattr(result, 'data'):
                result.data = block.id
            
            # Track performance
            render_time = (time.perf_counter() - start_time) * 1000
            self._update_render_metrics(render_time)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to render block {block.id}: {e}")
            return self._render_error_block(f"Render error: {e}")
    
    def render_inline_elements(self, elements: List[InlineElement]) -> List[ft.TextSpan]:
        """
        Render inline elements to text spans
        CLAUDE.md #7.2: Safe inline content rendering
        """
        try:
            spans = []
            
            for element in elements:
                span = self._render_inline_element(element)
                if span:
                    spans.append(span)
            
            return spans
            
        except Exception as e:
            logger.error(f"Failed to render inline elements: {e}")
            return [ft.TextSpan(text="[Render Error]", style=self._get_error_style())]
    
    def render_document_preview(self, blocks: List[TextBlock], max_blocks: int = 3) -> ft.Control:
        """
        Render document preview with limited blocks
        CLAUDE.md #1.5: Efficient preview rendering
        """
        try:
            preview_blocks = blocks[:max_blocks]
            rendered_blocks = []
            
            for block in preview_blocks:
                rendered = self.render_block(block)
                if rendered:
                    rendered_blocks.append(rendered)
            
            # Add "..." indicator if truncated
            if len(blocks) > max_blocks:
                rendered_blocks.append(
                    ft.Container(
                        content=ft.Text("...", style=ft.TextStyle(color="#9CA3AF")),
                        padding=ft.padding.symmetric(vertical=8)
                    )
                )
            
            return ft.Column(
                controls=rendered_blocks,
                spacing=self.config.paragraph_spacing,
                tight=True
            )
            
        except Exception as e:
            logger.error(f"Failed to render document preview: {e}")
            return self._render_error_block("Preview error")
    
    # Block renderers
    
    def _render_paragraph(self, block: TextBlock) -> ft.Control:
        """Render paragraph block"""
        if not block.children and not block.content:
            # Empty paragraph
            return ft.Container(
                content=ft.Text(" "),  # Non-breaking space for proper height
                height=self.config.base_font_size * self.config.line_height,
                data=block.id
            )
        
        # Render inline content
        if block.children:
            spans = self.render_inline_elements(block.children)
            text_content = ft.Text(
                spans=spans,
                style=self._get_paragraph_style()
            )
        else:
            text_content = ft.Text(
                value=block.content,
                style=self._get_paragraph_style()
            )
        
        return ft.Container(
            content=text_content,
            padding=ft.padding.only(bottom=self.config.paragraph_spacing),
            data=block.id
        )
    
    def _render_heading(self, block: TextBlock) -> ft.Control:
        """Render heading block"""
        # Get heading level
        level = int(block.type.value[1])  # h1 -> 1, h2 -> 2, etc.
        
        # Calculate font size based on level
        size_multipliers = {1: 2.0, 2: 1.75, 3: 1.5, 4: 1.25, 5: 1.1, 6: 1.0}
        font_size = int(self.config.base_font_size * size_multipliers.get(level, 1.0))
        
        style = ft.TextStyle(
            size=font_size,
            weight=ft.FontWeight.BOLD,
            color=self.config.text_color,
            font_family=self.config.font_family
        )
        
        if block.children:
            spans = self.render_inline_elements(block.children)
            text_content = ft.Text(spans=spans, style=style)
        else:
            text_content = ft.Text(value=block.content, style=style)
        
        return ft.Container(
            content=text_content,
            padding=ft.padding.only(
                top=self.config.heading_spacing if level <= 3 else self.config.paragraph_spacing,
                bottom=self.config.paragraph_spacing
            ),
            data=block.id
        )
    
    def _render_blockquote(self, block: TextBlock) -> ft.Control:
        """Render blockquote block"""
        if block.children:
            spans = self.render_inline_elements(block.children)
            text_content = ft.Text(
                spans=spans,
                style=ft.TextStyle(
                    size=self.config.base_font_size,
                    color="#6B7280",
                    italic=True,
                    font_family=self.config.font_family
                )
            )
        else:
            text_content = ft.Text(
                value=block.content,
                style=ft.TextStyle(
                    size=self.config.base_font_size,
                    color="#6B7280",
                    italic=True,
                    font_family=self.config.font_family
                )
            )
        
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    width=4,
                    bgcolor="#D1D5DB",
                    border_radius=2
                ),
                ft.Container(
                    content=text_content,
                    expand=True,
                    padding=ft.padding.only(left=16)
                )
            ]),
            padding=ft.padding.only(bottom=self.config.paragraph_spacing),
            data=block.id
        )
    
    def _render_code_block(self, block: TextBlock) -> ft.Control:
        """Render code block"""
        # Get language from attributes
        language = block.attributes.get("language", "")
        
        code_style = ft.TextStyle(
            size=self.config.base_font_size - 1,
            font_family=self.config.code_font_family,
            color=self.config.text_color
        )
        
        text_content = ft.Text(
            value=block.content,
            style=code_style,
            selectable=True
        )
        
        # Add language label if specified
        header = None
        if language:
            header = ft.Container(
                content=ft.Text(
                    value=language,
                    style=ft.TextStyle(
                        size=self.config.base_font_size - 2,
                        color="#6B7280",
                        weight=ft.FontWeight.W_500
                    )
                ),
                padding=ft.padding.symmetric(horizontal=12, vertical=4),
                bgcolor="#E5E7EB",
                border_radius=ft.border_radius.only(
                    top_left=self.config.code_border_radius,
                    top_right=self.config.code_border_radius
                )
            )
        
        content_container = ft.Container(
            content=text_content,
            padding=12,
            bgcolor=self.config.code_background,
            border_radius=self.config.code_border_radius if not header else ft.border_radius.only(
                bottom_left=self.config.code_border_radius,
                bottom_right=self.config.code_border_radius
            ),
            border=ft.border.all(1, "#D1D5DB")
        )
        
        if header:
            return ft.Container(
                content=ft.Column([header, content_container], spacing=0),
                padding=ft.padding.only(bottom=self.config.paragraph_spacing),
                data=block.id
            )
        else:
            return ft.Container(
                content=content_container,
                padding=ft.padding.only(bottom=self.config.paragraph_spacing),
                data=block.id
            )
    
    def _render_list(self, block: TextBlock) -> ft.Control:
        """Render list block"""
        # This would be implemented for full list support
        return self._render_paragraph(block)
    
    def _render_list_item(self, block: TextBlock) -> ft.Control:
        """Render list item block"""
        # This would be implemented for full list support
        return self._render_paragraph(block)
    
    def _render_divider(self, block: TextBlock) -> ft.Control:
        """Render divider block"""
        return ft.Container(
            content=ft.Divider(
                height=1,
                color="#E5E7EB"
            ),
            padding=ft.padding.symmetric(vertical=self.config.paragraph_spacing),
            data=block.id
        )
    
    def _render_image(self, block: TextBlock) -> ft.Control:
        """Render image block"""
        src = block.attributes.get("src", "")
        alt = block.attributes.get("alt", "")
        width = block.attributes.get("width")
        height = block.attributes.get("height")
        
        if not src:
            return self._render_error_block("Missing image source")
        
        image = ft.Image(
            src=src,
            width=float(width) if width else None,
            height=float(height) if height else None,
            fit=ft.ImageFit.CONTAIN,
            tooltip=alt
        )
        
        return ft.Container(
            content=image,
            padding=ft.padding.only(bottom=self.config.paragraph_spacing),
            alignment=ft.alignment.center,
            data=block.id
        )
    
    def _render_table(self, block: TextBlock) -> ft.Control:
        """Render table block"""
        # This would be implemented for full table support
        return self._render_error_block("Table rendering not implemented")
    
    def _render_error_block(self, message: str) -> ft.Control:
        """Render error block"""
        return ft.Container(
            content=ft.Text(
                value=f"⚠️ {message}",
                style=ft.TextStyle(
                    size=self.config.base_font_size - 1,
                    color="#EF4444",
                    font_family=self.config.font_family
                )
            ),
            padding=ft.padding.all(8),
            bgcolor="#FEF2F2",
            border=ft.border.all(1, "#FECACA"),
            border_radius=4
        )
    
    # Inline element renderers
    
    def _render_inline_element(self, element: InlineElement) -> Optional[ft.TextSpan]:
        """Render inline element to text span"""
        try:
            if element.type == InlineType.TEXT:
                return ft.TextSpan(
                    text=element.text,
                    style=self._get_text_style()
                )
            
            elif element.type == InlineType.STRONG:
                return ft.TextSpan(
                    text=element.text,
                    style=ft.TextStyle(
                        weight=ft.FontWeight.BOLD,
                        color=self.config.text_color,
                        font_family=self.config.font_family
                    )
                )
            
            elif element.type == InlineType.EMPHASIS:
                return ft.TextSpan(
                    text=element.text,
                    style=ft.TextStyle(
                        italic=True,
                        color=self.config.text_color,
                        font_family=self.config.font_family
                    )
                )
            
            elif element.type == InlineType.UNDERLINE:
                return ft.TextSpan(
                    text=element.text,
                    style=ft.TextStyle(
                        decoration=ft.TextDecoration.UNDERLINE,
                        color=self.config.text_color,
                        font_family=self.config.font_family
                    )
                )
            
            elif element.type == InlineType.STRIKETHROUGH:
                return ft.TextSpan(
                    text=element.text,
                    style=ft.TextStyle(
                        decoration=ft.TextDecoration.LINE_THROUGH,
                        color=self.config.text_color,
                        font_family=self.config.font_family
                    )
                )
            
            elif element.type == InlineType.CODE:
                return ft.TextSpan(
                    text=element.text,
                    style=ft.TextStyle(
                        font_family=self.config.code_font_family,
                        size=self.config.base_font_size - 1,
                        bgcolor=self.config.code_background,
                        color=self.config.text_color
                    )
                )
            
            elif element.type == InlineType.LINK:
                return ft.TextSpan(
                    text=element.text,
                    style=ft.TextStyle(
                        color=self.config.link_color,
                        decoration=ft.TextDecoration.UNDERLINE,
                        font_family=self.config.font_family
                    ),
                    url=element.attributes.get("href", "")
                )
            
            elif element.type == InlineType.BREAK:
                return ft.TextSpan(text="\n")
            
            else:
                logger.warning(f"Unknown inline type: {element.type}")
                return ft.TextSpan(text=element.text)
            
        except Exception as e:
            logger.error(f"Failed to render inline element: {e}")
            return ft.TextSpan(text="[Error]", style=self._get_error_style())
    
    # Style helpers
    
    def _init_base_styles(self) -> None:
        """Initialize base text styles"""
        self._style_cache["text"] = ft.TextStyle(
            size=self.config.base_font_size,
            color=self.config.text_color,
            font_family=self.config.font_family,
            height=self.config.line_height
        )
        
        self._style_cache["paragraph"] = ft.TextStyle(
            size=self.config.base_font_size,
            color=self.config.text_color,
            font_family=self.config.font_family,
            height=self.config.line_height
        )
        
        self._style_cache["error"] = ft.TextStyle(
            size=self.config.base_font_size - 1,
            color="#EF4444",
            font_family=self.config.font_family,
            weight=ft.FontWeight.W_500
        )
    
    def _get_text_style(self) -> ft.TextStyle:
        """Get base text style"""
        return self._style_cache["text"]
    
    def _get_paragraph_style(self) -> ft.TextStyle:
        """Get paragraph style"""
        return self._style_cache["paragraph"]
    
    def _get_error_style(self) -> ft.TextStyle:
        """Get error text style"""
        return self._style_cache["error"]
    
    def _update_render_metrics(self, render_time: float) -> None:
        """
        Update rendering performance metrics
        CLAUDE.md #12.1: Performance monitoring
        """
        self._render_count += 1
        self._total_render_time += render_time
        
        # Update rolling average
        if self._avg_render_time == 0:
            self._avg_render_time = render_time
        else:
            # Exponential moving average
            alpha = 0.1
            self._avg_render_time = alpha * render_time + (1 - alpha) * self._avg_render_time
        
        # Warn if performance degrades
        if render_time > self.config.max_render_time_ms:
            logger.warning(
                f"Slow render: {render_time:.1f}ms "
                f"(avg: {self._avg_render_time:.1f}ms, budget: {self.config.max_render_time_ms}ms)"
            )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            "render_count": self._render_count,
            "total_render_time_ms": self._total_render_time,
            "avg_render_time_ms": self._avg_render_time,
            "max_render_time_ms": self.config.max_render_time_ms,
            "style_cache_size": len(self._style_cache)
        }


# Global instance for easy access
_rich_text_renderer_instance: Optional[RichTextRenderer] = None


def get_rich_text_renderer(config: Optional[RenderConfig] = None) -> RichTextRenderer:
    """Get or create global rich text renderer instance"""
    global _rich_text_renderer_instance
    if _rich_text_renderer_instance is None:
        _rich_text_renderer_instance = RichTextRenderer(config)
    return _rich_text_renderer_instance


def reset_rich_text_renderer() -> None:
    """Reset global rich text renderer instance"""
    global _rich_text_renderer_instance
    _rich_text_renderer_instance = None