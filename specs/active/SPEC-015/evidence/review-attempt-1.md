# Independent review attempt 1 · SPEC-015 contract 2

Review date: 2026-11-08. Decision: changes_requested.

This record preserves the first independent audit communicated to the implementation agent before corrections. It is not a new finding against the corrected snapshot.

1. [P1] Redaction omitted opaque token/access_token/refresh_token credentials; malformed structured model output could fall back to unsanitized content. Reproduced with synthetic values only.
2. [P1] Enabled configuration with malformed IPv6 URL (https://[invalid) raised ValueError before the telemetry initialization exception boundary and could abort inference.
3. [P2] Metadata-mode input hashes were recomputed from already-projected empty inputs, yielding SHA256({}) instead of the sanitized original input fingerprint.
4. [P2] Legacy public engine.run and diagnostic CLI consumers still retained the old orchestration algorithm, conflicting with the single-facade requirement.
5. Additional robustness request: isolate exceptions from private-URL resolution in Observer.finish.

The implementation agent corrected these findings and added regression coverage. Retired legacy algorithms, CLI entry points and protocol-specific tests were externally preserved with hashes, while active boundary/provider/filter tests remained. The final independent decision is in review.json.
