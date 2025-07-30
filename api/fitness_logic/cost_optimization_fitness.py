"""
Cost Optimization Fitness Function

Analyzes cost optimization across applications using the CacheAccessor.
This demonstrates a simpler single-provider fitness function.
"""

from typing import Dict, Any, Optional
import logging
from .base import BaseFitnessFunction
from .cache_accessor import CacheAccessor

logger = logging.getLogger(__name__)


class CostOptimizationFitnessFunction(BaseFitnessFunction):
    """Analyzes cost optimization opportunities across applications."""
    
    @staticmethod
    def get_metadata() -> Dict[str, str]:
        """Returns metadata about this fitness function."""
        return {
            "id": "cost_optimization",
            "name": "Cost Optimization Opportunities",
            "description": "Identifies applications with potential cost optimization opportunities",
            "rule_id": "cost_analysis"
        }
    
    @staticmethod
    def calculate(rule_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Calculate cost optimization metrics."""
        # Get cache data
        from data_aggregator import get_aggregated_data
        
        try:
            cache_data = get_aggregated_data()
            accessor = CacheAccessor(cache_data)
        except Exception as e:
            logger.error(f"Failed to get cache data: {e}")
            return None
        
        # Categories
        optimized = []  # Low cost, good performance
        acceptable = []  # Medium cost or performance
        needs_review = []  # High cost or poor cost/performance ratio
        
        # Get all cost data
        cost_data = accessor.get_provider_data('cost_optimization_v1')
        
        if not cost_data:
            logger.warning("No cost optimization data available")
            return None
        
        # Analyze each application
        for app_id, app_cost_data in cost_data.items():
            if not isinstance(app_cost_data, dict):
                continue
                
            monthly_cost = float(app_cost_data.get('MonthlyCost', 0))
            
            # Get performance metrics to calculate cost efficiency
            response_time = accessor.get_field_value(
                app_id, 
                'cost_optimization_v1.AvgResponseTime',
                1000  # Default to 1000ms if not found
            )
            
            # Get additional context from other providers
            uptime = accessor.get_field_value(
                app_id,
                'operational_excellence_v1.UptimePercent',
                99.0
            )
            
            # Calculate cost efficiency score
            # Lower cost and better performance = higher score
            if response_time > 0:
                cost_efficiency = (1000 / response_time) * (10000 / (monthly_cost + 1)) * (uptime / 100)
            else:
                cost_efficiency = 0
            
            # Categorize based on absolute cost and efficiency
            if monthly_cost < 10000 and cost_efficiency > 50:
                optimized.append({
                    'app_id': app_id,
                    'monthly_cost': monthly_cost,
                    'cost_efficiency_score': round(cost_efficiency, 2)
                })
            elif monthly_cost < 50000 and cost_efficiency > 10:
                acceptable.append({
                    'app_id': app_id,
                    'monthly_cost': monthly_cost,
                    'cost_efficiency_score': round(cost_efficiency, 2)
                })
            else:
                needs_review.append({
                    'app_id': app_id,
                    'monthly_cost': monthly_cost,
                    'cost_efficiency_score': round(cost_efficiency, 2),
                    'reason': 'High cost' if monthly_cost >= 50000 else 'Poor efficiency'
                })
        
        # Use CacheAccessor for aggregations
        total_monthly_cost = accessor.aggregate_field('cost_optimization_v1', 'MonthlyCost', 'sum')
        avg_monthly_cost = accessor.aggregate_field('cost_optimization_v1', 'MonthlyCost', 'avg')
        max_monthly_cost = accessor.aggregate_field('cost_optimization_v1', 'MonthlyCost', 'max')
        
        # Count by cost ranges
        cost_ranges = accessor.count_by_condition(
            'cost_optimization_v1',
            'MonthlyCost',
            lambda cost: (
                'low' if cost < 10000 else
                'medium' if cost < 50000 else
                'high' if cost < 100000 else
                'very_high'
            )
        )
        
        # Calculate totals
        total = len(optimized) + len(acceptable) + len(needs_review)
        passing = len(optimized)
        warning = len(acceptable)
        failing = len(needs_review)
        
        if total == 0:
            return None
            
        passing_percentage = round((passing / total * 100), 2)
        
        metadata = CostOptimizationFitnessFunction.get_metadata()
        
        return {
            "id": "cost_optimization",
            "name": metadata["name"],
            "description": metadata["description"],
            "rule_id": metadata["rule_id"],
            "passing_count": passing,
            "warning_count": warning,
            "failing_count": failing,
            "total_count": total,
            "passing_percentage": passing_percentage,
            "application_breakdown": {
                "optimized": optimized,
                "acceptable": acceptable,
                "needs_review": needs_review,
                "statistics": {
                    "total_monthly_cost": round(total_monthly_cost, 2),
                    "average_monthly_cost": round(avg_monthly_cost, 2),
                    "max_monthly_cost": round(max_monthly_cost, 2),
                    "cost_distribution": cost_ranges,
                    "potential_savings": round(
                        sum(app['monthly_cost'] for app in needs_review) * 0.3,  # Assume 30% potential savings
                        2
                    )
                }
            }
        }