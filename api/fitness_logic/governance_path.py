"""
Governance Path Compliance Fitness Function

This fitness function evaluates applications for governance approval path
based on security, quality, and operational metrics.
"""

from typing import Dict, Any, Optional
from .base import BaseFitnessFunction


class GovernancePathFitnessFunction(BaseFitnessFunction):
    """Processes governance path decision rule results into fitness metrics."""
    
    @staticmethod
    def get_metadata() -> Dict[str, str]:
        """Returns metadata about this fitness function."""
        return {
            "id": "governance_path_compliance",
            "name": "Governance Path Compliance",
            "description": "Evaluates applications for governance approval path based on security, quality, and operational metrics",
            "rule_id": "governance_path_decision"
        }
    
    @staticmethod
    def calculate(rule_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Calculate fitness metrics from governance path decision rule results.
        
        Args:
            rule_results: Dictionary containing all rule results from cache
            
        Returns:
            Dictionary containing fitness function metrics or None if no data
        """
        # Check if governance_path_decision rule exists in results
        if 'governance_path_decision' not in rule_results:
            return None
            
        governance_data = rule_results['governance_path_decision']
        
        # Count applications by status
        passing = 0  # Fast Path
        warning = 0  # Slow Path
        failing = 0  # HALT
        
        for app_id, status in governance_data.items():
            if isinstance(status, str):
                if 'Fast Path' in status:
                    passing += 1
                elif 'Slow Path' in status:
                    warning += 1
                elif 'HALT' in status:
                    failing += 1
        
        total = passing + warning + failing
        passing_percentage = (passing / total * 100) if total > 0 else 0
        
        metadata = GovernancePathFitnessFunction.get_metadata()
        
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
            "application_breakdown": governance_data if isinstance(governance_data, dict) else {}
        }