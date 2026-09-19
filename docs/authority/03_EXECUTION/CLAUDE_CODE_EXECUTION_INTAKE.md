# CLAUDE CODE EXECUTION INTAKE — Mozare Academic Radar

**execution_intake_revision:** `RADAR-EXEC-2026-09-17-r1`  
**product_authority_snapshot_id:** `RADAR-PDA-2026-09-17-r2`  
**qa_snapshot_id:** `RADAR-QA-2026-09-17-r1`  
**planning donor:** `mimdot/CIK@8c300d28b9add865cd09b2e5e141f94a6b033c74`  
**status:** `READY_FOR_CODE_EXECUTION`

---

## A. START HERE

### Objective

Build the first production-worthy **Mozare Academic Radar**: a private, evidence-first research instrument for:
- supervisor-first PhD routes;
- advertised/funded PhD positions;
- structured doctoral programmes;
- English-taught MA/Research MA programmes;
- linked scholarship/funding routes;
- ongoing change monitoring of people, projects, programmes, calls, and funding pages.

Canonical evaluation unit:

```text
EvaluationCase = MozareRoute × TargetEntity × ApplicationRoute
```

### Terminal state

Target `RELEASE_CANDIDATE_READY`:

- local/self-hosted web application works end-to-end;
- target schema and migrations complete;
- priority-country discovery works;
- supervisor deep-research path works with evidence provenance;
- MA + funding path works;
- watch/change cycle works;
- exact-head CI green;
- all Tier-A QA obligations green;
- Docker Compose smoke green;
- no public production deploy is required.

### Donor baseline

No target implementation exists yet.

Use `mimdot/CIK` as donor only. Planning HEAD is `8c300d28b9add865cd09b2e5e141f94a6b033c74`.

At execution start:
1. clone/fork donor into a new target repo/worktree;
2. freeze actual donor HEAD;
3. compare if donor `main` advanced;
4. adopt later donor changes only when they are compatible and useful;
5. never modify upstream donor.

---

## B. AUTHORITY / CONFLICT RULE

Precedence:

1. explicit current owner decisions;
2. product/design authority `RADAR-PDA-2026-09-17-r2`;
3. QA authority `RADAR-QA-2026-09-17-r1`;
4. current external platform/API contracts;
5. target repo executable truth as baseline evidence;
6. donor CIK truth;
7. proposals/claims/history.

Implementation must not silently:
- restore a universal fit score;
- merge system suggestion and user disposition;
- make funding a duplicate MA case;
- drop evidence/provenance;
- promote model prose to evidence-ready;
- let source text act as instructions;
- infer missing deadline timezone;
- infer applicant acceptance causes from supervision precedent.

If an authority requirement conflicts with real technical evidence, record `FEASIBILITY_CONTRADICTION`, stop only the affected branch, and continue safe independent work.

---

## C. WORK MODE

`GREENFIELD_USING_DONOR_FORK`  
`RESEARCH_INSTRUMENT`  
`INTERNAL_TOOL`  
`AI_ASSISTED_SYSTEM`

V1 launch topology: **local/self-hosted container stack**.

Desktop/Tauri packaging, public multi-user hosting, Activepieces, changedetection.io, Neo4j, and vector DB are outside the V1 release requirement.

---

## D. CURRENT TRUTH

### Donor stack

Observed donor:
- Python 3.12+;
- FastAPI;
- SQLAlchemy + Alembic;
- Postgres support;
- Redis/RQ jobs;
- LiteLLM;
- requests/BeautifulSoup plus optional Playwright;
- Next.js 16 / React 19;
- Jest/Testing Library;
- CI for backend pytest/self-test, frontend test/lint/typecheck/build, dependency audit.

### Target
Repository: create/fork as `mozare-academic-radar` or equivalent.  
Current candidate: none.  
Current live deployment/domain: none.  
Secrets/accounts: unknown; never invent.

---

