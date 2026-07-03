"""Generate engineering insights and recommendations for the dashboard."""

from typing import Dict, List


def generate_engineering_insights(metrics: Dict[str, any]) -> Dict[str, List[str]]:
    """Generate human-readable engineering insights from metrics."""
    insights: List[str] = []
    recommendations: List[str] = []

    health_score = metrics.get("health_score")
    total_commits = metrics.get("total_commits")
    open_issues = metrics.get("open_issues")
    total_contributors = metrics.get("total_contributors")
    issue_close_rate = metrics.get("issue_close_rate")
    average_comments = metrics.get("average_comments")
    primary_language = metrics.get("primary_language")

    if isinstance(health_score, (int, float)) and health_score >= 85:
        insights.append("Repository health is strong with high stability and delivery velocity.")
    elif isinstance(health_score, (int, float)) and health_score >= 70:
        insights.append("Repository health is good, with room to improve issue throughput.")
    else:
        insights.append("Repository health requires attention, especially around issue resolution.")

    if isinstance(total_commits, int) and total_commits > 100:
        insights.append("Commit velocity remains high, indicating healthy engineering throughput.")
    if isinstance(total_contributors, int) and total_contributors > 5:
        insights.append("Contributor engagement is solid, suggesting good onboarding and collaboration.")
    if isinstance(issue_close_rate, (int, float)) and issue_close_rate >= 75:
        insights.append("Issues are closing quickly, supporting reliable delivery.")
    if isinstance(average_comments, (int, float)) and average_comments >= 2:
        insights.append("Collaborative issue discussion is strong, which supports quality review.")
    if primary_language:
        insights.append(f"Primary language is {primary_language}, which drives consistent codebase focus.")

    if isinstance(health_score, (int, float)) and health_score >= 85:
        recommendations.append("Continue maintaining the current development workflow.")
        recommendations.append("Focus on incremental automation and monitoring improvements.")
    elif isinstance(health_score, (int, float)) and health_score >= 70:
        recommendations.append("Prioritize issue backlog reduction to improve developer velocity.")
        recommendations.append("Review contributor workload distribution for better balance.")
    else:
        recommendations.append("Address open issue volume and improve merge cadence.")
        recommendations.append("Establish clearer release and triage processes.")

    if isinstance(open_issues, int) and open_issues > 50:
        recommendations.append("Consider reducing issue churn with stronger prioritization.")

    return {
        "insights": insights,
        "recommendations": recommendations,
    }
