# Windows Task Scheduler Setup Guide
=====================================

This guide will help you set up automated weekly scraping and monthly analysis tasks using Windows Task Scheduler.

## Prerequisites

✅ Created automation scripts:
- `weekly_scraping.bat`
- `monthly_analysis.bat`

✅ Created logs directory:
- `logs/` folder exists in scraper directory

✅ Completed initial setup:
- Run `python fix_scrape_log_constraint.py` (one-time)
- Run `python database_migrations.py` (one-time)
- Run initial `python update_active_postings.py` (one-time, ~2 hours)

## Setup Instructions

### Part 1: Create Weekly Scraping Task

1. **Open Task Scheduler**
   - Press `Win + R`
   - Type `taskschd.msc`
   - Press Enter

2. **Create New Task**
   - In the right panel, click "Create Basic Task..."
   - Name: `Alberta Construction - Weekly Scraping`
   - Description: `Weekly scraping for new postings and active updates (Tiers 1-3)`
   - Click "Next"

3. **Set Trigger (Weekly Schedule)**
   - Select "Weekly"
   - Click "Next"
   - Start date: Select today's date
   - Start time: `02:00:00 AM`
   - Recur every: `1` weeks
   - Check: `Sunday` (or whichever day you prefer)
   - Click "Next"

4. **Set Action (Run Batch File)**
   - Select "Start a program"
   - Click "Next"
   - Program/script: Click "Browse" and navigate to:
     ```
     C:\Users\ramih\llm_projects\scraper\Alberta Purchasing Construction\scraper\weekly_scraping.bat
     ```
   - Start in (optional): Leave blank (script handles this)
   - Click "Next"

5. **Review and Finish**
   - Review the summary
   - Check "Open the Properties dialog for this task when I click Finish"
   - Click "Finish"

6. **Configure Advanced Settings**
   - In the Properties dialog that opens:

   **General Tab:**
   - Check "Run whether user is logged on or not"
   - Check "Run with highest privileges"

   **Conditions Tab:**
   - Uncheck "Start the task only if the computer is on AC power"
   - Check "Wake the computer to run this task" (optional)

   **Settings Tab:**
   - Check "Allow task to be run on demand"
   - Check "Run task as soon as possible after a scheduled start is missed"
   - "If the task fails, restart every": `15 minutes`
   - "Attempt to restart up to": `3` times
   - "Stop the task if it runs longer than": `4 hours`

   - Click "OK"

7. **Enter Windows Password**
   - Windows will prompt for your password to save the task
   - Enter your password and click "OK"

### Part 2: Create Monthly Analysis Task

1. **Create New Task**
   - In Task Scheduler, click "Create Basic Task..." again
   - Name: `Alberta Construction - Monthly Analysis`
   - Description: `Monthly award verification and timing analysis (Tier 4)`
   - Click "Next"

2. **Set Trigger (Monthly Schedule)**
   - Select "Monthly"
   - Click "Next"
   - Start date: Select today's date
   - Start time: `03:00:00 AM`
   - Months: Check "All months"
   - Days: Select "1" (first day of month)
   - Click "Next"

3. **Set Action (Run Batch File)**
   - Select "Start a program"
   - Click "Next"
   - Program/script: Click "Browse" and navigate to:
     ```
     C:\Users\ramih\llm_projects\scraper\Alberta Purchasing Construction\scraper\monthly_analysis.bat
     ```
   - Start in (optional): Leave blank
   - Click "Next"

4. **Review and Finish**
   - Review the summary
   - Check "Open the Properties dialog for this task when I click Finish"
   - Click "Finish"

5. **Configure Advanced Settings**
   - Same as weekly task (see Part 1, Step 6)
   - Click "OK"

6. **Enter Windows Password**
   - Enter your password and click "OK"

## Testing Your Setup

### Test Weekly Scraping Task

1. Open Task Scheduler
2. Navigate to "Task Scheduler Library"
3. Find "Alberta Construction - Weekly Scraping"
4. Right-click and select "Run"
5. Watch the "Status" column - it should show "Running"
6. Check the logs:
   ```cmd
   cd "C:\Users\ramih\llm_projects\scraper\Alberta Purchasing Construction\scraper"
   type logs\scraping.log
   ```

### Test Monthly Analysis Task

1. Open Task Scheduler
2. Navigate to "Task Scheduler Library"
3. Find "Alberta Construction - Monthly Analysis"
4. Right-click and select "Run"
5. Watch the "Status" column
6. Check the logs:
   ```cmd
   cd "C:\Users\ramih\llm_projects\scraper\Alberta Purchasing Construction\scraper"
   type logs\analysis.log
   ```

## Monitoring and Maintenance

### Check Task Status

1. Open Task Scheduler
2. Click on "Task Scheduler Library"
3. Look for your tasks in the list
4. Columns to monitor:
   - **Status**: Should be "Ready" when not running
   - **Last Run Time**: Shows when task last executed
   - **Last Run Result**: `(0x0)` means success, other codes indicate errors
   - **Next Run Time**: Shows next scheduled execution

### View Execution History

1. Select a task in Task Scheduler
2. Click on the "History" tab at the bottom
3. Review events:
   - Event ID `200`: Task started
   - Event ID `201`: Task completed successfully
   - Event ID `203`: Task execution error

### Check Logs