## E. PROTECTED / TARGET HORIZON

Read the r2 Layer-1 files as authority.

Highest-risk invariants:

1. route-specific case identity;
2. human-only persisted disposition;
3. deterministic suggestion separated from LLM analysis;
4. explicit Unknown;
5. hard formal blockers;
6. route-specific research protocol completeness;
7. evidence authority + independence;
8. identity-before-relation;
9. evidence-linked AI claims;
10. hostile-source/prompt-injection isolation;
11. snapshot history;
12. dependency-targeted invalidation;
13. precise deadline semantics;
14. MA admission/funding/strategic separation;
15. no autonomous outreach/submission.

---

## F. CLOSED TECHNICAL DECISIONS

### TECH-DEC-001 — Preserve donor application stack
Keep FastAPI, SQLAlchemy/Alembic, Next.js/React, donor source-adapter conventions, donor HTTP/proxy behavior where useful, Redis/RQ, LiteLLM, and CI shape.

### TECH-DEC-002 — PostgreSQL is canonical state
Use PostgreSQL for normal development/integration/release-candidate use.

SQLite may be used only for unit tests whose semantics are equivalent.

No Neo4j in V1.

### TECH-DEC-003 — RQ for job transport, LangGraph inside deep-research jobs
RQ/Redis owns queue execution/retry visibility.  
LangGraph owns multi-step research orchestration inside one research job.

Avoid two job schedulers.

### TECH-DEC-004 — Tiered fetching
1. donor HTTP/static parser for known/simple sources;
2. direct scholarly APIs for structured metadata;
3. Crawl4AI/Playwright only for JS-heavy or extraction-heavy sources.

Do not browser-render every page.

### TECH-DEC-005 — Structured scholarly connectors
- OpenAlex for people, works, institutions, topics, citations/funding metadata.
- OpenAIRE **production Graph API v3** for persons/projects/organizations/research products. Do not default to beta v4.

Both are evidence providers, not final match authorities.

### TECH-DEC-006 — Internal watch subsystem first
Implement snapshots/fingerprints/change events in-product.  
External automation/change-monitoring products remain optional later.

### TECH-DEC-007 — Versioned structured model output
Use Pydantic-compatible schemas for every consequential research node:
- claims;
- evidence IDs;
- claim type;
- unknowns;
- contradictions;
- protocol coverage.

Free prose is display synthesis only.

### TECH-DEC-008 — Deterministic policy functions
Eligibility, protocol completion, freshness, deadline normalization, funding arithmetic, invalidation, and suggested disposition should be pure/testable domain logic wherever possible.

### TECH-DEC-009 — No vector DB in V1
Use relational/structured retrieval and bounded full-text search. Add embeddings only after demonstrated retrieval failure.

### TECH-DEC-010 — Single-owner semantics
Preserve donor auth only if removing it raises risk. Do not build tenant/org features.

---

## G. PRODUCT / SCENARIO ACCEPTANCE

Trace all critical cases:

- Discovery: `SCN-001..008`
- Evidence/AI: `SCN-009..015`
- Supervisor: `SCN-016..020`
- PhD: `SCN-021..024`
- MA/funding: `SCN-025..030`
- Watch/change: `SCN-031..034`
- User/application: `SCN-035..038`
- Security/protocol/time: `SCN-039..048`
- Responsive/accessibility: `SCN-X-001..005`

Do not substitute implementation documentation for these scenario meanings.

---

## H. DESIGN / UI / UX CONTRACT

Primary navigation:

```text
Radar
PhD
MA + Funding
Supervisors
Watch
Profile & Routes
```

Required UX properties:
- evidence-dense rows rather than generic card grids;
- Case Dossier is the main research workspace;
- hard blocker visible in first dossier region;
- system suggestion separate from user decision;
- assessment -> evidence within two deliberate interactions;
- Research Coverage shows `searched+found`, `searched+none`, `not searched`, `blocked`;
- source authority and freshness visible;
- original deadline wording preserved;
- no page horizontal overflow at 320px;
- mobile retains review/evidence/disposition actions;
- keyboard-complete evidence flow;
- status does not depend on color.

