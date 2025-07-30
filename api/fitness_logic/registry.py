"""
Fitness Functions Registry

Central registry for all fitness functions. This allows easy addition
of new fitness functions and provides a single place to get all available functions.
"""

from typing import List, Type, Dict, Any
from .base import BaseFitnessFunction
from .governance_path import GovernancePathFitnessFunction
from .technical_debt import TechnicalDebtFitnessFunction
from .application_health_score import ApplicationHealthScoreFitnessFunction
from .cost_optimization_fitness import CostOptimizationFitnessFunction


class FitnessFunctionRegistry:
    """Registry for all available fitness functions."""
    
    # List of all registered fitness function classes
    _functions: List[Type[BaseFitnessFunction]] = [
        GovernancePathFitnessFunction,
        TechnicalDebtFitnessFunction,
        ApplicationHealthScoreFitnessFunction,
        CostOptimizationFitnessFunction,
    ]
    
    @classmethod
    def get_all_functions(cls) -> List[Type[BaseFitnessFunction]]:
        """Get all registered fitness function classes."""
        return cls._functions
    
    @classmethod
    def register_function(cls, function_class: Type[BaseFitnessFunction]) -> None:
        """Register a new fitness function class."""
        if function_class not in cls._functions:
            cls._functions.append(function_class)
    
    @classmethod
    def calculate_all(cls, rule_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Calculate all fitness functions from rule results.
        
        Args:
            rule_results: Dictionary containing all rule results from cache
            
        Returns:
            List of fitness function results
        """
        results = []
        
        for i, function_class in enumerate(cls._functions, 1):
            result = function_class.calculate(rule_results)
            if result:
                # Ensure unique ID for GraphQL
                result["id"] = str(i)
                results.append(result)
                
        return results