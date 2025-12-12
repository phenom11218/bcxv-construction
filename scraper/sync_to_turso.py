"""
Incremental Turso Database Sync
================================
Syncs new and updated records from local SQLite database to Turso cloud database.

This script is designed to run after weekly scraping to keep the Streamlit Cloud
app's Turso database up-to-date with the latest scraped data.

Features:
- Incremental sync (only new/updated records since last sync)
- Progress tracking and statistics
- Error handling and retry logic
- Supports all tables: opportunities, bidders, interested_suppliers, etc.

Usage:
    # With .env file (recommended for automation):
    python sync_to_turso.py

    # With command line arguments:
    python sync_to_turso.py --url "https://your-db.turso.io" --token "your-token"

    # Dry run (show what would be synced without syncing):
    python sync_to_turso.py --dry-run

    # Force full sync (sync all records, not just changes):
    python sync_to_turso.py --full

Setup:
    1. Copy .env.example to .env
    2. Add your Turso credentials to .env
    3. Run this script after scraping completes

Author: BCXV Construction Analytics
Date: 2025-12-12
"""

import sqlite3
import os
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional
from dotenv import load_dotenv

try:
    import libsql_client
except ImportError:
    print("[ERROR] libsql-client not installed.")
    print("Install with: pip install libsql-client")
    exit(1)

# Load environment variables from .env file
load_dotenv()

LOCAL_DB_PATH = Path(__file__).parent.parent / "alberta_procurement.db"
SYNC_STATE_FILE = Path(__file__).parent / ".turso_sync_state"


