---
tier: contract
authority: agent
title: Retire exact merged work
---
> Contract: follow these steps within the approved scope.

# Retire exact merged work

## Purpose

Clean up delivered work without losing unmerged changes or branch ownership.

## Inputs

The run, exact owned branches/worktrees, hosting observations and cleanup
authority.

## Gates

Use [retirement-ready](../gates/retirement-ready.md) for each target. Ambiguous requests produce a dry-run report.

## Steps

1. Observe each exact worktree/branch and its current owner; never infer safety
   from a stale manifest.
2. Check synchronized target ancestry, clean tracked/untracked state, stopped
   workers and no open request needing the branch.
3. List Safe to remove and Would lose work or cannot prove safety, with exact
   absolute paths and reasons.
4. After authority and PASS, remove only the named worktree without force, then
   use git branch -d for its local branch.
5. If squash/rebase ancestry or branch advancement prevents proof, retain the
   branch and state the next bounded check. Never replace -d with -D.
6. Preserve the run manifest, journal actual cleanup and report anything
   retained.

## Output and handoff

Exact cleanup outcomes and remaining work; a push-only draft remains intact.

## Stop conditions

Do not delete from an unsafe/uncertain list or treat --all as permission to
discard work.
