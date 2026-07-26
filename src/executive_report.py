"""Prepare, orchestrate, validate, and export executive Gemini reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any

import pandas as pd

from src.ai_models import InsightContext, PromptPayloadMetadata
from src.ai_prompts import (
    build_executive_correction_prompt,
    build_executive_summary_prompt,
)
from src.ai_response_models import ExecutiveReport, GeminiUsageMetadata
from src.ai_response_validator import validate_executive_response
from src.gemini_client import GeminiExecutiveClient
from src.insight_context import build_insight_context, compact_insight_context


@dataclass(frozen=True, slots=True)
class PreparedExecutiveRequest:
    context: InsightContext
    context_payload: dict[str, Any]
    metadata: PromptPayloadMetadata
    prompt: str
    context_fingerprint: str


def context_fingerprint(payload: dict[str, Any]) -> str:
    """Hash canonical analytics while excluding volatile generation timestamps."""
    stable = dict(payload)
    stable.pop("generated_at_utc", None)
    encoded = json.dumps(
        stable, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def prepare_executive_report_request(
    analyzed_df: pd.DataFrame,
    *,
    raw_review_count: int | None = None,
    cleaning_report: dict[str, Any] | object | None = None,
    max_context_characters: int = 24_000,
) -> PreparedExecutiveRequest:
    """Build compact grounded context without initializing or calling Gemini."""
    context = build_insight_context(
        analyzed_df,
        raw_review_count=raw_review_count,
        cleaning_report=cleaning_report,
    )
    payload, metadata = compact_insight_context(
        context, max_characters=max_context_characters
    )
    return PreparedExecutiveRequest(
        context=context,
        context_payload=payload,
        metadata=metadata,
        prompt=build_executive_summary_prompt(payload),
        context_fingerprint=context_fingerprint(payload),
    )


def generate_executive_report(
    analyzed_df: pd.DataFrame,
    *,
    client: GeminiExecutiveClient,
    raw_review_count: int | None = None,
    cleaning_report: dict[str, Any] | object | None = None,
    max_context_characters: int = 24_000,
) -> ExecutiveReport:
    """Generate, validate, and make at most one evidence-correction request."""
    prepared = prepare_executive_report_request(
        analyzed_df,
        raw_review_count=raw_review_count,
        cleaning_report=cleaning_report,
        max_context_characters=max_context_characters,
    )
    response, usage = client.generate_executive_insights(prepared.prompt)
    validation = validate_executive_response(response, prepared.context_payload)
    if not validation.valid:
        correction_prompt = build_executive_correction_prompt(
            prepared.context_payload,
            response.model_dump(mode="json"),
            validation.errors,
        )
        response, correction_usage = client.generate_executive_insights(
            correction_prompt
        )
        usage = _combine_usage(usage, correction_usage)
        validation = validate_executive_response(response, prepared.context_payload)
    return ExecutiveReport(
        response=response,
        model=client.model,
        context_fingerprint=prepared.context_fingerprint,
        generated_at_utc=datetime.now(timezone.utc),
        usage=usage,
        validation_passed=validation.valid,
        validation_errors=validation.errors,
        validation_warnings=validation.warnings,
        validated_review_ids=validation.validated_review_ids,
    )


def _sum_optional(first: int | None, second: int | None) -> int | None:
    if first is None and second is None:
        return None
    return (first or 0) + (second or 0)


def _combine_usage(
    first: GeminiUsageMetadata,
    second: GeminiUsageMetadata,
) -> GeminiUsageMetadata:
    """Combine two bounded generation attempts for honest usage reporting."""
    return GeminiUsageMetadata(
        prompt_token_count=_sum_optional(
            first.prompt_token_count, second.prompt_token_count
        ),
        output_token_count=_sum_optional(
            first.output_token_count, second.output_token_count
        ),
        total_token_count=_sum_optional(
            first.total_token_count, second.total_token_count
        ),
        cached_token_count=_sum_optional(
            first.cached_token_count, second.cached_token_count
        ),
        retry_count=first.retry_count + second.retry_count,
        latency_seconds=first.latency_seconds + second.latency_seconds,
        finish_reason=second.finish_reason,
    )


def executive_report_to_markdown(report: ExecutiveReport) -> str:
    """Export a reviewed report as plain safe Markdown."""
    response = report.response
    lines = [
        "# InsightFlow AI — Executive Insights",
        "",
        f"Generated: {report.generated_at_utc.isoformat()}  ",
        f"Model: {report.model}  ",
        f"Evidence validation: {'Passed' if report.validation_passed else 'Failed'}",
        "",
        "## Executive Summary", "", response.executive_summary, "",
        "## Top Customer Problems", "",
    ]
    for item in sorted(response.customer_problems, key=lambda value: value.rank):
        lines.extend([
            f"### {item.rank}. {item.title}", item.problem_summary,
            f"- Affected users: {item.affected_users}",
            f"- Measured evidence: {item.measured_evidence}",
            f"- Severity / urgency / confidence: {item.severity} / {item.urgency} / {item.confidence}",
            f"- Review IDs: {', '.join(item.supporting_review_ids)}",
            f"- Limitations: {item.limitations}", "",
        ])
    lines.extend(["## Product Opportunities", ""])
    for item in sorted(response.product_opportunities, key=lambda value: value.rank):
        lines.extend([
            f"### {item.rank}. {item.title}", item.user_problem,
            f"- Supporting demand: {item.supporting_demand}",
            f"- Affected segments: {item.affected_segments}",
            f"- Product-impact hypothesis: {item.likely_product_impact_hypothesis}",
            f"- Validation step: {item.suggested_validation_step}",
            f"- Review IDs: {', '.join(item.supporting_review_ids)}",
            f"- Confidence / limitations: {item.confidence} / {item.limitations}", "",
        ])
    lines.extend(["## Release and Platform Risks", ""])
    for item in sorted(response.release_risks, key=lambda value: value.rank):
        lines.extend([
            f"### {item.rank}. {item.title}", item.observed_change,
            f"- Affected: {item.affected_platform_or_segment}",
            f"- Hypotheses: {item.hypotheses}",
            f"- Investigation: {item.recommended_investigation}",
            f"- Review IDs: {', '.join(item.supporting_review_ids)}",
            f"- Limitations: {item.limitations}", "",
        ])
    lines.extend(["## Recommended Next Actions", ""])
    for item in sorted(response.recommended_actions, key=lambda value: value.rank):
        lines.extend([
            f"### {item.rank}. {item.action}", item.rationale,
            f"- Evidence: {item.evidence_summary}",
            f"- Owner / timeframe: {item.owner} / {item.timeframe}",
            f"- Review IDs: {', '.join(item.supporting_review_ids)}",
            f"- Confidence / limitations: {item.confidence} / {item.limitations}", "",
        ])
    lines.extend(["## Evidence", ""])
    for evidence in response.evidence:
        lines.append(f"- **{evidence.review_id}:** “{evidence.quote}”")
    lines.extend([
        "", "## Confidence and Limitations", "",
        f"Overall confidence: **{response.confidence_assessment.overall_confidence}**",
        "", "Evidence strengths:",
        *[f"- {value}" for value in response.confidence_assessment.evidence_strengths],
        "", "Limitations:",
        *[f"- {value}" for value in response.confidence_assessment.limitations],
    ])
    return "\n".join(lines).strip() + "\n"


def executive_report_to_json(report: ExecutiveReport) -> str:
    """Export a Unicode-preserving, finite JSON report."""
    return json.dumps(
        report.model_dump(mode="json"), ensure_ascii=False, indent=2,
        sort_keys=True, allow_nan=False,
    )
