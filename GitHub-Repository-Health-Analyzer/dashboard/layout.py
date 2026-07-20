"""Page layout for the Streamlit dashboard."""

from html import escape
from typing import Any, Dict

import streamlit as st

from .components import render_kpi_card, render_metric_box, render_section_title
from .charts import (
    commit_trend_chart,
    contributor_chart,
    health_score_gauge,
    issue_chart,
    issue_timeline_chart,
    language_chart,
)
from .advanced_charts import (
    activity_timeline,
    contribution_heatmap,
    health_score_trend,
    leaderboard_chart,
)


def _render_repository_overview(repository_overview: Dict[str, str]) -> None:
    """Render live repository metadata returned by the GitHub API."""
    if not repository_overview:
        st.info("Repository overview is unavailable for this analysis.")
        return

    repository_url = repository_overview.get("Repository URL", "")
    escaped_url = escape(repository_url)
    overview_items = [
        ("Repository Name", repository_overview.get("Repository Name", "Not available")),
        ("Owner", repository_overview.get("Owner", "Not available")),
        ("Description", repository_overview.get("Description", "Not available")),
        ("Repository URL", f"<a href='{escaped_url}' target='_blank' rel='noopener noreferrer'>{escaped_url}</a>" if repository_url else "Not available"),
        ("Primary Language", repository_overview.get("Primary Language", "Not available")),
        ("Stars", repository_overview.get("Stars", "Not available")),
        ("Forks", repository_overview.get("Forks", "Not available")),
        ("Watchers", repository_overview.get("Watchers", "Not available")),
        ("Open Issues", repository_overview.get("Open Issues", "Not available")),
        ("License", repository_overview.get("License", "Not available")),
        ("Default Branch", repository_overview.get("Default Branch", "Not available")),
        ("Repository Age", repository_overview.get("Repository Age", "Not available")),
        ("Created Date", repository_overview.get("Created Date", "Not available")),
        ("Last Updated", repository_overview.get("Last Updated", "Not available")),
        ("Last Push Date", repository_overview.get("Last Push Date", "Not available")),
        ("Repository Visibility", repository_overview.get("Repository Visibility", "Not available")),
        ("Repository Size", repository_overview.get("Repository Size", "Not available")),
    ]
    detail_html = "".join(
        "<div class='overview-item'>"
        f"<span class='overview-item__label'>{escape(label)}</span>"
        f"<span class='overview-item__value'>{value if label == 'Repository URL' else escape(str(value))}</span>"
        "</div>"
        for label, value in overview_items
    )

    st.markdown(
        "<section class='repository-overview'>"
        "<div class='section-title'><h2>Repository Overview</h2>"
        "<p>Live repository metadata from the GitHub API for the selected repository.</p></div>"
        f"<div class='overview-grid'>{detail_html}</div>"
        "</section>",
        unsafe_allow_html=True,
    )


def _format_kpi_number(value: Any) -> str:
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "0"


def _format_health_score(value: Any) -> str:
    try:
        return f"{float(value):.1f}%"
    except (TypeError, ValueError):
        return "0.0%"


def _format_score(value: Any) -> str:
    try:
        return f"{float(value):.1f}"
    except (TypeError, ValueError):
        return "0.0"


