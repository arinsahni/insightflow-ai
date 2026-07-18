"""Experiment Center page shell."""

from src.ui import render_page_shell

render_page_shell(
    title="Experiment Center",
    intro="Translate selected product problems into testable experiment proposals.",
    planned_capabilities=(
        "Hypothesis, control, variant, audience, and instrumentation",
        "Primary, secondary, and guardrail metrics",
        "Decision rules, risks, and honest sample-size requirements",
    ),
)
