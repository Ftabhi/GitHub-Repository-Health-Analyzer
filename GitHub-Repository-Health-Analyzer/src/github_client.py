"""GitHub API client module."""

from typing import Any, Dict, Optional

import requests

from .config import GITHUB_TOKEN


class GitHubAPIError(Exception):
    """Exception raised when a GitHub API request fails."""


class GitHubNotFoundError(GitHubAPIError):
    """Exception raised when a requested GitHub repository is not found."""


class GitHubRateLimitError(GitHubAPIError):
    """Exception raised when the GitHub API rate limit is reached."""


class GitHubPrivateRepositoryError(GitHubAPIError):
    """Exception raised when a GitHub repository is private or access is denied."""


class GitHubClient:
    """Client for interacting with the GitHub REST API."""

    BASE_URL: str = "https://api.github.com"

    def __init__(self) -> None:
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {GITHUB_TOKEN}",
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Send a request to the GitHub API and return the parsed JSON response."""
        url = f"{self.BASE_URL}{endpoint}"
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                timeout=30,
            )
        except requests.RequestException as exc:
            raise GitHubAPIError(
                f"Network error while contacting GitHub API: {exc}"
            ) from exc

        if response.ok:
            try:
                return response.json()
            except ValueError as exc:
                raise GitHubAPIError(
                    f"Invalid JSON response from GitHub API for {url}"
                ) from exc

        response_text = response.text or ""
        if response.status_code == 404:
            raise GitHubNotFoundError(
                f"GitHub repository not found: {url} - {response_text}"
            )
        if response.status_code == 403 and "rate limit" in response_text.lower():
            raise GitHubRateLimitError(
                f"GitHub API rate limit exceeded for {url}."
            )
        if response.status_code == 403:
            raise GitHubPrivateRepositoryError(
                f"Access denied or private repository for {url}: {response_text}"
            )

        raise GitHubAPIError(
            f"GitHub API request failed: {response.status_code} {response.reason}"
            f" - {response_text}"
        )

    def get_repository(self, owner: str, repo: str) -> Any:
        """Fetch repository details."""
        return self._request("GET", f"/repos/{owner}/{repo}")

    def get_contributors(self, owner: str, repo: str) -> Any:
        """Fetch repository contributors."""
        return self._request("GET", f"/repos/{owner}/{repo}/contributors")

    def get_commits(self, owner: str, repo: str) -> Any:
        """Fetch repository commits."""
        return self._request("GET", f"/repos/{owner}/{repo}/commits")

    def get_issues(self, owner: str, repo: str) -> Any:
        """Fetch repository issues."""
        params = {"state": "all"}
        return self._request("GET", f"/repos/{owner}/{repo}/issues", params=params)

    def get_languages(self, owner: str, repo: str) -> Any:
        """Fetch repository language breakdown."""
        return self._request("GET", f"/repos/{owner}/{repo}/languages")
