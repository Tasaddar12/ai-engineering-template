# Deliver the approved result

## Purpose

A reviewed result has explicit authority for a commit, push or merge.

## Inputs

The reviewed revision, validation evidence, branch identity and delivery limits.

## Gates

Before each delivery action: [delivery-ready](../gates/delivery-ready.md).
Before merge, use [plan-verify](plan-verify.md) evidence for the intended revision;
for a bounded FIX without a plan, use its acceptance/spec/check evidence.
Before cleanup: [retirement-ready](../gates/retirement-ready.md).

## Steps

1. The pr-agent inspects the final diff, affected specs and branch identity in the assigned
   worktree. Confirm the authorized action and destination.
2. Draft the PR body using pull-request.md. Commit with a nonempty descriptive
   message when authorized; include the PLAN or FIX ID.
3. Push only the approved branch and verify its remote tip matches the local head.
4. For push-only delivery, report the branch and stop. Retain the worktree; a PR or
   merge needs its own authority.
5. After an authorized merge, observe the hosting result and synchronize the target.
   Once the worktree-only assignment ends, the orchestrator can use its integration
   checkout for authorized synchronization and exact worktree/local-branch retirement.
6. Confirm no unmerged work is being removed. Journal delivery/cleanup, update STATE,
   and move an accepted, fully delivered plan or FIX to done under its lifecycle.

## Output and handoff

Observed delivery references and a decision summary. Report incomplete cleanup honestly; a push-only draft can remain in review.

## Stop conditions

Never force-push, merge without approval or delete unrelated/advanced branches. Inspect uncertain external outcomes before retrying.
