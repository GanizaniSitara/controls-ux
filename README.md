# Enterprise Fitness Functions Platform

A proof-of-concept implementation of Enterprise-Wide Fitness Functions based on the concepts from "Building Evolutionary Architectures" by Neal Ford. This platform provides a flexible, scalable approach to enterprise assurance through data-driven validation and monitoring.

## Overview

The Fitness Functions platform connects metrics from heterogeneous systems across an enterprise, focusing on IT Business Applications (ITBA) as the central unit for measuring organizational health. It aggregates data from monitoring, logging, build pipelines, technical debt analysis, infrastructure, finance, HR, and project management systems to provide comprehensive insights into application and organizational fitness.

## Architecture

- **Backend**: Python FastAPI application with GraphQL endpoint
- **Frontend**: React TypeScript application (port 3003)  
- **Data Layer**: File-based data sources with dynamic schema detection
- **Rules Engine**: Configurable business rules for data processing
- **Migration System**: Automated schema change management

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 14+
- npm

### Setup

1. **Backend Setup**:
   ```bash
   cd api
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp settings.example.ini settings.ini
   ```

2. **Frontend Setup**:
   ```bash
   cd ui
   npm install
   ```

3. **Start Development Environment**:
   ```bash
   # Windows
   start_dev_environment.bat
   
   # Manual start
   # Terminal 1 (Backend)
   cd api && uvicorn app:app --reload
   
   # Terminal 2 (Frontend) 
   cd ui && npm start
   ```

4. **Access the Application**:
   - Frontend: http://localhost:3003
   - Backend API: http://localhost:8000
   - GraphQL Interface: http://localhost:8000/graphql

## Data Management and Schema Migration

### Overview

The platform uses a sophisticated **Dynamic Schema Detection and Migration System** that allows for flexible data source management without hard-coded column dependencies. This system automatically adapts to changes in data structure while maintaining data integrity and system stability.

### Key Features

- **Automatic Schema Detection**: Dynamically analyzes CSV files to understand column types, relationships, and structure
- **Flexible Column Mapping**: Adapts to different column names and structures across data sources
- **Safe Migration Processing**: Handles schema changes with backup creation and rollback capabilities
- **Non-Breaking Change Auto-Execution**: Automatically applies safe changes like adding columns
- **Breaking Change Protection**: Requires manual approval for potentially destructive changes

### Migration System Components

#### 1. Schema Detection (`schema_manager.py`)

The schema detector automatically analyzes data files to identify:

- **Column Information**: Data types, nullable status, uniqueness, sample values
- **Relationship Detection**: Primary key candidates, timestamp columns, identifier columns  
- **Schema Fingerprinting**: Generates hash signatures for change detection
- **Validation**: Ensures data quality and structural integrity

#### 2. Migration Engine (`schema_migration.py`)

The migration engine handles schema evolution through:

- **Change Detection**: Compares current schema against cached versions
- **Migration Planning**: Creates detailed migration plans with step-by-step instructions
- **Safe Execution**: Applies changes with backup creation and error handling
- **Audit Trail**: Maintains complete history of all migrations

#### 3. API Endpoints

Migration functionality is exposed through REST endpoints:

- `GET /api/migrations/pending` - List pending migration plans
- `POST /api/migrations/create/{provider_id}` - Create migration plan for specific provider
- `POST /api/migrations/execute/{provider_id}` - Execute pending migration

## How to Perform Schema Migrations

### Automatic Migration (Recommended)

The system automatically detects and handles schema changes during regular operation:

1. **Background Processing**: Every 5 minutes, the system checks all data sources for schema changes
2. **Auto-Detection**: Changes are automatically detected by comparing current files against cached schemas
3. **Safe Auto-Execution**: Non-breaking changes (like adding columns) are applied automatically
4. **Manual Review for Breaking Changes**: Destructive changes require explicit approval

**Example of automatic migration:**
```bash
# System automatically detects new column in data_mock/observability_v1.csv
# Creates migration plan: "Add new column 'monitoring_status' with type object"
# Auto-executes migration with backup creation
# Updates schema cache with new structure
```

### Manual Migration Process

For complex changes or when you need explicit control:

#### Step 1: Check Current Schema Status

```bash
# View schema report for all providers
curl http://localhost:8000/api/schema-report

# Validate specific provider schema  
curl http://localhost:8000/api/validate-schema/observability_v1
```

#### Step 2: Create Migration Plan

When you modify a CSV file structure, create a migration plan:

```bash
# Create migration plan for specific provider
curl -X POST http://localhost:8000/api/migrations/create/observability_v1

# Response example:
{
  "timestamp": "2025-07-15T21:25:09.000Z",
  "provider_id": "observability_v1", 
  "migration_needed": true,
  "plan_file": "migration_observability_v1_07111524_b127ba87.json",
  "steps_count": 1,
  "steps": [
    {
      "type": "add_column",
      "description": "Add new column 'monitoring_status' with type object"
    }
  ]
}
```

