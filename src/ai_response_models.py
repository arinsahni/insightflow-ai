"""Strict structured contracts for evidence-grounded executive insights."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


Confidence = Literal["High", "Medium", "Low"]
Severity = Literal["Critical", "High", "Medium", "Low"]
Urgency = Literal["Immediate", "Near term", "Monitor"]


class StrictResponseModel(BaseModel):
    """Forbid undeclared model output and non-finite numbers."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    @field_validator("*", mode="before")
    @classmethod
    def _reject_blank_strings(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            raise ValueError("strings cannot be blank")
        return value


class EvidenceReference(StrictResponseModel):
    review_id: str = Field(min_length=1, max_length=120)
    quote: str = Field(min_length=1, max_length=1_500)


class CustomerProblem(StrictResponseModel):
    rank: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=120)
    problem_summary: str = Field(min_length=1, max_length=800)
    affected_users: str = Field(min_length=1, max_length=400)
    measured_evidence: str = Field(min_length=1, max_length=600)
    severity: Severity
    urgency: Urgency
    confidence: Confidence
    supporting_review_ids: list[str] = Field(min_length=1, max_length=6)
    limitations: str = Field(min_length=1, max_length=500)

    @field_validator("supporting_review_ids")
    @classmethod
    def _ids_are_unique_and_nonblank(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned):
            raise ValueError("review IDs cannot be blank")
        if len(set(cleaned)) != len(cleaned):
            raise ValueError("review IDs must be unique within an item")
        return cleaned


class ProductOpportunity(StrictResponseModel):
    rank: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=120)
    user_problem: str = Field(min_length=1, max_length=700)
    supporting_demand: str = Field(min_length=1, max_length=600)
    affected_segments: str = Field(min_length=1, max_length=400)
    likely_product_impact_hypothesis: str = Field(min_length=1, max_length=600)
    confidence: Confidence
    supporting_review_ids: list[str] = Field(min_length=1, max_length=6)
    suggested_validation_step: str = Field(min_length=1, max_length=600)
    limitations: str = Field(min_length=1, max_length=500)

    _ids_are_valid = field_validator("supporting_review_ids")(
        CustomerProblem._ids_are_unique_and_nonblank.__func__
    )


class ReleaseRisk(StrictResponseModel):
    rank: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=120)
    observed_change: str = Field(min_length=1, max_length=700)
    affected_platform_or_segment: str = Field(min_length=1, max_length=400)
    severity: Severity
    urgency: Urgency
    confidence: Confidence
    supporting_review_ids: list[str] = Field(min_length=1, max_length=6)
    hypotheses: str = Field(min_length=1, max_length=600)
    recommended_investigation: str = Field(min_length=1, max_length=600)
    limitations: str = Field(min_length=1, max_length=500)

    _ids_are_valid = field_validator("supporting_review_ids")(
        CustomerProblem._ids_are_unique_and_nonblank.__func__
    )


class RecommendedAction(StrictResponseModel):
    rank: int = Field(ge=1)
    action: str = Field(min_length=1, max_length=500)
    rationale: str = Field(min_length=1, max_length=700)
    evidence_summary: str = Field(min_length=1, max_length=600)
    owner: str = Field(min_length=1, max_length=120)
    timeframe: str = Field(min_length=1, max_length=120)
    confidence: Confidence
    supporting_review_ids: list[str] = Field(min_length=1, max_length=6)
    limitations: str = Field(min_length=1, max_length=500)

    _ids_are_valid = field_validator("supporting_review_ids")(
        CustomerProblem._ids_are_unique_and_nonblank.__func__
    )


class ConfidenceAssessment(StrictResponseModel):
    overall_confidence: Confidence
    evidence_strengths: list[str] = Field(min_length=1, max_length=6)
    limitations: list[str] = Field(min_length=1, max_length=8)


class ExecutiveInsightsResponse(StrictResponseModel):
    executive_summary: str = Field(min_length=1, max_length=2_000)
    customer_problems: list[CustomerProblem] = Field(min_length=1, max_length=5)
    product_opportunities: list[ProductOpportunity] = Field(min_length=1, max_length=5)
    release_risks: list[ReleaseRisk] = Field(default_factory=list, max_length=5)
    recommended_actions: list[RecommendedAction] = Field(min_length=1, max_length=7)
    evidence: list[EvidenceReference] = Field(min_length=1, max_length=20)
    confidence_assessment: ConfidenceAssessment

    @model_validator(mode="after")
    def _section_ranks_are_unique(self) -> "ExecutiveInsightsResponse":
        for section in (
            self.customer_problems,
            self.product_opportunities,
            self.release_risks,
            self.recommended_actions,
        ):
            ranks = [item.rank for item in section]
            if len(ranks) != len(set(ranks)):
                raise ValueError("ranks must be unique within each section")
        return self


class GeminiUsageMetadata(StrictResponseModel):
    prompt_token_count: int | None = Field(default=None, ge=0)
    output_token_count: int | None = Field(default=None, ge=0)
    total_token_count: int | None = Field(default=None, ge=0)
    cached_token_count: int | None = Field(default=None, ge=0)
    retry_count: int = Field(default=0, ge=0)
    latency_seconds: float = Field(default=0.0, ge=0)
    finish_reason: str | None = None


class ExecutiveReport(StrictResponseModel):
    response: ExecutiveInsightsResponse
    model: str = Field(min_length=1)
    context_fingerprint: str = Field(min_length=16)
    generated_at_utc: datetime
    usage: GeminiUsageMetadata
    validation_passed: bool
    validation_errors: list[str] = Field(default_factory=list)
    validation_warnings: list[str] = Field(default_factory=list)
    validated_review_ids: list[str] = Field(default_factory=list)

