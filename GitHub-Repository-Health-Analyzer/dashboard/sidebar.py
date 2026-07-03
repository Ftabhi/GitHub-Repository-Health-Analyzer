"""Sidebar controls for the Streamlit dashboard."""

from typing import List, Tuple

import streamlit as st

from .theme import SIDEBAR_COLOR, TEXT_COLOR, SECONDARY_COLOR, PRIMARY_COLOR


def render_sidebar() -> Tuple[str, bool]:
    """Render repository input, analyze button, and filter controls."""
    st.sidebar.markdown("# Executive Dashboard")
    st.sidebar.markdown(
        "<p class='dashboard-sidebar-note'>Premium engineering analytics for repository performance, reliability, and team velocity.</p>",
        unsafe_allow_html=True,
    )

    repository_url = st.sidebar.text_input(
        "GitHub Repository URL",
        placeholder="https://github.com/owner/repository",
        key="repository_url_input",
    )

    analyze_button = st.sidebar.button("🚀 Analyze Repository", key="analyze_repository")

    st.sidebar.markdown("---")
    st.sidebar.markdown("<h4 style='margin: 0 0 8px; color: #F0F6FC;'>Filters</h4>", unsafe_allow_html=True)
    st.sidebar.checkbox("Show closed issues", value=True)
    st.sidebar.checkbox("Show pull requests", value=True)
    st.sidebar.checkbox("Show top contributors only", value=False)

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "<div class='dashboard-sidebar-note'>Analyze any public GitHub repository and load fresh analytics.</div>",
        unsafe_allow_html=True,
    )

    return repository_url, analyze_button
