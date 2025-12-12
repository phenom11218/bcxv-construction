#!/usr/bin/env python3
"""
Fix scrape_log UNIQUE constraint for re-scraping
=================================================
Removes UNIQUE constraint on (year, posting_number) to allow multiple
log entries for the same posting during re-scraping.

Author: BCXV Construction Analytics
Date: 2025-12-12
"""

import sqlite3
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent.parent / "alberta_procurement.db"

def fix_scrape_log_constraint():
    """Remove UNIQUE constraint from scrape_log table."""
    print("=" * 70)
    print("FIXING SCRAPE_LOG CONSTRAINT")
    print("=" * 70)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check current structure
        cursor.execute("SELECT COUNT(*) FROM scrape_log")
        log_count = cursor.fetchone()[0]
        print(f"\nCurrent scrape_log entries: {log_count:,}")

        # Create new table without UNIQUE constraint
        print("\n1. Creating new scrape_log table without UNIQUE constraint...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scrape_log_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL,
                posting_number INTEGER NOT NULL,
                reference_number TEXT,
                success BOOLEAN NOT NULL,
                error_message TEXT,
                http_status_code INTEGER,
                scraped_at TIMESTAMP NOT NULL
            )
        """)

        # Copy all data
        print("2. Copying existing log entries...")
        cursor.execute("""
            INSERT INTO scrape_log_new
            SELECT id, year, posting_number, reference_number, success,
                   error_message, http_status_code, scraped_at
            FROM scrape_log
        """)

        # Drop old table
        print("3. Dropping old scrape_log table...")
        cursor.execute("DROP TABLE scrape_log")

        # Rename new table
        print("4. Renaming new table...")
        cursor.execute("ALTER TABLE scrape_log_new RENAME TO scrape_log")

        # Recreate indexes (non-unique)
        print("5. Recreating indexes...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_scrape_year
            ON scrape_log(year)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_scrape_success
            ON scrape_log(success)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_scrape_reference
            ON scrape_log(reference_number)
        """)

        conn.commit()

        # Verify
        cursor.execute("SELECT COUNT(*) FROM scrape_log")
        new_count = cursor.fetchone()[0]

        print(f"\n✅ Migration complete!")
        print(f"   Entries preserved: {new_count:,}")
        print(f"   UNIQUE constraint removed - re-scraping now allowed!")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    fix_scrape_log_constraint()
