# Mandatory isolated executor dispatch

Resolve `engineer_run query dispatch-isolation --raw --phase "${PHASE_NUMBER}"` once for the phase. Accept only harness-worktree or orchestrator-worktree; a failure or unknown value blocks dispatch. Run `engineer_run query worktree.reap-orphans` for owned stale lifecycle records. The guard hook is advisory; no setting disables the required isolation.

## Harness-created checkout

Dispatch the assigned exact executor role with inline model/effort, omitting inherit, and literal `isolation="worktree"` on Claude. Include the complete branch-check guard with captured base and assigned identity. Read actual worker branch/path from host metadata and call `engineer_run query worktree.record-agent "${plan_id}" --phase "${PHASE_NUMBER}" --branch "${WORKER_BRANCH}" --path "${WORKER_PATH}" --base "${EXPECTED_BASE}" --files ... --deletions ...`. Use exact declared lists, including an explicitly empty deletion list when none was authorized. If metadata is unavailable, block integration until the stopped worker's path and branch are established from evidence. Do not register the coordinator checkout.

## Coordinator-created checkout

Run `engineer_run query worktree.create "${plan_id}" --phase "${PHASE_NUMBER}" --base "${EXPECTED_BASE}" --files ... --deletions ...`. Use the returned path, branch and base without constructing a guessed name. Read orchestrator-root-pin.md and embed its complete guard with that exact path. Dispatch the same executor through the native Agent tool; do not start a background worker process or substitute primary-checkout execution.

## Join and integrate

After dispatch, wait without editing owned paths. Confirm worker stop, reconcile actual commits and complete SUMMARY, then join the entire wave before runtime integration. Exit 42 from a worker guard marks the plan blocked and preserves the checkout. Merge and cleanup use the phase registry with worktree.merge-wave and worktree.cleanup-wave; ownership, clean branches, completed summaries and explicit deletion declarations are mandatory. Never replace a refusal with direct Git merge or deletion.
