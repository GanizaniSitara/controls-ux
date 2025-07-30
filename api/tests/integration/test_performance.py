"""
Performance tests for the Fitness Functions platform.

Tests performance characteristics of data loading, cache operations,
schema detection, and migration processes.
"""

import pytest
import pandas as pd
import time
import psutil
import os
import threading
from pathlib import Path
from typing import Dict, List
from unittest.mock import patch, MagicMock

from flexible_data_loader import FlexibleDataLoader
from schema_manager import schema_detector
from schema_migration import auto_migrate_all_providers
from data_aggregator import update_cache, get_aggregated_data


class TestDataLoadingPerformance:
    """Test performance of data loading operations."""
    
    
    
    def test_schema_detection_performance(self, temp_dir):
        """Test performance of schema detection operations."""
        api_dir = temp_dir / "api_test"
        api_dir.mkdir()
        
        # Create datasets with different complexities
        datasets = {
            'simple': pd.DataFrame({
                'id': range(1000),
                'value': range(1000)
            }),
            'medium': pd.DataFrame({
                'app_id': [f'App_{i}' for i in range(1000)],
                'score1': [i % 100 for i in range(1000)],
                'score2': [(i * 2) % 100 for i in range(1000)],
                'category': [f'Cat_{i % 10}' for i in range(1000)],
                'timestamp': pd.date_range('2024-01-01', periods=1000, freq='H')
            }),
            'complex': pd.DataFrame({
                **{f'metric_{i}': [j + i for j in range(1000)] for i in range(20)},
                'app_id': [f'App_{i}' for i in range(1000)],
                'timestamp': pd.date_range('2024-01-01', periods=1000, freq='H')
            })
        }
        
        for complexity, df in datasets.items():
            csv_file = api_dir / f"{complexity}_data.csv"
            df.to_csv(csv_file, index=False)
            
            # Measure schema detection time
            start_time = time.time()
            schema = schema_detector.detect_schema(str(csv_file), f"{complexity}_provider")
            end_time = time.time()
            
            detection_time = end_time - start_time
            
            assert schema is not None
            assert detection_time < 2.0, f"Schema detection for {complexity} took {detection_time}s"
            
            # Verify schema quality
            assert len(schema.columns) > 0
            assert schema.row_count == 1000


