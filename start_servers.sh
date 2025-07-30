#!/bin/bash

# Start both backend and frontend servers for Control-UX

echo "Starting Control-UX servers..."

# Start backend API server
cd /mnt/c/git/control-ux/api && python -m uvicorn app:app --reload --host 0.0.0.0 --port 8001 > ../api_server.log 2>&1 &
echo "Backend API starting on port 8001..."

# Start frontend UI server
cd /mnt/c/git/control-ux/ui && npm start > ../ui_server.log 2>&1 &
echo "Frontend UI starting on port 3004..."

# Wait a moment for servers to start
sleep 5

# Check if servers are running
echo ""
echo "Checking server status:"
ps aux | grep -E "(uvicorn|node)" | grep -v grep

echo ""
echo "Servers started! Access the application at:"
echo "- Frontend UI: http://localhost:3004"
echo "- Evidence Reports: http://localhost:3004/evidence-reports"
echo "- Backend API: http://localhost:8001"
echo "- GraphQL Playground: http://localhost:8001/graphql"
echo ""
echo "To view logs:"
echo "- Backend: tail -f /mnt/c/git/control-ux/api_server.log"
echo "- Frontend: tail -f /mnt/c/git/control-ux/ui_server.log"
echo ""
echo "To stop the servers later:"
echo "pkill -f 'uvicorn.*8001'"
echo "pkill -f 'react-scripts'"