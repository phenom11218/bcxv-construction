# Data Preservation Policy

## 🛡️ Core Principle: Never Delete Historical Data

This database serves as a **permanent historical archive** of Alberta procurement postings, not just a mirror of the current API state.

### The Problem

Alberta's procurement API **retroactively removes postings** after some time. Without preservation logic, we would lose valuable historical data when re-scraping.

### The Solution

**All historical data is PERMANENTLY preserved**, even when:
- Postings are removed from the API (404 errors)
- Postings are archived by the government
- API endpoints become unavailable

---

## 📋 How It Works

### When Re-scraping Existing Postings

```python
# Scenario: Posting AB-2023-12345 exists in our database
# We try to re-scrape it to check for status updates

if API returns 200 (success):
    ✓ Update with new data (status changes, awards, etc.)

if API returns 404 (not found):
    ✓ PRESERVE existing data (do NOT delete!)
    ✓ Mark as is_archived = 1
    ✓ Record archived_at timestamp
    ✓ Log in scrape_log: "Preserved historical data - posting removed from API"

if API returns 500 or network error:
    ✓ Keep existing data unchanged
    ✓ Log error for retry later
```

### Database Schema

**Archived Tracking Columns:**

```sql
ALTER TABLE opportunities ADD COLUMN is_archived INTEGER DEFAULT 0;
ALTER TABLE opportunities ADD COLUMN archived_at TEXT;
```

- `is_archived = 0`: Currently available in API (default)
- `is_archived = 1`: Removed from API but preserved in our archive
- `archived_at`: Timestamp when first detected as unavailable

---

## 🔍 Querying Archived Data

### Show All Postings (Including Archived)

```sql
SELECT * FROM opportunities;
-- Returns ALL postings ever scraped
```

### Show Only Active Postings

```sql
SELECT * FROM opportunities
WHERE is_archived = 0 OR is_archived IS NULL;
-- Only postings still in API
```

### Show Only Archived Postings

```sql
SELECT * FROM opportunities
WHERE is_archived = 1;
-- Postings removed from API
```

### Statistics

```sql
SELECT
    COUNT(*) as total,
    SUM(CASE WHEN is_archived = 1 THEN 1 ELSE 0 END) as archived,
    SUM(CASE WHEN is_archived = 0 OR is_archived IS NULL THEN 1 ELSE 0 END) as active
FROM opportunities;
```

---

## 📊 What Data Is Preserved

When a posting is archived, we preserve:

✅ **All opportunity data**
- Reference number, title, description
- Status code (at time of archival)
- Category, region, solicitation type
- Posting dates, close dates

✅ **Financial data**
- Estimated value
- Actual value (if awarded)
- Award amounts

✅ **Award information**
- Winner name and supplier ID
- Award date
- Trade agreements

✅ **Bidder lists**
- All companies that bid
- Bid amounts
- Winner designation

✅ **Document metadata**
- File names, types, sizes
- Upload timestamps
- Amendment numbers

✅ **Contact information**
- Project contacts
- Email, phone numbers
- Addresses

✅ **Raw JSON**
- Complete API response at time of scraping
- Stored in `raw_data` table

**NOTHING is ever deleted!**

---

## 🚀 Setup & Usage

### 1. Run Migration (One-Time)

Add archived tracking columns:

```bash
python scraper/database_migration_archived.py
```

This adds `is_archived` and `archived_at` columns and marks any existing 404s.

### 2. Update Existing Scripts

The smart re-scraping system (`update_active_postings.py`) automatically:
- Preserves data on 404 errors
- Marks postings as archived
- Logs preservation events

**No code changes needed** - it's built-in!

### 3. Verify Preservation

Check that archived postings are being tracked:

```sql
SELECT
    reference_number,
    short_title,
    status_code,
    is_archived,
    archived_at
FROM opportunities
WHERE is_archived = 1
ORDER BY archived_at DESC
LIMIT 20;
```

---

## 📈 Analytics Impact

### Historical Trends

With permanent data preservation, you can analyze:

**Removed Postings Analysis:**
```sql
-- Why are postings being removed?
SELECT
    status_code,
    COUNT(*) as archived_count
FROM opportunities
WHERE is_archived = 1
GROUP BY status_code
ORDER BY archived_count DESC;
```

**Archival Timeline:**
```sql
-- When do postings typically get archived?
SELECT
    DATE(archived_at) as archive_date,
    COUNT(*) as count
FROM opportunities
WHERE is_archived = 1
GROUP BY DATE(archived_at)
ORDER BY archive_date DESC;
```

