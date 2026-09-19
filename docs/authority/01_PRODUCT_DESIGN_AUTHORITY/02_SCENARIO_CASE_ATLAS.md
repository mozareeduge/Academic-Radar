# 02 — SCENARIO CASE ATLAS

**snapshot:** `RADAR-PDA-2026-09-17-r2`  
**Purpose:** materially distinct product consequences. Cases are intentionally consequence-based rather than Cartesian combinations.

## Shared acceptance rules

These apply to every case unless explicitly superseded:

- source-derived facts link to recoverable evidence/snapshot;
- `UNKNOWN` is preserved;
- user disposition/application state are never overwritten by a crawl/research run;
- consequential asynchronous state changes announce completion/failure accessibly;
- mobile/narrow layouts retain the same semantic actions by reflowing rather than hiding;
- external links are identified as external;
- destructive deletion is not offered in normal flows;
- every AI-derived interpretation is distinguishable from external fact.

---

## Discovery and run lifecycle

### SCN-001 — First discovery finds new targets
**AUTHORITY:** HZN-007, HZN-011, FLOW-002  
**ACTOR:** ACT-001 + ACT-002  
**STARTING_STATE:** no matching existing target/case  
**TRIGGER:** user starts priority-country discovery  
**SYSTEM_DECISION:** normalize, dedupe, record discovery trace, create target and route-neutral discovery record; create EvaluationCase only when route/application-route can be meaningfully assigned.  
**EXPECTED_PRODUCT_RESULT:** new records become `DISCOVERED`; run stores source counts and provenance.  
**VISIBLE EXPERIENCE:** Radar shows `New` group with type, institution/country, discovery reason, source, freshness, and `Research` / `Archive` actions.  
**FAILURE/RECOVERY:** one failed source does not block valid records from others.  
**NEGATIVE:** do not call targets “strong matches” before research.  
**QA HANDOFF:** DERIVED · high · candidate E2E + persisted record inspection.

### SCN-002 — Duplicate target appears from multiple sources
**AUTHORITY:** HZN-009, HZN-011  
**TRIGGER:** same vacancy/person/programme arrives via multiple adapters.  
**RESULT:** one canonical target with multiple source records/evidence artifacts; no duplicate case unless route/application route differs.  
**VISIBLE:** source count may show “3 sources”; evidence inspector lists each.  
**NEGATIVE:** no silent evidence loss during dedupe.  
**QA:** DERIVED · high · fixture duplicates + DB inspection.

### SCN-003 — Ambiguous person identity
**AUTHORITY:** HZN-005, DEC-006  
**TRIGGER:** scholarly graph returns multiple same/similar names without reliable institutional/ORCID resolution.  
**RESULT:** identity state remains ambiguous; supervisor deep research is blocked from becoming `EVIDENCE_READY`.  
**VISIBLE:** “Identity unresolved” blocker with candidate identities and resolution evidence; user can pick/confirm or research further.  
**NEGATIVE:** do not merge publication histories speculatively.  
**QA:** DERIVED · critical · ambiguous-author fixture.

### SCN-004 — Source run partially fails
**AUTHORITY:** HZN-011, DEC-027  
**TRIGGER:** at least one source timeout/block/error while others succeed.  
**RESULT:** `PARTIAL` run; successful records persist.  
**VISIBLE:** source health list distinguishes `found`, `0 results`, `failed`, `skipped`; retry failed sources available.  
**COPY:** COPY-007, COPY-008.  
**NEGATIVE:** no “Search completed successfully.”  
**QA:** DERIVED · high · injected source failure.

### SCN-005 — User cancels running discovery
**AUTHORITY:** DEC-017  
**RESULT:** running work transitions `CANCELLING -> CANCELLED` or `PARTIAL`; already committed valid findings remain.  
**VISIBLE:** progress stops; message states partial results are retained; `Resume/retry` available.  
**NEGATIVE:** do not discard valid records or call run complete.  
**QA:** DERIVED · high · E2E cancellation.

