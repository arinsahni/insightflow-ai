"""Structural tests for the immutable-style feature taxonomy."""

from copy import deepcopy

from src.feature_request_classifier import (
    FEATURE_REQUEST_GROUPS,
    FEATURE_REQUEST_TAXONOMY,
    detect_feature_request,
)


def test_taxonomy_has_one_rule_for_each_specific_canonical_group() -> None:
    assert tuple(FEATURE_REQUEST_TAXONOMY) == FEATURE_REQUEST_GROUPS[:-1]
    assert all(rule.phrases for rule in FEATURE_REQUEST_TAXONOMY.values())
    assert sorted(rule.priority for rule in FEATURE_REQUEST_TAXONOMY.values()) == list(range(1, 20))


def test_classification_does_not_mutate_taxonomy_constants() -> None:
    original = deepcopy(FEATURE_REQUEST_TAXONOMY)
    detect_feature_request("Please add CSV export and QuickBooks integration.")
    assert FEATURE_REQUEST_TAXONOMY == original
