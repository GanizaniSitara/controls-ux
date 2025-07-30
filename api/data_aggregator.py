# filepath: c:\\git\\FitnessFunctions\\api\\data_aggregator.py
import pandas as pd
import os
import glob
import importlib
import inspect # Added inspect
import re # Moved import re here
import configparser # Added for reading settings.ini
from cachetools import Cache
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import sys # Import sys for stdout
import threading
import time
from typing import Dict, Any, Optional, List # Added List
from rules_engine import load_rules, run_rules # Ensure rules engine imports are correct
import psutil # Add this import
from simple_data_loader import load_csv_data

logger = logging.getLogger(__name__)

# Define directories
API_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(API_DIR, 'data_mock')
PROVIDERS_DIR = os.path.join(API_DIR, 'providers')
LOGS_DIR = os.path.join(API_DIR, 'logs') # Define logs directory
os.makedirs(LOGS_DIR, exist_ok=True) # Ensure logs directory exists
PROFILER_LOG_PATH = os.path.join(LOGS_DIR, 'memory_profile_aggregator.log')
profiler_log_file = open(PROFILER_LOG_PATH, 'a+') # Changed mode to 'a+' for appending


# --- Configuration (Replace with a more robust config mechanism later) ---

# Define applications (could be loaded from a file or database)
# Let's get app_ids dynamically from one of the CSVs for now
def get_app_ids_from_mock_data() -> List[str]:
    try:
        sample_file = os.path.join(DATA_DIR, 'code_quality_v1.csv')
        if os.path.exists(sample_file):
            df = pd.read_csv(sample_file)
            if 'app_id' in df.columns:
                return df['app_id'].unique().tolist()
    except Exception as e:
        logger.error(f"Could not dynamically load app_ids: {e}")
    # Fallback if dynamic loading fails
    return ["app_a", "app_b", "app_c", "app_d"]

APPLICATIONS = [{ "app_id": app_id } for app_id in get_app_ids_from_mock_data()]
logger.info(f"Loaded applications: {APPLICATIONS}")

# Load provider configurations from settings.ini
def load_provider_configs() -> Dict[str, Dict[str, str]]:
    """
    Loads provider configurations from settings.ini file.
    Returns a dictionary mapping provider IDs to their configuration details.
    """
    config_path = os.path.join(API_DIR, 'settings.ini')
    logger.info(f"Loading provider configurations from {config_path}")
    
    if not os.path.exists(config_path):
        logger.error(f"Settings file not found: {config_path}")
        return {}
        
    try:
        config = configparser.ConfigParser()
        config.read(config_path)
        
        if not config.has_section('providers'):
            logger.error("No 'providers' section found in settings.ini")
            return {}
            
        provider_configs = {}
        for provider_key, file_path in config.items('providers'):
            # Convert provider_key to standard format with version
            provider_id = f"{provider_key}_v1"
            provider_configs[provider_id] = {
                "connector_type": "csv",
                "file_path": file_path.replace('\\', '/')  # Normalize path separators
            }
            
        logger.info(f"Loaded {len(provider_configs)} provider configurations from settings.ini")
        return provider_configs
    except Exception as e:
        logger.error(f"Error loading provider configurations from settings.ini: {e}")
        return {}

# Load provider configurations from settings.ini
PROVIDER_CONFIGS = load_provider_configs()

# Check if configurations were loaded, otherwise use fallback
if not PROVIDER_CONFIGS:
    logger.warning("Failed to load provider configurations from settings.ini, using hardcoded fallback.")
    # Fallback to hardcoded configurations
    PROVIDER_CONFIGS = {
        "code_quality_v1": {"connector_type": "csv", "file_path": "data_mock/code_quality_v1.csv"},
        "cost_optimization_v1": {"connector_type": "csv", "file_path": "data_mock/cost_optimization_v1.csv"},
        "documentation_v1": {"connector_type": "csv", "file_path": "data_mock/documentation_v1.csv"},
        "operational_excellence_v1": {"connector_type": "csv", "file_path": "data_mock/operational_excellence_v1.csv"},
        "security_v1": {"connector_type": "csv", "file_path": "data_mock/security_v1.csv"},
        "data_quality_v1": {"connector_type": "csv", "file_path": "data_mock/data_quality_v1.csv"},
        "resilience_v1": {"connector_type": "csv", "file_path": "data_mock/resilience_v1.csv"},
        "tech_debt_v1": {"connector_type": "csv", "file_path": "data_mock/tech_debt_v1.csv"},
        "vendor_mgmt_v1": {"connector_type": "csv", "file_path": "data_mock/vendor_mgmt_v1.csv"},
        "architecture_v1": {"connector_type": "csv", "file_path": "data_mock/architecture_v1.csv"},
        "workload_placement_v1": {"connector_type": "csv", "file_path": "data_mock/workload_placement_v1.csv"},
    }

