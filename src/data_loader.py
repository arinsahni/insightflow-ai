"""CSV loading and canonical column-mapping helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
import re
from typing import BinaryIO

import pandas as pd
from pandas.errors import EmptyDataError, ParserError

from src.config import PROJECT_ROOT


EXPECTED_FIELDS: tuple[str, ...] = (
    "review_text",
    "review_id",
    "date",
    "rating",
    "platform",
    "app_version",
    "country",
    "device",
    "user_segment",
)
OPTIONAL_FIELDS: tuple[str, ...] = EXPECTED_FIELDS[1:]

COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "review_text": (
        "review_text",
        "review",
        "text",
        "feedback",
        "content",
        "comment",
        "message",
        "review_body",
    ),
    "review_id": ("review_id", "reviewid", "id", "feedback_id"),
    "date": ("date", "created_at", "timestamp", "time", "at", "submitted_at"),
    "rating": ("rating", "score", "stars", "star_rating"),
    "platform": ("platform", "source", "channel", "os"),
    "app_version": ("app_version", "version", "appversion"),
    "country": ("country", "region", "location", "city"),
    "device": ("device", "device_type", "handset"),
    "user_segment": ("user_segment", "segment", "customer_segment", "user_type"),
}


@dataclass(slots=True)
class LoadResult:
    """Friendly result returned by CSV loading operations."""

    dataframe: pd.DataFrame | None = None
    filename: str | None = None
    encoding: str | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_success(self) -> bool:
        """Return whether a non-empty DataFrame was loaded."""
        return self.dataframe is not None and not self.errors


def normalize_column_name(name: object) -> str:
    """Normalize a source column name for alias matching."""
    value = str(name).strip().lower()
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", value)).strip("_")


def suggest_column_mapping(columns: list[object] | pd.Index) -> dict[str, str | None]:
    """Suggest a unique source column for every canonical field."""
    source_columns = [str(column) for column in columns]
    normalized_sources: dict[str, list[str]] = {}
    for source in source_columns:
        normalized_sources.setdefault(normalize_column_name(source), []).append(source)

    mapping: dict[str, str | None] = {}
    used: set[str] = set()
    for field_name in EXPECTED_FIELDS:
        suggestion = None
        for alias in COLUMN_ALIASES[field_name]:
            candidates = normalized_sources.get(normalize_column_name(alias), [])
            suggestion = next((candidate for candidate in candidates if candidate not in used), None)
            if suggestion is not None:
                break
        mapping[field_name] = suggestion
        if suggestion is not None:
            used.add(suggestion)
    return mapping


def mapping_has_unique_sources(mapping: dict[str, str | None]) -> bool:
    """Return whether each mapped source column is used at most once."""
    selected = [source for source in mapping.values() if source]
    return len(selected) == len(set(selected))


def read_csv_safely(
    content: bytes,
    *,
    filename: str,
    max_rows: int,
) -> LoadResult:
    """Read CSV bytes with encoding fallbacks and a strict row limit."""
    if not filename.lower().endswith(".csv"):
        return LoadResult(filename=filename, errors=["Please select a CSV file."])
    if not content or not content.strip():
        return LoadResult(filename=filename, errors=["The CSV file is empty."])

    encoding_errors: list[str] = []
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            dataframe = pd.read_csv(
                BytesIO(content),
                encoding=encoding,
                nrows=max_rows + 1,
                low_memory=False,
            )
        except UnicodeDecodeError:
            encoding_errors.append(encoding)
            continue
        except EmptyDataError:
            return LoadResult(filename=filename, errors=["The CSV file contains no data."])
        except ParserError:
            return LoadResult(
                filename=filename,
                errors=["The CSV structure is malformed and could not be read safely."],
            )
        except (OSError, ValueError):
            return LoadResult(
                filename=filename,
                errors=["The CSV file could not be read. Check its format and try again."],
            )

        if dataframe.empty:
            return LoadResult(filename=filename, encoding=encoding, errors=["The CSV contains no rows."])
        if len(dataframe) > max_rows:
            return LoadResult(
                filename=filename,
                encoding=encoding,
                errors=[
                    f"The CSV exceeds the configured limit of {max_rows:,} rows. "
                    "No rows were loaded."
                ],
            )
        warnings = []
        if encoding == "latin-1":
            warnings.append("The file was read using Latin-1 encoding.")
        return LoadResult(
            dataframe=dataframe,
            filename=filename,
            encoding=encoding,
            warnings=warnings,
        )

    return LoadResult(
        filename=filename,
        errors=[
            "The CSV encoding is unsupported. Save the file as UTF-8 and try again."
            if encoding_errors
            else "The CSV file could not be read."
        ],
    )


def load_uploaded_csv(
    uploaded_file: BinaryIO,
    *,
    filename: str | None = None,
    max_rows: int,
) -> LoadResult:
    """Load an uploaded CSV-like binary object without exposing exceptions."""
    resolved_name = filename or str(getattr(uploaded_file, "name", "uploaded.csv"))
    try:
        if hasattr(uploaded_file, "getvalue"):
            content = uploaded_file.getvalue()
        else:
            uploaded_file.seek(0)
            content = uploaded_file.read()
    except (AttributeError, OSError, ValueError):
        return LoadResult(filename=resolved_name, errors=["The uploaded file could not be accessed."])

    if isinstance(content, str):
        content = content.encode("utf-8")
    return read_csv_safely(content, filename=resolved_name, max_rows=max_rows)


def load_sample_data(
    *,
    max_rows: int,
    sample_path: Path | None = None,
) -> LoadResult:
    """Load the bundled fictional sample dataset."""
    path = sample_path or PROJECT_ROOT / "data" / "sample_reviews.csv"
    try:
        content = path.read_bytes()
    except OSError:
        return LoadResult(
            filename=path.name,
            errors=["The bundled sample dataset is unavailable."],
        )
    return read_csv_safely(content, filename=path.name, max_rows=max_rows)
