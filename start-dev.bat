@echo off
echo ================================
echo   Starting Full Stack App
echo ================================
echo.
echo Starting Backend on port 5000...
start "Backend - Flask" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate && python run.py"
echo Starting Frontend on port 3000...
timeout /t 3 /nobreak >nul
start "Frontend - React" cmd /k "cd /d %~dp0frontend && npm run dev"
echo.
echo ================================
echo   Backend:  http://localhost:5000
echo   Frontend: http://localhost:3000
echo ================================
