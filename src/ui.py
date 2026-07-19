"""Reusable Streamlit presentation and local analysis workflow components."""

from collections.abc import Iterable
from dataclasses import asdict
from hashlib import sha256
from html import escape
import logging

import streamlit as st

from src.config import get_settings
from src.analysis_pipeline import AnalysisResult, analyze_feedback
from src.data_cleaner import CleaningReport, clean_feedback_data
from src.data_loader import (
    EXPECTED_FIELDS,
    LoadResult,
    load_sample_data,
    load_uploaded_csv,
    suggest_column_mapping,
)
from src.data_validator import ValidationResult, validate_dataframe
from src.filters import apply_filters, build_filter_options, default_filters, summarize_active_filters
from src.metrics import calculate_theme_summary
from src.session import initialize_session_state, reset_data_state
from src.trends import calculate_trends


LOGGER = logging.getLogger(__name__)

FIELD_LABELS: dict[str, str] = {
    "review_text": "Feedback text *",
    "review_id": "Review ID",
    "date": "Date",
    "rating": "Rating",
    "platform": "Platform",
    "app_version": "App version",
    "country": "Country or region",
    "device": "Device",
    "user_segment": "User segment",
}


@st.cache_data(show_spinner=False)
def _cached_sample_data(max_rows: int) -> LoadResult:
    """Cache deterministic loading of the bundled sample CSV."""
    return load_sample_data(max_rows=max_rows)


@st.cache_data(show_spinner=False)
def _cached_analysis(dataframe) -> AnalysisResult:
    """Cache deterministic local analysis by cleaned DataFrame content."""
    return analyze_feedback(dataframe)


def _clear_analysis_state() -> None:
    """Invalidate analytics when source, mapping, or cleaning changes."""
    st.session_state["analyzed_reviews"] = None
    st.session_state["overall_metrics"] = None
    st.session_state["theme_summary"] = None
    st.session_state["feature_request_summary"] = None
    st.session_state["trend_summary"] = None
    st.session_state["representative_quotes"] = {}
    st.session_state["analytics_warnings"] = []
    st.session_state["analytics_processing_time"] = None
    st.session_state["analysis_complete"] = False
    st.session_state["filtered_reviews"] = None
    st.session_state["filtered_theme_summary"] = None
    st.session_state["active_filters"] = default_filters()
    st.session_state["executive_report"] = None
    st.session_state["executive_report_fingerprint"] = None
    st.session_state["executive_report_generated_at"] = None
    st.session_state["executive_report_error"] = None
    st.session_state["executive_request_metadata"] = None


def _upload_signature(filename: str, content: bytes) -> str:
    """Fingerprint uploaded content and its display filename."""
    digest = sha256()
    digest.update(filename.encode("utf-8", errors="replace"))
    digest.update(b"\0")
    digest.update(content)
    return digest.hexdigest()


def configure_page(*, page_title: str) -> None:
    """Apply consistent page metadata and the wide dashboard layout."""
    st.set_page_config(
        page_title=page_title,
        page_icon="💬",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """<style>
        .block-container{padding-top:1.5rem;padding-bottom:2rem;max-width:1500px}
        [data-testid="stVerticalBlock"]{gap:.75rem}
        .if-kpi{height:100%;min-height:132px;padding:1rem 1.05rem;border:1px solid
        color-mix(in srgb,currentColor 16%,transparent);border-radius:12px;
        background:color-mix(in srgb,currentColor 3%,transparent);display:flex;
        flex-direction:column;justify-content:space-between}
        .if-kpi-label{font-size:.82rem;font-weight:650;letter-spacing:.02em;opacity:.72}
        .if-kpi-value{font-size:clamp(1.25rem,2vw,2rem);line-height:1.15;font-weight:720;
        overflow-wrap:anywhere;margin:.45rem 0}
        .if-kpi-support{font-size:.82rem;line-height:1.35;opacity:.7}
        .if-quote{border:1px solid color-mix(in srgb,currentColor 16%,transparent);
        border-left:3px solid #64748b;border-radius:10px;padding:.9rem 1rem;margin:.5rem 0;
        background:color-mix(in srgb,currentColor 3%,transparent)}
        .if-quote-text{font-size:.98rem;line-height:1.55}.if-quote-meta{font-size:.78rem;
        opacity:.68;margin-top:.55rem}
        @media(max-width:800px){.if-kpi{min-height:112px}.block-container{padding-top:1rem}}
        </style>""",
        unsafe_allow_html=True,
    )


