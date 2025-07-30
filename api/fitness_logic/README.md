# Fitness Functions Module

This module contains the implementation of fitness functions that process rule results and generate fitness metrics for the dashboard.

## Structure

- `base.py` - Abstract base class defining the fitness function interface
- `cache_accessor.py` - Helper class for convenient cache data access
- `registry.py` - Central registry for all fitness functions
- Individual fitness function implementations (e.g., `governance_path.py`, `technical_debt.py`)

## Adding a New Fitness Function

To add a new fitness function:

1. Create a new Python file in this directory (e.g., `my_new_function.py`)

2. Import the base class and implement your fitness function:

```python
"""
My New Fitness Function

Description of what this fitness function measures.
"""

from typing import Dict, Any, Optional
from .base import BaseFitnessFunction


class MyNewFitnessFunction(BaseFitnessFunction):
    """Processes my_rule results into fitness metrics."""
    
    @staticmethod
    def get_metadata() -> Dict[str, str]:
        """Returns metadata about this fitness function."""
        return {
            "id": "my_fitness_function",
            "name": "My Fitness Function",
            "description": "Detailed description of what this measures",
            "rule_id": "my_rule_id"  # The rule this function processes
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
        # Check if your rule exists in results
        if 'my_rule_id' not in rule_results:
            return None
            
        my_data = rule_results['my_rule_id']
        
        # Process your data and count passing/warning/failing
        passing = 0
        warning = 0
        failing = 0
        
        # Your logic here...
        
        total = passing + warning + failing
        passing_percentage = (passing / total * 100) if total > 0 else 0
        
        metadata = MyNewFitnessFunction.get_metadata()
        
        return {
            "id": "will_be_set_by_registry",  # Registry sets this
            "name": metadata["name"],
            "description": metadata["description"],
            "rule_id": metadata["rule_id"],
            "passing_count": passing,
            "warning_count": warning,
            "failing_count": failing,
            "total_count": total,
            "passing_percentage": passing_percentage,
            "application_breakdown": my_data if isinstance(my_data, dict) else {}
        }
```

3. Register your fitness function in `registry.py`:

```python
from .my_new_function import MyNewFitnessFunction

class FitnessFunctionRegistry:
    _functions: List[Type[BaseFitnessFunction]] = [
        GovernancePathFitnessFunction,
        TechnicalDebtFitnessFunction,
        MyNewFitnessFunction,  # Add your function here
    ]
```

4. Update `__init__.py` to export your new function:

```python
from .my_new_function import MyNewFitnessFunction

__all__ = [
    # ... existing exports ...
    'MyNewFitnessFunction'
]
```

## How It Works

1. The `data_schema.py` GraphQL resolver calls `FitnessFunctionRegistry.calculate_all()`
2. The registry iterates through all registered fitness functions
3. Each fitness function's `calculate()` method is called with the rule results
4. Results are collected and returned to the GraphQL resolver
5. The frontend displays the fitness functions in the dashboard

## Using the Cache Accessor

The `CacheAccessor` class provides convenient methods for accessing data from the cache. It supports both raw data from providers and processed rule results.

### Basic Usage

```python
from .cache_accessor import CacheAccessor

def calculate(rule_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    # Get the full cache data (includes both raw_data and rule_results)
    # Note: You need to get this from the data aggregator
    from data_aggregator import get_aggregated_data
    cache_data = get_aggregated_data()
    
    # Create accessor
    accessor = CacheAccessor(cache_data)
    
    # Access data...
```

### Common Patterns

#### 1. Iterate Over Applications with Multiple Providers

```python
# Get data for all apps that have both code quality and security data
apps_data = accessor.iterate_apps_with_data(['code_quality_v1', 'security_v1'])

for app_id, data in apps_data.items():
    quality_score = data.get('code_quality_v1', {}).get('MaintainabilityIndex', 0)
    security_issues = data.get('security_v1', {}).get('VulnerabilityCount', 0)
    
    # Your fitness logic here...
```

#### 2. Access Specific Field Values

```python
# Get a specific field value for an app
test_coverage = accessor.get_field_value('MyApp', 'code_quality_v1.TestCoverage', 0)

# Or get multiple fields
for app_id in accessor.get_all_app_ids():
    uptime = accessor.get_field_value(app_id, 'operational_excellence_v1.UptimePercent', 100)
    cost = accessor.get_field_value(app_id, 'cost_optimization_v1.MonthlyCost', 0)
```

#### 3. Count Applications by Condition

```python
# Count apps by test coverage levels
coverage_counts = accessor.count_by_condition(
    'code_quality_v1',
    'TestCoverage',
    lambda x: 'good' if x >= 80 else 'medium' if x >= 60 else 'poor'
)
# Returns: {'good': 45, 'medium': 23, 'poor': 12}
```