**Data Retention:**
```sql
-- How much data have we preserved?
SELECT
    year,
    COUNT(*) as total_postings,
    SUM(CASE WHEN is_archived = 1 THEN 1 ELSE 0 END) as archived_postings,
    ROUND(SUM(CASE WHEN is_archived = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as pct_archived
FROM opportunities
GROUP BY year
ORDER BY year DESC;
```

### Bid Intelligence

Archived postings still valuable for:
- Historical pricing analysis
- Competitor tracking (who bid, who won)
- Project type trends
- Regional analysis
- Winning bid patterns

**Example:**
```sql
-- Analyze all construction bids (even archived projects)
SELECT
    AVG(actual_value) as avg_award,
    COUNT(*) as project_count
FROM opportunities
WHERE category_code = 'CNST'
  AND status_code = 'AWARD'
-- Includes archived postings! More complete data
```

---

## ⚠️ Important Notes

### 1. Never Manually Delete Data

**DON'T do this:**
```sql
-- ❌ BAD - Deletes historical data!
DELETE FROM opportunities WHERE is_archived = 1;
```

**Instead:**
```sql
-- ✓ GOOD - Query only active if needed
SELECT * FROM opportunities WHERE is_archived = 0;
```

### 2. Storage Considerations

Archived postings remain in the database forever, increasing size over time.

**Current database:** ~695MB with 13,445 postings

**Estimated growth:**
- Assume 10% of postings get archived per year
- ~1,300 archived postings/year
- ~50MB additional storage/year

**Conclusion:** Not a problem! Even after 10 years:
- ~13,000 archived postings
- ~500MB additional storage
- Total: ~1.2GB (well within limits)

### 3. Streamlit Dashboard

Update dashboard queries to filter archived postings if needed:

```python
# Show only active opportunities
df = db.execute_query("""
    SELECT * FROM opportunities
    WHERE (is_archived = 0 OR is_archived IS NULL)
      AND category_code = 'CNST'
""")
```

Or show all with indicator:

```python
# Show all with archived indicator
df = db.execute_query("""
    SELECT
        reference_number,
        short_title,
        status_code,
        actual_value,
        CASE WHEN is_archived = 1 THEN '📦 Archived' ELSE '✓ Active' END as availability
    FROM opportunities
""")
```

---

## 🔐 Data Integrity Guarantees

### What We Guarantee

✅ **Permanence**: Data once scraped is NEVER deleted

✅ **Completeness**: All fields preserved when archived

✅ **Auditability**: Scrape log tracks every attempt

✅ **Transparency**: `is_archived` flag clearly marks status

✅ **Reversibility**: If posting reappears in API, gets un-archived

### What We Track

**Scrape Log:**
```sql
SELECT * FROM scrape_log
WHERE reference_number = 'AB-2023-12345'
ORDER BY scraped_at DESC;
```

Shows complete history:
- Initial scrape (200 OK)
- Successful updates (200 OK)
- Archival detection (404, data preserved)
- Any errors (500, network issues)

---

## 📚 Examples

### Example 1: Posting Lifecycle

```
2024-01-15: AB-2024-00123 scraped (OPEN)
            → Stored in database

2024-02-10: Re-scraped (CLOSED)
            → Status updated to CLOSED

2024-03-05: Re-scraped (AWARD)
            → Status updated to AWARD
            → Award data populated

2024-06-20: Re-scraped (404 - Not Found)
            → is_archived = 1
            → archived_at = 2024-06-20
            → All data PRESERVED
            → Status remains AWARD (last known state)
```

### Example 2: Query Patterns

**Get all awarded construction projects (including archived):**
```sql
SELECT
    reference_number,
    short_title,
    actual_value,
    awarded_on,
    is_archived
FROM opportunities
WHERE category_code = 'CNST'
  AND status_code = 'AWARD'
ORDER BY awarded_on DESC;
```

**Get only current (non-archived) open postings:**
```sql
SELECT
    reference_number,
    short_title,
    close_date
FROM opportunities
WHERE status_code = 'OPEN'
  AND (is_archived = 0 OR is_archived IS NULL)
ORDER BY close_date ASC;
```

---

## 🎯 Summary

**Bottom Line:** Once data enters our database, it stays forever.

- ✅ API removals don't affect our archive
- ✅ Historical analysis remains accurate
- ✅ Trend data stays complete
- ✅ No data loss from government archival policies

**We are building a PERMANENT historical record, not a temporary mirror.**

---

**Last Updated:** 2025-12-11
**Policy Version:** 1.0