def _build_kpi_cards(metrics: Dict[str, Any]) -> list[tuple[str, str, str, str]]:
    """Build the executive KPI card data from precomputed dashboard metrics."""
    return [
        ("Total Commits", _format_kpi_number(metrics.get("total_commits", 0)), "Fetched commit activity", ""),
        ("Total Contributors", _format_kpi_number(metrics.get("total_contributors", 0)), "Unique contributors", ""),
        ("Open Issues", _format_kpi_number(metrics.get("open_issues", 0)), "Unresolved issue backlog", ""),
        ("Closed Issues", _format_kpi_number(metrics.get("closed_issues", 0)), "Resolved issue volume", ""),
        ("Open Pull Requests", _format_kpi_number(metrics.get("open_pull_requests", 0)), "Pull requests awaiting merge", ""),
        ("Merged Pull Requests", _format_kpi_number(metrics.get("merged_pull_requests", 0)), "Pull requests merged", ""),
        ("Repository Age", f"{_format_kpi_number(metrics.get('repository_age_days', 0))} days", "Time since repository creation", ""),
        ("Stars", _format_kpi_number(metrics.get("stars", 0)), "GitHub stars", ""),
        ("Forks", _format_kpi_number(metrics.get("forks", 0)), "Repository forks", ""),
        ("Watchers", _format_kpi_number(metrics.get("watchers", 0)), "GitHub watchers", ""),
        ("Health Score", _format_health_score(metrics.get("health_score", 0.0)), f"Grade {metrics.get('overall_grade', metrics.get('health_grade', 'Pending'))}", ""),
    ]


def _render_kpi_cards(metrics: Dict[str, Any]) -> None:
    """Render the executive KPI card grid organized by logical category."""
    render_section_title("Executive KPIs", "Live engineering signals for the analyzed repository.")
    cards = _build_kpi_cards(metrics)
    card_map = {label: (value, description) for label, value, description, _ in cards}

    # Group 1: General & Popularity
    st.markdown("<h4 class='sidebar-section-header' style='margin: 18px 0 10px; font-size: 0.95rem;'>Metadata & Popularity</h4>", unsafe_allow_html=True)
    g1_labels = ["Health Score", "Repository Age", "Stars", "Watchers", "Forks"]
    g1_cols = st.columns(5)
    for col, label in zip(g1_cols, g1_labels):
        if label in card_map:
            val, desc = card_map[label]
            with col:
                render_kpi_card(label, val, desc)

    # Group 2: Development Activity
    st.markdown("<h4 class='sidebar-section-header' style='margin: 18px 0 10px; font-size: 0.95rem;'>Development Activity</h4>", unsafe_allow_html=True)
    g2_labels = ["Total Commits", "Total Contributors"]
    g2_cols = st.columns(4)
    for col, label in zip(g2_cols[:2], g2_labels):
        if label in card_map:
            val, desc = card_map[label]
            with col:
                render_kpi_card(label, val, desc)

    # Group 3: Work Items (Issues & PRs)
    st.markdown("<h4 class='sidebar-section-header' style='margin: 18px 0 10px; font-size: 0.95rem;'>Work Items</h4>", unsafe_allow_html=True)
    g3_labels = ["Open Issues", "Closed Issues", "Open Pull Requests", "Merged Pull Requests"]
    g3_cols = st.columns(4)
    for col, label in zip(g3_cols, g3_labels):
        if label in card_map:
            val, desc = card_map[label]
            with col:
                render_kpi_card(label, val, desc)


