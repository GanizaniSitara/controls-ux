# Control-UX

Banking control monitoring platform for enterprise compliance.

## Quick Start (Windows)

### First Time Setup
```batch
# Run from control-ux directory
setup_control_ux.bat
```

### Configure for Work Environment
If your control scripts are in a parallel directory:
```
your-workspace/
├── scripts/
│   └── evidence/     # Control scripts write here
└── control-ux/       # This repository
```

Run:
```batch
configure_work_environment.bat
```

### Start the Platform
```batch
start_control_ux.bat
```

Access the platform at:
- UI: http://localhost:3004
- API: http://localhost:8002

### Stop the Platform
```batch
stop_control_ux.bat
```

## Quick Start (Linux/Mac)

1. Start the backend API:
```bash
cd api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --port 8002
```

2. Start the frontend UI:
```bash
cd ui
npm install
npm start
```

## Evidence Path Configuration

The API looks for evidence in these locations (in order):
1. Environment variable: `CONTROL_UX_EVIDENCE_PATH`
2. `../evidence` (relative to API directory)
3. `../../evidence` (for development)
4. `../../scripts/evidence` (for work environment)

To configure a custom path, set the environment variable:
```batch
# Windows
setx CONTROL_UX_EVIDENCE_PATH "C:\your\path\to\evidence"

# Linux/Mac
export CONTROL_UX_EVIDENCE_PATH="/your/path/to/evidence"
```

## Features

- Real-time control status monitoring
- Evidence comparison and analysis
- Compliance reporting
- Risk heat maps
- Control execution grid view
- Click-through to evidence reports

## Architecture

### Push Model
Control-UX operates on a push model where:
- Control scripts remain in your enterprise environment
- Scripts generate evidence files in a shared location
- Control-UX reads and analyzes these evidence files
- No control logic is stored in Control-UX

### Components
- **Backend API**: FastAPI application (Python)
- **Frontend UI**: React application (TypeScript)
- **Evidence Scanner**: Analyzes control execution results
- **Comparison Engine**: Tracks changes across control runs

## Development

This platform is designed to analyze control execution results from enterprise control scripts. The evidence folder structure should follow:

```
evidence/
├── CTRL-00042697_2025-01-30_08-15/
│   ├── STEP1_*.json
│   ├── STEP2_*.txt
│   └── Evidence_report.html
└── CTRL-00042697_2025-01-30_10-15/
    └── ...
```

## Troubleshooting

### Evidence Not Found
Check that:
1. The evidence path is correctly configured
2. Control scripts are writing to the expected location
3. The API has read permissions for the evidence folder

### Port Conflicts
If ports 8002 or 3004 are in use:
1. Stop conflicting services
2. Or modify the ports in the batch files

## License

Enterprise use only.