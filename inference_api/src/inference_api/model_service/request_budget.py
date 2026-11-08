"""Bound the exact HTTP JSON body, without retaining credentials or payload text."""
import hashlib
import json

POLICY = "http_json_body_utf8_v1"


class RequestBudgetExceeded(ValueError):
    def __init__(self, receipt: dict):
        super().__init__("input_context_limit")
        self.receipt = receipt


def encode_request(payload: dict, limit: int | None = None) -> tuple[bytes, dict]:
    body = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
    receipt = {"policy": POLICY, "bytes": len(body), "limit_bytes": limit,
               "sha256": hashlib.sha256(body).hexdigest()}
    if limit is not None:
        if type(limit) is not int or limit < 1:
            raise ValueError("invalid_request_byte_limit")
        if len(body) > limit:
            raise RequestBudgetExceeded(receipt)
    return body, receipt
