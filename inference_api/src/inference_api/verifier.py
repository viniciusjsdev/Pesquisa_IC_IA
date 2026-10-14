"""Partial deterministic checks; no gold set or truth judging."""
import re

from .contracts import CheckResult, EvidenceBundle, ModelOutput, SCHEMA_VERSION


def cited_ids(raw_text: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(re.findall(r"\[evidence:([^\]]+)\]", raw_text)))


def check(bundle: EvidenceBundle, output: ModelOutput) -> tuple[CheckResult, ...]:
    items = {item.id: item for item in bundle.items}
    required = {f"{tool}:{bundle.route.year}" for tool in bundle.route.tools}
    evidence_ok = (bundle.schema_version == SCHEMA_VERSION and
                   all(item.schema_version == SCHEMA_VERSION for item in bundle.items) and
                   required == set(items) and all(item.record_count > 0 for item in bundle.items))
    unknown = set(output.cited_evidence_ids) - set(items)
    return (
        CheckResult(SCHEMA_VERSION, "schema_and_required_evidence",
                    "passed" if evidence_ok else "failed",
                    "Bundle version, required IDs and nonempty source records."),
        CheckResult(SCHEMA_VERSION, "model_call_and_response",
                    "passed" if isinstance(output.raw_text, str) and output.raw_text.strip() else "failed",
                    "One model response returned and preserved."),
        CheckResult(SCHEMA_VERSION, "cited_evidence_ids",
                    "failed" if unknown else "passed" if output.cited_evidence_ids else "not_checked",
                    "Unknown IDs: " + ", ".join(sorted(unknown)) if unknown else
                    "All cited IDs exist." if output.cited_evidence_ids else "No evidence IDs cited."),
        CheckResult(SCHEMA_VERSION, "numerical_truth", "not_checked",
                    "No independent numerical gold set in exploratory execution."),
        CheckResult(SCHEMA_VERSION, "causality", "not_checked",
                    "Temporal association does not establish causality."),
    )