def _render_repository_intelligence(metrics: Dict[str, Any]) -> None:
    """Render the Repository Intelligence panel from the health score payload."""
    render_section_title(
        "Repository Intelligence",
        "A scored view of repository health, maintenance, community strength, and popularity.",
    )
    sub_scores = [
        ("Repository Health", metrics.get("repository_health", 0.0), "Activity, contributors, issue resolution, and age"),
        ("Maintenance Score", metrics.get("maintenance_score", 0.0), "Recent commits, issue handling, and pull request flow"),
        ("Community Score", metrics.get("community_score", 0.0), "Contributor diversity, watchers, and issue discussion"),
        ("Popularity Score", metrics.get("popularity_score", 0.0), "Stars, forks, and watchers"),
    ]
    score_cards = "".join(
        "<div class='intelligence-score-card'>"
        f"<span>{escape(label)}</span>"
        f"<strong>{escape(_format_score(value))}</strong>"
        f"<small>{escape(description)}</small>"
        "</div>"
        for label, value, description in sub_scores
    )
    explanation = metrics.get("score_explanation", "Repository intelligence is unavailable.")
    grade = metrics.get("overall_grade", metrics.get("health_grade", "Pending"))

    left_col, right_col = st.columns([1.35, 1])
    with left_col:
        st.markdown(
            "<section class='repository-intelligence'>"
            "<div class='intelligence-hero'>"
            "<div>"
            "<span class='intelligence-eyebrow'>Overall Repository Score</span>"
            f"<div class='intelligence-score'>{escape(_format_score(metrics.get('health_score', 0.0)))}</div>"
            f"<p>Repository Health: {escape(str(metrics.get('health_label', 'Pending')))}</p>"
            "</div>"
            f"<div class='intelligence-grade'>{escape(str(grade))}</div>"
            "</div>"
            f"<div class='intelligence-grid'>{score_cards}</div>"
            f"<p class='intelligence-explanation'>{escape(str(explanation))}</p>"
            "</section>",
            unsafe_allow_html=True,
        )
    with right_col:
        st.plotly_chart(
            health_score_gauge(metrics.get("health_score", 0.0)),
            use_container_width=True,
            key="repository_intelligence_gauge",
        )


def _render_insight_card(item: Any) -> str:
    """Return HTML for an engineering insight or recommendation card."""
    if isinstance(item, dict):
        severity = str(item.get("severity", "Info"))
        icon = str(item.get("icon", "&#9432;"))
        title = str(item.get("title", "Engineering signal"))
        explanation = str(item.get("explanation", "Metric-backed signal is unavailable."))
    else:
        severity = "Info"
        icon = "&#9432;"
        title = str(item)
        explanation = str(item)

    severity_class = severity.lower()
    return (
        f"<div class='engineering-card engineering-card--{escape(severity_class)}'>"
        "<div class='engineering-card__top'>"
        f"<span class='engineering-card__icon'>{icon}</span>"
        f"<span class='engineering-card__severity'>{escape(severity)}</span>"
        "</div>"
        f"<h3>{escape(title)}</h3>"
        f"<p>{escape(explanation)}</p>"
        "</div>"
    )


def _render_engineering_insights(insights: Dict[str, Any]) -> None:
    """Render deterministic engineering insights and recommendation cards."""
    render_section_title(
        "Engineering Insights",
        "Decision-support signals generated from repository analytics and health scoring.",
    )

    insight_items = insights.get("insights", [])
    recommendation_items = insights.get("recommendations", [])
    insight_html = "".join(_render_insight_card(item) for item in insight_items)
    recommendation_html = "".join(_render_insight_card(item) for item in recommendation_items)

    st.markdown(
        "<section class='engineering-insights-section'>"
        "<div class='engineering-insights-grid'>"
        f"{insight_html}"
        "</div>"
        "</section>",
        unsafe_allow_html=True,
    )

    render_section_title(
        "Recommendations",
        "Actionable next steps tied directly to detected repository conditions.",
    )
    st.markdown(
        "<section class='engineering-recommendations-section'>"
        "<div class='engineering-actions-grid'>"
        f"{recommendation_html}"
        "</div>"
        "</section>",
        unsafe_allow_html=True,
    )


