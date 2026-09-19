# MIDDLE LAYER INDEX — Mozare Academic Radar

**authority_snapshot_id:** `RADAR-PDA-2026-09-17-r2`  
**authority_revision:** `2`  
**generated_at:** `2026-09-17`  
**status:** `PRODUCT_DESIGN_AUTHORITY_CLOSED`  
**artifact mode:** `AUTHORITY_ONLY`

## Purpose

This packet is the Layer‑1 product/design authority for the Mozare Academic Radar. It closes product meaning, state, flows, evidence behavior, UI/UX behavior, copy, responsive/accessibility consequences, and reversible defaults before QA and implementation planning.

The product is a private, evidence-first research instrument for finding and evaluating:
- PhD supervisors and supervisor-first doctoral routes;
- advertised/funded PhD positions and structured programmes;
- English-taught MA/Research MA programmes;
- scholarship/funding routes attached to MA programmes;
- changes in high-value people, projects, calls, programmes, and funding pages.

Priority geography is **Belgium → Netherlands → Germany**. English-language study/research is a hard user constraint.

## Source corpus / authority basis

1. `MOZARE_ACADEMIC_RADAR_SESSION_MEMORY_v0.2.md` — accepted working memory and architecture decision.
2. User’s explicit current instructions and earlier project decisions.
3. Current CIK/Astra upstream inspected as reusable implementation evidence, especially:
   - `dashboard/app/(app)/opportunities/page.tsx`
   - `dashboard/app/(app)/supervisors/page.tsx`
   - `ARCHITECTURE.md`
4. `01_PRODUCT_DESIGN_POSSIBILITY_SPACE_COMPILER...md` — control governing this packet.

CIK is **CURRENT/REFERENCE PRODUCT TRUTH for the donor system**, not authority for the target product. Its useful collection/state/UI behaviors may be protected; its generic fit score and field assumptions are not.

## Files

| File | Authority |
|---|---|
| `00_PRODUCT_HORIZON.md` | purpose, target/protected horizon, actors, priorities, non-goals, product principles |
| `01_OBJECT_STATE_AND_FLOW_MODEL.md` | canonical object model, states, commands, surfaces, external dependencies, journeys |
| `02_SCENARIO_CASE_ATLAS.md` | consequence classes and scenario-level acceptance |
| `03_DESIGN_UIUX_BLUEPRINTS.md` | information architecture, component anatomy, responsive/accessibility/design grammar |
| `04_COPY_DECK.md` | consequential English UI copy |
| `05_DECISION_AND_SUPERSESSION_LEDGER.md` | DEC records, conflicts, reversible defaults, supersessions |

## Stable namespaces

`DEC-*` · `HZN-*` · `ACT-*` · `OBJ-*` · `SURF-*` · `FLOW-*` · `SCN-*` · `COPY-*`

## Product status

No Mozare Academic Radar implementation candidate is asserted to exist yet. CIK/Astra is a donor/reference system. Runtime QA therefore belongs to the next QA layer and must initially treat candidate execution as `UNTESTED`.

## Owner gates

None block product/design closure. All currently unresolved choices have been resolved as reversible defaults. They can be superseded later through explicit `DEC-*` revisions.

## Revision-2 reconciliation changes

- Funding moved from a peer application-route concept to linked FundingAssessments.
- Added versioned ResearchProtocol and protocol-based evidence readiness.
- Added source authority/independence semantics.
- Added deadline precision/time-zone semantics.
- Added explicit untrusted-source/prompt-injection boundary.
- Added evidence dependency edges and incremental invalidation.
- Added deterministic suggestion boundary and identity-before-relation rule.

## Superseded material

- Generic “one fit score ranks supervisors/programmes” behavior is superseded.
- Hard-coded astronomy/person-specific scholarship logic from CIK is not target behavior.
- Queue labels such as `New / Researching / Strong / Watch / Act / Rejected` are retained as a useful mental model, but this authority separates **system research state**, **system suggestion**, **user disposition**, and **application stage** so one overloaded status cannot corrupt meaning.
