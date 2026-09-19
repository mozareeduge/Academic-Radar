# 01 — OBJECT, STATE, AND FLOW MODEL

**snapshot:** `RADAR-PDA-2026-09-17-r2`

## 1. Actors

### ACT-001 — Owner / applicant
**Identity:** Mozare  
**Goals:** discover, understand, compare, decide, watch, prepare action.  
**Authority:** final case disposition, corrections, route activation, application progress.  
**Must see:** evidence, uncertainty, freshness, blockers, implications.

### ACT-002 — Deterministic collector/resolver
Fetches known sources, normalizes records, deduplicates, parses explicit dates/rules, resolves identities, computes deterministic arithmetic, creates snapshots.

It may never infer scholarly fit.

### ACT-003 — Research agent
Performs bounded interpretive tasks:
- evidence-seeking query generation;
- supervisor spine extraction;
- track reconstruction;
- concept/method/citation genealogy;
- route translation;
- missing-evidence detection;
- bounded narrative synthesis.

All outputs are claims with provenance and inference status.

### ACT-004 — Scheduler/watch process
Runs recurring lightweight discovery and watches selected URLs/sources. It may enqueue deeper research only under explicit trigger rules.

### ACT-005 — External academic source
University, project, funder, thesis repository, scholarly graph, publication page, job board. It can be current, stale, inconsistent, inaccessible, or changed.

## 2. Core objects

### OBJ-001 — CandidateProfile
The governed applicant profile.

Contains:
- fixed constraints;
- education;
- language evidence;
- scholarly work;
- artistic/curatorial work;
- professional/technical evidence;
- verified/self-reported status;
- application-relevant documents.

**State:** `ACTIVE` / `NEEDS_VERIFICATION` / `SUPERSEDED`.  
Profile facts are not edited by crawlers.

### OBJ-002 — MozareRoute
A bounded project/research route used to evaluate targets.

Examples: AvanT‑Trace, Mixt, Visible Genesis, Casebook/Staging, Persian modernist route, executable/procedural archive route.

Fields:
- route statement;
- core problem;
- operations/methods;
- relevant corpora/material;
- supporting candidate evidence;
- target disciplines;
- prohibited overclaims;
- route maturity.

**State:** `ACTIVE`, `EXPLORATORY`, `DORMANT`, `RETIRED`.

### OBJ-003 — TargetEntity
Normalized external entity: `Person`, `Programme`, `PhDOpportunity`, `FundedProject`, `Institution`, `FundingRoute`, `SupervisedProject`, `Work`.

External facts are versioned by source/snapshot rather than destructively overwritten.

### OBJ-004 — EvaluationCase
The core evaluative object.

Identity:
```text
case_id = route_id + target_id + application_route
```

Fields:
- application route;
- system research state;
- user disposition;
- suggested disposition;
- formal gates;
- fit dimensions;
- evidence completeness;
- blockers;
- unknowns;
- deadline/urgency;
- application stage;
- notes;
- next action.

#### Research state
```text
DISCOVERED
TRIAGED
RESEARCHING
EVIDENCE_READY
STALE
FAILED
ARCHIVED
```

Legal transitions:
```text
DISCOVERED -> TRIAGED | ARCHIVED
TRIAGED -> RESEARCHING | ARCHIVED
RESEARCHING -> EVIDENCE_READY | FAILED
FAILED -> RESEARCHING | ARCHIVED
EVIDENCE_READY -> STALE | RESEARCHING | ARCHIVED
STALE -> RESEARCHING | ARCHIVED
```

A fresh source change may move `EVIDENCE_READY -> STALE` but may **not** change user disposition.

#### User disposition
```text
UNDECIDED
STRONG
WATCH
ACT
REJECTED
```

Only ACT-001 persists this value. System suggestions are separate.

#### Application stage
```text
NOT_STARTED
PREPARING
CONTACTED
APPLICATION_OPEN
APPLIED
INTERVIEW
OFFER
DECLINED
CLOSED
```

Application stage never substitutes for research state.

### OBJ-005 — Claim
Atomic proposition used in an assessment.

