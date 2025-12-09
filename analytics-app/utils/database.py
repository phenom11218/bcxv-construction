"""
Database Utility Module
========================
Provides connection and query utilities for the Alberta Procurement SQLite database.

This module connects to the scraped procurement data and provides helper functions
for retrieving construction projects, bids, and related information.

Author: BCXV Construction Analytics
Date: 2025-12-08
Phase: 1 - Project Setup
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd


class DatabaseConnection:
    """
    Manages SQLite database connection for Alberta Procurement data.

    The database is located in the parent scraper project folder.
    It contains 8 tables with comprehensive procurement data from 2025.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database. If None, uses default location
                    in the parent scraper folder.
        """
        if db_path is None:
            # Default: look for database in project root
            # From analytics-app/utils/ -> ../../alberta_procurement.db
            default_path = Path(__file__).parent.parent.parent / "alberta_procurement.db"
            self.db_path = str(default_path)
        else:
            self.db_path = db_path

        # Verify database exists
        if not Path(self.db_path).exists():
            raise FileNotFoundError(
                f"Database not found at {self.db_path}\n"
                f"Please ensure the Alberta Procurement database has been scraped."
            )

    def get_connection(self) -> sqlite3.Connection:
        """
        Get a new database connection.

        Returns:
            sqlite3.Connection: Database connection object
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn

    def execute_query(self, query: str, params: tuple = ()) -> pd.DataFrame:
        """
        Execute a SQL query and return results as a pandas DataFrame.

        Args:
            query: SQL query string
            params: Query parameters (for prepared statements)

        Returns:
            pd.DataFrame: Query results
        """
        conn = self.get_connection()
        try:
            df = pd.read_sql_query(query, conn, params=params)
            return df
        finally:
            conn.close()

    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get overall database statistics.

        Returns:
            Dict with keys: total_projects, construction_projects, awarded_projects,
            year_range, categories, statuses
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        stats = {}

        # Total projects
        cursor.execute("SELECT COUNT(*) FROM opportunities")
        stats['total_projects'] = cursor.fetchone()[0]

        # Construction projects
        cursor.execute("SELECT COUNT(*) FROM opportunities WHERE category_code = 'CNST'")
        stats['construction_projects'] = cursor.fetchone()[0]

        # Awarded projects
        cursor.execute("SELECT COUNT(*) FROM opportunities WHERE status_code = 'AWARD'")
        stats['awarded_projects'] = cursor.fetchone()[0]

        # Year range
        cursor.execute("SELECT MIN(year), MAX(year) FROM opportunities")
        year_range = cursor.fetchone()
        stats['year_range'] = (year_range[0], year_range[1])

        # Category breakdown
        cursor.execute("""
            SELECT category_code, COUNT(*) as count
            FROM opportunities
            GROUP BY category_code
            ORDER BY count DESC
        """)
        stats['categories'] = {row[0]: row[1] for row in cursor.fetchall()}

        # Status breakdown
        cursor.execute("""
            SELECT status_code, COUNT(*) as count
            FROM opportunities
            GROUP BY status_code
            ORDER BY count DESC
        """)
        stats['statuses'] = {row[0]: row[1] for row in cursor.fetchall()}

        conn.close()
        return stats


