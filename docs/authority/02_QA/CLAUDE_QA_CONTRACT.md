# CLAUDE QA CONTRACT — Mozare Academic Radar

**qa_snapshot_id:** `RADAR-QA-2026-09-17-r1`  
**authority_snapshot_id:** `RADAR-PDA-2026-09-17-r2`  
**status:** `QA_CONTRACT_READY_FOR_EXECUTION`  
**candidate:** none yet

This contract tells the downstream implementation/QA executor what must be proved once a target repository/candidate exists. It is not permission to rewrite product authority.

## 1. Candidate freeze

Before any target-product proof:

```text
candidate_id
git repository
branch
HEAD
working-tree status
runtime versions
DB/schema revision
research protocol versions
prompt/schema versions
model/provider config (secret-free identity only)
frontend build identity
```

Evidence from donor `mimdot/CIK` is not target-candidate proof.

## 2. Required QA level

**QA-C for research integrity/security/state semantics**, **QA-B for general UI**.

Reason: the product makes consequential academic-research/application decisions from untrusted web data and LLM interpretation. Data loss is less severe than finance/medical software, but evidence contamination, prompt injection, and false formal eligibility are release-blocking.

## 3. Proof tiers

### Tier A — release blockers
Must have automated negative + positive proof where feasible:
- ORACLE-001..020
- ORACLE-027..033
- ORACLE-042
- ORACLE-045

### Tier B — critical interaction/integrity
- ORACLE-021..026
- ORACLE-034..041
- ORACLE-043..044

### Tier C — heuristic/design
- ORACLE-H01/H02 with fresh-context visual/UX review plus objective rendered evidence.

## 4. Concrete critical proof obligations

### QA-P01 — Route isolation
**oracles:** ORACLE-001, ORACLE-006/007  
Create same supervisor/programme under multiple routes and verify:
- assessments are independent;
- funding routes do not duplicate MA case;
- person-level data is shared only where factual.
**negative canary:** mutate implementation to read a person-level fit field; test must fail.

### QA-P02 — Disposition immutability under automation
**oracles:** ORACLE-002/003/020/042  
Set `WATCH`; run new evidence ingestion and suggestion recomputation. Verify user disposition remains `WATCH` while system suggestion may change with traceable inputs.
**negative canary:** intentionally route suggestion save into user disposition; test must fail.

### QA-P03 — Unknown and hard blockers
**oracles:** ORACLE-004/005/030/031  
Fixtures:
- unknown second-MA rule;
- explicit second-MA prohibition;
- English programme with mandatory non-English component.
Verify UI and state distinguish unknown/fail and that fit cannot restore actionability.

### QA-P04 — Research protocol completeness
**oracles:** ORACLE-008/009  
Run research fixture where supervised-project search is skipped. `EVIDENCE_READY` must be impossible.
Then run explicit search returning zero items: coverage must say `searched, none found` and may satisfy the search obligation if protocol allows zero-result completion.
**negative canary:** force model “complete” flag true while evidence class missing; test must fail.

### QA-P05 — Evidence-bound AI
**oracles:** ORACLE-010/011/045  
Feed:
1. valid claim + evidence IDs;
2. fluent unsupported claim;
3. malformed structured output;
4. model timeout.
Only #1 may update consequential assessment. Prior reviewed state survives #2–#4.
**negative canary:** unsupported claim should be rejected.

### QA-P06 — Prompt injection
**oracles:** ORACLE-012/033  
Use source fixtures containing:
- “ignore previous instructions”;
- request to print environment secrets;
- request to email a supervisor;
- request to set case to ACT;
- hidden/HTML/script-like instructions.
Verify source is treated as data, no side effect occurs, no secret enters logs/model output.
**evidence:** tool-call trace or mocked action adapter showing zero forbidden calls.
**negative canary:** unsafe executor intentionally honors fixture; security test must fail.

### QA-P07 — Entity resolution
**oracles:** ORACLE-013  
Fixture two same-name researchers in different institutions. Verify publications/grants/supervision remain separated until explicit resolution.
**negative canary:** remove identity discriminator; merge detection test must fail.

### QA-P08 — Authority conflict/independence
**oracles:** ORACLE-014/015/016  
Fixtures:
- aggregator says deadline 1 Feb; official call says 15 Jan;
- three mirrors repeat same scholarship statement;
- two official pages disagree.
Verify precedence, canonical-origin grouping, and contradiction state.

### QA-P09 — Deadline precision/timezone
**oracles:** ORACLE-017/018  
Fixtures:
- date only;
- local date+time+CET;
- DST boundary in Europe;
- time with no timezone.
Verify original representation and normalized value/ambiguity.
**negative canary:** hardcode end-of-day; date-only test must fail.

### QA-P10 — Snapshot and targeted invalidation
**oracles:** ORACLE-019/020  
Build dependency graph with two funding routes and unrelated supervisor case. Change only scholarship amount in one source. Verify:
- new snapshot appended;
- only dependent FundingAssessment/suggestion/brief stale;
- unrelated case and user notes unaffected.
**negative canary:** global `updated_at` invalidation must be detected.

