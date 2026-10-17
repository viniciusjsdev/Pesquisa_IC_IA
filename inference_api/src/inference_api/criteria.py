"""Bounded, declarative exploratory checks. No user expression is executed."""

CRITERIA_VERSION = 1
DEFAULT = {
    "schema_version": CRITERIA_VERSION,
    "require_evidence": True,
    "require_period": True,
    "required_units": [],
    "require_cited_ids": False,
    "required_caveats": [],
}


def validate(value: object) -> dict:
    """Return a clean copy, rejecting unknown keys and oversized plain text."""
    if not isinstance(value, dict) or set(value) != set(DEFAULT):
        raise ValueError("Criteria must contain only the documented structured fields")
    if type(value["schema_version"]) is not int or value["schema_version"] != CRITERIA_VERSION:
        raise ValueError("Unsupported criteria schema_version")
    for key in ("require_evidence", "require_period", "require_cited_ids"):
        if type(value[key]) is not bool:
            raise ValueError(f"{key} must be a boolean")
    for key in ("required_units", "required_caveats"):
        entries = value[key]
        if not isinstance(entries, list) or len(entries) > 8:
            raise ValueError(f"{key} must be a list of at most 8 strings")
        limit = 80 if key == "required_units" else 160
        if any(not isinstance(item, str) or not item.strip() or len(item) > limit
               for item in entries):
            raise ValueError(f"{key} contains an empty or oversized string")
        if len(set(entries)) != len(entries):
            raise ValueError(f"{key} contains duplicates")
    return {key: list(value[key]) if isinstance(value[key], list) else value[key]
            for key in DEFAULT}
