"""
Database Migrations for Smart Re-scraping System
=================================================
Adds tracking columns and status history table to support intelligent updates.

Usage:
    python database_migrations.py

This will:
1. Add last_scraped_at column to opportunities table
2. Add scrape_count column to opportunities table
3. Add previous_status column to opportunities table
4. Create status_history table for tracking transitions
"""

import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "alberta_procurement.db"


def run_migration(conn):
    """Run all database migrations."""
    cursor = conn.cursor()

    print("="*70)
    print("DATABASE MIGRATIONS FOR SMART RE-SCRAPING")
    print("="*70)
    print()

    # Migration 1: Add last_scraped_at column
    print("Migration 1: Adding last_scraped_at column...")
    try:
        cursor.execute("""
            ALTER TABLE opportunities
            ADD COLUMN last_scraped_at TEXT
        """)
        print("  ✓ Added last_scraped_at column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("  ⊘ Column already exists, skipping")
        else:
            raise

    # Migration 2: Add scrape_count column
    print("\nMigration 2: Adding scrape_count column...")
    try:
        cursor.execute("""
            ALTER TABLE opportunities
            ADD COLUMN scrape_count INTEGER DEFAULT 1
        """)
        print("  ✓ Added scrape_count column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("  ⊘ Column already exists, skipping")
        else:
            raise

    # Migration 3: Add previous_status column
    print("\nMigration 3: Adding previous_status column...")
    try:
        cursor.execute("""
            ALTER TABLE opportunities
            ADD COLUMN previous_status TEXT
        """)
        print("  ✓ Added previous_status column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("  ⊘ Column already exists, skipping")
        else:
            raise

    # Migration 4: Create status_history table
    print("\nMigration 4: Creating status_history table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS status_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference_number TEXT NOT NULL,
            old_status TEXT,
            new_status TEXT,
            changed_at TEXT NOT NULL,
            days_in_previous_status INTEGER,
            close_date TEXT,
            awarded_on TEXT,
            FOREIGN KEY (reference_number) REFERENCES opportunities(reference_number)
        )
    """)
    print("  ✓ Created status_history table")

    # Migration 5: Initialize last_scraped_at with scraped_at values
    print("\nMigration 5: Initializing last_scraped_at from scraped_at...")
    cursor.execute("""
        UPDATE opportunities
        SET last_scraped_at = scraped_at
        WHERE last_scraped_at IS NULL AND scraped_at IS NOT NULL
    """)
    updated = cursor.rowcount
    print(f"  ✓ Initialized {updated:,} records")

    # Migration 6: Initialize scrape_count to 1 for existing records
    print("\nMigration 6: Initializing scrape_count...")
    cursor.execute("""
        UPDATE opportunities
        SET scrape_count = 1
        WHERE scrape_count IS NULL
    """)
    updated = cursor.rowcount
    print(f"  ✓ Initialized {updated:,} records")

    # Create index for faster queries
    print("\nMigration 7: Creating performance indexes...")
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_status_award
        ON opportunities(status_code, awarded_on)
    """)
    print("  ✓ Created idx_status_award")

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_last_scraped
        ON opportunities(last_scraped_at)
    """)
    print("  ✓ Created idx_last_scraped")

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_close_date
        ON opportunities(close_date)
    """)
    print("  ✓ Created idx_close_date")

    conn.commit()

    print("\n" + "="*70)
    print("MIGRATIONS COMPLETE")
    print("="*70)
    print()


def verify_migrations(conn):
    """Verify that all migrations were applied successfully."""
    cursor = conn.cursor()

    print("Verifying migrations...")
    print()

    # Check columns
    cursor.execute("PRAGMA table_info(opportunities)")
    columns = {row[1] for row in cursor.fetchall()}

    required_columns = {'last_scraped_at', 'scrape_count', 'previous_status'}
    missing = required_columns - columns

    if missing:
        print(f"  ✗ Missing columns: {missing}")
        return False
    else:
        print(f"  ✓ All tracking columns present")

    # Check status_history table
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='status_history'
    """)
    if cursor.fetchone():
        print("  ✓ status_history table exists")
    else:
        print("  ✗ status_history table missing")
        return False

    # Show statistics
    print()
    print("Database Statistics:")
    print("-" * 70)

    cursor.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(last_scraped_at) as has_last_scraped,
            COUNT(CASE WHEN scrape_count > 1 THEN 1 END) as rescraped,
            COUNT(CASE WHEN awarded_on IS NULL AND status_code IN ('CLOSED', 'EVALUATION') THEN 1 END) as pending_awards
        FROM opportunities
    """)
    stats = cursor.fetchone()

    print(f"Total postings:          {stats[0]:,}")
    print(f"Has tracking data:       {stats[1]:,}")
    print(f"Re-scraped (count > 1):  {stats[2]:,}")
    print(f"Pending awards:          {stats[3]:,}")

    print()
    return True


def main():
    """Run migrations."""
    if not DB_PATH.exists():
        print(f"✗ Error: Database not found at {DB_PATH}")
        print("  Please ensure the database exists first.")
        return

    print(f"Database: {DB_PATH}")
    print()

    conn = sqlite3.connect(DB_PATH)

    try:
        run_migration(conn)
        verify_migrations(conn)

        print("="*70)
        print("SUCCESS!")
        print("="*70)
        print()
        print("Your database is now ready for smart re-scraping.")
        print()
        print("Next steps:")
        print("  1. Run update_active_postings.py to update existing postings")
        print("  2. Run scrape_new_postings.py to discover new postings")
        print("  3. Check SMART_SCRAPING_GUIDE.md for usage instructions")
        print()

    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        conn.close()


if __name__ == "__main__":
    main()
