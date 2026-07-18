# InsightFlow AI

**Turn customer feedback into product decisions.**

InsightFlow AI is a Voice of Customer and Product Analytics Copilot for product
managers and analysts. It is designed to turn customer feedback into recurring
pain points, measurable priorities, grounded recommendations, and experiment
ideas while keeping product teams in control.

> Phase 1 status: the project foundation, navigation shell, configuration,
> documentation, and synthetic demonstration dataset are available. Data
> processing and analytics are intentionally reserved for later phases.

## Problem statement

Product teams often export feedback, clean spreadsheets, tag comments manually,
count themes, copy quotes, and assemble recommendations. This process is slow,
subjective, and difficult to repeat. InsightFlow AI is intended to provide a
transparent, evidence-backed workflow without inventing customer quotes or
metrics.

## Product workflow

1. Upload or load customer feedback.
2. Map and validate columns.
3. Clean and classify the feedback.
4. Explore themes, sentiment, trends, and segments.
5. Review source-backed recommendations and experiment ideas.
6. Ask questions and export reviewed findings.

## Planned features

- Flexible CSV ingestion and validation
- Local sentiment and theme classification
- Pain-point and feature-request prioritization
- Source-linked representative quotes
- Product analytics dashboards and filters
- Optional Gemini-supported recommendations with deterministic fallback
- Experiment proposals, evaluation, and exports

Phase 1 provides the application shell for all seven product areas without
showing fabricated metrics.

## Screenshots

Screenshots will be added after the dashboard phase is implemented.

## Architecture

`app.py` is a small Streamlit entry point. Reusable configuration, session, and
presentation helpers live in `src/`. Streamlit discovers the seven files in
`pages/` and displays them in the sidebar. Later phases will add isolated data,
analytics, AI, and persistence modules without moving business logic into page
files. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

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

Following phases add the data pipeline, core analytics, dashboards, optional AI
support, evaluation, exports, and final polish. Potential post-MVP work includes
multilingual models, scheduled ingestion, integrations, and user authentication.

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