logger.info(f"Provider configurations loaded: {list(PROVIDER_CONFIGS.keys())}")

# --- Provider Discovery ---
# def load_provider_classes() -> Dict[str, Type[BaseFitnessProvider]]:
#     """Dynamically loads provider classes from the providers directory."""
#     provider_classes = {}
#     logger.info(f"Starting provider discovery in: {PROVIDERS_DIR}") # Enhanced log
#     if not os.path.isdir(PROVIDERS_DIR):
#         logger.error(f"Providers directory not found or is not a directory: {PROVIDERS_DIR}")
#         return provider_classes

#     for filename in os.listdir(PROVIDERS_DIR):
#         logger.debug(f"Checking file: {filename}") # Added log
#         if filename.endswith("_provider.py") and not filename.startswith("base_") and not filename == "__init__.py": # Exclude __init__.py
#             module_name_short = filename[:-3] # e.g., code_quality_provider
#             # Use relative import path from within the 'api' package
#             module_name_full = f".providers.{module_name_short}" # e.g., .providers.code_quality_provider
#             logger.debug(f"Attempting to import module: {module_name_full}") # Added log
#             try:
#                 # The package context for relative import is the current module's package
#                 module = importlib.import_module(module_name_full, package='api') # Specify package context
#                 logger.debug(f"Successfully imported module: {module_name_full}") # Added log

#                 for name, obj in inspect.getmembers(module):
#                     logger.debug(f"Inspecting member: {name} in module {module_name_full}") # Added log
#                     # Check if it's a class, subclass of BaseFitnessProvider, and not the base class itself
#                     if inspect.isclass(obj) and obj is not BaseFitnessProvider and issubclass(obj, BaseFitnessProvider):
#                         logger.debug(f"Found potential provider class: {name}")
#                         # Instantiate temporarily to get provider_id (requires config)
#                         # This assumes provider_id is accessible after init or as class attr
#                         # We need a config to instantiate, let's find matching config
#                         temp_provider_id = None
#                         # Try to get provider_id without full instantiation if possible (e.g., class variable)
#                         if hasattr(obj, 'provider_id') and isinstance(getattr(obj, 'provider_id'), property):
#                              logger.debug(f"Provider ID for {name} is a property, attempting instantiation.") # Added debug log
#                              # If it's a property, we need an instance. Find config.
#                              for pid, pconfig in PROVIDER_CONFIGS.items():
#                                  # Heuristic: class name often matches provider_id structure
#                                  # Convert class name to snake_case for comparison
#                                  # import re # Moved import re
#                                  s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
#                                  class_snake_case = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
#                                  # Check if snake_case class name starts with provider_id prefix
#                                  if class_snake_case.startswith(pid.split('_')[0]): # e.g. code_quality_provider starts with code_quality
#                                      logger.debug(f"Attempting to instantiate {name} using config for {pid} based on name heuristic.") # Added debug log
#                                      try:
#                                          temp_instance = obj(pconfig)
#                                          temp_provider_id = temp_instance.provider_id
#                                          logger.debug(f"Successfully instantiated {name}; got provider_id: {temp_provider_id}") # Added debug log
#                                          break # Found matching config
#                                      except Exception as init_err:
#                                          logger.warning(f"Could not temp-instantiate {name} to get ID using config for {pid}: {init_err}")
#                                          continue
#                                  else:
#                                      logger.debug(f"Class name {class_snake_case} did not match prefix for config {pid}") # Added debug log
#                         elif hasattr(obj, 'provider_id'): # Maybe it's a simple attribute
#                             temp_provider_id = getattr(obj, 'provider_id')
#                             logger.debug(f"Found provider_id attribute for {name}: {temp_provider_id}") # Added debug log
#                         else:
#                             logger.warning(f"Class {name} does not have a 'provider_id' property or attribute.") # Added warning

