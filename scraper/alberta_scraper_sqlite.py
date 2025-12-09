"""
Alberta Procurement Scraper - SQLite Edition
Scrapes ALL postings (not just awarded) from Alberta Purchasing Connection API
and stores everything in SQLite database with hybrid approach.

Features:
- Scrapes all posting types (AWARD, OPEN, CLOSED, CANCELLED, etc.)
- Stores raw JSON + normalized data
- Resume capability (skips already-scraped postings)
- Progress tracking and error handling
- 1-second delay between requests (respectful scraping)
"""

import requests
import sqlite3
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

# ========================================
# Configuration
# ========================================
API_BASE = "https://purchasing.alberta.ca/api/opportunity/public"
DELAY_BETWEEN_REQUESTS = 1.0  # seconds - be respectful
DB_PATH = Path(__file__).parent.parent / "alberta_procurement.db"

# Session with headers
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
})


# ========================================
# Database Helper Functions
# ========================================

def insert_raw_data(conn, year, posting_num, json_data):
    """Insert raw JSON data into database."""
    cursor = conn.cursor()
    ref_num = json_data['opportunity']['referenceNumber']

    cursor.execute("""
        INSERT OR REPLACE INTO raw_data (reference_number, year, posting_number, json_data, scraped_at)
        VALUES (?, ?, ?, ?, ?)
    """, (ref_num, year, posting_num, json.dumps(json_data), datetime.now().isoformat()))


def insert_opportunity(conn, json_data):
    """Insert opportunity data into normalized table."""
    cursor = conn.cursor()
    opp = json_data['opportunity']
    ref_num = opp['referenceNumber']

    # Extract year and posting number from reference (e.g., "AB-2025-04058")
    parts = ref_num.split('-')
    year = int(parts[1])
    posting_num = int(parts[2])

    cursor.execute("""
        INSERT OR REPLACE INTO opportunities (
            reference_number, year, posting_number,
            short_title, full_title, description, additional_requirements, solicitation_number,
            status_code, category_code, solicitation_type, posting_type, posting_hierarchy, region,
            post_date, close_date, delivery_start_date, delivery_end_date, awarded_on, cancelled_on,
            estimated_value, actual_value, show_estimated_value,
            bid_security, is_nda_required, use_email_submission, email_submission_value,
            estimated_trade_agreement, actual_trade_agreement, is_direct_award,
            amendment_number, num_interested_suppliers, num_bidders, num_documents,
            scraped_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ref_num, year, posting_num,
        opp.get('shortTitle'), opp.get('title'), opp.get('projectDescription'),
        opp.get('additionalRequirements'), opp.get('solicitationNumber'),
        opp.get('statusCode'), opp.get('categoryCode'), opp.get('solicitationTypeCode'),
        opp.get('postingTypeCode'), opp.get('postingHierarchy'), opp.get('regionOfDelivery'),
        opp.get('postDateTime'), opp.get('closeDateTime'), opp.get('deliveryStartDate'),
        opp.get('deliveryEndDate'), opp.get('awardedOnUtc'), opp.get('cancelledOnUtc'),
        opp.get('estimatedValue'), opp.get('actualValue'), opp.get('showEstimatedValue'),
        opp.get('bidSecurity'), opp.get('isNdaRequiredForDocumentsAccess'),
        opp.get('useEmailSubmission'), opp.get('emailSubmissionValue'),
        opp.get('estimatedTradeAgreement'), opp.get('actualTradeAgreement'),
        opp.get('isDirectAward'),
        opp.get('amendmentNumber', 0),
        len(json_data.get('interestedSuppliers', [])),
        len(json_data.get('bidders', [])),
        len(opp.get('documents', [])),
        datetime.now().isoformat()
    ))


def insert_bidders(conn, ref_num, json_data):
    """Insert bidder data."""
    cursor = conn.cursor()
    bidders = json_data.get('bidders', [])
    awards = json_data.get('awards', [])

    # Get winner name if exists
    winner_name = None
    if awards:
        winner_name = awards[0].get('alternativeSupplierDisplayName')

    for bidder in bidders:
        address = bidder.get('address', {})
        bid_amounts = bidder.get('bidAmounts', [])
        bid_amount = bid_amounts[0].get('amount') if bid_amounts else None

        company_name = bidder.get('alternativeSupplierDisplayName')
        is_winner = company_name == winner_name if winner_name else False

        cursor.execute("""
            INSERT INTO bidders (
                opportunity_ref, company_name, supplier_id,
                city, address_line1, address_line2, province, postal_code,
                contact_name, contact_email, contact_phone, contact_phone_extension, contact_job_title,
                bid_amount, is_winner, prequalified
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ref_num, company_name, bidder.get('supplierId'),
            address.get('city'), address.get('addressLine1'), address.get('addressLine2'),
            address.get('province'), address.get('postalCode'),
            bidder.get('contactName'), bidder.get('contactEmail'),
            bidder.get('contactPhoneNumber'), bidder.get('contactPhoneNumberExtension'),
            bidder.get('contactJobTitle'),
            bid_amount, is_winner, bidder.get('prequalified', False)
        ))