Do not prioritize landing/marketing polish over research workflow completion.

---

## I. TECHNICAL CONTRACT

### I.1 Target responsibility map

Add bounded target domains while respecting donor structure:

```text
astra/
  academic_radar/
    domain/
      cases
      claims
      evidence
      protocols
      funding
      deadlines
      suggestions
      invalidation
      identity
    discovery/
      normalize
      resolve
      traces
    research/
      graph
      state
      nodes/
      schemas/
      prompts/
    connectors/
      openalex
      openaire
      university
      crawl4ai_adapter
    watch/
      snapshots
      diff
      scheduler
    profile/
      mozare_import

  db/
  api/routes/

dashboard/
  app/(app)/
    radar/
    phd/
    ma/
    supervisors/
    watch/
    profile/
    cases/[id]/
```

Exact paths may adapt to donor conventions; ownership boundaries may not collapse.

### I.2 Canonical state

- PostgreSQL: semantic durable state.
- React/client: ephemeral form/view/query cache only.
- Redis/RQ: job transport/state only.
- LangGraph: run orchestration/checkpoints only.
- External services: evidence only.

No duplicate durable semantic source of truth.

### I.3 Minimum schema

```text
candidate_profiles
candidate_evidence
mozare_routes

target_entities
person_identities
programmes
opportunities
funding_routes
entity_relations

evaluation_cases
case_disposition_history
application_stage_history
user_notes

research_protocols
research_runs
research_coverage

evidence_artifacts
source_snapshots
source_authorities
discovery_traces
evidence_dependencies

claims
claim_evidence
gate_assessments
dimension_assessments
funding_assessments
supervision_precedents

watch_targets
watch_checks
change_events

application_briefs
brief_dependencies
```

### I.4 Identity

Internal canonical IDs: UUID.  
External identifiers may include DOI, ORCID, OpenAlex, OpenAIRE, ROR, canonical source URL.

Never use display name as a stable key.

Resolution order:
1. explicit external ID;
2. official URL + institution;
3. name + institution + corroborating work/topic data;
4. unresolved candidate set.

Unresolved identity blocks relation merges.

### I.5 Claim/evidence contract

Consequential claim:
- claim type;
- epistemic status;
- evidence IDs or explicit Unknown/search evidence;
- source authority;
- source freshness;
- generated-by/run identity;
- protocol version;
- dependency links.

User review never converts `INFERENCE` into `EXTERNAL_FACT`.

### I.6 ResearchProtocol

Versioned route protocol stores:
- mandatory evidence classes;
- optional evidence classes;
- source preferences;
- identity requirements;
- freshness;
- stop conditions;
- blocking/allowed unknowns;
- assessment rules.

`EVIDENCE_READY` is computed, not set by model prose.

### I.7 Model boundary

Each research node receives:
- trusted system/task instructions;
- structured case state;
- bounded source blocks explicitly marked UNTRUSTED.

Returned structured payload validates against schema.

Invalid/missing-evidence output:
- may log diagnostics;
- may retry boundedly;
- must not mutate consequential assessment.

Store model ID, provider ID, prompt hash/version, schema version, protocol version, run ID. Never store credentials.

### I.8 Source authority

Enum:
- OFFICIAL_REGULATION
- OFFICIAL_PROGRAMME
- OFFICIAL_DEPARTMENT_OR_PERSON
- AUTHORITATIVE_REGISTRY
- PRIMARY_RESEARCH_OUTPUT
- REPUTABLE_SECONDARY
- DISCOVERY_AGGREGATOR
- UNKNOWN

Also store canonical-origin grouping to distinguish mirrors from independent sources.

### I.9 Deadline contract

