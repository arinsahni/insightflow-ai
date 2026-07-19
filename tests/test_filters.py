"""Tests for global dashboard filtering."""

import pandas as pd

from src.filters import apply_filters, build_filter_options, default_filters, summarize_active_filters


def _data() -> pd.DataFrame:
    return pd.DataFrame({
        "date": pd.to_datetime(["2025-01-01", "2025-01-02", "2025-01-03"]),
        "platform": ["Android", "iOS", "Android"], "rating": [1, 5, 3],
        "sentiment": ["Negative", "Positive", "Neutral"],
        "primary_theme": ["App Performance", "Positive Feedback", "Feature Request"],
        "country": ["India", "India", "UK"],
    })


def test_no_filters_returns_all_without_mutation() -> None:
    source = _data(); original = source.copy(deep=True)
    result = apply_filters(source, default_filters())
    assert len(result) == 3
    pd.testing.assert_frame_equal(source, original)


def test_individual_and_combined_filters() -> None:
    source = _data()
    assert len(apply_filters(source, {"platform": ["Android"]})) == 2
    assert len(apply_filters(source, {"rating": [5]})) == 1
    assert len(apply_filters(source, {"sentiment": ["Negative"]})) == 1
    assert len(apply_filters(source, {"primary_theme": ["Feature Request"]})) == 1
    assert len(apply_filters(source, {"date_range": (pd.Timestamp("2025-01-02").date(), pd.Timestamp("2025-01-03").date())})) == 2
    assert len(apply_filters(source, {"platform": ["Android"], "rating": [1]})) == 1


def test_missing_columns_and_zero_results_are_safe() -> None:
    source = pd.DataFrame({"sentiment": ["Positive"]})
    assert len(apply_filters(source, {"platform": ["Android"]})) == 1
    assert apply_filters(source, {"sentiment": ["Negative"]}).empty


def test_options_defaults_and_summary() -> None:
    options = build_filter_options(_data())
    assert options["platform"] == ["Android", "iOS"]
    assert default_filters()["platform"] == []
    assert "Android" in summarize_active_filters({"platform": ["Android"]})
