"""Tests for safe CSV loading and mapping suggestions."""

from io import BytesIO

from src.data_loader import (
    load_sample_data,
    load_uploaded_csv,
    suggest_column_mapping,
)


def _upload(content: bytes, name: str = "reviews.csv") -> BytesIO:
    """Create a named in-memory upload."""
    upload = BytesIO(content)
    upload.name = name
    return upload


def test_valid_csv_loads_and_preserves_columns() -> None:
    result = load_uploaded_csv(
        _upload(b"content,score\nGreat app,5\nNeeds work,2\n"),
        max_rows=100,
    )

    assert result.is_success
    assert result.dataframe is not None
    assert list(result.dataframe.columns) == ["content", "score"]
    assert len(result.dataframe) == 2


def test_empty_csv_fails() -> None:
    result = load_uploaded_csv(_upload(b""), max_rows=100)

    assert not result.is_success
    assert "empty" in result.errors[0].lower()


def test_header_only_csv_fails() -> None:
    result = load_uploaded_csv(_upload(b"review_text,rating\n"), max_rows=100)

    assert not result.is_success
    assert "no rows" in result.errors[0].lower()


def test_non_csv_filename_fails() -> None:
    result = load_uploaded_csv(
        _upload(b"review_text\nGood\n", name="reviews.txt"),
        max_rows=100,
    )

    assert not result.is_success
    assert "csv" in result.errors[0].lower()


def test_oversized_dataset_fails_without_returning_partial_data() -> None:
    result = load_uploaded_csv(
        _upload(b"review_text\none\ntwo\nthree\n"),
        max_rows=2,
    )

    assert not result.is_success
    assert result.dataframe is None
    assert "limit" in result.errors[0].lower()


def test_sample_data_loads() -> None:
    result = load_sample_data(max_rows=50_000)

    assert result.is_success
    assert result.dataframe is not None
    assert len(result.dataframe) >= 300
    assert "review_text" in result.dataframe.columns


def test_common_aliases_receive_unique_suggestions() -> None:
    mapping = suggest_column_mapping(["content", "score", "at", "source", "id"])

    assert mapping["review_text"] == "content"
    assert mapping["rating"] == "score"
    assert mapping["date"] == "at"
    assert mapping["platform"] == "source"
    assert mapping["review_id"] == "id"
    selected = [source for source in mapping.values() if source]
    assert len(selected) == len(set(selected))
