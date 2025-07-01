"""Enhanced Project management functionality with comprehensive security and error handling

This module implements the project management requirements from the development plan
with full CLAUDE.md guideline compliance.
"""

import json
import asyncio
import logging
import re
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Union, Callable
import uuid
import shutil
import mimetypes
import threading
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

import flet as ft

from models.project import (
    ProjectMetadata, ProjectFile, ProjectSettings,
    ValidationError, ProjectSecurityError
)
from config.constants import (
    MAX_RECENT_PROJECTS, AUTO_SAVE_INTERVAL, MAX_PROJECT_FILES,
    SUPPORTED_WEB_EXTENSIONS, STORAGE_KEY_RECENT_PROJECTS
)

# Set up logging (CLAUDE.md #12.1)
logger = logging.getLogger(__name__)


class ProjectCreationError(Exception):
    """Exception raised when project creation fails"""
    pass


class ProjectImportError(Exception):
    """Exception raised when project import fails"""
    pass


class ProjectIOError(Exception):
    """Exception raised for project I/O operations"""
    pass


class AutoSaveManager:
    """Manages debounced auto-save operations (CLAUDE.md #2.1.3)"""
    
    def __init__(self, save_interval: int = 300):
        self.save_interval = save_interval
        self.pending_save: Optional[asyncio.Task] = None
        self.last_save_time = datetime.now()
        self.save_in_progress = False
        self._lock = asyncio.Lock()
        self._retry_count = 0
        self._max_retries = 3
    
    async def schedule_save(self, project_manager: 'EnhancedProjectManager') -> None:
        """Schedule a debounced save operation"""
        async with self._lock:
            if self.pending_save:
                self.pending_save.cancel()
            
            self.pending_save = asyncio.create_task(
                self._save_after_delay(project_manager)
            )
    
    async def _save_after_delay(self, project_manager: 'EnhancedProjectManager') -> None:
        """Save project after delay with retry logic"""
        await asyncio.sleep(self.save_interval)
        
        for attempt in range(self._max_retries):
            try:
                async with self._lock:
                    if self.save_in_progress:
                        return  # Another save is in progress
                    
                    self.save_in_progress = True
                
                success = await project_manager.save_project()
                if success:
                    self.last_save_time = datetime.now()
                    self._retry_count = 0
                    logger.info("Auto-save completed successfully")
                    break
                else:
                    raise ProjectIOError("Save operation failed")
                    
            except Exception as e:
                self._retry_count += 1
                wait_time = min(2 ** attempt, 60)  # Exponential backoff
                logger.warning(f"Auto-save attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s")
                await asyncio.sleep(wait_time)
                
                if attempt == self._max_retries - 1:
                    logger.error(f"Auto-save failed after {self._max_retries} attempts")
            finally:
                self.save_in_progress = False


