"""
Application Health Score Fitness Function

Calculates overall health score based on multiple factors across different providers.
This demonstrates how to use the CacheAccessor for cross-provider analysis.
"""

from typing import Dict, Any, Optional
import logging
from .base import BaseFitnessFunction
from .cache_accessor import CacheAccessor

logger = logging.getLogger(__name__)


class ApplicationHealthScoreFitnessFunction(BaseFitnessFunction):
    """Calculates application health scores based on multiple metrics."""
    
    @staticmethod
    def get_metadata() -> Dict[str, str]:
        """Returns metadata about this fitness function."""
        return {
            "id": "application_health_score",
            "name": "Application Health Score",
            "description": "Overall health score based on quality, operations, and cost efficiency",
            "rule_id": "cross_provider_health"  # Virtual rule ID since we're accessing raw data
        }
    
    @staticmethod
    def calculate(rule_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Calculate health scores across applications."""
        # Get the full cache data which includes raw_data
        # In a real implementation, this would be passed in or injected
        from data_aggregator import get_aggregated_data
        
        try:
            cache_data = get_aggregated_data()
            accessor = CacheAccessor(cache_data)
        except Exception as e:
            logger.error(f"Failed to get cache data: {e}")
            return None
        
        # Categories for health scores
        excellent = []
        good = []
        needs_attention = []
        critical = []
        
        # Detailed breakdown for each app
        app_scores = {}
        
        # Analyze each application
        apps_data = accessor.iterate_apps_with_data([
            'code_quality_v1',
            'operational_excellence_v1',
            'cost_optimization_v1',
            'security_v1'
        ])
        
        for app_id, data in apps_data.items():
            # Extract metrics from different providers
            quality = data.get('code_quality_v1', {})
            ops = data.get('operational_excellence_v1', {})
            cost = data.get('cost_optimization_v1', {})
            security = data.get('security_v1', {})
            
            # Calculate health score (0-100)
            health_score = 0
            factors = 0
            score_breakdown = {}
            
            # Quality factor (30% weight)
            if 'MaintainabilityIndex' in quality:
                quality_score = float(quality['MaintainabilityIndex'])
                health_score += quality_score * 0.3
                score_breakdown['quality'] = quality_score
                factors += 1
            
            # Operations factor (30% weight)
            if 'UptimePercent' in ops:
                ops_score = float(ops.get('UptimePercent', 0))
                health_score += ops_score * 0.3
                score_breakdown['operations'] = ops_score
                factors += 1
            
            # Security factor (25% weight)
            if 'VulnerabilityCount' in security:
                # Inverse relationship - fewer vulnerabilities is better
                vuln_count = int(security.get('VulnerabilityCount', 0))
                security_score = max(0, 100 - (vuln_count * 10))  # -10 points per vulnerability
                health_score += security_score * 0.25
                score_breakdown['security'] = security_score
                factors += 1
            
            # Cost efficiency factor (15% weight)
            if 'MonthlyCost' in cost:
                # Inverse relationship - lower cost is better
                # Normalize cost (assume $100k is max expected)
                monthly_cost = float(cost.get('MonthlyCost', 0))
                cost_score = max(0, 100 - (monthly_cost / 1000))
                health_score += cost_score * 0.15
                score_breakdown['cost_efficiency'] = cost_score
                factors += 1
            
            # Skip if no data
            if factors == 0:
                continue
            
            # Normalize score based on available factors
            health_score = health_score / (factors * sum([0.3, 0.3, 0.25, 0.15][:factors]))
            
            # Store detailed score
            app_scores[app_id] = {
                'overall_score': round(health_score, 2),
                'breakdown': score_breakdown,
                'factors_available': factors
            }
            
            # Categorize
            if health_score >= 85:
                excellent.append(app_id)
            elif health_score >= 70:
                good.append(app_id)
            elif health_score >= 50:
                needs_attention.append(app_id)
            else:
                critical.append(app_id)
        
        # Calculate totals
        total = len(excellent) + len(good) + len(needs_attention) + len(critical)
        passing = len(excellent) + len(good)
        warning = len(needs_attention)
        failing = len(critical)
        
        if total == 0:
            logger.warning("No applications found with sufficient data for health score calculation")
            return None
        
        passing_percentage = round((passing / total * 100), 2)
        
        # Get additional statistics using CacheAccessor
        avg_test_coverage = accessor.aggregate_field('code_quality_v1', 'TestCoverage', 'avg')
        total_monthly_cost = accessor.aggregate_field('cost_optimization_v1', 'MonthlyCost', 'sum')
        
        metadata = ApplicationHealthScoreFitnessFunction.get_metadata()
        
        return {
            "id": "application_health_score",
            "name": metadata["name"],
            "description": metadata["description"],
            "rule_id": metadata["rule_id"],
            "passing_count": passing,
            "warning_count": warning,
            "failing_count": failing,
            "total_count": total,
            "passing_percentage": passing_percentage,
            "application_breakdown": {
                "categories": {
                    "excellent": excellent,
                    "good": good,
                    "needs_attention": needs_attention,
                    "critical": critical
                },
                "detailed_scores": app_scores,
                "statistics": {
                    "average_test_coverage": round(avg_test_coverage, 2),
                    "total_monthly_cost": round(total_monthly_cost, 2)
                }
            }
        }