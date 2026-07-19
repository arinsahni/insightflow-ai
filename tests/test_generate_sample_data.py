"""Tests for the deterministic realistic synthetic dataset generator."""

from __future__ import annotations

import pandas as pd

from scripts.generate_sample_data import (
    PLATFORM_DEVICES,
    RELEASES,
    REQUIRED_COLUMNS,
    GeneratorConfig,
    generate_dataset,
    select_version_for_date,
)
from src.data_cleaner import clean_feedback_data
from src.data_loader import load_sample_data, suggest_column_mapping
from src.data_validator import validate_dataframe


def _small(seed: int = 42) -> tuple[pd.DataFrame, object]:
    return generate_dataset(GeneratorConfig(
        rows=600, seed=seed, duplicate_rows=12, invalid_dates=3,
        invalid_ratings=3, blank_texts=3, missing_optional_values=6,
    ))


def test_output_is_deterministic_for_same_seed_and_changes_for_new_seed() -> None:
    first, first_report = _small(42)
    second, second_report = _small(42)
    different, _ = _small(43)

    pd.testing.assert_frame_equal(first, second)
    assert first_report.base_rows == second_report.base_rows
    assert first_report.final_rows == second_report.final_rows
    assert first_report.duplicate_rows == second_report.duplicate_rows
    assert not first.equals(different)


def test_schema_counts_ids_and_intentional_quality_issues() -> None:
    dataframe, report = _small()
    primary = dataframe.iloc[:report.base_rows]

    assert report.base_rows == 600
    assert len(dataframe) == 612
    assert tuple(dataframe.columns) == REQUIRED_COLUMNS
    assert primary["review_id"].is_unique
    assert dataframe.duplicated().sum() == report.duplicate_rows == 12
    assert pd.to_datetime(dataframe["date"], errors="coerce").isna().sum() == report.invalid_dates
    assert pd.to_numeric(dataframe["rating"], errors="coerce").isna().sum() == report.invalid_ratings
    assert dataframe["review_text"].fillna("").str.strip().eq("").sum() == report.blank_texts


def test_segments_devices_versions_languages_and_requests_are_realistic() -> None:
    dataframe, report = _small()
    primary = dataframe.iloc[:report.base_rows].copy()
    normalized_platform = primary["platform"].str.strip().str.lower()

    assert set(normalized_platform) == {"android", "ios", "web"}
    assert set(primary["user_segment"]) == {"New User", "Returning User", "Power User", "Small Business", "Student"}
    assert set(primary["subscription_tier"].dropna()) == {"Free", "Premium", "Business"}
    assert primary["country"].nunique() > 1
    assert report.feature_request_rows >= 90
    assert report.hinglish_rows > 0
    assert report.noisy_text_rows > 0
    assert primary["review_text"].str.lower().str.contains(
        r"please add|would be useful|wish there was|can you add|need an option|"
        r"it would be better|add support|feature request"
    ).sum() >= 90
    for platform, devices in PLATFORM_DEVICES.items():
        rows = primary[normalized_platform.eq(platform.lower())]
        assert rows["device"].isin(devices).all()
    valid = pd.to_datetime(primary["date"], errors="coerce").notna()
    parsed = pd.to_datetime(primary.loc[valid, "date"])
    assert (
        primary.loc[valid, "app_version"].reset_index(drop=True)
        == parsed.dt.date.map(select_version_for_date).reset_index(drop=True)
    ).all()


def test_release_stories_are_visible_in_full_deterministic_sample() -> None:
    dataframe, report = generate_dataset(GeneratorConfig())
    primary = dataframe.iloc[:report.base_rows]
    text = primary["review_text"].str.lower()
    app_issue = text.str.contains(r"crash|freeze|slow|lag|blank screen|battery drain")
    payment_issue = text.str.contains(r"payment failed|payment pending|charged twice|money deducted|recipient was not credited")
    positive = primary["rating"].astype(str).isin(["4", "5"])
    late_request = text.str.contains(r"csv export|pdf statements|budgeting dashboard")

    android = primary["platform"].eq("Android")
    assert app_issue[android & primary["app_version"].eq("3.2.1")].mean() > app_issue[android & primary["app_version"].eq("3.2.2")].mean()
    assert payment_issue[primary["app_version"].eq("3.3.0")].mean() > payment_issue[primary["app_version"].eq("3.3.1")].mean()
    assert positive[primary["app_version"].eq("3.4.0")].mean() > positive[primary["app_version"].eq("3.3.1")].mean()
    dates = pd.to_datetime(primary["date"], errors="coerce")
    assert late_request[dates.ge("2026-04-01")].mean() > late_request[dates.lt("2026-04-01")].mean()


def test_generated_sample_is_loader_validator_and_cleaner_compatible(tmp_path) -> None:
    dataframe, report = _small()
    path = tmp_path / "sample.csv"
    dataframe.to_csv(path, index=False)
    loaded = load_sample_data(max_rows=10_000, sample_path=path)
    assert loaded.is_success and loaded.dataframe is not None
    mapping = suggest_column_mapping(loaded.dataframe.columns)
    validation = validate_dataframe(loaded.dataframe, mapping, max_rows=10_000)
    assert validation.can_proceed
    assert validation.duplicate_row_count == report.duplicate_rows
    assert validation.invalid_date_count == report.invalid_dates
    assert validation.invalid_rating_count == report.invalid_ratings
    cleaned = clean_feedback_data(loaded.dataframe, mapping)
    assert len(cleaned.dataframe) == report.base_rows - report.blank_texts
    assert cleaned.report.removed_duplicate_rows == report.duplicate_rows


def test_generation_does_not_mutate_shared_release_constants() -> None:
    original = tuple(RELEASES)
    _small()
    assert RELEASES == original