Fields:
- statement;
- claim type: `EXTERNAL_FACT`, `OBSERVED_RELATION`, `INFERENCE`, `USER_DECISION`;
- status: `SUPPORTED`, `PARTIAL`, `CONTRADICTED`, `UNKNOWN`, `STALE`;
- evidence links;
- generated_by;
- reviewed_by_user;
- created_at / last_checked_at.

Rule: inference can be user-accepted as an assessment, but never changes into `EXTERNAL_FACT`.

### OBJ-006 — EvidenceArtifact
A recoverable evidence unit.

Examples:
- official page;
- thesis record;
- grant page;
- publication metadata;
- PDF/abstract;
- CV item;
- Mozare work/repository;
- programme regulation.

Fields:
- source URL/reference;
- source type;
- excerpt/structured extraction;
- snapshot ID;
- date retrieved;
- publication/effective date if known;
- authority level;
- identity confidence.

### OBJ-007 — Snapshot
Immutable observation of an external source at a time.

States:
- `CAPTURED`
- `UNCHANGED`
- `CHANGED`
- `FETCH_FAILED`

A later fetch creates a new snapshot; it does not mutate history.

### OBJ-008 — SupervisionPrecedent
Structured representation of a supervised/co-supervised project.

Fields include:
- thesis/project;
- candidate formation if public;
- object/corpus;
- question;
- methods;
- theories;
- outputs;
- supervisor role;
- co-supervisors;
- project/funding relation;
- temporal relation to supervisor work.

Track classification:
`TRACK_CORE`, `TRACK_PERMITTED`, `TRACK_ADJACENT`, `NOVEL_PLAUSIBLE`, `UNSUPPORTED`.

### OBJ-009 — GateAssessment
Explicit yes/no/unknown gate.

Every gate stores:
- requirement statement;
- source authority;
- effective/freshness date;
- evaluation rule;
- result;
- evidence IDs;
- reviewer/source provenance;
- dependency links for invalidation.

Examples:
- English requirement;
- qualifying degree;
- second-MA rule;
- nationality;
- scholarship nomination rule;
- deadline open;
- supervisor status.

States:
`PASS`, `FAIL`, `UNKNOWN`, `NOT_APPLICABLE`, `STALE`.

Hard gate `FAIL` produces a visible formal blocker.

### OBJ-010 — DimensionAssessment
Evidence-bound graded assessment.

Fields:
- dimension ID;
- scale definition;
- value;
- evidence;
- unknowns;
- reviewer status.

Supervisor-first PhD uses 0–3 only where meaningful. No scale is inferred where evidence is absent.

### OBJ-011 — WatchTarget
A URL/entity/source selected for change monitoring.

State:
`ACTIVE`, `PAUSED`, `ERROR`, `RETIRED`.

Contains:
- target;
- last good snapshot;
- check cadence;
- change fingerprint;
- cases impacted.

### OBJ-012 — ResearchRun
One bounded collection/research execution.

State:
`QUEUED`, `RUNNING`, `CANCELLING`, `COMPLETED`, `PARTIAL`, `FAILED`, `CANCELLED`.

Records:
- scope;
- sources;
- records discovered;
- cases changed;
- source-level failures;
- agent/model identity when relevant;
- cost/token metadata if available.

### OBJ-013 — ApplicationBrief
A frozen, source-linked preparation artifact generated from one case.

Contents:
- target/application route;
- route rationale;
- verified candidate evidence to foreground;
- demonstrated supervisor/programme precedents;
- formal eligibility/funding state;
- unknowns/questions;
- prohibited claims;
- source ledger;
- suggested next action.

State:
`DRAFT`, `REVIEWED`, `SUPERSEDED`.


### OBJ-014 — ResearchProtocol
A versioned route-specific specification controlling deep research.

Fields:
- application route;
- mandatory evidence classes;
- optional evidence classes;
- preferred source authorities;
- identity requirements;
- stop conditions;
- freshness rules;
- allowed unknowns;
- blocking unknowns;
- assessment dimensions/rules;
- protocol version.

ResearchRun records the protocol version it executed.

### OBJ-015 — FundingAssessment
A relationship object linking an `EvaluationCase` (usually MA/structured PhD) to one `FundingRoute`.

