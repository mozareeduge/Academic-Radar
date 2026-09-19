# 00 — PRODUCT HORIZON

**snapshot:** `RADAR-PDA-2026-09-17-r2`  
**status:** closed

## 1. Current truth

### PROJECT

**Working name:** Mozare Academic Radar  
**Class:** `RESEARCH_INSTRUMENT` + `INTERNAL_TOOL` + `AI_ASSISTED_SYSTEM` + `DESIGN_RECOMPOSITION` + `GREENFIELD_USING_EXISTING_REUSE`

The target product is a private research workspace that continuously discovers academic opportunities and reconstructs enough evidence to judge whether a **specific Mozare research route** can credibly enter a **specific supervisor/programme/project/funding ecology**.

It is not a generic scholarship search engine and not a university recommender.

### Maturity

- Product/research method: substantially defined.
- Reusable donor product: CIK/Astra exists and is inspectable.
- Target implementation: not yet asserted.
- Public/deployed target: none.
- Candidate: none frozen.

### User/actor center

Primary human user: **Mozare**, acting as researcher/applicant/reviewer.  
The system may later be generalized, but V1 must optimize for one owner rather than introduce multi-user product complexity.

### Explicit user constraints

- PhD research/application path must support English.
- MA must be English-taught.
- Current geography priority: Belgium, then Netherlands, then Germany.
- Evidence and unknowns must remain visible.
- Supervisor matching must include actual supervision precedents, projects, methods, theories, citations, infrastructures, and funding routes where available.
- MA evaluation must separate programme admission from scholarship/funding.
- Existing MA and BSc background must be interpreted honestly rather than assumed to satisfy formal prerequisites.
- The system must operate cyclically and recognize new/changed opportunities.

## 2. Product request

The product must make the following true:

1. New relevant opportunities and people can be discovered without rereading the web manually.
2. Every serious target can become an evidence-bound dossier.
3. Supervisor matching reconstructs a supervision track rather than keyword similarity.
4. Programme matching treats admission, funding, and strategic value as different questions.
5. The user can see why the system thinks something is promising, uncertain, blocked, stale, or urgent.
6. Model-generated interpretations are never silently promoted to external fact.
7. Changes to tracked sources can trigger targeted re-research rather than full recrawls.
8. User decisions, notes, accepted/rejected hypotheses, and application state survive subsequent crawls.
9. The product remains useful with partial source failure.
10. It can later hand a bounded, evidence-backed application brief to a writing/research workflow without inventing claims.

## 3. Target horizon

### HZN-001 — Evidence before recommendation

Every consequential evaluation must expose:
- the proposition being made;
- source/evidence supporting it;
- contradiction/unknown state;
- source date/freshness;
- whether the proposition is observed, externally stated, or inferred.

A fluent model summary alone is never sufficient.

### HZN-002 — Case is the evaluation primitive

Canonical unit:

```text
EvaluationCase =
    MozareRoute
    × Target
    × ApplicationRoute
```

`Target` may be a supervisor, PhD vacancy/project, structured doctoral programme, or MA programme.

Consequences:
- one supervisor can have several different cases;
- one MA can be a strong intellectual match and weak admission/funding case;
- fit is never stored only on `Person` or `Programme`.

### HZN-003 — Separate route logic

At minimum the system must distinguish:

1. `SUPERVISOR_FIRST_PHD`
2. `ADVERTISED_PHD`
3. `STRUCTURED_PHD`
4. `MA_PROGRAMME`

Funding is not a fifth application route. A scholarship/fellowship/waiver is a linked `FundingRoute` assessed against a programme/case through a `FundingAssessment`. One MA case may therefore contain several competing funding packages without duplicating the programme case.

They may share evidence infrastructure, never one scoring rubric.

### HZN-004 — Human decision authority

The system may suggest:
- Strong
- Watch
- Act
- Reject

but the user controls the persistent **disposition**.

Automatic processes control only research lifecycle states such as `DISCOVERED`, `RESEARCHING`, `EVIDENCE_READY`, `STALE`, or `FAILED`.

### HZN-005 — Honest uncertainty

Unknown, contradictory, inaccessible, stale, and unverified are first-class states. The UI must never manufacture a positive or negative answer simply to complete a score.

### HZN-006 — Background as evidence architecture

Mozare’s biography is not one generic CV blob. Relevant evidence from education, scholarship, artworks, repositories, curatorial work, product/system practice, languages, and prior research is selected per case to prove execution capability or narrative coherence.

