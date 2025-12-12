# Turso Cloud Database Sync Guide
====================================

This guide explains how to keep your Streamlit Cloud app's Turso database synchronized with your local scraping data.

## Overview

### The Problem

You have two databases that need to stay in sync:

1. **Local SQLite Database** (`alberta_procurement.db`)
   - Updated weekly by scraping scripts running on your local computer
   - Contains the most recent data from Alberta Purchasing website

2. **Turso Cloud Database** (on turso.tech)
   - Used by your Streamlit Cloud app for public access
   - Needs to be updated with changes from local database

**Without sync:** Your Streamlit Cloud app shows stale data while your local database has fresh updates.

**With sync:** Weekly scraping automatically pushes changes to Turso, keeping your cloud app up-to-date.

### The Solution

**Automated Incremental Sync:**
- After weekly scraping completes, `sync_to_turso.py` automatically syncs changes
- Only new/updated records are sent (not the entire database)
- Runs as Step 6/6 of weekly automation
- Takes ~5-10 minutes for typical weekly changes

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     YOUR WORKFLOW                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Every Sunday 2:00 AM (Automated):                             │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ 1. Scrape Alberta Purchasing → Local SQLite DB         │   │
│  │ 2. Update OPEN postings → Local SQLite DB             │   │
│  │ 3. Update CLOSED postings → Local SQLite DB           │   │
│  │ 4. Update pending awards → Local SQLite DB            │   │
│  │ 5. Create local backup                                 │   │
│  │ 6. Sync changes to Turso Cloud DB ✨ NEW!            │   │
│  └────────────────────────────────────────────────────────┘   │
│                             ↓                                    │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ Turso Cloud Database (turso.tech)                      │   │
│  │ - Now has latest scraped data                          │   │
│  │ - Automatically updated weekly                          │   │
│  └────────────────────────────────────────────────────────┘   │
│                             ↓                                    │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ Streamlit Cloud App                                     │   │
│  │ - Reads from Turso Cloud Database                      │   │
│  │ - Always shows fresh data                              │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Initial Setup (One-Time)

### Step 1: Install Required Python Package

The sync script requires `libsql-client` and `python-dotenv`:

```cmd
cd "C:\Users\ramih\llm_projects\scraper\Alberta Purchasing Construction\scraper"
pip install libsql-client python-dotenv
```

Or if using virtual environment:

```cmd
..\venv\Scripts\pip.exe install libsql-client python-dotenv
```

### Step 2: Get Your Turso Credentials

Your Turso credentials are already configured in Streamlit Cloud. You need to copy them locally.

**Option A: From Streamlit Cloud Secrets**

1. Go to https://share.streamlit.io
2. Open your app settings
3. Go to "Secrets" section
4. Copy the values for:
   - `database_url` (under `[turso]` section)
   - `auth_token` (under `[turso]` section)

**Option B: From Turso Dashboard**

1. Go to https://turso.tech/dashboard
2. Select your database
3. Click "Show Credentials"
4. Copy:
   - Database URL (e.g., `https://your-db.turso.io` or `libsql://your-db.turso.io`)
   - Auth Token

### Step 3: Create .env File

1. Copy the example file:
   ```cmd
   cd "C:\Users\ramih\llm_projects\scraper\Alberta Purchasing Construction\scraper"
   copy .env.example .env
   ```

2. Edit `.env` file in your text editor
3. Replace the placeholders with your actual credentials:

   ```env
   # Turso database URL (convert libsql:// to https://)
   TURSO_DATABASE_URL=https://your-database-name.turso.io

   # Turso authentication token
   TURSO_AUTH_TOKEN=your-actual-token-here
   ```

4. Save the file

**Important:**
- `.env` is gitignored and won't be committed to GitHub
- Keep this file secure - it contains authentication credentials
- If URL starts with `libsql://`, change it to `https://`

### Step 4: Test the Sync (First Time)

Before enabling automation, test the sync manually:

```cmd
cd "C:\Users\ramih\llm_projects\scraper\Alberta Purchasing Construction\scraper"
python sync_to_turso.py --dry-run
```

