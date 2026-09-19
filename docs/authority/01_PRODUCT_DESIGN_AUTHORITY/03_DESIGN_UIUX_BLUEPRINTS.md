# 03 — DESIGN / UIUX BLUEPRINTS

**snapshot:** `RADAR-PDA-2026-09-17-r2`  
**Design goal:** an evidence-first research desk: fast to scan, deep enough to audit, and explicit about what is known, inferred, stale, blocked, or decided by the user.

The design must avoid two failure modes:
1. generic “dashboard card soup” that hides research structure;
2. academic dossier walls of prose that make comparison/action slow.

## DS-FOUNDATION — Information architecture

Primary navigation:

1. **Radar** — attention inbox
2. **PhD** — all doctoral cases, route-filtered
3. **MA + Funding**
4. **Supervisors**
5. **Watch**
6. **Profile & Routes**

Secondary/utility:
- research run/source health;
- global search;
- settings/export.

### SURF-001 Radar anatomy

Desktop:
```text
Page title + last cycle status                        [Run discovery]
---------------------------------------------------------------
Attention filters: New | Changed | Needs review | Urgent | Failed
---------------------------------------------------------------
Urgent / Act-worthy
  compact case rows
Changed
  source diff rows
Needs review
  completed-research rows
New
  discovery rows
System health (collapsed unless degraded)
```

No KPI vanity tiles. Counts are navigation aids only.

Each row includes:
- type icon/label;
- title/person/programme;
- institution + country;
- MozareRoute if case exists;
- application route;
- research state;
- user disposition;
- primary blocker/unknown;
- deadline/urgency where relevant;
- evidence freshness;
- one primary action.

### SURF-005 Case Dossier anatomy

Desktop wide ≥1280:
```text
[case header / route / disposition / primary action]
[hard-gate strip: Pass | Fail | Unknown | Stale]
---------------------------------------------------------------
MAIN 8 cols                                  ASIDE 4 cols
Assessment summary                           Next action
Route rationale                              Deadline/funding
Track / precedents                           Evidence health
Candidate execution evidence                 Notes
Funding/application route                    Application stage
Unknowns & contradictions
Source ledger
---------------------------------------------------------------
Evidence Inspector opens as 380–440px right drawer,
reducing main width rather than overlaying critical context when space permits.
```

Desktop compact/tablet:
- one main column;
- assessment summary and next action first;
- evidence inspector overlays as drawer;
- source ledger collapsible but never omitted.

Mobile:
- separate dossier page;
- sticky top: back + compact case identity;
- section outline under header;
- sticky bottom action bar only for contextually valid primary action (`Research`, `Recheck`, `Prepare brief`, `Set disposition`);
- disposition available from a full-width sheet;
- evidence inspector full-screen with explicit Close and source link.

## DS-TOKENS

Use semantic tokens rather than decorative color dependencies:

- `surface/base`, `surface/raised`, `surface/subtle`
- `text/primary`, `text/muted`, `text/inverse`
- `border/default`, `border/strong`
- `action/primary`, `action/secondary`
- `state/pass`, `state/fail`, `state/unknown`, `state/stale`, `state/inference`, `state/user`
- `focus/ring`

Every state token must be paired with text/icon/shape.

Spacing scale:
`4, 8, 12, 16, 24, 32, 48` px equivalent.

Content measures:
- prose/evidence summary: 65–78 characters;
- dossier main readable column: 720–860px equivalent;
- evidence drawer: 380–440px;
- left nav if persistent: 216–240px.

## DS-TYPOGRAPHY

- UI: legible sans-serif system/available app font.
- Monospace only for IDs, structured data, URLs, hashes, technical source traces.
- Body research prose: 15–16px desktop, 16px mobile.
- Metadata: not below 12px; default 13px.
- Line height: ~1.45–1.6 for prose.
- Headings communicate hierarchy rather than decorative scale.

No all-caps body labels. Status chips may use short title-case labels.

## DS-COLOR / STATE CUES

Required semantic presentation:

