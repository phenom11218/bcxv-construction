@echo off
REM Alberta Procurement Overnight Scraper
REM Scrapes all remaining 2025 postings (501-7557)

echo ======================================================================
echo ALBERTA PROCUREMENT - OVERNIGHT SCRAPE
echo ======================================================================
echo.
echo Starting scrape of 2025 postings 501-7557
echo This will take approximately 2-2.5 hours
echo.
echo Start time: %date% %time%
echo.
echo You can monitor progress by running:
echo   python check_progress.py
echo.
echo Press Ctrl+C to stop at any time (progress will be saved)
echo ======================================================================
echo.

REM Create logs directory if it doesn't exist
if not exist logs mkdir logs

REM Generate log filename with timestamp
set LOGFILE=logs\scrape_2025_501-7557_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log
set LOGFILE=%LOGFILE: =0%

echo Starting scrape...
echo Log file: %LOGFILE%
echo.

REM Run the scraper and log output
python alberta_scraper_sqlite.py 2025 501 7557 > "%LOGFILE%" 2>&1

echo.
echo ======================================================================
echo SCRAPE COMPLETED
echo ======================================================================
echo End time: %date% %time%
echo Log saved to: %LOGFILE%
echo.
echo Run the following to see results:
echo   python check_progress.py
echo   python database_setup.py
echo ======================================================================
echo.

pause