**What this does:**
- Connects to Turso using your credentials
- Shows what would be synced (without actually syncing)
- Verifies credentials are correct

**Expected output:**
```
======================================================================
TURSO DATABASE SYNC
======================================================================
Local database: C:\Users\ramih\...\alberta_procurement.db
Turso database: https://your-db.turso.io
Mode: INCREMENTAL SYNC
DRY RUN: No changes will be made

Last sync: Never (this is the first sync)

======================================================================
SYNCING TABLE: opportunities
======================================================================
  Records to sync: 14,187
  [DRY RUN] Would sync these records (not actually syncing)

...

======================================================================
SYNC SUMMARY
======================================================================
Total records checked: 14,187
Total records synced: 0
Total skipped (dry run): 14,187
Time elapsed: 0.5 minutes

[DRY RUN] No changes were made
```

### Step 5: Run First Full Sync

Now run the actual sync (this will take longer on first run):

```cmd
python sync_to_turso.py --full
```

**What this does:**
- Uploads ALL records from local database to Turso
- First sync only - future syncs will be incremental (much faster)
- May take 30-60 minutes depending on database size

**Expected output:**
```
======================================================================
TURSO DATABASE SYNC
======================================================================
Mode: FULL SYNC

======================================================================
SYNCING TABLE: opportunities
======================================================================
  Records to sync: 14,187
  Progress: 100/14187 (  0.7%) | Synced: 100 | Errors: 0
  Progress: 200/14187 (  1.4%) | Synced: 200 | Errors: 0
  ...
  [OK] Synced 14,187 records

...

======================================================================
SYNC SUMMARY
======================================================================
Total records synced: 14,187
Total errors: 0
Time elapsed: 35.2 minutes

[OK] Sync completed successfully
Next sync will only process records modified after: 2025-12-12T15:30:00
```

### Step 6: Verify on Streamlit Cloud

1. Go to your Streamlit Cloud app
2. Check that data is showing up correctly
3. Verify record counts match your local database

**Troubleshooting:**
- If no data shows: Check Turso credentials in Streamlit secrets
- If old data shows: Clear Streamlit cache and reload
- If errors appear: Check sync logs for error messages

## Automation (Weekly Sync)

### How It Works

Your `weekly_scraping.bat` has been updated to include automatic Turso sync as Step 6/6:

**Every Sunday at 2:00 AM:**
1. ✅ Scrape new postings
2. ✅ Update Tier 1 (OPEN)
3. ✅ Update Tier 2 (CLOSED)
4. ✅ Update Tier 3 (Pending awards)
5. ✅ Create local backup
6. ✅ **Sync changes to Turso** ✨

### What Gets Synced

**Incremental sync only uploads:**
- Records modified since last sync (tracked by `last_scraped_at` timestamp)
- New records discovered by scraping
- Updated records (status changes, new awards, etc.)

**Typical weekly sync:**
- ~100-500 changed records
- ~5-10 minutes
- Much faster than full sync

### Checking Sync Status

**View sync logs:**
```cmd
cd "C:\Users\ramih\llm_projects\scraper\Alberta Purchasing Construction\scraper"
type logs\scraping.log | findstr "Step 6/6"
```

**View last sync details:**
```cmd
type logs\scraping.log | findstr "TURSO"
```

**Expected log output:**
```
[2025-12-15 02:15:30] Step 6/6: Syncing to Turso cloud database...
[2025-12-15 02:18:45] Step 6/6: Complete
```

## Manual Sync Commands

### Sync After Manual Scraping

If you run scraping manually (not through automation):

```cmd
cd "C:\Users\ramih\llm_projects/scraper/Alberta Purchasing Construction/scraper"
python sync_to_turso.py
```

This runs an incremental sync (only changed records).

### Force Full Sync

To sync ALL records regardless of timestamp:

```cmd
python sync_to_turso.py --full
```

**When to use:**
- After major database changes
- If incremental sync seems to be missing records
- After restoring from backup

### Dry Run (Preview Changes)

To see what would be synced without actually syncing:

```cmd
python sync_to_turso.py --dry-run
```

Useful for:
- Checking how many records will be synced
- Verifying credentials still work
- Troubleshooting sync issues

