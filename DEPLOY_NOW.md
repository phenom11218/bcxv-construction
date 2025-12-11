# 🚀 DEPLOY NOW - Quick Deployment Guide

**Ready to deploy in 15 minutes!**

---

## ✅ Pre-Deployment Checklist

- [x] ✅ Code pushed to GitHub
- [x] ✅ Turso CLI installed
- [x] ✅ Turso account created
- [x] ✅ Database created: `alberta-procurement`
- [ ] ⏳ **Verify database import completed**
- [ ] ⏳ **Get Turso credentials**
- [ ] ⏳ **Deploy to Streamlit Cloud**

---

## 📋 STEP 1: Verify Turso Database (2 minutes)

**In your WSL terminal:**

```bash
# Check if import completed
turso db list
# You should see: alberta-procurement

# Test the data
turso db shell alberta-procurement "SELECT COUNT(*) FROM opportunities;"
# Should show: 6607
```

✅ **If you see 6,607** → Database is ready! Continue to Step 2.

❌ **If you get an error** → The import might still be running or failed.
- Check if import is still running in another WSL window
- If it failed, see [TURSO_UPLOAD_GUIDE.md](TURSO_UPLOAD_GUIDE.md) for troubleshooting

---

## 🔑 STEP 2: Get Your Turso Credentials (1 minute)

**In WSL, run these commands:**

```bash
# Get Database URL
turso db show alberta-procurement
```

**Copy the URL** - it looks like:
```
libsql://alberta-procurement-XXXX-YYYY.turso.io
```

**Then get Auth Token:**

```bash
# Create authentication token
turso db tokens create alberta-procurement
```

**Copy the token** - it's a long string starting with `eyJ...`

**Save both somewhere safe!** You'll need them in the next step.

---

## 🌐 STEP 3: Deploy to Streamlit Cloud (10 minutes)

### 3.1: Sign In

1. Go to: **https://share.streamlit.io/**
2. Click **"Sign in with GitHub"**
3. Authorize Streamlit to access your GitHub

### 3.2: Create New App

