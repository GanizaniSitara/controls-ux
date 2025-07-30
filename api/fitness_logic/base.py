"""
Base Fitness Function

Abstract base class for all fitness functions to ensure consistent interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseFitnessFunction(ABC):
    """Abstract base class for fitness functions."""
    
    @staticmethod
    @abstractmethod
    def get_metadata() -> Dict[str, str]:
        """
        Returns metadata about this fitness function.
        
        Should return a dictionary with:
        - id: Unique identifier for the fitness function
        - name: Display name
        - description: Detailed description
        - rule_id: The rule identifier this function processes
        """
        pass
    
    @staticmethod
    @abstractmethod
    def calculate(rule_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Calculate fitness metrics from rule results.
        
        Args:
            rule_results: Dictionary containing all rule results from cache
            
        Returns:
            Dictionary containing fitness function metrics or None if no data
            
        The returned dictionary should include:
        - id: Unique ID for GraphQL
        - name: Display name
        - description: Description
        - rule_id: Source rule ID
        - passing_count: Number of passing items
        - warning_count: Number of warning items
        - failing_count: Number of failing items
        - total_count: Total number of items
        - passing_percentage: Percentage of passing items
        - application_breakdown: Detailed breakdown by application
        """
        pass