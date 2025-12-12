"""
Upload 2023 Data to Turso (Direct API Method)
==============================================
Directly uploads 2023 data to Turso using their HTTP API.
No need to destroy database, preserves existing auth tokens.

This script:
1. Reads 2023 data from local SQLite database
2. Uploads it directly to Turso via HTTP API
3. Preserves all existing data (2024-2025)
4. No token regeneration needed

Usage:
    python upload_2023_to_turso.py

You'll be prompted for your Turso database URL and auth token.
"""

import sqlite3
import json
import requests
from pathlib import Path
from typing import List, Tuple, Any

DB_PATH = Path(__file__).parent.parent / "alberta_procurement.db"


def get_turso_credentials():
    """Get Turso credentials from user or environment."""
    print("="*70)
    print("TURSO DATABASE CREDENTIALS")
    print("="*70)
    print("\nYou can find these in your Turso dashboard or Streamlit secrets.")
    print()

    db_url = input("Enter Turso database URL (e.g., https://...turso.io): ").strip()
    if db_url.startswith('libsql://'):
        db_url = db_url.replace('libsql://', 'https://')

    auth_token = input("Enter Turso auth token: ").strip()

    return db_url, auth_token


def execute_turso_query(db_url: str, auth_token: str, sql: str, params: List[Any] = None):
    """Execute a query on Turso via HTTP API."""
    # Turso uses the /v2/pipeline endpoint for SQL execution
    url = f"{db_url}/v2/pipeline"

    headers = {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json'
    }

    # Build request payload
    payload = {
        "requests": [
            {
                "type": "execute",
                "stmt": {
                    "sql": sql,
                    "args": params or []
                }
            }
        ]
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Turso API error: {response.status_code} - {response.text}")


def upload_rows_in_batches(db_url: str, auth_token: str, table_name: str,
                           columns: List[str], rows: List[Tuple], batch_size: int = 100):
    """Upload rows in batches to Turso."""
    total = len(rows)
    uploaded = 0
    errors = 0

    print(f"  Uploading {total} rows in batches of {batch_size}...")

    for i in range(0, total, batch_size):
        batch = rows[i:i + batch_size]

        try:
            # Build INSERT statement with placeholders
            placeholders = ', '.join(['?' for _ in columns])
            column_list = ', '.join(columns)

            # Execute each row in the batch
            for row in batch:
                sql = f"INSERT OR REPLACE INTO {table_name} ({column_list}) VALUES ({placeholders})"
                execute_turso_query(db_url, auth_token, sql, list(row))
                uploaded += 1

            # Progress update
            progress = (i + len(batch)) / total * 100
            print(f"    Progress: {i + len(batch)}/{total} ({progress:.1f}%)")

        except Exception as e:
            errors += 1
            print(f"    ✗ Batch error: {e}")

    print(f"  ✓ Uploaded {uploaded}/{total} rows ({errors} errors)")
    return uploaded, errors


def export_and_upload_table(local_conn, db_url: str, auth_token: str,
                            table_name: str, where_clause: str = ""):
    """Export table data from local DB and upload to Turso."""
    cursor = local_conn.cursor()

    # Get column names
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]

    # Get data
    query = f"SELECT * FROM {table_name}"
    if where_clause:
        query += f" WHERE {where_clause}"

    cursor.execute(query)
    rows = cursor.fetchall()

    if not rows:
        print(f"  (no data to upload)")
        return 0, 0

    # Upload to Turso
    return upload_rows_in_batches(db_url, auth_token, table_name, columns, rows)


def main():
    """Main upload process."""
    print("\n" + "="*70)
    print("UPLOAD 2023 DATA TO TURSO")
    print("="*70)
    print("\nThis will upload 2023 postings to your existing Turso database.")
    print("Your existing 2024-2025 data will NOT be affected.")
    print("No need to regenerate auth tokens!\n")

    # Get credentials
    db_url, auth_token = get_turso_credentials()

    print("\n" + "="*70)
    print("CONNECTING TO LOCAL DATABASE")
    print("="*70)

    local_conn = sqlite3.connect(DB_PATH)

    # Verify 2023 data exists
    cursor = local_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM opportunities WHERE year = 2023")
    count_2023 = cursor.fetchone()[0]

    print(f"\n✓ Found {count_2023:,} postings from 2023 in local database")

    if count_2023 == 0:
        print("✗ No 2023 data to upload!")
        return

    print("\n" + "="*70)
    print("UPLOADING TO TURSO")
    print("="*70)

    # Tables to upload (in order for foreign key constraints)
    tables_to_upload = [
        ('opportunities', "year = 2023"),
        ('raw_data', "year = 2023"),
        ('scrape_log', "year = 2023"),
        ('bidders', "opportunity_ref LIKE 'AB-2023-%'"),
        ('interested_suppliers', "opportunity_ref LIKE 'AB-2023-%'"),
        ('awards', "opportunity_ref LIKE 'AB-2023-%'"),
        ('documents', "opportunity_ref LIKE 'AB-2023-%'"),
        ('contacts', "opportunity_ref LIKE 'AB-2023-%'"),
    ]

    total_uploaded = 0
    total_errors = 0

    for table_name, where_clause in tables_to_upload:
        print(f"\n{table_name}:")
        try:
            uploaded, errors = export_and_upload_table(
                local_conn, db_url, auth_token, table_name, where_clause
            )
            total_uploaded += uploaded
            total_errors += errors
        except Exception as e:
            print(f"  ✗ Error: {e}")
            total_errors += 1

    local_conn.close()

    print("\n" + "="*70)
    print("UPLOAD COMPLETE")
    print("="*70)
    print(f"Total rows uploaded: {total_uploaded:,}")
    print(f"Total errors: {total_errors}")

    print("\n✓ Your Turso database should now have all 2023-2025 data!")
    print("\nVerify with:")
    print("  turso db shell alberta-procurement \"SELECT year, COUNT(*) FROM opportunities GROUP BY year;\"")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Upload cancelled by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
