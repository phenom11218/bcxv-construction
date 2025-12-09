"""
Query Helper - Easy database queries for Alberta Procurement data
Run this to explore your scraped data with common queries
"""

import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "alberta_procurement.db"


def query(sql, params=()):
    """Execute a query and return results."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(sql, params)
    results = cursor.fetchall()
    conn.close()
    return results


def print_table(headers, rows, title=None):
    """Pretty print a table."""
    if title:
        print(f"\n{title}")
        print("=" * len(title))

    if not rows:
        print("  (No results)")
        return

    # Calculate column widths
    widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val)))

    # Print header
    header_line = " | ".join(str(h).ljust(w) for h, w in zip(headers, widths))
    print(header_line)
    print("-" * len(header_line))

    # Print rows
    for row in rows:
        print(" | ".join(str(v).ljust(w) for v, w in zip(row, widths)))

    print(f"\nTotal: {len(rows)} rows\n")


# ========================================
# Common Queries
# ========================================

def overview():
    """Database overview."""
    print("\n" + "="*70)
    print("DATABASE OVERVIEW")
    print("="*70)

    # Total postings
    total = query("SELECT COUNT(*) FROM opportunities")[0][0]
    print(f"\nTotal postings in database: {total:,}")

    # By year
    by_year = query("""
        SELECT year, COUNT(*) as count
        FROM opportunities
        GROUP BY year
        ORDER BY year
    """)
    print_table(["Year", "Count"], by_year, "Postings by Year")

    # By status
    by_status = query("""
        SELECT status_code, COUNT(*) as count
        FROM opportunities
        GROUP BY status_code
        ORDER BY count DESC
    """)
    print_table(["Status", "Count"], by_status, "Postings by Status")

    # By category
    by_category = query("""
        SELECT category_code, COUNT(*) as count
        FROM opportunities
        GROUP BY category_code
        ORDER BY count DESC
    """)
    print_table(["Category", "Count"], by_category, "Postings by Category")


def search_by_keyword(keyword):
    """Search postings by keyword in title or description."""
    results = query("""
        SELECT reference_number, short_title, status_code, category_code, actual_value
        FROM opportunities
        WHERE short_title LIKE ? OR description LIKE ?
        ORDER BY reference_number DESC
        LIMIT 20
    """, (f'%{keyword}%', f'%{keyword}%'))

    print_table(
        ["Reference", "Title", "Status", "Category", "Value"],
        [(r[0], r[1][:50], r[2], r[3], f"${r[4]:,.0f}" if r[4] else "N/A") for r in results],
        f"Search Results for '{keyword}' (max 20)"
    )


def construction_projects(limit=20):
    """Show recent construction projects."""
    results = query("""
        SELECT reference_number, short_title, status_code, actual_value, num_bidders
        FROM opportunities
        WHERE category_code = 'CNST'
        ORDER BY reference_number DESC
        LIMIT ?
    """, (limit,))

    print_table(
        ["Reference", "Title", "Status", "Value", "Bidders"],
        [(r[0], r[1][:50], r[2], f"${r[3]:,.0f}" if r[3] else "N/A", r[4]) for r in results],
        f"Recent Construction Projects (max {limit})"
    )


def top_bidders(limit=20):
    """Show companies that bid most frequently."""
    results = query("""
        SELECT company_name, COUNT(*) as num_bids,
               SUM(CASE WHEN is_winner = 1 THEN 1 ELSE 0 END) as wins,
               SUM(CASE WHEN is_winner = 1 THEN bid_amount ELSE 0 END) as total_won
        FROM bidders
        WHERE company_name IS NOT NULL
        GROUP BY company_name
        ORDER BY num_bids DESC
        LIMIT ?
    """, (limit,))

    formatted = []
    for company, bids, wins, total in results:
        win_rate = f"{wins/bids*100:.1f}%" if bids > 0 else "0%"
        formatted.append((company[:40], bids, wins, win_rate, f"${total:,.0f}" if total else "$0"))

    print_table(
        ["Company", "Bids", "Wins", "Win Rate", "Total Won"],
        formatted,
        f"Top {limit} Most Active Bidders"
    )


def top_winners(limit=20):
    """Show companies that won most contracts."""
    results = query("""
        SELECT winner_name, COUNT(*) as num_wins,
               SUM(award_amount) as total_value,
               AVG(award_amount) as avg_value
        FROM awards
        WHERE winner_name IS NOT NULL
        GROUP BY winner_name
        ORDER BY num_wins DESC
        LIMIT ?
    """, (limit,))

    formatted = []
    for company, wins, total, avg in results:
        formatted.append((
            company[:40],
            wins,
            f"${total:,.0f}" if total else "N/A",
            f"${avg:,.0f}" if avg else "N/A"
        ))

    print_table(
        ["Company", "Contracts Won", "Total Value", "Avg Value"],
        formatted,
        f"Top {limit} Contract Winners"
    )


def posting_details(reference_number):
    """Show detailed information about a specific posting."""
    # Main info
    opp = query("""
        SELECT reference_number, short_title, full_title, description, status_code, category_code,
               solicitation_type, region, post_date, close_date, actual_value, num_bidders, num_interested_suppliers
        FROM opportunities
        WHERE reference_number = ?
    """, (reference_number,))

    if not opp:
        print(f"No posting found with reference: {reference_number}")
        return

    opp = opp[0]

    print(f"\n{'='*70}")
    print(f"POSTING DETAILS: {opp[0]}")
    print(f"{'='*70}")
    print(f"Title: {opp[1]}")
    print(f"Full Title: {opp[2]}")
    print(f"Status: {opp[4]}")
    print(f"Category: {opp[5]}")
    print(f"Solicitation Type: {opp[6]}")
    print(f"Region: {opp[7]}")
    print(f"Post Date: {opp[8]}")
    print(f"Close Date: {opp[9]}")
    print(f"Value: ${opp[10]:,.0f}" if opp[10] else "Value: N/A")
    print(f"Number of Bidders: {opp[11]}")
    print(f"Interested Suppliers: {opp[12]}")
    print(f"\nDescription:\n{opp[3][:500]}..." if len(str(opp[3])) > 500 else f"\nDescription:\n{opp[3]}")

    # Bidders
    bidders = query("""
        SELECT company_name, bid_amount, city, is_winner
        FROM bidders
        WHERE opportunity_ref = ?
        ORDER BY bid_amount
    """, (reference_number,))

    if bidders:
        formatted = [(b[0][:40], f"${b[1]:,.2f}" if b[1] else "N/A", b[2] or "N/A", "*WINNER*" if b[3] else "") for b in bidders]
        print_table(["Company", "Bid Amount", "City", ""], formatted, "\nBidders")

    # Award
    award = query("""
        SELECT winner_name, award_amount, award_date, city
        FROM awards
        WHERE opportunity_ref = ?
    """, (reference_number,))

    if award:
        formatted = [(a[0], f"${a[1]:,.0f}" if a[1] else "N/A", a[2], a[3] or "N/A") for a in award]
        print_table(["Winner", "Award Amount", "Award Date", "City"], formatted, "\nAward Info")

    # Documents
    docs = query("""
        SELECT filename, type_code, size_bytes, uploaded_on
        FROM documents
        WHERE opportunity_ref = ?
        ORDER BY uploaded_on
    """, (reference_number,))

    if docs:
        formatted = [(d[0][:50], d[1], f"{d[2]/1024:.1f} KB" if d[2] else "N/A", d[3]) for d in docs]
        print_table(["Filename", "Type", "Size", "Uploaded"], formatted, f"\nDocuments ({len(docs)} total)")


def interested_by_company(company_name):
    """Show all postings a company expressed interest in."""
    results = query("""
        SELECT i.opportunity_ref, o.short_title, o.status_code, o.category_code, o.actual_value
        FROM interested_suppliers i
        JOIN opportunities o ON i.opportunity_ref = o.reference_number
        WHERE i.business_name LIKE ?
        ORDER BY i.opportunity_ref DESC
        LIMIT 50
    """, (f'%{company_name}%',))

    formatted = []
    for ref, title, status, cat, value in results:
        formatted.append((ref, title[:50], status, cat, f"${value:,.0f}" if value else "N/A"))

    print_table(
        ["Reference", "Title", "Status", "Category", "Value"],
        formatted,
        f"Postings where '{company_name}' showed interest"
    )


def recent_awards(limit=20):
    """Show most recent contract awards."""
    results = query("""
        SELECT o.reference_number, o.short_title, a.winner_name, a.award_amount, a.award_date
        FROM awards a
        JOIN opportunities o ON a.opportunity_ref = o.reference_number
        ORDER BY a.award_date DESC
        LIMIT ?
    """, (limit,))

    formatted = []
    for ref, title, winner, amount, date in results:
        formatted.append((ref, title[:40], winner[:30], f"${amount:,.0f}" if amount else "N/A", date))

    print_table(
        ["Reference", "Title", "Winner", "Amount", "Date"],
        formatted,
        f"Most Recent {limit} Contract Awards"
    )


def open_opportunities(limit=20):
    """Show currently open opportunities."""
    results = query("""
        SELECT reference_number, short_title, category_code, close_date, num_interested_suppliers
        FROM opportunities
        WHERE status_code = 'OPEN'
        ORDER BY close_date
        LIMIT ?
    """, (limit,))

    formatted = []
    for ref, title, cat, close, interested in results:
        formatted.append((ref, title[:50], cat, close, interested))

    print_table(
        ["Reference", "Title", "Category", "Close Date", "Interested"],
        formatted,
        f"Currently Open Opportunities ({limit} max)"
    )


# ========================================
# Interactive Menu
# ========================================

def interactive_menu():
    """Interactive query menu."""
    while True:
        print("\n" + "="*70)
        print("ALBERTA PROCUREMENT DATABASE - QUERY MENU")
        print("="*70)
        print("\n1. Database Overview")
        print("2. Search by Keyword")
        print("3. Recent Construction Projects")
        print("4. Top Bidders")
        print("5. Top Contract Winners")
        print("6. Posting Details (by reference number)")
        print("7. Company Interest History")
        print("8. Recent Contract Awards")
        print("9. Open Opportunities")
        print("0. Exit")

        choice = input("\nEnter your choice (0-9): ").strip()

        if choice == '1':
            overview()
        elif choice == '2':
            keyword = input("Enter keyword to search: ").strip()
            search_by_keyword(keyword)
        elif choice == '3':
            construction_projects()
        elif choice == '4':
            top_bidders()
        elif choice == '5':
            top_winners()
        elif choice == '6':
            ref = input("Enter reference number (e.g., AB-2025-00001): ").strip()
            posting_details(ref)
        elif choice == '7':
            company = input("Enter company name: ").strip()
            interested_by_company(company)
        elif choice == '8':
            recent_awards()
        elif choice == '9':
            open_opportunities()
        elif choice == '0':
            print("\nGoodbye!")
            break
        else:
            print("\nInvalid choice. Please try again.")


if __name__ == "__main__":
    import sys

    # Check if database exists
    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        print("Please run the scraper first to create the database.")
        sys.exit(1)

    # If arguments provided, run specific query
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == 'overview':
            overview()
        elif command == 'construction':
            construction_projects()
        elif command == 'bidders':
            top_bidders()
        elif command == 'winners':
            top_winners()
        elif command == 'awards':
            recent_awards()
        elif command == 'open':
            open_opportunities()
        elif command == 'search' and len(sys.argv) > 2:
            search_by_keyword(' '.join(sys.argv[2:]))
        elif command == 'details' and len(sys.argv) > 2:
            posting_details(sys.argv[2])
        else:
            print(f"Unknown command: {command}")
            print("\nAvailable commands:")
            print("  python query_database.py overview")
            print("  python query_database.py construction")
            print("  python query_database.py bidders")
            print("  python query_database.py winners")
            print("  python query_database.py awards")
            print("  python query_database.py open")
            print("  python query_database.py search <keyword>")
            print("  python query_database.py details <reference>")
    else:
        # Interactive mode
        interactive_menu()
