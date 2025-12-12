"""
Smart Re-scraping for Active Postings
======================================
Multi-tier system to capture status transitions and delayed awards.

This script re-scrapes postings based on their likelihood of change:
- Tier 1: OPEN postings (high chance of status change)
- Tier 2: Recently CLOSED postings (awaiting award)
- Tier 3: Pending awards (CLOSED/EVALUATION without award data, no age limit!)
- Tier 4: Recent awards (verification)

Usage:
    python update_active_postings.py [--tier TIER] [--dry-run] [--limit N]

Examples:
    # Update all tiers
    python update_active_postings.py

    # Only update pending awards (Tier 3)
    python update_active_postings.py --tier 3

    # Dry run to see what would be updated
    python update_active_postings.py --dry-run

    # Limit to first 100 postings (for testing)
    python update_active_postings.py --limit 100
"""

import requests
import sqlite3
import json
import time
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

# Import from alberta_scraper_sqlite
import sys
sys.path.append(str(Path(__file__).parent))
from alberta_scraper_sqlite import (
    fetch_opportunity,
    insert_full_posting,
    session,
    DELAY_BETWEEN_REQUESTS
)

DB_PATH = Path(__file__).parent.parent / "alberta_procurement.db"


def get_tier1_postings(conn) -> List[Tuple[str, int, int]]:
    """
    Tier 1: Get all OPEN postings.
    These have high chance of status change.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT reference_number, year, posting_number
        FROM opportunities
        WHERE status_code = 'OPEN'
        ORDER BY year DESC, posting_number DESC
    """)
    return cursor.fetchall()


def get_tier2_postings(conn, days=60) -> List[Tuple[str, int, int]]:
    """
    Tier 2: Get recently CLOSED postings (last N days).
    These are likely awaiting award announcement.
    """
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT reference_number, year, posting_number
        FROM opportunities
        WHERE status_code = 'CLOSED'
          AND close_date >= date('now', '-{days} days')
        ORDER BY close_date DESC
    """)
    return cursor.fetchall()


def get_tier3_postings(conn) -> List[Tuple[str, int, int, int]]:
    """
    Tier 3: Get ALL CLOSED/EVALUATION postings missing award data.
    NO AGE LIMIT - we keep checking until they get awarded!
    Returns (ref, year, posting_num, days_since_close) with most recent first.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            reference_number,
            year,
            posting_number,
            CAST(julianday('now') - julianday(close_date) AS INTEGER) as days_since_close
        FROM opportunities
        WHERE status_code IN ('CLOSED', 'EVALUATION')
          AND awarded_on IS NULL
          AND close_date IS NOT NULL
        ORDER BY close_date DESC
    """)
    return cursor.fetchall()


def get_tier4_postings(conn, days=90) -> List[Tuple[str, int, int]]:
    """
    Tier 4: Get recently awarded postings for verification.
    Check that award data is complete.
    """
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT reference_number, year, posting_number
        FROM opportunities
        WHERE status_code = 'AWARD'
          AND awarded_on >= date('now', '-{days} days')
          AND scrape_count = 1
        ORDER BY awarded_on DESC
    """)
    return cursor.fetchall()


def should_rescrape_tier3(days_since_close: int) -> bool:
    """
    Exponential backoff for Tier 3 (pending awards).
    Returns True if posting should be re-scraped based on age.
    """
    # This is called daily, so we use modulo to determine if today is a scrape day
    # In practice, you'd check last_scraped_at instead

    if days_since_close < 30:
        return True  # Weekly (always scrape if checked)
    elif days_since_close < 90:
        return days_since_close % 2 == 0  # Bi-weekly
    else:
        return days_since_close % 7 == 0  # Monthly


