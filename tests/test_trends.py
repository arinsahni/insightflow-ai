"""Tests for bounded date-aware trend calculations."""

import numpy as np
import pandas as pd

from src.trends import calculate_trends


def _dated(days: int) -> pd.DataFrame:
    return pd.DataFrame({
        "date": pd.date_range("2025-01-01", periods=days),
        "sentiment": ["Negative"] * days,
        "primary_theme": ["Delivery Experience"] * days,
    })


def test_adequate_coverage_calculates_trend() -> None:
    result = calculate_trends(_dated(30))
    assert not result.theme_trends.empty
    assert result.fastest_growing_theme == "Delivery Experience"
    assert result.theme_trends["trend_score"].between(0, 100).all()


def test_insufficient_coverage_is_neutral_with_warning() -> None:
    result = calculate_trends(_dated(7))
    assert (result.theme_trends["trend_score"] == 50).all()
    assert result.warnings


def test_zero_previous_volume_does_not_create_infinity() -> None:
    dataframe = _dated(30)
    dataframe.loc[:14, "primary_theme"] = "Other"
    result = calculate_trends(dataframe)
    assert np.isfinite(result.theme_trends["growth_rate"]).all()
    assert result.fastest_growing_theme is not None
