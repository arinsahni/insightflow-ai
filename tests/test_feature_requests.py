"""Tests for feature-request intent and grouping."""

import pytest

from src.feature_requests import detect_feature_request


@pytest.mark.parametrize(
    ("text", "group"),
    [
        ("Please add scheduled ordering because I order lunch daily.", "Scheduled delivery"),
        ("Wish there was a dark mode.", "Dark mode"),
        ("Can you add a one tap reorder option?", "Reorder"),
    ],
)
def test_known_request_groups(text, group) -> None:
    result = detect_feature_request(text)
    assert result.is_feature_request
    assert result.feature_request_group == group
    assert 0 <= result.feature_request_confidence <= 1


def test_normal_complaint_is_not_request() -> None:
    result = detect_feature_request("My delivery was late and cold.")
    assert not result.is_feature_request
    assert result.feature_request_group is None
