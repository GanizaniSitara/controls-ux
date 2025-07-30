from .base_provider import BaseFitnessProvider, Status
from typing import Dict, Any, Optional
import logging
import os
import csv

logger = logging.getLogger(__name__)

class ArchitectureProvider(BaseFitnessProvider):
    """Provides fitness data related to architecture compliance based on CSV data."""

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
        return "architecture_v1"

    def get_fitness_data(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        """Returns architecture compliance metrics read directly from the mock CSV file."""
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
            architecture_compliance = float(raw_data.get('ArchitectureCompliance', 0))
            modernization_score = float(raw_data.get('ModernizationScore', 0))
            pattern_adherence = raw_data.get('PatternAdherence', 'medium')
            technical_debt = float(raw_data.get('TechnicalDebt', 0))
            
            # Determine status based on the metrics
            status: Status = 'healthy'
            warnings = []
            
            if architecture_compliance < 75:
                status = 'critical'
                warnings.append(f"Architecture compliance is critical: {architecture_compliance}%")
            elif architecture_compliance < 85:
                status = 'warning'
                warnings.append(f"Architecture compliance needs improvement: {architecture_compliance}%")
                
            if modernization_score < 65:
                if status != 'critical':
                    status = 'warning'
                warnings.append(f"Modernization score is low: {modernization_score}/100")
            
            if pattern_adherence.lower() == 'low':
                if status != 'critical':
                    status = 'warning'
                warnings.append("Low pattern adherence identified")
            
            if technical_debt > 30:
                if status != 'critical':
                    status = 'warning'
                warnings.append(f"High technical debt score: {technical_debt}")
            
            details = {
                "architecture_compliance": architecture_compliance,
                "modernization_score": modernization_score,
                "pattern_adherence": pattern_adherence,
                "technical_debt": technical_debt,
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
