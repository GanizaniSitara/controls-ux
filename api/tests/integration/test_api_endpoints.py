"""
Integration tests for API endpoints.

Tests the FastAPI endpoints including schema management, migration endpoints,
and data access endpoints.
"""

import pytest
import json
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
from httpx import AsyncClient
from fastapi.testclient import TestClient

# Import the FastAPI app
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def async_client():
    """Create an async test client for the FastAPI app."""
    return AsyncClient(app=app, base_url="http://test")


class TestBasicEndpoints:
    """Test basic API endpoints."""
    
    def test_root_endpoint(self, client):
        """Test the root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Fitness Functions API" in data["message"]
    
    def test_graphql_endpoint_accessible(self, client):
        """Test that GraphQL endpoint is accessible."""
        response = client.get("/graphql")
        
        # GraphQL endpoint should return something (even if not a valid query)
        assert response.status_code in [200, 400]  # 400 is OK for GET without query


class TestCacheEndpoints:
    """Test cache-related endpoints."""
    
    @patch('app.get_aggregated_data')
    def test_cache_debug_endpoint(self, mock_get_data, client):
        """Test the cache debug endpoint."""
        mock_get_data.return_value = {"test": "data"}
        
        response = client.get("/api/cache-debug")
        
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "cache_content" in data
        assert data["cache_content"] == {"test": "data"}
    
    @patch('app.get_aggregated_data')
    def test_aggregated_data_endpoint(self, mock_get_data, client):
        """Test the aggregated data endpoint."""
        mock_get_data.return_value = {"raw_data": {"provider1": {"app1": {"score": 85}}}}
        
        response = client.get("/aggregated-data")
        
        assert response.status_code == 200
        data = response.json()
        assert "raw_data" in data
        assert data["raw_data"]["provider1"]["app1"]["score"] == 85
    
    @patch('app.get_aggregated_data')
    def test_aggregated_data_endpoint_error(self, mock_get_data, client):
        """Test the aggregated data endpoint with error."""
        mock_get_data.side_effect = Exception("Cache error")
        
        response = client.get("/aggregated-data")
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Internal server error" in data["detail"]
    
    @patch('app.get_cache_health')
    def test_cache_health_endpoint(self, mock_get_health, client):
        """Test the cache health endpoint."""
        mock_get_health.return_value = {
            "last_update": "2025-01-15T10:00:00",
            "cache_age_seconds": 300,
            "cache_size": 5
        }
        
        response = client.get("/api/cache-health")
        
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "status" in data
        assert "message" in data
        assert data["cache_age_seconds"] == 300
    
    @patch('app.get_cache_health')
    def test_cache_health_endpoint_warning(self, mock_get_health, client):
        """Test cache health endpoint with warning status."""
        mock_get_health.return_value = {
            "last_update": "2025-01-15T10:00:00",
            "cache_age_seconds": 400,  # > 5 minutes
            "cache_size": 5
        }
        
        response = client.get("/api/cache-health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "warning"
        assert "6.7 minutes old" in data["message"]


class TestApplicationEndpoints:
    """Test application-related endpoints."""
    
    @patch('app.get_application_details')
    def test_application_details_success(self, mock_get_details, client):
        """Test getting application details successfully."""
        mock_get_details.return_value = {
            "appId": "test-app",
            "raw_data": {"provider1": {"score": 85}},
            "provider_results": {}
        }
        
        response = client.get("/api/application-details/test-app")
        
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "details" in data
        assert data["details"]["appId"] == "test-app"
    
    @patch('app.get_application_details')
    def test_application_details_not_found(self, mock_get_details, client):
        """Test getting application details when not found."""
        mock_get_details.return_value = None
        
        response = client.get("/api/application-details/nonexistent-app")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Details not found" in data["detail"]
    
    @patch('app.get_application_details')
    def test_application_details_error(self, mock_get_details, client):
        """Test application details endpoint with error."""
        mock_get_details.side_effect = Exception("Database error")
        
        response = client.get("/api/application-details/test-app")
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Internal server error" in data["detail"]


class TestSchemaEndpoints:
    """Test schema management endpoints."""
    
    @patch('app.FlexibleDataLoader')
    @patch('app.PROVIDER_CONFIGS', {'test_provider': {'connector_type': 'csv'}})
    def test_schema_report_endpoint(self, mock_loader_class, client):
        """Test the schema report endpoint."""
        mock_loader = MagicMock()
        mock_loader.get_schema_report.return_value = {
            "summary": {
                "valid_schemas": 5,
                "schema_warnings": 1,
                "schema_errors": 0
            },
            "providers": {}
        }
        mock_loader_class.return_value = mock_loader
        
        response = client.get("/api/schema-report")
        
        assert response.status_code == 200
        data = response.json()
        assert "endpoint_timestamp" in data
        assert "summary" in data
        assert data["summary"]["valid_schemas"] == 5
    
    @patch('app.FlexibleDataLoader')
    @patch('app.PROVIDER_CONFIGS', {'observability_v1': {'connector_type': 'csv', 'file_path': 'test.csv'}})
    def test_validate_schema_endpoint_success(self, mock_loader_class, client):
        """Test schema validation endpoint successfully."""
        mock_loader = MagicMock()
        mock_loader.validate_data_against_schema.return_value = {
            "is_valid": True,
            "warnings": [],
            "errors": []
        }
        mock_loader_class.return_value = mock_loader
        
        response = client.get("/api/validate-schema/observability_v1")
        
        assert response.status_code == 200
        data = response.json()
        assert "endpoint_timestamp" in data
        assert data["is_valid"] is True
    
    @patch('app.PROVIDER_CONFIGS', {})
    def test_validate_schema_endpoint_provider_not_found(self, client):
        """Test schema validation with non-existent provider."""
        response = client.get("/api/validate-schema/nonexistent_provider")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"]
    
    @patch('app.PROVIDER_CONFIGS', {'test_provider': {'connector_type': 'rest'}})
    def test_validate_schema_endpoint_non_csv(self, client):
        """Test schema validation with non-CSV provider."""
        response = client.get("/api/validate-schema/test_provider")
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "only supported for CSV" in data["detail"]


class TestMigrationEndpoints:
    """Test migration management endpoints."""
    
    @patch('app.get_migrator')
    def test_pending_migrations_endpoint_empty(self, mock_get_migrator, client):
        """Test pending migrations endpoint with no migrations."""
        mock_migrator = MagicMock()
        mock_migrator.get_pending_migrations.return_value = []
        mock_get_migrator.return_value = mock_migrator
        
        response = client.get("/api/migrations/pending")
        
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert data["pending_count"] == 0
        assert data["migrations"] == []
    
    @patch('app.get_migrator')
    def test_pending_migrations_endpoint_with_migrations(self, mock_get_migrator, client):
        """Test pending migrations endpoint with pending migrations."""
        mock_plan = MagicMock()
        mock_plan.provider_id = "test_provider"
        mock_plan.created_at = "2025-01-15T10:00:00"
        mock_plan.migration_steps = [
            MagicMock(step_type="add_column", description="Add test column")
        ]
        
        mock_migrator = MagicMock()
        mock_migrator.get_pending_migrations.return_value = ["/path/to/migration_test_123_456.json"]
        mock_migrator.load_migration_plan.return_value = mock_plan
        mock_get_migrator.return_value = mock_migrator
        
        response = client.get("/api/migrations/pending")
        
        assert response.status_code == 200
        data = response.json()
        assert data["pending_count"] == 1
        assert len(data["migrations"]) == 1
        assert data["migrations"][0]["provider_id"] == "test_provider"
    
    @patch('app.get_migrator')
    @patch('app.PROVIDER_CONFIGS', {'test_provider': {'connector_type': 'csv', 'file_path': 'test.csv'}})
    def test_create_migration_plan_success(self, mock_get_migrator, client):
        """Test creating migration plan successfully."""
        mock_plan = MagicMock()
        mock_plan.migration_steps = [
            MagicMock(step_type="add_column", description="Add test column")
        ]
        
        mock_migrator = MagicMock()
        mock_migrator.create_migration_plan.return_value = mock_plan
        mock_migrator.save_migration_plan.return_value = "/path/to/plan.json"
        mock_get_migrator.return_value = mock_migrator
        
        response = client.post("/api/migrations/create/test_provider")
        
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert data["provider_id"] == "test_provider"
        assert data["migration_needed"] is True
        assert data["steps_count"] == 1
    
    @patch('app.get_migrator')
    @patch('app.PROVIDER_CONFIGS', {'test_provider': {'connector_type': 'csv', 'file_path': 'test.csv'}})
    def test_create_migration_plan_no_changes(self, mock_get_migrator, client):
        """Test creating migration plan when no changes detected."""
        mock_migrator = MagicMock()
        mock_migrator.create_migration_plan.return_value = None
        mock_get_migrator.return_value = mock_migrator
        
        response = client.post("/api/migrations/create/test_provider")
        
        assert response.status_code == 200
        data = response.json()
        assert data["migration_needed"] is False
        assert data["message"] == "No schema changes detected"
    
    @patch('app.PROVIDER_CONFIGS', {})
    def test_create_migration_plan_provider_not_found(self, client):
        """Test creating migration plan for non-existent provider."""
        response = client.post("/api/migrations/create/nonexistent_provider")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]
    
    @patch('app.get_migrator')
    @patch('app.PROVIDER_CONFIGS', {'test_provider': {'connector_type': 'csv', 'file_path': 'test.csv'}})
    def test_execute_migration_success(self, mock_get_migrator, client):
        """Test executing migration successfully."""
        mock_plan = MagicMock()
        mock_plan.executed_at = "2025-01-15T10:30:00"
        mock_plan.error_message = None
        
        mock_migrator = MagicMock()
        mock_migrator.get_pending_migrations.return_value = ["/path/to/migration_test_provider_123_456.json"]
        mock_migrator.load_migration_plan.return_value = mock_plan
        mock_migrator.execute_migration_plan.return_value = True
        mock_get_migrator.return_value = mock_migrator
        
        response = client.post("/api/migrations/execute/test_provider?backup=true")
        
        assert response.status_code == 200
        data = response.json()
        assert data["provider_id"] == "test_provider"
        assert data["migration_executed"] is True
        assert data["backup_created"] is True
        assert data["executed_at"] == "2025-01-15T10:30:00"
    
    @patch('app.get_migrator')
    @patch('app.PROVIDER_CONFIGS', {'test_provider': {'connector_type': 'csv', 'file_path': 'test.csv'}})
    def test_execute_migration_no_pending(self, mock_get_migrator, client):
        """Test executing migration when no pending migrations exist."""
        mock_migrator = MagicMock()
        mock_migrator.get_pending_migrations.return_value = []
        mock_get_migrator.return_value = mock_migrator
        
        response = client.post("/api/migrations/execute/test_provider")
        
        assert response.status_code == 404
        data = response.json()
        assert "No pending migration found" in data["detail"]
    
    @patch('app.get_migrator')
    @patch('app.PROVIDER_CONFIGS', {'test_provider': {'connector_type': 'csv', 'file_path': 'test.csv'}})
    def test_execute_migration_failure(self, mock_get_migrator, client):
        """Test executing migration with failure."""
        mock_plan = MagicMock()
        mock_plan.executed_at = "2025-01-15T10:30:00"
        mock_plan.error_message = "Migration failed"
        
        mock_migrator = MagicMock()
        mock_migrator.get_pending_migrations.return_value = ["/path/to/migration_test_provider_123_456.json"]
        mock_migrator.load_migration_plan.return_value = mock_plan
        mock_migrator.execute_migration_plan.return_value = False
        mock_get_migrator.return_value = mock_migrator
        
        response = client.post("/api/migrations/execute/test_provider")
        
        assert response.status_code == 200
        data = response.json()
        assert data["migration_executed"] is False
        assert data["error_message"] == "Migration failed"


@pytest.mark.integration
@pytest.mark.api
class TestAPIIntegration:
    """Integration tests for complete API workflows."""
    
    @patch('app.get_aggregated_data')
    @patch('app.get_cache_health')
    def test_full_cache_workflow(self, mock_health, mock_data, client):
        """Test complete cache-related workflow."""
        # Setup mocks
        mock_data.return_value = {"test": "data"}
        mock_health.return_value = {"cache_age_seconds": 60, "cache_size": 3}
        
        # Test cache health
        health_response = client.get("/api/cache-health")
        assert health_response.status_code == 200
        
        # Test cache debug
        debug_response = client.get("/api/cache-debug")
        assert debug_response.status_code == 200
        
        # Test aggregated data
        data_response = client.get("/aggregated-data")
        assert data_response.status_code == 200
        
        # Verify all responses have timestamps
        for response in [health_response, debug_response]:
            data = response.json()
            assert "timestamp" in data
    
    @patch('app.get_migrator')
    @patch('app.PROVIDER_CONFIGS', {'test_provider': {'connector_type': 'csv', 'file_path': 'test.csv'}})
    def test_full_migration_workflow(self, mock_get_migrator, client):
        """Test complete migration workflow."""
        # Setup mocks
        mock_plan = MagicMock()
        mock_plan.provider_id = "test_provider"
        mock_plan.migration_steps = [MagicMock(step_type="add_column", description="Add column")]
        mock_plan.executed_at = None
        
        mock_migrator = MagicMock()
        mock_migrator.create_migration_plan.return_value = mock_plan
        mock_migrator.save_migration_plan.return_value = "/path/plan.json"
        mock_migrator.get_pending_migrations.return_value = ["/path/plan.json"]
        mock_migrator.load_migration_plan.return_value = mock_plan
        mock_migrator.execute_migration_plan.return_value = True
        mock_get_migrator.return_value = mock_migrator
        
        # 1. Create migration plan
        create_response = client.post("/api/migrations/create/test_provider")
        assert create_response.status_code == 200
        create_data = create_response.json()
        assert create_data["migration_needed"] is True
        
        # 2. Check pending migrations
        pending_response = client.get("/api/migrations/pending")
        assert pending_response.status_code == 200
        pending_data = pending_response.json()
        assert pending_data["pending_count"] == 1
        
        # 3. Execute migration
        mock_plan.executed_at = "2025-01-15T10:30:00"
        execute_response = client.post("/api/migrations/execute/test_provider")
        assert execute_response.status_code == 200
        execute_data = execute_response.json()
        assert execute_data["migration_executed"] is True
    
    def test_error_handling_consistency(self, client):
        """Test that error responses have consistent format."""
        # Test various error scenarios
        error_responses = [
            client.get("/api/application-details/nonexistent"),
            client.get("/api/validate-schema/nonexistent"),
            client.post("/api/migrations/create/nonexistent"),
            client.post("/api/migrations/execute/nonexistent")
        ]
        
        for response in error_responses:
            assert response.status_code >= 400
            data = response.json()
            assert "detail" in data
            assert isinstance(data["detail"], str)
            assert len(data["detail"]) > 0


@pytest.mark.integration
@pytest.mark.slow
class TestAPIPerformance:
    """Performance-related integration tests."""
    
    @patch('app.get_aggregated_data')
    def test_large_data_response(self, mock_get_data, client):
        """Test API performance with large data responses."""
        # Create large mock data
        large_data = {
            "raw_data": {
                f"provider_{i}": {
                    f"app_{j}": {"score": j * 10}
                    for j in range(100)
                }
                for i in range(10)
            }
        }
        mock_get_data.return_value = large_data
        
        import time
        start_time = time.time()
        response = client.get("/aggregated-data")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 5.0  # Should respond within 5 seconds
        
        data = response.json()
        assert "raw_data" in data
    
    def test_concurrent_requests(self, client):
        """Test handling multiple concurrent requests."""
        import threading
        import time
        
        results = []
        
        def make_request():
            try:
                response = client.get("/")
                results.append(response.status_code)
            except Exception as e:
                results.append(str(e))
        
        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=10)
        
        # Check results
        assert len(results) == 10
        assert all(result == 200 for result in results)