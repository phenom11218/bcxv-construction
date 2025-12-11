"""
Award Timing Analysis Tool
===========================
Analyzes the time between posting close and award announcement.
Helps understand how long to keep checking CLOSED postings for awards.

Usage:
    python analyze_award_timing.py [--year YEAR] [--category CATEGORY]

Examples:
    # Analyze all years
    python analyze_award_timing.py

    # Analyze specific year
    python analyze_award_timing.py --year 2024

    # Analyze construction projects only
    python analyze_award_timing.py --category CNST
"""

import sqlite3
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

DB_PATH = Path(__file__).parent.parent / "alberta_procurement.db"


def parse_datetime(dt_str: str) -> datetime:
    """Parse ISO datetime string, handling timezone."""
    if not dt_str:
        return None
    # Remove 'Z' suffix if present
    dt_str = dt_str.replace('Z', '')
    try:
        return datetime.fromisoformat(dt_str)
    except:
        return None


def analyze_award_timing(conn, year: int = None, category: str = None):
    """Analyze time between close and award."""
    cursor = conn.cursor()

    # Build query
    where_clauses = [
        "status_code = 'AWARD'",
        "close_date IS NOT NULL",
        "awarded_on IS NOT NULL"
    ]

    if year:
        where_clauses.append(f"year = {year}")

    if category:
        where_clauses.append(f"category_code = '{category}'")

    where_clause = " AND ".join(where_clauses)

    query = f"""
        SELECT
            reference_number,
            close_date,
            awarded_on,
            category_code,
            actual_value
        FROM opportunities
        WHERE {where_clause}
    """

    cursor.execute(query)
    results = cursor.fetchall()

    if not results:
        print("No awarded projects found matching criteria")
        return

    # Calculate days to award
    timing_data = []
    for ref, close_date, awarded_on, cat, value in results:
        close_dt = parse_datetime(close_date)
        award_dt = parse_datetime(awarded_on)

        if close_dt and award_dt:
            days = (award_dt - close_dt).days
            timing_data.append((ref, days, cat, value))

    if not timing_data:
        print("No valid date data found")
        return

    # Sort by days
    timing_data.sort(key=lambda x: x[1])

    # Statistics
    days_list = [x[1] for x in timing_data]
    count = len(days_list)
    min_days = min(days_list)
    max_days = max(days_list)
    avg_days = sum(days_list) / count
    median_days = days_list[count // 2]

    # Percentiles
    p25 = days_list[count // 4]
    p75 = days_list[3 * count // 4]
    p90 = days_list[int(0.9 * count)]
    p95 = days_list[int(0.95 * count)]
    p99 = days_list[int(0.99 * count)]

    # Distribution
    within_30 = sum(1 for d in days_list if d <= 30)
    within_60 = sum(1 for d in days_list if d <= 60)
    within_90 = sum(1 for d in days_list if d <= 90)
    within_120 = sum(1 for d in days_list if d <= 120)

    # Print results
    print("\n" + "="*70)
    print("AWARD TIMING ANALYSIS")
    print("="*70)

    if year:
        print(f"Year: {year}")
    if category:
        print(f"Category: {category}")

    print(f"\nTotal awarded projects analyzed: {count:,}")
    print()

    print("TIMING STATISTICS (days from close to award):")
    print("-" * 70)
    print(f"{'Minimum:':<20} {min_days:>6} days")
    print(f"{'Maximum:':<20} {max_days:>6} days")
    print(f"{'Average:':<20} {avg_days:>6.1f} days")
    print(f"{'Median:':<20} {median_days:>6} days")
    print()

    print("PERCENTILES:")
    print("-" * 70)
    print(f"{'25th percentile:':<20} {p25:>6} days")
    print(f"{'50th percentile:':<20} {median_days:>6} days (median)")
    print(f"{'75th percentile:':<20} {p75:>6} days")
    print(f"{'90th percentile:':<20} {p90:>6} days")
    print(f"{'95th percentile:':<20} {p95:>6} days")
    print(f"{'99th percentile:':<20} {p99:>6} days")
    print()

    print("DISTRIBUTION:")
    print("-" * 70)
    print(f"{'Within 30 days:':<20} {within_30:>6,} ({within_30/count*100:>5.1f}%)")
    print(f"{'Within 60 days:':<20} {within_60:>6,} ({within_60/count*100:>5.1f}%)")
    print(f"{'Within 90 days:':<20} {within_90:>6,} ({within_90/count*100:>5.1f}%)")
    print(f"{'Within 120 days:':<20} {within_120:>6,} ({within_120/count*100:>5.1f}%)")
    print()

    # Extreme cases
    print("FASTEST AWARDS (Top 10):")
    print("-" * 70)
    print(f"{'Reference':<20} {'Days':<10} {'Category':<10} {'Value':>15}")
    print("-" * 70)
    for ref, days, cat, value in timing_data[:10]:
        value_str = f"${value:,.0f}" if value else "N/A"
        print(f"{ref:<20} {days:<10} {cat or 'N/A':<10} {value_str:>15}")

    print()
    print("SLOWEST AWARDS (Top 10):")
    print("-" * 70)
    print(f"{'Reference':<20} {'Days':<10} {'Category':<10} {'Value':>15}")
    print("-" * 70)
    for ref, days, cat, value in timing_data[-10:]:
        value_str = f"${value:,.0f}" if value else "N/A"
        print(f"{ref:<20} {days:<10} {cat or 'N/A':<10} {value_str:>15}")

    print()
    print("="*70)
    print("INSIGHTS FOR RE-SCRAPING STRATEGY")
    print("="*70)
    print()
    print(f"• {within_30/count*100:.1f}% of awards happen within 30 days of closing")
    print(f"• {within_60/count*100:.1f}% of awards happen within 60 days of closing")
    print(f"• {within_90/count*100:.1f}% of awards happen within 90 days of closing")
    print(f"• {(count-within_90)/count*100:.1f}% of awards take LONGER than 90 days")
    print()
    print(f"RECOMMENDATION:")
    print(f"  - Check CLOSED postings weekly for first 60 days")
    print(f"  - Check bi-weekly for days 60-90")
    print(f"  - Check monthly for days 90+")
    print(f"  - Keep checking until awarded (no age limit!) to capture {(count-within_90)/count*100:.1f}% late awards")
    print()


def analyze_pending_awards(conn):
    """Analyze current pending awards."""
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            reference_number,
            status_code,
            close_date,
            CAST(julianday('now') - julianday(close_date) AS INTEGER) as days_waiting
        FROM opportunities
        WHERE status_code IN ('CLOSED', 'EVALUATION')
          AND awarded_on IS NULL
          AND close_date IS NOT NULL
        ORDER BY days_waiting DESC
    """)

    results = cursor.fetchall()

    if not results:
        print("\nNo pending awards found")
        return

    print("\n" + "="*70)
    print("CURRENTLY PENDING AWARDS")
    print("="*70)
    print(f"\nTotal: {len(results):,} postings waiting for award")
    print()

    # Distribution
    within_30 = sum(1 for r in results if r[3] <= 30)
    within_60 = sum(1 for r in results if r[3] <= 60)
    within_90 = sum(1 for r in results if r[3] <= 90)
    over_90 = len(results) - within_90

    print("AGE DISTRIBUTION:")
    print("-" * 70)
    print(f"{'<= 30 days:':<20} {within_30:>6,}")
    print(f"{'31-60 days:':<20} {within_60-within_30:>6,}")
    print(f"{'61-90 days:':<20} {within_90-within_60:>6,}")
    print(f"{'> 90 days:':<20} {over_90:>6,}")
    print()

    # Oldest pending
    print("OLDEST PENDING AWARDS (waiting longest):")
    print("-" * 70)
    print(f"{'Reference':<20} {'Status':<12} {'Close Date':<20} {'Days Waiting':>12}")
    print("-" * 70)
    for ref, status, close_date, days in results[:20]:
        close_str = close_date[:10] if close_date else "N/A"
        print(f"{ref:<20} {status:<12} {close_str:<20} {days:>12}")

    print()
    print("These postings should be prioritized for re-scraping!")
    print()


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(description="Analyze award timing")
    parser.add_argument('--year', type=int, help="Filter by year")
    parser.add_argument('--category', type=str, help="Filter by category code (e.g., CNST)")
    args = parser.parse_args()

    if not DB_PATH.exists():
        print(f"✗ Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)

    try:
        analyze_award_timing(conn, args.year, args.category)
        analyze_pending_awards(conn)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        conn.close()


if __name__ == "__main__":
    main()
