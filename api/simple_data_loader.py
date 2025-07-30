"""
Simple CSV data loader that assumes first column is always app_id.
No schema detection, no migration, just load what's in the file.
"""
import pandas as pd
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def load_csv_data(provider_id: str, config: Dict[str, str], api_dir: str) -> Optional[Dict[str, Dict[str, Any]]]:
    """
    Load CSV data with simple assumption: first column is always app_id.
    Returns a dictionary mapping app_id to row data.
    
    Args:
        provider_id: The provider identifier
        config: Configuration dict with 'file_path' key
        api_dir: The API directory base path
        
    Returns:
        Dictionary mapping app_id to row data, or None if error
    """
    if not config or 'file_path' not in config:
        logger.warning(f"No file_path in config for provider {provider_id}")
        return None
    
    # Construct absolute path
    file_path = os.path.join(api_dir, config['file_path'])
    
    if not os.path.exists(file_path):
        logger.warning(f"File not found for provider {provider_id}: {file_path}")
        return None
    
    try:
        # Read CSV file
        df = pd.read_csv(file_path)
        
        if df.empty:
            logger.warning(f"Empty CSV file for provider {provider_id}")
            return None
        
        # First column is app_id
        app_id_col = df.columns[0]
        
        # Convert app_id column to string to ensure consistency
        df[app_id_col] = df[app_id_col].astype(str)
        
        # Rename first column to 'app_id' for consistency in the output
        df = df.rename(columns={app_id_col: 'app_id'})
        
        # Convert to dictionary with app_id as key
        result = df.set_index('app_id').to_dict(orient='index')
        
        logger.info(f"Loaded {len(result)} records for provider {provider_id}")
        logger.debug(f"Columns in {provider_id}: {list(df.columns)}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error loading CSV for provider {provider_id}: {e}")
        return None