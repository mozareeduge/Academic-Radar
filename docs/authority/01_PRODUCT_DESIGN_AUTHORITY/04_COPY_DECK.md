# 04 — COPY DECK

**snapshot:** `RADAR-PDA-2026-09-17-r2`  
**Language:** English  
**Principle:** copy states what happened, what remains known/preserved, and the next viable action. It does not claim verification, persistence, eligibility, funding, or success that has not occurred.

## Discovery / runs

### COPY-001 — Discovery CTA
**Surface:** Radar / PhD / MA  
**Text:** `Discover new opportunities`

### COPY-002 — Stored search label
**Text:** `Search saved cases`

### COPY-003 — Run starting
**Text:** `Starting discovery…`

### COPY-004 — Run active
**Template:** `Checking {completed} of {total} sources…`

### COPY-005 — Run complete
**Template:** `Discovery finished. {new_count} new, {changed_count} changed, {failed_count} sources need attention.`

### COPY-006 — No findings
**Template:** `No new records were found for this scope. This does not mean no opportunities exist. Review the source coverage or broaden the search.`

### COPY-007 — Partial run
**Template:** `Discovery finished with partial coverage. Results from successful sources were kept; {failed_count} source(s) could not be checked.`

### COPY-008 — Cancelled run
**Text:** `Discovery stopped. Results already collected were kept.`

### COPY-009 — Retry
**Text:** `Retry failed sources`

## Research / evidence

### COPY-010 — Research CTA
**Text:** `Research this case`

### COPY-011 — Research active
**Text:** `Reconstructing evidence…`

### COPY-012 — Evidence-ready
**Text:** `Research complete. Review the evidence before deciding.`

### COPY-013 — Unsupported model output
**Text:** `This research output could not be linked to sufficient evidence, so it was not added to the assessment.`

### COPY-014 — Identity ambiguity
**Text:** `Identity unresolved`

**Detail:** `More than one person may match this record. Resolve the identity before using publication or supervision history.`

### COPY-015 — Unknown
**Text:** `Unknown`

**Tooltip/detail:** `The available evidence does not establish this yet.`

### COPY-016 — Stale critical fact
**Text:** `Needs recheck`

**Detail:** `This fact may have changed since it was last verified.`

### COPY-017 — Source unavailable
**Template:** `Source unavailable on recheck. Last captured {date}.`

### COPY-018 — Contradiction
**Text:** `Sources disagree`

**Detail:** `Two current records support different conclusions. Review both before relying on this fact.`

### COPY-019 — Inference marker
**Text:** `Inference`

**Detail:** `Interpretation derived from the evidence; not an external fact.`

### COPY-020 — User-reviewed inference
**Text:** `Inference · reviewed by you`

## Disposition

### COPY-021 — System suggestion
**Template:** `System suggests: {disposition}`

### COPY-022 — User disposition
**Text:** `Your decision`

Options:
`Undecided` · `Strong` · `Watch` · `Act` · `Rejected`

### COPY-023 — Suggestion disagreement
**Template:** `You set {user_disposition}. The system currently suggests {system_disposition} because {reason}.`

No action is taken automatically.

## Formal gates

### COPY-024 — Formal blocker
**Text:** `Formal blocker`

**Template detail:** `{requirement} is not met according to {source}.`

### COPY-025 — Eligibility supported
**Text:** `Meets the stated requirement`

Do not use `Eligible` alone when only a subset of requirements has been checked.

### COPY-026 — Requirement ambiguous
**Text:** `Requirement needs clarification`

**Action:** `Open the official wording`

### COPY-027 — Second MA rule
Labels:
- `Second Master's rule: permitted`
- `Second Master's rule: not permitted`
- `Second Master's rule: not established`

## MA / funding

### COPY-028 — MA headings
`Admission viability`  
`Funding viability`  
`Strategic value`

### COPY-029 — Funding gap
**Template:** `Known funding gap: {amount} per {period}`

### COPY-030 — Cost uncertainty
**Template:** `{count} cost item(s) are still unknown, so the funding result is incomplete.`

### COPY-031 — Partial scholarship caution
**Text:** `Scholarship available; full financial viability is not yet established.`

### COPY-032 — Strategic redundancy
**Text:** `The programme overlaps substantially with your existing MA. A clear capability gain has not yet been established.`

## PhD / supervisor

