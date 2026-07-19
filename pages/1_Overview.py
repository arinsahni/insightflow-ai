"""Polished filtered product-analytics overview."""

from datetime import date

import plotly.express as px
import streamlit as st

from src.dashboard_formatting import curated_feedback_table, executive_theme_table, technical_feedback_table
from src.filters import summarize_active_filters
from src.metrics import calculate_overall_metrics
from src.session import initialize_session_state
from src.trends import calculate_trends
from src.ui import configure_page, render_app_header, render_kpi_cards, render_phase_notice, render_sidebar
from src.visualizations import (
    feedback_volume_chart, negative_sentiment_trend_chart, priority_matrix_chart,
    rating_distribution_chart, sentiment_distribution_chart, top_themes_chart,
    theme_by_segment_heatmap,
)

configure_page(page_title="Overview · InsightFlow AI")
initialize_session_state()
render_sidebar()
render_app_header(section="Overview")

if not st.session_state["analysis_complete"]:
    render_phase_notice("Analysis required", "Load, validate, clean, and analyze feedback from the sidebar.")
else:
    reviews = st.session_state["filtered_reviews"]
    themes = st.session_state["filtered_theme_summary"]
    if reviews is None or reviews.empty:
        render_phase_notice("No matching feedback", "Adjust or reset the global filters in the sidebar.")
    else:
        trends = calculate_trends(reviews)
        metrics = calculate_overall_metrics(reviews, themes, trends)
        dates = reviews["date"].dropna()
        st.success(f"Dashboard ready · {len(reviews):,} of {len(st.session_state['analyzed_reviews']):,} reviews shown")
        st.caption(
            f"Date coverage: {dates.min().date()} to {dates.max().date()}" if not dates.empty
            else "Date coverage: Not available"
        )
        st.caption(summarize_active_filters(st.session_state["active_filters"]))
        pain = themes[~themes["theme"].isin(["Positive Feedback", "Feature Request", "Other"])]
        top_pain = pain.sort_values(["frequency", "priority_score"], ascending=False).iloc[0] if not pain.empty else None
        fastest = metrics.fastest_growing_pain_point
        negative_count = int(reviews["sentiment"].eq("Negative").sum())
        render_kpi_cards([
            ("Total feedback", f"{metrics.total_feedback_items:,}", f"{metrics.total_feedback_items:,} filtered reviews"),
            ("Average rating", f"{metrics.average_rating:.2f}" if metrics.average_rating is not None else "Not available", None),
            ("Negative feedback", f"{metrics.negative_feedback_percentage:.1f}%", f"{negative_count:,} of {len(reviews):,} reviews"),
            ("Feature requests", f"{metrics.feature_request_count:,}", f"{metrics.feature_request_count:,} detected requests"),
            ("Top pain point", metrics.most_frequent_pain_point or "Not available", f"{int(top_pain['frequency'])} mentions · {top_pain['priority_label']}" if top_pain is not None else None),
            ("Fastest-growing issue", fastest or "Not available", "Trend signal · requires sufficient coverage"),
        ])
        pairs = [
            (feedback_volume_chart(reviews), sentiment_distribution_chart(reviews)),
            (rating_distribution_chart(reviews), top_themes_chart(reviews)),
            (negative_sentiment_trend_chart(reviews), priority_matrix_chart(themes)),
        ]
        for left_figure, right_figure in pairs:
            left, right = st.columns(2)
            left.plotly_chart(left_figure, width="stretch")
            right.plotly_chart(right_figure, width="stretch")
        st.subheader("Executive Theme Summary")
        st.caption("Priority is a prioritization aid combining frequency, severity, trend, business risk, and classification confidence.")
        st.dataframe(executive_theme_table(themes), width="stretch", hide_index=True)
        st.subheader("Filtered Feedback Preview")
        st.dataframe(curated_feedback_table(reviews.head(100)), width="stretch", hide_index=True)
        with st.expander("Technical fields"):
            st.dataframe(technical_feedback_table(reviews.head(100)), width="stretch", hide_index=True)
        with st.expander("Segment analysis", expanded=False):
            segment = next(
                (field for field in ("platform", "device") if field in reviews and reviews[field].dropna().nunique() > 1),
                None,
            )
            if segment:
                st.plotly_chart(theme_by_segment_heatmap(reviews, segment), width="stretch")
            if "app_version" in reviews and reviews["app_version"].dropna().nunique() > 1:
                app_sentiment = reviews.dropna(subset=["app_version", "sentiment"]).groupby(["app_version", "sentiment"]).size().rename("feedback").reset_index()
                st.plotly_chart(px.bar(app_sentiment, x="app_version", y="feedback", color="sentiment", barmode="group", title="Sentiment by app version"), width="stretch")
            segment_tables = st.columns(3)
            for container, field, label in zip(segment_tables, ("country", "user_segment", "platform"), ("Complaints by country", "Complaints by user segment", "Rating by platform"), strict=True):
                if field not in reviews or reviews[field].dropna().empty:
                    container.caption(f"{label}: Not available")
                    continue
                if field == "platform":
                    table = reviews.groupby(field)["rating"].mean().rename("average_rating").reset_index()
                else:
                    table = reviews[reviews["sentiment"].eq("Negative")].groupby(field).size().rename("complaints").reset_index()
                container.markdown(f"**{label}**")
                container.dataframe(table, hide_index=True, width="stretch")
        first, second = st.columns(2)
        first.download_button("Download filtered analyzed CSV", reviews.to_csv(index=False).encode("utf-8"), f"insightflow_filtered_reviews_{date.today().isoformat()}.csv", "text/csv", width="stretch")
        second.download_button("Download filtered theme summary CSV", themes.to_csv(index=False).encode("utf-8"), f"insightflow_filtered_themes_{date.today().isoformat()}.csv", "text/csv", width="stretch")
        st.caption("Severity and priority are prioritization aids, not objective truth.")
