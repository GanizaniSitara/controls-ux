#!/usr/bin/env python3
"""
Test script for fitness function editor API endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_list_fitness_functions():
    """Test the REST endpoint to list fitness functions."""
    print("=== Testing List Fitness Functions (REST) ===")
    response = requests.get(f"{BASE_URL}/api/fitness-functions")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data['fitness_functions'])} fitness functions:")
        for func in data['fitness_functions']:
            print(f"  - {func['name']} ({func['module_name']}.py)")
            print(f"    ID: {func['id']}")
            print(f"    Class: {func['class_name']}")
        return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False

def test_get_source_code():
    """Test getting source code for a fitness function."""
    print("\n=== Testing Get Source Code (REST) ===")
    
    # First, get the list to know which modules are available
    response = requests.get(f"{BASE_URL}/api/fitness-functions")
    if response.status_code != 200:
        print("Failed to get function list")
        return False
        
    functions = response.json()['fitness_functions']
    if not functions:
        print("No functions found")
        return False
    
    # Test getting source for the first function
    test_module = functions[0]['module_name']
    print(f"Getting source code for: {test_module}")
    
    response = requests.get(f"{BASE_URL}/api/fitness-functions/{test_module}/source")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Retrieved source code for {data['module_name']}")
        print(f"  File path: {data['file_path']}")
        print(f"  Source length: {len(data['source_code'])} characters")
        print(f"  First 200 chars: {data['source_code'][:200]}...")
        return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False

def test_graphql_endpoints():
    """Test the GraphQL endpoints."""
    print("\n=== Testing GraphQL Endpoints ===")
    
    # Test listing functions
    query = """
    query {
        fitnessFunctionList {
            id
            name
            description
            moduleName
            className
        }
    }
    """
    
    response = requests.post(
        f"{BASE_URL}/graphql",
        json={"query": query},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        if 'data' in data and 'fitnessFunctionList' in data['data']:
            functions = data['data']['fitnessFunctionList']
            print(f"✓ GraphQL query successful. Found {len(functions)} functions")
            
            # Test getting source for the first function
            if functions:
                module_name = functions[0]['moduleName']
                source_query = f"""
                query {{
                    fitnessFunctionSource(moduleName: "{module_name}") {{
                        moduleName
                        filePath
                        sourceCode
                    }}
                }}
                """
                
                response = requests.post(
                    f"{BASE_URL}/graphql",
                    json={"query": source_query},
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and data['data']['fitnessFunctionSource']:
                        print(f"✓ Retrieved source via GraphQL for {module_name}")
                        return True
                    else:
                        print("✗ Failed to get source via GraphQL")
                        print(data)
            return True
        else:
            print("✗ GraphQL query failed")
            print(data)
    else:
        print(f"Error: {response.status_code} - {response.text}")
    
    return False

if __name__ == "__main__":
    print("Testing Fitness Function Editor API Endpoints")
    print("Make sure the API server is running on http://localhost:8000")
    print("=" * 50)
    
    try:
        # Test if server is running
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("Error: API server is not running")
            exit(1)
            
        # Run tests
        test_list_fitness_functions()
        test_get_source_code()
        test_graphql_endpoints()
        
        print("\n✓ All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to API server. Make sure it's running.")
    except Exception as e:
        print(f"Error: {e}")