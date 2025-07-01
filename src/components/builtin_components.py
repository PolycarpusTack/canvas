"""
Built-in Component Library
Defines all the standard components available in Canvas Editor.
"""

from typing import Dict
from component_types import (
    ComponentDefinition, ComponentCategory, ComponentSlot,
    ComponentConstraints, PropertyDefinition, PropertyType,
    PropertyValidation, PropertyOption
)


class BuiltInComponents:
    """Registry of all built-in component definitions"""
    
    @staticmethod
    def get_all_definitions() -> Dict[str, ComponentDefinition]:
        """Get all built-in component definitions"""
        return {
            # Layout Components
            "section": BuiltInComponents._create_section(),
            "container": BuiltInComponents._create_container(),
            "grid": BuiltInComponents._create_grid(),
            "flex": BuiltInComponents._create_flex(),
            "stack": BuiltInComponents._create_stack(),
            "columns": BuiltInComponents._create_columns(),
            
            # Content Components
            "heading": BuiltInComponents._create_heading(),
            "paragraph": BuiltInComponents._create_paragraph(),
            "text": BuiltInComponents._create_text(),
            "image": BuiltInComponents._create_image(),
            "video": BuiltInComponents._create_video(),
            "icon": BuiltInComponents._create_icon(),
            
            # Form Components
            "form": BuiltInComponents._create_form(),
            "input": BuiltInComponents._create_input(),
            "textarea": BuiltInComponents._create_textarea(),
            "select": BuiltInComponents._create_select(),
            "checkbox": BuiltInComponents._create_checkbox(),
            "radio": BuiltInComponents._create_radio(),
            "button": BuiltInComponents._create_button(),
            "label": BuiltInComponents._create_label(),
            
            # Navigation Components
            "navbar": BuiltInComponents._create_navbar(),
            "sidebar": BuiltInComponents._create_sidebar(),
            "tabs": BuiltInComponents._create_tabs(),
            "breadcrumb": BuiltInComponents._create_breadcrumb(),
            "link": BuiltInComponents._create_link(),
            
            # Data Display
            "table": BuiltInComponents._create_table(),
            "list": BuiltInComponents._create_list(),
            "card": BuiltInComponents._create_card(),
            "badge": BuiltInComponents._create_badge(),
            "progress": BuiltInComponents._create_progress(),
            
            # Feedback
            "alert": BuiltInComponents._create_alert(),
            "modal": BuiltInComponents._create_modal(),
            "tooltip": BuiltInComponents._create_tooltip(),
            "toast": BuiltInComponents._create_toast(),
        }
    
    # Layout Components
    
    @staticmethod
    def _create_section() -> ComponentDefinition:
        """Create section component definition"""
        return ComponentDefinition(
            id="section",
            name="Section",
            category=ComponentCategory.LAYOUT,
            icon="dashboard",
            description="A semantic section container with customizable padding and background",
            tags=["layout", "container", "semantic", "html5", "wrapper"],
            
            properties=[
                PropertyDefinition(
                    name="padding",
                    type=PropertyType.SPACING,
                    default_value="2rem",
                    description="Internal spacing",
                    group="Spacing"
                ),
                PropertyDefinition(
                    name="margin",
                    type=PropertyType.SPACING,
                    default_value="0 auto",
                    description="External spacing",
                    group="Spacing"
                ),
                PropertyDefinition(
                    name="background",
                    type=PropertyType.COLOR,
                    default_value="transparent",
                    description="Background color",
                    group="Appearance"
                ),
                PropertyDefinition(
                    name="fullWidth",
                    type=PropertyType.BOOLEAN,
                    default_value=False,
                    description="Expand to full viewport width",
                    group="Layout"
                ),
                PropertyDefinition(
                    name="maxWidth",
                    type=PropertyType.SIZE,
                    default_value="1200px",
                    description="Maximum width",
                    group="Layout",
                    depends_on={"fullWidth": False}
                ),
            ],
            
            default_values={
                "padding": "2rem",
                "margin": "0 auto",
                "maxWidth": "1200px",
                "background": "transparent",
                "fullWidth": False
            },
            
            slots=[
                ComponentSlot(
                    name="content",
                    description="Section content",
                    accepts=["*"],  # Accept any component
                    min_items=0,
                    max_items=None
                )
            ],
            
            constraints=ComponentConstraints(
                min_width=200,
                allowed_children=["*"],  # Accept any
                forbidden_children=["html", "head", "body"],  # No document elements
            ),
            
            accepts_children=True,
            draggable=True,
            droppable=True,
            resizable=True
        )
    
    @staticmethod
    def _create_container() -> ComponentDefinition:
        """Create container component definition"""
        return ComponentDefinition(
            id="container",
            name="Container",
            category=ComponentCategory.LAYOUT,
            icon="crop_square",
            description="A flexible container with customizable properties",
            tags=["layout", "container", "div", "wrapper"],
            
            properties=[
                PropertyDefinition(
                    name="display",
                    type=PropertyType.SELECT,
                    default_value="block",
                    description="Display type",
                    options=[
                        PropertyOption("block", "Block"),
                        PropertyOption("inline-block", "Inline Block"),
                        PropertyOption("flex", "Flex"),
                        PropertyOption("grid", "Grid"),
                        PropertyOption("none", "None")
                    ],
                    group="Layout"
                ),
                PropertyDefinition(
                    name="width",
                    type=PropertyType.SIZE,
                    default_value="auto",
                    description="Width",
                    group="Dimensions"
                ),
                PropertyDefinition(
                    name="height",
                    type=PropertyType.SIZE,
                    default_value="auto",
                    description="Height",
                    group="Dimensions"
                ),
                PropertyDefinition(
                    name="padding",
                    type=PropertyType.SPACING,
                    default_value="0",
                    description="Internal spacing",
                    group="Spacing"
                ),
                PropertyDefinition(
                    name="background",
                    type=PropertyType.COLOR,
                    default_value="transparent",
                    description="Background color",
                    group="Appearance"
                ),
                PropertyDefinition(
                    name="border",
                    type=PropertyType.STRING,
                    default_value="none",
                    description="Border style",
                    group="Appearance"
                ),
                PropertyDefinition(
                    name="borderRadius",
                    type=PropertyType.SIZE,
                    default_value="0",
                    description="Corner radius",
                    group="Appearance"
                ),
            ],
            
            default_values={
                "display": "block",
                "width": "auto",
                "height": "auto",
                "padding": "0",
                "background": "transparent"
            },
            
            slots=[
                ComponentSlot(
                    name="children",
                    description="Container content",
                    accepts=["*"],
                    min_items=0,
                    max_items=None
                )
            ],
            
            constraints=ComponentConstraints(
                allowed_children=["*"],
                forbidden_children=["html", "head", "body"]
            ),
            
            accepts_children=True,
            draggable=True,
            droppable=True,
            resizable=True
        )
    
    @staticmethod
    def _create_grid() -> ComponentDefinition:
        """Create grid component definition"""
        return ComponentDefinition(
            id="grid",
            name="Grid",
            category=ComponentCategory.LAYOUT,
            icon="grid_view",
            description="Responsive CSS grid container",
            tags=["layout", "grid", "responsive", "css-grid"],
            
            properties=[
                PropertyDefinition(
                    name="columns",
                    type=PropertyType.STRING,
                    default_value="repeat(auto-fit, minmax(250px, 1fr))",
                    description="Grid template columns",
                    group="Grid"
                ),
                PropertyDefinition(
                    name="rows",
                    type=PropertyType.STRING,
                    default_value="auto",
                    description="Grid template rows",
                    group="Grid"
                ),
                PropertyDefinition(
                    name="gap",
                    type=PropertyType.SIZE,
                    default_value="1rem",
                    description="Gap between items",
                    group="Grid"
                ),
                PropertyDefinition(
                    name="alignItems",
                    type=PropertyType.SELECT,
                    default_value="stretch",
                    description="Align items",
                    options=[
                        PropertyOption("start", "Start"),
                        PropertyOption("center", "Center"),
                        PropertyOption("end", "End"),
                        PropertyOption("stretch", "Stretch")
                    ],
                    group="Alignment"
                ),
                PropertyDefinition(
                    name="justifyItems",
                    type=PropertyType.SELECT,
                    default_value="stretch",
                    description="Justify items",
                    options=[
                        PropertyOption("start", "Start"),
                        PropertyOption("center", "Center"),
                        PropertyOption("end", "End"),
                        PropertyOption("stretch", "Stretch")
                    ],
                    group="Alignment"
                ),
            ],
            
            default_values={
                "display": "grid",
                "columns": "repeat(auto-fit, minmax(250px, 1fr))",
                "rows": "auto",
                "gap": "1rem",
                "alignItems": "stretch",
                "justifyItems": "stretch"
            },
            
            slots=[
                ComponentSlot(
                    name="items",
                    description="Grid items",
                    accepts=["*"],
                    min_items=0,
                    max_items=None
                )
            ],
            
            constraints=ComponentConstraints(
                min_width=200,
                allowed_children=["*"]
            ),
            
            accepts_children=True,
            draggable=True,
            droppable=True,
            resizable=True
        )
    
    @staticmethod
    def _create_flex() -> ComponentDefinition:
        """Create flex container component definition"""
        return ComponentDefinition(
            id="flex",
            name="Flex",
            category=ComponentCategory.LAYOUT,
            icon="view_week",
            description="Flexible box layout container",
            tags=["layout", "flex", "flexbox", "responsive"],
            
            properties=[
                PropertyDefinition(
                    name="direction",
                    type=PropertyType.SELECT,
                    default_value="row",
                    description="Flex direction",
                    options=[
                        PropertyOption("row", "Row"),
                        PropertyOption("row-reverse", "Row Reverse"),
                        PropertyOption("column", "Column"),
                        PropertyOption("column-reverse", "Column Reverse")
                    ],
                    group="Flex"
                ),
                PropertyDefinition(
                    name="wrap",
                    type=PropertyType.SELECT,
                    default_value="nowrap",
                    description="Flex wrap",
                    options=[
                        PropertyOption("nowrap", "No Wrap"),
                        PropertyOption("wrap", "Wrap"),
                        PropertyOption("wrap-reverse", "Wrap Reverse")
                    ],
                    group="Flex"
                ),
                PropertyDefinition(
                    name="justifyContent",
                    type=PropertyType.SELECT,
                    default_value="flex-start",
                    description="Justify content",
                    options=[
                        PropertyOption("flex-start", "Start"),
                        PropertyOption("center", "Center"),
                        PropertyOption("flex-end", "End"),
                        PropertyOption("space-between", "Space Between"),
                        PropertyOption("space-around", "Space Around"),
                        PropertyOption("space-evenly", "Space Evenly")
                    ],
                    group="Alignment"
                ),
                PropertyDefinition(
                    name="alignItems",
                    type=PropertyType.SELECT,
                    default_value="stretch",
                    description="Align items",
                    options=[
                        PropertyOption("flex-start", "Start"),
                        PropertyOption("center", "Center"),
                        PropertyOption("flex-end", "End"),
                        PropertyOption("stretch", "Stretch"),
                        PropertyOption("baseline", "Baseline")
                    ],
                    group="Alignment"
                ),
                PropertyDefinition(
                    name="gap",
                    type=PropertyType.SIZE,
                    default_value="0",
                    description="Gap between items",
                    group="Spacing"
                ),
            ],
            
            default_values={
                "display": "flex",
                "direction": "row",
                "wrap": "nowrap",
                "justifyContent": "flex-start",
                "alignItems": "stretch",
                "gap": "0"
            },
            
            slots=[
                ComponentSlot(
                    name="items",
                    description="Flex items",
                    accepts=["*"],
                    min_items=0,
                    max_items=None
                )
            ],
            
            constraints=ComponentConstraints(
                allowed_children=["*"]
            ),
            
            accepts_children=True,
            draggable=True,
            droppable=True,
            resizable=True
        )
    
    @staticmethod
    def _create_stack() -> ComponentDefinition:
        """Create vertical stack component definition"""
        return ComponentDefinition(
            id="stack",
            name="Stack",
            category=ComponentCategory.LAYOUT,
            icon="view_agenda",
            description="Vertical stack with consistent spacing",
            tags=["layout", "stack", "vertical", "spacing"],
            
            properties=[
                PropertyDefinition(
                    name="spacing",
                    type=PropertyType.SIZE,
                    default_value="1rem",
                    description="Space between items",
                    group="Spacing"
                ),
                PropertyDefinition(
                    name="align",
                    type=PropertyType.SELECT,
                    default_value="stretch",
                    description="Horizontal alignment",
                    options=[
                        PropertyOption("stretch", "Stretch"),
                        PropertyOption("start", "Start"),
                        PropertyOption("center", "Center"),
                        PropertyOption("end", "End")
                    ],
                    group="Alignment"
                ),
                PropertyDefinition(
                    name="divider",
                    type=PropertyType.BOOLEAN,
                    default_value=False,
                    description="Show dividers between items",
                    group="Appearance"
                ),
            ],
            
            default_values={
                "display": "flex",
                "flexDirection": "column",
                "spacing": "1rem",
                "align": "stretch",
                "divider": False
            },
            
            slots=[
                ComponentSlot(
                    name="items",
                    description="Stack items",
                    accepts=["*"],
                    min_items=0,
                    max_items=None
                )
            ],
            
            constraints=ComponentConstraints(
                allowed_children=["*"]
            ),
            
            accepts_children=True,
            draggable=True,
            droppable=True,
            resizable=True
        )
    
    @staticmethod
    def _create_columns() -> ComponentDefinition:
        """Create columns layout component definition"""
        return ComponentDefinition(
            id="columns",
            name="Columns",
            category=ComponentCategory.LAYOUT,
            icon="view_column",
            description="Multi-column layout",
            tags=["layout", "columns", "grid", "responsive"],
            
            properties=[
                PropertyDefinition(
                    name="columns",
                    type=PropertyType.NUMBER,
                    default_value=2,
                    description="Number of columns",
                    validation=PropertyValidation(min_value=1, max_value=12),
                    group="Layout"
                ),
                PropertyDefinition(
                    name="gap",
                    type=PropertyType.SIZE,
                    default_value="1rem",
                    description="Gap between columns",
                    group="Spacing"
                ),
                PropertyDefinition(
                    name="responsive",
                    type=PropertyType.BOOLEAN,
                    default_value=True,
                    description="Stack on mobile",
                    group="Responsive"
                ),
            ],
            
            default_values={
                "display": "grid",
                "columns": 2,
                "gap": "1rem",
                "responsive": True
            },
            
            slots=[
                ComponentSlot(
                    name="columns",
                    description="Column content",
                    accepts=["*"],
                    min_items=1,
                    max_items=12
                )
            ],
            
            constraints=ComponentConstraints(
                min_width=200,
                allowed_children=["*"]
            ),
            
            accepts_children=True,
            draggable=True,
            droppable=True,
            resizable=True
        )
    
    # Content Components
    
    @staticmethod
    def _create_heading() -> ComponentDefinition:
        """Create heading component definition"""
        return ComponentDefinition(
            id="heading",
            name="Heading",
            category=ComponentCategory.CONTENT,
            icon="title",
            description="Heading text (h1-h6)",
            tags=["text", "heading", "title", "typography"],
            
            properties=[
                PropertyDefinition(
                    name="text",
                    type=PropertyType.STRING,
                    default_value="Heading",
                    description="Heading text",
                    required=True,
                    group="Content"
                ),
                PropertyDefinition(
                    name="level",
                    type=PropertyType.SELECT,
                    default_value="2",
                    description="Heading level",
                    options=[
                        PropertyOption("1", "H1"),
                        PropertyOption("2", "H2"),
                        PropertyOption("3", "H3"),
                        PropertyOption("4", "H4"),
                        PropertyOption("5", "H5"),
                        PropertyOption("6", "H6")
                    ],
                    group="Typography"
                ),
                PropertyDefinition(
                    name="align",
                    type=PropertyType.SELECT,
                    default_value="left",
                    description="Text alignment",
                    options=[
                        PropertyOption("left", "Left"),
                        PropertyOption("center", "Center"),
                        PropertyOption("right", "Right"),
                        PropertyOption("justify", "Justify")
                    ],
                    group="Typography"
                ),
                PropertyDefinition(
                    name="color",
                    type=PropertyType.COLOR,
                    default_value="inherit",
                    description="Text color",
                    group="Appearance"
                ),
            ],
            
            default_values={
                "text": "Heading",
                "level": "2",
                "align": "left",
                "color": "inherit"
            },
            
            constraints=ComponentConstraints(
                forbidden_children=["*"]  # Headings don't accept children
            ),
            
            accepts_children=False,
            draggable=True,
            resizable=True
        )
    
    @staticmethod
    def _create_paragraph() -> ComponentDefinition:
        """Create paragraph component definition"""
        return ComponentDefinition(
            id="paragraph",
            name="Paragraph",
            category=ComponentCategory.CONTENT,
            icon="subject",
            description="Paragraph text block",
            tags=["text", "paragraph", "content", "typography"],
            
            properties=[
                PropertyDefinition(
                    name="text",
                    type=PropertyType.STRING,
                    default_value="Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                    description="Paragraph text",
                    required=True,
                    group="Content"
                ),
                PropertyDefinition(
                    name="align",
                    type=PropertyType.SELECT,
                    default_value="left",
                    description="Text alignment",
                    options=[
                        PropertyOption("left", "Left"),
                        PropertyOption("center", "Center"),
                        PropertyOption("right", "Right"),
                        PropertyOption("justify", "Justify")
                    ],
                    group="Typography"
                ),
                PropertyDefinition(
                    name="fontSize",
                    type=PropertyType.SIZE,
                    default_value="1rem",
                    description="Font size",
                    group="Typography"
                ),
                PropertyDefinition(
                    name="lineHeight",
                    type=PropertyType.NUMBER,
                    default_value=1.5,
                    description="Line height",
                    validation=PropertyValidation(min_value=1, max_value=3),
                    group="Typography"
                ),
                PropertyDefinition(
                    name="color",
                    type=PropertyType.COLOR,
                    default_value="inherit",
                    description="Text color",
                    group="Appearance"
                ),
            ],
            
            default_values={
                "text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                "align": "left",
                "fontSize": "1rem",
                "lineHeight": 1.5,
                "color": "inherit"
            },
            
            constraints=ComponentConstraints(
                allowed_children=["text", "link", "icon"]  # Allow inline elements
            ),
            
            accepts_children=True,
            draggable=True,
            resizable=True
        )
    
    @staticmethod
    def _create_text() -> ComponentDefinition:
        """Create text span component definition"""
        return ComponentDefinition(
            id="text",
            name="Text",
            category=ComponentCategory.CONTENT,
            icon="text_fields",
            description="Inline text element",
            tags=["text", "span", "inline", "typography"],
            
            properties=[
                PropertyDefinition(
                    name="text",
                    type=PropertyType.STRING,
                    default_value="Text",
                    description="Text content",
                    required=True,
                    group="Content"
                ),
                PropertyDefinition(
                    name="fontWeight",
                    type=PropertyType.SELECT,
                    default_value="normal",
                    description="Font weight",
                    options=[
                        PropertyOption("normal", "Normal"),
                        PropertyOption("bold", "Bold"),
                        PropertyOption("lighter", "Lighter"),
                        PropertyOption("100", "100"),
                        PropertyOption("200", "200"),
                        PropertyOption("300", "300"),
                        PropertyOption("400", "400"),
                        PropertyOption("500", "500"),
                        PropertyOption("600", "600"),
                        PropertyOption("700", "700"),
                        PropertyOption("800", "800"),
                        PropertyOption("900", "900")
                    ],
                    group="Typography"
                ),
                PropertyDefinition(
                    name="fontStyle",
                    type=PropertyType.SELECT,
                    default_value="normal",
                    description="Font style",
                    options=[
                        PropertyOption("normal", "Normal"),
                        PropertyOption("italic", "Italic")
                    ],
                    group="Typography"
                ),
                PropertyDefinition(
                    name="textDecoration",
                    type=PropertyType.SELECT,
                    default_value="none",
                    description="Text decoration",
                    options=[
                        PropertyOption("none", "None"),
                        PropertyOption("underline", "Underline"),
                        PropertyOption("overline", "Overline"),
                        PropertyOption("line-through", "Line Through")
                    ],
                    group="Typography"
                ),
                PropertyDefinition(
                    name="color",
                    type=PropertyType.COLOR,
                    default_value="inherit",
                    description="Text color",
                    group="Appearance"
                ),
            ],
            
            default_values={
                "text": "Text",
                "fontWeight": "normal",
                "fontStyle": "normal",
                "textDecoration": "none",
                "color": "inherit"
            },
            
            constraints=ComponentConstraints(
                forbidden_children=["*"],  # Text spans don't have children
                allowed_parents=["paragraph", "heading", "text", "link", "button", "label"]
            ),
            
            accepts_children=False,
            draggable=True,
            resizable=False
        )
    
    @staticmethod
    def _create_image() -> ComponentDefinition:
        """Create image component definition"""
        return ComponentDefinition(
            id="image",
            name="Image",
            category=ComponentCategory.MEDIA,
            icon="image",
            description="Image element with responsive support",
            tags=["media", "image", "img", "picture", "responsive"],
            
            properties=[
                PropertyDefinition(
                    name="src",
                    type=PropertyType.URL,
                    default_value="https://via.placeholder.com/300x200",
                    description="Image source URL",
                    required=True,
                    group="Content"
                ),
                PropertyDefinition(
                    name="alt",
                    type=PropertyType.STRING,
                    default_value="",
                    description="Alternative text for accessibility",
                    required=True,
                    group="Content"
                ),
                PropertyDefinition(
                    name="width",
                    type=PropertyType.SIZE,
                    default_value="100%",
                    description="Image width",
                    group="Dimensions"
                ),
                PropertyDefinition(
                    name="height",
                    type=PropertyType.SIZE,
                    default_value="auto",
                    description="Image height",
                    group="Dimensions"
                ),
                PropertyDefinition(
                    name="objectFit",
                    type=PropertyType.SELECT,
                    default_value="cover",
                    description="How image fits container",
                    options=[
                        PropertyOption("fill", "Fill"),
                        PropertyOption("contain", "Contain"),
                        PropertyOption("cover", "Cover"),
                        PropertyOption("none", "None"),
                        PropertyOption("scale-down", "Scale Down")
                    ],
                    group="Appearance"
                ),
                PropertyDefinition(
                    name="borderRadius",
                    type=PropertyType.SIZE,
                    default_value="0",
                    description="Corner radius",
                    group="Appearance"
                ),
                PropertyDefinition(
                    name="loading",
                    type=PropertyType.SELECT,
                    default_value="lazy",
                    description="Loading behavior",
                    options=[
                        PropertyOption("lazy", "Lazy"),
                        PropertyOption("eager", "Eager")
                    ],
                    group="Performance"
                ),
            ],
            
            default_values={
                "src": "https://via.placeholder.com/300x200",
                "alt": "",
                "width": "100%",
                "height": "auto",
                "objectFit": "cover",
                "borderRadius": "0",
                "loading": "lazy"
            },
            
            constraints=ComponentConstraints(
                forbidden_children=["*"],  # Images don't have children
                min_width=50,
                min_height=50
            ),
            
            accepts_children=False,
            draggable=True,
            resizable=True
        )
    
    @staticmethod
    def _create_video() -> ComponentDefinition:
        """Create video component definition"""
        return ComponentDefinition(
            id="video",
            name="Video",
            category=ComponentCategory.MEDIA,
            icon="videocam",
            description="Video player with controls",
            tags=["media", "video", "player", "multimedia"],
            
            properties=[
                PropertyDefinition(
                    name="src",
                    type=PropertyType.URL,
                    default_value="",
                    description="Video source URL",
                    required=True,
                    group="Content"
                ),
                PropertyDefinition(
                    name="poster",
                    type=PropertyType.URL,
                    default_value="",
                    description="Poster image URL",
                    group="Content"
                ),
                PropertyDefinition(
                    name="width",
                    type=PropertyType.SIZE,
                    default_value="100%",
                    description="Video width",
                    group="Dimensions"
                ),
                PropertyDefinition(
                    name="height",
                    type=PropertyType.SIZE,
                    default_value="auto",
                    description="Video height",
                    group="Dimensions"
                ),
                PropertyDefinition(
                    name="controls",
                    type=PropertyType.BOOLEAN,
                    default_value=True,
                    description="Show video controls",
                    group="Playback"
                ),
                PropertyDefinition(
                    name="autoplay",
                    type=PropertyType.BOOLEAN,
                    default_value=False,
                    description="Autoplay video",
                    group="Playback"
                ),
                PropertyDefinition(
                    name="loop",
                    type=PropertyType.BOOLEAN,
                    default_value=False,
                    description="Loop video",
                    group="Playback"
                ),
                PropertyDefinition(
                    name="muted",
                    type=PropertyType.BOOLEAN,
                    default_value=False,
                    description="Mute video",
                    group="Playback"
                ),
            ],
            
            default_values={
                "src": "",
                "poster": "",
                "width": "100%",
                "height": "auto",
                "controls": True,
                "autoplay": False,
                "loop": False,
                "muted": False
            },
            
            constraints=ComponentConstraints(
                forbidden_children=["*"],
                min_width=100,
                min_height=100
            ),
            
            accepts_children=False,
            draggable=True,
            resizable=True
        )
    
    @staticmethod
    def _create_icon() -> ComponentDefinition:
        """Create icon component definition"""
        return ComponentDefinition(
            id="icon",
            name="Icon",
            category=ComponentCategory.CONTENT,
            icon="emoji_symbols",
            description="Icon from icon library",
            tags=["icon", "symbol", "graphic", "ui"],
            
            properties=[
                PropertyDefinition(
                    name="icon",
                    type=PropertyType.ICON,
                    default_value="star",
                    description="Icon name",
                    required=True,
                    group="Content"
                ),
                PropertyDefinition(
                    name="size",
                    type=PropertyType.SIZE,
                    default_value="24px",
                    description="Icon size",
                    group="Dimensions"
                ),
                PropertyDefinition(
                    name="color",
                    type=PropertyType.COLOR,
                    default_value="currentColor",
                    description="Icon color",
                    group="Appearance"
                ),
                PropertyDefinition(
                    name="rotation",
                    type=PropertyType.NUMBER,
                    default_value=0,
                    description="Rotation in degrees",
                    validation=PropertyValidation(min_value=-360, max_value=360),
                    group="Transform"
                ),
            ],
            
            default_values={
                "icon": "star",
                "size": "24px",
                "color": "currentColor",
                "rotation": 0
            },
            
            constraints=ComponentConstraints(
                forbidden_children=["*"],
                min_width=16,
                min_height=16,
                max_width=200,
                max_height=200
            ),
            
            accepts_children=False,
            draggable=True,
            resizable=True,
            rotatable=True
        )
    
    # Form Components
    
    @staticmethod
    def _create_form() -> ComponentDefinition:
        """Create form component definition"""
        return ComponentDefinition(
            id="form",
            name="Form",
            category=ComponentCategory.FORMS,
            icon="edit_note",
            description="Form container for input elements",
            tags=["form", "input", "data", "submit"],
            
            properties=[
                PropertyDefinition(
                    name="action",
                    type=PropertyType.URL,
                    default_value="#",
                    description="Form submission URL",
                    group="Form"
                ),
                PropertyDefinition(
                    name="method",
                    type=PropertyType.SELECT,
                    default_value="POST",
                    description="HTTP method",
                    options=[
                        PropertyOption("GET", "GET"),
                        PropertyOption("POST", "POST")
                    ],
                    group="Form"
                ),
                PropertyDefinition(
                    name="name",
                    type=PropertyType.STRING,
                    default_value="",
                    description="Form name",
                    group="Form"
                ),
                PropertyDefinition(
                    name="novalidate",
                    type=PropertyType.BOOLEAN,
                    default_value=False,
                    description="Disable browser validation",
                    group="Validation"
                ),
            ],
            
            default_values={
                "action": "#",
                "method": "POST",
                "name": "",
                "novalidate": False
            },
            
            slots=[
                ComponentSlot(
                    name="fields",
                    description="Form fields",
                    accepts=["input", "textarea", "select", "checkbox", "radio", "label", "fieldset", "container", "flex", "stack"],
                    min_items=0,
                    max_items=None
                ),
                ComponentSlot(
                    name="actions",
                    description="Form actions",
                    accepts=["button", "container", "flex"],
                    min_items=0,
                    max_items=None
                )
            ],
            
            constraints=ComponentConstraints(
                allowed_children=["input", "textarea", "select", "checkbox", "radio", "button", "label", "fieldset", "container", "flex", "stack"],
                forbidden_parents=["form"]  # Forms can't be nested
            ),
            
            accepts_children=True,
            draggable=True,
            droppable=True,
            resizable=True
        )
    
    @staticmethod
    def _create_input() -> ComponentDefinition:
        """Create input component definition"""
        return ComponentDefinition(
            id="input",
            name="Input",
            category=ComponentCategory.FORMS,
            icon="input",
            description="Text input field",
            tags=["form", "input", "text", "field"],
            
            properties=[
                PropertyDefinition(
                    name="type",
                    type=PropertyType.SELECT,
                    default_value="text",
                    description="Input type",
                    options=[
                        PropertyOption("text", "Text"),
                        PropertyOption("email", "Email"),
                        PropertyOption("password", "Password"),
                        PropertyOption("number", "Number"),
                        PropertyOption("tel", "Telephone"),
                        PropertyOption("url", "URL"),
                        PropertyOption("search", "Search"),
                        PropertyOption("date", "Date"),
                        PropertyOption("time", "Time"),
                        PropertyOption("datetime-local", "Date & Time"),
                        PropertyOption("color", "Color"),
                        PropertyOption("file", "File")
                    ],
                    group="Input"
                ),
                PropertyDefinition(
                    name="name",
                    type=PropertyType.STRING,
                    default_value="",
                    description="Field name",
                    required=True,
                    group="Input"
                ),
                PropertyDefinition(
                    name="placeholder",
                    type=PropertyType.STRING,
                    default_value="Enter text...",
                    description="Placeholder text",
                    group="Input"
                ),
                PropertyDefinition(
                    name="value",
                    type=PropertyType.STRING,
                    default_value="",
                    description="Default value",
                    group="Input"
                ),
                PropertyDefinition(
                    name="required",
                    type=PropertyType.BOOLEAN,
                    default_value=False,
                    description="Required field",
                    group="Validation"
                ),
                PropertyDefinition(
                    name="disabled",
                    type=PropertyType.BOOLEAN,
                    default_value=False,
                    description="Disabled state",
                    group="State"
                ),
                PropertyDefinition(
                    name="readonly",
                    type=PropertyType.BOOLEAN,
                    default_value=False,
                    description="Read-only state",
                    group="State"
                ),
                PropertyDefinition(
                    name="width",
                    type=PropertyType.SIZE,
                    default_value="100%",
                    description="Input width",
                    group="Dimensions"
                ),
            ],
            
            default_values={
                "type": "text",
                "name": "",
                "placeholder": "Enter text...",
                "value": "",
                "required": False,
                "disabled": False,
                "readonly": False,
                "width": "100%"
            },
            
            constraints=ComponentConstraints(
                forbidden_children=["*"],
                allowed_parents=["form", "label", "container", "flex", "stack", "grid", "section"],
                min_width=100
            ),
            
            accepts_children=False,
            draggable=True,
            resizable=True
        )
    
    @staticmethod
    def _create_textarea() -> ComponentDefinition:
        """Create textarea component definition"""
        return ComponentDefinition(
            id="textarea",
            name="Textarea",
            category=ComponentCategory.FORMS,
            icon="notes",
            description="Multi-line text input",
            tags=["form", "textarea", "text", "multiline"],
            
            properties=[
                PropertyDefinition(
                    name="name",
                    type=PropertyType.STRING,
                    default_value="",
                    description="Field name",
                    required=True,
                    group="Input"
                ),
                PropertyDefinition(
                    name="placeholder",
                    type=PropertyType.STRING,
                    default_value="Enter text...",
                    description="Placeholder text",
                    group="Input"
                ),
                PropertyDefinition(
                    name="value",
                    type=PropertyType.STRING,
                    default_value="",
                    description="Default value",
                    group="Input"
                ),
                PropertyDefinition(
                    name="rows",
                    type=PropertyType.NUMBER,
                    default_value=4,
                    description="Number of rows",
                    validation=PropertyValidation(min_value=1, max_value=50),
                    group="Dimensions"
                ),
                PropertyDefinition(
                    name="cols",
                    type=PropertyType.NUMBER,
                    default_value=50,
                    description="Number of columns",
                    validation=PropertyValidation(min_value=1, max_value=200),
                    group="Dimensions"
                ),
                PropertyDefinition(
                    name="maxlength",
                    type=PropertyType.NUMBER,
                    default_value=0,
                    description="Maximum length (0 = no limit)",
                    validation=PropertyValidation(min_value=0),
                    group="Validation"
                ),
                PropertyDefinition(
                    name="required",
                    type=PropertyType.BOOLEAN,
                    default_value=False,
                    description="Required field",
                    group="Validation"
                ),
                PropertyDefinition(
                    name="resize",
                    type=PropertyType.SELECT,
                    default_value="vertical",
                    description="Resize behavior",
                    options=[
                        PropertyOption("none", "None"),
                        PropertyOption("vertical", "Vertical"),
                        PropertyOption("horizontal", "Horizontal"),
                        PropertyOption("both", "Both")
                    ],
                    group="Behavior"
                ),
            ],
            
            default_values={
                "name": "",
                "placeholder": "Enter text...",
                "value": "",
                "rows": 4,
                "cols": 50,
                "maxlength": 0,
                "required": False,
                "resize": "vertical"
            },
            
            constraints=ComponentConstraints(
                forbidden_children=["*"],
                allowed_parents=["form", "label", "container", "flex", "stack", "grid", "section"],
                min_width=100,
                min_height=60
            ),
            
            accepts_children=False,
            draggable=True,
            resizable=True
        )
    
    @staticmethod
    def _create_select() -> ComponentDefinition:
        """Create select dropdown component definition"""
        return ComponentDefinition(
            id="select",
            name="Select",
            category=ComponentCategory.FORMS,
            icon="arrow_drop_down_circle",
            description="Dropdown selection input",
            tags=["form", "select", "dropdown", "choice"],
            
            properties=[
                PropertyDefinition(
                    name="name",
                    type=PropertyType.STRING,
                    default_value="",
                    description="Field name",
                    required=True,
                    group="Input"
                ),
                PropertyDefinition(
                    name="options",
                    type=PropertyType.ARRAY,
                    default_value=[
                        {"value": "option1", "label": "Option 1"},
                        {"value": "option2", "label": "Option 2"},
                        {"value": "option3", "label": "Option 3"}
                    ],
                    description="Select options",
                    required=True,
                    group="Options"
                ),
                PropertyDefinition(
                    name="value",
                    type=PropertyType.STRING,
                    default_value="",
                    description="Selected value",
                    group="Input"
                ),
                PropertyDefinition(
                    name="placeholder",
                    type=PropertyType.STRING,
                    default_value="Choose an option...",
                    description="Placeholder text",
                    group="Input"
                ),
                PropertyDefinition(
                    name="required",
                    type=PropertyType.BOOLEAN,
                    default_value=False,
                    description="Required field",
                    group="Validation"
                ),
                PropertyDefinition(
                    name="multiple",
                    type=PropertyType.BOOLEAN,
                    default_value=False,
                    description="Allow multiple selections",
                    group="Behavior"
                ),
                PropertyDefinition(
                    name="size",
                    type=PropertyType.NUMBER,
                    default_value=1,
                    description="Visible options",
                    validation=PropertyValidation(min_value=1, max_value=20),
                    group="Display"
                ),
            ],
            
            default_values={
                "name": "",
                "options": [
                    {"value": "option1", "label": "Option 1"},
                    {"value": "option2", "label": "Option 2"},
                    {"value": "option3", "label": "Option 3"}
                ],
                "value": "",
                "placeholder": "Choose an option...",
                "required": False,
                "multiple": False,
                "size": 1
            },
            
            constraints=ComponentConstraints(
                forbidden_children=["*"],  # Options are defined in properties
                allowed_parents=["form", "label", "container", "flex", "stack", "grid", "section"],
                min_width=100
            ),
            
            accepts_children=False,
            draggable=True,
            resizable=True
        )
    
    @staticmethod
    def _create_checkbox() -> ComponentDefinition:
        """Create checkbox component definition"""
        return ComponentDefinition(
            id="checkbox",
            name="Checkbox",
            category=ComponentCategory.FORMS,
            icon="check_box",
            description="Checkbox input",
            tags=["form", "checkbox", "toggle", "boolean"],
            
            properties=[
                PropertyDefinition(
                    name="name",
                    type=PropertyType.STRING,
                    default_value="",
                    description="Field name",
                    required=True,
                    group="Input"
                ),
                PropertyDefinition(
                    name="label",
                    type=PropertyType.STRING,
                    default_value="Checkbox",
                    description="Checkbox label",
                    required=True,
                    group="Content"
                ),
                PropertyDefinition(
                    name="value",
                    type=PropertyType.STRING,
                    default_value="on",
                    description="Value when checked",
                    group="Input"
                ),
                PropertyDefinition(
                    name="checked",
                    type=PropertyType.BOOLEAN,
                    default_value=False,
                    description="Checked state",
                    group="State"
                ),
                PropertyDefinition(
                    name="required",
                    type=PropertyType.BOOLEAN,
                    default_value=False,
                    description="Required field",
                    group="Validation"
                ),
                PropertyDefinition(
                    name="disabled",
                    type=PropertyType.BOOLEAN,
                    default_value=False,
                    description="Disabled state",
                    group="State"
                ),
            ],
            
            default_values={
                "name": "",
                "label": "Checkbox",
                "value": "on",
                "checked": False,
                "required": False,
                "disabled": False
            },
            
            constraints=ComponentConstraints(
                forbidden_children=["*"],
                allowed_parents=["form", "container", "flex", "stack", "grid", "section"]
            ),
            
            accepts_children=False,
            draggable=True,
            resizable=False
        )
    
    @staticmethod
    def _create_radio() -> ComponentDefinition:
        """Create radio button component definition"""
        return ComponentDefinition(
            id="radio",
            name="Radio",
            category=ComponentCategory.FORMS,
            icon="radio_button_checked",
            description="Radio button input",
            tags=["form", "radio", "choice", "option"],
            
            properties=[
                PropertyDefinition(
                    name="name",
                    type=PropertyType.STRING,
                    default_value="",
                    description="Radio group name",
                    required=True,
                    group="Input"
                ),
                PropertyDefinition(
                    name="label",
                    type=PropertyType.STRING,
                    default_value="Radio",
                    description="Radio label",
                    required=True,
                    group="Content"
                ),
                PropertyDefinition(
                    name="value",
                    type=PropertyType.STRING,
                    default_value="",
                    description="Radio value",
                    required=True,
                    group="Input"
                ),
                PropertyDefinition(
                    name="checked",
                    type=PropertyType.BOOLEAN,
                    default_value=False,
                    description="Checked state",
                    group="State"
                ),
                PropertyDefinition(
                    name="required",
                    type=PropertyType.BOOLEAN,
                    default_value=False,
                    description="Required field",
                    group="Validation"
                ),
                PropertyDefinition(
                    name="disabled",
                    type=PropertyType.BOOLEAN,
                    default_value=False,
                    description="Disabled state",
                    group="State"
                ),
            ],
            
            default_values={
                "name": "",
                "label": "Radio",
                "value": "",
                "checked": False,
                "required": False,
                "disabled": False
            },
            
            constraints=ComponentConstraints(
                forbidden_children=["*"],
                allowed_parents=["form", "container", "flex", "stack", "grid", "section"]
            ),
            
            accepts_children=False,
            draggable=True,
            resizable=False
        )
    
    @staticmethod
    def _create_button() -> ComponentDefinition:
        """Create button component definition"""
        return ComponentDefinition(
            id="button",
            name="Button",
            category=ComponentCategory.FORMS,
            icon="smart_button",
            description="Interactive button element",
            tags=["button", "action", "click", "submit"],
            
            properties=[
                PropertyDefinition(
                    name="text",
                    type=PropertyType.STRING,
                    default_value="Button",
                    description="Button text",
                    required=True,
                    group="Content"
                ),
                PropertyDefinition(
                    name="type",
                    type=PropertyType.SELECT,
                    default_value="button",
                    description="Button type",
                    options=[
                        PropertyOption("button", "Button"),
                        PropertyOption("submit", "Submit"),
                        PropertyOption("reset", "Reset")
                    ],
                    group="Behavior"
                ),
                PropertyDefinition(
                    name="variant",
                    type=PropertyType.SELECT,
                    default_value="primary",
                    description="Button variant",
                    options=[
                        PropertyOption("primary", "Primary"),
                        PropertyOption("secondary", "Secondary"),
                        PropertyOption("success", "Success"),
                        PropertyOption("danger", "Danger"),
                        PropertyOption("warning", "Warning"),
                        PropertyOption("info", "Info"),
                        PropertyOption("light", "Light"),
                        PropertyOption("dark", "Dark"),
                        PropertyOption("link", "Link")
                    ],
                    group="Appearance"
                ),
                PropertyDefinition(
                    name="size",
                    type=PropertyType.SELECT,
                    default_value="medium",
                    description="Button size",
                    options=[
                        PropertyOption("small", "Small"),
                        PropertyOption("medium", "Medium"),
                        PropertyOption("large", "Large")
                    ],
                    group="Appearance"
                ),
                PropertyDefinition(
                    name="fullWidth",
                    type=PropertyType.BOOLEAN,
                    default_value=False,
                    description="Full width button",
                    group="Layout"
                ),
                PropertyDefinition(
                    name="disabled",
                    type=PropertyType.BOOLEAN,
                    default_value=False,
                    description="Disabled state",
                    group="State"
                ),
                PropertyDefinition(
                    name="loading",
                    type=PropertyType.BOOLEAN,
                    default_value=False,
                    description="Loading state",
                    group="State"
                ),
                PropertyDefinition(
                    name="icon",
                    type=PropertyType.ICON,
                    default_value="",
                    description="Button icon",
                    group="Content"
                ),
                PropertyDefinition(
                    name="iconPosition",
                    type=PropertyType.SELECT,
                    default_value="left",
                    description="Icon position",
                    options=[
                        PropertyOption("left", "Left"),
                        PropertyOption("right", "Right")
                    ],
                    group="Content",
                    depends_on={"icon": {"$ne": ""}}
                ),
            ],
            
            default_values={
                "text": "Button",
                "type": "button",
                "variant": "primary",
                "size": "medium",
                "fullWidth": False,
                "disabled": False,
                "loading": False,
                "icon": "",
                "iconPosition": "left"
            },
            
            slots=[
                ComponentSlot(
                    name="content",
                    description="Button content (text/icon)",
                    accepts=["text", "icon"],
                    min_items=0,
                    max_items=2
                )
            ],
            
            constraints=ComponentConstraints(
                allowed_children=["text", "icon"],
                min_width=60
            ),
            
            accepts_children=True,
            draggable=True,
            resizable=True
        )
    
    @staticmethod
    def _create_label() -> ComponentDefinition:
        """Create label component definition"""
        return ComponentDefinition(
            id="label",
            name="Label",
            category=ComponentCategory.FORMS,
            icon="label",
            description="Form field label",
            tags=["form", "label", "text", "accessibility"],
            
            properties=[
                PropertyDefinition(
                    name="text",
                    type=PropertyType.STRING,
                    default_value="Label",
                    description="Label text",
                    required=True,
                    group="Content"
                ),
                PropertyDefinition(
                    name="for",
                    type=PropertyType.STRING,
                    default_value="",
                    description="Associated field ID",
                    group="Accessibility"
                ),
                PropertyDefinition(
                    name="required",
                    type=PropertyType.BOOLEAN,
                    default_value=False,
                    description="Show required indicator",
                    group="Display"
                ),
            ],
            
            default_values={
                "text": "Label",
                "for": "",
                "required": False
            },
            
            slots=[
                ComponentSlot(
                    name="field",
                    description="Associated form field",
                    accepts=["input", "textarea", "select", "checkbox", "radio"],
                    min_items=0,
                    max_items=1
                )
            ],
            
            constraints=ComponentConstraints(
                allowed_children=["input", "textarea", "select", "checkbox", "radio", "text"],
                allowed_parents=["form", "container", "flex", "stack", "grid", "section"]
            ),
            
            accepts_children=True,
            draggable=True,
            resizable=True
        )
    
    # Navigation Components
    
    @staticmethod
    def _create_navbar() -> ComponentDefinition:
        """Create navbar component definition"""
        return ComponentDefinition(
            id="navbar",
            name="Navbar",
            category=ComponentCategory.NAVIGATION,
            icon="menu",
            description="Navigation bar component",
            tags=["navigation", "navbar", "menu", "header"],
            
            properties=[
                PropertyDefinition(
                    name="brand",
                    type=PropertyType.STRING,
                    default_value="Brand",
                    description="Brand name",
                    group="Content"
                ),
                PropertyDefinition(
                    name="brandLogo",
                    type=PropertyType.URL,
                    default_value="",
                    description="Brand logo URL",
                    group="Content"
                ),
                PropertyDefinition(
                    name="variant",
                    type=PropertyType.SELECT,
                    default_value="light",
                    description="Navbar variant",
                    options=[
                        PropertyOption("light", "Light"),
                        PropertyOption("dark", "Dark"),
                        PropertyOption("primary", "Primary")
                    ],
                    group="Appearance"
                ),
                PropertyDefinition(
                    name="fixed",
                    type=PropertyType.SELECT,
                    default_value="none",
                    description="Fixed position",
                    options=[
                        PropertyOption("none", "None"),
                        PropertyOption("top", "Top"),
                        PropertyOption("bottom", "Bottom")
                    ],
                    group="Layout"
                ),
                PropertyDefinition(
                    name="expand",
                    type=PropertyType.SELECT,
                    default_value="lg",
                    description="Responsive expand",
                    options=[
                        PropertyOption("sm", "Small"),
                        PropertyOption("md", "Medium"),
                        PropertyOption("lg", "Large"),
                        PropertyOption("xl", "Extra Large"),
                        PropertyOption("never", "Never")
                    ],
                    group="Responsive"
                ),
            ],
            
            default_values={
                "brand": "Brand",
                "brandLogo": "",
                "variant": "light",
                "fixed": "none",
                "expand": "lg"
            },
            
            slots=[
                ComponentSlot(
                    name="brand",
                    description="Brand area",
                    accepts=["text", "image", "link", "container"],
                    min_items=0,
                    max_items=1
                ),
                ComponentSlot(
                    name="nav",
                    description="Navigation items",
                    accepts=["link", "button", "dropdown", "container"],
                    min_items=0,
                    max_items=None
                ),
                ComponentSlot(
                    name="actions",
                    description="Action items",
                    accepts=["button", "link", "icon", "container"],
                    min_items=0,
                    max_items=None
                )
            ],
            
            constraints=ComponentConstraints(
                allowed_children=["link", "button", "dropdown", "container", "text", "image"],
                forbidden_parents=["navbar"]  # Navbars can't be nested
            ),
            
            accepts_children=True,
            draggable=True,
            droppable=True,
            resizable=True
        )
    
    @staticmethod
    def _create_sidebar() -> ComponentDefinition:
        """Create sidebar component definition"""
        return ComponentDefinition(
            id="sidebar",
            name="Sidebar",
            category=ComponentCategory.NAVIGATION,
            icon="view_sidebar",
            description="Vertical navigation sidebar",
            tags=["navigation", "sidebar", "menu", "vertical"],
            
            properties=[
                PropertyDefinition(
                    name="width",
                    type=PropertyType.SIZE,
                    default_value="250px",
                    description="Sidebar width",
                    group="Dimensions"
                ),
                PropertyDefinition(
                    name="position",
                    type=PropertyType.SELECT,
                    default_value="left",
                    description="Sidebar position",
                    options=[
                        PropertyOption("left", "Left"),
                        PropertyOption("right", "Right")
                    ],
                    group="Layout"
                ),
                PropertyDefinition(
                    name="collapsible",
                    type=PropertyType.BOOLEAN,
                    default_value=True,
                    description="Can be collapsed",
                    group="Behavior"
                ),
                PropertyDefinition(
                    name="collapsed",
                    type=PropertyType.BOOLEAN,
                    default_value=False,
                    description="Initially collapsed",
                    group="State",
                    depends_on={"collapsible": True}
                ),
                PropertyDefinition(
                    name="variant",
                    type=PropertyType.SELECT,
                    default_value="light",
                    description="Sidebar variant",
                    options=[
                        PropertyOption("light", "Light"),
                        PropertyOption("dark", "Dark")
                    ],
                    group="Appearance"
                ),
            ],
            
            default_values={
                "width": "250px",
                "position": "left",
                "collapsible": True,
                "collapsed": False,
                "variant": "light"
            },
            
            slots=[
                ComponentSlot(
                    name="header",
                    description="Sidebar header",
                    accepts=["container", "text", "image"],
                    min_items=0,
                    max_items=1
                ),
                ComponentSlot(
                    name="nav",
                    description="Navigation items",
                    accepts=["link", "button", "container", "stack"],
                    min_items=0,
                    max_items=None
                ),
                ComponentSlot(
                    name="footer",
                    description="Sidebar footer",
                    accepts=["container", "text", "button"],
                    min_items=0,
                    max_items=1
                )
            ],
            
            constraints=ComponentConstraints(
                min_width=150,
                max_width=500,
                allowed_children=["link", "button", "container", "stack", "text", "image"]
            ),
            
            accepts_children=True,
            draggable=True,
            droppable=True,
            resizable=True
        )
    
    @staticmethod
    def _create_tabs() -> ComponentDefinition:
        """Create tabs component definition"""
        return ComponentDefinition(
            id="tabs",
            name="Tabs",
            category=ComponentCategory.NAVIGATION,
            icon="tab",
            description="Tabbed content container",
            tags=["navigation", "tabs", "tabpanel", "content"],
            
            properties=[
                PropertyDefinition(
                    name="tabs",
                    type=PropertyType.ARRAY,
                    default_value=[
                        {"id": "tab1", "label": "Tab 1", "active": True},
                        {"id": "tab2", "label": "Tab 2", "active": False},
                        {"id": "tab3", "label": "Tab 3", "active": False}
                    ],
                    description="Tab definitions",
                    required=True,
                    group="Content"
                ),
                PropertyDefinition(
                    name="variant",
                    type=PropertyType.SELECT,
                    default_value="tabs",
                    description="Tab style",
                    options=[
                        PropertyOption("tabs", "Tabs"),
                        PropertyOption("pills", "Pills"),
                        PropertyOption("underline", "Underline")
                    ],
                    group="Appearance"
                ),
                PropertyDefinition(
                    name="alignment",
                    type=PropertyType.SELECT,
                    default_value="left",
                    description="Tab alignment",
                    options=[
                        PropertyOption("left", "Left"),
                        PropertyOption("center", "Center"),
                        PropertyOption("right", "Right"),
                        PropertyOption("justify", "Justify")
                    ],
                    group="Layout"
                ),
            ],
            
            default_values={
                "tabs": [
                    {"id": "tab1", "label": "Tab 1", "active": True},
                    {"id": "tab2", "label": "Tab 2", "active": False},
                    {"id": "tab3", "label": "Tab 3", "active": False}
                ],
                "variant": "tabs",
                "alignment": "left"
            },
            
            slots=[
                ComponentSlot(
                    name="panels",
                    description="Tab panels",
                    accepts=["container", "section"],
                    min_items=1,
                    max_items=None
                )
            ],
            
            constraints=ComponentConstraints(
                allowed_children=["container", "section"],
                min_width=300
            ),
            
            accepts_children=True,
            draggable=True,
            droppable=True,
            resizable=True
        )
    
    @staticmethod
    def _create_breadcrumb() -> ComponentDefinition:
        """Create breadcrumb component definition"""
        return ComponentDefinition(
            id="breadcrumb",
            name="Breadcrumb",
            category=ComponentCategory.NAVIGATION,
            icon="navigation",
            description="Breadcrumb navigation",
            tags=["navigation", "breadcrumb", "path", "hierarchy"],
            
            properties=[
                PropertyDefinition(
                    name="items",
                    type=PropertyType.ARRAY,
                    default_value=[
                        {"label": "Home", "href": "/"},
                        {"label": "Category", "href": "/category"},
                        {"label": "Current Page", "href": "#", "active": True}
                    ],
                    description="Breadcrumb items",
                    required=True,
                    group="Content"
                ),
                PropertyDefinition(
                    name="separator",
                    type=PropertyType.STRING,
                    default_value="/",
                    description="Item separator",
                    group="Appearance"
                ),
            ],
            
            default_values={
                "items": [
                    {"label": "Home", "href": "/"},
                    {"label": "Category", "href": "/category"},
                    {"label": "Current Page", "href": "#", "active": True}
                ],
                "separator": "/"
            },
            
            constraints=ComponentConstraints(
                forbidden_children=["*"]  # Items defined in properties
            ),
            
            accepts_children=False,
            draggable=True,
            resizable=True
        )
    
    @staticmethod
    def _create_link() -> ComponentDefinition:
        """Create link component definition"""
        return ComponentDefinition(
            id="link",
            name="Link",
            category=ComponentCategory.NAVIGATION,
            icon="link",
            description="Hyperlink element",
            tags=["link", "anchor", "navigation", "href"],
            
            properties=[
                PropertyDefinition(
                    name="text",
                    type=PropertyType.STRING,
                    default_value="Link",
                    description="Link text",
                    required=True,
                    group="Content"
                ),
                PropertyDefinition(
                    name="href",
                    type=PropertyType.URL,
                    default_value="#",
                    description="Link destination",
                    required=True,
                    group="Navigation"
                ),
                PropertyDefinition(
                    name="target",
                    type=PropertyType.SELECT,
                    default_value="_self",
                    description="Link target",
                    options=[
                        PropertyOption("_self", "Same Window"),
                        PropertyOption("_blank", "New Window"),
                        PropertyOption("_parent", "Parent Frame"),
                        PropertyOption("_top", "Top Frame")
                    ],
                    group="Navigation"
                ),
                PropertyDefinition(
                    name="rel",
                    type=PropertyType.STRING,
                    default_value="",
                    description="Link relationship",
                    group="Navigation"
                ),
                PropertyDefinition(
                    name="underline",
                    type=PropertyType.SELECT,
                    default_value="hover",
                    description="Underline behavior",
                    options=[
                        PropertyOption("always", "Always"),
                        PropertyOption("hover", "On Hover"),
                        PropertyOption("none", "Never")
                    ],
                    group="Appearance"
                ),
                PropertyDefinition(
                    name="color",
                    type=PropertyType.COLOR,
                    default_value="#0066cc",
                    description="Link color",
                    group="Appearance"
                ),
            ],
            
            default_values={
                "text": "Link",
                "href": "#",
                "target": "_self",
                "rel": "",
                "underline": "hover",
                "color": "#0066cc"
            },
            
            slots=[
                ComponentSlot(
                    name="content",
                    description="Link content",
                    accepts=["text", "icon"],
                    min_items=0,
                    max_items=2
                )
            ],
            
            constraints=ComponentConstraints(
                allowed_children=["text", "icon"]
            ),
            
            accepts_children=True,
            draggable=True,
            resizable=False
        )
    
    # Data Display Components
    
    @staticmethod
    def _create_table() -> ComponentDefinition:
        """Create table component definition"""
        return ComponentDefinition(
            id="table",
            name="Table",
            category=ComponentCategory.DATA_DISPLAY,
            icon="table_chart",
            description="Data table with rows and columns",
            tags=["table", "data", "grid", "rows", "columns"],
            
            properties=[
                PropertyDefinition(
                    name="columns",
                    type=PropertyType.ARRAY,
                    default_value=[
                        {"key": "name", "label": "Name", "sortable": True},
                        {"key": "email", "label": "Email", "sortable": True},
                        {"key": "role", "label": "Role", "sortable": False}
                    ],
                    description="Table columns",
                    required=True,
                    group="Data"
                ),
                PropertyDefinition(
                    name="data",
                    type=PropertyType.ARRAY,
                    default_value=[
                        {"name": "John Doe", "email": "john@example.com", "role": "Admin"},
                        {"name": "Jane Smith", "email": "jane@example.com", "role": "User"}
                    ],
                    description="Table data",
                    group="Data"
                ),
                PropertyDefinition(
                    name="striped",
                    type=PropertyType.BOOLEAN,
                    default_value=True,
                    description="Striped rows",
                    group="Appearance"
                ),
                PropertyDefinition(
                    name="bordered",
                    type=PropertyType.BOOLEAN,
                    default_value=True,
                    description="Show borders",
                    group="Appearance"
                ),
                PropertyDefinition(
                    name="hover",
                    type=PropertyType.BOOLEAN,
                    default_value=True,
                    description="Hover effect",
                    group="Appearance"
                ),
                PropertyDefinition(
                    name="responsive",
                    type=PropertyType.BOOLEAN,
                    default_value=True,
                    description="Responsive table",
                    group="Responsive"
                ),
                PropertyDefinition(
                    name="sortable",
                    type=PropertyType.BOOLEAN,
                    default_value=True,
                    description="Enable sorting",
                    group="Behavior"
                ),
            ],
            
            default_values={
                "columns": [
                    {"key": "name", "label": "Name", "sortable": True},
                    {"key": "email", "label": "Email", "sortable": True},
                    {"key": "role", "label": "Role", "sortable": False}
                ],
                "data": [
                    {"name": "John Doe", "email": "john@example.com", "role": "Admin"},
                    {"name": "Jane Smith", "email": "jane@example.com", "role": "User"}
                ],
                "striped": True,
                "bordered": True,
                "hover": True,
                "responsive": True,
                "sortable": True
            },
            
            constraints=ComponentConstraints(
                forbidden_children=["*"],  # Table structure is auto-generated
                min_width=300
            ),
            
            accepts_children=False,
            draggable=True,
            resizable=True
        )
    
    @staticmethod
    def _create_list() -> ComponentDefinition:
        """Create list component definition"""
        return ComponentDefinition(
            id="list",
            name="List",
            category=ComponentCategory.DATA_DISPLAY,
            icon="list",
            description="Ordered or unordered list",
            tags=["list", "items", "ul", "ol", "enumeration"],
            
            properties=[
                PropertyDefinition(
                    name="type",
                    type=PropertyType.SELECT,
                    default_value="unordered",
                    description="List type",
                    options=[
                        PropertyOption("unordered", "Unordered (bullets)"),
                        PropertyOption("ordered", "Ordered (numbers)"),
                        PropertyOption("none", "No markers")
                    ],
                    group="Display"
                ),
                PropertyDefinition(
                    name="items",
                    type=PropertyType.ARRAY,
                    default_value=["Item 1", "Item 2", "Item 3"],
                    description="List items",
                    required=True,
                    group="Content"
                ),
                PropertyDefinition(
                    name="spacing",
                    type=PropertyType.SIZE,
                    default_value="0.5rem",
                    description="Item spacing",
                    group="Spacing"
                ),
            ],
            
            default_values={
                "type": "unordered",
                "items": ["Item 1", "Item 2", "Item 3"],
                "spacing": "0.5rem"
            },
            
            slots=[
                ComponentSlot(
                    name="items",
                    description="List items",
                    accepts=["text", "link", "container"],
                    min_items=0,
                    max_items=None
                )
            ],
            
            constraints=ComponentConstraints(
                allowed_children=["text", "link", "container"]
            ),
            
            accepts_children=True,
            draggable=True,
            resizable=True
        )
    
    @staticmethod
    def _create_card() -> ComponentDefinition:
        """Create card component definition"""
        return ComponentDefinition(
            id="card",
            name="Card",
            category=ComponentCategory.DATA_DISPLAY,
            icon="dashboard_customize",
            description="Content card with header, body, and footer",
            tags=["card", "container", "content", "panel"],
            
            properties=[
                PropertyDefinition(
                    name="title",
                    type=PropertyType.STRING,
                    default_value="Card Title",
                    description="Card title",
                    group="Content"
                ),
                PropertyDefinition(
                    name="subtitle",
                    type=PropertyType.STRING,
                    default_value="",
                    description="Card subtitle",
                    group="Content"
                ),
                PropertyDefinition(
                    name="shadow",
                    type=PropertyType.SELECT,
                    default_value="medium",
                    description="Shadow depth",
                    options=[
                        PropertyOption("none", "None"),
                        PropertyOption("small", "Small"),
                        PropertyOption("medium", "Medium"),
                        PropertyOption("large", "Large")
                    ],
                    group="Appearance"
                ),
                PropertyDefinition(
                    name="padding",
                    type=PropertyType.SIZE,
                    default_value="1.5rem",
                    description="Card padding",
                    group="Spacing"
                ),
                PropertyDefinition(
                    name="borderRadius",
                    type=PropertyType.SIZE,
                    default_value="0.5rem",
                    description="Corner radius",
                    group="Appearance"
                ),
            ],
            
            default_values={
                "title": "Card Title",
                "subtitle": "",
                "shadow": "medium",
                "padding": "1.5rem",
                "borderRadius": "0.5rem"
            },
            
            slots=[
                ComponentSlot(
                    name="header",
                    description="Card header",
                    accepts=["text", "heading", "container"],
                    min_items=0,
                    max_items=1
                ),
                ComponentSlot(
                    name="body",
                    description="Card body",
                    accepts=["*"],
                    min_items=0,
                    max_items=None
                ),
                ComponentSlot(
                    name="footer",
                    description="Card footer",
                    accepts=["button", "link", "container"],
                    min_items=0,
                    max_items=1
                )
            ],
            
            constraints=ComponentConstraints(
                allowed_children=["*"],
                min_width=200
            ),
            
            accepts_children=True,
            draggable=True,
            droppable=True,
            resizable=True
        )
    
    @staticmethod
    def _create_badge() -> ComponentDefinition:
        """Create badge component definition"""
        return ComponentDefinition(
            id="badge",
            name="Badge",
            category=ComponentCategory.DATA_DISPLAY,
            icon="sell",
            description="Small label or indicator",
            tags=["badge", "label", "tag", "chip", "indicator"],
            
            properties=[
                PropertyDefinition(
                    name="text",
                    type=PropertyType.STRING,
                    default_value="Badge",
                    description="Badge text",
                    required=True,
                    group="Content"
                ),
                PropertyDefinition(
                    name="variant",
                    type=PropertyType.SELECT,
                    default_value="primary",
                    description="Badge variant",
                    options=[
                        PropertyOption("primary", "Primary"),
                        PropertyOption("secondary", "Secondary"),
                        PropertyOption("success", "Success"),
                        PropertyOption("danger", "Danger"),
                        PropertyOption("warning", "Warning"),
                        PropertyOption("info", "Info"),
                        PropertyOption("light", "Light"),
                        PropertyOption("dark", "Dark")
                    ],
                    group="Appearance"
                ),
                PropertyDefinition(
                    name="pill",
                    type=PropertyType.BOOLEAN,
                    default_value=False,
                    description="Pill shape",
                    group="Appearance"
                ),
            ],
            
            default_values={
                "text": "Badge",
                "variant": "primary",
                "pill": False
            },
            
            constraints=ComponentConstraints(
                forbidden_children=["*"]
            ),
            
            accepts_children=False,
            draggable=True,
            resizable=False
        )
    
    @staticmethod
    def _create_progress() -> ComponentDefinition:
        """Create progress bar component definition"""
        return ComponentDefinition(
            id="progress",
            name="Progress",
            category=ComponentCategory.DATA_DISPLAY,
            icon="linear_scale",
            description="Progress bar indicator",
            tags=["progress", "bar", "loading", "percentage"],
            
            properties=[
                PropertyDefinition(
                    name="value",
                    type=PropertyType.NUMBER,
                    default_value=50,
                    description="Progress value (0-100)",
                    required=True,
                    validation=PropertyValidation(min_value=0, max_value=100),
                    group="Value"
                ),
                PropertyDefinition(
                    name="label",
                    type=PropertyType.STRING,
                    default_value="",
                    description="Progress label",
                    group="Content"
                ),
                PropertyDefinition(
                    name="showPercentage",
                    type=PropertyType.BOOLEAN,
                    default_value=True,
                    description="Show percentage",
                    group="Display"
                ),
                PropertyDefinition(
                    name="variant",
                    type=PropertyType.SELECT,
                    default_value="primary",
                    description="Progress variant",
                    options=[
                        PropertyOption("primary", "Primary"),
                        PropertyOption("success", "Success"),
                        PropertyOption("warning", "Warning"),
                        PropertyOption("danger", "Danger"),
                        PropertyOption("info", "Info")
                    ],
                    group="Appearance"
                ),
                PropertyDefinition(
                    name="striped",
                    type=PropertyType.BOOLEAN,
                    default_value=False,
                    description="Striped appearance",
                    group="Appearance"
                ),
                PropertyDefinition(
                    name="animated",
                    type=PropertyType.BOOLEAN,
                    default_value=False,
                    description="Animated stripes",
                    group="Appearance",
                    depends_on={"striped": True}
                ),
                PropertyDefinition(
                    name="height",
                    type=PropertyType.SIZE,
                    default_value="1rem",
                    description="Progress bar height",
                    group="Dimensions"
                ),
            ],
            
            default_values={
                "value": 50,
                "label": "",
                "showPercentage": True,
                "variant": "primary",
                "striped": False,
                "animated": False,
                "height": "1rem"
            },
            
            constraints=ComponentConstraints(
                forbidden_children=["*"],
                min_width=100
            ),
            
            accepts_children=False,
            draggable=True,
            resizable=True
        )
    
    # Feedback Components
    
    @staticmethod
    def _create_alert() -> ComponentDefinition:
        """Create alert component definition"""
        return ComponentDefinition(
            id="alert",
            name="Alert",
            category=ComponentCategory.FEEDBACK,
            icon="warning",
            description="Alert message box",
            tags=["alert", "message", "notification", "warning", "error"],
            
            properties=[
                PropertyDefinition(
                    name="message",
                    type=PropertyType.STRING,
                    default_value="This is an alert message",
                    description="Alert message",
                    required=True,
                    group="Content"
                ),
                PropertyDefinition(
                    name="title",
                    type=PropertyType.STRING,
                    default_value="",
                    description="Alert title",
                    group="Content"
                ),
                PropertyDefinition(
                    name="variant",
                    type=PropertyType.SELECT,
                    default_value="info",
                    description="Alert variant",
                    options=[
                        PropertyOption("success", "Success"),
                        PropertyOption("danger", "Danger"),
                        PropertyOption("warning", "Warning"),
                        PropertyOption("info", "Info")
                    ],
                    group="Appearance"
                ),
                PropertyDefinition(
                    name="dismissible",
                    type=PropertyType.BOOLEAN,
                    default_value=True,
                    description="Can be dismissed",
                    group="Behavior"
                ),
                PropertyDefinition(
                    name="icon",
                    type=PropertyType.BOOLEAN,
                    default_value=True,
                    description="Show icon",
                    group="Appearance"
                ),
            ],
            
            default_values={
                "message": "This is an alert message",
                "title": "",
                "variant": "info",
                "dismissible": True,
                "icon": True
            },
            
            slots=[
                ComponentSlot(
                    name="content",
                    description="Alert content",
                    accepts=["text", "link", "button"],
                    min_items=0,
                    max_items=None
                )
            ],
            
            constraints=ComponentConstraints(
                allowed_children=["text", "link", "button"],
                min_width=200
            ),
            
            accepts_children=True,
            draggable=True,
            resizable=True
        )
    
    @staticmethod
    def _create_modal() -> ComponentDefinition:
        """Create modal dialog component definition"""
        return ComponentDefinition(
            id="modal",
            name="Modal",
            category=ComponentCategory.FEEDBACK,
            icon="web_asset",
            description="Modal dialog overlay",
            tags=["modal", "dialog", "popup", "overlay"],
            
            properties=[
                PropertyDefinition(
                    name="title",
                    type=PropertyType.STRING,
                    default_value="Modal Title",
                    description="Modal title",
                    required=True,
                    group="Content"
                ),
                PropertyDefinition(
                    name="size",
                    type=PropertyType.SELECT,
                    default_value="medium",
                    description="Modal size",
                    options=[
                        PropertyOption("small", "Small"),
                        PropertyOption("medium", "Medium"),
                        PropertyOption("large", "Large"),
                        PropertyOption("xl", "Extra Large")
                    ],
                    group="Dimensions"
                ),
                PropertyDefinition(
                    name="centered",
                    type=PropertyType.BOOLEAN,
                    default_value=True,
                    description="Vertically centered",
                    group="Layout"
                ),
                PropertyDefinition(
                    name="backdrop",
                    type=PropertyType.SELECT,
                    default_value="true",
                    description="Backdrop behavior",
                    options=[
                        PropertyOption("true", "Click to close"),
                        PropertyOption("static", "Static"),
                        PropertyOption("false", "No backdrop")
                    ],
                    group="Behavior"
                ),
                PropertyDefinition(
                    name="keyboard",
                    type=PropertyType.BOOLEAN,
                    default_value=True,
                    description="Close on Escape",
                    group="Behavior"
                ),
            ],
            
            default_values={
                "title": "Modal Title",
                "size": "medium",
                "centered": True,
                "backdrop": "true",
                "keyboard": True
            },
            
            slots=[
                ComponentSlot(
                    name="header",
                    description="Modal header",
                    accepts=["text", "heading", "button"],
                    min_items=0,
                    max_items=1
                ),
                ComponentSlot(
                    name="body",
                    description="Modal body",
                    accepts=["*"],
                    min_items=0,
                    max_items=None
                ),
                ComponentSlot(
                    name="footer",
                    description="Modal footer",
                    accepts=["button", "link", "container"],
                    min_items=0,
                    max_items=1
                )
            ],
            
            constraints=ComponentConstraints(
                allowed_children=["*"],
                singleton=True  # Only one modal instance
            ),
            
            accepts_children=True,
            draggable=False,  # Modals aren't draggable
            resizable=False
        )
    
    @staticmethod
    def _create_tooltip() -> ComponentDefinition:
        """Create tooltip component definition"""
        return ComponentDefinition(
            id="tooltip",
            name="Tooltip",
            category=ComponentCategory.FEEDBACK,
            icon="help",
            description="Hover tooltip",
            tags=["tooltip", "hover", "hint", "popover"],
            
            properties=[
                PropertyDefinition(
                    name="text",
                    type=PropertyType.STRING,
                    default_value="Tooltip text",
                    description="Tooltip content",
                    required=True,
                    group="Content"
                ),
                PropertyDefinition(
                    name="placement",
                    type=PropertyType.SELECT,
                    default_value="top",
                    description="Tooltip placement",
                    options=[
                        PropertyOption("top", "Top"),
                        PropertyOption("bottom", "Bottom"),
                        PropertyOption("left", "Left"),
                        PropertyOption("right", "Right")
                    ],
                    group="Position"
                ),
                PropertyDefinition(
                    name="trigger",
                    type=PropertyType.SELECT,
                    default_value="hover",
                    description="Trigger event",
                    options=[
                        PropertyOption("hover", "Hover"),
                        PropertyOption("click", "Click"),
                        PropertyOption("focus", "Focus")
                    ],
                    group="Behavior"
                ),
                PropertyDefinition(
                    name="delay",
                    type=PropertyType.NUMBER,
                    default_value=0,
                    description="Show delay (ms)",
                    validation=PropertyValidation(min_value=0, max_value=5000),
                    group="Behavior"
                ),
            ],
            
            default_values={
                "text": "Tooltip text",
                "placement": "top",
                "trigger": "hover",
                "delay": 0
            },
            
            slots=[
                ComponentSlot(
                    name="target",
                    description="Target element",
                    accepts=["*"],
                    min_items=1,
                    max_items=1,
                    required=True
                )
            ],
            
            constraints=ComponentConstraints(
                allowed_children=["*"],
                max_instances_per_parent=1
            ),
            
            accepts_children=True,
            draggable=True,
            resizable=False
        )
    
    @staticmethod
    def _create_toast() -> ComponentDefinition:
        """Create toast notification component definition"""
        return ComponentDefinition(
            id="toast",
            name="Toast",
            category=ComponentCategory.FEEDBACK,
            icon="notifications",
            description="Toast notification",
            tags=["toast", "notification", "message", "snackbar"],
            
            properties=[
                PropertyDefinition(
                    name="message",
                    type=PropertyType.STRING,
                    default_value="Toast notification",
                    description="Toast message",
                    required=True,
                    group="Content"
                ),
                PropertyDefinition(
                    name="title",
                    type=PropertyType.STRING,
                    default_value="",
                    description="Toast title",
                    group="Content"
                ),
                PropertyDefinition(
                    name="variant",
                    type=PropertyType.SELECT,
                    default_value="default",
                    description="Toast variant",
                    options=[
                        PropertyOption("default", "Default"),
                        PropertyOption("success", "Success"),
                        PropertyOption("danger", "Danger"),
                        PropertyOption("warning", "Warning"),
                        PropertyOption("info", "Info")
                    ],
                    group="Appearance"
                ),
                PropertyDefinition(
                    name="position",
                    type=PropertyType.SELECT,
                    default_value="top-right",
                    description="Screen position",
                    options=[
                        PropertyOption("top-left", "Top Left"),
                        PropertyOption("top-center", "Top Center"),
                        PropertyOption("top-right", "Top Right"),
                        PropertyOption("bottom-left", "Bottom Left"),
                        PropertyOption("bottom-center", "Bottom Center"),
                        PropertyOption("bottom-right", "Bottom Right")
                    ],
                    group="Position"
                ),
                PropertyDefinition(
                    name="duration",
                    type=PropertyType.NUMBER,
                    default_value=5000,
                    description="Auto-hide duration (ms)",
                    validation=PropertyValidation(min_value=0, max_value=30000),
                    group="Behavior"
                ),
                PropertyDefinition(
                    name="dismissible",
                    type=PropertyType.BOOLEAN,
                    default_value=True,
                    description="Can be dismissed",
                    group="Behavior"
                ),
            ],
            
            default_values={
                "message": "Toast notification",
                "title": "",
                "variant": "default",
                "position": "top-right",
                "duration": 5000,
                "dismissible": True
            },
            
            constraints=ComponentConstraints(
                forbidden_children=["*"],
                singleton=False  # Multiple toasts allowed
            ),
            
            accepts_children=False,
            draggable=False,  # Toasts aren't draggable
            resizable=False
        )