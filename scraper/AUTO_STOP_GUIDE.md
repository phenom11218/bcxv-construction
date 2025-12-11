# Auto-Stop Scraping Guide

The Alberta scraper now includes **smart auto-stop** functionality that automatically stops scraping after hitting a dry spell of consecutive 404s (not found results).

## 🎯 Why This Feature?

Before, you had to manually find the endpoint for each year:
```bash
# Old way - had to know endpoint 11218
python alberta_scraper_sqlite.py 2024 1 11218
```

Now, the scraper automatically stops when it hits too many consecutive 404s:
```bash
# New way - just specify start, it finds the end automatically!
python alberta_scraper_sqlite.py 2024 1
```

## 🚀 Basic Usage

### Scrape a Year (Auto-Stop Enabled)
```bash
# Scrape 2025 from posting #1 until 50 consecutive 404s
python alberta_scraper_sqlite.py 2025 1

# Scrape 2024 starting from posting #5000
python alberta_scraper_sqlite.py 2024 5000

# Scrape 2023 from the beginning
python alberta_scraper_sqlite.py 2023 1
```

### Custom Auto-Stop Threshold
```bash
# Stop after 100 consecutive 404s (more aggressive)
python alberta_scraper_sqlite.py 2025 1 99999 100

# Stop after 25 consecutive 404s (more conservative)
python alberta_scraper_sqlite.py 2025 1 99999 25
```

### Disable Auto-Stop (Old Behavior)
```bash
# Scrape exactly 1-5000 without auto-stop
python alberta_scraper_sqlite.py 2025 1 5000 0
```

## 📊 Progress Display

The scraper now shows consecutive 404s in progress updates:

```
Progress:  100/99999 ( 0.1%) | Found:   85 | Skipped:   0 | Errors:  0 | Consecutive 404s:  3 | ETA: 162.5m
Progress:  125/99999 ( 0.1%) | Found:  105 | Skipped:   0 | Errors:  0 | Consecutive 404s:  0 | ETA: 158.3m
```

When auto-stop triggers:
```
[AUTO-STOP] Reached 50 consecutive 404s. Stopping scrape.
Last posting checked: AB-2025-11268
```

## 💡 Smart Behavior

The consecutive 404 counter **resets** when:
- ✅ A valid posting is found (new data)
- ✅ A posting is skipped (already in database)

The counter **increments** only when:
- ❌ HTTP 404 (posting doesn't exist)

The counter is **NOT affected** by:
- Network errors (temporary issues)
- HTTP errors other than 404 (server issues)

This ensures you don't stop prematurely due to temporary network hiccups!

## 📝 Command Line Arguments

```bash
python alberta_scraper_sqlite.py [year] [start_num] [end_num] [auto_stop]
```

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `year` | Yes | 2025 | Year to scrape (e.g., 2024, 2023) |
| `start_num` | Yes | 1 | Starting posting number |
| `end_num` | No | 99999 | Ending posting number (or until auto-stop) |
| `auto_stop` | No | 50 | Stop after N consecutive 404s (0 = disabled) |

## 🎯 Multi-Year Scraping Example

To scrape multiple years, just run the command for each year:

```bash
# Scrape 2025 (current year)
python alberta_scraper_sqlite.py 2025 1

# Scrape 2024 (last year)
python alberta_scraper_sqlite.py 2024 1

# Scrape 2023
python alberta_scraper_sqlite.py 2023 1

# etc...
```

Each will automatically stop when it hits 50 consecutive 404s!

## ⚙️ Recommended Settings

| Scenario | Auto-Stop Threshold | Reasoning |
|----------|-------------------|-----------|
| **Current year (2025)** | 50 (default) | Postings are sparse, gaps are normal |
| **Recent years (2023-2024)** | 50 (default) | Good balance of thoroughness |
| **Older years (pre-2023)** | 100 | More gaps expected, be more thorough |
| **Exploratory scraping** | 25 | Stop quickly to assess data availability |
| **Production scraping** | 75-100 | Be very thorough before stopping |

## 📈 Benefits

✅ **No manual endpoint hunting** - Just start from 1, let it find the end
✅ **Safe for all years** - Works for sparse and dense posting ranges
✅ **Resume-friendly** - Skipped entries reset the counter
✅ **Network resilient** - Only counts 404s, not network errors
✅ **Visible progress** - See consecutive 404s in real-time
✅ **Flexible** - Can still use manual endpoints if needed

## 🔍 Example Output

```
======================================================================
SCRAPING ALBERTA PROCUREMENT DATA
======================================================================
Year: 2025
Range: 1 to 99999 (99,999 postings)
Skip existing: True
Auto-stop after: 50 consecutive 404s
Database: ../alberta_procurement.db
======================================================================

  [AB-2025-00001] AWARD    | CNST | Highway 2 Bridge Repairs
  [AB-2025-00002] OPEN     | SERV | IT Support Services
  ...
Progress:   25/99999 ( 0.0%) | Found:   18 | Skipped:   0 | Errors:  0 | Consecutive 404s:  4 | ETA: 185.2m
  ...
  [AB-2025-11218] AWARD    | CNST | School Construction Project

[AUTO-STOP] Reached 50 consecutive 404s. Stopping scrape.
Last posting checked: AB-2025-11268

======================================================================
SCRAPING COMPLETE
======================================================================
Checked: 11,268 posting numbers
Found: 6,607 postings
Skipped (already scraped): 0
Errors: 0
Time elapsed: 187.8 minutes
======================================================================
```

## 🛠️ Troubleshooting

**Q: What if it stops too early?**
A: Increase the auto-stop threshold (e.g., 100 or 200)

**Q: What if it runs too long?**
A: Decrease the auto-stop threshold (e.g., 25)

**Q: Can I disable auto-stop?**
A: Yes! Set auto-stop to 0: `python alberta_scraper_sqlite.py 2025 1 10000 0`

**Q: Does it work with resume/skip_existing?**
A: Yes! Skipped postings reset the consecutive 404 counter, so it won't stop early when resuming.

---

**Happy Scraping! 🚀**