#                         if temp_provider_id:
#                             logger.debug(f"Determined provider_id for {name} as: {temp_provider_id}")
#                             if temp_provider_id in PROVIDER_CONFIGS:
#                                 provider_classes[temp_provider_id] = obj
#                                 logger.info(f"Successfully discovered and registered provider class: {name} for ID: {temp_provider_id}") # Enhanced log
#                             else:
#                                 logger.warning(f"Discovered provider class {name} with ID {temp_provider_id}, but no matching configuration found in PROVIDER_CONFIGS. Skipping registration.") # Enhanced log
#                         else:
#                              logger.warning(f"Could not determine provider_id for class {name} in {module_name_full}. Skipping registration.")
#                     elif inspect.isclass(obj):
#                         # logger.debug(f"Skipping class {name} in {module_name_full}: Not a valid provider class.") # Optional: Log skipped classes
#                         pass # Don't log every non-provider class unless needed
#                     else:
#                         # logger.debug(f"Skipping member {name} in {module_name_full}: Not a class.") # Optional: Log skipped members
#                         pass

#             except ImportError as e:
#                 logger.error(f"Failed to import module {module_name_full} relative to 'api': {e}", exc_info=True) # Added exc_info
#             except Exception as e:
#                  logger.error(f"Error processing module {module_name_full}: {e}", exc_info=True) # Added exc_info
#         else:
#             logger.debug(f"Skipping file: {filename} (doesn't match criteria)") # Added log

#     if not provider_classes:
#         logger.error("Provider discovery finished, but NO provider classes were loaded successfully!") # Enhanced log
#     else:
#         logger.info(f"Provider discovery finished. Loaded providers: {list(provider_classes.keys())}") # Enhanced log
#     return provider_classes

# Load providers on startup
# LOADED_PROVIDER_CLASSES = load_provider_classes() # Commented out - no longer needed for core logic

# --- Cache Setup ---
# Cache stores results from providers and potentially raw data
# Structure: { 'provider_results': {provider_id: {app_id: result}}, 'raw_data': {provider_id: {app_id: raw}} }
# Removed TTL to prevent data disappearing - cache management now handled manually
data_cache = Cache(maxsize=100)  # No TTL - cache managed manually
_cache_lock = threading.Lock() # Added a lock for thread-safe access to the cache

# Cache metadata for health monitoring
cache_metadata = {
    'last_update': None,
    'update_count': 0,
    'last_error': None,
    'error_count': 0,
    'cache_size': 0
}

# Fallback cache for emergency situations
fallback_cache = {}
_fallback_lock = threading.Lock()

# --- Core Logic ---

# Old loading functions removed - using simple_data_loader.load_csv_data() instead


