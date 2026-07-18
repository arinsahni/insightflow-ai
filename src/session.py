"""Streamlit session-state management for the feedback pipeline."""

from typing import Any

import streamlit as st


SESSION_DEFAULTS: dict[str, Any] = {
    "source_dataframe": None,
    "uploaded_filename": None,
    "column_mapping": {},
    "validation_result": None,
    "cleaned_reviews": None,
    "cleaning_report": None,
    "analyzed_reviews": None,
    "overall_metrics": None,
    "theme_summary": None,
    "feature_request_summary": None,
    "trend_summary": None,
    "representative_quotes": {},
    "analytics_warnings": [],
    "analytics_processing_time": None,
    "data_loaded": False,
    "data_processed": False,
    "analysis_complete": False,
    "processing_error": None,
    "source_signature": None,
    "uploader_generation": 0,
    "phase": 3,
}


def initialize_session_state() -> None:
    """Add data-pipeline defaults without overwriting normal rerun state."""
    for key, value in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_data_state() -> None:
    """Clear loaded and processed data while preserving unrelated UI state."""
    next_generation = int(st.session_state.get("uploader_generation", 0)) + 1
    for key, value in SESSION_DEFAULTS.items():
        st.session_state[key] = value.copy() if isinstance(value, dict) else value
    st.session_state["uploader_generation"] = next_generation
