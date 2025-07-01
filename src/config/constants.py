"""Configuration constants for Canvas Editor"""

# Panel configuration constants
SIDEBAR_WIDTH = 80
SIDEBAR_MIN_WIDTH = 60
SIDEBAR_MAX_WIDTH = 120

COMPONENTS_WIDTH = 280
COMPONENTS_MIN_WIDTH = 200
COMPONENTS_MAX_WIDTH = 400

PROPERTIES_WIDTH = 320
PROPERTIES_MIN_WIDTH = 250
PROPERTIES_MAX_WIDTH = 500

CANVAS_MIN_WIDTH = 400

# Resize handle configuration
RESIZE_HANDLE_WIDTH = 4
RESIZE_HANDLE_COLOR = "#E0E0E0"  # ft.Colors.GREY_300
RESIZE_HANDLE_HOVER_COLOR = "#2196F3"  # ft.Colors.BLUE_400

# Storage keys
STORAGE_KEY_WINDOW = "canvas_editor_window_state"
STORAGE_KEY_PANELS = "canvas_editor_panel_state"
STORAGE_KEY_PREFERENCES = "canvas_editor_preferences"
STORAGE_KEY_RECENT_PROJECTS = "canvas_editor_recent_projects"
STORAGE_KEY_CURRENT_PROJECT = "canvas_editor_current_project"
STORAGE_KEY_THEME = "canvas_editor_theme"

# Project configuration
MAX_RECENT_PROJECTS = 10
AUTO_SAVE_INTERVAL = 300  # 5 minutes in seconds
MAX_PROJECT_FILES = 1000
SUPPORTED_WEB_EXTENSIONS = {'.html', '.htm', '.css', '.js', '.jsx', '.ts', '.tsx', '.json', '.md', '.txt', '.xml', '.svg', '.vue', '.svelte'}
SUPPORTED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico'}

# Additional project management constants
PROJECT_FILE_SIZE_LIMIT = 50 * 1024 * 1024  # 50MB
PROJECT_PATH_MAX_LENGTH = 260  # Windows limit
PROJECT_SCAN_BATCH_SIZE = 100
PROJECT_AUTO_SAVE_RETRY_ATTEMPTS = 3

# Theme configuration
THEMES = {
    "light": {
        "primary": "#5E6AD2",
        "primary_light": "#818CF8",
        "primary_dark": "#4C1D95",
        "secondary": "#F59E0B",
        "accent": "#06B6D4",
        "success": "#10B981",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "background": "#FAFBFC",
        "surface": "#FFFFFF",
        "text": "#212529",
        "text_secondary": "#6C757D"
    },
    "dark": {
        "primary": "#818CF8",
        "primary_light": "#A5B4FC",
        "primary_dark": "#5E6AD2",
        "secondary": "#FBB040",
        "accent": "#22D3EE",
        "success": "#34D399",
        "warning": "#FBB040",
        "error": "#F87171",
        "background": "#0F172A",
        "surface": "#1E293B",
        "text": "#F1F5F9",
        "text_secondary": "#94A3B8"
    }
}

# Component configuration
COMPONENT_CATEGORIES = [
    {
        "name": "Layout",
        "icon": "view_quilt",
        "components": [
            {"name": "Section", "type": "section", "description": "Container with padding"},
            {"name": "Grid", "type": "grid", "description": "Responsive columns"},
            {"name": "Flex", "type": "flex", "description": "Flexible box layout"},
            {"name": "Stack", "type": "stack", "description": "Vertical stack"}
        ]
    },
    {
        "name": "OC2 Components",
        "icon": "widgets",
        "components": [
            {"name": "Tab Container", "type": "tabs", "description": "Multi-tab layout"},
            {"name": "Accordion", "type": "accordion", "description": "Expandable content"},
            {"name": "KPI Chart", "type": "kpi_chart", "description": "Data visualization"},
            {"name": "Timeline", "type": "timeline", "description": "Event timeline"}
        ]
    },
    {
        "name": "Content",
        "icon": "article",
        "components": [
            {"name": "Rich Text", "type": "rich_text", "description": "WYSIWYG editor"},
            {"name": "Image", "type": "image", "description": "Upload or URL"},
            {"name": "Video", "type": "video", "description": "Embed video"},
            {"name": "Code Block", "type": "code", "description": "Syntax highlighted"}
        ]
    },
    {
        "name": "Forms",
        "icon": "edit_note",
        "components": [
            {"name": "Input", "type": "input", "description": "Text input field"},
            {"name": "Select", "type": "select", "description": "Dropdown selection"},
            {"name": "Checkbox", "type": "checkbox", "description": "Multiple choice"},
            {"name": "Button", "type": "button", "description": "Action button"}
        ]
    }
]

# Editor configuration
EDITOR_TOOLBAR_ITEMS = [
    {"name": "Bold", "icon": "format_bold", "command": "bold"},
    {"name": "Italic", "icon": "format_italic", "command": "italic"},
    {"name": "Underline", "icon": "format_underlined", "command": "underline"},
    "separator",
    {"name": "Link", "icon": "link", "command": "link"},
    {"name": "Reference", "text": "REF", "command": "reference"},
    "separator",
    {"name": "Bullet List", "icon": "format_list_bulleted", "command": "bullet_list"},
    {"name": "Numbered List", "icon": "format_list_numbered", "command": "numbered_list"},
]

# Device presets for responsive design
DEVICE_PRESETS = {
    "desktop": {"width": 1920, "height": 1080, "icon": "computer"},
    "laptop": {"width": 1366, "height": 768, "icon": "laptop"},
    "tablet": {"width": 768, "height": 1024, "icon": "tablet"},
    "mobile": {"width": 375, "height": 812, "icon": "smartphone"}
}

# Keyboard shortcuts
KEYBOARD_SHORTCUTS = {
    "save": "Ctrl+S",
    "undo": "Ctrl+Z",
    "redo": "Ctrl+Y",
    "copy": "Ctrl+C",
    "paste": "Ctrl+V",
    "cut": "Ctrl+X",
    "delete": "Delete",
    "duplicate": "Ctrl+D",
    "preview": "Ctrl+P",
    "export": "Ctrl+E",
    "import": "Ctrl+I"
}