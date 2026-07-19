"""Deterministic global filtering for analyzed feedback."""

from __future__ import annotations

from typing import Any

import pandas as pd


FILTER_COLUMNS: dict[str, str] = {
    "platform": "platform",
    "rating": "rating",
    "country": "country",
    "device": "device",
    "app_version": "app_version",
    "primary_theme": "primary_theme",
    "sentiment": "sentiment",
    "user_segment": "user_segment",
}


def default_filters() -> dict[str, Any]:
    """Return an empty filter-state contract."""
    return {"date_range": None, **{key: [] for key in FILTER_COLUMNS}}


def build_filter_options(dataframe: pd.DataFrame) -> dict[str, Any]:
    """Build sorted usable options only for available columns."""
    options: dict[str, Any] = {}
    if "date" in dataframe:
        dates = pd.to_datetime(dataframe["date"], errors="coerce").dropna()
        if not dates.empty:
            options["date_range"] = (dates.min().date(), dates.max().date())
    for key, column in FILTER_COLUMNS.items():
        if column not in dataframe:
            continue
        values = dataframe[column].dropna().unique().tolist()
        if values:
            options[key] = sorted(values, key=lambda value: str(value))
    return options


def apply_filters(dataframe: pd.DataFrame, filters: dict[str, Any] | None) -> pd.DataFrame:
    """Return a filtered copy without mutating the analyzed source."""
    if dataframe.empty or not filters:
        return dataframe.copy()
    mask = pd.Series(True, index=dataframe.index)
    date_range = filters.get("date_range")
    if date_range and "date" in dataframe:
        dates = pd.to_datetime(dataframe["date"], errors="coerce")
        start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
        mask &= dates.between(start, end)
    for key, column in FILTER_COLUMNS.items():
        selected = filters.get(key) or []
        if selected and column in dataframe:
            mask &= dataframe[column].isin(selected)
    return dataframe.loc[mask].copy()


def summarize_active_filters(filters: dict[str, Any] | None) -> str:
    """Return a compact reader-facing active-filter description."""
    if not filters:
        return "No active filters"
    parts = []
    if filters.get("date_range"):
        start, end = filters["date_range"]
        parts.append(f"Date: {start} to {end}")
    for key in FILTER_COLUMNS:
        values = filters.get(key) or []
        if values:
            parts.append(f"{key.replace('_', ' ').title()}: {', '.join(map(str, values))}")
    return " · ".join(parts) if parts else "No active filters"


def reset_filters() -> dict[str, Any]:
    """Return fresh filter defaults."""
    return default_filters()
