\
# filepath: c:\git\FitnessFunctions\api\rules_engine.py
import os
import importlib
import inspect
import logging
from typing import List, Dict, Any

# Use absolute import for BaseRule
from rules.base_rule import BaseRule

logger = logging.getLogger(__name__)

# Point to the 'rules' subdirectory relative to this file
RULES_DIR = os.path.join(os.path.dirname(__file__), 'rules')

def load_rules() -> List[BaseRule]:
    """
    Dynamically loads rule classes from the 'rules' directory that inherit from BaseRule.
    """
    rules = []
    logger.info(f"Loading rules from directory: {RULES_DIR}")
    # Ensure the RULES_DIR actually exists before trying to list it
    if not os.path.isdir(RULES_DIR):
        logger.error(f"Rules directory not found: {RULES_DIR}")
        return rules

    for filename in os.listdir(RULES_DIR):
        if filename.endswith(".py") and not filename.startswith("__") and filename != "base_rule.py":            
            module_name = f"rules.{filename[:-3]}"
            try:
                # Import the module using its absolute path
                module = importlib.import_module(module_name)
                for name, obj in inspect.getmembers(module):
                    # Check if it's a class, defined in this module, and is a subclass of BaseRule (but not BaseRule itself)
                    if inspect.isclass(obj) and obj.__module__ == module_name and issubclass(obj, BaseRule) and obj is not BaseRule:
                        try:
                            rules.append(obj()) # Instantiate the rule
                            logger.info(f"Successfully loaded and instantiated rule: {name}")
                        except Exception as e:
                            logger.error(f"Failed to instantiate rule {name} from {module_name}: {e}")

            except ImportError as e:
                logger.error(f"Failed to import module {module_name}: {e}")
            except Exception as e:
                 logger.error(f"Error loading rules from {module_name}: {e}")

    if not rules:
        logger.warning("No rules were loaded.")
    else:
        logger.info(f"Finished loading rules. Total rules loaded: {len(rules)}")
    return rules

def run_rules(aggregated_data: Dict[str, Any], rules: List[BaseRule]) -> Dict[str, Any]:
    """
    Applies a list of rules to the aggregated data, collecting results from each rule.

    Args:
        aggregated_data: The data fetched from the cache, potentially containing 'raw_data'.
        rules: A list of instantiated rule objects.

    Returns:
        A dictionary where keys are rule identifiers (e.g., rule_id or class name)
        and values are the results returned by each rule's apply method.
    """
    if not rules:
        logger.warning("Rules engine run requested, but no rules are loaded. Returning empty results.")
        return {} # Return empty dict if no rules

    logger.info(f"Starting rules engine run with {len(rules)} rules.")
    all_rule_results: Dict[str, Any] = {} # Store results per rule

    # Determine the primary input data for rules (prefer 'raw_data' if available)
    # Some rules might expect the full structure, others just raw_data.
    # The rule's apply method should handle the structure it expects.
    rules_input = aggregated_data # Pass the whole cache content

    for rule in rules:
        # Use rule_id if available, otherwise fallback to class name
        rule_identifier = getattr(rule, 'rule_id', rule.__class__.__name__)
        try:
            logger.debug(f"Applying rule: {rule_identifier}")
            # Pass the potentially nested aggregated_data; the rule decides what to use
            rule_result = rule.apply(rules_input)
            all_rule_results[rule_identifier] = rule_result
            logger.debug(f"Rule {rule_identifier} applied successfully.")
        except Exception as e:
            logger.error(f"Error applying rule {rule_identifier}: {e}", exc_info=True)
            # Store error information for this specific rule
            all_rule_results[rule_identifier] = {"error": f"Rule execution failed: {e}"}

    logger.info("Rules engine run finished.")
    return all_rule_results # Return the dictionary of all rule results

