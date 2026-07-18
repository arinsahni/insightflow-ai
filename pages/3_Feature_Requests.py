"""Feature Requests page shell."""

from src.ui import render_page_shell

render_page_shell(
    title="Feature Requests",
    intro="Explore requested capabilities without mixing them with product defects.",
    planned_capabilities=(
        "Grouped feature requests and request trends",
        "Affected segments and source-linked quotes",
        "Filters, estimated priority, user value, and CSV export",
    ),
)
