@echo off
echo ==========================================
echo   AI Learning Agent - Starter Script
echo ==========================================
echo.

:: Check for port 5000 and kill it if occupied
echo [1/3] Checking for active servers...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000') do (
    echo Terminating old server process...
    taskkill /F /PID %%a >nul 2>&1
)

:: Check for .env file
if not exist .env (
    echo [WARNING] .env file not found! 
    echo Please make sure you have your API keys in a .env file.
    echo Creating a template for you...
    copy sample.env .env
)

:: Install/Verify requirements
echo [2/3] Verifying dependencies...
python -m pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Dependencies failed to install. Please check your internet connection.
    pause
    exit /b
)

:: Start the Application
echo [3/3] Launching AI Agent...
echo.
echo 📍 Open http://127.0.0.1:5000 in your browser
echo 💡 Press Ctrl+C to stop the agent.
echo.
python app.py
pause
