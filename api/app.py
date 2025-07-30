import logging
import os
import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
import strawberry
from strawberry.fastapi import GraphQLRouter
import numpy as np
import pandas as pd
from typing import Any

# Local imports
from data_schema import schema
from data_aggregator import get_aggregated_data, start_scheduler, shutdown_scheduler, get_cache_health, PROVIDER_CONFIGS, API_DIR # Make sure get_aggregated_data is imported
from data_reader import get_application_details
from evidence_scanner import EvidenceScanner
from control_discovery import get_control_discovery
import configparser

# --- Logging Setup ---
# Create a log directory if it doesn't exist (optional, adjust path as needed)
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

# Generate timestamped log filename
log_filename = datetime.datetime.now().strftime("api_log_%Y%m%d_%H%M%S.log")
log_filepath = os.path.join(log_dir, log_filename)

# Configure logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(name)s] - %(message)s",
    handlers=[
        logging.FileHandler(log_filepath),
        logging.StreamHandler() # To still see logs in the console
    ]
)

logger = logging.getLogger(__name__)
logger.info(f"Logging initialized. Log file: {log_filepath}")

# --- JSON Cleaning Function ---
def clean_for_json(obj: Any) -> Any:
    """Recursively clean NaN and Infinity values from data."""
    if isinstance(obj, float):
        if np.isnan(obj):
            return None
        elif np.isinf(obj):
            return None  # or "Infinity" if you want to preserve the information
        return obj
    elif isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(item) for item in obj]
    elif isinstance(obj, np.ndarray):
        return clean_for_json(obj.tolist())
    elif isinstance(obj, pd.DataFrame):
        # Replace NaN and inf values in DataFrame
        df_clean = obj.replace([np.inf, -np.inf], np.nan)
        df_clean = df_clean.where(pd.notnull(df_clean), None)
        return df_clean.to_dict(orient='records')
    elif isinstance(obj, pd.Series):
        return clean_for_json(obj.to_dict())
    return obj

# --- Application Lifecycle (Scheduler Start/Stop & DB Creation) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup: Initializing...")
    # Start the data aggregation scheduler
    logger.info("Starting data aggregation scheduler...")
    start_scheduler()
    yield # Application runs here
    logger.info("Application shutdown: Stopping data aggregation scheduler...")
    shutdown_scheduler()
    logger.info("Scheduler stopped.")

# --- FastAPI App Creation ---
# Pass the lifespan manager to the FastAPI app
app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods
    allow_headers=["*"], # Allows all headers
)

# --- GraphQL Endpoint ---
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

# --- REST Endpoints ---
@app.get("/")
def read_root():
    logger.info("Root endpoint accessed.")
    return {"message": "Control-UX API is running. Visit /graphql for the GraphQL interface."}

# New endpoint to inspect the cache directly
@app.get("/api/cache-debug")
def get_cache_debug():
    """Returns the entire content of the data cache for debugging, with a timestamp."""
    logger.info("Cache debug endpoint accessed.")
    cache_content = get_aggregated_data() # Use the existing function to get cache data
    current_time = datetime.datetime.now().isoformat()
    # Clean the cache content before returning
    cleaned_cache_content = clean_for_json(cache_content)
    response_data = {
        "timestamp": current_time,
        "cache_content": cleaned_cache_content
    }
    logger.debug(f"Returning cache debug data")
    return response_data

# Endpoint to serve aggregated data directly (as requested by UX)
@app.get("/aggregated-data")
def get_aggregated_data_endpoint():
    """Returns the current aggregated data."""
    logger.info("Aggregated data endpoint accessed.")
    # Wrap the call in a try-except block for debugging
    try:
        data = get_aggregated_data()
        # Clean the data before returning to handle NaN and Infinity values
        cleaned_data = clean_for_json(data)
        logger.debug("Returning cleaned aggregated data.")
        return cleaned_data
    except Exception as e:
        logger.error(f"ERROR in get_aggregated_data() or endpoint: {e}", exc_info=True)
        # Raise an HTTPException to see if the error response gets through with CORS headers
        raise HTTPException(status_code=500, detail=f"Internal server error while fetching aggregated data: {e}")

