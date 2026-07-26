"""Optional evidence-grounded Gemini executive-insights workspace."""

from __future__ import annotations

from datetime import date
import logging

import pandas as pd
import streamlit as st

from src.config import get_settings
from src.executive_report import (
    executive_report_to_json,
    executive_report_to_markdown,
    generate_executive_report,
    prepare_executive_report_request,
)
from src.gemini_client import (
    GeminiError,
    GeminiExecutiveClient,
    get_gemini_api_key,
    get_gemini_model,
    streamlit_secrets_safe,
)
from src.session import initialize_session_state
from src.ui import configure_page, render_app_header, render_phase_notice, render_sidebar


LOGGER = logging.getLogger(__name__)

configure_page(page_title="Executive Insights · InsightFlow AI")
initialize_session_state()
render_sidebar()
render_app_header(section="Executive Insights")
st.caption(
    "Optional Gemini synthesis grounded only in the compact deterministic "
    "analytics context. Generation occurs only when you click Generate."
)

if not st.session_state["analysis_complete"]:
    render_phase_notice(
        "Analysis required",
        "Load, validate, clean, and analyze feedback before preparing executive insights.",
    )
    st.stop()

reviews = st.session_state.get("filtered_reviews")
if reviews is None or reviews.empty:
    render_phase_notice(
        "No matching feedback",
        "Adjust or reset the global filters before preparing executive insights.",
    )
    st.stop()

try:
    prepared = prepare_executive_report_request(
        reviews,
        raw_review_count=len(st.session_state["source_dataframe"])
        if st.session_state.get("source_dataframe") is not None else None,
        cleaning_report=st.session_state.get("cleaning_report"),
    )
except (KeyError, TypeError, ValueError) as error:
    LOGGER.error("Executive request preparation failed type=%s", type(error).__name__)
    st.error("The grounded executive context could not be prepared.")
    st.stop()

metadata = prepared.metadata
st.session_state["executive_request_metadata"] = metadata.model_dump(mode="json")
summary_columns = st.columns(4)
summary_columns[0].metric("Reviews in context", f"{len(reviews):,}")
summary_columns[1].metric("Grounded quotes", f"{metadata.quote_count:,}")
summary_columns[2].metric("Pain points", f"{metadata.pain_point_count:,}")
summary_columns[3].metric("Approx. tokens", f"{metadata.approximate_token_count:,}")
st.caption(
    f"Context fingerprint: `{prepared.context_fingerprint[:12]}` · "
    f"{metadata.character_count:,} characters · "
    f"{'Compacted' if metadata.truncation_applied else 'No truncation'}"
)

secrets = streamlit_secrets_safe()
api_key = get_gemini_api_key(secrets=secrets)
model = get_gemini_model(secrets=secrets)
if not api_key:
    st.info(
        "**Gemini is not configured.** Add `GEMINI_API_KEY` to `.env` for local "
        "use or to Streamlit Community Cloud secrets, then restart the app."
    )

stored_report = st.session_state.get("executive_report")
stored_fingerprint = st.session_state.get("executive_report_fingerprint")
is_stale = bool(stored_report and stored_fingerprint != prepared.context_fingerprint)
if is_stale:
    st.warning(
        "This saved report is stale because the active filters or analytical "
        "evidence changed. Regenerate it before using the findings."
    )

generate_label = "Regenerate executive insights" if stored_report else "Generate executive insights"
left, right = st.columns([3, 1])
generate_clicked = left.button(
    generate_label,
    type="primary",
    disabled=not bool(api_key),
    width="stretch",
)
if right.button("Clear report", disabled=stored_report is None, width="stretch"):
    for key in (
        "executive_report", "executive_report_fingerprint",
        "executive_report_generated_at", "executive_report_error",
    ):
        st.session_state[key] = None
    st.rerun()

if generate_clicked:
    settings = get_settings()
    client = GeminiExecutiveClient(
        api_key=api_key,
        model=model,
        timeout_seconds=settings.gemini_timeout_seconds,
        max_retries=settings.gemini_max_retries,
    )
    try:
        with st.status("Generating grounded executive insights", expanded=True) as status:
            st.write("Preparing compact evidence")
            st.write("Requesting schema-constrained synthesis")
            report = generate_executive_report(
                reviews,
                client=client,
                raw_review_count=len(st.session_state["source_dataframe"])
                if st.session_state.get("source_dataframe") is not None else None,
                cleaning_report=st.session_state.get("cleaning_report"),
            )
            st.write("Validating review IDs, quotes, metrics, and causal language")
            status.update(label="Executive insight generation complete", state="complete")
        st.session_state["executive_report"] = report
        st.session_state["executive_report_fingerprint"] = report.context_fingerprint
        st.session_state["executive_report_generated_at"] = report.generated_at_utc
        st.session_state["executive_report_error"] = None
        stored_report = report
        is_stale = False
    except GeminiError as error:
        st.session_state["executive_report_error"] = str(error)
        st.error(str(error))
    except (KeyError, TypeError, ValueError) as error:
        LOGGER.error("Executive report generation failed type=%s", type(error).__name__)
        st.session_state["executive_report_error"] = (
            "Executive insights could not be generated safely."
        )
        st.error(st.session_state["executive_report_error"])

