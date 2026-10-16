"""Bounded, declarative exploratory checks. No user expression is executed."""

from .contracts import CheckResult, EvidenceBundle, ModelOutput, SCHEMA_VERSION

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


def check(bundle: EvidenceBundle, output: ModelOutput, config: dict) -> tuple[CheckResult, ...]:
    """Literal/schema checks only; they do not establish truth or causality."""
    config = validate(config)
    items = bundle.items
    results = []
    if config["require_evidence"]:
        ok = (bundle.schema_version == SCHEMA_VERSION and bundle.quality == "available"
              and bool(items) and all(item.record_count > 0 for item in items))
        results.append(CheckResult(SCHEMA_VERSION, "criteria_evidence_presence",
                                   "passed" if ok else "failed", "Evidence bundle has source records."))
    if config["require_period"]:
        ok = bool(items) and all(item.period.get("year") == bundle.route.year for item in items)
        results.append(CheckResult(SCHEMA_VERSION, "criteria_period",
                                   "passed" if ok else "failed", "Evidence items use the declared year."))
    for unit in config["required_units"]:
        ok = any(item.unit == unit for item in items)
        results.append(CheckResult(SCHEMA_VERSION, "criteria_unit",
                                   "passed" if ok else "failed", f"Required literal unit: {unit}"))
    if config["require_cited_ids"]:
        ids = set(output.cited_evidence_ids)
        ok = bool(ids) and ids <= {item.id for item in items}
        results.append(CheckResult(SCHEMA_VERSION, "criteria_cited_ids",
                                   "passed" if ok else "failed", "Cited IDs must exist in this bundle."))
    for phrase in config["required_caveats"]:
        ok = phrase.casefold() in (output.raw_text or "").casefold()
        results.append(CheckResult(SCHEMA_VERSION, "criteria_caveat_literal",
                                   "passed" if ok else "failed", f"Required literal caveat: {phrase}"))
    return tuple(results)
