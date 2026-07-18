"""Deterministic pain-point exploration."""

import pandas as pd
import streamlit as st

from src.session import initialize_session_state
from src.ui import configure_page, render_app_header, render_phase_notice, render_sidebar

configure_page(page_title="Pain Points · InsightFlow AI")
initialize_session_state()
render_sidebar()
render_app_header(section="Pain Points")
st.write("Investigate recurring problems, prioritization components, and grounded evidence.")

if not st.session_state["analysis_complete"]:
    render_phase_notice("Analysis required", "Prepare feedback and select **Analyze feedback** in the sidebar.")
else:
    summary = st.session_state["theme_summary"]
    pain = summary[~summary["theme"].isin(["Positive Feedback", "Feature Request", "Other"])].copy()
    pain.insert(0, "rank", range(1, len(pain) + 1))
    columns = [
        "rank", "theme", "frequency", "share_percentage", "negative_percentage",
        "average_rating", "severity_score", "trend_score", "priority_score",
        "priority_label", "business_risk", "average_confidence",
    ]
    st.dataframe(pain[columns], width="stretch", hide_index=True)
    st.caption("Severity and priority are prioritization aids, not objective truth.")
    if pain.empty:
        st.info("No pain-point themes were detected.")
    else:
        selected = st.selectbox("Select a pain point", pain["theme"].tolist())
        record = pain[pain["theme"].eq(selected)].iloc[0]
        st.subheader(selected)
        st.write(
            f"{int(record['frequency'])} reviews ({record['share_percentage']:.1f}% of feedback) "
            f"were classified here; {record['negative_percentage']:.1f}% are negative."
        )
        st.info(record["severity_explanation"])
        st.info(record["priority_explanation"])
        if int(record["frequency"]) < 3:
            st.warning("Small sample: fewer than three matching reviews.")

        analyzed = st.session_state["analyzed_reviews"]
        matching = analyzed[analyzed["primary_theme"].eq(selected)]
        segment_cols = st.columns(3)
        for container, field, label in zip(
            segment_cols, ("platform", "app_version", "country"),
            ("Platforms", "App versions", "Countries"), strict=True,
        ):
            values = matching[field].dropna().astype(str).value_counts().head(5)
            container.markdown(f"**{label}**")
            container.write(", ".join(values.index) if not values.empty else "Not available")

        st.subheader("Representative customer quotes")
        quotes = st.session_state["representative_quotes"].get(selected, [])
        for quote in quotes:
            metadata = " · ".join(
                str(value) for value in (
                    quote["review_id"],
                    quote["date"].date().isoformat() if isinstance(quote["date"], pd.Timestamp) else quote["date"],
                    f"Rating {quote['rating']}" if quote["rating"] is not None else None,
                    quote["platform"],
                ) if value is not None
            )
            st.markdown(f"> {quote['original_text']}\n\n{metadata}")
        st.caption("Quotes shown are taken directly from the uploaded dataset.")
