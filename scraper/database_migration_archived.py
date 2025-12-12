"""
Database Migration: Add Archived Flag
======================================
Adds a flag to track postings that have been removed from the API
but are preserved in our historical archive.

Usage:
    python database_migration_archived.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "alberta_procurement.db"


def run_migration(conn):
    """Add archived flag column."""
    cursor = conn.cursor()

    print("="*70)
    print("DATABASE MIGRATION: ARCHIVED FLAG")
    print("="*70)
    print()

    # Add is_archived column
    print("Adding is_archived column...")
    try:
        cursor.execute("""
            ALTER TABLE opportunities
            ADD COLUMN is_archived INTEGER DEFAULT 0
        """)
        print("  ✓ Added is_archived column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("  ⊘ Column already exists, skipping")
        else:
            raise

    # Add archived_at timestamp
    print("\nAdding archived_at column...")
    try:
        cursor.execute("""
            ALTER TABLE opportunities
            ADD COLUMN archived_at TEXT
        """)
        print("  ✓ Added archived_at column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("  ⊘ Column already exists, skipping")
        else:
            raise

    # Mark existing 404s as archived based on scrape_log
    print("\nMarking historical 404s as archived...")
    cursor.execute("""
        UPDATE opportunities
        SET is_archived = 1,
            archived_at = (
                SELECT scraped_at FROM scrape_log
                WHERE scrape_log.reference_number = opportunities.reference_number
                  AND scrape_log.http_status_code = 404
                ORDER BY scraped_at DESC
                LIMIT 1
            )
        WHERE reference_number IN (
            SELECT DISTINCT reference_number FROM scrape_log
            WHERE http_status_code = 404
        )
    """)
    updated = cursor.rowcount
    print(f"  ✓ Marked {updated} postings as archived")

    # Create index for faster queries
    print("\nCreating index...")
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_archived
        ON opportunities(is_archived, archived_at)
    """)
    print("  ✓ Created idx_archived")

    conn.commit()

    print("\n" + "="*70)
    print("MIGRATION COMPLETE")
    print("="*70)
    print()


def verify_migration(conn):
    """Verify migration."""
    cursor = conn.cursor()

    print("Verifying migration...")
    print()

    # Check columns
    cursor.execute("PRAGMA table_info(opportunities)")
    columns = {row[1] for row in cursor.fetchall()}

    required = {'is_archived', 'archived_at'}
    missing = required - columns

    if missing:
        print(f"  ✗ Missing columns: {missing}")
        return False
    else:
        print(f"  ✓ All archived columns present")

    # Show statistics
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN is_archived = 1 THEN 1 END) as archived
        FROM opportunities
    """)
    total, archived = cursor.fetchone()

    print()
    print("Statistics:")
    print("-" * 70)
    print(f"Total postings:      {total:,}")
    print(f"Archived (404):      {archived:,} ({archived/total*100:.1f}%)")
    print(f"Active in API:       {total-archived:,} ({(total-archived)/total*100:.1f}%)")
    print()

    return True


def main():
    """Run migration."""
    if not DB_PATH.exists():
        print(f"✗ Error: Database not found at {DB_PATH}")
        return

    print(f"Database: {DB_PATH}")
    print()

    conn = sqlite3.connect(DB_PATH)

    try:
        run_migration(conn)
        verify_migration(conn)

        print("="*70)
        print("SUCCESS!")
        print("="*70)
        print()
        print("The database now tracks archived postings:")
        print("  - is_archived = 1 if posting removed from API")
        print("  - archived_at = timestamp when first detected as 404")
        print()
        print("Historical data is NEVER deleted, only marked as archived.")
        print()
        print("Query examples:")
        print("  -- Show archived postings")
        print("  SELECT * FROM opportunities WHERE is_archived = 1;")
        print()
        print("  -- Show active postings only")
        print("  SELECT * FROM opportunities WHERE is_archived = 0;")
        print()

    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        conn.close()


if __name__ == "__main__":
    main()
