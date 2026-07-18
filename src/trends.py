"""Date-aware feedback trend calculations with conservative safeguards."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass(slots=True)
class TrendOutputs:
    """Reusable time-series and theme trend outputs."""

    daily_volume: pd.DataFrame = field(default_factory=pd.DataFrame)
    weekly_volume: pd.DataFrame = field(default_factory=pd.DataFrame)
    daily_negative_percentage: pd.DataFrame = field(default_factory=pd.DataFrame)
    weekly_negative_percentage: pd.DataFrame = field(default_factory=pd.DataFrame)
    theme_volume: pd.DataFrame = field(default_factory=pd.DataFrame)
    theme_trends: pd.DataFrame = field(default_factory=pd.DataFrame)
    fastest_growing_theme: str | None = None
    warnings: list[str] = field(default_factory=list)


def _empty_outputs(message: str) -> TrendOutputs:
    """Create neutral trend output with an explanatory warning."""
    return TrendOutputs(warnings=[message])


def calculate_trends(dataframe: pd.DataFrame, *, period_days: int = 14) -> TrendOutputs:
    """Calculate bounded recent-versus-previous trends from valid dated rows."""
    if dataframe.empty or "date" not in dataframe:
        return _empty_outputs("Trends require usable date data.")
    dated = dataframe.copy()
    dated["date"] = pd.to_datetime(dated["date"], errors="coerce")
    dated = dated.dropna(subset=["date"])
    if dated.empty:
        return _empty_outputs("Trends require usable date data.")

    dated["day"] = dated["date"].dt.normalize()
    coverage_days = int((dated["day"].max() - dated["day"].min()).days) + 1
    daily = dated.groupby("day").size().rename("feedback_count").reset_index()
    weekly = (
        dated.set_index("day").resample("W-MON").size().rename("feedback_count").reset_index()
    )
    negative = dated["sentiment"].eq("Negative").astype(float)
    daily_negative = (
        dated.assign(_negative=negative)
        .groupby("day")["_negative"].mean().mul(100)
        .rename("negative_percentage").reset_index()
    )
    weekly_negative = (
        dated.assign(_negative=negative).set_index("day")["_negative"]
        .resample("W-MON").mean().mul(100).rename("negative_percentage").reset_index()
    )
    theme_volume = (
        dated.groupby(["day", "primary_theme"]).size().rename("feedback_count").reset_index()
    )
    if coverage_days < 14:
        themes = sorted(dated["primary_theme"].dropna().unique())
        theme_trends = pd.DataFrame({
            "theme": themes, "recent_count": 0, "previous_count": 0,
            "growth_rate": 0.0, "trend_score": 50.0, "issue_velocity": 0.0,
        })
        return TrendOutputs(
            daily, weekly, daily_negative, weekly_negative, theme_volume, theme_trends,
            warnings=["Fewer than 14 days of usable coverage; trend scores are neutral."],
        )

    end = dated["day"].max()
    recent_start = end - pd.Timedelta(days=period_days - 1)
    previous_start = recent_start - pd.Timedelta(days=period_days)
    recent = dated[dated["day"].between(recent_start, end)]
    previous = dated[dated["day"].between(previous_start, recent_start - pd.Timedelta(days=1))]
    themes = sorted(dated["primary_theme"].dropna().unique())
    rows = []
    for theme in themes:
        recent_count = int(recent["primary_theme"].eq(theme).sum())
        previous_count = int(previous["primary_theme"].eq(theme).sum())
        smoothed_growth = (recent_count - previous_count) / (previous_count + 1)
        capped_growth = float(np.clip(smoothed_growth, -1.0, 1.0))
        rows.append({
            "theme": theme,
            "recent_count": recent_count,
            "previous_count": previous_count,
            "growth_rate": capped_growth,
            "trend_score": float(np.clip(50 + 50 * capped_growth, 0, 100)),
            "issue_velocity": (recent_count - previous_count) / period_days,
        })
    theme_trends = pd.DataFrame(rows)
    pain_trends = theme_trends[
        ~theme_trends["theme"].isin(["Positive Feedback", "Feature Request", "Other"])
    ]
    fastest = (
        pain_trends.sort_values(["trend_score", "recent_count", "theme"], ascending=[False, False, True])
        .iloc[0]["theme"] if not pain_trends.empty else None
    )
    return TrendOutputs(
        daily, weekly, daily_negative, weekly_negative, theme_volume,
        theme_trends, fastest, [],
    )
