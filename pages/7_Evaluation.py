"""Evaluation page shell."""

from src.ui import render_page_shell

render_page_shell(
    title="Evaluation",
    intro="Measure system quality and manually review model-assisted outputs.",
    planned_capabilities=(
        "Calculated classification and sentiment quality",
        "Quote grounding and recommendation evidence coverage",
        "Manual review workflow and an exportable evaluation sheet",
    ),
)
