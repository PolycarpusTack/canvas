"""
Custom Component Creation and Management System
Provides comprehensive functionality for creating, editing, and managing custom components.
"""

from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from copy import deepcopy

from component_types import (
    ComponentDefinition, ComponentCategory, ComponentSlot, ComponentConstraints,
    PropertyDefinition, PropertyType, ValidationResult, CustomComponent
)
from component_registry import ComponentRegistry, get_component_registry
from component_factory import ComponentFactory, get_component_factory
from models.component import Component, ComponentStyle


logger = logging.getLogger(__name__)


class CreationStep(Enum):
    """Steps in custom component creation"""
    SETUP = "setup"
    DESIGN = "design"
    PROPERTIES = "properties"
    CONSTRAINTS = "constraints"
    FINALIZE = "finalize"


class ComponentChangeType(Enum):
    """Types of changes in component versions"""
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


@dataclass
class ComponentVersion:
    """Version information for custom components"""
    version: str
    change_type: ComponentChangeType
    changelog: str
    created_at: datetime
    component_data: Dict[str, Any]
    deprecated: bool = False
    
    def __post_init__(self):
        if not self.version:
            raise ValueError("Version string is required")


@dataclass
class ComponentTemplate:
    """Template for rapid component creation"""
    id: str
    name: str
    description: str
    category: ComponentCategory
    base_component_id: str
    property_overrides: Dict[str, Any] = field(default_factory=dict)
    style_overrides: Dict[str, Any] = field(default_factory=dict)
    children_template: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    preview_image: Optional[str] = None
    usage_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()


@dataclass
class ComponentCreationSession:
    """Session for creating a custom component"""
    session_id: str
    name: str
    description: str
    category: ComponentCategory
    current_step: CreationStep
    base_components: List[Component] = field(default_factory=list)
    properties: List[PropertyDefinition] = field(default_factory=list)
    constraints: ComponentConstraints = field(default_factory=ComponentConstraints)
    slots: List[ComponentSlot] = field(default_factory=list)
    icon: str = "widgets"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    
    def update_step(self, step: CreationStep):
        """Update the current creation step"""
        self.current_step = step
        self.last_modified = datetime.now()


