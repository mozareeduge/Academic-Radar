# QA ORACLE REGISTER — Mozare Academic Radar

**qa_snapshot_id:** `RADAR-QA-2026-09-17-r1`  
**authority_snapshot_id:** `RADAR-PDA-2026-09-17-r2`  
**candidate:** none — pre-code  
**runtime verdict:** `UNTESTED`

This register derives acceptance oracles from the product/design authority. No oracle below is a runtime PASS. `AUTH` and `DERIVED` oracles are binding; `STANDARD` is binding where applicable; `HEURISTIC` identifies quality risk only.

## Critical oracle register

### ORACLE-001 — Case identity is route-specific
**revision:** 1  
**basis:** AUTH  
**sources:** HZN-002, DEC-001, SCN-016  
**statement:** Evaluative fit/assessment state belongs to `MozareRoute × Target × ApplicationRoute`; person/programme records cannot carry a universal case fit that leaks across routes.  
**risk:** critical  
**divergence:** one route's score/assessment appears automatically on another route case.

### ORACLE-002 — User disposition is automation-proof
**basis:** AUTH  
**sources:** HZN-004, DEC-004, SCN-035, SCN-047  
**statement:** Crawls, model research, deterministic suggestion recomputation, and evidence refresh cannot mutate the persisted user disposition.  
**risk:** critical

### ORACLE-003 — System suggestion is transparent and deterministic
**basis:** AUTH  
**sources:** HZN-024, DEC-041, SCN-047  
**statement:** system suggestion is derived from explicit stored gates/assessments/rules; an LLM response cannot directly set it. Reasons/inputs are inspectable.  
**risk:** critical

### ORACLE-004 — Unknown remains unknown
**basis:** AUTH  
**sources:** HZN-005, DEC-006  
**statement:** missing evidence is represented as `UNKNOWN`, not zero/fail/pass/neutral score.  
**risk:** critical

### ORACLE-005 — Hard formal blocker dominates actionability
**basis:** AUTH  
**sources:** HZN-017, DEC-005, SCN-022  
**statement:** a verified unmet hard requirement is visible before fit and blocks actionable application suggestion even when research fit is strong.  
**risk:** critical

### ORACLE-006 — MA heads remain independent
**basis:** AUTH  
**sources:** HZN-016, DEC-019, SCN-025..030  
**statement:** Admission Viability, Funding Viability, and Strategic Value are separate assessments; one cannot silently determine another or collapse into one “MA fit” score.  
**risk:** critical

### ORACLE-007 — Funding is relational under the programme case
**basis:** AUTH  
**sources:** DEC-035, OBJ-015, SCN-046  
**statement:** multiple scholarship/funding routes attach as FundingAssessments to one programme case; they do not create duplicate MA application cases.  
**risk:** high

### ORACLE-008 — Research completeness is protocol-based
**basis:** AUTH  
**sources:** HZN-019, DEC-036, OBJ-014, SCN-040  
**statement:** `EVIDENCE_READY` requires completion/disposition of every mandatory evidence class in the active protocol. Narrative/model completion is irrelevant.  
**risk:** critical

### ORACLE-009 — “searched none found” differs from “not searched”
**basis:** DERIVED  
**sources:** HZN-019, DS-PROTOCOL-COVERAGE, COPY-058/059  
**statement:** protocol coverage distinguishes searched-with-zero-evidence from a skipped/not-yet-searched evidence class.  
**risk:** high

### ORACLE-010 — Consequential AI claims require evidence links
**basis:** AUTH  
**sources:** HZN-001, DEC-018, SCN-009/010  
**statement:** unsupported model assertions cannot enter gates, dimensions, suggestions, or briefs.  
**risk:** critical

### ORACLE-011 — Inference never mutates into external fact
**basis:** AUTH  
**sources:** OBJ-005, SCN-013/014  
**statement:** user review can accept/reject an inference but cannot reclassify it as an externally observed fact.  
**risk:** critical

### ORACLE-012 — Untrusted source content has no control authority
**basis:** AUTH  
**sources:** HZN-022, DEC-040, SCN-039  
**statement:** crawled webpage/PDF/source text cannot change prompts, invoke arbitrary tools, reveal secrets, contact people, execute code, or mutate scores/dispositions.  
**risk:** critical

### ORACLE-013 — Identity precedes relational inference
**basis:** AUTH  
**sources:** HZN-023, DEC-043, SCN-003/048  
**statement:** ambiguous persons/institutions/projects cannot have publications, supervision, grants, or collaborations merged until identity confidence meets the relation's threshold.  
**risk:** critical

### ORACLE-014 — Source authority governs formal rules
**basis:** AUTH  
**sources:** HZN-020, DEC-037, SCN-041  
**statement:** current official programme/funder/university rules outrank discovery aggregators and secondary summaries for formal gates unless official authority/freshness is itself unresolved.  
**risk:** critical

