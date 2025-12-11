"""
BCXV Construction - Bid Analytics Platform
===========================================
Streamlit application for analyzing Alberta construction procurement data
and predicting optimal bid amounts using historical project similarity.

Author: BCXV Construction Analytics
Date: 2025-12-08
Phase: 1 - Project Setup
"""

import streamlit as st
import sys
from pathlib import Path

# Add utils to path for imports
sys.path.append(str(Path(__file__).parent))

from utils.database import get_smart_database_connection

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="BCXV Construction Analytics",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/phenom11218/bcxv-construction',
        'Report a bug': 'https://github.com/phenom11218/bcxv-construction/issues',
        'About': """
        # BCXV Construction Bid Analytics

        This app helps construction companies analyze historical bid data
        and predict optimal bid amounts for new opportunities.

        **Version**: 1.0.0 (Phase 1)
        **Data Source**: Alberta Purchasing Connection
        **Last Updated**: December 2025
        """
    }
)

# ============================================================================
# SIDEBAR - NAVIGATION & INFO
# ============================================================================

with st.sidebar:
    st.title("🏗️ BCXV Construction")
    st.caption("Bid Analytics Platform")

    st.markdown("---")

    # Database connection status
    st.subheader("📊 Database Status")

    try:
        # Debug: Show what's in secrets
        st.caption("🔍 Debug Info:")
        if hasattr(st, 'secrets'):
            if 'database' in st.secrets:
                st.caption(f"✓ Found [database] section, type={st.secrets['database'].get('type', 'NOT SET')}")
            else:
                st.warning("❌ No [database] section in secrets")

            if 'turso' in st.secrets:
                st.caption(f"✓ Found [turso] section")
                st.caption(f"  - database_url: {st.secrets['turso'].get('database_url', 'NOT SET')[:50]}...")
                st.caption(f"  - auth_token: {'SET' if st.secrets['turso'].get('auth_token') else 'NOT SET'}")
            else:
                st.warning("❌ No [turso] section in secrets")
        else:
            st.error("❌ st.secrets not available")

        # Initialize database connection (cached)
        @st.cache_resource
        def get_database():
            return get_smart_database_connection()

        db = get_database()
        stats = db.get_database_stats()

        st.success("✓ Connected")
        st.metric("Total Projects", f"{stats['total_projects']:,}")
        st.metric("Construction Projects", f"{stats['construction_projects']:,}")
        st.metric("Awarded Projects", f"{stats['awarded_projects']:,}")

        # Store in session state for other pages
        if 'db' not in st.session_state:
            st.session_state.db = db
            st.session_state.stats = stats

    except Exception as e:
        st.error("✗ Database connection failed")
        st.error(f"Error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        st.stop()

    st.markdown("---")

    # Navigation Info
    st.subheader("📖 Navigation")
    st.info("""
    **Current Phase: 1 - Setup Complete**

    Use the sidebar pages to navigate:
    - 📊 **Explorer**: Browse projects
    - 🎯 **Predictor**: Bid predictions
    - 📈 **Analytics**: Dashboard
    - 🕵️ **Competitors**: Intel

    *(Pages coming in future phases)*
    """)

    st.markdown("---")
    st.caption("v1.0.0 | Phase 1")

# ============================================================================
# MAIN PAGE - HOME / WELCOME
# ============================================================================

st.title("🏗️ BCXV Construction Bid Analytics Platform")
st.subheader("Predict Winning Bids Using Historical Data")

st.markdown("---")

# Welcome message and overview
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Construction Projects",
        value=f"{stats['construction_projects']:,}",
        help="Total construction category projects in database"
    )

with col2:
    st.metric(
        label="Awarded Contracts",
        value=f"{stats['awarded_projects']:,}",
        help="Projects with final award information"
    )

with col3:
    st.metric(
        label="Data Coverage",
        value=f"{stats['year_range'][0]}-{stats['year_range'][1]}",
        help="Year range of available data"
    )

st.markdown("---")

# Feature overview
st.header("🎯 Platform Features")

feature1, feature2 = st.columns(2)