class CustomComponentManager:
    """
    Manages custom component creation, editing, versioning, and sharing.
    Provides a complete workflow for user-created components.
    """
    
    def __init__(
        self,
        registry: Optional[ComponentRegistry] = None,
        factory: Optional[ComponentFactory] = None,
        storage_path: Optional[Path] = None
    ):
        """Initialize the custom component manager"""
        self.registry = registry or get_component_registry()
        self.factory = factory or get_component_factory()
        self.storage_path = storage_path or Path("user_data/custom_components")
        
        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Component management
        self.custom_components: Dict[str, CustomComponent] = {}
        self.component_versions: Dict[str, List[ComponentVersion]] = {}
        self.component_templates: Dict[str, ComponentTemplate] = {}
        self.creation_sessions: Dict[str, ComponentCreationSession] = {}
        
        # Load existing components
        self._load_custom_components()
        self._load_templates()
        
        logger.info("Custom component manager initialized")
    
    # Creation Session Management
    
    def start_component_creation(
        self,
        name: str,
        description: str,
        category: ComponentCategory,
        base_template: Optional[str] = None
    ) -> str:
        """
        Start a new component creation session.
        
        Args:
            name: Component name
            description: Component description
            category: Component category
            base_template: Optional template to start from
            
        Returns:
            Session ID
        """
        session_id = f"session_{uuid4().hex[:8]}"
        
        # Create new session
        session = ComponentCreationSession(
            session_id=session_id,
            name=name,
            description=description,
            category=category,
            current_step=CreationStep.SETUP
        )
        
        # Apply template if provided
        if base_template and base_template in self.component_templates:
            template = self.component_templates[base_template]
            session.properties = deepcopy(template.property_overrides)
            session.tags = template.tags.copy()
            session.icon = "widgets"  # Default icon, can be changed
        
        self.creation_sessions[session_id] = session
        
        logger.info(f"Started component creation session: {session_id} for '{name}'")
        return session_id
    
    def get_creation_session(self, session_id: str) -> Optional[ComponentCreationSession]:
        """Get a creation session by ID"""
        return self.creation_sessions.get(session_id)
    
    def update_creation_session(
        self,
        session_id: str,
        step: Optional[CreationStep] = None,
        **updates
    ) -> ValidationResult:
        """Update a creation session"""
        session = self.creation_sessions.get(session_id)
        if not session:
            return ValidationResult(
                is_valid=False,
                errors=[f"Creation session not found: {session_id}"]
            )
        
        # Update step if provided
        if step:
            session.update_step(step)
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(session, key):
                setattr(session, key, value)
        
        session.last_modified = datetime.now()
        
        logger.debug(f"Updated creation session {session_id}")
        return ValidationResult(is_valid=True)
    
    def add_component_to_creation(
        self,
        session_id: str,
        component: Component,
        position: Optional[int] = None
    ) -> ValidationResult:
        """Add a component to the creation session"""
        session = self.creation_sessions.get(session_id)
        if not session:
            return ValidationResult(
                is_valid=False,
                errors=[f"Creation session not found: {session_id}"]
            )
        
        # Add component to session
        if position is not None and 0 <= position <= len(session.base_components):
            session.base_components.insert(position, component)
        else:
            session.base_components.append(component)
        
        session.last_modified = datetime.now()
        
        logger.debug(f"Added component {component.id} to session {session_id}")
        return ValidationResult(is_valid=True)
    
    def remove_component_from_creation(
        self,
        session_id: str,
        component_id: str
    ) -> ValidationResult:
        """Remove a component from the creation session"""
        session = self.creation_sessions.get(session_id)
        if not session:
            return ValidationResult(
                is_valid=False,
                errors=[f"Creation session not found: {session_id}"]
            )
        
        # Find and remove component
        for i, component in enumerate(session.base_components):
            if component.id == component_id:
                session.base_components.pop(i)
                session.last_modified = datetime.now()
                logger.debug(f"Removed component {component_id} from session {session_id}")
                return ValidationResult(is_valid=True)
        
        return ValidationResult(
            is_valid=False,
            errors=[f"Component {component_id} not found in session"]
        )
    
    def finalize_custom_component(
        self,
        session_id: str,
        icon: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> ValidationResult:
        """
        Finalize the custom component creation.
        
        Args:
            session_id: Creation session ID
            icon: Component icon
            tags: Component tags
            
        Returns:
            ValidationResult with component ID if successful
        """
        session = self.creation_sessions.get(session_id)
        if not session:
            return ValidationResult(
                is_valid=False,
                errors=[f"Creation session not found: {session_id}"]
            )
        
        # Validate session
        if not session.base_components:
            return ValidationResult(
                is_valid=False,
                errors=["Custom component must contain at least one base component"]
            )
        
        # Generate component ID
        component_id = f"custom_{session.name.lower().replace(' ', '_')}_{uuid4().hex[:8]}"
        
        # Create component definition
        definition = ComponentDefinition(
            id=component_id,
            name=session.name,
            category=session.category,
            icon=icon or session.icon,
            description=session.description,
            tags=tags or session.tags,
            properties=session.properties,
            default_values={prop.name: prop.default_value for prop in session.properties},
            slots=session.slots,
            constraints=session.constraints,
            accepts_children=len(session.base_components) > 0,
            draggable=True,
            droppable=True,
            resizable=True,
            version="1.0.0",
            author="User"
        )
        
        # Create template component
        if len(session.base_components) == 1:
            template_component = session.base_components[0]
        else:
            # Create container with multiple components
            template_component = Component(
                id=str(uuid4()),
                type="container",
                name=session.name,
                children=session.base_components
            )
        
        # Create custom component
        custom_component = CustomComponent(
            definition=definition,
            template=template_component,
            created_at=session.created_at,
            updated_at=datetime.now(),
            usage_count=0
        )
        
        # Register the component
        registry_result = self.registry.register_custom_component(custom_component)
        if not registry_result.is_valid:
            return registry_result
        
        # Store custom component
        self.custom_components[component_id] = custom_component
        
        # Create initial version
        version = ComponentVersion(
            version="1.0.0",
            change_type=ComponentChangeType.MAJOR,
            changelog="Initial creation",
            created_at=datetime.now(),
            component_data=custom_component.definition.to_dict()
        )
        self.component_versions[component_id] = [version]
        
        # Save to storage
        self._save_custom_component(custom_component)
        
        # Clean up session
        del self.creation_sessions[session_id]
        
        logger.info(f"Finalized custom component: {component_id}")
        return ValidationResult(
            is_valid=True,
            warnings=[f"Created custom component: {component_id}"]
        )
    
    def cancel_creation_session(self, session_id: str) -> bool:
        """Cancel a creation session"""
        if session_id in self.creation_sessions:
            del self.creation_sessions[session_id]
            logger.info(f"Cancelled creation session: {session_id}")
            return True
        return False
    
    # Component Management
    
    def get_custom_component(self, component_id: str) -> Optional[CustomComponent]:
        """Get a custom component by ID"""
        return self.custom_components.get(component_id)
    
    def get_all_custom_components(self) -> Dict[str, CustomComponent]:
        """Get all custom components"""
        return self.custom_components.copy()
    
    def update_custom_component(
        self,
        component_id: str,
        updates: Dict[str, Any],
        change_type: ComponentChangeType = ComponentChangeType.PATCH,
        changelog: str = "Updated component"
    ) -> ValidationResult:
        """Update a custom component"""
        custom_component = self.custom_components.get(component_id)
        if not custom_component:
            return ValidationResult(
                is_valid=False,
                errors=[f"Custom component not found: {component_id}"]
            )
        
        # Create new version
        current_version = self._parse_version(custom_component.definition.version)
        new_version = self._increment_version(current_version, change_type)
        
        # Apply updates to definition
        definition = custom_component.definition
        for key, value in updates.items():
            if hasattr(definition, key):
                setattr(definition, key, value)
        
        definition.version = new_version
        definition.updated_at = datetime.now()
        custom_component.updated_at = datetime.now()
        
        # Create version record
        version = ComponentVersion(
            version=new_version,
            change_type=change_type,
            changelog=changelog,
            created_at=datetime.now(),
            component_data=definition.to_dict()
        )
        
        if component_id not in self.component_versions:
            self.component_versions[component_id] = []
        self.component_versions[component_id].append(version)
        
        # Save to storage
        self._save_custom_component(custom_component)
        
        logger.info(f"Updated custom component {component_id} to version {new_version}")
        return ValidationResult(is_valid=True)
    
    def delete_custom_component(self, component_id: str) -> ValidationResult:
        """Delete a custom component"""
        if component_id not in self.custom_components:
            return ValidationResult(
                is_valid=False,
                errors=[f"Custom component not found: {component_id}"]
            )
        
        # Remove from registry
        self.registry.unregister(component_id)
        
        # Remove from storage
        component_file = self.storage_path / f"{component_id}.json"
        if component_file.exists():
            component_file.unlink()
        
        # Remove from memory
        del self.custom_components[component_id]
        self.component_versions.pop(component_id, None)
        
        logger.info(f"Deleted custom component: {component_id}")
        return ValidationResult(is_valid=True)
    
    def duplicate_custom_component(
        self,
        component_id: str,
        new_name: str,
        new_description: Optional[str] = None
    ) -> ValidationResult:
        """Duplicate a custom component"""
        original = self.custom_components.get(component_id)
        if not original:
            return ValidationResult(
                is_valid=False,
                errors=[f"Custom component not found: {component_id}"]
            )
        
        # Create new component ID
        new_component_id = f"custom_{new_name.lower().replace(' ', '_')}_{uuid4().hex[:8]}"
        
        # Create duplicated definition
        new_definition = deepcopy(original.definition)
        new_definition.id = new_component_id
        new_definition.name = new_name
        new_definition.description = new_description or f"Copy of {original.definition.description}"
        new_definition.version = "1.0.0"
        new_definition.created_at = datetime.now()
        new_definition.updated_at = datetime.now()
        
        # Create duplicated component
        new_custom = CustomComponent(
            definition=new_definition,
            template=deepcopy(original.template),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            usage_count=0
        )
        
        # Register and store
        registry_result = self.registry.register_custom_component(new_custom)
        if not registry_result.is_valid:
            return registry_result
        
        self.custom_components[new_component_id] = new_custom
        self._save_custom_component(new_custom)
        
        logger.info(f"Duplicated custom component {component_id} as {new_component_id}")
        return ValidationResult(
            is_valid=True,
            warnings=[f"Created duplicate: {new_component_id}"]
        )
    
    # Template Management
    
    def create_component_template(
        self,
        name: str,
        description: str,
        base_component: Component,
        property_overrides: Optional[Dict[str, Any]] = None,
        style_overrides: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """Create a component template for rapid creation"""
        template_id = f"template_{name.lower().replace(' ', '_')}_{uuid4().hex[:6]}"
        
        template = ComponentTemplate(
            id=template_id,
            name=name,
            description=description,
            category=ComponentCategory.CUSTOM,
            base_component_id=base_component.type,
            property_overrides=property_overrides or {},
            style_overrides=style_overrides or {},
            tags=tags or []
        )
        
        self.component_templates[template_id] = template
        self._save_template(template)
        
        logger.info(f"Created component template: {template_id}")
        return template_id
    
    def get_component_templates(self) -> Dict[str, ComponentTemplate]:
        """Get all component templates"""
        return self.component_templates.copy()
    
    def get_template(self, template_id: str) -> Optional[ComponentTemplate]:
        """Get a template by ID"""
        return self.component_templates.get(template_id)
    
    def use_template(self, template_id: str) -> Optional[Component]:
        """Create a component instance from a template"""
        template = self.component_templates.get(template_id)
        if not template:
            return None
        
        # Create component from template
        try:
            component = self.factory.create_component(
                template.base_component_id,
                template.property_overrides
            )
            
            # Apply style overrides
            if template.style_overrides:
                for key, value in template.style_overrides.items():
                    if hasattr(component.style, key):
                        setattr(component.style, key, value)
            
            # Increment usage count
            template.usage_count += 1
            template.updated_at = datetime.now()
            self._save_template(template)
            
            return component
            
        except Exception as e:
            logger.error(f"Failed to create component from template {template_id}: {e}")
            return None
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a component template"""
        if template_id not in self.component_templates:
            return False
        
        # Remove from storage
        template_file = self.storage_path / "templates" / f"{template_id}.json"
        if template_file.exists():
            template_file.unlink()
        
        # Remove from memory
        del self.component_templates[template_id]
        
        logger.info(f"Deleted component template: {template_id}")
        return True
    
    # Import/Export
    
    def export_custom_component(self, component_id: str) -> Optional[Dict[str, Any]]:
        """Export a custom component for sharing"""
        custom_component = self.custom_components.get(component_id)
        if not custom_component:
            return None
        
        export_data = {
            "format_version": "1.0",
            "export_timestamp": datetime.now().isoformat(),
            "component": {
                "definition": custom_component.definition.to_dict(),
                "template": custom_component.template.to_dict() if custom_component.template else None,
                "metadata": {
                    "created_at": custom_component.created_at.isoformat(),
                    "updated_at": custom_component.updated_at.isoformat(),
                    "usage_count": custom_component.usage_count
                }
            },
            "versions": [
                {
                    "version": v.version,
                    "change_type": v.change_type.value,
                    "changelog": v.changelog,
                    "created_at": v.created_at.isoformat(),
                    "deprecated": v.deprecated
                }
                for v in self.component_versions.get(component_id, [])
            ]
        }
        
        logger.info(f"Exported custom component: {component_id}")
        return export_data
    
    def import_custom_component(
        self,
        import_data: Dict[str, Any],
        resolve_conflicts: bool = True
    ) -> ValidationResult:
        """Import a custom component"""
        try:
            # Validate import format
            if import_data.get("format_version") != "1.0":
                return ValidationResult(
                    is_valid=False,
                    errors=["Unsupported import format version"]
                )
            
            component_data = import_data["component"]
            definition_data = component_data["definition"]
            
            # Create definition
            definition = ComponentDefinition.from_dict(definition_data)
            
            # Handle ID conflicts
            original_id = definition.id
            if definition.id in self.custom_components:
                if resolve_conflicts:
                    definition.id = f"{definition.id}_imported_{uuid4().hex[:6]}"
                    definition.name = f"{definition.name} (Imported)"
                else:
                    return ValidationResult(
                        is_valid=False,
                        errors=[f"Component ID conflict: {definition.id}"]
                    )
            
            # Create template component
            template_data = component_data.get("template")
            template_component = None
            if template_data:
                template_component = Component.from_dict(template_data)
            
            # Create custom component
            custom_component = CustomComponent(
                definition=definition,
                template=template_component,
                created_at=datetime.fromisoformat(component_data["metadata"]["created_at"]),
                updated_at=datetime.now(),
                usage_count=0  # Reset usage count for imported components
            )
            
            # Register component
            registry_result = self.registry.register_custom_component(custom_component)
            if not registry_result.is_valid:
                return registry_result
            
            # Store component
            self.custom_components[definition.id] = custom_component
            self._save_custom_component(custom_component)
            
            # Import version history
            if "versions" in import_data:
                versions = []
                for version_data in import_data["versions"]:
                    version = ComponentVersion(
                        version=version_data["version"],
                        change_type=ComponentChangeType(version_data["change_type"]),
                        changelog=version_data["changelog"],
                        created_at=datetime.fromisoformat(version_data["created_at"]),
                        component_data=definition.to_dict(),
                        deprecated=version_data.get("deprecated", False)
                    )
                    versions.append(version)
                
                self.component_versions[definition.id] = versions
            
            result_msg = f"Imported custom component: {definition.id}"
            if definition.id != original_id:
                result_msg += f" (renamed from {original_id})"
            
            logger.info(result_msg)
            return ValidationResult(
                is_valid=True,
                warnings=[result_msg]
            )
            
        except Exception as e:
            logger.error(f"Failed to import custom component: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Import failed: {e}"]
            )
    
    def export_all_custom_components(self) -> Dict[str, Any]:
        """Export all custom components"""
        exported_components = {}
        
        for component_id, custom_component in self.custom_components.items():
            exported_components[component_id] = self.export_custom_component(component_id)
        
        export_data = {
            "format_version": "1.0",
            "export_timestamp": datetime.now().isoformat(),
            "component_count": len(exported_components),
            "components": exported_components
        }
        
        logger.info(f"Exported {len(exported_components)} custom components")
        return export_data
    
    # Version Management
    
    def get_component_versions(self, component_id: str) -> List[ComponentVersion]:
        """Get version history for a component"""
        return self.component_versions.get(component_id, []).copy()
    
    def get_component_version(self, component_id: str, version: str) -> Optional[ComponentVersion]:
        """Get a specific version of a component"""
        versions = self.component_versions.get(component_id, [])
        return next((v for v in versions if v.version == version), None)
    
    def revert_to_version(
        self,
        component_id: str,
        version: str,
        create_backup: bool = True
    ) -> ValidationResult:
        """Revert a component to a previous version"""
        target_version = self.get_component_version(component_id, version)
        if not target_version:
            return ValidationResult(
                is_valid=False,
                errors=[f"Version {version} not found for component {component_id}"]
            )
        
        custom_component = self.custom_components.get(component_id)
        if not custom_component:
            return ValidationResult(
                is_valid=False,
                errors=[f"Custom component not found: {component_id}"]
            )
        
        # Create backup if requested
        if create_backup:
            backup_version = ComponentVersion(
                version=f"{custom_component.definition.version}_backup_{uuid4().hex[:6]}",
                change_type=ComponentChangeType.PATCH,
                changelog="Backup before revert",
                created_at=datetime.now(),
                component_data=custom_component.definition.to_dict()
            )
            
            if component_id not in self.component_versions:
                self.component_versions[component_id] = []
            self.component_versions[component_id].append(backup_version)
        
        # Restore from version data
        try:
            restored_definition = ComponentDefinition.from_dict(target_version.component_data)
            restored_definition.updated_at = datetime.now()
            
            custom_component.definition = restored_definition
            custom_component.updated_at = datetime.now()
            
            # Save changes
            self._save_custom_component(custom_component)
            
            logger.info(f"Reverted component {component_id} to version {version}")
            return ValidationResult(is_valid=True)
            
        except Exception as e:
            logger.error(f"Failed to revert component {component_id} to version {version}: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Revert failed: {e}"]
            )
    
    # Statistics and Analytics
    
    def get_component_statistics(self) -> Dict[str, Any]:
        """Get statistics about custom components"""
        total_components = len(self.custom_components)
        total_templates = len(self.component_templates)
        
        # Category breakdown
        category_counts = {}
        for component in self.custom_components.values():
            category = component.definition.category
            category_counts[category.name] = category_counts.get(category.name, 0) + 1
        
        # Usage statistics
        usage_stats = [comp.usage_count for comp in self.custom_components.values()]
        avg_usage = sum(usage_stats) / len(usage_stats) if usage_stats else 0
        
        # Template usage
        template_usage = [template.usage_count for template in self.component_templates.values()]
        avg_template_usage = sum(template_usage) / len(template_usage) if template_usage else 0
        
        return {
            "total_custom_components": total_components,
            "total_templates": total_templates,
            "category_distribution": category_counts,
            "average_component_usage": avg_usage,
            "average_template_usage": avg_template_usage,
            "most_used_component": max(
                self.custom_components.items(),
                key=lambda x: x[1].usage_count,
                default=(None, None)
            )[0],
            "most_used_template": max(
                self.component_templates.items(),
                key=lambda x: x[1].usage_count,
                default=(None, None)
            )[0]
        }
    
    # Private Methods
    
    def _load_custom_components(self):
        """Load custom components from storage"""
        try:
            components_dir = self.storage_path / "components"
            if not components_dir.exists():
                return
            
            for component_file in components_dir.glob("*.json"):
                try:
                    with open(component_file, 'r') as f:
                        data = json.load(f)
                    
                    # Load component
                    definition = ComponentDefinition.from_dict(data["definition"])
                    template = None
                    if data.get("template"):
                        template = Component.from_dict(data["template"])
                    
                    custom_component = CustomComponent(
                        definition=definition,
                        template=template,
                        created_at=datetime.fromisoformat(data["created_at"]),
                        updated_at=datetime.fromisoformat(data["updated_at"]),
                        usage_count=data.get("usage_count", 0)
                    )
                    
                    self.custom_components[definition.id] = custom_component
                    
                    # Load versions if available
                    if "versions" in data:
                        versions = []
                        for version_data in data["versions"]:
                            version = ComponentVersion(
                                version=version_data["version"],
                                change_type=ComponentChangeType(version_data["change_type"]),
                                changelog=version_data["changelog"],
                                created_at=datetime.fromisoformat(version_data["created_at"]),
                                component_data=version_data["component_data"],
                                deprecated=version_data.get("deprecated", False)
                            )
                            versions.append(version)
                        
                        self.component_versions[definition.id] = versions
                    
                except Exception as e:
                    logger.error(f"Failed to load custom component from {component_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to load custom components: {e}")
    
    def _load_templates(self):
        """Load component templates from storage"""
        try:
            templates_dir = self.storage_path / "templates"
            if not templates_dir.exists():
                return
            
            for template_file in templates_dir.glob("*.json"):
                try:
                    with open(template_file, 'r') as f:
                        data = json.load(f)
                    
                    template = ComponentTemplate(
                        id=data["id"],
                        name=data["name"],
                        description=data["description"],
                        category=ComponentCategory[data["category"]],
                        base_component_id=data["base_component_id"],
                        property_overrides=data.get("property_overrides", {}),
                        style_overrides=data.get("style_overrides", {}),
                        children_template=data.get("children_template", []),
                        tags=data.get("tags", []),
                        preview_image=data.get("preview_image"),
                        usage_count=data.get("usage_count", 0),
                        created_at=datetime.fromisoformat(data["created_at"]),
                        updated_at=datetime.fromisoformat(data["updated_at"])
                    )
                    
                    self.component_templates[template.id] = template
                    
                except Exception as e:
                    logger.error(f"Failed to load template from {template_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to load templates: {e}")
    
    def _save_custom_component(self, custom_component: CustomComponent):
        """Save a custom component to storage"""
        try:
            components_dir = self.storage_path / "components"
            components_dir.mkdir(exist_ok=True)
            
            component_file = components_dir / f"{custom_component.definition.id}.json"
            
            data = {
                "definition": custom_component.definition.to_dict(),
                "template": custom_component.template.to_dict() if custom_component.template else None,
                "created_at": custom_component.created_at.isoformat(),
                "updated_at": custom_component.updated_at.isoformat(),
                "usage_count": custom_component.usage_count
            }
            
            # Include version history
            versions = self.component_versions.get(custom_component.definition.id, [])
            if versions:
                data["versions"] = [
                    {
                        "version": v.version,
                        "change_type": v.change_type.value,
                        "changelog": v.changelog,
                        "created_at": v.created_at.isoformat(),
                        "component_data": v.component_data,
                        "deprecated": v.deprecated
                    }
                    for v in versions
                ]
            
            with open(component_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save custom component {custom_component.definition.id}: {e}")
    
    def _save_template(self, template: ComponentTemplate):
        """Save a component template to storage"""
        try:
            templates_dir = self.storage_path / "templates"
            templates_dir.mkdir(exist_ok=True)
            
            template_file = templates_dir / f"{template.id}.json"
            
            data = {
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "category": template.category.name,
                "base_component_id": template.base_component_id,
                "property_overrides": template.property_overrides,
                "style_overrides": template.style_overrides,
                "children_template": template.children_template,
                "tags": template.tags,
                "preview_image": template.preview_image,
                "usage_count": template.usage_count,
                "created_at": template.created_at.isoformat(),
                "updated_at": template.updated_at.isoformat()
            }
            
            with open(template_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save template {template.id}: {e}")
    
    def _parse_version(self, version_string: str) -> Tuple[int, int, int]:
        """Parse a semantic version string"""
        try:
            parts = version_string.split('.')
            return (int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError):
            return (1, 0, 0)
    
    def _increment_version(
        self,
        current_version: Tuple[int, int, int],
        change_type: ComponentChangeType
    ) -> str:
        """Increment version based on change type"""
        major, minor, patch = current_version
        
        if change_type == ComponentChangeType.MAJOR:
            return f"{major + 1}.0.0"
        elif change_type == ComponentChangeType.MINOR:
            return f"{major}.{minor + 1}.0"
        else:  # PATCH
            return f"{major}.{minor}.{patch + 1}"


# Global manager instance
_custom_component_manager_instance: Optional[CustomComponentManager] = None


def get_custom_component_manager() -> CustomComponentManager:
    """Get the global custom component manager instance"""
    global _custom_component_manager_instance
    if _custom_component_manager_instance is None:
        _custom_component_manager_instance = CustomComponentManager()
    return _custom_component_manager_instance