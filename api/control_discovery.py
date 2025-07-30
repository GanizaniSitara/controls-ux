import ast
import os
import logging
from typing import List, Dict, Optional
from pathlib import Path
import hashlib
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class ControlScriptDiscovery:
    """Discovers control scripts and extracts @step decorated functions."""
    
    def __init__(self, script_path: Optional[str] = None):
        self.script_path = script_path
        self._cache = {}
        self._cache_time = None
        self._cache_duration = 300  # 5 minutes
        
    def _get_mock_data(self) -> Dict[str, List[Dict]]:
        """Return mock data for development when scripts aren't available."""
        return {
            "DAILY_CTRL": [
                {
                    "name": "validate_trade_reconciliation",
                    "docstring": "Validates that all trades are properly reconciled",
                    "line_number": 45,
                    "parameters": ["trade_date", "system_id"]
                },
                {
                    "name": "check_risk_limits",
                    "docstring": "Verifies risk limits are within acceptable thresholds",
                    "line_number": 78,
                    "parameters": ["portfolio_id", "limit_type"]
                },
                {
                    "name": "generate_daily_report",
                    "docstring": "Generates daily summary report",
                    "line_number": 112,
                    "parameters": ["report_date", "format"]
                }
            ],
            "RISK_MONITOR_CTRL": [
                {
                    "name": "calculate_var",
                    "docstring": "Calculates Value at Risk for all portfolios",
                    "line_number": 23,
                    "parameters": ["confidence_level", "time_horizon"]
                },
                {
                    "name": "stress_test_portfolios",
                    "docstring": "Runs stress test scenarios",
                    "line_number": 67,
                    "parameters": ["scenario_name", "portfolios"]
                },
                {
                    "name": "alert_on_breaches",
                    "docstring": "Sends alerts for limit breaches",
                    "line_number": 99,
                    "parameters": ["breach_type", "severity"]
                }
            ],
            "COMPLIANCE_CHECK_CTRL": [
                {
                    "name": "verify_mifid_compliance",
                    "docstring": "Checks MiFID II compliance for all trades",
                    "line_number": 34,
                    "parameters": ["trade_ids", "reporting_date"]
                },
                {
                    "name": "validate_dodd_frank",
                    "docstring": "Validates Dodd-Frank reporting requirements",
                    "line_number": 89,
                    "parameters": ["swap_data", "counterparty_id"]
                },
                {
                    "name": "audit_trail_check",
                    "docstring": "Ensures complete audit trail exists",
                    "line_number": 156,
                    "parameters": ["start_date", "end_date"]
                }
            ],
            "TRADE_VALIDATION_CTRL": [
                {
                    "name": "validate_counterparty",
                    "docstring": "Validates counterparty is approved and active",
                    "line_number": 12,
                    "parameters": ["counterparty_code", "trade_date"]
                },
                {
                    "name": "check_pricing_tolerance",
                    "docstring": "Verifies trade price is within market tolerance",
                    "line_number": 45,
                    "parameters": ["trade_price", "market_price", "tolerance"]
                },
                {
                    "name": "validate_settlement_instructions",
                    "docstring": "Checks settlement instructions are complete",
                    "line_number": 78,
                    "parameters": ["trade_id", "settlement_date"]
                }
            ]
        }
    
    def _parse_python_file(self, filepath: Path) -> List[Dict]:
        """Parse a Python file and extract @step decorated functions."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(filepath))
            step_functions = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check if function has @step decorator
                    has_step_decorator = False
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Name) and decorator.id == 'step':
                            has_step_decorator = True
                            break
                        elif isinstance(decorator, ast.Attribute) and decorator.attr == 'step':
                            has_step_decorator = True
                            break
                    
                    if has_step_decorator:
                        # Extract function details
                        func_info = {
                            "name": node.name,
                            "docstring": ast.get_docstring(node) or "No description available",
                            "line_number": node.lineno,
                            "parameters": [arg.arg for arg in node.args.args if arg.arg != 'self']
                        }
                        step_functions.append(func_info)
            
            return step_functions
            
        except Exception as e:
            logger.error(f"Error parsing file {filepath}: {e}")
            return []
    
    def discover_control_scripts(self, use_cache: bool = True) -> Dict[str, List[Dict]]:
        """Discover all control scripts and their @step decorated functions."""
        
        # Check cache first
        if use_cache and self._cache_time:
            cache_age = (datetime.now() - self._cache_time).total_seconds()
            if cache_age < self._cache_duration:
                logger.debug("Returning cached control script data")
                return self._cache
        
        # If no script path configured or doesn't exist, return mock data
        if not self.script_path or not os.path.exists(self.script_path):
            logger.warning(f"Script path not found or not configured: {self.script_path}")
            logger.info("Returning mock control script data for development")
            return self._get_mock_data()
        
        # Discover scripts
        logger.info(f"Discovering control scripts in: {self.script_path}")
        scripts = {}
        
        try:
            script_dir = Path(self.script_path)
            
            # Find all Python files
            for py_file in script_dir.glob("*.py"):
                # Skip __init__.py and test files
                if py_file.name.startswith('__') or 'test' in py_file.name.lower():
                    continue
                
                # Extract control name from filename (remove .py extension)
                control_name = py_file.stem
                
                # Parse the file
                step_functions = self._parse_python_file(py_file)
                
                if step_functions:
                    scripts[control_name] = step_functions
                    logger.info(f"Found {len(step_functions)} steps in {control_name}")
            
            # Update cache
            self._cache = scripts
            self._cache_time = datetime.now()
            
            logger.info(f"Discovered {len(scripts)} control scripts")
            return scripts
            
        except Exception as e:
            logger.error(f"Error discovering control scripts: {e}")
            # Return mock data as fallback
            return self._get_mock_data()
    
    def get_script_details(self, script_name: str) -> Optional[List[Dict]]:
        """Get details for a specific control script."""
        scripts = self.discover_control_scripts()
        return scripts.get(script_name)
    
    def get_all_steps(self) -> List[Dict]:
        """Get all steps from all control scripts."""
        scripts = self.discover_control_scripts()
        all_steps = []
        
        for script_name, steps in scripts.items():
            for step in steps:
                step_with_script = step.copy()
                step_with_script['script_name'] = script_name
                all_steps.append(step_with_script)
        
        return all_steps
    
    def search_steps(self, query: str) -> List[Dict]:
        """Search for steps by name or description."""
        query_lower = query.lower()
        all_steps = self.get_all_steps()
        
        matching_steps = []
        for step in all_steps:
            if (query_lower in step['name'].lower() or 
                query_lower in step.get('docstring', '').lower()):
                matching_steps.append(step)
        
        return matching_steps


# Singleton instance
_discovery_instance = None


def get_control_discovery(script_path: Optional[str] = None) -> ControlScriptDiscovery:
    """Get or create the singleton ControlScriptDiscovery instance."""
    global _discovery_instance
    
    if _discovery_instance is None:
        _discovery_instance = ControlScriptDiscovery(script_path)
    elif script_path and _discovery_instance.script_path != script_path:
        # Update path if provided
        _discovery_instance.script_path = script_path
    
    return _discovery_instance