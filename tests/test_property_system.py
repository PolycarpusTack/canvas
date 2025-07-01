"""
Unit Tests for Property Editor System
Comprehensive tests for property definitions, validation, and registry
Following CLAUDE.md guidelines for robust testing
"""

import pytest
import unittest
from unittest.mock import Mock, patch
from typing import Any, Dict, List

# Import modules to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.components.property_definitions import (
    PropertyDefinition, PropertyType, PropertyCategory, PropertyValidation,
    PropertyOption, PropertyDependency, ValidationResult, ResponsiveValue,
    AnimationConfig, COMMON_PROPERTIES
)
from src.components.property_registry import (
    PropertyRegistry, ColorValidator, URLValidator, NumberValidator, SpacingValidator
)
from src.ui.inputs.color_picker import ColorUtil
from src.ui.inputs.spacing_input import SpacingValue


class TestPropertyValidation(unittest.TestCase):
    """Test property validation system"""
    
    def test_basic_validation(self):
        """Test basic validation rules"""
        validation = PropertyValidation(
            min_value=0,
            max_value=100,
            min_length=2,
            max_length=50,
            pattern=r'^[a-zA-Z]+$'
        )
        
        # Test numeric validation
        result = validation.validate(50)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
        
        result = validation.validate(-1)
        self.assertFalse(result.is_valid)
        self.assertIn("minimum", result.errors[0].lower())
        
        result = validation.validate(150)
        self.assertFalse(result.is_valid)
        self.assertIn("maximum", result.errors[0].lower())
        
        # Test string validation
        result = validation.validate("abc")
        self.assertTrue(result.is_valid)
        
        result = validation.validate("a")
        self.assertFalse(result.is_valid)
        self.assertIn("minimum", result.errors[0].lower())
        
        result = validation.validate("a" * 60)
        self.assertFalse(result.is_valid)
        self.assertIn("maximum", result.errors[0].lower())
        
        result = validation.validate("abc123")
        self.assertFalse(result.is_valid)
        self.assertIn("pattern", result.errors[0].lower())
    
    def test_custom_error_messages(self):
        """Test custom error messages"""
        validation = PropertyValidation(
            min_value=0,
            max_value=100,
            error_messages={
                "min_value": "Value too small!",
                "max_value": "Value too large!"
            }
        )
        
        result = validation.validate(-1)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.errors[0], "Value too small!")
        
        result = validation.validate(150)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.errors[0], "Value too large!")


class TestPropertyDefinition(unittest.TestCase):
    """Test property definition system"""
    
    def test_basic_property_definition(self):
        """Test creating basic property definition"""
        prop_def = PropertyDefinition(
            name="test_prop",
            label="Test Property",
            category=PropertyCategory.CONTENT,
            type=PropertyType.TEXT,
            default_value="default"
        )
        
        self.assertEqual(prop_def.name, "test_prop")
        self.assertEqual(prop_def.label, "Test Property")
        self.assertEqual(prop_def.category, PropertyCategory.CONTENT)
        self.assertEqual(prop_def.type, PropertyType.TEXT)
        self.assertEqual(prop_def.default_value, "default")
        self.assertTrue(prop_def.visible)
        self.assertTrue(prop_def.editable)
        self.assertFalse(prop_def.required)
    
    def test_property_definition_validation(self):
        """Test property definition validation"""
        # Test invalid property name
        with self.assertRaises(ValueError):
            PropertyDefinition(
                name="123invalid",  # Starts with number
                label="Test",
                category=PropertyCategory.CONTENT,
                type=PropertyType.TEXT,
                default_value=""
            )
        
        # Test select type without options
        with self.assertRaises(ValueError):
            PropertyDefinition(
                name="test",
                label="Test",
                category=PropertyCategory.CONTENT,
                type=PropertyType.SELECT,
                default_value="option1"
                # Missing options
            )
    
    def test_property_dependencies(self):
        """Test property dependency evaluation"""
        prop_def = PropertyDefinition(
            name="dependent_prop",
            label="Dependent Property",
            category=PropertyCategory.STYLE,
            type=PropertyType.COLOR,
            default_value="#FF0000",
            dependencies=[
                PropertyDependency("parent_prop", "equals", "show", "show"),
                PropertyDependency("other_prop", "greater_than", 0, "enable")
            ]
        )
        
        # Test when dependencies are met
        property_values = {"parent_prop": "show", "other_prop": 5}
        states = prop_def.evaluate_dependencies(property_values)
        self.assertTrue(states["visible"])
        self.assertTrue(states["enabled"])
        
        # Test when dependencies are not met
        property_values = {"parent_prop": "hide", "other_prop": -1}
        states = prop_def.evaluate_dependencies(property_values)
        self.assertFalse(states["visible"])
        self.assertFalse(states["enabled"])
    
    def test_responsive_value(self):
        """Test responsive value system"""
        responsive_val = ResponsiveValue(
            base="16px",
            breakpoints={
                "sm": "14px",
                "md": "18px",
                "lg": "20px"
            }
        )
        
        self.assertEqual(responsive_val.get_value("base"), "16px")
        self.assertEqual(responsive_val.get_value("sm"), "14px")
        self.assertEqual(responsive_val.get_value("md"), "18px")
        self.assertEqual(responsive_val.get_value("xl"), "16px")  # Falls back to base


