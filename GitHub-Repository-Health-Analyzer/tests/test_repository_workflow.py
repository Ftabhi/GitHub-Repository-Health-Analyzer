import importlib

import pytest

from dashboard.app import _parse_github_repository_url
from src import config


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
