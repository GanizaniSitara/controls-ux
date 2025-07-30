from .base_provider import BaseFitnessProvider, Status
from typing import Dict, Any, Optional
import logging
import os
import csv

logger = logging.getLogger(__name__)

class SecurityProvider(BaseFitnessProvider):
    """Provides fitness data related to security based on mock CSV data."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the provider. Config is currently unused.
        """
        self.config = config
        # Get CSV file path from settings.ini
        self.mock_file_path = self.get_csv_filepath()
        logger.info(f"[{self.provider_id}] Initialized to read from mock file: {self.mock_file_path}")

    @property
    def provider_id(self) -> str:
        return "security_v1"

    def get_fitness_data(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        """Returns security data read directly from the mock CSV file."""

        app_id = app_config.get('app_id')
        if not app_id:
            logger.warning(f"[{self.provider_id}] app_id missing in app_config.")
            return {"status": "unknown", "details": {"error": "app_id missing."}}

        # Read data directly from the mock CSV file
        raw_data: Optional[Dict[str, Any]] = None
        try:
            with open(self.mock_file_path, mode='r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row.get('ApplicationName') == app_id:
                        raw_data = row
                        break
        except FileNotFoundError:
            logger.error(f"[{self.provider_id}] Mock data file not found: {self.mock_file_path}")
            return {"status": "unknown", "details": {"error": f"Mock data file not found: {self.mock_file_path}"}}
        except Exception as e:
            logger.error(f"[{self.provider_id}] Error reading mock data file {self.mock_file_path}: {e}", exc_info=True)
            return {"status": "unknown", "details": {"error": f"Error reading mock data file: {e}"}}

        if raw_data is None:
            logger.warning(f"[{self.provider_id}] No data found for app_id: {app_id} in {self.mock_file_path}")
            return {"status": "not_found", "details": {"message": f"No data found for app_id {app_id} in mock file."}}

        # --- Determine Status and Details from raw_data ---
        # Assuming columns 'CriticalVulnerabilities', 'HighSCAIssues' based on previous logic
        try:
            vuln_critical = int(raw_data.get('CriticalVulnerabilities', 0))
            sca_high = int(raw_data.get('HighSCAIssues', 0))

            # Example status logic
            status: Status = 'healthy'
            warnings = []
            if vuln_critical > 0:
                warnings.append(f"Critical vulnerabilities found: {vuln_critical}")
            if sca_high > 5:
                 warnings.append(f"High severity SCA issues found (>5): {sca_high}")

            if vuln_critical > 2 or sca_high > 15:
                status = 'critical'
            elif len(warnings) > 0:
                status = 'warning'

            details = {
                "vulnerability_count_critical": vuln_critical,
                "sca_issues_high": sca_high,
                "warnings": warnings
                # "raw_timestamp": raw_data.get('timestamp') # Timestamp not in mock CSV
            }
            logger.info(f"[{self.provider_id}] Processed mock data for app: {app_id}, Status: {status}")
            return {
                "status": status,
                "details": details
                # "raw_data": raw_data # Optionally include raw data
            }
        except ValueError as e:
             logger.error(f"[{self.provider_id}] Error converting data types for app {app_id}: {e}. Data: {raw_data}", exc_info=True)
             return {"status": "unknown", "details": {"error": f"Error processing data types: {e}"}}
        except Exception as e:
            logger.error(f"[{self.provider_id}] Error processing raw data for app {app_id}: {e}. Data: {raw_data}", exc_info=True)
            return {"status": "unknown", "details": {"error": f"Error processing data: {e}"}}
