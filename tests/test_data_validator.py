"""Tests for non-mutating feedback validation."""

import pandas as pd

from src.data_validator import validate_dataframe


FULL_MAPPING = {
    "review_text": "review_text",
    "review_id": "review_id",
    "date": "date",
    "rating": "rating",
    "platform": "platform",
    "app_version": "app_version",
    "country": "country",
    "device": "device",
    "user_segment": "user_segment",
}


def _valid_dataframe(rows: int = 10) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "review_id": [f"R-{index}" for index in range(rows)],
            "review_text": [f"Review number {index}" for index in range(rows)],
            "date": ["2025-01-01"] * rows,
            "rating": [4] * rows,
            "platform": ["Android"] * rows,
            "app_version": ["1.0"] * rows,
            "country": ["India"] * rows,
            "device": ["Phone"] * rows,
            "user_segment": ["Regular"] * rows,
        }
    )


def test_valid_dataset_passes() -> None:
    result = validate_dataframe(_valid_dataframe(), FULL_MAPPING, max_rows=100)

    assert result.can_proceed
    assert result.is_valid
    assert result.errors == []
    assert result.row_count == 10


def test_missing_review_text_mapping_fails() -> None:
    mapping = dict(FULL_MAPPING, review_text=None)
    result = validate_dataframe(_valid_dataframe(), mapping, max_rows=100)

    assert not result.can_proceed
    assert any("review_text" in error for error in result.errors)


def test_empty_dataset_fails() -> None:
    result = validate_dataframe(pd.DataFrame(), {}, max_rows=100)

    assert not result.can_proceed
    assert any("empty" in error.lower() for error in result.errors)


def test_duplicate_rows_and_text_are_counted() -> None:
    dataframe = _valid_dataframe()
    dataframe = pd.concat([dataframe, dataframe.iloc[[0]]], ignore_index=True)

    result = validate_dataframe(dataframe, FULL_MAPPING, max_rows=100)

    assert result.can_proceed
    assert result.duplicate_row_count == 1
    assert result.duplicate_text_count == 1


def test_missing_feedback_rows_are_counted() -> None:
    dataframe = _valid_dataframe()
    dataframe.loc[0, "review_text"] = None
    dataframe.loc[1, "review_text"] = "   "

    result = validate_dataframe(dataframe, FULL_MAPPING, max_rows=100)

    assert result.can_proceed
    assert result.missing_feedback_count == 2


def test_invalid_dates_are_counted() -> None:
    dataframe = _valid_dataframe()
    dataframe.loc[0, "date"] = "not-a-date"

    result = validate_dataframe(dataframe, FULL_MAPPING, max_rows=100)

    assert result.invalid_date_count == 1


def test_invalid_and_out_of_range_ratings_are_counted_separately() -> None:
    dataframe = _valid_dataframe()
    dataframe["rating"] = dataframe["rating"].astype("object")
    dataframe.loc[0, "rating"] = "unknown"
    dataframe.loc[1, "rating"] = 7
    dataframe.loc[2, "rating"] = 0

    result = validate_dataframe(dataframe, FULL_MAPPING, max_rows=100)

    assert result.invalid_rating_count == 1
    assert result.out_of_range_rating_count == 2


def test_missing_optional_columns_create_warnings() -> None:
    dataframe = pd.DataFrame({"review_text": [f"Text {index}" for index in range(10)]})
    mapping = {"review_text": "review_text"}

    result = validate_dataframe(dataframe, mapping, max_rows=100)

    assert result.can_proceed
    assert set(result.missing_optional_fields) == set(FULL_MAPPING) - {"review_text"}
    assert result.warnings


def test_small_dataset_creates_warning() -> None:
    result = validate_dataframe(_valid_dataframe(rows=3), FULL_MAPPING, max_rows=100)

    assert result.can_proceed
    assert any("fewer than 10" in warning for warning in result.warnings)


def test_validation_does_not_mutate_source() -> None:
    dataframe = _valid_dataframe()
    original = dataframe.copy(deep=True)

    validate_dataframe(dataframe, FULL_MAPPING, max_rows=100)

    pd.testing.assert_frame_equal(dataframe, original)
