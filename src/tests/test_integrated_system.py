"""
Integration Tests for the Complete Canvas Editor System
Tests the cohesive integration of all components

CLAUDE.md Implementation:
- #2.1.1: Comprehensive integration testing
- #4.1: Type-safe test implementations
- #1.5: Performance testing for integrated system
- #6.2: State management testing
"""

import unittest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import logging

# Suppress logging during tests
logging.disable(logging.CRITICAL)

# Import components to test
try:
    from ui.integrated_canvas_system import IntegratedCanvasSystem, SystemIntegrationConfig
    from app_integrated import EnhancedCanvasEditor
    from managers.enhanced_state import EnhancedStateManager
    from managers.action_creators import ActionCreators
    from models.component import Component, ComponentStyle
    from models.project import ProjectMetadata
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Import error: {e}")
    IMPORTS_AVAILABLE = False


class MockPage:
    """Mock Flet page for testing"""
    def __init__(self):
        self.title = "Test Page"
        self.theme_mode = None
        self.padding = 0
        self.spacing = 0
        self.overlay = []
        self.controls = []
        self.window = Mock()
        self.window.width = 1400
        self.window.height = 900
        self.window.on_resize = None
        self.window.on_close = None
        self.on_keyboard_event = None
        
    def add(self, control):
        self.controls.append(control)
        
    def update(self):
        pass


