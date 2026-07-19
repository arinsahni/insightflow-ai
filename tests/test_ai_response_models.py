"""Strict executive response contract tests."""

import json

import pytest
from pydantic import ValidationError

from src.ai_response_models import (
    ConfidenceAssessment, CustomerProblem, EvidenceReference,
    ExecutiveInsightsResponse, ProductOpportunity, RecommendedAction,
)


def valid_response() -> ExecutiveInsightsResponse:
    return ExecutiveInsightsResponse(
        executive_summary="Payment failures are the leading observed problem.",
        customer_problems=[CustomerProblem(
            rank=1, title="Payment failures", problem_summary="Customers report failed payments.",
            affected_users="Android customers", measured_evidence="Observed in supplied feedback.",
            severity="High", urgency="Near term", confidence="High",
            supporting_review_ids=["R1"], limitations="Evidence is feedback-only.",
        )],
        product_opportunities=[ProductOpportunity(
            rank=1, title="Improve payment recovery", user_problem="Customers cannot complete payment.",
            supporting_demand="Repeated payment evidence.", affected_segments="Android customers",
            likely_product_impact_hypothesis="This may reduce checkout friction.",
            confidence="Medium", supporting_review_ids=["R1"],
            suggested_validation_step="Review payment failure telemetry.",
            limitations="No conversion metric was supplied.",
        )],
        recommended_actions=[RecommendedAction(
            rank=1, action="Audit payment failures", rationale="The supplied evidence is consistent.",
            evidence_summary="Payment failure reviews are present.", owner="Payments team",
            timeframe="Next planning cycle", confidence="High",
            supporting_review_ids=["R1"], limitations="Root cause is unknown.",
        )],
        evidence=[EvidenceReference(review_id="R1", quote="Payment failed")],
        confidence_assessment=ConfidenceAssessment(
            overall_confidence="Medium", evidence_strengths=["Exact review IDs"],
            limitations=["Feedback does not establish causality."],
        ),
    )


def test_valid_response_serializes_and_forbids_unknown_fields() -> None:
    response = valid_response()
    assert json.loads(response.model_dump_json())["customer_problems"][0]["rank"] == 1
    with pytest.raises(ValidationError):
        ExecutiveInsightsResponse.model_validate({
            **response.model_dump(), "unknown": "blocked",
        })


@pytest.mark.parametrize("field,value", [("executive_summary", " "), ("confidence", "Certain")])
def test_blank_and_invalid_confidence_fail(field, value) -> None:
    payload = valid_response().model_dump()
    if field == "confidence":
        payload["customer_problems"][0]["confidence"] = value
    else:
        payload[field] = value
    with pytest.raises(ValidationError):
        ExecutiveInsightsResponse.model_validate(payload)


def test_negative_duplicate_ranks_blank_ids_and_oversized_sections_fail() -> None:
    payload = valid_response().model_dump()
    payload["customer_problems"][0]["rank"] = -1
    with pytest.raises(ValidationError):
        ExecutiveInsightsResponse.model_validate(payload)
    payload = valid_response().model_dump()
    payload["customer_problems"] *= 2
    with pytest.raises(ValidationError, match="ranks"):
        ExecutiveInsightsResponse.model_validate(payload)
    payload = valid_response().model_dump()
    payload["customer_problems"][0]["supporting_review_ids"] = [" "]
    with pytest.raises(ValidationError):
        ExecutiveInsightsResponse.model_validate(payload)
    payload = valid_response().model_dump()
    payload["customer_problems"] *= 6
    with pytest.raises(ValidationError):
        ExecutiveInsightsResponse.model_validate(payload)

