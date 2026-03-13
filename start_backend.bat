@echo off
echo ===================================================
echo   Predictive Logistics Engine - Hackathon Starter
echo ===================================================
echo.
echo Starting all backend services...
echo.

:: Initialize virtual environment if it exists, otherwise just use system python
IF EXIST "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo [1/3] Starting the Logistics Simulator (Fake Trucks)...
start "Simulator" cmd /c "python simulation\simulator.py"

echo [2/3] Starting the ML Prediction Worker (AI Engine)...
start "ML Worker" cmd /c "python backend\ml_worker.py"

echo [3/3] Starting the Data API server...
start "API Server" cmd /c "python backend\api.py"

echo.
echo ===================================================
echo   SUCCESS! All services are running in new windows.
echo   Your Vercel dashboard should now update LIVE!
echo ===================================================
echo.
echo Note: Keep those 3 black windows open while presenting.
echo       When finished, just close the terminal windows.
pause
