# Data Dictionary

## Canonical input mapping

| Field | Required | Accepted data | Cleaning behavior |
| --- | --- | --- | --- |
| `review_text` | Yes | Text-like feedback | Blank rows removed; source preserved |
| `review_id` | No | Text or numeric identifier | Missing values receive `IF-#######` IDs |
| `date` | No | Parseable date or timestamp | Parsed to pandas datetime; invalid values become `NaT` |
| `rating` | No | Numeric value from 1 to 5 | Converted to numeric; invalid/out-of-range values become `NaN` |
| `platform` | No | Text, such as Android or iOS | Surrounding whitespace removed |
| `app_version` | No | Text or version-like value | Surrounding whitespace removed |
| `country` | No | Country, city, or region text | Surrounding whitespace removed |
| `device` | No | Device model or family text | Surrounding whitespace removed |
| `user_segment` | No | Segment label | Surrounding whitespace removed |

Uploaded columns keep their original names until the user confirms a mapping.
Automatic suggestions recognize common aliases, but the mapping remains
editable. A source column can supply only one canonical field.

## Cleaned fields

The cleaned dataset begins with these fields in order:

| Field | Type | Origin |
| --- | --- | --- |
| `review_id` | String | Preserved or generated |
| `original_text` | String | Exact mapped feedback source value |
| `clean_text` | String | Unicode-normalized text without HTML, URLs, or repeated whitespace |
| `date` | Datetime | Parsed optional date |
| `rating` | Float | Valid optional 1–5 rating |
| `platform` | String | Optional mapped value |
| `app_version` | String | Optional mapped value |
| `country` | String | Optional mapped value |
| `device` | String | Optional mapped value |
| `user_segment` | String | Optional mapped value |
| `source_row_number` | Integer | Original CSV row number including the header offset |

Missing optional fields are created with null values. Text is not stemmed,
lemmatized, aggressively filtered, or lowercased in `original_text`.

## Sample dataset

`data/sample_reviews.csv` represents a fictional Indian food-delivery app. The
reviews are synthetic and are not customer testimony. Deliberate duplicates,
missing optional values, short ambiguous comments, and multi-issue reviews are
included for future validation tests.

Sentiment, taxonomy, feature-request, scoring, trend, and AI fields do not exist
in Phase 2. They will be documented only when implemented.