### SCN-006 — No results
**AUTHORITY:** HZN-013  
**RESULT:** zero-record run remains valid; discovery trace retained.  
**VISIBLE:** causal empty state showing scope and a next action: broaden scope, include slow sources, or inspect source health.  
**NEGATIVE:** empty state must not imply no opportunities exist globally.  
**QA:** DERIVED · normal.

### SCN-007 — Opportunity is expired/closed
**AUTHORITY:** HZN-005, HZN-010  
**TRIGGER:** explicit deadline/status proves closure.  
**RESULT:** target historical state retained; active action path closes; case may remain as precedent/watch but cannot be `ACT` suggestion.  
**VISIBLE:** `Closed` with source/date; user disposition not erased.  
**NEGATIVE:** do not delete; do not show “Apply”.  
**QA:** AUTH/DERIVED · high.

### SCN-008 — Previously seen target materially changes
**AUTHORITY:** HZN-007, DEC-032  
**RESULT:** new snapshot; impacted claims/cases `STALE`; unrelated cases untouched.  
**VISIBLE:** Radar `Changed` item links to diff and impacted claims.  
**QA:** DERIVED · high · snapshot diff fixture.

---

## Evidence and AI research

### SCN-009 — Deep research returns evidence-backed claims
**AUTHORITY:** HZN-001, HZN-009  
**TRIGGER:** ACT-003 produces schema-valid output with recoverable evidence IDs.  
**RESULT:** claims saved as `EXTERNAL_FACT`, `OBSERVED_RELATION`, or `INFERENCE` with correct status; case advances when route evidence requirements are met.  
**VISIBLE:** each assessment expands to source-linked claim rows.  
**NEGATIVE:** summary text is not stored as untraceable truth.  
**QA:** DERIVED · critical · structured-output + link-integrity proof.

### SCN-010 — Model returns fluent assertion with no evidence
**AUTHORITY:** DEC-018  
**RESULT:** assertion is rejected from consequential assessment; run may be `PARTIAL` and issue recorded.  
**VISIBLE:** “Research output needs evidence” with rerun/review. Existing reviewed assessment remains.  
**NEGATIVE:** no score/fit change from unsupported assertion.  
**QA:** DERIVED · critical · canary response without evidence.

### SCN-011 — Sources contradict one another
**AUTHORITY:** HZN-005  
**TRIGGER:** e.g., department page says accepting students while official profile says unavailable, or two deadline pages conflict.  
**RESULT:** claim `CONTRADICTED/PARTIAL`; no forced resolution unless authority precedence is clear.  
**VISIBLE:** contradiction callout lists both sources and dates; action asks user/research agent to resolve from higher-authority current source.  
**QA:** DERIVED · high.

### SCN-012 — Critical fact is stale before action
**AUTHORITY:** DEC-028, FLOW-009  
**TRIGGER:** case disposition `ACT` or brief generation while deadline/eligibility/supervisor availability exceeds freshness policy.  
**RESULT:** brief freeze blocked until reverification or explicit user override with warning.  
**VISIBLE:** stale-critical-facts panel with `Recheck now`.  
**NEGATIVE:** do not present old fact as current.  
**QA:** DERIVED · critical.

### SCN-013 — User accepts an inference
**AUTHORITY:** HZN-004, OBJ-005  
**RESULT:** inference gains `reviewed_by_user`; claim type remains `INFERENCE`.  
**VISIBLE:** “Reviewed” marker separate from “verified fact”.  
**NEGATIVE:** acceptance cannot relabel inference as external fact.  
**QA:** DERIVED · high.

### SCN-014 — User rejects/corrects an inference
**AUTHORITY:** FLOW-008  
**RESULT:** prior claim history preserved; corrected assessment becomes active; dependent summary/suggestion invalidated/recomputed.  
**VISIBLE:** correction timeline and changed assessments.  
**QA:** DERIVED · high.

