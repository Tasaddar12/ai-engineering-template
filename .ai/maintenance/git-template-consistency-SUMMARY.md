---
maintenance: git-template-consistency
status: complete
acceptance: []
documentation:
  - .ai/templates/issue.md
  - .ai/templates/pull-request.md
  - .ai/references/git-workflow.md
  - .ai/workflows/ship.md
commits:
  - cd94c3564cd4fffce534438f0b5e89f899864fbc
plan_head_before: 582f818fe15c92291ca7dbbe2c81f955491f9293
---

# Git template consistency

Status: implementation complete.

## Scope and identity

Standalone authorized template maintenance; no adopting-project identity or phase records changed.

- Worker root: D:/Codex Projects/ai-engineering-template/.worktrees/git-template-consistency-093504244.
- Worker branch: agent-git-template-consistency.
- Worker base: 582f818fe15c92291ca7dbbe2c81f955491f9293.
- Original body reference: b770c90e6cad1307385bc225d902523c3613cbd0.
- Tasks: 2/2 implemented; each slice includes this owned summary.
- Context usage: unavailable.

## Changes

- Task 1: .ai/templates/issue.md and .ai/templates/pull-request.md now have purpose,
  producer/consumer and separate-public-file destination guidance. Each original
  body remains inside one markdown fence under File Template. Short filling
  instructions, concrete good/bad examples and completion/handoff guidance remain
  outside it. Guidance covers safe evidence, observable acceptance, duplicate
  review, in-scope defects, truthful tracking drafts and conditional Stack fields.
- Task 2: .ai/references/git-workflow.md explicitly directs issue and PR authors
  to read the source and copy only its File Template block into a body file.
  .ai/workflows/ship.md selects that same block in generate_pr_body.
- This file: .ai/maintenance/git-template-consistency-SUMMARY.md records both slices.

No native forms or merge-request template added. Catalogs, runtime code, capture
procedures, check scripts and planning records are unchanged. Original issue and
PR headings, verification/stack fields and safety comments remain compatible.
Publication authority, evidence rules and operational sequences are unchanged.

## Checks

Author inspections, separate from coordinator final verification:

- Task 1 inline standard-library Python extraction found exactly one markdown body
  fence per source and compared its bytes with git show b770c90:<path>; both match
  except terminal newline. Both authored Git workflow links exist.
- Scoped task 1 git diff confirms original headings, fields and comments are
  unchanged and all examples/guidance remain outside the fence. git diff --check
  passed. Before staging, git diff --cached was empty and git status named only
  the three owned slice paths.
- Task 2 scoped diff confirms all three direct references select File Template;
  no existing command arguments, policy, workflow steps or body fields changed.
  The links at these sites are retained existing links.
- Source inspection: todo_issues.reviewed_body requires a separate non-empty public
  file, rejects the private TODO path and existing marker, then appends the marker;
  it does not validate headings. delivery.open_pr forwards the composed body file.
  Capture routes to add-todo/check-todos and their reviewed publication procedure.
  No automatic source copying was introduced.

At commit time: test scripts not run by worker. Coordinator records checks for
the integrated revision in draft PR #69. Author inspection is not runtime consumer
execution, independent review or final verification.

## Commits and handoff

- Task 1: cd94c3564cd4fffce534438f0b5e89f899864fbc.
- Task 2 and final summary: the commit containing this completed summary; its exact
  hash is returned in the worker completion response and available in git log.
- Coordinator owns integration, push, PR evidence and final verification.
  No worker push, merge, cleanup, test scripts or benchmarks.

## Deviations

None. The supplied standalone plan and assignment govern the summary location
and defer test scripts, independent review and publication to the coordinator.

## Remaining

At this worker handoff, coordinator evidence is outstanding for the integrated
revision: extraction/consumer execution, repository unit suite, four hook suites,
independent review and required remote CI. These checks determine final acceptance
and readiness; this summary records implementation and author inspection only.
Keep draft PR #69 unmerged as explicitly requested. No shared planning updates,
project requirement IDs or new decisions are proposed.

## Self-Check: PASSED

All five owned files exist. Task 1 commit exists and contains only its two templates
and summary; no deletion occurred. The final slice owns only the two direct consumers
and this summary. Both source bodies preserve the original copy contract.
