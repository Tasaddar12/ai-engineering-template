# Worktree recovery policy

What happens when an isolated wave does not go cleanly. Two rules, both
fail-safe.

## The orchestrator owns the lifecycle

`worktree-branch-check` is verify-only. An executor that hits a base or
namespace mismatch prints `FATAL:` and exits **42** instead of repairing itself.

When any executor reports a `FATAL:` or exit 42 — or when its commits never
appear because it halted at the check — mark that plan **blocked**:

- Do **not** merge its branch, and do **not** clean up its worktree. Preserve
  the checkout for inspection.
- Do **not** count the wave as successful.
- Surface the mismatch with recovery guidance to the user.

The orchestrator performs any base correction, for example recreating the
worktree on the expected base. The subagent never does. Never proceed past a
halted executor on the assumption it succeeded.

## A rejected isolated run stays isolated

When an isolated run is *rejected* — the user declines the merge, the
orchestrator surfaces recovery guidance for a blocked plan, or the run reached
past the scope it was asked for — the isolation contract still holds through
recovery.

Do **not** propose continuing in the primary checkout as the default or
recommended recovery path. Default to a safe halt and offer:

1. re-attempt in a fresh, narrowly scoped worktree, or
2. inspect or discard the rejected worktree without merging.

Any path that edits the primary checkout needs an explicit, clearly labelled
confirmation from the user first. Editing the main working tree is never the
proposed or default option for work the user configured to be isolated.

## Cleanup needs merge evidence

`worktree.cleanup-wave` removes a worktree only when git agrees its branch is an
ancestor of HEAD. Anything else — blocked, conflicted, empty, missing, or merged
according to the manifest but not according to the repository — is preserved and
reported with the reason.

Ignored files are not automatically disposable, and worktree isolation does not
isolate databases, ports, accounts or caches. Declare those resources before
running plans in parallel; two isolated checkouts still share one dev database.

Adapted from `gsd-core/workflows/execute-phase/steps/worktree-recovery-policy.md`;
see [THIRD-PARTY-NOTICES](../THIRD-PARTY-NOTICES.md).
