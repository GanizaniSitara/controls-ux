from .base_connector import BaseConnector
from typing import Dict, Any, Optional
import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)

class CsvConnector(BaseConnector):
    """Connects to and fetches data from a local CSV file."""

    def fetch_data(self, app_config: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Reads the CSV file specified in parameters, finds the latest entry
        for a given app_id (if provided in app_config).
        If no app_id is provided, it might return data for all apps or the latest overall.
        (Behavior might need refinement based on how providers use it).
        For now, let's assume it finds the latest for a specific app_id.
        """
        file_path = self.params.get('file_path')
        app_id_to_find = app_config.get('app_id') if app_config else None

        if not file_path:
            logger.error("CSV Connector: Missing 'file_path' parameter.")
            return None

        absolute_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', file_path)) # Assume relative to api dir

        if not os.path.exists(absolute_file_path):
            logger.error(f"CSV Connector: File not found at {absolute_file_path}")
            return None

        try:
            df = pd.read_csv(absolute_file_path)
            logger.info(f"CSV Connector: Successfully read {absolute_file_path}")

            # --- Logic to find the specific app's latest data --- 
            # This replicates part of the logic from data_aggregator, 
            # but focused on a single app if specified.
            if 'app_id' not in df.columns:
                 logger.error(f"CSV Connector: CSV file {absolute_file_path} missing 'app_id' column.")
                 return None

            if app_id_to_find:
                app_df = df[df['app_id'] == app_id_to_find]
                if app_df.empty:
                    logger.warning(f"CSV Connector: No data found for app_id '{app_id_to_find}' in {absolute_file_path}")
                    return None
                
                if 'timestamp' in app_df.columns:
                    try:
                        app_df['timestamp'] = pd.to_datetime(app_df['timestamp'])
                        latest_entry = app_df.loc[app_df['timestamp'].idxmax()]
                    except Exception as time_e:
                         logger.warning(f"CSV Connector: Could not parse timestamp for app '{app_id_to_find}'. Using last entry. Error: {time_e}")
                         latest_entry = app_df.iloc[-1]
                else:
                    logger.warning(f"CSV Connector: No 'timestamp' column found for app '{app_id_to_find}'. Using last entry.")
                    latest_entry = app_df.iloc[-1]
                
                # Convert the row to a dictionary
                data = latest_entry.to_dict()
                logger.info(f"CSV Connector: Fetched latest data for app '{app_id_to_find}'")
                return data
            else:
                # If no app_id specified, maybe return all latest data? Or raise error?
                # For now, let's return None, assuming provider needs specific app data.
                logger.warning("CSV Connector: app_id not specified in app_config. Cannot fetch specific data.")
                return None
            # --- End specific app logic ---

        except Exception as e:
            logger.error(f"CSV Connector: Error processing file {absolute_file_path}: {e}")
            return None
