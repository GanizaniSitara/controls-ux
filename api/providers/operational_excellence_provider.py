from .base_provider import BaseFitnessProvider, Status
from typing import Dict, Any, Optional
import logging
import os # Added for path joining
import csv # Added for CSV reading

logger = logging.getLogger(__name__)

class OperationalExcellenceProvider(BaseFitnessProvider):
    """Provides fitness data related to operational excellence based on mock CSV data."""

    def __init__(self, config: Dict[str, Any]): # Added config parameter
        """
        Initializes the provider. Config is currently unused.
        """
        self.config = config
        # Get CSV file path from settings.ini
        self.mock_file_path = self.get_csv_filepath()
        logger.info(f"[{self.provider_id}] Initialized to read from mock file: {self.mock_file_path}")

    @property
    def provider_id(self) -> str:
        return "operational_excellence_v1"

    def get_fitness_data(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        """Returns operational excellence data read directly from the mock CSV file."""
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
        # Assuming columns 'UptimePercent', 'AvgResponseTimeMS', 'IncidentsLast30d'
        try:
            uptime = float(raw_data.get('UptimePercent', 0.0))
            response_time = int(raw_data.get('AvgResponseTimeMS', 9999))
            incidents = int(raw_data.get('IncidentsLast30d', 99))

            # Example status logic
            status: Status = 'healthy'
            warnings = []
            if uptime < 99.5:
                warnings.append(f"Uptime below threshold (<99.5%): {uptime}%")
            if response_time > 500:
                 warnings.append(f"Average response time high (>500ms): {response_time}ms")
            if incidents > 1:
                 warnings.append(f"Multiple incidents in last 30 days: {incidents}")

            if uptime < 99.0 or response_time > 1000 or incidents > 3:
                status = 'critical'
            elif len(warnings) > 0:
                status = 'warning'

            details = {
                "uptime_percent_last_30d": uptime,
                "avg_response_time_ms": response_time,
                "incidents_last_30d": incidents,
                "warnings": warnings
                # "last_incident_date": ... # This wasn't in the assumed columns, maybe add later
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

        # --- Remove old mock data generation ---
        # status: Status = random.choice(['healthy', 'warning', 'critical'])
        # details = {
        #     "uptime_percent_last_30d": round(random.uniform(99.0, 100.0), 2),
        #     "avg_response_time_ms": random.randint(50, 500),
        #     "last_incident_date": (datetime.date.today() - datetime.timedelta(days=random.randint(1, 90))).isoformat()
        # }
        # logging.info(f"[{self.provider_id}] Generating data for app: {app_config.get('name', 'Unknown')}")
        # return {
        #     "status": status,
        #     "details": details
        # }
