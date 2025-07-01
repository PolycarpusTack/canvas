# Project Management - Solution Design Document

## Overview
The Project Management system handles all project-related operations including creation, import, save, load, and file management for the Canvas Editor.

## Functional Requirements

### 1. Create New Project
- Generate unique project ID
- Create project directory structure
- Initialize with boilerplate files (HTML, CSS, JS)
- Save project metadata
- Add to recent projects list

### 2. Import Existing Project
- Scan folder for web files
- Detect framework (React, Vue, Angular, Svelte)
- Create project metadata
- Preserve existing file structure
- Find main entry file

### 3. Save/Load Project
- Save project state and metadata
- Auto-save functionality (configurable interval)
- Load project from disk
- Restore last opened project

### 4. Project File Management
- Track all project files
- Monitor file changes
- Support file operations (create, rename, delete)
- Handle assets (images, fonts, etc.)

## Technical Specifications

### Data Models

```python
@dataclass
class ProjectFile:
    path: str                    # Absolute file path
    relative_path: str          # Path relative to project root
    size: int                   # File size in bytes
    modified: str               # ISO timestamp
    mime_type: str             # MIME type
    is_web_file: bool          # True if editable web file
    content: Optional[str]      # File content (lazy loaded)

@dataclass
class ProjectMetadata:
    id: str                     # UUID
    name: str                   # Project name
    path: str                   # Project root path
    created: str                # ISO timestamp
    modified: str               # ISO timestamp
    description: str            # Project description
    version: str                # Project version
    files_count: int            # Number of files
    main_file: Optional[str]    # Entry point (e.g., index.html)
    framework: Optional[str]    # Detected framework
    tags: List[str]             # Project tags
    settings: Dict[str, Any]    # Project-specific settings
```

### API Interface

```python
class ProjectManager:
    async def create_new_project(
        name: str, 
        description: str = "", 
        location: Optional[str] = None
    ) -> bool
    
    async def import_existing_project(folder_path: str) -> bool
    
    async def save_project() -> bool
    
    async def load_project(project_path: str) -> bool
    
    async def get_recent_projects() -> List[ProjectMetadata]
    
    async def close_project() -> None
    
    def get_project_files() -> List[ProjectFile]
    
    async def create_file(relative_path: str, content: str = "") -> bool
    
    async def rename_file(old_path: str, new_path: str) -> bool
    
    async def delete_file(relative_path: str) -> bool
```

### Storage Structure

```
~/CanvasEditor/Projects/
└── ProjectName/
    ├── canvas-project.json    # Project metadata
    ├── .canvas/              # Canvas-specific files
    │   ├── components.json   # Saved components
    │   ├── history.json      # Undo/redo history
    │   └── cache/           # Cached data
    ├── index.html           # Main entry file
    ├── src/                 # Source files
    │   ├── style.css
    │   └── script.js
    └── assets/              # Images, fonts, etc.
```

### Configuration

```python
# Project-related constants
MAX_RECENT_PROJECTS = 10
AUTO_SAVE_INTERVAL = 300  # 5 minutes
MAX_PROJECT_FILES = 1000
SUPPORTED_WEB_EXTENSIONS = {'.html', '.htm', '.css', '.js', '.json', '.md', '.txt', '.xml', '.svg'}
IGNORED_PATHS = ['node_modules', '.git', 'dist', 'build', '.cache']
```

## Implementation Guidelines

### 1. Project Creation Flow
```python
def create_new_project():
    # 1. Validate project name (no special chars, not empty)
    # 2. Check if location exists and is writable
    # 3. Create directory structure
    # 4. Generate project ID (UUID)
    # 5. Create metadata file
    # 6. Create boilerplate files
    # 7. Add to recent projects
    # 8. Set as current project
    # 9. Start auto-save timer
```

### 2. Import Flow
```python
def import_existing_project():
    # 1. Validate folder exists and is readable
    # 2. Check if already a Canvas project
    # 3. Scan for web files (respect ignore patterns)
    # 4. Detect framework by checking:
    #    - package.json dependencies
    #    - Framework-specific config files
    # 5. Find main entry file
    # 6. Create project metadata
    # 7. Save canvas-project.json
    # 8. Add to recent projects
```

### 3. File Monitoring
```python
def monitor_files():
    # Use watchdog library for file system events
    # Track: create, modify, delete, rename
    # Update project metadata on changes
    # Trigger auto-save if enabled
```

### 4. Error Handling

- **Invalid project name**: Show error, suggest valid name
- **Permission denied**: Show error, suggest different location
- **Disk full**: Show error, provide cleanup options
- **Corrupted project**: Attempt recovery from backup
- **Too many files**: Warn user, offer to exclude folders

### 5. Performance Considerations

- Lazy load file contents (don't read all files at once)
- Use file system cache for frequently accessed files
- Batch file operations when possible
- Debounce auto-save to avoid excessive writes
- Index files for fast searching

## Testing Requirements

### Unit Tests
- Project creation with various inputs
- Import of different project types
- File operation edge cases
- Metadata serialization/deserialization

### Integration Tests
- Full project lifecycle (create → edit → save → load)
- Auto-save functionality
- Recent projects management
- File system error handling

### Performance Tests
- Large project import (1000+ files)
- Auto-save with many changes
- File search performance

## Security Considerations

- Validate all file paths to prevent directory traversal
- Sanitize project names to prevent injection
- Check file permissions before operations
- Limit file size for web files
- Validate imported content

## Dependencies

- `pathlib` - Path operations
- `uuid` - Generate project IDs
- `shutil` - File operations
- `watchdog` - File system monitoring
- `aiofiles` - Async file operations

## Future Enhancements

1. **Project Templates**: Pre-configured project types
2. **Git Integration**: Version control support
3. **Project Search**: Full-text search across files
4. **Project Export**: Package project for deployment
5. **Cloud Backup**: Optional cloud storage integration
6. **Project Sharing**: Share read-only project links
7. **File Diff**: Show changes between saves
8. **Project Analytics**: File count, size, complexity metrics

## Example Usage

```python
# Create new project
project_manager = ProjectManager(page)
success = await project_manager.create_new_project(
    name="My Portfolio",
    description="Personal portfolio website",
    location="/Users/me/Projects/portfolio"
)

# Import existing project
success = await project_manager.import_existing_project(
    "/Users/me/existing-website"
)

# Get recent projects
recent = await project_manager.get_recent_projects()
for project in recent:
    print(f"{project.name} - {project.path}")

# Create a new file
await project_manager.create_file(
    "components/header.html",
    "<header>My Header</header>"
)
```