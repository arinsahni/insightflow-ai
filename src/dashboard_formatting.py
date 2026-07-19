"""Presentation-only formatting for executive dashboard views."""

from __future__ import annotations

import pandas as pd


FEEDBACK_COLUMNS: dict[str, str] = {
    "review_id": "Review ID", "original_text": "Feedback", "rating": "Rating",
    "sentiment": "Sentiment", "primary_theme": "Theme", "subtheme": "Subtheme",
    "platform": "Platform", "app_version": "App Version", "date": "Date",
}
TECHNICAL_COLUMNS: dict[str, str] = {
    "review_id": "Review ID", "classification_confidence": "Classification Confidence",
    "classification_method": "Classification Method", "sentiment_score": "Sentiment Score",
    "negativity_score": "Negativity Score", "feature_request_confidence": "Feature Request Confidence",
}


def format_kpi_value(value: object, *, decimals: int = 1, suffix: str = "") -> str:
    """Format a KPI value safely for cards."""
    if value is None or pd.isna(value):
        return "Not available"
    if isinstance(value, (int, float)):
        return f"{value:,.{decimals}f}{suffix}" if decimals else f"{value:,.0f}{suffix}"
    return str(value)


def executive_theme_table(summary: pd.DataFrame) -> pd.DataFrame:
    """Return a human-friendly, sorted theme summary view."""
    columns = {
        "theme": "Theme", "frequency": "Mentions", "share_percentage": "Share",
        "average_rating": "Avg. Rating", "negative_percentage": "Negative Feedback",
        "severity_score": "Severity", "priority_score": "Priority",
        "priority_label": "Priority Level", "business_risk": "Business Risk",
    }
    if summary.empty:
        return pd.DataFrame(columns=columns.values())
    available = [column for column in columns if column in summary]
    output = summary.sort_values(
        ["priority_score", "frequency"], ascending=[False, False]
    )[available].rename(columns=columns).copy()
    for column in ("Share", "Avg. Rating", "Negative Feedback", "Severity", "Priority"):
        if column in output:
            output[column] = pd.to_numeric(output[column], errors="coerce").round(1)
    if "Mentions" in output:
        output["Mentions"] = output["Mentions"].astype(int)
    return output.reset_index(drop=True)


def curated_feedback_table(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return the curated feedback preview without internal text duplicates."""
    output = dataframe[[column for column in FEEDBACK_COLUMNS if column in dataframe]].rename(columns=FEEDBACK_COLUMNS).copy()
    if "Date" in output:
        output["Date"] = pd.to_datetime(output["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
    if "Rating" in output:
        output["Rating"] = pd.to_numeric(output["Rating"], errors="coerce").round(1)
    return output


def technical_feedback_table(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return optional internal diagnostic fields."""
    return dataframe[[column for column in TECHNICAL_COLUMNS if column in dataframe]].rename(columns=TECHNICAL_COLUMNS).copy()