with feature1:
    st.subheader("📊 Historical Project Explorer")
    st.markdown("""
    Browse and filter 831 awarded construction projects:
    - Filter by value, region, and project type
    - View detailed bid breakdowns
    - Analyze competition patterns
    - Export data for offline analysis

    *Status: Coming in Phase 2*
    """)

    st.subheader("📈 Analytics Dashboard")
    st.markdown("""
    Visualize trends and patterns:
    - Award amount trends over time
    - Regional competition heatmaps
    - Bid spread analysis by project type
    - Seasonal bidding patterns

    *Status: Coming in Phase 5*
    """)

with feature2:
    st.subheader("🎯 Bid Prediction Tool")
    st.markdown("""
    Predict optimal bid amounts for new opportunities:
    - Find similar historical projects
    - Calculate expected winning bid range
    - Assess competition level
    - Get confidence intervals

    *Status: Coming in Phase 4*
    """)

    st.subheader("🕵️ Competitor Intelligence")
    st.markdown("""
    Track competitor bidding behavior:
    - Company win rates and patterns
    - Typical project types by competitor
    - Bidding strategies (high/low)
    - Recent activity monitoring

    *Status: Coming in Phase 6*
    """)

st.markdown("---")

# Data overview section
st.header("📊 Current Data Overview")

# Category breakdown
st.subheader("Projects by Category")
category_data = stats['categories']
st.bar_chart(category_data)

# Status breakdown
st.subheader("Projects by Status")
status_data = stats['statuses']
st.bar_chart(status_data)

st.markdown("---")

# How it works
st.header("🔍 How It Works")

step1, step2, step3 = st.columns(3)

with step1:
    st.markdown("""
    ### 1️⃣ Data Collection
    Scraped from Alberta Purchasing Connection:
    - 6,607 total opportunities
    - Complete bid histories
    - 137K interested supplier records
    - Document attachments metadata
    """)

with step2:
    st.markdown("""
    ### 2️⃣ Similarity Matching
    Find similar historical projects using:
    - Project type keywords (NLP)
    - Size/value bucketing
    - Geographic region
    - Duration and timing
    """)

with step3:
    st.markdown("""
    ### 3️⃣ Prediction
    Generate bid recommendations:
    - Average from similar projects
    - ML model predictions
    - Confidence intervals
    - Competition assessment
    """)

st.markdown("---")

# Getting started
st.header("🚀 Getting Started")

st.success("""
**Phase 2 Complete!** ✓

The Historical Project Explorer is now available:
1. Navigate to 📊 Explorer in the sidebar
2. Filter projects by value, region, keywords, and dates
3. View detailed bid information for any project
4. Export filtered results to CSV/JSON
5. Analyze bid statistics and trends

**Coming Next**: Phase 3 will add ML-powered bid prediction.
""")

# Development status
with st.expander("📋 Development Roadmap"):
    st.markdown("""
    ### Phase 1: Project Setup & Git Integration ✓ COMPLETE
    - [x] GitHub repo connected
    - [x] Streamlit app structure
    - [x] Database utilities
    - [x] Basic navigation skeleton

    ### Phase 2: Historical Project Explorer ✓ COMPLETE
    - [x] Browse awarded construction projects
    - [x] Filter by value, region, keywords
    - [x] View project details and bids
    - [x] Export to CSV/JSON functionality
    - [x] Bid statistics and visualizations

    ### Phase 3: Text Processing & Similarity Engine
    - [ ] Keyword extraction from titles/descriptions
    - [ ] Project type classifier
    - [ ] Similarity scoring algorithm
    - [ ] Testing with sample projects

    ### Phase 4: Bid Prediction Tool
    - [ ] Simple predictor (average similar projects)
    - [ ] ML model (regression on bid data)
    - [ ] Confidence interval calculations
    - [ ] Prediction interface

    ### Phase 5: Analytics Dashboard
    - [ ] Trend charts
    - [ ] Regional analysis maps
    - [ ] Competition heatmaps
    - [ ] Interactive filters

    ### Phase 6: Competitor Intelligence & Polish
    - [ ] Competitor tracking page
    - [ ] UI/UX improvements
    - [ ] Comprehensive documentation
    - [ ] Production deployment
    """)

# Footer
st.markdown("---")
st.caption("""
**BCXV Construction Bid Analytics** | Phase 1 | December 2025
Data Source: [Alberta Purchasing Connection](https://purchasing.alberta.ca/)
GitHub: [bcxv-construction](https://github.com/phenom11218/bcxv-construction)
""")