"""Display a selected record range for manual annotation review."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from polygraf_ner.audit import audit_record  # noqa: E402
from polygraf_ner.io import read_jsonl, render_xml  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument(
        "--input",
        type=Path,
        default=REPO_ROOT
        / "data"
        / "raw"
        / "stage1_starter"
        / "starter_100.jsonl",
    )
    args = parser.parse_args()

    records = read_jsonl(args.input)
    for record in records:
        index = record["unique_index"]
        if not args.start <= index < args.end:
            continue
        issues = audit_record(record)
        print(f"\n### {index}")
        print(render_xml(record["source_text"], record["privacy_mask"]))
        print(
            "FLAGS:",
            ", ".join(sorted({issue.code for issue in issues})) or "none",
        )


if __name__ == "__main__":
    main()
