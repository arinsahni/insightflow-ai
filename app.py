"""Streamlit entry point for InsightFlow AI."""

import streamlit as st

from src.session import initialize_session_state
from src.ui import configure_page, render_app_header, render_phase_notice, render_sidebar


def main() -> None:
    """Render the Phase 3 landing page."""
    configure_page(page_title="InsightFlow AI")
    initialize_session_state()
    render_sidebar()
    render_app_header()

    st.markdown(
        """
        InsightFlow AI is the workspace for turning customer feedback into
        evidence-backed product decisions. Upload a CSV or load the bundled
        sample, prepare it, then run transparent local product analytics.
        """
    )
    if st.session_state["analysis_complete"]:
        render_phase_notice(
            "Analysis ready",
            "Open Overview, Pain Points, or Feature Requests to inspect measured results and source quotes.",
        )
    elif st.session_state["data_processed"]:
        render_phase_notice(
            "Clean dataset ready",
            "Select **Analyze feedback** in the sidebar to run local sentiment, themes, trends, and prioritization.",
        )
    elif st.session_state["data_loaded"]:
        render_phase_notice(
            "Dataset loaded",
            "Complete the column mapping, validation, and cleaning controls in the sidebar.",
        )
    else:
        render_phase_notice(
            "Start with feedback data",
            "Use the sidebar to upload a CSV or load the fictional sample dataset.",
        )

    st.subheader("Local analysis workflow")
    columns = st.columns(3)
    steps = (
        ("1. Bring feedback", "Upload a CSV or load the fictional sample dataset."),
        ("2. Map and validate", "Confirm the feedback field and review recoverable data issues."),
        ("3. Analyze locally", "Measure sentiment, themes, requests, trends, and priorities without an API."),
    )
    for column, (title, body) in zip(columns, steps, strict=True):
        with column:
            st.markdown(f"#### {title}")
            st.caption(body)


if __name__ == "__main__":
    main()