### HZN-007 — Living cycles

The system supports:
- manual discovery runs;
- lightweight scheduled/incremental discovery;
- deeper research only for promising/changed cases;
- snapshots/diffs for watched pages;
- targeted reevaluation after material evidence changes.

No-change pages should not trigger expensive deep research.

### HZN-008 — Local/private by default

V1 is a private single-owner workspace. No public profile, social layer, employer marketplace, or collaboration model is required.

Data may originate from public web sources, but the user’s notes, case dispositions, application strategy, and derived analyses are private.

### HZN-009 — Source truth survives abstraction

The user must always be able to open:
- original source URL;
- captured snapshot metadata;
- extracted evidence;
- claim using that evidence.

A score/label cannot become the only representation of the source.

### HZN-010 — Actionable end state

A mature case exposes:
- route;
- formal gates;
- fit dimensions;
- evidence completeness;
- key precedents;
- current funding/application path;
- unresolved questions;
- deadline/urgency;
- recommended next research/action;
- user disposition;
- application progress if started.

## 4. Reuse / protected horizon from CIK

CIK is donor implementation evidence. Preserve these behaviors unless later repo evidence proves reuse is more expensive than replacement:

### HZN-011 — Useful ingestion behavior
- source adapters;
- concurrent source runs;
- freshness and deduplication;
- country/type/source filtering;
- source-run progress;
- partial results remain usable after cancellation where data integrity is safe.

### HZN-012 — Useful persistence behavior
- saved items survive recrawls;
- notes/state must not be erased by refreshed external data;
- user-facing export should represent the filtered/current view rather than silently query a different dataset.

### HZN-013 — Useful interaction behavior
- user can trigger a manual search;
- progress and source failures are visible;
- empty state offers a next action;
- external source links open explicitly as external evidence.

### Not protected
- current CIK field taxonomy;
- astronomy/person-specific assumptions;
- universal 0–100 fit score;
- source-specific visual design;
- current authentication/product marketing;
- page/component boundaries.

## 5. Owner priorities translated into product principles

### HZN-014 — Research depth is allocated, not uniform

Broad discovery must be cheap. Deep evidence reconstruction is reserved for:
- candidates that pass hard filters;
- candidates the user promotes;
- changed watch targets;
- ambiguous high-value cases.

### HZN-015 — No score without evidence

Arithmetic may summarize evidence already stored; no LLM may emit a final numeric score from hidden reasoning.

For supervisor-first PhD, existing 0–3 fit dimensions remain available:
1. topic resonance;
2. method alignment;
3. theory alignment;
4. practice/prototype openness;
5. ecosystem/infrastructure;
6. supervision capacity;
7. funding plausibility.

Each dimension must show evidence and uncertainty.

### HZN-016 — MA three-headline model

MA case displays three independent headline assessments:
- `Admission Viability`
- `Funding Viability`
- `Strategic Value`

No combined “MA fit score” is required.

### HZN-017 — Formal blockers dominate presentation

If a hard eligibility rule is clearly not met, intellectual fit stays visible but the case is marked `FORMALLY_BLOCKED`. The product must not bury this behind a high research-fit score.

### HZN-018 — Application writing remains downstream

V1 may create an **Application Brief** consisting of verified facts, matched candidate evidence, route rationale, unknowns, and source links. Full motivation letter/pre-proposal generation is downstream and must use that brief as authority rather than scrape the dossier ad hoc.


### HZN-019 — Route-specific research protocol

Every case type has an explicit evidence-requirement protocol defining:
- mandatory evidence classes;
- optional strengthening evidence;
- stop conditions;
- source-authority preference;
- freshness requirements;
- what may remain unknown;
- what blocks `EVIDENCE_READY`.

The research agent may search creatively inside this protocol, but may not decide that a missing mandatory class is “close enough.”

### HZN-020 — Source authority and independence

Evidence carries an authority class and, where relevant, an independence relation.

Default authority order for current programme/application facts:
1. official programme/funder/university regulation or call;
2. official department/project/supervisor page;
3. authoritative repository/registry or scholarly metadata;
4. primary publication/thesis/project output;
5. reputable secondary source;
6. discovery aggregator/search result/snippet.

A lower-authority source may discover a fact but must not silently override a conflicting higher-authority current source.

Multiple URLs that merely repeat the same upstream statement do not count as independent corroboration.

### HZN-021 — Temporal truth and deadline semantics

Every deadline/current-status fact must retain:
- source-local date/time text;
- source timezone if stated or inferable from authoritative context;
- normalized timestamp used for sorting/urgency;
- retrieval date;
- ambiguity flag.

