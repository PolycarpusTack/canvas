"""
Default Component Property Definitions
Registers common components with their property definitions
Following CLAUDE.md guidelines for comprehensive component definitions
"""

from typing import List
import logging

from property_definitions import (
    PropertyDefinition, PropertyType, PropertyCategory, PropertyValidation,
    PropertyOption, PropertyDependency, AnimationConfig, COMMON_PROPERTIES
)
from property_registry import get_registry

logger = logging.getLogger(__name__)


def register_default_components():
    """Register all default component property definitions"""
    registry = get_registry()
    
    # Register button component
    registry.register_component_properties("button", _get_button_properties())
    
    # Register text component
    registry.register_component_properties("text", _get_text_properties())
    
    # Register image component
    registry.register_component_properties("image", _get_image_properties())
    
    # Register container/div component
    registry.register_component_properties("container", _get_container_properties())
    registry.register_component_properties("div", _get_container_properties())
    
    # Register form components
    registry.register_component_properties("input", _get_input_properties())
    registry.register_component_properties("textarea", _get_textarea_properties())
    
    logger.info("Registered default component properties")


def _get_button_properties() -> List[PropertyDefinition]:
    """Get property definitions for button component"""
    return [
        # Content properties
        PropertyDefinition(
            name="text",
            label="Button Text",
            category=PropertyCategory.CONTENT,
            type=PropertyType.TEXT,
            default_value="Button",
            description="The text displayed on the button",
            required=True,
            placeholder="Enter button text",
            icon="text_fields",
            tags=["content", "text", "label"]
        ),
        
        PropertyDefinition(
            name="type",
            label="Button Type",
            category=PropertyCategory.CONTENT,
            type=PropertyType.SELECT,
            default_value="button",
            description="The HTML type attribute for the button",
            options=[
                PropertyOption("button", "Button"),
                PropertyOption("submit", "Submit"),
                PropertyOption("reset", "Reset")
            ],
            icon="category",
            tags=["type", "form", "behavior"]
        ),
        
        PropertyDefinition(
            name="disabled",
            label="Disabled",
            category=PropertyCategory.CONTENT,
            type=PropertyType.BOOLEAN,
            default_value=False,
            description="Whether the button is disabled",
            icon="block",
            tags=["disabled", "state", "interaction"]
        ),
        
        # Style properties
        PropertyDefinition(
            name="variant",
            label="Style Variant",
            category=PropertyCategory.STYLE,
            type=PropertyType.SELECT,
            default_value="primary",
            description="The visual style variant of the button",
            options=[
                PropertyOption("primary", "Primary", description="Main action button"),
                PropertyOption("secondary", "Secondary", description="Secondary action"),
                PropertyOption("outlined", "Outlined", description="Outlined style"),
                PropertyOption("text", "Text", description="Text-only button"),
                PropertyOption("danger", "Danger", description="Destructive action")
            ],
            icon="palette",
            tags=["variant", "style", "appearance"]
        ),
        
        PropertyDefinition(
            name="size",
            label="Size",
            category=PropertyCategory.STYLE,
            type=PropertyType.SELECT,
            default_value="medium",
            description="The size of the button",
            options=[
                PropertyOption("small", "Small"),
                PropertyOption("medium", "Medium"),
                PropertyOption("large", "Large")
            ],
            icon="height",
            tags=["size", "dimensions"]
        ),
        
        PropertyDefinition(
            name="background_color",
            label="Background Color",
            category=PropertyCategory.STYLE,
            type=PropertyType.COLOR,
            default_value="#5E6AD2",
            description="The background color of the button",
            dependencies=[
                PropertyDependency("variant", "equals", "primary", "show")
            ],
            icon="format_color_fill",
            responsive=True,
            animatable=True,
            animation_config=AnimationConfig(duration=0.2, property_name="background-color"),
            tags=["color", "background", "theme"]
        ),
        
        PropertyDefinition(
            name="text_color",
            label="Text Color",
            category=PropertyCategory.STYLE,
            type=PropertyType.COLOR,
            default_value="#FFFFFF",
            description="The text color of the button",
            icon="format_color_text",
            responsive=True,
            animatable=True,
            tags=["color", "text", "foreground"]
        ),
        
        PropertyDefinition(
            name="border_radius",
            label="Border Radius",
            category=PropertyCategory.STYLE,
            type=PropertyType.SIZE,
            default_value="6px",
            description="The border radius of the button",
            validation=PropertyValidation(
                min_value=0,
                max_value=50,
                error_messages={
                    "min_value": "Border radius cannot be negative",
                    "max_value": "Border radius too large"
                }
            ),
            units=["px", "em", "rem", "%"],
            default_unit="px",
            icon="rounded_corner",
            responsive=True,
            tags=["border", "radius", "shape"]
        ),
        
        # Layout properties
        PropertyDefinition(
            name="width",
            label="Width",
            category=PropertyCategory.LAYOUT,
            type=PropertyType.SIZE,
            default_value="auto",
            description="The width of the button",
            units=["px", "em", "rem", "%", "auto", "fit-content"],
            default_unit="px",
            icon="width",
            responsive=True,
            tags=["width", "size", "dimensions"]
        ),
        
        PropertyDefinition(
            name="margin",
            label="Margin",
            category=PropertyCategory.SPACING,
            type=PropertyType.SPACING,
            default_value="0",
            description="The margin around the button",
            units=["px", "em", "rem", "%"],
            default_unit="px",
            icon="space_bar",
            responsive=True,
            tags=["margin", "spacing", "layout"]
        ),
        
        PropertyDefinition(
            name="padding",
            label="Padding",
            category=PropertyCategory.SPACING,
            type=PropertyType.SPACING,
            default_value="12px 24px",
            description="The padding inside the button",
            units=["px", "em", "rem", "%"],
            default_unit="px",
            icon="padding",
            responsive=True,
            tags=["padding", "spacing", "internal"]
        ),
        
        # Typography
        PropertyDefinition(
            name="font_size",
            label="Font Size",
            category=PropertyCategory.TYPOGRAPHY,
            type=PropertyType.SIZE,
            default_value="14px",
            description="The font size of the button text",
            validation=PropertyValidation(
                min_value=8,
                max_value=72,
                error_messages={
                    "min_value": "Font size too small",
                    "max_value": "Font size too large"
                }
            ),
            units=["px", "em", "rem", "%"],
            default_unit="px",
            icon="format_size",
            responsive=True,
            tags=["font", "size", "typography"]
        ),
        
        PropertyDefinition(
            name="font_weight",
            label="Font Weight",
            category=PropertyCategory.TYPOGRAPHY,
            type=PropertyType.SELECT,
            default_value="500",
            description="The font weight of the button text",
            options=[
                PropertyOption("300", "Light"),
                PropertyOption("400", "Normal"),
                PropertyOption("500", "Medium"),
                PropertyOption("600", "Semibold"),
                PropertyOption("700", "Bold")
            ],
            icon="format_bold",
            responsive=True,
            tags=["font", "weight", "typography"]
        ),
        
        # Effects
        PropertyDefinition(
            name="shadow",
            label="Box Shadow",
            category=PropertyCategory.EFFECTS,
            type=PropertyType.SHADOW,
            default_value="0 2px 4px rgba(0,0,0,0.1)",
            description="The box shadow of the button",
            icon="shadow",
            animatable=True,
            tags=["shadow", "effect", "depth"]
        ),
        
        # Advanced
        PropertyDefinition(
            name="onclick",
            label="Click Handler",
            category=PropertyCategory.INTERACTIONS,
            type=PropertyType.TEXT,
            default_value="",
            description="JavaScript code to execute when clicked",
            placeholder="alert('Button clicked!')",
            advanced=True,
            icon="touch_app",
            tags=["onclick", "event", "javascript", "interaction"]
        )
    ]