def _store_load_result(result: LoadResult, *, signature: str) -> None:
    """Store a successful load or a friendly error in session state."""
    if not result.is_success:
        st.session_state["processing_error"] = result.errors[0]
        return

    dataframe = result.dataframe
    st.session_state["source_dataframe"] = dataframe
    st.session_state["uploaded_filename"] = result.filename
    st.session_state["column_mapping"] = suggest_column_mapping(dataframe.columns)
    st.session_state["validation_result"] = None
    st.session_state["cleaned_reviews"] = None
    st.session_state["cleaning_report"] = None
    st.session_state["data_loaded"] = True
    st.session_state["data_processed"] = False
    _clear_analysis_state()
    st.session_state["processing_error"] = None
    st.session_state["source_signature"] = signature


def _render_mapping_controls() -> dict[str, str | None]:
    """Render unique canonical-to-source mapping controls."""
    dataframe = st.session_state["source_dataframe"]
    source_columns = [str(column) for column in dataframe.columns]
    saved_mapping = st.session_state.get("column_mapping") or {}
    mapping: dict[str, str | None] = {}
    used_sources: set[str] = set()
    signature = str(st.session_state.get("source_signature"))

    st.markdown("#### Column mapping")
    st.caption("Feedback text is required. Each source column can be used once.")
    for field_name in EXPECTED_FIELDS:
        current = saved_mapping.get(field_name)
        available = [column for column in source_columns if column not in used_sources]
        options: list[str | None] = [None, *available]
        default_index = options.index(current) if current in options else 0
        selection = st.selectbox(
            FIELD_LABELS[field_name],
            options=options,
            index=default_index,
            format_func=lambda value: "Not mapped" if value is None else value,
            key=f"mapping_{signature}_{field_name}",
        )
        mapping[field_name] = selection
        if selection:
            used_sources.add(selection)

    if mapping != saved_mapping:
        st.session_state["column_mapping"] = mapping
        st.session_state["validation_result"] = None
        st.session_state["cleaned_reviews"] = None
        st.session_state["cleaning_report"] = None
        st.session_state["data_processed"] = False
        _clear_analysis_state()
    return mapping


def render_validation_summary(result: ValidationResult) -> None:
    """Display a compact professional validation summary."""
    status = "Ready with warnings" if result.can_proceed and result.warnings else (
        "Ready" if result.can_proceed else "Blocked"
    )
    date_range = (
        f"{result.detected_date_range[0].isoformat()} to "
        f"{result.detected_date_range[1].isoformat()}"
        if result.detected_date_range
        else "Not available"
    )
    rating_range = (
        f"{result.rating_min:g}–{result.rating_max:g}"
        if result.rating_min is not None and result.rating_max is not None
        else "Not available"
    )
    summary = {
        "File status": status,
        "Rows detected": f"{result.row_count:,}",
        "Columns detected": f"{result.column_count:,}",
        "Duplicate rows": f"{result.duplicate_row_count:,}",
        "Duplicate feedback texts": f"{result.duplicate_text_count:,}",
        "Missing feedback rows": f"{result.missing_feedback_count:,}",
        "Invalid dates": f"{result.invalid_date_count:,}",
        "Invalid ratings": f"{result.invalid_rating_count:,}",
        "Out-of-range ratings": f"{result.out_of_range_rating_count:,}",
        "Rating range": rating_range,
        "Date range": date_range,
        "Missing optional fields": (
            ", ".join(result.missing_optional_fields)
            if result.missing_optional_fields
            else "None"
        ),
    }
    for label, value in summary.items():
        st.markdown(f"**{label}:** {value}")
    for message in result.errors:
        st.error(message)
    for message in result.warnings:
        st.warning(message)
    if result.can_proceed:
        st.success("Validation complete. The dataset can be cleaned and processed.")


def render_cleaning_report(report: CleaningReport) -> None:
    """Display cleaning audit counts without analytics."""
    values = asdict(report)
    labels = (
        ("input_rows", "Input rows"),
        ("output_rows", "Output rows"),
        ("removed_duplicate_rows", "Duplicates removed"),
        ("removed_missing_feedback_rows", "Missing feedback removed"),
        ("generated_review_ids", "Review IDs generated"),
        ("invalid_dates_coerced", "Invalid dates cleared"),
        ("invalid_ratings_coerced", "Invalid ratings cleared"),
    )
    columns = st.columns(4)
    for index, (key, label) in enumerate(labels):
        columns[index % 4].metric(label, f"{values[key]:,}")
    st.caption(f"Cleaning completed in {report.processing_time_seconds:.3f} seconds.")


def render_kpi_cards(items: list[tuple[str, str, str | None]]) -> None:
    """Render equal-height responsive KPI cards."""
    columns = st.columns(3)
    for index, (label, value, caption) in enumerate(items):
        with columns[index % 3]:
            st.markdown(
                f'<div class="if-kpi"><div class="if-kpi-label">{escape(label)}</div>'
                f'<div class="if-kpi-value">{escape(value or "Not available")}</div>'
                f'<div class="if-kpi-support">{escape(caption or "")}</div></div>',
                unsafe_allow_html=True,
            )


