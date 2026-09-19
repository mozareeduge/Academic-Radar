# QA RECONCILIATION NOTES

**qa_snapshot_id:** `RADAR-QA-2026-09-17-r1`  
**authority:** `RADAR-PDA-2026-09-17-r2`

## What was challenged before implementation

The QA derivation identified and caused Layer-1 revision before oracle freeze:

1. `MA_FUNDING_ROUTE` as a peer application route would duplicate programme cases and confuse funding alternatives. Repaired as `FundingAssessment`.
2. “Research complete” lacked a protocol-level stopping condition. Added `ResearchProtocol`.
3. Evidence authority and independence were implicit. Added explicit source authority + canonical-origin semantics.
4. Deadline normalization lacked precision/timezone rules. Added original representation + precision semantics.
5. Arbitrary crawled sources create a prompt-injection/control-boundary risk. Added untrusted-source product invariant.
6. Evidence change propagation lacked explicit dependency edges. Added `EvidenceDependency`.
7. LLM/system suggestion authority was underspecified. Suggestion is now deterministic downstream of stored evidence/assessments.
8. Entity resolution was not strong enough to prevent cross-person evidence contamination. Added identity-before-relation invariant.

These are product-authority repairs, not QA inventions.

## No-candidate honesty

There is no Mozare Academic Radar candidate. Therefore:
- no E2E was executed;
- no browser/device PASS is claimed;
- no security PASS is claimed;
- no model robustness PASS is claimed;
- donor CIK tests/architecture do not count as target evidence.

## Risk ordering used for downstream execution

1. evidence epistemics / source authority;
2. prompt injection and autonomous-side-effect boundary;
3. identity and dependency integrity;
4. eligibility/funding/deadline correctness;
5. user-state persistence;
6. failure/cancellation;
7. application-brief provenance;
8. accessibility/responsive reachability;
9. visual/interaction quality.

## QA stop condition

Satisfied for pre-code:

`QA_CONTRACT_READY_FOR_EXECUTION`