| State | Text label | Non-color cue |
|---|---|---|
| PASS | Pass | check icon |
| FAIL | Blocked/Fail | stop/x icon + strong border |
| UNKNOWN | Unknown | ? icon + dashed/neutral border |
| STALE | Needs recheck | clock/refresh icon |
| INFERENCE | Inference | sparkle/analysis icon |
| USER_DECISION | Your decision | person/bookmark icon |

Do not use green/red alone.

## DS-GRID / DENSITY

Desktop list surfaces use structured rows, not full marketing cards.

Case row minimum:
- 56px compact; 72px when blocker/next action line exists.
- title allowed max 2 lines.
- metadata wraps before controls.
- primary action has fixed minimum target; never stretched across entire row unless mobile.

Tables are used only where column comparison is the task:
- supervisor comparison;
- funding arithmetic;
- explicit eligibility matrix.

Long prose stays outside tables.

## DS-COMPONENT-ANATOMY

### C-01 CaseRow
Slots:
1. type + research-state marker;
2. title;
3. institution/country;
4. route/application-route;
5. critical gate/blocker;
6. deadline/freshness;
7. user disposition;
8. primary action + overflow.

States:
`new`, `researching`, `ready`, `stale`, `failed`, `archived`.

### C-02 AssessmentHead
Used for:
- Admission Viability;
- Funding Viability;
- Strategic Value;
- supervisor dimension summary.

Contains:
- assessment label;
- calibrated state/value;
- one-line reason;
- evidence count/coverage;
- unknown count;
- expand action.

It never contains unsupported probability language.

### C-03 GateStrip
Horizontal on desktop; vertical/key-value on mobile.

Each gate:
- name;
- PASS/FAIL/UNKNOWN/STALE;
- one-line evidence basis;
- open evidence.

Hard FAIL receives prominence but not destructive alarm styling if no user action can change it.

### C-04 ClaimRow
Contains:
- statement;
- claim type;
- epistemic status;
- source count;
- freshness;
- reviewed marker;
- actions: inspect evidence, correct, accept/reject inference.

### C-05 EvidenceChip / SourceRef
Shows authority/source class + date. Activating opens Evidence Inspector.
Never show opaque `[1]` only; compact citation may be `[Official · 12 Sep 2026]`.

### C-06 EvidenceInspector
Sections:
- claim using this evidence;
- source title/authority;
- captured/extracted text;
- retrieval/effective dates;
- snapshot/change history;
- original source;
- related claims.

### C-07 PrecedentRow
For supervised projects:
- project/student;
- supervisor role;
- object/corpus;
- method/theory/output summary;
- funding/project linkage;
- classification: core/permitted/adjacent/novel;
- evidence strength.

### C-08 FundingPackage
Represents an `OBJ-015 FundingAssessment`, not a separate application case.

- award;
- tuition/waiver;
- duration;
- eligibility gates;
- reliable known costs;
- funding gap/surplus;
- unknown costs;
- source date.

### C-09 SuggestedDisposition
Displays:
`System suggests: Watch`
with reasons and uncertainty.
Adjacent user control:
`Your decision: Strong/Watch/Act/Rejected/Undecided`.

Never visually merge the two.

### C-10 DiffRow
- source;
- previous check/current check;
- material change;
- impacted claims/cases;
- actions `Review`, `Rerun impacted research`, `Acknowledge`.

### C-11 RunProgress
Preserve useful CIK behavior:
- status;
- source completed/total;
- source-by-source counts/errors;
- records arriving;
- cancel;
- partial result semantics.

### C-12 ApplicationBriefPreview
Structured, exportable:
- case identity;
- why this route here;
- candidate evidence;
- precedents;
- formal/funding facts;
- unknowns/questions;
- prohibited claims;
- source ledger.

## DS-RESPONSIVE-TRANSFORMATIONS

### Desktop wide ≥1280
- persistent nav;
- dossier main + aside;
- optional evidence drawer;
- comparison table allowed.

### Desktop compact/tablet 768–1279
- nav collapses to rail/drawer;
- dossier single content column with summary cards in 2-column grid when width allows;
- evidence drawer overlays;
- comparison table can horizontally scroll **inside its own bounded container only** with first column sticky.

