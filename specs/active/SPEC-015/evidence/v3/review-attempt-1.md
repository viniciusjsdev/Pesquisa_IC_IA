# Independent review attempt 1 · SPEC-015 contract 3

Decision during implementation: changes requested; subsequently corrected before final review.

Confirmed findings communicated to the implementation agent:

- A with model_calls=3 took a Specialist-to-Writer budget path missing from permitted graph edges and raised KeyError('writer'). The permitted edge was added.
- Selected packet rows were promoted into accumulated evidence before a Specialist had validated its analysis. The budget path could consequently expose unexamined facts/IDs to the Writer. Evidence is now staged and promoted only after successful analysis; the Writer receives no staged item at this boundary.
- Throttled receipt updates could miss the final pending=0 state. Final delivery now forces a coalesced durable update.
- Reconciliation initially checked time/response size only after eager body loading. It now bounds caller time and reads the body incrementally with byte/deadline checks.
- Synchronous receipt persistence around Observer.finish could exceed the advertised flush budget. A coalescing background receipt writer and slow-store regression now isolate it from the inference/final flush path.
- The initial frontend lint record failed for synchronous state updates in an effect. The keyed child component replacement passes an independent canonical lint run.

Independent local checks on the corrected snapshot: 44 focused SPEC-015 methods passed, including 26 v3 methods and 39 preserved B differential cases; canonical frontend lint passed; git diff --check passed. No hosted APIs, paid models or research databases were accessed by the reviewer.

This document preserves the implementation-time audit. The final decision and evidence scope are recorded separately in review.json.

Further combined-boundary findings corrected before final approval:

- A repair pending at selector budget 3, specialist budget 4, or reviewer budget 5 crossed into the reserved Writer with stale role input/feedback and raised ValidationError. The role switch now clears repair state. An independent 45-combination budget/repair matrix (budgets 1–9 by five roles) has no unhandled exceptions after correction.
- Fail-soft receipt reads could make the reconcile endpoint return a null public DTO and discard a previously verified UI link. Reconciliation now falls back to the last authorized receipt with a sanitized storage error, preserving prior verification and URL.

Final focused independent run: 47 methods passed in 5.785 seconds, including the corrected combined boundaries, 29 v3 methods and 39 preserved B differential cases.