def _get_text_properties() -> List[PropertyDefinition]:
    """Get property definitions for text component"""
    return [
        # Content
        PropertyDefinition(
            name="content",
            label="Text Content",
            category=PropertyCategory.CONTENT,
            type=PropertyType.TEXTAREA,
            default_value="Text content",
            description="The text content to display",
            required=True,
            placeholder="Enter your text here...",
            icon="text_fields",
            tags=["content", "text", "copy"]
        ),
        
        PropertyDefinition(
            name="tag",
            label="HTML Tag",
            category=PropertyCategory.CONTENT,
            type=PropertyType.SELECT,
            default_value="p",
            description="The HTML tag to use for the text",
            options=[
                PropertyOption("p", "Paragraph"),
                PropertyOption("h1", "Heading 1"),
                PropertyOption("h2", "Heading 2"),
                PropertyOption("h3", "Heading 3"),
                PropertyOption("h4", "Heading 4"),
                PropertyOption("h5", "Heading 5"),
                PropertyOption("h6", "Heading 6"),
                PropertyOption("span", "Span"),
                PropertyOption("div", "Div"),
                PropertyOption("strong", "Strong"),
                PropertyOption("em", "Emphasis")
            ],
            icon="title",
            tags=["tag", "semantic", "html"]
        ),
        
        # Typography
        PropertyDefinition(
            name="font_family",
            label="Font Family",
            category=PropertyCategory.TYPOGRAPHY,
            type=PropertyType.SELECT,
            default_value="system-ui",
            description="The font family for the text",
            options=[
                PropertyOption("system-ui", "System"),
                PropertyOption("Georgia, serif", "Georgia"),
                PropertyOption("'Times New Roman', serif", "Times"),
                PropertyOption("Arial, sans-serif", "Arial"),
                PropertyOption("Helvetica, sans-serif", "Helvetica"),
                PropertyOption("'Courier New', monospace", "Courier"),
                PropertyOption("Monaco, monospace", "Monaco")
            ],
            icon="font_download",
            responsive=True,
            tags=["font", "family", "typography"]
        ),
        
        PropertyDefinition(
            name="font_size",
            label="Font Size",
            category=PropertyCategory.TYPOGRAPHY,
            type=PropertyType.SIZE,
            default_value="16px",
            description="The size of the text",
            validation=PropertyValidation(
                min_value=8,
                max_value=120,
                error_messages={
                    "min_value": "Font size too small for readability",
                    "max_value": "Font size too large"
                }
            ),
            units=["px", "em", "rem", "%"],
            default_unit="px",
            icon="format_size",
            responsive=True,
            tags=["font", "size", "typography"]
        ),
        
        PropertyDefinition(
            name="line_height",
            label="Line Height",
            category=PropertyCategory.TYPOGRAPHY,
            type=PropertyType.NUMBER,
            default_value=1.5,
            description="The line height of the text",
            validation=PropertyValidation(
                min_value=0.8,
                max_value=3.0,
                error_messages={
                    "min_value": "Line height too small",
                    "max_value": "Line height too large"
                }
            ),
            step=0.1,
            icon="format_line_spacing",
            responsive=True,
            tags=["line", "height", "spacing", "typography"]
        ),
        
        PropertyDefinition(
            name="text_align",
            label="Text Align",
            category=PropertyCategory.TYPOGRAPHY,
            type=PropertyType.SELECT,
            default_value="left",
            description="The text alignment",
            options=[
                PropertyOption("left", "Left"),
                PropertyOption("center", "Center"),
                PropertyOption("right", "Right"),
                PropertyOption("justify", "Justify")
            ],
            icon="format_align_left",
            responsive=True,
            tags=["align", "text", "typography"]
        ),
        
        PropertyDefinition(
            name="color",
            label="Text Color",
            category=PropertyCategory.STYLE,
            type=PropertyType.COLOR,
            default_value="#1F2937",
            description="The color of the text",
            icon="format_color_text",
            responsive=True,
            animatable=True,
            tags=["color", "text", "foreground"]
        )
    ]


