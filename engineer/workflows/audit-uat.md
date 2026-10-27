Read and execute `engineer/workflows/_runtime-launcher.snippet.sh` before runtime calls. Resolve the configured response language with `engineer_run query config-get response_language --raw`; when an init result already supplies `response_language`, use that value. Apply this language to all user-facing prose: narration between tool calls, status updates, progress notes, questions, explanations and reported findings. Preserve code, paths, command names, identifiers, machine-readable keys and required protocol markers verbatim. Do not translate source code or a consumer-required sentinel.

<purpose>
Cross-phase audit of all UAT and verification files. Finds every outstanding item (pending, skipped, blocked, human_needed), optionally verifies against the codebase to detect stale docs, and produces a prioritized human test plan.
</purpose>

<process>

<step name="initialize">
Run the CLI audit:

Read and execute engineer/workflows/_runtime-launcher.snippet.sh; run the read-only source:

```bash
AUDIT=$(engineer_run query audit-uat)
```

Parse the actual `{items, count}` output, not an invented results/summary envelope. Each item retains stable id, status, file, phase or quick identity, name/body/reason as supplied. Independently inventory active and archived UAT/VERIFICATION paths under `.planning/phases/`, `.planning/quick/` and `.planning/milestones/` using read-only Glob/Read. The runtime's active-session packet alone does not prove archived coverage. Count every discovered source, parse its Tests/action/checklist/Human acceptance sections, retain unparsed blocks, and merge by source path plus stable item ID. Do not equate absence from runtime output with acceptance.

Build the report-local `results` and `summary` views from that cited inventory: total_items, total_files, phase_count and parse_gap_files. They are authored evidence, not runtime stdout fields. Cite unsupported/malformed files and exact blocks so they remain visible even alongside valid pending items.

If `summary.total_items` is 0 AND `summary.parse_gap_files` is 0:
```
## All Clear

No outstanding UAT or verification items found across all phases.
No outstanding items were found in the completely examined scope. This audit does not attest that unexecuted tests passed or that a diagnosis/fix plan grants human acceptance.
```
Stop here.

If `summary.total_items` is 0 but `summary.parse_gap_files` is greater than 0, this is NOT all-clear — one or more files have test blocks that could not be parsed and may be hiding outstanding work. Continue to the `categorize` and `present` steps below; `present` renders the Unparsed section from these `parse_gap: true` entries even though `items` is empty for a mixed project.
</step>

<step name="categorize">
Group items by what's actionable NOW vs. what needs prerequisites:

**Testable Now** (no external dependencies):
- `pending` — tests never run
- `human_uat` — human verification items
- `skipped_unresolved` — skipped without clear blocking reason

**Needs Prerequisites:**
- `server_blocked` — needs external server running
- `device_needed` — needs physical device (not simulator)
- `build_needed` — needs release/preview build
- `third_party` — needs external service configuration

For each item in "Testable Now", use Grep/Read to check if the underlying feature still exists in the codebase:
- If the test references a component/function that no longer exists → mark as `stale`
- If the test references code that has been significantly rewritten → mark as `needs_update`
- Otherwise → mark as `active`
</step>

<step name="present">
If `summary.parse_gap_files` is greater than 0, render this section FIRST (before the `## UAT Audit Report` below, or standalone if `total_items` is also 0). Filter `results` for entries with `parse_gap: true`:
```
## Unparsed UAT Files ({parse_gap_files} files)

| Phase | File | Unparsed Blocks |
|-------|------|------------------|
| {phase} | {file_path} | {unparsed_blocks} |
...

These files have `### N.` test blocks with no readable `result:` line. Fix the file's structure, then re-run the audit.
```
This fires for ANY project with `parse_gap_files > 0`, including a mixed project where other phases also have real outstanding `items` — the two sections are not mutually exclusive. An outstanding item does not stop mattering because its phase belongs to an already-archived milestone (a deferred human-UAT scenario or a `skipped` live-stack test is exactly what gets archived still-open), so an archived phase's parse gap is listed in this same table, unfiltered by `archived_milestone`. If `total_items` is 0, stop after this section (there is no `## UAT Audit Report` to present). Otherwise continue below.

Present the audit report:

```
## UAT Audit Report

**{total_items} outstanding items across {total_files} files in {phase_count} phases**

### Testable Now ({count})

| # | Phase | Test | Description | Status |
|---|-------|------|-------------|--------|
| 1 | {phase} | {test_name} | {expected} | {active/stale/needs_update} |
...

### Needs Prerequisites ({count})

| # | Phase | Test | Blocked By | Description |
|---|-------|------|------------|-------------|
| 1 | {phase} | {test_name} | {category} | {expected} |
...

### Stale candidates (require scope reconciliation) ({count})

| # | Phase | Test | Why Stale |
|---|-------|------|-----------|
| 1 | {phase} | {test_name} | {reason} |
...

---

## Open tracking and decisions

For each unresolved item, report its canonical issue URL (or Pending reconciliation), actual blocker, owner, next action and evidence. Source removal or rewriting is evidence for scope reconciliation, never permission to close an acceptance item. A resolved_by PLAN/SUMMARY must be real, committed, executed, identity-matching and carry specific gap-resolution evidence plus resolved_at. Preserve the historical failed result and any required human retest; diagnosis alone never resolves it. Final human acceptance separately requires actual ACCEPTED status, accepted_by, accepted_at and decision.

This command is read-only: do not edit UAT, mark stale items resolved, publish/close issues or execute tests. Route concrete bounded defects to the authorized correction caller; return human obligations as the runnable script below.
```
</step>

<step name="test_plan">
Read the complete engineer/templates/UAT.md and the full UAT variant of engineer/templates/issue.md. Render the human script for "Testable Now" + "active" items using their actual acceptance contract. Preserve stable action IDs, setup/fixtures, exact action, expected observation, evidence to retain, reset/cleanup, accepted/failed/blocked reply and final Human acceptance fields. Group compatible actions together, but never combine away independent required outcomes. Report prerequisites for blocked actions separately.

The example below supplements the canonical script; it does not replace mandatory template fields:

Group by what can be tested together (same screen, same feature, same prerequisite):

```
## Human UAT Test Plan

### Group 1: {category — e.g., "Billing Flow"}
Prerequisites: {what needs to be running/configured}

1. **{Test name}** (Phase {N})
   - Navigate to: {where}
   - Do: {action}
   - Expected: {expected behavior}

2. **{Test name}** (Phase {N})
   ...

### Group 2: {category}
...
```
</step>

</process>
