"""Filtered pain-point ranking and drill-down."""

from datetime import date

import pandas as pd
import streamlit as st

from src.dashboard_formatting import curated_feedback_table
from src.quotes import select_representative_quotes
from src.session import initialize_session_state
from src.trends import calculate_trends
from src.ui import configure_page, render_app_header, render_kpi_cards, render_phase_notice, render_quote_card, render_sidebar
from src.visualizations import theme_trend_chart

configure_page(page_title="Pain Points · InsightFlow AI")
initialize_session_state()
render_sidebar()
render_app_header(section="Pain Points")
st.caption("Severity and priority are prioritization aids, not objective truth.")

if not st.session_state["analysis_complete"]:
    render_phase_notice("Analysis required", "Prepare and analyze feedback from the sidebar.")
else:
    reviews = st.session_state["filtered_reviews"]
    themes = st.session_state["filtered_theme_summary"]
    pain = themes[~themes["theme"].isin(["Positive Feedback", "Feature Request", "Other"])].copy() if themes is not None and not themes.empty else pd.DataFrame()
    if pain.empty:
        render_phase_notice("No matching pain points", "Adjust or reset the global filters.")
    else:
        pain.insert(0, "rank", range(1, len(pain) + 1))
        display = pain[["rank", "theme", "frequency", "share_percentage", "average_rating", "negative_percentage", "severity_score", "trend_score", "priority_score", "priority_label", "business_risk", "average_confidence"]].rename(columns={"rank":"Rank","theme":"Theme","frequency":"Mentions","share_percentage":"Share","average_rating":"Avg. Rating","negative_percentage":"Negative Feedback","severity_score":"Severity","trend_score":"Trend","priority_score":"Priority","priority_label":"Priority Level","business_risk":"Business Risk","average_confidence":"Confidence"})
        for column in ("Share", "Avg. Rating", "Negative Feedback", "Severity", "Trend", "Priority"):
            display[column] = pd.to_numeric(display[column], errors="coerce").round(1)
        display["Confidence"] = pd.to_numeric(display["Confidence"], errors="coerce").round(2)
        st.dataframe(display, width="stretch", hide_index=True)
        options = pain["theme"].tolist()
        selected = st.selectbox("Select a pain point", options, key="pain_point_selector")
        st.session_state["selected_pain_point"] = selected
        record = pain[pain["theme"].eq(selected)].iloc[0]
        matching = reviews[reviews["primary_theme"].eq(selected)]
        render_kpi_cards([
            ("Mentions", f"{int(record['frequency']):,}", f"{record['share_percentage']:.1f}% of filtered feedback"),
            ("Average rating", f"{record['average_rating']:.2f}" if pd.notna(record["average_rating"]) else "Not available", None),
            ("Negative feedback", f"{record['negative_percentage']:.1f}%", None),
            ("Severity", f"{record['severity_score']:.1f}", None),
            ("Priority", f"{record['priority_score']:.1f} · {record['priority_label']}", None),
            ("Business risk", str(record["business_risk"]), f"Confidence {record['average_confidence']:.2f}"),
        ])
        st.write(f"**Problem summary:** {selected} appears in {int(record['frequency'])} filtered reviews.")
        st.info(record["severity_explanation"])
        st.info(record["priority_explanation"])
        st.plotly_chart(theme_trend_chart(matching, [selected]), width="stretch")
        if int(record["frequency"]) < 3:
            st.warning("Small sample: fewer than three matching reviews.")
        for warning in calculate_trends(matching).warnings:
            st.warning(warning)
        segment_fields = [("platform", "Platforms"), ("app_version", "App versions"), ("country", "Countries"), ("device", "Devices"), ("user_segment", "User segments")]
        cols = st.columns(5)
        for col, (field, label) in zip(cols, segment_fields, strict=True):
            values = matching[field].dropna().astype(str).value_counts().head(5) if field in matching else pd.Series(dtype=int)
            col.markdown(f"**{label}**")
            col.write(", ".join(values.index) if not values.empty else "Not available")
        st.subheader("Representative quotes")
        for quote in select_representative_quotes(matching, selected, limit=5):
            metadata = " · ".join(str(v) for v in [quote["review_id"], quote["date"], quote["rating"], quote["platform"]] if v is not None)
            render_quote_card(str(quote["original_text"]), metadata)
        st.caption("Quotes shown are taken directly from the uploaded dataset.")
        st.subheader("Matching feedback")
        st.dataframe(curated_feedback_table(matching), width="stretch", hide_index=True)
        st.download_button("Download selected pain-point CSV", matching.to_csv(index=False).encode("utf-8"), f"insightflow_{selected.lower().replace(' ', '_')}_{date.today().isoformat()}.csv", "text/csv", width="stretch")
