---
category: Development
description: Start both backend API and frontend UI servers for Control-UX
---

# Start both backend and frontend servers

```bash
# Start backend API server on port 8001
cd /mnt/c/git/control-ux/api && python -m uvicorn app:app --reload --host 0.0.0.0 --port 8001 > ../api_server.log 2>&1 &

# Start frontend UI server on port 3004
cd /mnt/c/git/control-ux/ui && npm start > ../ui_server.log 2>&1 &

# Wait a moment for servers to start
sleep 5

# Check if servers are running
ps aux | grep -E "(uvicorn|node)" | grep -v grep

echo ""
echo "Servers started! Access the application at:"
echo "- Frontend UI: http://localhost:3004"
echo "- Control Dashboard: http://localhost:3004/"
echo "- Backend API: http://localhost:8001"
echo "- GraphQL Playground: http://localhost:8001/graphql"
```

To stop the servers later:
```bash
pkill -f "uvicorn.*8001"
pkill -f "react-scripts.*3004"
```

To check logs:
```bash
# Backend logs
tail -f /mnt/c/git/control-ux/api_server.log

# Frontend logs
tail -f /mnt/c/git/control-ux/ui_server.log
```

To restart servers:
```bash
# Stop servers
pkill -f "uvicorn.*8001"
pkill -f "react-scripts.*3004"

# Start again
cd /mnt/c/git/control-ux/api && python -m uvicorn app:app --reload --host 0.0.0.0 --port 8001 > ../api_server.log 2>&1 &
cd /mnt/c/git/control-ux/ui && npm start > ../ui_server.log 2>&1 &
```