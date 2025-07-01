"""
Component Tree Management System
Manages hierarchical component structures with validation and operations.
"""

from typing import Dict, List, Optional, Set, Any, Callable, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from uuid import uuid4
from copy import deepcopy

from component_types import ComponentDefinition, ValidationResult, ComponentSlot
from component_registry import ComponentRegistry, get_component_registry
from component_factory import ComponentFactory, get_component_factory
from models.component import Component


logger = logging.getLogger(__name__)


class TreeOperation(Enum):
    """Types of tree operations"""
    ADD = "add"
    REMOVE = "remove"
    MOVE = "move"
    REORDER = "reorder"
    UPDATE = "update"
    REPLACE = "replace"


@dataclass
class TreeNode:
    """Represents a node in the component tree"""
    component: Component
    parent: Optional['TreeNode'] = None
    children: List['TreeNode'] = field(default_factory=list)
    depth: int = 0
    path: str = ""  # Dot-separated path from root
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize node after creation"""
        if not self.path:
            self.path = self.component.id
    
    def is_root(self) -> bool:
        """Check if this is a root node"""
        return self.parent is None
    
    def is_leaf(self) -> bool:
        """Check if this is a leaf node"""
        return len(self.children) == 0
    
    def get_siblings(self) -> List['TreeNode']:
        """Get sibling nodes"""
        if self.parent:
            return [child for child in self.parent.children if child != self]
        return []
    
    def get_ancestors(self) -> List['TreeNode']:
        """Get all ancestor nodes from root to parent"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors
    
    def get_descendants(self) -> List['TreeNode']:
        """Get all descendant nodes"""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants
    
    def find_child_by_id(self, component_id: str) -> Optional['TreeNode']:
        """Find direct child by component ID"""
        for child in self.children:
            if child.component.id == component_id:
                return child
        return None
    
    def find_descendant_by_id(self, component_id: str) -> Optional['TreeNode']:
        """Find any descendant by component ID"""
        for child in self.children:
            if child.component.id == component_id:
                return child
            found = child.find_descendant_by_id(component_id)
            if found:
                return found
        return None


@dataclass
class TreeChange:
    """Represents a change to the component tree"""
    operation: TreeOperation
    node_id: str
    old_parent_id: Optional[str] = None
    new_parent_id: Optional[str] = None
    old_position: Optional[int] = None
    new_position: Optional[int] = None
    component_data: Optional[Dict[str, Any]] = None
    timestamp: float = 0.0
    
    def __post_init__(self):
        """Initialize change record"""
        if self.timestamp == 0.0:
            import time
            self.timestamp = time.time()


