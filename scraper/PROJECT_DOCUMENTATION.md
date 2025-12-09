# Alberta Purchasing Connection - Contract Scraper

## Project Overview

**Purpose**: Build a historical database of awarded construction contracts from Alberta Purchasing Connection to enable bidding strategy analysis and competitive intelligence.

**Data Source**: Alberta government public procurement API
- **API Endpoint**: `https://purchasing.alberta.ca/api/opportunity/public/{year}/{id}`
- **Web Portal**: https://purchasing.alberta.ca/

## Project Motivation

This scraper enables construction companies to:
1. **Competitive Intelligence**: See all bidders and their bid amounts on past projects
2. **Win Rate Analysis**: Track which companies win contracts and at what price points
3. **Pricing Strategy**: Analyze bid spreads, identify competitive positioning
4. **Market Research**: Understand bidding patterns, identify active competitors
5. **Historical Database**: Build a comprehensive dataset for long-term trend analysis

## Key Features

### Data Extracted
- **Project Details**: Title, description, dates, requirements, region
- **Bidder Information**: All companies that bid, their bid amounts, locations
- **Award Data**: Winner, award amount, award date
- **Competition Metrics**: Number of bidders, interested suppliers
- **Contact Information**: Project contacts, phone, email
- **Bid Analysis**: Lowest/highest bids, spread, averages, percentages

### Outputs Generated
1. **Contracts CSV** (`alberta_contracts_YYYY_XXXX-XXXX.csv`): Main contract data with one row per project
2. **Bids CSV** (`alberta_bids_YYYY_XXXX-XXXX.csv`): Detailed bidder data with one row per bid
3. **Raw JSON** (`alberta_contracts_raw_YYYY_XXXX-XXXX.json`): Complete API responses for future analysis

## Technical Architecture

### Implementation: Jupyter Notebook
- **File**: [alberta_contract_scraper.ipynb](alberta_contract_scraper.ipynb)
- **Language**: Python
- **Key Libraries**: requests, pandas, json

### Core Components

1. **API Client** (Cell 3)
   - `fetch_opportunity(year, posting_num)`: Fetches single posting from API
   - Session management with proper headers
   - Error handling for 404s and timeouts
   - Respectful rate limiting (1 second delay)

2. **Data Extraction** (Cell 3)
   - `extract_contract_data(raw)`: Transforms raw JSON into flat structure
   - Handles nested data (bidders, awards, contacts)
   - Calculates bid statistics (spreads, averages, rankings)

3. **Batch Scraper** (Cell 6)
   - `scrape_opportunities()`: Scrapes ranges of posting numbers
   - Filters by status (e.g., 'AWARD' for awarded contracts)
   - Filters by category (e.g., 'CNST' for construction)
   - Progress tracking during scraping

4. **Data Management** (Cell 13)
   - `load_contracts()`: Loads previously scraped data
   - `combine_datasets()`: Merges multiple datasets, removes duplicates
   - Supports incremental scraping

## Current Status - COMPLETE ✓

### 2025 Full Dataset - SCRAPING COMPLETE (December 8, 2025)
- **Scraping Range**: AB-2025-00001 to AB-2025-07557 (complete year)
- **Total Postings Found**: 6,607 opportunities
- **Success Rate**: 99.93% (only 5 errors out of 7,557 attempts)
- **Scraping Time**: ~3.5 hours total
- **Database Size**: alberta_procurement.db with 182,348 total records

### Comprehensive Data Collected
- **All Categories**:
  - Services (SRV): 3,278 postings
  - Goods (GD): 1,733 postings
  - Construction (CNST): 1,596 postings

- **All Statuses**:
  - Awarded: 3,014 contracts
  - Under Evaluation: 1,977 postings
  - Open for Bidding: 881 opportunities
  - Closed: 376 postings
  - Cancelled: 225 postings
  - Unawardable: 105 postings
  - Selection: 29 postings

- **Detailed Records**:
  - Bidders: 3,895 bid submissions
  - Interested Suppliers: 137,153 expressions of interest
  - Awards: 3,896 contract awards
  - Documents: 15,877 document attachments
  - Contacts: 6,613 contact records

### Sample Data Collected (Initial Test)
- **Date Range**: Test scrape of postings AB-2025-04050 to AB-2025-04070
- **Contracts Found**: 6 awarded construction contracts
- **Total Value**: $12,153,190
- **Bidder Records**: 12 individual bids across all projects

