from .base_provider import BaseFitnessProvider, Status
from typing import Dict, Any, Optional
import logging
import os
import csv

logger = logging.getLogger(__name__)

class WorkloadPlacementProvider(BaseFitnessProvider):
    """Provides fitness data related to workload placement and optimization based on CSV data."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the provider. Config is currently unused as we read directly from mock.
        """
        self.config = config
        # Get CSV file path from settings.ini
        self.mock_file_path = self.get_csv_filepath()
        logger.info(f"[{self.provider_id}] Initialized to read from mock file: {self.mock_file_path}")

    @property
    def provider_id(self) -> str:
        return "workload_placement_v1"

    def get_fitness_data(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        """Returns workload placement metrics read directly from the mock CSV file."""
        app_id = app_config.get('app_id')
        if not app_id:
            logger.warning(f"[{self.provider_id}] app_id missing in app_config. Cannot fetch specific data.")
            return {"status": "unknown", "details": {"error": "app_id missing."}}
        
        # Read data directly from the mock CSV file
        raw_data: Optional[Dict[str, Any]] = None
        try:
            # Use CSV connector to fetch data for this app
            connector = self.get_connector()
            if not connector:
                logger.error(f"[{self.provider_id}] Failed to create connector.")
                return {"status": "unknown", "details": {"error": "Failed to create connector."}}
            
            raw_data = connector.fetch_data(app_config)
            if not raw_data:
                logger.warning(f"[{self.provider_id}] No data found for app {app_id}")
                return {"status": "unknown", "details": {"error": f"No data found for app {app_id}"}}
            
            # Extract important metrics
            cloud_optimization = float(raw_data.get('CloudOptimization', 0))
            resource_utilization = float(raw_data.get('ResourceUtilization', 0))
            environment_placement = raw_data.get('EnvironmentPlacement', 'unknown')
            cost_efficiency = float(raw_data.get('CostEfficiency', 0))
            
            # Determine status based on the metrics
            status: Status = 'healthy'
            warnings = []
            
            if cloud_optimization < 75 or cost_efficiency < 75:
                status = 'critical'
                warnings.append(f"Cloud optimization is critical: {cloud_optimization}%")
            elif cloud_optimization < 85 or cost_efficiency < 85:
                status = 'warning'
                warnings.append(f"Cloud optimization needs improvement: {cloud_optimization}%")
                
            if resource_utilization < 70:
                if status != 'critical':
                    status = 'warning'
                warnings.append(f"Low resource utilization: {resource_utilization}%")
            
            if environment_placement.lower() == 'suboptimal':
                if status != 'critical':
                    status = 'warning'
                warnings.append("Suboptimal environment placement identified")
            
            details = {
                "cloud_optimization": cloud_optimization,
                "resource_utilization": resource_utilization,
                "environment_placement": environment_placement,
                "cost_efficiency": cost_efficiency,
                "warnings": warnings
            }
            
            logger.info(f"[{self.provider_id}] Processed mock data for app: {app_id}, Status: {status}")
            return {
                "status": status,
                "details": details
            }
        except ValueError as e:
            logger.error(f"[{self.provider_id}] Error converting data types for app {app_id}: {e}. Data: {raw_data}", exc_info=True)
            return {"status": "unknown", "details": {"error": f"Error processing data types: {e}"}}
        except Exception as e:
            logger.error(f"[{self.provider_id}] Error processing raw data for app {app_id}: {e}. Data: {raw_data}", exc_info=True)
            return {"status": "unknown", "details": {"error": f"Error processing data: {e}"}}
