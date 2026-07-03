"""Page layout for the Streamlit dashboard."""

from typing import Any, Dict

import streamlit as st

from .components import render_kpi_card, render_metric_box, render_section_title
from .charts import (
    commit_trend_chart,
    contributor_chart,
    health_score_gauge,
    issue_chart,
    language_chart,
)
from .advanced_charts import (
    activity_timeline,
    contribution_heatmap,
    health_score_trend,
    leaderboard_chart,
)


def render_dashboard(metrics: Dict[str, Any], chart_data: Dict[str, Any], insights: Dict[str, Any]) -> None:
    """Render the main dashboard layout with KPIs, advanced charts, and premium insights."""
    st.markdown(
        "<div style='display: flex; justify-content: space-between; align-items: flex-start; gap: 24px; margin-bottom: 26px;'>"
        "<div><h1 style='margin: 0; font-size: 2.7rem;'>Executive Dashboard</h1>"
        "<p style='margin: 10px 0 0; color: #8B949E; font-size: 1rem;'>Premium insights across repository stability, velocity, and community health.</p></div>"
        "<div style='background: #161B22; border: 1px solid #30363D; border-radius: 18px; padding: 14px 24px; color: #58A6FF; font-weight: 600;'>Repository Analytics</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div class='summary-grid'>"
        "<div class='summary-card'><h3>Repository Summary</h3>"
        f"<p>{metrics.get('primary_language', 'N/A')} • {metrics.get('repository_age_days', 'N/A')} days old</p></div>"
        "<div class='summary-card'><h3>Engineering Metrics</h3>"
        f"<p>{metrics.get('total_commits', 'N/A')} commits • {metrics.get('total_contributors', 'N/A')} contributors</p></div>"
        "<div class='summary-card'><h3>Repository Health</h3>"
        f"<p>{metrics.get('health_score', 'N/A')}% • {metrics.get('health_grade', 'N/A')}</p></div>"
        "</div>",
        unsafe_allow_html=True,
    )

    kpi_cols = st.columns(4)
    with kpi_cols[0]:
        render_kpi_card("Total Commits", metrics.get("total_commits", "N/A"), "Historical commit volume", "↗ 8%")
    with kpi_cols[1]:
        render_kpi_card("Contributors", metrics.get("total_contributors", "N/A"), "Active collaborators", "↗ 4%")
    with kpi_cols[2]:
        render_kpi_card("Open Issues", metrics.get("open_issues", "N/A"), "Current backlog", "▼ 3%")
    with kpi_cols[3]:
        render_kpi_card("Health Score", metrics.get("health_score", "N/A"), metrics.get("health_grade", ""), "Stable")

    render_section_title("Analytics Overview", "A polished view of repository trends and adoption.")

    chart_cols = st.columns([2, 1])
    chart_cols[0].plotly_chart(commit_trend_chart(chart_data["commits"]), use_container_width=True, key="commit_activity_chart")
    chart_cols[1].plotly_chart(health_score_gauge(metrics.get("health_score", 0.0)), use_container_width=True, key="repository_health_gauge")

    chart_cols = st.columns(2)
    chart_cols[0].plotly_chart(contributor_chart(chart_data["contributors"]), use_container_width=True, key="top_contributors_chart")
    chart_cols[1].plotly_chart(language_chart(chart_data["languages"]), use_container_width=True, key="language_distribution_chart")

    st.plotly_chart(issue_chart(chart_data["issues"]), use_container_width=True, key="issue_status_chart")

    render_section_title("Advanced Engineering Analytics", "Team velocity, contributor momentum, and operational health trends.")
    advanced_cols = st.columns([1.2, 1])
    advanced_cols[0].plotly_chart(activity_timeline(chart_data["raw_commits"]), use_container_width=True, key="repository_growth_chart")
    advanced_cols[0].plotly_chart(contribution_heatmap(chart_data["raw_commits"]), use_container_width=True, key="contribution_heatmap_chart")
    advanced_cols[1].plotly_chart(leaderboard_chart(chart_data["raw_contributors"]), use_container_width=True, key="contributor_leaderboard_chart")
    advanced_cols[1].plotly_chart(health_score_trend(chart_data["health_history"]), use_container_width=True, key="health_score_trend_chart")

    render_section_title("Premium Recommendations", "Actionable guidance based on current repository health and team signals.")
    rec_cols = st.columns([2, 1])
    with rec_cols[0]:
        st.markdown("<div style='background: #161B22; border: 1px solid #30363D; border-radius: 18px; padding: 20px; margin-bottom: 18px;'>", unsafe_allow_html=True)
        st.markdown("<h3 style='margin-top: 0; color: #F0F6FC;'>Key Insights</h3>", unsafe_allow_html=True)
        for insight in insights.get("insights", []):
            st.markdown(f"<p style='color: #C9D1D9; margin: 8px 0 12px;'>&#8226; {insight}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='background: #161B22; border: 1px solid #30363D; border-radius: 18px; padding: 20px;'>", unsafe_allow_html=True)
        st.markdown("<h3 style='margin-top: 0; color: #F0F6FC;'>Recommendations</h3>", unsafe_allow_html=True)
        for recommendation in insights.get("recommendations", []):
            st.markdown(f"<p style='color: #C9D1D9; margin: 8px 0 12px;'>&#8226; {recommendation}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with rec_cols[1]:
        render_metric_box("Top Contributor", metrics.get("top_contributor", "N/A"), "Most active team member this period")
        render_metric_box("Contributions", metrics.get("total_contributions", "N/A"), "Across the top contributors")
        render_metric_box("Issue Close Rate", f"{metrics.get('issue_close_rate', 'N/A')}%", "Resolution velocity")
        render_metric_box("Avg Comments", metrics.get("average_comments", "N/A"), "Collaboration depth")

    st.markdown(
        "<footer class='dashboard-footer'>Powered by premium engineering analytics • Built for modern teams.</footer>",
        unsafe_allow_html=True,
    )