def render_dashboard(
    metrics: Dict[str, Any],
    chart_data: Dict[str, Any],
    insights: Dict[str, Any],
    repository_overview: Dict[str, str],
) -> None:
    """Render the main dashboard layout with KPIs, advanced charts, and premium insights."""
    repo_name = repository_overview.get("Repository Name", "")
    repo_owner = repository_overview.get("Owner", "")
    repo_title = f"{repo_owner} / {repo_name}" if (repo_owner and repo_name) else "Repository Dashboard"
    
    st.markdown(
        f"<div class='dashboard-header'>"
        f"<div>"
        f"<span class='dashboard-eyebrow'>GitHub Repository Analytics</span>"
        f"<h1 class='dashboard-title'>{escape(repo_title)}</h1>"
        f"<p class='dashboard-subtitle'>Premium insights across repository stability, velocity, and community health.</p>"
        f"</div>"
        f"<div class='dashboard-badge'>Repository Analytics</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    _render_repository_overview(repository_overview)
    _render_kpi_cards(metrics)
    _render_repository_intelligence(metrics)

    st.markdown(
        "<div class='summary-grid'>"
        "<div class='summary-card'><h3>Repository Summary</h3>"
        f"<p>{metrics.get('primary_language', 'N/A')} • {metrics.get('repository_age_days', 'N/A')} days old</p></div>"
        "<div class='summary-card'><h3>Engineering Metrics</h3>"
        f"<p>{metrics.get('total_commits', 'N/A')} commits • {metrics.get('total_contributors', 'N/A')} contributors</p></div>"
        "<div class='summary-card'><h3>Repository Health</h3>"
        f"<p>{metrics.get('health_score', 'N/A')}% • Grade {metrics.get('overall_grade', 'N/A')}</p></div>"
        "</div>",
        unsafe_allow_html=True,
    )

    render_section_title("Core Charts", "Live Plotly charts for repository activity, issues, languages, and contributors.")

    chart_cols = st.columns([2, 1])
    chart_cols[0].plotly_chart(commit_trend_chart(chart_data["commits"]), use_container_width=True, key="commit_timeline_chart")
    chart_cols[1].plotly_chart(health_score_gauge(metrics.get("health_score", 0.0)), use_container_width=True, key="repository_health_gauge")

    chart_cols = st.columns(2)
    chart_cols[0].plotly_chart(issue_timeline_chart(chart_data["issue_timeline"]), use_container_width=True, key="issue_timeline_chart")
    chart_cols[1].plotly_chart(language_chart(chart_data["languages"]), use_container_width=True, key="language_distribution_chart")

    chart_cols = st.columns(2)
    chart_cols[0].plotly_chart(contributor_chart(chart_data["contributors"]), use_container_width=True, key="contributor_leaderboard_chart")
    chart_cols[1].plotly_chart(issue_chart(chart_data["issues"]), use_container_width=True, key="issue_status_chart")

    render_section_title("Advanced Engineering Analytics", "Team velocity, contributor momentum, and operational health trends.")
    advanced_cols = st.columns([1.2, 1])
    advanced_cols[0].plotly_chart(activity_timeline(chart_data["raw_commits"], chart_data["raw_issues"]), use_container_width=True, key="repository_activity_chart")
    advanced_cols[0].plotly_chart(contribution_heatmap(chart_data["raw_commits"]), use_container_width=True, key="contribution_heatmap_chart")
    advanced_cols[1].plotly_chart(leaderboard_chart(chart_data["raw_contributors"]), use_container_width=True, key="advanced_contributor_leaderboard_chart")
    advanced_cols[1].plotly_chart(health_score_trend(chart_data["health_history"]), use_container_width=True, key="health_score_trend_chart")

    _render_engineering_insights(insights)

    rec_cols = st.columns([1, 1, 1, 1])
    with rec_cols[0]:
        render_metric_box("Top Contributor", metrics.get("top_contributor", "N/A"), "Most active team member this period")
    with rec_cols[1]:
        render_metric_box("Contributions", metrics.get("total_contributions", "N/A"), "Across the top contributors")
    with rec_cols[2]:
        render_metric_box("Issue Close Rate", f"{metrics.get('issue_close_rate', 'N/A')}%", "Resolution velocity")
    with rec_cols[3]:
        render_metric_box("Avg Comments", metrics.get("average_comments", "N/A"), "Collaboration depth")

    st.markdown(
        "<footer class='dashboard-footer'>Powered by premium engineering analytics • Built for modern teams.</footer>",
        unsafe_allow_html=True,
    )