class TestPropertyRegistry(unittest.TestCase):
    """Test property registry system"""
    
    def setUp(self):
        """Set up test registry"""
        # Create a fresh registry instance for each test
        PropertyRegistry._instance = None
        self.registry = PropertyRegistry()
    
    def test_singleton_pattern(self):
        """Test that registry follows singleton pattern"""
        registry1 = PropertyRegistry()
        registry2 = PropertyRegistry()
        self.assertIs(registry1, registry2)
    
    def test_register_component_properties(self):
        """Test registering component properties"""
        properties = [
            PropertyDefinition(
                name="prop1",
                label="Property 1",
                category=PropertyCategory.CONTENT,
                type=PropertyType.TEXT,
                default_value="value1"
            ),
            PropertyDefinition(
                name="prop2",
                label="Property 2",
                category=PropertyCategory.STYLE,
                type=PropertyType.COLOR,
                default_value="#FF0000"
            )
        ]
        
        self.registry.register_component_properties("test_component", properties)
        
        # Test getting properties
        retrieved_props = self.registry.get_component_properties("test_component")
        self.assertEqual(len(retrieved_props), len(properties) + len(COMMON_PROPERTIES))
        
        # Test getting specific property
        prop1 = self.registry.get_property("test_component", "prop1")
        self.assertIsNotNone(prop1)
        self.assertEqual(prop1.name, "prop1")
    
    def test_duplicate_property_names(self):
        """Test that duplicate property names are rejected"""
        properties = [
            PropertyDefinition(
                name="duplicate",
                label="First",
                category=PropertyCategory.CONTENT,
                type=PropertyType.TEXT,
                default_value="value1"
            ),
            PropertyDefinition(
                name="duplicate",  # Duplicate name
                label="Second",
                category=PropertyCategory.STYLE,
                type=PropertyType.COLOR,
                default_value="#FF0000"
            )
        ]
        
        with self.assertRaises(ValueError):
            self.registry.register_component_properties("test_component", properties)
    
    def test_property_validation(self):
        """Test property value validation"""
        # Register a property with validation
        properties = [
            PropertyDefinition(
                name="validated_prop",
                label="Validated Property",
                category=PropertyCategory.STYLE,
                type=PropertyType.NUMBER,
                default_value=50,
                validation=PropertyValidation(min_value=0, max_value=100)
            )
        ]
        
        self.registry.register_component_properties("test_component", properties)
        
        # Test valid value
        result = self.registry.validate_property_value("test_component", "validated_prop", 75)
        self.assertTrue(result.is_valid)
        
        # Test invalid value
        result = self.registry.validate_property_value("test_component", "validated_prop", 150)
        self.assertFalse(result.is_valid)
        self.assertTrue(len(result.errors) > 0)
    
    def test_search_properties(self):
        """Test property search functionality"""
        properties = [
            PropertyDefinition(
                name="background_color",
                label="Background Color",
                category=PropertyCategory.STYLE,
                type=PropertyType.COLOR,
                default_value="#FFFFFF",
                tags=["color", "background", "style"]
            ),
            PropertyDefinition(
                name="font_size",
                label="Font Size",
                category=PropertyCategory.TYPOGRAPHY,
                type=PropertyType.SIZE,
                default_value="16px",
                tags=["font", "typography", "size"]
            )
        ]
        
        self.registry.register_component_properties("test_component", properties)
        
        # Search by name
        results = self.registry.search_properties("background", "test_component")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "background_color")
        
        # Search by tag
        results = self.registry.search_properties("font", "test_component")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "font_size")
        
        # Search by category
        results = self.registry.search_properties("", "test_component", ["STYLE"])
        color_props = [r for r in results if r.name == "background_color"]
        self.assertTrue(len(color_props) > 0)


