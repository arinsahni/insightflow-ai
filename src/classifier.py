"""Deterministic taxonomy classification with TF-IDF fallback."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import re

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.taxonomy import TAXONOMY, TaxonomyRule


@dataclass(frozen=True, slots=True)
class ClassificationResult:
    """Theme classification outputs for one review."""

    primary_theme: str
    secondary_theme: str | None
    subtheme: str
    classification_confidence: float
    classification_method: str


def _contains(text: str, term: str) -> bool:
    """Match phrases or whole keyword tokens deterministically."""
    return term in text if " " in term or "-" in term else bool(re.search(rf"\b{re.escape(term)}\b", text))


def _rule_matches(text: str) -> list[tuple[float, TaxonomyRule, str]]:
    """Return scored taxonomy matches, strongest first."""
    matches: list[tuple[float, TaxonomyRule, str]] = []
    for rule in TAXONOMY:
        if rule.theme == "Other":
            continue
        phrase_hits = sum(_contains(text, phrase) for phrase in rule.phrases)
        keyword_hits = sum(_contains(text, keyword) for keyword in rule.keywords)
        if phrase_hits or keyword_hits:
            score = 3.0 * phrase_hits + keyword_hits
            method = "rule_exact_phrase" if phrase_hits else "rule_keyword"
            matches.append((score, rule, method))
    return sorted(matches, key=lambda item: (-item[0], TAXONOMY.index(item[1])))


@lru_cache(maxsize=1)
def _tfidf_resources() -> tuple[TfidfVectorizer, object]:
    """Build reusable taxonomy reference vectors, never sample-trained vectors."""
    references = [
        " ".join((rule.theme, rule.subtheme, *rule.phrases, *rule.keywords))
        for rule in TAXONOMY
        if rule.theme != "Other"
    ]
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), lowercase=True, sublinear_tf=True)
    return vectorizer, vectorizer.fit_transform(references)


def classify_review(text: object, sentiment: str | None = None) -> ClassificationResult:
    """Classify one review using rules, then taxonomy-only TF-IDF similarity."""
    if text is None or pd.isna(text) or not str(text).strip():
        return ClassificationResult("Other", None, "Ambiguous", 0.1, "fallback_other")
    lowered = re.sub(r"\s+", " ", str(text).lower()).strip()
    matches = _rule_matches(lowered)
    if matches:
        top_score, top_rule, method = matches[0]
        secondary = next(
            (rule.theme for _, rule, _ in matches[1:] if rule.theme != top_rule.theme),
            None,
        )
        confidence = min(0.98, 0.62 + 0.09 * top_score)
        return ClassificationResult(top_rule.theme, secondary, top_rule.subtheme, confidence, method)

    vectorizer, reference_matrix = _tfidf_resources()
    similarities = cosine_similarity(vectorizer.transform([lowered]), reference_matrix)[0]
    best_index = int(np.argmax(similarities))
    best_score = float(similarities[best_index])
    reference_rules = [rule for rule in TAXONOMY if rule.theme != "Other"]
    if best_score >= 0.16:
        rule = reference_rules[best_index]
        return ClassificationResult(
            rule.theme, None, rule.subtheme, min(0.7, 0.35 + best_score), "tfidf_similarity"
        )
    if sentiment == "Positive":
        return ClassificationResult(
            "Positive Feedback", None, "General praise", 0.55, "fallback_positive"
        )
    return ClassificationResult("Other", None, "Ambiguous", 0.2, "fallback_other")


def add_classification_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with deterministic taxonomy classification fields."""
    output = dataframe.copy()
    sentiments = output.get("sentiment", pd.Series(None, index=output.index))
    results = []
    for index, (text, sentiment) in enumerate(
        zip(output["clean_text"], sentiments, strict=True)
    ):
        if "is_feature_request" in output and bool(output["is_feature_request"].iloc[index]):
            group = output["feature_request_group"].iloc[index]
            results.append(ClassificationResult(
                "Feature Request", None,
                str(group) if pd.notna(group) else "Other requested capability",
                max(0.8, float(output["feature_request_confidence"].iloc[index])),
                "rule_exact_phrase",
            ))
        else:
            results.append(classify_review(text, sentiment))
    output["primary_theme"] = [result.primary_theme for result in results]
    output["secondary_theme"] = [result.secondary_theme for result in results]
    output["subtheme"] = [result.subtheme for result in results]
    output["classification_confidence"] = [
        result.classification_confidence for result in results
    ]
    output["classification_method"] = [result.classification_method for result in results]
    return output
