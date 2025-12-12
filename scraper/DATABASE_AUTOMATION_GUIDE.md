# Database Automation Guide
=====================================

This guide explains how your database is managed, backed up, and synchronized.

## Current Setup

### 📁 **Local-First Architecture**

Your system operates on a **local-first** model:
- Weekly scraping updates the local SQLite database (`alberta_procurement.db`)
- Analytics app reads from the local database
- No automatic sync to GitHub or cloud required
- All data stays on your local machine

###  Database Locations

| Database | Location | Purpose |
|----------|----------|---------|
| **Primary** | `alberta_procurement.db` | Main database used by scraper and analytics app |
| **Backups** | `database_backups/` | Timestamped backups (keeps last 4 weeks) |
| **Turso Cloud** | Optional | For cloud deployment (manual sync only) |

## Automated Backup System

### ✅ **Weekly Automatic Backups**

Your `weekly_scraping.bat` now includes automatic database backups:

**When it runs:**
- Every Sunday at 2:00 AM (via Windows Task Scheduler)
- After completing all scraping tiers (Steps 1-4)
- Before the job finishes (Step 5/5)

**What it does:**
1. Creates timestamped backup: `alberta_procurement_backup_YYYYMMDD_HHMMSS.db`
2. Saves to `database_backups/` folder
3. Keeps last 4 backups (deletes older ones)
4. Logs backup status to `logs/scraping.log`

**Backup retention:**
- Default: 4 weekly backups (~1 month of history)
- Customizable: Run `python backup_database.py --keep 8` to keep more

### 📋 **Manual Backup Commands**

**Create a backup anytime:**
```cmd
cd "C:\Users\ramih\llm_projects\scraper\Alberta Purchasing Construction\scraper"
python backup_database.py
```

**Keep more backups:**
```cmd
python backup_database.py --keep 8   # Keep 8 backups instead of 4
```

**List all backups:**
```cmd
python backup_database.py --list
```

**Restore from a backup:**
```cmd
python backup_database.py --restore "database_backups\alberta_procurement_backup_20251212_140000.db"
```

## Do You Need to Push to GitHub?

### ❌ **No - GitHub Push NOT Required**

**For local use:**
- Your current setup is **local-only**
- Scraping updates the local database
- Analytics app reads from local database
- **No GitHub sync needed**

**Why not push database to GitHub:**
- Database files are large (currently ~50+ MB)
- Binary files don't work well with Git
- Git is designed for code, not data
- Backups serve this purpose better

### ✅ **What You SHOULD Push to GitHub**

Push these files to GitHub (code changes only):
- Python scripts (`.py` files)
- Batch files (`.bat` files)
- Configuration files
- Documentation (`.md` files)
- Analytics app code

**DO NOT push:**
- `alberta_procurement.db` (database file)
- `database_backups/` folder
- `logs/` folder
- `*.log` files

## Cloud Deployment Options

If you want to deploy the analytics app to the cloud (e.g., Streamlit Cloud), you have two options:

### Option 1: Turso Cloud Database (Recommended for Cloud)

**Benefits:**
- Free tier available
- Globally distributed
- Fast read performance
- Easy to sync

**Setup:**
1. Create Turso account and database (already done)
2. Get database URL and auth token
3. Update `analytics-app/.streamlit/secrets.toml`:
   ```toml
   [database]
   type = "turso"

   [turso]
   database_url = "libsql://your-db.turso.io"
   auth_token = "your-token-here"
   ```

**Manual sync after scraping:**
```cmd
cd "C:\Users\ramih\llm_projects\scraper\Alberta Purchasing Construction\scraper"
python upload_to_turso.py  # Script needs to be created
```

### Option 2: GitHub + Streamlit Cloud (Not Recommended)

**Issues:**
- Database file too large for Git
- Slow deployments
- Not designed for this use case

**Alternative:**
- Use Turso for cloud deployment
- Keep local database for development

## Automation Summary

###  **Current Weekly Automation**