```text
original_text
date_value
local_time_value?
timezone_name?
utc_instant?
precision: DATE_ONLY | LOCAL_TIME | OFFSET_AWARE | AMBIGUOUS
source_evidence_id
last_checked_at
```

Use IANA timezone when known. Never synthesize a missing 23:59/timezone.

### I.10 Funding

Use Decimal/NUMERIC.

FundingAssessment:
- source currency;
- award/period/duration;
- tuition/waiver;
- known mandatory costs;
- unknown costs;
- uncovered gap;
- eligibility/nomination/deadline gates.

Do not label `fully funded` with unknown material coverage.

### I.11 Dependency invalidation

Persist explicit edges:

```text
snapshot/evidence -> claim -> gate/dimension/funding assessment
                  -> suggestion
                  -> application brief
```

Change event traverses downstream only. Global invalidation is fallback/error recovery, not normal behavior.

### I.12 OpenAlex

Implement bounded queries with explicit selected fields and caching.

Prefer official identifiers/ORCID/ROR when available; OpenAlex author disambiguation is evidence, not absolute identity truth.

Support free API start; configuration may optionally accept API key.

### I.13 OpenAIRE

Use stable production `/graph/v3` endpoints for:
- persons;
- projects;
- organizations;
- research products.

Treat beta v4 as non-production unless a later implementation decision explicitly validates it.

### I.14 Crawler security

Before arbitrary fetch:
- allow only http/https;
- block local/private/link-local/metadata endpoints;
- restrict redirects with same SSRF policy;
- resource/time/size limits;
- content-type validation;
- PDF/parser limits;
- sanitize captured HTML for rendering;
- source text never enters control-message role.

Reuse donor SSRF/proxy protections where correct.

---

## J. QA CONTRACT

Use `RADAR-QA-2026-09-17-r1` as binding proof authority.

Tier-A release blockers include:
- route isolation;
- disposition immutability;
- Unknown/hard blockers;
- protocol completeness;
- evidence-bound AI;
- prompt injection;
- identity separation;
- source authority/independence;
- deadline precision/timezone;
- targeted invalidation;
- supervisor epistemics;
- funding arithmetic;
- application brief provenance;
- no autonomous outreach;
- user-state persistence.

Before trusting green results, run all required canaries in `CLAUDE_QA_CONTRACT.md`.

No donor-only evidence may close target QA.

---

## K. ALREADY DONE / DO NOT REDO

Already resolved:
- product meaning;
- target information architecture;
- case primitive;
- route models;
- evidence epistemics;
- user/system state separation;
- core UI behavior;
- route protocols;
- QA oracles;
- architecture direction.

Do not spend a new discovery sprint selecting an entirely different generic agent framework.

Do not add:
- Neo4j;
- vector DB;
- Kubernetes;
- external workflow automation;
- public multi-user features;
unless a concrete blocker proves necessary.

---

## L. LAUNCH MANIFEST

### Source control
- target repo: create/fork;
- default branch: `main` preferred;
- exact target HEAD must be frozen at release-candidate gate;
- retain donor remote if useful for selective upstream comparison.

### Release units
`UNIT-WEB`
- Next.js dashboard
- build: donor-aligned frontend build

`UNIT-API`
- FastAPI backend

`UNIT-WORKER`
- RQ worker with research/discovery/watch jobs

`UNIT-DB`
- PostgreSQL + Alembic migrations

`UNIT-REDIS`
- Redis queue/cache transport

No desktop release unit required for V1.

### Environment
Required:
- local;
- CI;
- release-candidate Docker Compose.

Staging/production: NOT_REQUIRED for terminal state.

### Configuration contract

Create/maintain `.env.example` with names only, no credentials.

Likely configuration classes:
- DATABASE_URL
- REDIS_URL
- SECRET_KEY/auth settings if donor auth retained
- LLM provider/model keys/settings
- OPENALEX_API_KEY optional
- OPENAIRE config/base URL
- crawler/proxy config
- research cycle/watch cadence

