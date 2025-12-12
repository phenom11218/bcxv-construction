"""
Alberta Procurement Scraper - Universal Endpoint Detector
Finds the highest posting number for ANY year (2010-2099+)

Usage:
    python find_endpoint.py 2024              # Find 2024 endpoint from posting 1
    python find_endpoint.py 2024 10284        # Test from 10284 onwards
    python find_endpoint.py 2023              # Find 2023 endpoint
    python find_endpoint.py 2010              # Find 2010 endpoint

Features:
    - Year-agnostic: works with ANY year
    - Configurable consecutive 404 threshold
    - Safe exploratory testing
    - Progress reporting
"""

import requests
import time
import sys
from datetime import datetime

# API configuration
API_BASE = "https://purchasing.alberta.ca/api/opportunity/public"
DELAY_BETWEEN_REQUESTS = 1.0  # seconds - be respectful

# Session with headers
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
})


def fetch_opportunity(year, posting_num):
    """
    Fetch a single opportunity from the API.

    Args:
        year: Any year (e.g., 2024, 2010, 2099)
        posting_num: Posting number (e.g., 10284)

    Returns:
        Tuple of (json_data, http_status_code)
    """
    url = f"{API_BASE}/{year}/{posting_num}"
    try:
        response = session.get(url, timeout=30)
        if response.status_code == 200:
            return response.json(), 200
        else:
            return None, response.status_code
    except requests.RequestException as e:
        print(f"  [ERROR] Request failed: {e}")
        return None, None


def find_endpoint(year, start_from=1, max_consecutive_404s=50, max_tests=200):
    """
    Find the highest posting number for a given year.

    Args:
        year: Year to test (e.g., 2024)
        start_from: Starting posting number (default: 1)
        max_consecutive_404s: Stop after this many consecutive 404s (default: 50)
        max_tests: Maximum number of postings to test (safety limit)

    Returns:
        Highest posting number found
    """
    print(f"\n{'='*70}")
    print(f"ENDPOINT DETECTION FOR {year}")
    print(f"{'='*70}")
    print(f"\nConfiguration:")
    print(f"  Starting from:      {start_from}")
    print(f"  Stop after:         {max_consecutive_404s} consecutive 404s")
    print(f"  Max tests:          {max_tests} postings")
    print(f"  API delay:          {DELAY_BETWEEN_REQUESTS}s between requests")
    print(f"\nTesting posting numbers...")
    print("-" * 70)

    consecutive_404s = 0
    highest_found = 0
    current = start_from
    tests_run = 0
    found_count = 0
    start_time = time.time()

    # Track found postings for summary
    found_postings = []

    while consecutive_404s < max_consecutive_404s and tests_run < max_tests:
        json_data, status = fetch_opportunity(year, current)
        tests_run += 1

        if status == 200:
            highest_found = current
            consecutive_404s = 0
            found_count += 1

            ref = json_data['opportunity']['referenceNumber']
            title = json_data['opportunity'].get('shortTitle', 'No title')[:40]
            status_code = json_data['opportunity'].get('statusCode', 'N/A')

            print(f"  {current:5}: ✓ Found - {ref} [{status_code:8}] {title}")

            # Store found posting
            found_postings.append((current, ref, status_code))

        elif status == 404:
            consecutive_404s += 1
            print(f"  {current:5}: ✗ 404 (consecutive: {consecutive_404s}/{max_consecutive_404s})")

        elif status is None:
            print(f"  {current:5}: ⚠ Network error - retrying...")
            time.sleep(2)  # Extra delay on error
            continue

        else:
            print(f"  {current:5}: ⚠ HTTP {status}")
            consecutive_404s += 1  # Treat other errors as 404

        current += 1

        # Be respectful - rate limit
        time.sleep(DELAY_BETWEEN_REQUESTS)

    # Summary
    elapsed = time.time() - start_time

    print("-" * 70)
    print(f"\n{'='*70}")
    print(f"DETECTION RESULTS FOR {year}")
    print(f"{'='*70}")

    if highest_found > 0:
        print(f"\n✅ Highest posting found: AB-{year}-{highest_found:05d}")
        print(f"   Reference: AB-{year}-{highest_found:05d}")
        print(f"   Recommended scraping range: 1 to {highest_found}")

        if found_count > 0:
            print(f"\nFound {found_count} postings in this test:")
            print(f"   Range: AB-{year}-{found_postings[0][0]:05d} to AB-{year}-{found_postings[-1][0]:05d}")

    else:
        print(f"\n❌ No postings found for {year}")
        print(f"   Either no data exists for this year, or starting point {start_from} is too high")
        print(f"   Try: python find_endpoint.py {year} 1")

    print(f"\nStatistics:")
    print(f"   Tests run:          {tests_run}")
    print(f"   Postings found:     {found_count}")
    print(f"   Final 404 streak:   {consecutive_404s}")
    print(f"   Time elapsed:       {elapsed:.1f} seconds")
    print(f"   Average rate:       {tests_run/elapsed:.1f} tests/second")

    if tests_run >= max_tests:
        print(f"\n⚠ WARNING: Reached maximum test limit ({max_tests})")
        print(f"   Consider running again with higher --max-tests value")

    print("=" * 70 + "\n")

    return highest_found


