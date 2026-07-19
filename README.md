# InsightFlow AI

**Turn customer feedback into product decisions.**

InsightFlow AI is a Voice of Customer and Product Analytics Copilot for product
managers and analysts. It is designed to turn customer feedback into recurring
pain points, measurable priorities, grounded recommendations, and experiment
ideas while keeping product teams in control.

> Phase 4.6 status: the bundled demonstration data now contains 10,000 primary
> synthetic fintech reviews plus controlled quality issues. Generation is
> deterministic, local, and safe for a public portfolio.

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
- Interactive product analytics dashboard and global filters
- Optional Gemini-supported recommendations with deterministic fallback
- Experiment proposals, evaluation, and exports

Phase 4.5 polishes the deterministic dashboard without changing analytics.

## Dashboard

After analysis, global sidebar filters cover date, platform, rating, geography,
device, app version, theme, sentiment, and user segment when those fields are
available. Filters update KPI cards, charts, tables, drill-downs, quotes, and
exports without rerunning sentiment or classification.

The Overview includes feedback volume, negative sentiment trend, sentiment and
rating distributions, ranked themes, and an issue-priority matrix. Pain Points
adds deterministic explanations, time trends, five segment breakdowns, grounded
quotes, matching feedback, and selected-theme export. Feature Requests adds
group ranking, request trends, platform/user-segment views, source evidence, and
filtered or selected-group exports.

Empty datasets, missing dates/ratings/segments, one sentiment class, and
zero-result filters render explicit safe states instead of broken charts.

Executive KPI cards pair each value with denominator or interpretation context.
The chart inventory includes feedback volume, weekly negative feedback rate,
sentiment and discrete rating distributions, ranked product themes, the issue
priority matrix, theme/request trends, and segment views. Reader tables use
human-friendly labels and rounded values; full analytical fields remain in
downloads and the optional technical view.

Weekly negative feedback is negative reviews divided by all reviews in each
calendar week. Semantic colors remain fixed across views, and text labels plus
descriptive hover details ensure color is not the only signal.

## Screenshots

Screenshots: _Overview, Pain Points, and Feature Requests images to be added._

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

`data/sample_reviews.csv` contains fictional consumer-fintech reviews for local
demonstration. It includes deliberate duplicates and malformed optional values
so validation and cleaning behavior can be exercised.

## Realistic Synthetic Dataset

The bundled CSV contains 10,000 primary reviews dated from July 2025 through
June 2026, followed by 150 intentional exact duplicates. It covers Android,
iOS, and Web; ten date-aligned app versions; six countries; five user segments;
and Free, Premium, and Business subscription tiers.

The probabilistic generation model includes an Android 3.2.1 crash regression
and 3.2.2 recovery, a temporary 3.3.0 payment incident, increasing final-quarter
fee complaints, growing budgeting/export requests, and improved sentiment after
3.4.0. Reviews use varied lengths, mostly English with light Hinglish and
controlled typographical noise. Feature requests, mixed reviews, platform and
segment differences, seasonality, and release spikes are encoded in the review
records—not in precomputed analytics fields.

Controlled quality issues are intentional: exact duplicates, blank feedback,
malformed dates and ratings, missing optional values, inconsistent platform
casing, and surrounding whitespace let the validation workflow demonstrate
real remediation. Every record is synthetic; there is no real customer
information, contact data, or externally downloaded content.

Regenerate the exact public sample with:

```bash
python scripts/generate_sample_data.py \
  --rows 10000 \
  --seed 42 \
  --output data/sample_reviews.csv
```

The same seed produces the same CSV. The generator uses no network calls or API
keys.

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

The next phase objective is the optional evidence-constrained AI layer. DuckDB
and evaluation remain later.
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
