"""Tests for transparent local sentiment analysis."""

import pandas as pd
import pytest

from src.sentiment import analyze_sentiment


@pytest.mark.parametrize(
    ("text", "rating", "expected"),
    [
        ("great", None, "Positive"),
        ("bad", None, "Negative"),
        ("okay", None, "Neutral"),
        ("Great food but payment failed", 1, "Negative"),
        ("Excellent service", 5, "Positive"),
        ("not working", None, "Negative"),
        ("", None, "Neutral"),
        (None, None, "Neutral"),
    ],
)
def test_sentiment_behavior(text, rating, expected) -> None:
    result = analyze_sentiment(text, rating)
    assert result.sentiment == expected
    assert -1 <= result.sentiment_score <= 1
    assert 0 <= result.negativity_score <= 1


def test_missing_rating_uses_text() -> None:
    assert analyze_sentiment("Terrible experience", pd.NA).sentiment == "Negative"
