"""Phase 2 dataset overview and preparation audit."""

from datetime import date

import streamlit as st

from src.session import initialize_session_state
from src.ui import (
    configure_page,
    render_app_header,
    render_cleaning_report,
    render_phase_notice,
    render_sidebar,
    render_validation_summary,
)


configure_page(page_title="Overview · InsightFlow AI")
initialize_session_state()
render_sidebar()
render_app_header(section="Overview")
st.write("Review loaded feedback, validation findings, and the cleaned canonical dataset.")

if not st.session_state["data_loaded"]:
    render_phase_notice(
        "No feedback loaded",
        "Upload a CSV or choose **Load sample data** in the sidebar to begin.",
    )
elif not st.session_state["data_processed"]:
    dataframe = st.session_state["source_dataframe"]
    st.subheader("Raw data preview")
    first, second = st.columns(2)
    first.metric("Rows", f"{len(dataframe):,}")
    second.metric("Columns", f"{len(dataframe.columns):,}")
    st.dataframe(dataframe.head(25), width="stretch", hide_index=True)

    st.subheader("Current mapping")
    mapping_rows = [
        {"Expected field": field_name, "Source column": source or "Not mapped"}
        for field_name, source in st.session_state["column_mapping"].items()
    ]
    st.dataframe(mapping_rows, width="stretch", hide_index=True)

    validation_result = st.session_state.get("validation_result")
    if validation_result is None:
        render_phase_notice(
            "Validation not run",
            "Confirm the sidebar mapping and select **Validate data**.",
        )
    else:
        st.subheader("Validation summary")
        render_validation_summary(validation_result)
else:
    cleaned_reviews = st.session_state["cleaned_reviews"]
    cleaning_report = st.session_state["cleaning_report"]
    st.success("The cleaned dataset is ready for review and download.")
    st.subheader("Cleaning report")
    render_cleaning_report(cleaning_report)

    st.subheader("Cleaned data preview")
    st.dataframe(cleaned_reviews.head(50), width="stretch", hide_index=True)
    csv_data = cleaned_reviews.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download cleaned CSV",
        data=csv_data,
        file_name=f"insightflow_cleaned_reviews_{date.today().isoformat()}.csv",
        mime="text/csv",
        width="stretch",
    )
    st.caption("No sentiment, themes, scores, or analytics have been added in Phase 2.")
