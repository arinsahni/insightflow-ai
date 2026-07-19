"""Grounding, determinism, compaction, and real-sample context tests."""

from __future__ import annotations

import json
import math
from time import perf_counter

import pandas as pd
import pytest

from src.ai_models import InsightContext
from src.analysis_pipeline import analyze_feedback
from src.data_cleaner import clean_feedback_data
from src.data_loader import load_sample_data, suggest_column_mapping
from src.insight_context import (
    build_insight_context,
    compact_insight_context,
    serialize_insight_context,
)


@pytest.fixture(scope="module")
def real_pipeline():
    raw = load_sample_data(max_rows=50_000).dataframe
    mapping = suggest_column_mapping(raw.columns)
    cleaned = clean_feedback_data(raw, mapping)
    analysis = analyze_feedback(cleaned.dataframe)
    return raw, cleaned, analysis


def test_builder_returns_grounded_deterministic_context_without_mutation(real_pipeline) -> None:
    raw, cleaned, analysis = real_pipeline
    source = analysis.analyzed_reviews
    original = source.copy(deep=True)
    first = build_insight_context(
        source, raw_review_count=len(raw), cleaning_report=cleaned.report
    )
    shuffled = build_insight_context(
        source.sample(frac=1, random_state=7),
        raw_review_count=len(raw),
        cleaning_report=cleaned.report,
    )

    assert isinstance(first, InsightContext)
    assert first.dataset.total_cleaned_reviews == len(source) == 9_985
    assert first.sentiment.negative_count == int(source["sentiment"].eq("Negative").sum())
    assert first.ratings.one_star_count == int(pd.to_numeric(source["rating"], errors="coerce").eq(1).sum())
    assert [item.theme for item in first.top_pain_points] == [
        item.theme for item in shuffled.top_pain_points
    ]
    assert [item.group for item in first.top_feature_requests] == [
        item.group for item in shuffled.top_feature_requests
    ]
    assert [item.value for item in first.platform_insights] == [
        item.value for item in shuffled.platform_insights
    ]
    pd.testing.assert_frame_equal(source, original)


def test_quotes_and_release_stories_are_source_grounded(real_pipeline) -> None:
    _, _, analysis = real_pipeline
    source = analysis.analyzed_reviews
    context = build_insight_context(source)
    source_pairs = set(zip(source["review_id"].astype(str), source["original_text"].astype(str)))
    quote_pairs = {(quote.review_id, quote.review_text) for quote in context.representative_quotes}

    assert quote_pairs.issubset(source_pairs)
    assert len({quote.review_id for quote in context.representative_quotes}) == len(context.representative_quotes)
    assert all(story.supporting_review_ids for story in context.release_stories)
    assert all("memory leak" not in story.evidence_note.lower() for story in context.release_stories)
    assert all(set(story.supporting_review_ids).issubset(set(source["review_id"].astype(str))) for story in context.release_stories)


def test_serialization_round_trip_unicode_and_finite_values(real_pipeline) -> None:
    _, _, analysis = real_pipeline
    source = analysis.analyzed_reviews.copy()
    source.loc[source.index[0], "original_text"] = "OTP nahi aa raha — कृपया help"
    context = build_insight_context(source, max_quotes=16)
    serialized = serialize_insight_context(context)
    decoded = json.loads(serialized)

    assert decoded["schema_version"] == "1.0"
    assert "NaN" not in serialized and "Infinity" not in serialized
    assert all(
        not isinstance(value, float) or math.isfinite(value)
        for section in decoded.values()
        for value in (section.values() if isinstance(section, dict) else [])
    )


def test_compaction_is_bounded_and_preserves_minimum_evidence(real_pipeline) -> None:
    _, _, analysis = real_pipeline
    context = build_insight_context(analysis.analyzed_reviews)
    payload, metadata = compact_insight_context(context, max_characters=24_000)

    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    assert len(encoded) <= 24_000
    assert metadata.character_count == len(encoded)
    assert metadata.approximate_token_count == math.ceil(len(encoded) / 4)
    assert len(payload["top_pain_points"]) >= 3
    assert len(payload["top_feature_requests"]) >= 3
    assert len(payload["representative_quotes"]) >= 4
    with pytest.raises(ValueError, match="too small"):
        compact_insight_context(context, max_characters=100)


def test_missing_optional_columns_are_safe_and_required_columns_are_clear(real_pipeline) -> None:
    _, _, analysis = real_pipeline
    optional = analysis.analyzed_reviews.drop(
        columns=["platform", "app_version", "country", "user_segment", "date"],
        errors="ignore",
    )
    context = build_insight_context(optional)
    assert context.platform_insights == []
    assert context.version_insights == []

    with pytest.raises(ValueError, match="original_text"):
        build_insight_context(optional.drop(columns=["original_text"]))
    with pytest.raises(ValueError, match="empty"):
        build_insight_context(optional.iloc[:0])


def test_real_context_generation_performance(real_pipeline) -> None:
    _, _, analysis = real_pipeline
    started = perf_counter()
    context = build_insight_context(analysis.analyzed_reviews)
    assert perf_counter() - started < 1.5
    assert context.top_pain_points
    assert context.top_feature_requests
