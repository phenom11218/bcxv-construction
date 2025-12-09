@echo off
REM BCXV Construction - Quick Start Script
REM Activates venv and runs Streamlit app
REM Date: 2025-12-08

echo ========================================
echo BCXV Construction - Bid Analytics
echo ========================================
echo.

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then run: venv\Scripts\activate
    echo Then run: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
echo [1/3] Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if streamlit is installed
venv\Scripts\streamlit.exe --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Streamlit not installed!
    echo Please run: pip install -r requirements.txt
    pause
    exit /b 1
)

echo [2/3] Testing database connection...
cd streamlit_app\utils
python database.py
if errorlevel 1 (
    echo [ERROR] Database connection failed!
    echo Check that alberta_procurement.db exists in:
    echo   ..\scraper\Alberta Purchasing Construction\
    pause
    exit /b 1
)

echo.
echo [3/3] Starting Streamlit app...
echo.
echo ========================================
echo App will open in your browser shortly
echo Press Ctrl+C to stop the server
echo ========================================
echo.

cd ..
streamlit run app.py

pause