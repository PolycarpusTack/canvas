"""
Comprehensive Integration Tests for Complete Property Editor System
Tests the full property editor system end-to-end
Following CLAUDE.md guidelines for comprehensive testing
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Dict, List
import threading
import time

# Import modules to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.components.property_definitions import (
    PropertyDefinition, PropertyType, PropertyCategory, PropertyValidation,
    PropertyDependency, ValidationResult, ResponsiveValue
)
from src.components.property_registry import PropertyRegistry, get_registry
from src.components.default_component_properties import register_default_components
from src.ui.panels.complete_property_panel import PropertyPanel, EnhancedPropertiesPanel
from src.ui.inputs.property_input_base import create_property_input
from src.ui.inputs.advanced_inputs import (
    FilePropertyInput, IconPropertyInput, DatePropertyInput, RangePropertyInput
)
from src.ui.components.virtual_property_list import VirtualPropertyList, DependencyAwarePropertyGroup
from src.integration.property_canvas_integration import PropertyCanvasIntegrator, PropertyEditorManager
from src.models.component import Component, ComponentStyle


class TestCompletePropertySystemIntegration(unittest.TestCase):
    """
    Integration tests for the complete property editor system
    Tests all components working together
    """
    
    def setUp(self):
        """Set up test environment"""
        # Reset singleton
        PropertyRegistry._instance = None
        self.registry = PropertyRegistry()
        
        # Register default components
        register_default_components()
        
        # Mock canvas container
        self.mock_canvas = Mock()
        
        # Track callbacks
        self.property_changes = []
        self.validation_results = []
        
    def test_end_to_end_property_editing_workflow(self):
        """Test complete workflow from component selection to property editing"""
        # 1. Create property editor manager
        manager = PropertyEditorManager(self.mock_canvas)
        
        # 2. Get property panel
        property_panel = manager.get_property_panel()
        self.assertIsInstance(property_panel, PropertyPanel)
        
        # 3. Create a test component
        test_component_data = {
            "id": "test_button_1",
            "type": "button",
            "name": "Test Button",
            "properties": {
                "text": "Click me",
                "variant": "primary",
                "background_color": "#5E6AD2"
            },
            "style": {
                "width": "120px",
                "height": "40px"
            }
        }
        
        # 4. Select component for editing
        manager.select_component("test_button_1", test_component_data)
        
        # 5. Verify component is loaded in property panel
        current_component = property_panel.get_current_component()
        self.assertIsNotNone(current_component)
        self.assertEqual(current_component.id, "test_button_1")
        self.assertEqual(current_component.type, "button")
        
        # 6. Verify properties are available
        integrator = manager.get_integrator()
        button_properties = integrator.get_component_properties("button")
        self.assertTrue(len(button_properties) > 0)
        
        # 7. Test property value retrieval
        text_value = integrator.get_property_value("test_button_1", "text")
        self.assertEqual(text_value, "Click me")
        
        # 8. Test property value setting
        success = integrator.set_property_value("test_button_1", "text", "Updated Text")
        self.assertTrue(success)
        
        # 9. Verify value was updated
        updated_text = integrator.get_property_value("test_button_1", "text")
        self.assertEqual(updated_text, "Updated Text")
    
    def test_property_validation_integration(self):
        """Test property validation throughout the system"""
        # Create integrator
        integrator = PropertyCanvasIntegrator()
        
        # Create test component with invalid properties
        invalid_component_data = {
            "id": "invalid_button",
            "type": "button",
            "properties": {
                "text": "",  # Empty text (invalid for required field)
                "background_color": "not-a-color",  # Invalid color
                "font_size": "abc"  # Invalid number
            }
        }
        
        # Set component
        integrator.set_selected_component("invalid_button", invalid_component_data)
        
        # Get validation state
        validation_state = integrator.get_validation_state("invalid_button")
        
        # Should have validation errors
        self.assertTrue(len(validation_state) > 0)
        
        # Test individual property validation
        text_result = integrator.registry.validate_property_value("button", "text", "")
        self.assertFalse(text_result.is_valid)
        
        color_result = integrator.registry.validate_property_value("button", "background_color", "not-a-color")
        self.assertFalse(color_result.is_valid)
        
        # Test valid values
        valid_text_result = integrator.registry.validate_property_value("button", "text", "Valid Text")
        self.assertTrue(valid_text_result.is_valid)
        
        valid_color_result = integrator.registry.validate_property_value("button", "background_color", "#FF0000")
        self.assertTrue(valid_color_result.is_valid)
    
    def test_property_dependencies_system(self):
        """Test property dependency evaluation and UI updates"""
        # Create properties with dependencies
        properties = [
            PropertyDefinition(
                name="show_advanced",
                label="Show Advanced Options",
                category=PropertyCategory.CONTENT,
                type=PropertyType.BOOLEAN,
                default_value=False
            ),
            PropertyDefinition(
                name="advanced_option",
                label="Advanced Option",
                category=PropertyCategory.ADVANCED,
                type=PropertyType.TEXT,
                default_value="",
                dependencies=[
                    PropertyDependency("show_advanced", "equals", True, "show")
                ]
            ),
            PropertyDefinition(
                name="variant",
                label="Button Variant",
                category=PropertyCategory.STYLE,
                type=PropertyType.SELECT,
                default_value="primary",
                options=[
                    PropertyOption("primary", "Primary"),
                    PropertyOption("secondary", "Secondary"),
                    PropertyOption("custom", "Custom")
                ]
            ),
            PropertyDefinition(
                name="custom_color",
                label="Custom Color",
                category=PropertyCategory.STYLE,
                type=PropertyType.COLOR,
                default_value="#FF0000",
                dependencies=[
                    PropertyDependency("variant", "equals", "custom", "show")
                ]
            )
        ]
        
        # Register test component
        self.registry.register_component_properties("test_deps", properties)
        
        # Test dependency evaluation
        advanced_prop = self.registry.get_property("test_deps", "advanced_option")
        custom_color_prop = self.registry.get_property("test_deps", "custom_color")
        
        # Test when dependencies are not met
        values = {"show_advanced": False, "variant": "primary"}
        
        advanced_states = advanced_prop.evaluate_dependencies(values)
        self.assertFalse(advanced_states["visible"])
        
        custom_color_states = custom_color_prop.evaluate_dependencies(values)
        self.assertFalse(custom_color_states["visible"])
        
        # Test when dependencies are met
        values = {"show_advanced": True, "variant": "custom"}
        
        advanced_states = advanced_prop.evaluate_dependencies(values)
        self.assertTrue(advanced_states["visible"])
        
        custom_color_states = custom_color_prop.evaluate_dependencies(values)
        self.assertTrue(custom_color_states["visible"])
    
    def test_multi_component_selection(self):
        """Test editing multiple components simultaneously"""
        integrator = PropertyCanvasIntegrator()
        
        # Create multiple components
        component_ids = ["button1", "button2", "button3"]
        
        # Test multi-selection
        integrator.set_multi_selection(component_ids)
        
        # Should handle multi-selection properly
        self.assertEqual(len(integrator.selected_components), 3)
    
    def test_virtual_scrolling_performance(self):
        """Test virtual scrolling with large property lists"""
        # Create a large number of properties
        large_property_list = []
        for i in range(100):
            prop = PropertyDefinition(
                name=f"property_{i}",
                label=f"Property {i}",
                category=PropertyCategory.CONTENT,
                type=PropertyType.TEXT,
                default_value=f"value_{i}"
            )
            large_property_list.append(prop)
        
        # Create property values
        property_values = {f"property_{i}": f"value_{i}" for i in range(100)}
        
        # Create virtual list
        virtual_list = VirtualPropertyList(
            properties=large_property_list,
            property_values=property_values,
            on_property_change=lambda name, value: None,
            item_height=80,
            visible_items=10
        )
        
        # Test performance stats
        stats = virtual_list.get_performance_stats()
        self.assertEqual(stats["total_properties"], 100)
        self.assertEqual(stats["item_height"], 80)
        
        # Test that only visible items are rendered initially
        self.assertTrue(len(virtual_list.rendered_inputs) <= 12)  # visible + buffer
    
    def test_property_search_and_filtering(self):
        """Test property search and filtering functionality"""
        # Get button properties
        button_properties = self.registry.get_component_properties("button")
        
        # Test search by name
        search_results = self.registry.search_properties("text", "button")
        text_props = [p for p in search_results if "text" in p.name.lower()]
        self.assertTrue(len(text_props) > 0)
        
        # Test search by tag
        color_results = self.registry.search_properties("color", "button")
        self.assertTrue(len(color_results) > 0)
        
        # Test category filtering
        style_props = [p for p in button_properties if p.category == PropertyCategory.STYLE]
        self.assertTrue(len(style_props) > 0)
    
    def test_property_export_import(self):
        """Test property export and import functionality"""
        integrator = PropertyCanvasIntegrator()
        
        # Create test component
        component_data = {
            "id": "export_test",
            "type": "button",
            "properties": {
                "text": "Export Test",
                "variant": "primary",
                "background_color": "#FF0000"
            }
        }
        
        integrator.set_selected_component("export_test", component_data)
        
        # Export properties
        exported = integrator.export_component_properties("export_test")
        self.assertIsNotNone(exported)
        self.assertEqual(exported["component_id"], "export_test")
        self.assertEqual(exported["component_type"], "button")
        self.assertIn("properties", exported)
        
        # Create new component and import properties
        new_component_data = {
            "id": "import_test",
            "type": "button",
            "properties": {}
        }
        
        integrator.set_selected_component("import_test", new_component_data)
        
        # Import properties
        success = integrator.import_component_properties("import_test", exported)
        self.assertTrue(success)
        
        # Verify imported values
        imported_text = integrator.get_property_value("import_test", "text")
        self.assertEqual(imported_text, "Export Test")
    
    def test_responsive_breakpoint_system(self):
        """Test responsive breakpoint functionality"""
        # Create responsive property
        responsive_prop = PropertyDefinition(
            name="font_size",
            label="Font Size",
            category=PropertyCategory.TYPOGRAPHY,
            type=PropertyType.SIZE,
            default_value="16px",
            responsive=True
        )
        
        # Test responsive value
        responsive_value = ResponsiveValue(
            base="16px",
            breakpoints={
                "sm": "14px",
                "md": "18px",
                "lg": "20px"
            }
        )
        
        # Test value retrieval for different breakpoints
        self.assertEqual(responsive_prop.get_responsive_value(responsive_value, "base"), "16px")
        self.assertEqual(responsive_prop.get_responsive_value(responsive_value, "sm"), "14px")
        self.assertEqual(responsive_prop.get_responsive_value(responsive_value, "md"), "18px")
        self.assertEqual(responsive_prop.get_responsive_value(responsive_value, "xl"), "16px")  # fallback
    
    def test_advanced_input_types(self):
        """Test all advanced input types"""
        # File input
        file_prop = PropertyDefinition(
            name="file_upload",
            label="File Upload",
            category=PropertyCategory.CONTENT,
            type=PropertyType.FILE,
            default_value="",
            validation=PropertyValidation(
                allowed_extensions=["jpg", "png", "pdf"],
                max_file_size=5 * 1024 * 1024  # 5MB
            )
        )
        
        file_input = FilePropertyInput(file_prop, "", lambda name, val: None)
        self.assertIsInstance(file_input, FilePropertyInput)
        
        # Icon input
        icon_prop = PropertyDefinition(
            name="icon",
            label="Icon",
            category=PropertyCategory.STYLE,
            type=PropertyType.ICON,
            default_value="home"
        )
        
        icon_input = IconPropertyInput(icon_prop, "home", lambda name, val: None)
        self.assertIsInstance(icon_input, IconPropertyInput)
        
        # Date input
        date_prop = PropertyDefinition(
            name="date",
            label="Date",
            category=PropertyCategory.CONTENT,
            type=PropertyType.DATE,
            default_value=""
        )
        
        date_input = DatePropertyInput(date_prop, "", lambda name, val: None)
        self.assertIsInstance(date_input, DatePropertyInput)
        
        # Range input
        range_prop = PropertyDefinition(
            name="opacity",
            label="Opacity",
            category=PropertyCategory.EFFECTS,
            type=PropertyType.RANGE,
            default_value=1.0,
            min_value=0.0,
            max_value=1.0,
            step=0.1
        )
        
        range_input = RangePropertyInput(range_prop, 1.0, lambda name, val: None)
        self.assertIsInstance(range_input, RangePropertyInput)
    
    def test_property_history_tracking(self):
        """Test property change history tracking"""
        integrator = PropertyCanvasIntegrator()
        
        # Create test component
        component_data = {
            "id": "history_test",
            "type": "button",
            "properties": {"text": "Initial"}
        }
        
        integrator.set_selected_component("history_test", component_data)
        
        # Make several property changes
        integrator.set_property_value("history_test", "text", "First Change")
        integrator.set_property_value("history_test", "text", "Second Change")
        integrator.set_property_value("history_test", "text", "Third Change")
        
        # Get change history
        history = integrator.get_property_history("history_test", "text")
        
        # Should have tracked changes
        self.assertTrue(len(history) >= 3)
    
    def test_property_reset_functionality(self):
        """Test property reset to defaults"""
        integrator = PropertyCanvasIntegrator()
        
        # Create component with modified properties
        component_data = {
            "id": "reset_test",
            "type": "button",
            "properties": {
                "text": "Modified Text",
                "variant": "secondary",
                "background_color": "#FF0000"
            }
        }
        
        integrator.set_selected_component("reset_test", component_data)
        
        # Reset all properties
        success = integrator.reset_component_properties("reset_test")
        self.assertTrue(success)
        
        # Verify properties are reset to defaults
        text_value = integrator.get_property_value("reset_test", "text")
        variant_value = integrator.get_property_value("reset_test", "variant")
        
        # Should match default values from component definition
        button_props = integrator.get_component_properties("button")
        text_prop = next(p for p in button_props if p.name == "text")
        variant_prop = next(p for p in button_props if p.name == "variant")
        
        self.assertEqual(text_value, text_prop.default_value)
        self.assertEqual(variant_value, variant_prop.default_value)
    
    def test_concurrent_property_updates(self):
        """Test thread safety with concurrent property updates"""
        integrator = PropertyCanvasIntegrator()
        
        # Create test component
        component_data = {
            "id": "concurrent_test",
            "type": "button",
            "properties": {"text": "Initial"}
        }
        
        integrator.set_selected_component("concurrent_test", component_data)
        
        # Track results
        results = []
        errors = []
        
        def update_property(prop_name, value):
            try:
                success = integrator.set_property_value("concurrent_test", prop_name, value)
                results.append((prop_name, value, success))
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads updating properties
        threads = []
        for i in range(10):
            thread = threading.Thread(
                target=update_property,
                args=("text", f"Concurrent Update {i}")
            )
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify no errors occurred
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), 10)
        
        # All updates should have succeeded
        for prop_name, value, success in results:
            self.assertTrue(success)
    
    def test_property_panel_ui_integration(self):
        """Test property panel UI integration"""
        # Create property panel
        property_panel = PropertyPanel(on_property_change=lambda comp_id, prop, val: None)
        
        # Create test component
        component = Component(
            id="ui_test",
            type="button",
            name="UI Test Button"
        )
        component.properties = {
            "text": "Test",
            "variant": "primary"
        }
        
        # Set component in panel
        property_panel.set_component(component)
        
        # Verify component is set
        current_comp = property_panel.get_current_component()
        self.assertIsNotNone(current_comp)
        self.assertEqual(current_comp.id, "ui_test")
        
        # Test property value operations
        property_panel.set_property_value("text", "Updated Text")
        updated_value = property_panel.get_property_value("text")
        self.assertEqual(updated_value, "Updated Text")
        
        # Test validation
        validation_result = property_panel.validate_all_properties()
        self.assertIsInstance(validation_result, ValidationResult)
        
        # Test property export
        exported = property_panel.export_properties()
        self.assertIsInstance(exported, dict)
        self.assertIn("text", exported)
    
    def test_complete_system_performance(self):
        """Test overall system performance with realistic data"""
        # Create large component with many properties
        large_component_props = []
        for i in range(50):
            prop = PropertyDefinition(
                name=f"prop_{i}",
                label=f"Property {i}",
                category=PropertyCategory.CONTENT,
                type=PropertyType.TEXT,
                default_value=f"value_{i}"
            )
            large_component_props.append(prop)
        
        # Register large component
        self.registry.register_component_properties("large_component", large_component_props)
        
        # Create integrator and component
        integrator = PropertyCanvasIntegrator()
        
        component_data = {
            "id": "large_test",
            "type": "large_component",
            "properties": {f"prop_{i}": f"value_{i}" for i in range(50)}
        }
        
        # Measure performance of key operations
        start_time = time.time()
        
        # Set component
        integrator.set_selected_component("large_test", component_data)
        
        # Validate all properties
        validation_state = integrator.get_validation_state("large_test")
        
        # Update multiple properties
        for i in range(10):
            integrator.set_property_value("large_test", f"prop_{i}", f"updated_value_{i}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        self.assertLess(duration, 5.0, "System performance test failed - operations took too long")


class TestPropertySystemErrorHandling(unittest.TestCase):
    """Test error handling throughout the property system"""
    
    def setUp(self):
        """Set up test environment"""
        PropertyRegistry._instance = None
        self.registry = PropertyRegistry()
    
    def test_invalid_property_definitions(self):
        """Test handling of invalid property definitions"""
        # Invalid property name
        with self.assertRaises(ValueError):
            PropertyDefinition(
                name="123invalid",
                label="Invalid",
                category=PropertyCategory.CONTENT,
                type=PropertyType.TEXT,
                default_value=""
            )
        
        # Missing options for select type
        with self.assertRaises(ValueError):
            PropertyDefinition(
                name="select_prop",
                label="Select",
                category=PropertyCategory.CONTENT,
                type=PropertyType.SELECT,
                default_value="option1"
            )
    
    def test_component_service_errors(self):
        """Test error handling in component service integration"""
        integrator = PropertyCanvasIntegrator()
        
        # Test with non-existent component
        result = integrator.set_property_value("non_existent", "text", "value")
        self.assertFalse(result)
        
        # Test export of non-existent component
        exported = integrator.export_component_properties("non_existent")
        self.assertIsNone(exported)
    
    def test_validation_error_handling(self):
        """Test validation error handling"""
        # Create property with validation
        prop = PropertyDefinition(
            name="validated_prop",
            label="Validated",
            category=PropertyCategory.CONTENT,
            type=PropertyType.NUMBER,
            default_value=50,
            validation=PropertyValidation(min_value=0, max_value=100)
        )
        
        self.registry.register_component_properties("test_validation", [prop])
        
        # Test invalid value
        result = self.registry.validate_property_value("test_validation", "validated_prop", 150)
        self.assertFalse(result.is_valid)
        self.assertTrue(len(result.errors) > 0)
        
        # Test with non-existent property
        result = self.registry.validate_property_value("test_validation", "non_existent", "value")
        self.assertFalse(result.is_valid)


if __name__ == '__main__':
    # Create comprehensive test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestCompletePropertySystemIntegration,
        TestPropertySystemErrorHandling
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"PROPERTY EDITOR SYSTEM INTEGRATION TEST RESULTS")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES ({len(result.failures)}):")
        for test, failure in result.failures:
            print(f"- {test}: {failure.split('AssertionError: ')[-1].split('\\n')[0]}")
    
    if result.errors:
        print(f"\nERRORS ({len(result.errors)}):")
        for test, error in result.errors:
            print(f"- {test}: {error.split('Exception: ')[-1].split('\\n')[0]}")
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)