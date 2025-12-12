"""
Competitor Analysis Queries
============================
Database queries for competitor intelligence and analysis.

Author: BCXV Construction Analytics
Date: 2025-12-11
"""

import pandas as pd
from typing import Optional, List, Dict, Any


class CompetitorQueries:
    """Queries for analyzing bidders and competitors."""

    def __init__(self, db):
        """
        Initialize with database connection.

        Args:
            db: DatabaseConnection or TursoDatabaseConnection instance
        """
        self.db = db

    def get_market_overview(self) -> Dict[str, Any]:
        """
        Get high-level market statistics.

        Returns:
            Dict with market overview metrics
        """
        stats = {}

        # Total unique companies (bidders)
        query = "SELECT COUNT(DISTINCT company_name) as count FROM bidders WHERE company_name IS NOT NULL"
        result = self.db.execute_query(query)
        stats['total_companies'] = int(result.iloc[0]['count']) if not result.empty else 0

        # Total bids placed
        query = "SELECT COUNT(*) as count FROM bidders WHERE company_name IS NOT NULL"
        result = self.db.execute_query(query)
        stats['total_bids'] = int(result.iloc[0]['count']) if not result.empty else 0

        # Total awards won
        query = "SELECT COUNT(*) as count FROM bidders WHERE is_winner = 1"
        result = self.db.execute_query(query)
        stats['total_awards'] = int(result.iloc[0]['count']) if not result.empty else 0

        # Average win rate
        if stats['total_bids'] > 0:
            stats['avg_win_rate'] = (stats['total_awards'] / stats['total_bids']) * 100
        else:
            stats['avg_win_rate'] = 0.0

        # Total unique interested suppliers
        query = "SELECT COUNT(DISTINCT business_name) as count FROM interested_suppliers WHERE business_name IS NOT NULL"
        result = self.db.execute_query(query)
        stats['total_interested_suppliers'] = int(result.iloc[0]['count']) if not result.empty else 0

        return stats

    def get_all_companies(self, min_bids: int = 1) -> pd.DataFrame:
        """
        Get list of all companies with bid counts.

        Args:
            min_bids: Minimum number of bids to include company

        Returns:
            DataFrame with company names and bid counts
        """
        query = f"""
            SELECT
                company_name,
                COUNT(*) as bid_count
            FROM bidders
            WHERE company_name IS NOT NULL
            GROUP BY company_name
            HAVING COUNT(*) >= {min_bids}
            ORDER BY bid_count DESC
        """
        return self.db.execute_query(query)

    def get_company_summary_stats(self, company_name: str) -> Dict[str, Any]:
        """
        Get summary statistics for a specific company.

        Args:
            company_name: Name of the company

        Returns:
            Dict with company statistics
        """
        query = """
            SELECT
                COUNT(*) as total_bids,
                SUM(CASE WHEN is_winner = 1 THEN 1 ELSE 0 END) as wins,
                AVG(bid_amount) as avg_bid,
                MIN(bid_amount) as min_bid,
                MAX(bid_amount) as max_bid,
                SUM(CASE WHEN is_winner = 1 THEN bid_amount ELSE 0 END) as total_won_value
            FROM bidders
            WHERE company_name = ?
        """
        result = self.db.execute_query(query, (company_name,))

        if result.empty:
            return {}

        row = result.iloc[0]
        stats = {
            'total_bids': int(row['total_bids']) if pd.notna(row['total_bids']) else 0,
            'wins': int(row['wins']) if pd.notna(row['wins']) else 0,
            'avg_bid': float(row['avg_bid']) if pd.notna(row['avg_bid']) else 0.0,
            'min_bid': float(row['min_bid']) if pd.notna(row['min_bid']) else 0.0,
            'max_bid': float(row['max_bid']) if pd.notna(row['max_bid']) else 0.0,
            'total_won_value': float(row['total_won_value']) if pd.notna(row['total_won_value']) else 0.0,
        }

        # Calculate win rate
        if stats['total_bids'] > 0:
            stats['win_rate'] = (stats['wins'] / stats['total_bids']) * 100
        else:
            stats['win_rate'] = 0.0

        return stats

    def get_top_bidders(self, limit: int = 20, sort_by: str = 'bids') -> pd.DataFrame:
        """
        Get top companies by various metrics.

        Args:
            limit: Number of companies to return
            sort_by: Sort criteria ('bids', 'wins', 'win_rate', 'value')

        Returns:
            DataFrame with top companies
        """
        query = """
            SELECT
                company_name,
                COUNT(*) as total_bids,
                SUM(CASE WHEN is_winner = 1 THEN 1 ELSE 0 END) as wins,
                ROUND(AVG(bid_amount), 2) as avg_bid,
                ROUND(SUM(CASE WHEN is_winner = 1 THEN bid_amount ELSE 0 END), 2) as total_value
            FROM bidders
            WHERE company_name IS NOT NULL
            GROUP BY company_name
            HAVING COUNT(*) >= 3
        """

        df = self.db.execute_query(query)

        if df.empty:
            return df

        # Calculate win rate
        df['win_rate'] = (df['wins'] / df['total_bids'] * 100).round(1)

        # Sort based on criteria
        if sort_by == 'wins':
            df = df.sort_values('wins', ascending=False)
        elif sort_by == 'win_rate':
            df = df.sort_values('win_rate', ascending=False)
        elif sort_by == 'value':
            df = df.sort_values('total_value', ascending=False)
        else:  # Default to bids
            df = df.sort_values('total_bids', ascending=False)

        return df.head(limit)

    def get_company_bidding_history(
        self,
        company_name: str,
        category: Optional[str] = None,
        year: Optional[int] = None,
        status: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get detailed bidding history for a company.

        Args:
            company_name: Name of the company
            category: Filter by category code (optional)
            year: Filter by year (optional)
            status: Filter by status code (optional)

        Returns:
            DataFrame with bidding history
        """
        query = """
            SELECT
                o.reference_number,
                o.short_title,
                o.category_code,
                o.region,
                o.status_code,
                o.close_date,
                o.awarded_on,
                o.actual_value,
                o.year,
                b.bid_amount,
                b.is_winner
            FROM bidders b
            JOIN opportunities o ON b.opportunity_ref = o.reference_number
            WHERE b.company_name = ?
        """

        params = [company_name]

        if category:
            query += " AND o.category_code = ?"
            params.append(category)

        if year:
            query += " AND o.year = ?"
            params.append(year)

        if status:
            query += " AND o.status_code = ?"
            params.append(status)

        query += " ORDER BY o.close_date DESC"

        return self.db.execute_query(query, tuple(params))

    def get_win_rate_by_category(self, company_name: str) -> pd.DataFrame:
        """
        Get win rate breakdown by category for a company.

        Args:
            company_name: Name of the company

        Returns:
            DataFrame with category breakdown
        """
        query = """
            SELECT
                o.category_code,
                COUNT(*) as bids,
                SUM(CASE WHEN b.is_winner = 1 THEN 1 ELSE 0 END) as wins,
                ROUND(AVG(b.bid_amount), 2) as avg_bid
            FROM bidders b
            JOIN opportunities o ON b.opportunity_ref = o.reference_number
            WHERE b.company_name = ?
            GROUP BY o.category_code
            ORDER BY bids DESC
        """

        df = self.db.execute_query(query, (company_name,))

        if not df.empty:
            df['win_rate'] = (df['wins'] / df['bids'] * 100).round(1)

        return df

    def get_win_rate_by_year(self, company_name: str) -> pd.DataFrame:
        """
        Get win rate over time for a company.

        Args:
            company_name: Name of the company

        Returns:
            DataFrame with yearly breakdown
        """
        query = """
            SELECT
                o.year,
                COUNT(*) as bids,
                SUM(CASE WHEN b.is_winner = 1 THEN 1 ELSE 0 END) as wins,
                ROUND(AVG(b.bid_amount), 2) as avg_bid
            FROM bidders b
            JOIN opportunities o ON b.opportunity_ref = o.reference_number
            WHERE b.company_name = ?
            GROUP BY o.year
            ORDER BY o.year DESC
        """

        df = self.db.execute_query(query, (company_name,))

        if not df.empty:
            df['win_rate'] = (df['wins'] / df['bids'] * 100).round(1)

        return df

    def get_head_to_head(self, company_a: str, company_b: str) -> pd.DataFrame:
        """
        Get projects where two companies competed directly.

        Args:
            company_a: First company name
            company_b: Second company name

        Returns:
            DataFrame with head-to-head competitions
        """
        query = """
            SELECT
                o.reference_number,
                o.short_title,
                o.category_code,
                o.close_date,
                o.actual_value,
                b1.bid_amount as company_a_bid,
                b2.bid_amount as company_b_bid,
                b1.is_winner as company_a_won,
                b2.is_winner as company_b_won
            FROM bidders b1
            JOIN bidders b2 ON b1.opportunity_ref = b2.opportunity_ref
            JOIN opportunities o ON b1.opportunity_ref = o.reference_number
            WHERE b1.company_name = ?
              AND b2.company_name = ?
              AND b1.company_name != b2.company_name
            ORDER BY o.close_date DESC
        """

        return self.db.execute_query(query, (company_a, company_b))

    def get_head_to_head_summary(self, company_a: str, company_b: str) -> Dict[str, Any]:
        """
        Get summary statistics for head-to-head competition.

        Args:
            company_a: First company name
            company_b: Second company name

        Returns:
            Dict with head-to-head statistics
        """
        df = self.get_head_to_head(company_a, company_b)

        if df.empty:
            return {
                'total_competitions': 0,
                'company_a_wins': 0,
                'company_b_wins': 0,
                'company_a_avg_bid': 0.0,
                'company_b_avg_bid': 0.0,
            }

        return {
            'total_competitions': len(df),
            'company_a_wins': int(df['company_a_won'].sum()),
            'company_b_wins': int(df['company_b_won'].sum()),
            'company_a_avg_bid': float(df['company_a_bid'].mean()) if pd.notna(df['company_a_bid'].mean()) else 0.0,
            'company_b_avg_bid': float(df['company_b_bid'].mean()) if pd.notna(df['company_b_bid'].mean()) else 0.0,
        }

    def get_interested_suppliers_stats(self, business_name: str) -> Dict[str, Any]:
        """
        Get statistics for interested suppliers (non-bidders).

        Args:
            business_name: Name of the supplier

        Returns:
            Dict with supplier statistics
        """
        query = """
            SELECT
                COUNT(*) as total_interests,
                COUNT(DISTINCT city) as cities,
                MIN(o.post_date) as first_interest,
                MAX(o.post_date) as last_interest
            FROM interested_suppliers i
            JOIN opportunities o ON i.opportunity_ref = o.reference_number
            WHERE i.business_name = ?
        """

        result = self.db.execute_query(query, (business_name,))

        if result.empty:
            return {}

        row = result.iloc[0]
        return {
            'total_interests': int(row['total_interests']) if pd.notna(row['total_interests']) else 0,
            'cities': int(row['cities']) if pd.notna(row['cities']) else 0,
            'first_interest': row['first_interest'],
            'last_interest': row['last_interest'],
        }

    def get_company_regional_focus(self, company_name: str) -> pd.DataFrame:
        """
        Get regional distribution of bids for a company.

        Args:
            company_name: Name of the company

        Returns:
            DataFrame with regional breakdown
        """
        query = """
            SELECT
                o.region,
                COUNT(*) as bids,
                SUM(CASE WHEN b.is_winner = 1 THEN 1 ELSE 0 END) as wins
            FROM bidders b
            JOIN opportunities o ON b.opportunity_ref = o.reference_number
            WHERE b.company_name = ?
              AND o.region IS NOT NULL
            GROUP BY o.region
            ORDER BY bids DESC
        """

        df = self.db.execute_query(query, (company_name,))

        if not df.empty:
            df['win_rate'] = (df['wins'] / df['bids'] * 100).round(1)

        return df

    def search_companies(self, search_term: str, limit: int = 50) -> List[str]:
        """
        Search for companies by name (for autocomplete).

        Args:
            search_term: Search string
            limit: Maximum results to return

        Returns:
            List of matching company names
        """
        query = f"""
            SELECT DISTINCT company_name
            FROM bidders
            WHERE company_name LIKE ?
              AND company_name IS NOT NULL
            GROUP BY company_name
            HAVING COUNT(*) >= 3
            ORDER BY company_name
            LIMIT {limit}
        """

        df = self.db.execute_query(query, (f'%{search_term}%',))

        if df.empty:
            return []

        return df['company_name'].tolist()

    # Alias methods for consistency
    def get_company_win_rate_by_category(self, company_name: str) -> pd.DataFrame:
        """Alias for get_win_rate_by_category."""
        df = self.get_win_rate_by_category(company_name)

        if not df.empty:
            # Add percentage column for UI
            total_bids = df['bids'].sum()
            df['percentage'] = (df['bids'] / total_bids * 100).round(1)
            # Rename for consistency
            df = df.rename(columns={'bids': 'total_bids'})

        return df

    def get_company_win_rate_by_year(self, company_name: str) -> pd.DataFrame:
        """Alias for get_win_rate_by_year."""
        df = self.get_win_rate_by_year(company_name)

        if not df.empty:
            # Rename for consistency
            df = df.rename(columns={'bids': 'total_bids'})

        return df

    def get_company_win_rate_by_region(self, company_name: str) -> pd.DataFrame:
        """Alias for get_company_regional_focus."""
        df = self.get_company_regional_focus(company_name)

        if not df.empty:
            # Add percentage column for UI
            total_bids = df['bids'].sum()
            df['percentage'] = (df['bids'] / total_bids * 100).round(1)
            # Rename for consistency
            df = df.rename(columns={'bids': 'total_bids'})

        return df