# @profile(stream=profiler_log_file) # Remove memory profiler decorator
def update_cache():
    """
    Updates the cache by:
    1. Loading latest raw data for each provider/source.
    2. Running the rules engine on the collected raw data.
    3. Updating cache metadata for health monitoring.
    """
    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / (1024 * 1024) # Memory in MB
    logger.info(f"MEMORY_DEBUG: update_cache started. RSS: {mem_before:.2f} MB")
    logger.info("CACHE_TRACE: update_cache function started.")
    
    # Update cache metadata at start
    with _cache_lock:
        cache_metadata['last_update'] = datetime.datetime.now()
        cache_metadata['update_count'] += 1
    logger.info("Scheduler executing update_cache function.") # Existing log

    # Initialize cache structure for this run
    current_raw_data: Dict[str, Dict[str, Any]] = {}

    # Load Raw Data using simple CSV loader
    logger.info("Starting raw data loading...")
    for provider_id, config in PROVIDER_CONFIGS.items():
        raw_data_for_provider = load_csv_data(provider_id, config, API_DIR)
        
        if raw_data_for_provider:
            current_raw_data[provider_id] = raw_data_for_provider
        else:
            logger.warning(f"No raw data loaded for provider: {provider_id}")
    logger.info(f"Raw data loading finished. Loaded data for {len(current_raw_data)} providers.")
    # logger.debug(f"Raw data content: {current_raw_data}") # Debug log for raw data
    logger.info(f"CACHE_TRACE: current_raw_data (first 500 chars): {str(current_raw_data)[:500]}")


    # Update the main cache object with raw data
    with _cache_lock:
        data_cache['raw_data'] = current_raw_data
        logger.info(f"CACHE_TRACE: After setting 'raw_data'. Cache keys: {list(data_cache.keys())}")

    # Clear previous provider/rule results if they exist from old structure
    with _cache_lock:
        popped_provider_results = data_cache.pop('provider_results', None)
        popped_rule_results = data_cache.pop('rule_results', None)
        logger.info(f"CACHE_TRACE: Popped 'provider_results' (was present: {popped_provider_results is not None}), Popped 'rule_results' (was present: {popped_rule_results is not None}). Cache keys: {list(data_cache.keys())}")

    # --- REMOVED STEP 2: Running Provider Classes ---
    # The part using get_all_connectors() and LOADED_PROVIDER_CLASSES is already removed/commented.
    # No further changes needed here regarding connector usage.

    # 3. Run Rules Engine (on raw data)
    logger.info("Starting rules engine execution on raw data...")
    try:
        # Get the raw data we just loaded, plus potentially other cache items if needed by rules
        rules_input_data = dict(data_cache) # Pass a copy of the current cache state
        # logger.debug(f"Data passed to rules engine: {rules_input_data}")
        logger.info(f"CACHE_TRACE: rules_input_data (first 500 chars of raw_data): {str(rules_input_data.get('raw_data'))[:500]}")


        if not rules_input_data.get('raw_data'): # Check specifically for raw_data presence
            logger.warning("Raw data is empty in cache. Skipping rules engine run.")
            # Store empty results to indicate rules ran on empty data
            with _cache_lock:
                data_cache['rule_results'] = {}
                logger.info(f"CACHE_TRACE: Raw data empty, set 'rule_results' to {{}}. Cache keys: {list(data_cache.keys())}")
            # Ensure to log memory and finish before returning
            mem_after_empty_raw = process.memory_info().rss / (1024 * 1024)
            logger.info(f"MEMORY_DEBUG: update_cache finished (empty raw data). RSS: {mem_after_empty_raw:.2f} MB. Delta: {mem_after_empty_raw - mem_before:.2f} MB")
            logger.info("CACHE_TRACE: update_cache function finished (empty raw data).")
            return

        rules = load_rules() # Load rules dynamically
        if not rules:
            logger.warning("No rules loaded. Skipping rules engine run.")
            # Store empty results
            with _cache_lock:
                data_cache['rule_results'] = {}
                logger.info(f"CACHE_TRACE: No rules loaded, set 'rule_results' to {{}}. Cache keys: {list(data_cache.keys())}")
            # Ensure to log memory and finish before returning
            mem_after_no_rules = process.memory_info().rss / (1024 * 1024)
            logger.info(f"MEMORY_DEBUG: update_cache finished (no rules). RSS: {mem_after_no_rules:.2f} MB. Delta: {mem_after_no_rules - mem_before:.2f} MB")
            logger.info("CACHE_TRACE: update_cache function finished (no rules).")
            return

        # run_rules now returns a dictionary of results keyed by rule identifier
        all_rule_results = run_rules(rules_input_data, rules)
        logger.info(f"CACHE_TRACE: all_rule_results (first 500 chars): {str(all_rule_results)[:500]}")

        # Store the dictionary of rule results in the cache
        with _cache_lock:
            data_cache['rule_results'] = all_rule_results
            # Update fallback cache with successful data
            update_fallback_cache()
        logger.info(f"Rules engine finished. Results stored in cache under 'rule_results'.")
        # logger.debug(f"Rule results dictionary: {all_rule_results}") # Debug log for rule results dict
        logger.info(f"CACHE_TRACE: After setting 'rule_results'. Cache keys: {list(data_cache.keys())}")


    except Exception as e:
        logger.error(f"Error during rules engine execution: {e}", exc_info=True)
        # Store error state in rule results
        with _cache_lock:
            data_cache['rule_results'] = {"error": f"Rules engine failed: {e}"}
            logger.info(f"CACHE_TRACE: Exception in rules engine, set 'rule_results' to error. Cache keys: {list(data_cache.keys())}")
            
            # Update error metadata
            cache_metadata['last_error'] = str(e)
            cache_metadata['error_count'] += 1

    # Update cache metadata at end
    with _cache_lock:
        cache_metadata['cache_size'] = len(data_cache)
        cache_metadata['last_error'] = None  # Clear error on successful update
    
    mem_after = process.memory_info().rss / (1024 * 1024) # Memory in MB
    logger.info(f"MEMORY_DEBUG: update_cache finished. RSS: {mem_after:.2f} MB. Delta: {mem_after - mem_before:.2f} MB")
    logger.info("Cache update and rules engine cycle finished.") # Existing log
    logger.info(f"CACHE_TRACE: update_cache function finished. Final cache keys: {list(data_cache.keys())}")

