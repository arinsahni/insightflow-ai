"""Overview page shell."""

from src.ui import render_page_shell

render_page_shell(
    title="Overview",
    intro="Monitor feedback coverage and the highest-level product signals.",
    planned_capabilities=(
        "Dataset status, date coverage, and global filters",
        "Feedback volume, sentiment, ratings, themes, and priority views",
        "Grounded summary metrics after processing",
    ),
)
