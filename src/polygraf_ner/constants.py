"""Project-wide immutable constants."""

LABELS = (
    "PERSON",
    "ORGANIZATION",
    "LOCATION",
    "TIMEDATE",
    "PRODUCT",
    "WORKOFART",
    "JOB",
    "AMOUNT",
)

REQUIRED_RECORD_FIELDS = ("unique_index", "source_text", "privacy_mask")
REQUIRED_ENTITY_FIELDS = ("start", "end", "label", "value")
