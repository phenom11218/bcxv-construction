# Multi-Year Scraping Guide

**Complete guide for scraping Alberta procurement data from 2010-2025+**

---

## 📋 Quick Reference

```bash
# 1. Check current progress
python check_progress.py

# 2. Find endpoint for a year
python find_endpoint.py 2024

# 3. Scrape the year
python alberta_scraper_sqlite.py 2024 1 10284

# 4. Monitor progress
python check_progress.py
```

---

## 🎯 Step-by-Step Workflow

### Step 1: Choose Your Year

The scraper works with **any year from 2010-2025+**. Common targets:
- **2024**: Most recent complete year (~10,284 postings)
- **2023**: Previous year (~10,000 postings estimated)
- **2020-2022**: Recent historical data
- **2010-2019**: Older historical data

### Step 2: Find the Endpoint

Before scraping, determine the maximum posting number for that year.

**Option A: Start from beginning (recommended for unknown years)**
```bash
cd scraper
python find_endpoint.py 2023
```

**Option B: Test from estimated endpoint (if you have a guess)**
```bash
python find_endpoint.py 2024 10284
```

**What it does:**
- Tests posting numbers sequentially
- Stops after 50 consecutive 404s
- Reports the highest posting found
- Takes ~2-5 minutes depending on range

**Example output:**
```
ENDPOINT DETECTION FOR 2024
Testing from posting 10284...
  10284: ✓ Found - AB-2024-10284 [AWARD   ] Project Title...
  10285: ✓ Found - AB-2024-10285 [CLOSED  ] Another Project...
  10286: ✗ 404 (consecutive: 1/50)
  10287: ✗ 404 (consecutive: 2/50)
  ...
  10335: ✗ 404 (consecutive: 50/50)

✅ Highest posting found: AB-2024-10285
   Recommended scraping range: 1 to 10285
```

### Step 3: Scrape the Full Year

Once you know the endpoint, scrape the entire year.

**Option A: Single batch (for smaller years < 5000 postings)**
```bash
python alberta_scraper_sqlite.py 2023 1 8500
```

**Option B: Multiple batches (recommended for larger years > 5000)**
```bash
# Batch 1
python alberta_scraper_sqlite.py 2024 1 5000

# Batch 2
python alberta_scraper_sqlite.py 2024 5001 10285
```

**Why multiple batches?**
- Easier to monitor progress
- Can run in parallel (faster)
- Resume-friendly if interrupted
- Safer for very large ranges

**Running in background:**
The scrapers run automatically - you can close the terminal and they'll continue. Check progress anytime with:
```bash
python check_progress.py
```

### Step 4: Monitor Progress

While scraping is running, check progress anytime:

```bash
python check_progress.py
```

**Example output:**
```
ALBERTA PROCUREMENT SCRAPING PROGRESS - ALL YEARS
=====================================================================================
Year | Attempts | Found | 404s  | Range       | CNST | Status
2025 |    7,557 | 6,604 |   948 |   1- 7557   |1,596 | Complete
2024 |    5,000 | 1,250 | 3,750 |   1- 5000   |  112 | 5000/10285 (48.6%)
2023 |        0 |     0 |     0 | Not started |    0 | Not started
```

**For detailed stats on a specific year:**
```bash
python check_progress.py 2024
```

---

## 🗓️ Year-by-Year Examples

### Example 1: Scrape 2024 (Estimated ~10,284 postings)

```bash
# Step 1: Find exact endpoint
python find_endpoint.py 2024 10284

# Step 2: Scrape in batches
python alberta_scraper_sqlite.py 2024 1 5000      # Batch 1 (~2-3 hours)
python alberta_scraper_sqlite.py 2024 5001 10285  # Batch 2 (~2-3 hours)

# Step 3: Verify completion
python check_progress.py
```

**Estimated time:** 4-6 hours total

### Example 2: Scrape 2023 (Unknown endpoint)

