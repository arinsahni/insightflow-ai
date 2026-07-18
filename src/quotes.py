"""Grounded representative quote selection."""

from __future__ import annotations

import pandas as pd


QUOTE_FIELDS = ("review_id", "original_text", "date", "rating", "platform", "primary_theme")


def select_representative_quotes(
    dataframe: pd.DataFrame,
    theme: str,
    *,
    limit: int = 5,
) -> list[dict[str, object]]:
    """Return deterministic, non-paraphrased source reviews for one theme."""
    if dataframe.empty or limit <= 0:
        return []
    candidates = dataframe[dataframe["primary_theme"].eq(theme)].copy()
    if candidates.empty:
        return []
    candidates["_quote_key"] = candidates["original_text"].astype("string").str.strip()
    candidates = candidates[candidates["_quote_key"].ne("")].drop_duplicates("_quote_key")
    desired_sentiment = "Positive" if theme == "Positive Feedback" else "Negative"
    candidates["_sentiment_rank"] = candidates["sentiment"].eq(desired_sentiment).astype(int)
    candidates["_clarity"] = candidates["_quote_key"].str.len().between(20, 400).astype(int)
    candidates = candidates.sort_values(
        ["_sentiment_rank", "classification_confidence", "_clarity", "review_id"],
        ascending=[False, False, False, True],
    ).head(min(limit, 5))
    records = []
    for row in candidates.itertuples(index=False):
        record = {}
        for field in QUOTE_FIELDS:
            value = getattr(row, field)
            record[field] = None if pd.isna(value) else value
        records.append(record)
    return records


def build_quote_index(
    dataframe: pd.DataFrame,
    *,
    limit_per_theme: int = 5,
) -> dict[str, list[dict[str, object]]]:
    """Build representative quotes for every detected theme."""
    return {
        str(theme): select_representative_quotes(
            dataframe, str(theme), limit=limit_per_theme
        )
        for theme in sorted(dataframe["primary_theme"].dropna().unique())
    }


def quotes_are_grounded(
    dataframe: pd.DataFrame,
    quote_index: dict[str, list[dict[str, object]]],
) -> bool:
    """Check that every quote text/ID pair exists in its assigned source theme."""
    source = {
        (str(row.review_id), str(row.original_text), str(row.primary_theme))
        for row in dataframe.itertuples()
    }
    return all(
        (str(quote["review_id"]), str(quote["original_text"]), theme) in source
        for theme, quotes in quote_index.items()
        for quote in quotes
    )