1. Click **"New app"** (big blue button)
2. Fill in the form:

   **Repository:**
   ```
   phenom11218/bcxv-construction
   ```

   **Branch:**
   ```
   feature/2025-12-08-phase-2-explorer
   ```

   (Or use `main` if you've merged)

   **Main file path:**
   ```
   analytics-app/app.py
   ```

   **App URL** (choose custom name):
   ```
   alberta-procurement-analytics
   ```
   (Or any name you want)

### 3.3: Configure Secrets

1. Click **"Advanced settings"** (before deploying)
2. In the **"Secrets"** text box, paste this:

   ```toml
   [database]
   type = "turso"

   [turso]
   database_url = "PASTE_YOUR_DATABASE_URL_HERE"
   auth_token = "PASTE_YOUR_AUTH_TOKEN_HERE"
   ```

3. **REPLACE** the placeholder values with:
   - Your actual database URL from Step 2
   - Your actual auth token from Step 2

### 3.4: Deploy!

1. Click **"Deploy!"**
2. Watch the logs as it builds (2-5 minutes)
3. Wait for the green checkmark ✓

---

## ✅ STEP 4: Test Your Live App (5 minutes)

Once deployment completes, your app will be live at:
```
https://YOUR-APP-NAME.streamlit.app
```

**Test these features:**

### 4.1: Check Database Connection
- Look at the sidebar
- Should show "✓ Connected"
- Should display project counts

### 4.2: Test Explorer Page
- Click **"📊 Explorer"** in sidebar
- Should load projects
- Try filtering by value or region

### 4.3: Test Similar Projects
- Click **"🔍 Similar Projects"** in sidebar
- Try entering: `AB-2025-05281`
- Should show similar projects and bid recommendations

### 4.4: Test Live API Fetching
- In Similar Projects, try: `https://purchasing.alberta.ca/posting/AB-2024-10281`
- Should fetch the project and show bid recommendations

---

## 🎉 STEP 5: Share Your App!

Your app is now live! Share it:

- **Public URL:** `https://your-app-name.streamlit.app`
- LinkedIn: Post about your project
- Resume/Portfolio: Add the live demo link
- Email: Share with clients/colleagues
- Twitter/X: Tag @streamlit

---

## 🐛 Troubleshooting

### Problem: "Database connection failed"

**Solution:**
1. Check secrets are correct in Streamlit Cloud settings
2. Go to your app → Settings → Secrets
3. Verify database_url and auth_token are correct
4. Reboot the app

### Problem: "Import errors" or "Module not found"

**Solution:**
1. Check that `analytics-app/requirements.txt` has all dependencies
2. Especially verify: `libsql-client>=0.3.0`
3. Reboot the app in Streamlit Cloud

### Problem: App is slow or times out

**Solution:**
1. This might happen on first load (cold start)
2. Refresh the page
3. Turso free tier should be fast enough for normal use

### Problem: Features not showing data

**Solution:**
1. Clear Streamlit cache: Go to app menu → "Rerun"
2. Check database has data:
   ```bash
   turso db shell alberta-procurement "SELECT COUNT(*) FROM opportunities;"
   ```
3. Check app logs in Streamlit Cloud dashboard

---

## 📊 What You've Deployed

### Features Live on Your App:

✅ **Historical Project Explorer**
- Browse 1,596 construction projects
- Filter by value, region, keywords, dates
- View detailed bid breakdowns
- Export to CSV/JSON

✅ **Similar Projects Finder**
- Enter any project reference or URL
- ML-powered similarity matching
- Bid recommendations with confidence levels
- Competition analysis

✅ **Live API Integration**
- Fetch ANY Alberta project in real-time
- Works even if not in your database
- Automatic fallback to database

✅ **Competitive Intelligence**
- Who bids on similar projects
- Win rates and patterns
- Average bid amounts
- Historical pricing data

---

## 💰 Your Stack (All Free!)

| Service | Cost | What It Does |
|---------|------|--------------|
| **Turso Cloud** | $0/mo | Hosts your 663MB database |
| **Streamlit Cloud** | $0/mo | Hosts your web app |
| **GitHub** | $0/mo | Version control & deployment |
| **Total** | **$0/month** 🎉 | Professional deployment! |

---

## 📚 Need Help?

- **Full Guide:** [DEPLOYMENT.md](DEPLOYMENT.md)
- **Troubleshooting:** [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)
- **Turso Issues:** [TURSO_UPLOAD_GUIDE.md](TURSO_UPLOAD_GUIDE.md)
- **Project Docs:** [README.md](README.md)

---

## 🎯 Quick Command Reference

### Turso Commands (In WSL)

```bash
# List databases
turso db list

# Show database info
turso db show alberta-procurement

# Query database
turso db shell alberta-procurement "SELECT COUNT(*) FROM opportunities;"

# Create new token
turso db tokens create alberta-procurement

# Check who you're logged in as
turso auth whoami
```

### Git Commands (In Git Bash)

```bash
# Check status
git status

# Check current branch
git branch

# View recent commits
git log --oneline -5

# Pull latest changes
git pull origin feature/2025-12-08-phase-2-explorer
```

---

## ⏱️ Time Estimate

| Step | Time |
|------|------|
| Verify Turso database | 2 min |
| Get credentials | 1 min |
| Deploy to Streamlit | 10 min |
| Test deployment | 5 min |
| **Total** | **~18 minutes** |

---

## 🚀 Ready? Let's Deploy!

**Start with Step 1:** Verify your Turso database import completed successfully.

**In WSL, run:**
```bash
turso db shell alberta-procurement "SELECT COUNT(*) FROM opportunities;"
```

**Then come back here and follow Steps 2-5!**

---

**Good luck! 🎉 You're about to have a live, professional web app!**

---

**Last Updated:** December 10, 2025
