"""
{name} Fitness Function

{description}
"""

from typing import Dict, Any, Optional
from .base import BaseFitnessFunction
from .cache_accessor import CacheAccessor


class {class_name}(BaseFitnessFunction):
    """{description}"""
    
    @staticmethod
    def get_metadata() -> Dict[str, str]:
        """Returns metadata about this fitness function."""
        return {
            "id": "{id}",
            "name": "{name}",
            "description": "{description}",
            "rule_id": "{rule_id}"
        }
    
    @staticmethod
    def calculate(rule_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Calculate fitness metrics from rule results.
        
        Args:
            rule_results: Dictionary containing all rule results from cache
            
        Returns:
            Dictionary containing fitness function metrics or None if no data
        """
        # Example: Access data using CacheAccessor
        cache = CacheAccessor(rule_results)
        
        # Initialize counters
        passing = 0
        warning = 0
        failing = 0
        application_breakdown = {}
        
        # Example: Iterate through a specific data feed
        # Replace 'data_feed_id' with actual feed ID from data dictionary
        for app_id, app_data in cache.iterate_apps_with_data('data_feed_id'):
            # Example: Check some condition
            # field_value = cache.get_field_value(app_id, 'data_feed_id', 'field_name')
            
            # Example business logic
            status = "passing"  # Replace with actual logic
            
            if status == "passing":
                passing += 1
            elif status == "warning":
                warning += 1
            else:
                failing += 1
                
            application_breakdown[app_id] = status
        
        # Calculate totals
        total = passing + warning + failing
        if total == 0:
            return None
            
        passing_percentage = (passing / total * 100) if total > 0 else 0
        
        metadata = {class_name}.get_metadata()
        
        return {
            "id": "1",  # For GraphQL compatibility
            "name": metadata["name"],
            "description": metadata["description"],
            "rule_id": metadata["rule_id"],
            "passing_count": passing,
            "warning_count": warning,
            "failing_count": failing,
            "total_count": total,
            "passing_percentage": passing_percentage,
            "application_breakdown": application_breakdown
        }