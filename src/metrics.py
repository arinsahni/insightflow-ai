"""Overall and theme-level product metrics from analyzed feedback."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.prioritization import calculate_priority
from src.taxonomy import CRITICAL_KEYWORDS, PRIMARY_RISK_BY_THEME
from src.trends import TrendOutputs


@dataclass(frozen=True, slots=True)
class OverallMetrics:
    """Reader-facing aggregate metrics."""

    total_feedback_items: int = 0
    total_unique_feedback_items: int = 0
    average_rating: float | None = None
    positive_feedback_percentage: float = 0.0
    neutral_feedback_percentage: float = 0.0
    negative_feedback_percentage: float = 0.0
    detected_theme_count: int = 0
    feature_request_count: int = 0
    most_frequent_pain_point: str | None = None
    fastest_growing_pain_point: str | None = None


def calculate_theme_summary(
    dataframe: pd.DataFrame,
    trend_outputs: TrendOutputs,
) -> pd.DataFrame:
    """Calculate bounded, explainable metrics for each detected theme."""
    if dataframe.empty:
        return pd.DataFrame()
    total = len(dataframe)
    grouped = dataframe.groupby("primary_theme", dropna=False)
    summary = grouped.agg(
        frequency=("review_id", "size"),
        average_rating=("rating", "mean"),
        negative_percentage=("sentiment", lambda values: values.eq("Negative").mean() * 100),
        average_sentiment_score=("sentiment_score", "mean"),
        average_confidence=("classification_confidence", "mean"),
    ).reset_index().rename(columns={"primary_theme": "theme"})
    dominant = (
        dataframe.groupby(["primary_theme", "subtheme"]).size().rename("count").reset_index()
        .sort_values(["primary_theme", "count", "subtheme"], ascending=[True, False, True])
        .drop_duplicates("primary_theme").rename(columns={"primary_theme": "theme"})
    )
    summary = summary.merge(dominant[["theme", "subtheme"]], on="theme", how="left")
    summary["share_percentage"] = summary["frequency"] / total * 100
    trend_table = trend_outputs.theme_trends
    if trend_table.empty:
        summary["trend_score"] = 50.0
        summary["growth_rate"] = 0.0
        summary["issue_velocity"] = 0.0
    else:
        summary = summary.merge(
            trend_table[["theme", "trend_score", "growth_rate", "issue_velocity"]],
            on="theme", how="left",
        )
        summary[["trend_score", "growth_rate", "issue_velocity"]] = summary[
            ["trend_score", "growth_rate", "issue_velocity"]
        ].fillna({"trend_score": 50.0, "growth_rate": 0.0, "issue_velocity": 0.0})

    max_frequency = max(int(summary["frequency"].max()), 1)
    rows: list[dict[str, object]] = []
    lowered_text = dataframe["clean_text"].astype("string").str.lower()
    for record in summary.to_dict("records"):
        theme = str(record["theme"])
        theme_mask = dataframe["primary_theme"].eq(theme)
        critical_mask = pd.Series(False, index=dataframe.index)
        for keyword in CRITICAL_KEYWORDS:
            critical_mask |= lowered_text.str.contains(keyword, regex=False, na=False)
        critical_count = int((theme_mask & critical_mask).sum())
        frequency_component = float(record["frequency"]) / max_frequency * 100
        business_risk = PRIMARY_RISK_BY_THEME.get(theme, "Customer satisfaction risk")
        rare_critical = critical_count > 0 and int(record["frequency"]) <= max(3, round(total * 0.02))
        priority = calculate_priority(
            frequency_component=frequency_component,
            negative_component=float(record["negative_percentage"]),
            average_rating=(
                None if pd.isna(record["average_rating"]) else float(record["average_rating"])
            ),
            trend_component=float(record["trend_score"]),
            critical_keyword_component=min(100.0, critical_count / max(int(record["frequency"]), 1) * 100),
            business_risk=business_risk,
            confidence_component=float(record["average_confidence"]) * 100,
            rare_critical=rare_critical,
        )
        record.update({
            "business_risk": business_risk,
            "severity_score": priority.severity_score,
            "priority_score": priority.priority_score,
            "priority_label": priority.priority_label,
            "frequency_component": priority.frequency_component,
            "negative_component": priority.negative_component,
            "rating_component": priority.rating_component,
            "trend_component": priority.trend_component,
            "critical_keyword_component": priority.critical_keyword_component,
            "business_risk_component": priority.business_risk_component,
            "confidence_component": priority.confidence_component,
            "severity_explanation": priority.severity_explanation,
            "priority_explanation": priority.priority_explanation,
        })
        rows.append(record)
    return pd.DataFrame(rows).sort_values(
        ["priority_score", "frequency", "theme"], ascending=[False, False, True]
    ).reset_index(drop=True)


def calculate_overall_metrics(
    dataframe: pd.DataFrame,
    theme_summary: pd.DataFrame,
    trend_outputs: TrendOutputs,
) -> OverallMetrics:
    """Calculate safe aggregate metrics without division errors."""
    if dataframe.empty:
        return OverallMetrics()
    total = len(dataframe)
    percentages = dataframe["sentiment"].value_counts(normalize=True).mul(100)
    pain = theme_summary[
        ~theme_summary["theme"].isin(["Positive Feedback", "Feature Request", "Other"])
    ]
    most_frequent = (
        pain.sort_values(["frequency", "theme"], ascending=[False, True]).iloc[0]["theme"]
        if not pain.empty else None
    )
    rating = pd.to_numeric(dataframe["rating"], errors="coerce").mean()
    return OverallMetrics(
        total_feedback_items=total,
        total_unique_feedback_items=int(dataframe["original_text"].astype("string").nunique()),
        average_rating=None if pd.isna(rating) else float(rating),
        positive_feedback_percentage=float(percentages.get("Positive", 0.0)),
        neutral_feedback_percentage=float(percentages.get("Neutral", 0.0)),
        negative_feedback_percentage=float(percentages.get("Negative", 0.0)),
        detected_theme_count=int(dataframe["primary_theme"].nunique()),
        feature_request_count=int(dataframe["is_feature_request"].sum()),
        most_frequent_pain_point=str(most_frequent) if most_frequent is not None else None,
        fastest_growing_pain_point=trend_outputs.fastest_growing_theme,
    )


def calculate_feature_request_summary(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Aggregate detected feature requests by normalized group."""
    requests = dataframe[dataframe["is_feature_request"]].copy()
    if requests.empty:
        return pd.DataFrame(columns=[
            "feature_request_group", "mentions", "share_percentage",
            "average_rating", "request_confidence",
        ])
    total = len(dataframe)
    return (
        requests.groupby("feature_request_group", dropna=False)
        .agg(
            mentions=("review_id", "size"),
            average_rating=("rating", "mean"),
            request_confidence=("feature_request_confidence", "mean"),
        )
        .reset_index()
        .assign(share_percentage=lambda frame: frame["mentions"] / total * 100)
        .sort_values(["mentions", "feature_request_group"], ascending=[False, True])
        .reset_index(drop=True)
    )
