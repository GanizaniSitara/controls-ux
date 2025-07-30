---
category: Development
description: Start both backend API and frontend UI servers
---

# Start both backend and frontend servers

```bash
# Start backend API server
cd /mnt/c/Solutions/fitness-functions/api && python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000 > ../api_server.log 2>&1 &

# Start frontend UI server
cd /mnt/c/Solutions/fitness-functions/ui && npm start > ../ui_server.log 2>&1 &

# Wait a moment for servers to start
sleep 5

# Check if servers are running
ps aux | grep -E "(uvicorn|node)" | grep -v grep

echo ""
echo "Servers started! Access the application at:"
echo "- Frontend UI: http://localhost:3003"
echo "- Fitness Function Editor: http://localhost:3003/fitness-functions"
echo "- Backend API: http://localhost:8000"
echo "- GraphQL Playground: http://localhost:8000/graphql"
```

To stop the servers later:
```bash
pkill -f uvicorn
pkill -f "react-scripts"
```