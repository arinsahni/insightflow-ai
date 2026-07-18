"""Tests for representative quote grounding."""

import pandas as pd

from src.quotes import quotes_are_grounded, select_representative_quotes


def test_quotes_are_unique_limited_and_grounded() -> None:
    dataframe = pd.DataFrame({
        "review_id": ["1", "2", "3", "4"],
        "original_text": ["Late delivery again", "Late delivery again", "Order took an hour", "Great app"],
        "date": pd.to_datetime(["2025-01-01"] * 4),
        "rating": [1, 1, 2, 5],
        "platform": ["iOS", "iOS", "Android", "iOS"],
        "primary_theme": ["Delivery Experience", "Delivery Experience", "Delivery Experience", "Positive Feedback"],
        "sentiment": ["Negative", "Negative", "Negative", "Positive"],
        "classification_confidence": [0.9, 0.8, 0.7, 0.9],
    })
    quotes = select_representative_quotes(dataframe, "Delivery Experience", limit=2)
    assert len(quotes) == 2
    assert len({quote["original_text"] for quote in quotes}) == 2
    assert all(quote["review_id"] in {"1", "2", "3"} for quote in quotes)
    assert all(quote["primary_theme"] == "Delivery Experience" for quote in quotes)
    assert quotes_are_grounded(dataframe, {"Delivery Experience": quotes})