report = st.session_state.get("executive_report")
if report is None:
    st.info("No report has been generated for this analysis context.")
    st.stop()
if not report.validation_passed:
    st.error(
        "The generated report contained unsupported evidence and was not marked "
        "as validated."
    )
    with st.expander("Validation findings"):
        for error in report.validation_errors:
            st.write(f"- {error}")
    st.stop()

response = report.response
st.success(
    f"Evidence validation passed · {len(report.validated_review_ids)} cited review IDs checked"
)
st.subheader("Executive Summary")
st.markdown(response.executive_summary)

st.subheader("Top Customer Problems")
for item in sorted(response.customer_problems, key=lambda value: value.rank):
    with st.expander(f"{item.rank}. {item.title}", expanded=item.rank == 1):
        st.markdown(item.problem_summary)
        st.write(f"**Affected users:** {item.affected_users}")
        st.write(f"**Measured evidence:** {item.measured_evidence}")
        st.write(f"**Severity:** {item.severity} · **Urgency:** {item.urgency} · **Confidence:** {item.confidence}")
        st.caption(f"Review IDs: {', '.join(item.supporting_review_ids)}")
        st.caption(f"Limitation: {item.limitations}")

st.subheader("Product Opportunities")
for item in sorted(response.product_opportunities, key=lambda value: value.rank):
    with st.expander(f"{item.rank}. {item.title}"):
        st.markdown(item.user_problem)
        st.write(f"**Supporting demand:** {item.supporting_demand}")
        st.write(f"**Impact hypothesis:** {item.likely_product_impact_hypothesis}")
        st.write(f"**Suggested validation:** {item.suggested_validation_step}")
        st.caption(f"Review IDs: {', '.join(item.supporting_review_ids)}")

st.subheader("Release and Platform Risks")
for item in sorted(response.release_risks, key=lambda value: value.rank):
    with st.expander(f"{item.rank}. {item.title}"):
        st.markdown(item.observed_change)
        st.write(f"**Affected:** {item.affected_platform_or_segment}")
        st.write(f"**Hypotheses:** {item.hypotheses}")
        st.write(f"**Investigation:** {item.recommended_investigation}")
        st.caption(f"Review IDs: {', '.join(item.supporting_review_ids)}")

st.subheader("Recommended Next Actions")
for item in sorted(response.recommended_actions, key=lambda value: value.rank):
    with st.expander(f"{item.rank}. {item.action}"):
        st.markdown(item.rationale)
        st.write(f"**Evidence:** {item.evidence_summary}")
        st.write(f"**Owner:** {item.owner} · **Timeframe:** {item.timeframe}")
        st.caption(f"Review IDs: {', '.join(item.supporting_review_ids)}")

st.subheader("Evidence Explorer")
evidence_table = pd.DataFrame([
    {"Review ID": item.review_id, "Exact source quote": item.quote}
    for item in response.evidence
])
st.dataframe(evidence_table, hide_index=True, width="stretch")
st.caption("Quotes are exact evidence from the compact payload; they are never paraphrased.")

st.subheader("Confidence and Limitations")
st.write(f"**Overall confidence:** {response.confidence_assessment.overall_confidence}")
for limitation in response.confidence_assessment.limitations:
    st.write(f"- {limitation}")

with st.expander("Request and usage metadata"):
    st.json({
        "model": report.model,
        "generated_at_utc": report.generated_at_utc.isoformat(),
        "context_fingerprint": report.context_fingerprint,
        "context_characters": metadata.character_count,
        "approximate_context_tokens": metadata.approximate_token_count,
        "usage": report.usage.model_dump(mode="json"),
        "stale": is_stale,
    })

markdown = executive_report_to_markdown(report).encode("utf-8")
json_export = executive_report_to_json(report).encode("utf-8")
download_a, download_b = st.columns(2)
download_a.download_button(
    "Download Markdown",
    markdown,
    f"insightflow_executive_insights_{date.today().isoformat()}.md",
    "text/markdown",
    width="stretch",
)
download_b.download_button(
    "Download JSON",
    json_export,
    f"insightflow_executive_insights_{date.today().isoformat()}.json",
    "application/json",
    width="stretch",
)
