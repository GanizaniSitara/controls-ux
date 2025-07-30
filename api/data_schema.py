import typing
from typing import List, Optional
import strawberry
from enum import Enum
from dataclasses import dataclass
import os
import configparser

# Load domain definitions from settings.ini
def load_domain_definitions():
    API_DIR = os.path.dirname(__file__)
    settings_path = os.path.join(API_DIR, 'settings.ini')
    config = configparser.ConfigParser()
    config.read(settings_path)
    
    domain_dict = {}
    if config.has_section('domains_definition'):
        for domain_key, domain_name in config.items('domains_definition'):
            # Convert to uppercase for enum keys
            domain_dict[domain_key.upper()] = domain_name
    else:
        # Fallback to default domains if section doesn't exist
        domain_dict = {
            "GITLAB": "GitLab Engineering Excellence",
            "DATA_PORTAL": "Data Portal",
            "GOVERNANCE": "Governance",
            "DATA_CONTROL": "Data Control",
            "SYSTEMS_RESILIENCE": "Systems Resilience",
            "SYSTEMS_MANAGEMENT": "Systems Management",
            "COST_FINANCE": "Cost and Finance",
            "APPLICATION_LIFECYCLE": "Application Lifecycle",
            "VENDOR_MANAGEMENT": "Vendor Management",
            "SERVICE_MANAGEMENT": "Service Management",
            "ARCHITECTURE": "Architecture"
        }
    return domain_dict

# Load provider metadata from settings.ini
def load_provider_metadata():
    API_DIR = os.path.dirname(__file__)
    settings_path = os.path.join(API_DIR, 'settings.ini')
    config = configparser.ConfigParser()
    config.read(settings_path)
    
    provider_metadata = {}
    
    # Get provider names and descriptions from settings
    for provider_id in config.options('providers') if config.has_section('providers') else []:
        name = provider_id.replace('_', ' ').title()  # Default name
        description = f"Metrics for {provider_id.replace('_', ' ')}"  # Default description
        
        # Get custom name if available
        if config.has_section('provider_names') and config.has_option('provider_names', provider_id):
            name = config.get('provider_names', provider_id)
        
        # Get custom description if available
        if config.has_section('provider_descriptions') and config.has_option('provider_descriptions', provider_id):
            description = config.get('provider_descriptions', provider_id)
        
        # Automatically detect provider type based on folder path
        provider_type = "demo"  # Default type
        if config.has_section('providers') and config.has_option('providers', provider_id):
            file_path = config.get('providers', provider_id)
            if 'data_prod' in file_path or 'data_migration' in file_path:
                provider_type = "production"
            elif 'data_mock' in file_path:
                provider_type = "demo"
            elif 'data_test' in file_path:
                provider_type = "test"
            else:
                provider_type = "demo"  # Default fallback
        
        provider_metadata[provider_id] = {
            "name": name,
            "description": description,
            "provider_type": provider_type
        }
    
    return provider_metadata

# Dynamically create Domain enum from settings
Domain = Enum('Domain', load_domain_definitions())

# Make it a Strawberry enum
Domain = strawberry.enum(Domain)


@strawberry.type
class FitnessFunction:
    id: str
    name: str
    domain: Domain
    description: str
    current_value: float
    target_value: float
    is_passing: bool
    app_count: int = 0  # Count of loaded applications for this fitness function
    provider_type: str = "demo"  # Type of data source: production, demo, mock, test
    data_status: str = "DEMO DATA"  # Status: LOAD OK, DEMO DATA, LOAD ERROR, NO DATA


@strawberry.type
class DomainMetrics:
    domain: Domain
    passing_count: int
    total_count: int
    passing_percentage: float
    fitness_functions: typing.List[FitnessFunction]


@strawberry.type
class RuleFitnessFunction:
    id: str
    name: str
    description: str
    rule_id: str  # The rule identifier (e.g., "governance_path_decision")
    passing_count: int
    warning_count: int
    failing_count: int
    total_count: int
    passing_percentage: float
    application_breakdown: strawberry.scalars.JSON  # app_id -> status


