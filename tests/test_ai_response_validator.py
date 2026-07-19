"""Grounding validation tests for model-produced executive reports."""

from src.ai_response_validator import validate_executive_response
from tests.test_ai_response_models import valid_response


PAYLOAD = {
    "dataset": {"total_cleaned_reviews": 100},
    "sentiment": {"negative_share": 0.4, "negative_count": 40},
    "representative_quotes": [
        {"review_id": "R1", "review_text": "Payment failed"},
        {"review_id": "R2", "review_text": "OTP nahi aa raha"},
    ],
    "top_pain_points": [{"representative_review_ids": ["R1"], "review_count": 40}],
    "limitations": ["Synthetic evidence."],
}


def test_valid_ids_exact_quotes_and_supplied_metrics_pass() -> None:
    response = valid_response()
    response.customer_problems[0].measured_evidence = "40 reviews, or 40%, are represented."
    result = validate_executive_response(response, PAYLOAD)
    assert result.valid
    assert result.validated_review_ids == ["R1"]


def test_invented_id_and_fabricated_quote_fail() -> None:
    response = valid_response()
    response.customer_problems[0].supporting_review_ids = ["FAKE"]
    response.evidence[0].quote = "Paraphrased payment problem"
    result = validate_executive_response(response, PAYLOAD)
    assert not result.valid
    assert result.invalid_review_ids == ["FAKE"]
    assert any("not exact" in value for value in result.errors)


def test_duplicate_ids_are_rejected_by_response_model() -> None:
    payload = valid_response().model_dump()
    payload["customer_problems"][0]["supporting_review_ids"] = ["R1", "R1"]
    from pydantic import ValidationError
    from src.ai_response_models import ExecutiveInsightsResponse
    try:
        ExecutiveInsightsResponse.model_validate(payload)
    except ValidationError:
        pass
    else:
        raise AssertionError("duplicate IDs must fail")


def test_unsupported_causal_business_and_numeric_claims_fail() -> None:
    response = valid_response()
    response.executive_summary = (
        "Payment failures caused churn and reduced revenue by 73% across 73 reviews."
    )
    result = validate_executive_response(response, PAYLOAD)
    assert not result.valid
    assert result.unsupported_metrics


def test_hypothesis_wording_and_format_variants_pass() -> None:
    response = valid_response()
    response.executive_summary = (
        "A hypothesis is that payment friction may affect conversion; "
        "the supplied context contains 100 reviews and a 40.0% negative share."
    )
    assert validate_executive_response(response, PAYLOAD).valid


def test_limitations_are_required_by_model() -> None:
    payload = valid_response().model_dump()
    payload["confidence_assessment"]["limitations"] = []
    from pydantic import ValidationError
    from src.ai_response_models import ExecutiveInsightsResponse
    try:
        ExecutiveInsightsResponse.model_validate(payload)
    except ValidationError:
        pass
    else:
        raise AssertionError("limitations must fail")

