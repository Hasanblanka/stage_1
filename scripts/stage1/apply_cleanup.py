"""Apply the correction manifest to a copy of the raw dataset."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from polygraf_ner.audit import audit_dataset  # noqa: E402
from polygraf_ner.io import read_jsonl, sha256_file, write_json, write_jsonl  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=REPO_ROOT / "configs" / "project.yaml",
    )
    parser.add_argument(
        "--corrections",
        type=Path,
        default=REPO_ROOT / "configs" / "stage1_corrections.yaml",
    )
    return parser.parse_args()


def find_text_occurrences(text: str, value: str) -> list[tuple[int, int]]:
    occurrences: list[tuple[int, int]] = []
    cursor = 0
    while True:
        start = text.find(value, cursor)
        if start < 0:
            break
        occurrences.append((start, start + len(value)))
        cursor = start + 1
    return occurrences


def entity_matches(entity: dict[str, Any], spec: dict[str, Any]) -> bool:
    return all(
        entity.get(field) == spec[field]
        for field in ("label", "value", "start", "end")
        if field in spec
    )


def remove_entities(
    entities: list[dict[str, Any]],
    specs: list[dict[str, Any]],
    record_id: int,
) -> list[dict[str, Any]]:
    result = list(entities)
    for spec in specs:
        matches = [
            index
            for index, entity in enumerate(result)
            if entity_matches(entity, spec)
        ]
        if not matches:
            raise ValueError(f"Record {record_id}: entity to remove was not found: {spec}")
        if spec.get("all", False):
            selected = set(matches)
        else:
            occurrence = int(spec.get("occurrence", 1))
            if occurrence < 1 or occurrence > len(matches):
                raise ValueError(
                    f"Record {record_id}: entity occurrence does not exist: {spec}"
                )
            selected = {matches[occurrence - 1]}
        result = [
            entity for index, entity in enumerate(result) if index not in selected
        ]
    return result


def add_entities(
    text: str,
    entities: list[dict[str, Any]],
    specs: list[dict[str, Any]],
    record_id: int,
) -> list[dict[str, Any]]:
    result = list(entities)
    for spec in specs:
        value = str(spec["value"])
        label = str(spec["label"])
        occurrences = find_text_occurrences(text, value)
        if not occurrences:
            raise ValueError(f"Record {record_id}: value was not found in text: {spec}")
        if spec.get("all", False):
            selected = occurrences
        else:
            occurrence = int(spec.get("occurrence", 1))
            if occurrence < 1 or occurrence > len(occurrences):
                raise ValueError(
                    f"Record {record_id}: text occurrence does not exist: {spec}"
                )
            selected = [occurrences[occurrence - 1]]

        for start, end in selected:
            entity = {"start": start, "end": end, "label": label, "value": value}
            if entity in result:
                raise ValueError(f"Record {record_id}: duplicate entity addition: {entity}")
            result.append(entity)
    return result


def ensure_no_overlap(record: dict[str, Any]) -> None:
    entities = sorted(
        record["privacy_mask"], key=lambda item: (item["start"], item["end"])
    )
    for previous, current in zip(entities, entities[1:]):
        if current["start"] < previous["end"]:
            raise ValueError(
                f"Record {record['unique_index']}: overlapping entities: "
                f"{previous} and {current}"
            )


def count_labels(records: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for record in records:
        counts.update(entity["label"] for entity in record["privacy_mask"])
    return dict(sorted(counts.items()))


def main() -> None:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    corrections = yaml.safe_load(args.corrections.read_text(encoding="utf-8"))

    raw_path = REPO_ROOT / config["stage1"]["raw_dir"] / "starter_100.jsonl"
    output_dir = REPO_ROOT / "data" / "processed" / "stage1_cleaned"
    artifact_dir = REPO_ROOT / config["stage1"]["artifact_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    raw_hash_before = sha256_file(raw_path)
    raw_records = read_jsonl(raw_path)
    records_by_id = {record["unique_index"]: record for record in raw_records}
    removal_ids = {
        int(item["unique_index"]) for item in corrections.get("remove_records", [])
    }
    unknown_removals = removal_ids - set(records_by_id)
    if unknown_removals:
        raise ValueError(f"Unknown removal IDs: {sorted(unknown_removals)}")

    cleaned_records: list[dict[str, Any]] = []
    change_log: list[dict[str, Any]] = []
    correction_map = {
        int(record_id): decision
        for record_id, decision in corrections.get("records", {}).items()
    }

    for raw_record in raw_records:
        record_id = raw_record["unique_index"]
        if record_id in removal_ids:
            removal = next(
                item
                for item in corrections["remove_records"]
                if int(item["unique_index"]) == record_id
            )
            change_log.append(
                {
                    "unique_index": record_id,
                    "action": "removed",
                    "reason": removal["reason"],
                    "spans_before": len(raw_record["privacy_mask"]),
                    "spans_after": 0,
                }
            )
            continue

        record = {
            "unique_index": record_id,
            "source_text": raw_record["source_text"],
            "privacy_mask": [dict(entity) for entity in raw_record["privacy_mask"]],
        }
        decision = correction_map.get(record_id)
        if decision:
            record["privacy_mask"] = remove_entities(
                record["privacy_mask"],
                decision.get("remove", []),
                record_id,
            )
            record["privacy_mask"] = add_entities(
                record["source_text"],
                record["privacy_mask"],
                decision.get("add", []),
                record_id,
            )

        record["privacy_mask"] = sorted(
            record["privacy_mask"],
            key=lambda item: (item["start"], item["end"], item["label"]),
        )
        ensure_no_overlap(record)
        cleaned_records.append(record)

        if record["privacy_mask"] != raw_record["privacy_mask"]:
            change_log.append(
                {
                    "unique_index": record_id,
                    "action": "changed",
                    "reason": decision.get("reason", "Annotation correction"),
                    "spans_before": len(raw_record["privacy_mask"]),
                    "spans_after": len(record["privacy_mask"]),
                }
            )

    unhandled_ids = set(correction_map) - set(records_by_id)
    if unhandled_ids:
        raise ValueError(f"Unknown correction IDs: {sorted(unhandled_ids)}")

    audit_result = audit_dataset(cleaned_records)
    error_count = audit_result["summary"]["severity_counts"].get("error", 0)
    if error_count:
        raise ValueError(f"Clean dataset audit still has {error_count} errors.")

    jsonl_path = output_dir / "stage1_cleaned.jsonl"
    parquet_path = output_dir / "stage1_cleaned.parquet"
    write_jsonl(cleaned_records, jsonl_path)
    pd.DataFrame(cleaned_records).to_parquet(parquet_path, index=False)

    changed_ids = {
        item["unique_index"] for item in change_log if item["action"] == "changed"
    }
    summary = {
        "source_revision": corrections["source_revision"],
        "policy_version": corrections["policy_version"],
        "raw_sha256_before": raw_hash_before,
        "raw_sha256_after": sha256_file(raw_path),
        "raw_unchanged": raw_hash_before == sha256_file(raw_path),
        "records_before": len(raw_records),
        "records_after": len(cleaned_records),
        "records_changed": len(changed_ids),
        "records_unchanged": len(cleaned_records) - len(changed_ids),
        "records_removed": len(removal_ids),
        "removed_ids": sorted(removal_ids),
        "spans_before": sum(len(record["privacy_mask"]) for record in raw_records),
        "spans_after": sum(len(record["privacy_mask"]) for record in cleaned_records),
        "label_counts_before": count_labels(raw_records),
        "label_counts_after": count_labels(cleaned_records),
        "automatic_audit_after": audit_result["summary"],
        "output_files": {
            "jsonl": str(jsonl_path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "parquet": str(parquet_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        },
    }
    write_json(summary, artifact_dir / "cleanup_summary.json")
    write_json(audit_result["summary"], artifact_dir / "after_cleanup_stats.json")
    write_json(change_log, artifact_dir / "change_log.json")

    print(f"Raw record: {len(raw_records)}")
    print(f"Clean records: {len(cleaned_records)}")
    print(f"Changed: {len(changed_ids)}")
    print(f"Removed: {len(removal_ids)}")
    print(f"Raw unchanged: {summary['raw_unchanged']}")
    print(f"Output: {jsonl_path}")


if __name__ == "__main__":
    main()
