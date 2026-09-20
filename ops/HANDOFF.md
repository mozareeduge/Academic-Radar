# HANDOFF — Academic Radar (state at commit 0c30eee, 2026-09-20)

> **UPDATE 2026-09-20 ~15:10 (Hermes session):** CI verdict for 0c30eee = SUCCESS (all 4 jobs). Item 4 (live checks) done for both scholarly APIs: OpenAlex OK as-written; OpenAIRE Graph v3 was BROKEN live (guessed params 400/405) and FIXED+verified in commit `7359179` — see that commit message for the full contract (search/authorId/fundingShortName/research-products/results). Remaining open: P03b (private folder — maintainer only), stronger-model review of Haiku tests (item 3), real LLM provider check (item 4, provider not configured on this machine), browser layout pass (item 5).
>
> **UPDATE 2026-09-20 ~16:30 (Hermes session):** ChatGPT UI drop-in v1 integrated at `f2f6ffe` (28 radar files + contract-corrected types; BriefTab freeze guards restored after revision had inverted that oracle; their jest/eslint config reconstructions and shadow types.ts excluded). Gates: tsc 0 / jest 273 / eslint 0 / build 0. next@16.3.5 kept.

The Haiku runner is STOPPED and nothing is scheduled to restart it. Whoever continues owns the working tree.

## Landed (all on origin/main, repo is PRIVATE)
- Donor fork of mimdot/CIK@8c300d28 (MIT) + full Radar backend: schema (32 `radar_` tables, migrations r001-r005), security boundary, discovery, OpenAlex/OpenAIRE clients (fixture-tested), identity, evidence, protocols, research graph, gates/dimensions/funding/deadlines/suggestions, watch + targeted invalidation, API, web UI, brief, accessibility tests.
- Research results now persist for real (P22c) and funding/watch/brief are real code paths (P22d).
- Independent referee: `scripts/smoke_assertions.py` reads the real SQLite state after `scripts/local_smoke.py`. Run: `.venv\Scripts\python scripts\local_smoke.py` (fresh run + API restart + durable check + DB assertions). Passed at 0c30eee on the maintainer machine.
- 8 mutation canaries pass; QA report `ops/evidence/qa_report.md` lists all Tier-A oracles as tagged (tag-based, NOT proof of quality).

## Not done / not verified
1. CI verdict for 0c30eee (Backend, Dashboard, Docker Compose smoke) was still running when the runner was stopped. Check it first.
2. P03b: real profile seed (from `Apply\_radar_private\...MEMORY_v0.2.md`) is NOT created. Never commit personal data; keep it outside the repo.
3. Independent review of Haiku-written tests by a stronger model was never run (oracle tags may be loose).
4. Live checks never done: OpenAIRE v3 base URL, OpenAlex live calls, any real LLM provider (only the mock provider is used).
5. No browser verification of 320/390/768/1024/1440 px layout or 200% zoom.
6. Docker Desktop is not installed on the maintainer machine; the compose smoke runs only in GitHub Actions.

## Rules that bit us (read before editing)
- `ops/haiku-runner/driver.py` runs `git add -A`, commits and pushes after each slice and REVERTS tracked edits outside a slice's allowed paths. Never run it while another agent edits the same working tree. Commit a436741 (12:44, next bump) was made by another writer during a slice and swept in the runner's in-progress files.
- Do not edit `scripts/local_smoke.py` or `scripts/smoke_assertions.py` to make a run pass; they are the referee.
- Do not add `__init__.py` under `astra/tests/` (it shadows the `academic_radar` package).
- Tool guard: private folder `Apply\_radar_private\` must not be read by executors.
- 8 local stashes (`git stash list`) hold failed/orphan partial attempts; they are not pushed and can be dropped.

## Restart the runner only if you want it (single writer)
`.venv\Scripts\python ops\haiku-runner\driver.py` (state: `ops/haiku-runner/state.json`, log: `driver.log`, status: `STATUS.md`).
