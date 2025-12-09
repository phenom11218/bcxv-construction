# Alberta Procurement Analytics

**Complete platform for scraping, analyzing, and predicting Alberta construction bid data**

---

## 📊 Project Overview

This unified repository contains both the **data scraper** and the **analytics application** for Alberta government procurement data.

### Components

1. **[scraper/](scraper/)** - Data collection tools (6,607 opportunities collected)
2. **[analytics-app/](analytics-app/)** - Streamlit web application for bid analytics
3. **alberta_procurement.db** - Shared database (461 MB, 182,348 records)

---

## 🚀 Quick Start

### Scraper (Data Collection)
```bash
cd scraper
python database_setup.py     # View stats
python query_database.py      # Interactive queries
```
**Full docs**: [scraper/README.md](scraper/README.md)

### Analytics App (Web Dashboard)
```bash
cd analytics-app
python -m venv venv
source venv/Scripts/activate  # Windows Git Bash
pip install -r requirements.txt
cd streamlit_app && streamlit run app.py
```
**Full docs**: [analytics-app/README.md](analytics-app/README.md)

---

## 📂 Structure

```
Alberta Purchasing Construction/
├── scraper/              # Data collection (Complete ✓)
├── analytics-app/        # Web app (Phase 1 Complete ✓)
└── alberta_procurement.db  # Shared database
```

---

## 📊 Data (2025 Complete)

- **6,607** total opportunities
- **1,596** construction projects (24.2%)
- **3,014** awarded contracts
- **137,153** interested supplier records
- **Success Rate**: 99.93% (5 errors / 7,557 attempts)

---

## 🔧 Tech Stack

- Python 3.8+, SQLite, Streamlit
- pandas, plotly, scikit-learn
- Git/GitHub

---

## 📖 Documentation

- **[scraper/SESSION_SUMMARY.md](scraper/SESSION_SUMMARY.md)** - Complete scraper guide
- **[analytics-app/DEVELOPMENT.md](analytics-app/DEVELOPMENT.md)** - App development log
- **[analytics-app/PHASE1_COMPLETE.md](analytics-app/PHASE1_COMPLETE.md)** - Phase 1 summary

---

## 🎯 Status

**Scraper**: ✅ Complete (2025 data)
**Analytics App**: 🚧 Phase 1 Complete, Phase 2 Starting

**Last Updated**: December 8, 2025 | **Version**: 1.0.0
