# Worktree branch check (spawn-time guard)

The canonical, fail-closed, **verify-only** guard embedded into an executor
prompt under `harness-worktree`, where the host chose the checkout's base and
the orchestrator cannot know what it picked. Under `orchestrator-worktree` the
runtime created the worktree and set its base, so there is nothing to
re-derive and the root pin in [worktree-path-safety](worktree-path-safety.md)
is the guard instead. This file is the single source of truth for the block —
do not inline a copy elsewhere.

**Contract for the orchestrator:** before dispatch, capture
`EXPECTED_BASE=$(git rev-parse HEAD)`, then embed the block below into the
subagent prompt verbatim, substituting `{EXPECTED_BASE}` with that revision.
When the wave deliberately makes a planning-record commit before dispatch,
substitute `{EXPECTED_BASE_ALTERNATE}` with that commit's immediate parent so an
executor that forked from either side passes the same guard. Otherwise
substitute `{EXPECTED_BASE_ALTERNATE}` with an empty string.

**The executor only verifies.** The orchestrator owns the worktree lifecycle, so
it performs any base correction — recreating the worktree on the expected base.
A subagent never rewrites a worktree it did not create: it has no business
holding hard-reset, `update-ref`, force-move or index-discard on someone else's
checkout, and an agent that "fixes" its own base silently discards whatever the
mismatch was trying to tell you.

<worktree_branch_check>
FIRST ACTION: this assertion runs before anything else, and it is VERIFY-ONLY.
Worktrees the host creates for a dispatch use the `agent-<id>` namespace
(`worktree-agent-<id>` is also accepted); worktrees this runtime creates use
`phase-*`, `quick-*`, `review-*` or `verify-*`. If ANY assertion below fails,
HALT immediately — print the FATAL line, `exit 42`, and let the orchestrator
decide recovery. Do NOT self-recover. Do NOT commit.

```bash
HEAD_REF=$(git symbolic-ref --quiet HEAD || echo "DETACHED")
ACTUAL_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$HEAD_REF" = "DETACHED" ] || echo "$ACTUAL_BRANCH" | grep -Eq '^(main|master|develop|trunk|release/.*)$'; then
  echo "FATAL: worktree HEAD is on '$ACTUAL_BRANCH' (expected an isolation branch); refusing to commit or self-recover." >&2
  exit 42
fi
if ! echo "$ACTUAL_BRANCH" | grep -Eq '^((worktree-)?agent-|worktree-wf_|phase-|quick-|review-|verify-)[A-Za-z0-9._/-]+$'; then
  echo "FATAL: worktree HEAD '$ACTUAL_BRANCH' is outside the isolation namespaces; refusing to commit." >&2
  exit 42
fi
ACTUAL_BASE=$(git rev-parse HEAD)
EXPECTED_BASE_ALTERNATE="{EXPECTED_BASE_ALTERNATE}"
if [ "$ACTUAL_BASE" != "{EXPECTED_BASE}" ] && { [ -z "$EXPECTED_BASE_ALTERNATE" ] || [ "$ACTUAL_BASE" != "$EXPECTED_BASE_ALTERNATE" ]; }; then
  echo "FATAL: worktree base mismatch — HEAD is $ACTUAL_BASE, expected {EXPECTED_BASE}${EXPECTED_BASE_ALTERNATE:+ or $EXPECTED_BASE_ALTERNATE}. The orchestrator owns recovery; this executor refuses to rewrite the worktree." >&2
  exit 42
fi
```

</worktree_branch_check>

## What the orchestrator does with exit 42

An executor that exits 42 has not committed anything. Treat its plan as
**blocked**:

- Do not merge or clean up its worktree. Preserve it for inspection.
- Do not count the wave as successful.
- Surface the mismatch to the user with the expected and actual base.

Never proceed past a halted executor on the assumption it succeeded. Its commits
are absent, not pending.
