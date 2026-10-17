"""Private, immutable packet lookup by case ID and body SHA-256."""
import hashlib
import os
from pathlib import Path
import re
import sys

from .config import ROOT, packet_directory

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from model_evaluation.export import CASE_ID, MAX_BYTES, verify_packet_bytes  # noqa: E402

SHA = re.compile(r"[0-9a-f]{64}\Z")


def _read(path: Path) -> tuple[dict, bytes]:
    if path.is_symlink() or not path.is_file() or path.suffix != ".json" or not CASE_ID.fullmatch(path.stem):
        raise ValueError("Invalid or linked evidence packet file")
    # O_NOFOLLOW protects the final component on platforms that implement it.
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        if os.fstat(fd).st_size > MAX_BYTES:
            raise ValueError("Evidence packet exceeds size limit")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            payload = stream.read(MAX_BYTES + 1)
    finally:
        os.close(fd)
    packet = verify_packet_bytes(payload, expected_case_id=path.stem)
    return packet, payload


def _directory() -> Path:
    directory = packet_directory()
    if any(part.is_symlink() for part in (directory, *directory.parents)):
        raise ValueError("Linked packet directory is forbidden")
    return directory


def list_packets() -> list[dict]:
    directory = _directory()
    if not directory.exists():
        return []
    if not directory.is_dir():
        raise ValueError("Packet location is not a directory")
    result = []
    seen = set()
    for path in sorted(directory.iterdir()):
        packet, payload = _read(path)
        body = packet["body"]
        key = body["case_id"].casefold()
        if key in seen:
            raise ValueError("Duplicate evidence packet case ID")
        seen.add(key)
        result.append({"case_id": body["case_id"], "sha256": packet["sha256"],
                       "file_sha256": hashlib.sha256(payload).hexdigest(),
                       "question": body["question"], "domain": body["domain"],
                       "source_snapshot": body["source_snapshot"]})
    return result


def select_packet(case_id: str, sha256: str) -> tuple[dict, bytes]:
    if not isinstance(case_id, str) or not CASE_ID.fullmatch(case_id):
        raise ValueError("Invalid case_id")
    if not isinstance(sha256, str) or not SHA.fullmatch(sha256):
        raise ValueError("Invalid packet SHA-256")
    directory = _directory()
    if not directory.is_dir():
        raise ValueError("No evidence packets configured")
    # Validate all files so duplicates and invalid files cannot be bypassed.
    matches = [item for item in list_packets() if item["case_id"] == case_id]
    if len(matches) != 1 or matches[0]["sha256"] != sha256:
        raise ValueError("Evidence packet ID/hash not found")
    packet, payload = _read(directory / f"{case_id}.json")
    if packet["sha256"] != sha256:
        raise ValueError("Evidence packet changed during selection")
    return packet, payload