@strawberry.type
class Query:
    @strawberry.field
    def fitness_functions(self) -> typing.List[FitnessFunction]:
        # Simulated data for our POC, now with app_count
        import os
        import pandas as pd
        from typing import Dict
        
        # Define the path to the data directory
        API_DIR = os.path.dirname(__file__)
        DATA_DIR = os.path.join(API_DIR, 'data_mock')
        
        # Get the count of applications from each CSV file and track loading status
        provider_app_counts: Dict[str, int] = {}
        provider_load_status: Dict[str, str] = {}
        
        # Read from settings.ini to get the mapping of provider IDs to CSV files
        import configparser
        config = configparser.ConfigParser()
        settings_path = os.path.join(API_DIR, 'settings.ini')
        config.read(settings_path)
        
        # Read domain mappings from settings.ini
        domain_mappings = {}
        if config.has_section('domains'):
            for provider_id, domain_key in config.items('domains'):
                # Map domain key to Domain enum member
                try:
                    # Get the enum member by name (domain_key should match enum keys)
                    domain_mappings[provider_id] = Domain[domain_key.upper()]
                except KeyError:
                    # Fallback to first available domain if key not found
                    domain_mappings[provider_id] = list(Domain)[0] if list(Domain) else None
        
        # Iterate through provider mappings in settings.ini
        for provider_id, file_path in config.items('providers'):
            # Build the full path by joining API_DIR with the path from settings
            # The path in settings.ini should be relative to API_DIR
            # Replace backslashes with forward slashes for cross-platform compatibility
            file_path = file_path.replace('\\', '/')
            full_path = os.path.join(API_DIR, file_path)
                
            try:
                if os.path.exists(full_path):
                    df = pd.read_csv(full_path)
                    if not df.empty and len(df.columns) > 0:
                        # Count unique values in first column (app_id)
                        first_col = df.columns[0]
                        provider_app_counts[provider_id] = len(df[first_col].unique())
                        provider_load_status[provider_id] = "loaded_ok"
                    else:
                        provider_app_counts[provider_id] = 0
                        provider_load_status[provider_id] = "no_data"
                else:
                    provider_app_counts[provider_id] = 0
                    provider_load_status[provider_id] = "file_not_found"
            except Exception as e:
                print(f"Error reading CSV file for provider {provider_id}: {e}")
                provider_app_counts[provider_id] = 0
                provider_load_status[provider_id] = "load_error"
        # Load provider metadata from settings.ini
        provider_metadata = load_provider_metadata()
        
        # Generate fitness functions dynamically based on providers in settings.ini
        fitness_functions = []
        function_id = 1
        
        for provider_id in config.options('providers'):
            # Get domain from settings or use default (first available domain)
            domain = domain_mappings.get(provider_id, list(Domain)[0] if list(Domain) else None)
            
            # Get metadata or use defaults
            metadata = provider_metadata.get(provider_id, {
                "name": provider_id.replace('_', ' ').title(),
                "description": f"Metrics for {provider_id.replace('_', ' ')}",
                "provider_type": "demo"
            })
            
            # Determine data status based on provider type and load status
            provider_type = metadata.get("provider_type", "demo")
            load_status = provider_load_status.get(provider_id, "unknown")
            
            if load_status == "loaded_ok":
                if provider_type == "production":
                    data_status = "LOAD OK"
                    is_passing = True
                else:
                    data_status = "DEMO DATA"
                    is_passing = True
            elif load_status == "no_data":
                data_status = "NO DATA"
                is_passing = False
            elif load_status == "file_not_found":
                data_status = "NO DATA"
                is_passing = False
            else:  # load_error
                data_status = "LOAD ERROR"
                is_passing = False
            
            # Create fitness function
            fitness_functions.append(
                FitnessFunction(
                    id=str(function_id),
                    name=metadata["name"],
                    domain=domain,
                    description=metadata["description"],
                    current_value=85.0,  # Default value
                    target_value=100.0,  # Default target
                    is_passing=is_passing,
                    app_count=provider_app_counts.get(provider_id, 0),
                    provider_type=provider_type,
                    data_status=data_status
                )
            )
            function_id += 1
        
        return fitness_functions
    
    @strawberry.field
    def rule_fitness_functions(self) -> typing.List[RuleFitnessFunction]:
        """
        Returns fitness functions based on rule results using the fitness function registry.
        """
        from data_aggregator import get_aggregated_data
        from fitness_logic.registry import FitnessFunctionRegistry
        
        # Get the cached data
        cached_data = get_aggregated_data()
        rule_results = cached_data.get('rule_results', {})
        
        # Use the registry to calculate all fitness functions
        fitness_function_results = FitnessFunctionRegistry.calculate_all(rule_results)
        
        # Convert to RuleFitnessFunction objects for GraphQL
        fitness_functions = []
        for result in fitness_function_results:
            fitness_functions.append(
                RuleFitnessFunction(
                    id=result["id"],
                    name=result["name"],
                    description=result["description"],
                    rule_id=result["rule_id"],
                    passing_count=result["passing_count"],
                    warning_count=result["warning_count"],
                    failing_count=result["failing_count"],
                    total_count=result["total_count"],
                    passing_percentage=result["passing_percentage"],
                    application_breakdown=result["application_breakdown"]
                )
            )
        
        return fitness_functions
    
    @strawberry.field
    def fitness_function_list(self) -> List["FitnessFunctionInfo"]:
        """Get list of all fitness functions with metadata."""
        from fitness_logic.registry import FitnessFunctionRegistry
        
        functions = []
        for func_class in FitnessFunctionRegistry.get_all_functions():
            metadata = func_class.get_metadata()
            module_name = func_class.__module__.split('.')[-1]
            functions.append(
                FitnessFunctionInfo(
                    id=metadata["id"],
                    name=metadata["name"],
                    description=metadata["description"],
                    rule_id=metadata["rule_id"],
                    module_name=module_name,
                    class_name=func_class.__name__
                )
            )
        return functions
    
    @strawberry.field
    def fitness_function_source(self, module_name: str) -> Optional["FitnessFunctionSource"]:
        """Get source code of a specific fitness function."""
        import os
        from pathlib import Path
        
        api_dir = Path(__file__).parent
        fitness_logic_dir = api_dir / "fitness_logic"
        file_path = fitness_logic_dir / f"{module_name}.py"
        
        if not file_path.exists():
            return None
            
        try:
            source_code = file_path.read_text(encoding='utf-8')
            return FitnessFunctionSource(
                module_name=module_name,
                source_code=source_code,
                file_path=f"fitness_logic/{module_name}.py"
            )
        except Exception:
            return None

