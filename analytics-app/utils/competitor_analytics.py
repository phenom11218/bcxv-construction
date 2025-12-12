"""
Competitor Analytics Helper Functions
======================================
Utility functions for analyzing competitor data and generating insights.

Author: BCXV Construction Analytics
Date: 2025-12-11
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List


def format_currency(value: float) -> str:
    """Format value as currency."""
    if pd.isna(value) or value == 0:
        return "N/A"
    return f"${value:,.0f}"


def format_percentage(value: float) -> str:
    """Format value as percentage."""
    if pd.isna(value):
        return "N/A"
    return f"{value:.1f}%"


def calculate_win_rate_trend(df: pd.DataFrame, period: str = 'year') -> pd.DataFrame:
    """
    Calculate win rate trend over time.

    Args:
        df: DataFrame with bidding history (must have close_date, is_winner)
        period: 'year', 'quarter', or 'month'

    Returns:
        DataFrame with time periods and win rates
    """
    if df.empty or 'close_date' not in df.columns:
        return pd.DataFrame()

    df = df.copy()
    df['close_date'] = pd.to_datetime(df['close_date'])

    if period == 'year':
        df['period'] = df['close_date'].dt.year
    elif period == 'quarter':
        df['period'] = df['close_date'].dt.to_period('Q').astype(str)
    else:  # month
        df['period'] = df['close_date'].dt.to_period('M').astype(str)

    trend = df.groupby('period').agg({
        'is_winner': ['sum', 'count']
    }).reset_index()

    trend.columns = ['period', 'wins', 'total']
    trend['win_rate'] = (trend['wins'] / trend['total'] * 100).round(1)

    return trend


def create_win_rate_chart(df: pd.DataFrame, company_name: str) -> go.Figure:
    """
    Create win rate timeline chart.

    Args:
        df: DataFrame with time periods and win rates (expects 'year' or 'period' column)
        company_name: Name of company for title

    Returns:
        Plotly figure
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", showarrow=False)
        return fig

    # Make a copy to avoid modifying original
    df = df.copy()

    # Detect column names - handle both 'year'/'period' and 'total_bids'/'bids'
    period_col = 'year' if 'year' in df.columns else 'period'
    bids_col = 'total_bids' if 'total_bids' in df.columns else 'bids'

    fig = go.Figure()

    # Add line for win rate
    fig.add_trace(go.Scatter(
        x=df[period_col],
        y=df['win_rate'],
        mode='lines+markers',
        name='Win Rate',
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=8)
    ))

    # Add bars for total bids
    fig.add_trace(go.Bar(
        x=df[period_col],
        y=df[bids_col],
        name='Total Bids',
        yaxis='y2',
        opacity=0.3,
        marker=dict(color='#ff7f0e')
    ))

    fig.update_layout(
        title=f"Win Rate Trend - {company_name}",
        xaxis_title="Year",
        yaxis_title="Win Rate (%)",
        yaxis2=dict(
            title="Total Bids",
            overlaying='y',
            side='right'
        ),
        hovermode='x unified',
        height=400
    )

    return fig


def create_category_breakdown_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create pie chart of category distribution.

    Args:
        df: DataFrame with category breakdown

    Returns:
        Plotly figure
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", showarrow=False)
        return fig

    # Detect column name - handle both 'total_bids' and 'bids'
    bids_col = 'total_bids' if 'total_bids' in df.columns else 'bids'

    fig = px.pie(
        df,
        values=bids_col,
        names='category_code',
        title="Bid Distribution by Category",
        hole=0.3
    )

    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=400)

    return fig


def create_regional_focus_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create bar chart of regional distribution.

    Args:
        df: DataFrame with regional breakdown

    Returns:
        Plotly figure
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", showarrow=False)
        return fig

    # Detect column name - handle both 'total_bids' and 'bids'
    bids_col = 'total_bids' if 'total_bids' in df.columns else 'bids'

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df['region'],
        y=df[bids_col],
        name='Total Bids',
        marker=dict(color='#1f77b4')
    ))

    fig.add_trace(go.Bar(
        x=df['region'],
        y=df['wins'],
        name='Wins',
        marker=dict(color='#2ca02c')
    ))

    fig.update_layout(
        title="Regional Focus",
        xaxis_title="Region",
        yaxis_title="Count",
        barmode='group',
        height=400
    )

    return fig


def create_bid_distribution_histogram(bid_amounts, company_name: str = "") -> go.Figure:
    """
    Create histogram of bid amounts.

    Args:
        bid_amounts: Series or DataFrame with bid amounts
        company_name: Name of company for title (optional)

    Returns:
        Plotly figure
    """
    # Handle both Series and DataFrame inputs
    if isinstance(bid_amounts, pd.DataFrame):
        if 'bid_amount' not in bid_amounts.columns:
            fig = go.Figure()
            fig.add_annotation(text="No data available", showarrow=False)
            return fig
        bid_data = bid_amounts['bid_amount'].dropna()
    else:
        # It's a Series
        bid_data = bid_amounts.dropna() if hasattr(bid_amounts, 'dropna') else bid_amounts

    if len(bid_data) == 0:
        fig = go.Figure()
        fig.add_annotation(text="No bid amount data available", showarrow=False)
        return fig

    title = f"Bid Amount Distribution - {company_name}" if company_name else "Bid Amount Distribution"

    fig = px.histogram(
        bid_data,
        nbins=20,
        title=title,
        labels={'value': 'Bid Amount ($)', 'count': 'Frequency'}
    )

    fig.update_layout(
        xaxis_title="Bid Amount ($)",
        yaxis_title="Number of Bids",
        height=400,
        showlegend=False
    )

    return fig


