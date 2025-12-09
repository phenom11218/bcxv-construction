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

# Title
st.title("📊 Historical Project Explorer")
st.markdown("Browse and analyze awarded construction projects from Alberta's procurement database.")

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

# Region filter
st.sidebar.subheader("Region")
region_filter = st.sidebar.text_input(
    "Region (e.g., Calgary, Edmonton)",
    value="",
    help="Filter by city or region name"
)

# Keyword filter
st.sidebar.subheader("Keywords")
keyword_filter = st.sidebar.text_input(
    "Search title/description",
    value="",
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
                keywords=keyword_filter if keyword_filter else None
            )

            # Apply date filter
            if not df.empty and 'awarded_on' in df.columns:
                df['awarded_on'] = pd.to_datetime(df['awarded_on'], errors='coerce')
                df = df[
                    (df['awarded_on'] >= pd.Timestamp(start_date)) &
                    (df['awarded_on'] <= pd.Timestamp(end_date))
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

        # Select columns to display
        display_columns = ['reference_number', 'short_title', 'actual_value', 'awarded_on', 'region']
        available_columns = [col for col in display_columns if col in display_df.columns]

        # Display with clickable rows
        st.dataframe(
            display_df[available_columns],
            use_container_width=True,
            hide_index=True,
            column_config={
                "reference_number": st.column_config.TextColumn("Reference", width="small"),
                "short_title": st.column_config.TextColumn("Project Title", width="large"),
                "actual_value": st.column_config.TextColumn("Award Value", width="medium"),
                "awarded_on": st.column_config.TextColumn("Award Date", width="medium"),
                "region": st.column_config.TextColumn("Region", width="medium")
            }
        )

        # Project details section
        st.markdown("---")
        st.subheader("🔍 View Project Details")

        # Select a project to view details
        project_refs = df['reference_number'].tolist()
        selected_ref = st.selectbox(
            "Select a project to view details:",
            options=project_refs,
            format_func=lambda x: f"{x} - {df[df['reference_number']==x]['short_title'].values[0][:60]}..."
        )

        if selected_ref:
            # Get full project details with bids
            project_details = queries.get_project_with_bids(selected_ref)

            if project_details:
                st.markdown(f"### 📄 Project {selected_ref}")

                # Project info
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Award Value", f"${project_details['award_value']:,.2f}" if project_details.get('award_value') else "N/A")
                with col2:
                    st.metric("Number of Bids", len(project_details.get('bids', [])))
                with col3:
                    st.metric("Award Date", project_details.get('award_date', 'N/A'))

                # Description
                st.markdown("**Description:**")
                st.info(project_details.get('description', 'No description available'))

                # Bids table
                if project_details.get('bids'):
                    st.markdown("#### 💰 All Bids Received")
                    bids_data = []
                    for bid in project_details['bids']:
                        bids_data.append({
                            "Supplier": bid.get('supplier_name', 'Unknown'),
                            "Bid Amount": f"${bid.get('bid_amount', 0):,.2f}",
                            "Awarded": "✓ Winner" if bid.get('awarded') else ""
                        })

                    bids_df = pd.DataFrame(bids_data)
                    st.dataframe(bids_df, use_container_width=True, hide_index=True)

                    # Bid statistics
                    bid_amounts = [b['bid_amount'] for b in project_details['bids'] if b.get('bid_amount')]
                    if len(bid_amounts) > 1:
                        st.markdown("#### 📊 Bid Statistics")
                        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
                        with stat_col1:
                            st.metric("Lowest Bid", f"${min(bid_amounts):,.2f}")
                        with stat_col2:
                            st.metric("Highest Bid", f"${max(bid_amounts):,.2f}")
                        with stat_col3:
                            st.metric("Average Bid", f"${sum(bid_amounts)/len(bid_amounts):,.2f}")
                        with stat_col4:
                            spread = ((max(bid_amounts) - min(bid_amounts)) / min(bid_amounts) * 100)
                            st.metric("Spread", f"{spread:.1f}%")

                        # Bid distribution chart
                        fig = go.Figure()
                        fig.add_trace(go.Bar(
                            x=[b.get('supplier_name', 'Unknown')[:20] for b in project_details['bids']],
                            y=bid_amounts,
                            marker_color=['green' if b.get('awarded') else 'lightblue' for b in project_details['bids']]
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