# --- Application Details Endpoint ---
@app.get("/api/application-details/{app_id}")
def get_app_details(app_id: str):    
    # Log entry point *immediately*
    logger.info(f"==> Handling request for /api/application-details/{app_id}")
    current_time = datetime.datetime.now().isoformat()

    try:
        details = get_application_details(app_id) # Call the function to get data

        if not details:
            logger.warning(f"No details found for appId: '{app_id}'. Returning 404.")
            # Raise the standard 404 exception
            raise HTTPException(status_code=404, detail=f"Details not found for application: {app_id}")

        logger.debug(f"Returning details for appId: '{app_id}'")
        # Add timestamp to the successful response
        return {
            "timestamp": current_time,
            "details": details
        }
    except Exception as e:
        # Log any unexpected errors during detail fetching
        logger.error(f"Error fetching details for appId '{app_id}': {e}", exc_info=True)
        # Re-raise HTTPException or raise a 500 Internal Server Error
        if isinstance(e, HTTPException):
            raise e
        else:
            raise HTTPException(status_code=500, detail="Internal server error while fetching application details")

# --- Cache Health Endpoint ---
@app.get("/api/cache-health")
def get_cache_health_endpoint():
    """Endpoint to check cache health and status."""
    logger.info("==> Handling request for /api/cache-health")
    current_time = datetime.datetime.now().isoformat()
    
    try:
        health_data = get_cache_health()
        health_data["timestamp"] = current_time
        
        # Add status indicators
        if health_data.get("cache_age_seconds"):
            age_minutes = health_data["cache_age_seconds"] / 60
            if age_minutes > 5:
                health_data["status"] = "warning"
                health_data["message"] = f"Cache is {age_minutes:.1f} minutes old"
            elif age_minutes > 3:
                health_data["status"] = "caution"
                health_data["message"] = f"Cache is {age_minutes:.1f} minutes old"
            else:
                health_data["status"] = "healthy"
                health_data["message"] = "Cache is fresh"
        else:
            health_data["status"] = "unknown"
            health_data["message"] = "Cache age unknown"
        
        logger.info(f"Cache health check completed: {health_data['status']}")
        return health_data
        
    except Exception as e:
        logger.error(f"ERROR in cache health check: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while checking cache health")

# --- Fitness Function Editor Endpoints ---
@app.get("/api/fitness-functions")
def list_fitness_functions():
    """List all available fitness functions with their metadata."""
    logger.info("Listing all fitness functions")
    from fitness_logic.registry import FitnessFunctionRegistry
    
    functions = []
    for func_class in FitnessFunctionRegistry.get_all_functions():
        metadata = func_class.get_metadata()
        # Get the module name to derive the file name
        module_name = func_class.__module__.split('.')[-1]
        functions.append({
            "id": metadata["id"],
            "name": metadata["name"],
            "description": metadata["description"],
            "rule_id": metadata["rule_id"],
            "module_name": module_name,
            "class_name": func_class.__name__
        })
    
    return {"fitness_functions": functions}

@app.get("/api/fitness-functions/{module_name}/source")
def get_fitness_function_source(module_name: str):
    """Get the source code of a specific fitness function."""
    logger.info(f"Retrieving source code for fitness function: {module_name}")
    
    import os
    fitness_logic_dir = os.path.join(API_DIR, "fitness_logic")
    file_path = os.path.join(fitness_logic_dir, f"{module_name}.py")
    
    if not os.path.exists(file_path):
        logger.warning(f"Fitness function file not found: {file_path}")
        raise HTTPException(status_code=404, detail=f"Fitness function '{module_name}' not found")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        return {
            "module_name": module_name,
            "source_code": source_code,
            "file_path": f"fitness_logic/{module_name}.py"
        }
    except Exception as e:
        logger.error(f"Error reading fitness function source: {e}")
        raise HTTPException(status_code=500, detail="Error reading fitness function source")

