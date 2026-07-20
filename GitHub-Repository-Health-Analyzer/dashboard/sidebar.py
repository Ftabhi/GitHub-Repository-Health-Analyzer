"""Sidebar controls for the Streamlit dashboard."""

from typing import List, Tuple

import streamlit as st

from .theme import SIDEBAR_COLOR, TEXT_COLOR, SECONDARY_COLOR, PRIMARY_COLOR


def render_sidebar(discovered_repos: List[str]) -> Tuple[str, bool, str]:
    """Render repository input, analyze button, and filter controls."""
    st.sidebar.markdown("<h2 class='sidebar-title'>Executive Dashboard</h2>", unsafe_allow_html=True)
    st.sidebar.markdown(
        "<p class='dashboard-sidebar-note'>Premium engineering analytics for repository performance, reliability, and team velocity.</p>",
        unsafe_allow_html=True,
    )

    st.sidebar.markdown("---")

    # 1. Switch Repository Selectbox
    st.sidebar.markdown("<h4 class='sidebar-section-header'>Switch Repository</h4>", unsafe_allow_html=True)
    current_selected = st.session_state.get("selected_repository", "")
    
    # Standard options
    options = [""] + sorted(discovered_repos)
    default_idx = 0
    if current_selected in options:
        default_idx = options.index(current_selected)
    elif len(options) > 1:
        # Default to first discovered repository if none is set
        default_idx = 1
        st.session_state["selected_repository"] = options[1]

    selected_repo = st.sidebar.selectbox(
        "Select an analyzed repository",
        options=options,
        index=default_idx,
        format_func=lambda x: "Select repository..." if x == "" else x,
        key="sidebar_repo_selectbox",
    )

    st.sidebar.markdown("---")

    # 2. Analyze New Repository
    st.sidebar.markdown("<h4 class='sidebar-section-header'>Analyze New Repository</h4>", unsafe_allow_html=True)
    repository_url = st.sidebar.text_input(
        "GitHub Repository URL",
        placeholder="https://github.com/owner/repository",
        key="repository_url_input",
    )

    analyze_button = st.sidebar.button("🚀 Analyze Repository", key="analyze_repository")

    st.sidebar.markdown("---")
    st.sidebar.markdown("<h4 class='sidebar-section-header'>Filters</h4>", unsafe_allow_html=True)
    st.sidebar.checkbox("Show closed issues", value=True)
    st.sidebar.checkbox("Show pull requests", value=True)
    st.sidebar.checkbox("Show top contributors only", value=False)

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "<div class='dashboard-sidebar-note'>Analyze any public GitHub repository and load fresh analytics.</div>",
        unsafe_allow_html=True,
    )

    return repository_url, analyze_button, selected_repo

