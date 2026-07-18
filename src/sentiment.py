"""Transparent local sentiment analysis using VADER and optional ratings."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import numpy as np
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


@dataclass(frozen=True, slots=True)
class SentimentResult:
    """Sentiment outputs for one feedback item."""

    sentiment: str
    sentiment_score: float
    negativity_score: float
    sentiment_method: str


@lru_cache(maxsize=1)
def get_sentiment_analyzer() -> SentimentIntensityAnalyzer:
    """Return one reusable local VADER analyzer."""
    return SentimentIntensityAnalyzer()


def analyze_sentiment(text: object, rating: object = None) -> SentimentResult:
    """Classify one review using text polarity plus a transparent rating adjustment."""
    if text is None or pd.isna(text) or not str(text).strip():
        return SentimentResult("Neutral", 0.0, 0.0, "safe_neutral")

    normalized = str(text).strip()
    lowered = normalized.lower()
    vader_score = float(get_sentiment_analyzer().polarity_scores(normalized)["compound"])
    keyword_score: float | None = None
    if lowered in {"bad", "terrible", "awful", "not working", "broken"}:
        keyword_score = -0.8
    elif lowered in {"great", "excellent", "amazing", "love it", "good"}:
        keyword_score = 0.8
    elif lowered in {"okay", "ok", "fine", "average"}:
        keyword_score = 0.0
    elif "not working" in lowered or "doesn't work" in lowered or "does not work" in lowered:
        keyword_score = min(vader_score, -0.7)

    text_score = keyword_score if keyword_score is not None else vader_score
    numeric_rating = pd.to_numeric(pd.Series([rating]), errors="coerce").iloc[0]
    valid_rating = pd.notna(numeric_rating) and 1 <= float(numeric_rating) <= 5

    if valid_rating:
        rating_score = {1: -1.0, 2: -0.65, 3: 0.0, 4: 0.65, 5: 1.0}[int(round(float(numeric_rating)))]
        score = 0.55 * text_score + 0.45 * rating_score
        if numeric_rating <= 2:
            score = min(score, -0.35)
        elif numeric_rating >= 4:
            score = max(score, 0.25)
        elif numeric_rating == 3 and abs(text_score) < 0.6:
            score = 0.5 * text_score
        method = "keyword_rating_hybrid" if keyword_score is not None else "vader_rating_hybrid"
    else:
        score = text_score
        method = "keyword" if keyword_score is not None else "vader"

    score = float(np.clip(score, -1.0, 1.0))
    label = "Positive" if score >= 0.25 else "Negative" if score <= -0.25 else "Neutral"
    return SentimentResult(label, score, float(np.clip(-score, 0.0, 1.0)), method)


def add_sentiment_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with local sentiment outputs for every review."""
    output = dataframe.copy()
    ratings = output["rating"] if "rating" in output else pd.Series(pd.NA, index=output.index)
    results = [
        analyze_sentiment(text, rating)
        for text, rating in zip(output["clean_text"], ratings, strict=True)
    ]
    output["sentiment"] = [result.sentiment for result in results]
    output["sentiment_score"] = [result.sentiment_score for result in results]
    output["negativity_score"] = [result.negativity_score for result in results]
    output["sentiment_method"] = [result.sentiment_method for result in results]
    return output
