# Architecture

## Phase 4

The application is a Python 3.11 Streamlit multipage app:

```text
app.py                 Small landing-page entry point
pages/                 Seven Streamlit navigation destinations
src/config.py          Validated environment configuration and row limit
src/data_loader.py     CSV decoding, limits, and mapping suggestions
src/data_validator.py  Non-mutating structured validation
src/data_cleaner.py    Deterministic canonical cleaning and audit report
src/sentiment.py       VADER, keyword, and rating hybrid sentiment
src/taxonomy.py        Maintained themes, subthemes, risks, and critical terms
src/classifier.py      Rule matching and taxonomy-only TF-IDF fallback
src/feature_requests.py Request intent and normalized grouping
src/trends.py          Bounded date-aware trend calculations
src/prioritization.py  Explainable severity and priority components
src/metrics.py         Overall, theme, and request aggregates
src/quotes.py          Deterministic grounded quote selection
src/analysis_pipeline.py Phase 3 orchestration and processing report
src/filters.py          Global filter options, application, and summaries
src/visualizations.py   Safe reusable Plotly figure factories
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

## Analytics orchestration

The explicit **Analyze feedback** action runs `analyze_feedback`; analysis never
runs merely because a page rerenders. The function copies its cleaned input,
adds sentiment, request, and classification fields, then calculates trends,
metrics, prioritization, and quote indexes. `st.cache_data` caches deterministic
results by cleaned DataFrame content.

Sentiment uses local VADER output, short-text and negation corrections, and a
bounded rating adjustment. Classification first scores exact phrases and whole
keywords. Unresolved reviews are compared with TF-IDF vectors built only from
taxonomy descriptions. No uploaded data trains the classifier.

Trends compare a recent 14-day window with the preceding window using
add-one-smoothed, capped growth. Coverage below 14 days returns score 50 and a
warning. Severity and priority retain every normalized component and readable
explanations. A rare-critical floor prevents infrequent safety or trust events
from defaulting to low priority.

Session state additionally stores analyzed reviews, overall metrics, theme and
feature summaries, trend outputs, grounded quote indexes, warnings, and runtime.

## Dashboard data flow

The analyzed DataFrame remains immutable. Sidebar controls write
`active_filters`; `apply_filters` creates `filtered_reviews`, and existing
metric/trend aggregators create `filtered_theme_summary` without rerunning the
analysis pipeline. Pages consume only these filtered outputs.

Plotly factories accept prepared summaries or review DataFrames and return a
styled figure even for empty or incomplete input. Pages own layout, selection,
and UTF-8 CSV downloads. Reset Filters rotates filter widget keys and preserves
all loaded, cleaned, and analyzed data.

## Planned boundaries

Later phases add charts and filtering, optional AI, DuckDB, and broader exports.
Business logic remains independent from Streamlit page code.

## Runtime constraints

The target is macOS Apple Silicon, Python 3.11, CPU-only execution, no Docker,
and no Node.js. Gemini is optional and credentials are read only from the local
environment.
