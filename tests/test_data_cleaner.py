"""Tests for deterministic feedback cleaning."""

import pandas as pd

from src.data_cleaner import OUTPUT_COLUMNS, clean_feedback_data


MAPPING = {
    "review_text": "content",
    "review_id": "id",
    "date": "created_at",
    "rating": "score",
    "platform": "source",
    "app_version": None,
    "country": None,
    "device": None,
    "user_segment": None,
}


def _source_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": ["R-1", None, "R-3", "R-4", "R-5", "R-1"],
            "content": [
                "  Great   food!  ",
                "<b>Late</b> delivery https://example.com/order",
                "   ",
                "Payment failed",
                "Refund pending",
                "  Great   food!  ",
            ],
            "created_at": [
                "2025-01-01",
                "bad-date",
                "2025-01-03",
                "2025-01-04",
                "2025-01-05",
                "2025-01-01",
            ],
            "score": [5, 2, 3, "bad", 8, 5],
            "source": ["iOS", "Android", "iOS", "Android", "Android", "iOS"],
        }
    )


def test_canonical_columns_and_output_order_are_produced() -> None:
    result = clean_feedback_data(_source_dataframe(), MAPPING)

    assert tuple(result.dataframe.columns) == OUTPUT_COLUMNS
    assert result.dataframe.columns[:10].tolist() == [
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
    ]


def test_original_text_is_preserved_while_clean_text_is_normalized() -> None:
    result = clean_feedback_data(_source_dataframe(), MAPPING)

    assert result.dataframe.loc[0, "original_text"] == "  Great   food!  "
    assert result.dataframe.loc[0, "clean_text"] == "Great food!"
    assert result.dataframe.loc[1, "original_text"].startswith("<b>Late</b>")
    assert result.dataframe.loc[1, "clean_text"] == "Late delivery"


def test_blank_feedback_and_exact_duplicates_are_removed() -> None:
    result = clean_feedback_data(_source_dataframe(), MAPPING)

    assert result.report.input_rows == 6
    assert result.report.removed_duplicate_rows == 1
    assert result.report.removed_missing_feedback_rows == 1
    assert result.report.output_rows == 4


def test_invalid_dates_and_ratings_are_coerced() -> None:
    result = clean_feedback_data(_source_dataframe(), MAPPING)

    assert pd.isna(result.dataframe.loc[1, "date"])
    assert result.report.invalid_dates_coerced == 1
    assert result.dataframe["rating"].isna().sum() == 2
    assert result.report.invalid_ratings_coerced == 2


def test_missing_review_ids_are_generated() -> None:
    result = clean_feedback_data(_source_dataframe(), MAPPING)

    assert result.report.generated_review_ids == 1
    assert result.dataframe.loc[1, "review_id"].startswith("IF-")


def test_missing_optional_columns_are_created_with_null_values() -> None:
    result = clean_feedback_data(_source_dataframe(), MAPPING)

    assert result.dataframe["app_version"].isna().all()
    assert result.dataframe["country"].isna().all()
    assert result.dataframe["device"].isna().all()
    assert result.dataframe["user_segment"].isna().all()


def test_original_input_dataframe_is_not_mutated() -> None:
    dataframe = _source_dataframe()
    original = dataframe.copy(deep=True)

    clean_feedback_data(dataframe, MAPPING)

    pd.testing.assert_frame_equal(dataframe, original)
