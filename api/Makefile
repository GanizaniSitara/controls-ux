# Fitness Functions API - Development Makefile

.PHONY: help install test test-unit test-integration test-e2e test-performance test-coverage clean lint format dev

# Default target
help:
	@echo "Available targets:"
	@echo "  install           Install dependencies"
	@echo "  test              Run all tests"
	@echo "  test-unit         Run unit tests only"
	@echo "  test-integration  Run integration tests only"
	@echo "  test-e2e          Run end-to-end tests only"
	@echo "  test-performance  Run performance tests"
	@echo "  test-coverage     Run tests with coverage report"
	@echo "  test-watch        Run tests in watch mode (requires pytest-watch)"
	@echo "  lint              Run linting checks"
	@echo "  format            Format code"
	@echo "  dev               Start development server"
	@echo "  clean             Clean up temporary files"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install pytest-watch flake8 black isort safety bandit

# Testing targets
test:
	python -m pytest tests/ -v

test-unit:
	python -m pytest tests/unit/ -v

test-integration:
	python -m pytest tests/integration/ -v

test-e2e:
	python -m pytest tests/e2e/ -v

test-performance:
	python -m pytest tests/integration/test_performance.py -v -m "not slow"

test-performance-all:
	python -m pytest tests/integration/test_performance.py -v

test-coverage:
	python -m pytest tests/ --cov=. --cov-report=html --cov-report=term-missing --cov-report=xml -v

test-coverage-unit:
	python -m pytest tests/unit/ --cov=. --cov-report=html --cov-report=term-missing -v

test-watch:
	ptw tests/ -- -v

# Quality checks
lint:
	@echo "Running flake8..."
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	@echo "Running black check..."
	black --check .
	@echo "Running isort check..."
	isort --check-only .

format:
	@echo "Formatting with black..."
	black .
	@echo "Sorting imports with isort..."
	isort .

security:
	@echo "Running safety check..."
	safety check -r requirements.txt
	@echo "Running bandit security scan..."
	bandit -r . -x tests/

# Development
dev:
	uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Cleanup
clean:
	@echo "Cleaning up temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + || true
	find . -type f -name "*.pyc" -delete || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + || true
	find . -type d -name "htmlcov" -exec rm -rf {} + || true
	find . -type f -name "coverage.xml" -delete || true
	find . -type f -name ".coverage" -delete || true

# Migration-specific testing
test-migration:
	python -m pytest tests/integration/test_migration_scenarios.py -v

test-schema:
	python -m pytest tests/unit/test_schema_manager.py tests/unit/test_schema_migration.py -v

# CI simulation
ci:
	@echo "Running CI pipeline locally..."
	make lint
	make test-coverage
	make security

# Docker targets (future use)
docker-build:
	docker build -t fitness-functions-api .

docker-test:
	docker run --rm fitness-functions-api make test

# Documentation generation (future use)
docs:
	@echo "Documentation generation placeholder"
	# sphinx-build -b html docs/ docs/_build/