### Example Results
- **Best Competition**: AB-2025-04058 had 12 bidders (71 interested suppliers)
  - Bridge construction project
  - Bid spread: $995,816 (79.7% difference between lowest and highest)
  - Winner bid 25% below average

## Usage Instructions

### Quick Start
```python
# 1. Run setup cells (1-3)
# 2. Test single posting
raw_data = fetch_opportunity(2025, 4058)
contract = extract_contract_data(raw_data)

# 3. Batch scrape
contracts, raw_data = scrape_opportunities(
    year=2025,
    start_num=4000,
    end_num=4100,
    status_filter='AWARD',
    category_filter='CNST'
)

# 4. Save results (runs automatically)
```

### Incremental Scraping Strategy
```python
# Scrape in batches to avoid rate limiting
# Postings are numbered sequentially (e.g., 4000, 4001, 4002...)

# Week 1: Scrape 4000-4100
# Week 2: Scrape 4100-4200
# Week 3: Combine datasets

df1 = load_contracts("alberta_contracts_2025_4000-4100.csv")
df2 = load_contracts("alberta_contracts_2025_4100-4200.csv")
combined = combine_datasets(df1, df2)
```

## Data Schema

### Contracts CSV Columns
- `reference_number`: Unique ID (e.g., AB-2025-04058)
- `title`: Short project title
- `description`: Full project description
- `status`: AWARD, CLOSED, etc.
- `category_code`: CNST (construction), etc.
- `num_bidders`: Count of companies that submitted bids
- `num_interested`: Count of suppliers that expressed interest
- `lowest_bid`, `highest_bid`, `bid_spread`, `avg_bid`: Bid statistics
- `award_amount`: Final contract value
- `award_date`: Date contract was awarded
- `winner_name`, `winner_city`: Winning company details
- `contact_name`, `contact_email`, `contact_phone`: Project contact
- `region`: Geographic area
- `post_date`, `close_date`: Tender timeline

### Bids CSV Columns
- `reference_number`: Links to contract
- `project_title`: Short title
- `bidder_name`: Company name
- `bid_amount`: Their bid
- `bidder_city`: Location
- `is_winner`: True/False
- `award_amount`: Final contract value
- `bid_diff_from_award`: How much above/below winner
- `pct_above_winner`: Percentage difference

## Known Issues & Considerations

### API Behavior
- Not all postings have bidder data visible (some contracts show 0 bidders even when awarded)
- 404 responses are normal (not all posting numbers exist)
- Some older postings may not be available via API

### Rate Limiting
- Currently using 1 second delay between requests
- Alberta government does not publish rate limits
- Be respectful: Don't scrape during peak business hours if possible

### Data Quality
- Some contracts missing bid amounts (may be negotiated or restricted data)
- Contact information occasionally incomplete
- City names have inconsistent formatting

## Future Enhancements

### Potential Features
- [ ] Automated daily scraping of new postings
- [ ] Database storage (SQLite or PostgreSQL)
- [ ] Interactive dashboard for bid analysis
- [ ] Email alerts for new relevant postings
- [ ] Machine learning for bid prediction
- [ ] Historical trend analysis and visualization
- [ ] Competitor tracking and profiling
- [ ] Geographic analysis of project locations

### Scalability
- [ ] Multi-year scraping (2020-2025)
- [ ] Parallel requests (with careful rate limiting)
- [ ] Retry logic for failed requests
- [ ] Logging and error tracking
- [ ] Resume capability for interrupted scrapes

## Compliance & Ethics

### Legal Considerations
✅ **Publicly Available Data**: All data is from public government procurement portal
✅ **No Authentication Required**: API endpoints are open access
✅ **Respectful Scraping**: Implements delays, proper User-Agent
✅ **Legitimate Use**: Competitive research is standard business practice

### Best Practices
- Always respect robots.txt (if applicable)
- Don't overload the server with rapid requests
- Use the data responsibly and ethically
- Keep API responses for reference (raw JSON files)

## Discovery Process (From Previous Chat)

### Initial Approach
Started by examining the public posting page structure:
- **Web URL**: https://purchasing.alberta.ca/posting/AB-2025-04058
- Initially attempted to scrape the rendered HTML page

### Key Breakthrough 🎯
Discovered the **public API endpoint** that powers the website:
- **API URL**: `https://purchasing.alberta.ca/api/opportunity/public/2025/4058`
- Returns complete JSON with ALL data including bidder details
- Much more reliable than HTML scraping
- No authentication required
- Includes data not visible on the web page (full bidder lists, contact info)

