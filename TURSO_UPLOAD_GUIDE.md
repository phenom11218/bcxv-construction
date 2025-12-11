# 📤 Uploading Your Database to Turso - Troubleshooting Guide

## Problem: sqlite3 Not Found in WSL

The upload command failed because `sqlite3` is not installed in your WSL environment.

---

## Solution: Install sqlite3 in WSL

**In your WSL terminal, run:**

```bash
# Update package list
sudo apt update

# Install sqlite3
sudo apt install sqlite3 -y

# Verify installation
sqlite3 --version
```

---

## Alternative Method: Upload via Turso Dashboard (If CLI Fails)

If the CLI upload continues to fail, you can use Turso's web dashboard:

### Option 1: Convert to SQL Dump and Upload Manually

**Step 1: Create SQL dump file (in WSL):**

```bash
# Navigate to your database
cd /mnt/c/Users/ramih/llm_projects/scraper/"Alberta Purchasing Construction"

# Create a SQL dump file (this might take a few minutes)
sqlite3 alberta_procurement.db .dump > alberta_dump.sql

# Check the file size
ls -lh alberta_dump.sql
```

**Step 2: Upload via Turso CLI:**

```bash
# Upload the dump file
turso db shell alberta-construction < alberta_dump.sql
```

---

## Alternative: Use Turso's Database Import Feature

### Option 2: Split Database into Smaller Chunks

Large databases can sometimes fail. Let's try uploading table by table:

```bash
# Get list of tables
sqlite3 alberta_procurement.db ".tables"

# Export each table separately
sqlite3 alberta_procurement.db ".dump opportunities" > opportunities.sql
sqlite3 alberta_procurement.db ".dump bidders" > bidders.sql
# ... etc for each table

# Upload each table
turso db shell alberta-construction < opportunities.sql
turso db shell alberta-construction < bidders.sql
```

---

## Recommended Approach for You

**Run these commands in order:**

```bash
# 1. Install sqlite3
sudo apt update && sudo apt install sqlite3 -y

# 2. Navigate to database directory
cd /mnt/c/Users/ramih/llm_projects/scraper/"Alberta Purchasing Construction"

# 3. Test sqlite3 works
sqlite3 alberta_procurement.db "SELECT COUNT(*) FROM opportunities;"

# 4. Upload to Turso (THIS WILL TAKE 5-15 MINUTES)
sqlite3 alberta_procurement.db .dump | turso db shell alberta-construction

# 5. Verify upload worked
turso db shell alberta-construction "SELECT COUNT(*) FROM opportunities;"
```

---

## If Upload Still Fails: Quick Deploy Alternative

If Turso upload continues to have issues, we have a backup plan:

### Plan B: Deploy with Downloadable Database

1. Create a compressed version of your database
2. Upload to GitHub Releases or cloud storage
3. App downloads database on first run
4. Deploy to Streamlit Cloud immediately

This is less ideal but gets you deployed faster.

---

## Progress Check

After installing sqlite3 and running the upload, you should see:

```
BEGIN TRANSACTION;
CREATE TABLE opportunities (...);
INSERT INTO opportunities VALUES (...);
...
(lots of SQL statements scrolling by)
...
COMMIT;
```

This will take **5-15 minutes**. Be patient and don't interrupt!

---

**Next Steps:**
1. Install sqlite3 in WSL
2. Try the upload again
3. Let me know if you hit any more errors

I'm here to help! 🚀
