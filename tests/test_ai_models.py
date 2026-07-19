"""Validation tests for AI-readiness Pydantic contracts."""

import json

import pytest
from pydantic import ValidationError

from src.ai_models import (
    DatasetSummary,
    FeatureRequestInsight,
    QuoteEvidence,
    SentimentSummary,
)


def test_valid_models_are_json_safe() -> None:
    model = QuoteEvidence(
        review_id="REV-1", review_text="OTP nahi aa raha", rating=2,
        evidence_type="pain_point",
    )
    assert json.loads(model.model_dump_json())["review_text"] == "OTP nahi aa raha"


@pytest.mark.parametrize(
    "factory",
    [
        lambda: DatasetSummary(total_cleaned_reviews=-1),
        lambda: SentimentSummary(positive_share=1.1),
        lambda: FeatureRequestInsight(
            rank=1, group="Export", request_count=1, share_of_requests=0.5,
            average_confidence=1.2,
        ),
        lambda: QuoteEvidence(review_id=" ", review_text="Valid", evidence_type="pain"),
        lambda: QuoteEvidence(review_id="R1", review_text=" ", evidence_type="pain"),
    ],
)
def test_invalid_bounds_and_blank_grounding_fail(factory) -> None:
    with pytest.raises(ValidationError):
        factory()
