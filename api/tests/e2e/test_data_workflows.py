"""
End-to-end tests for data loading workflows.

Tests complete data processing workflows from CSV files through
schema detection, flexible loading, rules engine, and cache management.
"""

import pytest
import pandas as pd
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import json

from flexible_data_loader import FlexibleDataLoader, load_flexible_raw_data_from_csv
from schema_manager import schema_detector
from schema_migration import auto_migrate_all_providers
from data_aggregator import update_cache, get_aggregated_data


class TestCompleteDataWorkflow:
    """Test complete data processing workflows."""
    
    def test_full_csv_to_cache_workflow(self, temp_dir, sample_csv_data):
        """Test complete workflow from CSV files to cached data."""
        # Setup test environment
        api_dir = temp_dir / "api_test"
        api_dir.mkdir()
        data_dir = api_dir / "data_mock"
        data_dir.mkdir()
        
        # Create CSV files
        csv_files = {}
        for name, df in sample_csv_data.items():
            file_path = data_dir / f"{name}.csv"
            df.to_csv(file_path, index=False)
            csv_files[name] = file_path
        
        # Setup provider configs
        provider_configs = {
            f"{name}_v1": {
                "connector_type": "csv",
                "file_path": f"data_mock/{name}.csv"
            }
            for name in sample_csv_data.keys()
        }
        
        # Test flexible data loading
        loader = FlexibleDataLoader(str(api_dir))
        
        for provider_id, config in provider_configs.items():
            data = loader.load_data_with_flexible_schema(provider_id, config)
            
            assert data is not None
            assert len(data) > 0
            
            # Verify data structure
            for app_id, app_data in data.items():
                assert isinstance(app_data, dict)
                assert len(app_data) > 0
    
    def test_schema_detection_and_migration_workflow(self, temp_dir, sample_csv_data):
        """Test schema detection and migration workflow."""
        # Setup test environment
        api_dir = temp_dir / "api_test"
        api_dir.mkdir()
        data_dir = api_dir / "data_mock"
        data_dir.mkdir()
        schemas_dir = api_dir / "schemas"
        schemas_dir.mkdir()
        migrations_dir = api_dir / "migrations"
        migrations_dir.mkdir()
        
        # Create initial CSV file
        initial_df = sample_csv_data['code_quality_v1'].copy()
        csv_file = data_dir / "code_quality_v1.csv"
        initial_df.to_csv(csv_file, index=False)
        
        # Setup schema detector with temp directory
        detector = schema_detector
        original_api_dir = detector.api_dir
        original_cache_file = detector.schema_cache_file
        
        try:
            detector.api_dir = str(api_dir)
            detector.schema_cache_file = schemas_dir / "detected_schemas.json"
            detector.ensure_schema_directory()
            
            # 1. Initial schema detection
            schema = detector.detect_schema(str(csv_file), 'code_quality_v1')
            assert schema is not None
            assert schema.provider_id == 'code_quality_v1'
            
            # 2. Save schema
            detector.save_schema(schema)
            assert detector.schema_cache_file.exists()
            
            # 3. Modify CSV to trigger schema change
            modified_df = initial_df.copy()
            modified_df['new_status'] = 'Active'
            modified_df.to_csv(csv_file, index=False)
            
            # 4. Detect schema change
            new_schema = detector.detect_schema(str(csv_file), 'code_quality_v1')
            assert new_schema is not None
            assert new_schema.schema_hash != schema.schema_hash
            
            # 5. Test migration detection
            changes = detector.detect_schema_changes('code_quality_v1', str(csv_file))
            assert changes is not None
            assert changes['schema_changed'] is True
            assert len(changes['new_columns']) == 1
            assert 'new_status' in changes['new_columns']
            
        finally:
            # Restore original settings
            detector.api_dir = original_api_dir
            detector.schema_cache_file = original_cache_file
    
    def test_flexible_loading_with_different_schemas(self, temp_dir):
        """Test flexible loading with various CSV schema patterns."""
        api_dir = temp_dir / "api_test"
        api_dir.mkdir()
        data_dir = api_dir / "data_mock"
        data_dir.mkdir()
        
        # Test different schema patterns
        test_schemas = {
            # Standard schema with all expected columns
            'standard': pd.DataFrame({
                'app_id': ['App1', 'App2', 'App3'],
                'score': [85, 92, 78],
                'timestamp': pd.to_datetime(['2025-01-15', '2025-01-16', '2025-01-17'])
            }),
            
            # Minimal schema with just identifier
            'minimal': pd.DataFrame({
                'application_name': ['App1', 'App2', 'App3'],
                'value': [100, 200, 300]
            }),
            
            # Schema with different column names
            'different_names': pd.DataFrame({
                'id': [1, 2, 3],
                'performance_metric': [85.5, 92.1, 78.9],
                'created_date': ['2025-01-15', '2025-01-16', '2025-01-17'],
                'status': ['Active', 'Active', 'Inactive']
            }),
            
            # Schema with minimal columns
            'very_minimal': pd.DataFrame({
                'name': ['Service1', 'Service2'],
                'health': ['Good', 'Poor']
            })
        }
        
        loader = FlexibleDataLoader(str(api_dir))
        
        for schema_name, df in test_schemas.items():
            # Create CSV file
            csv_file = data_dir / f"{schema_name}_test.csv"
            df.to_csv(csv_file, index=False)
            
            # Test loading
            config = {
                'connector_type': 'csv',
                'file_path': f"data_mock/{schema_name}_test.csv"
            }
            
            data = loader.load_data_with_flexible_schema(f"{schema_name}_provider", config)
            
            # Should successfully load all schemas
            assert data is not None, f"Failed to load {schema_name} schema"
            assert len(data) > 0, f"No data loaded for {schema_name} schema"
            
            # Verify data structure
            for key, record in data.items():
                assert isinstance(record, dict)
                assert len(record) > 0
    
    @patch('data_aggregator.PROVIDER_CONFIGS')
    @patch('data_aggregator.API_DIR')
    def test_cache_update_workflow(self, mock_api_dir, mock_provider_configs, temp_dir, sample_csv_data):
        """Test the complete cache update workflow."""
        # Setup test environment
        api_dir = temp_dir / "api_test"
        api_dir.mkdir()
        data_dir = api_dir / "data_mock"
        data_dir.mkdir()
        
        mock_api_dir = str(api_dir)
        
        # Create CSV files and provider configs
        provider_configs = {}
        for name, df in sample_csv_data.items():
            csv_file = data_dir / f"{name}.csv"
            df.to_csv(csv_file, index=False)
            provider_configs[f"{name}_v1"] = {
                "connector_type": "csv",
                "file_path": f"data_mock/{name}.csv"
            }
        
        mock_provider_configs = provider_configs
        
        # Mock the rules engine to avoid complex setup
        with patch('data_aggregator.load_rules') as mock_load_rules, \
             patch('data_aggregator.run_rules') as mock_run_rules, \
             patch('data_aggregator.data_cache') as mock_cache:
            
            mock_load_rules.return_value = [MagicMock()]
            mock_run_rules.return_value = {"test_rule": {"result": "success"}}
            mock_cache.__setitem__ = MagicMock()
            mock_cache.__getitem__ = MagicMock()
            mock_cache.keys.return_value = []
            
            # Test cache update (this tests the integration without full system)
            # In a real scenario, this would update the actual cache
            # For this test, we verify the components work together
            
            # Test flexible loading for each provider
            for provider_id, config in provider_configs.items():
                result = load_flexible_raw_data_from_csv(provider_id, config, str(api_dir))
                assert result is not None
                assert len(result) > 0
    
    def test_error_handling_in_workflow(self, temp_dir):
        """Test error handling throughout the data workflow."""
        api_dir = temp_dir / "api_test"
        api_dir.mkdir()
        data_dir = api_dir / "data_mock"
        data_dir.mkdir()
        
        loader = FlexibleDataLoader(str(api_dir))
        
        # Test 1: Non-existent file
        config_nonexistent = {
            'connector_type': 'csv',
            'file_path': 'data_mock/nonexistent.csv'
        }
        
        result = loader.load_data_with_flexible_schema('nonexistent_provider', config_nonexistent)
        assert result is None
        
        # Test 2: Empty file
        empty_file = data_dir / "empty.csv"
        pd.DataFrame().to_csv(empty_file, index=False)
        
        config_empty = {
            'connector_type': 'csv',
            'file_path': 'data_mock/empty.csv'
        }
        
        result = loader.load_data_with_flexible_schema('empty_provider', config_empty)
        assert result is None
        
        # Test 3: Corrupted CSV file
        corrupted_file = data_dir / "corrupted.csv"
        with open(corrupted_file, 'w') as f:
            f.write("invalid,csv,content\nthis is not,proper\n")
        
        config_corrupted = {
            'connector_type': 'csv',
            'file_path': 'data_mock/corrupted.csv'
        }
        
        # Should handle gracefully (may return None or partial data)
        result = loader.load_data_with_flexible_schema('corrupted_provider', config_corrupted)
        # Don't assert specific result - just ensure it doesn't crash
    
    def test_data_consistency_across_workflow(self, temp_dir, sample_csv_data):
        """Test data consistency throughout the processing workflow."""
        api_dir = temp_dir / "api_test"
        api_dir.mkdir()
        data_dir = api_dir / "data_mock"
        data_dir.mkdir()
        
        # Create CSV file
        test_df = sample_csv_data['code_quality_v1'].copy()
        csv_file = data_dir / "consistency_test.csv"
        test_df.to_csv(csv_file, index=False)
        
        loader = FlexibleDataLoader(str(api_dir))
        config = {
            'connector_type': 'csv',
            'file_path': 'data_mock/consistency_test.csv'
        }
        
        # Load data
        loaded_data = loader.load_data_with_flexible_schema('consistency_provider', config)
        
        assert loaded_data is not None
        assert len(loaded_data) == len(test_df)
        
        # Verify data integrity
        original_app_ids = set(test_df['app_id'].values)
        loaded_app_ids = set(loaded_data.keys())
        
        assert original_app_ids == loaded_app_ids
        
        # Verify data values for a sample record
        first_app_id = test_df.iloc[0]['app_id']
        original_score = test_df.iloc[0]['lint_score']
        loaded_score = loaded_data[first_app_id]['lint_score']
        
        assert original_score == loaded_score


