"""
Database Backup Script
======================
Creates timestamped backups of the Alberta Procurement database
and maintains a rolling backup history (keeps last 4 weeks).

Usage:
    python backup_database.py
    python backup_database.py --keep 8  # Keep 8 backups instead of 4
"""

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
import argparse
import os

DB_PATH = Path(__file__).parent.parent / "alberta_procurement.db"
BACKUP_DIR = Path(__file__).parent.parent / "database_backups"


def get_database_stats(db_path: Path) -> dict:
    """Get basic statistics about the database."""
    if not db_path.exists():
        return None

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    stats = {}

    # Get row counts for main tables
    try:
        cursor.execute("SELECT COUNT(*) FROM opportunities")
        stats['opportunities'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM bidders")
        stats['bidders'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM interested_suppliers")
        stats['interested_suppliers'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM scrape_log")
        stats['scrape_log'] = cursor.fetchone()[0]

        # Get date range
        cursor.execute("SELECT MIN(year), MAX(year) FROM opportunities")
        min_year, max_year = cursor.fetchone()
        stats['year_range'] = f"{min_year}-{max_year}"

    except sqlite3.OperationalError:
        pass  # Table might not exist

    conn.close()

    # Get file size
    stats['size_mb'] = db_path.stat().st_size / (1024 * 1024)

    return stats


def create_backup(keep_last: int = 4) -> str:
    """
    Create a timestamped backup of the database.

    Args:
        keep_last: Number of backups to keep (default: 4 weeks)

    Returns:
        Path to the backup file
    """
    print("="*70)
    print("DATABASE BACKUP")
    print("="*70)

    # Check if database exists
    if not DB_PATH.exists():
        print(f"[ERROR] Database not found: {DB_PATH}")
        return None

    # Create backup directory if it doesn't exist
    BACKUP_DIR.mkdir(exist_ok=True)

    # Get database stats
    stats = get_database_stats(DB_PATH)

    print(f"\nDatabase: {DB_PATH.name}")
    print(f"Size: {stats['size_mb']:.1f} MB")
    print(f"Records:")
    print(f"  - Opportunities: {stats.get('opportunities', 0):,}")
    print(f"  - Bidders: {stats.get('bidders', 0):,}")
    print(f"  - Interested Suppliers: {stats.get('interested_suppliers', 0):,}")
    print(f"  - Scrape Log: {stats.get('scrape_log', 0):,}")
    print(f"  - Year Range: {stats.get('year_range', 'N/A')}")

    # Create timestamp for backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"alberta_procurement_backup_{timestamp}.db"
    backup_path = BACKUP_DIR / backup_filename

    # Create backup
    print(f"\nCreating backup: {backup_filename}")
    try:
        shutil.copy2(DB_PATH, backup_path)
        backup_size = backup_path.stat().st_size / (1024 * 1024)
        print(f"[OK] Backup created successfully ({backup_size:.1f} MB)")
    except Exception as e:
        print(f"[ERROR] Backup failed: {e}")
        return None

    # Clean up old backups
    print(f"\nManaging backup history (keeping last {keep_last} backups)...")
    backups = sorted(BACKUP_DIR.glob("alberta_procurement_backup_*.db"), reverse=True)

    if len(backups) > keep_last:
        to_delete = backups[keep_last:]
        for old_backup in to_delete:
            try:
                old_backup.unlink()
                print(f"  Deleted old backup: {old_backup.name}")
            except Exception as e:
                print(f"  [WARNING] Could not delete {old_backup.name}: {e}")

    # Show backup history
    print(f"\nBackup history ({len(backups)} total):")
    for i, backup in enumerate(backups[:keep_last], 1):
        size = backup.stat().st_size / (1024 * 1024)
        modified = datetime.fromtimestamp(backup.stat().st_mtime)
        print(f"  {i}. {backup.name} - {size:.1f} MB - {modified.strftime('%Y-%m-%d %H:%M')}")

    print("\n" + "="*70)
    print(f"[OK] Backup complete: {backup_path}")
    print("="*70)

    return str(backup_path)


def restore_backup(backup_file: str, confirm: bool = False):
    """
    Restore database from a backup file.

    Args:
        backup_file: Path to backup file to restore
        confirm: Skip confirmation prompt if True
    """
    backup_path = Path(backup_file)

    if not backup_path.exists():
        print(f"[ERROR] Backup file not found: {backup_file}")
        return False

    print("="*70)
    print("DATABASE RESTORE")
    print("="*70)
    print(f"\nBackup file: {backup_path.name}")

    # Get stats of backup
    stats = get_database_stats(backup_path)
    print(f"Size: {stats['size_mb']:.1f} MB")
    print(f"Records: {stats.get('opportunities', 0):,} opportunities")

    # Confirm restore
    if not confirm:
        print("\n[WARNING] This will REPLACE your current database!")
        response = input("Are you sure you want to restore? (yes/no): ")
        if response.lower() != 'yes':
            print("[CANCELLED] Restore cancelled by user")
            return False

    # Create backup of current database before restoring
    print("\nCreating safety backup of current database...")
    safety_backup = BACKUP_DIR / f"pre_restore_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    try:
        shutil.copy2(DB_PATH, safety_backup)
        print(f"[OK] Safety backup created: {safety_backup.name}")
    except Exception as e:
        print(f"[WARNING] Could not create safety backup: {e}")

    # Restore backup
    print(f"\nRestoring database from {backup_path.name}...")
    try:
        shutil.copy2(backup_path, DB_PATH)
        print("[OK] Database restored successfully!")
        print("\n" + "="*70)
        return True
    except Exception as e:
        print(f"[ERROR] Restore failed: {e}")
        print("\n" + "="*70)
        return False


def list_backups():
    """List all available backups."""
    print("="*70)
    print("AVAILABLE BACKUPS")
    print("="*70)

    if not BACKUP_DIR.exists():
        print("\nNo backup directory found. Run a backup first!")
        return

    backups = sorted(BACKUP_DIR.glob("alberta_procurement_backup_*.db"), reverse=True)

    if not backups:
        print("\nNo backups found.")
        return

    print(f"\nFound {len(backups)} backup(s):\n")
    for i, backup in enumerate(backups, 1):
        size = backup.stat().st_size / (1024 * 1024)
        modified = datetime.fromtimestamp(backup.stat().st_mtime)
        stats = get_database_stats(backup)

        print(f"{i}. {backup.name}")
        print(f"   Created: {modified.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Size: {size:.1f} MB")
        print(f"   Records: {stats.get('opportunities', 0):,} opportunities")
        print()


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(description="Database backup management")
    parser.add_argument('--keep', type=int, default=4,
                       help="Number of backups to keep (default: 4)")
    parser.add_argument('--restore', type=str,
                       help="Restore from backup file")
    parser.add_argument('--list', action='store_true',
                       help="List all available backups")
    parser.add_argument('--yes', action='store_true',
                       help="Skip confirmation prompts")

    args = parser.parse_args()

    if args.list:
        list_backups()
    elif args.restore:
        restore_backup(args.restore, confirm=args.yes)
    else:
        create_backup(keep_last=args.keep)


if __name__ == "__main__":
    main()
