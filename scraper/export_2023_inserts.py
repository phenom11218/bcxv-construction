"""
Export 2023 Data as SQL INSERT Statements
==========================================
Exports 2023 postings as clean SQL INSERT statements for Turso.
Generates smaller, manageable SQL files that can be uploaded incrementally.

Usage:
    python export_2023_inserts.py

This will create insert_2023.sql that you can run:
    turso db shell alberta-procurement < insert_2023.sql
"""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "alberta_procurement.db"
OUTPUT_FILE = Path(__file__).parent.parent / "insert_2023.sql"


def escape_sql_value(value):
    """Escape values for SQL, handling None, strings, numbers, etc."""
    if value is None:
        return 'NULL'
    if isinstance(value, bool):
        return '1' if value else '0'
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        # Escape single quotes by doubling them
        escaped = value.replace("'", "''")
        # Escape backslashes
        escaped = escaped.replace("\\", "\\\\")
        return f"'{escaped}'"
    return f"'{str(value)}'"


def export_table_data(conn, table_name, where_clause=""):
    """Export table data as INSERT statements."""
    cursor = conn.cursor()

    # Get column info
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    column_list = ', '.join(columns)

    # Get data
    query = f"SELECT * FROM {table_name}"
    if where_clause:
        query += f" WHERE {where_clause}"

    cursor.execute(query)
    rows = cursor.fetchall()

    if not rows:
        return []

    inserts = []
    for row in rows:
        values = [escape_sql_value(val) for val in row]
        values_str = ', '.join(values)
        inserts.append(f"INSERT OR REPLACE INTO {table_name} ({column_list}) VALUES ({values_str});")

    return inserts


def main():
    """Export all 2023 data."""
    conn = sqlite3.connect(DB_PATH)

    print("Exporting 2023 data from local database...")

    all_inserts = []

    # Export in order to respect foreign key constraints
    tables_and_filters = [
        ('opportunities', "year = 2023"),
        ('raw_data', "year = 2023"),
        ('scrape_log', "year = 2023"),
        ('bidders', "opportunity_ref LIKE 'AB-2023-%'"),
        ('interested_suppliers', "opportunity_ref LIKE 'AB-2023-%'"),
        ('awards', "opportunity_ref LIKE 'AB-2023-%'"),
        ('documents', "opportunity_ref LIKE 'AB-2023-%'"),
        ('contacts', "opportunity_ref LIKE 'AB-2023-%'"),
    ]

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        # Write header
        f.write("-- ========================================\n")
        f.write("-- Alberta Procurement 2023 Data Import\n")
        f.write("-- ========================================\n")
        f.write("-- Generated INSERT statements for 2023 postings\n")
        f.write("-- Total: 1,611 opportunities + related data\n")
        f.write("--\n")
        f.write("-- Usage:\n")
        f.write("--   turso db shell alberta-procurement < insert_2023.sql\n")
        f.write("-- ========================================\n\n")

        total_rows = 0

        for table_name, where_clause in tables_and_filters:
            print(f"  Exporting {table_name}...", end=' ')
            try:
                inserts = export_table_data(conn, table_name, where_clause)

                if inserts:
                    f.write(f"\n-- {table_name} ({len(inserts)} rows)\n")
                    for insert in inserts:
                        f.write(insert + '\n')
                    total_rows += len(inserts)
                    print(f"✓ {len(inserts)} rows")
                else:
                    print("(no data)")

            except Exception as e:
                print(f"✗ Error: {e}")
                f.write(f"-- ERROR in {table_name}: {e}\n")

        f.write(f"\n-- Total rows exported: {total_rows:,}\n")

    conn.close()

    print(f"\n✓ Export complete!")
    print(f"  File: {OUTPUT_FILE}")
    print(f"  Total rows: {total_rows:,}")
    print(f"\nNext step:")
    print(f"  turso db shell alberta-procurement < insert_2023.sql")


if __name__ == "__main__":
    main()
