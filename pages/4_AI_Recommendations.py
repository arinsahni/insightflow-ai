"""AI Recommendations page shell."""

from src.ui import render_page_shell

render_page_shell(
    title="AI Recommendations",
    intro="Review evidence-backed product actions with explicit limitations.",
    planned_capabilities=(
        "Up to five structured, evidence-supported recommendations",
        "Deterministic output when optional Gemini access is unavailable",
        "Human review controls: accept, modify, reject, or request evidence",
    ),
)
