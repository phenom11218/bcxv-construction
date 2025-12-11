# Multi-Year Scraping Quick Start

**Scrape any year (2010-2025+) in 3 simple steps**

---

## Step 1: Find Endpoint

```bash
python find_endpoint.py 2024
```

**What it does:** Finds the maximum posting number for that year
**Time:** ~2-5 minutes
**Stops after:** 50 consecutive 404s

---

## Step 2: Scrape Data

```bash
python alberta_scraper_sqlite.py 2024 1 10284
```

**What it does:** Scrapes all postings for that year
**Time:** ~4-6 hours for ~10K postings
**Rate:** 1-second delay between requests (respectful)

**For large years, use batches:**
```bash
python alberta_scraper_sqlite.py 2024 1 5000
python alberta_scraper_sqlite.py 2024 5001 10284
```

---

## Step 3: Verify Completion

```bash
python check_progress.py
```

**What it shows:**
- All years in database
- Progress for each year
- Construction project counts
- Last activity

**For detailed stats:**
```bash
python check_progress.py 2024
```

---

## Common Workflows

### Scrape 2024
```bash
python find_endpoint.py 2024 10284
python alberta_scraper_sqlite.py 2024 1 [endpoint]
python check_progress.py
```

### Scrape 2023 (unknown endpoint)
```bash
python find_endpoint.py 2023
python alberta_scraper_sqlite.py 2023 1 [endpoint]
python check_progress.py
```

### Monitor Active Scraping
```bash
# Run this while scraper is running
python check_progress.py

# Check every 5-10 minutes to see progress
```

---

## Tool Reference

| Tool | Purpose | Example |
|------|---------|---------|
| `find_endpoint.py` | Find max posting for a year | `python find_endpoint.py 2024` |
| `alberta_scraper_sqlite.py` | Scrape posting data | `python alberta_scraper_sqlite.py 2024 1 10284` |
| `check_progress.py` | Monitor all years | `python check_progress.py` |
| `check_progress.py <year>` | Detailed stats for year | `python check_progress.py 2024` |

---

## Tips

✅ **Always find endpoint first** - don't guess!
✅ **Use batches for years >5000** - easier to monitor
✅ **Check progress regularly** - every 5-10 minutes
✅ **Resume is automatic** - if interrupted, just re-run same command
✅ **Parallel scraping works** - open multiple terminals for different batches

---

## Need More Help?

📖 **Complete Guide:** [../MULTI_YEAR_SCRAPING_GUIDE.md](../MULTI_YEAR_SCRAPING_GUIDE.md)
📊 **Current Progress:** `python check_progress.py`
🔍 **Find Endpoint:** `python find_endpoint.py --help`

---

**Happy Scraping! 🎉**
