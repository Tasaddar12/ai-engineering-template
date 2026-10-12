---
maintenance: git-template-consistency
status: blocked
acceptance: []
documentation:
  - .ai/templates/issue.md
  - .ai/templates/pull-request.md
commits: []
plan_head_before: 582f818fe15c92291ca7dbbe2c81f955491f9293
---

# Git template consistency

Status: task 1 implementation complete; task 2 pending.

## Scope and identity

Standalone authorized template maintenance; no adopting-project identity or phase records changed.

- Worker root: D:/Codex Projects/ai-engineering-template/.worktrees/git-template-consistency-093504244.
- Worker branch: agent-git-template-consistency.
- Worker base: 582f818fe15c92291ca7dbbe2c81f955491f9293.
- Original body reference: b770c90e6cad1307385bc225d902523c3613cbd0.
- Context usage: unavailable.

## Changes

Task 1 wraps .ai/templates/issue.md and .ai/templates/pull-request.md with
purpose, producer/consumer and separate-public-file destination guidance. Each
original body remains inside one markdown fence under File Template. Short
instructions, concrete good/bad examples and completion/handoff guidance remain
outside it. Guidance covers safe evidence, observable acceptance, duplicate
review, in-scope defects, truthful drafts and conditional Stack fields.

Changed paths: the two templates and this summary. No native forms or
merge-request template added; no catalog, runtime, checks or planning records changed.

## Checks

Task 1 author inspection: inline standard-library Python extraction found exactly one markdown body fence per source and compared its bytes with git show b770c90:<path>; both match except terminal newline. Both authored Git workflow links exist. Scoped git diff confirms all original headings, fields and comments remain unchanged and all examples/guidance are outside the fence. git diff --cached was empty; git status lists only the three owned task 1 paths.
At commit time: test scripts not run by worker. Coordinator records checks for
the integrated revision in draft PR #69.

## Deviations

None. The supplied standalone plan and assignment govern the summary location
and defer test scripts, independent review and publication to the coordinator.

## Remaining

- Task 2: clarify the two Git workflow references and ship's generate_pr_body opening.
- Coordinator: integrated-revision extraction/consumer checks, repository unit
  suite, four hook suites, independent review and required remote CI.
- Keep PR #69 draft and unmerged; no benchmarks or worker publication.

## Self-Check: PASSED (task 1)

Both owned templates and the maintenance summary exist; body compatibility inspection passed. Task 2 and coordinator verification remain separate obligations.
