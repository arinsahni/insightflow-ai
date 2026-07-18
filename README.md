# InsightFlow AI

**Turn customer feedback into product decisions.**

InsightFlow AI is a Voice of Customer and Product Analytics Copilot for product
managers and analysts. It is designed to turn customer feedback into recurring
pain points, measurable priorities, grounded recommendations, and experiment
ideas while keeping product teams in control.

> Phase 3 status: the complete local analysis pipeline is available, including
> hybrid sentiment, taxonomy classification, feature requests, trends,
> explainable severity and priority, business risk, and grounded quotes.

## Problem statement

Product teams often export feedback, clean spreadsheets, tag comments manually,
count themes, copy quotes, and assemble recommendations. This process is slow,
subjective, and difficult to repeat. InsightFlow AI is intended to provide a
transparent, evidence-backed workflow without inventing customer quotes or
metrics.

## Product workflow

1. Upload or load customer feedback.
2. Map source columns to the canonical schema.
3. Validate and clean the feedback locally.
4. Explore themes, sentiment, trends, and segments in later phases.
5. Review source-backed recommendations and experiment ideas.
6. Ask questions and export reviewed findings.

## Planned features

- CSV ingestion with UTF-8, UTF-8-SIG, and Latin-1 handling
- Automatic mapping suggestions with editable, unique column mappings
- Structured validation and deterministic cleaning
- Local VADER and rating-assisted sentiment
- Rule-based taxonomy classification with taxonomy-only TF-IDF fallback
- Explicit feature-request detection and grouping
- Pain-point and feature-request prioritization
- Source-linked representative quotes
- Product analytics dashboards and filters
- Optional Gemini-supported recommendations with deterministic fallback
- Experiment proposals, evaluation, and exports

Phase 3 provides deterministic core analytics without external calls.

## Screenshots

Screenshots will be added after the dashboard phase is implemented.

## Architecture

`app.py` is a small Streamlit entry point. Reusable configuration, session,
loading, validation, cleaning, and presentation helpers live in `src/`.
Streamlit discovers the seven files in `pages/` and displays them in the
sidebar. Later phases will add isolated analytics, AI, and persistence modules
without moving business logic into page files. See
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Tech stack

Python 3.11, Streamlit, Pandas, NumPy, Plotly, DuckDB, scikit-learn,
python-dotenv, Pydantic, the official Google Gen AI SDK, VADER Sentiment, and
pytest. The project is CPU-only and does not require Docker, Node.js, or CUDA.

## Installation on macOS Apple Silicon

```bash
xcode-select --install
brew install python@3.11

git clone <repository-url>
cd insightflow-ai

python3.11 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

cp .env.example .env
streamlit run app.py
```

The application opens at <http://localhost:8501>.

## Environment variables

Copy `.env.example` to `.env`. A Gemini key is optional; the application starts
without one.

| Variable | Purpose | Default |
| --- | --- | --- |
| `GEMINI_API_KEY` | Optional Gemini API credential | Empty |
| `GEMINI_MODEL` | Central model override | Application default |
| `ENABLE_AI` | Enables optional AI features when configured | `true` |
| `MAX_AI_QUOTES_PER_THEME` | Maximum evidence quotes supplied per theme | `5` |
| `MAX_UPLOAD_ROWS` | Upload row safety limit | `50000` |

Never commit `.env` or place credentials in source code.

## Run

```bash
source .venv/bin/activate
streamlit run app.py
```

To verify the project:

```bash
python -m compileall app.py src pages tests
pytest -q
```

## Dataset format

The preferred CSV columns are:

| Column | Description |
| --- | --- |
| `review_id` | Stable feedback identifier |
| `date` | Review date |
| `rating` | Rating from 1 to 5 |
| `review_text` | Customer feedback text (the only required field) |
| `platform` | Android or iOS |
| `app_version` | Application version |
| `country` | City or region |
| `device` | Device model or family |
| `user_segment` | Customer segment |

`data/sample_reviews.csv` contains fictional food-delivery reviews for local
demonstration. It includes deliberate duplicates and missing optional values so
later validation behavior can be exercised.

## Load and prepare feedback

1. Open the application and use the sidebar.
2. Upload a `.csv` file or select **Load sample data**.
3. Review the detected columns and automatic mapping suggestions.
4. Map the mandatory feedback-text field and any available optional fields.
5. Select **Validate data** and review errors or warnings.
6. Select **Clean and process** when validation allows it.
7. Open **Overview** to inspect and download the cleaned CSV.

Mappings support arbitrary source names. Common aliases include `content` for
`review_text`, `score` for `rating`, `at` for `date`, and `source` for
`platform`. One source column cannot be mapped to multiple canonical fields.

