"""Deterministic schema, offset, boundary, and overlap audit for NER records."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any, Iterable

from polygraf_ner.constants import (
    LABELS,
    REQUIRED_ENTITY_FIELDS,
    REQUIRED_RECORD_FIELDS,
)
from polygraf_ner.io import normalize_json_value

_BARE_CATEGORY_WORDS = {
    "book",
    "city",
    "company",
    "hospital",
    "organization",
    "person",
    "product",
    "quantity",
    "team",
}
_FUNCTION_WORDS = {
    "a",
    "an",
    "and",
    "at",
    "by",
    "for",
    "from",
    "in",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}
_EDGE_PUNCTUATION = set(",.;:!?()[]{}\"")


@dataclass(frozen=True)
class AuditIssue:
    unique_index: Any
    code: str
    severity: str
    message: str
    entity_index: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _issue(
    issues: list[AuditIssue],
    unique_index: Any,
    code: str,
    severity: str,
    message: str,
    entity_index: int | None = None,
) -> None:
    issues.append(
        AuditIssue(
            unique_index=unique_index,
            entity_index=entity_index,
            code=code,
            severity=severity,
            message=message,
        )
    )


def audit_record(record: Any) -> list[AuditIssue]:
    record = normalize_json_value(record)
    issues: list[AuditIssue] = []

    if not isinstance(record, dict):
        _issue(issues, None, "RECORD_NOT_OBJECT", "error", "Record must be an object")
        return issues

    unique_index = record.get("unique_index")
    missing_fields = [field for field in REQUIRED_RECORD_FIELDS if field not in record]
    if missing_fields:
        _issue(
            issues,
            unique_index,
            "RECORD_MISSING_FIELDS",
            "error",
            f"Missing record fields: {missing_fields}",
        )

    if not isinstance(unique_index, int) or isinstance(unique_index, bool):
        _issue(
            issues,
            unique_index,
            "INDEX_INVALID_TYPE",
            "error",
            "unique_index must be an integer",
        )

    source_text = record.get("source_text")
    if not isinstance(source_text, str):
        _issue(
            issues,
            unique_index,
            "TEXT_INVALID_TYPE",
            "error",
            "source_text must be a string",
        )
        return issues
    if not source_text:
        _issue(issues, unique_index, "TEXT_EMPTY", "error", "source_text is empty")

    entities = record.get("privacy_mask")
    if not isinstance(entities, list):
        _issue(
            issues,
            unique_index,
            "MASK_INVALID_TYPE",
            "error",
            "privacy_mask must be a list",
        )
        return issues

    valid_offsets: list[tuple[int, int, int, str | None]] = []
    seen_entities: set[tuple[Any, ...]] = set()

    for entity_index, entity in enumerate(entities):
        if not isinstance(entity, dict):
            _issue(
                issues,
                unique_index,
                "ENTITY_NOT_OBJECT",
                "error",
                "Entity must be an object",
                entity_index,
            )
            continue

        missing_entity_fields = [
            field for field in REQUIRED_ENTITY_FIELDS if field not in entity
        ]
        if missing_entity_fields:
            _issue(
                issues,
                unique_index,
                "ENTITY_MISSING_FIELDS",
                "error",
                f"Missing entity fields: {missing_entity_fields}",
                entity_index,
            )

        start, end = entity.get("start"), entity.get("end")
        label, value = entity.get("label"), entity.get("value")

        offsets_are_int = (
            isinstance(start, int)
            and not isinstance(start, bool)
            and isinstance(end, int)
            and not isinstance(end, bool)
        )
        offsets_are_valid = False
        if not offsets_are_int:
            _issue(
                issues,
                unique_index,
                "OFFSET_INVALID_TYPE",
                "error",
                "start and end must be integers",
                entity_index,
            )
        elif start < 0 or end > len(source_text) or start >= end:
            _issue(
                issues,
                unique_index,
                "OFFSET_OUT_OF_BOUNDS",
                "error",
                f"Invalid half-open span [{start}, {end}) for text length {len(source_text)}",
                entity_index,
            )
        else:
            offsets_are_valid = True
            valid_offsets.append((start, end, entity_index, label))

        if label not in LABELS:
            _issue(
                issues,
                unique_index,
                "LABEL_INVALID",
                "error",
                f"Unknown label: {label!r}",
                entity_index,
            )

        if not isinstance(value, str):
            _issue(
                issues,
                unique_index,
                "VALUE_INVALID_TYPE",
                "error",
                "value must be a string",
                entity_index,
            )
        elif offsets_are_valid:
            observed = source_text[start:end]
            if value != observed:
                _issue(
                    issues,
                    unique_index,
                    "VALUE_OFFSET_MISMATCH",
                    "error",
                    f"value={value!r}, source_text[start:end]={observed!r}",
                    entity_index,
                )

            if observed != observed.strip():
                _issue(
                    issues,
                    unique_index,
                    "BOUNDARY_WHITESPACE",
                    "warning",
                    "Span includes leading or trailing whitespace",
                    entity_index,
                )

            if observed and (
                observed[0] in _EDGE_PUNCTUATION
                or observed[-1] in _EDGE_PUNCTUATION
            ):
                _issue(
                    issues,
                    unique_index,
                    "BOUNDARY_PUNCTUATION",
                    "warning",
                    f"Span has edge punctuation: {observed!r}",
                    entity_index,
                )

            observed_lower = observed.casefold()
            if observed_lower.endswith(("'s", "’s")):
                _issue(
                    issues,
                    unique_index,
                    "POSSESSIVE_INCLUDED",
                    "warning",
                    f"Span includes a possessive marker: {observed!r}",
                    entity_index,
                )

            if observed_lower.strip() in _BARE_CATEGORY_WORDS:
                _issue(
                    issues,
                    unique_index,
                    "BARE_CATEGORY_WORD",
                    "warning",
                    f"Possible bare category word: {observed!r}",
                    entity_index,
                )

            words = observed_lower.strip().split()
            if len(words) > 1 and (
                words[0] in _FUNCTION_WORDS or words[-1] in _FUNCTION_WORDS
            ):
                _issue(
                    issues,
                    unique_index,
                    "FUNCTION_WORD_BOUNDARY",
                    "warning",
                    f"Span starts or ends with a function word: {observed!r}",
                    entity_index,
                )

        signature = (start, end, label, value)
        if signature in seen_entities:
            _issue(
                issues,
                unique_index,
                "DUPLICATE_ENTITY",
                "error",
                f"Duplicate entity: {signature!r}",
                entity_index,
            )
        seen_entities.add(signature)

    original_offsets = [(start, end) for start, end, _, _ in valid_offsets]
    if original_offsets != sorted(original_offsets):
        _issue(
            issues,
            unique_index,
            "ENTITIES_UNSORTED",
            "warning",
            "Entities are not ordered by start/end offset",
        )

    sorted_offsets = sorted(valid_offsets)
    for previous, current in zip(sorted_offsets, sorted_offsets[1:]):
        previous_start, previous_end, previous_index, _ = previous
        current_start, current_end, current_index, _ = current
        if current_start < previous_end:
            _issue(
                issues,
                unique_index,
                "OVERLAPPING_ENTITIES",
                "error",
                (
                    f"Entity {previous_index} [{previous_start}, {previous_end}) "
                    f"overlaps entity {current_index} [{current_start}, {current_end})"
                ),
            )

    return issues


def audit_dataset(
    records: Iterable[dict[str, Any]], expected_records: int | None = None
) -> dict[str, Any]:
    normalized_records = [normalize_json_value(record) for record in records]
    issues: list[AuditIssue] = []

    for record in normalized_records:
        issues.extend(audit_record(record))

    indices = [
        record.get("unique_index")
        for record in normalized_records
        if isinstance(record, dict)
    ]
    duplicate_indices = sorted(
        index for index, count in Counter(indices).items() if count > 1
    )
    for index in duplicate_indices:
        _issue(
            issues,
            index,
            "DUPLICATE_UNIQUE_INDEX",
            "error",
            f"unique_index occurs {indices.count(index)} times",
        )

    if expected_records is not None and len(normalized_records) != expected_records:
        _issue(
            issues,
            None,
            "UNEXPECTED_RECORD_COUNT",
            "error",
            f"Expected {expected_records} records, found {len(normalized_records)}",
        )

    label_counts: Counter[str] = Counter()
    spans_total = 0
    for record in normalized_records:
        if not isinstance(record, dict):
            continue
        entities = record.get("privacy_mask")
        if not isinstance(entities, list):
            continue
        spans_total += len(entities)
        label_counts.update(
            entity.get("label")
            for entity in entities
            if isinstance(entity, dict) and isinstance(entity.get("label"), str)
        )

    issue_counts = Counter(issue.code for issue in issues)
    severity_counts = Counter(issue.severity for issue in issues)
    error_records = {
        issue.unique_index
        for issue in issues
        if issue.severity == "error" and issue.unique_index is not None
    }
    warning_records = {
        issue.unique_index
        for issue in issues
        if issue.severity == "warning" and issue.unique_index is not None
    }
    affected_records = error_records | warning_records

    return {
        "summary": {
            "records_total": len(normalized_records),
            "unique_indices": len(set(indices)),
            "spans_total": spans_total,
            "label_counts": {
                label: label_counts.get(label, 0) for label in LABELS
            },
            "unknown_label_counts": {
                label: count
                for label, count in sorted(label_counts.items())
                if label not in LABELS
            },
            "issues_total": len(issues),
            "issue_counts": dict(sorted(issue_counts.items())),
            "severity_counts": dict(sorted(severity_counts.items())),
            "records_with_errors": len(error_records),
            "records_with_warnings": len(warning_records),
            "records_flagged": len(affected_records),
            "records_without_automatic_flags": (
                len(normalized_records) - len(affected_records)
            ),
        },
        "issues": [issue.to_dict() for issue in issues],
    }