def insert_interested_suppliers(conn, ref_num, json_data):
    """Insert interested suppliers data."""
    cursor = conn.cursor()
    suppliers = json_data.get('interestedSuppliers', [])

    for supplier in suppliers:
        address = supplier.get('physicalAddress', {})
        description = ', '.join(supplier.get('description', [])) if supplier.get('description') else None

        cursor.execute("""
            INSERT INTO interested_suppliers (
                opportunity_ref, supplier_id, business_name, description,
                city, province, country
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            ref_num, supplier.get('supplierId'), supplier.get('businessName'), description,
            address.get('city'), address.get('province'), address.get('country')
        ))


def insert_awards(conn, ref_num, json_data):
    """Insert award data."""
    cursor = conn.cursor()
    awards = json_data.get('awards', [])

    for award in awards:
        address = award.get('address', {})

        cursor.execute("""
            INSERT INTO awards (
                opportunity_ref, winner_name, supplier_id, award_amount, award_date,
                city, province, country
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ref_num, award.get('alternativeSupplierDisplayName'), award.get('supplierId'),
            award.get('amount'), award.get('awardDate'),
            address.get('city'), address.get('province'), address.get('country')
        ))


def insert_documents(conn, ref_num, json_data):
    """Insert document metadata."""
    cursor = conn.cursor()
    documents = json_data['opportunity'].get('documents', [])

    for doc in documents:
        cursor.execute("""
            INSERT INTO documents (
                opportunity_ref, document_id, filename, title, type_code, mime_type,
                size_bytes, amendment_number, uploaded_on, deleted_on
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ref_num, doc.get('id'), doc.get('filename'), doc.get('title'),
            doc.get('typeCode'), doc.get('mimeType'), doc.get('size'),
            doc.get('amendmentNumber', 0), doc.get('uploadedOnUtc'), doc.get('deletedOnUtc')
        ))


def insert_contact(conn, ref_num, json_data):
    """Insert contact information."""
    cursor = conn.cursor()
    contact = json_data['opportunity'].get('contactInformation')
    if not contact:
        return

    cursor.execute("""
        INSERT INTO contacts (
            opportunity_ref, title, first_name, last_name, email, phone_number, phone_extension,
            address_line1, address_line2, city, province, postal_code, country,
            preferred_contact_method
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ref_num, contact.get('title'), contact.get('firstName'), contact.get('lastName'),
        contact.get('emailAddress'), contact.get('phoneNumber'), contact.get('phoneNumberExtension'),
        contact.get('addressLine1'), contact.get('addressLine2'), contact.get('city'),
        contact.get('province'), contact.get('postalCode'), contact.get('country'),
        contact.get('preferredContactMethodText')
    ))


def log_scrape_attempt(conn, year, posting_num, ref_num, success, error_msg=None, http_status=None):
    """Log a scraping attempt to the scrape_log table."""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO scrape_log
        (year, posting_number, reference_number, success, error_message, http_status_code, scraped_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (year, posting_num, ref_num, success, error_msg, http_status, datetime.now().isoformat()))


def is_already_scraped(conn, year, posting_num):
    """Check if a posting has already been successfully scraped."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT success FROM scrape_log
        WHERE year = ? AND posting_number = ? AND success = 1
    """, (year, posting_num))
    return cursor.fetchone() is not None


