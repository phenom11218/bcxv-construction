@echo off
REM ============================================================================
REM Weekly Smart Scraping Script
REM ============================================================================
REM Runs every Sunday to discover new postings and update active/pending ones
REM
REM Schedule: Weekly, Sundays at 2:00 AM
REM Runtime: ~1.5-2.5 hours
REM
REM Author: BCXV Construction Analytics
REM Date: 2025-12-12
REM ============================================================================

cd /d "C:\Users\ramih\llm_projects\scraper\Alberta Purchasing Construction\scraper"

echo ============================================================================ >> logs\scraping.log
echo [%date% %time%] WEEKLY SCRAPING STARTED >> logs\scraping.log
echo ============================================================================ >> logs\scraping.log

REM Step 1: Discover new postings for current year
echo [%date% %time%] Step 1/6: Discovering new postings... >> logs\scraping.log
python scrape_new_postings.py >> logs\scraping.log 2>&1
if %errorlevel% neq 0 (
    echo [%date% %time%] ERROR: scrape_new_postings.py failed with code %errorlevel% >> logs\scraping.log
    goto :error
)
echo [%date% %time%] Step 1/6: Complete >> logs\scraping.log

REM Step 2: Update Tier 1 (OPEN postings)
echo [%date% %time%] Step 2/6: Updating OPEN postings (Tier 1)... >> logs\scraping.log
python update_active_postings.py --tier 1 >> logs\scraping.log 2>&1
if %errorlevel% neq 0 (
    echo [%date% %time%] ERROR: Tier 1 update failed with code %errorlevel% >> logs\scraping.log
    goto :error
)
echo [%date% %time%] Step 2/6: Complete >> logs\scraping.log

REM Step 3: Update Tier 2 (Recently CLOSED)
echo [%date% %time%] Step 3/6: Updating recently CLOSED postings (Tier 2)... >> logs\scraping.log
python update_active_postings.py --tier 2 >> logs\scraping.log 2>&1
if %errorlevel% neq 0 (
    echo [%date% %time%] ERROR: Tier 2 update failed with code %errorlevel% >> logs\scraping.log
    goto :error
)
echo [%date% %time%] Step 3/6: Complete >> logs\scraping.log

REM Step 4: Update Tier 3 (Pending awards)
echo [%date% %time%] Step 4/6: Updating pending awards (Tier 3)... >> logs\scraping.log
python update_active_postings.py --tier 3 >> logs\scraping.log 2>&1
if %errorlevel% neq 0 (
    echo [%date% %time%] ERROR: Tier 3 update failed with code %errorlevel% >> logs\scraping.log
    goto :error
)
echo [%date% %time%] Step 4/6: Complete >> logs\scraping.log


REM Step 5: Create database backup
echo [%date% %time%] Step 5/6: Creating database backup... >> logs\scraping.log
python backup_database.py >> logs\scraping.log 2>&1
if %errorlevel% neq 0 (
    echo [%date% %time%] WARNING: Database backup failed with code %errorlevel% >> logs\scraping.log
    REM Don't fail the whole job if backup fails - scraping succeeded
)
echo [%date% %time%] Step 5/6: Complete >> logs\scraping.log


REM Step 6: Sync changes to Turso cloud database
echo [%date% %time%] Step 6/6: Syncing to Turso cloud database... >> logs\scraping.log
python sync_to_turso.py >> logs\scraping.log 2>&1
if %errorlevel% neq 0 (
    echo [%date% %time%] WARNING: Turso sync failed with code %errorlevel% >> logs\scraping.log
    REM Don't fail the whole job if Turso sync fails - scraping and backup succeeded
)
echo [%date% %time%] Step 6/6: Complete >> logs\scraping.log

echo [%date% %time%] WEEKLY SCRAPING COMPLETED SUCCESSFULLY >> logs\scraping.log
echo ============================================================================ >> logs\scraping.log
echo. >> logs\scraping.log
exit /b 0

:error
echo [%date% %time%] WEEKLY SCRAPING FAILED - CHECK LOGS >> logs\scraping.log
echo ============================================================================ >> logs\scraping.log
echo. >> logs\scraping.log
exit /b 1
