"""Pain Points page shell."""

from src.ui import render_page_shell

render_page_shell(
    title="Pain Points",
    intro="Investigate recurring customer problems and their supporting evidence.",
    planned_capabilities=(
        "Sortable theme and subtheme prioritization",
        "Representative source quotes and affected segments",
        "Trend, severity, business-risk, and confidence context",
    ),
)