def render_empty_state(title: str, guidance: str) -> None:
    """Render a consistent professional empty state."""
    st.info(f"**{title}**\n\n{guidance}")


def render_quote_card(quote: str, metadata: str) -> None:
    """Render an exact source quote in a subtle accessible card."""
    st.markdown(
        f'<div class="if-quote"><div class="if-quote-text">“{escape(quote)}”</div>'
        f'<div class="if-quote-meta">{escape(metadata)}</div></div>',
        unsafe_allow_html=True,
    )


def _run_validation(mapping: dict[str, str | None]) -> ValidationResult:
    """Validate current session data and store the structured result."""
    settings = get_settings()
    result = validate_dataframe(
        st.session_state["source_dataframe"],
        mapping,
        settings.max_upload_rows,
    )
    st.session_state["validation_result"] = result
    st.session_state["processing_error"] = None
    return result


def _run_cleaning(mapping: dict[str, str | None]) -> None:
    """Clean validated session data with friendly error handling."""
    try:
        result = clean_feedback_data(st.session_state["source_dataframe"], mapping)
    except (KeyError, TypeError, ValueError) as error:
        LOGGER.error("Feedback cleaning failed with %s", type(error).__name__)
        st.session_state["processing_error"] = (
            "The dataset could not be cleaned. Review the mapping and validation messages."
        )
        return

    st.session_state["cleaned_reviews"] = result.dataframe
    st.session_state["cleaning_report"] = result.report
    st.session_state["data_processed"] = True
    _clear_analysis_state()
    st.session_state["processing_error"] = None


def _run_analysis() -> None:
    """Run and store deterministic local analytics with safe error handling."""
    try:
        with st.status("Preparing dashboard analysis", expanded=True) as status:
            st.write("Preparing reviews")
            st.write("Calculating sentiment and classifying themes")
            st.write("Detecting feature requests")
            st.write("Calculating product metrics and ranking pain points")
            result = _cached_analysis(st.session_state["cleaned_reviews"])
            st.write("Preparing dashboard")
            status.update(label="Dashboard analysis ready", state="complete", expanded=False)
    except (KeyError, TypeError, ValueError) as error:
        LOGGER.error("Local analysis failed with %s", type(error).__name__)
        st.session_state["processing_error"] = (
            "Feedback analysis could not be completed. Reset the data and try again."
        )
        return
    st.session_state["analyzed_reviews"] = result.analyzed_reviews
    st.session_state["overall_metrics"] = result.overall_metrics
    st.session_state["theme_summary"] = result.theme_summary
    st.session_state["feature_request_summary"] = result.feature_request_summary
    st.session_state["trend_summary"] = result.trend_outputs
    st.session_state["representative_quotes"] = result.representative_quotes
    st.session_state["analytics_warnings"] = result.warnings
    st.session_state["analytics_processing_time"] = result.report.processing_time_seconds
    st.session_state["analysis_complete"] = True
    st.session_state["active_filters"] = default_filters()
    st.session_state["filtered_reviews"] = result.analyzed_reviews.copy()
    st.session_state["filtered_theme_summary"] = result.theme_summary.copy()
    st.session_state["processing_error"] = None


def _render_global_filters() -> None:
    """Render global filters and update derived filtered views."""
    analyzed = st.session_state["analyzed_reviews"]
    options = build_filter_options(analyzed)
    current = st.session_state.get("active_filters") or default_filters()
    generation = st.session_state.get("filter_generation", 0)
    filters = default_filters()
    st.divider()
    st.markdown("### Global filters")
    if "date_range" in options:
        selected_dates = st.date_input(
            "Date range", value=current.get("date_range") or options["date_range"],
            min_value=options["date_range"][0], max_value=options["date_range"][1],
            key=f"global_date_{generation}",
        )
        filters["date_range"] = selected_dates if isinstance(selected_dates, tuple) and len(selected_dates) == 2 else None
    labels = {"platform": "Platform", "rating": "Rating", "country": "Country", "device": "Device", "app_version": "App version", "primary_theme": "Theme", "sentiment": "Sentiment", "user_segment": "User segment"}
    for key, label in labels.items():
        if key in options:
            filters[key] = st.multiselect(label, options[key], default=current.get(key, []), key=f"global_{key}_{generation}")
    st.session_state["active_filters"] = filters
    filtered = apply_filters(analyzed, filters)
    st.session_state["filtered_reviews"] = filtered
    st.session_state["filtered_theme_summary"] = calculate_theme_summary(filtered, calculate_trends(filtered))
    st.caption(f"{len(filtered):,} of {len(analyzed):,} analyzed rows")
    st.caption(summarize_active_filters(filters))
    if st.button("Reset filters", width="stretch"):
        st.session_state["active_filters"] = default_filters()
        st.session_state["filter_generation"] = generation + 1
        st.rerun()


