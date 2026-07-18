"""Deterministic cleaning for mapped customer-feedback data."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter

import pandas as pd

from src.data_loader import EXPECTED_FIELDS, mapping_has_unique_sources


PRIMARY_COLUMNS: tuple[str, ...] = (
    "review_id",
    "original_text",
    "clean_text",
    "date",
    "rating",
    "platform",
    "app_version",
    "country",
    "device",
    "user_segment",
)
OUTPUT_COLUMNS: tuple[str, ...] = PRIMARY_COLUMNS + ("source_row_number",)


@dataclass(frozen=True, slots=True)
class CleaningReport:
    """Auditable row and coercion counts from one cleaning run."""

    input_rows: int
    output_rows: int
    removed_duplicate_rows: int
    removed_missing_feedback_rows: int
    generated_review_ids: int
    invalid_dates_coerced: int
    invalid_ratings_coerced: int
    processing_time_seconds: float


@dataclass(slots=True)
class CleaningResult:
    """Cleaned data plus its audit report and recoverable warnings."""

    dataframe: pd.DataFrame
    report: CleaningReport
    warnings: list[str] = field(default_factory=list)


def _nonblank_mask(series: pd.Series) -> pd.Series:
    """Return a mask for non-null, non-whitespace values."""
    return series.notna() & series.astype("string").str.strip().ne("")


def _clean_text(series: pd.Series) -> pd.Series:
    """Normalize text while preserving words and meaningful punctuation."""
    return (
        series.astype("string")
        .str.normalize("NFKC")
        .str.replace(r"<[^>]+>", " ", regex=True)
        .str.replace(r"https?://\S+|www\.\S+", " ", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )


def clean_feedback_data(
    dataframe: pd.DataFrame,
    mapping: dict[str, str | None],
) -> CleaningResult:
    """Create canonical clean feedback without mutating the source DataFrame."""
    started = perf_counter()
    text_column = mapping.get("review_text")
    if not text_column or text_column not in dataframe.columns:
        raise ValueError("A valid review_text mapping is required.")
    if not mapping_has_unique_sources(mapping):
        raise ValueError("Each source column can be mapped only once.")

    input_rows = len(dataframe)
    working = dataframe.copy()
    working["source_row_number"] = dataframe.index.to_series().add(2).to_numpy()

    duplicate_mask = working.drop(columns="source_row_number").duplicated(keep="first")
    removed_duplicate_rows = int(duplicate_mask.sum())
    working = working.loc[~duplicate_mask].copy()

    usable_feedback = _nonblank_mask(working[text_column])
    removed_missing_feedback_rows = int((~usable_feedback).sum())
    working = working.loc[usable_feedback].copy()

    output = pd.DataFrame(index=working.index)
    output["original_text"] = working[text_column].astype("string")
    output["clean_text"] = _clean_text(working[text_column])

    for field_name in EXPECTED_FIELDS[1:]:
        source_column = mapping.get(field_name)
        output[field_name] = (
            working[source_column] if source_column and source_column in working.columns else pd.NA
        )

    date_source = output["date"]
    supplied_dates = _nonblank_mask(date_source)
    output["date"] = pd.to_datetime(date_source, errors="coerce", format="mixed")
    invalid_dates_coerced = int((supplied_dates & output["date"].isna()).sum())

    rating_source = output["rating"]
    supplied_ratings = _nonblank_mask(rating_source)
    numeric_ratings = pd.to_numeric(rating_source, errors="coerce")
    invalid_ratings = supplied_ratings & (
        numeric_ratings.isna() | ~numeric_ratings.between(1, 5)
    )
    invalid_ratings_coerced = int(invalid_ratings.sum())
    output["rating"] = numeric_ratings.where(numeric_ratings.between(1, 5))

    id_source = output["review_id"].astype("string")
    missing_ids = ~_nonblank_mask(id_source)
    generated_review_ids = int(missing_ids.sum())
    generated_values = pd.Series(
        [f"IF-{row_number:07d}" for row_number in working["source_row_number"]],
        index=working.index,
        dtype="string",
    )
    output["review_id"] = id_source.mask(missing_ids, generated_values)

    for field_name in ("platform", "app_version", "country", "device", "user_segment"):
        output[field_name] = output[field_name].astype("string").str.strip()
        output[field_name] = output[field_name].mask(output[field_name].eq(""), pd.NA)

    output["source_row_number"] = working["source_row_number"].astype("int64")
    output = output.loc[:, OUTPUT_COLUMNS].reset_index(drop=True)

    warnings: list[str] = []
    if removed_duplicate_rows:
        warnings.append(f"Removed {removed_duplicate_rows:,} exact duplicate rows.")
    if removed_missing_feedback_rows:
        warnings.append(f"Removed {removed_missing_feedback_rows:,} blank feedback rows.")
    if invalid_dates_coerced:
        warnings.append(f"Cleared {invalid_dates_coerced:,} invalid date values.")
    if invalid_ratings_coerced:
        warnings.append(f"Cleared {invalid_ratings_coerced:,} invalid rating values.")

    report = CleaningReport(
        input_rows=input_rows,
        output_rows=len(output),
        removed_duplicate_rows=removed_duplicate_rows,
        removed_missing_feedback_rows=removed_missing_feedback_rows,
        generated_review_ids=generated_review_ids,
        invalid_dates_coerced=invalid_dates_coerced,
        invalid_ratings_coerced=invalid_ratings_coerced,
        processing_time_seconds=perf_counter() - started,
    )
    return CleaningResult(dataframe=output, report=report, warnings=warnings)