All config must validate at startup with actionable errors.

### Secrets
Server-side only. No LLM/API/database secrets in browser bundles, logs, evidence, prompts returned to UI, or exports.

### Jobs
RQ:
- discovery queue;
- research queue;
- watch queue or named job types;
- bounded retries/backoff;
- failed-job visibility;
- idempotency key where duplicate execution could create repeated state.

### Observability
Minimum:
- structured logs with run/case/source IDs;
- source-level failure classification;
- model node failure classification;
- prompt injection detection event;
- secret redaction;
- `/health` readiness checks for DB/Redis as appropriate.

No external paid error tracker required.

### Backup/rollback
For release-candidate local stack:
- migration test from clean DB;
- migration test from donor-compatible seed/previous target revision when one exists;
- pre-migration PostgreSQL dump procedure documented;
- Alembic downgrade only when safe; otherwise documented restore-from-backup path.

### CI
Preserve donor pattern and extend:
- backend pytest;
- offline/fixture self-test;
- frontend tests;
- lint;
- TypeScript;
- frontend build;
- dependency audits;
- migration-from-empty test;
- critical security/canary tests;
- Docker Compose build/smoke.

### External APIs
No external API is allowed to be the only copy of evidence; persist relevant metadata/source reference/snapshot.

Rate limit/backoff required.

### Domain/DNS/TLS
NOT_APPLICABLE for `RELEASE_CANDIDATE_READY`.

---

## M. MINIMAL EXECUTION HARNESS

Use:

```text
.git/mozare-academic-radar-execution/
  state.json
  logs/
  scratch/
  evidence-dev/
```

Example state:

```json
{
  "start_head": "",
  "donor_head": "8c300d28b9add865cd09b2e5e141f94a6b033c74",
  "current_phase": "",
  "completed": [],
  "open": [],
  "last_verified_sha": "",
  "last_full_gate": null,
  "blocking": null
}
```

Execution-local only; never use as product authority.

---

## N. CONCURRENCY SAFETY

Primary worktree is single-writer.

Before parallel work:
- record `git status`;
- save tracked/untracked baseline information;
- isolate parallel implementation agents in worktrees;
- read-only reviewers may inspect primary.

Never use destructive reset/clean on owner work without explicit authority.

---

## O. PREFLIGHT

Run:

```bash
git status --short
git branch --show-current
git rev-parse HEAD
git log --oneline -12
git diff --stat
```

Then:
1. record target start HEAD;
2. record donor HEAD;
3. run donor tests before semantic changes;
4. inspect existing schema/source adapters/job runner/API/frontend routing;
5. do not reread the full repo indiscriminately.

Use `map -> target -> inspect`.

---

## P. TASK DAG

### TASK-P00 — Fork and baseline
**Objective:** create target repo from donor; freeze donor and target identities.  
**Proof:** donor baseline tests/build or explicit donor failure report.  
**Gate:** GATE-BASELINE.

### TASK-P01 — Characterization + target test harness
Protect reusable donor behaviors:
- source run progress;
- partial failure;
- cancel;
- dedupe;
- saved/user state;
- exports;
- auth/local stack if retained.

Add target fixture conventions and QA canary scaffolding.

### TASK-P02 — Domain schema and migrations
Implement:
- canonical IDs;
- routes;
- cases;
- claim/evidence/snapshot;
- protocols/coverage;
- funding;
- dependencies;
- watch;
- brief/history.

**Oracles:** 001, 004..009, 019..020, 042..043.  
**Gate:** GATE-MIGRATION + targeted domain tests.

### TASK-P03 — Candidate profile + Mozare route importer
Import session/wiki-derived governed profile/routes into target seed/import mechanism.

Requirements:
- provenance of imported facts;
- route status;
- constraints;
- no hidden generic “field profile” replacing route model.