class TestColorValidator(unittest.TestCase):
    """Test color validation"""
    
    def setUp(self):
        """Set up color validator"""
        self.validator = ColorValidator()
        self.mock_prop_def = Mock()
    
    def test_valid_hex_colors(self):
        """Test valid hex color formats"""
        valid_colors = ["#FF0000", "#00FF00", "#0000FF", "#FFF", "#000", "#123456"]
        
        for color in valid_colors:
            result = self.validator.validate(color, self.mock_prop_def)
            self.assertTrue(result.is_valid, f"Color {color} should be valid")
    
    def test_valid_rgb_colors(self):
        """Test valid RGB color formats"""
        valid_colors = ["rgb(255, 0, 0)", "rgb(0, 255, 0)", "rgb(0, 0, 255)"]
        
        for color in valid_colors:
            result = self.validator.validate(color, self.mock_prop_def)
            self.assertTrue(result.is_valid, f"Color {color} should be valid")
    
    def test_valid_css_colors(self):
        """Test valid CSS color names"""
        valid_colors = ["red", "green", "blue", "white", "black", "transparent"]
        
        for color in valid_colors:
            result = self.validator.validate(color, self.mock_prop_def)
            self.assertTrue(result.is_valid, f"Color {color} should be valid")
    
    def test_invalid_colors(self):
        """Test invalid color formats"""
        invalid_colors = ["#GGG", "rgb(300, 0, 0)", "invalid", ""]
        
        for color in invalid_colors:
            result = self.validator.validate(color, self.mock_prop_def)
            self.assertFalse(result.is_valid, f"Color {color} should be invalid")


class TestColorUtil(unittest.TestCase):
    """Test color utility functions"""
    
    def test_hex_to_rgb(self):
        """Test hex to RGB conversion"""
        self.assertEqual(ColorUtil.hex_to_rgb("#FF0000"), (255, 0, 0))
        self.assertEqual(ColorUtil.hex_to_rgb("#00FF00"), (0, 255, 0))
        self.assertEqual(ColorUtil.hex_to_rgb("#0000FF"), (0, 0, 255))
        self.assertEqual(ColorUtil.hex_to_rgb("#FFF"), (255, 255, 255))
        self.assertEqual(ColorUtil.hex_to_rgb("#000"), (0, 0, 0))
    
    def test_rgb_to_hex(self):
        """Test RGB to hex conversion"""
        self.assertEqual(ColorUtil.rgb_to_hex(255, 0, 0), "#ff0000")
        self.assertEqual(ColorUtil.rgb_to_hex(0, 255, 0), "#00ff00")
        self.assertEqual(ColorUtil.rgb_to_hex(0, 0, 255), "#0000ff")
        self.assertEqual(ColorUtil.rgb_to_hex(255, 255, 255), "#ffffff")
        self.assertEqual(ColorUtil.rgb_to_hex(0, 0, 0), "#000000")
    
    def test_rgb_hsl_conversion(self):
        """Test RGB to HSL and back conversion"""
        # Test red
        hsl = ColorUtil.rgb_to_hsl(255, 0, 0)
        rgb = ColorUtil.hsl_to_rgb(*hsl)
        self.assertEqual(rgb, (255, 0, 0))
        
        # Test white
        hsl = ColorUtil.rgb_to_hsl(255, 255, 255)
        rgb = ColorUtil.hsl_to_rgb(*hsl)
        # Allow small rounding differences
        self.assertTrue(all(abs(a - b) <= 1 for a, b in zip(rgb, (255, 255, 255))))
    
    def test_parse_color(self):
        """Test color parsing"""
        self.assertEqual(ColorUtil.parse_color("#FF0000"), (255, 0, 0))
        self.assertEqual(ColorUtil.parse_color("rgb(255, 0, 0)"), (255, 0, 0))
        self.assertEqual(ColorUtil.parse_color("red"), (255, 0, 0))
        self.assertEqual(ColorUtil.parse_color("white"), (255, 255, 255))