@app.put("/api/fitness-functions/{module_name}/source")
def save_fitness_function_source(module_name: str, request: dict):
    """Save the source code of a specific fitness function."""
    logger.info(f"Saving source code for fitness function: {module_name}")
    
    import os
    import ast
    import importlib
    import sys
    
    fitness_logic_dir = os.path.join(API_DIR, "fitness_logic")
    file_path = os.path.join(fitness_logic_dir, f"{module_name}.py")
    
    if not os.path.exists(file_path):
        logger.warning(f"Fitness function file not found: {file_path}")
        raise HTTPException(status_code=404, detail=f"Fitness function '{module_name}' not found")
    
    source_code = request.get("source_code", "")
    
    # Validate Python syntax
    try:
        ast.parse(source_code)
    except SyntaxError as e:
        logger.warning(f"Syntax error in fitness function code: {e}")
        return {
            "status": "error",
            "message": f"Syntax error: {str(e)}",
            "line": e.lineno,
            "offset": e.offset
        }
    
    # Create timestamped backup
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(fitness_logic_dir, "backups")
    
    # Create backups directory if it doesn't exist
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    backup_filename = f"{module_name}_{timestamp}.py.bak"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            backup_content = f.read()
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(backup_content)
        logger.info(f"Created backup: {backup_filename}")
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        raise HTTPException(status_code=500, detail="Error creating backup")
    
    # Save the new code
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(source_code)
        
        # Try to reload the module
        module_full_name = f"fitness_logic.{module_name}"
        if module_full_name in sys.modules:
            # Remove from module cache
            del sys.modules[module_full_name]
        
        # Force reimport
        try:
            module = importlib.import_module(module_full_name)
            importlib.reload(module)
            
            # Re-register the fitness function in the registry
            from fitness_logic.registry import FitnessFunctionRegistry
            # The registry should auto-detect the change on next request
            
            logger.info(f"Successfully saved and reloaded fitness function: {module_name}")
            return {
                "status": "success",
                "message": f"Fitness function saved and reloaded successfully. Backup created: {backup_filename}",
                "backup": backup_filename
            }
            
        except Exception as import_error:
            # Restore from backup if import fails
            logger.error(f"Error importing updated module: {import_error}")
            try:
                with open(backup_path, 'r', encoding='utf-8') as f:
                    backup_content = f.read()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(backup_content)
                logger.info(f"Restored from backup: {backup_filename}")
            except:
                logger.error("Failed to restore from backup")
            
            return {
                "status": "error",
                "message": f"Import error: {str(import_error)}. Code reverted from backup.",
                "details": str(import_error)
            }
            
    except Exception as e:
        logger.error(f"Error saving fitness function source: {e}")
        # Try to restore backup
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_content = f.read()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(backup_content)
        except:
            pass
        raise HTTPException(status_code=500, detail="Error saving fitness function source")

# --- Create New Fitness Function Endpoint ---
@app.post("/api/fitness-functions/create")
def create_fitness_function(request: dict):
    """Create a new fitness function from template."""
    logger.info("Creating new fitness function")
    
    import os
    import re
    
    # Extract parameters
    name = request.get("name", "")
    description = request.get("description", "")
    
    # Validate name
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    
    # Generate file-safe names
    module_name = re.sub(r'[^a-z0-9_]', '_', name.lower().replace(' ', '_'))
    class_name = ''.join(word.capitalize() for word in name.split()) + "FitnessFunction"
    rule_id = module_name
    
    # Check if file already exists
    fitness_logic_dir = os.path.join(API_DIR, "fitness_logic")
    file_path = os.path.join(fitness_logic_dir, f"{module_name}.py")
    
    if os.path.exists(file_path):
        raise HTTPException(status_code=409, detail=f"Fitness function '{module_name}' already exists")
    
    # Read template
    template_path = os.path.join(fitness_logic_dir, "template.py")
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
    except Exception as e:
        logger.error(f"Error reading template: {e}")
        raise HTTPException(status_code=500, detail="Error reading template")
    
    # Replace placeholders
    content = template_content.format(
        name=name,
        description=description or f"Fitness function for {name}",
        class_name=class_name,
        id=module_name,
        rule_id=rule_id
    )
    
    # Create the new file
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Created new fitness function: {module_name}")
        
        return {
            "status": "success",
            "module_name": module_name,
            "class_name": class_name,
            "file_path": f"fitness_logic/{module_name}.py",
            "message": f"Fitness function '{name}' created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating fitness function: {e}")
        raise HTTPException(status_code=500, detail="Error creating fitness function")

