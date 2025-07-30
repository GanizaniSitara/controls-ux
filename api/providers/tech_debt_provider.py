from .base_provider import BaseFitnessProvider, Status
from typing import Dict, Any, Optional
import logging
import os
import csv

logger = logging.getLogger(__name__)

class TechDebtProvider(BaseFitnessProvider):
    """Provides fitness data related to technical debt based on CSV data."""

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
        return "tech_debt_v1"

    def get_fitness_data(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        """Returns technical debt metrics read directly from the mock CSV file."""
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
            tech_debt_ratio = float(raw_data.get('TechDebtRatio', 0))
            legacy_code_percentage = float(raw_data.get('LegacyCodePercentage', 0))
            refactoring_needed = raw_data.get('RefactoringNeeded', 'low')
            outdated_dependencies = int(raw_data.get('OutdatedDependencies', 0))
            
            # Determine status based on the metrics
            status: Status = 'healthy'
            warnings = []
            
            if tech_debt_ratio > 25 or legacy_code_percentage > 40:
                status = 'critical'
                warnings.append(f"Critical technical debt ratio: {tech_debt_ratio}%")
            elif tech_debt_ratio > 15 or legacy_code_percentage > 25:
                status = 'warning'
                warnings.append(f"Technical debt needs attention: {tech_debt_ratio}%")
                
            if refactoring_needed.lower() == 'high':
                if status != 'critical':
                    status = 'warning'
                warnings.append("High refactoring needs identified")
            
            if outdated_dependencies > 10:
                if status != 'critical':
                    status = 'warning'
                warnings.append(f"High number of outdated dependencies: {outdated_dependencies}")
            
            details = {
                "tech_debt_ratio": tech_debt_ratio,
                "legacy_code_percentage": legacy_code_percentage,
                "refactoring_needed": refactoring_needed,
                "outdated_dependencies": outdated_dependencies,
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