class TestCachePerformance:
    """Test performance of cache operations."""
    
    @patch('data_aggregator.PROVIDER_CONFIGS')
    @patch('data_aggregator.API_DIR')
    def test_cache_update_performance(self, mock_api_dir, mock_provider_configs, temp_dir, sample_csv_data):
        """Test cache update performance with multiple providers."""
        api_dir = temp_dir / "api_test"
        api_dir.mkdir()
        data_dir = api_dir / "data_mock"
        data_dir.mkdir()
        
        mock_api_dir.return_value = str(api_dir)
        
        # Create multiple CSV files
        provider_configs = {}
        for name, df in sample_csv_data.items():
            csv_file = data_dir / f"{name}.csv"
            df.to_csv(csv_file, index=False)
            provider_configs[f"{name}_v1"] = {
                "connector_type": "csv",
                "file_path": f"data_mock/{name}.csv"
            }
        
        mock_provider_configs.return_value = provider_configs
        
        # Mock rules engine to focus on data loading performance
        with patch('data_aggregator.load_rules') as mock_load_rules, \
             patch('data_aggregator.run_rules') as mock_run_rules:
            
            mock_load_rules.return_value = [MagicMock()]
            mock_run_rules.return_value = {"test_rule": {"result": "success"}}
            
            # Measure cache update time
            start_time = time.time()
            
            # Note: This is a mock test since update_cache uses globals
            # In practice, you'd need to refactor for better testability
            memory_before = psutil.Process().memory_info().rss
            
            # Simulate cache update logic
            loader = FlexibleDataLoader(str(api_dir))
            loaded_data = {}
            for provider_id, config in provider_configs.items():
                data = loader.load_data_with_flexible_schema(provider_id, config)
                if data:
                    loaded_data[provider_id] = data
            
            end_time = time.time()
            memory_after = psutil.Process().memory_info().rss
            
            update_time = end_time - start_time
            memory_used = (memory_after - memory_before) / (1024 * 1024)  # MB
            
            assert update_time < 10.0, f"Cache update took {update_time}s"
            assert memory_used < 100.0, f"Memory usage too high: {memory_used}MB"
            assert len(loaded_data) == len(provider_configs)
    
    def test_cache_access_performance(self, temp_dir):
        """Test performance of cache access operations."""
        # Create large mock cache data
        large_cache_data = {
            'raw_data': {
                f'provider_{i}': {
                    f'app_{j}': {
                        'score': j * 10,
                        'category': f'cat_{j % 5}',
                        'timestamp': f'2024-01-{j % 30 + 1:02d}T10:00:00'
                    }
                    for j in range(1000)  # 1000 apps per provider
                }
                for i in range(10)  # 10 providers
            },
            'rule_results': {
                'test_rule': {
                    f'provider_{i}': {
                        f'app_{j}': {'result': j % 2}
                        for j in range(1000)
                    }
                    for i in range(10)
                }
            }
        }
        
        # Mock get_aggregated_data function
        with patch('data_aggregator.get_aggregated_data') as mock_get_data:
            mock_get_data.return_value = large_cache_data
            
            # Test multiple cache access calls
            access_times = []
            
            for _ in range(10):
                start_time = time.time()
                data = get_aggregated_data()
                end_time = time.time()
                
                access_times.append(end_time - start_time)
                assert data is not None
                assert 'raw_data' in data
            
            # Verify performance
            avg_access_time = sum(access_times) / len(access_times)
            max_access_time = max(access_times)
            
            assert avg_access_time < 0.1, f"Average access time too slow: {avg_access_time}s"
            assert max_access_time < 0.5, f"Max access time too slow: {max_access_time}s"


class TestMigrationPerformance:
    """Test performance of migration operations."""
    
    def test_migration_detection_performance(self, temp_dir):
        """Test performance of migration detection with large schemas."""
        api_dir = temp_dir / "api_test"
        api_dir.mkdir()
        
        # Create large dataframes for before/after comparison
        large_before = pd.DataFrame({
            **{f'metric_{i}': [j + i for j in range(5000)] for i in range(50)},
            'app_id': [f'App_{i}' for i in range(5000)]
        })
        
        large_after = large_before.copy()
        # Add some new columns
        for i in range(5):
            large_after[f'new_metric_{i}'] = [j * i for j in range(5000)]
        
        # Save to files
        before_file = api_dir / "before_large.csv"
        after_file = api_dir / "after_large.csv"
        large_before.to_csv(before_file, index=False)
        large_after.to_csv(after_file, index=False)
        
        # Test schema detection performance
        start_time = time.time()
        before_schema = schema_detector.detect_schema(str(before_file), "large_provider")
        before_time = time.time() - start_time
        
        start_time = time.time()
        after_schema = schema_detector.detect_schema(str(after_file), "large_provider")
        after_time = time.time() - start_time
        
        assert before_schema is not None
        assert after_schema is not None
        assert before_time < 5.0, f"Before schema detection took {before_time}s"
        assert after_time < 5.0, f"After schema detection took {after_time}s"
        
        # Test migration detection performance
        from schema_migration import SchemaMigrator
        migrator = SchemaMigrator(str(api_dir))
        
        start_time = time.time()
        changes = migrator.detect_schema_changes("large_provider", before_schema, after_schema)
        detection_time = time.time() - start_time
        
        assert detection_time < 2.0, f"Migration detection took {detection_time}s"
        assert len(changes) > 0  # Should detect the new columns
    
    def test_auto_migration_performance(self, temp_dir):
        """Test performance of auto-migration process."""
        api_dir = temp_dir / "api_test"
        api_dir.mkdir()
        data_dir = api_dir / "data_mock"
        data_dir.mkdir()
        
        # Create multiple providers for migration testing
        provider_configs = {}
        for i in range(5):  # 5 providers
            df = pd.DataFrame({
                'app_id': [f'App_{j}' for j in range(100)],
                'score': [j % 100 for j in range(100)]
            })
            
            csv_file = data_dir / f"provider_{i}.csv"
            df.to_csv(csv_file, index=False)
            
            provider_configs[f"provider_{i}_v1"] = {
                "connector_type": "csv",
                "file_path": f"data_mock/provider_{i}.csv"
            }
        
        # Measure auto-migration performance
        start_time = time.time()
        results = auto_migrate_all_providers(provider_configs, str(api_dir))
        end_time = time.time()
        
        migration_time = end_time - start_time
        
        assert len(results) == 5
        assert migration_time < 10.0, f"Auto-migration took {migration_time}s"
        
        # Verify all providers processed successfully
        for provider_id, success in results.items():
            assert success is True, f"Provider {provider_id} failed migration"