### ORACLE-015 — Repeated sources do not fake corroboration
**basis:** AUTH  
**sources:** HZN-020, DEC-038, SCN-042  
**statement:** syndicated/copied statements sharing a canonical origin count as one upstream assertion for independence/corroboration.  
**risk:** high

### ORACLE-016 — Contradiction remains visible
**basis:** AUTH  
**sources:** HZN-005, SCN-011  
**statement:** unresolved contradictory evidence is stored/displayed as contradiction rather than arbitrarily resolved.  
**risk:** high

### ORACLE-017 — Deadline precision is not invented
**basis:** AUTH  
**sources:** HZN-021, DEC-039, SCN-043/044  
**statement:** original deadline text and precision are retained; missing time/timezone is not fabricated. Any normalized instant is only created when justified.  
**risk:** critical

### ORACLE-018 — Official local deadline survives timezone conversion
**basis:** AUTH/STANDARD  
**sources:** HZN-021, SCN-044  
**statement:** when a timezone-aware institutional deadline exists, UI preserves it and any user-local conversion is secondary and mathematically correct, including DST.  
**risk:** critical

### ORACLE-019 — Evidence refresh is append/version based
**basis:** AUTH  
**sources:** HZN-009, DEC-011, OBJ-007  
**statement:** re-fetch creates a new snapshot; historical source state is not silently overwritten.  
**risk:** high

### ORACLE-020 — Invalidation follows dependency edges
**basis:** AUTH  
**sources:** HZN-025, DEC-042, OBJ-016, SCN-034/045  
**statement:** evidence changes stale/recompute only dependent claims/assessments/suggestions/briefs in normal operation; unrelated reviewed state survives.  
**risk:** critical

### ORACLE-021 — Source failure does not erase valid work
**basis:** AUTH  
**sources:** DEC-027, SCN-004/015  
**statement:** valid results/evidence from successful sources persist through failures; failure remains visible.  
**risk:** high

### ORACLE-022 — Cancellation preserves partial valid results honestly
**basis:** AUTH  
**sources:** DEC-017, SCN-005  
**statement:** cancellation produces `CANCELLED` or `PARTIAL`, preserves already committed valid results, and never emits complete-success copy.  
**risk:** high

### ORACLE-023 — Deduplication preserves provenance
**basis:** AUTH/DERIVED  
**sources:** HZN-009, SCN-002  
**statement:** canonical entity dedupe retains all materially distinct source/evidence records and discovery traces.  
**risk:** high

### ORACLE-024 — Discovery reason is inspectable
**basis:** AUTH  
**sources:** DEC-033, OBJ-017, SCN-001  
**statement:** every discovered target retains run/source/query/trace sufficient to explain why/how it entered the system.  
**risk:** normal

### ORACLE-025 — No-results copy is scoped
**basis:** AUTH  
**sources:** SCN-006, COPY-006  
**statement:** zero results for a run never implies no opportunities exist globally.  
**risk:** normal

### ORACLE-026 — Closed opportunities remain historical but non-actionable
**basis:** AUTH  
**sources:** SCN-007, COPY-042  
**statement:** closed target is retained; Apply/Act suggestion is removed/blocked while evidence/history remain.  
**risk:** high

### ORACLE-027 — Supervisor track distinguishes authored vs supervised work
**basis:** AUTH  
**sources:** OBJ-008, SCN-017/018, COPY-035  
**statement:** supervised work can demonstrate supervision permissiveness but is never misattributed as the supervisor's own authored research.  
**risk:** critical

### ORACLE-028 — No causal acceptance claim
**basis:** AUTH  
**sources:** explicit project method, COPY-035  
**statement:** the system may identify supervision precedents but does not claim those characteristics caused historical applicant acceptance.  
**risk:** high

### ORACLE-029 — Funding viability uses coverage arithmetic
**basis:** AUTH  
**sources:** SCN-028, C-08, COPY-029..031  
**statement:** award existence alone cannot produce “fully funded”; tuition/fees/duration/known mandatory costs and unknowns are represented in coverage.  
**risk:** critical

### ORACLE-030 — Existing MA is an explicit gate/question
**basis:** AUTH  
**sources:** DEC-020, SCN-026  
**statement:** second-MA eligibility is neither assumed acceptable nor disqualifying; official evidence governs.  
**risk:** critical

### ORACLE-031 — English hard constraint is actual completion language
**basis:** AUTH  
**sources:** user constraint, SCN-029  
**statement:** a programme fails the English constraint if a mandatory component prevents degree completion in English.  
**risk:** critical

