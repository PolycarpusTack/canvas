"""
Component Search Engine
Provides advanced search and filtering capabilities for the component library.
"""

from typing import Dict, List, Optional, Set, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import re
import logging
from datetime import datetime, timedelta

from component_types import ComponentDefinition, ComponentCategory, ComponentList
from component_registry import ComponentRegistry, get_component_registry


logger = logging.getLogger(__name__)


class SearchScope(Enum):
    """Search scope options"""
    ALL = "all"
    BUILTIN = "builtin"
    CUSTOM = "custom"
    FAVORITES = "favorites"
    RECENT = "recent"


class SortOrder(Enum):
    """Sort order options"""
    RELEVANCE = "relevance"
    NAME_ASC = "name_asc"
    NAME_DESC = "name_desc"
    CATEGORY = "category"
    RECENT = "recent"
    USAGE = "usage"


@dataclass
class SearchFilters:
    """Search filter criteria"""
    categories: Optional[List[ComponentCategory]] = None
    tags: Optional[List[str]] = None
    accepts_children: Optional[bool] = None
    draggable: Optional[bool] = None
    resizable: Optional[bool] = None
    scope: SearchScope = SearchScope.ALL
    author: Optional[str] = None
    min_version: Optional[str] = None
    max_version: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


@dataclass
class SearchResult:
    """Search result with relevance scoring"""
    component: ComponentDefinition
    relevance_score: float
    matched_fields: List[str] = field(default_factory=list)
    matched_terms: List[str] = field(default_factory=list)


@dataclass
class SearchResults:
    """Complete search results"""
    results: List[SearchResult]
    total_count: int
    query: str
    filters: Optional[SearchFilters]
    execution_time_ms: float
    suggestions: List[str] = field(default_factory=list)