Fields:
- funding route target;
- eligibility gates;
- nomination/application route;
- award/waiver/tuition facts;
- duration;
- currency;
- known costs;
- normalized coverage arithmetic;
- uncovered gap;
- unknown cost items;
- deadline/freshness;
- assessment state.

One case may have zero, one, or many FundingAssessments.

### OBJ-016 — EvidenceDependency
Explicit edge:
`EvidenceArtifact/Snapshot -> Claim -> Gate/Dimension -> Suggestion/Brief`.

This edge is the invalidation/recomputation authority used by change watching.

### OBJ-017 — DiscoveryTrace
Stores why/how an entity entered the system:
- run ID;
- source adapter/query;
- source URL;
- discovered type;
- country/scope;
- matching terms if deterministic;
- created/last-seen dates.

A discovery trace is not fit evidence by itself.

### OBJ-018 — SourceAuthority
Controlled classification of evidence source:
`OFFICIAL_REGULATION`, `OFFICIAL_PROGRAMME`, `OFFICIAL_DEPARTMENT_OR_PERSON`,
`AUTHORITATIVE_REGISTRY`, `PRIMARY_RESEARCH_OUTPUT`, `REPUTABLE_SECONDARY`,
`DISCOVERY_AGGREGATOR`, `UNKNOWN`.

It also stores canonical-origin grouping so copied/repeated pages are not counted as independent evidence.


## 3. Commands

`discover`, `research`, `rerun`, `resolve_identity`, `mark_source_authority`, `watch`, `unwatch`, `compare`, `set_disposition`, `set_application_stage`, `correct_claim`, `accept_assessment`, `reject_assessment`, `add_evidence`, `open_source`, `create_brief`, `export`, `archive_case`, `restore_case`, `cancel_run`.

No destructive delete is primary UI for cases/evidence. Archive is default so research history remains recoverable.

## 4. Surfaces

### SURF-001 — Radar
**Purpose:** current attention queue.  
Shows:
- new discoveries;
- changed watched targets;
- urgent deadlines;
- research failures;
- cases awaiting review;
- actionable user dispositions.

Primary actions: review, research, triage.

### SURF-002 — PhD
Unified PhD cases with tabs/filters for:
- supervisor-first;
- advertised positions;
- structured programmes.

### SURF-003 — MA + Funding
Programme cases with admission/funding/strategic assessments and linked scholarship packages.

### SURF-004 — Supervisors
Entity browse/discovery surface. A person itself is not “fit”; the surface shows route-specific cases under that person.

### SURF-005 — Case Dossier
Primary research workspace for one `OBJ-004`.

Sections:
1. case header and route;
2. hard gates;
3. assessment summary;
4. evidence-backed rationale;
5. precedents/track;
6. candidate execution evidence;
7. funding/application route;
8. unknowns/contradictions;
9. sources/freshness;
10. actions/notes/application brief.

### SURF-006 — Evidence Inspector
Displays a claim, evidence artifacts, source snapshot metadata, extraction, and external link. Used as drawer on wide screens and full-screen sheet/page on mobile.

### SURF-007 — Track Explorer
Supervisor/project genealogy:
- supervisor work;
- supervised projects;
- funded projects;
- concepts/methods/corpora/infrastructures;
- continuity/transformation classification.

Graph visualization is optional; the canonical representation is a navigable evidence list/timeline so the feature remains usable without a graph engine.

### SURF-008 — Watch / Changes
Diff-centered surface:
- changed source;
- material change summary;
- impacted cases;
- rerun recommendation;
- acknowledge/ignore/watch controls.

### SURF-009 — Profile & Routes
Applicant evidence, constraints, route definitions, evidence verification state.

### SURF-010 — Research Run / Source Health
Run progress, sources, records, failures, cancellation, partial-results state.

## 5. External dependencies as product outcomes

### Academic/job boards
All returned page text is untrusted data under HZN-022.

Outcome classes: success, no records, blocked, malformed, timeout, source changed.

### University/faculty pages
Outcome classes: static HTML, JS-heavy, PDF, inaccessible, moved/404, bot-blocked.

