"""
New Postings Discovery Script
==============================
Automatically discovers and scrapes new postings for specified year(s).

Instead of manually finding endpoints, this uses auto-stop to find new postings.
Starts from the highest known posting number + 1 for each year.

Usage:
    python scrape_new_postings.py [year] [--auto-stop N]

Examples:
    # Scrape new 2025 postings (auto-stop after 50 consecutive 404s)
    python scrape_new_postings.py 2025

    # Scrape multiple years
    python scrape_new_postings.py 2024 2025

    # Custom auto-stop threshold
    python scrape_new_postings.py 2025 --auto-stop 100

    # Scrape current year (default)
    python scrape_new_postings.py
"""

import sqlite3
import argparse
from datetime import datetime
from pathlib import Path
import sys

# Import from alberta_scraper_sqlite
sys.path.append(str(Path(__file__).parent))
from alberta_scraper_sqlite import scrape_range, get_scrape_status

DB_PATH = Path(__file__).parent.parent / "alberta_procurement.db"


def get_highest_posting_number(year: int) -> int:
    """Get the highest posting number we have for a given year."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT MAX(posting_number)
        FROM opportunities
        WHERE year = ?
    """, (year,))

    result = cursor.fetchone()
    conn.close()

    return result[0] if result[0] is not None else 0


def get_posting_stats(year: int) -> dict:
    """Get statistics for postings in a given year."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    stats = {}

    # Total count
    cursor.execute("SELECT COUNT(*) FROM opportunities WHERE year = ?", (year,))
    stats['total'] = cursor.fetchone()[0]

    # Status breakdown
    cursor.execute("""
        SELECT status_code, COUNT(*) as count
        FROM opportunities
        WHERE year = ?
        GROUP BY status_code
        ORDER BY count DESC
    """, (year,))
    stats['by_status'] = dict(cursor.fetchall())

    # Date range
    cursor.execute("""
        SELECT MIN(post_date), MAX(post_date)
        FROM opportunities
        WHERE year = ?
    """, (year,))
    dates = cursor.fetchone()
    stats['date_range'] = dates

    conn.close()
    return stats


def scrape_year(year: int, auto_stop: int = 50):
    """Scrape new postings for a specific year."""
    print("\n" + "="*70)
    print(f"NEW POSTINGS DISCOVERY: {year}")
    print("="*70)
    print()

    # Get current status
    highest = get_highest_posting_number(year)
    stats = get_posting_stats(year)

    print(f"Current status for {year}:")
    print(f"  Highest posting number: {highest:,}")
    print(f"  Total postings: {stats['total']:,}")

    if stats['by_status']:
        print(f"  Status breakdown:")
        for status, count in list(stats['by_status'].items())[:5]:
            print(f"    {status:15} {count:,}")

    print()

    # Determine start number
    start_num = highest + 1

    print(f"Starting discovery from: {start_num:,}")
    print(f"Auto-stop after: {auto_stop} consecutive 404s")
    print()

    # Run scraper with auto-stop
    scrape_range(
        year=year,
        start_num=start_num,
        end_num=99999,  # Large number, rely on auto-stop
        skip_existing=True,
        auto_stop_after=auto_stop
    )

    # Show updated status
    print("\n" + "="*70)
    print(f"DISCOVERY COMPLETE FOR {year}")
    print("="*70)

    new_highest = get_highest_posting_number(year)
    new_stats = get_posting_stats(year)
    new_found = new_stats['total'] - stats['total']

    print(f"\nNew postings found: {new_found:,}")
    print(f"New highest posting number: {new_highest:,}")
    print(f"Total postings for {year}: {new_stats['total']:,}")
    print()


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(
        description="Discover and scrape new postings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape current year
  python scrape_new_postings.py

  # Scrape specific year
  python scrape_new_postings.py 2024

  # Scrape multiple years
  python scrape_new_postings.py 2023 2024 2025

  # Custom auto-stop threshold
  python scrape_new_postings.py 2025 --auto-stop 100
        """
    )

    parser.add_argument(
        'years',
        nargs='*',
        type=int,
        help="Years to scrape (default: current year)"
    )

    parser.add_argument(
        '--auto-stop',
        type=int,
        default=50,
        help="Stop after N consecutive 404s (default: 50)"
    )

    args = parser.parse_args()

    # Default to current year if none specified
    years = args.years if args.years else [datetime.now().year]

    print("\n" + "="*70)
    print("ALBERTA PROCUREMENT - NEW POSTINGS DISCOVERY")
    print("="*70)
    print(f"Database: {DB_PATH}")
    print(f"Years to check: {', '.join(map(str, years))}")
    print(f"Auto-stop threshold: {args.auto_stop} consecutive 404s")
    print()

    # Scrape each year
    for year in sorted(years):
        try:
            scrape_year(year, args.auto_stop)
        except KeyboardInterrupt:
            print(f"\n\n[INTERRUPTED] Scraping interrupted for {year}. Progress saved.")
            break
        except Exception as e:
            print(f"\n[ERROR] Error scraping {year}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # Final summary
    print("\n" + "="*70)
    print("ALL YEARS COMPLETE")
    print("="*70)
    print()

    for year in sorted(years):
        stats = get_posting_stats(year)
        highest = get_highest_posting_number(year)
        print(f"{year}: {stats['total']:,} postings (highest: AB-{year}-{highest:05d})")

    print()
    print("Next steps:")
    print("  1. Run update_active_postings.py to update status of existing postings")
    print("  2. Schedule this script to run weekly for continuous discovery")
    print("  3. Check analyze_award_timing.py for award statistics")
    print()


if __name__ == "__main__":
    main()
