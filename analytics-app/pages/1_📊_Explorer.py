"""
Historical Project Explorer
============================
Browse and analyze awarded construction projects with detailed bid information.

Features:
- Filter by value range, region, keywords, and date range
- View all awarded construction projects in a sortable table
- Click to view detailed project information with all bids
- Export filtered results to CSV
- Bid statistics and competition analysis

Author: BCXV Construction Analytics
Date: 2025-12-08
Phase: 2 - Historical Project Explorer
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add utils to path
sys.path.append(str(Path(__file__).parent.parent))
from utils.database import DatabaseConnection, ConstructionProjectQueries

# Page configuration
st.set_page_config(
    page_title="Project Explorer - BCXV Analytics",
    page_icon="📊",
    layout="wide"
)

# Initialize database connection
@st.cache_resource
def get_database():
    return DatabaseConnection()

@st.cache_data
def get_queries(_db):
    """Get ConstructionProjectQueries instance (underscore prevents caching the db object)"""
    return ConstructionProjectQueries(_db)

db = get_database()
queries = get_queries(db)

# Load suggestions (cached)
@st.cache_data
def load_suggestions(_queries):
    """Load region, keyword, and supplier suggestions from database"""
    regions = _queries.get_unique_regions()
    keywords = _queries.get_common_keywords(limit=100)  # Get top 100, sorted alphabetically
    suppliers = _queries.get_all_suppliers()
    return regions, keywords, suppliers

regions_list, keywords_list, suppliers_list = load_suggestions(queries)

# Title
st.title("📊 Historical Project Explorer")
st.markdown("Browse and analyze awarded construction projects from Alberta's procurement database.")

# Show helpful info
with st.expander("💡 Quick Tips - Click to expand", expanded=False):
    st.markdown(f"""
    **Available Data:**
    - **{len(regions_list)} regions/cities** across Alberta
    - **{len(keywords_list)} common keywords** extracted from project titles
    - **{len(suppliers_list)} suppliers/companies** that have submitted bids
    - **831 awarded construction projects** from 2025

    **Search Tips:**
    - Use **Region dropdown** to see all available cities
    - Use **Keyword suggestions** to discover common project types
    - Use **Supplier filter** to track competitor bidding behavior
    - Use **Competition level** to find less competitive projects
    - Use **Size buckets** for quick project size filtering
    - Combine multiple filters for precise results

    **Common Keywords Include:**
    `{', '.join(keywords_list[:15])}`...

    **Top Regions:**
    `{', '.join(regions_list[:10])}`...
    """)

# Sidebar filters
st.sidebar.header("🔍 Filters")

# Value range filter
st.sidebar.subheader("Project Value")
col1, col2 = st.sidebar.columns(2)
with col1:
    min_value = st.number_input(
        "Min ($)",
        min_value=0,
        value=0,
        step=10000,
        format="%d"
    )
with col2:
    max_value = st.number_input(
        "Max ($)",
        min_value=0,
        value=10000000,
        step=100000,
        format="%d"
    )

# Region filter with dropdown + free text
st.sidebar.subheader("Region / City")
region_mode = st.sidebar.radio(
    "Select mode:",
    options=["Choose from list", "Type custom"],
    horizontal=True,
    label_visibility="collapsed"
)

if region_mode == "Choose from list":
    region_filter = st.sidebar.selectbox(
        "Select region:",
        options=[""] + regions_list,
        help=f"{len(regions_list)} regions available"
    )
else:
    region_filter = st.sidebar.text_input(
        "Enter region:",
        value="",
        placeholder="e.g., Calgary, Edmonton, Red Deer",
        help="Filter by city or region name"
    )

# Keyword filter with suggestions + free text
st.sidebar.subheader("Keywords")
keyword_mode = st.sidebar.radio(
    "Select mode:",
    options=["Choose from common", "Type custom"],
    horizontal=True,
    label_visibility="collapsed",
    key="keyword_mode"
)

if keyword_mode == "Choose from common":
    keyword_filter = st.sidebar.selectbox(
        "Select keyword:",
        options=[""] + keywords_list,
        help=f"Top {len(keywords_list)} most common keywords"
    )
else:
    keyword_filter = st.sidebar.text_input(
        "Enter keywords:",
        value="",
        placeholder="e.g., road, building, paving",
        help="Search for projects containing specific keywords"
    )

# Date range filter
st.sidebar.subheader("Date Range")
date_col1, date_col2 = st.sidebar.columns(2)
with date_col1:
    start_date = st.date_input(
        "From",
        value=datetime(2025, 1, 1),
        help="Award date from"
    )
with date_col2:
    end_date = st.date_input(
        "To",
        value=datetime(2025, 12, 31),
        help="Award date to"
    )

# Supplier/Company filter
st.sidebar.subheader("Supplier / Company")
supplier_mode = st.sidebar.radio(
    "Select mode:",
    options=["All suppliers", "Specific supplier"],
    horizontal=True,
    label_visibility="collapsed",
    key="supplier_mode"
)

if supplier_mode == "Specific supplier":
    supplier_filter = st.sidebar.selectbox(
        "Select supplier:",
        options=[""] + suppliers_list,
        help=f"Filter projects where this company bid ({len(suppliers_list)} suppliers)"
    )
    if not supplier_filter:
        supplier_filter = None
else:
    supplier_filter = None

# Competition Level filter
st.sidebar.subheader("Competition Level")
competition_filter = st.sidebar.select_slider(
    "Number of bidders:",
    options=["All", "Low (1-3)", "Medium (4-6)", "High (7+)"],
    value="All",
    help="Filter by number of competing bids"
)

# Convert to min/max bidders
min_bidders, max_bidders = None, None
if competition_filter == "Low (1-3)":
    min_bidders, max_bidders = 1, 3
elif competition_filter == "Medium (4-6)":
    min_bidders, max_bidders = 4, 6
elif competition_filter == "High (7+)":
    min_bidders = 7

# Project Size Buckets
st.sidebar.subheader("Project Size")
size_bucket = st.sidebar.select_slider(
    "Quick size filter:",
    options=["All", "Small (<$500K)", "Medium ($500K-$2M)", "Large ($2M-$10M)", "XL (>$10M)"],
    value="All",
    help="Pre-defined project size categories"
)

size_bucket_filter = None if size_bucket == "All" else size_bucket

# Show supplier stats if supplier is selected
if supplier_filter:
    supplier_stats = queries.get_supplier_stats(supplier_filter)

    st.sidebar.markdown("---")
    st.sidebar.subheader(f"📊 {supplier_filter[:30]}{'...' if len(supplier_filter) > 30 else ''}")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("Total Bids", supplier_stats['total_bids'])
        st.metric("Wins", supplier_stats['wins'])
    with col2:
        st.metric("Win Rate", f"{supplier_stats['win_rate']:.1f}%")
        st.metric("Losses", supplier_stats['losses'])

    if supplier_stats['total_won_value'] > 0:
        st.sidebar.metric("Total Won Value", f"${supplier_stats['total_won_value']:,.0f}")

    if supplier_stats['regions']:
        st.sidebar.caption("**Top Regions:**")
        for region, count in list(supplier_stats['regions'].items())[:3]:
            st.sidebar.caption(f"• {region}: {count} projects")

# Fetch data button
if st.sidebar.button("🔎 Apply Filters", type="primary"):
    st.session_state.fetch_data = True

# Initialize session state
if 'fetch_data' not in st.session_state:
    st.session_state.fetch_data = False
if 'selected_project' not in st.session_state:
    st.session_state.selected_project = None

# Main content area
tab1, tab2, tab3 = st.tabs(["📋 Projects Table", "📊 Statistics", "💾 Export"])

with tab1:
    if st.session_state.fetch_data or st.sidebar.button("Load All Projects"):
        with st.spinner("Loading projects..."):
            # Fetch projects with filters
            df = queries.get_awarded_construction_projects(
                min_value=min_value if min_value > 0 else None,
                max_value=max_value if max_value < 10000000 else None,
                region=region_filter if region_filter else None,
                keywords=keyword_filter if keyword_filter else None,
                supplier=supplier_filter,
                min_bidders=min_bidders,
                max_bidders=max_bidders,
                size_bucket=size_bucket_filter
            )

            # Apply date filter
            if not df.empty and 'awarded_on' in df.columns:
                df['awarded_on'] = pd.to_datetime(df['awarded_on'], errors='coerce')
                # Drop rows with invalid dates and filter by date range
                df = df.dropna(subset=['awarded_on'])
                if not df.empty:
                    df = df[
                        (df['awarded_on'].dt.date >= start_date) &
                        (df['awarded_on'].dt.date <= end_date)
                    ]

            st.session_state.projects_df = df

    # Display projects table
    if 'projects_df' in st.session_state and not st.session_state.projects_df.empty:
        df = st.session_state.projects_df

        st.success(f"Found **{len(df)}** projects matching your filters")

        # Format currency columns
        display_df = df.copy()
        if 'actual_value' in display_df.columns:
            display_df['actual_value'] = display_df['actual_value'].apply(
                lambda x: f"${x:,.2f}" if pd.notna(x) else "N/A"
            )
        if 'awarded_on' in display_df.columns:
            display_df['awarded_on'] = pd.to_datetime(display_df['awarded_on'], errors='coerce').dt.strftime('%Y-%m-%d')

        # Keep reference_number as-is for lookups, create URL column for linking
        display_df['ref_link'] = display_df['reference_number'].apply(
            lambda x: f"https://purchasing.alberta.ca/posting/{x}"
        )

        # Select columns to display
        display_columns = ['reference_number', 'short_title', 'actual_value', 'awarded_on', 'region']
        available_columns = [col for col in display_columns if col in display_df.columns]

        # Display interactive table with clickable links and row selection
        event = st.dataframe(
            display_df[available_columns],
            use_container_width=True,
            hide_index=True,
            column_config={
                "reference_number": st.column_config.TextColumn(
                    "Reference",
                    width="small",
                    help="Project reference number"
                ),
                "short_title": st.column_config.TextColumn("Project Title", width="large"),
                "actual_value": st.column_config.TextColumn("Award Value", width="medium"),
                "awarded_on": st.column_config.TextColumn("Award Date", width="medium"),
                "region": st.column_config.TextColumn("Region", width="medium")
            },
            on_select="rerun",
            selection_mode="single-row",
            key="projects_table"
        )

        # Project details section
        st.markdown("---")
        st.subheader("🔍 Project Details")

        # Get selected row from table interaction
        selected_ref = None
        if event.selection and event.selection.rows:
            selected_idx = event.selection.rows[0]
            selected_ref = df.iloc[selected_idx]['reference_number']
            st.success(f"Selected: **{selected_ref}** - {df.iloc[selected_idx]['short_title']}")
        else:
            st.info("👆 Click on any row in the table above to view full project details with all bids")

        if selected_ref:
            # Get full project details with bids
            project_details = queries.get_project_with_bids(selected_ref)

            if project_details is not None and len(project_details) > 0:
                project_df = project_details.get('project')
                bids_df = project_details.get('bids')
                award_df = project_details.get('award')
                stats = project_details.get('stats', {})

                st.markdown(f"### 📄 Project {selected_ref}")

                # Project info
                col1, col2, col3 = st.columns(3)
                with col1:
                    if not award_df.empty and 'award_amount' in award_df.columns:
                        award_amount = award_df['award_amount'].iloc[0]
                        st.metric("Award Value", f"${award_amount:,.2f}" if pd.notna(award_amount) else "N/A")
                    else:
                        st.metric("Award Value", "N/A")
                with col2:
                    num_bids = len(bids_df) if not bids_df.empty else 0
                    st.metric("Number of Bids", num_bids)
                with col3:
                    if not award_df.empty and 'award_date' in award_df.columns:
                        award_date = award_df['award_date'].iloc[0]
                        st.metric("Award Date", award_date if pd.notna(award_date) else "N/A")
                    else:
                        st.metric("Award Date", "N/A")

                # Description
                st.markdown("**Description:**")
                if not project_df.empty and 'description' in project_df.columns:
                    description = project_df['description'].iloc[0]
                    st.info(description if pd.notna(description) else 'No description available')
                else:
                    st.info('No description available')

                # Bids table
                if not bids_df.empty:
                    st.markdown("#### 💰 All Bids Received")

                    # Format bids for display
                    display_bids = bids_df.copy()
                    if 'bid_amount' in display_bids.columns:
                        display_bids['bid_amount'] = display_bids['bid_amount'].apply(
                            lambda x: f"${x:,.2f}" if pd.notna(x) else "N/A"
                        )
                    if 'is_winner' in display_bids.columns:
                        display_bids['status'] = display_bids['is_winner'].apply(
                            lambda x: "✓ Winner" if x else ""
                        )

                    # Select columns to show
                    show_cols = ['company_name', 'bid_amount', 'status', 'city']
                    available_cols = [col for col in show_cols if col in display_bids.columns]

                    st.dataframe(
                        display_bids[available_cols],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "company_name": "Supplier",
                            "bid_amount": "Bid Amount",
                            "status": "Status",
                            "city": "City"
                        }
                    )

                    # Bid statistics (use pre-calculated stats from database)
                    if stats and len(stats) > 0:
                        st.markdown("#### 📊 Bid Statistics")
                        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
                        with stat_col1:
                            st.metric("Lowest Bid", f"${stats['lowest_bid']:,.2f}")
                        with stat_col2:
                            st.metric("Highest Bid", f"${stats['highest_bid']:,.2f}")
                        with stat_col3:
                            st.metric("Average Bid", f"${stats['average_bid']:,.2f}")
                        with stat_col4:
                            spread_pct = (stats['bid_spread'] / stats['lowest_bid'] * 100)
                            st.metric("Spread", f"{spread_pct:.1f}%")

                        # Bid distribution chart
                        if 'bid_amount' in bids_df.columns and 'company_name' in bids_df.columns:
                            fig = go.Figure()
                            bid_amounts = bids_df['bid_amount'].dropna()
                            suppliers = bids_df.loc[bid_amounts.index, 'company_name'].apply(lambda x: str(x)[:20])
                            colors = bids_df.loc[bid_amounts.index, 'is_winner'].apply(
                                lambda x: 'green' if x else 'lightblue'
                            ) if 'is_winner' in bids_df.columns else 'lightblue'

                            fig.add_trace(go.Bar(
                                x=suppliers,
                                y=bid_amounts,
                                marker_color=colors
                            ))
                            fig.update_layout(
                                title="Bid Amounts Comparison",
                                xaxis_title="Supplier",
                                yaxis_title="Bid Amount ($)",
                                height=400
                            )
                            st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No bid data available for this project")

                # Interested suppliers section (companies that viewed but may not have bid)
                st.markdown("---")
                st.markdown("#### 👀 Interested Suppliers")
                st.caption("Companies that viewed this opportunity (may include bidders)")

                interested_df = queries.get_interested_suppliers(selected_ref)

                if not interested_df.empty:
                    st.info(f"**{len(interested_df)}** companies viewed this opportunity")

                    # Show top interested suppliers
                    display_interested = interested_df.copy()

                    # Select columns to show
                    interest_cols = ['business_name', 'city', 'province', 'description']
                    available_interest_cols = [col for col in interest_cols if col in display_interested.columns]

                    # Show expandable section with all interested suppliers
                    with st.expander(f"View all {len(interested_df)} interested suppliers", expanded=False):
                        st.dataframe(
                            display_interested[available_interest_cols],
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "business_name": "Company",
                                "city": "City",
                                "province": "Province",
                                "description": "Business Type"
                            }
                        )
                else:
                    st.info("No interested supplier data available for this project")

    elif st.session_state.fetch_data:
        st.warning("No projects found matching your filters. Try adjusting the criteria.")
    else:
        st.info("👆 Click 'Apply Filters' or 'Load All Projects' to start exploring")

with tab2:
    st.subheader("📊 Overall Statistics")

    if 'projects_df' in st.session_state and not st.session_state.projects_df.empty:
        df = st.session_state.projects_df

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Projects", len(df))
        with col2:
            total_value = df['actual_value'].sum() if 'actual_value' in df.columns else 0
            st.metric("Total Value", f"${total_value:,.0f}")
        with col3:
            avg_value = df['actual_value'].mean() if 'actual_value' in df.columns else 0
            st.metric("Average Value", f"${avg_value:,.0f}")
        with col4:
            median_value = df['actual_value'].median() if 'actual_value' in df.columns else 0
            st.metric("Median Value", f"${median_value:,.0f}")

        # Value distribution
        if 'actual_value' in df.columns and not df['actual_value'].isna().all():
            st.markdown("#### 💵 Value Distribution")
            fig = px.histogram(
                df,
                x='actual_value',
                nbins=30,
                title="Distribution of Award Values",
                labels={'actual_value': 'Award Value ($)'}
            )
            st.plotly_chart(fig, use_container_width=True)

        # Regional distribution
        if 'region' in df.columns:
            st.markdown("#### 🌍 Regional Distribution")
            region_counts = df['region'].value_counts().head(10)
            fig = px.bar(
                x=region_counts.index,
                y=region_counts.values,
                title="Top 10 Regions by Project Count",
                labels={'x': 'Region', 'y': 'Number of Projects'}
            )
            st.plotly_chart(fig, use_container_width=True)

        # Timeline
        if 'awarded_on' in df.columns:
            st.markdown("#### 📅 Award Timeline")
            df_timeline = df.copy()
            df_timeline['awarded_on'] = pd.to_datetime(df_timeline['awarded_on'], errors='coerce')
            df_timeline = df_timeline.dropna(subset=['awarded_on'])
            df_timeline['month'] = df_timeline['awarded_on'].dt.to_period('M').astype(str)
            monthly_counts = df_timeline.groupby('month').size().reset_index(name='count')

            fig = px.line(
                monthly_counts,
                x='month',
                y='count',
                title="Projects Awarded Over Time",
                labels={'month': 'Month', 'count': 'Number of Projects'}
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Load projects first to see statistics")

with tab3:
    st.subheader("💾 Export Data")

    if 'projects_df' in st.session_state and not st.session_state.projects_df.empty:
        df = st.session_state.projects_df

        st.markdown(f"**Ready to export {len(df)} projects**")

        # Export options
        export_format = st.radio(
            "Select export format:",
            options=["CSV", "Excel", "JSON"],
            horizontal=True
        )

        if export_format == "CSV":
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"construction_projects_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

        elif export_format == "Excel":
            # Note: This requires openpyxl to be installed
            st.info("Excel export requires openpyxl package. Use CSV for now or add openpyxl to requirements.txt")

        elif export_format == "JSON":
            json_data = df.to_json(orient='records', date_format='iso')
            st.download_button(
                label="📥 Download JSON",
                data=json_data,
                file_name=f"construction_projects_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )

        # Preview export data
        with st.expander("Preview export data"):
            st.dataframe(df.head(10), use_container_width=True)
    else:
        st.info("Load projects first to enable export")

# Footer
st.markdown("---")
st.markdown("*Data from Alberta Procurement Database | Updated: 2025-12-08*")
