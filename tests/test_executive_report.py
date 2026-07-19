"""Preparation, orchestration, validation, and export tests."""

import json

import pandas as pd

from src.ai_response_models import GeminiUsageMetadata
from src.analysis_pipeline import analyze_feedback
from src.data_cleaner import clean_feedback_data
from src.data_loader import load_sample_data, suggest_column_mapping
from src.executive_report import (
    context_fingerprint, executive_report_to_json, executive_report_to_markdown,
    generate_executive_report, prepare_executive_report_request,
)
from tests.test_ai_response_models import valid_response


class FakeClient:
    model = "mock-gemini"

    def __init__(self, response):
        self.response = response
        self.calls = 0

    def generate_executive_insights(self, prompt):
        self.calls += 1
        assert "BEGIN UNTRUSTED EVIDENCE JSON" in prompt
        return self.response, GeminiUsageMetadata(total_token_count=321)


def _small_analyzed() -> pd.DataFrame:
    cleaned = pd.DataFrame({
        "review_id": ["R1", "R2", "R3"],
        "original_text": ["Payment failed", "OTP nahi aa raha", "Great app"],
        "clean_text": ["Payment failed", "OTP nahi aa raha", "Great app"],
        "date": pd.to_datetime(["2025-01-01", "2025-01-20", "2025-02-10"]),
        "rating": [1, 2, 5], "platform": ["Android", "Android", "iOS"],
        "app_version": ["1.0", "1.0", "1.1"], "country": ["India"] * 3,
        "device": ["Phone"] * 3, "user_segment": ["New"] * 3,
        "source_row_number": [2, 3, 4],
    })
    return analyze_feedback(cleaned).analyzed_reviews


def test_preparation_is_deterministic_no_api_and_timestamp_excluded() -> None:
    analyzed = _small_analyzed()
    first = prepare_executive_report_request(analyzed)
    second = prepare_executive_report_request(analyzed)
    assert first.context_fingerprint == second.context_fingerprint
    changed = dict(first.context_payload)
    changed["generated_at_utc"] = "2099-01-01T00:00:00Z"
    assert context_fingerprint(changed) == first.context_fingerprint
    changed["dataset"] = {**changed["dataset"], "total_cleaned_reviews": 999}
    assert context_fingerprint(changed) != first.context_fingerprint


def test_orchestration_calls_once_validates_and_exports_unicode() -> None:
    analyzed = _small_analyzed()
    prepared = prepare_executive_report_request(analyzed)
    response = valid_response()
    quote = prepared.context_payload["representative_quotes"][0]
    response.evidence[0].review_id = quote["review_id"]
    response.evidence[0].quote = quote["review_text"]
    response.customer_problems[0].supporting_review_ids = [quote["review_id"]]
    response.product_opportunities[0].supporting_review_ids = [quote["review_id"]]
    response.recommended_actions[0].supporting_review_ids = [quote["review_id"]]
    response.executive_summary = "Evidence includes OTP nahi aa raha."
    client = FakeClient(response)
    report = generate_executive_report(analyzed, client=client)
    markdown = executive_report_to_markdown(report)
    exported = executive_report_to_json(report)
    assert client.calls == 1 and report.validation_passed
    assert "OTP nahi aa raha" in markdown
    assert json.loads(exported)["response"]["executive_summary"]
    assert "api_key" not in markdown.lower() and "api_key" not in exported.lower()


def test_failed_validation_is_represented_safely() -> None:
    response = valid_response()
    response.evidence[0].review_id = "INVENTED"
    response.customer_problems[0].supporting_review_ids = ["INVENTED"]
    client = FakeClient(response)
    report = generate_executive_report(_small_analyzed(), client=client)
    assert not report.validation_passed
    assert report.validation_errors


def test_full_sample_preparation_is_bounded() -> None:
    raw = load_sample_data(max_rows=50_000).dataframe
    cleaned = clean_feedback_data(raw, suggest_column_mapping(raw.columns))
    analyzed = analyze_feedback(cleaned.dataframe).analyzed_reviews
    prepared = prepare_executive_report_request(analyzed)
    assert len(analyzed) == 9_985
    assert prepared.metadata.character_count <= 24_000

