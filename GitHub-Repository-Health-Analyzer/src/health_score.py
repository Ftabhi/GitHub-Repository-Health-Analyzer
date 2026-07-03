"""Repository health scoring based on analytics outputs."""
from typing import Any, Dict, Optional

from src.analytics_engine import AnalyticsEngine, AnalyticsError


class HealthScoreError(Exception):
    """Exception raised when repository health scoring fails."""


class RepositoryHealthScore:
    """Calculate repository health score from analytics outputs."""

    WEIGHTS = {
        "commit_activity": 0.25,
        "contributor_activity": 0.20,
        "issue_resolution": 0.20,
        "pull_request_success": 0.15,
        "repository_growth": 0.10,
        "community_engagement": 0.10,
    }

    def __init__(self, analytics_engine: AnalyticsEngine) -> None:
        self.analytics_engine = analytics_engine

    @staticmethod
    def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
        return max(minimum, min(maximum, value))

    @staticmethod
    def _grade(score: float) -> str:
        if score >= 90:
            return "Excellent"
        if score >= 80:
            return "Very Healthy"
        if score >= 70:
            return "Healthy"
        if score >= 60:
            return "Fair"
        if score >= 40:
            return "Needs Attention"
        return "Critical"

    @staticmethod
    def _safe_division(numerator: float, denominator: float, default: float = 0.0) -> float:
        return numerator / denominator if denominator else default

    def commit_score(self) -> float:
        """Score commit activity on a 0-100 scale."""
        try:
            commit_stats = self.analytics_engine.commit_statistics()
        except AnalyticsError as exc:
            raise HealthScoreError("Unable to calculate commit score") from exc

        average_commits = float(commit_stats.get("average_commits_per_day", 0.0))
        commit_activity = min(100.0, average_commits * 25.0)
        return self._clamp(commit_activity)

    def contributor_score(self) -> float:
        """Score contributor activity on a 0-100 scale."""
        try:
            contributor_stats = self.analytics_engine.contributor_statistics()
        except AnalyticsError as exc:
            raise HealthScoreError("Unable to calculate contributor score") from exc

        total_contributors = float(contributor_stats.get("total_contributors", 0))
        average_contributions = float(contributor_stats.get("average_contributions", 0.0))
        contributor_activity = (
            min(50.0, total_contributors * 2.5)
            + min(50.0, average_contributions * 5.0)
        )
        return self._clamp(contributor_activity)

    def issue_score(self) -> float:
        """Score issue resolution on a 0-100 scale."""
        try:
            issue_stats = self.analytics_engine.issue_statistics()
        except AnalyticsError as exc:
            raise HealthScoreError("Unable to calculate issue score") from exc

        close_rate = float(issue_stats.get("issue_close_rate", 0.0))
        open_issues = float(issue_stats.get("open_issues", 0))
        total_issues = float(issue_stats.get("total_issues", 0))
        open_issue_penalty = self._safe_division(open_issues, total_issues) * 50.0
        issue_activity = self._clamp(close_rate * 0.8 + (100.0 - open_issue_penalty) * 0.2)
        return issue_activity

    def pull_request_score(self) -> float:
        """Score pull request activity and success on a 0-100 scale."""
        issues_df = self.analytics_engine.issues_df
        if issues_df is None or issues_df.empty:
            return 50.0

        pr_df = issues_df[issues_df["is_pull_request"] == True]
        if pr_df.empty:
            return 50.0

        closed_prs = int(pr_df[pr_df["state"].str.lower() == "closed"].shape[0])
        total_prs = int(pr_df.shape[0])
        pr_success_rate = self._safe_division(closed_prs, total_prs) * 100.0
        return self._clamp(pr_success_rate)

    def repository_growth_score(self) -> float:
        """Score repository growth based on stars, forks and commit velocity."""
        try:
            repo_summary = self.analytics_engine.repository_summary()
            commit_stats = self.analytics_engine.commit_statistics()
        except AnalyticsError as exc:
            raise HealthScoreError("Unable to calculate repository growth score") from exc

        stars = float(repo_summary.get("stars", 0))
        forks = float(repo_summary.get("forks", 0))
        commits_per_day = float(commit_stats.get("average_commits_per_day", 0.0))

        growth_score = (
            min(50.0, min(stars / 20.0, 50.0))
            + min(30.0, min(forks / 10.0, 30.0))
            + min(20.0, commits_per_day * 5.0)
        )
        return self._clamp(growth_score)

    def community_score(self) -> float:
        """Score community engagement based on contributors, watchers and issue interaction."""
        try:
            contributor_stats = self.analytics_engine.contributor_statistics()
            repo_summary = self.analytics_engine.repository_summary()
            issue_stats = self.analytics_engine.issue_statistics()
        except AnalyticsError as exc:
            raise HealthScoreError("Unable to calculate community score") from exc

        total_contributors = float(contributor_stats.get("total_contributors", 0))
        watchers = float(repo_summary.get("watchers", 0))
        average_comments = float(issue_stats.get("average_comments", 0.0))

        return self._clamp(
            min(40.0, total_contributors * 4.0)
            + min(40.0, min(watchers / 50.0, 40.0))
            + min(20.0, average_comments * 4.0)
        )

    def calculate_health_score(self) -> Dict[str, Any]:
        """Calculate the final repository health score and breakdown."""
        breakdown = {
            "commit_activity": round(self.commit_score(), 2),
            "contributor_activity": round(self.contributor_score(), 2),
            "issue_resolution": round(self.issue_score(), 2),
            "pull_request_success": round(self.pull_request_score(), 2),
            "repository_growth": round(self.repository_growth_score(), 2),
            "community_engagement": round(self.community_score(), 2),
        }

        total_score = sum(
            breakdown[key] * weight for key, weight in self.WEIGHTS.items()
        )
        normalized_score = round(self._clamp(total_score), 2)
        grade = self._grade(normalized_score)
        summary = (
            "A strong repository with balanced commit activity, contributor engagement, "
            "issue resolution, and community involvement."
        )

        return {
            "score": normalized_score,
            "grade": grade,
            "summary": summary,
            "metric_breakdown": breakdown,
        }
