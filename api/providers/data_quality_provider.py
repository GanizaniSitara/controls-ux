from .base_provider import BaseFitnessProvider, Status
from typing import Dict, Any, Optional
import logging
import os
import csv

logger = logging.getLogger(__name__)

class DataQualityProvider(BaseFitnessProvider):
    """Provides fitness data related to data quality based on CSV data."""

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
        return "data_quality_v1"

    def get_fitness_data(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        """Returns data quality metrics read directly from the mock CSV file."""
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
            data_accuracy = float(raw_data.get('DataAccuracy', 0))
            data_consistency = float(raw_data.get('DataConsistency', 0))
            data_completeness = float(raw_data.get('DataCompleteness', 0))
            
            # Calculate an overall data quality score (simple average)
            overall_score = (data_accuracy + data_consistency + data_completeness) / 3
            
            # Determine status based on the overall score
            status: Status = 'healthy'
            warnings = []
            
            if overall_score < 80:
                status = 'critical'
                warnings.append(f"Overall data quality score is critical: {overall_score:.1f}%")
            elif overall_score < 90:
                status = 'warning'
                warnings.append(f"Overall data quality score needs improvement: {overall_score:.1f}%")
                
            if data_accuracy < 85:
                warnings.append(f"Data accuracy below threshold: {data_accuracy}%")
            if data_consistency < 85:
                warnings.append(f"Data consistency below threshold: {data_consistency}%")
            if data_completeness < 85:
                warnings.append(f"Data completeness below threshold: {data_completeness}%")
            
            details = {
                "data_accuracy": data_accuracy,
                "data_consistency": data_consistency,
                "data_completeness": data_completeness,
                "overall_score": overall_score,
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