### Mobile <768
- list rows become stacked but remain compact;
- filters open sheet;
- dossier full-screen;
- tables become cards/key-value groups when semantic comparison remains understandable;
- primary action may be sticky bottom;
- external links and source buttons remain ≥44px touch target;
- no hover-only information.

### Narrow 320
- no page-level horizontal overflow;
- IDs/URLs break safely;
- disposition controls use sheet/radio list;
- 2-line titles, then accessible full title in detail;
- chips wrap.

### Landscape mobile
- bottom sheets max-height with internal scroll;
- sticky action never covers focused field;
- on-screen keyboard does not hide save/confirm.

### Large text / 200% zoom
- multi-column dossier collapses;
- fixed-height content containers prohibited except explicitly scroll-owned source lists;
- labels may wrap;
- no status conveyed by truncation.

## DS-FOCUS / ACCESSIBILITY

Global:
- skip link to main content;
- visible focus ring;
- logical heading hierarchy;
- landmarks for nav/main/aside where meaningful;
- no clickable `div`;
- target ≥44×44 CSS px for primary touch actions.

Dialogs/sheets:
- focus first meaningful element;
- trap focus;
- Escape closes unless irreversible operation is currently committing;
- closing restores focus to trigger.

Evidence drawer:
- title announced;
- opening does not change case state;
- closing restores focus to ClaimRow/SourceRef.

Async:
- start of long research is not repeatedly announced;
- completion/failure uses polite live announcement;
- cancelling communicates “finishing current source” when applicable.

Status:
- icon is decorative if label exists;
- `aria-current` for active nav;
- `aria-expanded` for expandable evidence;
- loading controls expose busy state.

Reduced motion:
- no meaning depends on animation;
- drawers/dialogs may transition instantly;
- progress is textual as well as animated.

## DS-MOTION

Motion is functional:
- 120–200ms standard UI reveal where motion is enabled;
- no celebratory success animations;
- changed/stale state uses static cue, not pulsing;
- research progress may animate but has textual stage/count.

## DS-HIERARCHY

### Dossier priority order
1. identity + application route;
2. blocker / deadline / required next action;
3. core assessments;
4. rationale;
5. precedents and candidate evidence;
6. unknowns/contradictions;
7. source detail.

The interface must not make source metadata visually dominant until the user opens it; provenance is always reachable, not always visually loud.

## FILTER / SEARCH DESIGN

Filters are explicit query state:
- country;
- application route/type;
- MozareRoute;
- research state;
- user disposition;
- formal blocker;
- deadline window;
- evidence freshness.

Changing filter resets pagination but never changes records.

The product must clearly distinguish:
- **Search within stored cases** (instant/local)
- **Discover/research the web** (background run)

Buttons must not both say generic “Search”.

## DESIGN ACCEPTANCE — core

1. In ≤10 seconds, a case row reveals what it is, why it matters, biggest blocker/unknown, deadline/freshness, and next action.
2. In ≤30 seconds, a dossier reveals whether evidence is sufficient and where uncertainty lives.
3. Any assessment can be traced to evidence in ≤2 interactions.
4. User decision and system suggestion are never visually confusable.
5. A hard formal blocker is visible without scrolling on the dossier.
6. MA admission/funding/strategic states can visibly disagree.
7. Mobile preserves review/decision/source access.
8. No page-level horizontal overflow at 320px.


## DS-SOURCE-AUTHORITY

Every evidence reference can expose:
- source authority label;
- original/canonical origin when known;
- retrieval/effective date;
- independence grouping;
- current/stale state.

The normal compact UI shows only the authority + date; detailed origin/independence appears in Evidence Inspector.

## DS-PROTOCOL-COVERAGE

Case Dossier includes a compact `Research coverage` control:
- mandatory evidence classes;
- `searched + found`;
- `searched + none found`;
- `not searched`;
- `blocked/unavailable`.

This is separate from “number of sources.” Ten URLs cannot visually imply completeness if a mandatory class was never investigated.

## DS-TIME

Deadline components:
- primary: original institutional representation (`15 January 2027`, `15 Jan 2027 17:00 CET`);
- secondary: user's local equivalent only when unambiguous;
- status: `time not stated` / `timezone not stated` when missing.

Urgency chips never replace the source deadline text.
