# Workflow language pass

Status: complete

## Coverage

Reviewed all 26 workflow Markdown files at base `77b5668f2003bea60127d87e8785469286abafb3`.

Changed (23): `.ai/workflows/{add-phase,add-todo,check-todos,clean-planning,complete-milestone,discuss-phase,edit-phase,execute-phase,insert-phase,milestone-summary,new-milestone,onboard,plan-phase,progress,quick,remove-phase,ship,update-workflows,verify-work}.md`; `.ai/workflows/discuss-phase/modes/{all,default,text}.md`; `.ai/workflows/discuss-phase/templates/context.md`.

Reviewed unchanged (3): `.ai/workflows/next.md`, `.ai/workflows/discuss-phase/modes/auto.md`, `.ai/workflows/discuss-phase/templates/discussion-log.md`.

## Changes

Removed metaphorical, motivational and explanatory prose; replaced hedging and dated example claims with direct instructions; clarified warning and stop branches. Preserved workflow behavior, optional branches, routing, authority, runtime commands, schemas, field names, status values, artifact names and required rationale fields.

## Checks

- `git diff --check`: passed.
- Reviewed local Markdown links in changed workflows: no broken links found.
- Tests, configured checks and workflow execution: not run, as assigned.

## Deviations

None.

## Remaining

None.
