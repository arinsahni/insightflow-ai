"""Non-mutating validation for mapped customer-feedback data."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import pandas as pd

from src.data_loader import OPTIONAL_FIELDS, mapping_has_unique_sources


@dataclass(slots=True)
class ValidationResult:
    """Structured validation summary for UI and downstream cleaning."""

    is_valid: bool
    can_proceed: bool
    row_count: int = 0
    column_count: int = 0
    duplicate_row_count: int = 0
    duplicate_text_count: int = 0
    missing_feedback_count: int = 0
    invalid_date_count: int = 0
    invalid_rating_count: int = 0
    out_of_range_rating_count: int = 0
    missing_optional_fields: list[str] = field(default_factory=list)
    mixed_type_columns: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    rating_min: float | None = None
    rating_max: float | None = None
    detected_date_range: tuple[date, date] | None = None


def _nonblank_mask(series: pd.Series) -> pd.Series:
    """Return a Boolean mask for non-null, non-blank values."""
    return series.notna() & series.astype("string").str.strip().ne("")


def _mixed_type_columns(dataframe: pd.DataFrame) -> list[str]:
    """Identify source columns containing multiple Python value types."""
    mixed: list[str] = []
    for column in dataframe.columns:
        types = dataframe[column].dropna().map(type).unique()
        if len(types) > 1:
            mixed.append(str(column))
    return mixed


def validate_dataframe(
    dataframe: pd.DataFrame | None,
    mapping: dict[str, str | None],
    max_rows: int,
) -> ValidationResult:
    """Validate a source DataFrame without mutating it."""
    if dataframe is None:
        return ValidationResult(
            is_valid=False,
            can_proceed=False,
            errors=["No dataset is loaded."],
        )

    row_count, column_count = dataframe.shape
    errors: list[str] = []
    warnings: list[str] = []

    if dataframe.empty:
        errors.append("The dataset is empty.")
    if row_count > max_rows:
        errors.append(f"The dataset exceeds the configured limit of {max_rows:,} rows.")
    if not mapping_has_unique_sources(mapping):
        errors.append("Each source column can be mapped only once.")

    text_column = mapping.get("review_text")
    if not text_column:
        errors.append("Map a source column to review_text before continuing.")
    elif text_column not in dataframe.columns:
        errors.append("The mapped review_text column does not exist in the dataset.")

    missing_feedback_count = 0
    duplicate_text_count = 0
    if text_column in dataframe.columns:
        usable_text = _nonblank_mask(dataframe[text_column])
        missing_feedback_count = int((~usable_text).sum())
        if not usable_text.any():
            errors.append("The mapped review_text column contains no usable feedback.")
        normalized_text = dataframe.loc[usable_text, text_column].astype("string").str.strip()
        duplicate_text_count = int(normalized_text.duplicated(keep="first").sum())
        if missing_feedback_count:
            warnings.append(f"{missing_feedback_count:,} feedback rows are missing or blank.")
        if duplicate_text_count:
            warnings.append(f"{duplicate_text_count:,} duplicate feedback texts were detected.")

    duplicate_row_count = int(dataframe.duplicated(keep="first").sum())
    if duplicate_row_count:
        warnings.append(f"{duplicate_row_count:,} exact duplicate rows were detected.")

    missing_optional_fields = [
        field_name
        for field_name in OPTIONAL_FIELDS
        if not mapping.get(field_name) or mapping[field_name] not in dataframe.columns
    ]
    if missing_optional_fields:
        warnings.append("Optional fields not mapped: " + ", ".join(missing_optional_fields) + ".")

    invalid_date_count = 0
    detected_date_range = None
    date_column = mapping.get("date")
    if date_column in dataframe.columns:
        date_values = dataframe[date_column]
        supplied_dates = _nonblank_mask(date_values)
        parsed_dates = pd.to_datetime(date_values, errors="coerce", format="mixed")
        invalid_date_count = int((supplied_dates & parsed_dates.isna()).sum())
        valid_dates = parsed_dates.dropna()
        if not valid_dates.empty:
            detected_date_range = (valid_dates.min().date(), valid_dates.max().date())
        else:
            warnings.append("No usable date data was detected.")
        if invalid_date_count:
            warnings.append(f"{invalid_date_count:,} date values are invalid and will be cleared.")
    else:
        warnings.append("No date data is available; time-based analysis will be limited.")

    invalid_rating_count = 0
    out_of_range_rating_count = 0
    rating_min = None
    rating_max = None
    rating_column = mapping.get("rating")
    if rating_column in dataframe.columns:
        rating_values = dataframe[rating_column]
        supplied_ratings = _nonblank_mask(rating_values)
        numeric_ratings = pd.to_numeric(rating_values, errors="coerce")
        invalid_rating_count = int((supplied_ratings & numeric_ratings.isna()).sum())
        out_of_range = numeric_ratings.notna() & ~numeric_ratings.between(1, 5)
        out_of_range_rating_count = int(out_of_range.sum())
        valid_ratings = numeric_ratings[numeric_ratings.between(1, 5)].dropna()
        if not valid_ratings.empty:
            rating_min = float(valid_ratings.min())
            rating_max = float(valid_ratings.max())
        else:
            warnings.append("No usable rating data was detected.")
        if invalid_rating_count:
            warnings.append(f"{invalid_rating_count:,} rating values are non-numeric and will be cleared.")
        if out_of_range_rating_count:
            warnings.append(
                f"{out_of_range_rating_count:,} ratings fall outside 1–5 and will be cleared."
            )
    else:
        warnings.append("No rating data is available; rating-based analysis will be limited.")

    mixed_type_columns = _mixed_type_columns(dataframe)
    if mixed_type_columns:
        warnings.append("Mixed value types detected in: " + ", ".join(mixed_type_columns) + ".")
    if 0 < row_count < 10:
        warnings.append("This dataset has fewer than 10 rows; conclusions may be unreliable.")

    can_proceed = not errors
    return ValidationResult(
        is_valid=can_proceed and not warnings,
        can_proceed=can_proceed,
        row_count=row_count,
        column_count=column_count,
        duplicate_row_count=duplicate_row_count,
        duplicate_text_count=duplicate_text_count,
        missing_feedback_count=missing_feedback_count,
        invalid_date_count=invalid_date_count,
        invalid_rating_count=invalid_rating_count,
        out_of_range_rating_count=out_of_range_rating_count,
        missing_optional_fields=missing_optional_fields,
        mixed_type_columns=mixed_type_columns,
        warnings=warnings,
        errors=errors,
        rating_min=rating_min,
        rating_max=rating_max,
        detected_date_range=detected_date_range,
    )
