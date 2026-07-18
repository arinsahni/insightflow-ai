"""Detected and grounded feature requests."""

from datetime import date

import streamlit as st

from src.session import initialize_session_state
from src.ui import configure_page, render_app_header, render_phase_notice, render_sidebar

configure_page(page_title="Feature Requests · InsightFlow AI")
initialize_session_state()
render_sidebar()
render_app_header(section="Feature Requests")
st.write("Explore explicit customer requests grouped by requested capability.")

if not st.session_state["analysis_complete"]:
    render_phase_notice("Analysis required", "Prepare feedback and select **Analyze feedback** in the sidebar.")
else:
    analyzed = st.session_state["analyzed_reviews"]
    requests = analyzed[analyzed["is_feature_request"]].copy()
    summary = st.session_state["feature_request_summary"]
    st.metric("Total feature requests", f"{len(requests):,}")
    if requests.empty:
        st.info("No explicit feature-request intent was detected.")
    else:
        st.subheader("Grouped requests")
        st.dataframe(summary, width="stretch", hide_index=True)
        selected = st.selectbox("Select a request group", summary["feature_request_group"].tolist())
        matching = requests[requests["feature_request_group"].eq(selected)]
        st.subheader(selected)
        detail = summary[summary["feature_request_group"].eq(selected)].iloc[0]
        st.write(
            f"{int(detail['mentions'])} mentions ({detail['share_percentage']:.1f}% of all feedback), "
            f"with average request confidence {detail['request_confidence']:.2f}."
        )
        left, right = st.columns(2)
        left.markdown("**Affected platforms**")
        left.write(", ".join(matching["platform"].dropna().astype(str).value_counts().head(5).index) or "Not available")
        right.markdown("**Affected user segments**")
        right.write(", ".join(matching["user_segment"].dropna().astype(str).value_counts().head(5).index) or "Not available")
        st.subheader("Representative customer quotes")
        quote_rows = (
            matching.sort_values(["feature_request_confidence", "review_id"], ascending=[False, True])
            .drop_duplicates("original_text").head(5)
        )
        for row in quote_rows.itertuples():
            st.markdown(f"> {row.original_text}\n\n{row.review_id}")
        st.caption("Quotes shown are taken directly from the uploaded dataset.")
        st.download_button(
            "Download feature requests CSV",
            requests.to_csv(index=False).encode("utf-8"),
            file_name=f"insightflow_feature_requests_{date.today().isoformat()}.csv",
            mime="text/csv",
            width="stretch",
        )
