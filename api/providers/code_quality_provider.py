from .base_provider import BaseFitnessProvider, Status # Relative import
from typing import Dict, Any, Optional
import logging
import os
import csv

logger = logging.getLogger(__name__)

class CodeQualityProvider(BaseFitnessProvider):
    """Provides fitness data related to code quality based on CSV data."""

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
        return "code_quality_v1"

    def get_fitness_data(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        """Returns code quality data read directly from the mock CSV file."""
        app_id = app_config.get('app_id')
        if not app_id:
            logger.warning(f"[{self.provider_id}] app_id missing in app_config. Cannot fetch specific data.")
            return {"status": "unknown", "details": {"error": "app_id missing."}}        # Read data directly from the mock CSV file
        raw_data: Optional[Dict[str, Any]] = None
        try:
            with open(self.mock_file_path, mode='r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # CSV has an 'app_id' column matching app_id
                    if row.get('app_id') == app_id:
                        raw_data = row
                        break # Found the app, stop reading
        except FileNotFoundError:
            logger.error(f"[{self.provider_id}] Mock data file not found: {self.mock_file_path}")
            return {"status": "unknown", "details": {"error": f"Mock data file not found: {self.mock_file_path}"}}
        except Exception as e:
            logger.error(f"[{self.provider_id}] Error reading mock data file {self.mock_file_path}: {e}", exc_info=True)
            return {"status": "unknown", "details": {"error": f"Error reading mock data file: {e}"}}

        if raw_data is None:
            logger.warning(f"[{self.provider_id}] No data found for app_id: {app_id} in {self.mock_file_path}")
            # Return 'not_found' status instead of 'unknown' for clarity
            return {"status": "not_found", "details": {"message": f"No data found for app_id {app_id} in mock file."}}

        # --- Determine Status and Details from raw_data ---
        # Using the columns from the provided CSV: LintScore, TestCoverage, ComplexityScore, MaintainabilityIndex
        try:
            # Convert values, providing defaults if missing or invalid
            lint_score = int(raw_data.get('LintScore', 0))
            test_coverage = int(raw_data.get('TestCoverage', 0))
            complexity_score = int(raw_data.get('ComplexityScore', 0))
            maintainability_index = int(raw_data.get('MaintainabilityIndex', 0))

            # Example status logic (adjust thresholds as needed)
            # Higher scores are generally better for LintScore, TestCoverage, MaintainabilityIndex
            # Lower scores are generally better for ComplexityScore
            status: Status = 'healthy'
            warnings = []
            if lint_score < 85: warnings.append("Low Lint Score")
            if test_coverage < 75: warnings.append("Low Test Coverage")
            if complexity_score > 15: warnings.append("High Complexity")
            if maintainability_index < 75: warnings.append("Low Maintainability")

            if len(warnings) > 2:
                status = 'critical'
            elif len(warnings) > 0:
                status = 'warning'


            details = {
                "lint_score": lint_score,
                "test_coverage_percent": test_coverage,
                "complexity_score": complexity_score,
                "maintainability_index": maintainability_index,
                "warnings": warnings, # Add warnings for context
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
