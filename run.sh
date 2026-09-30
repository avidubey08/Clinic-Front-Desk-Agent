#!/usr/bin/env bash
set -e

echo "============================================================"
echo "Starting Sunrise Clinic Front Desk Agent"
echo "============================================================"

# Start backend
echo "Starting FastAPI Backend on port 8000..."
python3 -m uvicorn backend.app.main:app --port 8000 --host 0.0.0.0 &
BACKEND_PID=$!

# Start frontend
echo "Starting React Frontend on port 5173..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "Application running!"
echo "Frontend: http://localhost:5173"
echo "Backend API: http://localhost:8000/agent/run"
echo "API Docs: http://localhost:8000/docs"
echo "============================================================"

# Wait on background processes
trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