```bash
# Step 1: Find endpoint from scratch
python find_endpoint.py 2023

# Output might show: "Highest posting found: AB-2023-09842"

# Step 2: Scrape the full year
python alberta_scraper_sqlite.py 2023 1 5000
python alberta_scraper_sqlite.py 2023 5001 9842

# Step 3: Check results
python check_progress.py 2023
```

### Example 3: Scrape 2020-2024 (Bulk historical data)

```bash
# For each year, repeat the process:

# 2024
python find_endpoint.py 2024 10000
python alberta_scraper_sqlite.py 2024 1 [endpoint]

# 2023
python find_endpoint.py 2023
python alberta_scraper_sqlite.py 2023 1 [endpoint]

# 2022
python find_endpoint.py 2022
python alberta_scraper_sqlite.py 2022 1 [endpoint]

# 2021
python find_endpoint.py 2021
python alberta_scraper_sqlite.py 2021 1 [endpoint]

# 2020
python find_endpoint.py 2020
python alberta_scraper_sqlite.py 2020 1 [endpoint]
```

**Note:** You can run multiple years in parallel by opening separate terminals!

---

## ⚙️ Advanced Configuration

### Customize Endpoint Detection

By default, `find_endpoint.py` stops after 50 consecutive 404s. You can adjust:

```bash
# More aggressive (100 consecutive 404s)
python find_endpoint.py 2024 1 100

# Quick test (20 consecutive 404s)
python find_endpoint.py 2024 10000 20

# Full syntax
python find_endpoint.py <year> <start> <max_404s> <max_tests>
```

**Parameters:**
- `year`: Year to test (required)
- `start`: Starting posting number (default: 1)
- `max_404s`: Stop after N consecutive 404s (default: 50)
- `max_tests`: Maximum postings to test (default: 200)

### Resume Interrupted Scraping

The scraper automatically resumes! If interrupted:

```bash
# Just run the same command again
python alberta_scraper_sqlite.py 2024 1 10285

# It will skip already-scraped postings
# Output: "Skipped: 2,450" (already in database)
```

### Parallel Scraping

Speed up by running multiple batches simultaneously:

**Terminal 1:**
```bash
python alberta_scraper_sqlite.py 2024 1 3000
```

**Terminal 2:**
```bash
python alberta_scraper_sqlite.py 2024 3001 6000
```

**Terminal 3:**
```bash
python alberta_scraper_sqlite.py 2024 6001 10285
```

**Terminal 4 (monitor):**
```bash
python check_progress.py
```

---

## 📊 Expected Timelines

### Single Year
- **Small year** (~5,000 postings): 2-3 hours
- **Medium year** (~10,000 postings): 4-5 hours
- **Large year** (~15,000 postings): 6-8 hours

### Multi-Year Projects
- **2020-2024** (5 years): ~1-2 weeks
- **2015-2024** (10 years): ~2-3 weeks
- **2010-2024** (15 years): ~3-4 weeks

**Note:** Times assume sequential scraping with 1-second delays. Parallel scraping is much faster!

---

## 🎯 Best Practices

### 1. Start with Recent Years
Work backwards from 2024 → 2023 → 2022, etc. Recent data is often more valuable.

### 2. Use Batches for Large Years
Split any year with >5,000 postings into multiple batches:
- Easier monitoring
- Better resume capability
- Can parallelize

### 3. Monitor Progress Regularly
Check progress every few hours:
```bash
python check_progress.py
```

### 4. Verify Completion
After scraping, confirm you got everything:
```bash
python check_progress.py 2024
```

Look for:
- ✅ Status: "Complete"
- ✅ Success rate > 95%
- ✅ Range matches expected endpoint

### 5. Database Backups
Before scraping a new year, consider backing up the database:
```bash
# Copy the database file
cp alberta_procurement.db alberta_procurement_backup_2024-12-08.db
```

---

## 🔍 Troubleshooting

### Issue: "No postings found for 2023"

**Cause:** Year may not have data, or starting point too high

**Solution:**
```bash
# Start from 1
python find_endpoint.py 2023 1

# If still no results, year may have no data
```

