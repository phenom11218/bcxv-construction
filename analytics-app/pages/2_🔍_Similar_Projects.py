"""
Similar Projects Page
=====================
Find construction projects similar to a target project using NLP and TF-IDF.

Features:
- Search by reference number or description
- Adjustable similarity threshold
- Side-by-side comparison
- Competitive landscape analysis

Author: BCXV Construction Analytics
Date: 2025-12-08
Phase: 3 - ML & Text Processing
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add utils to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.database import get_smart_database_connection, ConstructionProjectQueries
from utils.text_processing import TextProcessor, create_combined_text
from utils.api_fetcher import AlbertaAPIFetcher

# Page config
st.set_page_config(
    page_title="Similar Projects - Alberta Construction Analytics",
    page_icon="🔍",
    layout="wide"
)

# Initialize session state
if 'text_processor' not in st.session_state:
    st.session_state.text_processor = None
if 'corpus_df' not in st.session_state:
    st.session_state.corpus_df = None
if 'api_fetcher' not in st.session_state:
    st.session_state.api_fetcher = AlbertaAPIFetcher()

# Header
st.title("🔍 Find Similar Projects")
st.markdown("""
Find construction projects similar to your target project using machine learning.
Use this to discover comparable bids, pricing, and competition patterns.
""")

# Initialize database
@st.cache_resource
def get_db_connection():
    """Get cached database connection."""
    return get_smart_database_connection()

@st.cache_resource
def get_queries(_db):
    """Get cached query object."""
    return ConstructionProjectQueries(_db)

db = get_db_connection()
queries = get_queries(db)

# Load and prepare corpus
@st.cache_data
def load_corpus():
    """Load all projects for similarity analysis."""
    df = queries.get_projects_for_similarity()

    if not df.empty:
        # Create combined text column
        df['combined_text'] = df.apply(create_combined_text, axis=1)

    return df

# Sidebar - Search Options
st.sidebar.header("Search Options")

search_mode = st.sidebar.radio(
    "Search by:",
    options=["Reference Number", "Custom Description"],
    help="Choose how to specify the target project"
)

target_text = None
target_ref = None

if search_mode == "Reference Number":
    # Input reference number or URL
    target_ref = st.sidebar.text_input(
        "Project Reference or URL",
        placeholder="AB-2025-05281 or https://purchasing.alberta.ca/posting/AB-2025-05281",
        help="Enter a project reference number or paste the full Alberta Purchasing URL"
    )

    if target_ref:
        # Parse the reference (handles both URLs and direct reference numbers)
        api_fetcher = st.session_state.api_fetcher
        parsed = api_fetcher.parse_reference_number(target_ref)

        if not parsed:
            st.sidebar.error("Invalid format. Expected: AB-YYYY-NNNNN (e.g., AB-2024-10281)")
            target_text = None
        else:
            year, posting_id = parsed
            clean_ref = f"AB-{year}-{posting_id:05d}"

            # Try to get from database first
            project_details = queries.get_project_details_for_similarity(clean_ref)

            if project_details:
                # Found in database
                project = project_details['project']
                target_text = f"{project['short_title']} {project['description']}"

                # Show target project info
                st.sidebar.success(f"✓ Found in database: {clean_ref}")
                st.sidebar.caption(f"**{project['short_title'][:60]}...**")
                if project.get('actual_value'):
                    st.sidebar.caption(f"💰 Value: ${project['actual_value']:,.0f}")
                st.sidebar.caption(f"📍 Region: {project['region']}")

                # Store project info for bid recommendations
                if 'target_project' not in st.session_state or st.session_state.target_project.get('reference_number') != clean_ref:
                    st.session_state.target_project = project

            else:
                # Not in database - fetch from API
                with st.sidebar:
                    with st.spinner(f"Fetching {clean_ref} from Alberta Purchasing API..."):
                        api_data, error_msg = api_fetcher.fetch_by_reference(target_ref)

                        if api_data:
                            # Successfully fetched from API
                            project_info = api_fetcher.extract_project_details(api_data)
                            target_text = f"{project_info['short_title']} {project_info['description']}"

                            st.success(f"🌐 Fetched live: {clean_ref}")
                            st.caption(f"**{project_info['short_title'][:60]}...**")

                            # Show value (estimated or actual)
                            value = project_info.get('actual_value') or project_info.get('estimated_value')
                            if value:
                                st.caption(f"💰 Value: ${value:,.0f}")

                            st.caption(f"📍 Region: {project_info['region']}")
                            st.caption(f"📊 Status: {project_info['status_code']}")

                            if not project_info.get('is_construction'):
                                st.warning("⚠️ This is not a construction project")

                            # Store for bid recommendations
                            st.session_state.target_project = project_info

                        else:
                            # API fetch failed
                            st.error(error_msg)
                            target_text = None

else:
    # Custom description
    target_text = st.sidebar.text_area(
        "Project Description",
        placeholder="Enter project title and description...",
        height=150,
        help="Paste or type the project description to find similar projects"
    )

# Similarity threshold
min_similarity = st.sidebar.slider(
    "Minimum Similarity",
    min_value=10,
    max_value=95,
    value=30,
    step=5,
    help="Higher values show only very similar projects"
) / 100.0

# Number of results
top_n = st.sidebar.number_input(
    "Number of Results",
    min_value=5,
    max_value=50,
    value=10,
    step=5,
    help="How many similar projects to show"
)

# Main content
if target_text:
    with st.spinner("Analyzing project database..."):
        # Load corpus if not already loaded
        if st.session_state.corpus_df is None:
            st.session_state.corpus_df = load_corpus()

        corpus_df = st.session_state.corpus_df

        if corpus_df.empty:
            st.error("No projects found in database for similarity analysis.")
        else:
            # Initialize text processor if needed
            if st.session_state.text_processor is None:
                processor = TextProcessor()
                processor.fit_tfidf(
                    documents=corpus_df['combined_text'].tolist(),
                    document_ids=corpus_df['reference_number'].tolist()
                )
                st.session_state.text_processor = processor

            processor = st.session_state.text_processor

            # Find similar projects
            similar_results = processor.find_similar(
                target_text,
                top_n=top_n,
                min_similarity=min_similarity
            )

            if similar_results:
                st.success(f"Found {len(similar_results)} similar projects")

                # Create results DataFrame
                similar_refs = [r[0] for r in similar_results]
                similar_scores = [r[1] for r in similar_results]

                results_df = corpus_df[corpus_df['reference_number'].isin(similar_refs)].copy()

                # Add similarity scores
                score_map = dict(similar_results)
                results_df['Similarity'] = results_df['reference_number'].map(score_map)
                results_df['Similarity'] = (results_df['Similarity'] * 100).round(1)

                # Sort by similarity
                results_df = results_df.sort_values('Similarity', ascending=False)

                # Display results in tabs
                tab1, tab2, tab3 = st.tabs(["📋 Similar Projects", "📊 Analysis", "🎯 Competitive Landscape"])

                with tab1:
                    st.subheader("Similar Projects Found")

                    # Format display DataFrame
                    display_df = results_df[['reference_number', 'short_title', 'actual_value', 'Similarity', 'region', 'awarded_on']].copy()

                    # Format currency
                    display_df['actual_value'] = display_df['actual_value'].apply(
                        lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A"
                    )

                    # Format date
                    display_df['awarded_on'] = pd.to_datetime(display_df['awarded_on'], errors='coerce').dt.strftime('%Y-%m-%d')

                    # Create clickable reference links
                    display_df['reference_number'] = display_df['reference_number'].apply(
                        lambda x: f"https://purchasing.alberta.ca/posting/{x}"
                    )

                    # Display table
                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "reference_number": st.column_config.LinkColumn(
                                "Reference",
                                width="medium",
                                help="Click to view original posting",
                                display_text=r"https://purchasing\.alberta\.ca/posting/(AB-\d{4}-\d{5})"
                            ),
                            "short_title": st.column_config.TextColumn("Project Title", width="large"),
                            "actual_value": st.column_config.TextColumn("Value", width="small"),
                            "Similarity": st.column_config.TextColumn("Match %", width="small"),
                            "region": st.column_config.TextColumn("Region", width="medium"),
                            "awarded_on": st.column_config.TextColumn("Award Date", width="small")
                        }
                    )

                with tab2:
                    # Bid Recommendation Section
                    st.subheader("💡 Bid Recommendation")

                    # Calculate bid statistics from similar projects
                    similar_values = results_df['actual_value'].dropna()

                    if len(similar_values) >= 3:
                        avg_value = similar_values.mean()
                        median_value = similar_values.median()
                        std_value = similar_values.std()
                        min_value = similar_values.min()
                        max_value = similar_values.max()

                        # Calculate recommended bid range (median ± 0.5 std dev)
                        rec_low = max(median_value - (0.5 * std_value), min_value)
                        rec_high = min(median_value + (0.5 * std_value), max_value)

                        # Confidence level based on number of similar projects
                        num_similar = len(similar_values)
                        if num_similar >= 10:
                            confidence = "High"
                            confidence_color = "green"
                        elif num_similar >= 5:
                            confidence = "Medium"
                            confidence_color = "orange"
                        else:
                            confidence = "Low"
                            confidence_color = "red"

                        # Display recommendation in a prominent box
                        st.info(f"""
                        **Based on {num_similar} similar awarded projects:**

                        🎯 **Recommended Bid Range:** ${rec_low:,.0f} - ${rec_high:,.0f}

                        📊 **Target Bid (Median):** ${median_value:,.0f}

                        📈 **Confidence Level:** :{confidence_color}[{confidence}] ({num_similar} similar projects found)

                        💰 **Historical Range:** ${min_value:,.0f} - ${max_value:,.0f}
                        """)

                        # Additional context
                        st.caption("""
                        💡 **How to use this:** The recommended bid range represents the middle 50% of similar project values.
                        Bidding within this range increases your competitiveness while maintaining profitability.
                        Consider adjusting based on your costs, capacity, and strategic priorities.
                        """)

                    else:
                        st.warning(f"⚠️ Only {len(similar_values)} similar projects found. Need at least 3 for reliable bid recommendations.")

                    st.divider()

                    # Value Distribution Analysis
                    st.subheader("Value Distribution Analysis")

                    # Value statistics
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        avg_value = results_df['actual_value'].mean()
                        st.metric("Average Value", f"${avg_value:,.0f}")

                    with col2:
                        min_value = results_df['actual_value'].min()
                        st.metric("Min Value", f"${min_value:,.0f}")

                    with col3:
                        max_value = results_df['actual_value'].max()
                        st.metric("Max Value", f"${max_value:,.0f}")

                    with col4:
                        median_value = results_df['actual_value'].median()
                        st.metric("Median Value", f"${median_value:,.0f}")

                    # Value distribution chart
                    import plotly.express as px

                    fig = px.histogram(
                        results_df,
                        x='actual_value',
                        nbins=20,
                        title="Value Distribution of Similar Projects"
                    )
                    fig.update_layout(
                        xaxis_title="Project Value ($)",
                        yaxis_title="Number of Projects",
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Regional distribution
                    st.subheader("Regional Distribution")

                    region_counts = results_df['region'].value_counts().head(10)

                    fig2 = px.bar(
                        x=region_counts.index,
                        y=region_counts.values,
                        title="Top 10 Regions for Similar Projects"
                    )
                    fig2.update_layout(
                        xaxis_title="Region",
                        yaxis_title="Number of Projects",
                        height=400
                    )
                    st.plotly_chart(fig2, use_container_width=True)

                with tab3:
                    st.subheader("Typical Competition for Similar Projects")
                    st.caption("Companies that frequently bid on projects like this")

                    # Extract keywords from target
                    keywords = processor.extract_keywords(target_text, top_n=3)
                    keyword_list = [kw for kw, _ in keywords]

                    # Get competitive landscape
                    avg_value_similar = results_df['actual_value'].mean()
                    std_value_similar = results_df['actual_value'].std()

                    landscape_df = queries.get_competitive_landscape(
                        keywords=keyword_list if keyword_list else None,
                        min_value=avg_value_similar - std_value_similar if avg_value_similar > std_value_similar else None,
                        max_value=avg_value_similar + std_value_similar,
                        limit=20
                    )

                    if not landscape_df.empty:
                        # Format display
                        display_landscape = landscape_df.copy()
                        display_landscape['avg_bid_amount'] = display_landscape['avg_bid_amount'].apply(
                            lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A"
                        )

                        st.dataframe(
                            display_landscape[['company_name', 'total_bids', 'wins', 'win_rate', 'avg_bid_amount']],
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "company_name": "Supplier",
                                "total_bids": "Total Bids",
                                "wins": "Wins",
                                "win_rate": st.column_config.NumberColumn("Win Rate %", format="%.1f%%"),
                                "avg_bid_amount": "Avg Bid"
                            }
                        )
                    else:
                        st.info("No competitive data available for similar projects")

            else:
                st.warning(f"No projects found with similarity >= {min_similarity*100:.0f}%. Try lowering the threshold.")
else:
    # Show instructions
    st.info("👈 Enter a project reference number, URL, or custom description in the sidebar to find similar projects")

    st.markdown("""
    ### 🚀 How it Works

    This tool uses **TF-IDF vectorization** and **cosine similarity** to find projects with similar:
    - Project titles and descriptions
    - Technical keywords
    - Project characteristics

    **NEW:** You can now enter **any** Alberta procurement project - even if it's not in your database yet!
    Just paste the URL like: `https://purchasing.alberta.ca/posting/AB-2024-10281`

    ### 💼 Use Cases

    1. **💰 Bid Estimation**: Get recommended bid ranges based on similar past projects
    2. **🎯 Competition Analysis**: See who typically bids on similar projects
    3. **📊 Historical Context**: Learn from similar project outcomes and award patterns
    4. **📈 Market Intelligence**: Identify trends in similar project types

    ### 🔍 Input Options

    - **Reference Number:** `AB-2024-10281`
    - **Full URL:** `https://purchasing.alberta.ca/posting/AB-2024-10281`
    - **Custom Description:** Paste any project description to find matches

    ### ⚙️ Tips

    - **Higher similarity threshold** (70-90%): Very similar projects only
    - **Medium threshold** (30-60%): Related projects with some variation
    - **Lower threshold** (10-30%): Broader set of potentially relevant projects
    - **More results** = Better bid recommendations (aim for 10+ similar projects)
    """)

    # Show example projects
    st.subheader("📚 Sample Projects in Database")

    sample_df = queries.get_awarded_construction_projects(limit=10)

    if not sample_df.empty:
        sample_display = sample_df[['reference_number', 'short_title', 'actual_value', 'region']].copy()
        sample_display['actual_value'] = sample_display['actual_value'].apply(
            lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A"
        )

        st.dataframe(
            sample_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "reference_number": "Reference",
                "short_title": "Project Title",
                "actual_value": "Value",
                "region": "Region"
            }
        )