class TestConcurrencyPerformance:
    """Test performance under concurrent load."""
    
    def test_concurrent_data_loading(self, temp_dir, sample_csv_data):
        """Test concurrent data loading performance."""
        api_dir = temp_dir / "api_test"
        api_dir.mkdir()
        data_dir = api_dir / "data_mock"
        data_dir.mkdir()
        
        # Create CSV file
        df = sample_csv_data['code_quality_v1']
        csv_file = data_dir / "concurrent_test.csv"
        df.to_csv(csv_file, index=False)
        
        loader = FlexibleDataLoader(str(api_dir))
        config = {
            'connector_type': 'csv',
            'file_path': 'data_mock/concurrent_test.csv'
        }
        
        # Test concurrent loading
        results = []
        errors = []
        
        def load_data():
            try:
                start_time = time.time()
                data = loader.load_data_with_flexible_schema('concurrent_provider', config)
                end_time = time.time()
                results.append({
                    'success': data is not None,
                    'time': end_time - start_time,
                    'records': len(data) if data else 0
                })
            except Exception as e:
                errors.append(str(e))
        
        # Start multiple concurrent loads
        threads = []
        start_time = time.time()
        
        for _ in range(10):  # 10 concurrent requests
            thread = threading.Thread(target=load_data)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=10)
        
        total_time = time.time() - start_time
        
        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10
        assert total_time < 15.0, f"Concurrent loading took {total_time}s"
        
        # Verify all loads succeeded
        for result in results:
            assert result['success'] is True
            assert result['time'] < 5.0  # Individual load time
            assert result['records'] > 0
    
    def test_concurrent_schema_detection(self, temp_dir):
        """Test concurrent schema detection performance."""
        api_dir = temp_dir / "api_test"
        api_dir.mkdir()
        
        # Create test file
        df = pd.DataFrame({
            'app_id': [f'App_{i}' for i in range(1000)],
            'score': [i % 100 for i in range(1000)],
            'category': [f'Cat_{i % 10}' for i in range(1000)]
        })
        csv_file = api_dir / "schema_test.csv"
        df.to_csv(csv_file, index=False)
        
        # Test concurrent schema detection
        results = []
        errors = []
        
        def detect_schema():
            try:
                start_time = time.time()
                schema = schema_detector.detect_schema(str(csv_file), 'schema_provider')
                end_time = time.time()
                results.append({
                    'success': schema is not None,
                    'time': end_time - start_time,
                    'columns': len(schema.columns) if schema else 0
                })
            except Exception as e:
                errors.append(str(e))
        
        # Start concurrent detection
        threads = []
        start_time = time.time()
        
        for _ in range(5):  # 5 concurrent detections
            thread = threading.Thread(target=detect_schema)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join(timeout=10)
        
        total_time = time.time() - start_time
        
        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5
        assert total_time < 10.0, f"Concurrent detection took {total_time}s"
        
        # Verify consistency
        column_counts = [r['columns'] for r in results]
        assert all(count == column_counts[0] for count in column_counts), "Inconsistent schema detection"


