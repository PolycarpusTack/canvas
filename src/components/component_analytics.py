"""
Component Analytics System
Tracks usage, performance, and provides insights for component library optimization.
"""

from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4
import statistics
from collections import defaultdict, Counter

from component_types import ComponentDefinition, ValidationResult
from component_registry import ComponentRegistry, get_component_registry


logger = logging.getLogger(__name__)


class UsageAction(Enum):
    """Types of usage actions that can be tracked"""
    SEARCH = "search"
    VIEW = "view"
    DRAG = "drag"
    DROP = "drop"
    CREATE = "create"
    EDIT = "edit"
    DELETE = "delete"
    COPY = "copy"
    PASTE = "paste"
    FAVORITE = "favorite"
    UNFAVORITE = "unfavorite"
    PREVIEW = "preview"
    EXPORT = "export"
    IMPORT = "import"


class PerformanceMetric(Enum):
    """Types of performance metrics"""
    SEARCH_TIME = "search_time"
    RENDER_TIME = "render_time"
    CREATION_TIME = "creation_time"
    PREVIEW_GENERATION_TIME = "preview_generation_time"
    LOAD_TIME = "load_time"
    MEMORY_USAGE = "memory_usage"
    ERROR_RATE = "error_rate"


class TrendPeriod(Enum):
    """Time periods for trend analysis"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


@dataclass
class UsageEvent:
    """Single usage event record"""
    event_id: str
    user_id: Optional[str]
    session_id: str
    component_id: str
    action: UsageAction
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.event_id:
            self.event_id = str(uuid4())


@dataclass
class PerformanceEvent:
    """Performance measurement event"""
    metric: PerformanceMetric
    value: float
    component_id: Optional[str]
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None


@dataclass
class ComponentUsageStats:
    """Usage statistics for a component"""
    component_id: str
    component_name: str
    total_usage: int
    search_count: int
    view_count: int
    drag_count: int
    drop_count: int
    creation_count: int
    favorite_count: int
    preview_count: int
    last_used: Optional[datetime]
    first_used: Optional[datetime]
    avg_session_usage: float
    usage_trend: List[Tuple[datetime, int]]


@dataclass
class UserBehaviorStats:
    """User behavior analysis"""
    total_sessions: int
    avg_session_duration: timedelta
    most_used_components: List[Tuple[str, int]]
    favorite_categories: List[str]
    search_patterns: List[str]
    workflow_patterns: List[List[UsageAction]]
    error_rate: float
    component_discovery_rate: float


@dataclass
class PerformanceStats:
    """Performance statistics"""
    metric: PerformanceMetric
    avg_value: float
    min_value: float
    max_value: float
    median_value: float
    p95_value: float
    sample_count: int
    trend_data: List[Tuple[datetime, float]]


@dataclass
class AnalyticsReport:
    """Comprehensive analytics report"""
    report_id: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    
    # Component statistics
    most_popular_components: List[ComponentUsageStats]
    trending_components: List[ComponentUsageStats]
    underused_components: List[ComponentUsageStats]
    
    # Performance metrics
    performance_summary: Dict[PerformanceMetric, PerformanceStats]
    
    # User behavior
    user_behavior: UserBehaviorStats
    
    # Library health
    library_health_score: float
    recommendations: List[str]
    
    # Category insights
    category_usage: Dict[str, int]
    category_trends: Dict[str, List[Tuple[datetime, int]]]


class ComponentAnalytics:
    """
    Comprehensive analytics system for component library usage and performance.
    Tracks user behavior, component popularity, performance metrics, and provides insights.
    """
    
    def __init__(
        self,
        registry: Optional[ComponentRegistry] = None,
        storage_path: Optional[Path] = None
    ):
        """Initialize the analytics system"""
        self.registry = registry or get_component_registry()
        self.storage_path = storage_path or Path("user_data/analytics")
        
        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Event storage
        self.usage_events: List[UsageEvent] = []
        self.performance_events: List[PerformanceEvent] = []
        
        # Cached statistics
        self.component_stats_cache: Dict[str, ComponentUsageStats] = {}
        self.performance_stats_cache: Dict[PerformanceMetric, PerformanceStats] = {}
        self.user_behavior_cache: Optional[UserBehaviorStats] = None
        
        # Configuration
        self.max_events_in_memory = 10000
        self.cache_duration = timedelta(hours=1)
        self.auto_save_interval = timedelta(minutes=5)
        
        # Session tracking
        self.current_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_start_times: Dict[str, datetime] = {}
        
        # Load existing data
        self._load_analytics_data()
        
        # Start auto-save timer (in a real implementation)
        self._last_save = datetime.now()
        
        logger.info("Component analytics system initialized")
    
    # Usage Tracking
    
    def track_usage(
        self,
        component_id: str,
        action: UsageAction,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Track a usage event.
        
        Args:
            component_id: ID of the component
            action: Type of action performed
            user_id: Optional user identifier
            session_id: Session identifier
            context: Additional context data
            metadata: Event metadata
        """
        if not session_id:
            session_id = f"session_{uuid4().hex[:8]}"
        
        # Create usage event
        event = UsageEvent(
            event_id=str(uuid4()),
            user_id=user_id,
            session_id=session_id,
            component_id=component_id,
            action=action,
            timestamp=datetime.now(),
            context=context or {},
            metadata=metadata or {}
        )
        
        # Add to events
        self.usage_events.append(event)
        
        # Update session tracking
        self._update_session_tracking(session_id, action, component_id)
        
        # Invalidate relevant caches
        self._invalidate_component_cache(component_id)
        
        # Auto-save periodically
        if datetime.now() - self._last_save > self.auto_save_interval:
            self._save_analytics_data()
        
        # Manage memory usage
        self._manage_memory_usage()
        
        logger.debug(f"Tracked usage: {component_id} - {action.value}")
    
    def track_performance(
        self,
        metric: PerformanceMetric,
        value: float,
        component_id: Optional[str] = None,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Track a performance metric.
        
        Args:
            metric: Type of performance metric
            value: Measured value
            component_id: Optional component ID
            session_id: Optional session ID
            context: Additional context
        """
        event = PerformanceEvent(
            metric=metric,
            value=value,
            component_id=component_id,
            timestamp=datetime.now(),
            context=context or {},
            session_id=session_id
        )
        
        self.performance_events.append(event)
        
        # Invalidate performance cache
        self.performance_stats_cache.pop(metric, None)
        
        logger.debug(f"Tracked performance: {metric.value} = {value}")
    
    def start_session(self, session_id: str, user_id: Optional[str] = None) -> str:
        """Start a new analytics session"""
        self.current_sessions[session_id] = {
            "user_id": user_id,
            "start_time": datetime.now(),
            "components_used": set(),
            "actions_performed": [],
            "search_queries": [],
            "errors_encountered": 0
        }
        
        self.session_start_times[session_id] = datetime.now()
        
        logger.info(f"Started analytics session: {session_id}")
        return session_id
    
    def end_session(self, session_id: str):
        """End an analytics session"""
        if session_id in self.current_sessions:
            session_data = self.current_sessions[session_id]
            start_time = self.session_start_times.get(session_id)
            
            if start_time:
                duration = datetime.now() - start_time
                session_data["duration"] = duration
            
            # Track session completion
            self.track_usage(
                component_id="session",
                action=UsageAction.VIEW,  # Using VIEW as session end
                session_id=session_id,
                context={"session_summary": session_data}
            )
            
            # Clean up
            del self.current_sessions[session_id]
            self.session_start_times.pop(session_id, None)
            
            logger.info(f"Ended analytics session: {session_id}")
    
    # Statistics and Insights
    
    def get_component_usage_stats(
        self,
        component_id: str,
        days: int = 30
    ) -> Optional[ComponentUsageStats]:
        """Get usage statistics for a specific component"""
        # Check cache first
        cache_key = f"{component_id}_{days}"
        if cache_key in self.component_stats_cache:
            cached_stats = self.component_stats_cache[cache_key]
            if (datetime.now() - cached_stats.last_used or datetime.min) < self.cache_duration:
                return cached_stats
        
        # Calculate statistics
        cutoff_date = datetime.now() - timedelta(days=days)
        component_events = [
            event for event in self.usage_events
            if event.component_id == component_id and event.timestamp >= cutoff_date
        ]
        
        if not component_events:
            return None
        
        # Get component definition
        definition = self.registry.get(component_id)
        component_name = definition.name if definition else component_id
        
        # Calculate stats
        total_usage = len(component_events)
        search_count = len([e for e in component_events if e.action == UsageAction.SEARCH])
        view_count = len([e for e in component_events if e.action == UsageAction.VIEW])
        drag_count = len([e for e in component_events if e.action == UsageAction.DRAG])
        drop_count = len([e for e in component_events if e.action == UsageAction.DROP])
        creation_count = len([e for e in component_events if e.action == UsageAction.CREATE])
        favorite_count = len([e for e in component_events if e.action == UsageAction.FAVORITE])
        preview_count = len([e for e in component_events if e.action == UsageAction.PREVIEW])
        
        # Time range analysis
        timestamps = [event.timestamp for event in component_events]
        first_used = min(timestamps) if timestamps else None
        last_used = max(timestamps) if timestamps else None
        
        # Session analysis
        session_usage = defaultdict(int)
        for event in component_events:
            session_usage[event.session_id] += 1
        
        avg_session_usage = statistics.mean(session_usage.values()) if session_usage else 0
        
        # Usage trend
        usage_trend = self._calculate_usage_trend(component_events, days)
        
        stats = ComponentUsageStats(
            component_id=component_id,
            component_name=component_name,
            total_usage=total_usage,
            search_count=search_count,
            view_count=view_count,
            drag_count=drag_count,
            drop_count=drop_count,
            creation_count=creation_count,
            favorite_count=favorite_count,
            preview_count=preview_count,
            last_used=last_used,
            first_used=first_used,
            avg_session_usage=avg_session_usage,
            usage_trend=usage_trend
        )
        
        # Cache the result
        self.component_stats_cache[cache_key] = stats
        
        return stats
    
    def get_popular_components(
        self,
        limit: int = 10,
        days: int = 30,
        action_filter: Optional[List[UsageAction]] = None
    ) -> List[ComponentUsageStats]:
        """Get most popular components by usage"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filter events
        filtered_events = [
            event for event in self.usage_events
            if event.timestamp >= cutoff_date
        ]
        
        if action_filter:
            filtered_events = [
                event for event in filtered_events
                if event.action in action_filter
            ]
        
        # Count usage by component
        component_usage = Counter(event.component_id for event in filtered_events)
        
        # Get stats for top components
        popular_components = []
        for component_id, _ in component_usage.most_common(limit):
            stats = self.get_component_usage_stats(component_id, days)
            if stats:
                popular_components.append(stats)
        
        return popular_components
    
    def get_trending_components(
        self,
        limit: int = 10,
        days: int = 7
    ) -> List[ComponentUsageStats]:
        """Get components with increasing usage trends"""
        # Compare recent usage to previous period
        recent_start = datetime.now() - timedelta(days=days)
        previous_start = datetime.now() - timedelta(days=days * 2)
        
        # Get usage for both periods
        recent_events = [
            event for event in self.usage_events
            if recent_start <= event.timestamp
        ]
        
        previous_events = [
            event for event in self.usage_events
            if previous_start <= event.timestamp < recent_start
        ]
        
        recent_usage = Counter(event.component_id for event in recent_events)
        previous_usage = Counter(event.component_id for event in previous_events)
        
        # Calculate growth rates
        trending_components = []
        for component_id in recent_usage:
            recent_count = recent_usage[component_id]
            previous_count = previous_usage.get(component_id, 0)
            
            # Calculate growth rate (avoid division by zero)
            if previous_count == 0:
                growth_rate = float('inf') if recent_count > 0 else 0
            else:
                growth_rate = (recent_count - previous_count) / previous_count
            
            # Only include components with significant growth
            if growth_rate > 0.1 and recent_count >= 3:
                stats = self.get_component_usage_stats(component_id, days)
                if stats:
                    trending_components.append((stats, growth_rate))
        
        # Sort by growth rate and return top components
        trending_components.sort(key=lambda x: x[1], reverse=True)
        return [stats for stats, _ in trending_components[:limit]]
    
    def get_underused_components(
        self,
        limit: int = 10,
        days: int = 30,
        threshold: int = 5
    ) -> List[ComponentUsageStats]:
        """Get components with low usage that might need attention"""
        all_components = self.registry.get_all()
        underused = []
        
        for component_id in all_components:
            stats = self.get_component_usage_stats(component_id, days)
            if stats and stats.total_usage < threshold:
                underused.append(stats)
        
        # Sort by usage (ascending)
        underused.sort(key=lambda x: x.total_usage)
        return underused[:limit]
    
    def get_performance_stats(
        self,
        metric: PerformanceMetric,
        days: int = 30
    ) -> Optional[PerformanceStats]:
        """Get performance statistics for a metric"""
        # Check cache
        if metric in self.performance_stats_cache:
            return self.performance_stats_cache[metric]
        
        cutoff_date = datetime.now() - timedelta(days=days)
        metric_events = [
            event for event in self.performance_events
            if event.metric == metric and event.timestamp >= cutoff_date
        ]
        
        if not metric_events:
            return None
        
        values = [event.value for event in metric_events]
        
        stats = PerformanceStats(
            metric=metric,
            avg_value=statistics.mean(values),
            min_value=min(values),
            max_value=max(values),
            median_value=statistics.median(values),
            p95_value=self._calculate_percentile(values, 95),
            sample_count=len(values),
            trend_data=self._calculate_performance_trend(metric_events, days)
        )
        
        # Cache the result
        self.performance_stats_cache[metric] = stats
        
        return stats
    
    def get_user_behavior_stats(self, days: int = 30) -> UserBehaviorStats:
        """Get user behavior analysis"""
        # Check cache
        if self.user_behavior_cache:
            return self.user_behavior_cache
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_events = [
            event for event in self.usage_events
            if event.timestamp >= cutoff_date
        ]
        
        # Session analysis
        sessions = defaultdict(list)
        for event in recent_events:
            sessions[event.session_id].append(event)
        
        # Calculate session durations
        session_durations = []
        for session_events in sessions.values():
            if len(session_events) > 1:
                start_time = min(event.timestamp for event in session_events)
                end_time = max(event.timestamp for event in session_events)
                session_durations.append(end_time - start_time)
        
        avg_session_duration = statistics.mean(session_durations) if session_durations else timedelta(0)
        
        # Most used components
        component_usage = Counter(event.component_id for event in recent_events)
        most_used_components = component_usage.most_common(10)
        
        # Favorite categories
        category_usage = defaultdict(int)
        for component_id, count in component_usage.items():
            definition = self.registry.get(component_id)
            if definition:
                category_usage[definition.category.name] += count
        
        favorite_categories = [cat for cat, _ in 
                             sorted(category_usage.items(), key=lambda x: x[1], reverse=True)]
        
        # Search patterns
        search_events = [event for event in recent_events if event.action == UsageAction.SEARCH]
        search_patterns = [
            event.context.get('query', '') for event in search_events
            if event.context.get('query')
        ]
        
        # Workflow patterns
        workflow_patterns = []
        for session_events in sessions.values():
            if len(session_events) >= 3:
                workflow = [event.action for event in sorted(session_events, key=lambda x: x.timestamp)]
                workflow_patterns.append(workflow)
        
        # Error rate calculation
        total_events = len(recent_events)
        error_events = len([event for event in recent_events 
                          if event.context.get('error') or event.action == UsageAction.DELETE])
        error_rate = error_events / total_events if total_events > 0 else 0
        
        # Component discovery rate
        unique_components_per_session = [
            len(set(event.component_id for event in session_events))
            for session_events in sessions.values()
        ]
        component_discovery_rate = statistics.mean(unique_components_per_session) if unique_components_per_session else 0
        
        behavior_stats = UserBehaviorStats(
            total_sessions=len(sessions),
            avg_session_duration=avg_session_duration,
            most_used_components=most_used_components,
            favorite_categories=favorite_categories,
            search_patterns=search_patterns[:20],  # Limit to top 20
            workflow_patterns=workflow_patterns[:10],  # Limit to top 10
            error_rate=error_rate,
            component_discovery_rate=component_discovery_rate
        )
        
        # Cache the result
        self.user_behavior_cache = behavior_stats
        
        return behavior_stats
    
    def generate_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> AnalyticsReport:
        """Generate a comprehensive analytics report"""
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        days = (end_date - start_date).days
        
        # Get component statistics
        popular_components = self.get_popular_components(limit=20, days=days)
        trending_components = self.get_trending_components(limit=10, days=min(days, 7))
        underused_components = self.get_underused_components(limit=10, days=days)
        
        # Get performance metrics
        performance_summary = {}
        for metric in PerformanceMetric:
            stats = self.get_performance_stats(metric, days)
            if stats:
                performance_summary[metric] = stats
        
        # Get user behavior
        user_behavior = self.get_user_behavior_stats(days)
        
        # Calculate library health score
        health_score = self._calculate_library_health_score(
            popular_components, performance_summary, user_behavior
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            popular_components, trending_components, underused_components,
            performance_summary, user_behavior
        )
        
        # Category usage analysis
        category_usage = self._calculate_category_usage(days)
        category_trends = self._calculate_category_trends(days)
        
        report = AnalyticsReport(
            report_id=str(uuid4()),
            generated_at=datetime.now(),
            period_start=start_date,
            period_end=end_date,
            most_popular_components=popular_components,
            trending_components=trending_components,
            underused_components=underused_components,
            performance_summary=performance_summary,
            user_behavior=user_behavior,
            library_health_score=health_score,
            recommendations=recommendations,
            category_usage=category_usage,
            category_trends=category_trends
        )
        
        logger.info(f"Generated analytics report: {report.report_id}")
        return report
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get real-time dashboard data"""
        popular_components = self.get_popular_components(limit=5, days=7)
        trending_components = self.get_trending_components(limit=5, days=7)
        
        # Recent activity
        recent_events = [
            event for event in self.usage_events[-100:]  # Last 100 events
        ]
        
        # Performance overview
        search_time_stats = self.get_performance_stats(PerformanceMetric.SEARCH_TIME, days=7)
        render_time_stats = self.get_performance_stats(PerformanceMetric.RENDER_TIME, days=7)
        
        return {
            "popular_components": [
                {"id": comp.component_id, "name": comp.component_name, "usage": comp.total_usage}
                for comp in popular_components
            ],
            "trending_components": [
                {"id": comp.component_id, "name": comp.component_name, "usage": comp.total_usage}
                for comp in trending_components
            ],
            "recent_activity": [
                {
                    "component_id": event.component_id,
                    "action": event.action.value,
                    "timestamp": event.timestamp.isoformat()
                }
                for event in recent_events
            ],
            "performance": {
                "search_time": search_time_stats.avg_value if search_time_stats else None,
                "render_time": render_time_stats.avg_value if render_time_stats else None
            },
            "total_components": len(self.registry.get_all()),
            "total_events": len(self.usage_events),
            "active_sessions": len(self.current_sessions)
        }
    
    # Private Methods
    
    def _update_session_tracking(self, session_id: str, action: UsageAction, component_id: str):
        """Update session tracking data"""
        if session_id not in self.current_sessions:
            self.start_session(session_id)
        
        session = self.current_sessions[session_id]
        session["components_used"].add(component_id)
        session["actions_performed"].append(action)
        
        if action == UsageAction.SEARCH:
            # In a real implementation, we'd capture the search query
            pass
    
    def _invalidate_component_cache(self, component_id: str):
        """Invalidate cached statistics for a component"""
        keys_to_remove = [key for key in self.component_stats_cache.keys() 
                         if key.startswith(component_id)]
        for key in keys_to_remove:
            del self.component_stats_cache[key]
    
    def _manage_memory_usage(self):
        """Manage memory usage by archiving old events"""
        if len(self.usage_events) > self.max_events_in_memory:
            # Archive oldest events
            cutoff = self.max_events_in_memory // 2
            archived_events = self.usage_events[:-cutoff]
            self.usage_events = self.usage_events[-cutoff:]
            
            # Save archived events
            self._archive_events(archived_events)
            
            logger.info(f"Archived {len(archived_events)} events to manage memory")
    
    def _calculate_usage_trend(
        self,
        events: List[UsageEvent],
        days: int
    ) -> List[Tuple[datetime, int]]:
        """Calculate usage trend over time"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Group events by day
        daily_usage = defaultdict(int)
        current_date = start_date.date()
        
        while current_date <= end_date.date():
            daily_usage[current_date] = 0
            current_date += timedelta(days=1)
        
        for event in events:
            event_date = event.timestamp.date()
            if start_date.date() <= event_date <= end_date.date():
                daily_usage[event_date] += 1
        
        # Convert to list of tuples
        trend_data = [
            (datetime.combine(date, datetime.min.time()), count)
            for date, count in sorted(daily_usage.items())
        ]
        
        return trend_data
    
    def _calculate_performance_trend(
        self,
        events: List[PerformanceEvent],
        days: int
    ) -> List[Tuple[datetime, float]]:
        """Calculate performance trend over time"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Group events by day and calculate averages
        daily_values = defaultdict(list)
        
        for event in events:
            if start_date <= event.timestamp <= end_date:
                event_date = event.timestamp.date()
                daily_values[event_date].append(event.value)
        
        # Calculate daily averages
        trend_data = []
        current_date = start_date.date()
        
        while current_date <= end_date.date():
            if current_date in daily_values:
                avg_value = statistics.mean(daily_values[current_date])
            else:
                avg_value = 0.0
            
            trend_data.append((
                datetime.combine(current_date, datetime.min.time()),
                avg_value
            ))
            current_date += timedelta(days=1)
        
        return trend_data
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = (percentile / 100) * (len(sorted_values) - 1)
        
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower_index = int(index)
            upper_index = lower_index + 1
            weight = index - lower_index
            
            if upper_index >= len(sorted_values):
                return sorted_values[-1]
            
            return (sorted_values[lower_index] * (1 - weight) + 
                   sorted_values[upper_index] * weight)
    
    def _calculate_library_health_score(
        self,
        popular_components: List[ComponentUsageStats],
        performance_summary: Dict[PerformanceMetric, PerformanceStats],
        user_behavior: UserBehaviorStats
    ) -> float:
        """Calculate overall library health score (0-100)"""
        score = 100.0
        
        # Performance impact (30% of score)
        performance_score = 100.0
        if PerformanceMetric.SEARCH_TIME in performance_summary:
            search_stats = performance_summary[PerformanceMetric.SEARCH_TIME]
            if search_stats.avg_value > 500:  # 500ms threshold
                performance_score -= 20
        
        if PerformanceMetric.ERROR_RATE in performance_summary:
            error_stats = performance_summary[PerformanceMetric.ERROR_RATE]
            performance_score -= error_stats.avg_value * 50  # Scale error rate
        
        # Usage distribution (30% of score)
        usage_score = 100.0
        if popular_components:
            total_usage = sum(comp.total_usage for comp in popular_components)
            if total_usage > 0:
                # Check if usage is concentrated on few components
                top_3_usage = sum(comp.total_usage for comp in popular_components[:3])
                concentration_ratio = top_3_usage / total_usage
                if concentration_ratio > 0.8:  # Too concentrated
                    usage_score -= 30
        
        # User engagement (40% of score)
        engagement_score = 100.0
        if user_behavior.error_rate > 0.1:  # 10% error rate threshold
            engagement_score -= user_behavior.error_rate * 200
        
        if user_behavior.component_discovery_rate < 2:  # Users discovering < 2 components per session
            engagement_score -= 20
        
        # Calculate weighted average
        final_score = (
            performance_score * 0.3 +
            usage_score * 0.3 +
            engagement_score * 0.4
        )
        
        return max(0, min(100, final_score))
    
    def _generate_recommendations(
        self,
        popular_components: List[ComponentUsageStats],
        trending_components: List[ComponentUsageStats],
        underused_components: List[ComponentUsageStats],
        performance_summary: Dict[PerformanceMetric, PerformanceStats],
        user_behavior: UserBehaviorStats
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Performance recommendations
        if PerformanceMetric.SEARCH_TIME in performance_summary:
            search_stats = performance_summary[PerformanceMetric.SEARCH_TIME]
            if search_stats.avg_value > 200:
                recommendations.append(
                    f"Search performance is slow (avg: {search_stats.avg_value:.0f}ms). "
                    "Consider optimizing search indexing or implementing caching."
                )
        
        # Usage pattern recommendations
        if len(underused_components) > 5:
            recommendations.append(
                f"Found {len(underused_components)} underused components. "
                "Consider improving documentation, adding examples, or removing deprecated components."
            )
        
        if user_behavior.error_rate > 0.05:
            recommendations.append(
                f"High error rate detected ({user_behavior.error_rate:.1%}). "
                "Review error logs and improve component validation."
            )
        
        # Discovery recommendations
        if user_behavior.component_discovery_rate < 3:
            recommendations.append(
                "Low component discovery rate. Consider improving search functionality "
                "or adding component recommendations."
            )
        
        # Trending component recommendations
        if trending_components:
            trending_names = [comp.component_name for comp in trending_components[:3]]
            recommendations.append(
                f"Components gaining popularity: {', '.join(trending_names)}. "
                "Consider creating variations or related components."
            )
        
        # Category balance recommendations
        if len(user_behavior.favorite_categories) <= 2:
            recommendations.append(
                "Users are focused on few categories. Consider promoting components "
                "from underutilized categories or improving cross-category workflows."
            )
        
        return recommendations
    
    def _calculate_category_usage(self, days: int) -> Dict[str, int]:
        """Calculate usage by category"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_events = [
            event for event in self.usage_events
            if event.timestamp >= cutoff_date
        ]
        
        category_usage = defaultdict(int)
        for event in recent_events:
            definition = self.registry.get(event.component_id)
            if definition:
                category_usage[definition.category.name] += 1
        
        return dict(category_usage)
    
    def _calculate_category_trends(self, days: int) -> Dict[str, List[Tuple[datetime, int]]]:
        """Calculate usage trends by category"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get events in date range
        events_in_range = [
            event for event in self.usage_events
            if start_date <= event.timestamp <= end_date
        ]
        
        # Group by category and date
        category_daily_usage = defaultdict(lambda: defaultdict(int))
        
        for event in events_in_range:
            definition = self.registry.get(event.component_id)
            if definition:
                event_date = event.timestamp.date()
                category_daily_usage[definition.category.name][event_date] += 1
        
        # Convert to trend format
        category_trends = {}
        for category, daily_usage in category_daily_usage.items():
            trend_data = []
            current_date = start_date.date()
            
            while current_date <= end_date.date():
                count = daily_usage.get(current_date, 0)
                trend_data.append((
                    datetime.combine(current_date, datetime.min.time()),
                    count
                ))
                current_date += timedelta(days=1)
            
            category_trends[category] = trend_data
        
        return category_trends
    
    def _load_analytics_data(self):
        """Load analytics data from storage"""
        try:
            # Load usage events
            events_file = self.storage_path / "usage_events.json"
            if events_file.exists():
                with open(events_file, 'r') as f:
                    events_data = json.load(f)
                
                for event_data in events_data:
                    event = UsageEvent(
                        event_id=event_data["event_id"],
                        user_id=event_data.get("user_id"),
                        session_id=event_data["session_id"],
                        component_id=event_data["component_id"],
                        action=UsageAction(event_data["action"]),
                        timestamp=datetime.fromisoformat(event_data["timestamp"]),
                        context=event_data.get("context", {}),
                        metadata=event_data.get("metadata", {})
                    )
                    self.usage_events.append(event)
            
            # Load performance events
            perf_file = self.storage_path / "performance_events.json"
            if perf_file.exists():
                with open(perf_file, 'r') as f:
                    perf_data = json.load(f)
                
                for perf_event_data in perf_data:
                    event = PerformanceEvent(
                        metric=PerformanceMetric(perf_event_data["metric"]),
                        value=perf_event_data["value"],
                        component_id=perf_event_data.get("component_id"),
                        timestamp=datetime.fromisoformat(perf_event_data["timestamp"]),
                        context=perf_event_data.get("context", {}),
                        session_id=perf_event_data.get("session_id")
                    )
                    self.performance_events.append(event)
            
            logger.info(f"Loaded {len(self.usage_events)} usage events and {len(self.performance_events)} performance events")
            
        except Exception as e:
            logger.error(f"Failed to load analytics data: {e}")
    
    def _save_analytics_data(self):
        """Save analytics data to storage"""
        try:
            # Save usage events (keep last 30 days)
            cutoff_date = datetime.now() - timedelta(days=30)
            recent_usage_events = [
                event for event in self.usage_events
                if event.timestamp >= cutoff_date
            ]
            
            events_data = [
                {
                    "event_id": event.event_id,
                    "user_id": event.user_id,
                    "session_id": event.session_id,
                    "component_id": event.component_id,
                    "action": event.action.value,
                    "timestamp": event.timestamp.isoformat(),
                    "context": event.context,
                    "metadata": event.metadata
                }
                for event in recent_usage_events
            ]
            
            events_file = self.storage_path / "usage_events.json"
            with open(events_file, 'w') as f:
                json.dump(events_data, f, indent=2)
            
            # Save performance events
            recent_perf_events = [
                event for event in self.performance_events
                if event.timestamp >= cutoff_date
            ]
            
            perf_data = [
                {
                    "metric": event.metric.value,
                    "value": event.value,
                    "component_id": event.component_id,
                    "timestamp": event.timestamp.isoformat(),
                    "context": event.context,
                    "session_id": event.session_id
                }
                for event in recent_perf_events
            ]
            
            perf_file = self.storage_path / "performance_events.json"
            with open(perf_file, 'w') as f:
                json.dump(perf_data, f, indent=2)
            
            self._last_save = datetime.now()
            logger.debug(f"Saved {len(events_data)} usage events and {len(perf_data)} performance events")
            
        except Exception as e:
            logger.error(f"Failed to save analytics data: {e}")
    
    def _archive_events(self, events: List[UsageEvent]):
        """Archive old events to separate storage"""
        try:
            archive_file = self.storage_path / "archived_events.json"
            
            # Load existing archived events
            archived_events = []
            if archive_file.exists():
                with open(archive_file, 'r') as f:
                    archived_events = json.load(f)
            
            # Add new events to archive
            new_archived_events = [
                {
                    "event_id": event.event_id,
                    "component_id": event.component_id,
                    "action": event.action.value,
                    "timestamp": event.timestamp.isoformat()
                }
                for event in events
            ]
            
            archived_events.extend(new_archived_events)
            
            # Save archive
            with open(archive_file, 'w') as f:
                json.dump(archived_events, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to archive events: {e}")


# Global analytics instance
_analytics_instance: Optional[ComponentAnalytics] = None


def get_component_analytics() -> ComponentAnalytics:
    """Get the global component analytics instance"""
    global _analytics_instance
    if _analytics_instance is None:
        _analytics_instance = ComponentAnalytics()
    return _analytics_instance