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
import re
from collections import Counter
import os


def get_smart_database_connection():
    """
    Smart factory function that auto-detects the best database connection.

    Checks in order:
    1. Streamlit secrets (for cloud deployment)
    2. Environment variables (for local config)
    3. Falls back to local SQLite file

    Returns:
        DatabaseConnection or TursoDatabaseConnection

    Usage in Streamlit apps:
        db = get_smart_database_connection()
        queries = ConstructionProjectQueries(db)
    """
    # Try Streamlit secrets first (cloud deployment)
    try:
        import streamlit as st
        if 'database' in st.secrets and st.secrets['database'].get('type') == 'turso':
            # Use Turso cloud database
            from .database_turso import TursoDatabaseConnection
            return TursoDatabaseConnection(
                database_url=st.secrets['turso']['database_url'],
                auth_token=st.secrets['turso']['auth_token']
            )
    except ImportError:
        # Streamlit not available (not running in Streamlit)
        pass
    except (KeyError, AttributeError) as e:
        # Secrets exist but missing required keys
        print(f"[WARNING] Turso secrets configuration error: {e}")
        print(f"[WARNING] Falling back to local database")
        pass
    except Exception as e:
        # Other errors - log and continue
        print(f"[WARNING] Unexpected error accessing Turso secrets: {e}")
        pass

    # Try environment variables (alternative config method)
    turso_url = os.getenv('TURSO_DATABASE_URL')
    turso_token = os.getenv('TURSO_AUTH_TOKEN')
    if turso_url and turso_token:
        from .database_turso import TursoDatabaseConnection
        return TursoDatabaseConnection(turso_url, turso_token)

    # Fall back to local SQLite
    return DatabaseConnection()


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
        region: Optional[str] = None,
        keywords: Optional[str] = None,
        supplier: Optional[str] = None,
        min_bidders: Optional[int] = None,
        max_bidders: Optional[int] = None,
        size_bucket: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get awarded construction projects with optional filters.

        Args:
            limit: Maximum number of results (None = all)
            min_value: Minimum award amount
            max_value: Maximum award amount
            region: Filter by region (partial match)
            keywords: Search keywords in title and description (partial match)
            supplier: Filter projects where this company submitted a bid
            min_bidders: Minimum number of bidders (competition level)
            max_bidders: Maximum number of bidders
            size_bucket: Project size category (Small, Medium, Large, XL)

        Returns:
            pd.DataFrame with project details
        """
        # Handle size buckets
        if size_bucket:
            if size_bucket == "Small (<$500K)":
                max_value = 500000
            elif size_bucket == "Medium ($500K-$2M)":
                min_value = 500000
                max_value = 2000000
            elif size_bucket == "Large ($2M-$10M)":
                min_value = 2000000
                max_value = 10000000
            elif size_bucket == "XL (>$10M)":
                min_value = 10000000
                max_value = None

        query = """
            SELECT
                o.reference_number,
                o.short_title,
                o.description,
                o.actual_value,
                o.num_bidders,
                o.region,
                o.post_date,
                o.close_date,
                o.awarded_on,
                o.delivery_start_date,
                o.delivery_end_date,
                o.solicitation_type
            FROM opportunities o
            WHERE o.category_code = 'CNST'
              AND o.status_code = 'AWARD'
        """

        params = []

        # Supplier filter (join with bidders table)
        if supplier is not None:
            query = query.replace(
                "FROM opportunities o",
                """FROM opportunities o
                INNER JOIN bidders b ON o.reference_number = b.opportunity_ref"""
            )
            query += " AND b.company_name = ?"
            params.append(supplier)

        if min_value is not None:
            query += " AND o.actual_value >= ?"
            params.append(min_value)

        if max_value is not None:
            query += " AND o.actual_value <= ?"
            params.append(max_value)

        if region is not None:
            query += " AND o.region LIKE ?"
            params.append(f"%{region}%")

        if keywords is not None:
            query += " AND (o.short_title LIKE ? OR o.description LIKE ?)"
            keyword_pattern = f"%{keywords}%"
            params.append(keyword_pattern)
            params.append(keyword_pattern)

        if min_bidders is not None:
            query += " AND o.num_bidders >= ?"
            params.append(min_bidders)

        if max_bidders is not None:
            query += " AND o.num_bidders <= ?"
            params.append(max_bidders)

        query += " ORDER BY o.awarded_on DESC"

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

    def get_unique_regions(self) -> List[str]:
        """
        Get all unique regions/cities from awarded construction projects.

        Returns:
            List of unique region names, sorted alphabetically
        """
        query = """
            SELECT DISTINCT region
            FROM opportunities
            WHERE category_code = 'CNST'
              AND status_code = 'AWARD'
              AND region IS NOT NULL
              AND region != ''
            ORDER BY region
        """
        result = self.db.execute_query(query)
        return result['region'].tolist() if not result.empty else []

    def get_common_keywords(self, limit: int = 100) -> List[str]:
        """
        Extract common keywords from construction project titles.

        Args:
            limit: Maximum number of keywords to extract before sorting

        Returns:
            List of common keywords, sorted alphabetically
        """
        query = """
            SELECT short_title
            FROM opportunities
            WHERE category_code = 'CNST'
              AND status_code = 'AWARD'
              AND short_title IS NOT NULL
        """
        result = self.db.execute_query(query)

        if result.empty:
            return []

        # Common stop words to exclude
        stop_words = {
            'the', 'and', 'for', 'of', 'in', 'to', 'a', 'an', 'is', 'at', 'by',
            'on', 'with', 'from', 'as', 'or', 'be', 'are', 'was', 'were', 'will',
            'project', 'projects', 'work', 'works', 'construction', 'phase',
            '2025', '2024', '2023', 'rfq', 'rfp', 'tender'
        }

        all_words = []
        for title in result['short_title']:
            if pd.notna(title):
                # Extract words (alphanumeric, keeping hyphens)
                words = re.findall(r'\b[a-zA-Z][\w-]*\b', str(title).lower())
                # Filter out stop words and very short words
                words = [w for w in words if len(w) > 3 and w not in stop_words]
                all_words.extend(words)

        # Count occurrences and get most common
        word_counts = Counter(all_words)
        # Get top keywords by frequency, then sort alphabetically
        common_keywords = [word for word, count in word_counts.most_common(limit)]
        common_keywords.sort()  # Sort alphabetically

        return common_keywords

    def get_all_suppliers(self) -> List[str]:
        """
        Get all unique supplier/company names that have submitted bids.

        Returns:
            List of unique supplier names, sorted alphabetically
        """
        query = """
            SELECT DISTINCT company_name
            FROM bidders
            WHERE company_name IS NOT NULL
              AND company_name != ''
            ORDER BY company_name
        """
        result = self.db.execute_query(query)
        return result['company_name'].tolist() if not result.empty else []

    def get_supplier_stats(self, company_name: str) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a specific supplier.

        Args:
            company_name: Name of the supplier/company

        Returns:
            Dict with bid statistics, win rate, typical bid behavior
        """
        # Get all bids by this supplier
        bids_query = """
            SELECT
                b.bid_amount,
                b.is_winner,
                b.opportunity_ref,
                o.actual_value,
                o.awarded_on,
                o.region,
                o.short_title
            FROM bidders b
            JOIN opportunities o ON b.opportunity_ref = o.reference_number
            WHERE b.company_name = ?
              AND o.category_code = 'CNST'
            ORDER BY o.awarded_on DESC
        """
        bids = self.db.execute_query(bids_query, (company_name,))

        stats = {
            'total_bids': len(bids),
            'wins': 0,
            'losses': 0,
            'win_rate': 0.0,
            'total_won_value': 0.0,
            'avg_bid_amount': 0.0,
            'regions': [],
            'recent_projects': []
        }

        if bids.empty:
            return stats

        # Calculate statistics
        stats['wins'] = bids['is_winner'].sum()
        stats['losses'] = len(bids) - stats['wins']
        stats['win_rate'] = (stats['wins'] / len(bids) * 100) if len(bids) > 0 else 0.0

        # Total value won
        won_bids = bids[bids['is_winner'] == True]
        if not won_bids.empty:
            stats['total_won_value'] = won_bids['actual_value'].sum()

        # Average bid amount
        if 'bid_amount' in bids.columns:
            stats['avg_bid_amount'] = bids['bid_amount'].mean()

        # Active regions
        if 'region' in bids.columns:
            region_counts = bids['region'].value_counts()
            stats['regions'] = region_counts.head(5).to_dict()

        # Recent projects (last 5)
        stats['recent_projects'] = bids.head(5).to_dict('records')

        return stats

    def get_interested_suppliers(self, reference_number: str) -> pd.DataFrame:
        """
        Get all companies that viewed a project (interested) but may not have bid.

        Args:
            reference_number: Project reference number

        Returns:
            DataFrame with interested supplier information
        """
        query = """
            SELECT
                business_name,
                city,
                province,
                country,
                description
            FROM interested_suppliers
            WHERE opportunity_ref = ?
            ORDER BY business_name
        """
        return self.db.execute_query(query, (reference_number,))

    def get_projects_for_similarity(self) -> pd.DataFrame:
        """
        Get all awarded construction projects with text for similarity analysis.

        Returns:
            DataFrame with reference_number, short_title, description, actual_value, region
        """
        query = """
            SELECT
                reference_number,
                short_title,
                description,
                actual_value,
                region,
                awarded_on
            FROM opportunities
            WHERE category_code = 'CNST'
              AND status_code = 'AWARD'
              AND short_title IS NOT NULL
            ORDER BY awarded_on DESC
        """
        return self.db.execute_query(query)

    def get_project_details_for_similarity(self, reference_number: str) -> Dict[str, Any]:
        """
        Get comprehensive project details for similarity comparison.

        Args:
            reference_number: Project reference number

        Returns:
            Dictionary with project details including bids
        """
        # Get project info
        project_query = """
            SELECT
                reference_number,
                short_title,
                description,
                actual_value,
                region,
                awarded_on
            FROM opportunities
            WHERE reference_number = ?
        """
        project_df = self.db.execute_query(project_query, (reference_number,))

        if project_df.empty:
            return None

        # Get bids for context
        bids_query = """
            SELECT
                company_name,
                bid_amount,
                is_winner
            FROM bidders
            WHERE opportunity_ref = ?
            ORDER BY bid_amount
        """
        bids_df = self.db.execute_query(bids_query, (reference_number,))

        return {
            'project': project_df.iloc[0].to_dict(),
            'bids': bids_df.to_dict('records'),
            'num_bids': len(bids_df)
        }

    def get_training_data_for_prediction(self) -> pd.DataFrame:
        """
        Get training data for machine learning bid prediction.

        Returns:
            DataFrame with project features and actual award values
        """
        query = """
            SELECT
                o.reference_number,
                o.short_title,
                o.description,
                o.actual_value,
                o.region,
                o.awarded_on,
                COUNT(b.id) as num_bidders,
                MIN(b.bid_amount) as lowest_bid,
                MAX(b.bid_amount) as highest_bid,
                AVG(b.bid_amount) as average_bid
            FROM opportunities o
            LEFT JOIN bidders b ON o.reference_number = b.opportunity_ref
            WHERE o.category_code = 'CNST'
              AND o.status_code = 'AWARD'
              AND o.actual_value > 0
            GROUP BY o.reference_number
            HAVING num_bidders > 0
            ORDER BY o.awarded_on DESC
        """
        return self.db.execute_query(query)

    def get_competitive_landscape(
        self,
        keywords: Optional[List[str]] = None,
        region: Optional[str] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        limit: int = 20
    ) -> pd.DataFrame:
        """
        Get competitive landscape analysis - who typically bids on similar projects.

        Args:
            keywords: Keywords to match in project title/description
            region: Region filter
            min_value: Minimum project value
            max_value: Maximum project value
            limit: Max number of competitors to return

        Returns:
            DataFrame with supplier names, bid counts, win rates
        """
        query = """
            SELECT
                b.company_name,
                COUNT(*) as total_bids,
                SUM(CASE WHEN b.is_winner = 1 THEN 1 ELSE 0 END) as wins,
                ROUND(100.0 * SUM(CASE WHEN b.is_winner = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as win_rate,
                AVG(b.bid_amount) as avg_bid_amount,
                MIN(o.awarded_on) as first_bid_date,
                MAX(o.awarded_on) as last_bid_date
            FROM bidders b
            JOIN opportunities o ON b.opportunity_ref = o.reference_number
            WHERE o.category_code = 'CNST'
              AND o.status_code = 'AWARD'
              AND b.company_name IS NOT NULL
              AND b.company_name != ''
        """

        params = []

        # Add filters
        if keywords:
            keyword_conditions = []
            for keyword in keywords:
                keyword_conditions.append("(o.short_title LIKE ? OR o.description LIKE ?)")
                params.extend([f"%{keyword}%", f"%{keyword}%"])
            query += " AND (" + " OR ".join(keyword_conditions) + ")"

        if region:
            query += " AND o.region LIKE ?"
            params.append(f"%{region}%")

        if min_value is not None:
            query += " AND o.actual_value >= ?"
            params.append(min_value)

        if max_value is not None:
            query += " AND o.actual_value <= ?"
            params.append(max_value)

        query += """
            GROUP BY b.company_name
            HAVING total_bids >= 2
            ORDER BY total_bids DESC, win_rate DESC
            LIMIT ?
        """
        params.append(limit)

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