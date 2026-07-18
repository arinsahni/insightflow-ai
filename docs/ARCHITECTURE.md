# Architecture

## Phase 2

The application is a Python 3.11 Streamlit multipage app:

```text
app.py                 Small landing-page entry point
pages/                 Seven Streamlit navigation destinations
src/config.py          Validated environment configuration and row limit
src/data_loader.py     CSV decoding, limits, and mapping suggestions
src/data_validator.py  Non-mutating structured validation
src/data_cleaner.py    Deterministic canonical cleaning and audit report
src/session.py         Data workflow session state and reset behavior
src/ui.py              Shared visual components and sidebar orchestration
data/                  Fictional source data and ignored processed outputs
tests/                 Foundation configuration tests
docs/                  Product and engineering documentation
```

Streamlit automatically discovers files in `pages/`. Every page delegates shared
branding and data preparation to `src/ui.py`. `pages/1_Overview.py` adds the raw
preview, validation summary, cleaned preview, cleaning report, and CSV download.

## Data-loader flow

1. The sidebar receives uploaded bytes or requests the bundled sample.
2. `src/data_loader.py` rejects non-CSV and empty input.
3. Parsing tries UTF-8, UTF-8-SIG, and Latin-1 where necessary.
4. Parsing reads at most `MAX_UPLOAD_ROWS + 1` to detect oversize input without
   returning a silently truncated DataFrame.
5. Original column names are preserved.
6. Normalized aliases provide unique mapping suggestions.

The deterministic sample load is cached with `st.cache_data`. Uploaded file
objects are not cached; their bytes are fingerprinted to prevent unnecessary
reruns.

## Validation flow

`validate_dataframe` receives a DataFrame, canonical-to-source mapping, and row
limit. It does not mutate its input. Blocking errors are separated from
recoverable warnings in a typed `ValidationResult`. Counts cover row and column
size, duplicates, blank feedback, invalid dates, invalid and out-of-range
ratings, missing optional fields, mixed types, and available ranges.

## Cleaning flow

`clean_feedback_data` copies the validated source once, removes exact duplicate
rows and blank feedback, and creates the canonical output. `original_text`
retains source text while `clean_text` receives safe Unicode, HTML, URL, and
whitespace normalization. Dates and ratings are coerced transparently, optional
columns are created when absent, and missing review IDs receive deterministic
IDs. A typed report records every removal and coercion.

## Session-state flow

`src/session.py` initializes state only when keys are absent, so normal Streamlit
reruns do not discard work. Session state stores:

- source DataFrame and filename
- source fingerprint and column mapping
- structured validation result
- cleaned DataFrame and cleaning report
- loaded, processed, and friendly error status

Changing a mapping invalidates prior validation and cleaning results. Reset
clears only the data workflow and rotates the uploader key.

## Planned boundaries

Later phases will add separate modules for classification and metrics, charts
and filtering, optional AI, DuckDB, and broader exports. Business logic remains
independent from Streamlit page code.

## Runtime constraints

The target is macOS Apple Silicon, Python 3.11, CPU-only execution, no Docker,
and no Node.js. Gemini is optional and credentials are read only from the local
environment.
