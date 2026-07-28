"""Standard I/O utilities for record-level NER data."""

from __future__ import annotations

import hashlib
import json
from html import escape
from pathlib import Path
from typing import Any, Iterable


def normalize_json_value(value: Any) -> Any:
    """Convert pandas/numpy objects into JSON-compatible Python values."""
    if isinstance(value, dict):
        return {str(key): normalize_json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalize_json_value(item) for item in value]
    if hasattr(value, "tolist"):
        return normalize_json_value(value.tolist())
    if hasattr(value, "item"):
        return normalize_json_value(value.item())
    return value


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"Line {line_number} is not a JSON object")
            records.append(normalize_json_value(value))
    return records


def write_jsonl(records: Iterable[dict[str, Any]], path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(
                json.dumps(
                    normalize_json_value(record),
                    ensure_ascii=False,
                    sort_keys=False,
                )
                + "\n"
            )


def write_json(value: Any, path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(normalize_json_value(value), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def render_xml(source_text: str, entities: list[dict[str, Any]]) -> str:
    """Render valid non-overlapping spans as XML-style report text."""
    valid_entities = [
        entity
        for entity in entities
        if isinstance(entity, dict)
        and isinstance(entity.get("start"), int)
        and isinstance(entity.get("end"), int)
        and 0 <= entity["start"] < entity["end"] <= len(source_text)
        and isinstance(entity.get("label"), str)
    ]
    valid_entities.sort(key=lambda item: (item["start"], item["end"]))

    if any(
        current["start"] < previous["end"]
        for previous, current in zip(valid_entities, valid_entities[1:])
    ):
        return escape(source_text)

    output: list[str] = []
    cursor = 0
    for entity in valid_entities:
        start, end, label = entity["start"], entity["end"], entity["label"]
        output.append(escape(source_text[cursor:start]))
        output.append(f"<{label}>{escape(source_text[start:end])}</{label}>")
        cursor = end
    output.append(escape(source_text[cursor:]))
    return "".join(output)
