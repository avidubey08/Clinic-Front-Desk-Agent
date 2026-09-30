@echo off
echo ============================================================
echo Starting Sunrise Clinic Front Desk Agent
echo ============================================================

echo Starting FastAPI Backend on port 8000...
start "Backend - FastAPI" cmd /k "python -m uvicorn backend.app.main:app --port 8000 --host 127.0.0.1"

echo Starting React Frontend on port 5173...
cd frontend
start "Frontend - React" cmd /k "npm run dev"

echo.
echo Application started!
echo Frontend: http://localhost:5173
echo Backend API: http://localhost:8000/agent/run
echo API Docs: http://localhost:8000/docs
echo ============================================================
