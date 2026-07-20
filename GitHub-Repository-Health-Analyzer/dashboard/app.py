"""Streamlit dashboard entry point."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse
import re
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import streamlit as st

from dashboard.exports import export_to_csv, export_to_json, export_to_pdf
from dashboard.insights import generate_engineering_insights
from dashboard.layout import render_dashboard
from dashboard.sidebar import render_sidebar
from src.analytics_engine import AnalyticsEngine, AnalyticsError
from src.data_cleaner import DataCleaner, DataCleaningError
from src.data_storage import DataStorage, DataStorageError
from src.github_client import (
    GitHubClient,
    GitHubAPIError,
    GitHubNotFoundError,
    GitHubPrivateRepositoryError,
    GitHubRateLimitError,
)
from src.health_score import RepositoryHealthScore, HealthScoreError

PROCESSED_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"
REPOSITORY_SUFFIX = "_repository.csv"
COMMITS_SUFFIX = "_commits.csv"
CONTRIBUTORS_SUFFIX = "_contributors.csv"
ISSUES_SUFFIX = "_issues.csv"
LANGUAGES_SUFFIX = "_languages.csv"


from html import escape

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import streamlit as st

from dashboard.exports import export_to_csv, export_to_json, export_to_pdf
from dashboard.insights import generate_engineering_insights
from dashboard.layout import render_dashboard
from dashboard.sidebar import render_sidebar
from src.analytics_engine import AnalyticsEngine, AnalyticsError
from src.data_cleaner import DataCleaner, DataCleaningError
from src.data_storage import DataStorage, DataStorageError
from src.github_client import (
    GitHubClient,
    GitHubAPIError,
    GitHubNotFoundError,
    GitHubPrivateRepositoryError,
    GitHubRateLimitError,
)
from src.health_score import RepositoryHealthScore, HealthScoreError

PROCESSED_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"
REPOSITORY_SUFFIX = "_repository.csv"
COMMITS_SUFFIX = "_commits.csv"
CONTRIBUTORS_SUFFIX = "_contributors.csv"
ISSUES_SUFFIX = "_issues.csv"
LANGUAGES_SUFFIX = "_languages.csv"


def _configure_page() -> None:
    """Configure the Streamlit page metadata."""
    st.set_page_config(
        page_title="Repository Health Dashboard",
        page_icon="📊",
        layout="wide",
    )
    st.markdown(
        """
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&display=swap');
        
        <style>
        html, body, .stApp {
            background-color: #0D1117; 
            color: #F0F6FC; 
            font-family: 'Inter', system-ui, sans-serif;
        }
        h1, h2, h3, h4, h5, h6, .dashboard-title, .sidebar-title {
            font-family: 'Outfit', system-ui, sans-serif;
            font-weight: 700;
        }
        .block-container {
            padding: 24px 32px 36px; 
            max-width: 1600px;
        }
        
        /* Sidebar Styling */
        .stSidebar {
            background-color: #161B22; 
            color: #F0F6FC; 
            padding: 24px 18px;
            border-right: 1px solid #30363D;
        }
        .stSidebar .css-1d391kg, .stSidebar .css-1rs6os.edgvbvh3 {
            background: transparent;
        }
        .sidebar-title {
            color: #F0F6FC;
            font-size: 1.5rem;
            margin: 0 0 6px;
            letter-spacing: -0.02em;
        }
        .sidebar-section-header {
            margin: 18px 0 8px; 
            color: #F0F6FC;
            font-size: 0.98rem;
            font-weight: 600;
            letter-spacing: -0.01em;
        }
        .dashboard-sidebar-note {
            color: #8B949E; 
            font-size: 0.88rem; 
            line-height: 1.5;
        }
        
        /* Premium Buttons */
        .stButton>button, .stDownloadButton>button {
            background-color: #21262D; 
            color: #58A6FF; 
            border: 1px solid #30363D; 
            box-shadow: none; 
            border-radius: 8px; 
            padding: 10px 16px; 
            font-weight: 600;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            width: 100%;
        }
        .stButton>button:hover, .stDownloadButton>button:hover {
            background-color: #30363D;
            border-color: #8B949E;
            color: #C9D1D9;
            transform: translateY(-1px);
        }
        .stButton>button:active, .stDownloadButton>button:active {
            background-color: #21262D;
            transform: translateY(0);
        }
        
        /* Analysis Progress (CI/CD Timeline) */
        .progress-container {
            background: #0D1117;
            border: 1px solid #30363D;
            border-radius: 10px;
            padding: 12px;
            margin-top: 14px;
        }
        .stage-row {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 6px 0;
            border-bottom: 1px solid rgba(48, 54, 61, 0.4);
        }
        .stage-row:last-child {
            border-bottom: none;
        }
        .stage-name {
            font-size: 0.84rem;
            color: #8B949E;
            font-weight: 500;
        }
        .stage-row--running .stage-name {
            color: #58A6FF;
            font-weight: 600;
        }
        .stage-row--success .stage-name {
            color: #C9D1D9;
        }
        .stage-row--failed .stage-name {
            color: #F85149;
            font-weight: 600;
        }
        .stage-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            font-size: 0.72rem;
            font-weight: bold;
        }
        .stage-badge--pending {
            background: rgba(139, 148, 158, 0.1);
            color: #8B949E;
            border: 1px solid rgba(139, 148, 158, 0.2);
        }
        .stage-badge--running {
            background: rgba(88, 166, 255, 0.15);
            color: #58A6FF;
            border: 1px solid rgba(88, 166, 255, 0.3);
            animation: pulse 1.6s infinite ease-in-out;
        }
        .stage-badge--success {
            background: rgba(46, 160, 67, 0.15);
            color: #3FB950;
            border: 1px solid rgba(46, 160, 67, 0.3);
        }
        .stage-badge--failed {
            background: rgba(248, 81, 73, 0.15);
            color: #F85149;
            border: 1px solid rgba(248, 81, 73, 0.3);
        }
        @keyframes pulse {
            0% { transform: scale(1); opacity: 0.8; }
            50% { transform: scale(1.06); opacity: 1; }
            100% { transform: scale(1); opacity: 0.8; }
        }
        
        /* Dashboard Layout & Section Titles */
        .dashboard-header {
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            gap: 24px; 
            margin-bottom: 28px;
            padding-bottom: 18px;
            border-bottom: 1px solid #30363D;
        }
        .dashboard-title {
            margin: 0; 
            font-size: 2.4rem;
            letter-spacing: -0.02em;
            color: #F0F6FC;
        }
        .dashboard-eyebrow {
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #58A6FF;
            font-weight: 700;
            margin-bottom: 6px;
            display: block;
        }
        .dashboard-subtitle {
            margin: 8px 0 0; 
            color: #8B949E; 
            font-size: 0.98rem;
        }
        .dashboard-badge {
            background: #161B22; 
            border: 1px solid #30363D; 
            border-radius: 20px; 
            padding: 8px 18px; 
            color: #58A6FF; 
            font-weight: 600;
            font-size: 0.88rem;
        }
        
        .section-title {
            margin: 28px 0 16px;
            padding-bottom: 8px;
            border-bottom: 1px solid rgba(48, 54, 61, 0.5);
        }
        .section-title h2 {
            margin: 0; 
            color: #F0F6FC; 
            font-size: 1.55rem;
            letter-spacing: -0.01em;
        }
        .section-title p {
            margin: 6px 0 0; 
            color: #8B949E; 
            font-size: 0.92rem;
        }
        
        /* KPI Cards */
        .kpi-card {
            background: #161B22; 
            border: 1px solid #30363D; 
            border-radius: 12px; 
            padding: 20px; 
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15); 
            color: #F0F6FC; 
            margin-bottom: 16px; 
            min-height: 140px; 
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .kpi-card:hover {
            background: #1C2128; 
            border-color: #58A6FF; 
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
        }
        .kpi-card__top {
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            gap: 12px; 
            margin-bottom: 12px;
        }
        .kpi-card__icon {
            align-items: center; 
            background: rgba(88, 166, 255, 0.08); 
            border: 1px solid rgba(88, 166, 255, 0.15); 
            border-radius: 8px; 
            color: #58A6FF; 
            display: inline-flex; 
            font-size: 18px; 
            height: 32px; 
            width: 32px;
            justify-content: center; 
        }
        .kpi-card__label {
            font-size: 0.78rem; 
            color: #8B949E; 
            font-weight: 600;
            letter-spacing: 0.06em; 
            text-transform: uppercase;
        }
        .kpi-card__value {
            font-size: 2.1rem; 
            font-weight: 700; 
            margin-bottom: 8px; 
            line-height: 1.1; 
            overflow-wrap: anywhere;
            letter-spacing: -0.02em;
        }
        .kpi-card__subtitle {
            font-size: 0.88rem; 
            color: #8B949E;
        }
        .kpi-card__trend {
            font-size: 0.84rem; 
            color: #58A6FF;
            font-weight: 500;
        }
        
        /* Summary Grid */
        .summary-grid {
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); 
            gap: 16px; 
            margin-bottom: 24px;
        }
        .summary-card {
            background: #161B22; 
            border: 1px solid #30363D; 
            border-radius: 12px; 
            padding: 18px; 
            color: #F0F6FC; 
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1); 
            min-height: 100px; 
            transition: background 0.2s ease;
        }
        .summary-card:hover {
            background: #1C2128;
        }
        .summary-card h3 {
            margin: 0 0 8px; 
            color: #FFFFFF; 
            font-size: 0.95rem;
            font-weight: 600;
        }
        .summary-card p {
            margin: 0; 
            color: #8B949E; 
            font-size: 0.92rem;
            line-height: 1.4;
        }
        
        .dashboard-footer {
            padding: 32px 0 16px; 
            color: #8B949E; 
            font-size: 0.88rem; 
            text-align: center;
            border-top: 1px solid #30363D;
            margin-top: 40px;
        }
        
        /* Metric Box */
        .metric-box {
            background: #161B22; 
            border: 1px solid #30363D; 
            border-radius: 12px; 
            padding: 16px; 
            margin-bottom: 12px; 
            transition: all 0.2s ease; 
            min-height: 100px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        }
        .metric-box:hover {
            background: #1C2128;
            border-color: #58A6FF;
        }
        .metric-box__label {
            font-size: 0.78rem; 
            color: #8B949E; 
            text-transform: uppercase; 
            font-weight: 600;
            margin-bottom: 8px;
            letter-spacing: 0.04em;
        }
        .metric-box__value {
            font-size: 1.55rem; 
            font-weight: 700; 
            margin-bottom: 6px; 
            color: #F0F6FC;
            letter-spacing: -0.01em;
        }
        .metric-box__description {
            font-size: 0.88rem; 
            color: #8B949E;
            line-height: 1.35;
        }
        
        /* Repository Overview */
        .repository-overview {
            background: #161B22; 
            border: 1px solid #30363D; 
            border-radius: 14px; 
            padding: 20px; 
            margin-bottom: 24px;
        }
        .overview-grid {
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); 
            gap: 12px; 
            margin-top: 14px;
        }
        .overview-item {
            background: #0D1117; 
            border: 1px solid #30363D; 
            border-radius: 10px; 
            padding: 12px 14px; 
            min-height: 76px;
            transition: border-color 0.2s ease;
        }
        .overview-item:hover {
            border-color: #58A6FF;
        }
        .overview-item__label {
            display: block; 
            color: #8B949E; 
            font-size: 0.74rem; 
            font-weight: 600; 
            letter-spacing: 0.06em; 
            text-transform: uppercase; 
            margin-bottom: 6px;
        }
        .overview-item__value {
            display: block; 
            color: #F0F6FC; 
            font-size: 0.94rem; 
            line-height: 1.35; 
            overflow-wrap: anywhere;
        }
        .overview-item__value a {
            color: #58A6FF; 
            text-decoration: none;
            font-weight: 500;
        }
        .overview-item__value a:hover {
            text-decoration: underline;
        }
        
        /* Repository Intelligence */
        .repository-intelligence {
            background: #161B22; 
            border: 1px solid #30363D; 
            border-radius: 14px; 
            padding: 20px; 
            margin-bottom: 24px;
        }
        .intelligence-hero {
            align-items: flex-start; 
            display: flex; 
            justify-content: space-between; 
            gap: 16px; 
            margin-bottom: 18px;
        }
        .intelligence-eyebrow {
            color: #8B949E; 
            display: block; 
            font-size: 0.76rem; 
            font-weight: 600; 
            letter-spacing: 0.06em; 
            margin-bottom: 6px; 
            text-transform: uppercase;
        }
        .intelligence-score {
            color: #F0F6FC; 
            font-size: 3.6rem; 
            font-weight: 800; 
            line-height: 0.9;
            letter-spacing: -0.03em;
        }
        .intelligence-hero p {
            color: #8B949E; 
            font-size: 0.94rem; 
            margin: 10px 0 0;
        }
        .intelligence-grade {
            align-items: center; 
            background: rgba(88, 166, 255, 0.08); 
            border: 1px solid rgba(88, 166, 255, 0.25); 
            border-radius: 12px; 
            color: #58A6FF; 
            display: flex; 
            font-size: 2.2rem; 
            font-weight: 800; 
            justify-content: center; 
            min-height: 74px; 
            min-width: 86px; 
            padding: 8px 14px;
        }
        .intelligence-grid {
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); 
            gap: 12px; 
            margin-bottom: 16px;
        }
        .intelligence-score-card {
            background: #0D1117; 
            border: 1px solid #30363D; 
            border-radius: 10px; 
            min-height: 120px; 
            padding: 14px;
            transition: border-color 0.2s ease;
        }
        .intelligence-score-card:hover {
            border-color: #58A6FF;
        }
        .intelligence-score-card span {
            color: #8B949E; 
            display: block; 
            font-size: 0.74rem; 
            font-weight: 600; 
            letter-spacing: 0.06em; 
            margin-bottom: 8px; 
            text-transform: uppercase;
        }
        .intelligence-score-card strong {
            color: #F0F6FC; 
            display: block; 
            font-size: 1.85rem; 
            line-height: 1; 
            margin-bottom: 8px;
            font-weight: 700;
        }
        .intelligence-score-card small {
            color: #8B949E; 
            display: block; 
            font-size: 0.84rem; 
            line-height: 1.35;
        }
        .intelligence-explanation {
            border-top: 1px solid #30363D; 
            color: #C9D1D9; 
            font-size: 0.94rem; 
            line-height: 1.55; 
            margin: 0; 
            padding-top: 14px;
        }
        
        /* Engineering Insights & Recommendations Cards */
        .engineering-insights-section, .engineering-recommendations-section {
            margin-bottom: 24px;
        }
        .engineering-insights-grid, .engineering-actions-grid {
            display: grid; 
            gap: 14px; 
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        }
        .engineering-card {
            background: #161B22; 
            border: 1px solid #30363D; 
            border-left: 4px solid #58A6FF; 
            border-radius: 12px; 
            color: #F0F6FC; 
            min-height: 150px; 
            padding: 16px; 
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .engineering-card:hover {
            background: #1C2128; 
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
            border-color: #8B949E;
        }
        .engineering-card__top {
            align-items: center; 
            display: flex; 
            justify-content: space-between; 
            gap: 10px; 
            margin-bottom: 12px;
        }
        .engineering-card__icon {
            align-items: center; 
            background: rgba(88, 166, 255, 0.08); 
            border: 1px solid rgba(88, 166, 255, 0.18); 
            border-radius: 8px; 
            color: #58A6FF; 
            display: inline-flex; 
            font-size: 0.95rem; 
            height: 30px; 
            width: 30px;
            justify-content: center; 
        }
        .engineering-card__severity {
            border: 1px solid #30363D; 
            border-radius: 20px; 
            color: #C9D1D9; 
            font-size: 0.7rem; 
            font-weight: 600; 
            letter-spacing: 0.06em; 
            padding: 4px 8px; 
            text-transform: uppercase;
        }
        .engineering-card h3 {
            color: #FFFFFF; 
            font-size: 0.98rem; 
            line-height: 1.3; 
            margin: 0 0 8px;
            font-weight: 600;
        }
        .engineering-card p {
            color: #8B949E; 
            font-size: 0.88rem; 
            line-height: 1.45; 
            margin: 0;
        }
        .engineering-card--good {
            border-left-color: #3FB950;
        }
        .engineering-card--good .engineering-card__icon {
            background: rgba(63, 185, 80, 0.08); 
            border-color: rgba(63, 185, 80, 0.18); 
            color: #3FB950;
        }
        .engineering-card--warning {
            border-left-color: #D29922;
        }
        .engineering-card--warning .engineering-card__icon {
            background: rgba(210, 153, 34, 0.08); 
            border-color: rgba(210, 153, 34, 0.2); 
            color: #D29922;
        }
        .engineering-card--critical {
            border-left-color: #F85149;
        }
        .engineering-card--critical .engineering-card__icon {
            background: rgba(248, 81, 73, 0.08); 
            border-color: rgba(248, 81, 73, 0.2); 
            color: #F85149;
        }
        
        /* Welcome Panel empty state */
        .welcome-panel {
            background: #161B22;
            border: 1px solid #30363D;
            border-radius: 14px;
            padding: 40px;
            color: #F0F6FC;
            max-width: 800px;
            margin: 40px auto;
            text-align: center;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.25);
        }
        .welcome-icon {
            font-size: 3.5rem;
            margin-bottom: 16px;
        }
        .welcome-panel h2 {
            font-size: 1.85rem;
            font-weight: 700;
            margin-bottom: 10px;
            color: #F0F6FC;
            letter-spacing: -0.02em;
        }
        .welcome-subtitle {
            font-size: 1rem;
            color: #8B949E;
            margin-bottom: 28px;
            line-height: 1.5;
        }
        .welcome-features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
            text-align: left;
        }
        .feature-item {
            background: #0D1117;
            border: 1px solid #30363D;
            border-radius: 10px;
            padding: 16px;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .feature-item:hover {
            transform: translateY(-2px);
            border-color: #58A6FF;
        }
        .feature-icon {
            font-size: 1.4rem;
            display: block;
            margin-bottom: 10px;
        }
        .feature-item strong {
            display: block;
            color: #F0F6FC;
            font-size: 0.95rem;
            margin-bottom: 4px;
        }
        .feature-item span {
            color: #8B949E;
            font-size: 0.84rem;
            line-height: 1.45;
        }
        .welcome-instruction {
            background: rgba(88, 166, 255, 0.08);
            border: 1px solid rgba(88, 166, 255, 0.2);
            border-radius: 10px;
            padding: 14px 18px;
            font-size: 0.92rem;
            color: #58A6FF;
            display: inline-block;
            max-width: 100%;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data
def _discover_repositories() -> List[str]:
    """Discover repository options from processed repository CSV files."""
    if not PROCESSED_DIR.exists():
        return []

    repositories: List[str] = []
    for path in sorted(PROCESSED_DIR.glob(f"*{REPOSITORY_SUFFIX}")):
        try:
            df = pd.read_csv(path, nrows=1)
            full_name = df.loc[0, "full_name"] if "full_name" in df.columns else None
            if isinstance(full_name, str) and full_name:
                repositories.append(full_name)
        except (ValueError, FileNotFoundError, KeyError):
            continue
    return repositories


def _parse_github_repository_url(repository_url: str) -> Tuple[str, str]:
    """Validate a GitHub repository URL and return owner/repo."""
    if not repository_url or not repository_url.strip():
        raise ValueError("Repository URL must not be empty.")

    normalized_url = repository_url.strip()
    if not re.match(r"^https?://", normalized_url, re.IGNORECASE):
        normalized_url = f"https://{normalized_url}"

    parsed = urlparse(normalized_url)
    if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        raise ValueError("Please enter a valid GitHub repository URL.")

    path_parts = [part for part in parsed.path.split("/") if part]
    if len(path_parts) < 2:
        raise ValueError("GitHub URL must include owner and repository name.")

    owner = path_parts[0].strip()
    repo = path_parts[1].strip().removesuffix(".git")
    if not owner or not repo:
        raise ValueError("GitHub URL must include owner and repository name.")

    return owner, repo


def _format_repository_file_prefix(repository: str) -> str:
    return repository.replace("/", "_")


def _load_dataframe(file_name: str, parse_dates: Optional[List[str]] = None) -> pd.DataFrame:
    """Load a processed CSV file into a DataFrame."""
    file_path = PROCESSED_DIR / file_name
    if not file_path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(file_path, parse_dates=parse_dates or [])
    except (ValueError, FileNotFoundError):
        return pd.DataFrame()


def _file_timestamps(repository: str) -> Tuple[float, ...]:
    """Return modification timestamps for repository-related processed files."""
    prefix = _format_repository_file_prefix(repository)
    files = [
        PROCESSED_DIR / f"{prefix}{suffix}"
        for suffix in (
            REPOSITORY_SUFFIX,
            COMMITS_SUFFIX,
            CONTRIBUTORS_SUFFIX,
            ISSUES_SUFFIX,
            LANGUAGES_SUFFIX,
        )
    ]
    return tuple(path.stat().st_mtime if path.exists() else 0.0 for path in files)


def _render_stage_progress(
    stage_container: st.delta_generator.DeltaGenerator,
    stage_statuses: Dict[str, str],
) -> None:
    """Render progress indicator for each stage in the sidebar."""
    html_lines = []
    for stage, status in stage_statuses.items():
        if status == "pending":
            badge_class = "stage-badge--pending"
            badge_text = "⏳"
        elif status == "running":
            badge_class = "stage-badge--running"
            badge_text = "🔄"
        elif status == "success":
            badge_class = "stage-badge--success"
            badge_text = "✓"
        else:
            badge_class = "stage-badge--failed"
            badge_text = "✗"
        
        html_lines.append(
            f"<div class='stage-row stage-row--{status}'>"
            f"<span class='stage-badge {badge_class}'>{badge_text}</span>"
            f"<span class='stage-name'>{escape(stage)}</span>"
            f"</div>"
        )
        
    container_html = f"<div class='progress-container'>{''.join(html_lines)}</div>"
    stage_container.markdown(container_html, unsafe_allow_html=True)


def _update_stage_status(
    stage_statuses: Dict[str, str],
    current_stage: str,
    status: str,
) -> None:
    stage_statuses[current_stage] = status


def _build_stage_statuses() -> Dict[str, str]:
    """Create the ordered stage status map for the analysis workflow."""
    return {
        "Validating repository": "pending",
        "Fetching repository metadata": "pending",
        "Fetching commits": "pending",
        "Fetching contributors": "pending",
        "Fetching issues": "pending",
        "Fetching languages": "pending",
        "Saving raw data": "pending",
        "Cleaning data": "pending",
        "Running analytics": "pending",
        "Calculating repository health": "pending",
        "Updating dashboard": "pending",
    }


def _reset_stage_statuses(stage_container: st.delta_generator.DeltaGenerator, stage: str, status: str) -> None:
    """Reset the sidebar progress states to reflect an error condition."""
    stage_statuses = _build_stage_statuses()
    stage_statuses[stage] = status
    _render_stage_progress(stage_container, stage_statuses)


def _fetch_github_data(
    owner: str,
    repo: str,
    advance: Optional[Any] = None,
) -> Tuple[Any, Any, Any, Any, Any]:
    """Fetch repository data from the GitHub client using the existing modules."""
    client = GitHubClient()

    if advance is not None:
        advance("Fetching repository metadata", "running")
    repository = client.get_repository(owner, repo)
    if advance is not None:
        advance("Fetching repository metadata", "success")

    if advance is not None:
        advance("Fetching commits", "running")
    commits = client.get_commits(owner, repo)
    if advance is not None:
        advance("Fetching commits", "success")

    if advance is not None:
        advance("Fetching contributors", "running")
    contributors = client.get_contributors(owner, repo)
    if advance is not None:
        advance("Fetching contributors", "success")

    if advance is not None:
        advance("Fetching issues", "running")
    issues = client.get_issues(owner, repo)
    if advance is not None:
        advance("Fetching issues", "success")

    if advance is not None:
        advance("Fetching languages", "running")
    languages = client.get_languages(owner, repo)
    if advance is not None:
        advance("Fetching languages", "success")

    return repository, commits, contributors, issues, languages


def _save_raw_data(
    owner: str,
    repo: str,
    repository: Any,
    commits: Any,
    contributors: Any,
    issues: Any,
    languages: Any,
) -> None:
    storage = DataStorage()
    storage.save_repository(owner, repo, repository)
    storage.save_commits(owner, repo, commits)
    storage.save_contributors(owner, repo, contributors)
    storage.save_issues(owner, repo, issues)
    storage.save_languages(owner, repo, languages)


def _clean_repository_data(owner: str, repo: str) -> None:
    cleaner = DataCleaner()
    cleaner.save_cleaned_repository(owner, repo)
    cleaner.save_cleaned_commits(owner, repo)
    cleaner.save_cleaned_contributors(owner, repo)
    cleaner.save_cleaned_issues(owner, repo)
    cleaner.save_cleaned_languages(owner, repo)


def _load_repository_data(repository: str, timestamps: Tuple[float, ...] = ()) -> Dict[str, pd.DataFrame]:
    """Load processed DataFrames for the selected repository."""
    prefix = _format_repository_file_prefix(repository)
    return {
        "repository_df": _load_dataframe(f"{prefix}{REPOSITORY_SUFFIX}", parse_dates=["created_at", "updated_at", "pushed_at"]),
        "commits_df": _load_dataframe(f"{prefix}{COMMITS_SUFFIX}", parse_dates=["commit_author_date", "commit_committer_date"]),
        "contributors_df": _load_dataframe(f"{prefix}{CONTRIBUTORS_SUFFIX}"),
        "issues_df": _load_dataframe(f"{prefix}{ISSUES_SUFFIX}", parse_dates=["created_at", "updated_at", "closed_at"]),
        "languages_df": _load_dataframe(f"{prefix}{LANGUAGES_SUFFIX}"),
    }


def _build_metrics(data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """Build dashboard KPI metrics from analytics engine outputs."""
    engine = AnalyticsEngine(
        repository_df=data["repository_df"],
        commits_df=data["commits_df"],
        contributors_df=data["contributors_df"],
        issues_df=data["issues_df"],
        languages_df=data["languages_df"],
    )

    metrics: Dict[str, Any] = {
        "total_commits": 0,
        "total_contributors": 0,
        "total_issues": 0,
        "open_issues": 0,
        "closed_issues": 0,
        "open_pull_requests": 0,
        "merged_pull_requests": 0,
        "issue_close_rate": 0.0,
        "average_comments": 0.0,
        "total_contributions": 0,
        "top_contributor": "Unknown",
        "top_contributor_commits": 0,
        "repository_age_days": 0,
        "stars": 0,
        "forks": 0,
        "watchers": 0,
        "health_score": 0.0,
        "health_grade": "Pending",
        "repository_health": 0.0,
        "maintenance_score": 0.0,
        "community_score": 0.0,
        "popularity_score": 0.0,
        "overall_grade": "Pending",
        "health_label": "Pending",
        "score_explanation": "Repository intelligence is unavailable until repository analytics are loaded.",
        "primary_language": "Unknown",
        "days_since_last_commit": 0,
        "recent_commits_30_days": 0,
        "previous_commits_30_days": 0,
        "commit_activity_change_pct": 0.0,
        "top_contributor_share": 0.0,
        "total_pull_requests": 0,
        "pull_request_backlog_ratio": 0.0,
        "issue_backlog_ratio": 0.0,
        "language_count": 0,
        "has_description": False,
        "has_license": False,
    }

    try:
        repo_summary = engine.repository_summary()
        metrics["repository_age_days"] = int(repo_summary.get("age_days", 0))
        metrics["primary_language"] = repo_summary.get("language") or "Unknown"
        metrics["stars"] = int(repo_summary.get("stars", 0))
        metrics["forks"] = int(repo_summary.get("forks", 0))
        metrics["watchers"] = int(repo_summary.get("watchers", 0))
    except AnalyticsError:
        pass

    repository_df = data["repository_df"]
    if not repository_df.empty:
        repo_row = repository_df.iloc[0]
        description = repo_row.get("description")
        license_value = repo_row.get("license")
        metrics["has_description"] = isinstance(description, str) and bool(description.strip())
        metrics["has_license"] = isinstance(license_value, str) and bool(license_value.strip())

    try:
        commit_stats = engine.commit_statistics()
        metrics["total_commits"] = int(commit_stats.get("total_commits", 0))
    except AnalyticsError:
        metrics["total_commits"] = 0

    commits_df = data["commits_df"]
    if not commits_df.empty and "commit_author_date" in commits_df.columns:
        commit_dates = pd.to_datetime(commits_df["commit_author_date"], errors="coerce", utc=True).dropna()
        if not commit_dates.empty:
            latest_commit = commit_dates.max()
            metrics["days_since_last_commit"] = max(
                int((pd.Timestamp.now(tz="UTC") - latest_commit).days),
                0,
            )
            recent_start = latest_commit - pd.Timedelta(days=30)
            previous_start = latest_commit - pd.Timedelta(days=60)
            recent_commits = int((commit_dates >= recent_start).sum())
            previous_commits = int(((commit_dates >= previous_start) & (commit_dates < recent_start)).sum())
            metrics["recent_commits_30_days"] = recent_commits
            metrics["previous_commits_30_days"] = previous_commits
            if previous_commits:
                metrics["commit_activity_change_pct"] = round(
                    (recent_commits - previous_commits) / previous_commits * 100,
                    2,
                )
            elif recent_commits:
                metrics["commit_activity_change_pct"] = 100.0

    try:
        contributor_stats = engine.contributor_statistics()
        metrics["total_contributors"] = int(contributor_stats.get("total_contributors", 0))
        metrics["total_contributions"] = int(contributor_stats.get("total_contributions", 0))
        top_contributor = contributor_stats.get("top_contributor", {}) or {}
        metrics["top_contributor"] = top_contributor.get("login") or "Unknown"
        metrics["top_contributor_commits"] = int(top_contributor.get("contributions", 0))
        if metrics["total_contributions"]:
            metrics["top_contributor_share"] = round(
                metrics["top_contributor_commits"] / metrics["total_contributions"] * 100,
                2,
            )
    except AnalyticsError:
        metrics["total_contributors"] = 0
        metrics["total_contributions"] = 0
        metrics["top_contributor"] = "Unknown"
        metrics["top_contributor_commits"] = 0

    try:
        issue_stats = engine.issue_statistics()
        metrics["open_issues"] = int(issue_stats.get("open_issues", 0))
        metrics["closed_issues"] = int(issue_stats.get("closed_issues", 0))
        metrics["total_issues"] = int(issue_stats.get("total_issues", 0))
        metrics["issue_close_rate"] = float(issue_stats.get("issue_close_rate", 0.0))
        metrics["average_comments"] = float(issue_stats.get("average_comments", 0.0))
        if metrics["total_issues"]:
            metrics["issue_backlog_ratio"] = round(
                metrics["open_issues"] / metrics["total_issues"] * 100,
                2,
            )
    except AnalyticsError:
        metrics["open_issues"] = 0
        metrics["closed_issues"] = 0
        metrics["total_issues"] = 0
        metrics["issue_close_rate"] = 0.0
        metrics["average_comments"] = 0.0

    try:
        pull_request_stats = engine.pull_request_statistics()
        metrics["total_pull_requests"] = int(pull_request_stats.get("total_pull_requests", 0))
        metrics["open_pull_requests"] = int(pull_request_stats.get("open_pull_requests", 0))
        metrics["merged_pull_requests"] = int(pull_request_stats.get("merged_pull_requests", 0))
        if metrics["total_pull_requests"]:
            metrics["pull_request_backlog_ratio"] = round(
                metrics["open_pull_requests"] / metrics["total_pull_requests"] * 100,
                2,
            )
    except AnalyticsError:
        metrics["total_pull_requests"] = 0
        metrics["open_pull_requests"] = 0
        metrics["merged_pull_requests"] = 0

    languages_df = data["languages_df"]
    if not languages_df.empty and "language" in languages_df.columns:
        metrics["language_count"] = int(languages_df["language"].nunique(dropna=True))

    try:
        health_score = RepositoryHealthScore(engine).calculate_health_score()
        metrics["health_score"] = round(float(health_score.get("score", 0.0)), 2)
        metrics["health_grade"] = health_score.get("grade", "Pending")
        metrics["repository_health"] = round(float(health_score.get("repository_health", 0.0)), 2)
        metrics["maintenance_score"] = round(float(health_score.get("maintenance_score", 0.0)), 2)
        metrics["community_score"] = round(float(health_score.get("community_score", 0.0)), 2)
        metrics["popularity_score"] = round(float(health_score.get("popularity_score", 0.0)), 2)
        metrics["overall_grade"] = health_score.get("overall_grade", metrics["health_grade"])
        metrics["health_label"] = health_score.get("health_label", "Pending")
        metrics["score_explanation"] = health_score.get("summary", metrics["score_explanation"])
    except (HealthScoreError, AnalyticsError):
        metrics["health_score"] = 0.0
        metrics["health_grade"] = "Pending"
        metrics["overall_grade"] = "Pending"

    return metrics


def _get_repository_value(row: pd.Series, key: str, default: Any = "Not available") -> Any:
    """Return a display-safe repository metadata value from a repository row."""
    value = row.get(key, default)
    if pd.isna(value):
        return default
    return value


def _format_count(value: Any) -> str:
    if pd.isna(value):
        return "Not available"
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return str(value)


def _format_date(value: Any) -> str:
    timestamp = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(timestamp):
        return "Not available"
    return timestamp.strftime("%Y-%m-%d %H:%M UTC")


def _repository_age_days(value: Any) -> str:
    created_at = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(created_at):
        return "Not available"
    return f"{max((pd.Timestamp.now(tz='UTC') - created_at).days, 0):,} days"


def _format_repository_size(value: Any) -> str:
    if pd.isna(value):
        return "Not available"
    try:
        size_kb = int(value)
    except (TypeError, ValueError):
        return str(value)
    if size_kb >= 1024:
        return f"{size_kb / 1024:.1f} MB"
    return f"{size_kb:,} KB"


def _build_repository_overview(repository_df: pd.DataFrame) -> Dict[str, str]:
    """Build the Repository Overview section from live GitHub repository metadata."""
    if repository_df.empty:
        return {}

    row = repository_df.iloc[0]
    return {
        "Repository Name": str(_get_repository_value(row, "repository_name")),
        "Owner": str(_get_repository_value(row, "owner_login")),
        "Description": str(_get_repository_value(row, "description", "No description provided")),
        "Repository URL": str(_get_repository_value(row, "repository_url")),
        "Primary Language": str(_get_repository_value(row, "language")),
        "Stars": _format_count(_get_repository_value(row, "stars")),
        "Forks": _format_count(_get_repository_value(row, "forks")),
        "Watchers": _format_count(_get_repository_value(row, "watchers")),
        "Open Issues": _format_count(_get_repository_value(row, "open_issues")),
        "License": str(_get_repository_value(row, "license", "No license detected")),
        "Default Branch": str(_get_repository_value(row, "default_branch")),
        "Repository Age": _repository_age_days(_get_repository_value(row, "created_at")),
        "Created Date": _format_date(_get_repository_value(row, "created_at")),
        "Last Updated": _format_date(_get_repository_value(row, "updated_at")),
        "Last Push Date": _format_date(_get_repository_value(row, "pushed_at")),
        "Repository Visibility": str(_get_repository_value(row, "visibility")).title(),
        "Repository Size": _format_repository_size(_get_repository_value(row, "size")),
    }


def _build_health_history(commits_df: pd.DataFrame, current_score: Any) -> pd.DataFrame:
    """Build a lightweight health score trend from weekly commit activity."""
    if commits_df.empty or "commit_author_date" not in commits_df.columns:
        return pd.DataFrame()

    df = commits_df.copy()
    df["commit_author_date"] = pd.to_datetime(df["commit_author_date"], errors="coerce", utc=True).dt.tz_convert(None)
    df = df.dropna(subset=["commit_author_date"])
    if df.empty:
        return pd.DataFrame()

    df["week_label"] = df["commit_author_date"].dt.to_period("W").apply(lambda value: value.start_time.strftime("%Y-%m-%d"))
    weekly = df.groupby("week_label")["commit_author_date"].size().reset_index(name="commits").sort_values("week_label")
    max_commits = weekly["commits"].max() if not weekly.empty else 0
    normalized_score = float(current_score) if isinstance(current_score, (int, float)) else 0.0
    weekly["health_score"] = weekly["commits"].apply(
        lambda commits: round((commits / max_commits) * normalized_score if max_commits else 0.0, 2)
    )
    weekly["date"] = pd.to_datetime(weekly["week_label"], errors="coerce").dt.strftime("%Y-%m-%d")
    return weekly[["date", "health_score"]]


def _build_issue_timeline(issues_df: pd.DataFrame) -> pd.DataFrame:
    """Build daily opened and closed issue counts for the issue timeline."""
    if issues_df.empty:
        return pd.DataFrame({"date": [], "opened": [], "closed": []})

    frames: List[pd.DataFrame] = []
    if "created_at" in issues_df.columns:
        opened = issues_df.copy()
        opened["date"] = pd.to_datetime(opened["created_at"], errors="coerce").dt.normalize()
        opened = opened.dropna(subset=["date"])
        if not opened.empty:
            frames.append(opened.groupby("date").size().reset_index(name="opened"))

    if "closed_at" in issues_df.columns:
        closed = issues_df.copy()
        closed["date"] = pd.to_datetime(closed["closed_at"], errors="coerce").dt.normalize()
        closed = closed.dropna(subset=["date"])
        if not closed.empty:
            frames.append(closed.groupby("date").size().reset_index(name="closed"))

    if not frames:
        return pd.DataFrame({"date": [], "opened": [], "closed": []})

    timeline = frames[0]
    for frame in frames[1:]:
        timeline = timeline.merge(frame, on="date", how="outer")
    for column in ("opened", "closed"):
        if column not in timeline.columns:
            timeline[column] = 0
        timeline[column] = timeline[column].fillna(0).astype(int)

    timeline = timeline.sort_values("date")
    timeline["date"] = timeline["date"].dt.strftime("%Y-%m-%d")
    return timeline[["date", "opened", "closed"]]


def _build_chart_data(data: Dict[str, pd.DataFrame], metrics: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
    """Build chart data frames for the dashboard charts."""
    commits_df = data["commits_df"].copy()
    chart_data: Dict[str, pd.DataFrame] = {}

    if not commits_df.empty and "commit_author_date" in commits_df.columns:
        commits_df["date"] = pd.to_datetime(commits_df["commit_author_date"], errors="coerce").dt.strftime("%Y-%m-%d")
        commits_summary = (
            commits_df.groupby("date")
            .size()
            .reset_index(name="commits")
            .sort_values("date")
        )
        chart_data["commits"] = commits_summary
    else:
        chart_data["commits"] = pd.DataFrame({"date": [], "commits": []})

    contributors_df = data["contributors_df"].copy()
    if not contributors_df.empty and "login" in contributors_df.columns and "contributions" in contributors_df.columns:
        chart_data["contributors"] = (
            contributors_df.sort_values("contributions", ascending=False)
            .head(10)
            [["login", "contributions"]]
            .rename(columns={"login": "contributor"})
        )
    else:
        chart_data["contributors"] = pd.DataFrame({"contributor": [], "contributions": []})

    issues_df = data["issues_df"].copy()
    if not issues_df.empty and "state" in issues_df.columns:
        chart_data["issues"] = (
            issues_df["state"].fillna("Unknown")
            .str.title()
            .value_counts()
            .reset_index(name="count")
            .rename(columns={"index": "state"})
        )
    else:
        chart_data["issues"] = pd.DataFrame({"state": [], "count": []})
    chart_data["issue_timeline"] = _build_issue_timeline(issues_df)

    languages_df = data["languages_df"].copy()
    if not languages_df.empty and "language" in languages_df.columns and "bytes" in languages_df.columns:
        chart_data["languages"] = languages_df.sort_values("bytes", ascending=False)
    else:
        chart_data["languages"] = pd.DataFrame({"language": [], "bytes": []})

    chart_data["raw_commits"] = commits_df
    chart_data["raw_contributors"] = contributors_df
    chart_data["raw_issues"] = issues_df
    chart_data["health_history"] = _build_health_history(commits_df, metrics.get("health_score", 0))

    return chart_data


def _render_export_controls(metrics: Dict[str, Any], chart_data: Dict[str, pd.DataFrame]) -> None:
    """Render export buttons in the sidebar for analytics assets."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Export Analytics")

    csv_bytes = export_to_csv(metrics, chart_data)
    json_bytes = export_to_json(metrics, chart_data)
    try:
        pdf_bytes = export_to_pdf(metrics, chart_data, "repository_analytics.pdf")
    except ImportError:
        pdf_bytes = None

    st.sidebar.download_button(
        label="Download CSV",
        data=csv_bytes,
        file_name="repository_analytics.csv",
        mime="text/csv",
    )
    st.sidebar.download_button(
        label="Download JSON",
        data=json_bytes,
        file_name="repository_analytics.json",
        mime="application/json",
    )

    if pdf_bytes is not None:
        st.sidebar.download_button(
            label="Download PDF",
            data=pdf_bytes,
            file_name="repository_analytics.pdf",
            mime="application/pdf",
        )
    else:
        st.sidebar.info("Install reportlab to enable PDF export.")


def _load_processed_data(repository: str) -> Tuple[Dict[str, pd.DataFrame], Dict[str, Any]]:
    timeline = _file_timestamps(repository)
    repository_data = _load_repository_data(repository, timeline)
    metrics = _build_metrics(repository_data)
    return repository_data, metrics


def _render_dashboard_for_repository(repository: str) -> None:
    repository_data, metrics = _load_processed_data(repository)
    repository_overview = _build_repository_overview(repository_data["repository_df"])
    chart_data = _build_chart_data(repository_data, metrics)
    dashboard_insights = generate_engineering_insights(metrics)
    _render_export_controls(metrics, chart_data)
    render_dashboard(metrics, chart_data, dashboard_insights, repository_overview)


def _analyze_repository(repository_url: str, stage_container: st.delta_generator.DeltaGenerator) -> str:
    stage_statuses = _build_stage_statuses()

    def advance(stage: str, status: str) -> None:
        _update_stage_status(stage_statuses, stage, status)
        _render_stage_progress(stage_container, stage_statuses)

    advance("Validating repository", "running")
    owner, repo = _parse_github_repository_url(repository_url)
    advance("Validating repository", "success")

    advance("Fetching repository metadata", "running")
    repository, commits, contributors, issues, languages = _fetch_github_data(owner, repo, advance)
    advance("Fetching repository metadata", "success")

    advance("Saving raw data", "running")
    _save_raw_data(owner, repo, repository, commits, contributors, issues, languages)
    advance("Saving raw data", "success")

    advance("Cleaning data", "running")
    _clean_repository_data(owner, repo)
    advance("Cleaning data", "success")

    advance("Running analytics", "running")
    repository_data = _load_repository_data(f"{owner}/{repo}", _file_timestamps(f"{owner}/{repo}"))
    _build_metrics(repository_data)
    advance("Running analytics", "success")

    advance("Calculating repository health", "running")
    try:
        engine = AnalyticsEngine(
            repository_df=repository_data["repository_df"],
            commits_df=repository_data["commits_df"],
            contributors_df=repository_data["contributors_df"],
            issues_df=repository_data["issues_df"],
            languages_df=repository_data["languages_df"],
        )
        RepositoryHealthScore(engine).calculate_health_score()
    except (HealthScoreError, AnalyticsError) as exc:
        import logging as _logging
        _logging.getLogger(__name__).warning(
            "_analyze_repository: health score calculation failed for %s/%s: %s",
            owner, repo, exc,
        )
    advance("Calculating repository health", "success")

    advance("Updating dashboard", "running")
    advance("Updating dashboard", "success")

    return f"{owner}/{repo}"


def main() -> None:
    """Dashboard entry point for Streamlit."""
    _configure_page()

    discovered_repos = _discover_repositories()
    repository_url, analyze_button, selected_repo = render_sidebar(discovered_repos)
    stage_container = st.sidebar.container()
    
    # Sync selectbox change to session state and trigger rerun
    if selected_repo != st.session_state.get("selected_repository", ""):
        st.session_state["selected_repository"] = selected_repo
        st.rerun()

    selected_repository = st.session_state.get("selected_repository", "")

    if analyze_button:
        try:
            selected_repository = _analyze_repository(repository_url, stage_container)
            st.session_state["selected_repository"] = selected_repository
            st.session_state["sidebar_repo_selectbox"] = selected_repository
            if "repository_url_input" in st.session_state:
                st.session_state["repository_url_input"] = ""
            st.cache_data.clear()  # clear cache so discovered repositories updates
            st.success(f"Analysis complete for {selected_repository}.")
            st.rerun()
        except ValueError as exc:
            _reset_stage_statuses(stage_container, "Validating repository", "failed")
            st.error(str(exc))
            selected_repository = ""
            st.session_state["selected_repository"] = ""
            st.session_state["sidebar_repo_selectbox"] = ""
        except GitHubNotFoundError:
            _reset_stage_statuses(stage_container, "Validating repository", "failed")
            st.error("Repository not found on GitHub. Please verify the URL.")
            selected_repository = ""
            st.session_state["selected_repository"] = ""
            st.session_state["sidebar_repo_selectbox"] = ""
        except GitHubRateLimitError:
            _reset_stage_statuses(stage_container, "Fetching repository metadata", "failed")
            st.error("GitHub API rate limit reached. Please wait and try again.")
            selected_repository = ""
            st.session_state["selected_repository"] = ""
            st.session_state["sidebar_repo_selectbox"] = ""
        except GitHubPrivateRepositoryError:
            _reset_stage_statuses(stage_container, "Fetching repository metadata", "failed")
            st.error("Unable to access repository. It may be private or require different credentials.")
            selected_repository = ""
            st.session_state["selected_repository"] = ""
            st.session_state["sidebar_repo_selectbox"] = ""
        except GitHubAPIError as exc:
            _reset_stage_statuses(stage_container, "Fetching repository metadata", "failed")
            st.error(f"GitHub API error: {exc}")
            selected_repository = ""
            st.session_state["selected_repository"] = ""
            st.session_state["sidebar_repo_selectbox"] = ""
        except (DataStorageError, DataCleaningError, AnalyticsError, HealthScoreError) as exc:
            _reset_stage_statuses(stage_container, "Running analytics", "failed")
            st.error(f"Repository analysis failed: {exc}")
            selected_repository = ""
            st.session_state["selected_repository"] = ""
            st.session_state["sidebar_repo_selectbox"] = ""

    if selected_repository:
        with st.spinner("Loading analytics..."):
            try:
                _render_dashboard_for_repository(selected_repository)
            except Exception as exc:
                st.error(f"Unable to render dashboard: {exc}")
    else:
        st.markdown(
            """
            <div class='welcome-panel'>
                <div class='welcome-icon'>📊</div>
                <h2>GitHub Repository Health Analyzer</h2>
                <p class='welcome-subtitle'>Get deep engineering analytics, repository health grades, team velocity indicators, and actionable insights.</p>
                <div class='welcome-features'>
                    <div class='feature-item'>
                        <span class='feature-icon'>⚡</span>
                        <strong>Executive KPIs</strong>
                        <span>Instantly view key metrics such as commits, contributors, stars, forks, and age.</span>
                    </div>
                    <div class='feature-item'>
                        <span class='feature-icon'>🧠</span>
                        <strong>Repository Intelligence</strong>
                        <span>Get an objective grade based on activity, community, and maintenance signals.</span>
                    </div>
                    <div class='feature-item'>
                        <span class='feature-icon'>💡</span>
                        <strong>Engineering Insights</strong>
                        <span>Identify bottlenecks, pull request backlogs, and release cadence patterns automatically.</span>
                    </div>
                </div>
                <div class='welcome-instruction'>
                    👉 Select an existing repository from the <strong>Switch Repository</strong> dropdown in the sidebar, or enter a GitHub URL to start a new analysis.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
