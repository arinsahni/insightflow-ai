"""Tests for safe Plotly dashboard figures."""

import pandas as pd
import plotly.graph_objects as go
import pytest

from src.visualizations import (
    feedback_volume_chart, frequency_severity_chart, negative_sentiment_trend_chart,
    priority_matrix_chart, rating_distribution_chart, sentiment_distribution_chart,
    theme_by_segment_heatmap, theme_trend_chart, top_feature_requests_chart,
    top_themes_chart,
)


def _reviews() -> pd.DataFrame:
    return pd.DataFrame({
        "date": pd.date_range("2025-01-01", periods=3), "sentiment": ["Negative"] * 3,
        "rating": [1, 2, pd.NA], "primary_theme": ["App Performance", "App Performance", "Other"],
        "platform": ["Android", "iOS", "Android"],
    })


def _themes() -> pd.DataFrame:
    return pd.DataFrame({"theme": ["App Performance"], "frequency": [2], "severity_score": [80], "priority_score": [75]})


@pytest.mark.parametrize("factory", [
    lambda: feedback_volume_chart(_reviews()),
    lambda: negative_sentiment_trend_chart(_reviews()),
    lambda: top_themes_chart(_reviews()),
    lambda: sentiment_distribution_chart(_reviews()),
    lambda: rating_distribution_chart(_reviews()),
    lambda: frequency_severity_chart(_themes()),
    lambda: theme_by_segment_heatmap(_reviews(), "platform"),
    lambda: theme_trend_chart(_reviews()),
    lambda: top_feature_requests_chart(pd.DataFrame({"feature_request_group": ["Dark mode"], "mentions": [2]})),
    lambda: priority_matrix_chart(_themes()),
])
def test_each_chart_returns_figure(factory) -> None:
    assert isinstance(factory(), go.Figure)


def test_empty_and_missing_inputs_are_safe() -> None:
    functions = [
        feedback_volume_chart, negative_sentiment_trend_chart, top_themes_chart,
        sentiment_distribution_chart, rating_distribution_chart, frequency_severity_chart,
        theme_by_segment_heatmap, theme_trend_chart, top_feature_requests_chart,
        priority_matrix_chart,
    ]
    assert all(isinstance(function(pd.DataFrame()), go.Figure) for function in functions)


def test_chart_inputs_are_not_mutated() -> None:
    source = _reviews(); original = source.copy(deep=True)
    feedback_volume_chart(source); sentiment_distribution_chart(source); theme_by_segment_heatmap(source)
    pd.testing.assert_frame_equal(source, original)


def test_feature_request_chart_keeps_long_category_labels_readable() -> None:
    summary = pd.DataFrame({
        "feature_request_group": [
            "Multi-Currency and International Support",
            "Scheduled and Recurring Payments",
        ],
        "mentions": [12, 8],
    })
    original = summary.copy(deep=True)
    figure = top_feature_requests_chart(summary)

    assert figure.layout.margin.l >= 200
    assert figure.layout.yaxis.automargin
    assert set(figure.data[0].y) == set(summary["feature_request_group"])
    pd.testing.assert_frame_equal(summary, original)


def test_negative_trend_is_weekly_aggregate_not_review_level() -> None:
    source = pd.DataFrame({
        "date": pd.date_range("2025-01-01", periods=21, freq="D"),
        "sentiment": ["Negative"] * 7 + ["Positive"] * 14,
    })
    figure = negative_sentiment_trend_chart(source)
    assert len(figure.data[0].x) <= 4
    assert all(0 <= value <= 100 for value in figure.data[0].y)
    assert "Weekly" in figure.layout.title.text


def test_priority_matrix_uses_readable_annotations_and_keeps_all_bubbles() -> None:
    themes = pd.DataFrame({
        "theme": ["Positive Feedback", "Other", *[f"Issue {i}" for i in range(8)]],
        "frequency": range(1, 11), "severity_score": range(10, 110, 10),
        "priority_score": range(5, 105, 10), "share_percentage": [10] * 10,
        "priority_label": ["P2 Medium"] * 10, "business_risk": ["Retention risk"] * 10,
    })
    original = themes.copy(deep=True)
    figure = priority_matrix_chart(themes)
    labels = [annotation.text for annotation in figure.layout.annotations]

    assert len(labels) <= 5
    assert all(annotation.font.color == "#F8FAFC" for annotation in figure.layout.annotations)
    assert "Positive Feedback" not in labels
    assert "Other" not in labels
    assert figure.data[0].mode == "markers"
    assert figure.data[0].text is None
    assert len(figure.data[0].x) == len(themes)
    pd.testing.assert_frame_equal(themes, original)