#### Step 3: Review Migration Plan

Examine the generated migration plan:

```bash
# Check pending migrations
curl http://localhost:8000/api/migrations/pending

# Review migration file in api/migrations/
cat api/migrations/migration_observability_v1_07111524_b127ba87.json
```

#### Step 4: Execute Migration

Apply the migration (with automatic backup):

```bash
# Execute migration with backup (default: backup=true)
curl -X POST http://localhost:8000/api/migrations/execute/observability_v1?backup=true

# Response example:
{
  "timestamp": "2025-07-15T21:25:41.000Z",
  "provider_id": "observability_v1",
  "migration_executed": true,
  "executed_at": "2025-07-15T21:25:41.916366",
  "backup_created": true,
  "error_message": null
}
```

### Migration Types and Handling

#### Non-Breaking Changes (Auto-Executed)

These changes are considered safe and applied automatically:

- **Adding new columns**: New data fields with default values
- **Increasing column precision**: Making numeric fields more precise
- **Adding indexes**: Performance improvements without data structure changes

#### Breaking Changes (Manual Approval Required)

These changes require explicit approval and manual execution:

- **Removing columns**: Data loss potential
- **Renaming columns**: May break existing rules and integrations  
- **Changing data types**: Potential data conversion issues
- **Reducing column size**: Potential data truncation

### Working with Data Sources

#### Data Folder Structure

The system supports multiple data folders with automatic status detection:

- **`data_migration/`** - Production data (migrated/transformed) → Shows as "LOAD OK"
- **`data_prod/`** - Production data → Shows as "LOAD OK"
- **`data_mock/`** - Demo/sample data → Shows as "DEMO DATA"
- **`data_test/`** - Test data → Shows as test data

#### Adding New Data Sources

1. **Create CSV File**: Place your CSV file in the appropriate folder
   ```csv
   app_id,metric_value,timestamp
   "App A",85,2025-01-15T10:00:00
   "App B",92,2025-01-15T10:00:00
   ```

2. **Update Configuration**: Add provider to `api/settings.ini`
   ```ini
   [providers]
   # For production data (shows as "LOAD OK")
   new_provider = data_migration/new_provider_v1.csv
   
   # For demo data (shows as "DEMO DATA")
   new_provider = data_mock/new_provider_v1.csv
   ```

3. **Schema Auto-Detection**: System automatically detects and validates schema
   ```bash
   # Validate new data source
   curl http://localhost:8000/api/validate-schema/new_provider_v1
   ```

4. **Restart Application**: Changes take effect on next cache update (within 5 minutes) or restart

#### Modifying Existing Data Sources

1. **Make Changes**: Edit CSV files in `api/data_mock/`
2. **Automatic Detection**: System detects changes during next cache update
3. **Review Migration**: Check logs or pending migrations endpoint
4. **Manual Intervention**: For breaking changes, manually execute migration if needed

### Best Practices

#### Data Source Design

- **Always include identifier column**: Use `app_id`, `id`, or similar unique identifier
- **Include timestamp columns**: Use `timestamp`, `date`, `created_at` for temporal tracking
- **Consistent naming**: Use snake_case or consistent column naming patterns
- **Avoid breaking changes**: Add columns rather than removing/renaming when possible

#### Migration Management

- **Test changes locally**: Validate schema changes in development before production
- **Monitor migration logs**: Check `api/logs/` for migration execution details
- **Backup strategy**: System creates automatic backups, but maintain external backups for critical data
- **Staged deployments**: Apply complex migrations during maintenance windows

#### Troubleshooting

1. **Check logs**: `api/logs/api_log_*.log` contains detailed migration information
2. **Validate schemas**: Use `/api/schema-report` to check all data source health
3. **Review migration plans**: Examine migration files in `api/migrations/`
4. **Rollback if needed**: Restore from backup files (`.backup_*` files in data directories)

### Schema Migration Examples

#### Example 1: Adding a New Column

**Before** (`observability_v1.csv`):
```csv
app_id,obs_platform
"App A",ELK
"App B",Splunk
```

**After** (`observability_v1.csv`):
```csv
app_id,obs_platform,monitoring_status
"App A",ELK,Active
"App B",Splunk,Inactive
```

**Migration Plan Generated**:
```json
{
  "provider_id": "observability_v1",
  "migration_steps": [
    {
      "step_type": "add_column",
      "description": "Add new column 'monitoring_status' with type object",
      "new_value": "monitoring_status",
      "default_value": "",
      "required": true
    }
  ]
}
```

**Result**: Auto-executed, backup created, schema cache updated

#### Example 2: Removing a Column (Breaking Change)

**Before** (`cost_optimization_v1.csv`):
```csv
app_id,cost_score,efficiency_rating,deprecated_field
"App A",85,High,old_value
"App B",92,Medium,old_value2
```

**After** (`cost_optimization_v1.csv`):
```csv
app_id,cost_score,efficiency_rating
"App A",85,High
"App B",92,Medium
```

