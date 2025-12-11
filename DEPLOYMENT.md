# 🚀 Deployment Guide: Alberta Construction Analytics

**Complete guide to deploying your analytics app to the cloud for free!**

---

## 📋 Overview

This guide will help you deploy the Alberta Construction Analytics app to **Streamlit Community Cloud** using **Turso** for cloud database hosting - all completely **FREE**.

### What You'll Need

- GitHub account (you already have this ✓)
- Turso account (free signup)
- 30-45 minutes

### Architecture

```
┌─────────────────┐         ┌─────────────────┐
│  Streamlit      │ ◄─────► │  Turso Cloud    │
│  Community      │         │  SQLite DB      │
│  Cloud (App)    │         │  (663 MB)       │
└─────────────────┘         └─────────────────┘
        ▲
        │
        │ (Public URL)
        │
        ▼
   👥 Users
```

---

## Part 1: Setup Turso Cloud Database (15 mins)

### Step 1.1: Sign Up for Turso

1. Go to [https://turso.tech/](https://turso.tech/)
2. Click "Get Started" or "Sign Up"
3. Sign up with GitHub (easiest) or email
4. Verify your email if required

### Step 1.2: Install Turso CLI

**For Windows (PowerShell):**
```powershell
powershell -c "irm https://raw.githubusercontent.com/tursodatabase/turso-cli/main/install.ps1 | iex"
```

**For macOS/Linux:**
```bash
curl -sSfL https://get.turso.tech/install.sh | bash
```

**Verify installation:**
```bash
turso --version
```

### Step 1.3: Login to Turso

```bash
turso auth login
```

This will open a browser window. Click "Authorize" to connect the CLI.

### Step 1.4: Create Your Cloud Database

```bash
turso db create alberta-construction
```

**Expected output:**
```
Created group default at [location] in 12 seconds.
Created database alberta-construction at group default in 3 seconds.
Start an interactive SQL shell with: turso db shell alberta-construction
```

### Step 1.5: Upload Your Local Database

**Important:** Make sure your `alberta_procurement.db` exists and is up-to-date.

**Check database size:**
```bash
ls -lh alberta_procurement.db
# Should show ~663 MB
```

**Upload to Turso:**
```bash
# Open Turso shell
turso db shell alberta-construction

# In the Turso shell, restore from your local file
.restore alberta_procurement.db

# Exit shell
.quit
```

**Alternative upload method (if .restore doesn't work):**
```bash
# Dump local database to SQL
sqlite3 alberta_procurement.db .dump > dump.sql

# Import to Turso
turso db shell alberta-construction < dump.sql
```

### Step 1.6: Get Your Turso Credentials

**Get Database URL:**
```bash
turso db show alberta-construction
```

Copy the **URL** (looks like: `libsql://alberta-construction-YOUR-USERNAME.turso.io`)

**Create Auth Token:**
```bash
turso db tokens create alberta-construction
```

Copy the **token** (long string starting with `eyJ...`)

⚠️ **IMPORTANT:** Save these credentials somewhere safe! You'll need them in Part 2.

### Step 1.7: Verify Upload (Optional)

```bash
turso db shell alberta-construction

# Run test query
SELECT COUNT(*) FROM opportunities;
# Should return 6,607 (or your total project count)

# Check construction projects
SELECT COUNT(*) FROM opportunities WHERE category_code = 'CNST';
# Should return ~1,596

.quit
```

✅ **Part 1 Complete!** Your database is now in the cloud.

---

## Part 2: Deploy App to Streamlit Cloud (20 mins)

### Step 2.1: Prepare Local Files

**1. Configure secrets locally (for testing):**

```bash
cd analytics-app
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

**2. Edit `.streamlit/secrets.toml`:**

```toml
[database]
type = "turso"  # Change from "local" to "turso"

[turso]
database_url = "libsql://alberta-construction-YOUR-USERNAME.turso.io"  # Your URL from Step 1.6
auth_token = "eyJ..."  # Your token from Step 1.6
```

**3. Test locally (IMPORTANT):**

```bash
# From analytics-app/ directory
streamlit run app.py
```

Navigate to "Similar Projects" and try searching for a project. If it works, you're ready!

### Step 2.2: Push to GitHub

**1. Commit all deployment files:**

```bash
cd ..  # Back to project root
git add .
git commit -m "Deploy: Add Turso cloud database support

- Added Turso database adapter
- Added secrets template
- Updated requirements.txt with libsql-client
- Ready for Streamlit Cloud deployment
"
git push origin feature/2025-12-08-phase-2-explorer
```

**2. Merge to main branch (if needed):**

```bash
git checkout main
git merge feature/2025-12-08-phase-2-explorer
git push origin main
```

### Step 2.3: Deploy on Streamlit Cloud

**1. Go to Streamlit Community Cloud:**
- Visit [https://share.streamlit.io/](https://share.streamlit.io/)
- Sign in with GitHub

**2. Create New App:**
- Click "New app"
- Repository: `phenom11218/bcxv-construction`
- Branch: `main` (or your feature branch)
- Main file path: `analytics-app/app.py`
- App URL: Choose a custom URL like `alberta-construction-analytics`

**3. Configure Secrets:**
- Click "Advanced settings"
- In the "Secrets" section, paste your Turso configuration:

```toml
[database]
type = "turso"

[turso]
database_url = "libsql://alberta-construction-YOUR-USERNAME.turso.io"
auth_token = "eyJ..."
```

⚠️ **Replace with your ACTUAL credentials from Step 1.6!**

**4. Deploy!**
- Click "Deploy!"
- Wait 2-5 minutes for initial deployment
- Watch the logs to ensure no errors

### Step 2.4: Test Your Deployed App

Once deployment completes (look for green checkmark ✓):

1. Click on the app URL (e.g., `https://alberta-construction-analytics.streamlit.app`)
2. Wait for the app to load
3. Check the sidebar - should show "✓ Connected" and project counts
4. Test "Similar Projects" page:
   - Try: `AB-2025-05281`
   - Try: `https://purchasing.alberta.ca/posting/AB-2024-10281`
5. Verify bid recommendations appear

✅ **Part 2 Complete!** Your app is now live and public!

---

## Part 3: Sharing & Maintenance

### Share Your App

**Public URL:**
```
https://your-app-name.streamlit.app
```

Share this with:
- Colleagues
- Clients
- Portfolio/resume
- LinkedIn

### Update Your Data

**When you scrape new data:**

```bash
# 1. Update local database
cd scraper
python alberta_scraper_sqlite.py

# 2. Upload to Turso
turso db shell alberta-construction
.restore ../alberta_procurement.db
.quit

# 3. Restart Streamlit app
# Go to Streamlit Cloud → Your App → Click "Reboot"
```

### Monitor Usage

**Turso Dashboard:**
- Visit [https://turso.tech/app](https://turso.tech/app)
- View database stats, queries, storage

**Streamlit Analytics:**
- Streamlit Cloud dashboard shows:
  - Visitor count
  - Page views
  - Error logs

---

## Troubleshooting

### Problem: "Database connection failed" on deployed app

**Solution:**
1. Check secrets are configured correctly in Streamlit Cloud
2. Verify Turso credentials are valid:
   ```bash
   turso db show alberta-construction
   turso db tokens create alberta-construction
   ```
3. Check Turso database has data:
   ```bash
   turso db shell alberta-construction
   SELECT COUNT(*) FROM opportunities;
   ```

### Problem: App is very slow

**Solutions:**
- Turso free tier should handle read-heavy apps fine
- If hitting limits, check Turso dashboard for usage
- Consider upgrading Turso plan ($30/month) if needed
- Add caching with `@st.cache_data` decorator

### Problem: "libsql-client not found"

**Solution:**
- Check `requirements.txt` has `libsql-client>=0.3.0`
- Reboot app in Streamlit Cloud
- Check deployment logs for Python errors

### Problem: Can't upload database to Turso

**Solution 1 - Split and upload:**
```bash
# Export schema
sqlite3 alberta_procurement.db .schema > schema.sql

# Import schema to Turso
turso db shell alberta-construction < schema.sql

# Export data in chunks (opportunities table)
sqlite3 alberta_procurement.db "SELECT * FROM opportunities" > opportunities.csv
# Import CSV to Turso (use Turso dashboard or API)
```

**Solution 2 - Use Turso API:**
```python
# Python script to upload data via Turso API
# (Contact Turso support for guidance)
```

### Problem: Free tier limits exceeded

**Current Limits (as of 2025):**
- Storage: 9 GB (you're using 663 MB ✓)
- Databases: 500 (you're using 1 ✓)
- Row reads: 1 billion/month
- Row writes: 25 million/month

**If exceeded:**
- Upgrade to paid plan ($30/mo)
- Optimize queries with caching
- Limit public access

---

## Cost Breakdown

| Service | Free Tier | Your Usage | Cost |
|---------|-----------|------------|------|
| **Turso** | 9 GB, 1B reads/mo | 663 MB, ~100K reads/mo | **$0** |
| **Streamlit Cloud** | Unlimited public apps | 1 app | **$0** |
| **GitHub** | Unlimited repos | 1 repo | **$0** |
| **Total** | | | **$0/month** 🎉 |

---

## Advanced: Auto-Update Database

### Option A: GitHub Actions (Automated)

Create `.github/workflows/update-db.yml`:

```yaml
name: Update Turso Database

on:
  schedule:
    - cron: '0 2 * * 0'  # Weekly on Sunday at 2 AM
  workflow_dispatch:  # Manual trigger

jobs:
  update-database:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r scraper/requirements.txt
          curl -sSfL https://get.turso.tech/install.sh | bash

      - name: Scrape latest data
        run: |
          cd scraper
          python alberta_scraper_sqlite.py

      - name: Upload to Turso
        env:
          TURSO_DB: alberta-construction
        run: |
          turso auth login --token ${{ secrets.TURSO_TOKEN }}
          turso db shell $TURSO_DB ".restore alberta_procurement.db"
```

### Option B: Local Cron (Manual)

**Windows (Task Scheduler):**
1. Create `update_and_deploy.bat`:
```bat
cd C:\path\to\scraper
python alberta_scraper_sqlite.py
turso db shell alberta-construction .restore ..\alberta_procurement.db
```

2. Task Scheduler → Create Basic Task → Weekly

**macOS/Linux (crontab):**
```bash
0 2 * * 0 /path/to/update_and_deploy.sh
```

---

## Next Steps

✅ **Your app is now live!**

**Recommended next steps:**
1. Add custom domain (Streamlit Cloud settings)
2. Set up error monitoring (Sentry, etc.)
3. Create documentation page in app
4. Add Google Analytics tracking
5. Create demo video for LinkedIn/portfolio

**Share your success:**
- GitHub README: Add "Live Demo" badge
- LinkedIn: Share your project
- Twitter/X: Tag @streamlit

---

## Support

**Need help?**
- Turso Docs: [https://docs.turso.tech/](https://docs.turso.tech/)
- Streamlit Docs: [https://docs.streamlit.io/](https://docs.streamlit.io/)
- GitHub Issues: [https://github.com/phenom11218/bcxv-construction/issues](https://github.com/phenom11218/bcxv-construction/issues)

**Resources:**
- Turso Discord: [https://discord.gg/turso](https://discord.gg/turso)
- Streamlit Forum: [https://discuss.streamlit.io/](https://discuss.streamlit.io/)

---

**Version:** 1.0
**Last Updated:** December 10, 2025
**Tested With:** Turso CLI 0.92+, Streamlit 1.28+