class EnhancedProjectManager:
    """Enhanced project manager with comprehensive security and error handling"""
    
    def __init__(self, page: ft.Page, progress_callback: Optional[Callable[[str, float], None]] = None):
        self.page = page
        self.client_storage = page.client_storage
        self.current_project: Optional[ProjectMetadata] = None
        self.project_files: List[ProjectFile] = []
        self.project_path: Optional[Path] = None
        self.settings: ProjectSettings = ProjectSettings()
        self.auto_save_manager = AutoSaveManager(self.settings.auto_save_interval)
        self.progress_callback = progress_callback
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._operation_lock = asyncio.Lock()  # Prevent concurrent operations
        
        # Security settings
        self._max_path_length = 260  # Windows path limit
        self._allowed_project_root = Path.home() / "CanvasEditor"  # Restrict to user directory
        
        # Performance settings
        self._file_scan_batch_size = 100
        self._max_file_size = 50 * 1024 * 1024  # 50MB per file
        
        logger.info("Enhanced ProjectManager initialized")
    
    async def create_new_project(self, name: str, description: str = "", location: Optional[str] = None) -> bool:
        """Create a new project with comprehensive validation and error handling (CLAUDE.md #2.1)"""
        async with self._operation_lock:
            try:
                # Input validation (CLAUDE.md #2.1.1)
                self._validate_project_name(name)
                
                if description and len(description) > 1000:
                    raise ValidationError("Description cannot exceed 1000 characters")
                
                # Generate unique project ID
                project_id = str(uuid.uuid4())
                
                # Determine project location with security checks
                project_path = await self._determine_project_location(name, location)
                
                # Report progress
                self._report_progress("Creating project structure...", 0.2)
                
                # Create project metadata with validation
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
                
                # Atomic project creation (CLAUDE.md #2.1.4)
                await self._create_project_atomically(metadata, project_path)
                
                self._report_progress("Finalizing project...", 0.8)
                
                # Set as current project
                self.current_project = metadata
                self.project_path = project_path
                
                # Add to recent projects
                await self._add_to_recent_projects(metadata)
                
                # Start auto-save if enabled
                if self.settings.auto_save:
                    await self.auto_save_manager.schedule_save(self)
                
                self._report_progress("Project created successfully!", 1.0)
                logger.info(f"Project '{name}' created successfully at {project_path}")
                return True
                
            except ValidationError as e:
                logger.error(f"Validation error creating project: {e}")
                raise
            except ProjectSecurityError as e:
                logger.error(f"Security error creating project: {e}")
                raise
            except PermissionError as e:
                logger.error(f"Permission denied creating project: {e}")
                raise ProjectCreationError(f"Permission denied: {e}")
            except OSError as e:
                logger.error(f"File system error creating project: {e}")
                raise ProjectCreationError(f"File system error: {e}")
            except Exception as e:
                logger.error(f"Unexpected error creating project: {e}")
                raise ProjectCreationError(f"Failed to create project: {e}")
    
    def _validate_project_name(self, name: str) -> None:
        """Validate project name with security checks (CLAUDE.md #7.2)"""
        if not name or not isinstance(name, str):
            raise ValidationError("Project name is required and must be a string")
        
        name = name.strip()
        if not name:
            raise ValidationError("Project name cannot be empty")
        
        if len(name) > 100:
            raise ValidationError("Project name cannot exceed 100 characters")
        
        # Check for dangerous characters
        if re.search(r'[<>:"/\\|?*\x00-\x1f]', name):
            raise ValidationError("Project name contains invalid characters")
        
        # Prevent reserved names
        reserved_names = {'con', 'prn', 'aux', 'null', 'nul', 'com1', 'com2', 'com3', 
                         'com4', 'com5', 'com6', 'com7', 'com8', 'com9', 'lpt1', 
                         'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'}
        if name.lower() in reserved_names:
            raise ValidationError(f"'{name}' is a reserved name")
    
    async def _determine_project_location(self, name: str, location: Optional[str]) -> Path:
        """Determine and validate project location (CLAUDE.md #7.1)"""
        if location:
            project_path = Path(location)
            
            # Security: Ensure path is within allowed directory
            try:
                project_path.resolve().relative_to(self._allowed_project_root)
            except ValueError:
                raise ProjectSecurityError(f"Project location must be within {self._allowed_project_root}")
        else:
            # Use default location
            projects_dir = self._allowed_project_root / "Projects"
            projects_dir.mkdir(parents=True, exist_ok=True)
            project_path = projects_dir / self._get_safe_filename(name)
        
        # Validate path length
        if len(str(project_path)) > self._max_path_length:
            raise ValidationError(f"Project path too long (max {self._max_path_length} characters)")
        
        # Check if project already exists
        if project_path.exists():
            raise ValidationError(f"Project already exists at {project_path}")
        
        return project_path
    
    def _get_safe_filename(self, name: str) -> str:
        """Convert project name to safe filename"""
        safe_name = re.sub(r'[^a-zA-Z0-9_\-\s]', '', name)
        safe_name = re.sub(r'\s+', '_', safe_name.strip())
        return safe_name[:50]  # Limit length
    
    async def _create_project_atomically(self, metadata: ProjectMetadata, project_path: Path) -> None:
        """Create project structure atomically with rollback on failure (CLAUDE.md #2.1.4)"""
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
                json.dump(metadata.to_dict(), f, indent=2)
            created_items.append(project_file)
            
        except Exception as e:
            # Rollback: Clean up any created items
            logger.warning(f"Project creation failed, rolling back: {e}")
            await self._cleanup_partial_project(created_items)
            raise
    
    async def _create_boilerplate_files(self, project_path: Path, name: str) -> None:
        """Create boilerplate files with safe content generation"""
        safe_name = self._escape_html(name)
        
        # Create index.html with safe content
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
        
        # Create CSS with safe content
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
        
        # Create JavaScript with safe content
        js_content = f'''// {safe_name} JavaScript
document.addEventListener('DOMContentLoaded', function() {{
    console.log("Application loaded successfully!");
}});'''
        
        # Write files safely
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
        for item in reversed(created_items):  # Remove in reverse order
            try:
                if item.exists():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up {item}: {cleanup_error}")
    
    async def import_existing_project(self, folder_path: str) -> bool:
        """Import an existing web project with enhanced validation and framework detection"""
        async with self._operation_lock:
            try:
                # Input validation
                if not folder_path or not isinstance(folder_path, str):
                    raise ValidationError("Folder path is required and must be a string")
                
                project_path = Path(folder_path)
                if not project_path.exists() or not project_path.is_dir():
                    raise ProjectImportError("Invalid project folder")
                
                # Security check: Ensure path is safe
                try:
                    project_path.resolve().relative_to(self._allowed_project_root)
                except ValueError:
                    logger.warning(f"Import from outside allowed directory: {project_path}")
                
                self._report_progress("Analyzing project structure...", 0.1)
                
                # Check if it's already a Canvas project
                canvas_project_file = project_path / "canvas-project.json"
                
                if canvas_project_file.exists():
                    # Load existing Canvas project
                    return await self.load_project(str(project_path))
                
                # Create new project metadata for imported project
                project_id = str(uuid.uuid4())
                now = datetime.now().isoformat()
                
                self._report_progress("Detecting framework...", 0.3)
                
                # Enhanced framework detection
                framework = await self._detect_framework_enhanced(project_path)
                
                self._report_progress("Scanning project files...", 0.5)
                
                # Enhanced file scanning with progress
                web_files = await self._scan_project_files_enhanced(project_path)
                
                self._report_progress("Finding main file...", 0.8)
                
                # Find main file
                main_file = self._find_main_file_enhanced(project_path, framework)
                
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
                    json.dump(metadata.to_dict(), f, indent=2)
                
                # Set as current project
                self.current_project = metadata
                self.project_path = project_path
                self.project_files = web_files
                
                # Add to recent projects
                await self._add_to_recent_projects(metadata)
                
                self._report_progress("Import completed!", 1.0)
                logger.info(f"Project imported successfully from {project_path}")
                return True
                
            except ValidationError as e:
                logger.error(f"Validation error importing project: {e}")
                raise
            except ProjectImportError as e:
                logger.error(f"Import error: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error importing project: {e}")
                raise ProjectImportError(f"Failed to import project: {e}")
    
    async def _detect_framework_enhanced(self, project_path: Path) -> Optional[str]:
        """Enhanced framework detection with better patterns (A-2-T1)"""
        try:
            # Check package.json first with dependency analysis
            package_json = project_path / "package.json"
            if package_json.exists():
                try:
                    with open(package_json, 'r', encoding='utf-8') as f:
                        package_data = json.load(f)
                    
                    # Check dependencies and devDependencies
                    all_deps = {}
                    all_deps.update(package_data.get("dependencies", {}))
                    all_deps.update(package_data.get("devDependencies", {}))
                    
                    # Framework detection based on dependencies
                    if any(dep in all_deps for dep in ["react", "react-dom"]):
                        return "React"
                    elif any(dep in all_deps for dep in ["vue", "@vue/cli"]):
                        return "Vue"
                    elif any(dep in all_deps for dep in ["@angular/core", "@angular/cli"]):
                        return "Angular"
                    elif any(dep in all_deps for dep in ["svelte", "@sveltejs/kit"]):
                        return "Svelte"
                    elif any(dep in all_deps for dep in ["next", "gatsby"]):
                        return "React"  # Next.js and Gatsby are React-based
                    elif any(dep in all_deps for dep in ["nuxt", "@nuxt/cli"]):
                        return "Vue"  # Nuxt is Vue-based
                    
                except (json.JSONDecodeError, OSError) as e:
                    logger.warning(f"Error reading package.json: {e}")
            
            # Check for framework-specific configuration files
            framework_files = {
                "Angular": ["angular.json", ".angular-cli.json", "ng.json"],
                "Vue": ["vue.config.js", "vue.config.ts", ".vuerc"],
                "React": ["craco.config.js", "react-scripts"],
                "Svelte": ["svelte.config.js", "svelte.config.mjs"],
                "Next.js": ["next.config.js", "next.config.mjs"],
                "Gatsby": ["gatsby-config.js", "gatsby-node.js"],
                "Vite": ["vite.config.js", "vite.config.ts"]
            }
            
            for framework, files in framework_files.items():
                if any((project_path / file).exists() for file in files):
                    return framework
            
            # Check for framework-specific file extensions
            if list(project_path.glob("**/*.vue")):
                return "Vue"
            elif list(project_path.glob("**/*.jsx")) or list(project_path.glob("**/*.tsx")):
                return "React"
            elif list(project_path.glob("**/*.svelte")):
                return "Svelte"
            elif list(project_path.glob("**/*.ts")) and not list(project_path.glob("**/*.vue")):
                # TypeScript without Vue likely indicates Angular
                if (project_path / "src" / "app").exists():
                    return "Angular"
            
            # Check for common build tools
            if (project_path / "webpack.config.js").exists():
                return "Webpack"
            elif (project_path / "rollup.config.js").exists():
                return "Rollup"
            
            # Default to HTML if we find HTML files
            if list(project_path.glob("**/*.html")):
                return "HTML"
            
            return None
            
        except Exception as e:
            logger.warning(f"Framework detection failed: {e}")
            return None
    
    async def _scan_project_files_enhanced(self, project_path: Path) -> List[ProjectFile]:
        """Enhanced file scanning with performance optimization (A-2-T2)"""
        files = []
        total_files = 0
        start_time = time.time()
        
        # Performance: Use batch processing for large directories
        ignore_patterns = {
            'node_modules', '.git', '.svn', 'dist', 'build', 'coverage',
            '__pycache__', '.pytest_cache', '.mypy_cache', '.tox'
        }
        
        def should_ignore(path_parts):
            return any(part.startswith('.') or part in ignore_patterns for part in path_parts)
        
        try:
            # Use thread pool for I/O operations
            futures = []
            batch = []
            
            for file_path in project_path.rglob("*"):
                if file_path.is_file():
                    total_files += 1
                    
                    # Performance: Skip files over limit
                    if total_files > MAX_PROJECT_FILES:
                        logger.warning(f"Project has more than {MAX_PROJECT_FILES} files, limiting scan")
                        break
                    
                    # Skip ignored patterns
                    if should_ignore(file_path.parts):
                        continue
                    
                    # Skip very large files
                    try:
                        file_size = file_path.stat().st_size
                        if file_size > self._max_file_size:
                            logger.warning(f"Skipping large file: {file_path} ({file_size} bytes)")
                            continue
                    except OSError:
                        continue
                    
                    batch.append(file_path)
                    
                    # Process in batches for better performance
                    if len(batch) >= self._file_scan_batch_size:
                        future = self._executor.submit(self._process_file_batch, batch, project_path)
                        futures.append(future)
                        batch = []
            
            # Process remaining files
            if batch:
                future = self._executor.submit(self._process_file_batch, batch, project_path)
                futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                try:
                    batch_files = future.result(timeout=30)
                    files.extend(batch_files)
                except Exception as e:
                    logger.warning(f"Error processing file batch: {e}")
            
            elapsed_time = time.time() - start_time
            logger.info(f"Scanned {len(files)} files in {elapsed_time:.2f} seconds")
            
            return files
            
        except Exception as e:
            logger.error(f"Error scanning project files: {e}")
            return []
    
    def _process_file_batch(self, file_paths: List[Path], project_root: Path) -> List[ProjectFile]:
        """Process a batch of files for scanning"""
        batch_files = []
        
        for file_path in file_paths:
            try:
                # Get file info
                relative_path = file_path.relative_to(project_root)
                stat = file_path.stat()
                mime_type, _ = mimetypes.guess_type(str(file_path))
                is_web_file = file_path.suffix.lower() in SUPPORTED_WEB_EXTENSIONS
                
                project_file = ProjectFile(
                    path=str(file_path),
                    relative_path=str(relative_path),
                    size=stat.st_size,
                    modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    mime_type=mime_type or "application/octet-stream",
                    is_web_file=is_web_file
                )
                
                batch_files.append(project_file)
                
            except Exception as e:
                logger.warning(f"Error processing file {file_path}: {e}")
        
        return batch_files
    
    def _find_main_file_enhanced(self, project_path: Path, framework: Optional[str]) -> Optional[str]:
        """Enhanced main file detection based on framework"""
        # Framework-specific entry points
        framework_entries = {
            "React": ["src/index.js", "src/index.jsx", "src/index.ts", "src/index.tsx", "src/App.js", "src/App.jsx"],
            "Vue": ["src/main.js", "src/main.ts", "src/App.vue", "index.html"],
            "Angular": ["src/main.ts", "src/index.html"],
            "Svelte": ["src/main.js", "src/App.svelte", "index.html"],
            "Next.js": ["pages/index.js", "pages/index.tsx", "src/pages/index.js"],
            "Gatsby": ["src/pages/index.js", "src/pages/index.tsx"]
        }
        
        # Check framework-specific entries first
        if framework and framework in framework_entries:
            for candidate in framework_entries[framework]:
                file_path = project_path / candidate
                if file_path.exists():
                    return candidate
        
        # Common entry files
        common_entries = [
            "index.html", "index.htm", "home.html", "main.html", "app.html",
            "src/index.html", "public/index.html", "dist/index.html",
            "src/index.js", "src/main.js", "src/app.js"
        ]
        
        for candidate in common_entries:
            file_path = project_path / candidate
            if file_path.exists():
                return candidate
        
        # If no standard file found, look for any HTML file
        for file_path in project_path.glob("**/*.html"):
            return str(file_path.relative_to(project_path))
        
        return None
    
    async def save_project(self) -> bool:
        """Enhanced project save with atomic operations"""
        if not self.current_project or not self.project_path:
            return False
        
        try:
            # Update modified time
            self.current_project.update_modified()
            
            # Create temporary file for atomic write
            project_file = self.project_path / "canvas-project.json"
            temp_file = self.project_path / "canvas-project.json.tmp"
            
            # Write to temporary file first
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_project.to_dict(), f, indent=2)
            
            # Atomic rename
            temp_file.replace(project_file)
            
            logger.info(f"Project saved: {self.current_project.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving project: {e}")
            # Clean up temp file if it exists
            temp_file = self.project_path / "canvas-project.json.tmp"
            if temp_file.exists():
                temp_file.unlink()
            return False
    
    async def load_project(self, project_path: str) -> bool:
        """Enhanced project loading with validation"""
        try:
            path = Path(project_path)
            project_file = path / "canvas-project.json"
            
            if not project_file.exists():
                raise ProjectIOError("Not a valid Canvas project")
            
            # Load and validate metadata
            with open(project_file, 'r', encoding='utf-8') as f:
                metadata_dict = json.load(f)
            
            self.current_project = ProjectMetadata.from_dict(metadata_dict)
            self.project_path = path
            
            # Load project settings with validation
            if self.current_project.settings:
                self.settings = ProjectSettings.from_dict(self.current_project.settings)
            
            # Scan files in background
            self.project_files = await self._scan_project_files_enhanced(path)
            
            # Add to recent projects
            await self._add_to_recent_projects(self.current_project)
            
            # Start auto-save if enabled
            if self.settings.auto_save:
                await self.auto_save_manager.schedule_save(self)
            
            logger.info(f"Project loaded: {self.current_project.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading project: {e}")
            return False
    
    async def _add_to_recent_projects(self, project: ProjectMetadata):
        """Add project to recent projects list with validation"""
        try:
            # Get existing recent projects
            recent_json = await self.client_storage.get_async(STORAGE_KEY_RECENT_PROJECTS)
            recent_projects = json.loads(recent_json) if recent_json else []
            
            # Validate existing projects
            valid_projects = []
            for p in recent_projects:
                try:
                    ProjectMetadata.from_dict(p)
                    valid_projects.append(p)
                except ValidationError:
                    logger.warning(f"Removing invalid recent project: {p}")
            
            # Remove if already exists
            valid_projects = [p for p in valid_projects if p.get("id") != project.id]
            
            # Add to beginning
            valid_projects.insert(0, project.to_dict())
            
            # Limit to max
            valid_projects = valid_projects[:MAX_RECENT_PROJECTS]
            
            # Save
            await self.client_storage.set_async(
                STORAGE_KEY_RECENT_PROJECTS,
                json.dumps(valid_projects)
            )
            
        except Exception as e:
            logger.error(f"Error updating recent projects: {e}")
    
    async def get_recent_projects(self) -> List[ProjectMetadata]:
        """Get list of recent projects with validation"""
        try:
            recent_json = await self.client_storage.get_async(STORAGE_KEY_RECENT_PROJECTS)
            if recent_json:
                recent_dicts = json.loads(recent_json)
                validated_projects = []
                
                for p in recent_dicts:
                    try:
                        project = ProjectMetadata.from_dict(p)
                        # Verify project still exists
                        if Path(project.path).exists():
                            validated_projects.append(project)
                    except ValidationError:
                        logger.warning(f"Skipping invalid recent project: {p}")
                
                return validated_projects
        except Exception as e:
            logger.error(f"Error loading recent projects: {e}")
        
        return []
    
    def close_project(self):
        """Close current project with cleanup"""
        if self.auto_save_manager.pending_save:
            self.auto_save_manager.pending_save.cancel()
        
        self.current_project = None
        self.project_path = None
        self.project_files = []
        
        logger.info("Project closed")
    
    def _report_progress(self, message: str, progress: float):
        """Report progress to callback if available"""
        if self.progress_callback:
            self.progress_callback(message, progress)
    
    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)