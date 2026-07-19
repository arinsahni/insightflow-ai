"""Filtered feature-request dashboard."""

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from src.dashboard_formatting import curated_feedback_table
from src.metrics import calculate_feature_request_summary
from src.session import initialize_session_state
from src.ui import configure_page, render_app_header, render_kpi_cards, render_phase_notice, render_quote_card, render_sidebar
from src.visualizations import theme_trend_chart, top_feature_requests_chart

configure_page(page_title="Feature Requests · InsightFlow AI")
initialize_session_state()
render_sidebar()
render_app_header(section="Feature Requests")

if not st.session_state["analysis_complete"]:
    render_phase_notice("Analysis required", "Prepare and analyze feedback from the sidebar.")
else:
    filtered = st.session_state["filtered_reviews"]
    requests = filtered[filtered["is_feature_request"]].copy()
    if requests.empty:
        render_phase_notice("No matching feature requests", "No explicit requests match the current filters.")
    else:
        summary = calculate_feature_request_summary(filtered)
        top = summary.sort_values(["mentions", "feature_request_group"], ascending=[False, True]).iloc[0]
        confident = summary.sort_values(["request_confidence", "mentions"], ascending=[False, False]).iloc[0]
        render_kpi_cards([
            ("Feature requests", f"{len(requests):,}", None),
            ("Distinct groups", f"{requests['feature_request_group'].nunique():,}", None),
            ("Most requested", str(top["feature_request_group"]), f"{int(top['mentions'])} mentions"),
            ("Highest confidence", str(confident["feature_request_group"]), f"{confident['request_confidence']:.2f}"),
        ])
        left, right = st.columns(2)
        left.plotly_chart(top_feature_requests_chart(summary), width="stretch")
        right.plotly_chart(theme_trend_chart(requests, ["Feature Request"]), width="stretch")
        segment_cols = [field for field in ("platform", "user_segment") if field in requests and requests[field].dropna().nunique() > 1]
        for field in segment_cols:
            counts = requests[field].dropna().value_counts().rename_axis(field).reset_index(name="requests")
            st.plotly_chart(px.bar(counts, x=field, y="requests", title=f"Feature requests by {field.replace('_', ' ')}"), width="stretch")
        enriched = summary.copy()
        for field, label in (("platform", "affected_platforms"), ("user_segment", "affected_user_segments")):
            mapping = requests.dropna(subset=[field]).groupby("feature_request_group")[field].agg(lambda values: ", ".join(sorted(set(map(str, values)))))
            enriched[label] = enriched["feature_request_group"].map(mapping).fillna("Not available")
        display = enriched.rename(columns={"feature_request_group":"Feature Request","mentions":"Mentions","share_percentage":"Share","average_rating":"Avg. Rating","request_confidence":"Confidence","affected_platforms":"Platforms","affected_user_segments":"User Segments"})
        for column in ("Share", "Avg. Rating"):
            display[column] = pd.to_numeric(display[column], errors="coerce").round(1)
        display["Confidence"] = pd.to_numeric(display["Confidence"], errors="coerce").round(2)
        st.dataframe(display[["Feature Request","Mentions","Share","Avg. Rating","Confidence","Platforms","User Segments"]], width="stretch", hide_index=True)
        selected = st.selectbox("Select a request group", summary["feature_request_group"].tolist(), key="feature_group_selector")
        st.session_state["selected_feature_request_group"] = selected
        matching = requests[requests["feature_request_group"].eq(selected)]
        st.subheader(selected)
        st.write(f"{len(matching)} explicit requests match this group.")
        for row in matching.sort_values(["feature_request_confidence", "review_id"], ascending=[False, True]).drop_duplicates("original_text").head(5).itertuples():
            render_quote_card(str(row.original_text), f"{row.review_id} · {row.platform if pd.notna(row.platform) else 'Platform unavailable'}")
        st.dataframe(curated_feedback_table(matching), width="stretch", hide_index=True)
        first, second = st.columns(2)
        first.download_button("Download filtered feature requests", requests.to_csv(index=False).encode("utf-8"), f"insightflow_filtered_feature_requests_{date.today().isoformat()}.csv", "text/csv", width="stretch")
        second.download_button("Download selected request group", matching.to_csv(index=False).encode("utf-8"), f"insightflow_{selected.lower().replace(' ', '_')}_{date.today().isoformat()}.csv", "text/csv", width="stretch")
