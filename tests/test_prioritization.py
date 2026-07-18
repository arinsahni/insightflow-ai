"""Tests for explainable severity and priority."""

import pytest

from src.prioritization import calculate_priority, priority_label


@pytest.mark.parametrize(
    ("score", "label"),
    [(80, "P0 Critical"), (60, "P1 High"), (40, "P2 Medium"), (39.99, "P3 Low")],
)
def test_priority_thresholds(score, label) -> None:
    assert priority_label(score) == label


def test_scores_are_bounded_and_explained() -> None:
    result = calculate_priority(
        frequency_component=120, negative_component=80, average_rating=None,
        trend_component=-5, critical_keyword_component=100,
        business_risk="Trust risk", confidence_component=90,
    )
    assert 0 <= result.severity_score <= 100
    assert 0 <= result.priority_score <= 100
    assert result.severity_explanation
    assert result.priority_explanation


def test_rare_critical_safeguard_prevents_low_priority() -> None:
    result = calculate_priority(
        frequency_component=2, negative_component=100, average_rating=1,
        trend_component=10, critical_keyword_component=100,
        business_risk="Trust risk", confidence_component=80, rare_critical=True,
    )
    assert result.priority_score >= 60
    assert "safeguard" in result.priority_explanation


def test_higher_severity_inputs_increase_priority() -> None:
    low = calculate_priority(
        frequency_component=50, negative_component=10, average_rating=5,
        trend_component=50, critical_keyword_component=0,
        business_risk="Low direct business risk", confidence_component=80,
    )
    high = calculate_priority(
        frequency_component=50, negative_component=100, average_rating=1,
        trend_component=50, critical_keyword_component=100,
        business_risk="Trust risk", confidence_component=80,
    )
    assert high.priority_score > low.priority_score
