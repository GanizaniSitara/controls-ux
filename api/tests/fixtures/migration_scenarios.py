"""
Migration test scenarios and fixtures.

Provides realistic migration scenarios for comprehensive testing
of the schema migration system.
"""

import pandas as pd
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MigrationScenario:
    """Represents a migration test scenario."""
    name: str
    description: str
    before_df: pd.DataFrame
    after_df: pd.DataFrame
    expected_steps: List[Dict[str, Any]]
    is_breaking: bool
    should_auto_execute: bool
    expected_warnings: List[str] = None


class MigrationScenarioFactory:
    """Factory for creating migration test scenarios."""
    
    @staticmethod
    def get_all_scenarios() -> List[MigrationScenario]:
        """Get all migration test scenarios."""
        return [
            MigrationScenarioFactory.add_column_scenario(),
            MigrationScenarioFactory.remove_column_scenario(),
            MigrationScenarioFactory.rename_column_scenario(),
            MigrationScenarioFactory.change_type_scenario(),
            MigrationScenarioFactory.multiple_changes_scenario(),
            MigrationScenarioFactory.breaking_changes_scenario(),
            MigrationScenarioFactory.safe_evolution_scenario(),
            MigrationScenarioFactory.complex_schema_scenario(),
            MigrationScenarioFactory.minimal_schema_scenario(),
            MigrationScenarioFactory.real_world_scenario()
        ]
    
    @staticmethod
    def add_column_scenario() -> MigrationScenario:
        """Scenario: Adding a new column (non-breaking)."""
        before_df = pd.DataFrame({
            'app_id': ['App1', 'App2', 'App3'],
            'score': [85, 92, 78]
        })
        
        after_df = pd.DataFrame({
            'app_id': ['App1', 'App2', 'App3'],
            'score': [85, 92, 78],
            'status': ['Active', 'Active', 'Inactive']
        })
        
        return MigrationScenario(
            name="add_column",
            description="Adding a new status column",
            before_df=before_df,
            after_df=after_df,
            expected_steps=[{
                'step_type': 'add_column',
                'new_value': 'status',
                'default_value': ''
            }],
            is_breaking=False,
            should_auto_execute=True
        )
    
    @staticmethod
    def remove_column_scenario() -> MigrationScenario:
        """Scenario: Removing a column (breaking)."""
        before_df = pd.DataFrame({
            'app_id': ['App1', 'App2', 'App3'],
            'score': [85, 92, 78],
            'deprecated_field': ['old1', 'old2', 'old3']
        })
        
        after_df = pd.DataFrame({
            'app_id': ['App1', 'App2', 'App3'],
            'score': [85, 92, 78]
        })
        
        return MigrationScenario(
            name="remove_column",
            description="Removing a deprecated column",
            before_df=before_df,
            after_df=after_df,
            expected_steps=[{
                'step_type': 'remove_column',
                'old_value': 'deprecated_field'
            }],
            is_breaking=True,
            should_auto_execute=False,
            expected_warnings=['Breaking schema changes detected']
        )
    
    @staticmethod
    def rename_column_scenario() -> MigrationScenario:
        """Scenario: Renaming a column (breaking)."""
        before_df = pd.DataFrame({
            'app_id': ['App1', 'App2', 'App3'],
            'old_score': [85, 92, 78]
        })
        
        after_df = pd.DataFrame({
            'app_id': ['App1', 'App2', 'App3'],
            'performance_score': [85, 92, 78]
        })
        
        return MigrationScenario(
            name="rename_column",
            description="Renaming old_score to performance_score",
            before_df=before_df,
            after_df=after_df,
            expected_steps=[
                {'step_type': 'remove_column', 'old_value': 'old_score'},
                {'step_type': 'add_column', 'new_value': 'performance_score'}
            ],
            is_breaking=True,
            should_auto_execute=False
        )
    
    @staticmethod
    def change_type_scenario() -> MigrationScenario:
        """Scenario: Changing column data type."""
        before_df = pd.DataFrame({
            'app_id': ['App1', 'App2', 'App3'],
            'score': [85, 92, 78]  # int
        })
        
        after_df = pd.DataFrame({
            'app_id': ['App1', 'App2', 'App3'],
            'score': [85.5, 92.1, 78.9]  # float
        })
        
        return MigrationScenario(
            name="change_type",
            description="Changing score from int to float",
            before_df=before_df,
            after_df=after_df,
            expected_steps=[{
                'step_type': 'change_type',
                'old_value': 'int64',
                'new_value': 'float64'
            }],
            is_breaking=False,
            should_auto_execute=True
        )
    
    @staticmethod
    def multiple_changes_scenario() -> MigrationScenario:
        """Scenario: Multiple simultaneous changes."""
        before_df = pd.DataFrame({
            'app_id': ['App1', 'App2', 'App3'],
            'score': [85, 92, 78],
            'old_field': ['a', 'b', 'c']
        })
        
        after_df = pd.DataFrame({
            'app_id': ['App1', 'App2', 'App3'],
            'score': [85.5, 92.1, 78.9],  # Type change
            'status': ['Active', 'Active', 'Inactive'],  # New column
            'category': ['A', 'B', 'C']  # Another new column
        })
        
        return MigrationScenario(
            name="multiple_changes",
            description="Multiple changes: type change, add columns, remove column",
            before_df=before_df,
            after_df=after_df,
            expected_steps=[
                {'step_type': 'remove_column', 'old_value': 'old_field'},
                {'step_type': 'add_column', 'new_value': 'status'},
                {'step_type': 'add_column', 'new_value': 'category'},
                {'step_type': 'change_type', 'old_value': 'int64', 'new_value': 'float64'}
            ],
            is_breaking=True,  # Due to remove_column
            should_auto_execute=False
        )
    
    @staticmethod
    def breaking_changes_scenario() -> MigrationScenario:
        """Scenario: Multiple breaking changes."""
        before_df = pd.DataFrame({
            'app_id': ['App1', 'App2', 'App3'],
            'score': [85, 92, 78],
            'category': ['A', 'B', 'C'],
            'deprecated1': ['x', 'y', 'z'],
            'deprecated2': [1, 2, 3]
        })
        
        after_df = pd.DataFrame({
            'application_id': ['App1', 'App2', 'App3'],  # Renamed
            'performance_rating': [85, 92, 78],  # Renamed
            'category': ['A', 'B', 'C']  # Unchanged
        })
        
        return MigrationScenario(
            name="breaking_changes",
            description="Multiple breaking changes: renames and removals",
            before_df=before_df,
            after_df=after_df,
            expected_steps=[
                {'step_type': 'remove_column', 'old_value': 'app_id'},
                {'step_type': 'remove_column', 'old_value': 'score'},
                {'step_type': 'remove_column', 'old_value': 'deprecated1'},
                {'step_type': 'remove_column', 'old_value': 'deprecated2'},
                {'step_type': 'add_column', 'new_value': 'application_id'},
                {'step_type': 'add_column', 'new_value': 'performance_rating'}
            ],
            is_breaking=True,
            should_auto_execute=False,
            expected_warnings=['Breaking schema changes detected']
        )
    
    @staticmethod
    def safe_evolution_scenario() -> MigrationScenario:
        """Scenario: Safe schema evolution with only additions."""
        before_df = pd.DataFrame({
            'app_id': ['App1', 'App2'],
            'score': [85, 92]
        })
        
        after_df = pd.DataFrame({
            'app_id': ['App1', 'App2'],
            'score': [85, 92],
            'timestamp': ['2025-01-15T10:00:00', '2025-01-15T11:00:00'],
            'environment': ['prod', 'dev'],
            'team': ['TeamA', 'TeamB'],
            'version': ['1.0', '1.1']
        })
        
        return MigrationScenario(
            name="safe_evolution",
            description="Safe evolution with multiple new columns",
            before_df=before_df,
            after_df=after_df,
            expected_steps=[
                {'step_type': 'add_column', 'new_value': 'timestamp'},
                {'step_type': 'add_column', 'new_value': 'environment'},
                {'step_type': 'add_column', 'new_value': 'team'},
                {'step_type': 'add_column', 'new_value': 'version'}
            ],
            is_breaking=False,
            should_auto_execute=True
        )
    
    @staticmethod
    def complex_schema_scenario() -> MigrationScenario:
        """Scenario: Complex schema with many columns."""
        before_df = pd.DataFrame({
            'app_id': ['App1', 'App2', 'App3'],
            'performance_score': [85.5, 92.1, 78.9],
            'security_score': [88, 95, 72],
            'maintainability_index': [70, 85, 60],
            'test_coverage': [65.5, 88.2, 45.1],
            'code_quality_rating': ['B', 'A', 'C'],
            'deployment_frequency': [5, 8, 3],
            'lead_time_hours': [24, 12, 48],
            'mttr_hours': [2, 1, 4],
            'change_failure_rate': [0.05, 0.02, 0.08]
        })
        
        after_df = pd.DataFrame({
            'app_id': ['App1', 'App2', 'App3'],
            'performance_score': [85.5, 92.1, 78.9],
            'security_score': [88, 95, 72],
            'maintainability_index': [70, 85, 60],
            'test_coverage': [65.5, 88.2, 45.1],
            'code_quality_rating': ['B', 'A', 'C'],
            'deployment_frequency': [5, 8, 3],
            'lead_time_hours': [24, 12, 48],
            'mttr_hours': [2, 1, 4],
            'change_failure_rate': [0.05, 0.02, 0.08],
            'dora_score': [75, 88, 65],  # New calculated field
            'last_updated': ['2025-01-15', '2025-01-15', '2025-01-15']  # New timestamp
        })
        
        return MigrationScenario(
            name="complex_schema",
            description="Complex schema evolution with DORA metrics",
            before_df=before_df,
            after_df=after_df,
            expected_steps=[
                {'step_type': 'add_column', 'new_value': 'dora_score'},
                {'step_type': 'add_column', 'new_value': 'last_updated'}
            ],
            is_breaking=False,
            should_auto_execute=True
        )
    
    @staticmethod
    def minimal_schema_scenario() -> MigrationScenario:
        """Scenario: Minimal schema evolution."""
        before_df = pd.DataFrame({
            'id': [1, 2],
            'value': [100, 200]
        })
        
        after_df = pd.DataFrame({
            'id': [1, 2],
            'value': [100, 200],
            'active': [True, False]
        })
        
        return MigrationScenario(
            name="minimal_schema",
            description="Minimal schema with basic columns",
            before_df=before_df,
            after_df=after_df,
            expected_steps=[{
                'step_type': 'add_column',
                'new_value': 'active'
            }],
            is_breaking=False,
            should_auto_execute=True
        )
    
    @staticmethod
    def real_world_scenario() -> MigrationScenario:
        """Scenario: Real-world observability platform migration."""
        before_df = pd.DataFrame({
            'app_id': ['WebApp', 'MobileApp', 'DataService'],
            'obs_platform': ['ELK', 'Splunk', 'AppDynamics']
        })
        
        after_df = pd.DataFrame({
            'app_id': ['WebApp', 'MobileApp', 'DataService'],
            'obs_platform': ['ELK', 'Splunk', 'AppDynamics'],
            'monitoring_status': ['Active', 'Active', 'Inactive'],
            'alert_count_24h': [5, 2, 8],
            'dashboard_url': [
                'https://elk.company.com/dashboard/webapp',
                'https://splunk.company.com/dashboard/mobile',
                'https://appdynamics.company.com/dashboard/data'
            ],
            'sla_compliance': [99.5, 99.8, 98.2]
        })
        
        return MigrationScenario(
            name="real_world_observability",
            description="Real-world observability platform enhancement",
            before_df=before_df,
            after_df=after_df,
            expected_steps=[
                {'step_type': 'add_column', 'new_value': 'monitoring_status'},
                {'step_type': 'add_column', 'new_value': 'alert_count_24h'},
                {'step_type': 'add_column', 'new_value': 'dashboard_url'},
                {'step_type': 'add_column', 'new_value': 'sla_compliance'}
            ],
            is_breaking=False,
            should_auto_execute=True
        )