def print_usage():
    """Print usage instructions."""
    print("\nAlberta Procurement Endpoint Detector")
    print("=" * 70)
    print("\nUsage:")
    print("  python find_endpoint.py <year> [start] [max_404s] [max_tests]")
    print("\nArguments:")
    print("  year        Year to test (required, e.g., 2024, 2023, 2010)")
    print("  start       Starting posting number (optional, default: 1)")
    print("  max_404s    Stop after N consecutive 404s (optional, default: 50)")
    print("  max_tests   Maximum tests to run (optional, default: 200)")
    print("\nExamples:")
    print("  python find_endpoint.py 2024")
    print("     -> Find 2024 endpoint from posting 1")
    print("\n  python find_endpoint.py 2024 10284")
    print("     -> Test 2024 from 10284 onwards (verify estimated endpoint)")
    print("\n  python find_endpoint.py 2023")
    print("     -> Find 2023 endpoint")
    print("\n  python find_endpoint.py 2024 10000 20")
    print("     -> Test from 10000, stop after 20 consecutive 404s")
    print("\n  python find_endpoint.py 2010 1 10 500")
    print("     -> Find 2010 endpoint, test up to 500 postings")
    print("\nNotes:")
    print("  - This tool works with ANY year (2000-2099)")
    print("  - Uses 1-second delay between requests (respectful scraping)")
    print("  - Safe to run multiple times - read-only operation")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("\n[ERROR] Year argument required")
        print_usage()
        sys.exit(1)

    try:
        year = int(sys.argv[1])

        if year < 2000 or year > 2099:
            print(f"\n[WARNING] Year {year} seems unusual. Are you sure? (2000-2099 expected)")
            response = input("Continue? (y/n): ")
            if response.lower() != 'y':
                sys.exit(0)

        start_from = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        max_404s = int(sys.argv[3]) if len(sys.argv) > 3 else 50
        max_tests = int(sys.argv[4]) if len(sys.argv) > 4 else 200

        if start_from < 1:
            print("\n[ERROR] Start posting number must be >= 1")
            sys.exit(1)

        if max_404s < 1:
            print("\n[ERROR] max_404s must be >= 1")
            sys.exit(1)

        if max_tests < 1:
            print("\n[ERROR] max_tests must be >= 1")
            sys.exit(1)

        # Run endpoint detection
        highest = find_endpoint(year, start_from, max_404s, max_tests)

        # Provide next steps
        if highest > 0:
            print(f"💡 Next Steps:")
            print(f"   1. Check progress: python check_progress.py {year}")
            print(f"   2. Scrape full year: python alberta_scraper_sqlite.py {year} 1 {highest}")
            print(f"   3. Or scrape in batches:")
            print(f"      python alberta_scraper_sqlite.py {year} 1 5000")
            print(f"      python alberta_scraper_sqlite.py {year} 5001 {highest}\n")

    except ValueError:
        print("\n[ERROR] Invalid arguments. Year must be a number.")
        print_usage()
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Detection stopped by user.")
        sys.exit(0)
