"""Streamlit entry point for InsightFlow AI."""

import streamlit as st

from src.session import initialize_session_state
from src.ui import configure_page, render_app_header, render_phase_notice, render_sidebar


def main() -> None:
    """Render the Phase 1 landing page."""
    configure_page(page_title="InsightFlow AI")
    initialize_session_state()
    render_sidebar()
    render_app_header()

    st.markdown(
        """
        InsightFlow AI is the workspace for turning customer feedback into
        evidence-backed product decisions. The foundation is ready; data
        processing and analytics will be introduced in their dedicated phases.
        """
    )
    render_phase_notice(
        "Foundation ready",
        "Use the sidebar to open each product area. No customer metrics are "
        "displayed until a dataset has been processed in a later phase.",
    )

    st.subheader("Planned workflow")
    columns = st.columns(3)
    steps = (
        ("1. Bring feedback", "Upload a CSV or load the fictional sample dataset."),
        ("2. Review evidence", "Inspect validated themes, trends, segments, and source quotes."),
        ("3. Decide together", "Review recommendations, experiments, and exports with human judgment."),
    )
    for column, (title, body) in zip(columns, steps, strict=True):
        with column:
            st.markdown(f"#### {title}")
            st.caption(body)


if __name__ == "__main__":
    main()