def render_sidebar() -> None:
    """Render the shared upload, mapping, validation, and cleaning workflow."""
    initialize_session_state()
    settings = get_settings()
    with st.sidebar:
        st.markdown("## InsightFlow AI")
        st.caption("Voice of Customer and Product Analytics Copilot")
        st.divider()

        st.markdown("### Feedback data")
        uploaded_file = st.file_uploader(
            "Upload customer feedback",
            type=["csv"],
            key=f"feedback_uploader_{st.session_state['uploader_generation']}",
            help=f"CSV only, up to {settings.max_upload_rows:,} rows.",
        )
        if uploaded_file is not None:
            content = uploaded_file.getvalue()
            signature = _upload_signature(uploaded_file.name, content)
            if signature != st.session_state.get("source_signature"):
                result = load_uploaded_csv(
                    uploaded_file,
                    filename=uploaded_file.name,
                    max_rows=settings.max_upload_rows,
                )
                _store_load_result(result, signature=signature)

        if st.button("Load sample data", width="stretch"):
            result = _cached_sample_data(settings.max_upload_rows)
            current_upload_signature = (
                _upload_signature(uploaded_file.name, uploaded_file.getvalue())
                if uploaded_file is not None
                else "sample"
            )
            _store_load_result(result, signature=current_upload_signature)

        if st.session_state["data_loaded"]:
            dataframe = st.session_state["source_dataframe"]
            st.success(f"Loaded {st.session_state['uploaded_filename']}")
            st.caption(f"{len(dataframe):,} rows · {len(dataframe.columns):,} columns")
            with st.expander("Detected columns"):
                st.write(", ".join(str(column) for column in dataframe.columns))

            mapping = _render_mapping_controls()
            if not mapping.get("review_text"):
                st.warning("Map a feedback-text column before validation.")

            validate_clicked = st.button(
                "Validate data",
                width="stretch",
                disabled=not bool(mapping.get("review_text")),
            )
            if validate_clicked:
                _run_validation(mapping)

            validation_result = st.session_state.get("validation_result")
            if validation_result is not None:
                with st.expander("Validation summary", expanded=not validation_result.can_proceed):
                    render_validation_summary(validation_result)

            if st.button(
                "Clean and process",
                type="primary",
                width="stretch",
                disabled=not (
                    validation_result is not None and validation_result.can_proceed
                ),
            ):
                _run_cleaning(mapping)

            if st.session_state["data_processed"]:
                st.success("Cleaned data is ready.")
                if st.button(
                    "Analyze feedback",
                    type="primary",
                    width="stretch",
                    disabled=st.session_state["analysis_complete"],
                ):
                    _run_analysis()
                if st.session_state["analysis_complete"]:
                    st.success("Local feedback analysis is ready.")
                    st.caption(
                        f"Analyzed in {st.session_state['analytics_processing_time']:.3f} seconds."
                    )
                    _render_global_filters()

        if st.session_state.get("processing_error"):
            st.error(st.session_state["processing_error"])

        if st.button("Reset data", width="stretch"):
            reset_data_state()
            st.rerun()

        st.divider()
        status = "Available" if settings.ai_available else "Not configured"
        st.caption(f"Optional AI: {status}")
        st.caption("Loading, cleaning, and analysis run locally on this device.")
        st.caption("Data is sent to Gemini only after an explicit Generate click.")


def render_app_header(*, section: str | None = None) -> None:
    """Render consistent InsightFlow branding on the current page."""
    settings = get_settings()
    st.title(settings.app_name if section is None else section)
    st.caption(settings.subtitle)


def render_phase_notice(title: str, message: str) -> None:
    """Show a consistent, non-error empty state."""
    st.info(f"**{title}**\n\n{message}", icon="ℹ️")


def render_page_shell(
    *,
    title: str,
    intro: str,
    planned_capabilities: Iterable[str],
) -> None:
    """Render a complete, reusable shell for a future product area."""
    configure_page(page_title=f"{title} · InsightFlow AI")
    initialize_session_state()
    render_sidebar()
    render_app_header(section=title)
    st.write(intro)
    render_phase_notice(
        "Available after feedback processing",
        "This page is ready to open. Its data-backed analytics and "
        "results will be added only in the appropriate later phase.",
    )
    st.subheader("This workspace will include")
    for capability in planned_capabilities:
        st.markdown(f"- {capability}")
    st.caption("No metrics or customer quotes are fabricated in this empty state.")