### SCN-015 — Source becomes unavailable
**AUTHORITY:** HZN-005, DEC-027  
**RESULT:** previous snapshot remains; new fetch recorded `FETCH_FAILED`; claims remain historically supported but freshness becomes uncertain/stale if current truth required.  
**VISIBLE:** source badge “Unavailable on recheck · last captured DATE”.  
**NEGATIVE:** no deletion of historical evidence.  
**QA:** DERIVED · normal/high depending claim.

---

## Supervisor / supervision-track cases

### SCN-016 — Create route-specific supervisor case
**AUTHORITY:** HZN-002, FLOW-003  
**TRIGGER:** user selects supervisor + MozareRoute + supervisor-first PhD.  
**RESULT:** new EvaluationCase independent from other routes for same person.  
**VISIBLE:** case header always names route and application route.  
**NEGATIVE:** person-level fit score cannot leak into case.  
**QA:** AUTH · critical.

### SCN-017 — Strong publication similarity but no supervision precedent
**AUTHORITY:** Phase 2A/2B memory, HZN-005  
**RESULT:** topic/method dimensions may be strong; `supervision precedent strength` remains weak/unknown; system may classify `NOVEL_PLAUSIBLE`, not `TRACK_CORE`.  
**VISIBLE:** rationale states what is demonstrated and what is not.  
**QA:** AUTH/DERIVED · high.

### SCN-018 — Supervised projects demonstrate broader track than supervisor publications
**AUTHORITY:** OBJ-008  
**RESULT:** case can gain `TRACK_PERMITTED` or `TRACK_ADJACENT` support from supervision evidence even when publication core differs.  
**VISIBLE:** Track Explorer distinguishes supervisor-authored core from supervised precedents.  
**NEGATIVE:** supervised project is not falsely attributed as supervisor’s own research.  
**QA:** AUTH · high.

### SCN-019 — Past student background is unavailable
**AUTHORITY:** HZN-005  
**RESULT:** applicant-formation comparison remains unknown; other precedent dimensions proceed.  
**VISIBLE:** explicit “Student prior formation not publicly established.”  
**NEGATIVE:** do not infer from dissertation subject.  
**QA:** AUTH · normal.

### SCN-020 — Multiple supervisor cases compared
**AUTHORITY:** DEC-002, DEC-021  
**RESULT:** comparison uses aligned explicit dimensions, blockers, precedent strength, funding plausibility, freshness, unknowns.  
**VISIBLE:** comparison table; no single overall winner score by default. User may sort by one chosen dimension.  
**NEGATIVE:** no prestige proxy ranking.  
**QA:** AUTH · high.

---

## PhD opportunity cases

### SCN-021 — Advertised PhD passes formal gates
**AUTHORITY:** HZN-003, FLOW-005  
**RESULT:** evaluate defined-project/method/corpus fit and execution evidence; funding/employment/deadline visible.  
**VISIBLE:** `Eligible on stated criteria` means criteria checked, not admission prediction.  
**QA:** AUTH · high.

### SCN-022 — Advertised PhD has one unmet hard requirement
**AUTHORITY:** HZN-017  
**RESULT:** `FORMALLY_BLOCKED`; intellectual fit may remain documented.  
**VISIBLE:** blocker is first summary item; primary action changes from `Prepare` to `Watch/Archive` unless rule itself is disputable.  
**QA:** AUTH · critical.

### SCN-023 — Requirement wording is ambiguous
**AUTHORITY:** HZN-005  
**RESULT:** gate `UNKNOWN`; case remains researchable but cannot be called formally eligible.  
**VISIBLE:** `Clarify with programme` next action and exact source wording.  
**QA:** DERIVED · high.