@strawberry.type
class FitnessFunctionInfo:
    """Information about a fitness function."""
    id: str
    name: str
    description: str
    rule_id: str
    module_name: str
    class_name: str

@strawberry.type
class FitnessFunctionSource:
    """Source code of a fitness function."""
    module_name: str
    source_code: str
    file_path: str

@strawberry.type
class SaveResult:
    """Result of saving a fitness function."""
    status: str
    message: str
    line: Optional[int] = None
    offset: Optional[int] = None
    details: Optional[str] = None

@strawberry.type
class Mutation:
    @strawberry.mutation
    def save_fitness_function(self, module_name: str, source_code: str) -> SaveResult:
        """Save fitness function source code."""
        import os
        import ast
        import importlib
        import sys
        from pathlib import Path
        
        api_dir = Path(__file__).parent
        fitness_logic_dir = api_dir / "fitness_logic"
        file_path = fitness_logic_dir / f"{module_name}.py"
        
        if not file_path.exists():
            return SaveResult(
                status="error",
                message=f"Fitness function '{module_name}' not found"
            )
        
        # Validate Python syntax
        try:
            ast.parse(source_code)
        except SyntaxError as e:
            return SaveResult(
                status="error",
                message=f"Syntax error: {str(e)}",
                line=e.lineno,
                offset=e.offset
            )
        
        # Create timestamped backup
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = fitness_logic_dir / "backups"
        
        # Create backups directory if it doesn't exist
        backup_dir.mkdir(exist_ok=True)
        
        backup_filename = f"{module_name}_{timestamp}.py.bak"
        backup_path = backup_dir / backup_filename
        
        try:
            backup_content = file_path.read_text(encoding='utf-8')
            backup_path.write_text(backup_content, encoding='utf-8')
        except Exception as e:
            return SaveResult(
                status="error",
                message=f"Error creating backup: {str(e)}"
            )
        
        # Save the new code
        try:
            file_path.write_text(source_code, encoding='utf-8')
            
            # Try to reload the module
            module_full_name = f"fitness_logic.{module_name}"
            if module_full_name in sys.modules:
                del sys.modules[module_full_name]
            
            try:
                module = importlib.import_module(module_full_name)
                importlib.reload(module)
                
                return SaveResult(
                    status="success",
                    message="Fitness function saved and reloaded successfully"
                )
                
            except Exception as import_error:
                # Restore from backup if import fails
                backup_path.read_text(encoding='utf-8')
                file_path.write_text(backup_content, encoding='utf-8')
                
                return SaveResult(
                    status="error",
                    message=f"Import error: {str(import_error)}. Code reverted.",
                    details=str(import_error)
                )
                
        except Exception as e:
            # Try to restore backup
            try:
                backup_content = backup_path.read_text(encoding='utf-8')
                file_path.write_text(backup_content, encoding='utf-8')
            except:
                pass
            
            return SaveResult(
                status="error",
                message=f"Error saving: {str(e)}"
            )

schema = strawberry.Schema(query=Query, mutation=Mutation)
