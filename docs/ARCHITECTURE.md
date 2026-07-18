# Architecture

## Phase 1

The application is a Python 3.11 Streamlit multipage app:

```text
app.py                 Small landing-page entry point
pages/                 Seven Streamlit navigation destinations
src/config.py          Validated environment configuration
src/session.py         Session-state defaults
src/ui.py              Shared visual components and page shell
data/                  Fictional source data and ignored processed outputs
tests/                 Foundation configuration tests
docs/                  Product and engineering documentation
```

Streamlit automatically discovers files in `pages/`. Every page delegates shared
branding, configuration, and empty-state behavior to `src/ui.py`.

## Planned boundaries

Later phases will add separate modules for ingestion and validation, cleaning,
classification and metrics, charts and filtering, optional AI, DuckDB, and
exports. Business logic remains independent from Streamlit page code.

## Runtime constraints

The target is macOS Apple Silicon, Python 3.11, CPU-only execution, no Docker,
and no Node.js. Gemini is optional and credentials are read only from the local
environment.
