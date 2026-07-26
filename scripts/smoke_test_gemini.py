#!/usr/bin/env python3
"""Optional one-call Gemini smoke test; excluded from normal pytest."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.analysis_pipeline import analyze_feedback
from src.config import get_settings
from src.data_cleaner import clean_feedback_data
from src.data_loader import load_sample_data, suggest_column_mapping
from src.executive_report import generate_executive_report, prepare_executive_report_request
from src.gemini_client import GeminiError, GeminiExecutiveClient


def main() -> int:
    settings = get_settings()
    if not settings.gemini_api_key:
        print("GEMINI_API_KEY is not configured; optional smoke test skipped safely.")
        return 0
    loaded = load_sample_data(max_rows=settings.max_upload_rows)
    if not loaded.is_success or loaded.dataframe is None:
        print("Sample data could not be loaded.")
        return 1
    cleaned = clean_feedback_data(
        loaded.dataframe, suggest_column_mapping(loaded.dataframe.columns)
    )
    analyzed = analyze_feedback(cleaned.dataframe).analyzed_reviews
    prepared = prepare_executive_report_request(
        analyzed, raw_review_count=len(loaded.dataframe),
        cleaning_report=cleaned.report,
    )
    print(
        f"Prepared {prepared.metadata.character_count} context characters; "
        f"fingerprint={prepared.context_fingerprint[:12]}"
    )
    client = GeminiExecutiveClient(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        timeout_seconds=settings.gemini_timeout_seconds,
        max_retries=settings.gemini_max_retries,
    )
    try:
        report = generate_executive_report(
            analyzed, client=client, raw_review_count=len(loaded.dataframe),
            cleaning_report=cleaned.report,
        )
    except GeminiError as error:
        print(str(error))
        return 1
    print(
        f"validation={report.validation_passed}; "
        f"problems={len(report.response.customer_problems)}; "
        f"opportunities={len(report.response.product_opportunities)}; "
        f"risks={len(report.response.release_risks)}; "
        f"actions={len(report.response.recommended_actions)}"
    )
    if not report.validation_passed:
        for error in report.validation_errors:
            print(f"Validation error: {error}")
        for warning in report.validation_warnings:
            print(f"Validation warning: {warning}")
    return 0 if report.validation_passed else 1


if __name__ == "__main__":
    sys.exit(main())
