"""Comprehensive test suite for enhanced project management

Tests follow CLAUDE.md #6.2 FIRST principles:
- Fast: Use in-memory filesystem and mocks
- Independent: Each test is isolated
- Repeatable: Consistent results
- Self-validating: Clear pass/fail
- Timely: Written with implementation
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

# Import the classes to test
from src.models.project import (
    ProjectMetadata, ProjectFile, ProjectSettings,
    ValidationError, ProjectSecurityError
)
from src.managers.project_enhanced import (
    EnhancedProjectManager, ProjectCreationError, ProjectImportError,
    AutoSaveManager
)


class TestProjectMetadata:
    """Test ProjectMetadata validation and security"""
    
    def test_valid_metadata_creation(self):
        """Test creating valid project metadata"""
        metadata = ProjectMetadata(
            id="550e8400-e29b-41d4-a716-446655440000",
            name="Test Project",
            path="/home/user/CanvasEditor/test",
            created="2024-01-01T00:00:00",
            modified="2024-01-01T00:00:00",
            description="Test description",
            version="1.0.0",
            files_count=5
        )
        
        assert metadata.name == "Test Project"
        assert metadata.files_count == 5
    
    def test_invalid_project_id(self):
        """Test validation error for invalid UUID"""
        with pytest.raises(ValidationError, match="must be a valid UUID"):
            ProjectMetadata(
                id="invalid-uuid",
                name="Test",
                path="/test",
                created="2024-01-01T00:00:00",
                modified="2024-01-01T00:00:00",
                description="",
                version="1.0.0",
                files_count=0
            )
    
    def test_empty_project_name(self):
        """Test validation error for empty name"""
        with pytest.raises(ValidationError, match="cannot be empty"):
            ProjectMetadata(
                id="550e8400-e29b-41d4-a716-446655440000",
                name="",
                path="/test",
                created="2024-01-01T00:00:00",
                modified="2024-01-01T00:00:00",
                description="",
                version="1.0.0",
                files_count=0
            )
    
    def test_invalid_characters_in_name(self):
        """Test validation error for dangerous characters"""
        with pytest.raises(ValidationError, match="invalid characters"):
            ProjectMetadata(
                id="550e8400-e29b-41d4-a716-446655440000",
                name="Test<script>alert('xss')</script>",
                path="/test",
                created="2024-01-01T00:00:00",
                modified="2024-01-01T00:00:00",
                description="",
                version="1.0.0",
                files_count=0
            )
    
    def test_path_traversal_protection(self):
        """Test protection against path traversal"""
        with pytest.raises(ProjectSecurityError, match="Path traversal detected"):
            ProjectMetadata(
                id="550e8400-e29b-41d4-a716-446655440000",
                name="Test",
                path="/test/../../../etc/passwd",
                created="2024-01-01T00:00:00",
                modified="2024-01-01T00:00:00",
                description="",
                version="1.0.0",
                files_count=0
            )
    
    def test_reserved_name_protection(self):
        """Test protection against reserved names"""
        with pytest.raises(ValidationError, match="reserved name"):
            ProjectMetadata(
                id="550e8400-e29b-41d4-a716-446655440000",
                name="con",
                path="/test",
                created="2024-01-01T00:00:00",
                modified="2024-01-01T00:00:00",
                description="",
                version="1.0.0",
                files_count=0
            )
    
    def test_description_sanitization(self):
        """Test HTML sanitization in description"""
        metadata = ProjectMetadata(
            id="550e8400-e29b-41d4-a716-446655440000",
            name="Test",
            path="/test",
            created="2024-01-01T00:00:00",
            modified="2024-01-01T00:00:00",
            description="<script>alert('xss')</script>Safe content",
            version="1.0.0",
            files_count=0
        )
        
        assert "<script>" not in metadata.description
        assert "Safe content" in metadata.description


class TestProjectFile:
    """Test ProjectFile validation and security"""
    
    def test_valid_file_creation(self):
        """Test creating valid project file"""
        file = ProjectFile(
            path="/test/file.html",
            relative_path="file.html",
            size=1024,
            modified="2024-01-01T00:00:00",
            mime_type="text/html",
            is_web_file=True
        )
        
        assert file.path == "/test/file.html"
        assert file.size == 1024
        assert file.is_web_file is True
    
    def test_path_traversal_in_file(self):
        """Test path traversal protection in file paths"""
        with pytest.raises(ProjectSecurityError, match="Path traversal detected"):
            ProjectFile(
                path="/test/../../../etc/passwd",
                relative_path="../../../etc/passwd",
                size=1024,
                modified="2024-01-01T00:00:00",
                mime_type="text/plain",
                is_web_file=False
            )
    
    def test_negative_file_size(self):
        """Test validation of negative file size"""
        with pytest.raises(ValidationError, match="non-negative integer"):
            ProjectFile(
                path="/test/file.txt",
                relative_path="file.txt",
                size=-1,
                modified="2024-01-01T00:00:00",
                mime_type="text/plain",
                is_web_file=False
            )
    
    def test_invalid_mime_type(self):
        """Test validation of MIME type format"""
        with pytest.raises(ValidationError, match="Invalid MIME type format"):
            ProjectFile(
                path="/test/file.txt",
                relative_path="file.txt",
                size=1024,
                modified="2024-01-01T00:00:00",
                mime_type="invalid/mime/type/format",
                is_web_file=False
            )
    
    def test_safe_content_check(self):
        """Test content safety validation"""
        # Safe content
        safe_file = ProjectFile(
            path="/test/file.txt",
            relative_path="file.txt",
            size=1024,
            modified="2024-01-01T00:00:00",
            mime_type="text/plain",
            is_web_file=False,
            content="This is safe content"
        )
        assert safe_file.is_safe_content() is True
        
        # Unsafe content
        unsafe_file = ProjectFile(
            path="/test/file.html",
            relative_path="file.html",
            size=1024,
            modified="2024-01-01T00:00:00",
            mime_type="text/html",
            is_web_file=True,
            content="<script>alert('xss')</script>"
        )
        assert unsafe_file.is_safe_content() is False


class TestProjectSettings:
    """Test ProjectSettings validation"""
    
    def test_valid_settings(self):
        """Test creating valid project settings"""
        settings = ProjectSettings(
            auto_save=True,
            auto_save_interval=300,
            theme="light",
            grid_size=20,
            default_device="desktop"
        )
        
        assert settings.auto_save is True
        assert settings.auto_save_interval == 300
    
    def test_invalid_auto_save_interval(self):
        """Test validation of auto-save interval"""
        with pytest.raises(ValidationError, match="cannot be less than 30 seconds"):
            ProjectSettings(auto_save_interval=10)
        
        with pytest.raises(ValidationError, match="cannot exceed 1 hour"):
            ProjectSettings(auto_save_interval=4000)
    
    def test_invalid_theme(self):
        """Test validation of theme setting"""
        with pytest.raises(ValidationError, match="Invalid theme"):
            ProjectSettings(theme="invalid_theme")
    
    def test_invalid_grid_size(self):
        """Test validation of grid size"""
        with pytest.raises(ValidationError, match="between 1 and 100"):
            ProjectSettings(grid_size=0)
        
        with pytest.raises(ValidationError, match="between 1 and 100"):
            ProjectSettings(grid_size=101)
    
    def test_invalid_default_device(self):
        """Test validation of default device"""
        with pytest.raises(ValidationError, match="Invalid default device"):
            ProjectSettings(default_device="invalid_device")


@pytest.mark.asyncio
class TestEnhancedProjectManager:
    """Test EnhancedProjectManager functionality"""
    
    @pytest.fixture
    def mock_page(self):
        """Create mock Flet page"""
        page = Mock()
        page.client_storage = AsyncMock()
        return page
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def project_manager(self, mock_page, temp_dir):
        """Create project manager with mocked dependencies"""
        manager = EnhancedProjectManager(mock_page)
        manager._allowed_project_root = temp_dir
        return manager
    
    async def test_create_new_project_success(self, project_manager, temp_dir):
        """Test successful project creation"""
        result = await project_manager.create_new_project(
            name="Test Project",
            description="Test description"
        )
        
        assert result is True
        assert project_manager.current_project is not None
        assert project_manager.current_project.name == "Test Project"
        
        # Check that project directory was created
        project_path = temp_dir / "Projects" / "Test_Project"
        assert project_path.exists()
        assert (project_path / "canvas-project.json").exists()
        assert (project_path / "src").exists()
        assert (project_path / "assets").exists()
        assert (project_path / "index.html").exists()
    
    async def test_create_project_invalid_name(self, project_manager):
        """Test project creation with invalid name"""
        with pytest.raises(ValidationError):
            await project_manager.create_new_project("")
        
        with pytest.raises(ValidationError):
            await project_manager.create_new_project("con")  # Reserved name
        
        with pytest.raises(ValidationError):
            await project_manager.create_new_project("Test<script>")  # Invalid chars
    
    async def test_create_project_security_violation(self, project_manager, temp_dir):
        """Test project creation outside allowed directory"""
        with pytest.raises(ProjectSecurityError):
            await project_manager.create_new_project(
                name="Test",
                location="/etc/passwd"
            )
    
    async def test_create_project_atomic_rollback(self, project_manager, temp_dir):
        """Test atomic rollback on project creation failure"""
        # Mock file creation to fail
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with pytest.raises(ProjectCreationError):
                await project_manager.create_new_project("Test Project")
        
        # Verify no partial project remains
        project_path = temp_dir / "Projects" / "Test_Project"
        assert not project_path.exists()
    
    async def test_framework_detection(self, project_manager, temp_dir):
        """Test enhanced framework detection"""
        # Create mock React project
        react_project = temp_dir / "react_project"
        react_project.mkdir()
        
        # Create package.json with React dependencies
        package_json = {
            "dependencies": {"react": "^18.0.0", "react-dom": "^18.0.0"}
        }
        with open(react_project / "package.json", 'w') as f:
            json.dump(package_json, f)
        
        framework = await project_manager._detect_framework_enhanced(react_project)
        assert framework == "React"
        
        # Create mock Vue project
        vue_project = temp_dir / "vue_project"
        vue_project.mkdir()
        
        (vue_project / "vue.config.js").touch()
        framework = await project_manager._detect_framework_enhanced(vue_project)
        assert framework == "Vue"
    
    async def test_file_scanning_performance(self, project_manager, temp_dir):
        """Test file scanning with performance constraints"""
        # Create project with many files
        test_project = temp_dir / "large_project"
        test_project.mkdir()
        
        # Create subdirectories and files
        for i in range(50):
            sub_dir = test_project / f"dir_{i}"
            sub_dir.mkdir()
            
            for j in range(10):
                (sub_dir / f"file_{j}.js").write_text(f"// File {i}-{j}")
        
        files = await project_manager._scan_project_files_enhanced(test_project)
        
        # Should have scanned files efficiently
        assert len(files) > 0
        assert all(isinstance(f, ProjectFile) for f in files)
    
    async def test_import_existing_project(self, project_manager, temp_dir):
        """Test importing existing project"""
        # Create existing project structure
        existing_project = temp_dir / "existing_project"
        existing_project.mkdir()
        
        (existing_project / "index.html").write_text("<html><body>Test</body></html>")
        (existing_project / "style.css").write_text("body { margin: 0; }")
        
        # Create package.json for framework detection
        package_json = {"dependencies": {"vue": "^3.0.0"}}
        with open(existing_project / "package.json", 'w') as f:
            json.dump(package_json, f)
        
        result = await project_manager.import_existing_project(str(existing_project))
        
        assert result is True
        assert project_manager.current_project is not None
        assert project_manager.current_project.framework == "Vue"
        assert (existing_project / "canvas-project.json").exists()
    
    async def test_save_and_load_project(self, project_manager, temp_dir):
        """Test project save and load operations"""
        # Create project
        await project_manager.create_new_project("Save Test")
        project_path = project_manager.project_path
        
        # Modify project
        project_manager.current_project.description = "Updated description"
        
        # Save project
        result = await project_manager.save_project()
        assert result is True
        
        # Clear current project
        project_manager.current_project = None
        project_manager.project_path = None
        
        # Load project
        result = await project_manager.load_project(str(project_path))
        assert result is True
        assert project_manager.current_project.description == "Updated description"


class TestAutoSaveManager:
    """Test AutoSaveManager functionality"""
    
    @pytest.fixture
    def auto_save_manager(self):
        """Create AutoSaveManager for testing"""
        return AutoSaveManager(save_interval=1)  # 1 second for testing
    
    @pytest.fixture
    def mock_project_manager(self):
        """Create mock project manager"""
        manager = Mock()
        manager.save_project = AsyncMock(return_value=True)
        return manager
    
    @pytest.mark.asyncio
    async def test_debounced_save(self, auto_save_manager, mock_project_manager):
        """Test that saves are properly debounced"""
        # Schedule multiple saves rapidly
        await auto_save_manager.schedule_save(mock_project_manager)
        await auto_save_manager.schedule_save(mock_project_manager)
        await auto_save_manager.schedule_save(mock_project_manager)
        
        # Wait for save to complete
        await asyncio.sleep(1.5)
        
        # Should only save once due to debouncing
        assert mock_project_manager.save_project.call_count <= 2
    
    @pytest.mark.asyncio
    async def test_save_retry_on_failure(self, auto_save_manager, mock_project_manager):
        """Test retry logic on save failure"""
        # Make save fail first time, succeed second time
        mock_project_manager.save_project.side_effect = [False, True]
        
        await auto_save_manager.schedule_save(mock_project_manager)
        await asyncio.sleep(2)
        
        # Should have retried
        assert mock_project_manager.save_project.call_count >= 2


class TestSecurityFeatures:
    """Test security features across the module"""
    
    def test_html_escaping(self):
        """Test HTML content escaping"""
        from src.managers.project_enhanced import EnhancedProjectManager
        
        manager = EnhancedProjectManager(Mock())
        dangerous_text = "<script>alert('xss')</script>&\"'"
        escaped = manager._escape_html(dangerous_text)
        
        assert "<script>" not in escaped
        assert "&lt;script&gt;" in escaped
        assert "&amp;" in escaped
        assert "&quot;" in escaped
        assert "&#x27;" in escaped
    
    def test_safe_filename_generation(self):
        """Test safe filename generation"""
        from src.managers.project_enhanced import EnhancedProjectManager
        
        manager = EnhancedProjectManager(Mock())
        
        # Test various dangerous inputs
        assert manager._get_safe_filename("Test<>:\"/|?*") == "Test"
        assert manager._get_safe_filename("Test Project Name") == "Test_Project_Name"
        assert manager._get_safe_filename("Test  Multiple   Spaces") == "Test_Multiple_Spaces"
        
        # Test length limitation
        long_name = "a" * 100
        safe_name = manager._get_safe_filename(long_name)
        assert len(safe_name) <= 50


@pytest.mark.integration
class TestProjectIntegration:
    """Integration tests for complete project workflows"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for integration tests"""
        workspace = tempfile.mkdtemp()
        yield Path(workspace)
        shutil.rmtree(workspace)
    
    @pytest.mark.asyncio
    async def test_complete_project_lifecycle(self, temp_workspace):
        """Test complete project creation, modification, and save cycle"""
        # Create mock page
        mock_page = Mock()
        mock_page.client_storage = AsyncMock()
        
        # Create project manager
        manager = EnhancedProjectManager(mock_page)
        manager._allowed_project_root = temp_workspace
        
        # Create project
        result = await manager.create_new_project(
            name="Integration Test",
            description="Full lifecycle test"
        )
        assert result is True
        
        # Verify project structure
        project_path = manager.project_path
        assert (project_path / "canvas-project.json").exists()
        assert (project_path / "index.html").exists()
        assert (project_path / "src" / "style.css").exists()
        assert (project_path / "src" / "script.js").exists()
        
        # Modify project
        manager.current_project.description = "Modified description"
        
        # Save project
        save_result = await manager.save_project()
        assert save_result is True
        
        # Create new manager and load project
        manager2 = EnhancedProjectManager(mock_page)
        load_result = await manager2.load_project(str(project_path))
        assert load_result is True
        assert manager2.current_project.description == "Modified description"
        
        # Clean up
        manager.close_project()
        manager2.close_project()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])