def _get_image_properties() -> List[PropertyDefinition]:
    """Get property definitions for image component"""
    return [
        # Content
        PropertyDefinition(
            name="src",
            label="Image Source",
            category=PropertyCategory.CONTENT,
            type=PropertyType.URL,
            default_value="",
            description="The URL or path to the image",
            required=True,
            placeholder="https://example.com/image.jpg",
            validation=PropertyValidation(
                pattern=r'^(https?://|/|\./).*\.(jpg|jpeg|png|gif|svg|webp)$',
                error_messages={
                    "pattern": "Must be a valid image URL or path"
                }
            ),
            icon="image",
            tags=["src", "url", "image", "content"]
        ),
        
        PropertyDefinition(
            name="alt",
            label="Alt Text",
            category=PropertyCategory.CONTENT,
            type=PropertyType.TEXT,
            default_value="",
            description="Alternative text for accessibility",
            placeholder="Describe the image...",
            validation=PropertyValidation(
                max_length=150,
                error_messages={
                    "max_length": "Alt text should be concise (max 150 characters)"
                }
            ),
            icon="accessibility",
            tags=["alt", "accessibility", "description"]
        ),
        
        PropertyDefinition(
            name="title",
            label="Title",
            category=PropertyCategory.CONTENT,
            type=PropertyType.TEXT,
            default_value="",
            description="Tooltip text when hovering over the image",
            placeholder="Image title...",
            icon="title",
            tags=["title", "tooltip", "hover"]
        ),
        
        # Layout
        PropertyDefinition(
            name="width",
            label="Width",
            category=PropertyCategory.LAYOUT,
            type=PropertyType.SIZE,
            default_value="auto",
            description="The width of the image",
            units=["px", "em", "rem", "%", "auto"],
            default_unit="px",
            icon="width",
            responsive=True,
            tags=["width", "size", "dimensions"]
        ),
        
        PropertyDefinition(
            name="height",
            label="Height",
            category=PropertyCategory.LAYOUT,
            type=PropertyType.SIZE,
            default_value="auto",
            description="The height of the image",
            units=["px", "em", "rem", "%", "auto"],
            default_unit="px",
            icon="height",
            responsive=True,
            tags=["height", "size", "dimensions"]
        ),
        
        PropertyDefinition(
            name="object_fit",
            label="Object Fit",
            category=PropertyCategory.LAYOUT,
            type=PropertyType.SELECT,
            default_value="cover",
            description="How the image should be resized to fit its container",
            options=[
                PropertyOption("cover", "Cover", description="Covers entire container, may crop"),
                PropertyOption("contain", "Contain", description="Fits entire image, may letterbox"),
                PropertyOption("fill", "Fill", description="Stretches to fill container"),
                PropertyOption("scale-down", "Scale Down", description="Scales down if needed"),
                PropertyOption("none", "None", description="Original size")
            ],
            icon="aspect_ratio",
            tags=["fit", "resize", "aspect"]
        ),
        
        # Style
        PropertyDefinition(
            name="border_radius",
            label="Border Radius",
            category=PropertyCategory.STYLE,
            type=PropertyType.SIZE,
            default_value="0",
            description="The border radius of the image",
            units=["px", "em", "rem", "%"],
            default_unit="px",
            icon="rounded_corner",
            responsive=True,
            tags=["border", "radius", "shape"]
        ),
        
        PropertyDefinition(
            name="opacity",
            label="Opacity",
            category=PropertyCategory.EFFECTS,
            type=PropertyType.RANGE,
            default_value=1.0,
            description="The opacity of the image",
            min_value=0.0,
            max_value=1.0,
            step=0.1,
            icon="opacity",
            animatable=True,
            tags=["opacity", "transparency", "alpha"]
        )
    ]