### SCN-024 — Deadline becomes urgent
**AUTHORITY:** HZN-010, DEC defaults  
**TRIGGER:** open deadline ≤30 days.  
**RESULT:** Radar urgency rises; disposition unchanged.  
**VISIBLE:** days remaining + unverified critical facts; `ACT` suggestion only if no known hard blocker.  
**NEGATIVE:** urgency cannot override eligibility.  
**QA:** DERIVED · high.

---

## MA + funding cases

### SCN-025 — Strong intellectual fit, formal eligibility unknown
**AUTHORITY:** FLOW-006, HZN-016  
**RESULT:** Strategic Value may be strong; Admission Viability remains `UNKNOWN`.  
**VISIBLE:** three headline assessments diverge visibly.  
**NEGATIVE:** do not merge into “strong MA match”.  
**QA:** AUTH · critical.

### SCN-026 — Existing MA may affect eligibility/funding
**AUTHORITY:** DEC-020  
**RESULT:** dedicated gate requires explicit official evidence.  
**VISIBLE:** `Second Master's rule: Unknown/Pass/Fail` near admission/funding heads.  
**QA:** AUTH · critical.

### SCN-027 — Programme admission strong, scholarship ineligible
**AUTHORITY:** HZN-016  
**RESULT:** Admission strong; Funding blocked/weak; Strategic Value independent.  
**VISIBLE:** funding head shows specific scholarship blocker and alternate funding search action.  
**QA:** AUTH · critical.

### SCN-028 — Scholarship amount leaves material funding gap
**AUTHORITY:** memory Gate E, HZN-016  
**RESULT:** deterministic funding arithmetic produces gap; `Funding Viability` cannot be marked strong solely because scholarship exists.  
**VISIBLE:** annual award, tuition/fees, estimated mandatory costs, known gap, unknown cost items.  
**NEGATIVE:** no false “fully funded”.  
**QA:** AUTH · critical.

### SCN-029 — Programme is English-taught but one mandatory component is not
**AUTHORITY:** user hard constraint  
**RESULT:** language gate `FAIL` if degree cannot be completed under English requirement.  
**VISIBLE:** exact mandatory-language evidence.  
**QA:** AUTH · critical.

### SCN-030 — Programme repeats existing MA without strategic gain
**AUTHORITY:** HZN-016 / memory Gate C  
**RESULT:** Strategic Value weak despite formal admissibility; system explains missing capability gain.  
**VISIBLE:** “Second-MA rationale weak” assessment, not rejection as fact.  
**QA:** DERIVED/HEURISTIC · normal.

---

## Watch / change cases

### SCN-031 — Watched page unchanged
**AUTHORITY:** DEC-032  
**RESULT:** snapshot/fingerprint records no material change; no agent deep rerun.  
**VISIBLE:** last checked updates quietly.  
**QA:** DERIVED · high because cost-control invariant.

### SCN-032 — Watched project gains new PhD vacancy
**AUTHORITY:** HZN-007  
**RESULT:** create/link PhDOpportunity; impacted supervisor/project cases receive change event; user sees New + Changed.  
**VISIBLE:** relationship between prior watch target and new opportunity.  
**QA:** DERIVED · high.

### SCN-033 — Watch fetch repeatedly fails
**AUTHORITY:** OBJ-011  
**RESULT:** `ERROR` after configured retry policy; prior evidence preserved.  
**VISIBLE:** Radar health issue; `Retry`, `Open source`, `Pause watch`.  
**QA:** DERIVED · normal.

### SCN-034 — Change invalidates only one claim
**AUTHORITY:** HZN-007 invariant  
**RESULT:** dependent claim/case section becomes stale; unaffected dimensions remain reviewed.  
**VISIBLE:** partial stale indicator at section/claim level rather than whole-dossier reset.  
**QA:** DERIVED · high.

---

## Application preparation / user decisions