### Sync with Command-Line Credentials

If you don't want to use .env file:

```cmd
python sync_to_turso.py --url "https://your-db.turso.io" --token "your-token"
```

## Monitoring and Maintenance

### Check Last Sync Time

The sync state is stored in `.turso_sync_state` file:

```cmd
type .turso_sync_state
```

Output shows the timestamp of last successful sync:
```
2025-12-15T02:18:45.123456
```

### Verify Streamlit Cloud Has Latest Data

1. Check local database record count:
   ```cmd
   sqlite3 ../alberta_procurement.db "SELECT COUNT(*) FROM opportunities"
   ```

2. Check Streamlit Cloud app shows similar count

3. If counts don't match:
   - Check sync logs for errors
   - Run manual sync
   - Verify Turso credentials haven't expired

### Troubleshooting Sync Failures

**Issue:** Sync fails with authentication error

**Solution:**
- Verify `.env` file has correct credentials
- Check if Turso token has expired
- Regenerate token in Turso dashboard if needed

**Issue:** Sync takes too long

**Solution:**
- Check internet connection speed
- Verify you're using incremental sync (not --full)
- Check how many records are being synced with --dry-run

**Issue:** Some records not syncing

**Solution:**
- Run `python sync_to_turso.py --full` to force full sync
- Check for error messages in logs
- Verify local database isn't corrupted

## FAQ

**Q: How often does sync run?**
A: Automatically every Sunday at 2:00 AM as part of weekly scraping. You can also run it manually anytime.

**Q: Does sync slow down weekly scraping?**
A: Yes, adds ~5-10 minutes. But scraping and backup complete first, so if sync fails, your local data is safe.

**Q: What happens if sync fails?**
A: Weekly scraping still completes successfully. Sync failure is logged as WARNING, not ERROR. You can manually re-run sync later.

**Q: Can I sync more frequently?**
A: Yes! Run `python sync_to_turso.py` manually whenever you want. Or modify `weekly_scraping.bat` to run daily.

**Q: Will this sync everything, even old data?**
A: No. Incremental sync only uploads records modified since last sync. Use `--full` flag to sync everything.

**Q: How do I know if sync is working?**
A: Check `logs\scraping.log` for "Step 6/6: Complete" after weekly scraping. Also verify Streamlit Cloud app shows updated data.

**Q: What if I want to stop using Turso?**
A: Remove Step 6 from `weekly_scraping.bat`. Your local database will continue to work fine.

**Q: Can I sync to a different Turso database?**
A: Yes, just update the credentials in `.env` file.

**Q: Is my data secure?**
A: Yes. Credentials in `.env` are gitignored. Turso uses HTTPS and authentication tokens. Keep your `.env` file secure.

**Q: What if I accidentally delete records in Turso?**
A: Run `python sync_to_turso.py --full` to restore all records from your local database.

## Summary

### What You Did

✅ Installed required packages (`libsql-client`, `python-dotenv`)
✅ Created `.env` file with Turso credentials
✅ Tested sync with `--dry-run`
✅ Ran initial full sync
✅ Verified data appears in Streamlit Cloud app

### What Happens Now

🔄 **Every Sunday at 2:00 AM:**
- Local scraping runs and updates local database
- Sync automatically pushes changes to Turso
- Streamlit Cloud app automatically has latest data

### Your Responsibilities

✅ Keep `.env` file secure (never commit to Git)
✅ Monitor sync logs occasionally
✅ Verify Streamlit Cloud app shows current data

### Files Created

| File | Purpose |
|------|---------|
| `sync_to_turso.py` | Incremental sync script |
| `.env` | Turso credentials (gitignored) |
| `.env.example` | Template for credentials |
| `.turso_sync_state` | Tracks last sync timestamp |
| `TURSO_SYNC_GUIDE.md` | This guide |

### Next Steps

1. ✅ Setup complete!
2. Wait for next Sunday's automated scraping/sync
3. Verify Streamlit Cloud app updates automatically
4. Enjoy automated data pipeline! 🎉

---

**Author:** BCXV Construction Analytics
**Date:** 2025-12-12
**Version:** 1.0
