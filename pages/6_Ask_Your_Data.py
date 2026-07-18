"""Ask Your Data page shell."""

from src.ui import render_page_shell

render_page_shell(
    title="Ask Your Data",
    intro="Ask product questions against a compact, grounded analysis context.",
    planned_capabilities=(
        "Direct answers supported by relevant metrics",
        "Source review IDs, confidence, and limitations",
        "A constrained context instead of sending the full raw dataset",
    ),
)