class TestSpacingValue(unittest.TestCase):
    """Test spacing value parsing and generation"""
    
    def test_single_value(self):
        """Test single value parsing"""
        spacing = SpacingValue("10px")
        self.assertEqual(spacing.top, "10")
        self.assertEqual(spacing.right, "10")
        self.assertEqual(spacing.bottom, "10")
        self.assertEqual(spacing.left, "10")
        self.assertEqual(spacing.unit, "px")
        self.assertTrue(spacing.linked)
    
    def test_two_values(self):
        """Test two value parsing (vertical horizontal)"""
        spacing = SpacingValue("10px 20px")
        self.assertEqual(spacing.top, "10")
        self.assertEqual(spacing.right, "20")
        self.assertEqual(spacing.bottom, "10")
        self.assertEqual(spacing.left, "20")
        self.assertEqual(spacing.unit, "px")
        self.assertFalse(spacing.linked)
    
    def test_four_values(self):
        """Test four value parsing (top right bottom left)"""
        spacing = SpacingValue("10px 20px 30px 40px")
        self.assertEqual(spacing.top, "10")
        self.assertEqual(spacing.right, "20")
        self.assertEqual(spacing.bottom, "30")
        self.assertEqual(spacing.left, "40")
        self.assertEqual(spacing.unit, "px")
        self.assertFalse(spacing.linked)
    
    def test_to_css(self):
        """Test CSS generation"""
        # Single value
        spacing = SpacingValue("10px")
        self.assertEqual(spacing.to_css(), "10px")
        
        # Four different values
        spacing = SpacingValue("10px 20px 30px 40px")
        self.assertEqual(spacing.to_css(), "10px 20px 30px 40px")
        
        # Vertical/horizontal pattern
        spacing = SpacingValue("10px 20px")
        self.assertEqual(spacing.to_css(), "10px 20px")
    
    def test_get_numeric_values(self):
        """Test numeric value extraction"""
        spacing = SpacingValue("10px 20px 30px 40px")
        numeric = spacing.get_numeric_values()
        self.assertEqual(numeric, (10.0, 20.0, 30.0, 40.0))


class TestURLValidator(unittest.TestCase):
    """Test URL validation"""
    
    def setUp(self):
        """Set up URL validator"""
        self.validator = URLValidator()
        self.mock_prop_def = Mock()
    
    def test_valid_urls(self):
        """Test valid URL formats"""
        valid_urls = [
            "https://example.com",
            "http://example.com",
            "https://example.com/path/to/resource",
            "/relative/path",
            "./relative/path",
            "../relative/path"
        ]
        
        for url in valid_urls:
            result = self.validator.validate(url, self.mock_prop_def)
            self.assertTrue(result.is_valid, f"URL {url} should be valid")
    
    def test_invalid_urls(self):
        """Test invalid URL formats"""
        invalid_urls = [
            "not a url",
            "ftp://example.com",  # Not http/https
            "example",  # Missing protocol and invalid format
        ]
        
        for url in invalid_urls:
            result = self.validator.validate(url, self.mock_prop_def)
            self.assertFalse(result.is_valid, f"URL {url} should be invalid")


class TestSpacingValidator(unittest.TestCase):
    """Test spacing validation"""
    
    def setUp(self):
        """Set up spacing validator"""
        self.validator = SpacingValidator()
        self.mock_prop_def = Mock()
    
    def test_valid_spacing(self):
        """Test valid spacing formats"""
        valid_spacing = [
            "10px",
            "10px 20px",
            "10px 20px 30px",
            "10px 20px 30px 40px",
            "1em 2em",
            "50% auto",
            "auto"
        ]
        
        for spacing in valid_spacing:
            result = self.validator.validate(spacing, self.mock_prop_def)
            self.assertTrue(result.is_valid, f"Spacing {spacing} should be valid")
    
    def test_invalid_spacing(self):
        """Test invalid spacing formats"""
        invalid_spacing = [
            "10",  # Missing unit
            "10px 20px 30px 40px 50px",  # Too many values
            "invalid",  # Invalid value
            ""  # Empty string
        ]
        
        for spacing in invalid_spacing:
            result = self.validator.validate(spacing, self.mock_prop_def)
            self.assertFalse(result.is_valid, f"Spacing {spacing} should be invalid")