The UI may show the user's local equivalent, but the original institutional deadline representation remains visible. If time-of-day/timezone is absent, the product must not invent one; the gate remains appropriately uncertain.

### HZN-022 — Untrusted-source boundary

All crawled webpages, PDFs, repository text, application calls, and extracted source content are **data**, never instructions to the research agent.

Embedded text that asks the agent to ignore rules, reveal secrets, alter scores, contact people, execute code, or change system behavior has no authority. The product must:
- isolate source content from control prompts;
- prohibit autonomous side effects from source instructions;
- preserve suspicious source text only as evidence when relevant;
- mark any research run invalid if control/data boundaries cannot be established.

### HZN-023 — Identity resolution before relational inference

Person, programme, project, institution, and funding identities require confidence sufficient for the downstream claim.

Ambiguous identity may be stored as candidates, but publication, supervision, grant, or eligibility relations must not be merged across unresolved entities.

### HZN-024 — Deterministic suggestion boundary

System suggestions (`Strong/Watch/Act/Reject`) are derived from explicit stored gates/assessments and configurable transparent rules after research. The LLM may propose evidence interpretations, but it does not directly set the suggestion field.

### HZN-025 — Incremental recomputation

When evidence changes, only claims, assessments, suggestions, briefs, and cases with explicit dependency links to that evidence are invalidated/recomputed. A global rerun is a fallback, not normal behavior.

## 6. Explicit non-goals

- predicting admissions probability without valid base-rate evidence;
- ranking universities as “best” through prestige heuristics;
- automatically emailing supervisors;
- auto-submitting applications;
- replacing official admissions advice;
- fabricating causal explanations for past PhD acceptance;
- maintaining a universal vector similarity score;
- generic career-market features;
- social/community features;
- public applicant profile;
- multi-user organization/tenant behavior in V1;
- Neo4j/vector DB/multi-agent swarm as product requirements;
- paid search/crawl services as mandatory core dependencies.

## 7. Route protocol minimums

The minimum research protocol is part of product meaning.

### Supervisor-first PhD
Mandatory before `EVIDENCE_READY`:
- identity resolved;
- current institutional/supervision context checked;
- recent/current research spine;
- at least one search for supervised/co-supervised projects, with `none found` distinguishable from `not searched`;
- route-specific theory/method/material/corpus relation;
- relevant funding/institutional route search;
- formal doctoral-route requirements;
- explicit unknowns and contradictions.

### Advertised PhD
Mandatory:
- official call;
- deadline/status;
- formal requirements;
- funding/employment facts;
- project/supervisor context where named;
- route-specific fit and applicant execution evidence;
- application mechanism.

### Structured PhD
Mandatory:
- official programme call/regulations;
- cohort/selection route;
- supervisor-selection timing;
- funding structure;
- formal admission requirements;
- route/track relevance.

### MA programme
Mandatory:
- official curriculum/programme page;
- teaching language;
- formal admission prerequisites;
- treatment of prior degree/second master's where decision-relevant;
- programme structure and actual capability gain;
- linked funding routes searched separately.

### Funding assessment
Mandatory per candidate funding route:
- official funding source;
- eligibility;
- nomination/application route;
- amount/coverage/duration;
- tuition/fee interaction where available;
- deadline;
- material uncovered costs/unknowns.

## 8. Success criteria for the first production-worthy version

The first production-worthy version is complete when the user can:

1. import/inspect the current Mozare routes and evidence;
2. run discovery for the priority countries;
3. open a discovered supervisor and create a route-specific case;
4. run bounded supervisor-track research and inspect every claim/evidence link;
5. compare several supervisor cases without a hidden universal score;
6. inspect a PhD vacancy case with eligibility/deadline/funding/action state;
7. inspect an MA case with separate admission/funding/strategic assessments;
8. save Watch/Strong/Act/Rejected dispositions without them being overwritten by future runs;
9. see changed watched pages and selectively rerun impacted research;
10. export or copy an evidence-backed Application Brief.

## 9. Technical consequence tags — not architecture authority

The product meaning implies:
- persistence;
- provenance;
- background jobs;
- temporal sequencing;
- source snapshots;
- deterministic eligibility rules;
- human review of model-derived claims;
- recoverable failures;
- scheduled work;
- data migration from donor schema if CIK is forked.

Framework/database/deployment details belong to the final execution compiler, notwithstanding the current architecture preference documented in session memory.
