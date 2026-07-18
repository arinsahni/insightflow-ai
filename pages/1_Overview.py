"""Phase 3 feedback analysis overview."""

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
elif not st.session_state["analysis_complete"]:
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
    render_phase_notice(
        "Ready for analysis",
        "Select **Analyze feedback** in the sidebar to calculate local metrics.",
    )
else:
    metrics = st.session_state["overall_metrics"]
    themes = st.session_state["theme_summary"]
    analyzed = st.session_state["analyzed_reviews"]
    st.success("Local analysis is complete. No API key was used.")
    cards = st.columns(6)
    cards[0].metric("Feedback", f"{metrics.total_feedback_items:,}")
    cards[1].metric("Average rating", f"{metrics.average_rating:.2f}" if metrics.average_rating is not None else "N/A")
    cards[2].metric("Negative feedback", f"{metrics.negative_feedback_percentage:.1f}%")
    cards[3].metric("Feature requests", f"{metrics.feature_request_count:,}")
    cards[4].metric("Top pain point", metrics.most_frequent_pain_point or "N/A")
    cards[5].metric("Fastest-growing issue", metrics.fastest_growing_pain_point or "Insufficient data")

    st.subheader("Sentiment distribution")
    sentiment = (
        analyzed["sentiment"].value_counts().rename_axis("sentiment").reset_index(name="count")
    )
    sentiment["percentage"] = sentiment["count"] / len(analyzed) * 100
    st.dataframe(sentiment, width="stretch", hide_index=True)

    left, right = st.columns(2)
    with left:
        st.subheader("Top themes")
        st.dataframe(
            themes[["theme", "frequency", "share_percentage", "negative_percentage"]].head(10),
            width="stretch", hide_index=True,
        )
    with right:
        st.subheader("Priority summary")
        priority_themes = themes[
            ~themes["theme"].isin(["Positive Feedback", "Feature Request", "Other"])
        ]
        st.dataframe(
            priority_themes[["theme", "severity_score", "priority_score", "priority_label", "business_risk"]].head(10),
            width="stretch", hide_index=True,
        )
    for warning in st.session_state["analytics_warnings"]:
        st.warning(warning)
    st.caption("Severity and priority are prioritization aids, not objective truth.")