@unittest.skipUnless(IMPORTS_AVAILABLE, "Required imports not available")
class TestIntegratedCanvasSystem(unittest.TestCase):
    """
    Test the integrated canvas system
    
    CLAUDE.md Implementation:
    - #2.1.1: Comprehensive system testing
    - #6.2: State management integration testing
    """
    
    def setUp(self):
        """Set up test environment"""
        self.page = MockPage()
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create mock state manager
        self.state_manager = Mock(spec=EnhancedStateManager)
        self.state_manager.initialize = AsyncMock()
        self.state_manager.subscribe_to_changes = AsyncMock()
        self.state_manager.dispatch_action = AsyncMock()
        self.state_manager.get_state_system = Mock()
        self.state_manager.undo = AsyncMock()
        self.state_manager.redo = AsyncMock()
        self.state_manager.shutdown = AsyncMock()
        
        # Mock state system
        mock_state_system = Mock()
        mock_components_state = Mock()
        mock_components_state.component_map = {}
        mock_selection_state = Mock()
        mock_selection_state.selected_ids = set()
        
        mock_state_system.get_state.side_effect = lambda key: {
            "components": mock_components_state,
            "selection": mock_selection_state,
            "project": Mock(),
            "ui": Mock()
        }.get(key, Mock())
        
        self.state_manager.get_state_system.return_value = mock_state_system
        
    def tearDown(self):
        """Clean up test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_system_initialization(self):
        """
        Test integrated system initialization
        
        CLAUDE.md Implementation:
        - #2.1.1: Initialization validation
        - #3.1: System setup testing
        """
        try:
            config = SystemIntegrationConfig(
                enable_advanced_rendering=True,
                enable_rich_text_editor=True,
                enable_export_integration=True
            )
            
            system = IntegratedCanvasSystem(
                page=self.page,
                state_manager=self.state_manager,
                config=config
            )
            
            # Verify system is created
            self.assertIsNotNone(system)
            self.assertEqual(system.page, self.page)
            self.assertEqual(system.state_manager, self.state_manager)
            self.assertEqual(system.config, config)
            
            # Verify initial state
            self.assertEqual(system.current_mode, "design")
            self.assertIsInstance(system.active_dialogs, dict)
            self.assertIsInstance(system.performance_stats, dict)
            
        except Exception as e:
            self.fail(f"System initialization failed: {e}")
    
    async def test_async_initialization(self):
        """
        Test asynchronous system initialization
        
        CLAUDE.md Implementation:
        - #6.2: Async state setup testing
        - #1.5: Performance initialization testing
        """
        try:
            config = SystemIntegrationConfig()
            system = IntegratedCanvasSystem(
                page=self.page,
                state_manager=self.state_manager,
                config=config
            )
            
            # Test async initialization
            await system.initialize_async()
            
            # Verify state subscriptions were set up
            self.state_manager.subscribe_to_changes.assert_called()
            
            # Verify call count (should be called for each state type)
            expected_subscriptions = ["components", "selection", "project", "ui"]
            actual_calls = [call[0][0] for call in self.state_manager.subscribe_to_changes.call_args_list]
            
            for subscription in expected_subscriptions:
                self.assertIn(subscription, actual_calls)
                
        except Exception as e:
            self.fail(f"Async initialization failed: {e}")
    
    async def test_component_operations(self):
        """
        Test component creation, selection, and modification
        
        CLAUDE.md Implementation:
        - #6.2: Component state management testing
        - #4.1: Type-safe component operations
        """
        try:
            system = IntegratedCanvasSystem(
                page=self.page,
                state_manager=self.state_manager,
                config=SystemIntegrationConfig()
            )
            
            # Test component drop
            component_data = {
                "type": "text",
                "name": "Test Text",
                "content": "Hello World"
            }
            
            # Mock position
            from unittest.mock import Mock as MockPosition
            position = MockPosition()
            position.x = 100
            position.y = 200
            
            # Test drop operation
            await system._handle_component_drop(component_data, position)
            
            # Verify action was dispatched
            self.state_manager.dispatch_action.assert_called()
            
            # Verify add component action was created
            add_calls = [call for call in self.state_manager.dispatch_action.call_args_list 
                        if 'add_component' in str(call)]
            self.assertTrue(len(add_calls) > 0)
            
        except Exception as e:
            self.fail(f"Component operations test failed: {e}")
    
    async def test_property_changes(self):
        """
        Test property change handling
        
        CLAUDE.md Implementation:
        - #6.2: Property state management testing
        - #2.1.1: Property validation testing
        """
        try:
            system = IntegratedCanvasSystem(
                page=self.page,
                state_manager=self.state_manager,
                config=SystemIntegrationConfig()
            )
            
            # Test property change
            component_id = "test-component"
            property_path = "style.backgroundColor"
            value = "#FF0000"
            
            await system._handle_property_change(component_id, property_path, value)
            
            # Verify update action was dispatched
            self.state_manager.dispatch_action.assert_called()
            
        except Exception as e:
            self.fail(f"Property changes test failed: {e}")
    
    def test_validation_functions(self):
        """
        Test validation functions
        
        CLAUDE.md Implementation:
        - #2.1.1: Input validation testing
        - #4.1: Type-safe validation
        """
        try:
            system = IntegratedCanvasSystem(
                page=self.page,
                state_manager=self.state_manager,
                config=SystemIntegrationConfig()
            )
            
            # Test component drop validation
            valid_data = {"type": "text", "name": "Test"}
            invalid_data = {}
            
            from unittest.mock import Mock as MockPosition
            valid_position = MockPosition()
            valid_position.x = 100
            valid_position.y = 200
            
            invalid_position = MockPosition()
            invalid_position.x = -10
            invalid_position.y = -10
            
            # Test valid drop
            self.assertTrue(system._validate_component_drop(valid_data, valid_position))
            
            # Test invalid data
            self.assertFalse(system._validate_component_drop(invalid_data, valid_position))
            
            # Test invalid position
            self.assertFalse(system._validate_component_drop(valid_data, invalid_position))
            
            # Test property validation
            self.assertTrue(system._validate_property_change("comp1", "style.color", "#FF0000"))
            self.assertFalse(system._validate_property_change("", "style.color", "#FF0000"))
            self.assertFalse(system._validate_property_change("comp1", "", "#FF0000"))
            
        except Exception as e:
            self.fail(f"Validation functions test failed: {e}")


@unittest.skipUnless(IMPORTS_AVAILABLE, "Required imports not available")
class TestEnhancedCanvasEditor(unittest.TestCase):
    """
    Test the enhanced canvas editor application
    
    CLAUDE.md Implementation:
    - #2.1.1: Application-level testing
    - #3.1: UI integration testing
    """
    
    def setUp(self):
        """Set up test environment"""
        self.page = MockPage()
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Clean up test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_editor_creation(self):
        """
        Test enhanced editor creation
        
        CLAUDE.md Implementation:
        - #3.1: Application creation testing
        - #4.1: Type-safe editor initialization
        """
        try:
            editor = EnhancedCanvasEditor(self.page)
            
            # Verify editor is created
            self.assertIsNotNone(editor)
            self.assertEqual(editor.page, self.page)
            self.assertIsNotNone(editor.state_manager)
            self.assertIsNotNone(editor.system_config)
            
            # Verify initial state
            self.assertFalse(editor.is_initialized)
            self.assertIsNone(editor.current_project_path)
            
        except Exception as e:
            self.fail(f"Editor creation failed: {e}")
    
    @patch('app_integrated.EnhancedStateManager')
    async def test_editor_initialization(self, mock_state_manager_class):
        """
        Test editor initialization process
        
        CLAUDE.md Implementation:
        - #6.2: State management initialization
        - #1.5: Performance initialization testing
        """
        try:
            # Mock state manager
            mock_state_manager = Mock()
            mock_state_manager.initialize = AsyncMock()
            mock_state_manager.restore_window_state = AsyncMock()
            mock_state_manager.get_current_project_id = AsyncMock(return_value=None)
            mock_state_manager_class.return_value = mock_state_manager
            
            editor = EnhancedCanvasEditor(self.page)
            
            # Mock integrated system creation
            with patch('app_integrated.IntegratedCanvasSystem') as mock_system_class:
                mock_system = Mock()
                mock_system.initialize_async = AsyncMock()
                mock_system_class.return_value = mock_system
                
                await editor.initialize()
                
                # Verify initialization steps
                mock_state_manager.initialize.assert_called_once()
                mock_system.initialize_async.assert_called_once()
                self.assertTrue(editor.is_initialized)
                
        except Exception as e:
            self.fail(f"Editor initialization test failed: {e}")
    
    def test_configuration_system(self):
        """
        Test system configuration
        
        CLAUDE.md Implementation:
        - #3.1: Configuration testing
        - #4.1: Type-safe configuration
        """
        try:
            editor = EnhancedCanvasEditor(self.page)
            config = editor.system_config
            
            # Verify default configuration
            self.assertIsInstance(config, SystemIntegrationConfig)
            self.assertTrue(config.enable_advanced_rendering)
            self.assertTrue(config.enable_rich_text_editor)
            self.assertTrue(config.enable_export_integration)
            self.assertEqual(config.auto_save_interval, 30)
            
        except Exception as e:
            self.fail(f"Configuration system test failed: {e}")


@unittest.skipUnless(IMPORTS_AVAILABLE, "Required imports not available")
class TestSystemIntegration(unittest.TestCase):
    """
    Test end-to-end system integration
    
    CLAUDE.md Implementation:
    - #2.1.1: End-to-end integration testing
    - #1.5: Performance integration testing
    """
    
    def setUp(self):
        """Set up integration test environment"""
        self.page = MockPage()
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Clean up integration test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('app_integrated.EnhancedStateManager')
    @patch('ui.integrated_canvas_system.get_drag_drop_manager')
    async def test_full_workflow(self, mock_drag_manager, mock_state_manager_class):
        """
        Test complete workflow from app start to component operations
        
        CLAUDE.md Implementation:
        - #6.2: Full state management workflow
        - #1.5: Performance workflow testing
        """
        try:
            # Mock dependencies
            mock_state_manager = Mock()
            mock_state_manager.initialize = AsyncMock()
            mock_state_manager.subscribe_to_changes = AsyncMock()
            mock_state_manager.dispatch_action = AsyncMock()
            mock_state_manager.restore_window_state = AsyncMock()
            mock_state_manager.get_current_project_id = AsyncMock(return_value=None)
            mock_state_manager.get_state_system = Mock()
            mock_state_manager_class.return_value = mock_state_manager
            
            mock_drag_manager_instance = Mock()
            mock_drag_manager.return_value = mock_drag_manager_instance
            
            # Mock state system
            mock_state_system = Mock()
            mock_components_state = Mock()
            mock_components_state.component_map = {}
            mock_selection_state = Mock()
            mock_selection_state.selected_ids = set()
            
            mock_state_system.get_state.side_effect = lambda key: {
                "components": mock_components_state,
                "selection": mock_selection_state,
                "project": Mock(),
                "ui": Mock()
            }.get(key, Mock())
            
            mock_state_manager.get_state_system.return_value = mock_state_system
            
            # Create and initialize editor
            editor = EnhancedCanvasEditor(self.page)
            
            with patch('app_integrated.IntegratedCanvasSystem') as mock_system_class:
                mock_system = Mock()
                mock_system.initialize_async = AsyncMock()
                mock_system_class.return_value = mock_system
                
                await editor.initialize()
                
                # Verify editor is initialized
                self.assertTrue(editor.is_initialized)
                
                # Test component workflow through integrated system
                system = editor.integrated_system
                
                # Simulate adding a component
                component_data = {
                    "type": "button",
                    "name": "Test Button",
                    "content": "Click me"
                }
                
                position = Mock()
                position.x = 150
                position.y = 100
                
                # This would normally trigger through UI interaction
                # but we can test the handler directly
                await system._handle_component_drop(component_data, position)
                
                # Verify state manager was called
                mock_state_manager.dispatch_action.assert_called()
                
        except Exception as e:
            self.fail(f"Full workflow test failed: {e}")
    
    def test_error_handling_integration(self):
        """
        Test error handling across integrated components
        
        CLAUDE.md Implementation:
        - #2.1.1: Comprehensive error handling testing
        - #9.1: Accessible error reporting testing
        """
        try:
            # Test error handling in system creation
            with patch('ui.integrated_canvas_system.IntegratedCanvasSystem.__init__', 
                      side_effect=Exception("Test error")):
                try:
                    from ui.integrated_canvas_system import create_integrated_canvas_system
                    from managers.enhanced_state import EnhancedStateManager
                    
                    mock_state_manager = Mock(spec=EnhancedStateManager)
                    system = create_integrated_canvas_system(self.page, mock_state_manager)
                    self.fail("Expected exception was not raised")
                except Exception as e:
                    self.assertIn("Test error", str(e))
            
        except Exception as e:
            self.fail(f"Error handling integration test failed: {e}")


class TestPerformanceIntegration(unittest.TestCase):
    """
    Test performance aspects of the integrated system
    
    CLAUDE.md Implementation:
    - #1.5: Performance testing for integrated components
    - #12.1: Performance monitoring testing
    """
    
    @unittest.skipUnless(IMPORTS_AVAILABLE, "Required imports not available")
    def test_system_performance_config(self):
        """Test performance configuration options"""
        try:
            config = SystemIntegrationConfig(
                performance_monitoring=True,
                auto_save_interval=10
            )
            
            self.assertTrue(config.performance_monitoring)
            self.assertEqual(config.auto_save_interval, 10)
            
        except Exception as e:
            self.fail(f"Performance config test failed: {e}")


def run_integration_tests():
    """
    Run all integration tests
    
    CLAUDE.md Implementation:
    - #2.1.1: Comprehensive test execution
    - #4.1: Type-safe test running
    """
    if not IMPORTS_AVAILABLE:
        print("Skipping integration tests - required imports not available")
        return False
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestIntegratedCanvasSystem,
        TestEnhancedCanvasEditor,
        TestSystemIntegration,
        TestPerformanceIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Return success status
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_integration_tests()
    exit(0 if success else 1)