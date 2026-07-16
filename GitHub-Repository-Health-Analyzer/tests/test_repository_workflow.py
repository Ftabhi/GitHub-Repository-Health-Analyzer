import importlib
import json

import pandas as pd
import pytest

from dashboard.app import (
    _build_chart_data,
    _build_metrics,
    _build_repository_overview,
    _load_repository_data,
    _parse_github_repository_url,
)
from dashboard.advanced_charts import activity_timeline
from dashboard.charts import commit_trend_chart, contributor_chart, issue_timeline_chart, language_chart
from dashboard.layout import _build_kpi_cards
from src import config
from src.data_cleaner import DataCleaner
from src.github_client import GitHubClient


def test_parse_valid_github_repository_url() -> None:
    owner, repo = _parse_github_repository_url("https://github.com/microsoft/vscode")
    assert (owner, repo) == ("microsoft", "vscode")


def test_parse_invalid_github_repository_url() -> None:
    with pytest.raises(ValueError):
        _parse_github_repository_url("https://example.com/microsoft/vscode")


def test_config_allows_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    reloaded = importlib.reload(config)
    assert isinstance(reloaded.GITHUB_TOKEN, str)


def test_github_client_handles_empty_paginated_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        ok = True
        headers = {}
        text = ""

        def json(self):
            return []

    def fake_request(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr("src.github_client.requests.request", fake_request)
    client = GitHubClient()

    assert client.get_contributors("owner", "repo") == []


def test_github_client_follows_paginated_results(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = [
        type(
            "Response",
            (),
            {
                "ok": True,
                "headers": {"Link": '<https://api.github.com/repos/owner/repo/issues?page=2>; rel="next">'},
                "text": "",
                "json": lambda self: [{"id": 1}],
            },
        )(),
        type(
            "Response",
            (),
            {
                "ok": True,
                "headers": {},
                "text": "",
                "json": lambda self: [{"id": 2}],
            },
        )(),
    ]

    def fake_request(*args, **kwargs):
        return responses.pop(0)

    monkeypatch.setattr("src.github_client.requests.request", fake_request)
    client = GitHubClient()

    assert client.get_issues("owner", "repo") == [{"id": 1}, {"id": 2}]


def test_build_metrics_uses_numeric_defaults_for_empty_data() -> None:
    empty_data = {
        "repository_df": pd.DataFrame(),
        "commits_df": pd.DataFrame(),
        "contributors_df": pd.DataFrame(),
        "issues_df": pd.DataFrame(),
        "languages_df": pd.DataFrame(),
    }

    metrics = _build_metrics(empty_data)

    assert metrics["total_commits"] == 0
    assert metrics["health_score"] == 0.0
    assert metrics["primary_language"] == "Unknown"


@pytest.mark.parametrize(
    "repository",
    [
        "microsoft/vscode",
        "facebook/react",
        "pallets/flask",
        "streamlit/streamlit",
    ],
)
def test_core_chart_data_uses_selected_repository_rows(repository: str) -> None:
    repository_data = _load_repository_data(repository)
    metrics = _build_metrics(repository_data)
    chart_data = _build_chart_data(repository_data, metrics)

    assert not repository_data["repository_df"].empty
    assert not chart_data["commits"].empty
    assert not chart_data["contributors"].empty
    assert not chart_data["languages"].empty
    assert set(chart_data["issue_timeline"].columns) == {"date", "opened", "closed"}
    assert chart_data["raw_issues"].equals(repository_data["issues_df"])


def test_core_charts_render_empty_states_without_fake_slices() -> None:
    empty_commits = pd.DataFrame({"date": [], "commits": []})
    empty_issues = pd.DataFrame({"date": [], "opened": [], "closed": []})
    empty_languages = pd.DataFrame({"language": [], "bytes": []})
    empty_contributors = pd.DataFrame({"contributor": [], "contributions": []})

    figures = [
        commit_trend_chart(empty_commits),
        issue_timeline_chart(empty_issues),
        language_chart(empty_languages),
        contributor_chart(empty_contributors),
        activity_timeline(pd.DataFrame(), pd.DataFrame()),
    ]

    assert all(figure.layout.annotations for figure in figures)
    assert all(len(figure.data) == 0 for figure in figures)


def test_core_charts_include_meaningful_hover_templates() -> None:
    commit_fig = commit_trend_chart(pd.DataFrame({"date": ["2026-07-16"], "commits": [3]}))
    issue_fig = issue_timeline_chart(pd.DataFrame({"date": ["2026-07-16"], "opened": [2], "closed": [1]}))
    language_fig = language_chart(pd.DataFrame({"language": ["Python"], "bytes": [1200]}))
    contributor_fig = contributor_chart(pd.DataFrame({"contributor": ["octocat"], "contributions": [42]}))
    activity_fig = activity_timeline(
        pd.DataFrame({"commit_author_date": ["2026-07-16T00:00:00Z"]}),
        pd.DataFrame({"created_at": ["2026-07-16T00:00:00Z"], "closed_at": ["2026-07-17T00:00:00Z"]}),
    )

    assert "commits" in commit_fig.data[0].hovertemplate
    assert "opened issues" in issue_fig.data[0].hovertemplate
    assert "bytes" in language_fig.data[0].hovertemplate
    assert "contributions" in contributor_fig.data[0].hovertemplate
    assert {trace.name for trace in activity_fig.data} == {"Commits", "Opened issues", "Closed issues"}


def test_build_kpi_cards_use_real_repository_metrics() -> None:
    repository_data = _load_repository_data("microsoft/vscode")
    metrics = _build_metrics(repository_data)

    cards = _build_kpi_cards(metrics)
    card_map = {label: value for label, value, description, trend in cards}

    assert card_map["Total Commits"] == "300"
    assert card_map["Total Contributors"] == "200"
    assert card_map["Open Issues"] == "128"
    assert card_map["Health Score"].endswith("%")
    assert all(not trend for _, _, _, trend in cards)
    assert "Pending" not in card_map["Health Score"]
    assert "N/A" not in card_map["Health Score"]


def test_build_kpi_cards_refresh_when_metrics_change() -> None:
    metrics_a = {
        "total_commits": 100,
        "total_contributors": 20,
        "open_issues": 10,
        "closed_issues": 5,
        "open_pull_requests": 3,
        "merged_pull_requests": 1,
        "repository_age_days": 365,
        "stars": 1000,
        "forks": 200,
        "watchers": 500,
        "health_score": 72.4,
        "health_grade": "Healthy",
    }
    metrics_b = {
        "total_commits": 250,
        "total_contributors": 40,
        "open_issues": 25,
        "closed_issues": 20,
        "open_pull_requests": 8,
        "merged_pull_requests": 6,
        "repository_age_days": 730,
        "stars": 4000,
        "forks": 900,
        "watchers": 1500,
        "health_score": 93.1,
        "health_grade": "Excellent",
    }

    cards_a = _build_kpi_cards(metrics_a)
    cards_b = _build_kpi_cards(metrics_b)
    card_map_a = {label: value for label, value, description, trend in cards_a}
    card_map_b = {label: value for label, value, description, trend in cards_b}

    assert card_map_a["Total Commits"] != card_map_b["Total Commits"]
    assert card_map_a["Stars"] != card_map_b["Stars"]
    assert card_map_a["Health Score"] != card_map_b["Health Score"]


def test_data_cleaner_preserves_repository_overview_metadata(tmp_path) -> None:
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir()
    payload = {
        "id": 1,
        "name": "vscode",
        "full_name": "microsoft/vscode",
        "owner": {"login": "microsoft", "id": 6154722},
        "description": "Visual Studio Code",
        "html_url": "https://github.com/microsoft/vscode",
        "stargazers_count": 170000,
        "forks_count": 32000,
        "watchers_count": 170000,
        "open_issues_count": 5000,
        "language": "TypeScript",
        "license": {"spdx_id": "MIT", "name": "MIT License"},
        "created_at": "2015-09-03T20:23:38Z",
        "updated_at": "2026-07-16T10:00:00Z",
        "pushed_at": "2026-07-16T11:00:00Z",
        "visibility": "public",
        "size": 900000,
        "default_branch": "main",
    }
    (raw_dir / "microsoft_vscode_repository.json").write_text(json.dumps(payload), encoding="utf-8")

    cleaner = DataCleaner(raw_dir=raw_dir, processed_dir=processed_dir)
    repository_df = cleaner.clean_repository("microsoft", "vscode")
    overview = _build_repository_overview(repository_df)

    assert overview["Repository Name"] == "vscode"
    assert overview["Owner"] == "microsoft"
    assert overview["Description"] == "Visual Studio Code"
    assert overview["Repository URL"] == "https://github.com/microsoft/vscode"
    assert overview["Primary Language"] == "TypeScript"
    assert overview["Stars"] == "170,000"
    assert overview["Forks"] == "32,000"
    assert overview["Watchers"] == "170,000"
    assert overview["Open Issues"] == "5,000"
    assert overview["License"] == "MIT"
    assert overview["Default Branch"] == "main"
    assert overview["Repository Age"].endswith(" days")
    assert overview["Created Date"] == "2015-09-03 20:23 UTC"
    assert overview["Last Updated"] == "2026-07-16 10:00 UTC"
    assert overview["Last Push Date"] == "2026-07-16 11:00 UTC"
    assert overview["Repository Visibility"] == "Public"
    assert overview["Repository Size"] == "878.9 MB"