def _get_container_properties() -> List[PropertyDefinition]:
    """Get property definitions for container/div component"""
    return [
        # Layout
        PropertyDefinition(
            name="display",
            label="Display",
            category=PropertyCategory.LAYOUT,
            type=PropertyType.SELECT,
            default_value="block",
            description="The CSS display property",
            options=[
                PropertyOption("block", "Block"),
                PropertyOption("inline", "Inline"),
                PropertyOption("inline-block", "Inline Block"),
                PropertyOption("flex", "Flex"),
                PropertyOption("grid", "Grid"),
                PropertyOption("none", "None")
            ],
            icon="dashboard",
            tags=["display", "layout", "css"]
        ),
        
        PropertyDefinition(
            name="flex_direction",
            label="Flex Direction",
            category=PropertyCategory.LAYOUT,
            type=PropertyType.SELECT,
            default_value="row",
            description="The direction of flex items",
            options=[
                PropertyOption("row", "Row"),
                PropertyOption("column", "Column"),
                PropertyOption("row-reverse", "Row Reverse"),
                PropertyOption("column-reverse", "Column Reverse")
            ],
            dependencies=[
                PropertyDependency("display", "equals", "flex", "show")
            ],
            icon="view_column",
            responsive=True,
            tags=["flex", "direction", "layout"]
        ),
        
        PropertyDefinition(
            name="justify_content",
            label="Justify Content",
            category=PropertyCategory.LAYOUT,
            type=PropertyType.SELECT,
            default_value="flex-start",
            description="How flex items are justified along main axis",
            options=[
                PropertyOption("flex-start", "Start"),
                PropertyOption("flex-end", "End"),
                PropertyOption("center", "Center"),
                PropertyOption("space-between", "Space Between"),
                PropertyOption("space-around", "Space Around"),
                PropertyOption("space-evenly", "Space Evenly")
            ],
            dependencies=[
                PropertyDependency("display", "equals", "flex", "show")
            ],
            icon="format_align_justify",
            responsive=True,
            tags=["justify", "align", "flex"]
        ),
        
        PropertyDefinition(
            name="align_items",
            label="Align Items",
            category=PropertyCategory.LAYOUT,
            type=PropertyType.SELECT,
            default_value="stretch",
            description="How flex items are aligned along cross axis",
            options=[
                PropertyOption("flex-start", "Start"),
                PropertyOption("flex-end", "End"),
                PropertyOption("center", "Center"),
                PropertyOption("baseline", "Baseline"),
                PropertyOption("stretch", "Stretch")
            ],
            dependencies=[
                PropertyDependency("display", "equals", "flex", "show")
            ],
            icon="vertical_align_center",
            responsive=True,
            tags=["align", "items", "flex"]
        ),
        
        # Spacing
        PropertyDefinition(
            name="padding",
            label="Padding",
            category=PropertyCategory.SPACING,
            type=PropertyType.SPACING,
            default_value="16px",
            description="The padding inside the container",
            units=["px", "em", "rem", "%"],
            default_unit="px",
            icon="padding",
            responsive=True,
            tags=["padding", "spacing", "internal"]
        ),
        
        PropertyDefinition(
            name="margin",
            label="Margin",
            category=PropertyCategory.SPACING,
            type=PropertyType.SPACING,
            default_value="0",
            description="The margin around the container",
            units=["px", "em", "rem", "%", "auto"],
            default_unit="px",
            icon="space_bar",
            responsive=True,
            tags=["margin", "spacing", "external"]
        ),
        
        PropertyDefinition(
            name="gap",
            label="Gap",
            category=PropertyCategory.SPACING,
            type=PropertyType.SIZE,
            default_value="0",
            description="The gap between child elements",
            dependencies=[
                PropertyDependency("display", "in", ["flex", "grid"], "show")
            ],
            units=["px", "em", "rem", "%"],
            default_unit="px",
            icon="space_dashboard",
            responsive=True,
            tags=["gap", "spacing", "children"]
        ),
        
        # Style
        PropertyDefinition(
            name="background_color",
            label="Background Color",
            category=PropertyCategory.STYLE,
            type=PropertyType.COLOR,
            default_value="transparent",
            description="The background color of the container",
            icon="format_color_fill",
            responsive=True,
            animatable=True,
            tags=["background", "color", "fill"]
        ),
        
        PropertyDefinition(
            name="border",
            label="Border",
            category=PropertyCategory.STYLE,
            type=PropertyType.BORDER,
            default_value="none",
            description="The border around the container",
            icon="border_style",
            responsive=True,
            tags=["border", "outline", "stroke"]
        ),
        
        PropertyDefinition(
            name="border_radius",
            label="Border Radius",
            category=PropertyCategory.STYLE,
            type=PropertyType.SPACING,
            default_value="0",
            description="The border radius of the container",
            units=["px", "em", "rem", "%"],
            default_unit="px",
            icon="rounded_corner",
            responsive=True,
            tags=["border", "radius", "corner"]
        )
    ]


