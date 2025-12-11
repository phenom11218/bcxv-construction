"""
Turso Cloud Database Adapter
============================
Adapter for connecting to Turso Cloud SQLite database.

This module provides a drop-in replacement for the local SQLite connection
that works with Turso's cloud-hosted SQLite database.

Author: BCXV Construction Analytics
Date: 2025-12-10
Purpose: Cloud deployment support
"""

import pandas as pd
from typing import Optional, Dict, Any
import libsql_client


class TursoDatabaseConnection:
    """
    Turso Cloud SQLite database connection.

    This class provides the same interface as DatabaseConnection but connects
    to a Turso cloud database instead of local SQLite.
    """

    def __init__(self, database_url: str, auth_token: str):
        """
        Initialize Turso database connection.

        Args:
            database_url: Turso database URL (e.g., libsql://db-name.turso.io)
            auth_token: Turso authentication token
        """
        self.database_url = database_url
        self.auth_token = auth_token

        # Convert libsql:// URL to https:// for HTTP API (more reliable than WebSocket)
        http_url = database_url.replace('libsql://', 'https://')

        # Create Turso client (using sync version for Streamlit)
        self.client = libsql_client.create_client_sync(
            url=http_url,
            auth_token=auth_token
        )

    def execute_query(self, query: str, params: tuple = ()) -> pd.DataFrame:
        """
        Execute a SQL query and return results as a pandas DataFrame.

        Args:
            query: SQL query string
            params: Query parameters (for prepared statements)

        Returns:
            pd.DataFrame: Query results
        """
        try:
            # Turso uses libsql_client which returns results differently
            # We need to convert params tuple to list for Turso
            param_list = list(params) if params else None

            # Execute query
            result_set = self.client.execute(query, param_list)

            # Convert to pandas DataFrame
            if result_set.rows:
                # Get column names from result_set
                columns = list(result_set.columns) if hasattr(result_set, 'columns') else []

                # Convert rows to list format
                # Turso rows can be dicts, tuples, or special objects - convert uniformly
                data = []
                for row in result_set.rows:
                    # Try to extract values as a list
                    try:
                        if hasattr(row, 'values'):
                            # Row has a values() method (dict-like)
                            row_values = list(row.values())
                        elif hasattr(row, '__iter__') and not isinstance(row, (str, bytes)):
                            # Row is iterable (list/tuple)
                            row_values = list(row)
                        else:
                            # Fallback: wrap in list
                            row_values = [row]
                        data.append(row_values)
                    except Exception as e:
                        print(f"[WARNING] Failed to parse row: {e}, row type: {type(row)}")
                        continue

                # Create DataFrame with explicit columns
                if data:
                    df = pd.DataFrame(data, columns=columns if len(columns) > 0 else None)
                    return df
                else:
                    return pd.DataFrame()
            else:
                # Empty result
                return pd.DataFrame()

        except Exception as e:
            print(f"[ERROR] Turso query failed: {e}")
            print(f"[ERROR] Query: {query}")
            print(f"[ERROR] Params: {params}")
            raise

    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get overall database statistics.

        Returns:
            Dict with keys: total_projects, construction_projects, awarded_projects,
            year_range, categories, statuses
        """
        stats = {}

        # Total projects
        result = self.execute_query("SELECT COUNT(*) as count FROM opportunities")
        stats['total_projects'] = int(result.iloc[0]['count']) if not result.empty else 0

        # Construction projects
        result = self.execute_query("SELECT COUNT(*) as count FROM opportunities WHERE category_code = 'CNST'")
        stats['construction_projects'] = int(result.iloc[0]['count']) if not result.empty else 0

        # Awarded projects
        result = self.execute_query("SELECT COUNT(*) as count FROM opportunities WHERE status_code = 'AWARD'")
        stats['awarded_projects'] = int(result.iloc[0]['count']) if not result.empty else 0

        # Year range
        result = self.execute_query("SELECT MIN(year) as min_year, MAX(year) as max_year FROM opportunities")
        if not result.empty:
            stats['year_range'] = (int(result.iloc[0]['min_year']), int(result.iloc[0]['max_year']))
        else:
            stats['year_range'] = (0, 0)

        # Category breakdown
        result = self.execute_query("""
            SELECT category_code, COUNT(*) as count
            FROM opportunities
            GROUP BY category_code
            ORDER BY count DESC
        """)
        stats['categories'] = dict(zip(result['category_code'], result['count'])) if not result.empty else {}

        # Status breakdown
        result = self.execute_query("""
            SELECT status_code, COUNT(*) as count
            FROM opportunities
            GROUP BY status_code
            ORDER BY count DESC
        """)
        stats['statuses'] = dict(zip(result['status_code'], result['count'])) if not result.empty else {}

        return stats

    def close(self):
        """Close the database connection."""
        if hasattr(self.client, 'close'):
            self.client.close()


def get_database_connection(use_turso: bool = False,
                            database_url: Optional[str] = None,
                            auth_token: Optional[str] = None,
                            local_db_path: Optional[str] = None):
    """
    Factory function to get the appropriate database connection.

    Args:
        use_turso: If True, connect to Turso; if False, use local SQLite
        database_url: Turso database URL (required if use_turso=True)
        auth_token: Turso auth token (required if use_turso=True)
        local_db_path: Path to local SQLite file (required if use_turso=False)

    Returns:
        DatabaseConnection or TursoDatabaseConnection
    """
    if use_turso:
        if not database_url or not auth_token:
            raise ValueError("database_url and auth_token required for Turso connection")
        return TursoDatabaseConnection(database_url, auth_token)
    else:
        # Import local database connection
        from .database import DatabaseConnection
        return DatabaseConnection(db_path=local_db_path)


# Example usage
if __name__ == "__main__":
    """
    Test the Turso database connection.

    NOTE: This requires valid Turso credentials to work.
    """
    import os

    # Try to get credentials from environment
    url = os.getenv('TURSO_DATABASE_URL')
    token = os.getenv('TURSO_AUTH_TOKEN')

    if url and token:
        print("=" * 70)
        print("TESTING TURSO DATABASE CONNECTION")
        print("=" * 70)

        try:
            db = TursoDatabaseConnection(url, token)
            stats = db.get_database_stats()

            print(f"[OK] Connected to Turso database")
            print(f"  Total Projects: {stats['total_projects']:,}")
            print(f"  Construction Projects: {stats['construction_projects']:,}")
            print(f"  Awarded Projects: {stats['awarded_projects']:,}")
            print(f"  Year Range: {stats['year_range'][0]} to {stats['year_range'][1]}")

            print("\n[SUCCESS] Turso connection working!")

        except Exception as e:
            print(f"\n[ERROR] Turso connection failed: {e}")
    else:
        print("Turso credentials not found in environment variables.")
        print("Set TURSO_DATABASE_URL and TURSO_AUTH_TOKEN to test.")
