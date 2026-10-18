# Workflow language pass

Status: final correction pass complete; language review pending.

## Coverage

Reviewed every paragraph in all 26 workflow Markdown files at base `77b5668f2003bea60127d87e8785469286abafb3`. All 26 are included in the language pass: `.ai/workflows/{add-phase,add-todo,check-todos,clean-planning,complete-milestone,discuss-phase,edit-phase,execute-phase,insert-phase,milestone-summary,new-milestone,next,onboard,plan-phase,progress,quick,remove-phase,ship,update-workflows,verify-work}.md`; `.ai/workflows/discuss-phase/modes/{all,auto,default,text}.md`; `.ai/workflows/discuss-phase/templates/{context,discussion-log}.md`.

Reviewed unchanged non-Markdown assets: `.ai/workflows/discuss-phase/templates/checkpoint.json` and `.ai/workflows/_runtime.snippet.sh`.

## Changes

Applied the contributing guide's concise imperative style while preserving workflow steps, conditions, optional paths, routing, authority, commands, schemas, field names, placeholders, status values, artifacts and required rationale/evidence. Restored discuss-phase constraints on technical-risk identification and success metrics, and restored the milestone summary's required before/after and user-benefit content. Replaced the first-pass explanations flagged by review, including incomplete-phase routing, auto-mode pass limits, onboarding, research evidence, wave conflicts, runtime ownership and archive eligibility. Kept user-facing questions, operational conditions, source authority, required rationale fields and supported legacy evidence.

The first independent review found two semantic regressions and incomplete style coverage, including prose in three files initially marked unchanged. The frozen semantic review at `b581594be9d3a532b45ab309a28b5a6022a72947` passed: both required content contracts were restored, with no semantic regressions. The doc review found four remaining style gaps; this pass removed rationale from the onboarding and execution instructions, corrected the phase-planning suggestion, and removed orphaned combination-rule text without changing supported mode behavior.

## Checks

- Manual review of all workflow Markdown and current diff: completed.
- `git diff --check`: passed.
- Local Markdown link review across all 26 workflow Markdown files: passed; no broken local links.
- Tests, configured checks and workflow execution: not run, as assigned.

## Deviations

None.

## Remaining

Independent language review of the final correction pass.