### SCN-035 — User marks case Strong/Watch/Act/Rejected
**AUTHORITY:** HZN-004  
**RESULT:** disposition persists independently of future system suggestion.  
**VISIBLE:** system suggestion remains visible if it differs: “You set Watch · system suggests Act because…”  
**NEGATIVE:** no automatic overwrite.  
**QA:** AUTH · critical.

### SCN-036 — Generate Application Brief
**AUTHORITY:** HZN-018, FLOW-009  
**PRECONDITION:** critical facts fresh enough or user explicitly acknowledges stale evidence.  
**RESULT:** frozen brief links every key assertion to case claims/evidence and records generated date.  
**VISIBLE:** sections for rationale, candidate evidence, precedents, formal/funding state, unknowns, prohibited claims, sources.  
**QA:** AUTH · critical.

### SCN-037 — Case changes after brief generation
**RESULT:** brief becomes `SUPERSEDED`/outdated; not silently rewritten.  
**VISIBLE:** “Case changed after this brief” with regenerate action and changed facts.  
**QA:** DERIVED · high.

### SCN-038 — User archives then restores a case
**AUTHORITY:** DEC-014  
**RESULT:** history, disposition, notes, evidence links preserved.  
**VISIBLE:** archive removes from active queues; restore returns with freshness status recalculated.  
**QA:** DERIVED · normal.

---

## Responsive, input, accessibility consequence cases

### SCN-X-001 — Dense dossier on mobile
**AUTHORITY:** DEC-024  
**RESULT:** dossier becomes single-column; section nav becomes sticky compact selector/outline; evidence inspector becomes full-screen sheet/page; all review/disposition/source actions remain reachable.  
**NEGATIVE:** no horizontal scrolling for core content; tables transform to key-value rows/cards.  
**QA:** DERIVED/STANDARD · high · 320/390px browser + keyboard/touch inspection.

### SCN-X-002 — Keyboard-only claim review
**RESULT:** user can traverse claim rows, expand evidence, open/close inspector, accept/reject assessment, restore focus to originating claim.  
**COPY/ARIA:** async update announced.  
**QA:** STANDARD · high.

### SCN-X-003 — Status without color
**RESULT:** Pass/Fail/Unknown/Stale/Suggested states remain distinguishable in monochrome/high-contrast through labels/icons/text/borders.  
**QA:** STANDARD/DERIVED · high.

### SCN-X-004 — Long institution/title/URL
**RESULT:** text wraps or truncates with accessible full value; controls remain inside container; no page-level horizontal overflow at 320px.  
**QA:** DERIVED · normal.

### SCN-X-005 — Research completes while user is elsewhere
**RESULT:** non-disruptive notification/Radar count updates; no focus steal; live region announces completion only when contextually appropriate.  
**QA:** STANDARD/DERIVED · normal.

---


## Security, source-control, time, and protocol integrity

### SCN-039 — Crawled page contains prompt injection
**AUTHORITY:** HZN-022  
**TRIGGER:** source text contains instructions to ignore system rules, alter evaluation, reveal credentials, execute code, contact a person, or follow arbitrary URLs/actions.  
**SYSTEM_DECISION:** treat instruction as inert source data; do not execute/follow it as control; continue extraction only within allowed crawler/research policy.  
**RESULT:** no product state changes solely because source text requested them. Suspicious content may be logged.  
**NEGATIVE:** no secret disclosure, autonomous email/action, score/disposition mutation, shell/tool execution, or control-prompt replacement.  
**QA:** AUTH · critical · adversarial fixture/canary.

### SCN-040 — Deep research stops before mandatory evidence class is searched
**AUTHORITY:** HZN-019, OBJ-014  
**RESULT:** run cannot become `EVIDENCE_READY`; missing evidence class is explicit and run is `PARTIAL`/needs research.  
**VISIBLE:** “Research incomplete: supervised-project evidence not searched” (example).  
**NEGATIVE:** narrative completeness cannot substitute for protocol completion.  
**QA:** AUTH · critical.

