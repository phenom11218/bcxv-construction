#!/bin/bash
# Quick-start script for BCXV Construction Analytics
# For Git Bash / Unix-like shells
# Activates virtual environment, tests database connection, and launches Streamlit

echo "================================================"
echo "BCXV Construction Analytics - Quick Start"
echo "================================================"
echo ""

echo "Activating virtual environment..."
source venv/Scripts/activate

echo ""
echo "Testing database connection..."
cd utils
python database.py
if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Database connection test failed!"
    echo "Please check that alberta_procurement.db exists in the project root."
    exit 1
fi

echo ""
echo "Database connection successful!"
echo ""
echo "Launching Streamlit app..."
cd ..
streamlit run app.py

read -p "Press Enter to exit..."
