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

Phase 3 automated tests cover required short-text sentiment behavior, canonical
theme examples, mixed-review secondary themes, request groups, metric
arithmetic, score bounds and thresholds, rare-critical safeguards, insufficient
trend coverage, zero-baseline growth, quote source grounding, and pipeline input
immutability.

These behavioral tests are not a measured accuracy evaluation. A later phase
will run a separately labelled dataset to calculate theme accuracy, sentiment
agreement, feature-request precision/recall, and the grounding measures above.
No target score is claimed as achieved yet.