def track_status_change(conn, ref_num: str, old_status: str, new_status: str,
                       close_date: str = None, awarded_on: str = None):
    """Record status change in status_history table."""
    cursor = conn.cursor()

    # Calculate days in previous status
    cursor.execute("""
        SELECT changed_at FROM status_history
        WHERE reference_number = ?
        ORDER BY changed_at DESC LIMIT 1
    """, (ref_num,))
    result = cursor.fetchone()

    days_in_previous = None
    if result:
        last_change = datetime.fromisoformat(result[0])
        days_in_previous = (datetime.now() - last_change).days

    cursor.execute("""
        INSERT INTO status_history
        (reference_number, old_status, new_status, changed_at, days_in_previous_status, close_date, awarded_on)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (ref_num, old_status, new_status, datetime.now().isoformat(),
          days_in_previous, close_date, awarded_on))


def update_posting(conn, year: int, posting_num: int, dry_run: bool = False) -> Dict[str, Any]:
    """
    Re-scrape and update a single posting.
    Returns dict with update status and any changes detected.
    """
    result = {
        'success': False,
        'status_changed': False,
        'award_added': False,
        'error': None,
        'old_status': None,
        'new_status': None
    }

    # Fetch current data from database
    cursor = conn.cursor()
    cursor.execute("""
        SELECT reference_number, status_code, awarded_on
        FROM opportunities
        WHERE year = ? AND posting_number = ?
    """, (year, posting_num))
    current = cursor.fetchone()

    if not current:
        result['error'] = "Not found in database"
        return result

    ref_num, old_status, old_award = current

    # Fetch from API
    data, status_code = fetch_opportunity(year, posting_num)

    if not data:
        # CRITICAL: Preserve historical data if API returns 404
        # The posting may have been archived/removed from API, but we keep our record
        if status_code == 404:
            result['error'] = "API_ARCHIVED"
            result['success'] = True  # Mark as successful - we preserved the data

            if not dry_run:
                # Update tracking info but DON'T delete data
                # Mark as archived if columns exist (graceful degradation)
                try:
                    cursor.execute("""
                        UPDATE opportunities
                        SET last_scraped_at = ?,
                            scrape_count = scrape_count + 1,
                            is_archived = 1,
                            archived_at = COALESCE(archived_at, ?)
                        WHERE year = ? AND posting_number = ?
                    """, (datetime.now().isoformat(), datetime.now().isoformat(), year, posting_num))
                except sqlite3.OperationalError:
                    # Columns don't exist yet - update without archived flags
                    cursor.execute("""
                        UPDATE opportunities
                        SET last_scraped_at = ?,
                            scrape_count = scrape_count + 1
                        WHERE year = ? AND posting_number = ?
                    """, (datetime.now().isoformat(), year, posting_num))

                # Add a note in scrape_log
                cursor.execute("""
                    INSERT INTO scrape_log
                    (year, posting_number, reference_number, success, error_message, http_status_code, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (year, posting_num, ref_num, True,
                      "Preserved historical data - posting removed from API", 404,
                      datetime.now().isoformat()))

                conn.commit()

            return result
        else:
            # Other errors (500, network issues, etc.) - return error
            result['error'] = f"HTTP {status_code}"
            return result

    # Extract new status
    new_status = data['opportunity'].get('statusCode')
    new_award = data['opportunity'].get('awardedOnUtc')

    # Detect changes
    status_changed = (new_status != old_status)
    award_added = (not old_award and new_award)

    result['old_status'] = old_status
    result['new_status'] = new_status
    result['status_changed'] = status_changed
    result['award_added'] = award_added

    if dry_run:
        result['success'] = True
        result['dry_run'] = True
        return result

    # Update database
    try:
        insert_full_posting(conn, year, posting_num, data)

        # Update tracking columns
        cursor.execute("""
            UPDATE opportunities
            SET last_scraped_at = ?,
                scrape_count = scrape_count + 1,
                previous_status = ?
            WHERE year = ? AND posting_number = ?
        """, (datetime.now().isoformat(), old_status, year, posting_num))

        # Track status change
        if status_changed:
            track_status_change(conn, ref_num, old_status, new_status,
                              data['opportunity'].get('closeDateTime'),
                              new_award)

        conn.commit()
        result['success'] = True

    except Exception as e:
        result['error'] = str(e)
        conn.rollback()

    return result


def run_tier(conn, tier_num: int, postings: List[Tuple], tier_name: str,
            dry_run: bool = False, limit: Optional[int] = None) -> Dict[str, int]:
    """
    Run updates for a specific tier.
    Returns statistics.
    """
    print(f"\n{'='*70}")
    print(f"TIER {tier_num}: {tier_name}")
    print(f"{'='*70}")

    if limit:
        postings = postings[:limit]

    total = len(postings)
    print(f"Postings to check: {total:,}")

    if total == 0:
        print("  No postings to update")
        return {'total': 0, 'updated': 0, 'status_changed': 0, 'award_added': 0, 'errors': 0}

    if dry_run:
        print("  [DRY RUN MODE - No changes will be made]")

    print()

    stats = {
        'total': total,
        'updated': 0,
        'status_changed': 0,
        'award_added': 0,
        'errors': 0,
        'skipped': 0
    }

    start_time = time.time()

    for i, posting_data in enumerate(postings, 1):
        # Handle both 3-tuple and 4-tuple (tier 3 has days_since_close)
        if len(posting_data) == 4:
            ref_num, year, posting_num, days_since_close = posting_data
            # Apply exponential backoff for tier 3
            if not should_rescrape_tier3(days_since_close):
                stats['skipped'] += 1
                continue
        else:
            ref_num, year, posting_num = posting_data

        # Progress update every 25 postings
        if i % 25 == 0:
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            remaining = (total - i) / rate if rate > 0 else 0
            print(f"Progress: {i:4}/{total} ({i/total*100:5.1f}%) | "
                  f"Updated: {stats['updated']:4} | Status changes: {stats['status_changed']:3} | "
                  f"Awards added: {stats['award_added']:3} | Errors: {stats['errors']:2} | "
                  f"ETA: {remaining/60:.1f}m")

        # Update posting
        result = update_posting(conn, year, posting_num, dry_run)

        if result['success']:
            stats['updated'] += 1

            if result['status_changed']:
                stats['status_changed'] += 1
                print(f"  [{ref_num}] Status change: {result['old_status']} -> {result['new_status']}")

            if result['award_added']:
                stats['award_added'] += 1
                print(f"  [{ref_num}] Award added!")

        else:
            stats['errors'] += 1
            if result['error'] != 'HTTP 404':  # Don't spam 404s
                print(f"  [{ref_num}] Error: {result['error']}")

        # Rate limiting
        time.sleep(DELAY_BETWEEN_REQUESTS)

    elapsed = time.time() - start_time
    print(f"\n{'='*70}")
    print(f"TIER {tier_num} COMPLETE")
    print(f"{'='*70}")
    print(f"Time elapsed: {elapsed/60:.1f} minutes")
    print(f"Total checked: {total:,}")
    print(f"Successfully updated: {stats['updated']:,}")
    print(f"Status changes detected: {stats['status_changed']:,}")
    print(f"Awards added: {stats['award_added']:,}")
    print(f"Errors: {stats['errors']:,}")
    if stats['skipped'] > 0:
        print(f"Skipped (exponential backoff): {stats['skipped']:,}")
    print()

    return stats


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(description="Smart re-scraping for active postings")
    parser.add_argument('--tier', type=int, choices=[1,2,3,4], help="Only run specific tier")
    parser.add_argument('--dry-run', action='store_true', help="Don't make changes, just show what would be updated")
    parser.add_argument('--limit', type=int, help="Limit number of postings per tier (for testing)")
    args = parser.parse_args()

    print("\n" + "="*70)
    print("SMART RE-SCRAPING SYSTEM")
    print("="*70)
    print(f"Database: {DB_PATH}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE UPDATE'}")
    if args.tier:
        print(f"Tier filter: Tier {args.tier} only")
    if args.limit:
        print(f"Limit: {args.limit} postings per tier")
    print()

    conn = sqlite3.connect(DB_PATH)

    try:
        all_stats = {}

        # Tier 1: OPEN postings
        if not args.tier or args.tier == 1:
            postings = get_tier1_postings(conn)
            all_stats[1] = run_tier(conn, 1, postings, "Active (OPEN) Postings",
                                   args.dry_run, args.limit)

        # Tier 2: Recently CLOSED
        if not args.tier or args.tier == 2:
            postings = get_tier2_postings(conn, days=60)
            all_stats[2] = run_tier(conn, 2, postings, "Recently CLOSED (last 60 days)",
                                   args.dry_run, args.limit)

        # Tier 3: Pending awards (CRITICAL - no age limit!)
        if not args.tier or args.tier == 3:
            postings = get_tier3_postings(conn)
            all_stats[3] = run_tier(conn, 3, postings, "Pending Awards (no age limit, exponential backoff)",
                                   args.dry_run, args.limit)

        # Tier 4: Recent awards (verification)
        if not args.tier or args.tier == 4:
            postings = get_tier4_postings(conn, days=90)
            all_stats[4] = run_tier(conn, 4, postings, "Recent Awards (verification)",
                                   args.dry_run, args.limit)

        # Summary
        print("="*70)
        print("OVERALL SUMMARY")
        print("="*70)
        total_updated = sum(s['updated'] for s in all_stats.values())
        total_status_changes = sum(s['status_changed'] for s in all_stats.values())
        total_awards = sum(s['award_added'] for s in all_stats.values())
        total_errors = sum(s['errors'] for s in all_stats.values())

        print(f"Total postings updated: {total_updated:,}")
        print(f"Status changes detected: {total_status_changes:,}")
        print(f"Awards added: {total_awards:,}")
        print(f"Errors: {total_errors:,}")
        print()

        if not args.dry_run:
            print("[OK] Database updated successfully")
            print()
            print("Next steps:")
            print("  - Run analyze_award_timing.py to see award statistics")
            print("  - Check status_history table for transition timeline")
            print("  - Schedule this script to run weekly for continuous updates")
        else:
            print("[SKIP] Dry run complete - no changes made")

        print()

    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        conn.close()


if __name__ == "__main__":
    main()