@pytest.mark.slow
@pytest.mark.performance
class TestSystemPerformance:
    """System-wide performance tests."""
    
    def test_system_scalability(self, temp_dir):
        """Test system performance with increasing data sizes."""
        api_dir = temp_dir / "api_test"
        api_dir.mkdir()
        data_dir = api_dir / "data_mock"
        data_dir.mkdir()
        
        loader = FlexibleDataLoader(str(api_dir))
        
        # Test different data sizes
        sizes = [100, 1000, 5000]  # Number of records
        performance_results = {}
        
        for size in sizes:
            # Create dataset of specified size
            df = pd.DataFrame({
                'app_id': [f'App_{i}' for i in range(size)],
                'performance_score': [i % 100 for i in range(size)],
                'security_score': [(i * 2) % 100 for i in range(size)],
                'category': [f'Cat_{i % 20}' for i in range(size)],
                'timestamp': pd.date_range('2024-01-01', periods=size, freq='H')
            })
            
            csv_file = data_dir / f"scalability_{size}.csv"
            df.to_csv(csv_file, index=False)
            
            config = {
                'connector_type': 'csv',
                'file_path': f"data_mock/scalability_{size}.csv"
            }
            
            # Measure performance
            start_time = time.time()
            memory_before = psutil.Process().memory_info().rss
            
            data = loader.load_data_with_flexible_schema(f'scalability_{size}', config)
            
            end_time = time.time()
            memory_after = psutil.Process().memory_info().rss
            
            performance_results[size] = {
                'load_time': end_time - start_time,
                'memory_used': (memory_after - memory_before) / (1024 * 1024),  # MB
                'records_loaded': len(data) if data else 0
            }
            
            assert data is not None
            assert len(data) == size
        
        # Analyze scaling characteristics
        for size, metrics in performance_results.items():
            records_per_second = metrics['records_loaded'] / metrics['load_time']
            memory_per_record = metrics['memory_used'] / metrics['records_loaded'] if metrics['records_loaded'] > 0 else 0
            
            # Performance should be reasonable across all sizes
            assert records_per_second > 100, f"Too slow at size {size}: {records_per_second} records/sec"
            assert memory_per_record < 1.0, f"Too much memory at size {size}: {memory_per_record} MB/record"
        
        # Verify scalability (linear or better)
        small_time = performance_results[100]['load_time']
        large_time = performance_results[5000]['load_time']
        time_ratio = large_time / small_time
        size_ratio = 5000 / 100
        
        # Time should scale reasonably (not more than 2x the size ratio)
        assert time_ratio < size_ratio * 2, f"Poor time scalability: {time_ratio} vs {size_ratio}"
    
    def test_memory_efficiency(self, temp_dir):
        """Test memory efficiency of the system."""
        api_dir = temp_dir / "api_test"
        api_dir.mkdir()
        data_dir = api_dir / "data_mock"
        data_dir.mkdir()
        
        # Create moderately large dataset
        df = pd.DataFrame({
            'app_id': [f'App_{i}' for i in range(2000)],
            'metrics': [{'score': i, 'category': f'Cat_{i % 10}'} for i in range(2000)]
        })
        
        csv_file = data_dir / "memory_test.csv"
        df.to_csv(csv_file, index=False)
        
        # Monitor memory usage during loading
        initial_memory = psutil.Process().memory_info().rss / (1024 * 1024)  # MB
        
        loader = FlexibleDataLoader(str(api_dir))
        config = {
            'connector_type': 'csv',
            'file_path': 'data_mock/memory_test.csv'
        }
        
        data = loader.load_data_with_flexible_schema('memory_provider', config)
        
        peak_memory = psutil.Process().memory_info().rss / (1024 * 1024)  # MB
        memory_increase = peak_memory - initial_memory
        
        assert data is not None
        assert len(data) == 2000
        assert memory_increase < 50.0, f"Memory increase too large: {memory_increase}MB"
        
        # Memory per record should be reasonable
        memory_per_record = memory_increase / len(data)
        assert memory_per_record < 0.025, f"Memory per record too high: {memory_per_record}MB"