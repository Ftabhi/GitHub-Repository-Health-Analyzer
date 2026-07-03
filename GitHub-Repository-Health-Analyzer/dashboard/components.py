"""Reusable Streamlit components for the dashboard."""

from typing import Any

import streamlit as st

from .theme import CARD_COLOR, PRIMARY_COLOR, SECONDARY_COLOR, TEXT_COLOR, BORDER_COLOR, BORDER_RADIUS


def _kpi_icon(label: str) -> str:
    icons = {
        "Total Commits": "📈",
        "Contributors": "👥",
        "Open Issues": "🐞",
        "Repository Age": "⏳",
        "Health Score": "💚",
        "Primary Language": "🧩",
    }
    return icons.get(label, "✨")


def render_section_title(title: str, subtitle: str) -> None:
    """Render a section title with subtitle text."""
    st.markdown(
        f"""
        <div class='section-title'>
            <div>
                <h2>{title}</h2>
                <p>{subtitle}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_card(label: str, value: Any, subtitle: str, trend: str = "") -> None:
    """Render a premium KPI card with icon, title, value, subtitle, and trend."""
    icon = _kpi_icon(label)
    st.markdown(
        f"""
        <div class='kpi-card'>
            <div class='kpi-card__top'>
                <span class='kpi-card__icon'>{icon}</span>
                <span class='kpi-card__label'>{label}</span>
            </div>
            <div class='kpi-card__value'>{value}</div>
            <div class='kpi-card__bottom'>
                <span class='kpi-card__subtitle'>{subtitle}</span>
                <span class='kpi-card__trend'>{trend}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_box(label: str, value: Any, description: str) -> None:
    """Render a compact metric box with a description."""
    st.markdown(
        f"""
        <div class='metric-box'>
            <div class='metric-box__label'>{label}</div>
            <div class='metric-box__value'>{value}</div>
            <div class='metric-box__description'>{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
