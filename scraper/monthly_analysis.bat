@echo off
REM ============================================================================
REM Monthly Analysis & Maintenance Script
REM ============================================================================
REM Runs on the 1st of each month to verify awards and generate statistics
REM
REM Schedule: Monthly, 1st at 3:00 AM
REM Runtime: ~30 minutes
REM
REM Author: BCXV Construction Analytics
REM Date: 2025-12-12
REM ============================================================================

cd /d "C:\Users\ramih\llm_projects\scraper\Alberta Purchasing Construction\scraper"

echo ============================================================================ >> logs\analysis.log
echo [%date% %time%] MONTHLY ANALYSIS STARTED >> logs\analysis.log
echo ============================================================================ >> logs\analysis.log

REM Step 1: Verify recent awards (Tier 4)
echo [%date% %time%] Step 1/2: Verifying recent awards (Tier 4)... >> logs\analysis.log
python update_active_postings.py --tier 4 >> logs\analysis.log 2>&1
if %errorlevel% neq 0 (
    echo [%date% %time%] ERROR: Tier 4 update failed with code %errorlevel% >> logs\analysis.log
    goto :error
)
echo [%date% %time%] Step 1/2: Complete >> logs\analysis.log

REM Step 2: Generate award timing analysis
echo [%date% %time%] Step 2/2: Generating award timing report... >> logs\analysis.log
python analyze_award_timing.py >> logs\analysis.log 2>&1
if %errorlevel% neq 0 (
    echo [%date% %time%] ERROR: Analysis failed with code %errorlevel% >> logs\analysis.log
    goto :error
)
echo [%date% %time%] Step 2/2: Complete >> logs\analysis.log

echo [%date% %time%] MONTHLY ANALYSIS COMPLETED SUCCESSFULLY >> logs\analysis.log
echo ============================================================================ >> logs\analysis.log
echo. >> logs\analysis.log
exit /b 0

:error
echo [%date% %time%] MONTHLY ANALYSIS FAILED - CHECK LOGS >> logs\analysis.log
echo ============================================================================ >> logs\analysis.log
echo. >> logs\analysis.log
exit /b 1