### TASK-P04 — Discovery adaptation
Preserve/adapt useful donor source adapters for priority countries and add:
- application-route classification;
- DiscoveryTrace;
- canonical dedupe;
- source authority baseline;
- target entity normalization.

**SCN:** 001..008.

### TASK-P05 — Structured scholarly connectors + identity resolution
Implement OpenAlex/OpenAIRE connectors and identity resolution.

**Oracles:** 013..016, 023, 027.  
**Canary:** same-name researcher merge.

### TASK-P06 — Evidence/snapshot/source-authority layer
Implement immutable-ish source snapshots, authority, independence grouping, evidence artifacts, claim links, Evidence Inspector API.

### TASK-P07 — ResearchProtocol engine
Create versioned protocols for:
- supervisor-first;
- advertised PhD;
- structured PhD;
- MA;
- funding assessment.

Implement deterministic completion/coverage.

**Oracles:** 008/009.

### TASK-P08 — Deep research graph
Implement LangGraph workflow nodes:
1. resolve identity;
2. current context/formal route;
3. recent research spine;
4. supervised/co-supervised projects;
5. concept/method/corpus genealogy;
6. project/funding context;
7. route translation;
8. contradictions/unknowns;
9. structured synthesis.

All nodes evidence-bound.

### TASK-P09 — Untrusted-source security boundary
Implement:
- control/data separation;
- SSRF policy;
- URL/resource limits;
- prompt-injection fixtures;
- secret/log redaction.

**Oracles:** 012/033.  
**Gate:** critical security canary.

### TASK-P10 — Deterministic assessments/suggestions
Implement:
- gates;
- supervisor 0–3 dimensions;
- MA three heads;
- funding arithmetic;
- freshness;
- suggestion rules.

System suggestion is not user disposition.

### TASK-P11 — Deadline engine
Implement precision-aware parsing/storage/display/urgency.

**Oracles:** 017/018.

### TASK-P12 — Watch + dependency invalidation
Implement WatchTarget, checks, fingerprints/diffs, change events, dependency traversal, targeted stale/recompute.

**Oracles:** 019/020.

### TASK-P13 — API surface
Add target endpoints with explicit schemas for:
- Radar;
- cases;
- evidence;
- research runs;
- funding;
- watch;
- routes/profile.

Preserve public contracts only where still semantically correct.

### TASK-P14 — UI shell and Radar
Implement accepted IA and attention queues.

### TASK-P15 — Case Dossier + evidence inspection
Implement gates, assessments, coverage, precedents, claim rows, source authority, evidence inspector, notes/disposition/application stage.

### TASK-P16 — PhD experiences
Supervisor-first, advertised, structured route filters/dossier states.

### TASK-P17 — MA + Funding
Implement programme case with independent heads and multiple linked funding packages.

### TASK-P18 — Watch/change UI
Diff/impacted-case review, rerun affected research, source health.

### TASK-P19 — Application Brief
Freeze evidence-bound brief with dependency versions; supersession detection.

### TASK-P20 — Responsive/accessibility closure
320/390/768/1024/1440 + 200% zoom, keyboard/focus/live-region/color-independent states.

### TASK-P21 — QA canaries + full regression
Execute entire r1 QA contract on exact target candidate.

### TASK-P22 — Container/release-candidate closure
Docker Compose, clean DB migration, seed/import, smoke, full CI, exact SHA freeze, docs truth.

---

## Q. PER-PHASE EXECUTION LOOP

For every task:

1. inspect smallest relevant donor/target area;
2. bind task to SCN/ORACLE;
3. make negative proof fail where defect/risk exists;
4. implement smallest coherent slice;
5. run targeted tests;
6. run adjacent tests;
7. update execution state;
8. commit coherent verified batch;
9. run full gate at phase boundary.

Never weaken oracle/test thresholds to get green.

---

## R. TEST / QA GATES

### GATE-BASELINE
Donor/fork runs its baseline suites or exact failures are recorded before target semantic changes.

