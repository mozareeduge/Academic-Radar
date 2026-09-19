# TRACEABILITY MATRIX

This is a compact navigation matrix. The detailed semantics remain in the three authority layers.

| Product consequence | SCN | Main QA oracle(s) | Primary implementation task(s) | Release gate |
|---|---|---|---|---|
| Route-specific case identity | SCN-016, SCN-046 | ORACLE-001, 006, 007 | TASK-P02, P10, P15, P17 | TARGETED, FULL |
| Discovery + provenance | SCN-001..008 | ORACLE-021..026 | TASK-P04 | TARGETED, ADJACENT |
| Evidence-bound AI | SCN-009, 010, 013, 014 | ORACLE-010, 011, 045 | TASK-P07, P08 | TARGETED, SECURITY, FULL |
| Prompt-injection boundary | SCN-039 | ORACLE-012, 033 | TASK-P09 | SECURITY |
| Identity resolution | SCN-003, 048 | ORACLE-013 | TASK-P05 | TARGETED, SECURITY |
| Source authority/conflicts | SCN-011, 041, 042 | ORACLE-014..016 | TASK-P06, P10 | TARGETED |
| Research protocol completeness | SCN-040 | ORACLE-008, 009 | TASK-P07, P08 | TARGETED, FULL |
| Supervisor track epistemics | SCN-017..020 | ORACLE-027, 028 | TASK-P05, P08, P10, P16 | TARGETED |
| Formal PhD gates | SCN-021..024 | ORACLE-004, 005, 017, 018 | TASK-P10, P11, P16 | TARGETED |
| MA independent heads | SCN-025..030 | ORACLE-005..007, 029..031 | TASK-P10, P17 | TARGETED, FULL |
| Funding arithmetic | SCN-027, 028, 045, 046 | ORACLE-007, 029 | TASK-P10, P17 | TARGETED |
| Deadline precision | SCN-043, 044 | ORACLE-017, 018 | TASK-P11 | TARGETED |
| Snapshot history | SCN-008, 015, 031..034 | ORACLE-019, 020 | TASK-P06, P12 | TARGETED |
| Targeted invalidation | SCN-034, 045 | ORACLE-020 | TASK-P12 | TARGETED, FULL |
| User disposition immutability | SCN-035, 047 | ORACLE-002, 003, 042 | TASK-P10, P15 | TARGETED, FULL |
| Application brief provenance | SCN-036, 037 | ORACLE-032 | TASK-P19 | TARGETED |
| No autonomous outreach | SCN-039 + V1 non-goal | ORACLE-033 | TASK-P09, P19 | SECURITY |
| Mobile/keyboard/a11y | SCN-X-001..005 | ORACLE-035..041 | TASK-P20 | ACCESSIBILITY, RESPONSIVE |
| Archive/restore/export persistence | SCN-038 | ORACLE-042..044 | TASK-P02, P15, P21 | ADJACENT, FULL |
| Clean local release candidate | all critical | all Tier-A | TASK-P22 | MIGRATION, BUILD, CI, RC-SMOKE |

## Required end-to-end chain

Critical semantics must be traceable as:

`SCN-* → ORACLE-* → QA-P* → TASK-P* → GATE-*`

The execution agent may add narrower tests/tasks, but may not remove or weaken this chain.
