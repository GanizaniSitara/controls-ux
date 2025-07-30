from .base_provider import BaseFitnessProvider, Status
from typing import Dict, Any, Optional
import logging
import os
import csv

logger = logging.getLogger(__name__)

class ResilienceProvider(BaseFitnessProvider):
    """Provides fitness data related to system resilience based on CSV data."""

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
        return "resilience_v1"

    def get_fitness_data(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        """Returns resilience metrics read directly from the mock CSV file."""
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
            failover_success_rate = float(raw_data.get('FailoverSuccessRate', 0))
            recovery_time_minutes = float(raw_data.get('RecoveryTimeMinutes', 0))
            resiliency_score = float(raw_data.get('ResiliencyScore', 0))
            incident_count = int(raw_data.get('IncidentCount', 0))
            
            # Determine status based on the metrics
            status: Status = 'healthy'
            warnings = []
            
            if failover_success_rate < 95:
                status = 'critical'
                warnings.append(f"Failover success rate is below critical threshold: {failover_success_rate}%")
            elif failover_success_rate < 98:
                status = 'warning'
                warnings.append(f"Failover success rate needs improvement: {failover_success_rate}%")
                
            if recovery_time_minutes > 60:
                if status != 'critical':
                    status = 'warning'
                warnings.append(f"Recovery time is high: {recovery_time_minutes} minutes")
            
            if incident_count > 5:
                if status != 'critical':
                    status = 'warning'
                warnings.append(f"High number of incidents: {incident_count}")
            
            details = {
                "failover_success_rate": failover_success_rate,
                "recovery_time_minutes": recovery_time_minutes,
                "resiliency_score": resiliency_score,
                "incident_count": incident_count,
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