def _get_input_properties() -> List[PropertyDefinition]:
    """Get property definitions for input component"""
    return [
        # Content
        PropertyDefinition(
            name="type",
            label="Input Type",
            category=PropertyCategory.CONTENT,
            type=PropertyType.SELECT,
            default_value="text",
            description="The type of input field",
            options=[
                PropertyOption("text", "Text"),
                PropertyOption("email", "Email"),
                PropertyOption("password", "Password"),
                PropertyOption("number", "Number"),
                PropertyOption("tel", "Phone"),
                PropertyOption("url", "URL"),
                PropertyOption("search", "Search"),
                PropertyOption("date", "Date"),
                PropertyOption("time", "Time")
            ],
            icon="input",
            tags=["type", "input", "form"]
        ),
        
        PropertyDefinition(
            name="placeholder",
            label="Placeholder",
            category=PropertyCategory.CONTENT,
            type=PropertyType.TEXT,
            default_value="",
            description="Placeholder text when input is empty",
            placeholder="Enter placeholder text...",
            icon="text_fields",
            tags=["placeholder", "hint", "help"]
        ),
        
        PropertyDefinition(
            name="value",
            label="Default Value",
            category=PropertyCategory.CONTENT,
            type=PropertyType.TEXT,
            default_value="",
            description="The default value of the input",
            icon="edit",
            tags=["value", "default", "content"]
        ),
        
        PropertyDefinition(
            name="required",
            label="Required",
            category=PropertyCategory.CONTENT,
            type=PropertyType.BOOLEAN,
            default_value=False,
            description="Whether the input is required",
            icon="star",
            tags=["required", "validation", "mandatory"]
        ),
        
        PropertyDefinition(
            name="disabled",
            label="Disabled",
            category=PropertyCategory.CONTENT,
            type=PropertyType.BOOLEAN,
            default_value=False,
            description="Whether the input is disabled",
            icon="block",
            tags=["disabled", "state", "readonly"]
        )
    ]