### COPY-033 — No supervision precedent
**Text:** `Relevant research found; comparable supervision precedent not established.`

### COPY-034 — Track classification
Labels:
`Track core` · `Track permitted` · `Track adjacent` · `Novel but plausible` · `Unsupported`

### COPY-035 — Causal caution
**Text:** `This is a demonstrated precedent, not evidence of why the earlier applicant was accepted.`

### COPY-036 — Availability unknown
**Text:** `Current supervision availability is not established.`

## Watch / changes

### COPY-037 — Watched page changed
**Template:** `{source_name} changed since {previous_date}. {impacted_count} case item(s) may need review.`

### COPY-038 — No material change
**Template:** `Checked {date}. No material change detected.`

### COPY-039 — Watch error
**Text:** `This source could not be checked.`

Actions: `Retry` · `Open source` · `Pause watch`

## Deadline / action

### COPY-040 — Deadline
**Template:** `{days} days until the stated deadline`

### COPY-041 — Deadline source caution
**Template:** `Deadline last checked {date}. Recheck before applying.`

### COPY-042 — Closed
**Text:** `Closed`

**Detail:** `This opportunity is no longer open according to the current source.`

## Application Brief

### COPY-043 — Generate brief
**Text:** `Prepare evidence brief`

### COPY-044 — Brief freshness block
**Text:** `Recheck critical facts before freezing this brief.`

### COPY-045 — Brief superseded
**Text:** `This brief is older than the current case evidence.`

**Action:** `Generate updated brief`

### COPY-046 — Prohibited-claims heading
**Text:** `Claims to avoid`

### COPY-047 — Unknowns heading
**Text:** `Questions still open`

## Empty states

### COPY-048 — No cases
**Text:** `No cases here yet.`

**Contextual action:** `Discover new opportunities`

### COPY-049 — No watched items
**Text:** `Nothing is being watched yet. Add a high-value supervisor, project, programme, or funding page to monitor changes.`

### COPY-050 — No evidence
**Text:** `No evidence has been captured for this claim yet.`

## Archive

### COPY-051 — Archive
**Text:** `Archive case`

**Confirmation:** `Archive this case? Its evidence, notes, and history will be preserved.`

### COPY-052 — Restore
**Text:** `Restore case`

## Errors

### COPY-053 — Generic known-scope fetch failure
**Template:** `Could not check {source_name}. Your existing evidence and decisions were preserved.`

### COPY-054 — Model unavailable
**Text:** `Research model unavailable. Collected source evidence was preserved; no assessment was changed.`

### COPY-055 — Save failure
**Text:** `Your change was not saved. Nothing else was modified.`

## Accessibility announcements

### COPY-056 — Research completion announcement
**Template:** `Research complete for {case_title}. Review is ready.`

### COPY-057 — Research failure announcement
**Template:** `Research could not finish for {case_title}. Existing evidence was preserved.`

## Prohibited ambiguous copy

Do not use these without qualification:
- `Best match`
- `High chance`
- `Eligible` when not all hard gates were checked
- `Fully funded` without funding arithmetic/evidence
- `Verified` for model inference
- `Saved` before persistence succeeds
- `Applied` before user records submission
- `Supervisor accepts students` unless current source supports it
- `Search found nothing` as a global conclusion
- `AI says`


## Research protocol / source authority / time

### COPY-058 — Mandatory research class not searched
**Template:** `Research incomplete: {evidence_class} has not been searched yet.`

### COPY-059 — Searched but no public evidence found
**Template:** `Searched for {evidence_class}; no public evidence was found in the checked sources.`

### COPY-060 — Lower-authority conflict
**Text:** `A secondary source conflicts with the current official source.`

### COPY-061 — Repeated-source caution
**Text:** `These records repeat the same upstream statement and are not independent corroboration.`

### COPY-062 — Date-only deadline
**Template:** `{date} · time not stated`

### COPY-063 — Timezone unknown
**Template:** `{date_time} · timezone not stated`

### COPY-064 — Untrusted-source handling
Not normally user-facing. Operator/research log:
`Source text contained control-like instructions. They were treated as source data and not executed.`

### COPY-065 — Funding alternatives
**Template:** `{count} funding route(s) are linked to this programme.`

### COPY-066 — Coverage label
**Text:** `Research coverage`

States:
`Complete for current protocol` · `Incomplete` · `Needs recheck`
