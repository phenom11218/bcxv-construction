"""
API Fetcher Module
==================
Fetches project data from the Alberta Purchasing API for real-time project analysis.

This module allows the analytics app to fetch projects that may not be in the
local database yet, enabling analysis of any Alberta procurement project.

Author: BCXV Construction Analytics
Date: 2025-12-10
Phase: 3 - Enhanced Similar Projects Feature
"""

import requests
import re
from typing import Optional, Dict, Any, Tuple
from datetime import datetime


class AlbertaAPIFetcher:
    """
    Fetches project data from Alberta Purchasing API.

    Supports:
    - Direct reference number input (e.g., "AB-2024-10281")
    - Full URLs (e.g., "https://purchasing.alberta.ca/posting/AB-2024-10281")
    - Real-time API fetching with error handling
    """

    API_BASE = "https://purchasing.alberta.ca/api/opportunity/public"

    def __init__(self):
        """Initialize API fetcher with session."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        })

    @staticmethod
    def parse_reference_number(input_str: str) -> Optional[Tuple[int, int]]:
        """
        Parse a reference number or URL to extract year and posting ID.

        Args:
            input_str: Can be:
                - Reference number: "AB-2024-10281"
                - Full URL: "https://purchasing.alberta.ca/posting/AB-2024-10281"
                - Partial URL: "purchasing.alberta.ca/posting/AB-2024-10281"

        Returns:
            Tuple of (year, posting_id) or None if parsing fails

        Examples:
            >>> parse_reference_number("AB-2024-10281")
            (2024, 10281)
            >>> parse_reference_number("https://purchasing.alberta.ca/posting/AB-2024-10281")
            (2024, 10281)
        """
        # Clean up the input
        input_str = input_str.strip()

        # Try to extract AB-YYYY-NNNNN pattern
        pattern = r'AB-(\d{4})-(\d{5})'
        match = re.search(pattern, input_str)

        if match:
            year = int(match.group(1))
            posting_id = int(match.group(2))
            return (year, posting_id)

        return None

    def fetch_project(self, year: int, posting_id: int) -> Tuple[Optional[Dict[str, Any]], int, Optional[str]]:
        """
        Fetch a project from the Alberta Purchasing API.

        Args:
            year: Year (e.g., 2024)
            posting_id: Posting ID (e.g., 10281)

        Returns:
            Tuple of (project_data, http_status, error_message)
            - project_data: Dict with full project JSON if successful, None otherwise
            - http_status: HTTP status code (200, 404, etc.)
            - error_message: Human-readable error message if failed, None if successful
        """
        url = f"{self.API_BASE}/{year}/{posting_id}"

        try:
            response = self.session.get(url, timeout=30)

            if response.status_code == 200:
                # Success!
                data = response.json()
                return (data, 200, None)

            elif response.status_code == 404:
                # Project not found
                return (None, 404, f"Project AB-{year}-{posting_id:05d} not found in Alberta Purchasing system")

            elif response.status_code == 403 or response.status_code == 503:
                # Cloudflare blocking or rate limiting
                return (None, response.status_code,
                       "Unable to access Alberta Purchasing API. The site may have rate limiting or access restrictions.")

            else:
                # Other HTTP error
                return (None, response.status_code,
                       f"API returned HTTP {response.status_code}. Please try again later.")

        except requests.Timeout:
            return (None, 0, "Request timed out. The Alberta Purchasing API may be slow or unavailable.")

        except requests.ConnectionError:
            return (None, 0, "Could not connect to Alberta Purchasing API. Check your internet connection.")

        except requests.RequestException as e:
            return (None, 0, f"Request failed: {str(e)}")

        except Exception as e:
            return (None, 0, f"Unexpected error: {str(e)}")

    def fetch_by_reference(self, reference_input: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Fetch a project by reference number or URL.

        This is the main convenience method for the Similar Projects feature.

        Args:
            reference_input: Reference number or URL (e.g., "AB-2024-10281" or full URL)

        Returns:
            Tuple of (project_data, error_message)
            - project_data: Full project JSON if successful, None otherwise
            - error_message: Human-readable error if failed, None if successful
        """
        # Parse the input
        parsed = self.parse_reference_number(reference_input)

        if not parsed:
            return (None, f"Invalid reference format. Expected format: AB-YYYY-NNNNN (e.g., AB-2024-10281)")

        year, posting_id = parsed

        # Fetch from API
        project_data, status_code, error_msg = self.fetch_project(year, posting_id)

        return (project_data, error_msg)

    @staticmethod
    def extract_project_details(api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key project details from API response for similarity analysis.

        Args:
            api_response: Full JSON response from Alberta API

        Returns:
            Dict with cleaned project details ready for similarity matching
        """
        if not api_response or 'opportunity' not in api_response:
            return {}

        opp = api_response['opportunity']

        # Extract key fields
        details = {
            'reference_number': opp.get('referenceNumber'),
            'short_title': opp.get('shortTitle', ''),
            'description': opp.get('projectDescription', ''),
            'actual_value': opp.get('actualValue'),
            'estimated_value': opp.get('estimatedValue'),
            'region': opp.get('regionOfDelivery', ''),
            'awarded_on': opp.get('awardedOnUtc'),
            'post_date': opp.get('postDateTime'),
            'close_date': opp.get('closeDateTime'),
            'status_code': opp.get('statusCode'),
            'category_code': opp.get('categoryCode'),
            'solicitation_type': opp.get('solicitationTypeCode'),

            # Additional useful info
            'num_bidders': len(api_response.get('bidders', [])),
            'num_interested': len(api_response.get('interestedSuppliers', [])),
            'is_awarded': opp.get('statusCode') == 'AWARD',
            'is_construction': opp.get('categoryCode') == 'CNST',
        }

        # Get bidder info if available
        bidders = api_response.get('bidders', [])
        if bidders:
            bid_amounts = [b.get('bidAmount') for b in bidders if b.get('bidAmount')]
            if bid_amounts:
                details['lowest_bid'] = min(bid_amounts)
                details['highest_bid'] = max(bid_amounts)
                details['average_bid'] = sum(bid_amounts) / len(bid_amounts)

        # Get award info
        awards = api_response.get('awards', [])
        if awards:
            award = awards[0]  # Usually only one award
            details['winner_name'] = award.get('winnerBusinessName')
            details['award_amount'] = award.get('awardAmount')

        return details


# Example usage and testing
if __name__ == "__main__":
    """
    Test the API fetcher.
    """
    fetcher = AlbertaAPIFetcher()

    # Test reference number parsing
    test_inputs = [
        "AB-2024-10281",
        "https://purchasing.alberta.ca/posting/AB-2024-10281",
        "AB-2025-05281",
    ]

    print("=" * 70)
    print("TESTING REFERENCE NUMBER PARSING")
    print("=" * 70)

    for test_input in test_inputs:
        result = fetcher.parse_reference_number(test_input)
        print(f"Input: {test_input}")
        print(f"  -> Parsed: {result}")
        print()

    # Test fetching a real project
    print("=" * 70)
    print("TESTING API FETCH")
    print("=" * 70)

    test_ref = "AB-2024-10281"
    print(f"Fetching: {test_ref}")

    project_data, error_msg = fetcher.fetch_by_reference(test_ref)

    if project_data:
        details = fetcher.extract_project_details(project_data)
        print(f"\n[SUCCESS]")
        print(f"  Reference: {details.get('reference_number')}")
        print(f"  Title: {details.get('short_title')}")
        print(f"  Status: {details.get('status_code')}")
        print(f"  Category: {details.get('category_code')}")
        print(f"  Value: ${details.get('actual_value', 'N/A')}")
        print(f"  Region: {details.get('region')}")
        print(f"  Bidders: {details.get('num_bidders')}")
    else:
        print(f"\n[FAILED]: {error_msg}")