**Sunday 2:00 AM:**
1. Discover new postings (Step 1/5)
2. Update OPEN postings - Tier 1 (Step 2/5)
3. Update CLOSED postings - Tier 2 (Step 3/5)
4. Update pending awards - Tier 3 (Step 4/5)
5. **Create database backup** (Step 5/5) ✨ NEW!

**Duration:** ~1.5-2.5 hours

**Logs:** `logs/scraping.log`

### 📅 **Current Monthly Automation**

**1st of month, 3:00 AM:**
1. Verify recent awards - Tier 4
2. Generate award timing analysis

**Duration:** ~1 minute

**Logs:** `logs/analysis.log`

## Monitoring Your Backups

### Check Backup Status

**View recent backups:**
```cmd
cd "C:\Users\ramih\llm_projects\scraper\Alberta Purchasing Construction\scraper"
python backup_database.py --list
```

**Output example:**
```
======================================================================
AVAILABLE BACKUPS
======================================================================

Found 4 backup(s):

1. alberta_procurement_backup_20251212_020530.db
   Created: 2025-12-12 02:05:30
   Size: 52.3 MB
   Records: 6,720 opportunities

2. alberta_procurement_backup_20251205_020430.db
   Created: 2025-12-05 02:04:30
   Size: 51.8 MB
   Records: 6,607 opportunities

...
```

### Check Last Backup in Logs

```cmd
cd "C:\Users\ramih\llm_projects\scraper\Alberta Purchasing Construction\scraper"
findstr /C:"Step 5/5" logs\scraping.log
```

## Disaster Recovery

### Scenario 1: Database Corrupted

**Restore from most recent backup:**
```cmd
cd "C:\Users\ramih\llm_projects\scraper\Alberta Purchasing Construction\scraper"
python backup_database.py --list
python backup_database.py --restore "database_backups\alberta_procurement_backup_YYYYMMDD_HHMMSS.db"
```

### Scenario 2: Accidentally Deleted Data

**Restore from backup before the deletion:**
1. Check backup list to find the right backup
2. Restore that specific backup
3. A safety backup of current database is created automatically

### Scenario 3: Need Older Data

**Backups only keep 4 weeks by default.**

To keep longer history:
1. Update weekly_scraping.bat to keep more backups:
   ```batch
   python backup_database.py --keep 12  :: Keep 3 months
   ```
2. Or manually copy important backups to a separate location

## Best Practices

### ✅ **DO:**
- Keep local backups enabled (already done)
- Monitor backup logs after weekly scraping
- Test restore process occasionally
- Use Turso for cloud deployment if needed
- Push code changes to GitHub regularly

### ❌ **DON'T:**
- Don't push database file to GitHub
- Don't delete `database_backups/` folder
- Don't modify backups manually
- Don't rely solely on backups - they're 1 week old at most

## FAQ

**Q: How often is the database backed up?**
A: Every Sunday at 2:00 AM after scraping completes (Step 5/5).

**Q: How many backups are kept?**
A: 4 backups by default (~1 month). Customize with `--keep` flag.

**Q: Where are backups stored?**
A: `database_backups/` folder in the project root.

**Q: Do I need to push database to GitHub?**
A: No. The database stays local. Only push code changes.

**Q: How do I access data from another computer?**
A: Use Turso cloud database and configure analytics app to connect to it.

**Q: What if backup fails?**
A: Weekly scraping continues anyway. Backup failure won't stop scraping. Check logs for errors.

**Q: Can I restore to a specific date?**
A: Yes, if you have a backup from that date. Backups are timestamped.

**Q: Does backup slow down scraping?**
A: Minimal impact. Backup takes ~5-10 seconds for a 50MB database.

## Next Steps

Your automation is now complete with:
- ✅ Weekly scraping (Sunday 2:00 AM)
- ✅ Monthly analysis (1st of month, 3:00 AM)
- ✅ Automatic backups (after weekly scraping)
- ✅ Rolling backup history (4 weeks)

**Optional enhancements:**
- Set up Turso for cloud deployment
- Add email notifications for scraping status
- Create dashboard for monitoring backups
- Implement incremental backups

---

**Author:** BCXV Construction Analytics
**Date:** 2025-12-12
**Version:** 1.0
