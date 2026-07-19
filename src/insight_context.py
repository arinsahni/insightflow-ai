"""Deterministic extraction and compaction of grounded analytics evidence."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime, timezone
import json
import math
from typing import Any

import numpy as np
import pandas as pd

from src.ai_models import (
    DataQualitySummary,
    DatasetSummary,
    FeatureRequestInsight,
    InsightContext,
    MethodologySummary,
    PainPointInsight,
    PromptPayloadMetadata,
    QuoteEvidence,
    RatingSummary,
    ReleaseStory,
    SegmentInsight,
    SentimentSummary,
)
from src.metrics import calculate_theme_summary
from src.trends import calculate_trends


SCHEMA_VERSION = "1.0"
REQUIRED_COLUMNS = frozenset(
    {"review_id", "original_text", "rating", "sentiment", "primary_theme"}
)
NON_PAIN_THEMES = frozenset({"Positive Feedback", "Feature Request", "Other"})


def _safe_float(value: object, digits: int = 4) -> float | None:
    if value is None or pd.isna(value):
        return None
    number = float(value)
    return round(number, digits) if math.isfinite(number) else None


def _safe_share(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def _stable_unique(series: pd.Series, limit: int | None = None) -> list[str]:
    values = sorted(
        {str(value).strip() for value in series.dropna() if str(value).strip()}
    )
    return values[:limit] if limit is not None else values


def _to_iso_date(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None
    timestamp = pd.Timestamp(value)
    return timestamp.date().isoformat()


def _validate_required_columns(dataframe: pd.DataFrame) -> None:
    missing = sorted(REQUIRED_COLUMNS - set(dataframe.columns))
    if missing:
        raise ValueError(
            "Analyzed feedback is missing required columns: " + ", ".join(missing)
        )


def _build_dataset_summary(
    dataframe: pd.DataFrame, raw_review_count: int | None
) -> DatasetSummary:
    dates = (
        pd.to_datetime(dataframe["date"], errors="coerce").dropna()
        if "date" in dataframe else pd.Series(dtype="datetime64[ns]")
    )
    start = _to_iso_date(dates.min()) if not dates.empty else None
    end = _to_iso_date(dates.max()) if not dates.empty else None
    total_days = int((dates.max() - dates.min()).days) + 1 if not dates.empty else None
    distinct = lambda column: int(dataframe[column].dropna().astype("string").str.strip().replace("", pd.NA).nunique()) if column in dataframe else 0
    return DatasetSummary(
        total_raw_reviews=raw_review_count,
        total_cleaned_reviews=len(dataframe),
        date_start=start,
        date_end=end,
        total_days=total_days,
        platforms=distinct("platform"),
        versions=distinct("app_version"),
        countries=distinct("country"),
        user_segments=distinct("user_segment"),
        subscription_tiers=distinct("subscription_tier"),
    )


def _build_sentiment_summary(dataframe: pd.DataFrame) -> SentimentSummary:
    counts = dataframe["sentiment"].value_counts()
    total = len(dataframe)
    scores = (
        pd.to_numeric(dataframe["sentiment_score"], errors="coerce")
        if "sentiment_score" in dataframe else pd.Series(dtype=float)
    )
    positive, neutral, negative = (
        int(counts.get("Positive", 0)),
        int(counts.get("Neutral", 0)),
        int(counts.get("Negative", 0)),
    )
    return SentimentSummary(
        positive_count=positive,
        neutral_count=neutral,
        negative_count=negative,
        positive_share=_safe_share(positive, total),
        neutral_share=_safe_share(neutral, total),
        negative_share=_safe_share(negative, total),
        average_sentiment_score=_safe_float(scores.mean()) if not scores.empty else None,
    )


def _build_rating_summary(dataframe: pd.DataFrame) -> RatingSummary:
    ratings = pd.to_numeric(dataframe["rating"], errors="coerce")
    valid = ratings[ratings.between(1, 5)].dropna()
    counts = valid.round().astype(int).value_counts()
    return RatingSummary(
        average_rating=_safe_float(valid.mean()) if not valid.empty else None,
        median_rating=_safe_float(valid.median()) if not valid.empty else None,
        one_star_count=int(counts.get(1, 0)),
        two_star_count=int(counts.get(2, 0)),
        three_star_count=int(counts.get(3, 0)),
        four_star_count=int(counts.get(4, 0)),
        five_star_count=int(counts.get(5, 0)),
        low_rating_share=_safe_share(int(valid.isin([1, 2]).sum()), len(valid)),
        high_rating_share=_safe_share(int(valid.isin([4, 5]).sum()), len(valid)),
    )


def _trend_direction(growth: float | None) -> str | None:
    if growth is None:
        return None
    return "growing" if growth > 0.05 else "declining" if growth < -0.05 else "stable"


def _representative_ids(dataframe: pd.DataFrame, theme: str, limit: int = 3) -> list[str]:
    rows = dataframe[dataframe["primary_theme"].eq(theme)].copy()
    if rows.empty:
        return []
    rows["_negative"] = rows["sentiment"].eq("Negative").astype(int)
    if "classification_confidence" not in rows:
        rows["classification_confidence"] = 0.0
    rows = rows.sort_values(
        ["_negative", "classification_confidence", "review_id"],
        ascending=[False, False, True],
    )
    return [str(value) for value in rows["review_id"].drop_duplicates().head(limit)]


def _pain_record(
    dataframe: pd.DataFrame, record: Mapping[str, Any], rank: int
) -> PainPointInsight:
    theme = str(record["theme"])
    rows = dataframe[dataframe["primary_theme"].eq(theme)]
    growth = _safe_float(record.get("growth_rate"))
    return PainPointInsight(
        rank=rank,
        theme=theme,
        review_count=int(record["frequency"]),
        negative_review_count=int(rows["sentiment"].eq("Negative").sum()),
        share_of_reviews=_safe_share(len(rows), len(dataframe)),
        average_rating=_safe_float(record.get("average_rating")),
        severity_score=_safe_float(record.get("severity_score")),
        priority_score=_safe_float(record.get("priority_score")),
        business_risk=str(record["business_risk"]) if pd.notna(record.get("business_risk")) else None,
        trend_direction=_trend_direction(growth),
        growth_rate=growth,
        affected_platforms=_stable_unique(rows["platform"]) if "platform" in rows else [],
        affected_versions=_stable_unique(rows["app_version"]) if "app_version" in rows else [],
        representative_review_ids=_representative_ids(dataframe, theme),
    )


def _rank_pain(
    dataframe: pd.DataFrame,
    summary: pd.DataFrame,
    metric: str,
    limit: int,
) -> list[PainPointInsight]:
    pain = summary[~summary["theme"].isin(NON_PAIN_THEMES)].copy()
    if pain.empty:
        return []
    pain[metric] = pd.to_numeric(pain[metric], errors="coerce").fillna(0)
    ordered = pain.sort_values(
        [metric, "frequency", "theme"], ascending=[False, False, True]
    ).head(limit)
    return [
        _pain_record(dataframe, record, rank)
        for rank, record in enumerate(ordered.to_dict("records"), start=1)
    ]


def _feature_growth(rows: pd.DataFrame, all_dates: pd.Series) -> float | None:
    if "date" not in rows or all_dates.dropna().empty:
        return None
    end = all_dates.max()
    recent_start = end - pd.Timedelta(days=13)
    previous_start = recent_start - pd.Timedelta(days=14)
    dates = pd.to_datetime(rows["date"], errors="coerce")
    recent = int(dates.between(recent_start, end).sum())
    previous = int(dates.between(previous_start, recent_start - pd.Timedelta(days=1)).sum())
    return round(float(np.clip((recent - previous) / (previous + 1), -1, 1)), 4)


def _build_feature_request_insights(
    dataframe: pd.DataFrame, limit: int
) -> list[FeatureRequestInsight]:
    flag = "feature_request_detected" if "feature_request_detected" in dataframe else "is_feature_request"
    if flag not in dataframe or "feature_request_group" not in dataframe:
        return []
    requests = dataframe[dataframe[flag].fillna(False).astype(bool)].copy()
    requests = requests.dropna(subset=["feature_request_group"])
    if requests.empty:
        return []
    all_dates = (
        pd.to_datetime(dataframe["date"], errors="coerce")
        if "date" in dataframe else pd.Series(pd.NaT, index=dataframe.index)
    )
    records = []
    for group, rows in requests.groupby("feature_request_group", sort=True):
        confidence = (
            pd.to_numeric(rows["feature_request_confidence"], errors="coerce").mean()
            if "feature_request_confidence" in rows else np.nan
        )
        growth = _feature_growth(rows, all_dates)
        confidence_values = (
            pd.to_numeric(rows["feature_request_confidence"], errors="coerce").fillna(0)
            if "feature_request_confidence" in rows
            else pd.Series(0.0, index=rows.index)
        )
        ranked = rows.assign(_confidence=confidence_values).sort_values(
            ["_confidence", "review_id"], ascending=[False, True]
        )
        records.append({
            "group": str(group),
            "request_count": len(rows),
            "average_confidence": _safe_float(confidence),
            "growth_rate": growth,
            "affected_platforms": _stable_unique(rows["platform"]) if "platform" in rows else [],
            "affected_segments": _stable_unique(rows["user_segment"]) if "user_segment" in rows else [],
            "representative_review_ids": [str(value) for value in ranked["review_id"].head(3)],
        })
    records.sort(
        key=lambda item: (
            -item["request_count"],
            -(item["average_confidence"] or 0),
            item["group"],
        )
    )
    total = len(requests)
    return [
        FeatureRequestInsight(
            rank=rank,
            share_of_requests=_safe_share(record["request_count"], total),
            trend_direction=_trend_direction(record["growth_rate"]),
            **record,
        )
        for rank, record in enumerate(records[:limit], start=1)
    ]


def _top_value(rows: pd.DataFrame, column: str, excluded: set[str] | None = None) -> str | None:
    if column not in rows:
        return None
    values = rows[column].dropna().astype(str)
    if excluded:
        values = values[~values.isin(excluded)]
    if values.empty:
        return None
    counts = values.value_counts()
    maximum = counts.max()
    return sorted(counts[counts.eq(maximum)].index)[0]


def _build_segment_insights(
    dataframe: pd.DataFrame, column: str, limit: int
) -> list[SegmentInsight]:
    if column not in dataframe:
        return []
    usable = dataframe[dataframe[column].notna()].copy()
    usable = usable[usable[column].astype("string").str.strip().ne("")]
    if usable.empty:
        return []
    groups = sorted(
        usable.groupby(column),
        key=lambda item: (-len(item[1]), str(item[0])),
    )[:limit]
    insights = []
    for value, rows in groups:
        ratings = pd.to_numeric(rows["rating"], errors="coerce")
        requests = rows[
            rows.get("is_feature_request", pd.Series(False, index=rows.index)).fillna(False)
        ]
        insights.append(SegmentInsight(
            dimension=column,
            value=str(value),
            review_count=len(rows),
            negative_share=_safe_share(int(rows["sentiment"].eq("Negative").sum()), len(rows)),
            positive_share=_safe_share(int(rows["sentiment"].eq("Positive").sum()), len(rows)),
            average_rating=_safe_float(ratings.mean()),
            top_pain_point=_top_value(rows, "primary_theme", set(NON_PAIN_THEMES)),
            top_feature_request=_top_value(requests, "feature_request_group"),
        ))
    return insights


def _quote_from_row(row: pd.Series, evidence_type: str) -> QuoteEvidence:
    source_index = row.get("source_row_number")
    return QuoteEvidence(
        review_id=str(row["review_id"]),
        review_text=str(row["original_text"]),
        rating=_safe_float(row.get("rating")),
        date=_to_iso_date(row.get("date")),
        platform=str(row["platform"]) if pd.notna(row.get("platform")) else None,
        app_version=str(row["app_version"]) if pd.notna(row.get("app_version")) else None,
        sentiment_label=str(row["sentiment"]) if pd.notna(row.get("sentiment")) else None,
        pain_point_theme=str(row["primary_theme"]) if pd.notna(row.get("primary_theme")) else None,
        feature_request_group=str(row["feature_request_group"]) if pd.notna(row.get("feature_request_group")) else None,
        evidence_type=evidence_type,
        source_row_index=int(source_index) if pd.notna(source_index) else None,
    )


def _build_quote_evidence(
    dataframe: pd.DataFrame,
    pain_points: list[PainPointInsight],
    features: list[FeatureRequestInsight],
    limit: int,
) -> list[QuoteEvidence]:
    selected: list[QuoteEvidence] = []
    seen_ids: set[str] = set()
    seen_text: set[str] = set()
    for insight in pain_points[:8]:
        candidates = dataframe[dataframe["primary_theme"].eq(insight.theme)].copy()
        candidates["_negative"] = candidates["sentiment"].eq("Negative").astype(int)
        if "classification_confidence" not in candidates:
            candidates["classification_confidence"] = 0.0
        candidates = candidates.sort_values(
            ["_negative", "classification_confidence", "review_id"],
            ascending=[False, False, True],
        )
        for _, row in candidates.iterrows():
            identifier, text = str(row["review_id"]), str(row["original_text"])
            if identifier not in seen_ids and text not in seen_text and text.strip():
                selected.append(_quote_from_row(row, "pain_point"))
                seen_ids.add(identifier); seen_text.add(text)
                break
    for insight in features[:5]:
        candidates = dataframe[
            dataframe.get("feature_request_group", pd.Series(index=dataframe.index)).eq(insight.group)
        ].copy()
        if "feature_request_confidence" in candidates:
            candidates = candidates.sort_values(
                ["feature_request_confidence", "review_id"], ascending=[False, True]
            )
        for _, row in candidates.iterrows():
            identifier, text = str(row["review_id"]), str(row["original_text"])
            if identifier not in seen_ids and text not in seen_text and text.strip():
                selected.append(_quote_from_row(row, "feature_request"))
                seen_ids.add(identifier); seen_text.add(text)
                break
    return selected[:limit]


def _version_key(version: str) -> tuple[int, ...]:
    try:
        return tuple(int(part) for part in version.split("."))
    except ValueError:
        return (0,)


def _metric_story_candidates(
    dataframe: pd.DataFrame,
    *,
    theme: str,
    platform: str | None,
    max_stories: int,
) -> list[ReleaseStory]:
    if "app_version" not in dataframe:
        return []
    source = dataframe
    if platform and "platform" in source:
        source = source[source["platform"].eq(platform)]
    versions = sorted(_stable_unique(source["app_version"]), key=_version_key)
    if len(versions) < 2:
        return []
    rates = {
        version: float(source[source["app_version"].eq(version)]["primary_theme"].eq(theme).mean())
        for version in versions
    }
    stories: list[ReleaseStory] = []
    for index, version in enumerate(versions):
        before = rates.get(versions[index - 1]) if index else None
        during = rates[version]
        after = rates.get(versions[index + 1]) if index + 1 < len(versions) else None
        neighbors = [value for value in (before, after) if value is not None]
        baseline = sum(neighbors) / len(neighbors) if neighbors else None
        if baseline is None or abs(during - baseline) < 0.05:
            continue
        direction = "increase" if during > baseline else "decrease"
        rows = source[
            source["app_version"].eq(version) & source["primary_theme"].eq(theme)
        ].sort_values("review_id")
        ids = [str(value) for value in rows["review_id"].head(3)]
        if not ids:
            continue
        stories.append(ReleaseStory(
            title=f"Observed {theme} {direction} in version {version}",
            version=version,
            platform=platform,
            metric_name=f"{theme} share",
            before_value=_safe_float(before),
            during_value=_safe_float(during),
            after_value=_safe_float(after),
            direction=direction,
            magnitude=_safe_float(during - baseline),
            supporting_review_ids=ids,
            evidence_note=(
                f"Observed {direction} in {theme} feedback for "
                f"{platform + ' ' if platform else ''}version {version} relative to adjacent versions."
            ),
        ))
    return sorted(stories, key=lambda story: (-abs(story.magnitude or 0), story.version))[:max_stories]


def _build_release_stories(dataframe: pd.DataFrame, limit: int) -> list[ReleaseStory]:
    stories = _metric_story_candidates(
        dataframe, theme="App Performance", platform="Android", max_stories=limit
    )
    stories.extend(_metric_story_candidates(
        dataframe, theme="Payment and Checkout", platform=None, max_stories=limit
    ))
    unique: dict[tuple[str, str | None, str], ReleaseStory] = {}
    for story in stories:
        unique[(story.version, story.platform, story.metric_name)] = story
    return sorted(
        unique.values(),
        key=lambda story: (-abs(story.magnitude or 0), story.version, story.metric_name),
    )[:limit]


def _report_value(report: object, *keys: str) -> int | None:
    for key in keys:
        if isinstance(report, Mapping) and key in report:
            value = report[key]
        elif report is not None and hasattr(report, key):
            value = getattr(report, key)
        else:
            continue
        return int(value) if value is not None else None
    return None


def _build_data_quality_summary(report: object) -> DataQualitySummary:
    return DataQualitySummary(
        duplicates_removed=_report_value(report, "removed_duplicate_rows", "duplicates_removed"),
        invalid_dates=_report_value(report, "invalid_dates_coerced", "invalid_dates"),
        invalid_ratings=_report_value(report, "invalid_ratings_coerced", "invalid_ratings"),
        blank_reviews=_report_value(report, "removed_missing_feedback_rows", "blank_reviews"),
        missing_optional_values=_report_value(report, "missing_optional_values"),
        notes=[] if report is not None else ["Cleaning report was not supplied."],
    )


def _build_methodology_summary() -> MethodologySummary:
    return MethodologySummary(
        sentiment_method="Local VADER sentiment with rating-assisted and keyword corrections.",
        pain_point_method="Deterministic phrase and keyword taxonomy with taxonomy-only TF-IDF fallback.",
        feature_request_method="Request-intent detection plus deterministic scored feature taxonomy.",
        prioritization_method="Weighted frequency, severity, trend, business-risk, and confidence aid.",
        trend_method="Bounded recent-versus-previous 14-day aggregation.",
        quote_selection_method="Deterministic ranking of exact source reviews; no paraphrasing.",
        confidence_note="Confidence values are heuristic match-strength indicators, not probabilities.",
    )


def _build_limitations(dataframe: pd.DataFrame) -> list[str]:
    limitations = [
        "The bundled demonstration data is synthetic.",
        "Sentiment is lexicon- and rating-assisted and may miss sarcasm or multilingual nuance.",
        "Taxonomy rules may miss unfamiliar or implicit phrasing.",
        "Heuristic confidence is not probabilistic confidence.",
        "Growth rates may be unstable for low-volume categories.",
        "Release patterns are correlations and do not establish technical causes.",
        "Quotes are representative examples, not exhaustive evidence.",
        "Country and segment distributions reflect generated sample assumptions.",
    ]
    if "subscription_tier" not in dataframe:
        limitations.append("Subscription tier is not preserved in the current cleaned schema.")
    return limitations


def build_insight_context(
    analyzed_df: pd.DataFrame,
    *,
    raw_review_count: int | None = None,
    cleaning_report: dict[str, Any] | object | None = None,
    max_pain_points: int = 8,
    max_feature_requests: int = 8,
    max_quotes: int = 16,
    max_segment_values: int = 6,
    max_release_stories: int = 6,
) -> InsightContext:
    """Build a validated, bounded context from existing analyzed feedback."""
    _validate_required_columns(analyzed_df)
    if analyzed_df.empty:
        raise ValueError("Analyzed feedback is empty.")
    dataframe = analyzed_df.copy(deep=True)
    trends = calculate_trends(dataframe)
    theme_summary = calculate_theme_summary(dataframe, trends)
    top_pain = _rank_pain(dataframe, theme_summary, "frequency", max_pain_points)
    fastest = _rank_pain(dataframe, theme_summary, "growth_rate", max_pain_points)
    priority = _rank_pain(dataframe, theme_summary, "priority_score", max_pain_points)
    features = _build_feature_request_insights(dataframe, max_feature_requests)
    quotes = _build_quote_evidence(dataframe, top_pain, features, max_quotes)
    releases = _build_release_stories(dataframe, max_release_stories)
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    context = InsightContext(
        schema_version=SCHEMA_VERSION,
        generated_at_utc=generated,
        dataset=_build_dataset_summary(dataframe, raw_review_count),
        sentiment=_build_sentiment_summary(dataframe),
        ratings=_build_rating_summary(dataframe),
        top_pain_points=top_pain,
        fastest_growing_issues=fastest,
        highest_priority_issues=priority,
        top_feature_requests=features,
        platform_insights=_build_segment_insights(dataframe, "platform", max_segment_values),
        version_insights=_build_segment_insights(dataframe, "app_version", max_segment_values),
        user_segment_insights=_build_segment_insights(dataframe, "user_segment", max_segment_values),
        subscription_tier_insights=_build_segment_insights(dataframe, "subscription_tier", max_segment_values),
        representative_quotes=quotes,
        release_stories=releases,
        data_quality=_build_data_quality_summary(cleaning_report),
        methodology=_build_methodology_summary(),
        limitations=_build_limitations(dataframe),
        context_statistics={
            "cleaned_reviews": len(dataframe),
            "detected_feature_requests": int(dataframe.get("is_feature_request", pd.Series(False, index=dataframe.index)).sum()),
            "detected_pain_themes": len(top_pain),
            "weekly_periods": len(trends.weekly_volume),
        },
    )
    return context


def _json_length(payload: dict[str, Any]) -> int:
    return len(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False))


def compact_insight_context(
    context: InsightContext,
    *,
    max_characters: int = 24_000,
) -> tuple[dict[str, Any], PromptPayloadMetadata]:
    """Deterministically reduce optional evidence until the JSON fits."""
    if max_characters <= 0:
        raise ValueError("max_characters must be positive.")
    payload = deepcopy(context.model_dump(mode="json"))
    original_length = _json_length(payload)
    truncation = False
    segment_keys = (
        "subscription_tier_insights", "user_segment_insights",
        "version_insights", "platform_insights",
    )
    while _json_length(payload) > max_characters:
        changed = False
        if len(payload["representative_quotes"]) > min(4, len(context.representative_quotes)):
            payload["representative_quotes"].pop(); changed = True
        else:
            for key in segment_keys:
                if len(payload[key]) > 2:
                    payload[key].pop(); changed = True; break
        if not changed and len(payload["top_feature_requests"]) > min(3, len(context.top_feature_requests)):
            payload["top_feature_requests"].pop(); changed = True
        if not changed and payload["release_stories"]:
            payload["release_stories"].pop(); changed = True
        if not changed:
            for key in ("fastest_growing_issues", "highest_priority_issues"):
                if len(payload[key]) > 3:
                    payload[key].pop(); changed = True; break
        if not changed and len(payload["top_pain_points"]) > min(3, len(context.top_pain_points)):
            payload["top_pain_points"].pop(); changed = True
        if not changed:
            raise ValueError(
                "max_characters is too small for the mandatory grounding payload."
            )
        truncation = True
    character_count = _json_length(payload)
    metadata = PromptPayloadMetadata(
        schema_version=context.schema_version,
        character_count=character_count,
        approximate_token_count=math.ceil(character_count / 4),
        quote_count=len(payload["representative_quotes"]),
        pain_point_count=len(payload["top_pain_points"]),
        feature_request_count=len(payload["top_feature_requests"]),
        truncation_applied=truncation or character_count < original_length,
    )
    return payload, metadata


def serialize_insight_context(
    context: InsightContext,
    *,
    indent: int | None = 2,
) -> str:
    """Serialize a validated context to deterministic UTF-8-compatible JSON."""
    return json.dumps(
        context.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        indent=indent,
        allow_nan=False,
    )
