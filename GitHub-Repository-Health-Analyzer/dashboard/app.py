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


def _configure_page() -> None:
    """Configure the Streamlit page metadata."""
    st.set_page_config(
        page_title="Repository Health Dashboard",
        page_icon="📊",
        layout="wide",
    )
    st.markdown(
        """
        <style>
        html, body, .stApp {background-color: #0D1117; color: #F0F6FC; font-family: Inter, system-ui, sans-serif;}
        .block-container {padding: 28px 32px 34px; max-width: 1600px;}
        .stSidebar {background-color: #161B22; color: #F0F6FC; padding: 22px 18px;}
        .stSidebar .css-1d391kg, .stSidebar .css-1rs6os.edgvbvh3 {background: transparent;}
        .stButton>button, .stDownloadButton>button {background-color: #58A6FF; color: #0D1117; border: none; box-shadow: none; border-radius: 12px; padding: 12px 18px; font-weight: 600;}
        .stButton>button:hover, .stDownloadButton>button:hover {opacity: 0.92; transform: translateY(-1px); transition: all 0.18s ease;}
        .section-title h2 {margin: 0; color: #F0F6FC; font-size: 1.72rem; line-height: 1.12;}
        .section-title p {margin: 10px 0 0; color: #8B949E; font-size: 0.98rem; line-height: 1.6;}
        .kpi-card {background: #21262D; border: 1px solid #30363D; border-radius: 14px; padding: 22px; box-shadow: 0 18px 50px rgba(0, 0, 0, 0.22); color: #F0F6FC; margin-bottom: 18px; min-height: 154px; transition: background 0.18s ease, border-color 0.18s ease, transform 0.18s ease;}
        .kpi-card:hover {background: #262f38; border-color: #58A6FF; transform: translateY(-2px);}
        .kpi-card__top {display: flex; justify-content: space-between; align-items: center; gap: 14px; margin-bottom: 16px;}
        .kpi-card__icon {align-items: center; background: rgba(88, 166, 255, 0.12); border: 1px solid rgba(88, 166, 255, 0.22); border-radius: 10px; color: #58A6FF; display: inline-flex; font-size: 20px; height: 36px; justify-content: center; width: 36px;}
        .kpi-card__label {font-size: 0.82rem; color: #8B949E; letter-spacing: 0.09em; text-transform: uppercase;}
        .kpi-card__value {font-size: 2.35rem; font-weight: 700; margin-bottom: 10px; line-height: 1; overflow-wrap: anywhere;}
        .kpi-card__subtitle {font-size: 0.95rem; color: #8B949E;}
        .kpi-card__trend {font-size: 0.9rem; color: #58A6FF;}
        .summary-grid {display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 20px; margin-bottom: 28px;}
        .summary-card {background: #161B22; border: 1px solid #30363D; border-radius: 18px; padding: 22px; color: #F0F6FC; box-shadow: 0 18px 50px rgba(0, 0, 0, 0.15); min-height: 120px; transition: background 0.2s ease;}
        .summary-card:hover {background: #1f272f;}
        .summary-card h3 {margin: 0 0 10px; color: #FFFFFF; font-size: 1rem;}
        .summary-card p {margin: 0; color: #8B949E; font-size: 0.98rem;}
        .dashboard-footer {padding: 22px 0 0; color: #8B949E; font-size: 0.92rem; text-align: center;}
        .metric-box {background: #21262D; border: 1px solid #30363D; border-radius: 16px; padding: 18px; margin-bottom: 16px; transition: background 0.2s ease; min-height: 110px;}
        .metric-box:hover {background: #262f38;}
        .metric-box__label {font-size: 0.85rem; color: #8B949E; text-transform: uppercase; margin-bottom: 10px;}
        .metric-box__value {font-size: 1.75rem; font-weight: 700; margin-bottom: 8px; color: #F0F6FC;}
        .metric-box__description {font-size: 0.95rem; color: #8B949E;}
        .dashboard-sidebar-note {color: #8B949E; font-size: 0.94rem; line-height: 1.6;}
        .dashboard-section-box {background: #161B22; border: 1px solid #30363D; border-radius: 18px; padding: 20px;}
        .dashboard-section-box h3 {margin-top: 0; color: #F0F6FC;}
        .repository-overview {background: #161B22; border: 1px solid #30363D; border-radius: 18px; padding: 22px; margin-bottom: 28px;}
        .overview-grid {display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin-top: 18px;}
        .overview-item {background: #0D1117; border: 1px solid #30363D; border-radius: 12px; padding: 14px 16px; min-height: 84px;}
        .overview-item__label {display: block; color: #8B949E; font-size: 0.76rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 8px;}
        .overview-item__value {display: block; color: #F0F6FC; font-size: 0.98rem; line-height: 1.45; overflow-wrap: anywhere;}
        .overview-item__value a {color: #58A6FF; text-decoration: none;}
        .overview-item__value a:hover {text-decoration: underline;}
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
    lines: List[str] = []
    for stage, status in stage_statuses.items():
        if status == "pending":
            icon = "⏳"
        elif status == "running":
            icon = "🔵"
        elif status == "success":
            icon = "✅"
        else:
            icon = "❌"
        lines.append(f"{icon} **{stage}**")

    stage_container.markdown("\n".join(lines))


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
        "primary_language": "Unknown",
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

    try:
        commit_stats = engine.commit_statistics()
        metrics["total_commits"] = int(commit_stats.get("total_commits", 0))
    except AnalyticsError:
        metrics["total_commits"] = 0

    try:
        contributor_stats = engine.contributor_statistics()
        metrics["total_contributors"] = int(contributor_stats.get("total_contributors", 0))
        metrics["total_contributions"] = int(contributor_stats.get("total_contributions", 0))
        top_contributor = contributor_stats.get("top_contributor", {}) or {}
        metrics["top_contributor"] = top_contributor.get("login") or "Unknown"
        metrics["top_contributor_commits"] = int(top_contributor.get("contributions", 0))
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
    except AnalyticsError:
        metrics["open_issues"] = 0
        metrics["closed_issues"] = 0
        metrics["total_issues"] = 0
        metrics["issue_close_rate"] = 0.0
        metrics["average_comments"] = 0.0

    try:
        pull_request_stats = engine.pull_request_statistics()
        metrics["open_pull_requests"] = int(pull_request_stats.get("open_pull_requests", 0))
        metrics["merged_pull_requests"] = int(pull_request_stats.get("merged_pull_requests", 0))
    except AnalyticsError:
        metrics["open_pull_requests"] = 0
        metrics["merged_pull_requests"] = 0

    try:
        health_score = RepositoryHealthScore(engine).calculate_health_score()
        metrics["health_score"] = round(float(health_score.get("score", 0.0)), 2)
        metrics["health_grade"] = health_score.get("grade", "Pending")
    except (HealthScoreError, AnalyticsError):
        metrics["health_score"] = 0.0
        metrics["health_grade"] = "Pending"

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
    engine = AnalyticsEngine(
        repository_df=repository_data["repository_df"],
        commits_df=repository_data["commits_df"],
        contributors_df=repository_data["contributors_df"],
        issues_df=repository_data["issues_df"],
        languages_df=repository_data["languages_df"],
    )
    RepositoryHealthScore(engine).calculate_health_score()
    advance("Calculating repository health", "success")

    advance("Updating dashboard", "running")
    advance("Updating dashboard", "success")

    return f"{owner}/{repo}"


def main() -> None:
    """Dashboard entry point for Streamlit."""
    _configure_page()

    repository_url, analyze_button = render_sidebar()
    stage_container = st.sidebar.container()
    selected_repository = st.session_state.get("selected_repository", "")

    if analyze_button:
        try:
            selected_repository = _analyze_repository(repository_url, stage_container)
            st.session_state["selected_repository"] = selected_repository
            st.success(f"Analysis complete for {selected_repository}.")
        except ValueError as exc:
            _reset_stage_statuses(stage_container, "Validating repository", "failed")
            st.error(str(exc))
            selected_repository = ""
        except GitHubNotFoundError:
            _reset_stage_statuses(stage_container, "Validating repository", "failed")
            st.error("Repository not found on GitHub. Please verify the URL.")
            selected_repository = ""
        except GitHubRateLimitError:
            _reset_stage_statuses(stage_container, "Fetching repository metadata", "failed")
            st.error("GitHub API rate limit reached. Please wait and try again.")
            selected_repository = ""
        except GitHubPrivateRepositoryError:
            _reset_stage_statuses(stage_container, "Fetching repository metadata", "failed")
            st.error("Unable to access repository. It may be private or require different credentials.")
            selected_repository = ""
        except GitHubAPIError as exc:
            _reset_stage_statuses(stage_container, "Fetching repository metadata", "failed")
            st.error(f"GitHub API error: {exc}")
            selected_repository = ""
        except (DataStorageError, DataCleaningError, AnalyticsError, HealthScoreError) as exc:
            _reset_stage_statuses(stage_container, "Running analytics", "failed")
            st.error(f"Repository analysis failed: {exc}")
            selected_repository = ""

    if selected_repository:
        with st.spinner("Loading analytics..."):
            try:
                _render_dashboard_for_repository(selected_repository)
            except Exception as exc:
                st.error(f"Unable to render dashboard: {exc}")
    else:
        st.markdown(
            "<div style='background: #161B22; border: 1px solid #30363D; border-radius: 18px; padding: 22px; color: #F0F6FC;'>"
            "<h3 style='margin-top: 0;'>Ready to analyze</h3>"
            "<p>Enter a GitHub repository URL in the sidebar and click <strong>🚀 Analyze Repository</strong> to begin.</p>"
            "</div>",
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