### Core Business Objective
**Goal**: Build a predictive bidding system using historical data

**Use Case**: When a new construction posting appears, use historical data to:
1. Estimate the likely winning bid amount
2. Understand competitive landscape (who else might bid)
3. Determine optimal bid price to maximize win probability while maintaining margins
4. Identify pricing patterns based on:
   - Project type and scope
   - Geographic region
   - Number of competitors
   - Historical bid spreads
   - Seasonal trends
   - Specific winning company patterns

**Current Focus**: Scraping awarded contracts only (may expand to CLOSED, OPEN, CANCELLED later)

## Change Log

### Version 2.0 (Current - December 7-8, 2025) 🎯
**MAJOR UPDATE: SQLite Database Integration - COMPLETE**
- ✅ Created SQLite database with hybrid storage (raw JSON + normalized tables)
- ✅ 8 tables: raw_data, opportunities, bidders, interested_suppliers, awards, documents, contacts, scrape_log
- ✅ **Removed all filters** - now scrapes ALL postings (AWARD, OPEN, CLOSED, EVALUATION, CANCELLED, etc.)
- ✅ Enhanced scraper with resume capability (skips already-scraped postings)
- ✅ Progress tracking and error handling
- ✅ Database indexes for fast queries
- ✅ Query helper script for data exploration
- ✅ **COMPLETED:** Full 2025 scrape (1-7557) - 6,607 postings found
- ✅ **Success Rate:** 99.93% (only 5 errors out of 7,557 attempts)
- ✅ **Duration:** ~3.5 hours total scraping time

**Complete 2025 Dataset Captured:**
- ALL categories: Services (3,278), Goods (1,733), Construction (1,596), plus others
- ALL statuses: Awarded (3,014), Evaluation (1,977), Open (881), Closed (376), Cancelled (225), etc.
- Interested suppliers: 137,153 expressions of interest (massive lead database!)
- Complete bidder information: 3,895 bid submissions with contact details
- Document metadata: 15,877 document attachments tracked
- Full contact information: 6,613 contact records for all postings
- Awards: 3,896 contract awards with amounts and dates

### Version 1.0 (December 2025)
- Initial notebook implementation
- Discovered and integrated public API endpoint
- Basic API client with error handling
- Batch scraping with status/category filters
- CSV and JSON export functionality
- Sample data collection (AB-2025-04050 to 04070)
- Bid analysis and statistics
- Created project documentation

## Next Steps

### Immediate Tasks - COMPLETED ✓
- [x] Create working scraper prototype
- [x] Test with sample data (AB-2025-04050 to 04070)
- [x] Document project and methodology
- [x] **Determine optimal scraping strategy**
  - ✅ Started with 2025 (complete year scraped)
  - ✅ Discovered posting range: 1 to 7,557
  - ✅ Successfully collected 6,607 postings
  - ✅ Implemented incremental scraping approach

### Short-term Goals (READY TO START)
- [x] Scale up scraping to collect substantial historical data ✅ 2025 complete!
- [x] Improve error handling (missing data, network issues, timeouts) ✅ 99.93% success rate
- [x] Database storage (SQLite for easier querying) ✅ Fully implemented
- [ ] **Next: Scrape 2024 and 2023 data** (estimated ~15,000 more postings)
- [ ] Create initial exploratory data analysis notebook:
  - Distribution of project values
  - Bid spread analysis
  - Competitor frequency analysis
  - Regional pricing differences
  - Temporal trends (seasonality)

### Medium-term Goals (Next 1-3 months)
- [ ] Build simple predictive models
  - Linear regression for bid amount prediction
  - Feature engineering (project type, size, region, etc.)
  - Validate model accuracy on holdout set
- [ ] Create visualization dashboard
  - Interactive charts for exploring data
  - Competitor profiles and win rates
  - Geographic heat maps
- [ ] Automated monitoring system for new postings

### Long-term Vision
- [ ] Advanced machine learning models for bid optimization
- [ ] Real-time alerts for relevant opportunities
- [ ] Integration with company bidding workflow
- [ ] Competitive intelligence reports
- [ ] ROI tracking (track actual bids vs predictions)

---

**Last Updated**: 2025-12-08
**Current Data Range**: Complete 2025 (AB-2025-00001 to AB-2025-07557)
**Total Dataset**: 6,607 postings with 182,348 total records across all tables
**Project Status**: 2025 Complete ✓ - Ready for analysis or historical scraping (2024, 2023)