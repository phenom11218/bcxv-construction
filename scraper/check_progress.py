"""
Alberta Procurement Scraper - Universal Progress Monitor
Automatically detects and displays progress for ALL years (2010-2099+)

Usage:
    python check_progress.py              # Show all years
    python check_progress.py 2024         # Show specific year
    python check_progress.py summary      # Database summary only

Features:
    - Year-agnostic: works with ANY year in database
    - Auto-detection: no need to specify years
    - Real-time progress tracking
    - Construction project counts
    - Database statistics
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# Database path (one level up from scraper/)
DB_PATH = Path(__file__).parent.parent / "alberta_procurement.db"


def get_file_size(file_path):
    """Get human-readable file size."""
    if not file_path.exists():
        return "N/A"

    size_bytes = file_path.stat().st_size
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def check_all_years():
    """Check scraping progress for ALL years in database (year-agnostic)."""

    if not DB_PATH.exists():
        print(f"\n[ERROR] Database not found: {DB_PATH}")
        print("Have you run the scraper yet?")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n" + "="*85)
    print("ALBERTA PROCUREMENT SCRAPING PROGRESS - ALL YEARS")
    print("="*85)

    # Get progress for each year (completely year-agnostic query)
    cursor.execute('''
        SELECT
            year,
            COUNT(*) as total_attempts,
            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
            SUM(CASE WHEN http_status_code = 404 THEN 1 ELSE 0 END) as not_found,
            MIN(posting_number) as min_posting,
            MAX(posting_number) as max_posting
        FROM scrape_log
        GROUP BY year
        ORDER BY year DESC
    ''')

    year_data = cursor.fetchall()

    if not year_data:
        print("\n[INFO] No scraping data found yet.")
        print("Start scraping with: python alberta_scraper_sqlite.py 2025 1 500")
        conn.close()
        return

    # Get construction counts for each year (year-agnostic)
    cursor.execute('''
        SELECT year, COUNT(*) as construction_count
        FROM opportunities
        WHERE category_code = 'CNST'
        GROUP BY year
    ''')

    construction_counts = {row[0]: row[1] for row in cursor.fetchall()}

    # Display table header
    print(f"\n{'Year':>4} | {'Attempts':>9} | {'Found':>8} | {'404s':>7} | {'Range':>13} | {'CNST':>5} | {'Status':<20}")
    print("-" * 85)

    total_attempts = 0
    total_found = 0
    total_404s = 0
    total_construction = 0

    for row in year_data:
        year, attempts, successful, not_found, min_num, max_num = row
        construction = construction_counts.get(year, 0)

        # Determine status/progress (estimates based on known data)
        if year == 2025:
            expected = 7557
            if max_num >= expected:
                status = "Complete"
            else:
                pct = (max_num / expected) * 100
                status = f"{max_num}/{expected} ({pct:.1f}%)"
        elif year == 2024:
            expected = 10284
            if max_num >= expected:
                status = "Complete"
            else:
                pct = (max_num / expected) * 100
                status = f"{max_num}/{expected} ({pct:.1f}%)"
        else:
            # For other years, show range without assumptions
            if max_num >= 10000:
                status = "Range complete"
            else:
                status = f"In progress..."

        range_str = f"{min_num:5}-{max_num:5}"

        print(f"{year:4} | {attempts:9,} | {successful:8,} | {not_found:7,} | {range_str} | {construction:5,} | {status:<20}")

        total_attempts += attempts
        total_found += successful
        total_404s += not_found
        total_construction += construction

    # Summary statistics
    print("-" * 85)
    print(f"{'TOTAL':>4} | {total_attempts:9,} | {total_found:8,} | {total_404s:7,} | {'':<13} | {total_construction:5,} |")
    print("=" * 85)

    # Database info
    db_size = get_file_size(DB_PATH)
    num_years = len(year_data)

    print(f"\nDatabase Statistics:")
    print(f"   Location: {DB_PATH.name}")
    print(f"   Size: {db_size}")
    print(f"   Years tracked: {num_years} ({', '.join(str(r[0]) for r in year_data)})")
    print(f"   Total opportunities: {total_found:,}")
    print(f"   Construction projects: {total_construction:,} ({total_construction/total_found*100:.1f}% of total)")

    # Recent activity
    cursor.execute('''
        SELECT MAX(scraped_at) as last_scrape
        FROM scrape_log
    ''')

    last_scrape = cursor.fetchone()[0]
    if last_scrape:
        try:
            last_dt = datetime.fromisoformat(last_scrape)
            time_ago = datetime.now() - last_dt

            if time_ago.total_seconds() < 60:
                time_str = f"{int(time_ago.total_seconds())} seconds ago"
            elif time_ago.total_seconds() < 3600:
                time_str = f"{int(time_ago.total_seconds() / 60)} minutes ago"
            elif time_ago.total_seconds() < 86400:
                time_str = f"{int(time_ago.total_seconds() / 3600)} hours ago"
            else:
                time_str = f"{int(time_ago.total_seconds() / 86400)} days ago"

            print(f"   Last activity: {time_str}")
        except:
            print(f"   Last activity: {last_scrape}")

    # Legend
    print(f"\nLegend:")
    print(f"   Attempts  = Total posting numbers checked")
    print(f"   Found     = Successfully scraped postings")
    print(f"   404s      = Posting numbers that don't exist")
    print(f"   Range     = Min-Max posting numbers attempted")
    print(f"   CNST      = Construction projects (category_code='CNST')")

    print(f"\nUsage:")
    print(f"   python check_progress.py           # Show all years (this view)")
    print(f"   python check_progress.py 2024      # Show detailed stats for 2024")
    print(f"   python check_progress.py summary   # Show database summary")

    print("=" * 85 + "\n")

    conn.close()


def check_single_year(year):
    """Check detailed progress for a specific year."""

    if not DB_PATH.exists():
        print(f"\n[ERROR] Database not found: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n" + "="*70)
    print(f"SCRAPING PROGRESS FOR {year}")
    print("="*70)

    # Get scrape log statistics for this year
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

    stats = cursor.fetchone()
    total_checked, found, not_found, errors, min_num, max_num = stats

    if total_checked == 0:
        print(f"\n[INFO] No scraping activity found for {year}.")
        print(f"Start scraping with: python alberta_scraper_sqlite.py {year} 1 10000")
        conn.close()
        return

    # Estimate target (can be adjusted)
    known_targets = {
        2025: 7557,
        2024: 10284,
    }
    target_total = known_targets.get(year, max_num)  # Use max_num as fallback

    # Calculate percentages
    pct_complete = (max_num / target_total * 100) if target_total > 0 else 0
    success_rate = (found / total_checked * 100) if total_checked > 0 else 0

    print(f"\nRange Attempted: {min_num} to {max_num} ({max_num - min_num + 1:,} posting numbers)")
    if year in known_targets:
        print(f"Expected Total:  1 to {target_total:,} ({target_total:,} posting numbers)")

    print(f"\nCurrent Status:")
    print(f"  Checked:        {total_checked:,}")
    print(f"  Found:          {found:,} postings")
    print(f"  Not Found:      {not_found:,} (404s)")
    print(f"  Errors:         {errors:,}")
    print(f"  Success Rate:   {success_rate:.1f}%")

    if year in known_targets:
        print(f"  Progress:       {pct_complete:.1f}% complete")

    # Progress bar
    if year in known_targets:
        bar_width = 50
        filled = int(bar_width * pct_complete / 100)
        bar = '#' * filled + '-' * (bar_width - filled)
        print(f"\n  [{bar}] {pct_complete:.1f}%")

    # Category breakdown
    cursor.execute("""
        SELECT category_code, COUNT(*) as count
        FROM opportunities
        WHERE year = ?
        GROUP BY category_code
        ORDER BY count DESC
        LIMIT 10
    """, (year,))

    categories = cursor.fetchall()
    if categories:
        print(f"\nTop Categories:")
        for cat, count in categories:
            cat_name = cat or 'NULL'
            pct = (count / found * 100) if found > 0 else 0
            print(f"  {cat_name:15} {count:6,} postings ({pct:5.1f}%)")

    # Status breakdown
    cursor.execute("""
        SELECT status_code, COUNT(*) as count
        FROM opportunities
        WHERE year = ?
        GROUP BY status_code
        ORDER BY count DESC
    """, (year,))

    statuses = cursor.fetchall()
    if statuses:
        print(f"\nStatus Breakdown:")
        for status, count in statuses:
            status_name = status or 'NULL'
            pct = (count / found * 100) if found > 0 else 0
            print(f"  {status_name:15} {count:6,} postings ({pct:5.1f}%)")

    print("="*70 + "\n")

    conn.close()


def get_database_summary():
    """Show overall database statistics (year-agnostic)."""

    if not DB_PATH.exists():
        print(f"\n[ERROR] Database not found: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n" + "="*70)
    print("DATABASE SUMMARY")
    print("="*70)

    tables = [
        ('raw_data', 'Raw JSON backups'),
        ('opportunities', 'Normalized postings'),
        ('bidders', 'Bidder submissions'),
        ('interested_suppliers', 'Interested suppliers'),
        ('awards', 'Contract awards'),
        ('documents', 'Attached documents'),
        ('contacts', 'Contact records'),
        ('scrape_log', 'Scraping attempts'),
    ]

    print("\nTable Statistics:")
    for table, description in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table:25} {count:8,} rows - {description}")
        except:
            print(f"  {table:25}     N/A rows - {description}")

    # Year breakdown (completely year-agnostic)
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

    # Database file info
    db_size = get_file_size(DB_PATH)
    print(f"\nDatabase File:")
    print(f"  Path: {DB_PATH}")
    print(f"  Size: {db_size}")

    print("="*70 + "\n")

    conn.close()


if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()

        if arg == 'summary':
            get_database_summary()
        else:
            try:
                year = int(sys.argv[1])
                check_single_year(year)
            except ValueError:
                print("\n[ERROR] Invalid argument. Usage:")
                print("  python check_progress.py           # Show all years")
                print("  python check_progress.py 2024      # Show specific year")
                print("  python check_progress.py summary   # Database summary\n")
    else:
        # Default: show ALL years (year-agnostic)
        check_all_years()
