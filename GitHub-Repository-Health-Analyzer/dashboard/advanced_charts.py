"""Advanced Plotly charts for engineering analytics."""

from typing import Dict

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def _placeholder_figure(title: str, message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(color="#8B949E", size=14),
    )
    fig.update_layout(
        title=title,
        paper_bgcolor="#161B22",
        plot_bgcolor="#0D1117",
        font_color="#F0F6FC",
        margin=dict(l=24, r=18, t=40, b=24),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig


def contribution_heatmap(commits_df: pd.DataFrame) -> go.Figure:
    """Render a weekly contribution-style heatmap from commit history."""
    if commits_df.empty or "commit_author_date" not in commits_df.columns:
        return _placeholder_figure(
            "Commit Contribution Heatmap",
            "No commit history is available to render the heatmap.",
        )

    df = commits_df.copy()
    df["date"] = pd.to_datetime(df["commit_author_date"], errors="coerce")
    df = df.dropna(subset=["date"])
    if df.empty:
        return _placeholder_figure(
            "Commit Contribution Heatmap",
            "No valid commit dates were found in the dataset.",
        )

    df["week_label"] = df["date"].dt.strftime("%Y-%U")
    df["weekday"] = df["date"].dt.weekday
    df = df.groupby(["week_label", "weekday"]).size().reset_index(name="commits")
    weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    df["weekday_name"] = df["weekday"].apply(
        lambda value: weekday_names[value] if 0 <= value < len(weekday_names) else str(value)
    )

    pivot = df.pivot(index="weekday_name", columns="week_label", values="commits").fillna(0)
    fig = go.Figure(
        go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale="Blues",
            hovertemplate="Week %{x}<br>%{y}: %{z} commits<extra></extra>",
        )
    )
    fig.update_layout(title="Commit Contribution Heatmap", xaxis_title="Week", yaxis_title="Day")
    return fig


def leaderboard_chart(contributors_df: pd.DataFrame) -> go.Figure:
    """Render a contributor leaderboard chart."""
    if contributors_df.empty or "login" not in contributors_df.columns:
        return _placeholder_figure(
            "Top Contributors Leaderboard",
            "No contributors data is available for this repository.",
        )

    df = contributors_df.copy()
    if "contributions" in df.columns:
        df["contributions"] = pd.to_numeric(df["contributions"], errors="coerce").fillna(0).astype(int)
    df = df.sort_values("contributions", ascending=False).head(10)
    if df.empty:
        return _placeholder_figure(
            "Top Contributors Leaderboard",
            "No contributor activity was detected in the selected period.",
        )

    fig = px.bar(
        df,
        x="contributions",
        y="login",
        orientation="h",
        color="contributions",
        color_continuous_scale="Blues",
        labels={"login": "Contributor", "contributions": "Contributions"},
    )
    fig.update_layout(title="Top Contributors Leaderboard", yaxis=dict(autorange="reversed"))
    return fig


def activity_timeline(commits_df: pd.DataFrame) -> go.Figure:
    """Render a repository activity timeline from commit history."""
    if commits_df.empty or "commit_author_date" not in commits_df.columns:
        return _placeholder_figure(
            "Repository Activity Timeline",
            "No repository activity data is available.",
        )

    df = commits_df.copy()
    df["date"] = pd.to_datetime(df["commit_author_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df = df.dropna(subset=["date"])
    summary = df.groupby("date").size().reset_index(name="commits").sort_values("date")
    if summary.empty:
        return _placeholder_figure(
            "Repository Activity Timeline",
            "No commit dates were available to build the timeline.",
        )

    fig = px.area(summary, x="date", y="commits", labels={"date": "Date", "commits": "Commits"})
    fig.update_layout(title="Repository Activity Timeline", xaxis_title="Date", yaxis_title="Commits")
    return fig


def health_score_trend(health_history: pd.DataFrame) -> go.Figure:
    """Render a health score trend chart."""
    if health_history.empty or "date" not in health_history.columns:
        return _placeholder_figure(
            "Health Score Trend",
            "Historical health score data is unavailable.",
        )

    fig = px.line(
        health_history,
        x="date",
        y="health_score",
        markers=True,
        labels={"date": "Date", "health_score": "Health Score"},
    )
    fig.update_layout(title="Health Score Trend", yaxis=dict(range=[0, 100]))
    return fig