**Weekly Scraping Logs:**
```cmd
cd "C:\Users\ramih\llm_projects\scraper\Alberta Purchasing Construction\scraper"
type logs\scraping.log
```

**Monthly Analysis Logs:**
```cmd
cd "C:\Users\ramih\llm_projects\scraper\Alberta Purchasing Construction\scraper"
type logs\analysis.log
```

### View Recent Log Entries

**Last 50 lines of scraping log:**
```cmd
powershell "Get-Content logs\scraping.log -Tail 50"
```

**Last 50 lines of analysis log:**
```cmd
powershell "Get-Content logs\analysis.log -Tail 50"
```

## Troubleshooting

### Task Shows "Could not start" Error

**Cause:** Path to batch file is incorrect

**Fix:**
1. Right-click task → Properties
2. Go to "Actions" tab
3. Edit the action
4. Verify the full path is correct:
   ```
   C:\Users\ramih\llm_projects\scraper\Alberta Purchasing Construction\scraper\weekly_scraping.bat
   ```

### Task Runs But Nothing Happens

**Cause:** Python virtual environment not activated or script errors

**Fix:**
1. Check logs for errors
2. Manually run the batch file to see if it works:
   ```cmd
   cd "C:\Users\ramih\llm_projects\scraper\Alberta Purchasing Construction\scraper"
   weekly_scraping.bat
   ```
3. Verify Python path in batch file is correct

### Task Runs Too Long

**Cause:** Update taking longer than expected (Tier 3 can be slow)

**Fix:**
1. Check "Settings" tab in task properties
2. Increase "Stop the task if it runs longer than" to 6 hours
3. Or remove the time limit entirely (not recommended)

### Computer Is Asleep When Task Should Run

**Cause:** Power settings preventing task execution

**Fix:**
1. Task Properties → "Conditions" tab
2. Check "Wake the computer to run this task"
3. Or change task schedule to when computer is usually awake

### Permission Denied Errors

**Cause:** Task not running with sufficient privileges

**Fix:**
1. Task Properties → "General" tab
2. Check "Run with highest privileges"
3. Verify the user account has access to database files

## Task Schedule Summary

| Task | Frequency | Time | Duration | Tiers | Purpose |
|------|-----------|------|----------|-------|---------|
| Weekly Scraping | Every Sunday | 2:00 AM | ~1-2 hours | 1, 2, 3 | Discover new postings, update OPEN/CLOSED/pending |
| Monthly Analysis | 1st of month | 3:00 AM | ~30 minutes | 4 | Verify recent awards, generate statistics |

## Expected Runtimes

- **Tier 1** (OPEN postings): ~50 postings → 5-10 minutes
- **Tier 2** (Recent CLOSED): ~200 postings → 15-20 minutes
- **Tier 3** (Pending awards): ~5,000 postings → 1-2 hours
- **Tier 4** (Recent awards): ~300 postings → 10-15 minutes
- **New posting discovery**: ~50 postings → 5-10 minutes
- **Award timing analysis**: ~15,000 postings → 5-10 minutes

## Next Steps

1. ✅ Complete initial setup (run fix_scrape_log_constraint.py and migrations)
2. ✅ Run initial update_active_postings.py manually (one-time, ~2 hours)
3. ✅ Create both tasks in Task Scheduler following this guide
4. ✅ Test both tasks manually
5. ✅ Check logs to verify successful execution
6. ✅ Wait for first scheduled run and monitor logs

## Log File Examples

**Successful Weekly Scraping Log:**
```
============================================================================
[12/12/2025  2:00:15.23] WEEKLY SCRAPING STARTED
============================================================================
[12/12/2025  2:00:15.45] Step 1/5: Discovering new postings...
[12/12/2025  2:05:32.12] Found 12 new postings
[12/12/2025  2:05:32.15] Step 1/5: Complete
[12/12/2025  2:05:32.20] Step 2/5: Updating OPEN postings (Tier 1)...
[12/12/2025  2:10:15.34] Updated 45 OPEN postings
[12/12/2025  2:10:15.40] Step 2/5: Complete
...
[12/12/2025  4:15:22.10] WEEKLY SCRAPING COMPLETED SUCCESSFULLY
============================================================================
```

**Successful Monthly Analysis Log:**
```
============================================================================
[01/01/2026  3:00:10.15] MONTHLY ANALYSIS STARTED
============================================================================
[01/01/2026  3:00:10.25] Step 1/2: Verifying recent awards (Tier 4)...
[01/01/2026  3:12:45.50] Verified 287 recent awards
[01/01/2026  3:12:45.55] Step 1/2: Complete
[01/01/2026  3:12:45.60] Step 2/2: Generating award timing report...
[01/01/2026  3:18:22.75] Report saved to reports/
[01/01/2026  3:18:22.80] Step 2/2: Complete
[01/01/2026  3:18:22.85] MONTHLY ANALYSIS COMPLETED SUCCESSFULLY
============================================================================
```

## Support

If you encounter issues:

1. Check the log files first
2. Verify all paths are correct
3. Test batch files manually before scheduling
4. Ensure initial setup (migrations, constraint fix) was completed
5. Verify Python environment is accessible

---

**Author:** BCXV Construction Analytics
**Date:** 2025-12-12
**Purpose:** Automated smart scraping and analysis
