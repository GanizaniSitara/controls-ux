from .base_connector import BaseConnector
from typing import Dict, Any, Optional, List
import openpyxl
import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)

class ExcelConnector(BaseConnector):
    """Connects to and fetches data from a local Excel (.xlsx) file."""

    def fetch_data(self, app_config: Optional[Dict[str, Any]] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Reads data from an Excel file sheet.

        Required params:
            - file_path: Path to the .xlsx file (relative to api directory assumed).
        Optional params:
            - sheet_name: Name of the sheet to read (default: first sheet).
            - header_row: Row number (0-indexed) containing headers (default: 0).
            - app_id_column: Name of the column containing the application ID (if filtering needed).

        Optional app_config usage:
            - If 'app_id_column' param and app_config['app_id'] are provided,
              it filters the data to return only rows matching the app_id.
              Otherwise, returns all rows from the sheet.
        """
        file_path = self.params.get('file_path')
        sheet_name = self.params.get('sheet_name') # Defaults to None, pandas reads first sheet
        header_row = self.params.get('header_row', 0)
        app_id_col = self.params.get('app_id_column')
        app_id_to_find = app_config.get('app_id') if app_config else None

        if not file_path:
            logger.error("Excel Connector: Missing 'file_path' parameter.")
            return None

        absolute_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', file_path))

        if not os.path.exists(absolute_file_path):
            logger.error(f"Excel Connector: File not found at {absolute_file_path}")
            return None

        try:
            logger.info(f"Excel Connector: Reading sheet '{sheet_name or 'default'}' from {absolute_file_path}")
            # Use pandas for easier reading and filtering
            df = pd.read_excel(
                absolute_file_path,
                sheet_name=sheet_name, # None reads the first sheet
                header=header_row
            )

            # Convert NaNs to None for better JSON compatibility later
            df = df.where(pd.notnull(df), None)

            logger.info(f"Excel Connector: Successfully read {len(df)} rows.")

            # Filter by app_id if requested and possible
            if app_id_col and app_id_to_find:
                if app_id_col not in df.columns:
                    logger.error(f"Excel Connector: Specified app_id_column '{app_id_col}' not found in sheet.")
                    return None # Or maybe return all data with a warning? Returning None for now.
                
                # Ensure consistent type for comparison if possible (e.g., handle numeric app IDs)
                # This might need refinement based on actual data types
                try:
                    # Attempt conversion if column is numeric, otherwise compare as string
                    if pd.api.types.is_numeric_dtype(df[app_id_col]):
                         app_id_to_find_typed = type(df[app_id_col].iloc[0])(app_id_to_find)
                    else:
                         app_id_to_find_typed = str(app_id_to_find)
                    
                    filtered_df = df[df[app_id_col] == app_id_to_find_typed]
                except Exception as filter_err:
                     logger.warning(f"Excel Connector: Could not filter by app_id '{app_id_to_find}' using column '{app_id_col}'. Comparing as string. Error: {filter_err}")
                     filtered_df = df[df[app_id_col].astype(str) == str(app_id_to_find)]


                if filtered_df.empty:
                    logger.warning(f"Excel Connector: No data found for app_id '{app_id_to_find}' using column '{app_id_col}'.")
                    # Return empty list instead of None if filter yields no results
                    return [] 
                else:
                    logger.info(f"Excel Connector: Filtered data for app_id '{app_id_to_find}'. Found {len(filtered_df)} rows.")
                    # Convert filtered DataFrame to list of dictionaries
                    return filtered_df.to_dict(orient='records')
            else:
                 # Return all data if no filtering requested
                 logger.info("Excel Connector: No app_id filtering requested or possible. Returning all rows.")
                 return df.to_dict(orient='records')


        except FileNotFoundError:
             logger.error(f"Excel Connector: File not found error for {absolute_file_path}")
             return None
        except ValueError as ve: # Catches sheet not found errors from pandas
             logger.error(f"Excel Connector: Error reading Excel file (maybe sheet '{sheet_name}' not found?): {ve}")
             return None
        except Exception as e:
            logger.error(f"Excel Connector: Error processing file {absolute_file_path}: {e}")
            return None

