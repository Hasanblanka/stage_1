"""Run the deterministic Stage 1 audit and create a manual review queue."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from polygraf_ner.audit import audit_dataset  # noqa: E402
from polygraf_ner.io import read_jsonl, render_xml, write_json  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=REPO_ROOT / "configs" / "project.yaml",
    )
    parser.add_argument(
        "--fail-on-errors",
        action="store_true",
        help="Return a non-zero exit code if deterministic errors are found.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    stage = config["stage1"]
    raw_path = REPO_ROOT / stage["raw_dir"] / "starter_100.jsonl"
    artifact_dir = REPO_ROOT / stage["artifact_dir"]
    artifact_dir.mkdir(parents=True, exist_ok=True)

    records = read_jsonl(raw_path)
    result = audit_dataset(records, expected_records=stage["expected_records"])
    write_json(result, artifact_dir / "automatic_audit.json")
    write_json(result["summary"], artifact_dir / "before_cleanup_stats.json")

    issues_by_index: dict[object, list[dict[str, object]]] = defaultdict(list)
    for issue in result["issues"]:
        issues_by_index[issue["unique_index"]].append(issue)

    review_path = artifact_dir / "manual_review_queue.csv"
    with review_path.open("w", encoding="utf-8-sig", newline="") as handle:
        fieldnames = [
            "unique_index",
            "priority",
            "issue_codes",
            "issue_details",
            "source_text",
            "annotated_text",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            record_issues = issues_by_index.get(record["unique_index"], [])
            priority = (
                "error"
                if any(issue["severity"] == "error" for issue in record_issues)
                else "warning"
                if record_issues
                else "manual"
            )
            writer.writerow(
                {
                    "unique_index": record["unique_index"],
                    "priority": priority,
                    "issue_codes": " | ".join(
                        sorted({str(issue["code"]) for issue in record_issues})
                    ),
                    "issue_details": " | ".join(
                        str(issue["message"]) for issue in record_issues
                    ),
                    "source_text": record["source_text"],
                    "annotated_text": render_xml(
                        record["source_text"], record["privacy_mask"]
                    ),
                }
            )

    summary = result["summary"]
    print(
        f"Audited {summary['records_total']} records / "
        f"{summary['spans_total']} spans"
    )
    print(
        f"Automatic flags: {summary['records_flagged']} records, "
        f"{summary['issues_total']} issues"
    )
    print(f"Audit JSON: {artifact_dir / 'automatic_audit.json'}")
    print(f"Review queue: {review_path}")

    if args.fail_on_errors and summary["severity_counts"].get("error", 0):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
