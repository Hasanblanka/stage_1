 Technical Report

Status: Stage 1 local cleanup is complete. The public Hugging Face dataset URL
will be added after publication.

## Stage 1 - Rulecraft and Cleanup

### Approach

1. Downloaded the starter dataset from a pinned Hugging Face revision.
2. Preserved the raw JSONL unchanged and monitored it with SHA256.
3. Ran a deterministic schema, offset, boundary, label, and overlap audit.
4. Manually reviewed all 100 starter records and identified recurring issue
   patterns.
5. Wrote additional policy rules before applying bulk corrections.
6. Stored correction decisions in a manifest instead of editing the raw data.
7. Applied the manifest to a copy of the raw data to create separate JSONL and
   Parquet outputs.
8. Manually reviewed all 90 retained records a second time.
9. Re-ran automatic validation and reproducibility checks.

This mixed method was selected because scripts apply structural and recurring
rules consistently, while manual review is required for semantic labels and
context-dependent boundaries.

### Recurring Issue Patterns

- Split multi-word person names.
- `AMOUNT/TIMEDATE`, `PRODUCT/WORKOFART/ORGANIZATION`, and
  `ORGANIZATION/LOCATION` confusion.
- Generic departments, fields, and category words labeled as entities.
- Extra function words, conjunctions, punctuation, and possessive markers in
  span boundaries.
- Missing named entities.
- Invalid `COMPANY` labels.
- OCR, encoding, keyword-spam, and nonsensical text failures.

### Additional Policy Rules

| Rule | Gap closed and reason |
| --- | --- |
| A1 - Temporal specificity | Separates dates, durations, frequencies, and ages from vague adverbs and question placeholders such as `how long`. |
| A2 - Quantity boundaries | Defines numeric, scale, unit, currency, and modifier boundaries and separates numeric identifiers from measurable quantities. |
| A3 - Person names | Defines full names, nicknames, usernames, and dialogue placeholders consistently. |
| A4 - Product/organization/work | Resolves recurring confusion among software, platforms, companies, and publication titles. |
| A5 - Job/department | Separates formal occupational roles from departments, teams, fields, and activities. |
| A6 - Location/establishment | Separates restaurants, casinos, and companies from physical and geographic places according to context. |
| A7 - Nested work titles | Prevents nested labels inside complete work titles in the flat annotation format. |
| A8 - Proposed names | Labels explicitly proposed product and work names even before release. |
| A9 - Removal threshold | Restricts removals to objective OCR, encoding, truncation, spam, or nonsensical-text failures. |



***The full rules, examples, and justifications are in
`policies/annotation_policy.md`. They do not alter the fixed baseline rules.***



### Removed Records

Removals were applied only to the processed dataset:

- ID 59: a long unrelated random-word fragment after a useful opening.
- IDs 60, 68, 69, 71, and 75: severe recurring encoding corruption.
- ID 61: severe OCR errors that prevent reliable span selection.
- ID 80: keyword spam and nonsensical word lists dominate the text.
- ID 81: severe multi-layer encoding corruption.
- ID 92: generated nonsense and mixed-language fragments dominate the record.

These records were removed under rule A9 because they were likely to harm model
behavior, not because they were merely difficult to annotate.

### Change Tracking

- `configs/stage1_corrections.yaml`: exact remove/add operations and an English
  reason for every changed or removed record.
- `artifacts/stage1/change_log.json`: generated record-level action log.
- `artifacts/stage1/before_cleanup_stats.json`: raw statistics.
- `artifacts/stage1/after_cleanup_stats.json`: final cleaned statistics.
- `artifacts/stage1/cleanup_summary.json`: comparison, removed IDs, hashes, and
  output paths.

The report summarizes recurring patterns and representative examples; the
manifest and change log preserve the full record-level trail.

### First Cleanup Pass

| Metric | Before | First pass |
| --- | ---: | ---: |
| Records | 100 | 90 |
| Spans | 835 | 610 |
| Changed records | - | 74 |
| Unchanged records | - | 16 |
| Removed records | 0 | 10 |
| Automatic errors | 8 | 0 |
| Automatic warnings | 35 | 17 |

### Second Manual QA

#### Batch 1 - IDs 0-9

- Reviewed: 10.
- Accepted unchanged: 8.
- Corrected: IDs 6 and 9.
- Additional corrections: 3 span boundaries.

Examples:

- ID 6:
  `<TIMEDATE>18 months' treatment</TIMEDATE>` became
  `<TIMEDATE>18 months</TIMEDATE>' treatment`.
  `treatment` is not part of the duration, and the possessive marker stays
  outside the minimal span.
- ID 6:
  `<TIMEDATE>12 month period</TIMEDATE>` became
  `<TIMEDATE>12 month</TIMEDATE> period`.
