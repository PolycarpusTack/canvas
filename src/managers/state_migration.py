"""
State migration system for handling state structure changes over time.
Provides versioned migrations to ensure compatibility with older saved states.
"""

import logging
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class MigrationInfo:
    """Information about a state migration"""
    version: str
    description: str
    migration_func: Callable[[Dict[str, Any]], Dict[str, Any]]
    created_at: str
    breaking_change: bool = False


class StateMigrationError(Exception):
    """Raised when state migration fails"""
    pass


class StateMigrationManager:
    """
    Manages state migrations to handle schema changes over time.
    Ensures backward compatibility when state structure evolves.
    """
    
    def __init__(self):
        self.current_version = "1.0.0"
        self.migrations: Dict[str, MigrationInfo] = {}
        self.migration_order: List[str] = []
        
        # Register built-in migrations
        self._register_builtin_migrations()
        
        logger.info(f"StateMigrationManager initialized (current version: {self.current_version})")
    
    def register_migration(
        self,
        from_version: str,
        to_version: str,
        description: str,
        migration_func: Callable[[Dict[str, Any]], Dict[str, Any]],
        breaking_change: bool = False
    ):
        """Register a migration from one version to another"""
        migration_key = f"{from_version}->{to_version}"
        
        migration_info = MigrationInfo(
            version=to_version,
            description=description,
            migration_func=migration_func,
            created_at=datetime.now().isoformat(),
            breaking_change=breaking_change
        )
        
        self.migrations[migration_key] = migration_info
        
        # Maintain order for sequential migrations
        if migration_key not in self.migration_order:
            self.migration_order.append(migration_key)
        
        logger.info(f"Registered migration {migration_key}: {description}")
    
    def migrate_state(self, state_data: Dict[str, Any], from_version: Optional[str] = None) -> Dict[str, Any]:
        """
        Migrate state data from its current version to the latest version.
        Automatically detects version and applies necessary migrations.
        """
        # Detect current version
        current_version = from_version or self._detect_version(state_data)
        
        if current_version == self.current_version:
            logger.debug("State is already at current version")
            return state_data
        
        logger.info(f"Migrating state from {current_version} to {self.current_version}")
        
        # Find migration path
        migration_path = self._find_migration_path(current_version, self.current_version)
        
        if not migration_path:
            raise StateMigrationError(
                f"No migration path found from {current_version} to {self.current_version}"
            )
        
        # Apply migrations sequentially
        migrated_data = state_data.copy()
        
        for migration_key in migration_path:
            if migration_key not in self.migrations:
                raise StateMigrationError(f"Migration {migration_key} not found")
            
            migration = self.migrations[migration_key]
            
            try:
                logger.debug(f"Applying migration {migration_key}: {migration.description}")
                migrated_data = migration.migration_func(migrated_data)
                
                # Update version in migrated data
                migrated_data['_schema_version'] = migration.version
                
            except Exception as e:
                raise StateMigrationError(
                    f"Migration {migration_key} failed: {e}"
                ) from e
        
        logger.info(f"State migration completed successfully")
        return migrated_data
    
    def _detect_version(self, state_data: Dict[str, Any]) -> str:
        """Detect the version of the state data"""
        # Check for explicit version
        if '_schema_version' in state_data:
            return state_data['_schema_version']
        
        # Check for version in metadata
        if 'metadata' in state_data and 'version' in state_data['metadata']:
            return state_data['metadata']['version']
        
        # Heuristic detection based on structure
        return self._detect_version_by_structure(state_data)
    
    def _detect_version_by_structure(self, state_data: Dict[str, Any]) -> str:
        """Detect version based on state structure (heuristic)"""
        # Check for known structural markers of different versions
        
        # Version 0.1.0 detection
        if 'components' in state_data and isinstance(state_data['components'], list):
            return "0.1.0"
        
        # Version 0.2.0 detection
        if 'components' in state_data and 'component_map' in state_data['components']:
            return "0.2.0"
        
        # Default to oldest version if unsure
        return "0.1.0"
    
    def _find_migration_path(self, from_version: str, to_version: str) -> List[str]:
        """Find the sequence of migrations needed to go from one version to another"""
        # Simple implementation - assumes linear migration path
        # In a more complex system, this could use graph algorithms
        
        path = []
        current = from_version
        
        # Build version ordering
        version_order = ["0.1.0", "0.2.0", "1.0.0"]
        
        try:
            start_idx = version_order.index(current)
            end_idx = version_order.index(to_version)
        except ValueError:
            return []  # Unknown version
        
        if start_idx >= end_idx:
            return []  # No forward migration needed
        
        # Find migrations in order
        for i in range(start_idx, end_idx):
            from_ver = version_order[i]
            to_ver = version_order[i + 1]
            migration_key = f"{from_ver}->{to_ver}"
            
            if migration_key in self.migrations:
                path.append(migration_key)
            else:
                logger.warning(f"Missing migration: {migration_key}")
                return []  # Incomplete migration path
        
        return path
    
    def _register_builtin_migrations(self):
        """Register built-in migrations for known schema changes"""
        
        # Migration from 0.1.0 to 0.2.0: Components list to component tree
        self.register_migration(
            from_version="0.1.0",
            to_version="0.2.0",
            description="Convert components list to component tree structure",
            migration_func=self._migrate_0_1_0_to_0_2_0,
            breaking_change=True
        )
        
        # Migration from 0.2.0 to 1.0.0: Add spatial indexing and enhanced state
        self.register_migration(
            from_version="0.2.0",
            to_version="1.0.0",
            description="Add spatial indexing support and enhanced state management",
            migration_func=self._migrate_0_2_0_to_1_0_0,
            breaking_change=False
        )
    
    def _migrate_0_1_0_to_0_2_0(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate from 0.1.0 to 0.2.0: Components list to tree structure"""
        migrated = state_data.copy()
        
        # Convert old components list to new component tree structure
        if 'components' in state_data and isinstance(state_data['components'], list):
            old_components = state_data['components']
            
            # Build new component tree structure
            component_map = {}
            root_components = []
            parent_map = {}
            
            for i, component in enumerate(old_components):
                component_id = component.get('id', f"component_{i}")
                component_map[component_id] = component
                
                # Assume all components are root in old structure
                root_components.append(component_id)
            
            migrated['components'] = {
                'root_components': root_components,
                'component_map': component_map,
                'parent_map': parent_map,
                'dirty_components': []
            }
        
        # Add selection state if missing
        if 'selection' not in migrated:
            migrated['selection'] = {
                'selected_ids': [],
                'last_selected': None,
                'selection_box': None
            }
        
        # Add canvas state if missing
        if 'canvas' not in migrated:
            migrated['canvas'] = {
                'zoom': 1.0,
                'pan_x': 0.0,
                'pan_y': 0.0,
                'show_grid': False,
                'show_guides': True,
                'grid_size': 20,
                'snap_to_grid': False
            }
        
        logger.info("Migrated state from 0.1.0 to 0.2.0")
        return migrated
    
    def _migrate_0_2_0_to_1_0_0(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate from 0.2.0 to 1.0.0: Add enhanced features"""
        migrated = state_data.copy()
        
        # Add clipboard state if missing
        if 'clipboard' not in migrated:
            migrated['clipboard'] = {
                'copied_components': [],
                'cut_components': []
            }
        
        # Add history state if missing
        if 'history' not in migrated:
            migrated['history'] = {
                'can_undo': False,
                'can_redo': False,
                'current_index': -1,
                'total_entries': 0
            }
        
        # Add preferences if missing
        if 'preferences' not in migrated:
            migrated['preferences'] = {
                'auto_save': True,
                'auto_save_interval': 300,
                'show_tooltips': True,
                'enable_animations': True,
                'default_device': 'desktop',
                'language': 'en'
            }
        
        # Add runtime state if missing
        if 'is_loading' not in migrated:
            migrated['is_loading'] = False
        if 'has_unsaved_changes' not in migrated:
            migrated['has_unsaved_changes'] = False
        if 'last_saved' not in migrated:
            migrated['last_saved'] = None
        
        # Ensure component tree has all required fields
        if 'components' in migrated:
            components = migrated['components']
            if 'dirty_components' not in components:
                components['dirty_components'] = []
        
        logger.info("Migrated state from 0.2.0 to 1.0.0")
        return migrated
    
    def validate_migrated_state(self, state_data: Dict[str, Any]) -> bool:
        """Validate that migrated state has correct structure"""
        try:
            # Check for required top-level keys
            required_keys = ['window', 'panels', 'theme', 'components', 'selection', 'canvas']
            for key in required_keys:
                if key not in state_data:
                    logger.error(f"Missing required key in migrated state: {key}")
                    return False
            
            # Check component tree structure
            components = state_data['components']
            required_component_keys = ['root_components', 'component_map', 'parent_map']
            for key in required_component_keys:
                if key not in components:
                    logger.error(f"Missing required component key: {key}")
                    return False
            
            # Validate component references
            for component_id in components['root_components']:
                if component_id not in components['component_map']:
                    logger.error(f"Root component {component_id} not found in component_map")
                    return False
            
            for child_id, parent_id in components['parent_map'].items():
                if parent_id not in components['component_map']:
                    logger.error(f"Parent {parent_id} not found in component_map")
                    return False
            
            logger.info("Migrated state validation passed")
            return True
            
        except Exception as e:
            logger.error(f"State validation failed: {e}")
            return False
    
    def get_migration_info(self) -> Dict[str, Any]:
        """Get information about available migrations"""
        return {
            'current_version': self.current_version,
            'available_migrations': {
                key: {
                    'version': migration.version,
                    'description': migration.description,
                    'created_at': migration.created_at,
                    'breaking_change': migration.breaking_change
                }
                for key, migration in self.migrations.items()
            },
            'migration_order': self.migration_order
        }
    
    def create_backup(self, state_data: Dict[str, Any], version: str) -> Dict[str, Any]:
        """Create a backup of state before migration"""
        return {
            'version': version,
            'timestamp': datetime.now().isoformat(),
            'state': state_data.copy(),
            'migration_manager_version': self.current_version
        }