"""
Alberta Procurement Database Setup
Creates SQLite database with hybrid storage approach:
- Raw JSON for complete backup
- Normalized tables for fast queries and analysis
"""

import sqlite3
from datetime import datetime
from pathlib import Path

# Database file location (in project root, one level up from scraper/)
DB_PATH = Path(__file__).parent.parent / "alberta_procurement.db"


def create_database():
    """Create the SQLite database with all required tables and indexes."""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Enable foreign key constraints
    cursor.execute("PRAGMA foreign_keys = ON;")

    print("Creating database tables...")

    # ========================================
    # Table 1: Raw JSON Storage (complete backup)
    # ========================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raw_data (
        reference_number TEXT PRIMARY KEY,
        year INTEGER NOT NULL,
        posting_number INTEGER NOT NULL,
        json_data TEXT NOT NULL,
        scraped_at TIMESTAMP NOT NULL,
        UNIQUE(year, posting_number)
    );
    """)

    # ========================================
    # Table 2: Opportunities (normalized key fields)
    # ========================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS opportunities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reference_number TEXT UNIQUE NOT NULL,
        year INTEGER NOT NULL,
        posting_number INTEGER NOT NULL,

        -- Basic Info
        short_title TEXT,
        full_title TEXT,
        description TEXT,
        additional_requirements TEXT,
        solicitation_number TEXT,

        -- Classification
        status_code TEXT,
        category_code TEXT,
        solicitation_type TEXT,
        posting_type TEXT,
        posting_hierarchy TEXT,
        region TEXT,

        -- Dates
        post_date TIMESTAMP,
        close_date TIMESTAMP,
        delivery_start_date TIMESTAMP,
        delivery_end_date TIMESTAMP,
        awarded_on TIMESTAMP,
        cancelled_on TIMESTAMP,

        -- Values
        estimated_value REAL,
        actual_value REAL,
        show_estimated_value BOOLEAN,

        -- Requirements
        bid_security TEXT,
        is_nda_required BOOLEAN,
        use_email_submission BOOLEAN,
        email_submission_value TEXT,

        -- Trade Agreements
        estimated_trade_agreement TEXT,
        actual_trade_agreement TEXT,
        is_direct_award BOOLEAN,

        -- Counts and Metadata
        amendment_number INTEGER DEFAULT 0,
        num_interested_suppliers INTEGER DEFAULT 0,
        num_bidders INTEGER DEFAULT 0,
        num_documents INTEGER DEFAULT 0,

        -- Tracking
        scraped_at TIMESTAMP NOT NULL,

        FOREIGN KEY (reference_number) REFERENCES raw_data(reference_number)
    );
    """)

    # ========================================
    # Table 3: Bidders
    # ========================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bidders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        opportunity_ref TEXT NOT NULL,

        -- Company Info
        company_name TEXT NOT NULL,
        supplier_id TEXT,
        city TEXT,
        address_line1 TEXT,
        address_line2 TEXT,
        province TEXT,
        postal_code TEXT,

        -- Contact Info
        contact_name TEXT,
        contact_email TEXT,
        contact_phone TEXT,
        contact_phone_extension TEXT,
        contact_job_title TEXT,

        -- Bid Info
        bid_amount REAL,
        is_winner BOOLEAN DEFAULT 0,
        prequalified BOOLEAN DEFAULT 0,

        FOREIGN KEY (opportunity_ref) REFERENCES opportunities(reference_number)
    );
    """)

    # ========================================
    # Table 4: Interested Suppliers
    # ========================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interested_suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        opportunity_ref TEXT NOT NULL,

        -- Company Info
        supplier_id TEXT,
        business_name TEXT NOT NULL,
        description TEXT,

        -- Address
        city TEXT,
        province TEXT,
        country TEXT,

        FOREIGN KEY (opportunity_ref) REFERENCES opportunities(reference_number)
    );
    """)

    # ========================================
    # Table 5: Awards
    # ========================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS awards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        opportunity_ref TEXT NOT NULL,

        -- Winner Info
        winner_name TEXT NOT NULL,
        supplier_id TEXT,
        award_amount REAL,
        award_date TIMESTAMP,

        -- Address
        city TEXT,
        province TEXT,
        country TEXT,

        FOREIGN KEY (opportunity_ref) REFERENCES opportunities(reference_number)
    );
    """)

    # ========================================
    # Table 6: Documents (optional but useful)
    # ========================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        opportunity_ref TEXT NOT NULL,

        -- Document Info
        document_id TEXT,
        filename TEXT,
        title TEXT,
        type_code TEXT,
        mime_type TEXT,
        size_bytes INTEGER,

        -- Metadata
        amendment_number INTEGER DEFAULT 0,
        uploaded_on TIMESTAMP,
        deleted_on TIMESTAMP,

        FOREIGN KEY (opportunity_ref) REFERENCES opportunities(reference_number)
    );
    """)

    # ========================================
    # Table 7: Contacts
    # ========================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        opportunity_ref TEXT NOT NULL,

        -- Contact Info
        title TEXT,
        first_name TEXT,
        last_name TEXT,
        email TEXT,
        phone_number TEXT,
        phone_extension TEXT,

        -- Address
        address_line1 TEXT,
        address_line2 TEXT,
        city TEXT,
        province TEXT,
        postal_code TEXT,
        country TEXT,

        -- Metadata
        preferred_contact_method TEXT,

        FOREIGN KEY (opportunity_ref) REFERENCES opportunities(reference_number)
    );
    """)

    # ========================================
    # Table 8: Scraping Metadata (track progress)
    # ========================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scrape_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        year INTEGER NOT NULL,
        posting_number INTEGER NOT NULL,
        reference_number TEXT,
        success BOOLEAN NOT NULL,
        error_message TEXT,
        http_status_code INTEGER,
        scraped_at TIMESTAMP NOT NULL,
        UNIQUE(year, posting_number)
    );
    """)

    print("Creating indexes for fast queries...")

    # ========================================
    # Indexes for Performance
    # ========================================

    # Raw data indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_year ON raw_data(year);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_year_posting ON raw_data(year, posting_number);")

    # Opportunities indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_opp_year ON opportunities(year);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_opp_status ON opportunities(status_code);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_opp_category ON opportunities(category_code);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_opp_year_category ON opportunities(year, category_code);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_opp_status_category ON opportunities(status_code, category_code);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_opp_post_date ON opportunities(post_date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_opp_close_date ON opportunities(close_date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_opp_region ON opportunities(region);")

    # Bidders indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bidders_opp ON bidders(opportunity_ref);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bidders_company ON bidders(company_name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bidders_winner ON bidders(is_winner);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bidders_city ON bidders(city);")

    # Interested suppliers indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_interested_opp ON interested_suppliers(opportunity_ref);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_interested_company ON interested_suppliers(business_name);")

    # Awards indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_awards_opp ON awards(opportunity_ref);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_awards_winner ON awards(winner_name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_awards_date ON awards(award_date);")

    # Documents indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_docs_opp ON documents(opportunity_ref);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_docs_type ON documents(type_code);")

    # Scrape log indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scrape_year ON scrape_log(year);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scrape_success ON scrape_log(success);")

    conn.commit()
    conn.close()

    print(f"[SUCCESS] Database created successfully: {DB_PATH}")
    print(f"   Tables: raw_data, opportunities, bidders, interested_suppliers, awards, documents, contacts, scrape_log")
    return DB_PATH


