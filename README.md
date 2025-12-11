# Alberta Procurement Analytics

**Complete platform for scraping, analyzing, and predicting Alberta construction bid data**

![Status](https://img.shields.io/badge/Scraper-Complete-success)
![Status](https://img.shields.io/badge/Analytics-Phase%202%20Complete-blue)
![Data](https://img.shields.io/badge/Projects-6,607-informational)
![Database](https://img.shields.io/badge/Database-461MB-orange)

---

## 📊 Project Overview

This unified repository contains both the **data scraper** and the **analytics application** for Alberta government procurement data. The platform enables contractors to analyze historical bid data, compare similar projects, and make data-driven bidding decisions.

### Components

1. **[scraper/](scraper/)** - Data collection from Alberta Purchasing Connection
   - 6,607 opportunities scraped (2025 complete)
   - 1,596 construction projects identified
   - 831 awarded construction contracts with bid data

2. **[analytics-app/](analytics-app/)** - Interactive Streamlit web application
   - ✅ Phase 1: Database integration & setup
   - ✅ Phase 2: Historical Project Explorer with filtering & analytics
   - 🚧 Phase 3: ML-powered bid prediction (coming next)

3. **alberta_procurement.db** - Shared SQLite database
   - 461 MB, 182,348 total records
   - 8 tables with comprehensive procurement data
   - Hybrid storage: Raw JSON + normalized tables

---

## 🚀 Quick Start

### Analytics App (Recommended - Start Here!)

The easiest way to explore the data:

**For Git Bash (recommended):**
```bash
cd analytics-app
./run_app.sh
```

**For Windows CMD:**
```cmd
cd analytics-app
run_app.bat
```

Both scripts will:
1. ✅ Activate virtual environment
2. ✅ Test database connection
3. ✅ Launch web app in your browser

**Manual start** (if you prefer):
```bash
cd analytics-app
source venv/Scripts/activate  # Git Bash
# OR
venv\Scripts\activate.bat     # Windows CMD

streamlit run app.py
```

The app will open at `http://localhost:8501`

### Scraper (Data Collection)

The scraper can collect data from **any year** (2010-2025+):

```bash
cd scraper

# Monitor progress for ALL years
python check_progress.py

# Scrape specific year
python alberta_scraper_sqlite.py 2024 1 10284

# Find endpoint for a year
python find_endpoint.py 2024
```

**📖 Complete guide**: [MULTI_YEAR_SCRAPING_GUIDE.md](MULTI_YEAR_SCRAPING_GUIDE.md) | **Quick ref**: See below

---

## 📂 Project Structure

```
Alberta Purchasing Construction/
├── alberta_procurement.db        # Shared database (441 MB, growing)
├── MULTI_YEAR_SCRAPING_GUIDE.md  # Complete multi-year scraping guide
│
├── scraper/                      # Data Collection (Multi-Year Ready ✓)
│   ├── alberta_scraper_sqlite.py # Main scraper (year-agnostic)
│   ├── check_progress.py         # Universal progress monitor
│   ├── find_endpoint.py          # Universal endpoint detector
│   ├── database_setup.py         # Schema creation
│   ├── QUICK_START.md            # Quick reference card
│   └── query_database.py         # Interactive queries
│
└── analytics-app/                # Web Application (Phase 2 Complete ✓)
    ├── app.py                    # Main Streamlit app
    ├── run_app.sh               # Quick-start script (Git Bash)
    ├── run_app.bat              # Quick-start script (Windows CMD)
    ├── pages/
    │   └── 1_📊_Explorer.py     # Historical Project Explorer
    ├── utils/
    │   └── database.py          # Database query utilities
    ├── venv/                    # Python virtual environment
    ├── requirements.txt         # Dependencies
    ├── PHASE1_COMPLETE.md       # Phase 1 documentation
    └── PHASE2_COMPLETE.md       # Phase 2 documentation
```

---

## 🎯 Analytics App Features

### ✅ Phase 1: Project Setup & Git Integration (Complete)
- GitHub repository with feature branch workflow
- Database connection utilities (6 specialized query methods)
- Streamlit app skeleton with navigation
- Virtual environment setup
- 100% test coverage on database queries

### ✅ Phase 2: Historical Project Explorer (Complete)

**📊 Explorer Page** - Browse all 831 awarded construction projects:

**Advanced Filtering:**
- 💵 Value range (min/max dollar amounts)
- 🌍 Region (city or area)
- 🔍 Keywords (search titles/descriptions)
- 📅 Date range (award dates)

**Project Details:**
- Click any project to view complete bid information
- See all bids received (not just the winner)
- Bid statistics: lowest, highest, average, spread %
- Interactive charts comparing all bids (Plotly)
- Winner identification (green highlighting)

**Analytics & Visualizations:**
- Summary metrics (total value, average, median)
- Value distribution histogram
- Regional distribution (top 10 regions)
- Award timeline (monthly trends)

**Export Functionality:**
- Download filtered results as CSV or JSON
- Timestamped filenames
- Preview before export

### 🚧 Coming Next: Phase 3 - ML Bid Prediction
- Text processing & similarity engine
- Find comparable historical projects
- Predict bid amounts using ML regression
- Confidence intervals & competition analysis

---

## 📊 Data Overview (2025 Complete)

### Overall Statistics
- **6,607** total opportunities
- **1,596** construction projects (24.2%)
- **831** awarded construction contracts
- **172** projects with full bid data (for ML training)
- **3,014** total awarded contracts (all categories)
- **137,153** interested supplier records
- **99.93%** scraping success rate (5 errors / 7,557 attempts)

### Database Tables
1. `opportunities` - Main project records
2. `bids` - Individual bid amounts and suppliers
3. `interested_suppliers` - Companies that viewed postings
4. `commodity_codes` - Project classification codes
5. `documents` - Attachment metadata
6. `raw_json` - Complete API responses
7. `scraping_log` - Data collection audit trail
8. `statuses` - Opportunity status history

---

## 🔄 Multi-Year Data Collection

The scraper supports **any year from 2010-2025+** using year-agnostic tools.

### Check Progress for All Years

```bash
cd scraper
python check_progress.py           # Auto-detects all years in database
```

**Output example:**
```
Year | Attempts | Found | 404s  | Range       | CNST | Status
2025 |    7,557 | 6,604 |   948 |   1- 7557   |1,596 | Complete
2024 |      500 |   110 |   390 |   1-  500   |   14 | 500/10284 (4.9%)
```

### Find Endpoint for Any Year

Before scraping a new year, find its max posting number:

```bash
python find_endpoint.py 2024           # Find 2024 endpoint from start
python find_endpoint.py 2024 10284     # Test from 10284 onwards
python find_endpoint.py 2023           # Find 2023 endpoint
```

The tool automatically stops after 50 consecutive 404s (configurable).

### Scrape Historical Data

Once you know the endpoint, scrape the full year:

```bash
# Single batch (small years)
python alberta_scraper_sqlite.py 2024 1 10284

# Multiple batches (large years - recommended)
python alberta_scraper_sqlite.py 2024 1 5000
python alberta_scraper_sqlite.py 2024 5001 10284
```

**Features:**
- ✅ Works with ANY year (2010-2099)
- ✅ Resume capability (skips already-scraped postings)
- ✅ Real-time progress monitoring
- ✅ Respectful rate limiting (1-second delays)
- ✅ Year-agnostic database schema

**Estimated timelines:**
- Single year (~10,000 postings): 3-4 hours
- 2010-2023 (14 years): 2-4 weeks total

**📖 Complete Guide:** See [MULTI_YEAR_SCRAPING_GUIDE.md](MULTI_YEAR_SCRAPING_GUIDE.md) for:
- Step-by-step workflows
- Year-by-year examples
- Troubleshooting tips
- Best practices
- Advanced configurations

---

## 💡 How to Use the Analytics App

### Example Workflow 1: Find Similar Projects
1. Launch app: `run_app.bat`
2. Click **📊 Explorer** in sidebar
3. Set filters:
   - Min Value: $500,000
   - Keywords: "road construction"
   - Region: "Calgary"
4. Click "Apply Filters"
5. Browse results, click project for bid details

### Example Workflow 2: Analyze Regional Trends
1. Navigate to **📊 Explorer**
2. Click "Load All Projects"
3. Switch to **Statistics** tab
4. View regional distribution chart
5. Analyze timeline trends

### Example Workflow 3: Export Data for Analysis
1. Filter projects by your criteria
2. Switch to **Export** tab
3. Choose CSV or JSON format
4. Click download
5. Open in Excel or your preferred tool

---

## 🔧 Tech Stack

### Backend
- **Python 3.8+** - Core language
- **SQLite** - Database (461 MB, production-ready)
- **pandas** - Data manipulation
- **requests** - HTTP scraping

### Frontend (Analytics App)
- **Streamlit** - Web framework
- **Plotly** - Interactive visualizations
- **plotly.express** - Quick charts
- **altair** - Alternative charting

### ML/Analytics (Phase 3+)
- **scikit-learn** - Machine learning
- **numpy** - Numerical computing
- **python-dateutil** - Date handling

### Development
- **Git/GitHub** - Version control with feature branch workflow
- **Virtual Environment** - Isolated dependencies

---

## 📖 Documentation

### Analytics App
- **[PHASE1_COMPLETE.md](analytics-app/PHASE1_COMPLETE.md)** - Setup & database integration
- **[PHASE2_COMPLETE.md](analytics-app/PHASE2_COMPLETE.md)** - Historical Project Explorer
- **[utils/database.py](analytics-app/utils/database.py)** - Database API reference (inline docs)

### Scraper
- **[scraper/SESSION_SUMMARY.md](scraper/SESSION_SUMMARY.md)** - Complete scraping guide
- **[scraper/README.md](scraper/README.md)** - Quick reference

---

## 🌲 Git Workflow

This project uses a **feature branch workflow** - we NEVER push directly to main!

### Current Branches
- `feature/2025-12-08-phase-1-setup` - Phase 1 work (merged ready)
- `feature/2025-12-08-phase-2-explorer` - Phase 2 work (current)

### Branch Naming Convention
```
feature/YYYY-MM-DD-phase-N-description
```

### Workflow
1. Create dated feature branch from main
2. Develop and test on feature branch
3. Commit with descriptive messages
4. Push feature branch to origin
5. Create Pull Request for review
6. Merge to main after approval

**Example:**
```bash
git checkout -b feature/2025-12-09-phase-3-ml
# ... make changes ...
git add -A
git commit -m "Phase 3: Add similarity engine"
git push -u origin feature/2025-12-09-phase-3-ml
```

---

## 🎯 Development Status

| Component | Status | Details |
|-----------|--------|---------|
| **Scraper** | ✅ Complete | 2025 data fully scraped (6,607 opportunities) |
| **Phase 1** | ✅ Complete | Database utilities, app skeleton, Git setup |
| **Phase 2** | ✅ Complete | Historical Explorer with filtering & analytics |
| **Phase 3** | 🚧 Planned | Text processing & similarity engine |
| **Phase 4** | 📋 Planned | ML bid prediction tool |
| **Phase 5** | 📋 Planned | Advanced analytics dashboard |
| **Phase 6** | 📋 Planned | Competitor intelligence & polish |

---

## 🤝 Development Roadmap

### ✅ Completed
- [x] Scrape all 2025 Alberta procurement data
- [x] Build SQLite database with 8 normalized tables
- [x] Create Streamlit web application
- [x] Implement database query utilities
- [x] Build Historical Project Explorer
- [x] Add advanced filtering (value, region, keywords, dates)
- [x] Create bid analytics with visualizations
- [x] Add CSV/JSON export functionality

### 🚧 In Progress
- [ ] Text processing for project descriptions
- [ ] Keyword extraction & project classification
- [ ] Similarity scoring algorithm

### 📋 Upcoming
- [ ] ML regression model for bid prediction
- [ ] Confidence interval calculations
- [ ] Competition heatmaps
- [ ] Regional analysis maps
- [ ] Competitor tracking page
- [ ] Production deployment

---

## 🐛 Known Issues

1. **Empty `streamlit_app/` folder** in analytics-app/ (locked by Windows, harmless)
2. **Excel export** not yet implemented (use CSV for now)
3. **Large result sets** may be slow (pagination coming in Phase 5)

---

## 📞 Support & Feedback

- **Issues**: Report bugs via GitHub Issues
- **Documentation**: See individual phase completion docs
- **Questions**: Check inline code documentation

---

## 📝 License

Private repository - All rights reserved

---

**Last Updated**: December 8, 2025 | **Version**: 2.0.0 (Phase 2 Complete)

**Repository**: https://github.com/phenom11218/bcxv-construction

---

## 🚀 Getting Started Checklist

- [ ] Clone repository
- [ ] Navigate to `analytics-app/`
- [ ] Run `./run_app.sh` (Git Bash) or `run_app.bat` (Windows CMD)
- [ ] Click **📊 Explorer** in sidebar
- [ ] Start exploring 831 construction projects!

**That's it!** The database is already populated with 2025 data. Just launch and explore! 🎉