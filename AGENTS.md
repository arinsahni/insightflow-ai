# InsightFlow AI — Codex Working Instructions

## Project objective

Build InsightFlow AI, a Voice of Customer and Product Analytics Copilot.

The complete product specification is stored in:

`INSIGHTFLOW_MASTER_SPEC.txt`

Read that file before implementing any phase.

## Target environment

- macOS Apple Silicon M4
- Python 3.11
- Local virtual environment: `.venv`
- CPU-only execution
- No CUDA or GPU-specific packages
- No Docker
- No Node.js or React

## Required stack

- Streamlit
- Pandas
- NumPy
- Plotly
- DuckDB
- scikit-learn
- python-dotenv
- Pydantic
- google-genai
- vaderSentiment
- pytest

## Development rules

1. Work only inside this repository.
2. Build one phase at a time.
3. Do not begin later-phase functionality early.
4. Keep `app.py` small.
5. Put business logic inside `src/`.
6. Put all AI prompts inside `src/prompts.py`.
7. Never hardcode API keys.
8. Never expose API keys in logs or UI.
9. The application must work without Gemini.
10. Use deterministic fallback behavior for AI features.
11. Use type hints for important functions.
12. Add clear docstrings.
13. Do not create fake metrics or fake customer quotes.
14. Quotes must come from the uploaded dataset.
15. Do not show raw Python tracebacks to application users.
16. Preserve working functionality when adding features.
17. Run tests after every phase.
18. Fix errors before declaring a phase complete.
19. Do not create commits automatically.
20. Do not modify files outside the repository.

## Verification commands

Run after every phase:

```bash
python -m compileall app.py src pages tests
pytest -q