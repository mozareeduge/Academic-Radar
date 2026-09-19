# MOZARE ACADEMIC RADAR — FINAL THREE-LAYER PACKAGE

**Package revision:** `RADAR-PACKAGE-2026-09-17-r1`

## Frozen identities

- Product/design authority: `RADAR-PDA-2026-09-17-r2`
- QA authority: `RADAR-QA-2026-09-17-r1`
- Execution intake: `RADAR-EXEC-2026-09-17-r1`
- Donor planning baseline: `mimdot/CIK@8c300d28b9add865cd09b2e5e141f94a6b033c74`

## Status

- Layer 1: `PRODUCT_DESIGN_AUTHORITY_CLOSED`
- Layer 2: `QA_CONTRACT_READY_FOR_EXECUTION`
- Layer 3: `READY_FOR_CODE_EXECUTION`
- Runtime target verification: `UNTESTED` — no target implementation exists yet
- Execution terminal target: `RELEASE_CANDIDATE_READY`

## Read order

1. `01_PRODUCT_DESIGN_AUTHORITY/MIDDLE_LAYER_INDEX.md`
2. `01_PRODUCT_DESIGN_AUTHORITY/00_PRODUCT_HORIZON.md`
3. `01_PRODUCT_DESIGN_AUTHORITY/01_OBJECT_STATE_AND_FLOW_MODEL.md`
4. `01_PRODUCT_DESIGN_AUTHORITY/02_SCENARIO_CASE_ATLAS.md`
5. `01_PRODUCT_DESIGN_AUTHORITY/03_DESIGN_UIUX_BLUEPRINTS.md`
6. `01_PRODUCT_DESIGN_AUTHORITY/04_COPY_DECK.md`
7. `01_PRODUCT_DESIGN_AUTHORITY/05_DECISION_AND_SUPERSESSION_LEDGER.md`
8. `02_QA/QA_STATE.yaml`
9. `02_QA/QA_ORACLE_REGISTER.md`
10. `02_QA/CLAUDE_QA_CONTRACT.md`
11. `03_EXECUTION/CLAUDE_CODE_EXECUTION_INTAKE.md`
12. `TRACEABILITY_MATRIX.md`
13. `CROSS_LAYER_VALIDATION_REPORT.md`

## One-sentence system definition

A private living academic-intelligence system that discovers opportunities, reconstructs evidence-bound supervisor/programme/funding tracks, evaluates them against route-specific Mozare research possibilities, watches material changes, and produces auditable action/application briefs without hiding uncertainty or delegating decisions to the model.

## Architecture frozen for V1

- CIK/Astra donor application skeleton
- FastAPI
- SQLAlchemy + Alembic
- PostgreSQL canonical state
- Redis/RQ jobs
- LangGraph inside deep-research jobs
- tiered HTTP → structured APIs → Crawl4AI/Playwright fetching
- OpenAlex
- OpenAIRE production Graph API v3
- Next.js / React UI
- internal snapshot/watch subsystem
- no Neo4j/vector DB/external workflow product in V1