**Migration Plan Generated**:
```json
{
  "provider_id": "cost_optimization_v1",
  "migration_steps": [
    {
      "step_type": "remove_column", 
      "description": "Remove column 'deprecated_field'",
      "old_value": "deprecated_field"
    }
  ]
}
```

**Result**: Requires manual execution due to breaking change

### API Documentation

#### Schema Management Endpoints

- **GET /api/schema-report**: Comprehensive schema report for all data sources
- **GET /api/validate-schema/{provider_id}**: Validate specific provider schema
- **GET /api/cache-health**: Check cache status and health

#### Migration Management Endpoints

- **GET /api/migrations/pending**: List all pending migration plans
- **POST /api/migrations/create/{provider_id}**: Create migration plan for provider
- **POST /api/migrations/execute/{provider_id}**: Execute pending migration with optional backup

#### Data Access Endpoints

- **GET /graphql**: GraphQL interface for querying fitness function data
- **GET /api/cache-debug**: Debug cache contents
- **GET /aggregated-data**: Raw aggregated data access

## Development Guide

### Project Structure

```
fitness-functions/
├── api/                          # Backend API
│   ├── data_mock/               # CSV data files
│   ├── migrations/              # Migration plan storage
│   ├── schemas/                 # Cached schema definitions
│   ├── rules/                   # Business rule implementations
│   ├── providers/               # Data provider classes (legacy)
│   ├── schema_manager.py        # Dynamic schema detection
│   ├── schema_migration.py      # Migration system
│   ├── flexible_data_loader.py  # Flexible data loading
│   ├── data_aggregator.py       # Core data aggregation
│   ├── app.py                   # FastAPI application
│   └── settings.ini             # Data source configuration
├── ui/                          # React frontend
│   └── src/                     # React components and logic
└── README.md                    # This file
```

### Adding New Fitness Functions

1. **Create data source**: Add CSV file with application metrics
2. **Configure provider**: Update `settings.ini` with new data source
3. **Create business rules**: Add rule classes in `api/rules/`
4. **Update GraphQL schema**: Extend `data_schema.py` for new data access patterns

### Testing

The platform includes a comprehensive test suite covering unit tests, integration tests, end-to-end scenarios, performance tests, and migration testing.

#### Test Structure

```
api/tests/
├── unit/                    # Unit tests for individual components
├── integration/             # Integration tests for API endpoints and workflows
├── e2e/                     # End-to-end workflow tests
├── fixtures/                # Test data and scenarios
└── conftest.py             # Shared test configuration
```

#### Running Tests

**Quick Start**:
```bash
# Run all tests
./run_tests.sh

# Run with coverage
./run_tests.sh -c

# Run specific test types
./run_tests.sh unit
./run_tests.sh integration
./run_tests.sh e2e
./run_tests.sh performance
./run_tests.sh migration
```

**Advanced Options**:
```bash
# Verbose output
./run_tests.sh unit -v

# Fast tests only (skip slow markers)
./run_tests.sh performance -f

# Watch mode for development
./run_tests.sh unit -w

# Generate coverage report
./run_tests.sh all -c
```

**Using Make (Alternative)**:
```bash
cd api

# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific types
make test-unit
make test-integration
make test-performance
```

#### Test Categories

- **Unit Tests**: Schema manager, migration system, data loading components
- **Integration Tests**: API endpoints, migration scenarios, performance testing
- **End-to-End Tests**: Complete workflows, schema evolution, error handling
- **Performance Tests**: Data loading benchmarks, cache operations, concurrent access
- **Migration Tests**: Schema change scenarios, breaking vs safe changes

#### Coverage Targets
- Unit Tests: >95% coverage for core components
- Integration Tests: >90% coverage for API endpoints  
- Overall: >80% code coverage

View coverage report: `api/htmlcov/index.html`

#### React Tests
```bash
cd ui && npm test
```

## Production Deployment

### Environment Configuration

- Set up proper Python virtual environment
- Configure production database if moving away from file-based storage
- Set up proper logging and monitoring
- Configure authentication and authorization (SSO)

### Performance Considerations

- Monitor cache performance and adjust TTL settings
- Consider database storage for large-scale deployments
- Implement proper error handling and retry mechanisms
- Set up health checks and monitoring

## Troubleshooting

### Common Issues

1. **Schema validation errors**: Check CSV file format and column consistency
2. **Migration failures**: Review migration logs and backup files
3. **Cache timeouts**: Monitor cache health endpoint and adjust refresh intervals
4. **Performance issues**: Check data file sizes and consider optimization

### Support

- Check logs in `api/logs/` for detailed error information
- Use debug endpoints (`/api/cache-debug`, `/api/schema-report`) for system status
- Review migration history in `api/migrations/` for change tracking

## Contributing

This is a proof-of-concept system. Contributions should focus on:

- Improving schema detection accuracy
- Adding new data source connectors
- Enhancing migration safety and rollback capabilities
- Performance optimizations for large-scale data
- Better error handling and user feedback

## License

[Add appropriate license information]