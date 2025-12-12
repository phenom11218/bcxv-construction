"""
Export Specific Years to SQL for Turso Upload
==============================================
Generates clean INSERT OR REPLACE statements for specified years.

Usage:
    python export_years.py 2021 2022 2023
    python export_years.py 2021  # Single year
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "alberta_procurement.db"


def escape_sql_value(value):
    """Escape values for SQL."""
    if value is None:
        return 'NULL'
    if isinstance(value, bool):
        return '1' if value else '0'
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        # Escape single quotes by doubling them
        escaped = value.replace("'", "''")
        return f"'{escaped}'"
    return f"'{str(value)}'"


def export_table(conn, table_name, where_clause, output_file):
    """Export table data with INSERT OR REPLACE."""
    cursor = conn.cursor()

    # Get column names
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    col_list = ', '.join(columns)

    # Get data
    query = f"SELECT * FROM {table_name} WHERE {where_clause}"
    cursor.execute(query)
    rows = cursor.fetchall()

    if not rows:
        return 0

    print(f"  {table_name}: {len(rows):,} rows")

    # Write INSERT statements
    output_file.write(f"\n-- {table_name} ({len(rows)} rows)\n")

    for row in rows:
        values = ', '.join(escape_sql_value(val) for val in row)
        output_file.write(f"INSERT OR REPLACE INTO {table_name} ({col_list}) VALUES ({values});\n")

    return len(rows)


def main():
    """Export specified years."""
    if len(sys.argv) < 2:
        print("Usage: python export_years.py <year1> [year2] [year3] ...")
        print("Example: python export_years.py 2021 2022 2023")
        sys.exit(1)

    years = [int(y) for y in sys.argv[1:]]
    years_str = '_'.join(map(str, years))
    output_filename = f"export_years_{years_str}.sql"

    print("="*70)
    print("EXPORT YEARS TO SQL")
    print("="*70)
    print(f"Database: {DB_PATH}")
    print(f"Years: {', '.join(map(str, years))}")
    print(f"Output: {output_filename}")
    print()

    if not DB_PATH.exists():
        print(f"✗ Error: Database not found at {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)

    # Check how many records per year
    print("Checking records per year:")
    cursor = conn.cursor()
    for year in years:
        cursor.execute("SELECT COUNT(*) FROM opportunities WHERE year = ?", (year,))
        count = cursor.fetchone()[0]
        print(f"  {year}: {count:,} postings")
    print()

    # Start export
    with open(output_filename, 'w', encoding='utf-8') as f:
        # Header
        f.write("-- ========================================\n")
        f.write(f"-- Alberta Procurement Data Export\n")
        f.write(f"-- Years: {', '.join(map(str, years))}\n")
        f.write(f"-- Generated: {datetime.now().isoformat()}\n")
        f.write("-- ========================================\n\n")

        # Disable foreign keys during insert
        f.write("PRAGMA foreign_keys = OFF;\n\n")

        total_rows = 0

        # Export each table for all years
        tables_and_filters = [
            ('opportunities', f"year IN ({','.join(map(str, years))})"),
            ('raw_data', f"year IN ({','.join(map(str, years))})"),
            ('scrape_log', f"year IN ({','.join(map(str, years))})"),
        ]

        # For related tables, build OR conditions for reference numbers
        ref_conditions = ' OR '.join([f"opportunity_ref LIKE 'AB-{year}-%'" for year in years])

        tables_and_filters.extend([
            ('bidders', ref_conditions),
            ('interested_suppliers', ref_conditions),
            ('awards', ref_conditions),
            ('documents', ref_conditions),
            ('contacts', ref_conditions),
        ])

        print("Exporting tables:")
        for table, where in tables_and_filters:
            try:
                rows = export_table(conn, table, where, f)
                total_rows += rows
            except Exception as e:
                print(f"  ✗ Error exporting {table}: {e}")

        # Re-enable foreign keys
        f.write("\n-- Re-enable foreign key checks\n")
        f.write("PRAGMA foreign_keys = ON;\n")

        # Summary
        f.write(f"\n-- Total rows exported: {total_rows:,}\n")

    conn.close()

    print()
    print("="*70)
    print("EXPORT COMPLETE")
    print("="*70)
    print(f"File: {output_filename}")
    print(f"Total rows: {total_rows:,}")
    print()
    print("Next step:")
    print(f"  turso db shell alberta-procurement < {output_filename}")
    print()


if __name__ == "__main__":
    main()