def create_head_to_head_comparison_chart(stats_a: Dict, stats_b: Dict, name_a: str, name_b: str) -> go.Figure:
    """
    Create comparison chart for two companies.

    Args:
        stats_a: Statistics for company A
        stats_b: Statistics for company B
        name_a: Name of company A
        name_b: Name of company B

    Returns:
        Plotly figure
    """
    categories = ['Total Bids', 'Wins', 'Win Rate (%)', 'Avg Bid ($)']

    values_a = [
        stats_a.get('total_bids', 0),
        stats_a.get('wins', 0),
        stats_a.get('win_rate', 0),
        stats_a.get('avg_bid', 0) / 1000  # Convert to thousands for scale
    ]

    values_b = [
        stats_b.get('total_bids', 0),
        stats_b.get('wins', 0),
        stats_b.get('win_rate', 0),
        stats_b.get('avg_bid', 0) / 1000
    ]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name=name_a,
        x=categories,
        y=values_a,
        marker=dict(color='#1f77b4')
    ))

    fig.add_trace(go.Bar(
        name=name_b,
        x=categories,
        y=values_b,
        marker=dict(color='#ff7f0e')
    ))

    fig.update_layout(
        title=f"Head-to-Head Comparison: {name_a} vs {name_b}",
        barmode='group',
        yaxis_title="Value",
        height=400
    )

    return fig


def calculate_competitive_position(company_stats: Dict) -> str:
    """
    Calculate company's competitive position based on performance.

    Args:
        company_stats: Company statistics

    Returns:
        Position label string
    """
    win_rate = company_stats.get('win_rate', 0)
    total_bids = company_stats.get('total_bids', 0)

    # Determine position based on win rate and activity
    if win_rate > 50 and total_bids > 50:
        return "🏆 Market Leader"
    elif win_rate > 40 and total_bids > 20:
        return "💪 Strong Competitor"
    elif win_rate > 30 or total_bids > 30:
        return "✓ Average Performer"
    elif total_bids > 10:
        return "📊 Emerging Player"
    else:
        return "🌱 New Entrant"


def generate_company_insights(company_stats: Dict, category_df: pd.DataFrame, year_df: pd.DataFrame) -> List[str]:
    """
    Generate key insights about a company.

    Args:
        company_stats: Company summary statistics
        category_df: Category breakdown DataFrame
        year_df: Year-over-year DataFrame

    Returns:
        List of insight strings
    """
    insights = []

    # Win rate insight
    win_rate = company_stats.get('win_rate', 0)
    if win_rate > 50:
        insights.append(f"🎯 Strong performer with {win_rate:.1f}% win rate")
    elif win_rate > 30:
        insights.append(f"✓ Competitive with {win_rate:.1f}% win rate")
    else:
        insights.append(f"📊 Win rate at {win_rate:.1f}%")

    # Category specialization
    if not category_df.empty:
        top_category = category_df.iloc[0]
        # Use 'total_bids' column name (renamed by alias method)
        top_cat_bids = top_category.get('total_bids', top_category.get('bids', 0))
        if top_cat_bids >= company_stats.get('total_bids', 1) * 0.7:
            insights.append(f"🏗️ Specialized in {top_category['category_code']} ({top_cat_bids} bids)")

    # Trend analysis
    if not year_df.empty and len(year_df) >= 2:
        recent_year = year_df.iloc[0]
        prev_year = year_df.iloc[1]
        # Use 'total_bids' column name (renamed by alias method)
        recent_bids = recent_year.get('total_bids', recent_year.get('bids', 0))
        prev_bids = prev_year.get('total_bids', prev_year.get('bids', 0))
        if recent_bids > prev_bids * 1.2:
            insights.append(f"📈 Growing - {recent_bids} bids this year vs {prev_bids} last year")
        elif recent_bids < prev_bids * 0.8:
            insights.append(f"📉 Declining - {recent_bids} bids this year vs {prev_bids} last year")

    # Bid size analysis
    avg_bid = company_stats.get('avg_bid', 0)
    if avg_bid > 1_000_000:
        insights.append(f"💰 Large project focus - avg bid ${avg_bid:,.0f}")
    elif avg_bid > 500_000:
        insights.append(f"💵 Mid-size project focus - avg bid ${avg_bid:,.0f}")

    # Total value
    total_value = company_stats.get('total_won_value', 0)
    if total_value > 10_000_000:
        insights.append(f"🏆 Major player - ${total_value:,.0f} in total awards")

    return insights


def calculate_overlap_score(company_a_projects: set, company_b_projects: set) -> float:
    """
    Calculate competitive overlap between two companies.

    Args:
        company_a_projects: Set of project references for company A
        company_b_projects: Set of project references for company B

    Returns:
        Overlap score (0-100)
    """
    if not company_a_projects or not company_b_projects:
        return 0.0

    intersection = company_a_projects & company_b_projects
    union = company_a_projects | company_b_projects

    if len(union) == 0:
        return 0.0

    return (len(intersection) / len(union)) * 100
