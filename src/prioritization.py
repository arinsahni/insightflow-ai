"""Explainable severity and priority calculations."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.taxonomy import BUSINESS_RISK_SCORES


@dataclass(frozen=True, slots=True)
class PriorityResult:
    """All bounded components and explanations for one theme."""

    severity_score: float
    priority_score: float
    priority_label: str
    frequency_component: float
    negative_component: float
    rating_component: float
    trend_component: float
    critical_keyword_component: float
    business_risk_component: float
    confidence_component: float
    severity_explanation: str
    priority_explanation: str


def clamp_score(value: float) -> float:
    """Clamp a numeric score to 0–100."""
    return float(np.clip(value, 0.0, 100.0))


def priority_label(score: float) -> str:
    """Map a bounded score to the documented priority bands."""
    score = clamp_score(score)
    return "P0 Critical" if score >= 80 else "P1 High" if score >= 60 else "P2 Medium" if score >= 40 else "P3 Low"


def calculate_priority(
    *,
    frequency_component: float,
    negative_component: float,
    average_rating: float | None,
    trend_component: float,
    critical_keyword_component: float,
    business_risk: str,
    confidence_component: float,
    rare_critical: bool = False,
) -> PriorityResult:
    """Calculate severity and priority with a transparent rare-critical floor."""
    frequency = clamp_score(frequency_component)
    negative = clamp_score(negative_component)
    rating = 50.0 if average_rating is None or np.isnan(average_rating) else clamp_score((5 - average_rating) / 4 * 100)
    trend = clamp_score(trend_component)
    critical = clamp_score(critical_keyword_component)
    risk = clamp_score(BUSINESS_RISK_SCORES.get(business_risk, 50.0))
    confidence = clamp_score(confidence_component)
    severity = clamp_score(0.30 * negative + 0.25 * rating + 0.20 * frequency + 0.15 * trend + 0.10 * critical)
    priority = clamp_score(0.30 * frequency + 0.30 * severity + 0.20 * trend + 0.10 * risk + 0.10 * confidence)
    if rare_critical:
        severity = max(severity, 70.0)
        priority = max(priority, 60.0)
    return PriorityResult(
        severity, priority, priority_label(priority), frequency, negative, rating,
        trend, critical, risk, confidence,
        f"Severity combines negative sentiment ({negative:.1f}), rating impact ({rating:.1f}), frequency ({frequency:.1f}), trend ({trend:.1f}), and critical terms ({critical:.1f}).",
        f"Priority combines frequency ({frequency:.1f}), severity ({severity:.1f}), trend ({trend:.1f}), business risk ({risk:.1f}), and confidence ({confidence:.1f})"
        + (" with a rare-critical safeguard." if rare_critical else "."),
    )