- ID 9:
  `<TIMEDATE>less than six hours a night</TIMEDATE>` became
  `less than <TIMEDATE>six hours</TIMEDATE> a night`.

#### Batch 2 - IDs 10-19

- Reviewed: 10.
- Accepted unchanged: 10.
- Additional corrections: 0.

The automatic warnings on `an hour` and `a few months` were accepted because
the determiners carry the quantity meaning inside complete duration phrases.

#### Batch 3 - IDs 20-29

- Reviewed: 10.
- Accepted unchanged: 9.
- Corrected: ID 29.

Before:

`Refrain from sharing <AMOUNT>3339</AMOUNT> or
<AMOUNT>483</AMOUNT> on conspicuous platforms.`

After:

`Refrain from sharing 3339 or 483 on conspicuous platforms.`

The numbers function as numeric identifiers, not measurable or countable
quantities. Rule A2 was revised to document this distinction.

#### Final Batch - Remaining 60 Records

| ID group | Reviewed | Accepted unchanged | Corrected |
| --- | ---: | ---: | ---: |
| 30-44 | 15 | 11 | 4 |
| 45-58 | 14 | 11 | 3 |
| 62-74 | 10 | 9 | 1 |
| 76-90 | 13 | 10 | 3 |
| 91-99 | 8 | 8 | 0 |
| **Total** | **60** | **49** | **11** |

Corrections in this batch:

- ID 38: removed generic `Savings Account` from `ORGANIZATION`.
- ID 40: changed fictional country `Spade Kingdom` from `ORGANIZATION` to
  `LOCATION`.
- ID 41: added missing restaurant chain `mcdonalds` as `ORGANIZATION`.
- ID 44: added missing `La Liga` as `ORGANIZATION`.
- ID 45: added missing football club `West Ham` as `ORGANIZATION`.
- ID 54: added political party `Labour` as `ORGANIZATION`.
- ID 58: removed generic `employer` from `JOB`, removed the question
  placeholder `How long` from `TIMEDATE`, and added `GOP` as `ORGANIZATION`.
- ID 66: removed generic `Research Center` from `LOCATION`.
- ID 79: changed casino/establishment `Monte Carlo` from `LOCATION` to
  `ORGANIZATION`.
- ID 82: added frequency `weekly` as `TIMEDATE`.
- ID 84: removed generic `employee` from `JOB`.

### Final Warning Review

All 17 remaining warnings were manually reviewed and accepted:

- Official names beginning with `The`: `The Pledge`, `The New York Times`,
  `The Washington Post`, `The Urban Development Fund`, `The Matrix`, and
  `The Executioner Bug Zapper Racket`.
- Punctuation inside abbreviations: `U.N.` and `M.C.`.
- Possessive form in an official restaurant name: `Andre's`.
- Complete duration/frequency phrases: `a few days`, `an hour`,
  `a few months`, `a year`, and `a month`.
- Internal punctuation in a publication title:
  `The skinny on: 24712 (Athens WV)`.

These are accepted audit exceptions; no structural or invalid-label errors
remain.

### Final Stage 1 Statistics

| Metric | Raw | Clean |
| --- | ---: | ---: |
| Records | 100 | 90 |
| Spans | 835 | 609 |
| Changed records | - | 76 |
| Unchanged records | - | 14 |
| Removed records | 0 | 10 |
| Automatic errors | 8 | 0 |
| Manually accepted warnings | - | 17 |

| Label | Raw | Clean |
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

### Reproducibility and Quality Checks

- Raw SHA256 remained
  `25adafdcbb182fcb524b458abeca3e25ef073c519804783f6b06f9d933609b5a`.
- JSONL and Parquet contain the same 90 record IDs and source texts.
- Repeated cleanup runs produce identical JSONL and Parquet hashes.
- No invalid label, offset, value mismatch, duplicate, or overlap error remains.
- Annotation policy  was finalized after the second manual QA.

### Representative Label Examples

- ID 40:
  `<ORGANIZATION>Spade Kingdom</ORGANIZATION>` became
  `<LOCATION>Spade Kingdom</LOCATION>` because it is a fictional country.
- ID 45:
  `West Ham are hoping...` became
  `<ORGANIZATION>West Ham</ORGANIZATION> are hoping...` because the football
  club was missing from the annotations.
- ID 58:
  `<JOB>employer</JOB> verification procedures` became
  `employer verification procedures` because `employer` is not a concrete
  occupational title or formal work role in this context.

### Publication

The corrected dataset must be published in a separate public Stage 1 Hugging
Face repository. Its dataset card must contain the label definitions, fixed
baseline rules, full policy, source revision, license, statistics, removals,
and usage example.

Hugging Face dataset URL: 