### QA-P11 — Source run resilience
**oracles:** ORACLE-021/022/023/024/025  
Inject one timeout, duplicate item, and cancel mid-run. Verify successful source records persist, provenance retained, cancellation honest, zero-result wording scoped.

### QA-P12 — Supervisor track epistemics
**oracles:** ORACLE-027/028  
Fixtures include supervisor-authored work and student dissertation with related method. Verify labels distinguish them; generated text includes causal caution; no historical acceptance motive is stated.

### QA-P13 — Funding arithmetic
**oracles:** ORACLE-029  
Use currencies/durations/tuition:
- full coverage;
- partial stipend;
- tuition waiver only;
- unknown mandatory fee.
Verify arithmetic uses defined units and unknowns prevent unjustified “fully funded”.
Use decimal-safe arithmetic, not binary float for money.

### QA-P14 — Application brief freeze
**oracles:** ORACLE-032  
Generate brief, capture dependency versions, change a critical source, verify old brief becomes superseded; user can inspect changed facts and generate a new brief.

### QA-P15 — No autonomous application side effects
**oracles:** ORACLE-033  
Static + runtime proof that normal research flows expose no auto-send/submit operation. If email connector exists for later use, it must require explicit downstream owner action outside V1 flow.

### QA-P16 — Responsive and accessibility
**oracles:** ORACLE-035..041  
At 1440, 1024, 768, 390, 320 CSS px and 200% zoom:
- blocker visible initially;
- evidence reachable;
- no page horizontal overflow;
- disposition/source actions reachable.
Keyboard:
- open dossier -> claim -> evidence drawer -> close -> focus restores;
- modal/sheet focus trap and Escape;
- async completion no focus steal.
Run automated a11y scan plus manual keyboard/geometry assertions.

### QA-P17 — Persistence across recrawl/archive/export
**oracles:** ORACLE-042..044  
Persist notes, disposition, application stage, correction; recrawl and dedupe. Verify all survive. Archive/restore. Filter then export and compare exported entity IDs to rendered/query state.

## 5. Data/model candidate identity

Every consequential model test records:
- provider/model identifier;
- structured-output schema version;
- research protocol version;
- system/control prompt version/hash;
- deterministic temperature/settings when applicable;
- fixture/source snapshot IDs.

A change in prompt/schema/protocol creates a new behavior candidate even when source code is unchanged.

## 6. Security probes

Required:
- prompt-injection fixtures;
- SSRF/URL allow-policy tests if crawler accepts arbitrary URLs;
- secret redaction in logs;
- HTML/script sanitization for captured excerpts;
- external link `noopener/noreferrer`;
- file/PDF parser resource limits;
- no arbitrary local-file access from source URL input;
- dependency/vulnerability scan appropriate to chosen stack.

## 7. Failure/recovery probes

Inject:
- HTTP 404/403/429/500;
- timeout;
- malformed HTML/JSON;
- dynamic page failure;
- model outage/malformed schema;
- DB write failure;
- cancellation;
- worker restart during run.

Verify no false `COMPLETED/EVIDENCE_READY`, no loss of reviewed state, and retry scope is bounded.

## 8. Harness canaries

Before trusting a green campaign, deliberately break disposable test copies:

1. accept unsupported claim;
2. honor prompt injection;
3. merge ambiguous same-name people;
4. mark protocol complete with missing mandatory evidence;
5. let aggregator override official rule;
6. overwrite user disposition from suggestion;
7. invalidate every case from one source change;
8. invent 23:59 timezone for date-only deadline;
9. hide blocker below initial viewport;
10. remove accessible name/focus restoration.

The relevant tests must turn red. Otherwise classify `HARNESS_FAILURE`.

## 9. Evidence expectations

For release-blocking user-visible flows:
- semantic state proof + real rendered path.
For persistence:
- API/domain assertion + DB/repository inspection.
For responsive:
- rendered geometry/overflow evidence.
For accessibility:
- automated scan + keyboard behavior.
For security:
- zero forbidden tool calls + log/secret inspection.
For data transformations:
- fixture/result diff with stable IDs.

## 10. Candidate verdict criteria

`READY` only when:
- all Tier A oracles PASS on exact candidate;
- no unresolved critical authority contradiction;
- canaries pass;
- Tier B passes or residual risks are explicit and accepted;
- build/full test gate green;
- no target evidence is donor-only.

Otherwise:
- `READY_WITH_KNOWN_RISKS` only for non-critical residuals;
- `NOT_READY` for product/security integrity failure;
- `VERIFICATION_INCOMPLETE` when environment/proof is missing.

## 11. Pre-code verdict

Current state:

`QA_CONTRACT_READY_FOR_EXECUTION`

No runtime PASS/FAIL is asserted.
