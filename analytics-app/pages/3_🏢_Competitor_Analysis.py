"""
Competitor Analysis
===================
Comprehensive analysis of bidding companies and market intelligence.

Author: BCXV Construction Analytics
Date: 2025-12-11
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add utils to path
sys.path.append(str(Path(__file__).parent.parent / 'utils'))

from database import get_smart_database_connection
from competitor_queries import CompetitorQueries
from competitor_analytics import (
    format_currency, format_percentage,
    create_win_rate_chart,
    create_category_breakdown_chart,
    create_regional_focus_chart,
    create_bid_distribution_histogram
)

# Page config
st.set_page_config(
    page_title="Competitor Analysis",
    page_icon="🏢",
    layout="wide"
)

st.title("🏢 Competitor Analysis")
st.markdown("Comprehensive bidding intelligence and market analysis")

# Initialize database connection
@st.cache_resource
def get_database():
    return get_smart_database_connection()

@st.cache_resource
def get_competitor_queries(_db):
    return CompetitorQueries(_db)

try:
    db = get_database()
    comp_queries = get_competitor_queries(db)

    # Get all companies for dropdowns (alphabetically sorted)
    with st.spinner("Loading companies..."):
        all_companies = comp_queries.search_companies("", limit=1000)

    if not all_companies:
        st.warning("No bidder data available")
        st.stop()

    # Main tabs - removed Head-to-Head
    tab1, tab2 = st.tabs(["📊 Market Overview", "🔍 Company Deep Dive"])

    # ==================== TAB 1: Market Overview ====================
    with tab1:
        st.header("Market Overview")

        # Load market statistics
        with st.spinner("Loading market data..."):
            market_stats = comp_queries.get_market_overview()

        # Market metrics - 6 columns now
        col1, col2, col3, col4, col5, col6 = st.columns(6)

        with col1:
            st.metric(
                "Unique Companies",
                f"{market_stats['total_companies']:,}",
                help="Companies with 3+ bids placed"
            )

        with col2:
            st.metric(
                "Total Bids",
                f"{market_stats['total_bids']:,}",
                help="Total number of bids across all companies"
            )

        with col3:
            st.metric(
                "Total Awards",
                f"{market_stats['total_awards']:,}",
                help="Total contracts awarded"
            )

        with col4:
            st.metric(
                "Avg Win Rate",
                format_percentage(market_stats['avg_win_rate']),
                help="Average win rate across all bidders"
            )

        with col5:
            st.metric(
                "Interested Suppliers",
                f"{market_stats['total_interested_suppliers']:,}",
                help="Unique suppliers who expressed interest but didn't bid"
            )

        with col6:
            # Total interest expressions
            query = "SELECT COUNT(*) as count FROM interested_suppliers"
            result = db.execute_query(query)
            total_interests = int(result.iloc[0]['count']) if not result.empty else 0
            st.metric(
                "Total Interests",
                f"{total_interests:,}",
                help="Total number of interest expressions"
            )

        st.divider()

        # Top Competitors Section
        st.header("Top Competitors")

        col1, col2 = st.columns([1, 1])

        with col1:
            sort_by = st.selectbox(
                "Sort by",
                options=['bids', 'wins', 'win_rate', 'value'],
                format_func=lambda x: {
                    'bids': 'Total Bids',
                    'wins': 'Total Wins',
                    'win_rate': 'Win Rate',
                    'value': 'Total Value Won'
                }[x],
                key="market_sort"
            )

        with col2:
            top_n = st.slider("Number of companies to show", 10, 50, 20, key="market_top_n")

        # Get top companies
        with st.spinner("Loading top competitors..."):
            top_companies = comp_queries.get_top_bidders(limit=top_n, sort_by=sort_by)

        if not top_companies.empty:
            # Format for display
            display_df = top_companies.copy()
            display_df['avg_bid'] = display_df['avg_bid'].apply(lambda x: format_currency(x) if pd.notna(x) else 'N/A')
            display_df['total_value'] = display_df['total_value'].apply(lambda x: format_currency(x) if pd.notna(x) else 'N/A')
            display_df['win_rate'] = display_df['win_rate'].apply(lambda x: f"{x:.1f}%")

            display_df = display_df.rename(columns={
                'company_name': 'Company',
                'total_bids': 'Bids',
                'wins': 'Wins',
                'win_rate': 'Win Rate',
                'avg_bid': 'Avg Bid',
                'total_value': 'Total Value Won'
            })

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )

            # Download button
            csv = top_companies.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name="top_competitors.csv",
                mime="text/csv"
            )
        else:
            st.info("No competitor data available")

        # Tips
        with st.expander("💡 How to Use Market Overview"):
            st.markdown("""
            **Understanding the Market:**
            - **Unique Companies**: Shows active bidders with at least 3 bids
            - **Win Rate**: Industry average - compare individual companies against this benchmark
            - **Interested Suppliers**: Companies that expressed interest in projects
            - **Total Interests**: Total number of times companies expressed interest

            **Top Competitors Table:**
            - Sort by different metrics to find leaders in each category
            - High win rate = strong competitive position
            - High total bids = active market participant
            - High total value = major contract winner

            **Tips:**
            - Use Company Deep Dive tab for detailed individual analysis
            """)

    # ==================== TAB 2: Company Deep Dive ====================
    with tab2:
        st.header("Company Deep Dive")

        # Company selector - simple dropdown
        selected_company = st.selectbox(
            "Select a company to analyze",
            options=all_companies,
            key="deep_dive_company"
        )

        if not selected_company:
            st.info("👆 Select a company above to begin analysis")
            st.stop()

        # Load company data
        with st.spinner(f"Loading data for {selected_company}..."):
            company_stats = comp_queries.get_company_summary_stats(selected_company)

            if not company_stats:
                st.error(f"No data found for {selected_company}")
                st.stop()

            bidding_history = comp_queries.get_company_bidding_history(selected_company)
            category_breakdown = comp_queries.get_company_win_rate_by_category(selected_company)
            year_breakdown = comp_queries.get_company_win_rate_by_year(selected_company)
            region_breakdown = comp_queries.get_company_win_rate_by_region(selected_company)

            # Get interested supplier stats
            interest_query = """
                SELECT COUNT(*) as interest_count
                FROM interested_suppliers
                WHERE business_name = ?
            """
            interest_result = db.execute_query(interest_query, (selected_company,))
            interest_count = int(interest_result.iloc[0]['interest_count']) if not interest_result.empty else 0

        st.divider()

        # Company Profile Card
        st.subheader(f"📊 {selected_company}")

        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

        with col1:
            st.metric("Total Bids", f"{company_stats['total_bids']:,}")

        with col2:
            st.metric("Wins", f"{company_stats['wins']:,}")

        with col3:
            st.metric("Win Rate", format_percentage(company_stats['win_rate']))

        with col4:
            st.metric("Avg Bid", format_currency(company_stats['avg_bid']))

        with col5:
            st.metric("Total Value Won", format_currency(company_stats['total_won_value']))

        with col6:
            if not category_breakdown.empty:
                primary_category = category_breakdown.iloc[0]['category_code']
                primary_category_pct = category_breakdown.iloc[0]['percentage']
                st.metric("Primary Category", primary_category or "N/A", f"{primary_category_pct:.0f}%")
            else:
                st.metric("Primary Category", "N/A")

        with col7:
            st.metric("Interests Shown", f"{interest_count:,}", help="Times this company expressed interest in projects")

        st.divider()

        # Bidding History - moved up, right below profile
        st.subheader("📋 Bidding History")

        col1, col2, col3 = st.columns(3)

        with col1:
            categories = ['All'] + sorted(bidding_history['category_code'].dropna().unique().tolist())
            selected_category = st.selectbox("Filter by Category", categories, key="dd_category")

        with col2:
            years = ['All'] + sorted(bidding_history['year'].dropna().unique().tolist(), reverse=True)
            selected_year = st.selectbox("Filter by Year", years, key="dd_year")

        with col3:
            statuses = ['All'] + sorted(bidding_history['status_code'].dropna().unique().tolist())
            selected_status = st.selectbox("Filter by Status", statuses, key="dd_status")

        # Apply filters
        filtered_history = bidding_history.copy()

        if selected_category != 'All':
            filtered_history = filtered_history[filtered_history['category_code'] == selected_category]

        if selected_year != 'All':
            filtered_history = filtered_history[filtered_history['year'] == selected_year]

        if selected_status != 'All':
            filtered_history = filtered_history[filtered_history['status_code'] == selected_status]

        st.caption(f"Showing {len(filtered_history):,} of {len(bidding_history):,} bids")

        if not filtered_history.empty:
            display_df = filtered_history.copy()

            if 'bid_amount' in display_df.columns:
                display_df['bid_amount'] = display_df['bid_amount'].apply(
                    lambda x: format_currency(x) if pd.notna(x) else 'N/A'
                )

            if 'actual_value' in display_df.columns:
                display_df['actual_value'] = display_df['actual_value'].apply(
                    lambda x: format_currency(x) if pd.notna(x) else 'N/A'
                )

            if 'close_date' in display_df.columns:
                display_df['close_date'] = pd.to_datetime(display_df['close_date']).dt.strftime('%Y-%m-%d')

            if 'is_winner' in display_df.columns:
                display_df['Result'] = display_df['is_winner'].apply(
                    lambda x: '🏆 Won' if x == 1 else '❌ Lost' if x == 0 else 'Pending'
                )

            # Create clickable links for reference numbers
            display_df['Reference'] = display_df['reference_number'].apply(
                lambda ref: f'<a href="https://purchasing.alberta.ca/posting/{ref}" target="_blank">{ref}</a>'
            )

            display_df = display_df.rename(columns={
                'short_title': 'Project Title',
                'category_code': 'Category',
                'region': 'Region',
                'status_code': 'Status',
                'close_date': 'Close Date',
                'bid_amount': 'Bid Amount'
            })

            columns_to_show = ['Reference', 'Project Title', 'Category', 'Region',
                              'Status', 'Close Date', 'Bid Amount', 'Result']
            columns_to_show = [col for col in columns_to_show if col in display_df.columns]

            # Display with HTML for clickable links
            st.write(display_df[columns_to_show].to_html(escape=False, index=False), unsafe_allow_html=True)

            csv = filtered_history.to_csv(index=False)
            st.download_button(
                label="📥 Download Filtered Results as CSV",
                data=csv,
                file_name=f"{selected_company.replace(' ', '_')}_bidding_history.csv",
                mime="text/csv",
                key="dd_download"
            )

        st.divider()

        # Interest History - added below bidding history
        st.subheader("💡 Interest History")
        st.caption("Projects where this company expressed interest (but may not have bid)")

        # Get interest history
        interest_query = """
            SELECT
                i.opportunity_ref as reference_number,
                o.short_title,
                o.category_code,
                o.region,
                o.status_code,
                o.close_date,
                o.year,
                i.city,
                i.province
            FROM interested_suppliers i
            JOIN opportunities o ON i.opportunity_ref = o.reference_number
            WHERE i.business_name = ?
            ORDER BY o.close_date DESC
        """
        interest_history = db.execute_query(interest_query, (selected_company,))

        if not interest_history.empty:
            st.caption(f"Showing {len(interest_history):,} project interests")

            # Format for display
            display_interest = interest_history.copy()

            if 'close_date' in display_interest.columns:
                display_interest['close_date'] = pd.to_datetime(display_interest['close_date']).dt.strftime('%Y-%m-%d')

            # Create clickable links
            display_interest['Reference'] = display_interest['reference_number'].apply(
                lambda ref: f'<a href="https://purchasing.alberta.ca/posting/{ref}" target="_blank">{ref}</a>'
            )

            display_interest = display_interest.rename(columns={
                'short_title': 'Project Title',
                'category_code': 'Category',
                'region': 'Region',
                'status_code': 'Status',
                'close_date': 'Close Date',
                'city': 'City',
                'province': 'Province'
            })

            columns_to_show = ['Reference', 'Project Title', 'Category', 'Region',
                              'Status', 'Close Date', 'City', 'Province']
            columns_to_show = [col for col in columns_to_show if col in display_interest.columns]

            # Display with HTML for clickable links
            st.write(display_interest[columns_to_show].to_html(escape=False, index=False), unsafe_allow_html=True)

            # Download button
            csv_interest = interest_history.to_csv(index=False)
            st.download_button(
                label="📥 Download Interest History as CSV",
                data=csv_interest,
                file_name=f"{selected_company.replace(' ', '_')}_interest_history.csv",
                mime="text/csv",
                key="interest_download"
            )
        else:
            st.info("No interest history found for this company")

        st.divider()

        # Visualizations
        st.subheader("📈 Performance Analytics")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Win Rate Over Time**")
            if not year_breakdown.empty and len(year_breakdown) > 1:
                fig = create_win_rate_chart(year_breakdown, selected_company)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough data across multiple years")

        with col2:
            st.markdown("**Category Distribution**")
            if not category_breakdown.empty:
                fig = create_category_breakdown_chart(category_breakdown)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No category data available")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Regional Focus**")
            if not region_breakdown.empty:
                fig = create_regional_focus_chart(region_breakdown)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No regional data available")

        with col2:
            st.markdown("**Bid Amount Distribution**")
            if not bidding_history.empty and 'bid_amount' in bidding_history.columns:
                bid_amounts = bidding_history[bidding_history['bid_amount'].notna()]['bid_amount']
                if len(bid_amounts) > 0:
                    fig = create_bid_distribution_histogram(bid_amounts, selected_company)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No bid amount data available")
            else:
                st.info("No bid amount data available")

except Exception as e:
    st.error(f"Error loading competitor data: {str(e)}")
    import traceback
    with st.expander("Show error details"):
        st.code(traceback.format_exc())
