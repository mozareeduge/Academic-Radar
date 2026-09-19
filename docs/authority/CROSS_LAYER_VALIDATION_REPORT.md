# CROSS-LAYER VALIDATION REPORT

**Validation date:** 2026-09-17  
**Scope:** Product/Design r2 + QA r1 + Execution r1  
**Validation type:** structural + semantic + current-donor/platform reconciliation.  
**Important:** this validates the *handoff package*, not a target implementation.

## Verdict

`PACKAGE_INTEGRITY_VALIDATED_FOR_CODE_EXECUTION`

No product/design blocker remains. No runtime product PASS is asserted.

## A. Product/design closure checks

### A1. Evaluation unit
PASS — one canonical unit is used across layers:

`MozareRoute × TargetEntity × ApplicationRoute`

Funding was corrected from a peer route into a linked `FundingAssessment`, preventing duplicate MA cases.

### A2. State authority
PASS — four meanings are separated:
- research lifecycle;
- system suggestion;
- user disposition;
- application stage.

Automation is prohibited from overwriting user disposition.

### A3. Unknown / contradiction semantics
PASS — Unknown is first-class; contradiction is preserved; neither is silently converted into a score.

### A4. Research completion
PASS after revision — r1 had an implicit stop rule. r2 adds versioned `ResearchProtocol`, mandatory evidence classes, and explicit `searched none found` vs `not searched`.

### A5. Evidence authority
PASS after revision — source authority and source independence/canonical origin are explicit.

### A6. Temporal semantics
PASS after revision — deadline original wording, precision, timezone, normalization, and ambiguity are defined.

### A7. Hostile-source boundary
PASS after revision — arbitrary web/PDF content is untrusted data, never control instruction.

### A8. Incremental invalidation
PASS after revision — evidence dependency edges define targeted staleness/recomputation.

## B. QA integrity checks

### B1. Candidate honesty
PASS — candidate is explicitly absent; runtime results remain `UNTESTED`.

### B2. Oracle authority
PASS — 45 numbered binding oracles plus 2 heuristic quality oracles are frozen against Product/Design r2.

### B3. High-risk coverage
PASS — release-blocking proof obligations exist for:
- route isolation;
- user decision persistence;
- protocol completeness;
- unsupported AI output;
- prompt injection;
- identity collision;
- source authority;
- deadline normalization;
- dependency invalidation;
- funding arithmetic;
- application brief provenance;
- no autonomous outreach.

### B4. Negative controls
PASS — canaries are mandatory. A perfect-green campaign without canary sensitivity is invalid.

### B5. Evidence-mode correctness
PASS — donor inspection is not treated as target execution evidence.

## C. Execution-intake checks

### C1. Architecture proportionality
PASS — donor stack is reused rather than replaced. Additional infrastructure is introduced only for missing capabilities.

### C2. State source of truth
PASS — PostgreSQL owns semantic durable state; client/RQ/LangGraph/external APIs do not become competing semantic stores.

### C3. Job orchestration
PASS — RQ transports jobs; LangGraph runs inside deep-research jobs. No duplicate scheduler/orchestrator is required.

### C4. Crawling strategy
PASS — tiered fetching prevents browser automation from becoming the default cost/performance path.

### C5. Scholarly APIs
PASS with current correction:
- OpenAlex current REST API remains the structured scholarly source.
- OpenAIRE production Graph API **v3** is used; beta v4 is deliberately not the V1 default.

### C6. Scope control
PASS — Neo4j, vector DB, Activepieces, changedetection.io, public multi-user hosting, and Tauri release are outside the first release candidate unless a concrete blocker later justifies them.

### C7. Release topology
PASS — local/self-hosted Docker Compose is enough for the defined terminal state. No fabricated production domain/credentials are required.

### C8. Task dependency order
PASS — schema/evidence/protocol/security are implemented before final research UI and application brief.

## D. Cross-layer traceability checks

PASS — critical scenario families have explicit oracle and task families.

Particular high-risk chains:

1. `SCN-039 → ORACLE-012/033 → QA-P06/P15 → TASK-P09 → GATE-SECURITY`
2. `SCN-040 → ORACLE-008/009 → QA-P04 → TASK-P07/P08 → GATE-TARGETED`
3. `SCN-048 → ORACLE-013 → QA-P07 → TASK-P05 → GATE-TARGETED`
4. `SCN-043/044 → ORACLE-017/018 → QA-P09 → TASK-P11 → GATE-TARGETED`
5. `SCN-034/045 → ORACLE-020 → QA-P10 → TASK-P12 → GATE-FULL`
6. `SCN-035/047 → ORACLE-002/003/042 → QA-P02 → TASK-P10/P15 → GATE-FULL`
7. `SCN-028 → ORACLE-029 → QA-P13 → TASK-P10/P17 → GATE-TARGETED`
8. `SCN-036/037 → ORACLE-032 → QA-P14 → TASK-P19 → GATE-TARGETED`

## E. Supersession / leakage audit

Expected historical/supersession mentions remain:
- `MA_FUNDING_ROUTE` appears only when documenting the r1 correction.
- donor `0–100` / “ranked by fit” language appears only as explicitly superseded behavior.
- “fully funded” and “high chance” appear only in rules preventing unsupported use or in negative test cases.

No active target contract reintroduces them.

## F. Remaining uncertainty — intentionally deferred

These are not blockers for code execution:

1. exact LLM provider/model;
2. real production hosting/domain;
3. owner’s paid-service credentials;
4. exact watch cadence defaults after empirical cost measurements;
5. numeric performance SLA;
6. future external notifications/email integration;
7. whether Tauri desktop packaging is useful after web/local RC exists.

They are intentionally deferred because deciding them now would add implementation coupling without improving V1 product truth.

## G. Validation limitations

This report cannot prove:
- crawler success on every live academic site;
- model research quality;
- visual quality in a running browser;
- accessibility in the target;
- performance;
- migrations;
- security boundary implementation.

Those remain exact-candidate QA obligations in Layer 2/3.

## Final state

- Product/design authority: CLOSED
- QA contract: READY
- Execution intake: READY
- Package: VALIDATED FOR CODE EXECUTION
- Target runtime: UNTESTED