# --- Cache Access ---
def get_aggregated_data() -> Dict[str, Any]:
    """Returns the current content of the data cache (raw_data and rule_results).
    
    If cache is empty or stale, attempts to refresh it.
    Falls back to fallback cache if main cache fails.
    """
    logger.debug("CACHE_ACCESS: get_aggregated_data called")
    needs_refresh = False
    
    with _cache_lock:
        # Check if cache is empty or needs refresh
        cache_empty = not data_cache
        cache_stale = should_refresh_cache()
        
        if cache_empty or cache_stale:
            needs_refresh = True
            logger.info(f"CACHE_ACCESS: Cache needs refresh (empty: {cache_empty}, stale: {cache_stale})")
    
    # Call update_cache outside the lock to prevent deadlock
    if needs_refresh:
        try:
            logger.info("CACHE_ACCESS: Triggering cache refresh...")
            update_cache()
            logger.info("CACHE_ACCESS: Cache refresh completed")
        except Exception as e:
            logger.error(f"CACHE_ACCESS: Failed to refresh cache: {e}")
            # Try to use fallback data
            fallback_data = get_fallback_data()
            if fallback_data:
                logger.info("CACHE_ACCESS: Using fallback data")
                return fallback_data
    
    # Return main cache data
    with _cache_lock:
        if data_cache:
            logger.debug(f"CACHE_ACCESS: Returning main cache data with keys: {list(data_cache.keys())}")
            return dict(data_cache)
        else:
            # Last resort: try fallback
            logger.warning("CACHE_ACCESS: Main cache is empty, trying fallback")
            return get_fallback_data()

def should_refresh_cache() -> bool:
    """Determines if the cache should be refreshed based on age and content."""
    if not cache_metadata['last_update']:
        logger.debug("CACHE_CHECK: No last_update recorded, refresh needed")
        return True
    
    # Refresh if cache is older than 3 minutes (for testing)
    age_threshold = datetime.timedelta(minutes=3)
    cache_age = datetime.datetime.now() - cache_metadata['last_update']
    
    if cache_age > age_threshold:
        logger.info(f"CACHE_CHECK: Cache is {cache_age} old (threshold: {age_threshold}), triggering refresh")
        return True
    
    logger.debug(f"CACHE_CHECK: Cache is {cache_age} old, no refresh needed")
    return False

def get_cache_health() -> Dict[str, Any]:
    """Returns cache health information for monitoring."""
    with _cache_lock:
        health = dict(cache_metadata)
        health['cache_keys'] = list(data_cache.keys())
        health['cache_age_seconds'] = (
            (datetime.datetime.now() - cache_metadata['last_update']).total_seconds()
            if cache_metadata['last_update'] else None
        )
        return health

