"""
Progress Monitor for Alberta Procurement Scraper
Run this anytime to check scraping progress and database statistics
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "alberta_procurement.db"


def get_progress(year=None):
    """Get detailed scraping progress information."""

    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n" + "="*70)
    if year:
        print(f"SCRAPING PROGRESS FOR {year}")
    else:
        print("SCRAPING PROGRESS - ALL YEARS")
    print("="*70)

    # Get scrape log statistics
    if year:
        cursor.execute("""
            SELECT
                COUNT(*) as total_checked,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as found,
                SUM(CASE WHEN http_status_code = 404 THEN 1 ELSE 0 END) as not_found,
                SUM(CASE WHEN success = 0 AND http_status_code != 404 THEN 1 ELSE 0 END) as errors,
                MIN(posting_number) as min_num,
                MAX(posting_number) as max_num
            FROM scrape_log
            WHERE year = ?
        """, (year,))
    else:
        cursor.execute("""
            SELECT
                COUNT(*) as total_checked,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as found,
                SUM(CASE WHEN http_status_code = 404 THEN 1 ELSE 0 END) as not_found,
                SUM(CASE WHEN success = 0 AND http_status_code != 404 THEN 1 ELSE 0 END) as errors,
                MIN(posting_number) as min_num,
                MAX(posting_number) as max_num
            FROM scrape_log
        """)

    stats = cursor.fetchone()
    total_checked, found, not_found, errors, min_num, max_num = stats

    if total_checked == 0:
        print("\nNo scraping activity found yet.")
        conn.close()
        return

    # Known max for 2025
    known_max_2025 = 7557
    target_total = known_max_2025 if year == 2025 else max_num

    # Calculate percentages
    pct_complete = (total_checked / target_total * 100) if target_total > 0 else 0
    success_rate = (found / total_checked * 100) if total_checked > 0 else 0

    print(f"\nTarget Range: 1 to {target_total:,} ({target_total:,} total posting numbers)")
    print(f"\nCurrent Status:")
    print(f"  Checked:        {total_checked:,} / {target_total:,}  ({pct_complete:.1f}%)")
    print(f"  Found:          {found:,} postings")
    print(f"  Not Found:      {not_found:,} (404s)")
    print(f"  Errors:         {errors:,}")
    print(f"  Success Rate:   {success_rate:.1f}%")

    # Progress bar
    bar_width = 50
    filled = int(bar_width * pct_complete / 100)
    bar = '#' * filled + '-' * (bar_width - filled)
    print(f"\n  Progress: [{bar}] {pct_complete:.1f}%")

    # Get most recent scraping activity
    if year:
        cursor.execute("""
            SELECT scraped_at, posting_number, reference_number
            FROM scrape_log
            WHERE year = ? AND success = 1
            ORDER BY scraped_at DESC
            LIMIT 1
        """, (year,))
    else:
        cursor.execute("""
            SELECT scraped_at, posting_number, reference_number
            FROM scrape_log
            WHERE success = 1
            ORDER BY scraped_at DESC
            LIMIT 1
        """)

    recent = cursor.fetchone()
    if recent:
        last_scraped_at, last_num, last_ref = recent
        print(f"\nLast Scrape Activity:")
        print(f"  Time:     {last_scraped_at}")
        print(f"  Posting:  {last_ref}")

        # Calculate ETA
        if total_checked > 0 and pct_complete < 100:
            remaining = target_total - total_checked

            # Get first scrape time to calculate rate
            if year:
                cursor.execute("""
                    SELECT MIN(scraped_at), MAX(scraped_at), COUNT(*)
                    FROM scrape_log
                    WHERE year = ? AND success = 1
                """, (year,))
            else:
                cursor.execute("""
                    SELECT MIN(scraped_at), MAX(scraped_at), COUNT(*)
                    FROM scrape_log
                    WHERE success = 1
                """)

            time_stats = cursor.fetchone()
            if time_stats and time_stats[0] and time_stats[1]:
                first_time = datetime.fromisoformat(time_stats[0])
                last_time = datetime.fromisoformat(time_stats[1])
                count = time_stats[2]

                elapsed = (last_time - first_time).total_seconds()
                if elapsed > 0 and count > 0:
                    rate = count / elapsed  # postings per second
                    eta_seconds = remaining / rate if rate > 0 else 0
                    eta_minutes = eta_seconds / 60

                    print(f"\nTime Estimates:")
                    print(f"  Elapsed:    {elapsed/60:.1f} minutes")
                    print(f"  Rate:       {rate*60:.1f} postings/minute")
                    print(f"  Remaining:  {remaining:,} postings to check")
                    print(f"  ETA:        {eta_minutes:.1f} minutes")

    # Get category breakdown from opportunities table
    print(f"\nCategory Breakdown:")
    if year:
        cursor.execute("""
            SELECT category_code, COUNT(*) as count
            FROM opportunities
            WHERE year = ?
            GROUP BY category_code
            ORDER BY count DESC
        """, (year,))
    else:
        cursor.execute("""
            SELECT category_code, COUNT(*) as count
            FROM opportunities
            GROUP BY category_code
            ORDER BY count DESC
        """)

    categories = cursor.fetchall()
    for cat, count in categories[:10]:
        cat_name = cat or 'NULL'
        print(f"  {cat_name:15} {count:6,} postings")

    # Get status breakdown
    print(f"\nStatus Breakdown:")
    if year:
        cursor.execute("""
            SELECT status_code, COUNT(*) as count
            FROM opportunities
            WHERE year = ?
            GROUP BY status_code
            ORDER BY count DESC
        """, (year,))
    else:
        cursor.execute("""
            SELECT status_code, COUNT(*) as count
            FROM opportunities
            GROUP BY status_code
            ORDER BY count DESC
        """)

    statuses = cursor.fetchall()
    for status, count in statuses:
        status_name = status or 'NULL'
        print(f"  {status_name:15} {count:6,} postings")

    # Show recent postings found
    print(f"\nRecent Postings Found:")
    if year:
        cursor.execute("""
            SELECT reference_number, short_title, status_code, category_code
            FROM opportunities
            WHERE year = ?
            ORDER BY posting_number DESC
            LIMIT 5
        """, (year,))
    else:
        cursor.execute("""
            SELECT reference_number, short_title, status_code, category_code
            FROM opportunities
            ORDER BY posting_number DESC
            LIMIT 5
        """)

    recent_postings = cursor.fetchall()
    for ref, title, status, cat in recent_postings:
        title_short = title[:50] if title else "No title"
        print(f"  {ref}: [{status:8}] [{cat:4}] {title_short}")

    print("="*70 + "\n")

    conn.close()


def get_database_summary():
    """Show overall database statistics."""

    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n" + "="*70)
    print("DATABASE SUMMARY")
    print("="*70)

    tables = [
        ('opportunities', 'Total postings'),
        ('bidders', 'Bidder submissions'),
        ('interested_suppliers', 'Interested suppliers'),
        ('awards', 'Contract awards'),
        ('documents', 'Attached documents'),
        ('contacts', 'Contact records'),
        ('raw_data', 'Raw JSON backups'),
    ]

    print("\nTable Statistics:")
    for table, description in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table:25} {count:8,} rows - {description}")

    # Year breakdown
    cursor.execute("""
        SELECT year, COUNT(*) as count
        FROM opportunities
        GROUP BY year
        ORDER BY year DESC
    """)
    years = cursor.fetchall()

    if years:
        print(f"\nPostings by Year:")
        for year, count in years:
            print(f"  {year}: {count:,} postings")

    print("="*70 + "\n")

    conn.close()


if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) > 1:
        try:
            year = int(sys.argv[1])
            get_progress(year)
        except ValueError:
            if sys.argv[1].lower() == 'summary':
                get_database_summary()
            else:
                print("Usage: python check_progress.py [year|summary]")
                print("Example: python check_progress.py 2025")
                print("Example: python check_progress.py summary")
    else:
        # Default: show progress for 2025 (most recent)
        get_progress(2025)

    # Always show database summary at the end
    get_database_summary()