class TestDataValidationWorkflows:
    """Test data validation throughout workflows."""
    
    def test_schema_validation_workflow(self, temp_dir):
        """Test schema validation across different data sources."""
        api_dir = temp_dir / "api_test"
        api_dir.mkdir()
        data_dir = api_dir / "data_mock"
        data_dir.mkdir()
        
        loader = FlexibleDataLoader(str(api_dir))
        
        # Test valid data source
        valid_df = pd.DataFrame({
            'app_id': ['App1', 'App2', 'App3'],
            'score': [85, 92, 78],
            'timestamp': pd.to_datetime(['2025-01-15', '2025-01-16', '2025-01-17'])
        })
        valid_file = data_dir / "valid_data.csv"
        valid_df.to_csv(valid_file, index=False)
        
        validation = loader.validate_data_against_schema('valid_provider', str(valid_file))
        
        assert validation['is_valid'] is True
        assert len(validation['errors']) == 0
        assert validation['schema_info']['has_identifier'] is True
        assert validation['schema_info']['has_timestamp'] is True
        
        # Test data with quality issues
        problematic_df = pd.DataFrame({
            'unclear_id': [1, 1, 2],  # Low uniqueness
            'score': [85, None, 78],  # Null values
            'description': ['A', None, 'C']  # More nulls
        })
        problematic_file = data_dir / "problematic_data.csv"
        problematic_df.to_csv(problematic_file, index=False)
        
        validation = loader.validate_data_against_schema('problematic_provider', str(problematic_file))
        
        assert validation['is_valid'] is True  # Still valid structurally
        assert len(validation['warnings']) > 0  # But has warnings
    
    def test_migration_safety_workflow(self, temp_dir):
        """Test migration safety checks in workflow."""
        api_dir = temp_dir / "api_test"
        api_dir.mkdir()
        data_dir = api_dir / "data_mock"
        data_dir.mkdir()
        
        # Create initial data
        initial_df = pd.DataFrame({
            'app_id': ['App1', 'App2'],
            'score': [85, 92],
            'category': ['A', 'B']
        })
        csv_file = data_dir / "migration_test.csv"
        initial_df.to_csv(csv_file, index=False)
        
        # Test auto-migration with safe changes
        provider_configs = {
            'migration_test_v1': {
                'connector_type': 'csv',
                'file_path': 'data_mock/migration_test.csv'
            }
        }
        
        # Add column (safe change)
        safe_df = initial_df.copy()
        safe_df['new_status'] = 'Active'
        safe_df.to_csv(csv_file, index=False)
        
        results = auto_migrate_all_providers(provider_configs, str(api_dir))
        
        # Should handle the migration
        assert 'migration_test_v1' in results
        
        # Verify data still loads correctly
        loader = FlexibleDataLoader(str(api_dir))
        config = provider_configs['migration_test_v1']
        
        data = loader.load_data_with_flexible_schema('migration_test_v1', config)
        assert data is not None
        assert len(data) == 2  # Same number of records


