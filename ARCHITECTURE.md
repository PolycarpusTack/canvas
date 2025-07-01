# Canvas Editor - Architecture Documentation

## Overview

Canvas Editor has been refactored from a monolithic single-file application (2,127 lines) into a modular architecture with clear separation of concerns. This document describes the new structure and how components interact.

## Directory Structure

```
canvas/
├── src/
│   ├── __init__.py
│   ├── main.py                    # Entry point (43 lines)
│   ├── app.py                     # Main application class
│   │
│   ├── config/                    # Configuration and constants
│   │   ├── __init__.py
│   │   └── constants.py           # All app constants
│   │
│   ├── models/                    # Data models
│   │   ├── __init__.py
│   │   ├── project.py             # Project-related models
│   │   └── component.py           # Component models
│   │
│   ├── ui/                        # User interface components
│   │   ├── __init__.py
│   │   ├── components/            # Reusable UI components
│   │   │   ├── __init__.py
│   │   │   ├── resize_handle.py   # Panel resize handles
│   │   │   ├── toolbar.py         # Floating toolbar
│   │   │   └── rich_editor.py     # Rich text editor
│   │   ├── panels/                # Main UI panels
│   │   │   ├── __init__.py
│   │   │   ├── sidebar.py         # Left navigation
│   │   │   ├── components.py      # Component library
│   │   │   ├── canvas.py          # Main editing area
│   │   │   └── properties.py      # Properties editor
│   │   └── dialogs/               # Modal dialogs
│   │       ├── __init__.py
│   │       └── project_dialog.py  # Project dialogs
│   │
│   ├── managers/                  # Business logic managers
│   │   ├── __init__.py
│   │   ├── project.py             # Project management
│   │   └── state.py               # State persistence
│   │
│   └── services/                  # Application services
│       ├── __init__.py
│       ├── component_service.py   # Component operations
│       └── export_service.py      # Export functionality
```

## Architecture Principles

### 1. Separation of Concerns
Each module has a single, well-defined responsibility:
- **Models**: Data structures and schemas
- **UI**: Visual components and user interaction
- **Managers**: Business logic and state management
- **Services**: Reusable functionality and operations
- **Config**: Application-wide constants and settings

### 2. Dependency Flow
```
main.py
  └─> app.py
       ├─> ui/panels/*        (User Interface)
       ├─> managers/*         (Business Logic)
       ├─> services/*         (Operations)
       └─> models/*           (Data Structures)
```

### 3. Component Communication
- **Events**: UI components emit events that are handled by the app
- **Callbacks**: Components receive callbacks for user actions
- **State Management**: Centralized state managed by StateManager
- **Data Flow**: Unidirectional data flow from models through managers to UI

## Key Components

### App Layer (`app.py`)
The main application orchestrator that:
- Initializes all managers and services
- Creates and arranges UI panels
- Handles communication between components
- Manages application lifecycle

### UI Layer (`ui/`)
#### Panels
- **SidebarPanel**: Navigation between different views
- **ComponentsPanel**: Draggable component library
- **CanvasPanel**: Main visual editing area
- **PropertiesPanel**: Component property editor

#### Components
- **ResizeHandle**: Allows panels to be resized
- **FloatingToolbar**: Context menu for components
- **RichTextEditor**: WYSIWYG text editing

### Manager Layer (`managers/`)
- **ProjectManager**: Handles project CRUD operations
- **StateManager**: Persists and restores application state

### Service Layer (`services/`)
- **ComponentService**: Component creation and manipulation
- **ExportService**: Export to various formats (HTML, React, etc.)

## Adding New Features

### 1. New Component Type
1. Add template to `ComponentService._load_default_templates()`
2. Add icon mapping in `ComponentsPanel._get_icon()`
3. Add to `COMPONENT_CATEGORIES` in constants

### 2. New Export Format
1. Add format to `ExportService.export_formats`
2. Implement `export_to_[format]()` method
3. Add UI option in canvas toolbar

### 3. New Panel
1. Create panel class in `ui/panels/`
2. Add to app.py layout
3. Handle resize if needed
4. Export in `ui/__init__.py`

## State Management

### Persistent State
The following state is automatically persisted:
- Window size and position
- Panel sizes
- User preferences
- Recent projects
- Current project ID

### Runtime State
- Selected component
- Component tree
- Undo/redo history
- Drag and drop state

## Event Flow Example

User drops a component on canvas:
1. `ComponentsPanel` initiates drag with component data
2. `CanvasPanel` accepts drop and emits event
3. `app._on_component_drop()` handles event
4. `ComponentService` creates component instance
5. Component added to canvas and tree
6. `PropertiesPanel` updated with selection
7. State saved for undo/redo

## Future Enhancements

### Planned Modules
- `history/`: Undo/redo management
- `themes/`: Theme system
- `plugins/`: Plugin architecture
- `collaboration/`: Multi-user editing
- `templates/`: Project templates

### Performance Optimizations
- Lazy loading of components
- Virtual scrolling for large projects
- Web worker for heavy operations
- Component memoization

## Development Guidelines

1. **Keep modules focused**: Each file should have one clear purpose
2. **Use type hints**: All functions should have type annotations
3. **Document public APIs**: Classes and public methods need docstrings
4. **Handle errors gracefully**: Use try/except and show user-friendly messages
5. **Test in isolation**: Each module should be independently testable

## Testing Strategy

```
tests/
├── unit/
│   ├── test_models.py
│   ├── test_managers.py
│   └── test_services.py
├── integration/
│   └── test_app.py
└── e2e/
    └── test_workflows.py
```

This modular architecture makes Canvas Editor more maintainable, testable, and extensible while preserving all existing functionality.