class ComponentSearchEngine:
    """
    Advanced search engine for component discovery.
    Provides text search, filtering, sorting, and relevance scoring.
    """
    
    def __init__(self, registry: Optional[ComponentRegistry] = None):
        """Initialize the search engine"""
        self.registry = registry or get_component_registry()
        self._search_index: Dict[str, Set[str]] = {}
        self._component_scores: Dict[str, float] = {}
        self._search_analytics: Dict[str, int] = {}
        
        # Build initial search index
        self._build_search_index()
        
        # Listen for registry changes
        self.registry.add_listener(self._on_registry_change)
    
    def search(
        self,
        query: str = "",
        filters: Optional[SearchFilters] = None,
        sort_order: SortOrder = SortOrder.RELEVANCE,
        limit: Optional[int] = None
    ) -> SearchResults:
        """
        Perform component search with optional filtering and sorting.
        
        Args:
            query: Search query string
            filters: Optional search filters
            sort_order: How to sort results
            limit: Maximum number of results
            
        Returns:
            SearchResults object with components and metadata
        """
        start_time = datetime.now()
        
        # Track search analytics
        self._track_search(query)
        
        # Get initial component set based on scope
        components = self._get_component_scope(filters.scope if filters else SearchScope.ALL)
        
        # Apply text search if query provided
        if query.strip():
            components = self._apply_text_search(components, query)
        
        # Apply filters
        if filters:
            components = self._apply_filters(components, filters)
        
        # Calculate relevance scores
        search_results = []
        for component in components:
            result = SearchResult(
                component=component,
                relevance_score=self._calculate_relevance(component, query),
                matched_fields=self._get_matched_fields(component, query),
                matched_terms=self._get_matched_terms(component, query)
            )
            search_results.append(result)
        
        # Sort results
        search_results = self._sort_results(search_results, sort_order)
        
        # Apply limit
        if limit:
            search_results = search_results[:limit]
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Generate suggestions
        suggestions = self._generate_suggestions(query, len(search_results))
        
        return SearchResults(
            results=search_results,
            total_count=len(search_results),
            query=query,
            filters=filters,
            execution_time_ms=execution_time,
            suggestions=suggestions
        )
    
    def search_by_category(self, category: ComponentCategory) -> List[ComponentDefinition]:
        """Get all components in a specific category"""
        return self.registry.get_by_category(category)
    
    def search_by_tag(self, tag: str) -> List[ComponentDefinition]:
        """Get all components with a specific tag"""
        return self.registry.get_by_tag(tag)
    
    def get_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """Get search suggestions based on partial query"""
        suggestions = []
        query_lower = partial_query.lower()
        
        # Search in component names
        for component in self.registry.get_all().values():
            if query_lower in component.name.lower():
                suggestions.append(component.name)
        
        # Search in tags
        for tag in self.registry.get_tags():
            if query_lower in tag.lower():
                suggestions.append(tag)
        
        # Remove duplicates and sort by relevance
        suggestions = list(set(suggestions))
        suggestions.sort(key=lambda s: (
            s.lower().startswith(query_lower),  # Starts with query first
            len(s),  # Shorter suggestions first
            s.lower()  # Alphabetical
        ), reverse=True)
        
        return suggestions[:limit]
    
    def get_popular_searches(self, limit: int = 10) -> List[str]:
        """Get most popular search queries"""
        sorted_searches = sorted(
            self._search_analytics.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [query for query, count in sorted_searches[:limit]]
    
    def get_related_components(
        self,
        component_id: str,
        limit: int = 5
    ) -> List[ComponentDefinition]:
        """Get components related to the given component"""
        component = self.registry.get(component_id)
        if not component:
            return []
        
        related = []
        all_components = self.registry.get_all()
        
        for other_id, other_component in all_components.items():
            if other_id == component_id:
                continue
            
            # Calculate similarity
            similarity = self._calculate_similarity(component, other_component)
            if similarity > 0.3:  # Threshold for relatedness
                related.append((other_component, similarity))
        
        # Sort by similarity and return top results
        related.sort(key=lambda x: x[1], reverse=True)
        return [comp for comp, _ in related[:limit]]
    
    def clear_search_analytics(self):
        """Clear search analytics data"""
        self._search_analytics.clear()
    
    # Private methods
    
    def _build_search_index(self):
        """Build search index for fast text searching"""
        self._search_index.clear()
        
        for component_id, component in self.registry.get_all().items():
            # Index component name
            name_tokens = self._tokenize(component.name)
            for token in name_tokens:
                self._add_to_index(token, component_id)
            
            # Index description
            if component.description:
                desc_tokens = self._tokenize(component.description)
                for token in desc_tokens:
                    self._add_to_index(token, component_id)
            
            # Index tags
            for tag in component.tags:
                tag_tokens = self._tokenize(tag)
                for token in tag_tokens:
                    self._add_to_index(token, component_id)
            
            # Index category
            category_tokens = self._tokenize(component.category.display_name)
            for token in category_tokens:
                self._add_to_index(token, component_id)
            
            # Index property names
            for prop in component.properties:
                prop_tokens = self._tokenize(prop.name)
                for token in prop_tokens:
                    self._add_to_index(token, component_id)
        
        logger.debug(f"Built search index with {len(self._search_index)} terms")
    
    def _add_to_index(self, token: str, component_id: str):
        """Add a token to the search index"""
        if token not in self._search_index:
            self._search_index[token] = set()
        self._search_index[token].add(component_id)
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for search indexing"""
        if not text:
            return []
        
        # Convert to lowercase and split on non-alphanumeric characters
        tokens = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out very short tokens
        return [token for token in tokens if len(token) >= 2]
    
    def _get_component_scope(self, scope: SearchScope) -> ComponentList:
        """Get components based on search scope"""
        if scope == SearchScope.ALL:
            return list(self.registry.get_all().values())
        elif scope == SearchScope.BUILTIN:
            return [comp for comp in self.registry.get_all().values() 
                   if not comp.id.startswith('custom_')]
        elif scope == SearchScope.CUSTOM:
            return [comp for comp in self.registry.get_all().values() 
                   if comp.id.startswith('custom_')]
        elif scope == SearchScope.FAVORITES:
            return self.registry.get_favorites()
        elif scope == SearchScope.RECENT:
            return self.registry.get_recently_used()
        else:
            return list(self.registry.get_all().values())
    
    def _apply_text_search(self, components: ComponentList, query: str) -> ComponentList:
        """Apply text search to filter components"""
        if not query.strip():
            return components
        
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return components
        
        # Find components that match any query token
        matching_ids = set()
        for token in query_tokens:
            if token in self._search_index:
                matching_ids.update(self._search_index[token])
        
        # Filter components to only include matches
        return [comp for comp in components if comp.id in matching_ids]
    
    def _apply_filters(self, components: ComponentList, filters: SearchFilters) -> ComponentList:
        """Apply search filters to component list"""
        filtered = components
        
        # Category filter
        if filters.categories:
            filtered = [comp for comp in filtered if comp.category in filters.categories]
        
        # Tag filter
        if filters.tags:
            filtered = [comp for comp in filtered 
                       if any(tag in comp.tags for tag in filters.tags)]
        
        # Behavior filters
        if filters.accepts_children is not None:
            filtered = [comp for comp in filtered 
                       if comp.accepts_children == filters.accepts_children]
        
        if filters.draggable is not None:
            filtered = [comp for comp in filtered 
                       if comp.draggable == filters.draggable]
        
        if filters.resizable is not None:
            filtered = [comp for comp in filtered 
                       if comp.resizable == filters.resizable]
        
        # Author filter
        if filters.author:
            filtered = [comp for comp in filtered 
                       if comp.author.lower() == filters.author.lower()]
        
        # Date filters
        if filters.created_after:
            filtered = [comp for comp in filtered 
                       if comp.created_at and comp.created_at >= filters.created_after]
        
        if filters.created_before:
            filtered = [comp for comp in filtered 
                       if comp.created_at and comp.created_at <= filters.created_before]
        
        return filtered
    
    def _calculate_relevance(self, component: ComponentDefinition, query: str) -> float:
        """Calculate relevance score for a component based on query"""
        if not query.strip():
            return 1.0
        
        score = 0.0
        query_lower = query.lower()
        query_tokens = self._tokenize(query)
        
        # Exact name match (highest score)
        if component.name.lower() == query_lower:
            score += 10.0
        
        # Name starts with query
        elif component.name.lower().startswith(query_lower):
            score += 8.0
        
        # Name contains query
        elif query_lower in component.name.lower():
            score += 5.0
        
        # Tag matches
        for tag in component.tags:
            if tag.lower() == query_lower:
                score += 6.0
            elif query_lower in tag.lower():
                score += 3.0
        
        # Description matches
        if component.description and query_lower in component.description.lower():
            score += 2.0
        
        # Category matches
        if query_lower in component.category.display_name.lower():
            score += 1.5
        
        # Token-based scoring
        for token in query_tokens:
            # Check each searchable field
            fields = [
                component.name.lower(),
                component.description.lower() if component.description else "",
                component.category.display_name.lower(),
                " ".join(component.tags).lower()
            ]
            
            for field in fields:
                if token in field:
                    score += 0.5
        
        # Boost popular components
        usage_score = self._component_scores.get(component.id, 0.0)
        score += usage_score * 0.1
        
        return score
    
    def _get_matched_fields(self, component: ComponentDefinition, query: str) -> List[str]:
        """Get list of fields that matched the query"""
        matched = []
        if not query.strip():
            return matched
        
        query_lower = query.lower()
        
        if query_lower in component.name.lower():
            matched.append("name")
        
        if component.description and query_lower in component.description.lower():
            matched.append("description")
        
        if any(query_lower in tag.lower() for tag in component.tags):
            matched.append("tags")
        
        if query_lower in component.category.display_name.lower():
            matched.append("category")
        
        return matched
    
    def _get_matched_terms(self, component: ComponentDefinition, query: str) -> List[str]:
        """Get list of query terms that matched"""
        matched = []
        query_tokens = self._tokenize(query)
        
        searchable_text = " ".join([
            component.name,
            component.description or "",
            component.category.display_name,
            " ".join(component.tags)
        ]).lower()
        
        for token in query_tokens:
            if token in searchable_text:
                matched.append(token)
        
        return matched
    
    def _sort_results(self, results: List[SearchResult], sort_order: SortOrder) -> List[SearchResult]:
        """Sort search results based on specified order"""
        if sort_order == SortOrder.RELEVANCE:
            return sorted(results, key=lambda r: r.relevance_score, reverse=True)
        
        elif sort_order == SortOrder.NAME_ASC:
            return sorted(results, key=lambda r: r.component.name.lower())
        
        elif sort_order == SortOrder.NAME_DESC:
            return sorted(results, key=lambda r: r.component.name.lower(), reverse=True)
        
        elif sort_order == SortOrder.CATEGORY:
            return sorted(results, key=lambda r: (r.component.category.order, r.component.name.lower()))
        
        elif sort_order == SortOrder.RECENT:
            # Sort by creation/update time (newest first)
            return sorted(results, key=lambda r: r.component.updated_at or r.component.created_at or datetime.min, reverse=True)
        
        elif sort_order == SortOrder.USAGE:
            return sorted(results, key=lambda r: self._component_scores.get(r.component.id, 0.0), reverse=True)
        
        else:
            return results
    
    def _calculate_similarity(self, comp1: ComponentDefinition, comp2: ComponentDefinition) -> float:
        """Calculate similarity between two components"""
        similarity = 0.0
        
        # Same category
        if comp1.category == comp2.category:
            similarity += 0.3
        
        # Shared tags
        common_tags = set(comp1.tags) & set(comp2.tags)
        if common_tags:
            similarity += len(common_tags) * 0.1
        
        # Similar names
        name1_tokens = set(self._tokenize(comp1.name))
        name2_tokens = set(self._tokenize(comp2.name))
        common_name_tokens = name1_tokens & name2_tokens
        if common_name_tokens:
            similarity += len(common_name_tokens) * 0.05
        
        # Similar behavior
        if comp1.accepts_children == comp2.accepts_children:
            similarity += 0.1
        
        if comp1.draggable == comp2.draggable:
            similarity += 0.05
        
        if comp1.resizable == comp2.resizable:
            similarity += 0.05
        
        return min(similarity, 1.0)
    
    def _generate_suggestions(self, query: str, result_count: int) -> List[str]:
        """Generate search suggestions when results are limited"""
        suggestions = []
        
        if result_count == 0 and query.strip():
            # No results - suggest similar terms
            suggestions.extend(self.get_suggestions(query, 3))
            
            # Suggest broader categories
            for category in ComponentCategory:
                if query.lower() in category.display_name.lower():
                    suggestions.append(category.display_name)
        
        elif result_count < 5:
            # Few results - suggest related terms
            query_tokens = self._tokenize(query)
            for token in query_tokens:
                # Find related tags
                for tag in self.registry.get_tags():
                    if token in tag and tag not in suggestions:
                        suggestions.append(tag)
                        if len(suggestions) >= 3:
                            break
        
        return suggestions[:5]
    
    def _track_search(self, query: str):
        """Track search query for analytics"""
        if query.strip():
            query_lower = query.lower().strip()
            if query_lower not in self._search_analytics:
                self._search_analytics[query_lower] = 0
            self._search_analytics[query_lower] += 1
    
    def _on_registry_change(self, event: str, component_id: str):
        """Handle registry change events"""
        if event in ["registered", "unregistered"]:
            # Rebuild search index when components are added/removed
            self._build_search_index()


# Global search engine instance
_search_engine_instance: Optional[ComponentSearchEngine] = None


def get_component_search_engine() -> ComponentSearchEngine:
    """Get the global component search engine instance"""
    global _search_engine_instance
    if _search_engine_instance is None:
        _search_engine_instance = ComponentSearchEngine()
    return _search_engine_instance