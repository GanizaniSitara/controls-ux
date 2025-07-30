# filepath: c:\git\FitnessFunctions\api\data_reader.py
import logging
from typing import Dict, Any, Optional
# Import get_aggregated_data directly
from data_aggregator import get_aggregated_data

logger = logging.getLogger(__name__)

def get_application_details(app_id: str) -> Optional[Dict[str, Any]]:
    # Retrieves all available details for a specific application ID
    # by fetching the cache data internally.
    # Handles URL-decoded app_id which might contain spaces.
    logger.debug(f"DataReader: Attempting to retrieve details for appId: '{app_id}'")

    # Fetch cache data inside the function
    cache_data = get_aggregated_data()
    if not cache_data:
        logger.error("DataReader: Failed to retrieve cache data from data_aggregator.")
        return None # Cannot proceed without cache data

    details: Dict[str, Any] = {"appId": app_id, "raw_data": {}, "rule_results": {}}
    found_raw = False
    found_rules = False

    # Check raw_data from cache
    if "raw_data" in cache_data:
        for provider_name, provider_data in cache_data["raw_data"].items():
            if isinstance(provider_data, dict) and app_id in provider_data:
                details["raw_data"][provider_name] = provider_data[app_id]
                found_raw = True
                logger.debug(f"DataReader: Found raw data for '{app_id}' in provider '{provider_name}'")


    # Check rule_results from cache
    if "rule_results" in cache_data:
        app_rule_results = {}
        for rule_id, rule_data in cache_data["rule_results"].items():
             if isinstance(rule_data, dict) and app_id in rule_data:
                 app_rule_results[rule_id] = rule_data[app_id]
                 found_rules = True
        if found_rules:
            details["rule_results"] = app_rule_results
            logger.debug(f"DataReader: Found rule results for '{app_id}'")


    if found_raw or found_rules:
        logger.info(f"DataReader: Successfully retrieved details for appId: '{app_id}'")
        return details
    else:
        logger.warning(f"DataReader: No data found in cache for appId: '{app_id}'")
        return None
