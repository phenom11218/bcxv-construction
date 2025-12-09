@echo off
REM Quick-start script for BCXV Construction Analytics
REM Activates virtual environment, tests database connection, and launches Streamlit

echo ================================================
echo BCXV Construction Analytics - Quick Start
echo ================================================
echo.

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Testing database connection...
cd utils
python database.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Database connection test failed!
    echo Please check that alberta_procurement.db exists in the project root.
    pause
    exit /b 1
)

echo.
echo Database connection successful!
echo.
echo Launching Streamlit app...
cd ..
streamlit run app.py

pause
