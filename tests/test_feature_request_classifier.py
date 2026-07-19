"""Focused tests for canonical feature-request classification."""

from __future__ import annotations

import pandas as pd
import pytest

from src.feature_request_classifier import (
    FEATURE_REQUEST_GROUPS,
    add_feature_request_columns,
    detect_feature_request,
    normalize_feature_request_text,
)


@pytest.mark.parametrize(
    ("group", "examples"),
    [
        ("Data Export and Reports", (
            "Please add CSV export.", "Need an Excel download option.",
            "statement download ka option do",
        )),
        ("Budgeting and Spending Insights", (
            "Would love a budget planner.", "Please show spending by category.",
            "budget tracker hona chahiye",
        )),
        ("Scheduled and Recurring Payments", (
            "Allow recurring bank transfers.", "Need an autopay option.",
            "recurring payment ka option do",
        )),
        ("Dark Mode and Appearance", (
            "Please add dark mode.", "Need a larger font option.", "dark theme add karo",
        )),
        ("Multi-Currency and International Support", (
            "Please support multiple currencies.", "Need a USD wallet.",
            "Add international transfer support.",
        )),
        ("Card Controls", (
            "Allow me to freeze card.", "Add an ATM withdrawal toggle.",
            "card limit set karne ka option do",
        )),
        ("Search, Filters, and Sorting", (
            "Add search by merchant.", "Need advanced transaction filters.",
            "Allow sorting by amount.",
        )),
        ("Widgets and Quick Access", (
            "Please add an iOS home-screen widget.", "Need a quick transfer shortcut.",
            "Add Apple Watch support.",
        )),
        ("Family and Shared Accounts", (
            "Please add a family wallet.", "Need a joint account option.",
            "Allow parent and child accounts.",
        )),
        ("Team and Business Access", (
            "Allow team members with approval permissions.",
            "Need bulk payments and payroll.", "Add invoice generation.",
        )),
        ("API and Integrations", (
            "Please provide API access.", "Add QuickBooks integration.",
            "Need webhooks for transaction events.",
        )),
        ("Notifications and Custom Alerts", (
            "Add a low-balance alert.", "Let me choose transaction notifications.",
            "custom alert ka option chahiye",
        )),
        ("Security and Biometric Controls", (
            "Please add app lock.", "Support passkeys.", "Need biometric authentication.",
        )),
        ("Bank and Account Management", (
            "Allow multiple bank accounts.", "Let me change my primary account.",
            "Add beneficiary management.",
        )),
        ("Personalization", (
            "Let me rearrange dashboard cards.", "Allow account nicknames.",
            "I want a custom home screen.",
        )),
        ("Statements and Transaction History", (
            "Let me view two years of transaction history.",
            "Add access to older monthly statements.", "I need a digital passbook.",
        )),
        ("Rewards and Loyalty", (
            "Add cashback rewards.", "Need better referral rewards.",
            "Allow reward-point redemption.",
        )),
        ("Customer Support Improvements", (
            "Please add live chat.", "Need a callback option.",
            "Allow support ticket tracking.",
        )),
        ("Payment Methods and Wallets", (
            "Please support Apple Pay.", "Add another payment method.",
            "Need wallet integration.",
        )),
    ],
)
def test_each_canonical_group(group: str, examples: tuple[str, ...]) -> None:
    for example in examples:
        result = detect_feature_request(example)
        assert result.is_feature_request, example
        assert result.feature_request_group == group, example
        assert 0.65 <= result.feature_request_confidence <= 0.99
        assert result.feature_request_method == "taxonomy_phrase"
        assert result.feature_request_matched_terms


@pytest.mark.parametrize(
    "text",
    [
        "My payment is pending.",
        "I need my refund now.",
        "Support should respond faster.",
        "The app needs to stop crashing.",
        "OTP is not coming.",
        "I cannot view transaction history.",
        "International transfer failed.",
        "I want my transfer completed.",
    ],
)
def test_resolution_complaints_are_not_feature_requests(text: str) -> None:
    assert not detect_feature_request(text).is_feature_request


@pytest.mark.parametrize(
    ("text", "group"),
    [
        ("Add CSV export for reconciliation.", "Data Export and Reports"),
        ("Add QuickBooks integration and transaction export.", "Data Export and Reports"),
        ("Add custom spending categories.", "Budgeting and Spending Insights"),
        ("Add custom transaction alerts.", "Notifications and Custom Alerts"),
        ("Add dark mode and larger text.", "Dark Mode and Appearance"),
        ("Allow team members to export reconciliation reports.", "Data Export and Reports"),
        ("Download old statements as PDF.", "Data Export and Reports"),
        ("Show older statements in the app.", "Statements and Transaction History"),
        ("Need Face ID because OTP keeps failing.", "Security and Biometric Controls"),
    ],
)
def test_overlap_rules_are_deterministic(text: str, group: str) -> None:
    assert detect_feature_request(text).feature_request_group == group


def test_normalization_handles_case_hyphens_spacing_and_variants() -> None:
    variants = ("MULTI CURRENCY", "multi-currency", "multicurrency")
    assert len({normalize_feature_request_text(value) for value in variants}) == 1
    for value in ("auto pay", "auto-pay", "autopay"):
        assert detect_feature_request(f"Please add {value}.").feature_request_group == "Scheduled and Recurring Payments"
    for value in ("csv export", "export csv", "export to csv"):
        assert detect_feature_request(f"Please add {value}.").feature_request_group == "Data Export and Reports"


def test_dataframe_output_preserves_source_and_all_compatibility_fields() -> None:
    source = pd.DataFrame({"clean_text": ["Please add CSV export."], "original_text": ["Please add CSV export."]})
    original = source.copy(deep=True)
    output = add_feature_request_columns(source)
    expected = {
        "is_feature_request", "feature_request_detected", "feature_request_text",
        "feature_request_confidence", "feature_request_group",
        "feature_request_method", "feature_request_matched_terms",
        "feature_request_score",
    }
    assert expected.issubset(output.columns)
    assert output.loc[0, "original_text"] == source.loc[0, "original_text"]
    pd.testing.assert_frame_equal(source, original)


def test_same_input_is_deterministic_and_all_groups_are_declared() -> None:
    text = "Please add custom transaction alerts."
    assert detect_feature_request(text) == detect_feature_request(text)
    assert len(FEATURE_REQUEST_GROUPS) == 20
    assert FEATURE_REQUEST_GROUPS[-1] == "Other feature request"


def test_clear_unknown_capability_uses_other_fallback() -> None:
    result = detect_feature_request("Please add holographic receipt previews.")
    assert result.is_feature_request
    assert result.feature_request_group == "Other feature request"
    assert result.feature_request_method == "intent_fallback"
