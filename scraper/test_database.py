"""
Test the database by importing existing sample data
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "alberta_procurement.db"
SAMPLE_JSON = Path(__file__).parent / "alberta_contracts_raw_2025_4050-4070.json"


def insert_raw_data(conn, year, posting_num, json_data):
    """Insert raw JSON data into database."""
    cursor = conn.cursor()

    ref_num = json_data['opportunity']['referenceNumber']

    cursor.execute("""
        INSERT OR REPLACE INTO raw_data (reference_number, year, posting_number, json_data, scraped_at)
        VALUES (?, ?, ?, ?, ?)
    """, (ref_num, year, posting_num, json.dumps(json_data), datetime.now()))


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
        datetime.now()
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


def import_sample_data():
    """Import the existing sample JSON data into database."""

    print(f"Loading sample data from: {SAMPLE_JSON}")

    with open(SAMPLE_JSON, 'r') as f:
        data = json.load(f)

    print(f"Found {len(data)} postings in sample data")

    conn = sqlite3.connect(DB_PATH)

    try:
        for posting in data:
            ref_num = posting['opportunity']['referenceNumber']
            parts = ref_num.split('-')
            year = int(parts[1])
            posting_num = int(parts[2])

            print(f"  Importing {ref_num}...")

            # Insert raw JSON
            insert_raw_data(conn, year, posting_num, posting)

            # Insert normalized data
            insert_opportunity(conn, posting)
            insert_bidders(conn, ref_num, posting)
            insert_interested_suppliers(conn, ref_num, posting)
            insert_awards(conn, ref_num, posting)
            insert_documents(conn, ref_num, posting)
            insert_contact(conn, ref_num, posting)

        conn.commit()
        print("\n[SUCCESS] All sample data imported successfully!")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Import failed: {e}")
        raise

    finally:
        conn.close()


def run_sample_queries():
    """Run some sample queries to verify the data."""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n" + "="*60)
    print("SAMPLE QUERIES")
    print("="*60)

    # Query 1: All opportunities
    print("\n1. All Opportunities:")
    cursor.execute("""
        SELECT reference_number, short_title, status_code, category_code, actual_value
        FROM opportunities
        ORDER BY reference_number
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[1][:40]:40} | {row[2]:8} | {row[3]:4} | ${row[4]:,.0f}" if row[4] else f"   {row[0]}: {row[1][:40]:40} | {row[2]:8} | {row[3]:4} | N/A")

    # Query 2: Bidders for a specific posting
    print("\n2. Bidders for AB-2025-04058:")
    cursor.execute("""
        SELECT company_name, bid_amount, city, is_winner
        FROM bidders
        WHERE opportunity_ref = 'AB-2025-04058'
        ORDER BY bid_amount
    """)
    for row in cursor.fetchall():
        winner = " *WINNER*" if row[3] else ""
        print(f"   {row[0]:40} ${row[1]:>12,.2f}  ({row[2]}){winner}")

    # Query 3: Interested suppliers count
    print("\n3. Interested Suppliers per Posting:")
    cursor.execute("""
        SELECT o.reference_number, o.short_title, COUNT(i.id) as num_interested
        FROM opportunities o
        LEFT JOIN interested_suppliers i ON o.reference_number = i.opportunity_ref
        GROUP BY o.reference_number
        ORDER BY num_interested DESC
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[2]:3} interested - {row[1][:40]}")

    # Query 4: Documents count
    print("\n4. Documents per Posting:")
    cursor.execute("""
        SELECT o.reference_number, COUNT(d.id) as num_docs
        FROM opportunities o
        LEFT JOIN documents d ON o.reference_number = d.opportunity_ref
        GROUP BY o.reference_number
        ORDER BY num_docs DESC
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[1]:2} documents")

    print("\n" + "="*60)

    conn.close()


if __name__ == "__main__":
    # Import sample data
    import_sample_data()

    # Show stats
    from database_setup import get_database_stats
    get_database_stats()

    # Run sample queries
    run_sample_queries()

    print("\n[SUCCESS] Database test complete!")
