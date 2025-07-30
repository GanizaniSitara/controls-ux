from .base_provider import BaseFitnessProvider, Status
from typing import Dict, Any, Optional
import logging
import os
import csv

logger = logging.getLogger(__name__)

class VendorMgmtProvider(BaseFitnessProvider):
    """Provides fitness data related to vendor management based on CSV data."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the provider. Config is currently unused as we read directly from mock.
        """
        self.config = config
        # Get CSV file path from settings.ini
        self.mock_file_path = self.get_csv_filepath()
        logger.info(f"[{self.provider_id}] Initialized to read from mock file: {self.mock_file_path}")

    @property
    def provider_id(self) -> str:
        return "vendor_mgmt_v1"

    def get_fitness_data(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        """Returns vendor management metrics read directly from the mock CSV file."""
        app_id = app_config.get('app_id')
        if not app_id:
            logger.warning(f"[{self.provider_id}] app_id missing in app_config. Cannot fetch specific data.")
            return {"status": "unknown", "details": {"error": "app_id missing."}}
        
        # Read data directly from the mock CSV file
        raw_data: Optional[Dict[str, Any]] = None
        try:
            # Use CSV connector to fetch data for this app
            connector = self.get_connector()
            if not connector:
                logger.error(f"[{self.provider_id}] Failed to create connector.")
                return {"status": "unknown", "details": {"error": "Failed to create connector."}}
            
            raw_data = connector.fetch_data(app_config)
            if not raw_data:
                logger.warning(f"[{self.provider_id}] No data found for app {app_id}")
                return {"status": "unknown", "details": {"error": f"No data found for app {app_id}"}}
            
            # Extract important metrics
            vendor_compliance_score = float(raw_data.get('VendorComplianceScore', 0))
            contract_renewal_status = raw_data.get('ContractRenewalStatus', 'unknown')
            vendor_response_time = float(raw_data.get('VendorResponseTime', 0))
            support_quality_rating = float(raw_data.get('SupportQualityRating', 0))
            
            # Determine status based on the metrics
            status: Status = 'healthy'
            warnings = []
            
            if vendor_compliance_score < 75:
                status = 'critical'
                warnings.append(f"Vendor compliance score is critical: {vendor_compliance_score}%")
            elif vendor_compliance_score < 85:
                status = 'warning'
                warnings.append(f"Vendor compliance score needs improvement: {vendor_compliance_score}%")
                
            if contract_renewal_status.lower() in ['expired', 'expiring']:
                if status != 'critical':
                    status = 'warning'
                warnings.append(f"Contract status is {contract_renewal_status}")
            
            if vendor_response_time > 12:
                if status != 'critical':
                    status = 'warning'
                warnings.append(f"Vendor response time is high: {vendor_response_time} hours")
            
            if support_quality_rating < 70:
                if status != 'critical':
                    status = 'warning'
                warnings.append(f"Support quality rating is low: {support_quality_rating}/100")
            
            details = {
                "vendor_compliance_score": vendor_compliance_score,
                "contract_renewal_status": contract_renewal_status,
                "vendor_response_time": vendor_response_time,
                "support_quality_rating": support_quality_rating,
                "warnings": warnings
            }
            
            logger.info(f"[{self.provider_id}] Processed mock data for app: {app_id}, Status: {status}")
            return {
                "status": status,
                "details": details
            }
        except ValueError as e:
            logger.error(f"[{self.provider_id}] Error converting data types for app {app_id}: {e}. Data: {raw_data}", exc_info=True)
            return {"status": "unknown", "details": {"error": f"Error processing data types: {e}"}}
        except Exception as e:
            logger.error(f"[{self.provider_id}] Error processing raw data for app {app_id}: {e}. Data: {raw_data}", exc_info=True)
            return {"status": "unknown", "details": {"error": f"Error processing data: {e}"}}
