"""Reusable Streamlit presentation components."""

from collections.abc import Iterable

import streamlit as st

from src.config import get_settings


def configure_page(*, page_title: str) -> None:
    """Apply consistent page metadata and the wide dashboard layout."""
    st.set_page_config(
        page_title=page_title,
        page_icon="💬",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def render_sidebar() -> None:
    """Render application identity and safe Phase 1 status information."""
    settings = get_settings()
    with st.sidebar:
        st.markdown("## InsightFlow AI")
        st.caption("Voice of Customer and Product Analytics Copilot")
        st.divider()
        st.markdown("**Phase 1 · Foundation**")
        st.caption("Navigation and configuration are ready.")
        status = "Available" if settings.ai_available else "Not configured"
        st.caption(f"Optional AI: {status}")
        st.caption("The application works without a Gemini API key.")


def render_app_header(*, section: str | None = None) -> None:
    """Render consistent InsightFlow branding on the current page."""
    settings = get_settings()
    st.title(settings.app_name if section is None else section)
    st.caption(settings.subtitle)


def render_phase_notice(title: str, message: str) -> None:
    """Show a consistent, non-error Phase 1 empty state."""
    st.info(f"**{title}**\n\n{message}", icon="ℹ️")


def render_page_shell(
    *,
    title: str,
    intro: str,
    planned_capabilities: Iterable[str],
) -> None:
    """Render a complete, reusable shell for a future product area."""
    configure_page(page_title=f"{title} · InsightFlow AI")
    render_sidebar()
    render_app_header(section=title)
    st.write(intro)
    render_phase_notice(
        "Available after feedback processing",
        "This Phase 1 page is ready to open. Its data-backed controls and "
        "results will be added only in the appropriate later phase.",
    )
    st.subheader("This workspace will include")
    for capability in planned_capabilities:
        st.markdown(f"- {capability}")
    st.caption("No metrics or customer quotes are fabricated in this empty state.")
