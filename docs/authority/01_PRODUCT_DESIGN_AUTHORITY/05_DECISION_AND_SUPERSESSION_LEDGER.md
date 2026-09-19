# 05 — DECISION AND SUPERSESSION LEDGER

**snapshot:** `RADAR-PDA-2026-09-17-r2`

**revision note:** cross-layer reconciliation revision; see DEC-035 onward.

## Authority precedence

1. explicit current owner decisions;
2. this accepted product/design authority;
3. verified external rules applicable to a concrete programme/source;
4. current target implementation as baseline evidence;
5. donor CIK behavior;
6. proposals/heuristics;
7. historical/superseded material.

## Decision records

### DEC-001 — Evaluation primitive
**Question:** What is actually matched?  
**Decision:** `MozareRoute × Target × ApplicationRoute` is the canonical EvaluationCase.  
**Reason:** prevents person/programme-level overgeneralization.  
**Consequences:** fit data lives on cases; entities can have multiple cases.  
**owner_only:** no

### DEC-002 — No universal fit score
**Decision:** remove a cross-route universal 0–100 score as target authority.  
Supervisor dimensions may use explicit 0–3 values; MA uses separate viability heads.  
**Supersedes:** generic CIK ranked-fit presentation.

### DEC-003 — Status decomposition
Separate:
- system research state;
- system suggested disposition;
- user disposition;
- application stage.
Queue views may combine them visually but storage/behavior may not.

### DEC-004 — Human disposition authority
Only the user persists `STRONG/WATCH/ACT/REJECTED`.  
Automations may suggest but not silently decide.

### DEC-005 — Hard blockers
A verified hard eligibility failure creates a formal blocker. Intellectual/research fit remains visible for explanatory value but cannot present the case as actionable.

### DEC-006 — Unknown semantics
Unknown is not zero, fail, or neutral evidence. Calculations must preserve missingness.

### DEC-007 — Single-owner product
V1 is private/single-owner. Do not build organization, sharing, permissions, or public profiles.

### DEC-008 — English-first UI
Product UI and generated research artifacts use English. External source excerpts retain source language where needed with translated summary clearly marked if translation is generated.

### DEC-009 — Geography
Default discovery scopes Belgium, Netherlands, Germany. An `Explore Europe` filter exists but is off by default in scheduled runs.

### DEC-010 — Research economy
Default cycles:
- lightweight incremental discovery: daily-capable;
- deeper reevaluation: change-triggered or user-promoted;
- weekly review digest/queue is allowed.
Exact scheduling belongs to configuration, not product identity.

### DEC-011 — Evidence versioning
External source updates append snapshots and invalidate dependent claims; they do not destructively overwrite historical evidence.

### DEC-012 — Claim ontology
Claim type and epistemic status are visible data, not prose convention.

### DEC-013 — User correction
User corrections create or replace assessments with traceable history; they never edit an old external snapshot.

### DEC-014 — Archive over delete
Cases, reviewed claims, and application briefs are archived by default. Destructive deletion is an advanced maintenance operation outside normal flow.

### DEC-015 — Supervisor track representation
Canonical track representation is structured list/timeline/evidence relationships. A node-link graph may supplement it but is not required for correctness.

### DEC-016 — CIK reuse boundary
Reuse donor ingestion/progress/freshness/saved/export patterns where effective. Do not preserve donor field taxonomy, generic score, marketing/auth assumptions, or scholarship hard-coding as product requirements.

### DEC-017 — Source run cancellation
Cancellation preserves already-valid results and labels run `CANCELLED/PARTIAL`. No “success” copy.

### DEC-018 — Research output validation
Model output without recoverable evidence links is invalid for consequential claims. Store as failed/needs-review output, not assessment.

### DEC-019 — MA evaluation
MA case uses:
1. Admission Viability
2. Funding Viability
3. Strategic Value
plus evidence/unknowns.
No combined MA score.

### DEC-020 — Second-MA handling
Existing MA status is a dedicated formal gate and narrative question. It must never be assumed either disqualifying or acceptable.

### DEC-021 — Supervisor-first PhD dimensions
Retain the seven existing 0–3 dimensions as a transparent comparison aid; every non-unknown value requires evidence.

### DEC-022 — ApplicationBrief boundary
The product prepares an evidence-backed brief but does not automatically draft/send final correspondence as part of V1 product completion.

