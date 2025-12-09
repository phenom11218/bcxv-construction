# 🏗️ BCXV Construction - Bid Analytics Platform

**Predict optimal construction bid amounts using AI-powered analysis of historical Alberta procurement data.**

---

## 📊 Overview

BCXV Construction is a Streamlit-based analytics platform that helps construction companies:
- **Analyze** 831 awarded construction projects from Alberta Purchasing Connection
- **Predict** winning bid amounts based on historical similarity
- **Track** competitor bidding patterns and win rates
- **Optimize** bid strategies using data-driven insights

### Current Status: Phase 1 Complete ✓

**What's Working:**
- ✓ Database connection to 6,607 procurement records
- ✓ Core query utilities for construction project data
- ✓ Streamlit app skeleton with navigation
- ✓ Git integration with proper branching

**Coming Next:** Phase 2 - Historical Project Explorer

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Access to Alberta Procurement database (`alberta_procurement.db`)
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/phenom11218/bcxv-construction.git
   cd bcxv-construction
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**

   **Windows:**
   ```bash
   venv\Scripts\activate
   ```

   **Mac/Linux:**
   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Verify database location:**
   The app expects the database at:
   ```
   ../scraper/Alberta Purchasing Construction/alberta_procurement.db
   ```

   If your database is elsewhere, you can modify the path in `streamlit_app/utils/database.py`

6. **Test database connection:**
   ```bash
   cd streamlit_app/utils
   python database.py
   ```

   You should see:
   ```
   [OK] Connected to database
   [OK] Database Statistics
   ALL TESTS PASSED [SUCCESS]
   ```

7. **Run the app:**
   ```bash
   cd streamlit_app
   streamlit run app.py
   ```

8. **Open your browser:**
   Navigate to `http://localhost:8501`

---

## 📁 Project Structure

```
bcxv-construction/
├── streamlit_app/
│   ├── app.py                     # Main Streamlit application
│   ├── pages/                      # Multi-page app pages (coming in Phase 2+)
│   │   ├── 1_📊_Explorer.py       # Project browser (Phase 2)
│   │   ├── 2_🎯_Predictor.py      # Bid prediction tool (Phase 4)
│   │   ├── 3_📈_Analytics.py      # Dashboard (Phase 5)
│   │   └── 4_🕵️_Competitors.py    # Competitor intel (Phase 6)
│   └── utils/
│       ├── database.py             # Database connection & queries ✓
│       ├── similarity.py           # Project matching logic (Phase 3)
│       ├── predictor.py            # Bid prediction models (Phase 4)
│       └── text_processing.py      # NLP utilities (Phase 3)
├── .streamlit/
│   └── config.toml                 # Streamlit configuration
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── DEVELOPMENT.md                  # Development log (coming)
└── .gitignore                      # Git ignore patterns

```

---

## 🎯 Features

### Phase 1: Setup ✓ COMPLETE
- Database connection utilities
- Core query functions for construction projects
- Streamlit app skeleton
- Git workflow established

### Phase 2: Historical Project Explorer (Next)
- Browse 831 awarded construction projects
- Filter by value, region, project type
- View detailed bid breakdowns
- Export data for offline analysis

### Phase 3: Text Processing & Similarity Engine
- Keyword extraction from project titles/descriptions
- Project type classification (road, bridge, building, etc.)
- Similarity scoring algorithm
- Find 10-20 most similar historical projects

### Phase 4: Bid Prediction Tool
- Simple predictor: Average of similar projects
- ML model: Regression on 172 projects with full bid data
- Confidence intervals and win probability
- Expected number of bidders

### Phase 5: Analytics Dashboard
- Award amount trends over time
- Regional competition heatmaps
- Bid spread analysis by project type
- Seasonal bidding patterns

### Phase 6: Competitor Intelligence & Polish
- Track competitor win rates
- Analyze bidding strategies (high/low)
- Monitor recent competitor activity
- UI/UX improvements and production deployment

---

## 📊 Data Source

**Alberta Purchasing Connection**
- **Website**: https://purchasing.alberta.ca/
- **API**: Undocumented public API (discovered through analysis)
- **Data Coverage**: 2025 (6,607 opportunities)
- **Construction Projects**: 1,596 (24.2% of total)
- **Awarded Contracts**: 831 construction projects

### Database Schema

**8 Tables with 182,348 total records:**

1. **opportunities** (6,607 rows) - Main project data
2. **bidders** (3,895 rows) - Company bids with amounts
3. **awards** (3,896 rows) - Contract awards
4. **interested_suppliers** (137,153 rows) - Companies that expressed interest
5. **documents** (15,877 rows) - Attachment metadata
6. **contacts** (6,613 rows) - Project contact information
7. **raw_data** (6,607 rows) - Complete JSON backups
8. **scrape_log** (7,557 rows) - Scraping history

---

## 🛠️ Development

### Git Workflow

**IMPORTANT: Never push to main!**

Always use feature branches with date convention:
```bash
git checkout -b feature/YYYY-MM-DD-phase-N-description
```

Example:
```bash
git checkout -b feature/2025-12-08-phase-2-explorer
```

### Testing Database Connection

```bash
cd streamlit_app/utils
python database.py
```

Expected output:
```
================================================================================
TESTING DATABASE CONNECTION
================================================================================
[OK] Connected to database: .../alberta_procurement.db

[OK] Database Statistics:
  Total Projects: 6,607
  Construction Projects: 1,596
  Awarded Projects: 3,014
  Year Range: 2025 to 2025
...
ALL TESTS PASSED [SUCCESS]
================================================================================
```

---

## 📖 Documentation

- **README.md** (this file) - Project overview and setup
- **DEVELOPMENT.md** - Phase-by-phase development log (coming)
- **API_REFERENCE.md** - Code documentation (coming)
- **USER_GUIDE.md** - End-user instructions (coming)

---

## 🤝 Contributing

This is a private project for BCXV Construction. Development follows a phased approach:

1. Each phase is developed on a feature branch
2. Branch naming: `feature/YYYY-MM-DD-phase-N-description`
3. Merge to main via pull request after phase completion
4. Comprehensive documentation at each phase

---

## 📋 Phase Roadmap

| Phase | Status | Description | Est. Time |
|-------|--------|-------------|-----------|
| **1** | ✓ COMPLETE | Project setup & Git integration | 1-2 hours |
| **2** | Planned | Historical project explorer | 2-3 hours |
| **3** | Planned | Text processing & similarity engine | 3-4 hours |
| **4** | Planned | Bid prediction tool | 4-5 hours |
| **5** | Planned | Analytics dashboard | 3-4 hours |
| **6** | Planned | Competitor intelligence & polish | 2-3 hours |

**Total Estimated Development**: 15-21 hours across 6 phases

---

## 🔐 Data Privacy & Ethics

✅ **Public Data**: All data from government public procurement portal
✅ **Open Access**: No authentication required
✅ **Legitimate Use**: Competitive research is standard business practice
✅ **Attribution**: Full credit to Alberta Purchasing Connection

---

## 📞 Support

- **GitHub Issues**: https://github.com/phenom11218/bcxv-construction/issues
- **Repository**: https://github.com/phenom11218/bcxv-construction

---

## 📄 License

Private project - All rights reserved to BCXV Construction

---

**Last Updated**: December 8, 2025
**Version**: 1.0.0 (Phase 1)
**Status**: Phase 1 Complete ✓ | Phase 2 Next