# --- New Function ---
def get_application_details(app_id: str) -> Optional[Dict[str, Any]]:
    # Retrieves all available details for a specific application ID
    # from the cached raw data and provider results.
    # Handles URL-decoded app_id which might contain spaces.
    logger.debug(f"Attempting to retrieve details for appId: '{app_id}'")
    details: Dict[str, Any] = {"appId": app_id, "raw_data": {}, "provider_results": {}}
    found = False

    with _cache_lock:
        # Check raw_data from connectors
        if "raw_data" in data_cache:
            for provider_name, provider_data in data_cache["raw_data"].items():
                if isinstance(provider_data, dict) and app_id in provider_data:
                    details["raw_data"][provider_name] = provider_data[app_id]
                    found = True
                    logger.debug(f"Found raw data for '{app_id}' in provider '{provider_name}'")

        # Check provider_results from rules engine
        if "provider_results" in data_cache:
             for provider_name, provider_results_data in data_cache["provider_results"].items():
                if isinstance(provider_results_data, dict) and app_id in provider_results_data:
                    details["provider_results"][provider_name] = provider_results_data[app_id]
                    found = True
                    logger.debug(f"Found provider results for '{app_id}' in provider '{provider_name}'")

    if found:
        logger.info(f"Successfully retrieved details for appId: '{app_id}'")
        return details
    else:
        logger.warning(f"No data found in cache for appId: '{app_id}'")
        return None
# --- End New Function ---

def update_fallback_cache():
    """Updates the fallback cache with current successful data."""
    try:
        with _fallback_lock:
            fallback_cache.clear()
            fallback_cache.update(data_cache)
        logger.info(f"FALLBACK_CACHE: Updated successfully with {len(fallback_cache)} items")
    except Exception as e:
        logger.error(f"FALLBACK_CACHE: Failed to update: {e}")

def get_fallback_data() -> Dict[str, Any]:
    """Returns fallback data when main cache fails."""
    with _fallback_lock:
        if fallback_cache:
            logger.warning(f"FALLBACK_CACHE: Using fallback data with {len(fallback_cache)} items")
            return dict(fallback_cache)
        else:
            logger.error("FALLBACK_CACHE: No fallback data available")
            return {}

# --- Scheduler Setup ---
scheduler = BackgroundScheduler(daemon=True)

# Configure APScheduler logging to be more verbose
apscheduler_logger = logging.getLogger('apscheduler')
apscheduler_logger.setLevel(logging.DEBUG)

# Explicitly add a handler to ensure APScheduler logs are output
# This helps if the root logger or other configurations are not catching them
if not apscheduler_logger.handlers:
    stream_handler = logging.StreamHandler(sys.stdout) # Output to stdout
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - [%(name)s] - %(message)s") # Match your app's format
    stream_handler.setFormatter(formatter)
    apscheduler_logger.addHandler(stream_handler)
    apscheduler_logger.propagate = False # Prevent double-logging if root logger also has a handler

# Define a simple heartbeat function
def log_scheduler_heartbeat():
    logger.info("SCHEDULER_HEARTBEAT: APScheduler is alive and ticking.")

# Schedule update_cache to run every 5 minutes
scheduler.add_job(update_cache, 'interval', seconds=300, id='update_cache_job')
# Schedule heartbeat job to run every 1 minute
scheduler.add_job(log_scheduler_heartbeat, 'interval', seconds=60, id='scheduler_heartbeat_job')

# ... rest of start_scheduler, shutdown_scheduler ...

def start_scheduler():
    """Starts the background scheduler and performs an initial cache load."""
    try:
        # Perform initial data load immediately
        logger.info("Performing initial data load...")
        update_cache()        # Start the scheduler        scheduler.start()
        logger.info("Background scheduler started. Cache will update every 5 minutes.")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        # Ensure scheduler is shut down if it partially started
        if scheduler.running:
            scheduler.shutdown()

# --- Application Lifecycle Hook (Optional but recommended for clean shutdown) ---
def shutdown_scheduler():
    """Shuts down the scheduler gracefully."""
    logging.info("Shutting down background scheduler...")
    if scheduler.running:
        scheduler.shutdown()
    logging.info("Scheduler shut down.")