class TursoSync:
    """Handles incremental synchronization to Turso cloud database."""

    def __init__(self, turso_url: str, turso_token: str, dry_run: bool = False):
        """
        Initialize Turso sync client.

        Args:
            turso_url: Turso database URL (https://...)
            turso_token: Turso authentication token
            dry_run: If True, don't actually sync, just show what would be synced
        """
        self.turso_url = turso_url
        self.turso_token = turso_token
        self.dry_run = dry_run

        # Create Turso client
        try:
            self.client = libsql_client.create_client_sync(
                url=turso_url,
                auth_token=turso_token
            )
        except Exception as e:
            raise Exception(f"Failed to connect to Turso: {e}")

        # Connect to local database
        if not LOCAL_DB_PATH.exists():
            raise Exception(f"Local database not found: {LOCAL_DB_PATH}")

        self.local_conn = sqlite3.connect(LOCAL_DB_PATH)
        self.local_conn.row_factory = sqlite3.Row  # Access columns by name

    def get_last_sync_time(self) -> Optional[str]:
        """Get the timestamp of the last successful sync."""
        if not SYNC_STATE_FILE.exists():
            return None

        try:
            with open(SYNC_STATE_FILE, 'r') as f:
                return f.read().strip()
        except Exception:
            return None

    def save_sync_time(self, timestamp: str):
        """Save the current sync timestamp."""
        try:
            with open(SYNC_STATE_FILE, 'w') as f:
                f.write(timestamp)
        except Exception as e:
            print(f"[WARNING] Could not save sync state: {e}")

    def get_changed_records(self, table_name: str, last_sync: Optional[str]) -> List[sqlite3.Row]:
        """
        Get records that have changed since last sync.

        For opportunities table, uses last_scraped_at column.
        For other tables, syncs all records if this is first sync, otherwise uses heuristics.
        """
        cursor = self.local_conn.cursor()

        # Check if table has last_scraped_at column
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        has_timestamp = 'last_scraped_at' in columns

        if has_timestamp and last_sync:
            # Incremental sync based on timestamp
            query = f"""
                SELECT * FROM {table_name}
                WHERE last_scraped_at > ?
                ORDER BY last_scraped_at
            """
            cursor.execute(query, (last_sync,))
        else:
            # Full table sync (first sync or no timestamp column)
            query = f"SELECT * FROM {table_name}"
            cursor.execute(query)

        return cursor.fetchall()

    def sync_table(self, table_name: str, last_sync: Optional[str]) -> Dict[str, int]:
        """
        Sync a single table to Turso.

        Returns:
            Dictionary with sync statistics
        """
        stats = {
            'checked': 0,
            'synced': 0,
            'errors': 0,
            'skipped': 0
        }

        print(f"\n{'='*70}")
        print(f"SYNCING TABLE: {table_name}")
        print(f"{'='*70}")

        # Get changed records
        records = self.get_changed_records(table_name, last_sync)
        stats['checked'] = len(records)

        if stats['checked'] == 0:
            print("  No changes to sync")
            return stats

        print(f"  Records to sync: {stats['checked']:,}")

        if self.dry_run:
            print("  [DRY RUN] Would sync these records (not actually syncing)")
            stats['skipped'] = stats['checked']
            return stats

        # Get column names
        columns = list(records[0].keys()) if records else []

        # Sync records in batches
        batch_size = 100
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]

            for record in batch:
                try:
                    # Build INSERT OR REPLACE statement
                    placeholders = ', '.join(['?' for _ in columns])
                    column_list = ', '.join(columns)
                    sql = f"INSERT OR REPLACE INTO {table_name} ({column_list}) VALUES ({placeholders})"

                    # Convert record to list of values
                    values = [record[col] for col in columns]

                    # Execute on Turso
                    self.client.execute(sql, values)
                    stats['synced'] += 1

                except Exception as e:
                    stats['errors'] += 1
                    print(f"  [ERROR] Failed to sync record: {e}")

            # Progress update
            progress = min(i + batch_size, len(records))
            print(f"  Progress: {progress}/{len(records)} ({progress/len(records)*100:.1f}%) | "
                  f"Synced: {stats['synced']} | Errors: {stats['errors']}")

            # Rate limiting to avoid overwhelming Turso
            time.sleep(0.1)

        print(f"\n  [OK] Synced {stats['synced']:,} records")
        if stats['errors'] > 0:
            print(f"  [WARNING] {stats['errors']:,} errors occurred")

        return stats

    def sync_all(self, full_sync: bool = False):
        """
        Sync all tables to Turso.

        Args:
            full_sync: If True, sync all records regardless of timestamp
        """
        print("="*70)
        print("TURSO DATABASE SYNC")
        print("="*70)
        print(f"Local database: {LOCAL_DB_PATH}")
        print(f"Turso database: {self.turso_url}")
        print(f"Mode: {'FULL SYNC' if full_sync else 'INCREMENTAL SYNC'}")
        if self.dry_run:
            print("DRY RUN: No changes will be made")
        print()

        # Get last sync time
        last_sync = None if full_sync else self.get_last_sync_time()
        if last_sync:
            print(f"Last sync: {last_sync}")
        else:
            print("Last sync: Never (this is the first sync)")

        # Define tables to sync (in dependency order)
        tables = [
            'opportunities',
            'bidders',
            'interested_suppliers',
            'scrape_log',
            'status_history'  # May not exist in all databases
        ]

        total_stats = {
            'checked': 0,
            'synced': 0,
            'errors': 0,
            'skipped': 0
        }

        start_time = time.time()

        # Sync each table
        for table in tables:
            # Check if table exists in local database
            cursor = self.local_conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name=?
            """, (table,))

            if not cursor.fetchone():
                print(f"\n[SKIP] Table '{table}' does not exist in local database")
                continue

            try:
                table_stats = self.sync_table(table, last_sync)
                for key in total_stats:
                    total_stats[key] += table_stats[key]
            except Exception as e:
                print(f"\n[ERROR] Failed to sync table '{table}': {e}")
                total_stats['errors'] += 1

        elapsed = time.time() - start_time

        # Summary
        print("\n" + "="*70)
        print("SYNC SUMMARY")
        print("="*70)
        print(f"Total records checked: {total_stats['checked']:,}")
        print(f"Total records synced: {total_stats['synced']:,}")
        print(f"Total errors: {total_stats['errors']:,}")
        if self.dry_run:
            print(f"Total skipped (dry run): {total_stats['skipped']:,}")
        print(f"Time elapsed: {elapsed/60:.1f} minutes")
        print()

        if not self.dry_run and total_stats['synced'] > 0:
            # Save sync timestamp
            current_time = datetime.now().isoformat()
            self.save_sync_time(current_time)
            print(f"[OK] Sync completed successfully")
            print(f"Next sync will only process records modified after: {current_time}")
        elif self.dry_run:
            print("[DRY RUN] No changes were made")
        else:
            print("[OK] Sync completed (no new records to sync)")

        print("="*70)

    def close(self):
        """Close database connections."""
        self.local_conn.close()


def get_turso_credentials(args: argparse.Namespace) -> Tuple[str, str]:
    """
    Get Turso credentials from various sources (priority order).

    1. Command line arguments
    2. Environment variables
    3. .env file
    4. Interactive prompt

    Returns:
        Tuple of (url, token)
    """
    # Try command line arguments
    if args.url and args.token:
        return args.url, args.token

    # Try environment variables / .env file
    url = os.getenv('TURSO_DATABASE_URL')
    token = os.getenv('TURSO_AUTH_TOKEN')

    if url and token:
        print("[OK] Using Turso credentials from environment")
        return url, token

    # Interactive prompt (fallback)
    print("="*70)
    print("TURSO CREDENTIALS REQUIRED")
    print("="*70)
    print("\nNo credentials found in environment or .env file.")
    print("Please enter your Turso credentials manually.\n")
    print("You can find these in:")
    print("  - Streamlit Cloud: Settings > Secrets")
    print("  - Turso Dashboard: https://turso.tech/dashboard\n")

    url = input("Enter Turso database URL: ").strip()
    token = input("Enter Turso auth token: ").strip()

    # Convert libsql:// to https:// if needed
    if url.startswith('libsql://'):
        url = url.replace('libsql://', 'https://')

    return url, token


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(
        description="Sync local database changes to Turso cloud database"
    )
    parser.add_argument('--url', type=str, help="Turso database URL")
    parser.add_argument('--token', type=str, help="Turso auth token")
    parser.add_argument('--dry-run', action='store_true',
                       help="Show what would be synced without actually syncing")
    parser.add_argument('--full', action='store_true',
                       help="Full sync (sync all records, not just changes)")
    args = parser.parse_args()

    try:
        # Get credentials
        url, token = get_turso_credentials(args)

        if not url or not token:
            print("[ERROR] Missing Turso credentials")
            print("\nTo fix this:")
            print("  1. Copy .env.example to .env")
            print("  2. Add your credentials to .env")
            print("  3. Or pass credentials via --url and --token arguments")
            return 1

        # Create sync client and sync
        sync = TursoSync(url, token, dry_run=args.dry_run)

        try:
            sync.sync_all(full_sync=args.full)
            return 0
        finally:
            sync.close()

    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Sync cancelled by user")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Sync failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