### GATE-TARGETED
Task-specific unit/integration/UI tests.

### GATE-ADJACENT
Neighbors and preserved donor behavior around touched modules.

### GATE-MIGRATION
- empty DB upgrade;
- previous target revision upgrade when available;
- schema constraints;
- rollback/restore plan.

### GATE-SECURITY
- prompt-injection canary;
- SSRF;
- secret redaction;
- unsafe rendering;
- dependency audits.

### GATE-ACCESSIBILITY
- automated scan;
- keyboard path;
- focus restore/trap;
- no color-only state;
- 200% zoom.

### GATE-RESPONSIVE
320/390/768/1024/1440 geometry and action reachability.

### GATE-FULL
Backend + frontend + integration + canaries.

### GATE-BUILD
Frontend production build + API/worker import/start + container build.

### GATE-CI
Exact commit CI green with no unexpected critical skip.

### GATE-RC-SMOKE
Clean Docker Compose:
1. start;
2. migrate;
3. import/seed profile/routes;
4. run fixture-backed discovery;
5. create/research one supervisor case;
6. create one MA + funding case;
7. trigger one watch change;
8. generate brief;
9. restart services;
10. verify durable state.

No production smoke required.

---

## S. SOURCE-OF-TRUTH EDITING

Edit semantic sources only:
- models/migrations for data;
- domain rules for deterministic policy;
- prompt/schema source for research;
- components/pages for UI;
- compose/config source for deployment.

Do not hand-edit generated build output.

Prompt/schema versions are source artifacts and must be committed.

---

## T. NEW-DEFECT RULE

When execution finds a new issue, record:

```text
DEFECT_ID
SCN/ORACLE
Given/When
Expected/Actual
root cause
files
negative proof
targeted proof
closure
```

Fix without reopening planning only if it clearly violates accepted authority and introduces no new owner trade-off.

---

## U. SCOPE-FIDELITY AUDIT

Before closure, map every changed tracked file to:
- TASK-ID;
- intended effect;
- protected neighbor;
- proof.

Check specifically:
- no target behavior satisfied merely by hiding controls;
- no donor generic fit field remains authoritative;
- no old scholarship hard-coding remains reachable;
- no “research complete” path bypasses protocol;
- no user disposition write occurs from worker/suggestion code;
- no source text can generate tool/action instructions;
- no duplicate semantic state authority was introduced.

---

## V. FINAL FREEZE / CI / RELEASE-CANDIDATE

1. all authorized tasks complete;
2. no unexplained changes;
3. Tier-A QA green;
4. canaries green;
5. full local gate green;
6. build green;
7. migration clean;
8. exact candidate SHA recorded;
9. exact-head CI green;
10. clean Docker Compose RC smoke green;
11. create release-candidate evidence manifest;
12. stop at `RELEASE_CANDIDATE_READY`.

No public deploy without a later explicit owner instruction.

---

## W. OWNER-ACTION GATES

None block code execution.

Potential later owner action, not needed for V1 terminal state:
- production domain/hosting;
- paid model/provider credentials if chosen;
- public deployment;
- email/outreach integration;
- desktop packaging/signing.

Use local/mock/test provider configuration where real credentials are absent. Do not fake real-source success.

---

## X. FINAL RESPONSE FORMAT

Return:

```text
TARGET SHA
TERMINAL STATE

IMPLEMENTED
- task IDs

QA
- Tier-A
- Tier-B
- canary status
- full gate
- CI

RELEASE CANDIDATE
- compose/build identity
- migration
- smoke

KNOWN RISKS / UNTESTED
- exact items

OWNER ACTION REQUIRED
- only if applicable

EVIDENCE PATHS
```

No pass percentage as substitute for disposition.

---

## Y. ONE-LINE DIRECTIVE

Execute this intake against the target fork of the donor repository and continue through `RELEASE_CANDIDATE_READY` without reopening closed product/design decisions unless new authorized evidence proves a contradiction.
