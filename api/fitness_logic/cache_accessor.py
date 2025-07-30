"""
Cache Accessor

Provides a convenient interface for accessing data from the cache using a simple notation.
Supports accessing both raw_data and rule_results with easy iteration over applications.
"""

from typing import Dict, Any, Optional, List, Set, Union
import logging

logger = logging.getLogger(__name__)


class CacheAccessor:
    """Helper class for accessing cache data with convenient notation."""
    
    def __init__(self, cache_data: Dict[str, Any]):
        """
        Initialize with cache data.
        
        Args:
            cache_data: The full cache dictionary containing 'raw_data' and 'rule_results'
        """
        self.cache_data = cache_data
        self.raw_data = cache_data.get('raw_data', {})
        self.rule_results = cache_data.get('rule_results', {})
    
    def get_provider_data(self, provider_name: str) -> Dict[str, Any]:
        """
        Get all data for a specific provider.
        
        Args:
            provider_name: Name of the provider (e.g., 'code_quality_v1')
            
        Returns:
            Dictionary with app_id as keys and data as values
        """
        return self.raw_data.get(provider_name, {})
    
    def get_app_data(self, app_id: str, provider_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get data for a specific application, optionally from a specific provider.
        
        Args:
            app_id: Application identifier
            provider_name: Optional provider name. If None, returns data from all providers
            
        Returns:
            Dictionary of data for the application
        """
        if provider_name:
            provider_data = self.get_provider_data(provider_name)
            return provider_data.get(app_id, {})
        else:
            # Aggregate data from all providers for this app
            app_data = {}
            for provider, provider_data in self.raw_data.items():
                if isinstance(provider_data, dict) and app_id in provider_data:
                    app_data[provider] = provider_data[app_id]
            return app_data
    
    def get_all_app_ids(self) -> Set[str]:
        """
        Get all unique application IDs across all providers.
        
        Returns:
            Set of all application IDs
        """
        app_ids = set()
        for provider_data in self.raw_data.values():
            if isinstance(provider_data, dict):
                app_ids.update(provider_data.keys())
        return app_ids
    
    def get_field_value(self, app_id: str, field_path: str, default: Any = None) -> Any:
        """
        Get a specific field value using dot notation.
        
        Args:
            app_id: Application identifier
            field_path: Dot-separated path (e.g., 'code_quality_v1.MaintainabilityIndex')
            default: Default value if field not found
            
        Returns:
            Field value or default
            
        Example:
            value = accessor.get_field_value('MyApp', 'code_quality_v1.TestCoverage', 0)
        """
        parts = field_path.split('.')
        if len(parts) < 2:
            return default
            
        provider = parts[0]
        field_name = parts[1] if len(parts) > 1 else None
        
        # Get provider data
        provider_data = self.raw_data.get(provider, {})
        if not isinstance(provider_data, dict):
            return default
            
        # Get app data
        app_data = provider_data.get(app_id, {})
        if not isinstance(app_data, dict):
            return default
            
        # Navigate to the field
        current = app_data
        for part in parts[1:]:
            if isinstance(current, dict):
                current = current.get(part, default)
            else:
                return default
                
        return current
    
    def iterate_apps_with_data(self, providers: Union[str, List[str]]) -> Dict[str, Dict[str, Any]]:
        """
        Iterate over all applications that have data in specified providers.
        
        Args:
            providers: Single provider name or list of provider names
            
        Returns:
            Dictionary with app_id as keys and aggregated data as values
            
        Example:
            for app_id, data in accessor.iterate_apps_with_data(['code_quality_v1', 'security_v1']).items():
                quality_score = data.get('code_quality_v1', {}).get('MaintainabilityIndex', 0)
                security_issues = data.get('security_v1', {}).get('VulnerabilityCount', 0)
        """
        if isinstance(providers, str):
            providers = [providers]
            
        result = {}
        app_ids = self.get_all_app_ids()
        
        for app_id in app_ids:
            app_data = {}
            has_data = False
            
            for provider in providers:
                provider_data = self.get_provider_data(provider)
                if app_id in provider_data:
                    app_data[provider] = provider_data[app_id]
                    has_data = True
            
            if has_data:
                result[app_id] = app_data
                
        return result
    
    def get_rule_result(self, rule_id: str) -> Any:
        """
        Get results from a specific rule.
        
        Args:
            rule_id: Rule identifier
            
        Returns:
            Rule results or empty dict
        """
        return self.rule_results.get(rule_id, {})
    
    def count_by_condition(self, provider: str, field: str, condition_fn) -> Dict[str, int]:
        """
        Count applications by a condition on a specific field.
        
        Args:
            provider: Provider name
            field: Field name
            condition_fn: Function that takes a value and returns a category string
            
        Returns:
            Dictionary with category counts
            
        Example:
            counts = accessor.count_by_condition(
                'code_quality_v1', 
                'TestCoverage',
                lambda x: 'good' if x > 80 else 'poor'
            )
        """
        counts = {}
        provider_data = self.get_provider_data(provider)
        
        for app_id, app_data in provider_data.items():
            if isinstance(app_data, dict) and field in app_data:
                value = app_data[field]
                category = condition_fn(value)
                counts[category] = counts.get(category, 0) + 1
                
        return counts
    
    def aggregate_field(self, provider: str, field: str, operation: str = 'sum') -> float:
        """
        Aggregate a numeric field across all applications.
        
        Args:
            provider: Provider name
            field: Field name
            operation: 'sum', 'avg', 'min', 'max'
            
        Returns:
            Aggregated value
        """
        values = []
        provider_data = self.get_provider_data(provider)
        
        for app_data in provider_data.values():
            if isinstance(app_data, dict) and field in app_data:
                try:
                    value = float(app_data[field])
                    values.append(value)
                except (ValueError, TypeError):
                    continue
        
        if not values:
            return 0.0
            
        if operation == 'sum':
            return sum(values)
        elif operation == 'avg':
            return sum(values) / len(values)
        elif operation == 'min':
            return min(values)
        elif operation == 'max':
            return max(values)
        else:
            raise ValueError(f"Unknown operation: {operation}")