"""
Technical Debt Management Fitness Function

This fitness function prioritizes applications for technical debt reduction
based on code quality, sustainability, and operational impact.
"""

from typing import Dict, Any, Optional
from .base import BaseFitnessFunction


class TechnicalDebtFitnessFunction(BaseFitnessFunction):
    """Processes technical debt priority rule results into fitness metrics."""
    
    @staticmethod
    def get_metadata() -> Dict[str, str]:
        """Returns metadata about this fitness function."""
        return {
            "id": "technical_debt_management",
            "name": "Technical Debt Management",
            "description": "Prioritizes applications for technical debt reduction based on code quality, sustainability, and operational impact",
            "rule_id": "tech_debt_priority"
        }
    
    @staticmethod
    def calculate(rule_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Calculate fitness metrics from tech debt priority rule results.
        
        Args:
            rule_results: Dictionary containing all rule results from cache
            
        Returns:
            Dictionary containing fitness function metrics or None if no data
        """
        # Check if tech_debt_priority rule exists in results
        if 'tech_debt_priority' not in rule_results:
            return None
            
        tech_debt_data = rule_results['tech_debt_priority']
        
        # Count applications by priority
        passing = 0  # Low Priority
        warning = 0  # Medium Priority
        failing = 0  # High Priority
        
        for app_id, priority in tech_debt_data.items():
            if isinstance(priority, str):
                if 'Low Priority' in priority:
                    passing += 1
                elif 'Medium Priority' in priority:
                    warning += 1
                elif 'High Priority' in priority:
                    failing += 1
        
        total = passing + warning + failing
        passing_percentage = (passing / total * 100) if total > 0 else 0
        
        metadata = TechnicalDebtFitnessFunction.get_metadata()
        
        return {
            "id": "2",  # For GraphQL compatibility
            "name": metadata["name"],
            "description": metadata["description"],
            "rule_id": metadata["rule_id"],
            "passing_count": passing,
            "warning_count": warning,
            "failing_count": failing,
            "total_count": total,
            "passing_percentage": passing_percentage,
            "application_breakdown": tech_debt_data if isinstance(tech_debt_data, dict) else {}
        }