### Issue: "Many 404s / low success rate"

**Cause:** Normal! Alberta doesn't use every posting number sequentially

**Expected success rates:**
- 2025: ~87% (6,604 found / 7,557 checked)
- 2024: ~22% (110 found / 500 checked in range 1-500)

**Solution:** This is normal - just continue scraping

### Issue: "Scraper seems stuck"

**Cause:** Long stretches of 404s between valid postings

**Solution:**
```bash
# Check progress - it's likely still working
python check_progress.py

# Look for "Last activity: X seconds ago"
```

### Issue: "Want to scrape faster"

**Solution:**
```bash
# Run multiple batches in parallel
# Terminal 1:
python alberta_scraper_sqlite.py 2024 1 3000

# Terminal 2:
python alberta_scraper_sqlite.py 2024 3001 6000

# Terminal 3:
python alberta_scraper_sqlite.py 2024 6001 10000
```

---

## 📈 Database Growth Estimates

As you scrape more years, the database will grow:

| Years Scraped | Estimated Opportunities | Database Size |
|---------------|-------------------------|---------------|
| 2025 only     | ~6,600                 | ~440 MB       |
| 2024-2025     | ~13,000                | ~880 MB       |
| 2022-2025     | ~26,000                | ~1.8 GB       |
| 2020-2025     | ~40,000                | ~2.5 GB       |
| 2015-2025     | ~70,000                | ~4.5 GB       |
| 2010-2025     | ~100,000               | ~6-7 GB       |

**Note:** These are rough estimates. Actual size depends on number of bidders, documents, etc.

---

## 🚀 Quick Start Checklist

Ready to scrape a new year? Follow this checklist:

- [ ] Navigate to scraper directory: `cd scraper`
- [ ] Check current database status: `python check_progress.py`
- [ ] Find endpoint for target year: `python find_endpoint.py YYYY`
- [ ] Note the recommended range from output
- [ ] Start scraping: `python alberta_scraper_sqlite.py YYYY 1 [endpoint]`
- [ ] Monitor progress: `python check_progress.py`
- [ ] Verify completion when done
- [ ] Check construction project count

**Example for 2023:**
```bash
cd scraper
python check_progress.py                    # Current status
python find_endpoint.py 2023                # Find endpoint
python alberta_scraper_sqlite.py 2023 1 9842  # Scrape (if endpoint was 9842)
python check_progress.py                    # Verify completion
```

---

## 💡 Tips & Tricks

### Monitor While Scraping
Open two terminals side-by-side:
- **Left:** Scraper running
- **Right:** `python check_progress.py` (run every 5-10 minutes)

### Find Gaps in Your Data
```bash
python check_progress.py

# Look for missing years in the output
# Then scrape those years
```

### Estimate Time Remaining
```bash
python check_progress.py 2024

# Look for "ETA" and "Rate" in output
# Example: "Rate: 0.8 postings/second | ETA: 2.5 hours"
```

### Test Before Full Scrape
Test a small batch first to verify year has data:
```bash
python alberta_scraper_sqlite.py 2023 1 100

# If successful, proceed with full range
python alberta_scraper_sqlite.py 2023 101 [endpoint]
```

---

## 📞 Need Help?

**Check Progress:** `python check_progress.py`

**View This Guide:** `MULTI_YEAR_SCRAPING_GUIDE.md`

**API Documentation:** https://purchasing.alberta.ca/api/opportunity/public/{year}/{posting_number}

**Example API Call:** https://purchasing.alberta.ca/api/opportunity/public/2024/10284

---

## 📝 Summary

**Three simple steps to scrape any year:**

1. **Find endpoint:** `python find_endpoint.py 2024`
2. **Scrape data:** `python alberta_scraper_sqlite.py 2024 1 10284`
3. **Verify:** `python check_progress.py`

**The tools are 100% year-agnostic** - they work for 2024, 2010, 2030, or any year the API supports!

Happy scraping! 🎉

---

**Last Updated:** December 8, 2025
**Version:** 1.0
