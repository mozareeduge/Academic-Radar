# QA Traceability Report — P21

**snapshot_id:** `RADAR-QA-2026-09-17-r1`  
**date:** 2026-09-20  
**canary_tests_passed:** 8/8

## Oracle Coverage Table

| ORACLE-ID | Test File(s) Found | Tier |
|-----------|-------------------|------|
| ORACLE-001 | NONE | A |
| ORACLE-002 | astra/tests/academic_radar/test_suggestions.py | A |
| ORACLE-003 | NONE | A |
| ORACLE-004 | NONE | A |
| ORACLE-005 | NONE | A |
| ORACLE-006 | NONE | A |
| ORACLE-007 | NONE | A |
| ORACLE-008 | astra/tests/academic_radar/test_protocol_loader.py, astra/tests/academic_radar/test_protocols.py | A |
| ORACLE-009 | astra/tests/academic_radar/test_protocol_loader.py, astra/tests/academic_radar/test_protocols.py | A |
| ORACLE-010 | NONE | A |
| ORACLE-011 | NONE | A |
| ORACLE-012 | NONE | A |
| ORACLE-013 | NONE | A |
| ORACLE-014 | NONE | A |
| ORACLE-015 | NONE | A |
| ORACLE-016 | NONE | A |
| ORACLE-017 | NONE | A |
| ORACLE-018 | NONE | A |
| ORACLE-019 | astra/tests/academic_radar/test_snapshots.py, astra/tests/academic_radar/test_watch_checks.py | A |
| ORACLE-020 | astra/tests/academic_radar/test_invalidation.py | A |
| ORACLE-027 | NONE | A |
| ORACLE-028 | NONE | A |
| ORACLE-029 | NONE | A |
| ORACLE-030 | NONE | A |
| ORACLE-031 | NONE | A |
| ORACLE-032 | astra/tests/academic_radar/test_briefs.py | A |
| ORACLE-033 | NONE | A |
| ORACLE-042 | NONE | A |
| ORACLE-045 | NONE | A |

## UNCOVERED — Tier A

The following Tier A release-blocking oracles have no test coverage detected by grep:

- **ORACLE-001** — Case identity is route-specific
- **ORACLE-003** — System suggestion is transparent and deterministic
- **ORACLE-004** — Unknown remains unknown
- **ORACLE-005** — Hard formal blocker dominates actionability
- **ORACLE-006** — MA heads remain independent
- **ORACLE-007** — Funding is relational under the programme case
- **ORACLE-010** — Consequential AI claims require evidence links
- **ORACLE-011** — Inference never mutates into external fact
- **ORACLE-012** — Untrusted source content has no control authority
- **ORACLE-013** — Identity precedes relational inference
- **ORACLE-014** — Source authority governs formal rules
- **ORACLE-015** — Repeated sources do not fake corroboration
- **ORACLE-016** — Contradiction remains visible
- **ORACLE-017** — Deadline precision is not invented
- **ORACLE-018** — Official local deadline survives timezone conversion
- **ORACLE-027** — Supervisor track distinguishes authored vs supervised work
- **ORACLE-028** — No causal acceptance claim
- **ORACLE-029** — Funding viability uses coverage arithmetic
- **ORACLE-030** — Existing MA is an explicit gate/question
- **ORACLE-031** — English hard constraint is actual completion language
- **ORACLE-033** — No autonomous outreach/submission
- **ORACLE-042** — User-created notes/application state survive recrawl
- **ORACLE-045** — Research/model outage is non-destructive

## Summary

**Total Tier A Oracles:** 29  
**With Test Coverage:** 6  
**Coverage Rate:** 20.7% (6/29)  
**Uncovered (Critical Gaps):** 23

**Canary Test Status:** PASS (8/8 harness canaries)
