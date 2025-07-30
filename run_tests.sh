#!/bin/bash

# Fitness Functions Platform - Test Runner Script
# Usage: ./run_tests.sh [test-type] [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TEST_TYPE="all"
COVERAGE=false
VERBOSE=false
WATCH=false
FAST=false

# Help function
show_help() {
    echo "Fitness Functions Platform Test Runner"
    echo ""
    echo "Usage: $0 [OPTIONS] [TEST_TYPE]"
    echo ""
    echo "TEST_TYPE options:"
    echo "  all           Run all tests (default)"
    echo "  unit          Run unit tests only"
    echo "  integration   Run integration tests only"
    echo "  e2e           Run end-to-end tests only"
    echo "  performance   Run performance tests"
    echo "  migration     Run migration tests only"
    echo "  schema        Run schema-related tests only"
    echo ""
    echo "OPTIONS:"
    echo "  -c, --coverage    Generate coverage report"
    echo "  -v, --verbose     Verbose output"
    echo "  -w, --watch       Run tests in watch mode"
    echo "  -f, --fast        Run fast tests only (skip slow markers)"
    echo "  -h, --help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                              # Run all tests"
    echo "  $0 unit -c                      # Run unit tests with coverage"
    echo "  $0 integration -v               # Run integration tests verbosely"
    echo "  $0 performance -f               # Run fast performance tests only"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -w|--watch)
            WATCH=true
            shift
            ;;
        -f|--fast)
            FAST=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        all|unit|integration|e2e|performance|migration|schema)
            TEST_TYPE=$1
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check if we're in the right directory
if [[ ! -f "api/requirements.txt" ]]; then
    echo -e "${RED}Error: Please run this script from the fitness-functions root directory${NC}"
    exit 1
fi

# Change to API directory
cd api

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}Warning: No virtual environment detected. Consider activating one.${NC}"
fi

# Install dependencies if needed
if [[ ! -f ".deps_installed" ]]; then
    echo -e "${BLUE}Installing dependencies...${NC}"
    pip install -r requirements.txt
    touch .deps_installed
fi

# Build pytest command
PYTEST_CMD="python -m pytest"

# Add verbosity
if [[ "$VERBOSE" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# Add coverage options
if [[ "$COVERAGE" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD --cov=. --cov-report=html --cov-report=term-missing --cov-report=xml"
fi

# Add fast test filtering
if [[ "$FAST" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD -m 'not slow'"
fi

# Set test path based on type
case $TEST_TYPE in
    all)
        TEST_PATH="tests/"
        echo -e "${GREEN}Running all tests...${NC}"
        ;;
    unit)
        TEST_PATH="tests/unit/"
        echo -e "${GREEN}Running unit tests...${NC}"
        ;;
    integration)
        TEST_PATH="tests/integration/"
        echo -e "${GREEN}Running integration tests...${NC}"
        ;;
    e2e)
        TEST_PATH="tests/e2e/"
        echo -e "${GREEN}Running end-to-end tests...${NC}"
        ;;
    performance)
        TEST_PATH="tests/integration/test_performance.py"
        echo -e "${GREEN}Running performance tests...${NC}"
        ;;
    migration)
        TEST_PATH="tests/integration/test_migration_scenarios.py tests/unit/test_schema_migration.py"
        echo -e "${GREEN}Running migration tests...${NC}"
        ;;
    schema)
        TEST_PATH="tests/unit/test_schema_manager.py tests/unit/test_schema_migration.py"
        echo -e "${GREEN}Running schema tests...${NC}"
        ;;
esac

# Handle watch mode
if [[ "$WATCH" == true ]]; then
    if command -v ptw >/dev/null 2>&1; then
        echo -e "${BLUE}Starting tests in watch mode...${NC}"
        ptw $TEST_PATH -- $PYTEST_CMD
    else
        echo -e "${YELLOW}pytest-watch not installed. Installing...${NC}"
        pip install pytest-watch
        ptw $TEST_PATH -- $PYTEST_CMD
    fi
else
    # Run tests
    echo -e "${BLUE}Command: $PYTEST_CMD $TEST_PATH${NC}"
    $PYTEST_CMD $TEST_PATH

    # Show coverage report location if generated
    if [[ "$COVERAGE" == true ]]; then
        echo -e "${GREEN}Coverage report generated:${NC}"
        echo "  HTML: file://$(pwd)/htmlcov/index.html"
        echo "  XML:  $(pwd)/coverage.xml"
    fi
fi

echo -e "${GREEN}Test run completed!${NC}"