def insert_full_posting(conn, year, posting_num, json_data):
    """Insert complete posting data (all tables)."""
    ref_num = json_data['opportunity']['referenceNumber']

    # Insert into all tables
    insert_raw_data(conn, year, posting_num, json_data)
    insert_opportunity(conn, json_data)
    insert_bidders(conn, ref_num, json_data)
    insert_interested_suppliers(conn, ref_num, json_data)
    insert_awards(conn, ref_num, json_data)
    insert_documents(conn, ref_num, json_data)
    insert_contact(conn, ref_num, json_data)


# ========================================
# API Functions
# ========================================

def fetch_opportunity(year: int, posting_num: int) -> Optional[Dict[str, Any]]:
    """
    Fetch a single opportunity from the API.

    Args:
        year: Year (e.g., 2025)
        posting_num: Posting number (e.g., 4058 for AB-2025-04058)

    Returns:
        Tuple of (json_data, http_status_code) or (None, status_code) if failed
    """
    url = f"{API_BASE}/{year}/{posting_num}"
    try:
        response = session.get(url, timeout=30)
        if response.status_code == 200:
            return response.json(), 200
        elif response.status_code == 404:
            return None, 404
        else:
            print(f"  [WARNING] HTTP {response.status_code} for {year}/{posting_num}")
            return None, response.status_code
    except requests.RequestException as e:
        print(f"  [ERROR] Request failed for {year}/{posting_num}: {e}")
        return None, None


# ========================================
# Main Scraping Function
# ========================================

def scrape_range(year: int, start_num: int, end_num: int, skip_existing: bool = True):
    """
    Scrape a range of postings and store in database.

    Args:
        year: Year to scrape (e.g., 2025)
        start_num: Starting posting number (e.g., 1)
        end_num: Ending posting number (e.g., 500)
        skip_existing: Skip postings already in database (default: True)
    """

    conn = sqlite3.connect(DB_PATH)

    total = end_num - start_num + 1
    found = 0
    skipped = 0
    errors = 0

    print(f"\n{'='*70}")
    print(f"SCRAPING ALBERTA PROCUREMENT DATA")
    print(f"{'='*70}")
    print(f"Year: {year}")
    print(f"Range: {start_num} to {end_num} ({total:,} postings)")
    print(f"Skip existing: {skip_existing}")
    print(f"Database: {DB_PATH}")
    print(f"{'='*70}\n")

    start_time = time.time()

    try:
        for i, num in enumerate(range(start_num, end_num + 1), 1):
            posting_id = f"AB-{year}-{num:05d}"

            # Progress update every 25 postings
            if i % 25 == 0:
                elapsed = time.time() - start_time
                rate = i / elapsed if elapsed > 0 else 0
                remaining = (total - i) / rate if rate > 0 else 0
                print(f"Progress: {i:4}/{total} ({i/total*100:5.1f}%) | Found: {found:4} | Skipped: {skipped:3} | Errors: {errors:2} | ETA: {remaining/60:.1f}m")

            # Check if already scraped
            if skip_existing and is_already_scraped(conn, year, num):
                skipped += 1
                continue

            # Fetch from API
            result, status_code = fetch_opportunity(year, num)

            if result:
                # Successfully fetched
                found += 1
                try:
                    insert_full_posting(conn, year, num, result)
                    log_scrape_attempt(conn, year, num, posting_id, True, http_status=status_code)
                    conn.commit()

                    # Show some details
                    opp = result['opportunity']
                    status = opp.get('statusCode', 'UNKNOWN')
                    category = opp.get('categoryCode', 'N/A')
                    title = opp.get('shortTitle', 'No title')[:50]
                    print(f"  [{posting_id}] {status:8} | {category:4} | {title}")

                except Exception as e:
                    errors += 1
                    error_msg = str(e)
                    print(f"  [ERROR] Failed to insert {posting_id}: {error_msg}")
                    log_scrape_attempt(conn, year, num, posting_id, False, error_msg, status_code)
                    conn.commit()

            elif status_code == 404:
                # Not found - normal, just log it
                log_scrape_attempt(conn, year, num, None, False, "Not found (404)", 404)
                conn.commit()

            else:
                # Other error
                errors += 1
                error_msg = f"HTTP {status_code}" if status_code else "Network error"
                log_scrape_attempt(conn, year, num, None, False, error_msg, status_code)
                conn.commit()

            # Rate limiting
            time.sleep(DELAY_BETWEEN_REQUESTS)

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Scraping interrupted by user. Progress saved.")
        conn.commit()

    finally:
        conn.close()

    # Final summary
    elapsed = time.time() - start_time
    print(f"\n{'='*70}")
    print(f"SCRAPING COMPLETE")
    print(f"{'='*70}")
    print(f"Checked: {total:,} posting numbers")
    print(f"Found: {found:,} postings")
    print(f"Skipped (already scraped): {skipped:,}")
    print(f"Errors: {errors:,}")
    print(f"Time elapsed: {elapsed/60:.1f} minutes")
    print(f"{'='*70}\n")