def create_scenario_csv_files(scenario: MigrationScenario, temp_dir: Path) -> Tuple[Path, Path]:
    """Create before and after CSV files for a migration scenario."""
    before_file = temp_dir / f"{scenario.name}_before.csv"
    after_file = temp_dir / f"{scenario.name}_after.csv"
    
    scenario.before_df.to_csv(before_file, index=False)
    scenario.after_df.to_csv(after_file, index=False)
    
    return before_file, after_file


def get_scenario_by_name(name: str) -> MigrationScenario:
    """Get a specific migration scenario by name."""
    scenarios = MigrationScenarioFactory.get_all_scenarios()
    for scenario in scenarios:
        if scenario.name == name:
            return scenario
    raise ValueError(f"Scenario '{name}' not found")


def get_breaking_scenarios() -> List[MigrationScenario]:
    """Get only breaking migration scenarios."""
    return [s for s in MigrationScenarioFactory.get_all_scenarios() if s.is_breaking]


def get_safe_scenarios() -> List[MigrationScenario]:
    """Get only safe (non-breaking) migration scenarios."""
    return [s for s in MigrationScenarioFactory.get_all_scenarios() if not s.is_breaking]


def get_auto_executable_scenarios() -> List[MigrationScenario]:
    """Get scenarios that should auto-execute."""
    return [s for s in MigrationScenarioFactory.get_all_scenarios() if s.should_auto_execute]


def get_manual_scenarios() -> List[MigrationScenario]:
    """Get scenarios that require manual execution."""
    return [s for s in MigrationScenarioFactory.get_all_scenarios() if not s.should_auto_execute]