### ORACLE-032 — Application brief is candidate-bound and evidence-bound
**basis:** AUTH  
**sources:** HZN-018, OBJ-013, SCN-036/037  
**statement:** brief freezes case/evidence version, identifies unknowns/prohibited claims, and becomes superseded when dependent case evidence materially changes.  
**risk:** critical

### ORACLE-033 — No autonomous outreach/submission
**basis:** AUTH  
**sources:** non-goals, DEC-022  
**statement:** V1 does not send emails, contact supervisors, or submit applications automatically.  
**risk:** critical

### ORACLE-034 — Search stored data and discover web are distinct actions
**basis:** AUTH  
**sources:** FILTER/SEARCH DESIGN, COPY-001/002  
**statement:** UI distinguishes local/stored search from network discovery/background research.  
**risk:** normal

### ORACLE-035 — Hard blocker visible without scroll on dossier
**basis:** AUTH  
**sources:** DESIGN ACCEPTANCE #5  
**statement:** on target supported viewport, formal blocker is visible in the initial dossier summary/header region.  
**risk:** high

### ORACLE-036 — Assessment trace is reachable within two interactions
**basis:** AUTH  
**sources:** DESIGN ACCEPTANCE #3  
**statement:** user can move from an assessment to its supporting evidence in no more than two deliberate UI activations.  
**risk:** normal/high

### ORACLE-037 — Mobile preserves semantic actions
**basis:** AUTH/STANDARD  
**sources:** DEC-024, SCN-X-001  
**statement:** review, evidence/source opening, disposition, and valid primary action remain reachable at 320px/390px; no core capability disappears because of viewport.  
**risk:** high

### ORACLE-038 — Keyboard evidence review is complete
**basis:** STANDARD/AUTH  
**sources:** SCN-X-002, DS-FOCUS  
**statement:** claim/evidence workflow is fully keyboard-operable; modal/sheet focus trap and restoration are correct.  
**risk:** high

### ORACLE-039 — Status meaning is color-independent
**basis:** STANDARD/AUTH  
**sources:** DEC-026, SCN-X-003  
**statement:** pass/fail/unknown/stale/inference/user-decision remain distinguishable without color.  
**risk:** high

### ORACLE-040 — No page-level horizontal overflow at 320px
**basis:** AUTH  
**sources:** DESIGN ACCEPTANCE #8, SCN-X-004  
**statement:** core pages/components do not create page-level horizontal scroll at 320 CSS px; long tokens are contained.  
**risk:** normal

### ORACLE-041 — Async completion does not steal focus
**basis:** STANDARD/DERIVED  
**sources:** SCN-X-005  
**statement:** background completion updates notification/Radar state without moving keyboard focus.  
**risk:** normal

### ORACLE-042 — User-created notes/application state survive recrawl
**basis:** AUTH  
**sources:** HZN-012, cross-state invariants  
**statement:** external refresh/dedupe cannot erase notes, application stage, corrections, or dispositions.  
**risk:** critical

### ORACLE-043 — Archive is reversible with history
**basis:** AUTH  
**sources:** DEC-014, SCN-038  
**statement:** normal archive/restore preserves history, notes, evidence links, and disposition.  
**risk:** normal

### ORACLE-044 — Export reflects represented filtered view
**basis:** AUTH  
**sources:** HZN-012  
**statement:** a view-scoped export contains the records represented by the active filter/sort scope and declares export scope.  
**risk:** normal

### ORACLE-045 — Research/model outage is non-destructive
**basis:** AUTH  
**sources:** COPY-054, external dependency behavior  
**statement:** model outage preserves collected evidence and prior reviewed assessments; no assessment is cleared merely because generation failed.  
**risk:** high

## Heuristic quality oracles

### ORACLE-H01 — Evidence-dense without card soup
**basis:** HEURISTIC  
**sources:** DEC-025, DS-FOUNDATION  
**statement:** scanning and comparison should use structured rows/tables/timelines where semantically stronger than repeated cards. Divergence is a quality risk, not automatic defect.

### ORACLE-H02 — Case comprehension
**basis:** HEURISTIC/AUTH acceptance target  
**sources:** DESIGN ACCEPTANCE #1/#2  
**statement:** a reviewer should understand type/relevance/blocker/deadline/next action quickly and locate evidence completeness without reconstructing the page.

## Applicability / deferred oracles

- Multi-user authorization/tenant isolation: NOT_APPLICABLE V1.
- Email delivery/submission: NOT_APPLICABLE V1 except proof that no autonomous side effect exists.
- RTL/localized UI: NOT_APPLICABLE V1; source-language evidence may appear.
- Production deployment topology: TOPOLOGY_DEPENDENT until execution intake.
- Performance SLA: ORACLE_UNRESOLVED as numeric threshold; functional job progress/cancellation remains binding.
