# Worktree branch check (spawn-time guard)

Fail-closed verify-only guard for `harness-worktree` dispatch. The coordinator's root pin covers `orchestrator-worktree`; do not apply a harness namespace assumption to a coordinator-created checkout.

Before harness dispatch, capture the exact expected base. Substitute the actual SHA and an alternate only when the coordinator explicitly created a bookkeeping-only commit whose immediate parent is an accepted base. A worker verifies identity and never resets, moves refs or rewrites a checkout it did not create. A mismatch returns exit 42 for coordinator recovery.

<worktree_branch_check>
FIRST ACTION: HEAD assertion MUST run before anything else, and this block is
VERIFY-ONLY. Worktrees spawned by Claude Code's `isolation="worktree"` use the
`agent-<id>` namespace (previously `worktree-agent-<id>`; both are accepted). The orchestrator owns this worktree's lifecycle;
a sub-agent MUST NOT hold state-correction primitives (hard-reset, update-ref,
force-move, index-discard) on a worktree it did not create (#48, #2924). If ANY
assertion below fails, HALT immediately — print the FATAL line, `exit 42`, and let
the orchestrator (the lifecycle owner) decide recovery. Do NOT self-recover, do NOT
commit.
```bash
HEAD_REF=$(git symbolic-ref --quiet HEAD || echo "DETACHED")
ACTUAL_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$HEAD_REF" = "DETACHED" ] || echo "$ACTUAL_BRANCH" | grep -Eq '^(main|master|develop|trunk|release/.*)$'; then
  echo "FATAL: worktree HEAD on '$ACTUAL_BRANCH' (expected an assigned isolated worker branch); refusing to commit or self-recover via 'git update-ref' (#2924)." >&2
  exit 42
fi
if ! echo "$ACTUAL_BRANCH" | grep -Eq '^(codex/)?((worktree-)?agent-|worktree-wf_|phase-|quick-|review-|verify-)[A-Za-z0-9._/-]+$'; then
  echo "FATAL: worktree HEAD '$ACTUAL_BRANCH' is not in an accepted assigned worker namespace; refusing to commit (#2924)." >&2
  exit 42
fi
ACTUAL_BASE=$(git rev-parse HEAD)
EXPECTED_BASE_ALTERNATE="{EXPECTED_BASE_ALTERNATE}"
if [ "$ACTUAL_BASE" != "{EXPECTED_BASE}" ] && { [ -z "$EXPECTED_BASE_ALTERNATE" ] || [ "$ACTUAL_BASE" != "$EXPECTED_BASE_ALTERNATE" ]; }; then
  echo "FATAL: worktree base mismatch — HEAD is $ACTUAL_BASE, expected {EXPECTED_BASE}${EXPECTED_BASE_ALTERNATE:+ or $EXPECTED_BASE_ALTERNATE}. Orchestrator owns recovery; sub-agent refuses to rewrite the worktree (#48)." >&2
  exit 42
fi
```
</worktree_branch_check>
