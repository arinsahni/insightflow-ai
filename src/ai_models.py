"""Validated data contracts for future evidence-grounded AI features."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GroundedModel(BaseModel):
    """Strict JSON-safe base model for grounding payloads."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class DatasetSummary(GroundedModel):
    total_raw_reviews: int | None = Field(default=None, ge=0)
    total_cleaned_reviews: int = Field(ge=0)
    date_start: str | None = None
    date_end: str | None = None
    total_days: int | None = Field(default=None, ge=0)
    platforms: int = Field(default=0, ge=0)
    versions: int = Field(default=0, ge=0)
    countries: int = Field(default=0, ge=0)
    user_segments: int = Field(default=0, ge=0)
    subscription_tiers: int = Field(default=0, ge=0)


class SentimentSummary(GroundedModel):
    positive_count: int = Field(default=0, ge=0)
    neutral_count: int = Field(default=0, ge=0)
    negative_count: int = Field(default=0, ge=0)
    positive_share: float = Field(default=0.0, ge=0, le=1)
    neutral_share: float = Field(default=0.0, ge=0, le=1)
    negative_share: float = Field(default=0.0, ge=0, le=1)
    average_sentiment_score: float | None = None


class RatingSummary(GroundedModel):
    average_rating: float | None = None
    median_rating: float | None = None
    one_star_count: int = Field(default=0, ge=0)
    two_star_count: int = Field(default=0, ge=0)
    three_star_count: int = Field(default=0, ge=0)
    four_star_count: int = Field(default=0, ge=0)
    five_star_count: int = Field(default=0, ge=0)
    low_rating_share: float = Field(default=0.0, ge=0, le=1)
    high_rating_share: float = Field(default=0.0, ge=0, le=1)


class PainPointInsight(GroundedModel):
    rank: int = Field(ge=1)
    theme: str = Field(min_length=1)
    review_count: int = Field(ge=0)
    negative_review_count: int = Field(ge=0)
    share_of_reviews: float = Field(ge=0, le=1)
    average_rating: float | None = None
    severity_score: float | None = Field(default=None, ge=0, le=100)
    priority_score: float | None = Field(default=None, ge=0, le=100)
    business_risk: str | None = None
    trend_direction: str | None = None
    growth_rate: float | None = None
    affected_platforms: list[str] = Field(default_factory=list)
    affected_versions: list[str] = Field(default_factory=list)
    representative_review_ids: list[str] = Field(default_factory=list)


class FeatureRequestInsight(GroundedModel):
    rank: int = Field(ge=1)
    group: str = Field(min_length=1)
    request_count: int = Field(ge=0)
    share_of_requests: float = Field(ge=0, le=1)
    average_confidence: float | None = Field(default=None, ge=0, le=1)
    trend_direction: str | None = None
    growth_rate: float | None = None
    affected_platforms: list[str] = Field(default_factory=list)
    affected_segments: list[str] = Field(default_factory=list)
    representative_review_ids: list[str] = Field(default_factory=list)


class SegmentInsight(GroundedModel):
    dimension: str = Field(min_length=1)
    value: str = Field(min_length=1)
    review_count: int = Field(ge=0)
    negative_share: float = Field(ge=0, le=1)
    positive_share: float = Field(ge=0, le=1)
    average_rating: float | None = None
    top_pain_point: str | None = None
    top_feature_request: str | None = None


class QuoteEvidence(GroundedModel):
    review_id: str = Field(min_length=1)
    review_text: str = Field(min_length=1)
    rating: float | None = None
    date: str | None = None
    platform: str | None = None
    app_version: str | None = None
    sentiment_label: str | None = None
    pain_point_theme: str | None = None
    feature_request_group: str | None = None
    evidence_type: str = Field(min_length=1)
    source_row_index: int | None = Field(default=None, ge=0)

    @field_validator("review_id", "review_text")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("grounded quote fields cannot be blank")
        return value


class ReleaseStory(GroundedModel):
    title: str = Field(min_length=1)
    version: str = Field(min_length=1)
    platform: str | None = None
    period_start: str | None = None
    period_end: str | None = None
    metric_name: str = Field(min_length=1)
    before_value: float | None = None
    during_value: float | None = None
    after_value: float | None = None
    direction: str = Field(min_length=1)
    magnitude: float | None = None
    supporting_review_ids: list[str] = Field(default_factory=list)
    evidence_note: str = Field(min_length=1)


class DataQualitySummary(GroundedModel):
    duplicates_removed: int | None = Field(default=None, ge=0)
    invalid_dates: int | None = Field(default=None, ge=0)
    invalid_ratings: int | None = Field(default=None, ge=0)
    blank_reviews: int | None = Field(default=None, ge=0)
    missing_optional_values: int | None = Field(default=None, ge=0)
    notes: list[str] = Field(default_factory=list)


class MethodologySummary(GroundedModel):
    sentiment_method: str
    pain_point_method: str
    feature_request_method: str
    prioritization_method: str
    trend_method: str
    quote_selection_method: str
    confidence_note: str


class InsightContext(GroundedModel):
    schema_version: str = Field(min_length=1)
    generated_at_utc: str = Field(min_length=1)
    dataset: DatasetSummary
    sentiment: SentimentSummary
    ratings: RatingSummary
    top_pain_points: list[PainPointInsight] = Field(default_factory=list)
    fastest_growing_issues: list[PainPointInsight] = Field(default_factory=list)
    highest_priority_issues: list[PainPointInsight] = Field(default_factory=list)
    top_feature_requests: list[FeatureRequestInsight] = Field(default_factory=list)
    platform_insights: list[SegmentInsight] = Field(default_factory=list)
    version_insights: list[SegmentInsight] = Field(default_factory=list)
    user_segment_insights: list[SegmentInsight] = Field(default_factory=list)
    subscription_tier_insights: list[SegmentInsight] = Field(default_factory=list)
    representative_quotes: list[QuoteEvidence] = Field(default_factory=list)
    release_stories: list[ReleaseStory] = Field(default_factory=list)
    data_quality: DataQualitySummary
    methodology: MethodologySummary
    limitations: list[str] = Field(default_factory=list)
    context_statistics: dict[str, int | float | str] = Field(default_factory=dict)


class PromptPayloadMetadata(GroundedModel):
    schema_version: str = Field(min_length=1)
    character_count: int = Field(ge=0)
    approximate_token_count: int = Field(ge=0)
    quote_count: int = Field(ge=0)
    pain_point_count: int = Field(ge=0)
    feature_request_count: int = Field(ge=0)
    truncation_applied: bool = False


JsonDict = dict[str, Any]
