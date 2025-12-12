"""
Export 2023 Data to SQL Insert Statements
==========================================
Exports all 2023 postings as SQL INSERT statements that can be run on Turso.
This allows incremental updates without re-uploading the entire database.

Usage:
    python export_2023_data.py > insert_2023.sql
    turso db shell alberta-procurement < insert_2023.sql
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "alberta_procurement.db"


def escape_sql_string(value):
    """Escape single quotes for SQL."""
    if value is None:
        return 'NULL'
    if isinstance(value, str):
        return f"'{value.replace(chr(39), chr(39)+chr(39))}'"  # Escape single quotes
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, bool):
        return '1' if value else '0'
    return f"'{str(value)}'"


def export_table(conn, table_name, year_filter=None):
    """Export a table's data as INSERT statements."""
    cursor = conn.cursor()

    # Get column names
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]

    # Build query
    if year_filter and 'year' in columns:
        query = f"SELECT * FROM {table_name} WHERE year = {year_filter}"
    elif year_filter and table_name == 'opportunities':
        query = f"SELECT * FROM {table_name} WHERE year = {year_filter}"
    elif table_name in ['bidders', 'interested_suppliers', 'awards', 'documents', 'contacts']:
        # For related tables, filter by reference number prefix
        query = f"""
            SELECT * FROM {table_name}
            WHERE opportunity_ref LIKE 'AB-{year_filter}-%'
        """
    elif table_name == 'raw_data':
        query = f"SELECT * FROM {table_name} WHERE year = {year_filter}"
    elif table_name == 'scrape_log':
        query = f"SELECT * FROM {table_name} WHERE year = {year_filter}"
    else:
        query = f"SELECT * FROM {table_name}"

    cursor.execute(query)
    rows = cursor.fetchall()

    if not rows:
        print(f"-- No data in {table_name}")
        return 0

    print(f"\n-- {table_name} ({len(rows)} rows)")

    # Generate INSERT statements
    for row in rows:
        values = [escape_sql_string(val) for val in row]
        values_str = ', '.join(values)
        print(f"INSERT OR REPLACE INTO {table_name} ({', '.join(columns)}) VALUES ({values_str});")

    return len(rows)


def main():
    """Export 2023 data."""
    conn = sqlite3.connect(DB_PATH)

    print("-- ========================================")
    print("-- Alberta Procurement 2023 Data Export")
    print("-- ========================================")
    print("-- Generated SQL INSERT statements for 2023 postings")
    print("-- ")
    print("-- Usage:")
    print("--   turso db shell alberta-procurement < insert_2023.sql")
    print("-- ========================================\n")

    # Tables to export (in order to respect foreign keys)
    tables = [
        'opportunities',
        'bidders',
        'interested_suppliers',
        'awards',
        'documents',
        'contacts',
        'raw_data',
        'scrape_log'
    ]

    total_rows = 0
    for table in tables:
        try:
            rows = export_table(conn, table, year_filter=2023)
            total_rows += rows
        except Exception as e:
            print(f"-- ERROR exporting {table}: {e}")

    print(f"\n-- ========================================")
    print(f"-- Total rows exported: {total_rows:,}")
    print(f"-- ========================================")

    conn.close()


if __name__ == "__main__":
    main()
