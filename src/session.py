"""Streamlit session-state initialization for the application shell."""

from typing import Any

import streamlit as st


SESSION_DEFAULTS: dict[str, Any] = {
    "dataset_name": None,
    "dataset_ready": False,
    "phase": 1,
}


def initialize_session_state() -> None:
    """Add Phase 1 session defaults without overwriting existing values."""
    for key, value in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value