# --- Data Schema Endpoint ---
@app.get("/api/data-schema")
def get_data_schema():
    """Returns the schema of all available data feeds."""
    logger.info("Data schema endpoint accessed.")
    
    try:
        # Get the aggregated data
        data = get_aggregated_data()
        raw_data = data.get('raw_data', {})
        
        # Build schema information
        schema = {}
        for provider_id, provider_data in raw_data.items():
            if isinstance(provider_data, dict) and provider_data:
                # Get the first application's data as a sample
                first_app = next(iter(provider_data.values()))
                if isinstance(first_app, dict):
                    # Extract field names and types
                    fields = {}
                    for field_name, field_value in first_app.items():
                        field_type = type(field_value).__name__
                        if field_type == 'NoneType':
                            field_type = 'null'
                        elif field_type == 'str':
                            field_type = 'string'
                        elif field_type in ['int', 'float']:
                            field_type = 'number'
                        fields[field_name] = field_type
                    
                    # Get provider metadata
                    provider_name = provider_id.replace('_', ' ').title()
                    if hasattr(PROVIDER_CONFIGS, provider_id):
                        config = PROVIDER_CONFIGS.get(provider_id, {})
                        if 'name' in config:
                            provider_name = config['name']
                    
                    schema[provider_id] = {
                        "name": provider_name,
                        "fields": fields,
                        "sample_apps": list(provider_data.keys())[:5],  # First 5 apps as examples
                        "total_apps": len(provider_data)
                    }
        
        return {
            "schema": schema,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching data schema: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching data schema")

# --- Evidence Scanner Endpoints ---
@app.post("/api/evidence/scan")
def scan_evidence(evidence_path: str = None, bucket_hours: int = 2):
    """Scan evidence folders and analyze control runs."""
    logger.info(f"==> Scanning evidence folders: path={evidence_path}, bucket_hours={bucket_hours}")
    
    try:
        # Use provided path or default to a common evidence location
        if not evidence_path:
            # Try to find evidence folder relative to API directory
            possible_paths = [
                os.path.join(API_DIR, "..", "evidence"),
                os.path.join(API_DIR, "..", "..", "evidence"),
                "C:/evidence",  # Windows path from screenshot
                "/mnt/c/evidence"  # WSL path
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    evidence_path = path
                    break
            
            if not evidence_path:
                raise HTTPException(
                    status_code=400, 
                    detail="No evidence path provided and could not find default evidence folder"
                )
        
        # Create scanner and run analysis
        scanner = EvidenceScanner(evidence_path)
        analysis = scanner.get_latest_analysis(bucket_hours=bucket_hours)
        
        logger.info(f"Evidence scan completed: {analysis['summary']}")
        return analysis
        
    except Exception as e:
        logger.error(f"Error scanning evidence: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error scanning evidence: {str(e)}")

@app.get("/api/evidence/latest")
def get_latest_evidence_analysis():
    """Get the latest evidence analysis with default settings."""
    return scan_evidence()

@app.get("/api/evidence-folders")
def list_evidence_folders():
    """List all evidence folders with their report status."""
    logger.info("==> Fetching evidence folders")
    
    try:
        # Find evidence folder path
        evidence_path = None
        possible_paths = [
            os.path.join(API_DIR, "..", "evidence"),
            os.path.join(API_DIR, "..", "..", "evidence"),
            "C:/evidence",
            "/mnt/c/evidence"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                evidence_path = path
                break
        
        if not evidence_path:
            logger.warning("Evidence folder not found")
            return []
        
        folders = []
        for folder_name in os.listdir(evidence_path):
            folder_path = os.path.join(evidence_path, folder_name)
            if os.path.isdir(folder_path):
                # Check if Evidence_report.html exists
                report_path = os.path.join(folder_path, "Evidence_report.html")
                has_report = os.path.exists(report_path)
                
                # Get folder modification time
                timestamp = None
                if has_report:
                    stat = os.stat(report_path)
                    timestamp = datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
                
                folders.append({
                    "name": folder_name,
                    "path": folder_name,
                    "hasReport": has_report,
                    "timestamp": timestamp
                })
        
        # Sort by name
        folders.sort(key=lambda x: x["name"])
        
        logger.info(f"Found {len(folders)} evidence folders")
        return folders
        
    except Exception as e:
        logger.error(f"Error listing evidence folders: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing evidence folders: {str(e)}")

@app.get("/evidence/{folder_name}/Evidence_report.html")
def serve_evidence_report(folder_name: str):
    """Serve the Evidence_report.html file from a specific evidence folder."""
    logger.info(f"==> Serving evidence report for folder: {folder_name}")
    
    try:
        # Find evidence folder path
        evidence_path = None
        possible_paths = [
            os.path.join(API_DIR, "..", "evidence"),
            os.path.join(API_DIR, "..", "..", "evidence"),
            "C:/evidence",
            "/mnt/c/evidence"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                evidence_path = path
                break
        
        if not evidence_path:
            raise HTTPException(status_code=404, detail="Evidence folder not found")
        
        # Construct full path to the report
        report_path = os.path.join(evidence_path, folder_name, "Evidence_report.html")
        
        if not os.path.exists(report_path):
            raise HTTPException(status_code=404, detail=f"Evidence report not found for folder: {folder_name}")
        
        # Return the HTML file
        return FileResponse(report_path, media_type="text/html")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving evidence report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error serving evidence report: {str(e)}")

# --- Control Script Discovery Endpoints ---
@app.get("/api/control-scripts")
def list_control_scripts():
    """List all discovered control scripts and their steps."""
    logger.info("==> Fetching control scripts")
    
    try:
        # Read configuration
        config = configparser.ConfigParser()
        config_path = os.path.join(API_DIR, 'settings.ini')
        config.read(config_path)
        
        # Check if control discovery is enabled
        if not config.getboolean('control_discovery', 'enabled', fallback=False):
            logger.info("Control discovery is disabled")
            return {"enabled": False, "scripts": {}}
        
        # Get script path from config
        script_path = config.get('control_discovery', 'script_path', fallback=None)
        if script_path and not os.path.isabs(script_path):
            # Make relative paths relative to API directory
            script_path = os.path.join(API_DIR, script_path)
        
        # Get control discovery instance
        discovery = get_control_discovery(script_path)
        
        # Discover scripts
        scripts = discovery.discover_control_scripts()
        
        return {
            "enabled": True,
            "script_path": script_path,
            "scripts": scripts,
            "total_scripts": len(scripts),
            "total_steps": sum(len(steps) for steps in scripts.values())
        }
        
    except Exception as e:
        logger.error(f"Error discovering control scripts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error discovering control scripts: {str(e)}")

@app.get("/api/control-scripts/{script_name}/steps")
def get_control_script_steps(script_name: str):
    """Get steps for a specific control script."""
    logger.info(f"==> Fetching steps for control script: {script_name}")
    
    try:
        # Read configuration
        config = configparser.ConfigParser()
        config_path = os.path.join(API_DIR, 'settings.ini')
        config.read(config_path)
        
        # Check if control discovery is enabled
        if not config.getboolean('control_discovery', 'enabled', fallback=False):
            raise HTTPException(status_code=403, detail="Control discovery is disabled")
        
        # Get script path from config
        script_path = config.get('control_discovery', 'script_path', fallback=None)
        if script_path and not os.path.isabs(script_path):
            script_path = os.path.join(API_DIR, script_path)
        
        # Get control discovery instance
        discovery = get_control_discovery(script_path)
        
        # Get script details
        steps = discovery.get_script_details(script_name)
        
        if steps is None:
            raise HTTPException(status_code=404, detail=f"Control script not found: {script_name}")
        
        return {
            "script_name": script_name,
            "steps": steps,
            "total_steps": len(steps)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching control script steps: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching control script steps: {str(e)}")

@app.get("/api/control-scripts/search")
def search_control_steps(query: str):
    """Search for control steps by name or description."""
    logger.info(f"==> Searching control steps: query='{query}'")
    
    try:
        # Read configuration
        config = configparser.ConfigParser()
        config_path = os.path.join(API_DIR, 'settings.ini')
        config.read(config_path)
        
        # Check if control discovery is enabled
        if not config.getboolean('control_discovery', 'enabled', fallback=False):
            raise HTTPException(status_code=403, detail="Control discovery is disabled")
        
        # Get script path from config
        script_path = config.get('control_discovery', 'script_path', fallback=None)
        if script_path and not os.path.isabs(script_path):
            script_path = os.path.join(API_DIR, script_path)
        
        # Get control discovery instance
        discovery = get_control_discovery(script_path)
        
        # Search steps
        results = discovery.search_steps(query)
        
        return {
            "query": query,
            "results": results,
            "total_results": len(results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching control steps: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error searching control steps: {str(e)}")

# --- Main Execution (for direct run) ---
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server directly...")
    # Note: Uvicorn's reload doesn't always work perfectly with lifespan context
    # For development, running without reload might be more stable for scheduler testing
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
