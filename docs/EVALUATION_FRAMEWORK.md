# Evaluation Framework

## Principles

- Calculate results from labelled evidence; never fabricate achieved scores.
- Keep evaluation data separate from training or rule design where practical.
- Report dataset size and limitations with every result.
- Treat manual review as part of the quality workflow.

## Planned measures

- Theme-classification accuracy
- Sentiment agreement
- Feature-request precision and recall
- Quote-grounding accuracy
- Recommendation evidence coverage
- Unsupported-claim count
- Processing time
- Optional API success rate

Quote-grounding accuracy is valid quoted reviews divided by total quoted reviews.
Recommendation evidence coverage is recommendations containing valid evidence
divided by total recommendations.

Phase 1 tests configuration behavior and application foundations only. Metric
evaluation begins with the relevant analytics phases.
