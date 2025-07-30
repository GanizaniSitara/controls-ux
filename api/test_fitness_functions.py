#!/usr/bin/env python3
"""
Test script to validate new fitness functions
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fitness_logic.cache_accessor import CacheAccessor
from fitness_logic.application_health_score import ApplicationHealthScoreFitnessFunction
from fitness_logic.cost_optimization_fitness import CostOptimizationFitnessFunction

# Mock cache data for testing
mock_cache_data = {
    'raw_data': {
        'code_quality_v1': {
            'TestApp1': {'MaintainabilityIndex': 85, 'TestCoverage': 90, 'ComplexityScore': 5},
            'TestApp2': {'MaintainabilityIndex': 65, 'TestCoverage': 70, 'ComplexityScore': 15},
            'TestApp3': {'MaintainabilityIndex': 45, 'TestCoverage': 50, 'ComplexityScore': 25},
        },
        'operational_excellence_v1': {
            'TestApp1': {'UptimePercent': 99.9, 'AvgResponseTimeMS': 150},
            'TestApp2': {'UptimePercent': 98.5, 'AvgResponseTimeMS': 500},
            'TestApp3': {'UptimePercent': 95.0, 'AvgResponseTimeMS': 1500},
        },
        'cost_optimization_v1': {
            'TestApp1': {'MonthlyCost': 5000, 'AvgResponseTime': 150},
            'TestApp2': {'MonthlyCost': 25000, 'AvgResponseTime': 500},
            'TestApp3': {'MonthlyCost': 75000, 'AvgResponseTime': 1500},
        },
        'security_v1': {
            'TestApp1': {'VulnerabilityCount': 0},
            'TestApp2': {'VulnerabilityCount': 3},
            'TestApp3': {'VulnerabilityCount': 10},
        }
    },
    'rule_results': {
        'governance_path_decision': {},
        'tech_debt_priority': {}
    }
}

def test_cache_accessor():
    """Test CacheAccessor functionality"""
    print("=== Testing CacheAccessor ===")
    accessor = CacheAccessor(mock_cache_data)
    
    # Test get_all_app_ids
    app_ids = accessor.get_all_app_ids()
    print(f"All app IDs: {app_ids}")
    assert len(app_ids) == 3
    
    # Test get_field_value
    maint_index = accessor.get_field_value('TestApp1', 'code_quality_v1.MaintainabilityIndex', 0)
    print(f"TestApp1 MaintainabilityIndex: {maint_index}")
    assert maint_index == 85
    
    # Test iterate_apps_with_data
    apps_data = accessor.iterate_apps_with_data(['code_quality_v1', 'cost_optimization_v1'])
    print(f"Apps with quality and cost data: {list(apps_data.keys())}")
    assert len(apps_data) == 3
    
    # Test aggregate_field
    total_cost = accessor.aggregate_field('cost_optimization_v1', 'MonthlyCost', 'sum')
    avg_cost = accessor.aggregate_field('cost_optimization_v1', 'MonthlyCost', 'avg')
    print(f"Total monthly cost: ${total_cost:,.2f}")
    print(f"Average monthly cost: ${avg_cost:,.2f}")
    
    # Test count_by_condition
    cost_ranges = accessor.count_by_condition(
        'cost_optimization_v1',
        'MonthlyCost',
        lambda cost: 'low' if cost < 10000 else 'medium' if cost < 50000 else 'high'
    )
    print(f"Cost distribution: {cost_ranges}")
    
    print("✓ CacheAccessor tests passed\n")

def test_health_score_function():
    """Test ApplicationHealthScoreFitnessFunction"""
    print("=== Testing ApplicationHealthScoreFitnessFunction ===")
    
    # Mock get_aggregated_data to return our test data
    import fitness_logic.application_health_score
    original_get_data = getattr(fitness_logic.application_health_score, 'get_aggregated_data', None)
    fitness_logic.application_health_score.get_aggregated_data = lambda: mock_cache_data
    
    try:
        result = ApplicationHealthScoreFitnessFunction.calculate({})
        
        if result:
            print(f"Name: {result['name']}")
            print(f"Description: {result['description']}")
            print(f"Total apps: {result['total_count']}")
            print(f"Passing: {result['passing_count']}")
            print(f"Warning: {result['warning_count']}")
            print(f"Failing: {result['failing_count']}")
            print(f"Passing percentage: {result['passing_percentage']}%")
            
            breakdown = result['application_breakdown']
            print(f"Categories: {breakdown['categories'].keys()}")
            print(f"Statistics: {breakdown['statistics']}")
            print("✓ Health score function test passed\n")
        else:
            print("✗ Health score function returned None")
    finally:
        # Restore original if it existed
        if original_get_data:
            fitness_logic.application_health_score.get_aggregated_data = original_get_data

def test_cost_optimization_function():
    """Test CostOptimizationFitnessFunction"""
    print("=== Testing CostOptimizationFitnessFunction ===")
    
    # Mock get_aggregated_data
    import fitness_logic.cost_optimization_fitness
    original_get_data = getattr(fitness_logic.cost_optimization_fitness, 'get_aggregated_data', None)
    fitness_logic.cost_optimization_fitness.get_aggregated_data = lambda: mock_cache_data
    
    try:
        result = CostOptimizationFitnessFunction.calculate({})
        
        if result:
            print(f"Name: {result['name']}")
            print(f"Description: {result['description']}")
            print(f"Total apps: {result['total_count']}")
            print(f"Optimized: {result['passing_count']}")
            print(f"Acceptable: {result['warning_count']}")
            print(f"Needs review: {result['failing_count']}")
            
            breakdown = result['application_breakdown']
            print(f"Total monthly cost: ${breakdown['statistics']['total_monthly_cost']:,.2f}")
            print(f"Potential savings: ${breakdown['statistics']['potential_savings']:,.2f}")
            print("✓ Cost optimization function test passed")
        else:
            print("✗ Cost optimization function returned None")
    finally:
        if original_get_data:
            fitness_logic.cost_optimization_fitness.get_aggregated_data = original_get_data

if __name__ == '__main__':
    test_cache_accessor()
    test_health_score_function()
    test_cost_optimization_function()
    print("\nAll tests completed!")