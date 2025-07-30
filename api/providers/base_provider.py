# c:\git\FitnessFunctions\api\providers\base_provider.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Literal
import os
import configparser
import logging

logger = logging.getLogger(__name__)

Status = Literal['healthy', 'warning', 'critical', 'unknown']

class BaseFitnessProvider(ABC):
    """Abstract base class for all fitness function providers."""

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Return the unique identifier for this provider."""
        pass

    def get_csv_filepath(self) -> str:
        """
        Get the CSV file path for this provider from settings.ini.

        Returns:
            The full path to the CSV file.
        """
        # Default path in case settings are missing or invalid
        default_file_path = f"data_mock\\{self.provider_id}.csv"
        file_path = default_file_path # Initialize with default

        # Read settings.ini file
        config = configparser.ConfigParser()
        settings_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'settings.ini')

        if not os.path.exists(settings_path):
            logger.warning(f"Settings file not found at {settings_path}, using default CSV path: {default_file_path}")
            # Keep the initialized default_file_path
        else:
            try:
                config.read(settings_path)

                # Get provider name without version suffix for settings lookup
                provider_base_name = self.provider_id.split('_v')[0] if '_v' in self.provider_id else self.provider_id

                # Get file path from settings or use default if not found
                if 'providers' in config and provider_base_name in config['providers']:
                    file_path = config['providers'][provider_base_name] # Override default if found
                    logger.info(f"Using CSV file path from settings for provider {self.provider_id}: {file_path}")
                else:
                    logger.warning(f"Provider {provider_base_name} not found in settings, using default CSV path: {default_file_path}")
                    # Keep the initialized default_file_path
            except Exception as e:
                logger.error(f"Error reading settings file: {e}, using default CSV path: {default_file_path}")
                # Keep the initialized default_file_path in case of error

        # Build the full path to the CSV file
        base_dir = os.path.dirname(os.path.dirname(__file__))  # Points to api directory
        return os.path.join(base_dir, file_path)

    @abstractmethod
    def get_fitness_data(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetches or calculates fitness data for a specific application.

        Args:
            app_config: A dictionary containing application-specific configuration
                        needed by the provider (e.g., repo URL, API endpoint, file path).

        Returns:
            A dictionary containing:
            {
                "status": Status, # The calculated status for this control area
                "details": { ... } # A dictionary with specific metrics/details
            }
        """
        pass