def get_database_stats():
    """Print statistics about the current database."""

    if not DB_PATH.exists():
        print(f"Database does not exist yet: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"\n{'='*60}")
    print(f"DATABASE STATISTICS: {DB_PATH.name}")
    print(f"{'='*60}")

    tables = [
        ('raw_data', 'Raw JSON backups'),
        ('opportunities', 'Normalized opportunities'),
        ('bidders', 'Bidder submissions'),
        ('interested_suppliers', 'Interested suppliers'),
        ('awards', 'Contract awards'),
        ('documents', 'Attached documents'),
        ('contacts', 'Contact information'),
        ('scrape_log', 'Scraping attempts')
    ]

    for table_name, description in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        print(f"{table_name:25} {count:6,} rows  - {description}")

    # Additional stats
    cursor.execute("SELECT COUNT(DISTINCT year) FROM opportunities;")
    years = cursor.fetchone()[0]

    cursor.execute("SELECT MIN(year), MAX(year) FROM opportunities;")
    year_range = cursor.fetchone()

    if year_range[0]:
        print(f"\nYear range: {year_range[0]} to {year_range[1]} ({years} unique years)")

    # Category breakdown
    cursor.execute("""
        SELECT category_code, COUNT(*) as count
        FROM opportunities
        GROUP BY category_code
        ORDER BY count DESC
        LIMIT 5;
    """)
    categories = cursor.fetchall()

    if categories:
        print(f"\nTop categories:")
        for cat, count in categories:
            print(f"  {cat or 'NULL':10} {count:6,} postings")

    # Status breakdown
    cursor.execute("""
        SELECT status_code, COUNT(*) as count
        FROM opportunities
        GROUP BY status_code
        ORDER BY count DESC;
    """)
    statuses = cursor.fetchall()

    if statuses:
        print(f"\nStatus breakdown:")
        for status, count in statuses:
            print(f"  {status or 'NULL':15} {count:6,} postings")

    print(f"{'='*60}\n")

    conn.close()


if __name__ == "__main__":
    # Create the database
    db_path = create_database()

    # Show initial stats
    get_database_stats()

    print("\n[SUCCESS] Database setup complete!")
    print(f"   Location: {db_path}")
    print(f"   Ready for scraping!")
