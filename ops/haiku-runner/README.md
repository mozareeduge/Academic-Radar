# Haiku runner — how to start, stop, and read it

Start / resume (safe to run any time; it continues from `state.json`):

    .venv\Scripts\python ops\haiku-runner\driver.py

Detached (survives closing the terminal; log in `driver.log`):

    powershell -Command "Start-Process -WindowStyle Hidden -FilePath .venv\Scripts\python.exe -ArgumentList 'ops\haiku-runner\driver.py' -WorkingDirectory (Get-Location)"

Read progress: `Plans.md` (checklist) and `ops/haiku-runner/STATUS.md` (blocked / deferred items with the one question each needs).

- Haiku 4.5 executes one slice per call (thinking off, turn cap). The driver runs the gates, commits, pushes; Haiku never commits.
- Failure: 2 retries with the gate output attached, then the slice is BLOCKED (work stashed as `failed-<id>-*`) and independent slices continue.
- Usage/rate limit: the driver sleeps 20 min and retries the same attempt, so it rides through the weekly reset.
- Keep the PC awake; a sleeping machine pauses the loop.
- CI: slices with `ci=True` push, then wait for GitHub Actions on that exact SHA; two Haiku fix attempts if red.
- Deferred: `P03b` (real profile seed) needs a stronger model and must stay outside the repo.
- Not verifiable locally (Docker missing): compose smoke runs in GitHub Actions only.
- Reviewer pass (after the limit resets): run harness-review / test-wiring-auditor over `ops/evidence/qa_report.md`.
- Do not edit tracked files while the driver runs; it commits everything in the working tree after each slice.
