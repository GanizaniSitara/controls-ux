# filepath: c:\git\FitnessFunctions\api\connectors\base_connector.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class BaseConnector(ABC):
    """Abstract base class for all data connectors."""

    def __init__(self, params: Dict[str, Any]):
        """Initializes the connector with its specific parameters."""
        self.params = params
        logger.info(f"Initializing {self.__class__.__name__} with params: {params}")

    @abstractmethod
    def fetch_data(self, app_config: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Fetches data from the configured source.

        Args:
            app_config: Optional application-specific configuration that might
                        be needed for fetching (e.g., app-specific API key or query param).

        Returns:
            A dictionary containing the fetched data, or None if fetching fails.
            The structure of the returned dictionary depends on the source,
            it will be processed further by the Provider.
        """
        pass