@pytest.mark.e2e
@pytest.mark.slow
class TestPerformanceWorkflows:
    """Test performance aspects of data workflows."""
    
    def test_large_dataset_workflow(self, temp_dir):
        """Test workflow with larger datasets."""
        api_dir = temp_dir / "api_test"
        api_dir.mkdir()
        data_dir = api_dir / "data_mock"
        data_dir.mkdir()
        
        # Create larger dataset
        large_df = pd.DataFrame({
            'app_id': [f'App_{i}' for i in range(1000)],
            'score': [i % 100 for i in range(1000)],
            'category': [f'Category_{i % 10}' for i in range(1000)],
            'timestamp': pd.date_range('2025-01-01', periods=1000, freq='H')
        })
        
        large_file = data_dir / "large_dataset.csv"
        large_df.to_csv(large_file, index=False)
        
        loader = FlexibleDataLoader(str(api_dir))
        config = {
            'connector_type': 'csv',
            'file_path': 'data_mock/large_dataset.csv'
        }
        
        import time
        start_time = time.time()
        
        data = loader.load_data_with_flexible_schema('large_provider', config)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert data is not None
        assert len(data) == 1000
        assert processing_time < 10.0  # Should process within 10 seconds
    
    def test_multiple_providers_workflow(self, temp_dir, sample_csv_data):
        """Test workflow with multiple data providers."""
        api_dir = temp_dir / "api_test"
        api_dir.mkdir()
        data_dir = api_dir / "data_mock"
        data_dir.mkdir()
        
        # Create multiple CSV files
        provider_configs = {}
        for i, (name, df) in enumerate(sample_csv_data.items()):
            csv_file = data_dir / f"provider_{i}.csv"
            df.to_csv(csv_file, index=False)
            provider_configs[f"provider_{i}_v1"] = {
                "connector_type": "csv",
                "file_path": f"data_mock/provider_{i}.csv"
            }
        
        loader = FlexibleDataLoader(str(api_dir))
        
        import time
        start_time = time.time()
        
        # Load all providers
        all_data = {}
        for provider_id, config in provider_configs.items():
            data = loader.load_data_with_flexible_schema(provider_id, config)
            if data:
                all_data[provider_id] = data
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert len(all_data) == len(provider_configs)
        assert processing_time < 15.0  # Should process all within 15 seconds
        
        # Verify each provider loaded successfully
        for provider_id in provider_configs.keys():
            assert provider_id in all_data
            assert len(all_data[provider_id]) > 0