def _get_textarea_properties() -> List[PropertyDefinition]:
    """Get property definitions for textarea component"""
    return [
        # Content
        PropertyDefinition(
            name="placeholder",
            label="Placeholder",
            category=PropertyCategory.CONTENT,
            type=PropertyType.TEXT,
            default_value="",
            description="Placeholder text when textarea is empty",
            placeholder="Enter placeholder text...",
            icon="text_fields",
            tags=["placeholder", "hint", "help"]
        ),
        
        PropertyDefinition(
            name="value",
            label="Default Value",
            category=PropertyCategory.CONTENT,
            type=PropertyType.TEXTAREA,
            default_value="",
            description="The default content of the textarea",
            icon="edit_note",
            tags=["value", "default", "content"]
        ),
        
        PropertyDefinition(
            name="rows",
            label="Rows",
            category=PropertyCategory.LAYOUT,
            type=PropertyType.NUMBER,
            default_value=4,
            description="The number of visible text lines",
            validation=PropertyValidation(
                min_value=1,
                max_value=50,
                error_messages={
                    "min_value": "Must have at least 1 row",
                    "max_value": "Too many rows"
                }
            ),
            icon="format_list_numbered",
            tags=["rows", "height", "lines"]
        ),
        
        PropertyDefinition(
            name="cols",
            label="Columns",
            category=PropertyCategory.LAYOUT,
            type=PropertyType.NUMBER,
            default_value=50,
            description="The visible width in characters",
            validation=PropertyValidation(
                min_value=10,
                max_value=200,
                error_messages={
                    "min_value": "Must have at least 10 columns",
                    "max_value": "Too many columns"
                }
            ),
            icon="format_list_numbered",
            tags=["cols", "width", "characters"]
        ),
        
        PropertyDefinition(
            name="resize",
            label="Resize",
            category=PropertyCategory.LAYOUT,
            type=PropertyType.SELECT,
            default_value="both",
            description="Whether the textarea can be resized",
            options=[
                PropertyOption("none", "None"),
                PropertyOption("horizontal", "Horizontal"),
                PropertyOption("vertical", "Vertical"),
                PropertyOption("both", "Both")
            ],
            icon="resize",
            tags=["resize", "interaction", "user"]
        )
    ]


# Auto-register on import
register_default_components()