### Scholarly/project graphs
Outcome classes: exact identity, ambiguous identity, partial metadata, rate limit, unavailable.

### LLM/model
Control prompt and source text must be structurally separated. Model input includes only bounded source excerpts/structured facts plus explicit task instructions.

Outcome classes:
- valid structured claim set;
- partial;
- schema-invalid;
- evidence-less assertion;
- refusal/unavailable;
- timeout.

Product behavior: preserve collected evidence, mark run partial/failed, never replace prior reviewed analysis with an invalid generation.

## 6. User journeys

### FLOW-001 — First usable workspace
1. Open product.
2. Inspect imported CandidateProfile and active MozareRoutes.
3. Confirm hard constraints: English; country priorities.
4. Run initial discovery.
5. Reach Radar with new unreviewed cases.

Terminal state: discoveries exist without requiring complete deep research.

### FLOW-002 — Broad discovery → triage
`run discovery -> normalize/dedupe -> hard-filter -> create/update DISCOVERED cases -> user triage -> archive or research`

The user must be able to inspect source and reason for discovery before deep research.

### FLOW-003 — Supervisor deep research
`supervisor candidate -> select MozareRoute -> create EvaluationCase -> research spine -> reconstruct precedents -> genealogy -> assess dimensions -> review evidence -> set disposition`

Terminal state: `EVIDENCE_READY` or explicit `FAILED/PARTIAL`, never false completeness.

### FLOW-004 — Supervisor-first PhD route
`strong supervisor case -> verify doctoral route/institutional conditions -> verify supervision availability evidence -> identify funding paths -> prepare ApplicationBrief -> CONTACTED/PREPARING`

### FLOW-005 — Advertised PhD
`new vacancy -> formal eligibility -> defined-project fit -> execution evidence -> funding/employment -> urgency -> disposition/action`

Deadline changes/closure must update case urgency without deleting history.

### FLOW-006 — MA + scholarship
`programme discovery -> hard admission gates -> intellectual/strategic assessment -> scholarship discovery -> scholarship gates -> funding arithmetic -> user decision`

Terminal state explicitly distinguishes:
- admissible/fundable;
- admissible/funding gap;
- eligibility unknown;
- formally blocked.

### FLOW-007 — Watch-triggered re-evaluation
`watch fetch -> fingerprint change -> diff -> map impacted claims/cases -> mark STALE -> targeted research -> reviewed state`

No material change -> no deep rerun.

### FLOW-008 — User correction
`open claim -> add correction/evidence -> preserve previous claim history -> recompute impacted assessments -> mark system suggestion stale -> user disposition unchanged`

### FLOW-009 — Application preparation
`ACT disposition -> ApplicationBrief -> verify current deadlines/rules -> freeze brief -> downstream writing/outreach`

No auto-send.

### FLOW-010 — Failure and recovery
`run partially fails -> show completed sources + failure classes -> preserve partial valid results -> retry only failed/affected sources -> reconcile dedupe -> complete/partial`

## 7. Cross-state invariants

1. External refresh cannot overwrite user disposition.
2. External refresh cannot erase notes/application state.
3. A changed source invalidates only dependent claims/cases, not every case globally.
4. A hard gate fail cannot be visually hidden by fit.
5. An unknown cannot be converted to zero.
6. A model inference cannot become external fact after user acceptance.
7. Archived cases remain recoverable.
8. Evidence history is append/version based.
9. A filtered export contains the objects currently represented by that filter.
10. Research cancellation does not label partial results “complete”.


## 8. Deadline/time normalization invariant

For every current deadline/status:
- preserve original string;
- preserve source-local timezone when explicit;
- store normalized UTC timestamp only when sufficiently determined;
- store `time_precision = DATE_ONLY | LOCAL_TIME | OFFSET_AWARE | AMBIGUOUS`;
- urgency sorting must use the least-assumptive interpretation;
- any application brief generated near an ambiguous deadline requires recheck.

## 9. Research protocol state invariant

`EVIDENCE_READY` means “the active ResearchProtocol completed or explicitly recorded allowed unknowns,” not “the model stopped producing text.”

A run that skipped a mandatory evidence class is `PARTIAL` or `FAILED`, even if the narrative output looks complete.