class TestPropertySystemIntegration(unittest.TestCase):
    """Integration tests for the complete property system"""
    
    def setUp(self):
        """Set up integration test environment"""
        PropertyRegistry._instance = None
        self.registry = PropertyRegistry()
    
    def test_complete_button_component(self):
        """Test complete button component registration and validation"""
        # Define button properties
        button_properties = [
            PropertyDefinition(
                name="text",
                label="Button Text",
                category=PropertyCategory.CONTENT,
                type=PropertyType.TEXT,
                default_value="Button",
                required=True,
                validation=PropertyValidation(
                    min_length=1,
                    max_length=50,
                    error_messages={
                        "min_length": "Button text cannot be empty",
                        "max_length": "Button text too long"
                    }
                )
            ),
            PropertyDefinition(
                name="variant",
                label="Variant",
                category=PropertyCategory.STYLE,
                type=PropertyType.SELECT,
                default_value="primary",
                options=[
                    PropertyOption("primary", "Primary"),
                    PropertyOption("secondary", "Secondary"),
                    PropertyOption("danger", "Danger")
                ]
            ),
            PropertyDefinition(
                name="background_color",
                label="Background Color",
                category=PropertyCategory.STYLE,
                type=PropertyType.COLOR,
                default_value="#5E6AD2",
                dependencies=[
                    PropertyDependency("variant", "equals", "primary", "show")
                ]
            )
        ]
        
        # Register component
        self.registry.register_component_properties("button", button_properties)
        
        # Test getting all properties
        all_props = self.registry.get_component_properties("button")
        self.assertTrue(len(all_props) >= len(button_properties))
        
        # Test property validation
        property_values = {
            "text": "Click me",
            "variant": "primary",
            "background_color": "#FF0000"
        }
        
        result = self.registry.validate_all_properties("button", property_values)
        self.assertTrue(result.is_valid)
        
        # Test invalid property values
        invalid_values = {
            "text": "",  # Too short
            "variant": "invalid",  # Not in options
            "background_color": "not a color"  # Invalid color
        }
        
        result = self.registry.validate_all_properties("button", invalid_values)
        self.assertFalse(result.is_valid)
        self.assertTrue(len(result.errors) > 0)
    
    def test_property_dependencies(self):
        """Test property dependency system"""
        properties = [
            PropertyDefinition(
                name="show_advanced",
                label="Show Advanced",
                category=PropertyCategory.CONTENT,
                type=PropertyType.BOOLEAN,
                default_value=False
            ),
            PropertyDefinition(
                name="advanced_setting",
                label="Advanced Setting",
                category=PropertyCategory.ADVANCED,
                type=PropertyType.TEXT,
                default_value="",
                dependencies=[
                    PropertyDependency("show_advanced", "equals", True, "show")
                ]
            )
        ]
        
        self.registry.register_component_properties("test_deps", properties)
        
        # Test dependency evaluation
        advanced_prop = self.registry.get_property("test_deps", "advanced_setting")
        
        # When show_advanced is False
        values = {"show_advanced": False}
        states = advanced_prop.evaluate_dependencies(values)
        self.assertFalse(states["visible"])
        
        # When show_advanced is True
        values = {"show_advanced": True}
        states = advanced_prop.evaluate_dependencies(values)
        self.assertTrue(states["visible"])


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestPropertyValidation,
        TestPropertyDefinition,
        TestPropertyRegistry,
        TestColorValidator,
        TestColorUtil,
        TestSpacingValue,
        TestURLValidator,
        TestSpacingValidator,
        TestPropertySystemIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with error code if tests failed
    exit(0 if result.wasSuccessful() else 1)