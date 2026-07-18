"""Tests for deterministic hybrid theme classification."""

import pytest

from src.classifier import classify_review


@pytest.mark.parametrize(
    ("text", "sentiment", "theme"),
    [
        ("Payment failed and money was deducted", "Negative", "Payment and Checkout"),
        ("My order arrived very late", "Negative", "Delivery Experience"),
        ("Refund not received after ten days", "Negative", "Refunds and Cancellations"),
        ("The app crashes on checkout", "Negative", "App Performance"),
        ("OTP not received so I cannot login", "Negative", "Login and Account"),
        ("One item was missing from my order", "Negative", "Missing or Incorrect Items"),
        ("Please add dark mode", "Neutral", "Feature Request"),
        ("Great app and excellent service", "Positive", "Positive Feedback"),
        ("hmm", "Neutral", "Other"),
    ],
)
def test_expected_theme(text, sentiment, theme) -> None:
    result = classify_review(text, sentiment)
    assert result.primary_theme == theme
    assert 0 <= result.classification_confidence <= 1


def test_mixed_review_has_distinct_secondary_theme() -> None:
    result = classify_review("Delivery was late and payment failed", "Negative")
    assert result.secondary_theme is not None
    assert result.secondary_theme != result.primary_theme
