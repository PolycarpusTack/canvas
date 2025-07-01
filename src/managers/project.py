"""Project management functionality"""

import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
import shutil
import mimetypes
from dataclasses import asdict

import flet as ft

from models.project import ProjectMetadata, ProjectFile, ProjectSettings
from config.constants import (
    MAX_RECENT_PROJECTS, AUTO_SAVE_INTERVAL, MAX_PROJECT_FILES,
    SUPPORTED_WEB_EXTENSIONS, STORAGE_KEY_RECENT_PROJECTS
)


class ProjectManager:
    """Manages project operations - create, import, save, load"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.client_storage = page.client_storage
        self.current_project: Optional[ProjectMetadata] = None
        self.project_files: List[ProjectFile] = []
        self.project_path: Optional[Path] = None
        self.auto_save_timer: Optional[asyncio.Task] = None
        self.settings: ProjectSettings = ProjectSettings()
        
    async def create_new_project(self, name: str, description: str = "", location: str = None) -> bool:
        """Create a new empty project"""
        try:
            # Generate unique project ID
            project_id = str(uuid.uuid4())
            
            # Use default location if none provided
            if not location:
                home_dir = Path.home()
                projects_dir = home_dir / "CanvasEditor" / "Projects"
                projects_dir.mkdir(parents=True, exist_ok=True)
                location = str(projects_dir / name)
            
            project_path = Path(location)
            project_path.mkdir(parents=True, exist_ok=True)
            
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
            
            # Save project file
            project_file = project_path / "canvas-project.json"
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(metadata.to_dict(), f, indent=2)
            
            # Create basic project structure
            self._create_project_structure(project_path, name)
            
            # Set as current project
            self.current_project = metadata
            self.project_path = project_path
            
            # Add to recent projects
            await self._add_to_recent_projects(metadata)
            
            # Start auto-save
            if self.settings.auto_save:
                await self._start_auto_save()
            
            return True
            
        except Exception as e:
            print(f"Error creating project: {e}")
            return False
    
    def _create_project_structure(self, project_path: Path, name: str):
        """Create basic project structure with boilerplate files"""
        # Create directories
        (project_path / "src").mkdir(exist_ok=True)
        (project_path / "assets").mkdir(exist_ok=True)
        (project_path / "components").mkdir(exist_ok=True)
        
        # Create basic index.html
        index_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name}</title>
    <link rel="stylesheet" href="src/style.css">
</head>
<body>
    <div class="container">
        <h1>Welcome to {name}</h1>
        <p>Start building your application here.</p>
    </div>
    <script src="src/script.js"></script>
</body>
</html>'''
        
        with open(project_path / "index.html", 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        # Create basic CSS
        css_content = f'''/* {name} Styles */
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
        
        with open(project_path / "src" / "style.css", 'w', encoding='utf-8') as f:
            f.write(css_content)
        
        # Create basic JavaScript
        js_content = f'''// {name} JavaScript
document.addEventListener('DOMContentLoaded', function() {{
    console.log("{name} loaded successfully!");
}});'''
        
        with open(project_path / "src" / "script.js", 'w', encoding='utf-8') as f:
            f.write(js_content)
    
    async def import_existing_project(self, folder_path: str) -> bool:
        """Import an existing web project folder"""
        try:
            project_path = Path(folder_path)
            if not project_path.exists() or not project_path.is_dir():
                raise ValueError("Invalid project folder")
            
            # Check if it's already a Canvas project
            canvas_project_file = project_path / "canvas-project.json"
            
            if canvas_project_file.exists():
                # Load existing Canvas project
                return await self.load_project(str(project_path))
            
            # Create new project metadata for imported project
            project_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            # Detect framework
            framework = self._detect_framework(project_path)
            
            # Count web files
            web_files = self._scan_project_files(project_path)
            
            # Find main file
            main_file = self._find_main_file(project_path)
            
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
            
            return True
            
        except Exception as e:
            print(f"Error importing project: {e}")
            return False
    
    def _detect_framework(self, project_path: Path) -> Optional[str]:
        """Detect the web framework used in the project"""
        # Check for common framework indicators
        if (project_path / "package.json").exists():
            try:
                with open(project_path / "package.json", 'r') as f:
                    package_data = json.load(f)
                    deps = package_data.get("dependencies", {})
                    
                    if "react" in deps:
                        return "React"
                    elif "vue" in deps:
                        return "Vue"
                    elif "angular" in deps:
                        return "Angular"
                    elif "svelte" in deps:
                        return "Svelte"
            except:
                pass
        
        # Check for framework-specific files
        if (project_path / "angular.json").exists():
            return "Angular"
        elif (project_path / "vue.config.js").exists():
            return "Vue"
        elif (project_path / "svelte.config.js").exists():
            return "Svelte"
        
        return None
    
    def _scan_project_files(self, project_path: Path) -> List[ProjectFile]:
        """Scan project directory for web files"""
        files = []
        total_files = 0
        
        for file_path in project_path.rglob("*"):
            if file_path.is_file():
                total_files += 1
                
                # Skip if too many files
                if total_files > MAX_PROJECT_FILES:
                    break
                
                # Skip hidden files and common ignore patterns
                if any(part.startswith('.') for part in file_path.parts):
                    continue
                if 'node_modules' in file_path.parts:
                    continue
                
                # Get file info
                relative_path = file_path.relative_to(project_path)
                mime_type, _ = mimetypes.guess_type(str(file_path))
                is_web_file = file_path.suffix.lower() in SUPPORTED_WEB_EXTENSIONS
                
                files.append(ProjectFile(
                    path=str(file_path),
                    relative_path=str(relative_path),
                    size=file_path.stat().st_size,
                    modified=datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    mime_type=mime_type or "application/octet-stream",
                    is_web_file=is_web_file
                ))
        
        return files
    
    def _find_main_file(self, project_path: Path) -> Optional[str]:
        """Find the main entry file for the project"""
        # Common entry files
        candidates = [
            "index.html",
            "index.htm",
            "home.html",
            "main.html",
            "app.html",
            "src/index.html",
            "public/index.html",
            "dist/index.html"
        ]
        
        for candidate in candidates:
            file_path = project_path / candidate
            if file_path.exists():
                return str(file_path.relative_to(project_path))
        
        # If no standard file found, look for any HTML file
        for file_path in project_path.glob("**/*.html"):
            return str(file_path.relative_to(project_path))
        
        return None
    
    async def save_project(self) -> bool:
        """Save current project state"""
        if not self.current_project or not self.project_path:
            return False
        
        try:
            # Update modified time
            self.current_project.update_modified()
            
            # Save project metadata
            project_file = self.project_path / "canvas-project.json"
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_project.to_dict(), f, indent=2)
            
            # TODO: Save component tree and other project data
            
            return True
            
        except Exception as e:
            print(f"Error saving project: {e}")
            return False
    
    async def load_project(self, project_path: str) -> bool:
        """Load a Canvas project"""
        try:
            path = Path(project_path)
            project_file = path / "canvas-project.json"
            
            if not project_file.exists():
                raise ValueError("Not a valid Canvas project")
            
            # Load metadata
            with open(project_file, 'r', encoding='utf-8') as f:
                metadata_dict = json.load(f)
            
            self.current_project = ProjectMetadata.from_dict(metadata_dict)
            self.project_path = path
            
            # Load project settings
            if self.current_project.settings:
                self.settings = ProjectSettings.from_dict(self.current_project.settings)
            
            # Scan files
            self.project_files = self._scan_project_files(path)
            
            # Add to recent projects
            await self._add_to_recent_projects(self.current_project)
            
            # Start auto-save if enabled
            if self.settings.auto_save:
                await self._start_auto_save()
            
            return True
            
        except Exception as e:
            print(f"Error loading project: {e}")
            return False
    
    async def _add_to_recent_projects(self, project: ProjectMetadata):
        """Add project to recent projects list"""
        try:
            # Get existing recent projects
            recent_json = await self.client_storage.get_async(STORAGE_KEY_RECENT_PROJECTS)
            recent_projects = json.loads(recent_json) if recent_json else []
            
            # Remove if already exists
            recent_projects = [p for p in recent_projects if p.get("id") != project.id]
            
            # Add to beginning
            recent_projects.insert(0, project.to_dict())
            
            # Limit to max
            recent_projects = recent_projects[:MAX_RECENT_PROJECTS]
            
            # Save
            await self.client_storage.set_async(
                STORAGE_KEY_RECENT_PROJECTS,
                json.dumps(recent_projects)
            )
            
        except Exception as e:
            print(f"Error updating recent projects: {e}")
    
    async def get_recent_projects(self) -> List[ProjectMetadata]:
        """Get list of recent projects"""
        try:
            recent_json = await self.client_storage.get_async(STORAGE_KEY_RECENT_PROJECTS)
            if recent_json:
                recent_dicts = json.loads(recent_json)
                return [ProjectMetadata.from_dict(p) for p in recent_dicts]
        except:
            pass
        return []
    
    async def _start_auto_save(self):
        """Start auto-save timer"""
        if self.auto_save_timer:
            self.auto_save_timer.cancel()
        
        async def auto_save_loop():
            while True:
                await asyncio.sleep(self.settings.auto_save_interval)
                await self.save_project()
        
        self.auto_save_timer = asyncio.create_task(auto_save_loop())
    
    def close_project(self):
        """Close current project"""
        if self.auto_save_timer:
            self.auto_save_timer.cancel()
            self.auto_save_timer = None
        
        self.current_project = None
        self.project_path = None
        self.project_files = []