### DEC-023 — Alert strategy
V1 must have in-app Radar attention states. External email/push notifications are optional future integrations, not a dependency.

### DEC-024 — Responsive scope
Desktop is the research-primary environment; mobile supports complete triage/review/decision/action visibility. Complex editors reflow into full-screen tasks rather than losing capability.

### DEC-025 — UI density
Use evidence-dense research surfaces, not a card-only consumer dashboard. Cards are for queue scanning; dossier content uses structured sections, rows, tables/timelines where semantically appropriate.

### DEC-026 — Color semantics
State must never rely on color. Labels/icons/borders/text carry status; color reinforces.

### DEC-027 — External source failure
Source failures are visible per source. A failing source cannot invalidate valid results from other sources and cannot be silently ignored.

### DEC-028 — Freshness
Each consequential external fact exposes `last checked`. Stale critical facts are visually elevated before action/application brief freeze.

### DEC-029 — Suggested disposition
System may derive a suggestion from explicit rules/evidence but must show the reasons and uncertainty. It cannot masquerade as admission probability.

### DEC-030 — “High chance” language
Do not use probability labels without real base-rate evidence. Prefer `formally strong`, `intellectually strong`, `funding weak`, `eligibility uncertain`, etc.

### DEC-031 — Evidence completeness
Completeness is measured as coverage of required evidence classes for the route, not token count or number of URLs.

### DEC-032 — Changed-page reruns
Unchanged watched snapshots do not trigger deep model research. Material change marks only dependent cases stale.

### DEC-033 — Search trace
Every discovered target stores discovery source/query/run so the user can understand why it appeared.

### DEC-034 — Copy truthfulness
Copy must distinguish `found`, `researched`, `reviewed`, `saved`, `applied`, and `verified`. These words are not interchangeable.

## Reversible defaults resolved in this revision

- Default queue sort: urgency first when deadline ≤30 days, otherwise user disposition/system research priority, then evidence freshness.
- Default list density: comfortable-dense, ~56–72px case row equivalent on desktop.
- Default evidence drawer: right side on wide desktop; modal/full page on smaller viewports.
- Default manual discovery country scope: remembers the last user selection.
- Default scheduled discovery: priority countries only.
- Default “Explore Europe”: off.
- Default output language: English.
- Default archive retention: indefinite unless user later requests pruning.

## Supersession notes

- Any existing CIK text that says “ranked by fit” is implementation history, not target product wording.
- Any hard-coded scholarship record tied to the donor applicant is excluded.
- Earlier conceptual queue labels remain valid UI labels only when mapped to the decomposed states above.
- Architectural preferences from session memory (CIK + LangGraph + Crawl4AI + OpenAlex/OpenAIRE + Postgres) remain planning context but are not frozen here as product authority; the final execution compiler will choose/confirm technical architecture.

## Closure

`PRODUCT_DESIGN_AUTHORITY_CLOSED`


### DEC-035 — Funding is relational, not an application route
Funding opportunities are linked `FundingAssessment`s under a programme/case. They do not create duplicate MA cases merely because several scholarships exist.
**Supersedes:** r1 `MA_FUNDING_ROUTE` as a peer application-route enum.

### DEC-036 — Research completion is protocol-based
Deep research completes only against a versioned `ResearchProtocol`; model narrative completion is not completion.

### DEC-037 — Source authority is explicit
Official current programme/funder rules govern formal gates over aggregators/secondary summaries unless authority/freshness is unresolved.

### DEC-038 — Copied evidence is not independent evidence
Evidence stores canonical-origin grouping; repeated syndication cannot inflate corroboration strength.

### DEC-039 — Deadline precision is preserved
Do not invent time-of-day or timezone. Store original deadline representation and normalized timestamp only at justified precision.

### DEC-040 — Untrusted web content cannot control the agent
All retrieved content is data. Source instructions cannot alter control prompts, execute tools, contact people, expose secrets, or mutate dispositions.

### DEC-041 — Suggestions are deterministic downstream summaries
The LLM creates claims/interpretations; a transparent rule layer derives `suggested_disposition`. The user alone sets `user_disposition`.

### DEC-042 — Dependency-based invalidation
Changed evidence invalidates only explicitly dependent claims/assessments/suggestions/briefs whenever the dependency graph is intact.

### DEC-043 — Identity precedes relation
Unresolved entity identity blocks relational claims that could mix works/projects/supervision across entities.
