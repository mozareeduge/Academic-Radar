# Donor baseline (GATE-BASELINE) — mimdot/CIK@8c300d28 on Windows, Python 3.12.13, Node 24

- Backend: 1093 passed, 6 failed (Windows-only: CRLF line endings in csvout + cp1252 decode in pipeline html). Full log: backend_pytest.txt. `deselect.txt` lists the two test groups excluded from local gates. Linux CI is the authority for them.
- Frontend: 22 suites / 200 tests pass; `npm run lint` clean; `tsc --noEmit` clean.
- Donor HEAD unchanged since spec freeze (8c300d28b9add865cd09b2e5e141f94a6b033c74).
