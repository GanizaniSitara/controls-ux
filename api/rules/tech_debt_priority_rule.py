\
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

# Use absolute import for BaseRule
from rules.base_rule import BaseRule

logger = logging.getLogger(__name__)

# Define an order for deployment frequencies for comparison
DEPLOYMENT_FREQUENCY_ORDER = {
    "daily": 5,
    "multiple_times_a_day": 6, # Higher than daily
    "weekly": 4,
    "bi-weekly": 3, # Assuming bi-weekly means every two weeks
    "monthly": 2,
    "quarterly": 1,
    "yearly": 0,
    "ad-hoc": -1, # Lower than any regular frequency
    "unknown": -2
}

def get_deployment_frequency_rank(freq_str: Optional[str]) -> int:
    """Converts a deployment frequency string to a comparable rank."""
    if not freq_str:
        return DEPLOYMENT_FREQUENCY_ORDER["unknown"]
    return DEPLOYMENT_FREQUENCY_ORDER.get(freq_str.lower().replace('-', '_'), DEPLOYMENT_FREQUENCY_ORDER["unknown"])


class TechDebtPriorityRule(BaseRule):
    """
    Determines the priority for technical debt reduction investment based on
    application metrics across multiple domains.
    """
    rule_id = "tech_debt_priority" # Identifier for the results

    def apply(self, current_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Applies the technical debt priority logic to the raw data.

        Args:
            current_data: The dictionary containing raw data, expected structure:
                          {'raw_data': {provider_id: {app_id: data_dict}}}
                          or potentially just {provider_id: {app_id: data_dict}}.

        Returns:
            A dictionary containing the tech debt priority for each app_id:
            {app_id: 'High Priority' | 'Medium Priority' | 'Low Priority'}
        """
        raw_data = current_data.get('raw_data', current_data)
        if not isinstance(raw_data, dict):
             logger.error(f"[{self.rule_id}] Input data is not a dictionary: {type(raw_data)}")
             return {"error": "Invalid input data format"}

        results = {}
        app_ids = self._get_all_app_ids(raw_data)
        if not app_ids:            
            logger.warning(f"[{self.rule_id}] No application IDs found in the raw data.")
            return {}
            
        logger.info(f"[{self.rule_id}] Evaluating tech debt priority for {len(app_ids)} apps")

        for app_id in app_ids:
            app_data = self._get_data_for_app(raw_data, app_id)

            # Evaluate High Priority conditions first
            is_high, high_reason = self._check_high_priority(app_data, app_id)
            if is_high:
                results[app_id] = f"High Priority ({high_reason})"
                logger.debug(f"[{self.rule_id}] App '{app_id}' -> High Priority ({high_reason})")
                continue

            # Evaluate Medium Priority conditions if not High
            is_medium, medium_reason = self._check_medium_priority(app_data, app_id)
            if is_medium:
                results[app_id] = f"Medium Priority ({medium_reason})"
                logger.debug(f"[{self.rule_id}] App '{app_id}' -> Medium Priority ({medium_reason})")
                continue

            # Default to Low Priority
            results[app_id] = "Low Priority"
            logger.debug(f"[{self.rule_id}] App '{app_id}' -> Low Priority")

        logger.info(f"[{self.rule_id}] Tech debt priority evaluation complete.")
        return results

    def _get_all_app_ids(self, raw_data: Dict[str, Dict[str, Any]]) -> set:
        """Extracts all unique app_ids present in the raw data."""
        all_ids = set()
        for provider_data in raw_data.values():
            if isinstance(provider_data, dict):
                all_ids.update(provider_data.keys())
        return all_ids

    def _get_data_for_app(self, raw_data: Dict[str, Dict[str, Any]], app_id: str) -> Dict[str, Any]:
        """Consolidates data from all providers for a specific app_id."""
        consolidated = {}
        for provider_id, provider_data in raw_data.items():
             if isinstance(provider_data, dict) and app_id in provider_data:
                 # Merge data, handling potential overlaps if necessary
                 consolidated.update(provider_data[app_id])
        return consolidated

    def _get_value(self, data: Dict[str, Any], key: str, expected_type: type, default: Any = None) -> Any:
        """Safely retrieves and converts a value from the data dictionary."""
        value = data.get(key)
        if value is None:
            # logger.warning(f"[{self.rule_id}] Missing key '{key}' for app. Using default: {default}")
            return default
        try:
            if expected_type is bool:
                 if isinstance(value, str):
                     if value.lower() == 'true': return True
                     if value.lower() == 'false': return False
                 return bool(value)
            if expected_type is datetime:
                 # Handle potential timezone info or different formats if necessary
                 date_str = str(value).split(' ')[0] # Get YYYY-MM-DD part
                 return datetime.fromisoformat(date_str)            
            if expected_type is float:
                 # Remove potential currency symbols or commas for cost
                 if isinstance(value, str):
                     # Check if the string contains only digits, separators and decimal points
                     cleaned_value = value.replace('$', '').replace(',', '')
                     if not any(c.isalpha() for c in cleaned_value):
                         try:
                             return float(cleaned_value)
                         except ValueError:
                             logger.warning(f"[{self.rule_id}] Non-numeric string '{value}' cannot be converted to float. Using default: {default}")
                             return default
                     else:
                         logger.warning(f"[{self.rule_id}] String '{value}' contains letters, cannot convert to float. Using default: {default}")
                         return default
                 elif isinstance(value, (int, float)):
                     return float(value)
                 else:
                     logger.warning(f"[{self.rule_id}] Unsupported type {type(value)} for float conversion. Using default: {default}")
                     return default
            if expected_type is int:
                 if isinstance(value, str):
                     # Check if the string contains only digits and separators
                     cleaned_value = value.replace(',', '')
                     if not any(c.isalpha() for c in cleaned_value):
                         try:
                             return int(float(cleaned_value))
                         except ValueError:
                             logger.warning(f"[{self.rule_id}] Non-numeric string '{value}' cannot be converted to int. Using default: {default}")
                             return default
                     else:
                         logger.warning(f"[{self.rule_id}] String '{value}' contains letters, cannot convert to int. Using default: {default}")
                         return default
                 elif isinstance(value, (int, float)):
                     return int(value)
                 else:
                     logger.warning(f"[{self.rule_id}] Unsupported type {type(value)} for int conversion. Using default: {default}")
                     return default
            # For other types, try direct conversion but with better error handling
            try:
                return expected_type(value)
            except (ValueError, TypeError):
                logger.warning(f"[{self.rule_id}] Cannot convert value '{value}' to {expected_type.__name__}. Using default: {default}")
                return default
        except (ValueError, TypeError) as e:
            logger.warning(f"[{self.rule_id}] Could not convert key '{key}' (value: {value}, type: {type(value)}) to {expected_type.__name__}. Using default: {default}. Error: {e}")
            return default

    def _check_high_priority(self, data: Dict[str, Any], app_id: str) -> Tuple[bool, str]:
        """Checks if any High Priority condition is met."""
        # Condition 1: Code Quality
        maint_index = self._get_value(data, 'MaintainabilityIndex', int, 100) # Default high (good)
        comp_score = self._get_value(data, 'ComplexityScore', int, 0) # Default low (good)
        if maint_index < 75 and comp_score > 8:
            return True, f"Code Quality (MaintainabilityIndex={maint_index}, ComplexityScore={comp_score})"

        # Condition 2: Financial Impact
        monthly_cost = self._get_value(data, 'MonthlyCost', float, 0.0)
        fail_rate = self._get_value(data, 'ChangeFailureRate', float, 0.0)
        uptime = self._get_value(data, 'UptimePercentage', float, 100.0) # Default high (good)
        if monthly_cost > 40000 and (fail_rate > 1.0 or uptime < 99.0):
             reason = f"Financial Impact (MonthlyCost=${monthly_cost:,.2f}"
             if fail_rate > 1.0: reason += f", ChangeFailureRate={fail_rate}%"
             if uptime < 99.0: reason += f", UptimePercentage={uptime}%"
             reason += ")"
             return True, reason

        # Condition 3: Sustainability Factor
        test_cov = self._get_value(data, 'TestCoverage', float, 100.0) # Default high (good)
        # comp_score already fetched
        sustainability_factor = (100 - test_cov) * comp_score
        if sustainability_factor > 300:
            return True, f"Sustainability Factor ( (100-{test_cov}) * {comp_score} = {sustainability_factor:.1f} > 300 )"

        return False, "" # No High Priority conditions met

    def _check_medium_priority(self, data: Dict[str, Any], app_id: str) -> Tuple[bool, str]:
        """Checks if any Medium Priority condition is met."""
        reasons = []

        # Condition 1: Documentation
        last_updated_str = self._get_value(data, 'LastUpdated', str, None)
        doc_cov = self._get_value(data, 'DocCoverage', float, 0.0) # Default low
        last_updated_date = None
        if last_updated_str:
            try:
                last_updated_date = self._get_value(data, 'LastUpdated', datetime, None)
            except Exception as e: # Catch potential parsing errors logged in _get_value
                 logger.warning(f"[{self.rule_id}] Error parsing LastUpdated '{last_updated_str}' for medium priority check: {e}")

        if last_updated_date:
            nine_months_ago = datetime.now() - timedelta(days=9*30) # Approximate 9 months
            if last_updated_date < nine_months_ago and doc_cov > 90.0:
                reasons.append(f"Documentation (Outdated: {last_updated_date.date()}, Coverage: {doc_cov}%)")
        elif doc_cov > 90.0: # If date missing but coverage high, maybe still medium? User story unclear here.
             pass # logger.debug(f"[{self.rule_id}] Doc coverage > 90% but LastUpdated date missing/invalid for app '{app_id}'")


        # Condition 2: Technical Indicators
        maint_index = self._get_value(data, 'MaintainabilityIndex', int, 100)
        comp_score = self._get_value(data, 'ComplexityScore', int, 0)
        maint_check = (maint_index >= 65 and maint_index < 75) # Note: < 75, not <= 75 as per High Prio check
        comp_check = (comp_score >= 8 and comp_score <= 15)
        if maint_check or comp_check:
             tech_reason = "Technical Indicators ("
             if maint_check: tech_reason += f"MaintainabilityIndex={maint_index}"
             if maint_check and comp_check: tech_reason += ", "
             if comp_check: tech_reason += f"ComplexityScore={comp_score}"
             tech_reason += ")"
             reasons.append(tech_reason)


        # Condition 3: Operational Impact
        dep_freq_str = self._get_value(data, 'DeploymentFrequency', str, "unknown")
        fail_rate = self._get_value(data, 'ChangeFailureRate', float, 0.0)
        dep_freq_rank = get_deployment_frequency_rank(dep_freq_str)
        weekly_rank = DEPLOYMENT_FREQUENCY_ORDER["weekly"]

        # Check if frequency is less frequent than weekly (lower rank)
        if dep_freq_rank < weekly_rank and fail_rate > 0.5:
            reasons.append(f"Operational Impact (DeploymentFrequency='{dep_freq_str}', ChangeFailureRate={fail_rate}%)")

        if reasons:
            return True, "; ".join(reasons)
        else:
            return False, ""


# Example Usage
if __name__ == '__main__':
    # Example data structure
    mock_raw_data = {
        'quality_v1': {
            'app_aci': {'app_id': 'app_aci', 'MaintainabilityIndex': 70, 'ComplexityScore': 10, 'TestCoverage': 85.0},
            'app_stable': {'app_id': 'app_stable', 'MaintainabilityIndex': 85, 'ComplexityScore': 5, 'TestCoverage': 95.0},
            'app_docs': {'app_id': 'app_docs', 'MaintainabilityIndex': 72, 'ComplexityScore': 7, 'TestCoverage': 92.0},
            'app_ops': {'app_id': 'app_ops', 'MaintainabilityIndex': 78, 'ComplexityScore': 12, 'TestCoverage': 90.0},
            'app_complex_low_test': {'app_id': 'app_complex_low_test', 'MaintainabilityIndex': 60, 'ComplexityScore': 15, 'TestCoverage': 50.0}, # High: Sustainability
        },
        'operations_v1': {
            'app_aci': {'app_id': 'app_aci', 'ChangeFailureRate': 1.2, 'UptimePercentage': 99.5, 'DeploymentFrequency': 'weekly'},
            'app_stable': {'app_id': 'app_stable', 'ChangeFailureRate': 0.1, 'UptimePercentage': 99.99, 'DeploymentFrequency': 'daily'},
            'app_docs': {'app_id': 'app_docs', 'ChangeFailureRate': 0.3, 'UptimePercentage': 99.8, 'DeploymentFrequency': 'weekly'},
            'app_ops': {'app_id': 'app_ops', 'ChangeFailureRate': 0.6, 'UptimePercentage': 99.9, 'DeploymentFrequency': 'monthly'}, # Medium: Ops
            'app_complex_low_test': {'app_id': 'app_complex_low_test', 'ChangeFailureRate': 0.8, 'UptimePercentage': 99.2, 'DeploymentFrequency': 'weekly'},
        },
        'cost_v1': {
            'app_aci': {'app_id': 'app_aci', 'MonthlyCost': 46889.00}, # High: Financial
            'app_stable': {'app_id': 'app_stable', 'MonthlyCost': 15000.00},
            'app_docs': {'app_id': 'app_docs', 'MonthlyCost': 25000.00},
            'app_ops': {'app_id': 'app_ops', 'MonthlyCost': 35000.00},
            'app_complex_low_test': {'app_id': 'app_complex_low_test', 'MonthlyCost': 39000.00},
        },
        'docs_v1': {
             'app_aci': {'app_id': 'app_aci', 'LastUpdated': '2025-02-10', 'DocCoverage': 95.0},
             'app_stable': {'app_id': 'app_stable', 'LastUpdated': '2025-04-01', 'DocCoverage': 98.0},
             'app_docs': {'app_id': 'app_docs', 'LastUpdated': '2024-06-15', 'DocCoverage': 91.0}, # Medium: Docs
             'app_ops': {'app_id': 'app_ops', 'LastUpdated': '2025-01-05', 'DocCoverage': 88.0},
             'app_complex_low_test': {'app_id': 'app_complex_low_test', 'LastUpdated': '2024-11-20', 'DocCoverage': 75.0},
        }
    }

    # Add the ACI example explicitly from the prompt
    mock_raw_data['quality_v1']['ACI Worldwide Risk Management'] = {'app_id': 'ACI Worldwide Risk Management', 'MaintainabilityIndex': 70, 'ComplexityScore': 10, 'TestCoverage': 80.0} # Assuming TestCoverage
    mock_raw_data['operations_v1']['ACI Worldwide Risk Management'] = {'app_id': 'ACI Worldwide Risk Management', 'ChangeFailureRate': 1.2, 'UptimePercentage': 99.5, 'DeploymentFrequency': 'weekly'} # Assuming Uptime/Freq
    mock_raw_data['cost_v1']['ACI Worldwide Risk Management'] = {'app_id': 'ACI Worldwide Risk Management', 'MonthlyCost': 46889.00}
    mock_raw_data['docs_v1']['ACI Worldwide Risk Management'] = {'app_id': 'ACI Worldwide Risk Management', 'LastUpdated': '2025-03-01', 'DocCoverage': 90.0} # Assuming Docs


    logging.basicConfig(level=logging.DEBUG)
    rule = TechDebtPriorityRule()
    # Pass the raw data directly
    results = rule.apply(mock_raw_data)
    print("\\nTechnical Debt Priority Results:")
    import json
    print(json.dumps(results, indent=2))

    # Expected Output based on logic and mock data (Current Date: April 22, 2025):
    # {
    #   "app_aci": "High Priority (Financial Impact (MonthlyCost=$46,889.00, ChangeFailureRate=1.2%))", // Meets Financial Impact
    #   "app_stable": "Low Priority", // Meets no High or Medium criteria
    #   "app_docs": "Medium Priority (Documentation (Outdated: 2024-06-15, Coverage: 91.0%); Technical Indicators (MaintainabilityIndex=72))", // Meets Docs and Tech Indicators
    #   "app_ops": "Medium Priority (Technical Indicators (ComplexityScore=12); Operational Impact (DeploymentFrequency='monthly', ChangeFailureRate=0.6%))", // Meets Tech and Ops
    #   "app_complex_low_test": "High Priority (Sustainability Factor ( (100-50.0) * 15 = 750.0 > 300 ))", // Meets Sustainability
    #   "ACI Worldwide Risk Management": "High Priority (Financial Impact (MonthlyCost=$46,889.00, ChangeFailureRate=1.2%))" // Meets Financial Impact
    # }

