from .base_rule import BaseRule
import datetime
import logging
from collections import defaultdict

class AggregateByAppRule(BaseRule):
    """Aggregates data by application ID across different providers."""

    def apply(self, raw_data: dict) -> dict:
        """
        Restructures data from provider -> app -> metrics to app -> provider -> metrics.

        Args:
            raw_data: The input data, expected structure: {provider_id: {app_id: metrics}}

        Returns:
            A dictionary structured as: {app_id: {provider_id: metrics}}, plus metadata.
        """
        aggregated_by_app = defaultdict(dict)
        logging.info(f"Applying {self.__class__.__name__}...")

        # raw_data structure is assumed to be {provider_id: {app_id: data}}
        for provider_id, app_data in raw_data.items():
            if not isinstance(app_data, dict):
                logging.warning(f"Skipping provider '{provider_id}': data is not a dictionary ({type(app_data)}).")
                continue # Skip if provider data isn't a dict

            for app_id, metrics in app_data.items():
                # Store the provider's metrics under the app_id
                aggregated_by_app[app_id][provider_id] = metrics
                logging.debug(f"Aggregated data for app '{app_id}' from provider '{provider_id}'.")

        # Convert defaultdict back to a regular dict for the final output
        final_data = dict(aggregated_by_app)

        # Add metadata
        final_data['_metadata'] = {
            'rule_applied': self.__class__.__name__,
            'processed_timestamp': datetime.datetime.now().isoformat(),
            'original_providers': list(raw_data.keys())
        }

        logging.info(f"{self.__class__.__name__} applied successfully. Aggregated data for {len(final_data) -1} apps.") # -1 for metadata
        return final_data