class ComponentTreeManager:
    """
    Manages hierarchical component trees with validation and operations.
    Provides tree traversal, manipulation, and constraint enforcement.
    """
    
    def __init__(
        self,
        registry: Optional[ComponentRegistry] = None,
        factory: Optional[ComponentFactory] = None
    ):
        """Initialize the tree manager"""
        self.registry = registry or get_component_registry()
        self.factory = factory or get_component_factory()
        
        # Tree state
        self._trees: Dict[str, TreeNode] = {}  # tree_id -> root_node
        self._node_index: Dict[str, TreeNode] = {}  # component_id -> node
        self._tree_index: Dict[str, str] = {}  # component_id -> tree_id
        
        # Change tracking
        self._change_history: List[TreeChange] = []
        self._max_history = 1000
        
        # Event handlers
        self._change_handlers: List[Callable[[TreeChange], None]] = []
        self._validation_handlers: List[Callable[[TreeNode, TreeOperation], ValidationResult]] = []
        
        # Tree constraints
        self._max_depth = 20
        self._max_children_per_node = 100
        
        logger.info("Component tree manager initialized")
    
    def create_tree(self, root_component: Component, tree_id: Optional[str] = None) -> str:
        """
        Create a new component tree.
        
        Args:
            root_component: Root component of the tree
            tree_id: Optional tree ID, generated if not provided
            
        Returns:
            Tree ID
        """
        if not tree_id:
            tree_id = f"tree_{uuid4().hex[:8]}"
        
        # Create root node
        root_node = TreeNode(
            component=root_component,
            depth=0,
            path=root_component.id
        )
        
        # Build tree from component hierarchy
        self._build_tree_from_component(root_node, root_component)
        
        # Store tree
        self._trees[tree_id] = root_node
        self._index_tree(tree_id, root_node)
        
        # Record change
        change = TreeChange(
            operation=TreeOperation.ADD,
            node_id=root_component.id,
            new_parent_id=None
        )
        self._record_change(change)
        
        logger.info(f"Created component tree: {tree_id} with root {root_component.id}")
        return tree_id
    
    def remove_tree(self, tree_id: str) -> bool:
        """Remove a component tree"""
        if tree_id not in self._trees:
            return False
        
        root_node = self._trees[tree_id]
        
        # Remove from indexes
        self._unindex_tree(tree_id, root_node)
        
        # Remove tree
        del self._trees[tree_id]
        
        # Record change
        change = TreeChange(
            operation=TreeOperation.REMOVE,
            node_id=root_node.component.id
        )
        self._record_change(change)
        
        logger.info(f"Removed component tree: {tree_id}")
        return True
    
    def get_tree(self, tree_id: str) -> Optional[TreeNode]:
        """Get a component tree by ID"""
        return self._trees.get(tree_id)
    
    def get_tree_for_component(self, component_id: str) -> Optional[Tuple[str, TreeNode]]:
        """Get tree ID and root node for a component"""
        tree_id = self._tree_index.get(component_id)
        if tree_id:
            return tree_id, self._trees[tree_id]
        return None
    
    def get_node(self, component_id: str) -> Optional[TreeNode]:
        """Get a tree node by component ID"""
        return self._node_index.get(component_id)
    
    def add_component(
        self,
        parent_id: str,
        component: Component,
        position: Optional[int] = None,
        slot_name: Optional[str] = None
    ) -> ValidationResult:
        """
        Add a component to the tree.
        
        Args:
            parent_id: ID of parent component
            component: Component to add
            position: Insert position (None for append)
            slot_name: Target slot name
            
        Returns:
            ValidationResult indicating success/failure
        """
        # Find parent node
        parent_node = self._node_index.get(parent_id)
        if not parent_node:
            return ValidationResult(
                is_valid=False,
                errors=[f"Parent component not found: {parent_id}"]
            )
        
        # Validate the addition
        validation = self._validate_add_component(parent_node, component, slot_name)
        if not validation.is_valid:
            return validation
        
        # Create new node
        new_node = TreeNode(
            component=component,
            parent=parent_node,
            depth=parent_node.depth + 1,
            path=f"{parent_node.path}.{component.id}"
        )
        
        # Add to parent's children
        if position is not None and 0 <= position <= len(parent_node.children):
            parent_node.children.insert(position, new_node)
        else:
            parent_node.children.append(new_node)
            position = len(parent_node.children) - 1
        
        # Update component's parent relationship
        if component not in parent_node.component.children:
            if position is not None and 0 <= position <= len(parent_node.component.children):
                parent_node.component.children.insert(position, component)
            else:
                parent_node.component.children.append(component)
        
        # Update indexes
        tree_id = self._tree_index.get(parent_id)
        if tree_id:
            self._node_index[component.id] = new_node
            self._tree_index[component.id] = tree_id
        
        # Record change
        change = TreeChange(
            operation=TreeOperation.ADD,
            node_id=component.id,
            new_parent_id=parent_id,
            new_position=position
        )
        self._record_change(change)
        
        logger.debug(f"Added component {component.id} to parent {parent_id}")
        return ValidationResult(is_valid=True)
    
    def remove_component(self, component_id: str) -> ValidationResult:
        """Remove a component from the tree"""
        node = self._node_index.get(component_id)
        if not node:
            return ValidationResult(
                is_valid=False,
                errors=[f"Component not found: {component_id}"]
            )
        
        # Can't remove root nodes
        if node.is_root():
            return ValidationResult(
                is_valid=False,
                errors=["Cannot remove root component"]
            )
        
        parent_node = node.parent
        old_position = parent_node.children.index(node)
        
        # Remove from parent's children
        parent_node.children.remove(node)
        
        # Remove from component hierarchy
        if node.component in parent_node.component.children:
            parent_node.component.children.remove(node.component)
        
        # Remove from indexes
        self._unindex_node(node)
        
        # Record change
        change = TreeChange(
            operation=TreeOperation.REMOVE,
            node_id=component_id,
            old_parent_id=parent_node.component.id,
            old_position=old_position
        )
        self._record_change(change)
        
        logger.debug(f"Removed component {component_id}")
        return ValidationResult(is_valid=True)
    
    def move_component(
        self,
        component_id: str,
        new_parent_id: str,
        new_position: Optional[int] = None
    ) -> ValidationResult:
        """Move a component to a new parent"""
        # Get nodes
        node = self._node_index.get(component_id)
        new_parent = self._node_index.get(new_parent_id)
        
        if not node:
            return ValidationResult(
                is_valid=False,
                errors=[f"Component not found: {component_id}"]
            )
        
        if not new_parent:
            return ValidationResult(
                is_valid=False,
                errors=[f"New parent not found: {new_parent_id}"]
            )
        
        # Can't move to self or descendant
        if new_parent == node or new_parent in node.get_descendants():
            return ValidationResult(
                is_valid=False,
                errors=["Cannot move component to itself or its descendants"]
            )
        
        # Validate the move
        validation = self._validate_add_component(new_parent, node.component)
        if not validation.is_valid:
            return validation
        
        # Record old state
        old_parent = node.parent
        old_position = old_parent.children.index(node) if old_parent else None
        
        # Remove from old parent
        if old_parent:
            old_parent.children.remove(node)
            if node.component in old_parent.component.children:
                old_parent.component.children.remove(node.component)
        
        # Add to new parent
        node.parent = new_parent
        node.depth = new_parent.depth + 1
        
        if new_position is not None and 0 <= new_position <= len(new_parent.children):
            new_parent.children.insert(new_position, node)
            new_parent.component.children.insert(new_position, node.component)
        else:
            new_parent.children.append(node)
            new_parent.component.children.append(node.component)
            new_position = len(new_parent.children) - 1
        
        # Update paths
        self._update_node_paths(node)
        
        # Record change
        change = TreeChange(
            operation=TreeOperation.MOVE,
            node_id=component_id,
            old_parent_id=old_parent.component.id if old_parent else None,
            new_parent_id=new_parent_id,
            old_position=old_position,
            new_position=new_position
        )
        self._record_change(change)
        
        logger.debug(f"Moved component {component_id} to {new_parent_id}")
        return ValidationResult(is_valid=True)
    
    def reorder_children(self, parent_id: str, new_order: List[str]) -> ValidationResult:
        """Reorder children of a component"""
        parent_node = self._node_index.get(parent_id)
        if not parent_node:
            return ValidationResult(
                is_valid=False,
                errors=[f"Parent not found: {parent_id}"]
            )
        
        # Validate new order
        current_ids = {child.component.id for child in parent_node.children}
        new_order_set = set(new_order)
        
        if current_ids != new_order_set:
            return ValidationResult(
                is_valid=False,
                errors=["New order must contain exactly the same children"]
            )
        
        # Reorder children
        old_children = parent_node.children.copy()
        new_children = []
        new_components = []
        
        for child_id in new_order:
            child_node = next(child for child in old_children if child.component.id == child_id)
            new_children.append(child_node)
            new_components.append(child_node.component)
        
        parent_node.children = new_children
        parent_node.component.children = new_components
        
        # Record change
        change = TreeChange(
            operation=TreeOperation.REORDER,
            node_id=parent_id,
            component_data={"new_order": new_order}
        )
        self._record_change(change)
        
        logger.debug(f"Reordered children of {parent_id}")
        return ValidationResult(is_valid=True)
    
    def clone_subtree(self, component_id: str, new_parent_id: Optional[str] = None) -> Optional[TreeNode]:
        """Clone a subtree starting from the given component"""
        source_node = self._node_index.get(component_id)
        if not source_node:
            return None
        
        # Create cloned component
        cloned_component = self.factory.create_from_template(source_node.component)
        
        # Create new node
        cloned_node = TreeNode(
            component=cloned_component,
            depth=source_node.depth,
            metadata=source_node.metadata.copy()
        )
        
        # Clone children recursively
        for child in source_node.children:
            cloned_child = self.clone_subtree(child.component.id)
            if cloned_child:
                cloned_child.parent = cloned_node
                cloned_child.depth = cloned_node.depth + 1
                cloned_node.children.append(cloned_child)
        
        # Add to parent if specified
        if new_parent_id:
            self.add_component(new_parent_id, cloned_component)
        
        return cloned_node
    
    def validate_tree(self, tree_id: str) -> ValidationResult:
        """Validate an entire component tree"""
        root_node = self._trees.get(tree_id)
        if not root_node:
            return ValidationResult(
                is_valid=False,
                errors=[f"Tree not found: {tree_id}"]
            )
        
        return self._validate_subtree(root_node)
    
    def get_tree_stats(self, tree_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics about a tree"""
        root_node = self._trees.get(tree_id)
        if not root_node:
            return None
        
        stats = {
            "total_nodes": 0,
            "max_depth": 0,
            "component_types": {},
            "leaf_nodes": 0,
            "total_children": 0
        }
        
        def collect_stats(node: TreeNode):
            stats["total_nodes"] += 1
            stats["max_depth"] = max(stats["max_depth"], node.depth)
            
            comp_type = node.component.type
            stats["component_types"][comp_type] = stats["component_types"].get(comp_type, 0) + 1
            
            if node.is_leaf():
                stats["leaf_nodes"] += 1
            
            stats["total_children"] += len(node.children)
            
            for child in node.children:
                collect_stats(child)
        
        collect_stats(root_node)
        return stats
    
    def search_tree(
        self,
        tree_id: str,
        predicate: Callable[[TreeNode], bool]
    ) -> List[TreeNode]:
        """Search for nodes in a tree matching a predicate"""
        root_node = self._trees.get(tree_id)
        if not root_node:
            return []
        
        results = []
        
        def search_node(node: TreeNode):
            if predicate(node):
                results.append(node)
            for child in node.children:
                search_node(child)
        
        search_node(root_node)
        return results
    
    def get_change_history(self, limit: Optional[int] = None) -> List[TreeChange]:
        """Get change history"""
        if limit:
            return self._change_history[-limit:]
        return self._change_history.copy()
    
    def add_change_handler(self, handler: Callable[[TreeChange], None]):
        """Add change event handler"""
        self._change_handlers.append(handler)
    
    def add_validation_handler(self, handler: Callable[[TreeNode, TreeOperation], ValidationResult]):
        """Add custom validation handler"""
        self._validation_handlers.append(handler)
    
    # Private methods
    
    def _build_tree_from_component(self, parent_node: TreeNode, component: Component):
        """Recursively build tree from component hierarchy"""
        for child_component in component.children:
            child_node = TreeNode(
                component=child_component,
                parent=parent_node,
                depth=parent_node.depth + 1,
                path=f"{parent_node.path}.{child_component.id}"
            )
            
            parent_node.children.append(child_node)
            self._build_tree_from_component(child_node, child_component)
    
    def _index_tree(self, tree_id: str, root_node: TreeNode):
        """Index all nodes in a tree"""
        def index_node(node: TreeNode):
            self._node_index[node.component.id] = node
            self._tree_index[node.component.id] = tree_id
            for child in node.children:
                index_node(child)
        
        index_node(root_node)
    
    def _unindex_tree(self, tree_id: str, root_node: TreeNode):
        """Remove tree from indexes"""
        def unindex_node(node: TreeNode):
            self._node_index.pop(node.component.id, None)
            self._tree_index.pop(node.component.id, None)
            for child in node.children:
                unindex_node(child)
        
        unindex_node(root_node)
    
    def _unindex_node(self, node: TreeNode):
        """Remove node and descendants from indexes"""
        self._node_index.pop(node.component.id, None)
        self._tree_index.pop(node.component.id, None)
        
        for child in node.children:
            self._unindex_node(child)
    
    def _validate_add_component(
        self,
        parent_node: TreeNode,
        component: Component,
        slot_name: Optional[str] = None
    ) -> ValidationResult:
        """Validate adding a component to a parent"""
        errors = []
        
        # Check depth constraint
        if parent_node.depth + 1 >= self._max_depth:
            errors.append(f"Maximum tree depth ({self._max_depth}) would be exceeded")
        
        # Check children count constraint
        if len(parent_node.children) >= self._max_children_per_node:
            errors.append(f"Maximum children per node ({self._max_children_per_node}) would be exceeded")
        
        # Validate parent-child relationship
        validation = self.registry.validate_parent_child(
            parent_node.component.type,
            component.type
        )
        errors.extend(validation.errors)
        
        # Validate against component definition
        parent_def = self.registry.get(parent_node.component.type)
        if parent_def:
            # Check if parent accepts children
            if not parent_def.accepts_children:
                errors.append(f"Component {parent_def.name} does not accept children")
            
            # Validate slot constraints if specified
            if slot_name and parent_def.slots:
                slot = parent_def.get_slot(slot_name)
                if slot:
                    if not slot.accepts_component(component.type):
                        errors.append(f"Slot '{slot_name}' does not accept component type '{component.type}'")
                    
                    # Count current children in slot (simplified)
                    current_count = len([child for child in parent_node.children])
                    slot_validation = slot.validate_count(current_count + 1)
                    errors.extend(slot_validation.errors)
        
        # Run custom validation handlers
        for handler in self._validation_handlers:
            try:
                result = handler(parent_node, TreeOperation.ADD)
                errors.extend(result.errors)
            except Exception as e:
                logger.error(f"Error in validation handler: {e}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    def _validate_subtree(self, node: TreeNode) -> ValidationResult:
        """Validate a subtree recursively"""
        errors = []
        warnings = []
        
        # Validate component itself
        component_validation = self.factory.validate_component_tree(node.component)
        errors.extend(component_validation.errors)
        warnings.extend(component_validation.warnings)
        
        # Validate children
        for child in node.children:
            # Validate parent-child relationship
            validation = self._validate_add_component(node, child.component)
            errors.extend([f"Child {child.component.id}: {error}" for error in validation.errors])
            
            # Recursively validate child
            child_validation = self._validate_subtree(child)
            errors.extend([f"Child {child.component.id}: {error}" for error in child_validation.errors])
            warnings.extend([f"Child {child.component.id}: {warning}" for warning in child_validation.warnings])
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _update_node_paths(self, node: TreeNode):
        """Update paths for a node and its descendants"""
        if node.parent:
            node.path = f"{node.parent.path}.{node.component.id}"
        else:
            node.path = node.component.id
        
        for child in node.children:
            self._update_node_paths(child)
    
    def _record_change(self, change: TreeChange):
        """Record a tree change"""
        self._change_history.append(change)
        
        # Limit history size
        if len(self._change_history) > self._max_history:
            self._change_history = self._change_history[-self._max_history:]
        
        # Notify handlers
        for handler in self._change_handlers:
            try:
                handler(change)
            except Exception as e:
                logger.error(f"Error in change handler: {e}")


# Global tree manager instance
_tree_manager_instance: Optional[ComponentTreeManager] = None


def get_component_tree_manager() -> ComponentTreeManager:
    """Get the global component tree manager instance"""
    global _tree_manager_instance
    if _tree_manager_instance is None:
        _tree_manager_instance = ComponentTreeManager()
    return _tree_manager_instance