class ConstructionProjectQueries:
    """
    Specialized queries for construction project data.

    This class provides high-level query methods specifically for construction
    bid analysis and prediction.
    """

    def __init__(self, db: DatabaseConnection):
        """
        Initialize with a database connection.

        Args:
            db: DatabaseConnection instance
        """
        self.db = db

    def get_awarded_construction_projects(
        self,
        limit: Optional[int] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        region: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get awarded construction projects with optional filters.

        Args:
            limit: Maximum number of results (None = all)
            min_value: Minimum award amount
            max_value: Maximum award amount
            region: Filter by region (partial match)

        Returns:
            pd.DataFrame with columns: reference_number, short_title, description,
            actual_value, num_bidders, region, post_date, close_date, awarded_on,
            delivery_start_date, delivery_end_date
        """
        query = """
            SELECT
                reference_number,
                short_title,
                description,
                actual_value,
                num_bidders,
                region,
                post_date,
                close_date,
                awarded_on,
                delivery_start_date,
                delivery_end_date,
                solicitation_type
            FROM opportunities
            WHERE category_code = 'CNST'
              AND status_code = 'AWARD'
        """

        params = []

        if min_value is not None:
            query += " AND actual_value >= ?"
            params.append(min_value)

        if max_value is not None:
            query += " AND actual_value <= ?"
            params.append(max_value)

        if region is not None:
            query += " AND region LIKE ?"
            params.append(f"%{region}%")

        query += " ORDER BY awarded_on DESC"

        if limit is not None:
            query += f" LIMIT {limit}"

        return self.db.execute_query(query, tuple(params))

    def get_project_with_bids(self, reference_number: str) -> Dict[str, Any]:
        """
        Get complete project details including all bids.

        Args:
            reference_number: Project reference (e.g., 'AB-2025-00025')

        Returns:
            Dict with keys: 'project' (DataFrame), 'bids' (DataFrame),
            'award' (DataFrame), 'stats' (Dict)
        """
        # Get project details
        project_query = """
            SELECT * FROM opportunities
            WHERE reference_number = ?
        """
        project = self.db.execute_query(project_query, (reference_number,))

        # Get all bids
        bids_query = """
            SELECT
                company_name,
                bid_amount,
                is_winner,
                city,
                contact_name,
                contact_email,
                contact_phone
            FROM bidders
            WHERE opportunity_ref = ?
            ORDER BY bid_amount ASC
        """
        bids = self.db.execute_query(bids_query, (reference_number,))

        # Get award details
        award_query = """
            SELECT
                winner_name,
                award_amount,
                award_date,
                city,
                province
            FROM awards
            WHERE opportunity_ref = ?
        """
        award = self.db.execute_query(award_query, (reference_number,))

        # Calculate bid statistics if bids exist
        stats = {}
        if not bids.empty and 'bid_amount' in bids.columns:
            bid_amounts = bids['bid_amount'].dropna()
            if not bid_amounts.empty:
                stats['num_bids'] = len(bid_amounts)
                stats['lowest_bid'] = bid_amounts.min()
                stats['highest_bid'] = bid_amounts.max()
                stats['average_bid'] = bid_amounts.mean()
                stats['bid_spread'] = stats['highest_bid'] - stats['lowest_bid']

                # Win margin (if award amount available)
                if not award.empty and 'award_amount' in award.columns:
                    award_amount = award['award_amount'].iloc[0]
                    if pd.notna(award_amount):
                        stats['win_margin_from_avg'] = award_amount - stats['average_bid']
                        stats['win_margin_pct'] = (stats['win_margin_from_avg'] / stats['average_bid']) * 100

        return {
            'project': project,
            'bids': bids,
            'award': award,
            'stats': stats
        }

    def get_projects_with_bid_data(self, limit: Optional[int] = None) -> pd.DataFrame:
        """
        Get all awarded construction projects that have actual bid amount data.

        This is the subset of projects most useful for ML training (only ~172 projects).

        Args:
            limit: Maximum number of results

        Returns:
            pd.DataFrame with project and bid statistics
        """
        query = """
            SELECT
                o.reference_number,
                o.short_title,
                o.description,
                o.actual_value,
                o.region,
                o.delivery_start_date,
                o.delivery_end_date,
                COUNT(DISTINCT b.id) as num_bids,
                MIN(b.bid_amount) as lowest_bid,
                MAX(b.bid_amount) as highest_bid,
                AVG(b.bid_amount) as avg_bid,
                (MAX(b.bid_amount) - MIN(b.bid_amount)) as bid_spread
            FROM opportunities o
            INNER JOIN bidders b ON o.reference_number = b.opportunity_ref
            WHERE o.category_code = 'CNST'
              AND o.status_code = 'AWARD'
              AND b.bid_amount IS NOT NULL
            GROUP BY o.reference_number
            HAVING num_bids > 0
            ORDER BY o.actual_value DESC
        """

        if limit is not None:
            query += f" LIMIT {limit}"

        return self.db.execute_query(query)

    def search_projects_by_keywords(
        self,
        keywords: List[str],
        category: str = 'CNST',
        status: str = 'AWARD'
    ) -> pd.DataFrame:
        """
        Search for projects matching any of the provided keywords in title or description.

        Args:
            keywords: List of keywords to search for (e.g., ['road', 'bridge', 'paving'])
            category: Category code (default: 'CNST')
            status: Status code (default: 'AWARD')

        Returns:
            pd.DataFrame of matching projects
        """
        # Build LIKE clause for each keyword
        keyword_conditions = []
        params = []

        for keyword in keywords:
            keyword_conditions.append(
                "(short_title LIKE ? OR description LIKE ?)"
            )
            params.extend([f"%{keyword}%", f"%{keyword}%"])

        keyword_clause = " OR ".join(keyword_conditions)

        query = f"""
            SELECT
                reference_number,
                short_title,
                description,
                actual_value,
                num_bidders,
                region,
                awarded_on
            FROM opportunities
            WHERE category_code = ?
              AND status_code = ?
              AND ({keyword_clause})
            ORDER BY actual_value DESC
        """

        params = [category, status] + params

        return self.db.execute_query(query, tuple(params))


# Example usage and testing
if __name__ == "__main__":
    """
    Test the database connection and queries.
    Run this file directly to verify everything works.
    """
    print("=" * 80)
    print("TESTING DATABASE CONNECTION")
    print("=" * 80)

    try:
        # Initialize database
        db = DatabaseConnection()
        print(f"[OK] Connected to database: {db.db_path}")

        # Get stats
        stats = db.get_database_stats()
        print(f"\n[OK] Database Statistics:")
        print(f"  Total Projects: {stats['total_projects']:,}")
        print(f"  Construction Projects: {stats['construction_projects']:,}")
        print(f"  Awarded Projects: {stats['awarded_projects']:,}")
        print(f"  Year Range: {stats['year_range'][0]} to {stats['year_range'][1]}")

        # Test construction queries
        queries = ConstructionProjectQueries(db)

        # Get sample projects
        print(f"\n[OK] Testing Construction Queries:")
        projects = queries.get_awarded_construction_projects(limit=5)
        print(f"  Retrieved {len(projects)} sample awarded construction projects")

        # Get projects with bid data
        bid_projects = queries.get_projects_with_bid_data(limit=5)
        print(f"  Retrieved {len(bid_projects)} projects with bid data")

        # Test keyword search
        road_projects = queries.search_projects_by_keywords(['road', 'highway'])
        print(f"  Found {len(road_projects)} road/highway projects")

        print("\n" + "=" * 80)
        print("ALL TESTS PASSED [SUCCESS]")
        print("=" * 80)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()