## Validation behavior

Blocking errors include an empty dataset, missing feedback mapping, no usable
feedback, duplicate source mappings, and exceeding `MAX_UPLOAD_ROWS`. Warnings
cover exact duplicates, duplicate feedback text, blank feedback, invalid
optional dates or ratings, missing optional fields, mixed value types, and
datasets with limited rows, dates, or ratings. Warnings remain visible but do
not automatically block cleaning.

## Cleaning behavior

Cleaning removes exact duplicate rows and blank feedback, preserves the source
feedback in `original_text`, and creates normalized `clean_text`. It strips HTML
and URLs, normalizes Unicode and whitespace, parses dates, constrains ratings to
1–5, generates missing review IDs, and creates absent optional columns. It does
not remove stop words, stem, lemmatize, calculate sentiment, classify themes, or
send data to an API.

## Local analysis

Select **Analyze feedback** after cleaning. The pipeline:

1. combines VADER text polarity, short-text corrections, and valid ratings;
2. detects explicit feature-request intent and normalized groups;
3. classifies taxonomy phrases and keywords;
4. uses TF-IDF similarity against taxonomy descriptions for unresolved text;
5. calculates aggregate and theme metrics, bounded trends, severity, priority,
   and primary business risk; and
6. selects unmodified source quotes with review IDs.

TF-IDF references come only from the maintained taxonomy, never from the
uploaded or bundled review data.

### Severity

```text
0.30 × negative sentiment
+ 0.25 × rating impact
+ 0.20 × frequency
+ 0.15 × trend
+ 0.10 × critical terms
```

### Priority

```text
0.30 × frequency
+ 0.30 × severity
+ 0.20 × trend
+ 0.10 × business risk
+ 0.10 × classification confidence
```

All components are normalized to 0–100. Rare safety, fraud, food-poisoning,
duplicate-charge, blocked-account, and similar critical evidence receives a
documented minimum priority safeguard. Severity and priority are prioritization
aids, not objective truth.

Primary risk labels include revenue, retention, trust, operational, conversion,
customer-satisfaction, and low-direct-business-risk categories.

## Sample questions

- What is the biggest customer problem?
- Which issue is growing fastest?
- Which app version has the most complaints?
- What are users requesting most often?
- What experiment should the team run next?

## Evaluation approach

Later phases will calculate classification, sentiment, feature-request,
quote-grounding, and recommendation-evidence results from labelled data. No
achievement is claimed until it is measured. See
[docs/EVALUATION_FRAMEWORK.md](docs/EVALUATION_FRAMEWORK.md).

## Guardrails

- Customer quotes must exist in the input dataset and retain source IDs.
- Unsupported percentages and causal claims are prohibited.
- Assumptions must be labelled as hypotheses.
- Recommendations require evidence, confidence, and limitations.
- Personally identifiable information will be masked before optional AI use.
- Missing API credentials and AI failures must degrade gracefully.
- The system recommends; the product team decides.

## Failure modes

Known challenges include sarcasm, mixed sentiment, multilingual and code-mixed
text, spelling mistakes, vague feedback, duplicate feedback, multiple issues in
one review, and insufficient trend data. See
[docs/FAILURE_MODES.md](docs/FAILURE_MODES.md).

## Future improvements

The next phase builds the polished dashboard: filters, Plotly charts, richer
segment exploration, and responsive visual states. Optional AI support,
evaluation, and broader exports follow in their own phases.
Potential post-MVP work includes multilingual models, scheduled ingestion,
integrations, and user authentication.

## Current limitations

- Only CSV input is supported.
- `review_text` must be mapped before validation.
- Dates and ratings that cannot be safely parsed are cleared, not inferred.
- Duplicate removal is exact-row based; near-duplicate detection is not present.
- Rule and TF-IDF classification can miss sarcasm, spelling variants,
  multilingual meaning, and taxonomy gaps.
- Trends are neutral when usable date coverage is under 14 days.
- Scores depend on documented heuristic weights that require product-team
  calibration.
- No Gemini, recommendations, experiments, DuckDB persistence, or advanced
  exports are implemented.

## Resume bullet

Built InsightFlow AI, an AI-powered Voice of Customer and Product Analytics
Copilot using Python, Streamlit, DuckDB, Plotly, and Gemini, automating
customer-feedback classification, pain-point prioritization, evidence-backed
product recommendations, and A/B experiment generation.

This describes the target completed product and should only be used after the
corresponding phases are implemented.

## Demo

Demo link: _To be added._

## Author

Author: _To be added._