### SCN-041 — Lower-authority source conflicts with official rule
**AUTHORITY:** HZN-020  
**RESULT:** official current source governs the gate unless it is itself stale/ambiguous; lower-authority evidence remains visible as contradiction/context.  
**NEGATIVE:** aggregator snippet cannot override official eligibility/deadline.  
**QA:** AUTH · critical.

### SCN-042 — Three copied pages repeat the same claim
**AUTHORITY:** HZN-020  
**RESULT:** evidence coverage records one canonical-origin assertion with three manifestations, not three independent corroborations.  
**QA:** DERIVED · high.

### SCN-043 — Deadline has date but no timezone/time-of-day
**AUTHORITY:** HZN-021  
**RESULT:** preserve date-only precision; urgency may use date but no invented 23:59/local offset is shown as fact; case requests recheck near cutoff.  
**VISIBLE:** original wording and “time not stated”.  
**QA:** AUTH · high.

### SCN-044 — Deadline includes institutional local time
**AUTHORITY:** HZN-021  
**RESULT:** preserve original local time and timezone; normalized equivalent may be shown secondarily.  
**NEGATIVE:** DST/local conversion cannot silently alter the official representation.  
**QA:** AUTH/STANDARD · critical.

### SCN-045 — Source change affects one funding route only
**AUTHORITY:** HZN-025, OBJ-016  
**RESULT:** linked FundingAssessment becomes stale/recomputed; unrelated funding packages and programme Strategic Value remain unchanged.  
**QA:** AUTH · high.

### SCN-046 — Funding route attaches to one MA case
**AUTHORITY:** HZN-003 revision, OBJ-015  
**RESULT:** scholarship/funding is represented as a linked FundingAssessment, not a duplicate MA application case. Multiple funding routes can be compared under one programme case.  
**QA:** AUTH · critical.

### SCN-047 — System suggestion differs after deterministic recomputation
**AUTHORITY:** HZN-024  
**RESULT:** suggestion updates from explicit rule inputs; user disposition remains unchanged; UI shows reason for difference.  
**NEGATIVE:** LLM response cannot directly write user/system disposition.  
**QA:** AUTH · critical.

### SCN-048 — Ambiguous entity relation must not merge
**AUTHORITY:** HZN-023  
**TRIGGER:** same-name researcher or institution ambiguity exists.  
**RESULT:** relation remains unresolved; publication/project/supervision edges are not merged into the canonical entity.  
**QA:** AUTH · critical.


## Historical defect guards inherited from donor behavior

### HIST-001 — Status/source counts disagree
**Invariant:** headline result counts, run funnel, and visible canonical list must clearly state if they represent different stages; two supposedly identical counts cannot be derived from incompatible datasets.

### HIST-002 — Cancellation discards or mislabels partial results
**Invariant:** covered by SCN-005.

### HIST-003 — Person “fit” leaks across routes
**Invariant:** covered by SCN-016 and DEC-001.

### HIST-004 — Generic score hides missing evidence
**Invariant:** covered by DEC-002/DEC-006.

### HIST-005 — Source failure looks like no results
**Invariant:** covered by SCN-004/006.

---

## Cross-factor directed matrix

| Combination | Required case |
|---|---|
| hard blocker × urgent deadline | urgency never overrides blocker (SCN-022 + SCN-024) |
| stale evidence × ACT | reverification gate (SCN-012) |
| changed source × user disposition | mark stale, preserve disposition (SCN-008 + SCN-035) |
| model failure × prior reviewed analysis | preserve reviewed state (SCN-010) |
| partial scholarship × high tuition | funding gap explicit (SCN-028) |
| dense evidence × mobile | SCN-X-001 |
| ambiguous identity × supervisor publications | SCN-003 |
| user correction × derived suggestion | SCN-014 + SCN-035 |
| source outage × historical evidence | SCN-015 |