#### 4. Aggregate Fields Across Applications

```python
# Calculate total monthly cost across all applications
total_cost = accessor.aggregate_field('cost_optimization_v1', 'MonthlyCost', 'sum')

# Calculate average test coverage
avg_coverage = accessor.aggregate_field('code_quality_v1', 'TestCoverage', 'avg')
```

#### 5. Cross-Provider Analysis

```python
# Find applications with high cost but low quality
high_cost_low_quality = []

for app_id in accessor.get_all_app_ids():
    cost = accessor.get_field_value(app_id, 'cost_optimization_v1.MonthlyCost', 0)
    quality = accessor.get_field_value(app_id, 'code_quality_v1.MaintainabilityIndex', 100)
    
    if cost > 50000 and quality < 70:
        high_cost_low_quality.append({
            'app_id': app_id,
            'cost': cost,
            'quality': quality
        })
```

### Available Cache Accessor Methods

- `get_provider_data(provider_name)` - Get all data for a specific provider
- `get_app_data(app_id, provider_name=None)` - Get data for a specific application
- `get_all_app_ids()` - Get all unique application IDs
- `get_field_value(app_id, field_path, default)` - Get specific field using dot notation
- `iterate_apps_with_data(providers)` - Iterate over apps with data in specified providers
- `get_rule_result(rule_id)` - Get results from a specific rule
- `count_by_condition(provider, field, condition_fn)` - Count apps by condition
- `aggregate_field(provider, field, operation)` - Aggregate numeric field (sum/avg/min/max)

## Example: Creating a Cross-Provider Fitness Function

Here's a complete example of a fitness function that analyzes applications across multiple providers:

```python
"""
Application Health Score Fitness Function

Calculates overall health score based on multiple factors.
"""

from typing import Dict, Any, Optional
from .base import BaseFitnessFunction
from .cache_accessor import CacheAccessor
from data_aggregator import get_aggregated_data


class ApplicationHealthScoreFitnessFunction(BaseFitnessFunction):
    """Calculates application health scores based on multiple metrics."""
    
    @staticmethod
    def get_metadata() -> Dict[str, str]:
        """Returns metadata about this fitness function."""
        return {
            "id": "application_health_score",
            "name": "Application Health Score",
            "description": "Overall health score based on quality, operations, and cost efficiency",
            "rule_id": "health_score"  # Can be a virtual rule ID
        }
    
    @staticmethod
    def calculate(rule_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Calculate health scores across applications."""
        # Get full cache data
        cache_data = get_aggregated_data()
        accessor = CacheAccessor(cache_data)
        
        # Categories for health scores
        excellent = []
        good = []
        needs_attention = []
        critical = []
        
        # Analyze each application
        apps_data = accessor.iterate_apps_with_data([
            'code_quality_v1',
            'operational_excellence_v1',
            'cost_optimization_v1'
        ])
        
        for app_id, data in apps_data.items():
            # Extract metrics
            quality = data.get('code_quality_v1', {})
            ops = data.get('operational_excellence_v1', {})
            cost = data.get('cost_optimization_v1', {})
            
            # Calculate health score (0-100)
            health_score = 0
            factors = 0
            
            # Quality factor (40% weight)
            if 'MaintainabilityIndex' in quality:
                health_score += quality['MaintainabilityIndex'] * 0.4
                factors += 1
            
            # Operations factor (40% weight)
            if 'UptimePercent' in ops:
                health_score += ops['UptimePercent'] * 0.4
                factors += 1
            
            # Cost efficiency factor (20% weight)
            if 'MonthlyCost' in cost:
                # Inverse relationship - lower cost is better
                # Normalize cost (assume $100k is max expected)
                cost_score = max(0, 100 - (cost['MonthlyCost'] / 1000))
                health_score += cost_score * 0.2
                factors += 1
            
            # Skip if no data
            if factors == 0:
                continue
            
            # Normalize score
            health_score = health_score / factors * 3
            
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
        
        passing_percentage = (passing / total * 100) if total > 0 else 0
        
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
                "excellent": excellent,
                "good": good,
                "needs_attention": needs_attention,
                "critical": critical
            }
        }
```

## Best Practices

- Keep fitness function logic focused and single-purpose
- Use clear, descriptive names for passing/warning/failing states
- Include detailed descriptions to help users understand what the metric means
- Handle missing or invalid data gracefully (return None if no data)
- Follow the existing patterns for consistency
- Use the CacheAccessor for cleaner data access code
- Consider performance when iterating over large datasets
- Document any assumptions about data formats or ranges