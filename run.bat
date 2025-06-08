@echo off
echo Starting Smart Construction Platform...

REM Create necessary directories
mkdir data\video_frames 2>nul

REM Check if MongoDB is running
echo Checking MongoDB status...
mongo --eval "db.version()" >nul 2>&1
if %errorlevel% neq 0 (
  echo MongoDB is not running! Please start MongoDB first.
  echo You can start it by running: net start MongoDB
  exit /b 1
)

REM Set up the database
echo Setting up database...
cd database
python setup.py
cd ..

REM Start the backend in a new window
echo Starting backend server...
start cmd /k "cd backend && python run.py"

REM Wait for backend to start
echo Waiting for backend to initialize...
timeout /t 5 /nobreak > nul

REM Start the frontend in a new window
echo Starting frontend development server...
start cmd /k "cd frontend && npm run dev"

echo Smart Construction Platform is starting up...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to shut down the platform.
pause > nul

REM Shutdown procedure
echo Shutting down platform...
taskkill /f /im node.exe > nul 2>&1
taskkill /f /im python.exe > nul 2>&1

echo Platform shutdown complete.

REM Test video stream
echo Testing video stream...
cd backend
python test_stream.py 