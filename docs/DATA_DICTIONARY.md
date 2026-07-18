# Data Dictionary

## Preferred input fields

| Field | Required | Description |
| --- | --- | --- |
| `review_text` | Yes | Original customer feedback |
| `review_id` | No | Source or generated identifier |
| `date` | No | Feedback date |
| `rating` | No | Numeric rating, normally 1–5 |
| `platform` | No | Source platform, such as Android or iOS |
| `app_version` | No | Application version |
| `country` | No | Country, city, or region |
| `device` | No | Device model or family |
| `user_segment` | No | Customer segment |

## Sample dataset

`data/sample_reviews.csv` represents a fictional Indian food-delivery app. The
reviews are synthetic and are not customer testimony. Deliberate duplicates,
missing optional values, short ambiguous comments, and multi-issue reviews are
included for future validation tests.

Processed and derived fields will be documented when their implementation phase
begins.
