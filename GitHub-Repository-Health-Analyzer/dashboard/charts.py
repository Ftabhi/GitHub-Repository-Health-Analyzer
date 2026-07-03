"""Placeholder chart functions for the Streamlit dashboard."""

from typing import Any, Dict

import pandas as pd
import plotly.graph_objects as go


def commit_trend_chart(data: pd.DataFrame) -> go.Figure:
    """Return a commit activity timeline chart."""
    if data.empty:
        data = pd.DataFrame({"date": [], "commits": []})

    fig = go.Figure(
        go.Scatter(
            x=data["date"],
            y=data["commits"],
            mode="lines+markers",
            marker=dict(color="#58A6FF", size=6),
            line=dict(shape="spline", smoothing=1.2, color="#58A6FF"),
        )
    )
    fig.update_layout(
        title="Commit Activity Timeline",
        xaxis_title="Date",
        yaxis_title="Commits",
        paper_bgcolor="#161B22",
        plot_bgcolor="#0D1117",
        font_color="#F0F6FC",
        margin=dict(l=24, r=16, t=40, b=24),
    )
    fig.update_xaxes(gridcolor="#30363D", zeroline=False, color="#C9D1D9")
    fig.update_yaxes(gridcolor="#30363D", zeroline=False, color="#C9D1D9")
    return fig


def contributor_chart(data: pd.DataFrame) -> go.Figure:
    """Return a contributors bar chart."""
    if data.empty:
        data = pd.DataFrame({"contributor": [], "contributions": []})

    fig = go.Figure(
        go.Bar(
            x=data["contributor"],
            y=data["contributions"],
            marker_color="#58A6FF",
            marker_line_color="#0D1117",
            marker_line_width=1,
        )
    )
    fig.update_layout(
        title="Top Contributors",
        xaxis_title="Contributor",
        yaxis_title="Contributions",
        paper_bgcolor="#161B22",
        plot_bgcolor="#0D1117",
        font_color="#F0F6FC",
        margin=dict(l=22, r=16, t=40, b=30),
    )
    fig.update_xaxes(tickangle=-45, tickfont_color="#C9D1D9", gridcolor="#30363D", zeroline=False)
    fig.update_yaxes(gridcolor="#30363D", zeroline=False, color="#C9D1D9")
    return fig


def issue_chart(data: pd.DataFrame) -> go.Figure:
    """Return an issue status pie chart."""
    if data.empty:
        data = pd.DataFrame({"state": ["No Data"], "count": [1]})

    fig = go.Figure(
        go.Pie(
            labels=data["state"],
            values=data["count"],
            hole=0.4,
            marker=dict(line=dict(color="#0D1117", width=1)),
            textinfo="label+percent",
            textfont=dict(color="#F0F6FC"),
        )
    )
    fig.update_layout(
        title="Issue Status Breakdown",
        paper_bgcolor="#161B22",
        font_color="#F0F6FC",
        margin=dict(l=16, r=16, t=40, b=16),
    )
    return fig


def language_chart(data: pd.DataFrame) -> go.Figure:
    """Return a language distribution donut chart."""
    if data.empty:
        data = pd.DataFrame({"language": ["Unknown"], "bytes": [1]})

    fig = go.Figure(
        go.Pie(
            labels=data["language"],
            values=data["bytes"],
            hole=0.55,
            marker=dict(line=dict(color="#0D1117", width=1)),
            textinfo="label+percent",
            textfont=dict(color="#F0F6FC"),
        )
    )
    fig.update_layout(
        title="Language Distribution",
        paper_bgcolor="#161B22",
        font_color="#F0F6FC",
        margin=dict(l=16, r=16, t=40, b=16),
    )
    return fig


def health_score_gauge(score: float) -> go.Figure:
    """Return a repository health gauge chart."""
    display_score = score if isinstance(score, (int, float)) else 0.0
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=display_score,
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#C9D1D9"},
                "bar": {"color": "#58A6FF"},
                "bgcolor": "#0D1117",
                "steps": [
                    {"range": [0, 40], "color": "#F25F5C"},
                    {"range": [40, 70], "color": "#FFB850"},
                    {"range": [70, 100], "color": "#4CB944"},
                ],
            },
            number={"suffix": "%", "font": {"color": "#F0F6FC"}},
            domain={"x": [0, 1], "y": [0, 1]},
        )
    )
    fig.update_layout(
        title="Repository Health Score",
        paper_bgcolor="#161B22",
        font_color="#F0F6FC",
        margin=dict(l=16, r=16, t=40, b=16),
    )
    return fig
