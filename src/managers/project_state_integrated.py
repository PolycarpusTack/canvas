"""
Project Management Integrated with State Management System

This module integrates the enhanced project management functionality with the
comprehensive state management system, providing seamless state synchronization,
undo/redo support, and real-time UI updates.
"""

import asyncio
import logging
import re
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
import uuid
import shutil
import mimetypes
from concurrent.futures import ThreadPoolExecutor

import flet as ft

from models.project import (
    ProjectMetadata, ProjectFile, ProjectSettings,
    ValidationError, ProjectSecurityError
)
from config.constants import (
    MAX_RECENT_PROJECTS, MAX_PROJECT_FILES,
    SUPPORTED_WEB_EXTENSIONS
)
from .enhanced_state import EnhancedStateManager
from .action_creators import ActionCreators
from .state_types import ActionType, ProjectState

# Set up logging
logger = logging.getLogger(__name__)


class StateIntegratedProjectManager:
    """
    Project Management integrated with State Management System.
    
    Provides all project management functionality while maintaining state
    consistency, undo/redo support, and real-time UI synchronization.
    """
    
    def __init__(
        self, 
        state_manager: EnhancedStateManager,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ):
        self.state_manager = state_manager
        self.state_system = state_manager.state_system
        self.progress_callback = progress_callback
        
        # Get settings from state
        self.settings = ProjectSettings()
        
        # Security and performance settings
        self._max_path_length = 260
        self._allowed_project_root = Path.home() / "CanvasEditor"
        self._file_scan_batch_size = 100
        self._max_file_size = 50 * 1024 * 1024  # 50MB
        
        # Thread pool for I/O operations
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        logger.info("StateIntegratedProjectManager initialized")
    
    async def create_new_project(
        self, 
        name: str, 
        description: str = "", 
        location: Optional[str] = None
    ) -> bool:
        """
        Create a new project with full state management integration.
        
        This method:
        1. Validates inputs using existing validation
        2. Creates project structure atomically  
        3. Updates state management system
        4. Provides undo/redo support
        5. Triggers UI updates automatically
        """
        try:
            # Input validation (reuse existing validation)
            self._validate_project_name(name)
            
            if description and len(description) > 1000:
                raise ValidationError("Description cannot exceed 1000 characters")
            
            # Generate unique project ID
            project_id = str(uuid.uuid4())
            
            # Determine project location with security checks
            project_path = await self._determine_project_location(name, location)
            
            self._report_progress("Creating project structure...", 0.2)
            
            # Create project metadata
            now = datetime.now().isoformat()
            metadata = ProjectMetadata(
                id=project_id,
                name=name,
                path=str(project_path),
                created=now,
                modified=now,
                description=description,
                version="1.0.0",
                files_count=0,
                settings=self.settings.to_dict()
            )
            
            # Start batch operation for undo/redo
            batch_id = self.state_system.start_batch(f"Create Project: {name}")
            
            try:
                # Create project structure atomically
                await self._create_project_atomically(metadata, project_path)
                
                self._report_progress("Updating application state...", 0.8)
                
                # Update state management system
                await self._update_state_for_new_project(metadata)
                
                # End batch operation
                self.state_system.end_batch(batch_id)
                
                self._report_progress("Project created successfully!", 1.0)
                logger.info(f"Project '{name}' created and integrated with state system")
                
                return True
                
            except Exception as e:
                # Cancel batch operation on error
                self.state_system.cancel_batch(batch_id)
                raise
                
        except ValidationError as e:
            logger.error(f"Validation error creating project: {e}")
            raise
        except ProjectSecurityError as e:
            logger.error(f"Security error creating project: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating project: {e}")
            raise
    
    async def _update_state_for_new_project(self, metadata: ProjectMetadata) -> None:
        """Update state management system for new project"""
        
        # Dispatch action to set current project
        await self.state_system.dispatch(
            ActionCreators.create_project(
                project_id=metadata.id,
                name=metadata.name,
                path=metadata.path,
                metadata=metadata.to_dict()
            )
        )
        
        # Add to recent projects
        await self.state_system.dispatch(
            ActionCreators.add_recent_project(metadata.to_dict())
        )
        
        # Update preferences if needed
        if self.settings.auto_save:
            await self.state_system.dispatch(
                ActionCreators.update_preferences({
                    "auto_save": True,
                    "auto_save_interval": self.settings.auto_save_interval
                })
            )
    
    async def import_existing_project(self, folder_path: str) -> bool:
        """
        Import existing project with state management integration.
        
        Includes framework detection, file scanning, and state updates.
        """
        try:
            # Input validation
            if not folder_path or not isinstance(folder_path, str):
                raise ValidationError("Folder path is required and must be a string")
            
            project_path = Path(folder_path)
            if not project_path.exists() or not project_path.is_dir():
                raise ValueError("Invalid project folder")
            
            # Security check
            try:
                project_path.resolve().relative_to(self._allowed_project_root)
            except ValueError:
                logger.warning(f"Import from outside allowed directory: {project_path}")
            
            self._report_progress("Analyzing project structure...", 0.1)
            
            # Check if already a Canvas project
            canvas_project_file = project_path / "canvas-project.json"
            if canvas_project_file.exists():
                return await self.load_project(str(project_path))
            
            # Start batch operation
            batch_id = self.state_system.start_batch(f"Import Project: {project_path.name}")
            
            try:
                # Create metadata for imported project
                project_id = str(uuid.uuid4())
                now = datetime.now().isoformat()
                
                self._report_progress("Detecting framework...", 0.3)
                framework = await self._detect_framework_enhanced(project_path)
                
                self._report_progress("Scanning project files...", 0.5)
                web_files = await self._scan_project_files_enhanced(project_path)
                
                self._report_progress("Finding main file...", 0.8)
                main_file = self._find_main_file_enhanced(project_path, framework)
                
                # Create metadata
                metadata = ProjectMetadata(
                    id=project_id,
                    name=project_path.name,
                    path=str(project_path),
                    created=now,
                    modified=now,
                    description=f"Imported {framework or 'web'} project",
                    version="1.0.0",
                    files_count=len(web_files),
                    main_file=main_file,
                    framework=framework,
                    settings=self.settings.to_dict()
                )
                
                # Save Canvas metadata
                with open(canvas_project_file, 'w', encoding='utf-8') as f:
                    import json
                    json.dump(metadata.to_dict(), f, indent=2)
                
                # Update state management system
                await self._update_state_for_imported_project(metadata, web_files)
                
                # End batch operation
                self.state_system.end_batch(batch_id)
                
                self._report_progress("Import completed!", 1.0)
                logger.info(f"Project imported and integrated: {project_path}")
                
                return True
                
            except Exception as e:
                # Cancel batch on error
                self.state_system.cancel_batch(batch_id)
                raise
                
        except Exception as e:
            logger.error(f"Error importing project: {e}")
            raise
    
    async def _update_state_for_imported_project(
        self, 
        metadata: ProjectMetadata, 
        files: List[ProjectFile]
    ) -> None:
        """Update state for imported project"""
        
        # Set current project
        await self.state_system.dispatch(
            ActionCreators.open_project(
                project_id=metadata.id,
                name=metadata.name,
                path=metadata.path,
                metadata=metadata.to_dict()
            )
        )
        
        # Add to recent projects
        await self.state_system.dispatch(
            ActionCreators.add_recent_project(metadata.to_dict())
        )
        
        # Add file information to state if needed
        # (This could be extended for file management features)
    
    async def save_project(self) -> bool:
        """
        Save current project with state management integration.
        
        Automatically updates state and triggers UI updates.
        """
        try:
            # Get current project from state
            current_project_state = self.state_system.get_state("project")
            if not current_project_state or not current_project_state.path:
                logger.warning("No current project to save")
                return False
            
            project_path = Path(current_project_state.path)
            
            # Update modified time in state
            await self.state_system.dispatch(
                ActionCreators.update_project_meta({
                    "modified": datetime.now().isoformat(),
                    "has_unsaved_changes": False
                })
            )
            
            # Save project metadata to file
            project_file = project_path / "canvas-project.json"
            temp_file = project_path / "canvas-project.json.tmp"
            
            # Get complete project data from state
            project_data = {
                **current_project_state.to_dict(),
                "components": self.state_system.get_state("components").to_dict(),
                "canvas": self.state_system.get_state("canvas").to_dict(),
                "modified": datetime.now().isoformat()
            }
            
            # Atomic write
            with open(temp_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(project_data, f, indent=2)
            
            temp_file.replace(project_file)
            
            # Update last saved time in state
            await self.state_system.dispatch(
                ActionCreators.project_saved(datetime.now())
            )
            
            logger.info(f"Project saved: {current_project_state.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving project: {e}")
            return False
    
    async def load_project(self, project_path: str) -> bool:
        """
        Load project with full state integration.
        
        Loads all project data into state management system.
        """
        try:
            path = Path(project_path)
            project_file = path / "canvas-project.json"
            
            if not project_file.exists():
                raise ValueError("Not a valid Canvas project")
            
            # Start batch operation
            batch_id = self.state_system.start_batch(f"Load Project: {path.name}")
            
            try:
                # Load project data
                with open(project_file, 'r', encoding='utf-8') as f:
                    import json
                    project_data = json.load(f)
                
                # Create metadata object
                metadata = ProjectMetadata.from_dict(project_data)
                
                # Update state with loaded project
                await self.state_system.dispatch(
                    ActionCreators.open_project(
                        project_id=metadata.id,
                        name=metadata.name,
                        path=metadata.path,
                        metadata=project_data
                    )
                )
                
                # Load components if present
                if "components" in project_data:
                    components_data = project_data["components"]
                    # TODO: Load components into state
                    # This would involve dispatching ADD_COMPONENT actions
                
                # Load canvas state if present  
                if "canvas" in project_data:
                    canvas_data = project_data["canvas"]
                    await self.state_system.dispatch(
                        ActionCreators.update_canvas_state(canvas_data)
                    )
                
                # Add to recent projects
                await self.state_system.dispatch(
                    ActionCreators.add_recent_project(metadata.to_dict())
                )
                
                # End batch operation
                self.state_system.end_batch(batch_id)
                
                logger.info(f"Project loaded into state: {metadata.name}")
                return True
                
            except Exception as e:
                self.state_system.cancel_batch(batch_id)
                raise
                
        except Exception as e:
            logger.error(f"Error loading project: {e}")
            return False
    
    async def close_project(self) -> bool:
        """
        Close current project with state cleanup.
        """
        try:
            # Check if there are unsaved changes
            current_state = self.state_system.get_state()
            if current_state.has_unsaved_changes:
                # In a real UI, this would show a dialog
                logger.warning("Project has unsaved changes")
            
            # Dispatch close action
            await self.state_system.dispatch(ActionCreators.close_project())
            
            # Clear components
            await self.state_system.dispatch(ActionCreators.clear_components())
            
            # Reset canvas
            await self.state_system.dispatch(ActionCreators.reset_canvas())
            
            logger.info("Project closed and state cleared")
            return True
            
        except Exception as e:
            logger.error(f"Error closing project: {e}")
            return False
    
    def get_recent_projects(self) -> List[Dict[str, Any]]:
        """Get recent projects from state management system"""
        try:
            recent_projects = self.state_system.get_state("recent_projects")
            return [project.to_dict() for project in recent_projects] if recent_projects else []
        except Exception as e:
            logger.error(f"Error getting recent projects: {e}")
            return []
    
    def get_current_project(self) -> Optional[Dict[str, Any]]:
        """Get current project from state"""
        try:
            project_state = self.state_system.get_state("project")
            return project_state.to_dict() if project_state else None
        except Exception as e:
            logger.error(f"Error getting current project: {e}")
            return None
    
    def bind_ui_component(
        self,
        component: ft.Control,
        property_name: str,
        state_path: str,
        transformer: Optional[Callable[[Any], Any]] = None
    ) -> Callable[[], None]:
        """
        Bind UI component to state with automatic updates.
        
        Returns unsubscribe function for cleanup.
        """
        try:
            return self.state_system.bind_component(
                component, state_path, property_name, transformer
            )
        except Exception as e:
            logger.error(f"Error binding UI component: {e}")
            return lambda: None
    
    # Undo/Redo support through state management
    async def undo(self) -> bool:
        """Undo last operation"""
        try:
            return await self.state_system.undo()
        except Exception as e:
            logger.error(f"Error during undo: {e}")
            return False
    
    async def redo(self) -> bool:
        """Redo last undone operation"""
        try:
            return await self.state_system.redo()
        except Exception as e:
            logger.error(f"Error during redo: {e}")
            return False
    
    def can_undo(self) -> bool:
        """Check if undo is available"""
        history_state = self.state_system.get_state("history")
        return history_state.can_undo if history_state else False
    
    def can_redo(self) -> bool:
        """Check if redo is available"""
        history_state = self.state_system.get_state("history")
        return history_state.can_redo if history_state else False
    
    # Reuse existing helper methods (with minimal modifications)
    def _validate_project_name(self, name: str) -> None:
        """Validate project name with security checks"""
        if not name or not isinstance(name, str):
            raise ValidationError("Project name is required and must be a string")
        
        name = name.strip()
        if not name:
            raise ValidationError("Project name cannot be empty")
        
        if len(name) > 100:
            raise ValidationError("Project name cannot exceed 100 characters")
        
        if re.search(r'[<>:"/\\|?*\x00-\x1f]', name):
            raise ValidationError("Project name contains invalid characters")
        
        reserved_names = {'con', 'prn', 'aux', 'null', 'nul', 'com1', 'com2', 
                         'com3', 'com4', 'com5', 'com6', 'com7', 'com8', 'com9', 
                         'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 
                         'lpt8', 'lpt9'}
        if name.lower() in reserved_names:
            raise ValidationError(f"'{name}' is a reserved name")
    
    async def _determine_project_location(self, name: str, location: Optional[str]) -> Path:
        """Determine and validate project location"""
        if location:
            project_path = Path(location)
            try:
                project_path.resolve().relative_to(self._allowed_project_root)
            except ValueError:
                raise ProjectSecurityError(f"Project location must be within {self._allowed_project_root}")
        else:
            projects_dir = self._allowed_project_root / "Projects"
            projects_dir.mkdir(parents=True, exist_ok=True)
            project_path = projects_dir / self._get_safe_filename(name)
        
        if len(str(project_path)) > self._max_path_length:
            raise ValidationError(f"Project path too long (max {self._max_path_length} characters)")
        
        if project_path.exists():
            raise ValidationError(f"Project already exists at {project_path}")
        
        return project_path
    
    def _get_safe_filename(self, name: str) -> str:
        """Convert project name to safe filename"""
        safe_name = re.sub(r'[^a-zA-Z0-9_\-\s]', '', name)
        safe_name = re.sub(r'\s+', '_', safe_name.strip())
        return safe_name[:50]
    
    async def _create_project_atomically(self, metadata: ProjectMetadata, project_path: Path) -> None:
        """Create project structure atomically with rollback"""
        created_items = []
        
        try:
            # Create main directory
            project_path.mkdir(parents=True, exist_ok=False)
            created_items.append(project_path)
            
            # Create subdirectories
            subdirs = ["src", "assets", "components"]
            for subdir in subdirs:
                dir_path = project_path / subdir
                dir_path.mkdir(exist_ok=True)
                created_items.append(dir_path)
            
            # Create boilerplate files
            await self._create_boilerplate_files(project_path, metadata.name)
            
            # Save project metadata
            project_file = project_path / "canvas-project.json"
            with open(project_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(metadata.to_dict(), f, indent=2)
            created_items.append(project_file)
            
        except Exception as e:
            logger.warning(f"Project creation failed, rolling back: {e}")
            await self._cleanup_partial_project(created_items)
            raise
    
    async def _create_boilerplate_files(self, project_path: Path, name: str) -> None:
        """Create boilerplate files with safe content"""
        safe_name = self._escape_html(name)
        
        # Create index.html
        index_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{safe_name}</title>
    <link rel="stylesheet" href="src/style.css">
</head>
<body>
    <div class="container">
        <h1>Welcome to {safe_name}</h1>
        <p>Start building your application here.</p>
    </div>
    <script src="src/script.js"></script>
</body>
</html>'''
        
        # Create CSS
        css_content = f'''/* {safe_name} Styles */
.container {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}}

h1 {{
    color: #333;
    text-align: center;
}}

p {{
    color: #666;
    text-align: center;
    font-size: 18px;
}}'''
        
        # Create JavaScript
        js_content = f'''// {safe_name} JavaScript
document.addEventListener('DOMContentLoaded', function() {{
    console.log("Application loaded successfully!");
}});'''
        
        # Write files
        files_to_create = [
            (project_path / "index.html", index_content),
            (project_path / "src" / "style.css", css_content),
            (project_path / "src" / "script.js", js_content)
        ]
        
        for file_path, content in files_to_create:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML content for security"""
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#x27;')
    
    async def _cleanup_partial_project(self, created_items: List[Path]) -> None:
        """Clean up partially created project items"""
        for item in reversed(created_items):
            try:
                if item.exists():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up {item}: {cleanup_error}")
    
    # Include existing enhanced detection and scanning methods
    async def _detect_framework_enhanced(self, project_path: Path) -> Optional[str]:
        """Enhanced framework detection"""
        # Reuse existing implementation from project_enhanced.py
        try:
            package_json = project_path / "package.json"
            if package_json.exists():
                with open(package_json, 'r', encoding='utf-8') as f:
                    import json
                    package_data = json.load(f)
                
                all_deps = {}
                all_deps.update(package_data.get("dependencies", {}))
                all_deps.update(package_data.get("devDependencies", {}))
                
                if any(dep in all_deps for dep in ["react", "react-dom"]):
                    return "React"
                elif any(dep in all_deps for dep in ["vue", "@vue/cli"]):
                    return "Vue"
                elif any(dep in all_deps for dep in ["@angular/core", "@angular/cli"]):
                    return "Angular"
                elif any(dep in all_deps for dep in ["svelte", "@sveltejs/kit"]):
                    return "Svelte"
            
            # Check for framework-specific files
            framework_files = {
                "Angular": ["angular.json", ".angular-cli.json"],
                "Vue": ["vue.config.js", "vue.config.ts"],
                "React": ["craco.config.js"],
                "Svelte": ["svelte.config.js"]
            }
            
            for framework, files in framework_files.items():
                if any((project_path / file).exists() for file in files):
                    return framework
            
            # Check file extensions
            if list(project_path.glob("**/*.vue")):
                return "Vue"
            elif list(project_path.glob("**/*.jsx")) or list(project_path.glob("**/*.tsx")):
                return "React"
            elif list(project_path.glob("**/*.svelte")):
                return "Svelte"
            
            return "HTML" if list(project_path.glob("**/*.html")) else None
            
        except Exception as e:
            logger.warning(f"Framework detection failed: {e}")
            return None
    
    async def _scan_project_files_enhanced(self, project_path: Path) -> List[ProjectFile]:
        """Enhanced file scanning with performance optimization"""
        files = []
        total_files = 0
        
        ignore_patterns = {
            'node_modules', '.git', '.svn', 'dist', 'build', 'coverage',
            '__pycache__', '.pytest_cache', '.mypy_cache', '.tox'
        }
        
        def should_ignore(path_parts):
            return any(part.startswith('.') or part in ignore_patterns for part in path_parts)
        
        try:
            for file_path in project_path.rglob("*"):
                if file_path.is_file():
                    total_files += 1
                    
                    if total_files > MAX_PROJECT_FILES:
                        logger.warning(f"Project has more than {MAX_PROJECT_FILES} files, limiting scan")
                        break
                    
                    if should_ignore(file_path.parts):
                        continue
                    
                    try:
                        file_size = file_path.stat().st_size
                        if file_size > self._max_file_size:
                            continue
                    except OSError:
                        continue
                    
                    # Create ProjectFile
                    relative_path = file_path.relative_to(project_path)
                    stat = file_path.stat()
                    mime_type, _ = mimetypes.guess_type(str(file_path))
                    is_web_file = file_path.suffix.lower() in SUPPORTED_WEB_EXTENSIONS
                    
                    files.append(ProjectFile(
                        path=str(file_path),
                        relative_path=str(relative_path),
                        size=stat.st_size,
                        modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        mime_type=mime_type or "application/octet-stream",
                        is_web_file=is_web_file
                    ))
            
            logger.info(f"Scanned {len(files)} files")
            return files
            
        except Exception as e:
            logger.error(f"Error scanning project files: {e}")
            return []
    
    def _find_main_file_enhanced(self, project_path: Path, framework: Optional[str]) -> Optional[str]:
        """Enhanced main file detection"""
        framework_entries = {
            "React": ["src/index.js", "src/index.jsx", "src/App.js"],
            "Vue": ["src/main.js", "src/main.ts", "src/App.vue"],
            "Angular": ["src/main.ts", "src/index.html"],
            "Svelte": ["src/main.js", "src/App.svelte"]
        }
        
        if framework and framework in framework_entries:
            for candidate in framework_entries[framework]:
                if (project_path / candidate).exists():
                    return candidate
        
        # Common entries
        common_entries = [
            "index.html", "index.htm", "src/index.html", 
            "public/index.html", "src/index.js"
        ]
        
        for candidate in common_entries:
            if (project_path / candidate).exists():
                return candidate
        
        # Fallback to any HTML file
        for file_path in project_path.glob("**/*.html"):
            return str(file_path.relative_to(project_path))
        
        return None
    
    def _report_progress(self, message: str, progress: float):
        """Report progress to callback if available"""
        if self.progress_callback:
            self.progress_callback(message, progress)
    
    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)