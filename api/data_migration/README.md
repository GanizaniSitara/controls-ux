# Data Migration Folder

This folder is for production data that has been migrated or transformed from various sources.

## Purpose

- Contains production-ready CSV files that have been processed/migrated from source systems
- Data in this folder will show as "LOAD OK" in the UI (production status)
- Use this folder when you have real production data that needs to be loaded

## Usage

To use data from this folder, update your `settings.ini` file to point to files here:

```ini
[providers]
code_quality = data_migration\code_quality_v1.csv
security = data_migration\security_v1.csv
# ... etc
```

## Data Status

Files loaded from this folder will automatically be marked as:
- Provider Type: "production"
- Data Status: "LOAD OK"

This is in contrast to:
- `data_mock/` - Shows as "DEMO DATA"
- `data_prod/` - Also shows as "LOAD OK"
- `data_test/` - Shows as test data