\
# filepath: c:\\git\\FitnessFunctions\\api\\rules\\governance_path_rule.py
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Use absolute import for BaseRule
from rules.base_rule import BaseRule

logger = logging.getLogger(__name__)

class GovernancePathRule(BaseRule):
    """
    Determines the governance path (Fast Path, Slow Path, HALT) for applications
    based on aggregated metrics across multiple domains.
    """
    rule_id = "governance_path_decision" # Identifier for the results

    def apply(self, current_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Applies the governance path logic to the raw data.

        Args:
            current_data: The dictionary containing raw data, expected structure:
                          {'raw_data': {provider_id: {app_id: data_dict}}}
                          or potentially just {provider_id: {app_id: data_dict}}
                          if passed directly from data_aggregator.

        Returns:
            A dictionary containing the governance path decision for each app_id:
            {app_id: 'Fast Path' | 'Slow Path' | 'HALT'}
        """
        # Check if 'raw_data' key exists, otherwise assume current_data is the raw data dict
        raw_data = current_data.get('raw_data', current_data)
        if not isinstance(raw_data, dict):
             logger.error(f"[{self.rule_id}] Input data is not a dictionary: {type(raw_data)}")
             return {"error": "Invalid input data format"}

        results = {}
        app_ids = self._get_all_app_ids(raw_data)
        if not app_ids:
            logger.warning(f"[{self.rule_id}] No application IDs found in the raw data.")
            return {} # Return empty results if no apps        logger.info(f"[{self.rule_id}] Evaluating governance path for {len(app_ids)} apps")

        for app_id in app_ids:
            # Extract data for the current app from all providers
            app_data = self._get_data_for_app(raw_data, app_id)

            # Evaluate HALT conditions first
            halt_reason = self._check_halt_conditions(app_data, app_id)
            if halt_reason:
                results[app_id] = f"HALT ({halt_reason})"
                logger.debug(f"[{self.rule_id}] App '{app_id}' -> HALT ({halt_reason})")
                continue # Skip Fast Path check if HALTed

            # Evaluate Fast Path conditions
            fast_path_met, fast_path_details = self._check_fast_path_conditions(app_data, app_id)
            if fast_path_met:
                results[app_id] = "Fast Path"
                logger.debug(f"[{self.rule_id}] App '{app_id}' -> Fast Path")
            else:
                results[app_id] = f"Slow Path (Reason: {fast_path_details})" # Default to Slow Path if not HALT or Fast Path
                logger.debug(f"[{self.rule_id}] App '{app_id}' -> Slow Path (Reason: {fast_path_details})")

        logger.info(f"[{self.rule_id}] Governance path evaluation complete.")
        # The rule itself returns only its specific results
        return results # Return {app_id: decision}

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
                 # Merge data, handling potential overlaps if necessary (though unlikely here)
                 consolidated.update(provider_data[app_id])
        return consolidated

    def _get_value(self, data: Dict[str, Any], key: str, expected_type: type, default: Any = None) -> Any:
        """Safely retrieves and converts a value from the data dictionary."""
        value = data.get(key)
        if value is None:
            # logger.warning(f"[{self.rule_id}] Missing key '{key}' for app. Using default: {default}")
            return default
        try:
            if expected_type is bool: # Handle boolean strings
                 if isinstance(value, str):
                     if value.lower() == 'true': return True
                     if value.lower() == 'false': return False
                 # Fallback to standard bool conversion
                 return bool(value)
            if expected_type is datetime:
                # Attempt to parse various date formats if needed, assuming ISO format for now
                return datetime.fromisoformat(str(value).split(' ')[0]) # Handle 'YYYY-MM-DD HH:MM:SS'
            return expected_type(value)
        except (ValueError, TypeError) as e:
            logger.warning(f"[{self.rule_id}] Could not convert key '{key}' (value: {value}) to {expected_type.__name__}. Using default: {default}. Error: {e}")
            return default

    def _check_halt_conditions(self, data: Dict[str, Any], app_id: str) -> Optional[str]:
        """Checks if any HALT condition is met."""
        # Security HALT
        vuln_count = self._get_value(data, 'VulnerabilityCount', int, -1)
        patch_comp = self._get_value(data, 'PatchCompliance', float, 101.0) # Default high to avoid false halt
        access_rev = self._get_value(data, 'AccessReviewStatus', str, "error")

        if vuln_count >= 10: return f"VulnerabilityCount ({vuln_count}) >= 10"
        if patch_comp < 95.0: return f"PatchCompliance ({patch_comp}%) < 95%"
        if access_rev != "completed": return f"AccessReviewStatus is '{access_rev}' (not 'completed')"

        # Code Quality HALT
        lint_score = self._get_value(data, 'LintScore', int, 101) # Default high
        test_cov = self._get_value(data, 'TestCoverage', float, 101.0) # Default high
        comp_score = self._get_value(data, 'ComplexityScore', int, -1) # Default low

        if lint_score < 60: return f"LintScore ({lint_score}) < 60"
        if test_cov < 40.0: return f"TestCoverage ({test_cov}%) < 40%"
        if comp_score > 25: return f"ComplexityScore ({comp_score}) > 25"

        # Operational HALT
        uptime = self._get_value(data, 'UptimePercentage', float, 101.0) # Default high
        fail_rate = self._get_value(data, 'ChangeFailureRate', float, -1.0) # Default low

        if uptime < 95.0: return f"UptimePercentage ({uptime}%) < 95%"
        if fail_rate > 5.0: return f"ChangeFailureRate ({fail_rate}%) > 5%"

        # Cost HALT
        cost_increase = self._get_value(data, 'MonthlyCostIncreasePercent', float, -1.0) # Default low
        cost_trend = self._get_value(data, 'CostTrend', str, "stable")

        if cost_increase > 15.0 and cost_trend == "increasing":
             return f"MonthlyCostIncrease ({cost_increase}%) > 15% AND CostTrend is 'increasing'"

        return None # No HALT conditions met

    def _check_fast_path_conditions(self, data: Dict[str, Any], app_id: str) -> (bool, str):
        """Checks if ALL Fast Path conditions are met."""
        reasons_failed = []

        # Security Fast Path
        vuln_count = self._get_value(data, 'VulnerabilityCount', int, 100) # Default high to fail fast path
        patch_comp = self._get_value(data, 'PatchCompliance', float, 0.0) # Default low
        if not (vuln_count <= 3): reasons_failed.append(f"VulnerabilityCount ({vuln_count}) > 3")
        if not (patch_comp >= 98.0): reasons_failed.append(f"PatchCompliance ({patch_comp}%) < 98%")

        # Code Quality Fast Path
        lint_score = self._get_value(data, 'LintScore', int, 0) # Default low
        test_cov = self._get_value(data, 'TestCoverage', float, 0.0) # Default low
        comp_score = self._get_value(data, 'ComplexityScore', int, 100) # Default high
        if not (lint_score >= 75): reasons_failed.append(f"LintScore ({lint_score}) < 75")
        if not (test_cov >= 60.0): reasons_failed.append(f"TestCoverage ({test_cov}%) < 60%")
        if not (comp_score <= 12): reasons_failed.append(f"ComplexityScore ({comp_score}) > 12")

        # Operational Fast Path
        uptime = self._get_value(data, 'UptimePercentage', float, 0.0) # Default low
        fail_rate = self._get_value(data, 'ChangeFailureRate', float, 100.0) # Default high
        if not (uptime >= 98.0): reasons_failed.append(f"UptimePercentage ({uptime}%) < 98%")
        if not (fail_rate <= 2.0): reasons_failed.append(f"ChangeFailureRate ({fail_rate}%) > 2%")

        # Documentation Fast Path
        doc_cov = self._get_value(data, 'DocCoverage', float, 0.0) # Default low
        last_updated_str = self._get_value(data, 'LastUpdated', str, None)
        last_updated_date = None
        if last_updated_str:
            try:
                last_updated_date = datetime.fromisoformat(last_updated_str.split(' ')[0])
            except ValueError:
                 logger.warning(f"[{self.rule_id}] Could not parse LastUpdated date '{last_updated_str}' for app '{app_id}'")

        if not (doc_cov >= 90.0): reasons_failed.append(f"DocCoverage ({doc_cov}%) < 90%")
        if last_updated_date:
            if not (last_updated_date >= datetime.now() - timedelta(days=365)): # Approx 12 months
                reasons_failed.append(f"LastUpdated ({last_updated_date.date()}) > 12 months ago")
        else:
             reasons_failed.append("LastUpdated date missing or invalid")


        # Cost Fast Path
        cost_trend = self._get_value(data, 'CostTrend', str, "increasing") # Default bad
        unused_res = self._get_value(data, 'UnusedResources', int, 100) # Default high
        if not (cost_trend in ["stable", "decreasing"]): reasons_failed.append(f"CostTrend is '{cost_trend}'")
        if not (unused_res <= 2): reasons_failed.append(f"UnusedResources ({unused_res}) > 2")

        if not reasons_failed:
            return True, "All criteria met"
        else:
            return False, "; ".join(reasons_failed)

# Example Usage (if run directly, though usually loaded by rules_engine)
if __name__ == '__main__':
    # Example data structure (mimicking what the rule might receive)
    mock_raw_data = {
        'security_v1': {
            'app_a': {'app_id': 'app_a', 'VulnerabilityCount': 2, 'PatchCompliance': 99.0, 'AccessReviewStatus': 'completed'},
            'app_b': {'app_id': 'app_b', 'VulnerabilityCount': 12, 'PatchCompliance': 94.0, 'AccessReviewStatus': 'pending'},
            'app_c': {'app_id': 'app_c', 'VulnerabilityCount': 1, 'PatchCompliance': 98.5, 'AccessReviewStatus': 'completed'}
        },
        'code_quality_v1': {
            'app_a': {'app_id': 'app_a', 'LintScore': 80, 'TestCoverage': 70.0, 'ComplexityScore': 10},
            'app_b': {'app_id': 'app_b', 'LintScore': 55, 'TestCoverage': 35.0, 'ComplexityScore': 30},
            'app_c': {'app_id': 'app_c', 'LintScore': 70, 'TestCoverage': 55.0, 'ComplexityScore': 15} # Fails fast path on Lint/Test/Complexity
        },
        'operational_excellence_v1': {
             'app_a': {'app_id': 'app_a', 'UptimePercentage': 99.5, 'ChangeFailureRate': 1.0},
             'app_b': {'app_id': 'app_b', 'UptimePercentage': 94.0, 'ChangeFailureRate': 6.0},
             'app_c': {'app_id': 'app_c', 'UptimePercentage': 98.2, 'ChangeFailureRate': 1.5}
        },
        'documentation_v1': {
             'app_a': {'app_id': 'app_a', 'DocCoverage': 95.0, 'LastUpdated': '2025-03-15'},
             'app_b': {'app_id': 'app_b', 'DocCoverage': 70.0, 'LastUpdated': '2023-01-10'},
             'app_c': {'app_id': 'app_c', 'DocCoverage': 91.0, 'LastUpdated': '2024-01-20'} # Fails fast path on LastUpdated
        },
         'cost_optimization_v1': {
             'app_a': {'app_id': 'app_a', 'CostTrend': 'stable', 'UnusedResources': 1, 'MonthlyCostIncreasePercent': 2.0},
             'app_b': {'app_id': 'app_b', 'CostTrend': 'increasing', 'UnusedResources': 5, 'MonthlyCostIncreasePercent': 20.0}, # HALT on cost
             'app_c': {'app_id': 'app_c', 'CostTrend': 'decreasing', 'UnusedResources': 0, 'MonthlyCostIncreasePercent': -5.0}
        }
    }

    logging.basicConfig(level=logging.DEBUG)
    rule = GovernancePathRule()
    # Pass the raw data directly, as the rule handles the structure
    results = rule.apply(mock_raw_data)
    print("Governance Path Results:")
    import json
    print(json.dumps(results, indent=2))

    # Expected Output:
    # {
    #   "app_a": "Fast Path",
    #   "app_b": "HALT (VulnerabilityCount (12) >= 10)", # Halt checks run first
    #   "app_c": "Slow Path (Reason: LintScore (70) < 75; TestCoverage (55.0%) < 60%; ComplexityScore (15) > 12; LastUpdated (2024-01-20) > 12 months ago)"
    # }
