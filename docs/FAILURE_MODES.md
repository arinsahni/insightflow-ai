# Failure Modes

This starter register will be expanded alongside the related implementation.

| Failure mode | Example | Why it fails | Current mitigation | Future improvement |
| --- | --- | --- | --- | --- |
| Sarcasm | “Amazing, another failed payment.” | Literal polarity can be misleading. | Human review is explicit. | Evaluate contextual classifiers. |
| Mixed sentiment | “Food was great but two hours late.” | One label hides opposing signals. | Preserve original text. | Add primary and secondary issues. |
| Multilingual text | Feedback written outside English | English rules may miss meaning. | Mark limitations. | Add evaluated multilingual support. |
| Hindi-English code mixing | “Delivery bahut late thi.” | Token patterns cross languages. | Preserve text without aggressive cleaning. | Build a labelled code-mixed set. |
| Spelling mistakes | “paymnt faild” | Exact keywords can miss variants. | Retain raw evidence. | Add fuzzy and semantic matching. |
| Vague reviews | “Bad.” | Theme evidence is absent. | Use an `Other`/low-confidence path. | Request more context where possible. |
| Multiple issues | “Late, cold, and a missing item.” | Single-label models lose information. | Plan secondary themes. | Add multi-label evaluation. |
| Spam | Repeated promotional text | It distorts frequency. | Plan duplicate inspection. | Add transparent spam signals. |
| Review bombing | Coordinated bursts | Volume may not represent normal demand. | Avoid causal claims. | Add anomaly and provenance checks. |
| Duplicate feedback | Identical repeated reviews | Counts become inflated. | Sample data includes duplicates for testing. | Deduplicate with an audit summary. |
| Insufficient data | Two comments in a theme | Scores become unstable. | Plan small-sample warnings. | Define minimum evidence thresholds. |
| Incorrect theme mapping | Refund issue tagged as payment | Similar vocabulary overlaps. | Show confidence and manual review. | Expand labelled evaluation data. |
| Hallucinated recommendation | Action cites nonexistent evidence | Generative output can invent support. | Require source IDs and deterministic fallback. | Validate every cited item. |
| Invalid trend conclusion | Growth inferred from a short date range | Sparse time data is noisy. | Plan coverage warnings. | Require sufficient periods and volume. |
| Frequency over impact | Many dark-mode requests outrank payment loss | Volume alone ignores severity. | Plan explainable multi-factor priority. | Validate weights with product teams. |
| Rare critical safety issue | One food-poisoning report is ranked low | Frequency suppresses critical events. | Plan critical-risk overrides. | Add reviewed safety escalation rules. |