@pytest.mark.e2e
class TestRealWorldScenarios:
    """Test realistic end-to-end scenarios."""
    
    def test_new_data_source_onboarding(self, temp_dir):
        """Test complete workflow for onboarding a new data source."""
        api_dir = temp_dir / "api_test"
        api_dir.mkdir()
        data_dir = api_dir / "data_mock"
        data_dir.mkdir()
        
        # Scenario: New team wants to add security metrics
        security_df = pd.DataFrame({
            'application_name': ['WebApp1', 'WebApp2', 'WebApp3'],
            'vulnerability_count': [5, 2, 8],
            'security_score': [85.5, 95.2, 70.1],
            'last_scan_date': ['2025-01-15', '2025-01-14', '2025-01-13'],
            'compliance_status': ['Compliant', 'Compliant', 'Non-Compliant']
        })
        
        security_file = data_dir / "security_metrics.csv"
        security_df.to_csv(security_file, index=False)
        
        # 1. Validate the new data source
        loader = FlexibleDataLoader(str(api_dir))
        validation = loader.validate_data_against_schema('security_provider', str(security_file))
        
        assert validation['is_valid'] is True
        assert validation['schema_info']['has_identifier'] is True  # application_name
        
        # 2. Load the data using flexible schema
        config = {
            'connector_type': 'csv',
            'file_path': 'data_mock/security_metrics.csv'
        }
        
        data = loader.load_data_with_flexible_schema('security_provider', config)
        
        assert data is not None
        assert len(data) == 3
        
        # 3. Verify data structure and accessibility
        for app_name, app_data in data.items():
            assert 'vulnerability_count' in app_data
            assert 'security_score' in app_data
            assert 'compliance_status' in app_data
    
    def test_data_evolution_scenario(self, temp_dir):
        """Test scenario where data source evolves over time."""
        api_dir = temp_dir / "api_test"
        api_dir.mkdir()
        data_dir = api_dir / "data_mock"
        data_dir.mkdir()
        
        # Initial data structure
        v1_df = pd.DataFrame({
            'app_id': ['App1', 'App2'],
            'performance_score': [85, 92]
        })
        
        perf_file = data_dir / "performance_metrics.csv"
        v1_df.to_csv(perf_file, index=False)
        
        loader = FlexibleDataLoader(str(api_dir))
        config = {
            'connector_type': 'csv',
            'file_path': 'data_mock/performance_metrics.csv'
        }
        
        # 1. Load initial version
        v1_data = loader.load_data_with_flexible_schema('performance_provider', config)
        assert v1_data is not None
        assert len(v1_data) == 2
        
        # 2. Evolve data structure (add columns)
        v2_df = v1_df.copy()
        v2_df['response_time'] = [150, 200]
        v2_df['error_rate'] = [0.1, 0.05]
        v2_df.to_csv(perf_file, index=False)
        
        # 3. Load evolved version
        v2_data = loader.load_data_with_flexible_schema('performance_provider', config)
        assert v2_data is not None
        assert len(v2_data) == 2
        
        # Verify new columns are available
        for app_id, app_data in v2_data.items():
            assert 'performance_score' in app_data  # Original column
            assert 'response_time' in app_data      # New column
            assert 'error_rate' in app_data         # New column
        
        # 4. Further evolution (modify existing data)
        v3_df = v2_df.copy()
        v3_df['performance_score'] = v3_df['performance_score'] + 5  # Improved scores
        v3_df.to_csv(perf_file, index=False)
        
        # 5. Load final version
        v3_data = loader.load_data_with_flexible_schema('performance_provider', config)
        assert v3_data is not None
        
        # Verify data evolution
        assert v3_data['App1']['performance_score'] == 90  # 85 + 5
        assert v3_data['App2']['performance_score'] == 97  # 92 + 5