# ========================================
# Utility Functions
# ========================================

def get_scrape_status(year: int):
    """Get scraping status for a specific year."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"\n{'='*70}")
    print(f"SCRAPING STATUS FOR {year}")
    print(f"{'='*70}")

    # Total attempts
    cursor.execute("SELECT COUNT(*) FROM scrape_log WHERE year = ?", (year,))
    total_attempts = cursor.fetchone()[0]

    # Successful
    cursor.execute("SELECT COUNT(*) FROM scrape_log WHERE year = ? AND success = 1", (year,))
    successful = cursor.fetchone()[0]

    # 404s
    cursor.execute("SELECT COUNT(*) FROM scrape_log WHERE year = ? AND http_status_code = 404", (year,))
    not_found = cursor.fetchone()[0]

    # Errors
    cursor.execute("SELECT COUNT(*) FROM scrape_log WHERE year = ? AND success = 0 AND http_status_code != 404", (year,))
    errors = cursor.fetchone()[0]

    print(f"Total attempts: {total_attempts:,}")
    print(f"Successfully scraped: {successful:,}")
    print(f"Not found (404): {not_found:,}")
    print(f"Errors: {errors:,}")

    if successful > 0:
        # Get range
        cursor.execute("""
            SELECT MIN(posting_number), MAX(posting_number)
            FROM scrape_log
            WHERE year = ? AND success = 1
        """, (year,))
        min_num, max_num = cursor.fetchone()
        print(f"Range scraped: {min_num} to {max_num}")

        # Category breakdown
        cursor.execute("""
            SELECT category_code, COUNT(*) as count
            FROM opportunities
            WHERE year = ?
            GROUP BY category_code
            ORDER BY count DESC
            LIMIT 10
        """, (year,))
        categories = cursor.fetchall()

        if categories:
            print(f"\nTop categories:")
            for cat, count in categories:
                print(f"  {cat or 'NULL':10} {count:6,} postings")

        # Status breakdown
        cursor.execute("""
            SELECT status_code, COUNT(*) as count
            FROM opportunities
            WHERE year = ?
            GROUP BY status_code
            ORDER BY count DESC
        """, (year,))
        statuses = cursor.fetchall()

        if statuses:
            print(f"\nStatus breakdown:")
            for status, count in statuses:
                print(f"  {status or 'NULL':15} {count:6,} postings")

    print(f"{'='*70}\n")
    conn.close()


# ========================================
# Main Execution
# ========================================

if __name__ == "__main__":
    import sys

    print("\n" + "="*70)
    print("ALBERTA PROCUREMENT SCRAPER - SQLite Edition")
    print("="*70)

    # Default parameters (can be overridden via command line)
    year = 2025
    start_num = 1
    end_num = 100

    # Parse command line arguments if provided
    if len(sys.argv) >= 4:
        year = int(sys.argv[1])
        start_num = int(sys.argv[2])
        end_num = int(sys.argv[3])

    print(f"\nConfiguration:")
    print(f"  Year: {year}")
    print(f"  Start: {start_num}")
    print(f"  End: {end_num}")
    print(f"  Total to check: {end_num - start_num + 1:,}")
    print("\nPress Ctrl+C to stop at any time (progress will be saved)")
    print("="*70)

    # Start scraping
    scrape_range(year, start_num, end_num, skip_existing=True)

    # Show status
    get_scrape_status(year)

    # Show database stats
    from database_setup import get_database_stats
    get_database_stats()
