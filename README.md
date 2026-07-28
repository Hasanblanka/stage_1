Reproducible implementation of Stage 1 - Rulecraft and Cleanup for the English
NER technical task.

## Stage 1 Status

- All 100 raw records were reviewed.
- The raw dataset was not overwritten.
- Annotation policy was finalized before publication.
- All 90 retained records passed a second manual QA review.
- Final result: 76 changed, 14 unchanged, and 10 removed records.
- Final cleaned dataset: 90 records and 609 spans.
- Automatic structural errors: 0.
- The remaining 17 audit warnings were manually reviewed and accepted as valid
  names, abbreviations, possessive official names, or duration/frequency spans.

The cleaned dataset files are distributed through the separate Stage 1 Hugging
Face dataset repository. The public URL must be added here after publication.

## Environment

All Python commands were executed in the `machinelearning` Conda environment.

```powershell
conda run -n machinelearning python --version
```

To recreate the environment:

```powershell
conda env create -f environment.stage1.yml
```

## Reproduce Stage 1

```powershell
conda run -n machinelearning python scripts/stage1/download_starter.py
conda run -n machinelearning python scripts/stage1/audit_starter.py
conda run -n machinelearning python scripts/stage1/apply_cleanup.py
```

The download script retrieves the pinned raw source. The audit script creates
the automatic audit and local manual review queue. The cleanup script applies
`configs/stage1_corrections.yaml` to a copy of the raw dataset and writes the
clean JSONL/Parquet files and audit artifacts.

## Reports

- `reports/technical_report.md`: detailed approach, decisions, policy changes,
  QA results, statistics, and representative examples.
- `reports/stage1_summary.md`: short Stage 1 summary.
- `output/pdf/polygraf_ner_stage1_report.pdf`: two-page visual summary.

Regenerate the PDF:

```powershell
conda run -n machinelearning python scripts/report/create_project_report.py
```

## Repository Structure

```text
artifacts/              Small audit results and summary statistics
configs/                Project configuration and correction manifest
policies/               Fixed baseline and additional annotation policy
reports/                Detailed and short Stage 1 reports
scripts/                Download, audit, cleanup, inspection, and report scripts
src/polygraf_ner/       Reusable data I/O and deterministic audit code
```

Raw and processed datasets are intentionally excluded from GitHub and should
live in their corresponding Hugging Face repositories.
