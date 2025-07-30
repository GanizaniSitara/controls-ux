from api.connectors.base_connector import BaseConnector
from typing import Dict, Any, Optional
import requests
import logging

logger = logging.getLogger(__name__)

class RestConnector(BaseConnector):
    """Connects to and fetches data from a REST API endpoint."""

    def fetch_data(self, app_config: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Fetches data from the REST API endpoint specified in parameters.
        Uses 'url', 'method' (default GET), 'headers', 'params', 'json_payload' from self.params.
        Can potentially use app_config for dynamic parts like path parameters or query params.
        """
        url = self.params.get('url')
        method = self.params.get('method', 'GET').upper()
        headers = self.params.get('headers', {})
        query_params = self.params.get('params', {})
        json_payload = self.params.get('json_payload') # For POST/PUT etc.

        if not url:
            logger.error("REST Connector: Missing 'url' parameter.")
            return None

        # --- Placeholder for potentially using app_config --- 
        # Example: Maybe the app_id needs to be part of the URL or a query param
        if app_config and app_config.get('app_id'):
             # Example: url = url.format(app_id=app_config['app_id']) # If URL has {app_id}
             # Example: query_params['app'] = app_config['app_id']
             pass # Add specific logic here if needed based on API design
        # --- End placeholder ---

        try:
            logger.info(f"REST Connector: Fetching data from {method} {url}")
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=query_params,
                json=json_payload,
                timeout=10 # Add a reasonable timeout
            )

            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

            data = response.json()
            logger.info(f"REST Connector: Successfully fetched data from {url}")
            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"REST Connector: Error fetching data from {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"REST Connector: Unexpected error for {url}: {e}")
            return None
