# Stage 1 - Dataset Cleanup Summary

**Status:** cleanup, policy 1.0, and second manual QA are complete.

## Before and After

| Metric | Before | After |
| --- | ---: | ---: |
| Records | 100 | 90 |
| Spans | 835 | 609 |
| Invalid `COMPANY` labels | 8 | 0 |
| Automatic errors | 8 | 0 |
| Automatic warnings | 35 | 17 |

| Label | Before | After |
| --- | ---: | ---: |
| PERSON | 153 | 91 |
| ORGANIZATION | 80 | 82 |
| LOCATION | 101 | 60 |
| TIMEDATE | 164 | 122 |
| PRODUCT | 87 | 81 |
| WORKOFART | 59 | 50 |
| JOB | 100 | 58 |
| AMOUNT | 83 | 65 |
| Invalid COMPANY | 8 | 0 |

Automatic audit findings are not a count of all semantic errors. The initial
43 findings included 8 errors and 35 warnings.

## Cleanup Actions

- Merged split multi-word person names.
- Corrected semantic label confusions.
- Removed extra grammar and punctuation from span boundaries.
- Added missing entities.
- Removed unsupported `JOB` labels from generic departments, teams, and fields.
- Removed 10 records from the processed data because severe OCR, encoding, or
  nonsensical text prevented reliable annotation.

## Result

- 76 records changed.
- 14 records remained unchanged.
- 10 records were removed.
- The raw data remained unchanged and is stored separately.
- The processed data contains 90 records in JSONL and Parquet.
- All 90 retained records passed a second manual QA review.
- All 17 remaining automatic warnings were manually reviewed and accepted.
- The correction manifest and scripts reproduce the same outputs.

The remaining publication step is to upload the cleaned dataset with the full
dataset card to a separate public Stage 1 Hugging Face repository.
