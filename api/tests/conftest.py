"""
Pytest configuration and fixtures for the Fitness Functions test suite.
"""

import os
import sys
import pytest
import tempfile
import shutil
import pandas as pd
from pathlib import Path
from unittest.mock import patch
from typing import Dict, Any, Generator
import json

# Add the parent directory to the Python path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)

@pytest.fixture
def sample_csv_data() -> Dict[str, pd.DataFrame]:
    """Sample CSV data for testing."""
    return {
        'code_quality_v1': pd.DataFrame({
            'app_id': ['App A', 'App B', 'App C'],
            'lint_score': [85, 92, 78],
            'test_coverage': [65, 88, 45],
            'complexity_score': [10, 15, 25],
            'timestamp': pd.to_datetime(['2025-01-15', '2025-01-15', '2025-01-15'])
        }),
        'observability_v1': pd.DataFrame({
            'app_id': ['App A', 'App B', 'App C'],
            'obs_platform': ['ELK', 'Splunk', 'AppDynamics']
        }),
        'simple_data': pd.DataFrame({
            'id': [1, 2, 3],
            'value': [100, 200, 300],
            'status': ['Active', 'Inactive', 'Active']
        })
    }

@pytest.fixture
def sample_csv_files(temp_dir: Path, sample_csv_data: Dict[str, pd.DataFrame]) -> Dict[str, Path]:
    """Create sample CSV files in temp directory."""
    csv_files = {}
    for name, df in sample_csv_data.items():
        file_path = temp_dir / f"{name}.csv"
        df.to_csv(file_path, index=False)
        csv_files[name] = file_path
    return csv_files

@pytest.fixture
def mock_api_dir(temp_dir: Path) -> Path:
    """Create a mock API directory structure."""
    api_dir = temp_dir / "api"
    api_dir.mkdir()
    
    # Create subdirectories
    (api_dir / "data_mock").mkdir()
    (api_dir / "migrations").mkdir()
    (api_dir / "schemas").mkdir()
    (api_dir / "logs").mkdir()
    
    # Create settings file
    settings_content = """[providers]
code_quality = data_mock/code_quality_v1.csv
observability = data_mock/observability_v1.csv
"""
    (api_dir / "settings.ini").write_text(settings_content)
    
    return api_dir

@pytest.fixture
def provider_configs() -> Dict[str, Dict[str, str]]:
    """Sample provider configurations."""
    return {
        'code_quality_v1': {
            'connector_type': 'csv',
            'file_path': 'data_mock/code_quality_v1.csv'
        },
        'observability_v1': {
            'connector_type': 'csv', 
            'file_path': 'data_mock/observability_v1.csv'
        },
        'simple_data_v1': {
            'connector_type': 'csv',
            'file_path': 'data_mock/simple_data.csv'
        }
    }

@pytest.fixture
def sample_migration_plan() -> Dict[str, Any]:
    """Sample migration plan for testing."""
    return {
        "provider_id": "test_provider_v1",
        "from_schema_hash": "old_hash_123",
        "to_schema_hash": "new_hash_456", 
        "migration_steps": [
            {
                "step_type": "add_column",
                "description": "Add new column 'status' with type object",
                "old_value": None,
                "new_value": "status",
                "default_value": "Active",
                "required": False
            }
        ],
        "created_at": "2025-07-15T21:00:00.000000",
        "executed_at": None,
        "success": None,
        "error_message": None
    }

@pytest.fixture
def sample_schema_data() -> Dict[str, Any]:
    """Sample schema detection data."""
    return {
        'provider_id': 'test_provider_v1',
        'file_path': '/path/to/test.csv',
        'columns': {
            'app_id': {
                'name': 'app_id',
                'data_type': 'object',
                'is_nullable': False,
                'unique_values': 3,
                'sample_values': ['App A', 'App B', 'App C'],
                'is_numeric': False,
                'is_datetime': False
            },
            'score': {
                'name': 'score',
                'data_type': 'int64',
                'is_nullable': False,
                'unique_values': 3,
                'sample_values': [85, 92, 78],
                'is_numeric': True,
                'is_datetime': False
            }
        },
        'row_count': 3,
        'schema_hash': 'test_hash_123',
        'detected_at': '2025-07-15T21:00:00.000000',
        'primary_key_candidates': ['app_id'],
        'timestamp_columns': [],
        'identifier_columns': ['app_id']
    }

@pytest.fixture
def mock_cache_data() -> Dict[str, Any]:
    """Sample cache data for testing."""
    return {
        'raw_data': {
            'code_quality_v1': {
                'App A': {
                    'lint_score': 85,
                    'test_coverage': 65,
                    'complexity_score': 10,
                    'timestamp': pd.Timestamp('2025-01-15')
                },
                'App B': {
                    'lint_score': 92,
                    'test_coverage': 88,
                    'complexity_score': 15,
                    'timestamp': pd.Timestamp('2025-01-15')
                }
            }
        },
        'rule_results': {
            'AggregateByAppRule': {
                'code_quality_v1': {
                    'App A': {'overall_score': 85},
                    'App B': {'overall_score': 92}
                }
            }
        }
    }

# Mock environment fixtures
@pytest.fixture
def mock_settings_file(temp_dir: Path) -> Path:
    """Create a mock settings.ini file."""
    settings_content = """[providers]
code_quality = data_mock/code_quality_v1.csv
observability = data_mock/observability_v1.csv
security = data_mock/security_v1.csv
"""
    settings_file = temp_dir / "settings.ini"
    settings_file.write_text(settings_content)
    return settings_file

@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Cleanup any test files created during testing."""
    yield
    # Cleanup logic can be added here if needed
    pass

# Async fixtures for FastAPI testing
@pytest.fixture
def anyio_backend():
    """Configure anyio backend for async tests."""
    return 'asyncio'